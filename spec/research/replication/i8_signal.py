"""I8: the printed CTA signal needs no tick data, so test it. Printed for 30 October 2023:
TU -1.58, FV -1.69, TY -1.78, US -1.81. Price proxy: minus the matching CMT yield. No futures history is used.
The spec's averaged response is capped near 0.96, so it cannot print -1.78. Writes i8_results.json.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

import cache
from posmon.cta import response, trend_strength

HERE = Path(__file__).resolve().parent
PRINTED = {"TU": -1.58, "FV": -1.69, "TY": -1.78, "US": -1.81}
PAIRS = ((8, 24), (16, 48), (32, 96))
SERIES = {"TU": ["DGS2"], "FV": ["DGS5"], "TY": ["DGS7", "DGS10"], "US": ["DGS20", "DGS30"]}


def signals(price):
    ys = pd.DataFrame({p: trend_strength(price, *p) for p in PAIRS})
    return {"mean_response": response(ys).mean(axis=1), "mean_trend_strength": ys.mean(axis=1),
            "sum_response": response(ys).sum(axis=1), "response_of_mean": response(ys.mean(axis=1))}


def main():
    rows = []
    for dates in ("2023-10-30", "2023-10-27", "2023-10-26", "2023-10-25"):
        for contract, ids in SERIES.items():
            for sid in ids:
                price = -cache.fred(sid).dropna()
                for name, s in signals(price).items():
                    rows.append({"date": dates, "contract": contract, "series": sid, "form": name, "value": float(s.reindex([pd.Timestamp(dates)], method="ffill").iloc[0]), "printed": PRINTED[contract]})
    f = pd.DataFrame(rows)
    f["gap"] = (f.value - f.printed).abs()
    pd.set_option("display.width", 200)
    best = f[f.series.isin(["DGS2", "DGS5", "DGS7", "DGS20"])].pivot_table(index=["date", "form"], columns="contract", values="value")
    best["mae"] = (best[list(PRINTED)] - pd.Series(PRINTED)).abs().mean(axis=1)
    print(best.round(2).sort_values("mae").to_string())
    (HERE / "i8_results.json").write_text(json.dumps({"printed": PRINTED, "rows": rows, "table": best.reset_index().to_dict("records"), "variants": len(best)}, indent=1, default=float))


if __name__ == "__main__":
    main()
