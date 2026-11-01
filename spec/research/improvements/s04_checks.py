"""Leak test: cut every raw input at a date and confirm no signal known by then changes.

Also confirms that the rotation slope matches the panel slope. Writes derived/leak_check.json, which s03_report.py reads.
"""
import json

import numpy as np
import pandas as pd

import lib
import s01_signals as s1
from lib import DERIVED

CUTS = ("2012-06-30", "2019-06-30", "2023-06-30")
SYMBOLS = ("TY", "EC")
FULL = {"cftc": lib.cftc, "fred": lib.fred, "dv01_frame": lib.dv01_frame}


def install(cut):
    stamp = pd.Timestamp(cut)
    lib.cftc = lambda report, basis, symbol: FULL["cftc"](report, basis, symbol).loc[:stamp]
    lib.fred = lambda series: FULL["fred"](series).loc[:stamp]
    lib.dv01_frame = lambda: FULL["dv01_frame"]().loc[:stamp]


def restore():
    for name, function in FULL.items():
        setattr(lib, name, function)


def signal_columns(frame):
    wanted = ("I1", "I2", "I2_lev", "I3_lev", "I3_am", "I4", "past26", "sigma")
    prefixes = ("opt_", "fut_net_oi_", "i5fx_", "share_", "net_share_", "depth_", "net_depth_")
    return [c for c in frame.columns if c in wanted or c.startswith(prefixes)]


def compare(cut, panel):
    tasks = [(sym, group, side, 126, "pro_rata") for sym in SYMBOLS for group in s1.PAIN_FIELDS for side in ("long", "short")]
    install(cut)
    pain = dict(s1.pain_job(task) for task in tasks)
    report = {"max_abs_gap": 0.0, "nan_mismatch": 0, "cells": 0}
    i5_cut = s1.build_i5()
    for symbol in SYMBOLS:
        short = s1.contract_frame(symbol, pain).set_index("date")
        full = panel[panel["contract"] == symbol].set_index("date")
        rows = short.index[short["entry"].notna() & (short["entry"] <= pd.Timestamp(cut))]
        for column in signal_columns(short):
            a, b = short.loc[rows, column].astype(float), full.loc[rows, column].astype(float)
            report["nan_mismatch"] += int((a.isna() != b.isna()).sum())
            both = a.notna() & b.notna()
            report["cells"] += int(both.sum())
            if both.any():
                report["max_abs_gap"] = max(report["max_abs_gap"], float((a[both] - b[both]).abs().max()))
    restore()
    i5_full = s1.build_i5()
    gaps = {}
    for name in i5_full["groups"]:
        a, b = i5_cut["groups"][name]["table"]["score"], i5_full["groups"][name]["table"]["score"]
        common = a.dropna().index
        gaps[name] = float((a.loc[common] - b.loc[common]).abs().max())
    report["i5_score_max_gap"] = gaps
    return report


def main():
    panel = pd.read_pickle(DERIVED / "panel.pkl")
    out = {"cuts": {cut: compare(cut, panel) for cut in CUTS}}
    worst = max(v["max_abs_gap"] for v in out["cuts"].values())
    worst_i5 = max(max(v["i5_score_max_gap"].values()) for v in out["cuts"].values())
    mismatches = sum(v["nan_mismatch"] for v in out["cuts"].values())
    out["passed"] = bool(worst < 1e-8 and worst_i5 < 1e-8 and mismatches == 0)
    frame = panel[(panel["market"] == "UST") & (panel["date"] >= lib.HOLD_START)]
    frame = frame.dropna(subset=["I1", "I2", "I3_lev", "I3_am", "I4", "y13"])
    direct = lib.panel_test(frame, "y13", "I3_lev", 13, draws=100)["beta"]
    wide_x = frame.pivot(index="date", columns="contract", values="I3_lev")
    wide_y = frame.pivot(index="date", columns="contract", values="y13").reindex_like(wide_x)
    mask = wide_x.notna().values & wide_y.notna().values
    a = wide_x.values - np.nanmean(np.where(mask, wide_x.values, np.nan), axis=0)
    b = wide_y.values - np.nanmean(np.where(mask, wide_y.values, np.nan), axis=0)
    a, b = np.where(mask, a, 0.0), np.where(mask, b, 0.0)
    by_hand = float((a * b).sum() / (a * a).sum() * a[mask].std())
    out["rotation_slope_check"] = {"panel_test": float(direct), "by_hand": by_hand}
    (DERIVED / "leak_check.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    if not out["passed"]:
        raise SystemExit("leak check failed")


if __name__ == "__main__":
    main()
