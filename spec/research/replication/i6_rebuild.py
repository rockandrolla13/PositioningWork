"""I6: rebuild the drawn bands from the drawn line, using only the recipe. Then rerun the printed statistics.

Recipe: centre = exponential mean with half-life 63 days. Half-width = k x expanding sd. k = 0.85 from the report.
Writes i6_rebuild.json.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

import cache
import i6_opi as m

HERE = Path(__file__).resolve().parent


def main():
    o_x, u_x, l_x = m.read((0.0, 0.176, 0.325)), m.read((0.745, 0.196, 0.196)), m.read((0.027, 0.522, 0.286))
    m.X0_DATA, m.X1_DATA = o_x.index.min(), o_x.index.max()
    last = "2019-01-15"
    o, u, l = m.to_dates(o_x, last), m.to_dates(u_x, last), m.to_dates(l_x, last)
    cut = "2011-01-01"
    rows = []
    for lag, adjust in itertools.product((0, 1), (True, False)):
        centre = o.ewm(halflife=63, adjust=adjust).mean().shift(lag)
        sd = o.expanding(20).std().shift(lag)
        bu, bl = centre + 0.85 * sd, centre - 0.85 * sd
        rows.append({"lag": lag, "adjust": adjust, "rmse_upper": float(np.sqrt(((bu - u).loc[cut:] ** 2).mean())), "rmse_lower": float(np.sqrt(((bl - l).loc[cut:] ** 2).mean())),
                     "corr_upper": float(bu.loc[cut:].corr(u.loc[cut:])), "corr_lower": float(bl.loc[cut:].corr(l.loc[cut:]))})
    t = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(t.round(5).to_string())
    d10 = cache.fred("DGS10").dropna()
    centre = o.ewm(halflife=63, adjust=True).mean()
    sd = o.expanding(20).std()
    bu, bl = centre + 0.85 * sd, centre - 0.85 * sd
    stats = []
    for start, lag, horizon in itertools.product(("2010-01-04", "2010-04-01"), (0, 1), (20, 21)):
        sell, buy = (o > bu).shift(lag).fillna(False), (o < bl).shift(lag).fillna(False)
        ahead = (d10.shift(-horizon) - d10).reindex(o.index)
        mask = ahead.notna() & (o.index >= start)
        s, b = sell & mask, buy & mask
        stats.append({"start": start, "lag": lag, "horizon": horizon, "n_sell": int(s.sum()), "n_buy": int(b.sum()), "hit_sell": float((ahead[s] > 0).mean()), "hit_buy": float((ahead[b] < 0).mean()),
                      "hit_all": float(((ahead[s] > 0).sum() + (ahead[b] < 0).sum()) / (s.sum() + b.sum())), "mean_sell": float(ahead[s].mean()), "mean_buy": float(ahead[b].mean()), "median_sell": float(ahead[s].median()), "median_buy": float(ahead[b].median()),
                      "sd_sell": float(ahead[s].std()), "sd_buy": float(ahead[b].std()), "uncond_selloff": float((ahead[mask] > 0).mean())})
    s = pd.DataFrame(stats)
    pd.set_option("display.max_columns", 30); pd.set_option("display.width", 240)
    print(s.round(3).to_string())
    december = o.loc["2018-11-25":"2018-12-24"][(o < bl).loc["2018-11-25":"2018-12-24"]]
    print("rebuilt December buy days", december.index[0].date() if len(december) else None, december.index[-1].date() if len(december) else None, len(december))
    (HERE / "i6_rebuild.json").write_text(json.dumps({"band_match": rows, "stats": stats, "printed": {"n_sell": 189, "n_buy": 261, "hit_sell": 0.640, "hit_buy": 0.732, "hit_all": 0.693, "mean_sell": 0.10, "mean_buy": -0.12, "median_sell": 0.07, "median_buy": -0.13, "sd_sell": 0.24, "sd_buy": 0.20, "uncond_selloff": 0.47},
                                                      "december_first": december.index[0].date().isoformat() if len(december) else None, "december_last": december.index[-1].date().isoformat() if len(december) else None, "printed_december": ["2018-12-04", "2018-12-14"]}, indent=1, default=float))


if __name__ == "__main__":
    main()
