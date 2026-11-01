"""I4: score position variants on all three digitised curves of Exhibit 1, then test the winner on Exhibit 2.

Exhibit 2 (leveraged funds) plays no part in choosing the recipe. Every variant is counted.
Writes raw/i4_shape_grid.csv. Prints the top rows.
"""
from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np
import pandas as pd

import cache
from i4_search import forward_change, kde, positions

HERE = Path(__file__).resolve().parent


def targets(ex):
    c = np.load(HERE / "raw" / "i4_curves.npz")
    g = c[f"{ex}_x"]
    keep = (np.abs(g) > 0.02) & (g > -0.92) & (g < 0.75)
    return g[keep], {k: np.nan_to_num(np.maximum(c[f"{ex}_{k}"][keep], 0)) for k in ("uncond", "sell", "buy")}


def score(pos, change, start, end, g, cur, ties="le", multiple=1.0):
    s = pos.loc[start:end]
    d = change.reindex(s.index)
    ok = d.notna()
    s, d = s[ok], d[ok]
    z = (s - s.mean()) / s.std()
    buy, sell = z <= -multiple, z >= multiple
    if buy.sum() < 8 or sell.sum() < 8:
        return None
    rally = d <= 0 if ties == "le" else d < 0
    selloff = d > 0
    gaps = {"uncond": kde(d.values, g), "buy": kde(d[buy].values, g), "sell": kde(d[sell].values, g)}
    rm = {k: float(np.sqrt(np.mean((gaps[k] - cur[k]) ** 2))) for k in gaps}
    return {"n": len(d), "n_buy": int(buy.sum()), "n_sell": int(sell.sum()), "base": float(rally.mean()), "buy": float(rally[buy].mean()),
            "sell": float(selloff[sell].mean()), "rm_uncond": rm["uncond"], "rm_buy": rm["buy"], "rm_sell": rm["sell"],
            "rm_cond": float(np.sqrt((rm["buy"] ** 2 + rm["sell"] ** 2) / 2))}


def main():
    pos = positions()
    g1, c1 = targets("ex1")
    g2, c2 = targets("ex2")
    change = forward_change(0)
    starts = [d.date().isoformat() for d in pd.date_range("2006-06-01", "2011-01-01", freq="QS")]
    ends = [d.date().isoformat() for d in pd.date_range("2017-06-30", "2019-01-31", freq="QE")] + ["2019-01-17", "2018-01-31", "2018-02-28", "2018-07-31"]
    rows = []
    specs = [k for k in pos if k[0] == "spec"]
    for key, start, end in itertools.product(specs, starts, ends):
        r = score(pos[key], change, start, end, g1, c1)
        if r is None:
            continue
        lev = score(pos[("lev",) + key[1:]], change, start, end, g2, c2)
        rows.append({"basis": key[1], "contracts": key[2], "weight": key[3], "start": start, "end": end, **r,
                     "rate_gap": max(abs(r["base"] - .53), abs(r["buy"] - .63), abs(r["sell"] - .48)),
                     "lev_rm_cond": lev["rm_cond"] if lev else np.nan, "lev_rm_buy": lev["rm_buy"] if lev else np.nan,
                     "lev_rm_sell": lev["rm_sell"] if lev else np.nan, "lev_base": lev["base"] if lev else np.nan,
                     "lev_buy": lev["buy"] if lev else np.nan, "lev_sell": lev["sell"] if lev else np.nan})
    frame = pd.DataFrame(rows)
    frame.to_csv(HERE / "raw" / "i4_shape_grid.csv", index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40)
    print("variants", len(frame))
    print(frame.sort_values("rm_cond").head(25).round(3).to_string())
    print("Within 1.5 points on all three rates, best shape:")
    print(frame[frame.rate_gap < 0.015].sort_values("rm_cond").head(15).round(3).to_string())
    print("Best shape per contract set and basis:")
    print(frame.sort_values("rm_cond").groupby(["basis", "contracts", "weight"]).head(1).sort_values("rm_cond").round(3).to_string())


if __name__ == "__main__":
    main()
