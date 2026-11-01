"""I6: fit the band recipe on Goldman's own line, and test small timing variants on the printed statistics.

Bands: centre against an exponential mean of the line. Half-width against k times an exponential sd.
Statistics: printed counts 189 and 261, hit rates 64.0% and 73.2%, means +0.10 and -0.12.
Every variant is counted. Writes i6_bands.json.
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
    centre, half = (u + l) / 2, (u - l) / 2
    cut = "2011-01-01"
    rows = []
    for h in (10, 15, 21, 30, 42, 50, 63, 75, 84, 100, 126, 189, 252):
        c = o.ewm(halflife=h, adjust=True).mean()
        rows.append({"h": h, "rmse": float(np.sqrt(((c - centre).loc[cut:] ** 2).mean())), "corr": float(c.loc[cut:].corr(centre.loc[cut:]))})
    cen = pd.DataFrame(rows).sort_values("rmse")
    print("centre\n", cen.head(5).round(4).to_string())
    rows = []
    for h in (10, 15, 21, 30, 42, 50, 63, 75, 84, 100, 126, 189, 252):
        for scale_name, s in (("ew_sd", o.ewm(halflife=h, adjust=True).std()),
                              ("ew_sd_of_change", o.diff().ewm(halflife=h, adjust=True).std() * np.sqrt(h)),
                              ("ew_rms_about_zero", np.sqrt((o ** 2).ewm(halflife=h, adjust=True).mean()))):
            x = s.loc[cut:]
            y = half.loc[cut:]
            k = float((x * y).sum() / (x * x).sum())
            rows.append({"h": h, "scale": scale_name, "k_fit": k, "rmse": float(np.sqrt(((k * x - y) ** 2).mean())), "corr": float(x.corr(y)), "rmse_k085": float(np.sqrt(((0.85 * x - y) ** 2).mean()))})
    wid = pd.DataFrame(rows).sort_values("rmse")
    pd.set_option("display.width", 200)
    print("half-width\n", wid.head(8).round(4).to_string())
    print(wid[(wid.h == 63)].round(4).to_string())
    print("half-width mean", float(half.loc[cut:].mean()), "line sd", float(o.loc[cut:].std()))
    # Longer memories for the half-width, and an expanding sd, at the printed k = 0.85.
    rows = []
    for name, s in [(f"ew_sd_h{h}", o.ewm(halflife=h, adjust=True).std()) for h in (252, 378, 504, 756, 1008)] + [("expanding_sd", o.expanding(20).std()), ("rolling_sd_252", o.rolling(252, min_periods=20).std()), ("rolling_sd_504", o.rolling(504, min_periods=20).std())]:
        x, y = s.loc[cut:], half.loc[cut:]
        k = float((x * y).sum() / (x * x).sum())
        rows.append({"scale": name, "k_fit": k, "rmse": float(np.sqrt(((k * x - y) ** 2).mean())), "rmse_k085": float(np.sqrt(((0.85 * x - y) ** 2).mean())), "corr": float(x.corr(y))})
    longer = pd.DataFrame(rows)
    print(longer.round(4).to_string())
    # Is the half-width a smoothed version of something? Try an exponential mean of |line - centre|.
    dev = (o - centre).abs()
    rows = []
    for h in (21, 42, 63, 84, 126, 252):
        x = dev.ewm(halflife=h, adjust=True).mean().loc[cut:]
        y = half.loc[cut:]
        k = float((x * y).sum() / (x * x).sum())
        rows.append({"h": h, "k_fit": k, "rmse": float(np.sqrt(((k * x - y) ** 2).mean())), "corr": float(x.corr(y))})
    print(pd.DataFrame(rows).round(4).to_string())
    d10 = cache.fred("DGS10").dropna()
    rows = []
    for start, lag, horizon, tol in itertools.product(("2010-01-04", "2010-02-01", "2010-03-01", "2010-04-01", "2010-05-01", "2010-06-01", "2010-07-01", "2011-01-01"), (0, 1), (19, 20, 21, 22), (0.0, 0.0005, 0.001, 0.002)):
        sell = (o > u + tol).shift(lag).fillna(False)
        buy = (o < l - tol).shift(lag).fillna(False)
        ahead = (d10.shift(-horizon) - d10).reindex(o.index)
        mask = ahead.notna() & (o.index >= start)
        s, b = sell & mask, buy & mask
        r = {"start": start, "lag": lag, "horizon": horizon, "tol": tol, "n_sell": int(s.sum()), "n_buy": int(b.sum()), "hit_sell": float((ahead[s] > 0).mean()), "hit_buy": float((ahead[b] < 0).mean()),
             "mean_sell": float(ahead[s].mean()), "mean_buy": float(ahead[b].mean()), "median_sell": float(ahead[s].median()), "median_buy": float(ahead[b].median()), "sd_sell": float(ahead[s].std()), "sd_buy": float(ahead[b].std()),
             "uncond_sell": float((ahead[mask] > 0).mean())}
        r["gap"] = (abs(r["n_sell"] - 189) / 189 + abs(r["n_buy"] - 261) / 261 + abs(r["hit_sell"] - .64) + abs(r["hit_buy"] - .732))
        rows.append(r)
    t = pd.DataFrame(rows).sort_values("gap")
    pd.set_option("display.max_columns", 30); pd.set_option("display.width", 240)
    print(len(t), "variants")
    print(t.head(8).round(3).to_string())
    base = t[(t.start == "2010-01-04") & (t.lag == 0) & (t.horizon == 20) & (t.tol == 0)].iloc[0].to_dict()
    print("base", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in base.items()})
    (HERE / "i6_bands.json").write_text(json.dumps({"centre": cen.to_dict("records"), "half_width": wid.head(20).to_dict("records"), "half_width_h63": wid[wid.h == 63].to_dict("records"), "half_width_longer": longer.to_dict("records"),
                                                    "stats_variants": len(t), "stats_best": t.head(5).to_dict("records"), "stats_base": base}, indent=1, default=float))


if __name__ == "__main__":
    main()
