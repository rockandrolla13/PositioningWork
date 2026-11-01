"""T0 to T4, placebos, Holm family and rule outcomes. Reads the weekly panel from the work folder, writes statistics to results.json."""
from __future__ import annotations

import json

import lib
import numpy as np
import pandas as pd
from posmon.indicators import taarss

LEVELS = ("bond", "issuer", "bucket")
SIGNALS = ("m1_4", "m2")


def add_targets(panel: pd.DataFrame) -> pd.DataFrame:
    """Forward and past spread changes by exact week offset, then the market adjustment within bucket."""
    p = panel.sort_values(["cusip", "week"]).copy()
    p["wk"] = ((p["week"] - p["week"].min()).dt.days // 7).astype(int)
    index = p.set_index(["cusip", "wk"])
    for h in lib.HORIZONS:
        key = pd.MultiIndex.from_arrays([p["cusip"], p["wk"] + h])
        p[f"ds{h}"] = index["spread"].reindex(key).to_numpy() - p["spread"].to_numpy()
        p[f"end{h}"] = index["date"].reindex(key).to_numpy()
        later = index["cum_level"].reindex(key).to_numpy()
        p[f"sell{h}"] = -(later - p["cum_level"].to_numpy()) / p["scale"].to_numpy()
    p["past4"] = p["spread"].to_numpy() - index["spread"].reindex(pd.MultiIndex.from_arrays([p["cusip"], p["wk"] - 4])).to_numpy()
    previous = pd.MultiIndex.from_arrays([p["cusip"], p["wk"] - 1])
    p["ds0"] = p["spread"].to_numpy() - index["spread"].reindex(previous).to_numpy()
    p["flow0"] = (p["cum_level"].to_numpy() - index["cum_level"].reindex(previous).to_numpy()) / p["scale"].to_numpy()
    for h in (0, *lib.HORIZONS):
        p[f"adj{h}"] = adjust(p, f"ds{h}")
    return p


def adjust(p: pd.DataFrame, col: str) -> np.ndarray:
    """Own change minus the median change of same-bucket bonds from other issuers in that week."""
    out = np.full(len(p), np.nan)
    values = p[col].to_numpy()
    issuers = p["issuer"].to_numpy()
    for _, index in p.groupby(["week", "bucket"]).indices.items():
        here = values[index]
        ok = ~np.isnan(here)
        for issuer in np.unique(issuers[index][ok]):
            others = here[ok & (issuers[index] != issuer)]
            if len(others) >= 3:
                mine = issuers[index] == issuer
                out[index[mine]] = here[mine] - np.median(others)
    return out


def aggregate(p: pd.DataFrame, level: str, signal: str, h: int, extra: list = None) -> pd.DataFrame:
    """Scale-weighted issuer or bucket panel. Signals add up across bonds in par. Changes average with scale weights."""
    data = p.dropna(subset=[signal, "scale"]).copy()
    key = {"issuer": ["issuer"], "bucket": ["bucket"]}[level]
    rows = []
    wanted = [f"ds{h}", f"adj{h}", "past4", "spread", *(extra or [])]
    for keys, group in data.groupby(["week", *key]):
        weight = group["scale"].to_numpy()
        row = {"week": keys[0], key[0]: keys[1], signal: float((group[signal] * weight).sum() / weight.sum()),
               "scale_total": float(weight.sum())}
        for col in wanted:
            values = group[col].to_numpy()
            ok = ~np.isnan(values)
            row[col] = float((values[ok] * weight[ok]).sum() / weight[ok].sum()) if ok.any() else np.nan
        rows.append(row)
    out = pd.DataFrame(rows)
    out["unit"] = out[key[0]]
    if level == "issuer":
        out["bucket"] = "all"
    else:
        out["issuer"] = out["bucket"]  # four-cluster panel: inference is Driscoll-Kraay instead
    if level == "bucket":
        market = out.groupby("week")[f"ds{h}"].transform("mean")
        out[f"adj{h}"] = out[f"ds{h}"] - market
    return out


def sample(frame: pd.DataFrame, h: int, which: str) -> pd.DataFrame:
    weeks = frame["week"]
    last = weeks + pd.to_timedelta(7 * h, unit="D")
    if which == "dev":
        return frame[last <= lib.DEV_END]
    return frame[(weeks >= lib.HOLD_START) & (last <= lib.HOLD_END)]


def standardise(frame: pd.DataFrame, cols: list, h: int) -> pd.DataFrame:
    out = frame.copy()
    for col in cols:
        sd = sample(out, h, "dev")[col].std()
        out[col] = out[col] / sd
    return out


def design(level: str, kind: str, h: int) -> dict:
    if kind == "TS":
        return {"y": f"adj{h}", "fe": ["unit"]}
    if level == "bond":
        return {"y": f"ds{h}", "fe": ["week_bucket"]}
    if level == "issuer":
        return {"y": f"ds{h}", "fe": ["week"]}
    return {"y": f"ds{h}", "fe": ["week", "unit"]}


def issuer_signs(frame: pd.DataFrame, y: str, x: str, fe: list) -> dict:
    """Slope for each issuer alone after the panel's fixed effects are removed."""
    data = frame.dropna(subset=[y, x])
    if data.empty:
        return {}
    ids = [lib.codes(data[name]) for name in fe]
    m = lib.absorb(data[[y, x]].to_numpy(float), ids)
    table = pd.DataFrame({"y": m[:, 0], "x": m[:, 1], "issuer": data["issuer"].to_numpy()})
    slopes = table.groupby("issuer").apply(lambda t: (t["x"] * t["y"]).sum() / (t["x"] ** 2).sum() if (t["x"] ** 2).sum() > 0 else np.nan, include_groups=False)
    return slopes.dropna().to_dict()


def placebo(frame: pd.DataFrame, y: str, x: str, fe_name: str, rule: str, draws: int = 499, seed: int = lib.SEED) -> dict:
    """Circular shift by bond, or week-label shuffle by issuer. The share of draws with a slope as large as the real one."""
    data = frame.dropna(subset=[y]).copy()
    full = frame.dropna(subset=[x])
    if len(data) < 30 or len(full) < 30:
        return {"p": 1.0, "ran": False}
    weeks = sorted(frame["week"].unique())
    w_id = {w: i for i, w in enumerate(weeks)}
    bonds = sorted(frame["unit"].unique())
    b_id = {b: i for i, b in enumerate(bonds)}
    matrix = np.full((len(bonds), len(weeks)), np.nan)
    matrix[full["unit"].map(b_id).to_numpy(), full["week"].map(w_id).to_numpy()] = full[x].to_numpy()
    data = data[data[x].notna()]
    row_b, row_w = data["unit"].map(b_id).to_numpy(), data["week"].map(w_id).to_numpy()
    groups = lib.codes(data[fe_name])
    target = data[y].to_numpy()
    def slope(values: np.ndarray) -> float:
        ok = ~np.isnan(values)
        if ok.sum() < 30:
            return np.nan
        g = lib.codes(groups[ok])
        a, b = lib.demean(values[ok], g), lib.demean(target[ok], g)
        s = (a * a).sum()
        return float((a * b).sum() / s) if s > 0 else np.nan
    actual = slope(matrix[row_b, row_w])
    rng = np.random.default_rng(seed)
    n_w = len(weeks)
    issuer_of = pd.Series(frame["issuer"].to_numpy(), index=frame["unit"].to_numpy()).groupby(level=0).first()
    issuer_ids = lib.codes(issuer_of.reindex(bonds))
    n_iss = issuer_ids.max() + 1
    out = []
    for _ in range(draws):
        if rule == "shift":
            low = min(13, max(n_w // 4, 1))
            offset = rng.integers(low, max(n_w - low, low + 1), size=len(bonds))
            values = matrix[row_b, (row_w + offset[row_b]) % n_w]
        else:
            perms = np.argsort(rng.random((n_iss, n_w)), axis=1)
            values = matrix[row_b, perms[issuer_ids[row_b], row_w]]
        out.append(slope(values))
    out = np.array(out)
    out = out[~np.isnan(out)]
    return {"p": float((1 + (np.abs(out) >= abs(actual)).sum()) / (len(out) + 1)), "actual": actual, "sd": float(out.std()),
            "draws": int(len(out)), "ran": True}


def prepare_level(p: pd.DataFrame, level: str, signal: str, h: int, extra: list = None) -> pd.DataFrame:
    if level == "bond":
        data = p.copy()
        data["unit"] = data["cusip"]
    else:
        data = aggregate(p, level, signal, h, extra)
    data["week_bucket"] = data["week"].astype(str) + data["bucket"].astype(str)
    return data


def t1_row(p: pd.DataFrame, level: str, kind: str, signal: str, h: int, placebos: bool = False) -> dict:
    data = prepare_level(p, level, signal, h)
    data = standardise(data, [signal], h)
    spec = design(level, kind, h)
    dk = level == "bucket"
    out = {"level": level, "design": kind, "signal": signal, "h": h}
    for which in ("dev", "hold"):
        part = sample(data, h, which)
        out[which] = lib.fit(part, spec["y"], signal, spec["fe"], h=h, dk=dk)
    hold = sample(data, h, "hold")
    ctrl_data = standardise(hold, ["past4", "spread"], h) if False else hold
    out["hold_controls"] = lib.fit(ctrl_data, spec["y"], signal, spec["fe"], controls=["past4", "spread"], h=h, dk=dk)
    out["bench_past4"] = lib.fit(ctrl_data, spec["y"], "past4", spec["fe"], h=h, dk=dk)
    out["bench_level"] = lib.fit(ctrl_data, spec["y"], "spread", spec["fe"], h=h, dk=dk)
    out["sd_y_hold"] = float(hold[spec["y"]].std())
    signs = issuer_signs(hold, spec["y"], signal, spec["fe"]) if level != "bucket" else {}
    out["issuer_slopes"] = {k: round(v, 3) for k, v in signs.items()}
    if placebos and level == "bond":
        fe_name = spec["fe"][0]
        out["placebo_shift"] = placebo(hold, spec["y"], signal, fe_name, "shift")
        out["placebo_shuffle"] = placebo(hold, spec["y"], signal, fe_name, "shuffle")
    if level == "bond":
        loo = []
        for issuer in sorted(hold["issuer"].unique()):
            res = lib.fit(hold[hold["issuer"] != issuer], spec["y"], signal, spec["fe"], h=h, draws=199)
            if res.get("b") is not None:
                loo.append(res["b"])
        out["loo_range"] = [min(loo), max(loo)] if loo else None
    return out


def hit_rates(p: pd.DataFrame) -> list:
    rows = []
    for signal in SIGNALS:
        for h in lib.HORIZONS:
            dev = sample(p, h, "dev").dropna(subset=[signal, f"adj{h}"])
            hold = sample(p, h, "hold").dropna(subset=[signal, f"adj{h}"])
            if dev.empty or hold.empty:
                continue
            low, high = dev[signal].quantile([0.2, 0.8])
            top, bottom = hold[hold[signal] >= high], hold[hold[signal] <= low]
            rows.append({"signal": signal, "h": h, "base_tighter": float((hold[f"adj{h}"] < 0).mean()),
                         "top_quintile_tighter": float((top[f"adj{h}"] < 0).mean()), "top_n": int(len(top)),
                         "base_wider": float((hold[f"adj{h}"] > 0).mean()),
                         "bottom_quintile_wider": float((bottom[f"adj{h}"] > 0).mean()), "bottom_n": int(len(bottom))})
    return rows


def t3(p: pd.DataFrame) -> list:
    data = p.copy()
    data["unit"] = data["cusip"]
    start = data["week"].min() + pd.Timedelta(weeks=26)
    data = data[data["week"] >= start]
    data["coverage"] = data["ledger_open"] / data["scale"]
    data = data[data["coverage"] >= 0.005]
    data["week_bucket"] = data["week"].astype(str) + data["bucket"]
    rows = []
    sec = data[data["has_sec"]]
    main = sec if p.drop_duplicates("cusip")["has_sec"].mean() > 0.5 else data
    for signal in ("pain_share", "pain_depth"):
        for h in lib.HORIZONS:
            for target, y in (("spread", f"adj{h}"), ("sell", f"sell{h}")):
                std = standardise(main, [signal], h)
                std = std.copy()
                hold = sample(std, h, "hold")
                row = {"signal": signal, "h": h, "target": target, "dev": lib.fit(sample(std, h, "dev"), y, signal, ["unit"], h=h),
                       "hold": lib.fit(hold, y, signal, ["unit"], h=h), "sd_y_hold": float(hold[y].std()),
                       "issuer_slopes": {k: round(v, 3) for k, v in issuer_signs(hold, y, signal, ["unit"]).items()},
                       "hold_controls": lib.fit(hold, y, signal, ["unit"], controls=["past4", "spread", "m1_4"], h=h),
                       "placebo_shift": placebo(hold, y, signal, "unit", "shift")}
                rows.append(row)
    return rows


def t4(p: pd.DataFrame, draws: int = 1999) -> dict:
    """Bond TS: same-week flow on same-week change, next week and next 4 weeks. Pairs bootstrap by issuer on the difference."""
    out = {}
    for name, sub in (("hold", "hold"), ("dev", "dev"), ):
        data = p.copy()
        data["unit"] = data["cusip"]
        sd = sample(data, 4, "dev")["flow0"].std()
        data["flow0"] = data["flow0"] / sd
        part = sample(data, 4, sub)
        rows = {}
        for h in (0, 1, 4):
            rows[f"h{h}"] = lib.fit(part, f"adj{h}", "flow0", ["unit"], h=max(h, 1))
        # Bootstrap on issuer-level moments with a common bond-demeaned x.
        stats = {}
        for h in (0, 1, 4):
            d = part.dropna(subset=["flow0", f"adj{h}"])
            ids = lib.codes(d["unit"])
            m = lib.absorb(d[["flow0", f"adj{h}"]].to_numpy(float), [ids])
            t = pd.DataFrame({"xy": m[:, 0] * m[:, 1], "xx": m[:, 0] ** 2, "issuer": d["issuer"].to_numpy()}).groupby("issuer").sum()
            stats[h] = t
        rng = np.random.default_rng(lib.SEED)
        issuers = stats[0].index.to_numpy()
        pick = rng.integers(0, len(issuers), size=(draws, len(issuers)))
        slope = {}
        for h, t in stats.items():
            t = t.reindex(issuers).fillna(0.0)
            slope[h] = t["xy"].to_numpy()[pick].sum(1) / t["xx"].to_numpy()[pick].sum(1)
        gap1 = np.abs(slope[0]) - np.abs(slope[1])
        gap4 = np.abs(slope[0]) - np.abs(slope[4])
        rows["abs_h0_minus_abs_h1_ci95"] = [float(np.quantile(gap1, 0.025)), float(np.quantile(gap1, 0.975))]
        rows["abs_h0_minus_abs_h4_ci95"] = [float(np.quantile(gap4, 0.025)), float(np.quantile(gap4, 0.975))]
        out[name] = rows
    return out


def t0(p: pd.DataFrame, life_note: dict) -> dict:
    res = {}
    # Flow persistence: pooled lag autocorrelation of weekly scaled flow, against randomly signed flow.
    data = p.dropna(subset=["flow0"]).copy()
    weekly = data.pivot_table(index="wk", columns="cusip", values="flow0")
    rng = np.random.default_rng(lib.SEED)
    persistence = {}
    for lag in (1, 4, 13):
        a, b = weekly.iloc[lag:].to_numpy(), weekly.iloc[:-lag].to_numpy()
        ok = ~(np.isnan(a) | np.isnan(b))
        by_bond = []
        placebo_rs = []
        for j in range(a.shape[1]):
            keep = ok[:, j]
            if keep.sum() >= 30 and a[keep, j].std() > 0 and b[keep, j].std() > 0:
                by_bond.append(np.corrcoef(a[keep, j], b[keep, j])[0, 1])
                signs = rng.choice([-1.0, 1.0], size=weekly.shape[0])
                ap, bp = (weekly.iloc[:, j].to_numpy() * signs)[lag:], (weekly.iloc[:, j].to_numpy() * signs)[:-lag]
                placebo_rs.append(np.corrcoef(ap[keep], bp[keep])[0, 1])
        persistence[f"lag{lag}"] = {"median_bond_ac": float(np.median(by_bond)), "share_positive": float(np.mean(np.array(by_bond) > 0)),
                                    "random_sign_median": float(np.median(placebo_rs)), "bonds": len(by_bond)}
    res["persistence"] = persistence
    # Issuer flow and spread in chosen event windows.
    issuer_week = data.assign(flow=data["flow0"] * data["scale"]).groupby(["issuer", "week"]).agg(flow=("flow", "sum"), scale=("scale", "sum"), ds=("ds0", "median"), adj=("adj0", "median")).reset_index()
    issuer_week["flow_pct"] = issuer_week["flow"] / issuer_week["scale"] * 100
    res["issuer_flow_weekly_sd_pct"] = issuer_week.groupby("issuer")["flow_pct"].std().round(3).to_dict()
    window = issuer_week[(issuer_week["week"] >= "2025-04-04") & (issuer_week["week"] <= "2025-04-18")]
    res["april_2025"] = window.groupby("issuer").agg(flow_pct=("flow_pct", "sum"), ds_bp=("ds", "sum"), adj_bp=("adj", "sum")).round(2).to_dict("index")
    sd = issuer_week.set_index(["issuer", "week"])
    big = issuer_week.reindex(issuer_week["flow_pct"].abs().sort_values(ascending=False).index).head(10)
    res["largest_issuer_weeks"] = [{"issuer": r.issuer, "week": str(r.week.date()), "flow_pct": round(r.flow_pct, 2), "ds_bp": round(r.ds, 1), "adj_bp": round(r.adj, 1)} for r in big.itertuples()]
    panel_week = data.groupby("week")["ds0"].median()
    fred = pd.read_csv(lib.HERE / "raw" / "fred" / "BAMLC0A0CM.csv", parse_dates=["observation_date"], index_col="observation_date")["BAMLC0A0CM"]
    fred = pd.to_numeric(fred, errors="coerce").dropna()
    fred_week = (fred.resample("W-FRI").last().diff() * 100).reindex(panel_week.index)
    common = pd.concat([panel_week, fred_week], axis=1).dropna()
    res["panel_vs_ig_oas"] = {"weeks": int(len(common)), "correlation": float(common.corr().iloc[0, 1]),
                              "sd_panel_bp": float(common.iloc[:, 0].std()), "sd_oas_bp": float(common.iloc[:, 1].std())}
    last = p.sort_values("week").groupby("cusip").tail(1)
    cum = last.groupby("issuer").apply(lambda t: float(t["cum_level"].sum() / t["scale"].sum() * 100), include_groups=False)
    res["net_buying_since_start_pct_of_amount"] = cum.round(2).to_dict()
    res.update(life_note)
    return res


def new_issues(p: pd.DataFrame) -> dict:
    """First-5-day customer flow for bonds born inside the panel, from bond-day data, against amount issued."""
    daily = pd.read_parquet(lib.WORK / "daily.parquet")
    life = pd.read_parquet(lib.WORK / "bond_life.parquet")
    calendar = pd.DatetimeIndex(pd.read_parquet(lib.WORK / "calendar.parquet")["date"])
    reference = pd.read_csv(lib.HERE / "bond_reference.csv").set_index("cusip")
    rows = []
    for cusip, group in daily.groupby("cusip"):
        first = life.loc[cusip, "first_print"]
        if first <= calendar[5] or cusip not in reference.index:
            continue
        amount = reference.loc[cusip, "amount_outstanding_usd"]
        pos = calendar.searchsorted(first)
        window = calendar[pos:pos + 5]
        part = group[group["date"].isin(window)]
        rows.append({"amount": amount, "first_buy": float(part["c_nd_buy"].sum()), "first_sell": float(part["c_nd_sell"].sum()),
                     "max_qty": float(life.loc[cusip, "max_qty"]), "life_gross": float(group["c_nd_buy"].sum() + group["c_nd_sell"].sum())})
    t = pd.DataFrame(rows)
    known = t.dropna(subset=["amount"])
    return {"bonds_born_in_panel": int(len(t)), "with_amount": int(len(known)),
            "median_first5_buy_pct": float((known["first_buy"] / known["amount"]).median() * 100),
            "median_first5_sell_pct": float((known["first_sell"] / known["amount"]).median() * 100),
            "median_first5_net_pct": float(((known["first_buy"] - known["first_sell"]) / known["amount"]).median() * 100),
            "median_max_trade_over_amount": float((known["max_qty"] / known["amount"]).median()),
            "median_share_of_life_gross_in_first5": float(((t["first_buy"] + t["first_sell"]) / t["life_gross"]).median())}


def event_time_and_blocks(p: pd.DataFrame) -> dict:
    """Added after results: does the 5-day mask suffice, does a month's flow trend beat its own reshuffle, and who makes the largest weeks."""
    daily = pd.read_parquet(lib.WORK / "daily.parquet")
    life = pd.read_parquet(lib.WORK / "bond_life.parquet")
    calendar = pd.DatetimeIndex(pd.read_parquet(lib.WORK / "calendar.parquet")["date"])
    reference = pd.read_csv(lib.HERE / "bond_reference.csv").set_index("cusip")
    daily["net"] = daily["c_buy"].fillna(0.0) - daily["c_sell"].fillna(0.0)
    bins = [(0, 4), (5, 9), (10, 19), (20, 39), (40, 79), (80, 159)]
    rows = {b: [] for b in bins}
    for cusip, group in daily.groupby("cusip"):
        first = life.loc[cusip, "first_print"]
        amount = reference["amount_outstanding_usd"].get(cusip, np.nan)
        if first <= calendar[5] or not amount > 0:
            continue
        day_number = calendar.searchsorted(group["date"]) - calendar.searchsorted(first)
        for low, high in bins:
            if calendar.searchsorted(first) + high < len(calendar):
                rows[(low, high)].append(group["net"].to_numpy()[(day_number >= low) & (day_number <= high)].sum() / amount * 100)
    event = {f"day_{low}_{high}": {"median_net_pct": float(np.median(v)), "mean_net_pct": float(np.mean(v)), "bonds": len(v)} for (low, high), v in rows.items() if v}
    # Monthly trend against the same daily flows in random order. Under no steadiness, 10% of bond-months beat their own 90th percentile.
    rng = np.random.default_rng(lib.SEED)
    daily["month"] = daily["date"].dt.to_period("M")
    records = []
    data = daily[(daily["issuer"].isin(lib.SPREAD_ISSUERS))]
    groups = list(data.groupby(["cusip", "month"]).indices.items())
    picks = rng.choice(len(groups), size=min(3000, len(groups)), replace=False)
    months = {m: calendar[calendar.to_period("M") == m] for m in data["month"].unique()}
    net_values, date_values = data["net"].to_numpy(), data["date"].to_numpy()
    for i in picks:
        (cusip, month), index = groups[i]
        days = months[month]
        first = life.loc[cusip, "first_print"]
        if first >= days[0] - pd.Timedelta(days=10) and first > calendar[5]:
            continue
        if len(index) < 10:
            continue
        flows = pd.Series(net_values[index], index=date_values[index]).reindex(days).fillna(0.0).to_numpy()
        if not np.abs(flows).sum() > 0:
            continue
        actual = abs(taarss(np.cumsum(flows)))
        fake = [abs(taarss(np.cumsum(rng.permutation(flows)))) for _ in range(99)]
        records.append(actual > np.quantile(fake, 0.9))
    trend = {"bond_months": len(records), "share_above_own_reshuffle_p90": float(np.mean(records)), "expected_if_no_steadiness": 0.10}
    # Largest issuer weeks: how much of the gross comes from one bond-day.
    data = p.dropna(subset=["flow0"]).assign(flow=lambda t: t["flow0"] * t["scale"])
    weeks = data.groupby(["issuer", "week"]).agg(flow=("flow", "sum"), scale=("scale", "sum")).reset_index()
    weeks["pct"] = weeks["flow"] / weeks["scale"] * 100
    top = weeks.reindex(weeks["pct"].abs().sort_values(ascending=False).index).head(6)
    blocks = []
    for row in top.itertuples():
        days = daily[(daily["issuer"] == row.issuer) & (daily["date"] > row.week - pd.Timedelta(days=7)) & (daily["date"] <= row.week)]
        biggest = days.reindex(days["net"].abs().sort_values(ascending=False).index).head(1)
        blocks.append({"issuer": row.issuer, "week": str(row.week.date()), "flow_pct": round(row.pct, 2),
                       "largest_bond_day_share_of_abs_net": float(biggest["net"].abs().sum() / days["net"].abs().sum())})
    sizes = {"flow0_sd_pct_of_amount_dev": float(sample(data, 4, "dev")["flow0"].std() * 100),
             "flow0_sd_pct_of_amount_hold": float(sample(data, 4, "hold")["flow0"].std() * 100),
             "m1_4_sd_pct_of_amount_dev": float(sample(p, 4, "dev")["m1_4"].std() * 100),
             "m2_sd_dev": float(sample(p, 4, "dev")["m2"].std())}
    return {"event_time_net_flow": event, "monthly_trend_vs_reshuffle": trend, "largest_week_blocks": blocks, "signal_sizes": sizes}


def robustness(reads: dict) -> dict:
    out = {}
    for name, panel in reads.items():
        rows = {}
        for signal in SIGNALS:
            for kind in ("TS", "CS"):
                for h in lib.HORIZONS:
                    row = t1_row(panel, "bond", kind, signal, h)
                    rows[f"{signal}_{kind}_{h}"] = {"b": row["hold"].get("b"), "t": row["hold"].get("t"), "p": row["hold"].get("p"), "n": row["hold"].get("n")}
        out[name] = rows
    return out


def main() -> None:
    panels = {name: add_targets(pd.read_parquet(lib.WORK / f"weekly_{name}.parquet")) for name in
              ["C", "C_A", "C_A_T", "C_dedupe_all", "C_dedupe_none", "C_no_mask", "C_dealer_level"]}
    p = panels["C"]

    rows = []
    for signal in SIGNALS:
        for level in LEVELS:
            for kind in ("TS", "CS"):
                for h in lib.HORIZONS:
                    rows.append(t1_row(p, level, kind, signal, h, placebos=True))
    t3_rows = t3(p)
    family = {f"T1|{r['signal']}|{r['level']}|{r['design']}|{r['h']}": (r["hold"].get("p") if r["hold"].get("b") is not None else 1.0) for r in rows}
    family.update({f"T3|{r['signal']}|{r['target']}|{r['h']}": (r["hold"].get("p") if r["hold"].get("b") is not None else 1.0) for r in t3_rows})
    adjusted = lib.holm(family)

    def verdict(key: str, row: dict, robust: dict | None) -> dict:
        hold, dev = row["hold"], row["dev"]
        if hold.get("b") is None:
            return {"label": "not run", "holm": 1.0}
        same_dev = dev.get("b") is not None and np.sign(dev["b"]) == np.sign(hold["b"])
        signs = row.get("issuer_slopes", {})
        agree = int(sum(np.sign(v) == np.sign(hold["b"]) for v in signs.values()))
        ctrl_t = row.get("hold_controls", {}).get("t")
        shift = row.get("placebo_shift", {}).get("p")
        checks = {"holm_lt_05": adjusted[key] < 0.05, "same_sign_dev": bool(same_dev), "shift_lt_05": (shift is not None and shift < 0.05),
                  "controls_t_gt_2": (ctrl_t is not None and abs(ctrl_t) > 2), "issuers_agree": agree, "issuers_n": len(signs)}
        raw = hold["p"]
        if checks["holm_lt_05"] and same_dev and checks["shift_lt_05"] and checks["controls_t_gt_2"] and agree >= 9:
            label = "leading (before rule 6 check)"
        elif raw < 0.05 and same_dev:
            label = "suggestive, not established"
        else:
            label = "no evidence"
        thin = hold.get("mde80") is not None and row["sd_y_hold"] > 0 and hold["mde80"] > 0.25 * row["sd_y_hold"]
        return {"label": label + (" (too thin to say)" if thin else ""), "holm": adjusted[key], "raw_p": raw, "checks": checks, "thin": bool(thin)}

    for r in rows:
        r["verdict"] = verdict(f"T1|{r['signal']}|{r['level']}|{r['design']}|{r['h']}", r, None)
    for r in t3_rows:
        r["verdict"] = verdict(f"T3|{r['signal']}|{r['target']}|{r['h']}", r, None)
    lib.save_part("t1_t2", rows)
    lib.save_part("t3", t3_rows)
    lib.save_part("family", {"size": len(family), "raw": family, "holm": adjusted})

    lib.save_part("hit_rates", hit_rates(p))
    lib.save_part("t4", {"customer_levels": t4(p), "dealer_levels": t4(panels["C_dealer_level"])})
    data = p.copy()
    data["cov"] = data["ledger_open"] / data["scale"]
    lib.save_part("ledger_coverage", {
        "median_coverage_pct": float(data["cov"].median() * 100), "p90_coverage_pct": float(data["cov"].quantile(0.9) * 100),
        "last_week_median_coverage_pct": float(data.sort_values("week").groupby("cusip")["cov"].last().median() * 100),
        "last_week_median_coverage_pct_sec": float(data[data.has_sec].sort_values("week").groupby("cusip")["cov"].last().median() * 100),
        "median_unmatched_over_scale_pct": float((data["ledger_unmatched"] / data["scale"]).median() * 100),
        "share_rows_coverage_ge_half_pct": float((data["cov"] >= 0.005).mean()),
        "median_pain_share": float(data["pain_share"].median()), "median_pain_depth_bp": float(data["pain_depth"].median()),
    })
    desc = t0(p, {"new_issues": new_issues(p)})
    lib.save_part("t0", desc)
    alt = {k: panels[k] for k in ["C_A", "C_A_T", "C_dedupe_all", "C_dedupe_none", "C_no_mask"]}
    alt["C_sec_only"] = p[p["has_sec"]]
    # Added after results, outside the family: within-week ranks tame heavy tails, and M1_13 was planned but left out of the family.
    ranked = p.copy()
    for col in SIGNALS:
        ranked[col] = ranked.groupby("week")[col].rank(pct=True) - 0.5
    alt["C_rank_signal"] = ranked
    long_window = p.copy()
    long_window["m1_4"] = long_window["m1_13"]
    alt["M1_13_in_place_of_M1_4"] = long_window
    lib.save_part("t0_extra", event_time_and_blocks(p))
    lib.save_part("robustness", robustness(alt))
    print(json.dumps({"family": len(family), "min_holm": min(adjusted.values()), "min_raw": min(family.values())}))


if __name__ == "__main__":
    main()
