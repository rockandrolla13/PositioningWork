"""I10: how much of Morgan Stanley's UST row can public data rebuild?

Targets: printed UST carry 5.4 and momentum -4.6 on 5 March 2015, and the vector line of the UST overall
signal in Exhibit 2 (158 weekly points, March 2012 to March 2015). Writes i10_results.json.
Public inputs: FRED DGS2, DGS10, TB3MS and NASDAQCOM. Bund, Gilt, JGB, surprises and EM-DM are not rebuilt.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

import cache
from pdfkit import EVIDENCE, line_paths, pymupdf

HERE = Path(__file__).resolve().parent
PDF = EVIDENCE / "drive/positioning/MSBondMarketIndicators.pdf"
NAMES = {(0.898, 0.749, 0.38): "Bunds", (0.071, 0.459, 0.651): "USTs", (0.29, 0.675, 0.42): "UKTs", (0.592, 0.816, 0.867): "JGBs"}


def exhibit2():
    page = pymupdf.open(PDF)[3]
    out = {}
    # Axis: read tick positions from the words: 10 at the top and -10 at the bottom.
    words = {w[4]: (w[1] + w[3]) / 2 for w in page.get_text("words") if w[0] < 80 and w[4] in ("10", "-10", "0")}
    y10, ym10 = words["10"], words["-10"]
    for colour, width, rect, pts in line_paths(page, min_items=30):
        if colour in NAMES:
            xy = np.array(pts)
            out[NAMES[colour]] = {"x": xy[:, 0], "v": 10 - (xy[:, 1] - y10) * 20 / (ym10 - y10)}
    return out


def cap(z):
    return pd.Series(10 * (2 * norm.cdf(z) - 1), index=z.index).where(z.notna())


def expanding_z(s, start="1992-01-01"):
    s = s.loc[start:]
    return (s - s.expanding(52).mean()) / s.expanding(52).std()


def weekly(s, day="W-THU"):
    return s.dropna().asfreq("D").ffill().resample(day).last()


def excess_index(y10, bill, duration=8.0):
    """Excess return of a constant-maturity 10-year note over bills, from yields only. An approximation."""
    dy = y10.diff() / 100
    carry = (y10.shift(1) - bill.shift(1)) / 100 / 52
    return (1 + (-duration * dy + carry)).cumprod()


def main():
    d2, d10 = cache.fred("DGS2"), cache.fred("DGS10")
    bill = weekly(cache.fred("TB3MS"))
    y2w, y10w = weekly(d2), weekly(d10)
    slope = y10w - y2w
    rows = []
    date = pd.Timestamp("2015-03-05")
    # Carry variants: vol measure and z start.
    vols = {"10y weekly chg, 52w": y10w.diff().rolling(52).std() * np.sqrt(52),
            "10y daily chg, 252d": weekly(d10.dropna().diff().rolling(252).std() * np.sqrt(252)),
            "slope weekly chg, 52w": slope.diff().rolling(52).std() * np.sqrt(52),
            "10y weekly abs, 52w": y10w.diff().abs().rolling(52).mean() * np.sqrt(52)}
    for (name, vol), start in itertools.product(vols.items(), ("1992-01-01", "1993-01-01", "1990-01-01", "1980-01-01")):
        z = expanding_z(slope / vol, start)
        rows.append({"variant": name, "z_start": start, "carry": float(cap(z.dropna()).reindex([date], method="ffill").iloc[0])})
    carry = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(carry.round(2).to_string())
    # Momentum: raw value and the scale that the printed -4.6 implies.
    idx = excess_index(y10w, bill.reindex(y10w.index).ffill())
    rows = []
    for span in (4, 6, 8, 9, 13, 17, 18, 26):
        lagged = idx.shift(1)
        raw = (lagged - lagged.shift(1).ewm(span=span, adjust=False).mean()) / idx.diff().abs().shift(1).ewm(span=span, adjust=False).mean()
        val = float(raw.reindex([date], method="ffill").iloc[0])
        target = norm.ppf((-4.6 / 10 + 1) / 2)
        rows.append({"span": span, "raw": val, "implied_scale": target / val})
    mom = pd.DataFrame(rows)
    print(mom.round(3).to_string())
    # Exhibit 2 UST line against what public data can reach.
    e2 = exhibit2()
    ust = e2["USTs"]
    n = len(ust["x"])
    wk = y10w.loc[:"2015-03-05"].index[-n:]
    line = pd.Series(ust["v"], index=wk)
    print("points", n, "first", wk[0].date(), "last value", round(line.iloc[-1], 2), "weeks at zero", int((line.abs() < 0.05).sum()))
    best_vol = vols["10y weekly chg, 52w"]
    fc = cap(expanding_z(slope / best_vol).dropna())
    scale = float(mom[mom.span == 17].implied_scale.iloc[0])
    lagged = idx.shift(1)
    raw = (lagged - lagged.shift(1).ewm(span=17, adjust=False).mean()) / idx.diff().abs().shift(1).ewm(span=17, adjust=False).mean()
    fm = cap((abs(scale) * raw).dropna())
    w5k = weekly(cache.fred("NASDAQCOM"))    # Wilshire left FRED. This is a US-only proxy with no EM-DM leg.
    fe = cap(-expanding_z(np.log(w5k).diff(13)).dropna())
    frame = pd.DataFrame({"line": line, "carry": fc, "momentum": fm, "equity_us_only": fe}).dropna()
    frame["public_mean"] = frame[["carry", "momentum", "equity_us_only"]].mean(axis=1)
    frame["public_x34"] = frame[["carry", "momentum", "equity_us_only"]].sum(axis=1) / 4
    corr = frame.corr()["line"].round(3).to_dict()
    live = frame[frame.line.abs() > 0.05]
    print("corr all", corr)
    print("corr when live", live.corr()["line"].round(3).to_dict(), "n live", len(live))
    # Rule test on all four vector lines, with no data at all. Steps 3 and 4 of the recipe predict two facts.
    grid = pd.DataFrame({k: v["v"] for k, v in e2.items()}).round(2)
    live_cells = grid.abs() > 0.05
    inside_band = int(((grid.abs() <= 1.5) & live_cells).sum().sum())
    alone = 0
    for _, row in grid.iterrows():
        for market, value in row.items():
            if abs(value) > 0.05:
                others = row.drop(market)
                if not ((np.sign(others) == np.sign(value)) & (others.abs() > 0.05)).any():
                    alone += 1
    print("Exhibit 2 cells", grid.size, "live", int(live_cells.sum().sum()), "live but inside the 1.5 band", inside_band, "live with no same-sign partner", alone)
    # Implied residual business-cycle factor: 4 x overall - carry - momentum - equity, on live weeks.
    res = {"carry_variants": carry.to_dict("records"), "printed": {"carry": 5.4, "momentum": -4.6, "equity": 1.7, "business": 4.7},
           "momentum": mom.to_dict("records"), "exhibit2_points": n, "exhibit2_corr_all": corr, "exhibit2_corr_live": live.corr()["line"].to_dict(), "n_live": len(live),
           "carry_rule_value": float(fc.reindex([pd.Timestamp("2015-03-05")], method="ffill").iloc[0]), "equity_us_only_value": float(fe.reindex([pd.Timestamp("2015-03-05")], method="ffill").iloc[0]),
           "variants": len(carry) + len(mom), "exhibit2_cells": int(grid.size), "exhibit2_live": int(live_cells.sum().sum()), "exhibit2_live_inside_band": inside_band, "exhibit2_live_no_partner": alone}
    (HERE / "i10_results.json").write_text(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
