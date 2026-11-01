#!/usr/bin/env python3
"""Point-in-time check: rebuild a fund with data cut off at a past week. Every signal on that week must not change."""
from __future__ import annotations

import importlib.util
import json

import numpy as np
import pandas as pd

from common import HERE, WORK, treasury_curve

spec = importlib.util.spec_from_file_location("build_panel", HERE / "02_build_panel.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

SIGNALS = ["pain126", "gap126", "depth126", "p1_long_oi", "p1_short_oi", "gap_full", "gap_turn", "p5_water", "flow13", "i2_so",
           "i3_flow", "cs01_flow13", "i5_usd", "i5_pct", "i7_cont", "i7_rev", "i8_trend", "mom26", "level", "past26"]
curve = treasury_curve()
out = {}
for fund, stamp in (("LQD", "2020-03-20"), ("HYG", "2022-10-21"), ("JNK", "2018-12-21")):
    full = pd.read_pickle(WORK / f"weekly_{fund}.pkl")
    frame, _ = build.daily_panel(fund, curve)
    offset = build.choose_offset(frame)["offset"]
    cut = frame[frame.index <= pd.Timestamp(stamp)]
    short = build.weekly_panel(cut, fund, offset)
    a, b = full.loc[stamp, SIGNALS].astype(float), short.loc[stamp, SIGNALS].astype(float)
    # The level path is rolled from dated anchors and the duration path steps on dated holdings, so these match.
    gaps = (a - b).abs()
    out[fund] = {"week": stamp, "max_gap": float(np.nanmax(gaps.values)), "signals_checked": int(a.notna().sum()),
                 "worst": str(gaps.idxmax()), "nan_mismatch": int((a.isna() != b.isna()).sum())}
    print(fund, out[fund], flush=True)
(WORK / "pit_check.json").write_text(json.dumps(out, indent=1))
