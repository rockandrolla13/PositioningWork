"""I4: test rolling and exponentially weighted bands instead of a full-sample score.

The band choice is scored on Exhibit 1. Exhibit 2 takes the same recipe untouched.
Writes raw/i4_rolling_grid.csv and prints the best rows.
"""
from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np
import pandas as pd

from i4_search import forward_change, kde, positions
from i4_shape import targets

HERE = Path(__file__).resolve().parent


def zscore(pos, kind, n, lag):
    p = pos if not lag else pos
    if kind == "roll":
        mean, sd = p.rolling(n, min_periods=n).mean(), p.rolling(n, min_periods=n).std()
    elif kind == "ewm":
        mean, sd = p.ewm(halflife=n, adjust=False).mean(), p.ewm(halflife=n, adjust=False).std()
    else:
        raise ValueError(kind)
    if lag:
        mean, sd = mean.shift(1), sd.shift(1)
    return (pos - mean) / sd


def score(z, change, start, end, g, cur, multiple=1.0):
    zz = z.loc[start:end].dropna()
    d = change.reindex(zz.index)
    ok = d.notna()
    zz, d = zz[ok], d[ok]
    buy, sell = zz <= -multiple, zz >= multiple
    if buy.sum() < 8 or sell.sum() < 8 or len(d) < 100:
        return None
    k = {"uncond": kde(d.values, g), "buy": kde(d[buy].values, g), "sell": kde(d[sell].values, g)}
    rm = {x: float(np.sqrt(np.mean((k[x] - cur[x]) ** 2))) for x in k}
    return {"n": len(d), "first": zz.index[0].date().isoformat(), "n_buy": int(buy.sum()), "n_sell": int(sell.sum()),
            "base": float((d <= 0).mean()), "buy": float((d[buy] <= 0).mean()), "sell": float((d[sell] > 0).mean()),
            "rm_uncond": rm["uncond"], "rm_buy": rm["buy"], "rm_sell": rm["sell"], "rm_cond": float(np.sqrt((rm["buy"] ** 2 + rm["sell"] ** 2) / 2))}


def main():
    pos = positions()
    g1, c1 = targets("ex1")
    g2, c2 = targets("ex2")
    bands = [("roll", n) for n in (26, 52, 78, 104, 130, 156, 208, 260)] + [("ewm", n) for n in (13, 26, 52, 78, 104, 156)]
    offsets = {"Tue": 0, "Mon_before": -1, "Fri": 3, "Mon_after": 6}
    changes = {k: forward_change(v) for k, v in offsets.items()}
    ends = ["2017-12-31", "2018-06-30", "2018-12-31", "2019-01-17"]
    starts = ["2006-06-13", "2008-12-01", "2009-06-01", "2010-01-01"]
    rows = []
    for key, (kind, n), lag, (oname, change), start, end in itertools.product([k for k in pos if k[0] == "spec"], bands, (False,), changes.items(), starts, ends):
        z = zscore(pos[key], kind, n, lag)
        r = score(z, change, start, end, g1, c1)
        if r is None:
            continue
        lev = score(zscore(pos[("lev",) + key[1:]], kind, n, lag), change, start, end, g2, c2)
        rows.append({"basis": key[1], "contracts": key[2], "weight": key[3], "band": f"{kind}{n}", "obs": oname, "start": start, "end": end, **r,
                     "rate_gap": max(abs(r["base"] - .53), abs(r["buy"] - .63), abs(r["sell"] - .48)),
                     "lev_rm_cond": lev["rm_cond"] if lev else np.nan, "lev_buy": lev["buy"] if lev else np.nan, "lev_sell": lev["sell"] if lev else np.nan})
    frame = pd.DataFrame(rows)
    frame.to_csv(HERE / "raw" / "i4_rolling_grid.csv", index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40)
    print("variants", len(frame))
    print(frame.sort_values("rm_cond").head(25).round(3).to_string())
    print(frame[frame.rate_gap < .02].sort_values("rm_cond").head(15).round(3).to_string())
    print(frame.sort_values("rm_cond").groupby("band").head(1).round(3).to_string())


if __name__ == "__main__":
    main()
