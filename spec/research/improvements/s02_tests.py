"""Run every test listed in plan.md and write results.json. No test chooses anything from the holdout."""
import json
import math
import pickle
import warnings

import numpy as np
import pandas as pd
from scipy import stats as sps

import lib
from lib import (DERIVED, DESIGN_END, FX, GS_OOS_START, HALF_A_END, HALF_B_START, HERE, HOLD_START, LATE_RELEASES, NBOOT, RAW,
                 SEED, UST, block_for, block_index, boot_p, forward_from, hit_stats, holm, interval, level_at, nw_lag,
                 paired_corr_test, panel_hits, panel_paired, panel_test, past_from, period_mask, student_p, ts_test)
from posmon.indicators import dv01_weighted_net
from posmon.ledger import RemovalRule
from posmon.stats import newey_west_ols
from s01_signals import pain_rows

warnings.simplefilter("ignore", RuntimeWarning)
warnings.simplefilter("ignore", DeprecationWarning)

R = {}  # every result, by test
REG = {}  # the registry behind the Holm tables
PERIODS = ("GS-OOS", "HOLDOUT", "H-A", "H-B")
GROUPS = ("am_TYUS", "am_all6", "lev", "spec")
THREE = ("am_TYUS", "lev", "spec")


def reg(test_id, tier, text, result, sign_ok=None, extra_ok=True, stat=None, design=None, note=None):
    """Record one hypothesis. Tier is primary or secondary. A failure to run counts as p = 1 in Holm."""
    p_value = result.get("p_primary", float("nan")) if isinstance(result, dict) else float("nan")
    REG[test_id] = {"id": test_id, "tier": tier, "test": text, "p_raw": p_value, "stat": stat, "design_stat": design,
                    "sign_ok": sign_ok, "extra_ok": extra_ok, "n": result.get("n") if isinstance(result, dict) else None,
                    "n_eff": result.get("n_eff") if isinstance(result, dict) else None,
                    "ci_boot": result.get("ci_boot") if isinstance(result, dict) else None, "note": note,
                    "status": result.get("status", "ok") if isinstance(result, dict) else "not_run"}


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

with open(DERIVED / "i5.pkl", "rb") as handle:
    I5 = pickle.load(handle)
PANEL = pd.read_pickle(DERIVED / "panel.pkl")
INDEX, TEN = I5["index"], I5["ten"]
ENTRY, FRIDAY, TUESDAY = I5["entry"], I5["friday"], I5["tuesday"]
LEVEL_T = level_at(TEN, INDEX)
LEVEL_T.index = INDEX
DY = LEVEL_T.diff()
FIT_MASK = (INDEX >= pd.Timestamp(lib.FIT_START)) & (INDEX <= pd.Timestamp(lib.FIT_END))
FIT_SD = float(DY[FIT_MASK].std())
AHEAD = {("mon", k): forward_from(TEN, ENTRY, k) for k in lib.HORIZONS}
AHEAD.update({("tue", k): forward_from(TEN, TUESDAY, k) for k in lib.HORIZONS})
AHEAD.update({("fri", k): forward_from(TEN, FRIDAY, k) for k in lib.HORIZONS})
BENCH = {"mon": past_from(TEN, ENTRY, 26), "tue": past_from(TEN, TUESDAY, 26), "fri": past_from(TEN, FRIDAY, 26)}
BENCH_Z = {key: value / (FIT_SD * math.sqrt(26)) for key, value in BENCH.items()}
START = {"mon": ENTRY, "tue": TUESDAY, "fri": FRIDAY}


def score_of(group):
    return I5["groups"][group]["table"]["score"]


def rule_of(series, threshold=0.25):
    return pd.Series(np.where(series > threshold, 1.0, np.where(series < -threshold, -1.0, 0.0)), index=series.index).where(series.notna())


def mask_for(period, entry="mon", weeks=26):
    return pd.Series(period_mask(INDEX, period, START[entry], weeks), index=INDEX)


def on_period(frame, period, weeks, entry="mon"):
    return frame[mask_for(period, entry, weeks)]


# ---------------------------------------------------------------------------
# T1, T2, T5: I5 and the benchmark
# ---------------------------------------------------------------------------


def i5_table(entry, k):
    out = {}
    y = AHEAD[(entry, k)]
    for name in GROUPS + ("benchmark",):
        x = BENCH[entry] if name == "benchmark" else score_of(name)
        rule = rule_of(BENCH_Z[entry] if name == "benchmark" else x)
        rows = {}
        for period in PERIODS:
            keep = mask_for(period, entry, k)
            rows[period] = {"test": ts_test(y[keep], x[keep], k), "hits": hit_stats(rule[keep], y[keep])}
        out[name] = rows
    return out


def t1():
    R["T1"] = {"monday_26w": i5_table("mon", 26), "tuesday_26w_lookahead": i5_table("tue", 26)}
    table = R["T1"]["monday_26w"]
    ids = {"am_TYUS": "T1.1", "am_all6": "T1.2", "lev": "T1.3", "spec": "T1.4"}
    for name, test_id in ids.items():
        hold, gs = table[name]["HOLDOUT"], table[name]["GS-OOS"]
        hits = hold["hits"]
        both = (hits.get("pos_hit_fall") or 0) > hits.get("base_fall", 1) and (hits.get("neg_hit_rise") or 0) > hits.get("base_rise", 1)
        reg(test_id, "primary", f"I5 {name}, 26w, Monday entry, slope of forward DGS10 on score", hold["test"],
            sign_ok=hold["test"].get("beta", 0) < 0, extra_ok=both, stat=hold["test"].get("corr"), design=gs["test"].get("corr"))
    hold, gs = table["benchmark"]["HOLDOUT"], table["benchmark"]["GS-OOS"]
    reg("T1.5", "primary", "Benchmark: past 26w change, 26w, Monday entry", hold["test"], sign_ok=hold["test"].get("beta", 0) < 0,
        stat=hold["test"].get("corr"), design=gs["test"].get("corr"))
    # Secondary: Tuesday entry and paired comparisons.
    tues = R["T1"]["tuesday_26w_lookahead"]
    for name in GROUPS + ("benchmark",):
        hold = tues[name]["HOLDOUT"]["test"]
        reg(f"T1.S.tue.{name}", "secondary", f"{name}, 26w, Tuesday entry (look-ahead)", hold, sign_ok=hold.get("beta", 0) < 0, stat=hold.get("corr"))
    y = AHEAD[("mon", 26)]
    pairs = {}
    keep = mask_for("HOLDOUT")
    pairs["am_TYUS_minus_am_all6"] = paired_corr_test(score_of("am_TYUS")[keep], score_of("am_all6")[keep], y[keep], 26)
    reg("T1.S.TYUS_vs_all6", "secondary", "am_TYUS minus am_all6 corr", pairs["am_TYUS_minus_am_all6"], stat=pairs["am_TYUS_minus_am_all6"].get("diff"))
    for name in GROUPS:
        res = paired_corr_test(score_of(name)[keep], BENCH["mon"][keep], y[keep], 26)
        pairs[f"{name}_minus_benchmark"] = res
        reg(f"T1.S.{name}_vs_bench", "secondary", f"{name} corr minus benchmark corr, 26w", res, sign_ok=res.get("diff", 0) < 0, stat=res.get("diff"))
    R["T1"]["paired_holdout"] = pairs
    # How much of the published -43 percent came from the fit period itself? Tuesday basis, as Goldman measured it.
    claim = {}
    tue = AHEAD[("tue", 26)]
    cut = (INDEX + pd.Timedelta(weeks=26)) <= DESIGN_END
    fit_rows = cut & (INDEX <= pd.Timestamp(lib.FIT_END))
    post_rows = cut & (INDEX >= pd.Timestamp(GS_OOS_START))
    for name in GROUPS + ("benchmark",):
        x = BENCH["tue"] if name == "benchmark" else score_of(name)
        frame = pd.concat([x.rename("x"), tue.rename("y")], axis=1)
        claim[name] = {"whole_to_apr_2019": float(frame[cut].dropna().corr().iloc[0, 1]), "fit_rows_2006_2010": float(frame[fit_rows].dropna().corr().iloc[0, 1]),
                       "post_fit_2011_2018": float(frame[post_rows].dropna().corr().iloc[0, 1]), "n_fit_rows": int(frame[fit_rows].dropna().shape[0]), "n_post_rows": int(frame[post_rows].dropna().shape[0])}
    R["T1"]["published_corr_split"] = claim


def paired_two_y(x, y_a, y_b, weeks, seed=SEED):
    """corr(x, y_a) minus corr(x, y_b) with a shared block bootstrap."""
    frame = pd.concat([x.rename("x"), y_a.rename("a"), y_b.rename("b")], axis=1).dropna()
    n = len(frame)
    picks = block_index(n, block_for(weeks), NBOOT, np.random.default_rng(seed))
    diff = lib.batch_corr(frame["x"].values, frame["a"].values, picks) - lib.batch_corr(frame["x"].values, frame["b"].values, picks)
    gap = float(frame["x"].corr(frame["a"]) - frame["x"].corr(frame["b"]))
    return {"n": n, "n_eff": round(n / weeks, 1), "corr_a": float(frame["x"].corr(frame["a"])), "corr_b": float(frame["x"].corr(frame["b"])),
            "diff": gap, "ci_boot": interval(diff), "p_boot": boot_p(diff), "p_primary": boot_p(diff)}


def rule_backtest_bp(rule, start):
    """Average weekly bp earned by a +1/0/-1 duration rule entered at `start`. A sign of the lag's cost, not a strategy."""
    dates = pd.DatetimeIndex(start.values)
    level = pd.Series(level_at(TEN, dates).values, index=start.index)
    pnl = (-(level.shift(-1) - level)) * rule
    pnl = pnl.dropna()
    return pnl


def t2():
    out = {"by_entry": {}, "paired_tue_minus_mon": {}, "bp_cost": {}}
    for k in (4, 13, 26):
        for entry in ("tue", "fri", "mon"):
            out["by_entry"][f"{entry}_{k}w"] = i5_table(entry, k) if k != 26 or entry == "fri" else None
    for entry in ("tue", "mon"):
        out["by_entry"][f"{entry}_26w"] = R["T1"]["tuesday_26w_lookahead" if entry == "tue" else "monday_26w"]
    keep = mask_for("HOLDOUT")
    for name in GROUPS:
        for k in (4, 13, 26):
            res = paired_two_y(score_of(name)[keep], AHEAD[("tue", k)][keep], AHEAD[("mon", k)][keep], k)
            out["paired_tue_minus_mon"][f"{name}_{k}w"] = res
            test_id = "T2.1" if (name == "am_TYUS" and k == 26) else f"T2.S.lag.{name}.{k}"
            tier = "primary" if test_id == "T2.1" else "secondary"
            costly = (res["ci_boot"][0] > 0 or res["ci_boot"][1] < 0 or abs(res["diff"]) > 0.05)
            reg(test_id, tier, f"Lag cost {name} {k}w: corr(Tuesday) minus corr(Monday)", res, sign_ok=True, stat=res["diff"], note="costly" if costly else "not costly")
        rule = rule_of(score_of(name))
        for period in ("GS-OOS", "HOLDOUT"):
            keep_p = pd.Series(period_mask(INDEX, period), index=INDEX)
            tue = rule_backtest_bp(rule[keep_p], TUESDAY[keep_p])
            mon = rule_backtest_bp(rule[keep_p], ENTRY[keep_p])
            out["bp_cost"][f"{name}_{period}"] = {
                "tue_bp_per_week": float(tue.mean()), "mon_bp_per_week": float(mon.mean()), "tue_sharpe": float(tue.mean() / tue.std() * math.sqrt(52)),
                "mon_sharpe": float(mon.mean() / mon.std() * math.sqrt(52))}
    # Late releases dropped, on the holdout.
    late = pd.Series(False, index=INDEX)
    for first, last in LATE_RELEASES:
        late |= (INDEX >= pd.Timestamp(first)) & (INDEX <= pd.Timestamp(last))
    out["late_release_weeks_dropped"] = int((late & keep).sum())
    out["late_dropped"] = {}
    for name in GROUPS + ("benchmark",):
        x = BENCH["mon"] if name == "benchmark" else score_of(name)
        res = ts_test(AHEAD[("mon", 26)][keep & ~late], x[keep & ~late], 26)
        out["late_dropped"][name] = res
        reg(f"T2.S.late.{name}", "secondary", f"{name}, 26w, late-release weeks dropped", res, sign_ok=res.get("beta", 0) < 0, stat=res.get("corr"))
    # Fresh score: add the yield move from T to E, which is known at entry and the Tuesday score misses.
    out["fresh"] = {}
    move = (pd.Series(level_at(TEN, pd.DatetimeIndex(ENTRY.values)).values, index=INDEX) - LEVEL_T)
    for name in THREE:
        table = I5["groups"][name]["table"]
        fresh = table["score"] + move / table["scale"]
        res = {k: ts_test(AHEAD[("mon", k)][keep], fresh[keep], k) for k in (4, 13, 26)}
        pair = {k: paired_corr_test(fresh[keep], table["score"][keep], AHEAD[("mon", k)][keep], k) for k in (4, 13, 26)}
        out["fresh"][name] = {"tests": res, "fresh_minus_plain": pair}
        for k in (4, 13, 26):
            reg(f"T2.S.fresh.{name}.{k}", "secondary", f"Fresh {name} minus plain, {k}w, corr difference", pair[k], sign_ok=pair[k].get("diff", 0) < 0, stat=pair[k].get("diff"))
    R["T2"] = out


def t5():
    out = {f"{k}w": i5_table("mon", k) for k in (4, 8, 13)}
    out["26w"] = R["T1"]["monday_26w"]
    R["T5"] = out
    for spot, k in enumerate((4, 8, 13), start=1):
        hold, gs = out[f"{k}w"]["am_TYUS"]["HOLDOUT"]["test"], out[f"{k}w"]["am_TYUS"]["GS-OOS"]["test"]
        reg(f"T5.{spot}", "primary", f"I5 am_TYUS at {k}w", hold, sign_ok=hold.get("beta", 0) < 0, stat=hold.get("corr"), design=gs.get("corr"))
        for name in ("am_all6", "lev", "spec", "benchmark"):
            sec = out[f"{k}w"][name]["HOLDOUT"]["test"]
            reg(f"T5.S.{name}.{k}", "secondary", f"{name} at {k}w", sec, sign_ok=sec.get("beta", 0) < 0, stat=sec.get("corr"),
                design=out[f"{k}w"][name]["GS-OOS"]["test"].get("corr"))


# ---------------------------------------------------------------------------
# T3: does the score add to the benchmark
# ---------------------------------------------------------------------------


def expanding_forecasts(y, predictors, entry, weeks, start):
    """Fit with rows whose forward window has finished by this entry. Forecast the holdout rows only."""
    rows = pd.concat([y.rename("y"), predictors, entry.rename("entry")], axis=1).dropna()
    fit_rows = rows[rows.index >= pd.Timestamp(start)]
    columns = list(predictors.columns)
    forecasts = {}
    for stamp in rows.index[rows.index >= HOLD_START]:
        now = rows.loc[stamp, "entry"]
        usable = fit_rows[fit_rows["entry"] + pd.Timedelta(days=7 * weeks) <= now]
        if len(usable) < 52:
            continue
        design = np.column_stack([np.ones(len(usable))] + [usable[c].values for c in columns]) if columns else np.ones((len(usable), 1))
        coef = np.linalg.lstsq(design, usable["y"].values, rcond=None)[0]
        point = np.concatenate([[1.0], rows.loc[stamp, columns].values.astype(float)]) if columns else np.array([1.0])
        forecasts[stamp] = float(point @ coef)
    return pd.Series(forecasts)


def oos_compare(y, x_small, x_big, weeks):
    empty = pd.DataFrame(index=y.index)
    mean_only = expanding_forecasts(y, empty, ENTRY, weeks, GS_OOS_START)
    small = expanding_forecasts(y, x_small, ENTRY, weeks, GS_OOS_START)
    big = expanding_forecasts(y, x_big, ENTRY, weeks, GS_OOS_START)
    frame = pd.concat([y.rename("y"), mean_only.rename("mean"), small.rename("small"), big.rename("big")], axis=1).dropna()
    frame = frame[frame.index >= HOLD_START]
    sse = {c: float(((frame["y"] - frame[c]) ** 2).sum()) for c in ("mean", "small", "big")}
    zero = float((frame["y"] ** 2).sum())
    adjusted = (frame["y"] - frame["small"]) ** 2 - ((frame["y"] - frame["big"]) ** 2 - (frame["small"] - frame["big"]) ** 2)
    if adjusted.std() > 0:
        mean_loss = adjusted.mean()
        h = (adjusted - mean_loss).values
        lag = nw_lag(weeks)
        meat = float((h * h).sum())
        for step in range(1, min(lag, len(h) - 1) + 1):
            meat += 2.0 * (1.0 - step / (lag + 1.0)) * float((h[step:] * h[:-step]).sum())
        se = math.sqrt(max(meat, 0.0)) / len(h)
        cw_t = float(mean_loss / se) if se > 0 else float("nan")
        cw_p = float(sps.t.sf(cw_t, max(int(len(h) // weeks) - 1, 1)))
    else:
        cw_t, cw_p = float("nan"), float("nan")
    return {"n": int(len(frame)), "n_eff": round(len(frame) / weeks, 1), "oos_r2_big_vs_small": 1.0 - sse["big"] / sse["small"],
            "oos_r2_big_vs_mean": 1.0 - sse["big"] / sse["mean"], "oos_r2_small_vs_mean": 1.0 - sse["small"] / sse["mean"],
            "oos_r2_big_vs_zero": 1.0 - sse["big"] / zero, "oos_r2_small_vs_zero": 1.0 - sse["small"] / zero, "clark_west_t": cw_t,
            "clark_west_p_one_sided": cw_p}


def t3():
    out = {}
    y = AHEAD[("mon", 26)]
    bench = BENCH["mon"].rename("past26")
    ids = {"am_TYUS": "T3.1", "lev": "T3.2", "spec": "T3.3"}
    for name in THREE:
        item = I5["groups"][name]
        table = item["table"]
        score = table["score"]
        slope, scale = float(table["slope"].iloc[0]), float(table["scale"].iloc[0])
        positioning = (-slope * item["filtered"].rolling(26).sum() / scale).rename("positioning_term")
        row = {"corr_score_with_past26": {}, "joint": {}, "joint_lag_26": {}, "positioning_term_joint": {}}
        for period in PERIODS:
            keep = mask_for(period)
            controls = pd.DataFrame({"past26": bench[keep]})
            row["joint"][period] = ts_test(y[keep], score[keep], 26, controls=controls)
            row["joint_lag_26"][period] = ts_test(y[keep], score[keep], 26, controls=controls, lag=26)
            row["positioning_term_joint"][period] = ts_test(y[keep], positioning[keep], 26, controls=controls)
            frame = pd.concat([score[keep], bench[keep]], axis=1).dropna()
            row["corr_score_with_past26"][period] = float(frame.iloc[:, 0].corr(frame.iloc[:, 1]))
            design = pd.concat([y[keep].rename("y"), score[keep].rename("x"), bench[keep]], axis=1).dropna()
            lags = newey_west_ols(design["y"], design[["x", "past26"]], nw_lag(26))
            row["joint"][period]["past26_beta"] = float(lags.loc["past26", "beta"])
            row["joint"][period]["past26_t"] = float(lags.loc["past26", "t"])
        row["oos"] = oos_compare(y, pd.DataFrame({"past26": bench}), pd.DataFrame({"past26": bench, "score": score}), 26)
        out[name] = row
        hold, gs = row["joint"]["HOLDOUT"], row["joint"]["GS-OOS"]
        interval_clear = hold.get("ci_boot") is not None and (hold["ci_boot"][1] < 0)
        reg(ids[name], "primary", f"I5 {name} adds to benchmark, 26w", hold, sign_ok=hold.get("beta", 0) < 0,
            extra_ok=bool(interval_clear and row["oos"]["oos_r2_big_vs_small"] > 0), stat=hold.get("beta"), design=gs.get("beta"),
            note=f"oos_r2_incremental={row['oos']['oos_r2_big_vs_small']:.3f}")
    R["T3"] = out


# ---------------------------------------------------------------------------
# T4: stability
# ---------------------------------------------------------------------------


def param_paths(f, dy, window=None, start=lib.FIT_START):
    """Alpha, beta and residual SD at each date, from rows up to and including that date."""
    frame = pd.DataFrame({"x": f, "y": dy}).dropna()
    frame = frame[frame.index >= pd.Timestamp(start)]
    if window:
        roll = frame.rolling(window, min_periods=window)
        n = roll["x"].count()
        sx, sy = roll["x"].sum(), roll["y"].sum()
        sxx = (frame["x"] ** 2).rolling(window, min_periods=window).sum()
        sxy = (frame["x"] * frame["y"]).rolling(window, min_periods=window).sum()
        syy = (frame["y"] ** 2).rolling(window, min_periods=window).sum()
    else:
        n = pd.Series(np.arange(1, len(frame) + 1), index=frame.index, dtype=float)
        sx, sy = frame["x"].cumsum(), frame["y"].cumsum()
        sxx, sxy, syy = (frame["x"] ** 2).cumsum(), (frame["x"] * frame["y"]).cumsum(), (frame["y"] ** 2).cumsum()
    beta = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    alpha = (sy - beta * sx) / n
    rss = syy - alpha * sy - beta * sxy
    sd = np.sqrt(rss / (n - 1))
    return pd.DataFrame({"alpha": alpha, "beta": beta, "sd": sd}).reindex(f.index)


def score_variants(group):
    item = I5["groups"][group]
    f, table = item["filtered"], item["table"]
    d26 = DY.rolling(26).sum()
    f26 = f.rolling(26).sum()
    fixed_scale = float(table["scale"].iloc[0])
    alpha0, beta0 = float(table["intercept"].iloc[0]), float(table["slope"].iloc[0])
    exp, rol = param_paths(f, DY), param_paths(f, DY, window=260)
    return pd.DataFrame({
        "fixed": table["score"],
        "expanding_beta_fixed_scale": (d26 - 26 * exp["alpha"] - exp["beta"] * f26) / fixed_scale,
        "expanding_beta_expanding_scale": (d26 - 26 * exp["alpha"] - exp["beta"] * f26) / (exp["sd"] * math.sqrt(26)),
        "rolling_beta_rolling_scale": (d26 - 26 * rol["alpha"] - rol["beta"] * f26) / (rol["sd"] * math.sqrt(26)),
        "fixed_beta_expanding_scale": (d26 - 26 * alpha0 - beta0 * f26) / (exp["sd"] * math.sqrt(26)),
    }), exp, rol


def t4():
    out = {"variants": {}, "beta_by_period": {}, "paths": {}}
    y = AHEAD[("mon", 26)]
    keep = mask_for("HOLDOUT")
    spans = {"2006-2010": ("2006-06-13", "2010-12-31"), "2011-2015": ("2011-01-01", "2015-12-31"), "2016-Apr2019": ("2016-01-01", "2019-04-30"),
             "May2019-2022": ("2019-05-01", "2022-12-31"), "2023-end": ("2023-01-01", "2026-12-31")}
    for name in THREE:
        variants, exp, rol = score_variants(name)
        block = {}
        for column in variants:
            block[column] = {period: {"test": ts_test(y[mask_for(period)], variants[column][mask_for(period)], 26),
                                      "hits": hit_stats(rule_of(variants[column])[mask_for(period)], y[mask_for(period)])}
                             for period in ("GS-OOS", "HOLDOUT", "H-A", "H-B")}
        out["variants"][name] = block
        pairs = {}
        for spot, column in enumerate(("expanding_beta_expanding_scale", "rolling_beta_rolling_scale"), start=1):
            res = paired_corr_test(variants[column][keep], variants["fixed"][keep], y[keep], 26)
            pairs[column] = res
            test_id = f"T4.{spot}" if name == "am_TYUS" else f"T4.S.{name}.{column}"
            reg(test_id, "primary" if name == "am_TYUS" else "secondary", f"{column} minus fixed, {name}, 26w, corr difference", res,
                sign_ok=res.get("diff", 0) < 0, stat=res.get("diff"))
        out.setdefault("paired", {})[name] = pairs
        betas = {}
        for span, (first, last) in spans.items():
            part = (INDEX >= pd.Timestamp(first)) & (INDEX <= pd.Timestamp(last))
            betas[span] = ts_test(DY[part], I5["groups"][name]["filtered"][part], 1, lag=4)
        out["beta_by_period"][name] = betas
        # Post-hoc diagnostic, no p-value: what does each score measure? It is compared with the plain past yield change.
        out.setdefault("corr_with_past26", {})[name] = {column: {period: float(pd.concat([variants[column][mask_for(period)], BENCH["mon"][mask_for(period)]], axis=1).dropna().corr().iloc[0, 1])
                                                                  for period in ("GS-OOS", "HOLDOUT")} for column in variants}
        out["paths"][name] = {"expanding_beta_last": float(exp["beta"].iloc[-1]), "rolling_beta_min": float(rol["beta"].min()),
                              "rolling_beta_max": float(rol["beta"].max()), "fixed_beta": float(I5["groups"][name]["table"]["slope"].iloc[0]),
                              "fixed_alpha": float(I5["groups"][name]["table"]["intercept"].iloc[0]),
                              "score_mean_holdout": float(variants["fixed"][keep].mean()), "share_holdout_above_025": float((variants["fixed"][keep] > 0.25).mean()),
                              "share_holdout_below_m025": float((variants["fixed"][keep] < -0.25).mean())}
    R["T4"] = out


# ---------------------------------------------------------------------------
# Panel helpers
# ---------------------------------------------------------------------------


def panel_period(market, period, weeks):
    frame = PANEL[PANEL["market"] == market]
    dates = frame["date"]
    if period == "DESIGN":
        return frame[(dates <= DESIGN_END) & (frame["entry"] + pd.Timedelta(days=7 * weeks) <= DESIGN_END)]
    if period == "GS-OOS":
        return frame[(dates >= pd.Timestamp(GS_OOS_START)) & (dates <= DESIGN_END) & (frame["entry"] + pd.Timedelta(days=7 * weeks) <= DESIGN_END)]
    if period == "HOLDOUT":
        return frame[dates >= HOLD_START]
    if period == "H-A":
        return frame[(dates >= HOLD_START) & (dates <= HALF_A_END)]
    if period == "H-B":
        return frame[dates >= HALF_B_START]
    raise ValueError(period)


def panel_all(market, x_col, weeks, controls=None, frame_fn=None):
    """One signal on one panel across the design sample, holdout and holdout halves."""
    out = {}
    for period in ("DESIGN", "HOLDOUT", "H-A", "H-B"):
        frame = panel_period(market, period, weeks)
        if frame_fn is not None:
            frame = frame_fn(frame)
        out[period] = panel_test(frame, f"y{weeks}", x_col, weeks, controls=controls)
    return out


def sign_of(value):
    if value is None or not np.isfinite(value):
        return 0.0
    return float(np.sign(value))


def same_sign(block):
    return sign_of(block["HOLDOUT"].get("beta")) == sign_of(block["DESIGN"].get("beta")) != 0


# ---------------------------------------------------------------------------
# T6: pain
# ---------------------------------------------------------------------------


def t6():
    out = {"net_share": {}, "with_past_return": {}, "deck_rule_hits": {}, "missing": {}}
    spot = 1
    for market in ("UST", "FX"):
        for group in ("lev", "am", "spec"):
            col = f"net_share_{group}_w126_pro_rata"
            for k in (4, 13, 26):
                block = panel_all(market, col, k)
                out["net_share"][f"{market}_{group}_{k}w"] = block
                if k == 13:
                    reg(f"T6.{spot}", "primary", f"P2 net share, {group}, {market}, 13w", block["HOLDOUT"], sign_ok=same_sign(block),
                        stat=block["HOLDOUT"].get("beta"), design=block["DESIGN"].get("beta"))
                    spot += 1
                else:
                    reg(f"T6.S.{market}.{group}.{k}", "secondary", f"P2 net share, {group}, {market}, {k}w", block["HOLDOUT"], sign_ok=same_sign(block),
                        stat=block["HOLDOUT"].get("beta"), design=block["DESIGN"].get("beta"))
            block = panel_all(market, col, 13, controls=["past26"])
            out["with_past_return"][f"{market}_{group}_13w"] = block
            hold = panel_period(market, "HOLDOUT", 13)
            out.setdefault("corr_with_past26", {})[f"{market}_{group}"] = float(hold[[col, "past26"]].dropna().corr().iloc[0, 1])
            if group == "lev":
                test_id = "T6.7" if market == "UST" else "T6.8"
                reg(test_id, "primary", f"P2 lev given past return, {market}, 13w", block["HOLDOUT"], sign_ok=same_sign(block),
                    stat=block["HOLDOUT"].get("beta"), design=block["DESIGN"].get("beta"))
            else:
                reg(f"T6.S.past.{market}.{group}", "secondary", f"P2 {group} given past return, {market}, 13w", block["HOLDOUT"], sign_ok=same_sign(block),
                    stat=block["HOLDOUT"].get("beta"), design=block["DESIGN"].get("beta"))
            long_col = f"share_{group}_long_w126_pro_rata"
            for period in ("DESIGN", "HOLDOUT"):
                frame = panel_period(market, period, 13)
                # Deck rule: sell above 70 percent of longs in pain. Buy below 30 percent.
                out["deck_rule_hits"][f"{market}_{group}_{period}"] = panel_hits(frame, "y13", frame[long_col] < 0.30, frame[long_col] > 0.70)
            usable = panel_period(market, "HOLDOUT", 13)
            out["missing"][f"{market}_{group}"] = {"rows": int(len(usable)), "with_reading": int(usable[col].notna().sum())}
    R["T6"] = out


def t6b():
    """Is the synthetic price an improvement over an unadjusted front-month series?"""
    out = {"ty_real_closes": {}, "yahoo": {}}
    real = pd.read_csv(RAW / "project_ty_daily.csv", parse_dates=["date"], index_col="date")["close"].dropna()
    synth = lib.synthetic_price("TY")
    frame = pd.concat([real.diff().rename("real"), synth.diff().rename("synth")], axis=1).dropna()
    out["ty_real_closes"] = {"days": int(len(frame)), "first": str(frame.index[0])[:10], "last": str(frame.index[-1])[:10],
                             "corr_daily_change": float(frame["real"].corr(frame["synth"])),
                             "tracking_sd_points": float((frame["real"] - frame["synth"]).std()),
                             "real_sd_points": float(frame["real"].std()),
                             "slope_real_on_synth": float(np.polyfit(frame["synth"], frame["real"], 1)[0])}
    panel_rows = []
    for symbol in ("TU", "FV", "TY", "US"):
        path = RAW / f"yahoo_{symbol}.csv"
        if not path.exists():
            out["yahoo"][symbol] = {"status": "not_run", "reason": "download missing"}
            continue
        yahoo = pd.read_csv(path, parse_dates=["date"], index_col="date")["close"].dropna().sort_index()
        synth = lib.synthetic_price(symbol)
        joined = pd.concat([yahoo.rename("yahoo"), synth.rename("synth")], axis=1).dropna()
        daily = joined.diff().dropna()
        # The largest gaps between the two daily changes mark rolls and bad prints in the unadjusted series.
        gap = (daily["yahoo"] - daily["synth"]).abs()
        position_long = lib.cftc("tff", "futures", symbol)["lev_money_long"].dropna()
        position_short = lib.cftc("tff", "futures", symbol)["lev_money_short"].dropna()
        asof = lib.entry_dates(position_long.index, yahoo.index)
        sigma = yahoo.diff().rolling(126, min_periods=63).std()
        share_long = pain_rows(position_long, yahoo, asof, 126, RemovalRule.PRO_RATA, "long", sigma)["share"]
        share_short = pain_rows(position_short, yahoo, asof, 126, RemovalRule.PRO_RATA, "short", sigma)["share"]
        rows = PANEL[PANEL["contract"] == symbol].set_index("date")
        rows = rows[["contract", "entry", "y13", "net_share_lev_w126_pro_rata", "market"]].copy()
        rows["yahoo_net_share"] = (share_long - share_short).reindex(rows.index)
        rows["date"] = rows.index
        panel_rows.append(rows.reset_index(drop=True))
        out["yahoo"][symbol] = {"days": int(len(daily)), "corr_daily_change": float(daily["yahoo"].corr(daily["synth"])),
                                "tracking_sd_points": float((daily["yahoo"] - daily["synth"]).std()),
                                "days_gap_above_0p3_points": int((gap > 0.3).sum()),
                                "signal_corr_with_synthetic": float(rows[["net_share_lev_w126_pro_rata", "yahoo_net_share"]].dropna().corr().iloc[0, 1])}
    if panel_rows:
        both = pd.concat(panel_rows, ignore_index=True)
        out["slope_compare"] = {}
        for period, cut in (("DESIGN", (both["date"] <= DESIGN_END) & (both["entry"] + pd.Timedelta(days=91) <= DESIGN_END)), ("HOLDOUT", both["date"] >= HOLD_START)):
            frame = both[cut].dropna(subset=["net_share_lev_w126_pro_rata", "yahoo_net_share", "y13"])
            out["slope_compare"][period] = {"synthetic": panel_test(frame, "y13", "net_share_lev_w126_pro_rata", 13),
                                            "yahoo": panel_test(frame, "y13", "yahoo_net_share", 13),
                                            "abs_diff": panel_paired(frame, "y13", "net_share_lev_w126_pro_rata", "yahoo_net_share", 13)}
        design = out["slope_compare"]["DESIGN"]
        out["verdict_rule"] = {"corr_at_least_0p9": out["ty_real_closes"]["corr_daily_change"] >= 0.9,
                               "design_t_synthetic": design["synthetic"].get("t_dk"), "design_t_yahoo": design["yahoo"].get("t_dk"),
                               "synthetic_at_least_as_strong": abs(design["synthetic"].get("t_dk", 0)) >= abs(design["yahoo"].get("t_dk", 0))}
        reg("T6b.S.1", "secondary", "P2 lev on synthetic minus P2 lev on Yahoo, TU FV TY US, 13w", out["slope_compare"]["HOLDOUT"]["abs_diff"],
            stat=out["slope_compare"]["HOLDOUT"]["abs_diff"].get("diff"))
    R["T6b"] = out


# ---------------------------------------------------------------------------
# T7: pain improvements
# ---------------------------------------------------------------------------


def add_crowded():
    for group, si in (("spec", "I2"), ("lev", "I2_lev")):
        long_s, short_s = PANEL[f"share_{group}_long_w126_pro_rata"], PANEL[f"share_{group}_short_w126_pro_rata"]
        value = np.where((PANEL[si] >= 90) & (long_s >= 0.5), -1.0, np.where((PANEL[si] <= 10) & (short_s >= 0.5), 1.0, 0.0))
        PANEL[f"crowd_pain_{group}"] = pd.Series(value, index=PANEL.index).where(PANEL[si].notna())
        crowd = np.where(PANEL[si] >= 90, -1.0, np.where(PANEL[si] <= 10, 1.0, 0.0))
        PANEL[f"crowd_only_{group}"] = pd.Series(crowd, index=PANEL.index).where(PANEL[si].notna())


def t7():
    out = {"depth": {}, "crowded": {}, "windows": {}, "rules": {}}
    add_crowded()
    # Depth against share.
    for spot, market in enumerate(("UST", "FX"), start=1):
        for group in ("lev", "am", "spec"):
            share, depth = f"net_share_{group}_w126_pro_rata", f"net_depth_{group}_w126_pro_rata"
            design_share = panel_test(panel_period(market, "DESIGN", 13), "y13", share, 13)
            design_depth = panel_test(panel_period(market, "DESIGN", 13), "y13", depth, 13)
            sign_share, sign_depth = sign_of(design_share.get("beta")), sign_of(design_depth.get("beta"))
            hold = panel_period(market, "HOLDOUT", 13)
            pair = panel_paired(hold, "y13", depth, share, 13, sign_a=sign_depth or 1.0, sign_b=sign_share or 1.0)
            depth_block = panel_all(market, depth, 13)
            out["depth"][f"{market}_{group}"] = {"design_share": design_share, "design_depth": design_depth, "depth": depth_block, "paired_depth_minus_share": pair,
                                                 "signal_corr_holdout": float(hold[[share, depth]].dropna().corr().iloc[0, 1])}
            test_id = f"T7.{spot}" if group == "lev" else f"T7.S.depth.{market}.{group}"
            reg(test_id, "primary" if group == "lev" else "secondary", f"Depth minus share, {group}, {market}, 13w, signed by DESIGN", pair,
                sign_ok=pair.get("diff", 0) > 0, stat=pair.get("diff"))
            reg(f"T7.S.depthslope.{market}.{group}", "secondary", f"Depth slope, {group}, {market}, 13w", depth_block["HOLDOUT"], sign_ok=same_sign(depth_block),
                stat=depth_block["HOLDOUT"].get("beta"), design=depth_block["DESIGN"].get("beta"))
    # Pain crossed with crowding.
    for spot, market in enumerate(("UST", "FX"), start=3):
        for group in ("spec", "lev"):
            for kind in ("crowd_pain", "crowd_only"):
                col = f"{kind}_{group}"
                block = panel_all(market, col, 13)
                frame = panel_period(market, "HOLDOUT", 13)
                events = {"plus": int((frame[col] == 1).sum()), "minus": int((frame[col] == -1).sum())}
                hits = panel_hits(frame, "y13", frame[col] == 1, frame[col] == -1)
                out["crowded"][f"{market}_{group}_{kind}"] = {"block": block, "holdout_events": events, "holdout_hits": hits}
                if group == "spec" and kind == "crowd_pain":
                    enough = events["plus"] >= 30 and events["minus"] >= 30
                    reg(f"T7.{spot}", "primary", f"Crowded pain, spec, {market}, 13w", block["HOLDOUT"], sign_ok=same_sign(block), extra_ok=enough,
                        stat=block["HOLDOUT"].get("beta"), design=block["DESIGN"].get("beta"), note=f"events plus {events['plus']}, minus {events['minus']}")
                else:
                    reg(f"T7.S.{kind}.{market}.{group}", "secondary", f"{kind}, {group}, {market}, 13w", block["HOLDOUT"], sign_ok=same_sign(block),
                        stat=block["HOLDOUT"].get("beta"), design=block["DESIGN"].get("beta"))
    # Window length, chosen on DESIGN.
    for spot, market in enumerate(("UST", "FX"), start=5):
        for group in ("lev", "am", "spec"):
            block = {}
            for window in (30, 63, 90, 126, 252):
                block[str(window)] = panel_all(market, f"net_share_{group}_w{window}_pro_rata", 13)
            chosen = max(block, key=lambda w: abs(block[w]["DESIGN"].get("t_dk", 0) or 0))
            out["windows"][f"{market}_{group}"] = {"by_window": block, "design_choice": chosen}
            test_id = f"T7.{spot}" if group == "lev" else f"T7.S.window.{market}.{group}"
            reg(test_id, "primary" if group == "lev" else "secondary", f"Design-chosen window ({chosen}), {group}, {market}, 13w", block[chosen]["HOLDOUT"],
                sign_ok=same_sign(block[chosen]), stat=block[chosen]["HOLDOUT"].get("beta"), design=block[chosen]["DESIGN"].get("beta"), note=f"window {chosen}")
    # Removal rule sensitivity.
    for market in ("UST", "FX"):
        for group in ("lev", "am", "spec"):
            cols = {rule: f"net_share_{group}_w126_{rule}" for rule in ("pro_rata", "fifo", "low_price_first")}
            hold = panel_period(market, "HOLDOUT", 13)
            corr = hold[list(cols.values())].dropna().corr()
            tests = {rule: panel_all(market, col, 13) for rule, col in cols.items()}
            diffs = {}
            for rule in ("fifo", "low_price_first"):
                diffs[rule] = panel_paired(hold, "y13", cols["pro_rata"], cols[rule], 13)
                reg(f"T7.S.rule.{market}.{group}.{rule}", "secondary", f"pro_rata minus {rule} slope, {group}, {market}, 13w", diffs[rule], stat=diffs[rule].get("diff"))
            signs = {sign_of(tests[rule]["HOLDOUT"].get("beta")) for rule in cols}
            # The pooled correlation mixes contracts, so report the within-contract figure too.
            within = hold[list(cols.values()) + ["contract"]].dropna()
            within_corr = (within[list(cols.values())] - within.groupby("contract")[list(cols.values())].transform("mean")).corr()
            insensitive = (min(corr.iloc[0, 1], corr.iloc[0, 2], corr.iloc[1, 2]) >= 0.8 and len(signs) == 1
                           and all(abs(diffs[r].get("diff", 0)) < diffs[r].get("se_boot", 0) for r in diffs))
            out["rules"][f"{market}_{group}"] = {"corr": {"pro_rata_fifo": float(corr.iloc[0, 1]), "pro_rata_low": float(corr.iloc[0, 2]), "fifo_low": float(corr.iloc[1, 2])},
                                                 "within_corr": {"pro_rata_fifo": float(within_corr.iloc[0, 1]), "pro_rata_low": float(within_corr.iloc[0, 2]), "fifo_low": float(within_corr.iloc[1, 2])},
                                                 "mean_abs_gap": {r: float((hold[cols["pro_rata"]] - hold[cols[r]]).abs().mean()) for r in ("fifo", "low_price_first")},
                                                 "tests": tests, "paired": diffs, "insensitive_by_plan_rule": bool(insensitive)}
    R["T7"] = out


# ---------------------------------------------------------------------------
# T8: indicators head to head
# ---------------------------------------------------------------------------

INDICATORS = ("I1", "I2", "I3_lev", "I3_am", "I4")


def t8():
    out = {"panel": {}, "aggregate_i4": {}, "hits": {}}
    spot = 1
    for market in ("UST", "FX"):
        for k in lib.HORIZONS:
            common = lambda f, k=k: f.dropna(subset=list(INDICATORS) + [f"y{k}"])  # noqa: E731
            blocks = {name: panel_all(market, name, k, frame_fn=common) for name in INDICATORS}
            out["panel"][f"{market}_{k}w"] = blocks
            for name in INDICATORS:
                block = blocks[name]
                if k == 13:
                    reg(f"T8.{spot}", "primary", f"{name}, {market}, 13w, common sample", block["HOLDOUT"], sign_ok=same_sign(block),
                        stat=block["HOLDOUT"].get("beta"), design=block["DESIGN"].get("beta"))
                    spot += 1
                else:
                    reg(f"T8.S.{market}.{name}.{k}", "secondary", f"{name}, {market}, {k}w, common sample", block["HOLDOUT"], sign_ok=same_sign(block),
                        stat=block["HOLDOUT"].get("beta"), design=block["DESIGN"].get("beta"))
        hold = panel_period(market, "HOLDOUT", 13)
        common_rows = hold.dropna(subset=list(INDICATORS))
        within = common_rows[list(INDICATORS)] - common_rows.groupby("contract")[list(INDICATORS)].transform("mean")
        out.setdefault("signal_corr_within_holdout", {})[market] = within.corr().round(3).to_dict()
        out["hits"][f"{market}_I2_extremes"] = panel_hits(hold, "y13", hold["I2"] <= 10, hold["I2"] >= 90)
        design = panel_period(market, "DESIGN", 13)
        out["hits"][f"{market}_I2_extremes_design"] = panel_hits(design, "y13", design["I2"] <= 10, design["I2"] >= 90)
        out["hits"][f"{market}_I4_rule"] = panel_hits(hold, "y13", hold["I4"] <= -1, hold["I4"] >= 1)
        out["hits"][f"{market}_I4_rule_design"] = panel_hits(design, "y13", design["I4"] <= -1, design["I4"] >= 1)
    # The spec-style aggregate I4 on the 10-year, 4-week horizon.
    legacy = {k: lib.cftc("legacy", "futures", k) for k in UST}
    nets = {k: (t.noncomm_long - t.noncomm_short).reindex(INDEX) for k, t in legacy.items()}
    dv01 = {k: v.reindex(INDEX, method="ffill") for k, v in I5["dv01"].items()}
    position = dv01_weighted_net(nets, dv01)
    z = (position - position.expanding(104).mean()) / position.expanding(104).std()
    y = AHEAD[("mon", 4)]
    rule = pd.Series(np.where(z <= -1, 1.0, np.where(z >= 1, -1.0, 0.0)), index=z.index).where(z.notna())
    for period in ("GS-OOS", "HOLDOUT"):
        keep = mask_for(period, "mon", 4)
        out["aggregate_i4"][period] = {"test": ts_test(y[keep], z[keep], 4), "hits": hit_stats(rule[keep], y[keep])}
    out["aggregate_i4_position_range"] = {"z_median_design": float(z[INDEX <= DESIGN_END].median()), "z_median_holdout": float(z[INDEX >= HOLD_START].median()),
                                          "z_min_holdout": float(z[INDEX >= HOLD_START].min()), "z_max_holdout": float(z[INDEX >= HOLD_START].max())}
    # The I4 recipe as the spec text stood at the end of this run: TY, combined report, frozen 2007-2018 scale.
    combined = lib.cftc("legacy", "combined", "TY")
    money = ((combined.noncomm_long - combined.noncomm_short).reindex(INDEX) * dv01["TY"] / 1e6).dropna()
    frozen = money.loc["2007-01-01":"2018-06-30"]
    spec_z = ((money - frozen.mean()) / frozen.std()).reindex(INDEX)
    spec_rule = pd.Series(np.where(spec_z <= -1, 1.0, np.where(spec_z >= 1, -1.0, 0.0)), index=INDEX).where(spec_z.notna())
    out["spec_i4"] = {period: {"test": ts_test(y[mask_for(period, "mon", 4)], spec_z[mask_for(period, "mon", 4)], 4), "hits": hit_stats(spec_rule[mask_for(period, "mon", 4)], y[mask_for(period, "mon", 4)])}
                      for period in ("GS-OOS", "HOLDOUT", "H-A", "H-B")}
    reg("T8.S.specI4", "secondary", "I4 as now in the spec (TY, combined, frozen 2007-2018 scale), 4w", out["spec_i4"]["HOLDOUT"]["test"], stat=out["spec_i4"]["HOLDOUT"]["test"].get("corr"),
        design=out["spec_i4"]["GS-OOS"]["test"].get("corr"), note="GS-OOS sits inside the frozen scale window")
    hold = out["aggregate_i4"]["HOLDOUT"]["test"]
    reg("T8.S.aggI4", "secondary", "Aggregate I4 z-score on 10-year, 4w", hold, stat=hold.get("corr"), design=out["aggregate_i4"]["GS-OOS"]["test"].get("corr"))
    R["T8"] = out


# ---------------------------------------------------------------------------
# T9: FX filter
# ---------------------------------------------------------------------------


def t9():
    out = {"panel": {}, "given_past": {}, "by_currency": {}, "rule_hits": {}, "fit": {}}
    for spot, group in enumerate(("am", "lev", "spec"), start=1):
        col = f"i5fx_{group}"
        for k in (13, 26):
            block = {period: panel_test(panel_period("FX", period, k), f"y{k}", col, k) for period in ("GS-OOS", "HOLDOUT", "H-A", "H-B")}
            out["panel"][f"{group}_{k}w"] = block
            ok = block["HOLDOUT"].get("beta", 0) > 0
            if k == 26:
                reg(f"T9.{spot}", "primary", f"FX I5, {group}, 26w, fit FIT", block["HOLDOUT"], sign_ok=ok, stat=block["HOLDOUT"].get("beta"), design=block["GS-OOS"].get("beta"))
            else:
                reg(f"T9.S.{group}.{k}", "secondary", f"FX I5, {group}, {k}w", block["HOLDOUT"], sign_ok=ok, stat=block["HOLDOUT"].get("beta"), design=block["GS-OOS"].get("beta"))
        control = {period: panel_test(panel_period("FX", period, 26), "y26", col, 26, controls=["past26"]) for period in ("GS-OOS", "HOLDOUT")}
        out["given_past"][group] = control
        reg(f"T9.S.past.{group}", "secondary", f"FX I5 {group} given past return, 26w", control["HOLDOUT"], sign_ok=control["HOLDOUT"].get("beta", 0) > 0,
            stat=control["HOLDOUT"].get("beta"), design=control["GS-OOS"].get("beta"))
        hold, gs = panel_period("FX", "HOLDOUT", 26), panel_period("FX", "GS-OOS", 26)
        out["rule_hits"][group] = {"HOLDOUT": panel_hits(hold, "y26", hold[col] > 0.25, hold[col] < -0.25), "GS-OOS": panel_hits(gs, "y26", gs[col] > 0.25, gs[col] < -0.25)}
        out["fit"][group] = {sym: float(PANEL[PANEL["contract"] == sym][f"{col}_slope"].dropna().iloc[0]) for sym in FX}
        for symbol in FX:
            part = panel_period("FX", "HOLDOUT", 26)
            part = part[part["contract"] == symbol].set_index("date")
            res = ts_test(part["y26"], part[col], 26)
            out["by_currency"][f"{group}_{symbol}"] = res
            reg(f"T9.S.ccy.{group}.{symbol}", "secondary", f"FX I5 {group}, {symbol} alone, 26w", res, sign_ok=res.get("beta", 0) > 0, stat=res.get("beta"))
    hold = panel_period("FX", "HOLDOUT", 26)
    bench = panel_all("FX", "past26", 26)
    out["benchmark_past26"] = bench
    reg("T9.S.bench", "secondary", "FX past 26w return as a predictor, 26w", bench["HOLDOUT"], stat=bench["HOLDOUT"].get("beta"), design=bench["DESIGN"].get("beta"))
    bench_ust = panel_all("UST", "past26", 26)
    out["benchmark_past26_ust_panel"] = bench_ust
    R["T9"] = out
    _ = hold


# ---------------------------------------------------------------------------
# T10: option position from combined minus futures
# ---------------------------------------------------------------------------


def t10():
    out = {"flow": {}, "level": {}, "given_futures": {}}
    spot = 1
    for market in ("UST", "FX"):
        for group in ("am", "lev", "spec"):
            col = f"opt_flow_{group}"
            for k in (4, 13):
                block = panel_all(market, col, k)
                out["flow"][f"{market}_{group}_{k}w"] = block
                if k == 4:
                    reg(f"T10.{spot}", "primary", f"Option flow, {group}, {market}, 4w", block["HOLDOUT"], sign_ok=same_sign(block), stat=block["HOLDOUT"].get("beta"), design=block["DESIGN"].get("beta"))
                    spot += 1
                else:
                    reg(f"T10.S.flow.{market}.{group}.13", "secondary", f"Option flow, {group}, {market}, 13w", block["HOLDOUT"], sign_ok=same_sign(block), stat=block["HOLDOUT"].get("beta"), design=block["DESIGN"].get("beta"))
            level = panel_all(market, f"opt_level_{group}", 4)
            out["level"][f"{market}_{group}_4w"] = level
            reg(f"T10.S.level.{market}.{group}", "secondary", f"Option level z, {group}, {market}, 4w", level["HOLDOUT"], sign_ok=same_sign(level), stat=level["HOLDOUT"].get("beta"), design=level["DESIGN"].get("beta"))
            given = panel_all(market, col, 4, controls=[f"fut_net_oi_{group}"])
            out["given_futures"][f"{market}_{group}_4w"] = given
            reg(f"T10.S.given.{market}.{group}", "secondary", f"Option flow given futures position, {group}, {market}, 4w", given["HOLDOUT"], sign_ok=same_sign(given), stat=given["HOLDOUT"].get("beta"), design=given["DESIGN"].get("beta"))
    R["T10"] = out


# ---------------------------------------------------------------------------
# T12, T13, T14: filter placebo, filter value, benchmark bias
# ---------------------------------------------------------------------------


def placebo_group(name):
    item = I5["groups"][name]
    nets = item["nets"]
    contracts = list(nets)
    weeks = len(INDEX)
    change = np.column_stack([nets[c].diff().values for c in contracts])
    change = np.nan_to_num(change, nan=0.0)
    yields = I5["yields"]
    move = np.column_stack([yields[c].reindex(INDEX, method="ffill").diff().values for c in contracts])
    weight = np.column_stack([I5["dv01"][c].reindex(INDEX, method="ffill").values for c in contracts]) / 1e6
    dy = DY.values
    fit = FIT_MASK & ~np.isnan(dy)
    forward = {"HOLDOUT": mask_for("HOLDOUT").values, "GS-OOS": mask_for("GS-OOS").values}
    y26 = AHEAD[("mon", 26)].values
    d26 = pd.Series(dy).rolling(26).sum().values
    through = INDEX <= DESIGN_END

    def one(shift, return_score=False):
        rolled = np.roll(change, shift, axis=0)
        kept = np.where(np.sign(rolled) == -np.sign(move), rolled * weight, 0.0)
        kept = np.nan_to_num(kept, nan=0.0)
        f = kept.sum(axis=1)
        slope, intercept = np.polyfit(f[fit], dy[fit], 1)
        residual = dy - (intercept + slope * f)
        scale = np.nanstd(residual[fit], ddof=1) * math.sqrt(26)
        score = pd.Series(residual).rolling(26).sum().values / scale
        if return_score:
            return score
        f26 = pd.Series(f).rolling(26).sum().values
        out = {"beta": float(slope)}
        valid = ~np.isnan(f26) & ~np.isnan(d26) & through
        out["corr_F26_D26_design"] = float(np.corrcoef(f26[valid], d26[valid])[0, 1])
        for period, mask in forward.items():
            use = mask & ~np.isnan(score) & ~np.isnan(y26)
            out[f"corr_{period}"] = float(np.corrcoef(score[use], y26[use])[0, 1])
        return out

    real = one(0)
    # At zero shift this path must rebuild posmon's score exactly, or the placebo is not comparing like with like.
    rebuilt = one(0, return_score=True)
    gap = float(np.nanmax(np.abs(rebuilt - item["table"]["score"].values)))
    if gap > 1e-8:
        raise AssertionError(f"placebo path differs from posmon by {gap}")
    shifts = range(52, weeks - 52)
    rows = pd.DataFrame([one(s) for s in shifts])
    result = {"real": real, "placebo_count": int(len(rows)), "placebo_mean": rows.mean().to_dict(), "placebo_sd": rows.std().to_dict(),
              "placebo_q05": rows.quantile(0.05).to_dict(), "placebo_q95": rows.quantile(0.95).to_dict()}
    for period in forward:
        low = (np.sum(rows[f"corr_{period}"] <= real[f"corr_{period}"]) + 1.0) / (len(rows) + 1.0)
        result[f"p_real_more_negative_{period}"] = float(low)
        result[f"p_two_sided_{period}"] = float(min(1.0, 2.0 * min(low, 1.0 - low + 1.0 / (len(rows) + 1.0))))
    result["share_placebo_F26_at_least_as_negative"] = float((rows["corr_F26_D26_design"] <= real["corr_F26_D26_design"]).mean())
    return result


def t12():
    out = {name: placebo_group(name) for name in THREE}
    R["T12"] = out
    for spot, name in enumerate(THREE, start=1):
        res = out[name]
        wrapped = {"p_primary": res["p_two_sided_HOLDOUT"], "n": int(mask_for("HOLDOUT").sum())}
        reg(f"T12.{spot}", "primary", f"Filter placebo, {name}: real flows vs shifted flows, 26w corr", wrapped, sign_ok=res["real"]["corr_HOLDOUT"] < res["placebo_mean"]["corr_HOLDOUT"],
            stat=res["real"]["corr_HOLDOUT"] - res["placebo_mean"]["corr_HOLDOUT"], design=res["real"]["corr_GS-OOS"] - res["placebo_mean"]["corr_GS-OOS"])


def t13():
    keep = mask_for("HOLDOUT")
    y = AHEAD[("mon", 26)]
    out = {}
    for name in THREE:
        filtered = I5["groups"][name]["table"]["score"]
        plain = I5["groups"][name]["plain_table"]["score"]
        res = paired_corr_test(filtered[keep], plain[keep], y[keep], 26)
        gs_keep = mask_for("GS-OOS")
        gs = paired_corr_test(filtered[gs_keep], plain[gs_keep], y[gs_keep], 26)
        out[name] = {"HOLDOUT": res, "GS-OOS": gs, "plain_slope_bp_per_10mm": float(I5["groups"][name]["plain_table"]["slope"].iloc[0] * 10.0)}
        test_id = "T13.1" if name == "am_TYUS" else f"T13.S.{name}"
        reg(test_id, "primary" if name == "am_TYUS" else "secondary", f"Filter minus no filter, {name}, 26w, corr difference", res, sign_ok=res.get("diff", 0) < 0, stat=res.get("diff"), design=gs.get("diff"))
    R["T13"] = out


def benchmark_bias():
    """How often does a series with no real mean reversion show the benchmark's correlation over Goldman's sample?"""
    rng = np.random.default_rng(SEED)
    span = (INDEX >= pd.Timestamp(lib.FIT_START)) & (INDEX <= DESIGN_END)
    moves = DY[span].dropna().values
    actual = {"HOLDOUT": None}
    weeks = len(moves)
    out = {}

    def corr_path(path):
        level = np.cumsum(path)
        past = level[26:-26] - level[:-52]
        ahead = level[52:] - level[26:-26]
        return float(np.corrcoef(past, ahead)[0, 1])

    draws_iid = np.array([corr_path(rng.choice(moves, size=weeks, replace=True)) for _ in range(4000)])
    picks = block_index(weeks, 4, 4000, rng)
    draws_block = np.array([corr_path(moves[row]) for row in picks])
    observed = corr_path(moves)
    out["design"] = {"weeks": int(weeks), "observed_corr": observed, "iid_mean": float(draws_iid.mean()), "iid_sd": float(draws_iid.std()), "iid_q05": float(np.quantile(draws_iid, 0.05)),
                     "iid_share_below_observed": float((draws_iid <= observed).mean()), "block4_mean": float(draws_block.mean()), "block4_share_below_observed": float((draws_block <= observed).mean())}
    hold = DY[INDEX >= HOLD_START].dropna().values
    hold_draws = np.array([corr_path(rng.choice(hold, size=len(hold), replace=True)) for _ in range(4000)])
    observed_hold = corr_path(hold)
    out["holdout"] = {"weeks": int(len(hold)), "observed_corr": observed_hold, "iid_mean": float(hold_draws.mean()), "iid_sd": float(hold_draws.std()),
                      "iid_share_below_observed": float((hold_draws <= observed_hold).mean())}
    _ = actual
    R["T14"] = out


# ---------------------------------------------------------------------------
# T11: composite and backtests
# ---------------------------------------------------------------------------

COST = 5e-4
TARGET = 0.10 / math.sqrt(52)


def z_past(series, min_periods=52):
    mean = series.expanding(min_periods).mean()
    std = series.expanding(min_periods).std()
    return (series - mean) / std


def rates_grid():
    level = pd.Series(level_at(TEN, pd.DatetimeIndex(ENTRY.values)).values, index=INDEX)
    weekly = level.diff()
    sigma = weekly.rolling(52, min_periods=26).std()
    earn = -(level.shift(-1) - level)  # bp earned by a long held from this entry to the next
    dv = I5["dv01"]["TY"].reindex(INDEX, method="ffill") / 100000.0
    return earn, sigma, dv


def rates_returns(position, cost=COST):
    earn, sigma, dv = rates_grid()
    weight = position.fillna(0.0) * TARGET / sigma
    gross = weight * earn
    turnover = (weight / dv).diff().abs().fillna(0.0)
    return (gross - cost * turnover).where(sigma.notna() & earn.notna())


def fx_returns(positions, cost=COST):
    """positions: DataFrame of -1..1 by date and contract. Equal risk across seven currencies."""
    frame = PANEL[PANEL["market"] == "FX"]
    sigma = frame.pivot(index="date", columns="contract", values="sigma") / 100.0
    weekly = frame.pivot(index="date", columns="contract", values="weekly") / 100.0
    weight = positions.reindex_like(sigma).fillna(0.0) * TARGET / sigma
    gross = (weight * weekly).mean(axis=1)
    turnover = weight.diff().abs().mean(axis=1).fillna(0.0)
    return (gross - cost * turnover).where(sigma.notna().any(axis=1) & weekly.notna().any(axis=1))


def fx_signal_frame(col, sign, use_rule=False):
    frame = PANEL[PANEL["market"] == "FX"]
    wide = frame.pivot(index="date", columns="contract", values=col)
    if use_rule:
        return np.sign(sign) * wide.apply(lambda c: rule_of(c)).fillna(0.0)
    return (np.sign(sign) * wide.apply(lambda c: z_past(c))).clip(-1, 1).fillna(0.0)


def ty_signal(col, sign):
    frame = PANEL[PANEL["contract"] == "TY"].set_index("date")
    return (np.sign(sign) * z_past(frame[col])).clip(-1, 1).reindex(INDEX).fillna(0.0)


def screen():
    """Composite members come from DESIGN only."""
    pool = {"rates": {}, "fx": {}}
    for name in THREE:
        res = ts_test(AHEAD[("mon", 26)][mask_for("GS-OOS")], score_of(name)[mask_for("GS-OOS")], 26)
        pool["rates"][f"I5_{name}"] = {"t": res.get("t_nw"), "beta_long": -res.get("beta", 0.0), "horizon": 26}
    panel_cols = {"I1": ("I1", 13), "I2": ("I2", 13), "I3_lev": ("I3_lev", 13), "I3_am": ("I3_am", 13), "I4": ("I4", 13),
                  "P2_lev": ("net_share_lev_w126_pro_rata", 13), "P2_am": ("net_share_am_w126_pro_rata", 13), "P2_spec": ("net_share_spec_w126_pro_rata", 13),
                  "OPT_am": ("opt_flow_am", 4), "OPT_lev": ("opt_flow_lev", 4), "OPT_spec": ("opt_flow_spec", 4)}
    for label, (col, k) in panel_cols.items():
        res = panel_test(panel_period("UST", "DESIGN", k), f"y{k}", col, k)
        pool["rates"][label] = {"t": res.get("t_dk"), "beta_long": res.get("beta", 0.0), "horizon": k, "col": col}
        res = panel_test(panel_period("FX", "DESIGN", k), f"y{k}", col, k)
        pool["fx"][label] = {"t": res.get("t_dk"), "beta_long": res.get("beta", 0.0), "horizon": k, "col": col}
    for group in ("am", "lev", "spec"):
        res = panel_test(panel_period("FX", "GS-OOS", 26), "y26", f"i5fx_{group}", 26)
        pool["fx"][f"I5FX_{group}"] = {"t": res.get("t_dk"), "beta_long": res.get("beta", 0.0), "horizon": 26, "col": f"i5fx_{group}", "rule": True}
    members = {}
    for sleeve, items in pool.items():
        qualified = [k for k, v in items.items() if v["t"] is not None and np.isfinite(v["t"]) and abs(v["t"]) >= 2.0]
        qualified.sort(key=lambda k: -abs(items[k]["t"]))
        members[sleeve] = qualified[:5]
    return pool, members


def rates_position(label, info):
    if label.startswith("I5_"):
        name = label[3:]
        return np.sign(info["beta_long"]) * rule_of(score_of(name)).fillna(0.0)
    return ty_signal(info["col"], info["beta_long"])


def fx_position(label, info):
    return fx_signal_frame(info["col"], info["beta_long"], use_rule=info.get("rule", False))


def walkforward_ic_weights(positions, forward, entry, horizon_weeks):
    """Weights from past information coefficients only. A row counts once its forward window has finished."""
    names = list(positions)
    weights = pd.DataFrame(np.nan, index=entry.index, columns=names)
    for spot, stamp in enumerate(entry.index):
        now = entry.iloc[spot]
        if pd.isna(now) or spot < 104:
            continue
        done = (entry + pd.Timedelta(days=7 * horizon_weeks) <= now).values
        scores = {}
        for name in names:
            a, b = positions[name].values[done], forward.values[done]
            use = ~np.isnan(a) & ~np.isnan(b) & (a != 0)
            scores[name] = float(np.corrcoef(a[use], b[use])[0, 1]) if use.sum() > 52 and a[use].std() > 0 else 0.0
        positive = {k: max(v, 0.0) for k, v in scores.items()}
        total = sum(positive.values())
        for name in names:
            weights.loc[stamp, name] = positive[name] / total if total > 0 else 1.0 / len(names)
    return weights.ffill().fillna(1.0 / len(names))


def t11():
    pool, members = screen()
    out = {"screen": pool, "members_A": members, "cost_bps": 5, "note": "Carry is excluded from both sleeves."}
    rates_all = {label: rates_position(label, info) for label, info in pool["rates"].items()}
    fx_all = {label: fx_position(label, info) for label, info in pool["fx"].items()}
    benchmark_rates = rule_of(BENCH_Z["mon"]).fillna(0.0)
    fx_past = PANEL[PANEL["market"] == "FX"].pivot(index="date", columns="contract", values="past26")
    benchmark_fx = -np.sign(fx_past).where(fx_past.abs() > 0.25, 0.0).fillna(0.0)

    def compose(rate_names, fx_names, cost=COST):
        parts = {}
        if rate_names:
            parts["rates"] = rates_returns(sum(rates_all[n] for n in rate_names) / len(rate_names), cost)
        if fx_names:
            parts["fx"] = fx_returns(sum(fx_all[n] for n in fx_names) / len(fx_names), cost)
        if not parts:
            return None, parts
        return pd.concat(parts, axis=1).mean(axis=1, skipna=True), parts

    bench_rates = rates_returns(benchmark_rates)
    bench_fx = fx_returns(benchmark_fx)
    bench_both = pd.concat([bench_rates, bench_fx], axis=1).mean(axis=1, skipna=True)
    hold_mask = lambda s: s[s.index >= HOLD_START]  # noqa: E731
    design_mask = lambda s: s[(s.index >= pd.Timestamp(GS_OOS_START)) & (s.index <= DESIGN_END)]  # noqa: E731

    def both_periods(series, bench):
        half_a = lambda s: s[(s.index >= HOLD_START) & (s.index <= HALF_A_END)]  # noqa: E731
        half_b = lambda s: s[s.index >= HALF_B_START]  # noqa: E731
        return {"HOLDOUT": lib.strategy_metrics(hold_mask(series), hold_mask(bench)), "DESIGN": lib.strategy_metrics(design_mask(series), design_mask(bench)),
                "H-A": lib.strategy_metrics(half_a(series), half_a(bench)), "H-B": lib.strategy_metrics(half_b(series), half_b(bench))}

    out["benchmark"] = {"rates": both_periods(bench_rates, bench_rates), "fx": both_periods(bench_fx, bench_fx), "both": both_periods(bench_both, bench_both)}
    hold_long = {"rates": rates_returns(pd.Series(1.0, index=INDEX)), "fx": fx_returns(pd.DataFrame(1.0, index=fx_past.index, columns=fx_past.columns))}
    out["buy_hold"] = {k: both_periods(v, bench_rates if k == "rates" else bench_fx) for k, v in hold_long.items()}
    out["single"] = {"rates": {}, "fx": {}}
    for label, position in rates_all.items():
        out["single"]["rates"][label] = both_periods(rates_returns(position), bench_rates)
    for label, position in fx_all.items():
        out["single"]["fx"][label] = both_periods(fx_returns(position), bench_fx)
    composite, parts = compose(members["rates"], members["fx"])
    if composite is None:
        out["composite_A"] = {"status": "empty"}
        reg("T11.1", "primary", "Composite A net Sharpe", {"status": "empty", "p_primary": float("nan")}, sign_ok=False, extra_ok=False)
        reg("T11.2", "primary", "Composite A minus benchmark Sharpe", {"status": "empty", "p_primary": float("nan")}, sign_ok=False, extra_ok=False)
    else:
        bench_for = bench_both if (members["rates"] and members["fx"]) else (bench_rates if members["rates"] else bench_fx)
        metrics = both_periods(composite, bench_for)
        out["composite_A"] = {"metrics": metrics, "sleeves": {k: both_periods(v, bench_rates if k == "rates" else bench_fx) for k, v in parts.items()}}
        out["composite_A"]["cost_sensitivity_holdout_sharpe"] = {}
        for bps in (0, 1, 5, 10):
            net, _ = compose(members["rates"], members["fx"], cost=bps / 1e4)
            out["composite_A"]["cost_sensitivity_holdout_sharpe"][str(bps)] = lib.strategy_metrics(hold_mask(net)).get("sharpe")
        hold = metrics["HOLDOUT"]
        reg("T11.1", "primary", "Composite A net Sharpe, holdout", hold, sign_ok=hold.get("sharpe", 0) > 0, stat=hold.get("sharpe"), design=metrics["DESIGN"].get("sharpe"))
        pair = {"p_primary": hold.get("p_diff_boot", float("nan")), "n": hold.get("n"), "ci_boot": hold.get("sharpe_diff_ci_boot")}
        reg("T11.2", "primary", "Composite A minus benchmark Sharpe, holdout", pair, sign_ok=hold.get("sharpe_minus_benchmark", 0) > 0, stat=hold.get("sharpe_minus_benchmark"))
        # Walk-forward information-coefficient weights, secondary.
        ic = {}
        if members["rates"]:
            pos = pd.DataFrame({n: rates_all[n] for n in members["rates"]})
            earn26 = -forward_from(TEN, ENTRY, 26)
            w = walkforward_ic_weights(pos.replace(0.0, np.nan), earn26, ENTRY, 26)
            weighted = (pos * w).sum(axis=1)
            ic["rates"] = rates_returns(weighted)
        if members["fx"]:
            positions = {n: fx_all[n] for n in members["fx"]}
            dates = list(positions[members["fx"][0]].index)
            stacked = PANEL[PANEL["market"] == "FX"].pivot(index="date", columns="contract", values="y26").reindex(index=dates)
            pooled = {n: positions[n].reindex(index=dates) for n in members["fx"]}
            entry_fx = PANEL[(PANEL["market"] == "FX") & (PANEL["contract"] == "EC")].set_index("date")["entry"].reindex(dates)
            means = pd.DataFrame({n: (pooled[n] * stacked).mean(axis=1) for n in members["fx"]})
            weights = {}
            for spot, stamp in enumerate(dates):
                now = entry_fx.iloc[spot]
                if pd.isna(now) or spot < 104:
                    weights[stamp] = pd.Series(np.nan, index=members["fx"])
                    continue
                done = (entry_fx + pd.Timedelta(days=182) <= now).values
                mean = means[done].mean().clip(lower=0.0)
                weights[stamp] = mean / mean.sum() if mean.sum() > 0 else pd.Series(1.0 / len(members["fx"]), index=members["fx"])
            weight_frame = pd.DataFrame(weights).T.ffill().fillna(1.0 / len(members["fx"]))
            total = sum(pooled[n].mul(weight_frame[n], axis=0) for n in members["fx"])
            ic["fx"] = fx_returns(total)
        if ic:
            ic_series = pd.concat(ic, axis=1).mean(axis=1, skipna=True)
            ic_metrics = both_periods(ic_series, bench_for)
            out["composite_A_ic_weighted"] = ic_metrics
            reg("T11.S.ic", "secondary", "Composite A, walk-forward IC weights, Sharpe", ic_metrics["HOLDOUT"], sign_ok=ic_metrics["HOLDOUT"].get("sharpe", 0) > 0, stat=ic_metrics["HOLDOUT"].get("sharpe"))
    # Composite C: an amendment after A came back empty. Goldman's published direction for all three I5 groups, so no selection at all.
    names_c = ["I5_am_TYUS", "I5_lev", "I5_spec"]
    series_c = rates_returns(sum(rates_all[n] for n in names_c) / 3.0)
    metrics_c = both_periods(series_c, bench_rates)
    out["composite_C_prior_sign"] = {"members": names_c, "metrics": metrics_c,
                                     "cost_sensitivity_holdout_sharpe": {str(b): lib.strategy_metrics(hold_mask(rates_returns(sum(rates_all[n] for n in names_c) / 3.0, b / 1e4))).get("sharpe") for b in (0, 1, 5, 10)}}
    hold_c = metrics_c["HOLDOUT"]
    reg("T11.S.C", "secondary", "Composite C (three I5 groups, prior sign), net Sharpe", hold_c, sign_ok=hold_c.get("sharpe", 0) > 0, stat=hold_c.get("sharpe"), design=metrics_c["DESIGN"].get("sharpe"))
    reg("T11.S.C_vs_bench", "secondary", "Composite C minus benchmark Sharpe", {"p_primary": hold_c.get("p_diff_boot", float("nan")), "n": hold_c.get("n"), "ci_boot": hold_c.get("sharpe_diff_ci_boot")},
        sign_ok=hold_c.get("sharpe_minus_benchmark", 0) > 0, stat=hold_c.get("sharpe_minus_benchmark"))
    out["cost_sensitivity_single"] = {label: {str(b): lib.strategy_metrics(hold_mask(rates_returns(rates_all[label], b / 1e4))).get("sharpe") for b in (0, 1, 5, 10)}
                                      for label in ("I5_am_TYUS", "I5_lev", "I5_spec", "I3_lev")}
    out["cost_sensitivity_single"]["benchmark"] = {str(b): lib.strategy_metrics(hold_mask(rates_returns(benchmark_rates, b / 1e4))).get("sharpe") for b in (0, 1, 5, 10)}
    # Single-signal Sharpe tests, secondary.
    for sleeve, block in out["single"].items():
        for label, metrics in block.items():
            hold = metrics["HOLDOUT"]
            reg(f"T11.S.single.{sleeve}.{label}", "secondary", f"Single {label}, {sleeve}, net Sharpe", hold, sign_ok=hold.get("sharpe", 0) > 0, stat=hold.get("sharpe"), design=metrics["DESIGN"].get("sharpe"))
    for sleeve, block in out["benchmark"].items():
        hold = block["HOLDOUT"]
        reg(f"T11.S.bench.{sleeve}", "secondary", f"Benchmark strategy, {sleeve}, net Sharpe", hold, sign_ok=hold.get("sharpe", 0) > 0, stat=hold.get("sharpe"), design=block["DESIGN"].get("sharpe"))
    out["_compose"] = None
    R["T11"] = out
    return rates_all, fx_all, compose, both_periods, bench_rates, bench_fx, bench_both


def hindsight_composite(rates_all, fx_all, compose, both_periods, bench_rates, bench_fx, bench_both):
    """Composite B uses holdout survivors. It is contaminated by construction and is outside the Holm family."""
    rate_names, fx_names = [], []
    mapping = {"I1": 0, "I2": 1, "I3_lev": 2, "I3_am": 3, "I4": 4}
    for market, bucket, base in (("UST", rate_names, 1), ("FX", fx_names, 6)):
        for label, offset in mapping.items():
            rec = REG[f"T8.{base + offset}"]
            if rec["sign_ok"] and rec["p_raw"] is not None and rec["p_raw"] < 0.05:
                bucket.append(label)
    groups = {"lev": 0, "am": 1, "spec": 2}
    for market, bucket, base in (("UST", rate_names, 1), ("FX", fx_names, 4)):
        for group, offset in groups.items():
            rec = REG[f"T6.{base + offset}"]
            if rec["sign_ok"] and rec["p_raw"] is not None and rec["p_raw"] < 0.05:
                bucket.append(f"P2_{group}")
    for spot, name in {1: "am_TYUS", 3: "lev", 4: "spec"}.items():
        rec = REG[f"T1.{spot}"]
        if rec["sign_ok"] and rec["p_raw"] is not None and rec["p_raw"] < 0.05:
            rate_names.append(f"I5_{name}")
    for spot, group in {1: "am", 2: "lev", 3: "spec"}.items():
        rec = REG[f"T9.{spot}"]
        if rec["sign_ok"] and rec["p_raw"] is not None and rec["p_raw"] < 0.05:
            fx_names.append(f"I5FX_{group}")
    for market, bucket, base in (("UST", rate_names, 1), ("FX", fx_names, 4)):
        for group, offset in groups.items():
            rec = REG[f"T10.{base + {'am': 0, 'lev': 1, 'spec': 2}[group]}"]
            if rec["sign_ok"] and rec["p_raw"] is not None and rec["p_raw"] < 0.05:
                bucket.append(f"OPT_{group}")
    composite, parts = compose(rate_names, fx_names)
    block = {"label": "HINDSIGHT. Members chosen with holdout results. Not evidence.", "members": {"rates": rate_names, "fx": fx_names}}
    if composite is not None:
        bench_for = bench_both if (rate_names and fx_names) else (bench_rates if rate_names else bench_fx)
        block["metrics"] = both_periods(composite, bench_for)
    R["T11"]["composite_B_hindsight"] = block


# ---------------------------------------------------------------------------
# Size check and sample-size statement
# ---------------------------------------------------------------------------


def size_check():
    out = {}
    keep = mask_for("HOLDOUT")
    for name, k in (("am_TYUS", 26), ("am_TYUS", 13)):
        frame = pd.concat([AHEAD[("mon", k)][keep].rename("y"), score_of(name)[keep].rename("x")], axis=1).dropna()
        n = len(frame)
        rejects_primary, rejects_nw, rejects_normal, count = 0, 0, 0, 0
        for shift in range(k, n - k, 2):
            rotated = pd.Series(np.roll(frame["x"].values, shift), index=frame.index)
            res = ts_test(frame["y"], rotated, k, draws=400, seed=SEED + shift)
            count += 1
            rejects_primary += res["p_primary"] < 0.05
            rejects_nw += res["p_nw"] < 0.05
            rejects_normal += abs(res["t_nw"]) > 1.96
        out[f"{name}_{k}w"] = {"rotations": count, "reject_primary": rejects_primary / count, "reject_nw_student": rejects_nw / count, "reject_nw_normal": rejects_normal / count}
    frame = panel_period("UST", "HOLDOUT", 13)
    col = "net_share_lev_w126_pro_rata"
    dates = sorted(frame["date"].unique())
    rejects, count = 0, 0
    for shift in range(13, len(dates) - 13, 6):
        mapping = dict(zip(dates, dates[shift:] + dates[:shift]))
        moved = frame[["contract", "date", col]].copy()
        moved["date"] = moved["date"].map(mapping)
        rotated = frame.drop(columns=[col]).merge(moved, on=["contract", "date"], how="left")
        res = panel_test(rotated, "y13", col, 13, draws=300, seed=SEED + shift)
        count += 1
        rejects += res.get("p_primary", 1.0) < 0.05
    out["panel_UST_P2_lev_13w"] = {"rotations": count, "reject_primary": rejects / count}
    R["size_check"] = out


def rotations():
    """Amendment A2. The size check showed the bootstrap and Newey-West p-values reject too often at long horizons.

    Rotation keeps each series' own persistence, so it gives a second null for every primary slope test.
    It is reported beside the pre-registered p-value and does not replace it.
    """
    keep = mask_for("HOLDOUT")
    ts = {"T1.1": ("am_TYUS", 26), "T1.2": ("am_all6", 26), "T1.3": ("lev", 26), "T1.4": ("spec", 26), "T5.1": ("am_TYUS", 4), "T5.2": ("am_TYUS", 8), "T5.3": ("am_TYUS", 13)}
    out = {}
    for test_id, (name, k) in ts.items():
        out[test_id] = lib.rotation_p_ts(AHEAD[("mon", k)][keep], score_of(name)[keep], k)
    out["T1.5"] = lib.rotation_p_ts(AHEAD[("mon", 26)][keep], BENCH["mon"][keep], 26)
    for test_id, name in {"T3.1": "am_TYUS", "T3.2": "lev", "T3.3": "spec"}.items():
        out[test_id] = lib.rotation_p_ts(AHEAD[("mon", 26)][keep], score_of(name)[keep], 26, control=BENCH["mon"][keep])
    groups = ("lev", "am", "spec")
    spot = 1
    for market in ("UST", "FX"):
        for group in groups:
            out[f"T6.{spot}"] = lib.rotation_p_panel(panel_period(market, "HOLDOUT", 13), "y13", f"net_share_{group}_w126_pro_rata", 13)
            spot += 1
    out["T6.7"] = lib.rotation_p_panel(panel_period("UST", "HOLDOUT", 13), "y13", "net_share_lev_w126_pro_rata", 13, control="past26")
    out["T6.8"] = lib.rotation_p_panel(panel_period("FX", "HOLDOUT", 13), "y13", "net_share_lev_w126_pro_rata", 13, control="past26")
    out["T7.3"] = lib.rotation_p_panel(panel_period("UST", "HOLDOUT", 13), "y13", "crowd_pain_spec", 13)
    out["T7.4"] = lib.rotation_p_panel(panel_period("FX", "HOLDOUT", 13), "y13", "crowd_pain_spec", 13)
    for test_id, market in (("T7.5", "UST"), ("T7.6", "FX")):
        chosen = R["T7"]["windows"][f"{market}_lev"]["design_choice"]
        out[test_id] = lib.rotation_p_panel(panel_period(market, "HOLDOUT", 13), "y13", f"net_share_lev_w{chosen}_pro_rata", 13)
    spot = 1
    for market in ("UST", "FX"):
        for name in INDICATORS:
            frame = panel_period(market, "HOLDOUT", 13).dropna(subset=list(INDICATORS) + ["y13"])
            out[f"T8.{spot}"] = lib.rotation_p_panel(frame, "y13", name, 13)
            spot += 1
    for spot, group in enumerate(("am", "lev", "spec"), start=1):
        out[f"T9.{spot}"] = lib.rotation_p_panel(panel_period("FX", "HOLDOUT", 26), "y26", f"i5fx_{group}", 26)
    spot = 1
    for market in ("UST", "FX"):
        for group in ("am", "lev", "spec"):
            out[f"T10.{spot}"] = lib.rotation_p_panel(panel_period(market, "HOLDOUT", 4), "y4", f"opt_flow_{group}", 4)
            spot += 1
    for test_id, res in out.items():
        REG[test_id]["p_rotation"] = res["p_rotation"]
        REG[test_id]["rotations"] = res["rotations"]
    adjusted = holm({k: v["p_rotation"] for k, v in out.items()})
    for test_id, value in adjusted.items():
        REG[test_id]["p_rotation_holm"] = value
    R["rotation"] = out


def finish():
    primary = {k: v["p_raw"] for k, v in REG.items() if v["tier"] == "primary"}
    everything = {k: v["p_raw"] for k, v in REG.items()}
    adj_primary, adj_all = holm(primary), holm(everything)
    for key, rec in REG.items():
        rec["p_holm_primary"] = adj_primary.get(key)
        rec["p_holm_all"] = adj_all[key]
        rec["success"] = bool(rec["tier"] == "primary" and rec["p_holm_primary"] is not None and rec["p_holm_primary"] < 0.05 and rec["sign_ok"] is not False and rec["extra_ok"])
        design, stat = rec.get("design_stat"), rec.get("stat")
        rec["oos_beats_is_flag"] = bool(design is not None and stat is not None and np.isfinite(design) and np.isfinite(stat) and np.sign(design) == np.sign(stat) and abs(stat) > abs(design))
    alphas = {"26w": 14, "13w": 28, "8w": 45.5, "4w": 91}
    m = len(primary)
    R["power"] = {"goldman_minus_43_at_neff_14": {"raw_5pct": lib.power_for_corr(0.43, 14, 0.05), "holm_first_step": lib.power_for_corr(0.43, 14, 0.05 / m)},
                  "corr_0p2_at_neff_28": {"raw_5pct": lib.power_for_corr(0.2, 28, 0.05), "holm_first_step": lib.power_for_corr(0.2, 28, 0.05 / m)}}
    R["sample_size"] = {"family_size_primary": m, "family_size_all": len(everything), "holm_first_step_alpha": 0.05 / m,
                        "min_detectable_corr": {label: {"n_eff": n_eff, "raw_5pct": lib.min_detectable_corr(n_eff, 0.05), "holm_first_step": lib.min_detectable_corr(n_eff, 0.05 / m)}
                                                for label, n_eff in alphas.items()}}
    R["family"] = REG
    R["canonical"] = canonical()
    with open(DERIVED / "gate.json") as handle:
        R["replication_gate"] = json.load(handle)
    with open(DERIVED / "ledger_check.json") as handle:
        R["ledger_check"] = json.load(handle)
    R["boundaries"] = {"fit": [lib.FIT_START, lib.FIT_END], "design_end": str(DESIGN_END.date()), "holdout_start": str(HOLD_START.date()),
                       "holdout_a_end": str(HALF_A_END.date()), "holdout_b_start": str(HALF_B_START.date()), "last_report_date": str(INDEX[-1].date()),
                       "last_dgs10": str(TEN.index[-1].date()), "weeks_total": int(len(INDEX)), "weeks_design": int((INDEX <= DESIGN_END).sum()), "weeks_holdout": int((INDEX >= HOLD_START).sum())}
    R["seed"] = SEED
    R["bootstrap_draws"] = NBOOT
    R["T11"].pop("_compose", None)

    def clean(value):
        if isinstance(value, dict):
            return {str(k): clean(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [clean(v) for v in value]
        if isinstance(value, (np.floating, float)):
            return None if not np.isfinite(value) else float(value)
        if isinstance(value, (np.integer,)):
            return int(value)
        if isinstance(value, (np.bool_,)):
            return bool(value)
        return value

    (HERE / "results.json").write_text(json.dumps(clean(R), indent=1))


def canonical():
    rows = {}
    t11_block = R["T11"]
    for name in THREE:
        rows[f"I5_{name}"] = t11_block["single"]["rates"][f"I5_{name}"]["HOLDOUT"]
    rows["benchmark_rates"] = t11_block["benchmark"]["rates"]["HOLDOUT"]
    rows["buy_hold_rates"] = t11_block["buy_hold"]["rates"]["HOLDOUT"]
    if "metrics" in t11_block.get("composite_A", {}):
        rows["composite_A"] = t11_block["composite_A"]["metrics"]["HOLDOUT"]
    return {k: {"oos_sharpe": v.get("sharpe"), "t_stat": v.get("t_stat"), "max_drawdown": v.get("max_drawdown"), "info_ratio_vs_benchmark": v.get("info_ratio")} for k, v in rows.items()}


def main():
    for job in (t1, t2, t5, t3, t4, t6, t6b, t7, t8, t9, t10, t12, t13, benchmark_bias):
        job()
        print(job.__name__, "done", len(REG), flush=True)
    bundle = t11()
    print("t11 done", len(REG), flush=True)
    hindsight_composite(*bundle)
    size_check()
    print("size check done", flush=True)
    rotations()
    print("rotations done", flush=True)
    finish()
    print("results.json written")
    missing = [k for k, v in REG.items() if v["p_raw"] is None or not np.isfinite(v["p_raw"])]
    print("tests with no p-value:", missing)


if __name__ == "__main__":
    main()
