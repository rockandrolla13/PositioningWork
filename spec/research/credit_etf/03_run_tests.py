#!/usr/bin/env python3
"""Run the tests fixed in plan.md and write results.json. Reads work/ panels. Writes nothing outside this folder."""
from __future__ import annotations

import json
import math
import os
import warnings

import numpy as np
import pandas as pd
from scipy import stats as st

from common import CARRY, GROUP, HERE, RAW, WORK, holm, load_fred
from posmon.cta import rolling_proxy
from posmon.indicators import cross_section_weights, forward_stats, net_pct_oi
from posmon.pain import activity_by_price, cftc_pain
from posmon.stats import newey_west_ols

warnings.filterwarnings("ignore")
DEV_END = pd.Timestamp("2016-12-31")
SI_DEV_END = pd.Timestamp("2021-12-31")
HORIZONS = (1, 4, 13, 26)
PRIMARY = ["LQD", "HYG"]
REPLICATE = {"LQD": "USIG", "HYG": "JNK"}
EXTRA_REPLICATES = {"LQD": ["IGIB", "IGSB"], "HYG": ["USHY"]}
C2 = ["pain126", "p1_long_oi", "p1_short_oi", "gap126", "gap_full", "gap_turn", "p5_water", "flow13", "i2_so", "i3_flow",
      "i4_rule"]
C3 = ["i5_usd", "i5_pct"]
C4 = ["i7_cont", "i7_rev", "i8_trend"]
C5 = ["si_ratio", "si_chg", "si_i2"]
SIGNALS = C2 + C3 + C4 + C5
BENCHMARKS = ["mom26", "level", "past26"]
CS_POOL = ["LQD", "IGSB", "IGIB", "USIG", "SPSB", "SPIB", "SPLB", "HYG", "JNK", "USHY", "FALN", "SHYG", "SJNK", "EMB"]
SEED = 20261101
BOOT = 2000


def clean(value):
    """Strict JSON: NaN and infinity become null, and numpy values become plain numbers."""
    if isinstance(value, dict):
        return {str(key): clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (float, np.floating)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, np.integer):
        return int(value)
    if value is None or isinstance(value, (int, str)):
        return value
    return str(value)


def nw_lag(h: int) -> int:
    return max(4, math.ceil(1.5 * h))


def t_p(t_value: float, n: int, h: int) -> float:
    df = max(n / h - 2.0, 3.0)
    return float(2.0 * st.t.sf(abs(t_value), df))


def block_ci(y: np.ndarray, x: np.ndarray | None, h: int, rng: np.random.Generator) -> tuple:
    """Circular block bootstrap, block = max(8, 2h), for a slope or, with x None, a mean."""
    n = len(y)
    block = max(8, 2 * h)
    count = int(np.ceil(n / block))
    starts = rng.integers(0, n, size=(BOOT, count))
    index = (starts[:, :, None] + np.arange(block)[None, None, :]) % n
    index = index.reshape(BOOT, -1)[:, :n]
    ys = y[index]
    if x is None:
        draws = ys.mean(axis=1)
    else:
        xs = x[index]
        xd = xs - xs.mean(axis=1, keepdims=True)
        draws = (xd * ys).sum(axis=1) / np.maximum((xd * xd).sum(axis=1), 1e-12)
    return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def standardise(signal: pd.Series, dev_end: pd.Timestamp, discrete: bool = False) -> tuple:
    if discrete:
        return signal, {"mean": 0.0, "sd": 1.0, "dev_n": int(signal[signal.index <= dev_end].notna().sum()), "thin_dev": False}
    dev = signal[signal.index <= dev_end].dropna()
    thin = len(dev) < 52
    reference = dev if not thin else signal.dropna().iloc[:104]
    if len(reference) < 20 or reference.std() == 0:
        return signal * np.nan, {"mean": None, "sd": None, "dev_n": int(len(dev)), "thin_dev": True}
    return (signal - reference.mean()) / reference.std(), {"mean": float(reference.mean()), "sd": float(reference.std()),
                                                            "dev_n": int(len(dev)), "thin_dev": bool(thin)}


def ols_row(y: pd.Series, z: pd.Series, h: int) -> dict:
    frame = pd.concat([y.rename("y"), z.rename("z")], axis=1).dropna()
    if len(frame) < max(30, 2 * h):
        return {"n": int(len(frame)), "b": None, "t": None, "p": None}
    table = newey_west_ols(frame["y"], frame[["z"]], nw_lag(h))
    t_value = float(table.loc["z", "t"])
    return {"n": int(len(frame)), "n_eff": round(len(frame) / h, 1), "b": float(table.loc["z", "beta"]), "t": t_value,
            "p": t_p(t_value, len(frame), h), "const": float(table.loc["const", "beta"]),
            "r2": float(frame["y"].corr(frame["z"]) ** 2)}


def test_signal(week: pd.DataFrame, name: str, h: int, dev_end: pd.Timestamp, rng: np.random.Generator, alt=None) -> dict:
    y = week[f"xr{h}"]
    discrete = name == "i4_rule"
    z, scale = standardise(week[name], dev_end, discrete)
    hold = week.index > dev_end
    dev_mask = ~hold
    out = {"scale": scale, "holdout": ols_row(y[hold], z[hold], h), "dev": ols_row(y[dev_mask], z[dev_mask], h)}
    row = out["holdout"]
    if row.get("b") is None:
        return out
    frame = pd.concat([y[hold].rename("y"), z[hold].rename("z")], axis=1).dropna()
    row["ci95"] = block_ci(frame["y"].values, frame["z"].values, h, rng)
    if discrete:
        top, low = frame["z"] >= 1, frame["z"] <= -1
    else:
        reference = z[dev_mask].dropna()
        if len(reference) < 52:
            reference = z.dropna().iloc[:104]
        q80, q20 = reference.quantile(0.8), reference.quantile(0.2)
        top, low = frame["z"] >= q80, frame["z"] <= q20
    row["base_rate_pos"] = float((frame["y"] > 0).mean())
    row["mean_y"] = float(frame["y"].mean())
    row["top"] = {"n": int(top.sum()), "hit_pos": float((frame["y"][top] > 0).mean()) if top.any() else None,
                  "mean": float(frame["y"][top].mean()) if top.any() else None}
    row["bottom"] = {"n": int(low.sum()), "hit_pos": float((frame["y"][low] > 0).mean()) if low.any() else None,
                     "mean": float(frame["y"][low].mean()) if low.any() else None}
    controls = pd.DataFrame({"z": z[hold]})
    extras = [extra for extra in ("mom26", "level") if extra != name and not (name == "past26" and extra == "mom26")]
    for extra in extras:
        extra_z, _ = standardise(week[extra], dev_end)
        controls[extra] = extra_z[hold]
    joined = pd.concat([y[hold].rename("y"), controls], axis=1).dropna()
    if len(joined) > 50:
        table = newey_west_ols(joined["y"], joined[["z", *extras]], nw_lag(h))
        row["with_controls"] = {"b": float(table.loc["z", "beta"]), "t": float(table.loc["z", "t"]), "n": int(len(joined))}
    if alt:
        row["alt_targets"] = {}
        for label, target in alt.items():
            part = ols_row(target[h][hold], z[hold], h)
            row["alt_targets"][label] = {k: part.get(k) for k in ("n", "b", "t", "p")}
    return out


def verdict_for(entry: dict, adjusted: float | None, replicate_b: float | None) -> str:
    row = entry["holdout"]
    if row.get("b") is None:
        return "not_testable"
    dev_b = entry["dev"].get("b")
    sign_ok = dev_b is not None and np.sign(dev_b) == np.sign(row["b"])
    ci = row.get("ci95", (0, 0))
    ci_ok = ci[0] > 0 or ci[1] < 0
    repl_ok = replicate_b is not None and np.sign(replicate_b) == np.sign(row["b"])
    control_ok = abs(row.get("with_controls", {}).get("t", 0.0)) > 2.0
    if adjusted is not None and adjusted < 0.05 and ci_ok and sign_ok and repl_ok and control_ok:
        return "predictive"
    if row["p"] < 0.05 and sign_ok:
        return "suggestive"
    return "no_evidence"


def forward_level(series: pd.Series, weeks: pd.DatetimeIndex, h: int) -> pd.Series:
    level = series.dropna()
    level = level.reindex(level.index.union(weeks)).ffill(limit=10).reindex(weeks)
    return (level.shift(-h) - level) * 100.0  # percent to bp


def two_equation(y1, z1, y2, z2, h: int) -> dict:
    """Wald test of equal slopes for two funds with a joint Newey-West covariance."""
    frame = pd.concat([y1.rename("y1"), z1.rename("z1"), y2.rename("y2"), z2.rename("z2")], axis=1).dropna()
    n = len(frame)
    if n < max(40, 3 * h):
        return {"n": n}
    moments = []
    b_values = []
    for i in (1, 2):
        x = np.column_stack([np.ones(n), frame[f"z{i}"].values])
        beta = np.linalg.lstsq(x, frame[f"y{i}"].values, rcond=None)[0]
        moments.append(x * (frame[f"y{i}"].values - x @ beta)[:, None])
        b_values.append(float(beta[1]))
    u = np.hstack(moments)
    meat = u.T @ u
    lag = nw_lag(h)
    for k in range(1, lag + 1):
        weight = 1.0 - k / (lag + 1.0)
        cross = u[k:].T @ u[:-k]
        meat += weight * (cross + cross.T)
    a = np.zeros((4, 4))
    for i, block in enumerate((1, 2)):
        x = np.column_stack([np.ones(n), frame[f"z{block}"].values])
        a[2 * i:2 * i + 2, 2 * i:2 * i + 2] = x.T @ x
    inverse = np.linalg.inv(a)
    cov = inverse @ meat @ inverse
    var = cov[1, 1] + cov[3, 3] - 2.0 * cov[1, 3]
    t_value = (b_values[0] - b_values[1]) / math.sqrt(max(var, 1e-12))
    return {"n": n, "b1": b_values[0], "b2": b_values[1], "t_diff": float(t_value), "p": t_p(t_value, n, h),
            "same_sign": bool(np.sign(b_values[0]) == np.sign(b_values[1]))}


def strategy_row(position: pd.Series, xr1: pd.Series, half_spread: float, borrow: float) -> dict:
    """Weekly returns in bp. Costs: half-spread + 1 bp hedge per side, borrow on short weeks."""
    frame = pd.concat([position.rename("p"), xr1.rename("r")], axis=1).dropna()
    if frame.empty:
        return {}
    turnover = frame["p"].diff().abs().fillna(frame["p"].abs())
    gross = frame["p"] * frame["r"]
    cost = turnover * (half_spread + 1.0) + (frame["p"] < 0) * borrow * 1e4 / 52.0
    net = gross - cost
    scale = np.sqrt(52.0)
    return {"weeks": int(len(frame)), "gross_bp_year": float(gross.mean() * 52), "net_bp_year": float(net.mean() * 52),
            "vol_bp_year": float(gross.std() * scale), "sharpe_gross": float(gross.mean() / gross.std() * scale),
            "sharpe_net": float(net.mean() / net.std() * scale), "turnover_year": float(turnover.mean() * 52)}


def main() -> None:
    rng = np.random.default_rng(SEED)
    facts = json.loads((WORK / "panel_facts.json").read_text())
    weekly = {t: pd.read_pickle(WORK / f"weekly_{t}.pkl") for t, f in facts.items() if f.get("status") == "ok"}
    daily = {t: pd.read_pickle(WORK / f"daily_{t}.pkl") for t in weekly}
    short = {t: pd.read_pickle(WORK / f"si_{t}.pkl") for t in weekly}
    results: dict = {"as_of": "2026-11-01", "dev_end": str(DEV_END.date()), "si_dev_end": str(SI_DEV_END.date()),
                     "funds": {t: {k: facts[t].get(k) for k in ("fund_first", "fund_last", "first_week", "last_week", "nav_missing", "so_missing", "so_changed_share", "dividend_source", "splits")} for t in weekly}}

    baa = load_fred("BAA10Y")
    oas = {"IG": load_fred("BAMLC0A0CM"), "HY": load_fred("BAMLH0A0HYM2")}

    # I4 uses development mean and sd, because the function in posmon uses the full sample.
    for ticker, week in weekly.items():
        flow = week["cs01_flow13"]
        dev = flow[flow.index <= DEV_END].dropna()
        if len(dev) >= 52:
            score = (flow - dev.mean()) / dev.std()
        else:
            reference = flow.dropna().iloc[:104]
            score = (flow - reference.mean()) / reference.std()
        week["i4_rule"] = pd.Series(np.where(score <= -1.0, 1.0, np.where(score >= 1.0, -1.0, 0.0)), index=week.index).where(score.notna())

    # ------------------------------------------------------------------ family of predictive tests
    family: dict = {}
    pvals: dict = {}
    for name in SIGNALS:
        dev_end = SI_DEV_END if name in C5 else DEV_END
        for fund in PRIMARY:
            week = weekly[fund]
            group = GROUP[fund]
            alt = {"ds_impl": {h: week[f"ds{h}"] for h in HORIZONS}}
            alt["ds_oas"] = {h: forward_level(oas[group], week.index, h) for h in HORIZONS}
            if group == "IG":
                alt["ds_baa"] = {h: forward_level(baa, week.index, h) for h in HORIZONS}
            for h in HORIZONS:
                if name not in week:
                    continue
                entry = test_signal(week, name, h, dev_end, rng, alt)
                replicate = REPLICATE[fund]
                rep = test_signal(weekly[replicate], name, h, dev_end, rng) if replicate in weekly and name in weekly[replicate] else None
                entry["replicate"] = {"fund": replicate, **(rep["holdout"] if rep else {})}
                entry["extra_replicates"] = {}
                for other in EXTRA_REPLICATES[fund]:
                    if other in weekly and name in weekly[other]:
                        part = test_signal(weekly[other], name, h, dev_end, rng)["holdout"]
                        entry["extra_replicates"][other] = {k: part.get(k) for k in ("n", "b", "t", "p")}
                key = f"{name}|{fund}|{h}"
                family[key] = entry
                if entry["holdout"].get("p") is not None:
                    pvals[key] = entry["holdout"]["p"]

    # ------------------------------------------------------------------ cross-section tests (C4)
    panel = {name: pd.DataFrame({t: weekly[t][name] for t in CS_POOL if t in weekly and name in weekly[t]}) for name in ("i7_cont", "i7_rev")}
    cs_results: dict = {}
    for name, frame in panel.items():
        for h in HORIZONS:
            scaled = pd.DataFrame({t: weekly[t][f"xr{h}"] / (weekly[t]["sigma26"] * math.sqrt(h)) for t in frame.columns})
            rows = {}
            for pool_name, pool in (("all", list(frame.columns)), ("IG", [t for t in frame.columns if GROUP.get(t) == "IG"]), ("HY", [t for t in frame.columns if GROUP.get(t) == "HY"])):
                series = {}
                for stamp, row in frame[pool].iterrows():
                    signals = row.dropna()
                    if len(signals) < 4:
                        continue
                    weights = cross_section_weights(signals)
                    values = scaled.loc[stamp, signals.index]
                    if values.notna().sum() < len(signals):
                        continue
                    series[stamp] = float((weights * values).sum())
                rows[pool_name] = pd.Series(series, dtype=float)
            entry = {}
            for pool_name, series in rows.items():
                for sample, mask in (("dev", series.index <= DEV_END), ("holdout", series.index > DEV_END)):
                    part = series[mask].dropna()
                    if len(part) < max(30, 2 * h):
                        entry[f"{pool_name}_{sample}"] = {"n": int(len(part)), "b": None}
                        continue
                    design = pd.DataFrame({"z": np.ones(len(part))}, index=part.index)
                    # Regress on a constant only: newey_west_ols adds the constant, so use the mean directly.
                    x = np.ones((len(part), 1))
                    u = (part.values - part.mean())[:, None]
                    meat = float((u.T @ u)[0, 0])
                    lag = nw_lag(h)
                    for k in range(1, lag + 1):
                        meat += 2.0 * (1.0 - k / (lag + 1.0)) * float((u[k:].T @ u[:-k])[0, 0])
                    se = math.sqrt(meat) / len(part)
                    t_value = float(part.mean() / se)
                    entry[f"{pool_name}_{sample}"] = {"n": int(len(part)), "n_eff": round(len(part) / h, 1), "b": float(part.mean()), "t": t_value,
                                                      "p": t_p(t_value, len(part), h), "ci95": block_ci(part.values, None, h, rng),
                                                      "ann_ir": float(part.mean() / part.std() * math.sqrt(52.0 / h))}
                    del design, x
            cs_results[f"{name}_cs|{h}"] = entry
            if entry.get("all_holdout", {}).get("p") is not None:
                pvals[f"{name}_cs|all|{h}"] = entry["all_holdout"]["p"]

    adjusted = holm(pvals)
    labels = {}
    for key, entry in family.items():
        replicate_b = entry.get("replicate", {}).get("b")
        labels[key] = verdict_for(entry, adjusted.get(key), replicate_b)
        entry["holm_p"] = adjusted.get(key)
        entry["label"] = labels[key]
    for key, entry in cs_results.items():
        name, h = key.split("|")
        full = f"{name}|all|{h}"
        entry["holm_p"] = adjusted.get(full)
        holdout, dev = entry.get("all_holdout", {}), entry.get("all_dev", {})
        if holdout.get("b") is None:
            entry["label"] = "not_testable"
        else:
            sign_ok = dev.get("b") is not None and np.sign(dev["b"]) == np.sign(holdout["b"])
            both = all(entry.get(f"{p}_holdout", {}).get("b") is not None and np.sign(entry[f"{p}_holdout"]["b"]) == np.sign(holdout["b"]) for p in ("IG", "HY"))
            ci = holdout["ci95"]
            if entry["holm_p"] is not None and entry["holm_p"] < 0.05 and sign_ok and both and (ci[0] > 0 or ci[1] < 0):
                entry["label"] = "predictive"
            elif holdout["p"] < 0.05 and sign_ok:
                entry["label"] = "suggestive"
            else:
                entry["label"] = "no_evidence"
    results["family_size"] = len(pvals)
    results["holm_smallest_threshold"] = 0.05 / max(len(pvals), 1)
    results["family"] = family
    results["cross_section"] = cs_results
    results["label_counts"] = pd.Series(list(labels.values()) + [e["label"] for e in cs_results.values()]).value_counts().to_dict()

    # ------------------------------------------------------------------ benchmarks
    bench: dict = {}
    for fund in PRIMARY + ["JNK", "USIG"]:
        week = weekly[fund]
        hold = week[week.index > DEV_END]
        rows = {"buy_hold": {}}
        for h in HORIZONS:
            y = hold[f"xr{h}"].dropna()
            u = (y - y.mean()).values[:, None]
            lag = nw_lag(h)
            meat = float((u.T @ u)[0, 0])
            for k in range(1, lag + 1):
                meat += 2.0 * (1.0 - k / (lag + 1.0)) * float((u[k:].T @ u[:-k])[0, 0])
            se = math.sqrt(meat) / len(y)
            rows["buy_hold"][str(h)] = {"n": int(len(y)), "mean_bp": float(y.mean()), "t": float(y.mean() / se), "base_rate_pos": float((y > 0).mean()), "tr_mean_bp": float(hold[f"tr{h}"].mean())}
        for name in BENCHMARKS:
            rows[name] = {}
            for h in HORIZONS:
                part = test_signal(week, name, h, DEV_END, rng)
                rows[name][str(h)] = {"holdout": {k: part["holdout"].get(k) for k in ("n", "n_eff", "b", "t", "p", "ci95", "r2", "base_rate_pos", "top", "bottom")}, "dev": {k: part["dev"].get(k) for k in ("n", "b", "t", "p")}}
        bench[fund] = rows
    results["benchmarks"] = bench

    # ------------------------------------------------------------------ C1 stress check
    stress = {"2008-12-12": ["HYG", "JNK"], "2013-09-05": ["LQD"], "2016-02-11": ["HYG", "JNK"], "2020-03-23": ["LQD", "HYG", "JNK"], "2022-10-20": ["LQD", "HYG", "JNK"], "2025-04-08": ["LQD", "HYG", "JNK"]}
    c1: dict = {"rows": [], "unmatched": {}}
    for date, funds in stress.items():
        stamp = pd.Timestamp(date)
        for fund in funds:
            week = weekly[fund]
            position = week.index.searchsorted(stamp)
            if position >= len(week):
                continue
            row = week.iloc[position]
            near = week.iloc[max(0, position - 2):position + 3]
            depth_rank = float((week["depth126"].dropna() <= row["depth126"]).mean())
            pain_rank = float((week["pain126"].dropna() <= row["pain126"]).mean())
            c1["rows"].append({"trough": date, "fund": fund, "week": str(week.index[position].date()), "pain126": float(row["pain126"]), "pain_rank": pain_rank, "depth126_pct": float(row["depth126"] * 100), "depth_rank": depth_rank, "pain_near_max": float(near["pain126"].max()), "depth_near_rank_max": float((week["depth126"].dropna() <= near["depth126"].max()).mean()), "gap126_pct": float(row["gap126"] * 100), "p1_long_oi": float(row["p1_long_oi"]), "p1_short_oi": float(row["p1_short_oi"]), "pass": bool(row["pain126"] >= 0.75 and depth_rank >= 0.9)})
    for fund in ("LQD", "HYG", "JNK"):
        week = weekly[fund]
        c1["unmatched"][fund] = {"share_of_weeks_nonzero": float((week["unmatched126"] > 0).mean()), "mean_pain": float(week["pain126"].mean()), "base_rate_pain_ge_75": float((week["pain126"] >= 0.75).mean()), "p5_underwater_share": float(week["p5_underwater"].mean())}
    c1["pass_count"] = sum(row["pass"] for row in c1["rows"])
    c1["rows_count"] = len(c1["rows"])
    results["C1"] = c1

    # ------------------------------------------------------------------ C3 detail
    c3: dict = {}
    for fund in PRIMARY + ["JNK", "USIG"]:
        week = weekly[fund]
        if "i5_usd" not in week:
            continue
        hold = week.index > DEV_END
        fund_row: dict = {}
        fit = (week.index >= pd.Timestamp("2008-01-01")) & (week.index <= pd.Timestamp("2016-12-31"))
        for variant in ("usd", "pct"):
            filtered = week[f"filtered_{variant}"]
            move = week["s_impl"].diff()
            slope = float(week[f"i5_{variant}_slope"].iloc[-1])
            row = {"slope": slope, "scale": float(week[f"i5_{variant}_scale"].iloc[-1]), "fit_r2": float(filtered[fit].corr(move[fit]) ** 2), "kept_share_fit": float((filtered[fit] != 0).mean()), "kept_share_holdout": float((filtered[hold] != 0).mean())}
            score = week[f"i5_{variant}"]
            row["corr_with_past26_holdout"] = float(score[hold].corr(week["past26"][hold]))
            row["fwd_corr_26"] = float(score[hold].corr(week["ds26"][hold]))
            row["fwd_corr_26_dev"] = float(score[~hold].corr(week["ds26"][~hold]))
            row["benchmark_fwd_corr_26"] = float(week["past26"][hold].corr(week["ds26"][hold]))
            row["benchmark_fwd_corr_26_dev"] = float(week["past26"][~hold].corr(week["ds26"][~hold]))
            joined = pd.DataFrame({"y": week["ds26"], "i5": score, "past": week["past26"]})[hold].dropna()
            table = newey_west_ols(joined["y"], (joined[["i5", "past"]] - joined[["i5", "past"]].mean()) / joined[["i5", "past"]].std(), nw_lag(26))
            row["nested_t_i5"] = float(table.loc["i5", "t"])
            row["nested_t_past"] = float(table.loc["past", "t"])
            level = week["s_impl"]
            signal = week[f"i5_{variant}_signal"]
            row["hits_holdout"] = forward_stats(level[hold], signal[hold], 26)
            row["hits_dev"] = forward_stats(level[~hold], signal[~hold], 26)
            dev_sd = week["s_impl"].diff()[week.index <= DEV_END].std()
            plain = week["past26"] / (dev_sd * math.sqrt(26))
            plain_signal = pd.Series(np.where(plain > 0.25, 1.0, np.where(plain < -0.25, -1.0, 0.0)), index=week.index).where(plain.notna())
            row["benchmark_hits_holdout"] = forward_stats(level[hold], plain_signal[hold], 26)
            pos_lift = row["hits_holdout"]["pos_hit"] - row["hits_holdout"]["uncond_rally"]
            neg_lift = row["hits_holdout"]["neg_hit"] - (1.0 - row["hits_holdout"]["uncond_rally"])
            row["lift_pos_pts"], row["lift_neg_pts"] = float(pos_lift * 100), float(neg_lift * 100)
            row["pass_rule_extra"] = bool(abs(row["fwd_corr_26"]) > abs(row["benchmark_fwd_corr_26"]) and abs(row["nested_t_i5"]) > 2 and pos_lift >= 0.05 and neg_lift >= 0.05)
            fund_row[variant] = row
        c3[fund] = fund_row
    results["C3"] = c3

    # ------------------------------------------------------------------ C5 detail
    c5: dict = {"p1_vs_true": {t: facts[t].get("p1_vs_short_interest") for t in ("LQD", "HYG", "JNK", "USIG", "IGIB", "USHY") if t in facts}}
    c5["levels"] = {}
    for fund in ("LQD", "HYG", "JNK", "USIG", "IGSB", "USHY"):
        si = short.get(fund)
        if si is None or si.empty:
            continue
        c5["levels"][fund] = {"first": str(si.index[0].date()), "last": str(si.index[-1].date()), "rows": int(len(si)), "median_si_over_so_pct": float((si["si"] / si["so"]).median() * 100), "max_si_over_so_pct": float((si["si"] / si["so"]).max() * 100), "last_si_over_so_pct": float((si["si"] / si["so"]).iloc[-1] * 100)}
    c5["p1_rule"] = {t: bool(v and v.get("spearman_short", 0) >= 0.3 and v.get("sign_agree_short", 0) >= 0.6) for t, v in c5["p1_vs_true"].items()}
    c5["options"] = {"alpha_vantage": "HISTORICAL_OPTIONS answers 'premium endpoint' on this key. HISTORICAL_PUT_CALL_RATIO answers, one call per date, with no open interest and no delta.",
                     "databento_quote_usd": databento_quote()}
    results["C5"] = c5

    # ------------------------------------------------------------------ C6
    c6: dict = {"pairs": {}, "summary": {}}
    for label, a, b in (("LQD_vs_HYG", "LQD", "HYG"), ("LQD_vs_USIG", "LQD", "USIG"), ("HYG_vs_JNK", "HYG", "JNK")):
        rows = {}
        for name in SIGNALS:
            dev_end = SI_DEV_END if name in C5 else DEV_END
            if name not in weekly[a] or name not in weekly[b]:
                continue
            za, _ = standardise(weekly[a][name], dev_end, name == "i4_rule")
            zb, _ = standardise(weekly[b][name], dev_end, name == "i4_rule")
            for h in HORIZONS:
                vol_a = weekly[a]["xr1"][weekly[a].index <= DEV_END].std() * math.sqrt(h)
                vol_b = weekly[b]["xr1"][weekly[b].index <= DEV_END].std() * math.sqrt(h)
                ya = weekly[a][f"xr{h}"] / vol_a
                yb = weekly[b][f"xr{h}"] / vol_b
                hold_a = ya.index > dev_end
                part = two_equation(ya[hold_a], za[hold_a], yb.reindex(ya.index)[hold_a], zb.reindex(ya.index)[hold_a], h)
                if "p" in part:
                    rows[f"{name}|{h}"] = part
        reject = np.mean([r["p"] < 0.10 for r in rows.values()]) if rows else None
        same = np.mean([r["same_sign"] for r in rows.values()]) if rows else None
        c6["pairs"][label] = rows
        c6["summary"][label] = {"tests": len(rows), "share_not_rejected_10pct": None if reject is None else float(1 - reject), "share_same_sign": None if same is None else float(same),
                                "pool": bool(reject is not None and (1 - reject) >= 0.75 and same >= 0.75)}
    ig, hy = weekly["LQD"], weekly["HYG"]
    both = ig.index.intersection(hy.index)
    mask = both > DEV_END
    c6["correlations_holdout"] = {"xr1": float(ig.loc[both, "xr1"][mask].corr(hy.loc[both, "xr1"][mask])), "xr13": float(ig.loc[both, "xr13"][mask].corr(hy.loc[both, "xr13"][mask])), "flow13": float(ig.loc[both, "flow13"][mask].corr(hy.loc[both, "flow13"][mask])), "pain126": float(ig.loc[both, "pain126"][mask].corr(hy.loc[both, "pain126"][mask])), "weekly_flow": float(np.log(ig.loc[both, "so"]).diff()[mask].corr(np.log(hy.loc[both, "so"]).diff()[mask]))}
    results["C6"] = c6

    # ------------------------------------------------------------------ mechanism checks
    mech: dict = {}
    mech["M1_timing"] = {t: facts[t]["timing"] for t in ("LQD", "HYG", "JNK", "USIG", "IGIB", "IGSB", "USHY") if t in facts}
    m2, m3, m4, m5 = {}, {}, {}, {}
    for fund in ("LQD", "HYG", "JNK"):
        frame = daily[fund]
        offset = facts[fund]["timing"]["offset"]
        data = pd.DataFrame({"flow": frame["flow_pct"] * 100.0, "prem": frame["premium"].shift(offset) * 100.0, "ret": frame["ret_close"].shift(offset) * 100.0, "ret1": frame["ret_close"].shift(offset + 1) * 100.0}).dropna()
        rows = {}
        for sample, part in (("dev", data[data.index <= DEV_END]), ("holdout", data[data.index > DEV_END])):
            table = newey_west_ols(part["flow"], part[["prem", "ret", "ret1"]], 5)
            prem_only = float(part["flow"].corr(part["prem"]) ** 2)
            fitted = table.loc["const", "beta"] + (part[["prem", "ret", "ret1"]] * table["beta"].drop("const")).sum(axis=1)
            rows[sample] = {"r2_premium_only": prem_only, "r2_premium_returns": float(part["flow"].corr(fitted) ** 2), "t_premium": float(table.loc["prem", "t"]), "t_ret": float(table.loc["ret", "t"]), "n": int(len(part))}
        m2[fund] = rows
        ratio = (frame["flow"].abs().groupby(frame.index.year).sum() / frame["volume"].groupby(frame.index.year).sum())
        m3[fund] = {"overall_pct": float(frame["flow"].abs().sum() / frame["volume"].sum() * 100), "holdout_pct": float(frame["flow"].abs()[frame.index > DEV_END].sum() / frame["volume"][frame.index > DEV_END].sum() * 100), "by_year_pct": {str(k): float(v * 100) for k, v in ratio.items() if k >= 2017}, "daily_turnover_median_pct": float(frame["turnover"][frame.index > DEV_END].median() * 100)}
        week = weekly[fund]
        rows = {}
        for sample, mask in (("dev", week.index <= DEV_END), ("holdout", week.index > DEV_END)):
            z = pd.DataFrame({name: standardise(week[name], DEV_END)[0] for name in ("pain126", "flow13", "mom26")})[mask]
            joined = pd.concat([week["fwdflow4"][mask].rename("y"), z], axis=1).dropna()
            table = newey_west_ols(joined["y"], joined[["pain126", "flow13", "mom26"]], nw_lag(4))
            high = joined["y"][week["pain126"].reindex(joined.index) >= 0.75]
            rest = joined["y"][week["pain126"].reindex(joined.index) < 0.75]
            rows[sample] = {"b_pain": float(table.loc["pain126", "beta"]), "t_pain": float(table.loc["pain126", "t"]), "b_mom": float(table.loc["mom26", "beta"]), "t_mom": float(table.loc["mom26", "t"]), "b_flow13": float(table.loc["flow13", "beta"]), "t_flow13": float(table.loc["flow13", "t"]), "fwd_flow4_when_pain_ge_75": float(high.mean()) if len(high) else None, "fwd_flow4_otherwise": float(rest.mean()) if len(rest) else None, "n_high": int(len(high)), "n": int(len(joined))}
        m4[fund] = rows
        month = frame.index.to_period("M")
        rank_from_end = pd.Series(frame.index, index=frame.index).groupby(month).rank(ascending=False)
        for sample, mask in (("all", np.ones(len(frame), dtype=bool)), ("holdout", frame.index > DEV_END)):
            total = frame["flow"].abs()[mask].sum()
            m5.setdefault(fund, {})[sample] = float(frame["flow"].abs()[mask & (rank_from_end.values <= 3)].sum() / total)
        m5[fund]["even_spread"] = 3.0 / 21.0
    mech["M2_flow_on_premium"] = m2
    mech["M3_primary_vs_secondary"] = m3
    mech["M4_pain_predicts_redemptions"] = m4
    mech["M5_month_end_share"] = m5

    # M6 sensitivity of the pain share
    m6: dict = {}
    for fund in ("LQD", "HYG", "JNK"):
        week = weekly[fund]
        hold = week[week.index > DEV_END]
        base = hold["pain126"]
        rows = {}
        for name in ("pain126_fifo", "pain126_low", "pain126_close", "pain126_raw", "pain126_k0"):
            rows[name] = {"corr": float(base.corr(hold[name])), "mean_abs_gap": float((base - hold[name]).abs().mean()), "mean": float(hold[name].mean())}
        rows["base_mean"] = float(base.mean())
        m6[fund] = rows
    book_path = WORK / "book_daily.csv"
    if book_path.exists():
        book = pd.read_csv(book_path, parse_dates=["date"]).drop_duplicates(["symbol", "date"])
        book["half_spread_bp"] = book["spread"] / 2.0 / book["mid"] * 1e4
        entry_check = {}
        for fund in ("LQD", "HYG", "JNK"):
            part = book[book["symbol"] == fund].set_index("date").sort_index()
            frame = daily[fund].reindex(part.index)
            vwap_nav = (part["vwap"] / frame["nav"] - 1.0).dropna() * 1e4
            typical = (frame["high"] + frame["low"] + frame["close"]) / 3.0
            entry_check[fund] = {"days": int(len(part)), "first": str(part.index.min().date()), "last": str(part.index.max().date()), "half_spread_bp_median": float(part["half_spread_bp"].median()), "half_spread_bp_p95": float(part["half_spread_bp"].quantile(0.95)), "vwap_vs_nav_mean_abs_bp": float(vwap_nav.abs().mean()), "vwap_vs_nav_mean_bp": float(vwap_nav.mean()), "vwap_vs_typical_mean_abs_bp": float(((part["vwap"] / typical - 1.0).abs() * 1e4).mean()), "arca_share_of_consolidated_volume": float((part["volume"] / frame["volume"]).median())}
        m6["book_entry_check"] = entry_check
        # I8 second half: aggressor imbalance against the trend signal, on the 2024 run of days.
        i8_rows = {}
        for fund in ("LQD", "HYG"):
            part = book[(book["symbol"] == fund) & (book["date"].dt.year == 2024)].set_index("date").sort_index()
            week = daily[fund]
            from posmon.cta import cta_signal
            signal = cta_signal(week["trc"]).reindex(part.index)
            scaled = part["signed_volume"] / part["volume"]
            proxy = rolling_proxy(scaled, signal, 21).dropna()
            joined = pd.concat([scaled.rename("imb"), signal.rename("sig"), week["ret_close"].reindex(part.index).rename("ret")], axis=1).dropna()
            i8_rows[fund] = {"days": int(len(joined)), "corr_imbalance_signal": float(joined["imb"].corr(joined["sig"])), "corr_imbalance_same_day_return": float(joined["imb"].corr(joined["ret"])), "mean_rolling_corr": float(proxy["correlation"].mean()) if len(proxy) else None, "share_rolling_corr_positive": float((proxy["correlation"] > 0).mean()) if len(proxy) else None, "ci95_slope": block_ci((joined["imb"] - joined["imb"].mean()).values, (joined["sig"] - joined["sig"].mean()).values, 4, rng)}
        mech["I8_imbalance"] = i8_rows
        results["costs"] = {t: {"half_spread_bp": entry_check[t]["half_spread_bp_median"], "hedge_bp_per_side": 1.0, "borrow_pct_year": 0.5 if t == "LQD" else 1.0} for t in entry_check}
    mech["M6_sensitivity"] = m6

    # M7 implied spread against OAS and BAA
    m7: dict = {}
    for fund, group in (("LQD", "IG"), ("USIG", "IG"), ("HYG", "HY"), ("JNK", "HY")):
        week = weekly[fund]
        level = oas[group]
        aligned = level.reindex(level.index.union(week["input_date"])).ffill().reindex(week["input_date"])
        aligned.index = week.index
        move = aligned.diff() * 100.0
        implied = week["s_impl"].diff()
        overlap = week.index >= pd.Timestamp("2023-11-10")
        slope = np.polyfit(implied[overlap].dropna(), move[overlap].reindex(implied[overlap].dropna().index).ffill(), 1)[0]
        row = {"weeks": int(overlap.sum()), "corr_weekly": float(implied[overlap].corr(move[overlap])), "slope_oas_on_implied": float(slope), "mean_weekly_implied": float(implied[overlap].mean()), "mean_weekly_oas": float(move[overlap].mean()), "corr_13w": float(week["s_impl"].diff(13)[overlap].corr(aligned.diff(13)[overlap] * 100.0)), "level_corr": float(week["level"][overlap].corr(aligned[overlap] * 100.0)), "level_mean_gap_bp": float((week["level"][overlap] - aligned[overlap] * 100.0).mean())}
        if group == "IG":
            baa_w = baa.reindex(baa.index.union(week["input_date"])).ffill().reindex(week["input_date"])
            baa_w.index = week.index
            baa_move = baa_w.diff() * 100.0
            row["corr_baa_weekly_holdout"] = float(implied[week.index > DEV_END].corr(baa_move[week.index > DEV_END]))
            row["corr_baa_weekly_dev"] = float(implied[week.index <= DEV_END].corr(baa_move[week.index <= DEV_END]))
            row["corr_baa_oas_weekly"] = float(baa_move[overlap].corr(move[overlap]))
        m7[fund] = row
    mech["M7_implied_vs_oas"] = m7

    # M8 March 2020: closes against NAV
    m8: dict = {}
    for fund in ("LQD", "HYG", "JNK"):
        frame = daily[fund]["2020-02-15":"2020-04-30"]
        week = weekly[fund]
        pos = week.index.searchsorted(pd.Timestamp("2020-03-23"))
        row = week.iloc[pos]
        m8[fund] = {"min_premium_pct": float(frame["premium"].min() * 100), "min_premium_date": str(frame["premium"].idxmin().date()), "max_premium_pct": float(frame["premium"].max() * 100), "pain_nav": float(row["pain126"]), "pain_close": float(row["pain126_close"]), "flow_feb15_mar23_pct": float(np.log(frame["so"]["2020-03-23":].iloc[0] / frame["so"].iloc[0]) * 100), "flow_mar23_apr30_pct": float(np.log(frame["so"].iloc[-1] / frame["so"]["2020-03-23":].iloc[0]) * 100)}
    mech["M8_march_2020"] = m8
    results["mechanisms"] = mech

    # ------------------------------------------------------------------ does the harness work?
    results["harness_checks"] = harness_checks(weekly, rng)

    # ------------------------------------------------------------------ added after results, see plan.md
    results["post_hoc"] = post_hoc(weekly, daily, family, rng)

    # ------------------------------------------------------------------ P4 run, as a description only
    frame = daily["HYG"]["2020-01-01":"2020-12-31"]
    activity = activity_by_price(frame["trn"].round(1), frame["so"], pd.Series(0.0, index=frame.index)).sort_values("longs_net")
    results["P4_example"] = {"fund": "HYG", "year": 2020, "price_buckets": int(len(activity)), "largest_net_add_price": float(activity.index[-1]), "largest_net_add_shares": float(activity["longs_net"].iloc[-1]), "largest_net_cut_price": float(activity.index[0]), "largest_net_cut_shares": float(activity["longs_net"].iloc[0])}

    # ------------------------------------------------------------------ net-of-cost tests
    strategies: dict = {}
    costs = results.get("costs", {})
    for fund in PRIMARY:
        week = weekly[fund]
        hold = week[week.index > DEV_END]
        half = costs.get(fund, {}).get("half_spread_bp", 1.0)
        borrow = costs.get(fund, {}).get("borrow_pct_year", 1.0) / 100.0
        rows = {"buy_hold": strategy_row(pd.Series(1.0, index=hold.index), hold["xr1"], half, borrow)}
        mom = pd.Series(np.sign(week["mom26"]), index=week.index)
        rows["momentum_sign"] = strategy_row(mom[hold.index], hold["xr1"], half, borrow)
        for key, entry in family.items():
            name, owner, h = key.split("|")
            if owner != fund or entry.get("label") not in ("predictive", "suggestive"):
                continue
            dev_end = SI_DEV_END if name in C5 else DEV_END
            z, _ = standardise(week[name], dev_end, name == "i4_rule")
            reference = z[z.index <= dev_end].dropna()
            sign = np.sign(entry["dev"]["b"])
            position = sign * (pd.Series(np.where(z >= reference.quantile(0.8), 1.0, 0.0), index=z.index) - pd.Series(np.where(z <= reference.quantile(0.2), 1.0, 0.0), index=z.index))
            if name == "i4_rule":
                position = sign * z.fillna(0.0)
            sample = hold.index if name not in C5 else hold.index[hold.index > SI_DEV_END]
            rows[f"{name}|h{h}"] = {"label": entry["label"], **strategy_row(position[sample], week["xr1"][sample], half, borrow)}
        strategies[fund] = rows
    results["strategies"] = strategies

    # ------------------------------------------------------------------ CFTC reading
    cftc: dict = {"search": json.loads((RAW / "cftc" / "name_search.json").read_text())}
    readings = {}
    for label, proxy in (("BLOOMBERG_IG_CREDIT", "LQD"), ("BLOOMBERG_HY_CREDIT", "HYG")):
        rows = pd.DataFrame(json.loads((RAW / "cftc" / f"tff_fut_{label}.json").read_text()))
        rows["date"] = pd.to_datetime(rows["report_date_as_yyyy_mm_dd"])
        rows = rows.set_index("date").sort_index()
        numeric = {name: pd.to_numeric(rows[name], errors="coerce") for name in ("open_interest_all", "lev_money_positions_long", "lev_money_positions_short", "asset_mgr_positions_long", "asset_mgr_positions_short", "dealer_positions_long_all", "dealer_positions_short_all")}
        gaps = rows.index.to_series().diff().dt.days
        reading = {"reports": int(len(rows)), "first": str(rows.index[0].date()), "last": str(rows.index[-1].date()), "max_gap_days": int(gaps.max()) if len(rows) > 1 else None, "last_open_interest": float(numeric["open_interest_all"].iloc[-1]), "lev_net_pct_oi": float(net_pct_oi(numeric["lev_money_positions_long"], numeric["lev_money_positions_short"], numeric["open_interest_all"]).iloc[-1]), "am_net_pct_oi": float(net_pct_oi(numeric["asset_mgr_positions_long"], numeric["asset_mgr_positions_short"], numeric["open_interest_all"]).iloc[-1]), "dealer_net_pct_oi": float(net_pct_oi(numeric["dealer_positions_long_all"], numeric["dealer_positions_short_all"], numeric["open_interest_all"]).iloc[-1])}
        close = daily[proxy]["trc"]
        close = close[close.index >= rows.index[0] - pd.Timedelta(days=7)]
        window = min(90, len(close) - 2)
        try:
            pain = cftc_pain(numeric["asset_mgr_positions_long"], close, window=window)
            reading["p2_asset_mgr_long_share_in_pain_on_etf_price"] = float(pain["share_in_pain"].iloc[-1])
            reading["p2_window_days"] = int(window)
        except Exception as error:  # noqa: BLE001
            reading["p2_error"] = str(error)[:120]
        reading["weeks_short_of_i2"] = int(156 - len(rows))
        readings[label] = reading
    cftc["readings"] = readings
    results["CFTC"] = cftc

    # ------------------------------------------------------------------ CRSP: statistics only
    results["CRSP"] = crsp_statistics()
    results["data_log"] = json.loads((RAW / "fetch_log.json").read_text()) if (RAW / "fetch_log.json").exists() else {}
    results["duration_points"] = {t: facts[t].get("duration_points") for t in ("LQD", "HYG", "IGSB", "IGIB", "USIG", "USHY") if t in facts}
    results["baa_check"] = json.loads((WORK / "baa_check.json").read_text()) if (WORK / "baa_check.json").exists() else None
    results["pit_check"] = json.loads((WORK / "pit_check.json").read_text()) if (WORK / "pit_check.json").exists() else None
    (HERE / "results.json").write_text(json.dumps(clean(results), indent=1, allow_nan=False))
    print("family size", len(pvals), "labels", results["label_counts"])


def post_hoc(weekly: dict, daily: dict, family: dict, rng: np.random.Generator) -> dict:
    """Checks chosen after seeing results. They can only weaken a claim, and none of them changes a label."""
    out: dict = {"subperiods": {}, "placebo": {}, "hedge_check": {}, "ledger_coverage": {}}
    periods = {"2017_2021": ("2017-01-01", "2021-12-31"), "2022_2026": ("2022-01-01", "2026-12-31")}
    labelled = [key for key, entry in family.items() if entry.get("label") in ("suggestive", "predictive")]
    extras = [f"level|{f}|{h}" for f in PRIMARY for h in (4, 13, 26)] + [f"mom26|{f}|4" for f in PRIMARY] + [f"pain126|LQD|{h}" for h in (4, 13)]
    for key in labelled + extras:
        name, fund, h = key.split("|")
        h = int(h)
        week = weekly[fund]
        dev_end = SI_DEV_END if name in C5 else DEV_END
        z, _ = standardise(week[name], dev_end, name == "i4_rule")
        y = week[f"xr{h}"]
        rows = {}
        for label, (start, end) in periods.items():
            mask = (week.index >= start) & (week.index <= end) & (week.index > dev_end)
            rows[label] = {k: ols_row(y[mask], z[mask], h).get(k) for k in ("n", "b", "t", "p")}
        no2020 = (week.index > dev_end) & ~((week.index >= "2020-01-15") & (week.index <= "2020-12-31"))
        rows["holdout_excluding_2020"] = {k: ols_row(y[no2020], z[no2020], h).get(k) for k in ("n", "b", "t", "p")}
        full = ols_row(y[week.index > dev_end], z[week.index > dev_end], h)
        rows["holdout"] = {k: full.get(k) for k in ("n", "b", "t", "p", "r2")}
        out["subperiods"][key] = rows

    # Placebo: shift each fund's forward return by one common random offset. Signals stay as they are.
    tests = []
    for key, entry in family.items():
        name, fund, h = key.split("|")
        h = int(h)
        if entry["holdout"].get("b") is None:
            continue
        week = weekly[fund]
        dev_end = SI_DEV_END if name in C5 else DEV_END
        z, _ = standardise(week[name], dev_end, name == "i4_rule")
        hold = week.index > dev_end
        frame = pd.DataFrame({"y": week[f"xr{h}"][hold], "z": z[hold]}).dropna()
        tests.append((frame["y"].values, frame["z"].values, h, entry["holdout"]["p"]))

    def stat(y: np.ndarray, x: np.ndarray, h: int) -> float:
        xd = x - x.mean()
        denominator = (xd * xd).sum()
        if denominator == 0:
            return float("nan")
        b = (xd * y).sum() / denominator
        e = y - y.mean() - b * xd
        u = xd * e
        meat = (u * u).sum()
        lag = nw_lag(h)
        for k in range(1, lag + 1):
            meat += 2.0 * (1.0 - k / (lag + 1.0)) * (u[k:] * u[:-k]).sum()
        return float(b / (math.sqrt(meat) / denominator))

    draws = 400
    counts, minima = [], []
    for _ in range(draws):
        fraction = rng.uniform(0.1, 0.9)
        pvalues = []
        for y, x, h, _ in tests:
            shift = int(fraction * len(y))
            t_value = stat(np.roll(y, shift), x, h)
            pvalues.append(t_p(t_value, len(y), h))
        pvalues = np.array(pvalues)
        counts.append(int((pvalues < 0.05).sum()))
        minima.append(float(np.nanmin(pvalues)))
    observed = [row[3] for row in tests]
    observed_count = int(sum(p < 0.05 for p in observed))
    out["placebo"] = {"draws": draws, "tests": len(tests), "observed_raw_p_below_5pct": observed_count, "placebo_mean_count": float(np.mean(counts)), "placebo_p95_count": float(np.percentile(counts, 95)), "share_placebo_at_least_observed": float(np.mean(np.array(counts) >= observed_count)), "observed_min_p": float(min(observed)), "share_placebo_min_p_below_observed": float(np.mean(np.array(minima) <= min(observed)))}

    # Does the synthetic Treasury hedge look like the issuer's own hedged funds?
    for fund, hedged in (("LQD", "LQDH"), ("HYG", "HYGH")):
        if hedged not in daily:
            continue
        a = daily[fund]["xr_close"]
        b = daily[hedged]["ret_close"]
        both = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
        weekly_both = (1.0 + both).resample("W-FRI").prod() - 1.0
        out["hedge_check"][fund] = {"corr_weekly": float(weekly_both["a"].corr(weekly_both["b"])), "weeks": int(len(weekly_both)), "xr_annual_bp": float(weekly_both["a"].mean() * 52e4), "hedged_fund_annual_bp": float(weekly_both["b"].mean() * 52e4)}

    out["second_side"] = second_side_ledgers(weekly, daily, rng)

    for fund in ("LQD", "HYG", "JNK"):
        week = weekly[fund]
        hold = week[week.index > DEV_END]
        out["ledger_coverage"][fund] = {"median_open_share_of_so": float(hold["open126_share"].median()), "p90_open_share_of_so": float(hold["open126_share"].quantile(0.9)), "weeks_with_no_reading": int(hold["pain126"].isna().sum()), "weeks": int(len(hold)), "i4_rule_share_nonzero": float((hold["i4_rule"] != 0).mean())}
    return out


def second_side_ledgers(weekly: dict, daily: dict, rng: np.random.Generator) -> dict:
    """P2 on FINRA dates: a short ledger on short interest and a gross-long ledger on shares + short interest.

    Each as-of week sees only rows usable by then. The window is 13 FINRA rows, about 126 trading days.
    Short pain: open short lots entered at or below the level. Gross-long pain: open lots entered at or above it.
    These tests sit outside the Holm family because they were added after results.
    """
    from posmon.ledger import RemovalRule, build_ledger

    rows: dict = {}
    for fund in PRIMARY + ["JNK"]:
        si = pd.read_pickle(WORK / f"si_{fund}.pkl")
        frame = daily[fund]
        week = weekly[fund].copy()
        entries = frame["trn"].reindex(frame.index.union(si.index)).ffill().reindex(si.index)
        short_pain, long_pain = [], []
        for stamp, row in week.iterrows():
            part = si[si["usable"] <= row["input_date"]].tail(14)
            level = frame["trn"].get(row["input_date"], np.nan)
            if len(part) < 14 or not np.isfinite(level):
                short_pain.append(np.nan)
                long_pain.append(np.nan)
                continue
            price = entries.reindex(part.index).values[1:]
            short_book = build_ledger(part["si"].diff().values[1:], price, RemovalRule.PRO_RATA)
            long_book = build_ledger((part["si"] + part["so"]).diff().values[1:], price, RemovalRule.PRO_RATA)
            short_total, long_total = short_book.open_total, long_book.open_total
            short_pain.append(short_book.open_below(level) / short_total if short_total > 1e-6 * max(short_book.gross_total, 1.0) else np.nan)
            long_pain.append(long_book.open_above(level) / long_total if long_total > 1e-6 * max(long_book.gross_total, 1.0) else np.nan)
        week["short_pain"], week["gross_long_pain"] = short_pain, long_pain
        hold = week.index > SI_DEV_END
        rows[fund] = {"corr_with_pain126": float(week["gross_long_pain"][hold].corr(week["pain126"][hold]))}
        for name in ("short_pain", "gross_long_pain"):
            z, _ = standardise(week[name], SI_DEV_END)
            for h in HORIZONS:
                part = ols_row(week[f"xr{h}"][hold], z[hold], h)
                dev = ols_row(week[f"xr{h}"][~hold], z[~hold], h)
                rows[fund][f"{name}|{h}"] = {k: part.get(k) for k in ("n", "n_eff", "b", "t", "p")} | {"dev_t": dev.get("t")}
    return rows


def harness_checks(weekly: dict, rng: np.random.Generator) -> dict:
    """Size with random persistent signals, a planted signal the harness must find, and the power floor."""
    out: dict = {"size": {}, "planted": {}, "power_floor": {}}
    threshold = 0.05 / 160
    for fund in PRIMARY:
        week = weekly[fund]
        hold = week[week.index > DEV_END]
        for h in HORIZONS:
            y = hold[f"xr{h}"].dropna()
            rejections = []
            for _ in range(300):
                shocks = rng.standard_normal(len(y))
                z = np.zeros(len(y))
                for i in range(1, len(y)):
                    z[i] = 0.95 * z[i - 1] + shocks[i]
                part = ols_row(y, pd.Series(z, index=y.index), h)
                rejections.append(part["p"] < 0.05)
            df = max(len(y) / h - 2.0, 3.0)
            t_floor = float(st.t.isf(threshold / 2.0, df))
            t_5 = float(st.t.isf(0.025, df))
            out["size"][f"{fund}|{h}"] = float(np.mean(rejections))
            out["power_floor"][f"{fund}|{h}"] = {"n": int(len(y)), "n_eff": round(len(y) / h, 1), "sd_y_bp": float(y.std()), "t_needed_holm": t_floor, "r2_needed_holm": t_floor ** 2 / (t_floor ** 2 + df), "r2_needed_raw_5pct": t_5 ** 2 / (t_5 ** 2 + df), "slope_needed_holm_bp_per_sd": t_floor * float(y.std()) / math.sqrt(len(y) / h)}
            noise = rng.standard_normal(len(week))
            target = week[f"xr{h}"]
            planted = (target.fillna(target.mean()) - target.mean()) / target.std() + 0.5 * pd.Series(noise, index=week.index)
            check = test_signal(week.assign(planted=planted), "planted", h, DEV_END, rng)
            row = check["holdout"]
            out["planted"][f"{fund}|{h}"] = {"t": row["t"], "p": row["p"], "ci95": row["ci95"], "clears_holm": bool(row["p"] < threshold)}
    return out


def databento_quote() -> dict:
    key = os.environ.get("DATABENTO_API_KEY")
    if not key:
        return {"status": "no key"}
    try:
        import databento

        client = databento.Historical(key)
        quote = {}
        for label, schema, start, end in (("one_week_statistics", "statistics", "2024-03-11", "2024-03-16"), ("2018_to_2026_statistics", "statistics", "2018-01-01", "2026-10-01"), ("one_week_definition", "definition", "2024-03-11", "2024-03-16")):
            quote[label] = float(client.metadata.get_cost(dataset="OPRA.PILLAR", stype_in="parent", symbols=["LQD.OPT", "HYG.OPT"], schema=schema, start=start, end=end))
        return quote
    except Exception as error:  # noqa: BLE001
        return {"status": "failed", "error": str(error)[:200]}


def crsp_statistics() -> dict:
    try:
        import marketdb

        con = marketdb.connect(verify=False)
        coverage = con.sql("""SELECT n.ticker, count(*) AS days, min(d.date) AS first, max(d.date) AS last,
                                     sum(CASE WHEN d.shrout <> d.prev THEN 1 ELSE 0 END) AS changes
                              FROM (SELECT permno, date, shrout, lag(shrout) OVER (PARTITION BY permno ORDER BY date) AS prev FROM crsp_daily) d
                              JOIN (SELECT DISTINCT ON (permno) permno, ticker FROM crsp_names ORDER BY permno, nameenddt DESC) n USING (permno)
                              WHERE n.ticker IN ('LQD','HYG','JNK','VCIT','VCSH','TLT','IGSB','IGIB','USIG')
                              GROUP BY 1 ORDER BY 1""").df()
        trace = con.sql("SELECT min(trd_exctn_dt) AS first, max(trd_exctn_dt) AS last FROM trace").df()
        return {"funds": json.loads(coverage.to_json(orient="records", date_format="iso")), "trace": json.loads(trace.to_json(orient="records", date_format="iso")), "note": "Only VCIT and TLT among the credit and rate ETFs asked for, 2019-2021. CRSP cannot feed LQD or HYG on this machine."}
    except Exception as error:  # noqa: BLE001
        return {"status": "failed", "error": str(error)[:200]}


if __name__ == "__main__":
    main()
