"""Shared loaders, timing rules and statistics. Signals themselves come from posmon wherever posmon has them."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sps

HERE = Path(__file__).resolve().parent
SPEC = HERE.parents[1]
sys.path.insert(0, str(SPEC))
from posmon.data import publish_time  # noqa: E402
from posmon.stats import newey_west_ols  # noqa: E402

RAW = HERE / "raw"
DERIVED = HERE / "derived"
DERIVED.mkdir(exist_ok=True)

SEED = 42
NBOOT = 5000
FIT_START, FIT_END = "2006-06-13", "2010-12-31"
GS_OOS_START = "2011-01-04"
DESIGN_END = pd.Timestamp("2019-04-30")
HOLD_START = pd.Timestamp("2019-05-07")
HALF_A_END = pd.Timestamp("2022-12-27")
HALF_B_START = pd.Timestamp("2023-01-03")
# From the CFTC special announcements page, raw/cftc_special_announcements.html.
LATE_RELEASES = [("2023-01-31", "2023-03-14"), ("2025-09-30", "2025-12-23")]

UST = ["TU", "FV", "TY", "TN", "US", "WN"]
FX = ["EC", "JY", "BP", "AD", "CD", "SF", "NE"]
YIELD = {"TU": "DGS2", "FV": "DGS5", "TY": "DGS7", "TN": "DGS10", "US": "DGS20", "WN": "DGS30"}
FACE = {"TU": 200000.0, "FV": 100000.0, "TY": 100000.0, "TN": 100000.0, "US": 100000.0, "WN": 100000.0}
SPOT = {"EC": ("DEXUSEU", 1), "JY": ("DEXJPUS", -1), "BP": ("DEXUSUK", 1), "AD": ("DEXUSAL", 1),
        "CD": ("DEXCAUS", -1), "SF": ("DEXSZUS", -1), "NE": ("DEXUSNZ", 1)}
FX_SIZE = {"EC": 125000.0, "JY": 12500000.0, "BP": 62500.0, "AD": 100000.0, "CD": 100000.0, "SF": 125000.0,
           "NE": 100000.0}
HORIZONS = (4, 8, 13, 26)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def cftc(report: str, basis: str, symbol: str) -> pd.DataFrame:
    return pd.read_csv(RAW / f"cftc_{report}_{basis}_{symbol}.csv", parse_dates=["report_date"], index_col="report_date")


def fred(series: str) -> pd.Series:
    frame = pd.read_csv(RAW / f"fred_{series}.csv", parse_dates=["observation_date"], index_col="observation_date")
    return pd.to_numeric(frame[series], errors="coerce").dropna()


def dv01_frame() -> pd.DataFrame:
    long = pd.read_csv(RAW / "project_treasury_futures_dv01.csv", parse_dates=["date"])
    return long.pivot(index="date", columns="contract", values="dv01_usd")


def yields_bp() -> pd.DataFrame:
    """Forward-filled yields in basis points, per contract, on the union of their dates."""
    return pd.DataFrame({k: fred(v) for k, v in YIELD.items()}).ffill() * 100.0


def spot_usd(symbol: str) -> pd.Series:
    """USD per foreign unit."""
    series, sign = SPOT[symbol]
    raw = fred(series)
    return raw if sign == 1 else 1.0 / raw


def synthetic_price(symbol: str) -> pd.Series:
    """Roll-free price in percent of face: start at 100, then minus DV01/face x 100 x own-yield change in bp.

    The DV01 is the last weekly value known on the prior day, so the price uses no future DV01.
    """
    yld = fred(YIELD[symbol]) * 100.0
    dv01 = dv01_frame()[symbol].dropna()
    weight = dv01.reindex(yld.index.union(dv01.index)).ffill().reindex(yld.index).shift(1)
    step = -(weight / FACE[symbol] * 100.0) * yld.diff()
    step = step.dropna()
    return 100.0 + step.cumsum()


def asset_price(symbol: str) -> pd.Series:
    """Trading level used for ledgers and forward moves. Treasuries: synthetic price. FX: 100 x log(USD per unit)."""
    if symbol in UST:
        return synthetic_price(symbol)
    return 100.0 * np.log(spot_usd(symbol))


# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------


def level_at(series: pd.Series, dates: pd.DatetimeIndex) -> pd.Series:
    """Last observation on or before each date. NaN after the last observation's date."""
    values = series.dropna().sort_index()
    dates = pd.DatetimeIndex(dates)
    spots = values.index.searchsorted(dates, side="right") - 1
    data = np.where(spots >= 0, values.values[np.clip(spots, 0, None)], np.nan)
    late = np.asarray(dates > values.index[-1]) | np.asarray(dates.isna())
    data = np.where(late, np.nan, data)
    return pd.Series(data, index=dates)


def entry_dates(report_dates: pd.DatetimeIndex, trading: pd.DatetimeIndex) -> pd.Series:
    """First trading day on or after the Monday after release. Returns a Series indexed by report date."""
    out = []
    for report in report_dates:
        release = publish_time(report).tz_localize(None).normalize()
        monday = release + pd.Timedelta(days=7 - release.weekday())
        spot = trading.searchsorted(monday)
        out.append(trading[spot] if spot < len(trading) else pd.NaT)
    return pd.Series(out, index=report_dates)


def friday_dates(report_dates: pd.DatetimeIndex, trading: pd.DatetimeIndex) -> pd.Series:
    """Release-day close, or the next trading day. Not strictly tradable, since the quote and the release coincide."""
    out = []
    for report in report_dates:
        release = publish_time(report).tz_localize(None).normalize()
        spot = trading.searchsorted(release)
        out.append(trading[spot] if spot < len(trading) else pd.NaT)
    return pd.Series(out, index=report_dates)


def forward_from(series: pd.Series, start_dates: pd.Series, weeks: int) -> pd.Series:
    """level(start + 7 x weeks days) minus level(start), indexed like start_dates."""
    dates = pd.DatetimeIndex(start_dates.values)
    begin = level_at(series, dates)
    ending = level_at(series, dates + pd.Timedelta(days=7 * weeks))
    return pd.Series(ending.values - begin.values, index=start_dates.index)


def past_from(series: pd.Series, end_dates: pd.Series, weeks: int) -> pd.Series:
    dates = pd.DatetimeIndex(end_dates.values)
    ending = level_at(series, dates)
    begin = level_at(series, dates - pd.Timedelta(days=7 * weeks))
    return pd.Series(ending.values - begin.values, index=end_dates.index)


def period_mask(index: pd.Index, name: str, entry: pd.Series | None = None, weeks: int = 0) -> np.ndarray:
    """Boolean mask for a named sample. DESIGN and GS-OOS rows are purged so their forward window ends before the holdout."""
    dates = pd.DatetimeIndex(index)
    if name in ("DESIGN", "GS-OOS"):
        keep = dates <= DESIGN_END
        if name == "GS-OOS":
            keep &= dates >= pd.Timestamp(GS_OOS_START)
        if entry is not None:
            ends = pd.DatetimeIndex(entry.reindex(index).values) + pd.Timedelta(days=7 * weeks)
            keep &= np.asarray(ends <= DESIGN_END)
        return keep
    if name == "HOLDOUT":
        return dates >= HOLD_START
    if name == "H-A":
        return (dates >= HOLD_START) & (dates <= HALF_A_END)
    if name == "H-B":
        return dates >= HALF_B_START
    raise ValueError(name)


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------


def block_index(n: int, block: int, draws: int, rng: np.random.Generator) -> np.ndarray:
    """Circular block bootstrap positions, shape (draws, n)."""
    count = int(math.ceil(n / block))
    starts = rng.integers(0, n, size=(draws, count))
    picks = (starts[:, :, None] + np.arange(block)) % n
    return picks.reshape(draws, count * block)[:, :n]


def boot_p(draws: np.ndarray, null: float = 0.0) -> float:
    draws = draws[np.isfinite(draws)]
    if len(draws) == 0:
        return float("nan")
    below = (np.sum(draws <= null) + 1.0) / (len(draws) + 1.0)
    above = (np.sum(draws >= null) + 1.0) / (len(draws) + 1.0)
    return float(min(1.0, 2.0 * min(below, above)))


def interval(draws: np.ndarray) -> list:
    draws = draws[np.isfinite(draws)]
    return [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))]


def block_for(weeks: int) -> int:
    return max(8, 2 * weeks)


def nw_lag(weeks: int) -> int:
    return int(math.ceil(1.5 * weeks))


def student_p(t_value: float, n: int, weeks: int, regressors: int) -> tuple[float, int]:
    df = max(int(n // max(weeks, 1)) - regressors - 1, 1)
    return float(2.0 * sps.t.sf(abs(t_value), df)), df


def batch_corr(x: np.ndarray, y: np.ndarray, picks: np.ndarray) -> np.ndarray:
    a, b = x[picks], y[picks]
    a = a - a.mean(axis=1, keepdims=True)
    b = b - b.mean(axis=1, keepdims=True)
    return (a * b).sum(axis=1) / np.sqrt((a * a).sum(axis=1) * (b * b).sum(axis=1))


def batch_ols(y: np.ndarray, design: np.ndarray, picks: np.ndarray, chunk: int = 500) -> np.ndarray:
    """Coefficients for each draw. The design includes the constant."""
    rows = []
    for start in range(0, len(picks), chunk):
        part = picks[start:start + chunk]
        xb, yb = design[part], y[part]
        xtx = np.einsum("dti,dtj->dij", xb, xb)
        xty = np.einsum("dti,dt->di", xb, yb)
        rows.append(np.linalg.solve(xtx, xty[..., None])[..., 0])
    return np.vstack(rows)


# ---------------------------------------------------------------------------
# Time-series test
# ---------------------------------------------------------------------------


def ts_test(y: pd.Series, x: pd.Series, weeks: int, controls: pd.DataFrame | None = None, draws: int = NBOOT,
            seed: int = SEED, lag: int | None = None) -> dict:
    """Slope of y on x with optional controls. Newey-West, Student-t on N_eff, and block bootstrap."""
    names = ["x"] + (list(controls.columns) if controls is not None else [])
    frame = pd.concat([y.rename("y"), x.rename("x")] + ([controls] if controls is not None else []), axis=1).dropna()
    n = len(frame)
    if n < 30:
        return {"n": n, "status": "too_few_rows", "p_primary": float("nan")}
    lag = nw_lag(weeks) if lag is None else lag
    table = newey_west_ols(frame["y"], frame[names], lag)
    t_value = float(table.loc["x", "t"])
    p_nw, df = student_p(t_value, n, weeks, len(names))
    design = np.column_stack([np.ones(n), frame[names].values])
    picks = block_index(n, block_for(weeks), draws, np.random.default_rng(seed))
    slopes = batch_ols(frame["y"].values, design, picks)[:, 1]
    p_boot = boot_p(slopes)
    corr_ci = interval(batch_corr(frame["x"].values, frame["y"].values, picks))
    fitted = design @ np.linalg.lstsq(design, frame["y"].values, rcond=None)[0]
    r2 = 1.0 - ((frame["y"] - fitted) ** 2).sum() / ((frame["y"] - frame["y"].mean()) ** 2).sum()
    return {"n": n, "n_eff": round(n / weeks, 1), "df": df, "nw_lag": lag, "block": block_for(weeks),
            "beta": float(table.loc["x", "beta"]), "se_nw": float(table.loc["x", "se"]), "t_nw": t_value,
            "corr": float(frame["y"].corr(frame["x"])), "corr_ci_boot": corr_ci, "r2": float(r2), "p_nw": p_nw, "p_boot": p_boot,
            "ci_boot": interval(slopes), "p_primary": float(max(p_nw, p_boot)), "first": str(frame.index[0])[:10],
            "last": str(frame.index[-1])[:10]}


def paired_corr_test(a: pd.Series, b: pd.Series, y: pd.Series, weeks: int, draws: int = NBOOT, seed: int = SEED) -> dict:
    """corr(a, y) minus corr(b, y) with a paired block bootstrap on the same dates."""
    frame = pd.concat([a.rename("a"), b.rename("b"), y.rename("y")], axis=1).dropna()
    n = len(frame)
    if n < 30:
        return {"n": n, "status": "too_few_rows", "p_primary": float("nan")}
    picks = block_index(n, block_for(weeks), draws, np.random.default_rng(seed))
    diff = batch_corr(frame["a"].values, frame["y"].values, picks) - batch_corr(frame["b"].values, frame["y"].values, picks)
    return {"n": n, "n_eff": round(n / weeks, 1), "block": block_for(weeks), "corr_a": float(frame["a"].corr(frame["y"])),
            "corr_b": float(frame["b"].corr(frame["y"])),
            "diff": float(frame["a"].corr(frame["y"]) - frame["b"].corr(frame["y"])), "ci_boot": interval(diff),
            "p_boot": boot_p(diff), "p_primary": boot_p(diff)}


def hit_stats(signal: pd.Series, ahead: pd.Series) -> dict:
    """signal above 0 expects a fall in `ahead` (rates convention). Base rates sit beside the hits."""
    frame = pd.concat([signal.rename("s"), ahead.rename("a")], axis=1).dropna()
    if frame.empty:
        return {"n": 0}
    up, down = frame[frame["s"] > 0], frame[frame["s"] < 0]
    runs = (np.sign(frame["s"]) != np.sign(frame["s"]).shift()).sum()
    return {"n": int(len(frame)), "base_fall": float((frame["a"] < 0).mean()), "base_rise": float((frame["a"] > 0).mean()),
            "mean_all": float(frame["a"].mean()), "pos_n": int(len(up)),
            "pos_hit_fall": float((up["a"] < 0).mean()) if len(up) else None,
            "pos_avg": float(up["a"].mean()) if len(up) else None, "neg_n": int(len(down)),
            "neg_hit_rise": float((down["a"] > 0).mean()) if len(down) else None,
            "neg_avg": float(down["a"].mean()) if len(down) else None, "signal_runs": int(runs)}


# ---------------------------------------------------------------------------
# Panel test (Driscoll-Kraay and date-block bootstrap)
# ---------------------------------------------------------------------------


def _within(frame: pd.DataFrame, columns: list) -> pd.DataFrame:
    return frame[columns] - frame.groupby("contract")[columns].transform("mean")


def panel_prepare(panel: pd.DataFrame, y_col: str, x_col: str, controls: list | None = None) -> pd.DataFrame | None:
    """Contract effects removed, controls partialled out, x scaled to unit SD. Rows keep their date."""
    controls = controls or []
    need = ["date", "contract", y_col, x_col] + controls
    frame = panel[need].dropna()
    if frame.empty or frame[x_col].std() == 0:
        return None
    within = _within(frame, [y_col, x_col] + controls)
    y, x = within[y_col].values, within[x_col].values
    if controls:
        c = within[controls].values
        y = y - c @ np.linalg.lstsq(c, y, rcond=None)[0]
        x = x - c @ np.linalg.lstsq(c, x, rcond=None)[0]
    spread = x.std()
    if spread == 0:
        return None
    return pd.DataFrame({"date": frame["date"].values, "contract": frame["contract"].values, "y": y, "x": x / spread})


def panel_sums(prep: pd.DataFrame) -> pd.DataFrame:
    sums = pd.DataFrame({"date": prep["date"].values, "xx": prep["x"].values ** 2, "xy": prep["x"].values * prep["y"].values})
    return sums.groupby("date").sum().sort_index()


def panel_test(panel: pd.DataFrame, y_col: str, x_col: str, weeks: int, controls: list | None = None, draws: int = NBOOT,
               seed: int = SEED) -> dict:
    prep = panel_prepare(panel, y_col, x_col, controls)
    if prep is None:
        return {"n": 0, "status": "no_data", "p_primary": float("nan")}
    sums = panel_sums(prep)
    dates = len(sums)
    if dates < 30:
        return {"n": len(prep), "dates": dates, "status": "too_few_dates", "p_primary": float("nan")}
    xx, xy = sums["xx"].values, sums["xy"].values
    beta = xy.sum() / xx.sum()
    moments = pd.DataFrame({"date": prep["date"].values, "h": prep["x"].values * (prep["y"].values - beta * prep["x"].values)})
    h = moments.groupby("date")["h"].sum().sort_index().values
    lag = nw_lag(weeks)
    meat = float((h * h).sum())
    for step in range(1, min(lag, dates - 1) + 1):
        meat += 2.0 * (1.0 - step / (lag + 1.0)) * float((h[step:] * h[:-step]).sum())
    se = math.sqrt(max(meat, 0.0)) / xx.sum()
    t_value = beta / se if se > 0 else float("nan")
    p_dk, df = student_p(t_value, dates, weeks, 1 + len(controls or []))
    picks = block_index(dates, block_for(weeks), draws, np.random.default_rng(seed))
    draws_beta = xy[picks].sum(axis=1) / xx[picks].sum(axis=1)
    p_boot = boot_p(draws_beta)
    return {"n": int(len(prep)), "dates": int(dates), "contracts": int(prep["contract"].nunique()),
            "n_eff": round(dates / weeks, 1), "df": df, "nw_lag": lag, "block": block_for(weeks), "beta": float(beta),
            "se_dk": float(se), "t_dk": float(t_value), "p_dk": p_dk, "p_boot": p_boot, "ci_boot": interval(draws_beta),
            "p_primary": float(max(p_dk, p_boot)), "first": str(sums.index[0])[:10], "last": str(sums.index[-1])[:10]}


def panel_paired(panel: pd.DataFrame, y_col: str, col_a: str, col_b: str, weeks: int, sign_a: float = 1.0, sign_b: float = 1.0,
                 draws: int = NBOOT, seed: int = SEED) -> dict:
    """sign_a x b(a) minus sign_b x b(b) on the rows where both exist. Date blocks are shared."""
    frame = panel[["date", "contract", y_col, col_a, col_b]].dropna()
    prep_a = panel_prepare(frame, y_col, col_a)
    prep_b = panel_prepare(frame, y_col, col_b)
    if prep_a is None or prep_b is None:
        return {"n": 0, "status": "no_data", "p_primary": float("nan")}
    sums_a, sums_b = panel_sums(prep_a), panel_sums(prep_b)
    dates = sums_a.index.intersection(sums_b.index)
    if len(dates) < 30:
        return {"n": len(prep_a), "status": "too_few_dates", "p_primary": float("nan")}
    a, b = sums_a.loc[dates], sums_b.loc[dates]
    beta_a = a["xy"].sum() / a["xx"].sum()
    beta_b = b["xy"].sum() / b["xx"].sum()
    picks = block_index(len(dates), block_for(weeks), draws, np.random.default_rng(seed))
    draws_a = a["xy"].values[picks].sum(axis=1) / a["xx"].values[picks].sum(axis=1)
    draws_b = b["xy"].values[picks].sum(axis=1) / b["xx"].values[picks].sum(axis=1)
    diff = sign_a * draws_a - sign_b * draws_b
    return {"n": int(len(frame)), "dates": int(len(dates)), "n_eff": round(len(dates) / weeks, 1), "beta_a": float(beta_a),
            "beta_b": float(beta_b), "diff": float(sign_a * beta_a - sign_b * beta_b), "ci_boot": interval(diff),
            "p_boot": boot_p(diff), "p_primary": boot_p(diff), "se_boot": float(np.nanstd(diff))}


def panel_hits(panel: pd.DataFrame, y_col: str, up_mask: pd.Series, down_mask: pd.Series) -> dict:
    """Up rows expect y above 0. Down rows expect y below 0. Base rates come from the same usable rows."""
    usable = panel[y_col].notna()
    y = panel.loc[usable, y_col]
    up = y[up_mask.reindex(y.index).fillna(False).astype(bool)]
    down = y[down_mask.reindex(y.index).fillna(False).astype(bool)]
    return {"n": int(len(y)), "base_up": float((y > 0).mean()) if len(y) else None,
            "base_down": float((y < 0).mean()) if len(y) else None, "up_n": int(len(up)),
            "up_hit": float((up > 0).mean()) if len(up) else None, "up_avg": float(up.mean()) if len(up) else None,
            "down_n": int(len(down)), "down_hit": float((down < 0).mean()) if len(down) else None,
            "down_avg": float(down.mean()) if len(down) else None}


# ---------------------------------------------------------------------------
# Multiple testing and strategy metrics
# ---------------------------------------------------------------------------


def holm(pvalues: dict) -> dict:
    """Holm step-down. A test that could not run counts as p = 1."""
    names = list(pvalues)
    raw = np.array([1.0 if (pvalues[k] is None or not np.isfinite(pvalues[k])) else float(pvalues[k]) for k in names])
    order = np.argsort(raw)
    adjusted = np.empty(len(raw))
    running = 0.0
    for rank, spot in enumerate(order):
        running = max(running, min(1.0, (len(raw) - rank) * raw[spot]))
        adjusted[spot] = running
    return {k: float(v) for k, v in zip(names, adjusted)}


def strategy_metrics(returns: pd.Series, benchmark: pd.Series | None = None, seed: int = SEED, draws: int = NBOOT) -> dict:
    """Weekly decimal net returns. Sharpe and IR annualised by sqrt(52), the weekly form of sqrt(252)."""
    series = returns.dropna()
    n = len(series)
    if n < 30 or series.std() == 0:
        return {"n": n, "status": "too_few_rows_or_flat"}
    sharpe = float(series.mean() / series.std() * math.sqrt(52))
    wealth = series.cumsum()
    drawdown = float((wealth - wealth.cummax()).min())
    years = n / 52.0
    picks = block_index(n, 26, draws, np.random.default_rng(seed))
    resampled = series.values[picks]
    boot = resampled.mean(axis=1) / resampled.std(axis=1) * math.sqrt(52)
    out = {"n": n, "years": round(years, 2), "ann_return": float(series.mean() * 52), "ann_vol": float(series.std() * math.sqrt(52)),
           "sharpe": sharpe, "t_stat": float(sharpe * math.sqrt(years)), "max_drawdown": drawdown,
           "sharpe_ci_boot": interval(boot), "p_boot": boot_p(boot), "p_primary": boot_p(boot)}
    if benchmark is not None:
        frame = pd.concat([series.rename("a"), benchmark.rename("b")], axis=1).dropna()
        active = frame["a"] - frame["b"]
        if active.std() > 0:
            out["info_ratio"] = float(active.mean() / active.std() * math.sqrt(52))
        picks = block_index(len(frame), 26, draws, np.random.default_rng(seed + 1))
        a, b = frame["a"].values[picks], frame["b"].values[picks]
        diff = a.mean(axis=1) / a.std(axis=1) * math.sqrt(52) - b.mean(axis=1) / b.std(axis=1) * math.sqrt(52)
        out["sharpe_minus_benchmark"] = float(frame["a"].mean() / frame["a"].std() * math.sqrt(52)
                                              - frame["b"].mean() / frame["b"].std() * math.sqrt(52))
        out["sharpe_diff_ci_boot"] = interval(diff)
        out["p_diff_boot"] = boot_p(diff)
    return out


def rotation_p_ts(y: pd.Series, x: pd.Series, weeks: int, control: pd.Series | None = None) -> dict:
    """Rotate the signal against the outcome. Keeps both series' own persistence, so it does not assume a model.

    The statistic is the absolute slope (partial slope with a control). Shifts stay at least one horizon away from zero.
    """
    columns = [y.rename("y"), x.rename("x")] + ([control.rename("c")] if control is not None else [])
    frame = pd.concat(columns, axis=1).dropna()
    n = len(frame)
    if n < 2 * weeks + 30:
        return {"p_rotation": float("nan"), "rotations": 0}
    y_v, x_v = frame["y"].values, frame["x"].values

    def slope(values: np.ndarray) -> float:
        if control is None:
            return float(np.polyfit(values, y_v, 1)[0])
        design = np.column_stack([np.ones(n), values, frame["c"].values])
        return float(np.linalg.lstsq(design, y_v, rcond=None)[0][1])

    observed = abs(slope(x_v))
    draws = np.array([abs(slope(np.roll(x_v, shift))) for shift in range(weeks, n - weeks)])
    return {"p_rotation": float((np.sum(draws >= observed) + 1.0) / (len(draws) + 1.0)), "rotations": int(len(draws))}


def rotation_p_panel(panel: pd.DataFrame, y_col: str, x_col: str, weeks: int, control: str | None = None) -> dict:
    """Rotate every contract's signal by the same number of weeks, keeping cross-contract links. Statistic: absolute slope."""
    needed = ["date", "contract", y_col, x_col] + ([control] if control else [])
    frame = panel[needed]
    dates = np.sort(frame["date"].unique())
    if len(dates) < 2 * weeks + 30:
        return {"p_rotation": float("nan"), "rotations": 0}
    x_wide = frame.pivot(index="date", columns="contract", values=x_col).reindex(dates)
    y_wide = frame.pivot(index="date", columns="contract", values=y_col).reindex(index=dates, columns=x_wide.columns)
    c_wide = None
    if control:
        c_wide = frame.pivot(index="date", columns="contract", values=control).reindex(index=dates, columns=x_wide.columns).values
    x_a, y_a = x_wide.values, y_wide.values

    def slope(values: np.ndarray) -> float:
        mask = ~np.isnan(values) & ~np.isnan(y_a)
        if c_wide is not None:
            mask &= ~np.isnan(c_wide)
        if mask.sum() < 30:
            return float("nan")
        def within(array):
            total = np.where(mask, array, 0.0).sum(axis=0)
            count = mask.sum(axis=0)
            mean = np.divide(total, count, out=np.zeros_like(total, dtype=float), where=count > 0)
            return np.where(mask, array - mean, 0.0)
        a, b = within(values), within(y_a)
        if c_wide is not None:
            c = within(c_wide)
            cc = (c * c).sum()
            if cc > 0:
                a = a - c * (a * c).sum() / cc
                b = b - c * (b * c).sum() / cc
        spread = a[mask].std()
        if spread == 0:
            return float("nan")
        return float((a * b).sum() / (a * a).sum() * spread)

    observed = slope(x_a)
    draws = np.array([slope(np.roll(x_a, shift, axis=0)) for shift in range(weeks, len(dates) - weeks)])
    draws = np.abs(draws[np.isfinite(draws)])
    if not np.isfinite(observed) or len(draws) == 0:
        return {"p_rotation": float("nan"), "rotations": 0}
    return {"p_rotation": float((np.sum(draws >= abs(observed)) + 1.0) / (len(draws) + 1.0)), "rotations": int(len(draws))}


def power_for_corr(target: float, n_eff: float, alpha: float) -> float:
    """Power of a two-sided test of zero correlation against `target`, by the Fisher transform."""
    shift = abs(math.atanh(target)) * math.sqrt(max(n_eff - 3.0, 1.0))
    critical = sps.norm.isf(alpha / 2.0)
    return float(sps.norm.sf(critical - shift) + sps.norm.cdf(-critical - shift))


def min_detectable_corr(n_eff: float, alpha: float) -> float:
    df = max(int(n_eff) - 2, 1)
    t = sps.t.isf(alpha / 2.0, df)
    return float(t / math.sqrt(df + t * t))
