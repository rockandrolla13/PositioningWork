"""I4: search assumptions one at a time against Goldman's printed rates and digitised densities.

Fitted target: Exhibit 1 (specs). Unfitted check: Exhibit 2 (leveraged funds), which has no printed rates
and takes the same recipe with no further tuning. Writes raw/i4_grid.csv and i4_results.json.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

import cache

HERE = Path(__file__).resolve().parent
UST = {"TU": "042601", "FV": "044601", "TY": "043602", "TN": "043607", "US": "020601", "WN": "020604"}
FIXED = {"TU": 38.0, "FV": 45.0, "TY": 65.0, "TN": 90.0, "US": 140.0, "WN": 220.0}
CONTRACTS = {"TY": ("TY",), "TY+TN": ("TY", "TN"), "4": ("TU", "FV", "TY", "US"), "5": ("TU", "FV", "TY", "US", "WN"),
             "6": ("TU", "FV", "TY", "TN", "US", "WN")}


def bw_nrd0(x):
    sd = np.std(x, ddof=1)
    iqr = np.subtract(*np.percentile(x, [75, 25]))
    lo = min(sd, iqr / 1.34) or sd or 1.0
    return 0.9 * lo * len(x) ** -0.2


def kde(x, grid):
    h = bw_nrd0(x)
    z = (grid[:, None] - x[None, :]) / h
    return np.exp(-0.5 * z * z).sum(axis=1) / (len(x) * h * np.sqrt(2 * np.pi))


def positions():
    """Net position in $mm per bp, or plain contracts, per (group, basis, contract set, weight)."""
    dv = cache.dv01()
    out = {}
    for basis in ("futures", "combined"):
        for group, report, net_of in (("spec", "legacy", lambda t: t.noncomm_long - t.noncomm_short),
                                      ("lev", "tff", lambda t: t.lev_money_long - t.lev_money_short)):
            nets = {k: net_of(cache.cftc(report, c, basis)) for k, c in UST.items()}
            for label, members in CONTRACTS.items():
                for weight in ("dv01", "fixed", "contracts"):
                    if label == "TY" and weight == "fixed":
                        continue
                    frame = {}
                    for k in members:
                        if weight == "dv01":
                            w = dv[k].reindex(nets[k].index, method="ffill")
                        elif weight == "fixed":
                            w = FIXED[k]
                        else:
                            w = 1.0 / 1e6
                        frame[k] = nets[k] * w / 1e6 if weight != "contracts" else nets[k] / 1e3
                    # A contract that has not listed adds nothing, so the sum skips it.
                    out[(group, basis, label, weight)] = pd.DataFrame(frame).sum(axis=1, min_count=1).dropna()
    return out


def forward_change(offset_days: int, weeks: int = 4, series: str = "DGS10") -> pd.Series:
    """Yield change over the next `weeks`, read at report date + offset, on a weekly report index."""
    y = cache.fred(series).dropna().asfreq("D").ffill()
    idx = pd.date_range("1995-01-03", "2026-10-27", freq="W-TUE")
    start = y.reindex(idx + pd.Timedelta(days=offset_days)).values
    end = y.reindex(idx + pd.Timedelta(days=offset_days + 7 * weeks)).values
    return pd.Series(end - start, index=idx)


def rates(pos, change, start, end, ties="strict", multiple=1.0, z_window="sample"):
    s = pos.loc[start:end]
    c = change.reindex(s.index)
    keep = c.notna()
    s, c = s[keep], c[keep]
    base = pos if z_window == "history" else s
    z = (s - base.mean()) / base.std()
    buy, sell = z <= -multiple, z >= multiple
    rally = (c < 0) if ties == "strict" else (c <= 0)
    selloff = (c > 0) if ties in ("strict", "le") else (c >= 0)
    return {"n": int(len(c)), "base": float(rally.mean()), "buy": float(rally[buy].mean()) if buy.any() else np.nan,
            "sell": float(selloff[sell].mean()) if sell.any() else np.nan, "n_buy": int(buy.sum()), "n_sell": int(sell.sum()),
            "min": float(c.min()), "max": float(c.max())}, c, buy, sell


def curve_gap(c, mask, grid, curve):
    keep = np.isfinite(curve) & (np.abs(grid) > 0.015) & (curve >= -0.02)
    if mask.sum() < 5:
        return np.nan
    return float(np.sqrt(np.mean((kde(c[mask].values, grid[keep]) - np.maximum(curve[keep], 0)) ** 2)))


def main():
    curves = np.load(HERE / "raw" / "i4_curves.npz")
    pos = positions()
    offsets = {"Mon_before(-1)": -1, "Tue(0)": 0, "Wed(1)": 1, "Thu(2)": 2, "Fri(3)": 3, "Mon_after(6)": 6, "Tue_after(7)": 7}
    changes = {k: forward_change(v) for k, v in offsets.items()}
    starts = ["2006-06-13", "2007-01-01", "2008-01-01", "2008-12-01", "2009-01-01", "2009-06-01", "2010-01-01", "2010-03-01", "2011-01-01"]
    ends = ["2018-06-30", "2018-09-30", "2018-12-31", "2019-01-17"]
    rows = []
    specs = [k for k in pos if k[0] == "spec"]
    for key, (name, change), start, end, ties in itertools.product(specs, changes.items(), starts, ends, ("strict", "le")):
        r, c, buy, sell = rates(pos[key], change, start, end, ties)
        g = curves["ex1_x"]
        rows.append({"basis": key[1], "contracts": key[2], "weight": key[3], "obs": name, "start": start, "end": end, "ties": ties, **r,
                     "gap_rates": max(abs(r["base"] - 0.53), abs(r["buy"] - 0.63), abs(r["sell"] - 0.48)),
                     "gap_range": max(abs(r["min"] + 0.93), abs(r["max"] - 0.76))})
    frame = pd.DataFrame(rows)
    frame.to_csv(HERE / "raw" / "i4_grid.csv", index=False)
    print("variants", len(frame))
    show = ["basis", "contracts", "weight", "obs", "start", "end", "ties", "n", "base", "buy", "sell", "n_buy", "n_sell", "min", "max", "gap_rates", "gap_range"]
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(frame.sort_values("gap_rates")[show].head(25).round(3).to_string())
    print(frame[frame.gap_range < 0.025].sort_values("gap_rates")[show].head(25).round(3).to_string())


if __name__ == "__main__":
    main()
