"""I4: apply the band form that Goldman's OPI charts reveal: a smoothed centre and an expanding standard deviation.

Grid: centre, sd, burn-in start and end. Exhibit 1 and the printed rates choose. Exhibit 2 stays unfitted.
Writes raw/i4_opi_bands.csv and i4_opi_bands.json.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from i4_search import forward_change, kde, positions
from i4_shape import targets

HERE = Path(__file__).resolve().parent


def z_form(p, centre, sd):
    c = {"ewm13": p.ewm(halflife=13, adjust=True).mean(), "ewm26": p.ewm(halflife=26, adjust=True).mean(), "ewm52": p.ewm(halflife=52, adjust=True).mean(),
         "expanding": p.expanding(26).mean(), "full": pd.Series(p.mean(), index=p.index), "zero": pd.Series(0.0, index=p.index)}[centre]
    s = {"expanding": p.expanding(26).std(), "full": pd.Series(p.std(), index=p.index)}[sd]
    return (p - c) / s


def evaluate(z, change, start, end, g, cur, ties="le"):
    zz = z.loc[start:end].dropna()
    d = change.reindex(zz.index)
    ok = d.notna()
    zz, d = zz[ok], d[ok]
    buy, sell = zz <= -1, zz >= 1
    if buy.sum() < 8 or sell.sum() < 8:
        return None
    k = {"uncond": kde(d.values, g), "buy": kde(d[buy].values, g), "sell": kde(d[sell].values, g)}
    rm = {x: float(np.sqrt(np.mean((k[x] - cur[x]) ** 2))) for x in k}
    rally = d <= 0 if ties == "le" else d < 0
    return {"n": len(d), "n_buy": int(buy.sum()), "n_sell": int(sell.sum()), "base": float(rally.mean()), "buy": float(rally[buy].mean()), "sell": float((d[sell] > 0).mean()),
            "rm_uncond": rm["uncond"], "rm_buy": rm["buy"], "rm_sell": rm["sell"], "rm_cond": float(np.sqrt((rm["buy"] ** 2 + rm["sell"] ** 2) / 2))}


def main():
    pos = positions()
    g1, c1 = targets("ex1")
    g2, c2 = targets("ex2")
    change = forward_change(0)
    starts = ["2006-06-13", "2007-01-02", "2008-01-02", "2009-01-06", "2009-06-02", "2010-01-05"]
    ends = ["2018-01-30", "2018-06-26", "2018-12-18", "2019-01-08"]
    rows = []
    for key, centre, sd, start, end in itertools.product([k for k in pos if k[0] == "spec"], ("ewm13", "ewm26", "ewm52", "expanding", "full", "zero"), ("expanding", "full"), starts, ends):
        r = evaluate(z_form(pos[key], centre, sd), change, start, end, g1, c1)
        if r is None:
            continue
        lev = evaluate(z_form(pos[("lev",) + key[1:]], centre, sd), change, start, end, g2, c2)
        rows.append({"basis": key[1], "contracts": key[2], "weight": key[3], "centre": centre, "sd": sd, "start": start, "end": end, **r,
                     "rate_gap": max(abs(r["base"] - .53), abs(r["buy"] - .63), abs(r["sell"] - .48)),
                     "lev_rm_cond": lev["rm_cond"] if lev else np.nan, "lev_rm_uncond": lev["rm_uncond"] if lev else np.nan})
    f = pd.DataFrame(rows)
    f.to_csv(HERE / "raw" / "i4_opi_bands.csv", index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 30)
    print(len(f), "variants")
    show = ["basis", "contracts", "weight", "centre", "sd", "start", "end", "n", "n_buy", "n_sell", "base", "buy", "sell", "rm_uncond", "rm_cond", "rate_gap", "lev_rm_cond"]
    print(f.sort_values("rm_cond")[show].head(12).round(3).to_string())
    print(f[f.rate_gap < 0.02].sort_values("rm_cond")[show].head(12).round(3).to_string())
    print(f.sort_values("lev_rm_cond")[show].head(5).round(3).to_string())
    print(f.groupby(["centre", "sd"])[["rm_cond", "lev_rm_cond"]].min().round(3).to_string())
    (HERE / "i4_opi_bands.json").write_text(json.dumps({"variants": len(f), "best_shape": f.sort_values("rm_cond").head(5).to_dict("records"),
                                                        "best_rates_with_shape": f[f.rate_gap < 0.02].sort_values("rm_cond").head(5).to_dict("records"),
                                                        "by_form": f.groupby(["centre", "sd"])[["rm_cond", "lev_rm_cond"]].min().reset_index().to_dict("records")}, indent=1, default=float))


if __name__ == "__main__":
    main()
