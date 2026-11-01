"""I7: the 21-day volatility window was picked on one number, the 1W turnover. The other three bars test it.

Also runs the reversal and cross-sectional books for reference. Writes i7_vol21.json.
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from i7_align import corr, mapped
from i7_chart import chart_series
from i7_rebuild import build, run, sr
from i7_tranche import END, LINE, PRINTED, START, blue_bars

HERE = Path(__file__).resolve().parent


def main():
    data = pickle.load(open(HERE / "raw" / "i7_data.pkl", "rb"))
    lines = chart_series()
    chart = mapped(lines["ts"], START, END)
    total = data["total"]
    gross = blue_bars()["ts"]
    rows = []
    w = build("ts", data, returns=total, vol_days=21)
    for n, name in ((1, "1W"), (2, "2W"), (4, "1M"), (13, "3M")):
        pnl, turn = run(w.rolling(n, min_periods=1).mean(), total, 6)
        pnl99 = pnl.loc["1999-06":"2018"]
        cost = 0.0
        rows.append({"window": name, "corr_w": corr(chart, pnl, "W-FRI"), "corr_m": corr(chart, pnl, "ME"), "corr_q": corr(chart, pnl, "QE"), "gross_sharpe_1999": sr(pnl),
                     "printed_gross": gross[name], "printed_net": PRINTED["ts"][name][0], "turn_week_pct": float(turn.loc["1999-06":"2018"].mean() * 5 * 100), "printed_turn": PRINTED["ts"][name][1],
                     "vol_1999": float(pnl99.std() * np.sqrt(252))})
    f = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(f.round(3).to_string())
    (HERE / "i7_vol21.json").write_text(json.dumps({"rows": rows, "chart_vol_1999": 0.0494, "chart_sharpe_1999": 0.352}, indent=1, default=float))


if __name__ == "__main__":
    main()
