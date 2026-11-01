#!/usr/bin/env python3
"""Why do LQD signals look strong against BAA10Y but not against excess return? Added after results.

Writes work/baa_check.json. 03_run_tests.py copies it into results.json.
"""
from __future__ import annotations

import importlib.util
import json
import math

import numpy as np
import pandas as pd

from common import HERE, WORK, holm, load_fred

spec = importlib.util.spec_from_file_location("run_tests", HERE / "03_run_tests.py")
tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tests)
DEV_END = tests.DEV_END
SI_DEV_END = tests.SI_DEV_END
HORIZONS = tests.HORIZONS
C5 = tests.C5

baa = load_fred("BAA10Y")
oas = load_fred("BAMLC0A0CM")
week = pd.read_pickle(WORK / "weekly_LQD.pkl")
week["i4_rule"] = np.nan
flow = week["cs01_flow13"]
dev = flow[flow.index <= DEV_END].dropna()
score = (flow - dev.mean()) / dev.std()
week["i4_rule"] = pd.Series(np.where(score <= -1.0, 1.0, np.where(score >= 1.0, -1.0, 0.0)), index=week.index).where(score.notna())


def level_at(series: pd.Series, index: pd.DatetimeIndex) -> pd.Series:
    clean = series.dropna()
    return clean.reindex(clean.index.union(index)).ffill(limit=10).reindex(index)


level = level_at(baa, week.index)
treasury = level_at(load_fred("DGS10"), week.index)
hold = week.index > DEV_END
out: dict = {}

# 1. Is BAA10Y slow? Its weekly changes should not be forecast by last week's ETF-implied move.
move = level.diff() * 100.0
implied = week["s_impl"].diff()
frame = pd.DataFrame({"baa_next": move.shift(-1), "baa_now": move, "implied_now": implied})[hold].dropna()
oas_level = level_at(oas, week.index)
oas_move = oas_level.diff() * 100.0
window = week.index >= pd.Timestamp("2023-11-10")
table = tests.newey_west_ols(frame["baa_next"], frame[["implied_now"]], 4)
out["staleness"] = {"baa_weekly_autocorr": float(frame["baa_next"].corr(frame["baa_now"])), "implied_weekly_autocorr": float(implied[hold].corr(implied[hold].shift(1))), "t_baa_next_on_implied_now": float(table.loc["implied_now", "t"]), "oas_weekly_autocorr": float(oas_move[window].corr(oas_move[window].shift(1))),
                    "implied_leads_baa_corr": float(frame["baa_next"].corr(frame["implied_now"])), "baa_leads_implied_corr": float(move[hold].corr(implied[hold].shift(-1)))}

# 2. Every LQD cell on BAA10Y, then with last week's implied move as a control, then skipping a week, then without 2020.
rows = {}
pvalues = {}
for name in tests.SIGNALS:
    dev_end = SI_DEV_END if name in C5 else DEV_END
    z, _ = tests.standardise(week[name], dev_end, name == "i4_rule")
    mask = week.index > dev_end
    for h in HORIZONS:
        target = (level.shift(-h) - level) * 100.0
        skip = (level.shift(-h - 1) - level.shift(-1)) * 100.0
        base = tests.ols_row(target[mask], z[mask], h)
        skipped = tests.ols_row(skip[mask], z[mask], h)
        joined = pd.DataFrame({"y": target, "z": z, "past": week["s_impl"].diff(4)})[mask].dropna()
        control = tests.newey_west_ols(joined["y"], joined[["z", "past"]], tests.nw_lag(h))
        ten_year = (treasury.shift(-h) - treasury) * 100.0
        joined10 = pd.DataFrame({"y": target, "z": z, "fwd10": ten_year})[mask].dropna()
        control10 = tests.newey_west_ols(joined10["y"], joined10[["z", "fwd10"]], tests.nw_lag(h))
        no2020 = mask & ~((week.index >= "2020-01-15") & (week.index <= "2020-12-31"))
        base_no2020 = tests.ols_row(target[no2020], z[no2020], h)
        key = f"{name}|{h}"
        rows[key] = {"t": base["t"], "p": base["p"], "t_skip_one_week": skipped["t"], "t_with_past_4w_implied": float(control.loc["z", "t"]), "t_with_same_period_10y_change": float(control10.loc["z", "t"]), "t_without_2020": base_no2020["t"]}
        pvalues[key] = base["p"]
adjusted = holm(pvalues)
for key in rows:
    rows[key]["holm_p_within_baa"] = adjusted[key]
values = pd.DataFrame(rows).T
out["cells"] = rows
out["summary"] = {"cells": len(rows), "abs_t_above_2": int((values["t"].abs() > 2).sum()), "abs_t_above_2_skip_week": int((values["t_skip_one_week"].abs() > 2).sum()), "abs_t_above_2_with_control": int((values["t_with_past_4w_implied"].abs() > 2).sum()), "abs_t_above_2_with_10y": int((values["t_with_same_period_10y_change"].abs() > 2).sum()), "abs_t_above_2_without_2020": int((values["t_without_2020"].abs() > 2).sum()), "smallest_holm_p": float(values["holm_p_within_baa"].min())}

# 3. Placebo for the same 76 cells, with the BAA target shifted by a common random offset.
rng = np.random.default_rng(20261102)
cells = []
for name in tests.SIGNALS:
    dev_end = SI_DEV_END if name in C5 else DEV_END
    z, _ = tests.standardise(week[name], dev_end, name == "i4_rule")
    mask = week.index > dev_end
    for h in HORIZONS:
        data = pd.DataFrame({"y": (level.shift(-h) - level) * 100.0, "z": z})[mask].dropna()
        cells.append((data["y"].values, data["z"].values, h))


def t_stat(y: np.ndarray, x: np.ndarray, h: int) -> float:
    xd = x - x.mean()
    denominator = (xd * xd).sum()
    if denominator == 0:
        return float("nan")
    b = (xd * y).sum() / denominator
    u = xd * (y - y.mean() - b * xd)
    meat = (u * u).sum()
    lag = tests.nw_lag(h)
    for k in range(1, lag + 1):
        meat += 2.0 * (1.0 - k / (lag + 1.0)) * (u[k:] * u[:-k]).sum()
    return float(b / (math.sqrt(meat) / denominator))


counts = []
for _ in range(400):
    fraction = rng.uniform(0.1, 0.9)
    counts.append(sum(abs(t_stat(np.roll(y, int(fraction * len(y))), x, h)) > 2 for y, x, h in cells))
out["placebo"] = {"draws": 400, "mean_count": float(np.mean(counts)), "p95_count": float(np.percentile(counts, 95)), "share_at_least_observed": float(np.mean(np.array(counts) >= out["summary"]["abs_t_above_2"]))}

# 4. Other IG funds' flows against BAA10Y, and the same signals against excess return on those funds.
others = {}
for fund in ("USIG", "IGIB", "IGSB"):
    other = pd.read_pickle(WORK / f"weekly_{fund}.pkl")
    z, _ = tests.standardise(other["flow13"], DEV_END)
    mask = other.index > DEV_END
    target_level = level_at(baa, other.index)
    others[fund] = {f"flow13|{h}": tests.ols_row((target_level.shift(-h) - target_level)[mask] * 100.0, z[mask], h)["t"] for h in HORIZONS}
out["other_ig_flow13_on_baa_t"] = others
(WORK / "baa_check.json").write_text(json.dumps(tests.clean(out), indent=1))
print(json.dumps({k: out[k] for k in ("staleness", "summary", "placebo", "other_ig_flow13_on_baa_t")}, indent=1))
for key in ("flow13|1", "flow13|4", "flow13|13", "i7_cont|4", "i4_rule|4", "gap126|1", "i5_usd|4", "gap_turn|1"):
    print(key, {k: round(v, 3) if isinstance(v, float) else v for k, v in rows[key].items()})
