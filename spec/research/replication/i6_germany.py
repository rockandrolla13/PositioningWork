"""I6: unfitted check of the band recipe on Exhibit 4 (Bunds). Goldman prints k = 1.25 there.

The recipe (exponential centre with half-life 63, expanding sd) came from Exhibit 3 only. Writes i6_germany.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import cache
from pdfkit import EVIDENCE, line_paths, pymupdf

HERE = Path(__file__).resolve().parent
PDF = EVIDENCE / "drive/positioning/Options_implied_position_indicator.pdf"
X0, X1 = 334.2, 539.3


def page_words():
    page = pymupdf.open(PDF)[2]
    ticks = {}
    for w in page.get_text("words"):
        if 315 < w[0] < 332 and 380 < w[1] < 515:
            try:
                value = float(w[4])
            except ValueError:
                continue
            if abs(value) <= 1:     # year labels sit in the same box
                ticks[value] = (w[1] + w[3]) / 2
    return ticks


def read(colour, ticks):
    page = pymupdf.open(PDF)[2]
    a, b = np.polyfit(list(ticks.values()), list(ticks.keys()), 1)
    paths = []
    for c, w, r, p in line_paths(page):
        if max(abs(c[i] - colour[i]) for i in range(3)) < 0.01 and r.x0 >= X0 - 2 and r.x1 <= X1 + 2 and r.y1 < 515:
            paths.append(np.array(p))
    xy = np.vstack(paths)
    return pd.Series(a * xy[:, 1] + b, index=np.round(xy[:, 0], 3)).groupby(level=0).last().sort_index()


def main():
    ticks = page_words()
    print(ticks)
    o, u, l = read((0.0, 0.176, 0.325), ticks), read((0.745, 0.196, 0.196), ticks), read((0.027, 0.522, 0.286), ticks)
    x0, x1 = o.index.min(), o.index.max()
    n = 2300    # A daily grid. Exact dates do not matter here, because the test compares lines with each other.
    grid = x0 + (x1 - x0) * np.arange(n) / (n - 1)
    f = lambda s: pd.Series(np.interp(grid, s.index.values, s.values))
    O, U, L = f(o), f(u), f(l)
    centre, half = (U + L) / 2, (U - L) / 2
    cut = int(n / 9)     # skip the first of nine years
    rows = []
    for h in (21, 42, 63, 84, 126):
        c = O.ewm(halflife=h, adjust=True).mean()
        rows.append({"h": h, "rmse": float(np.sqrt(((c - centre).iloc[cut:] ** 2).mean())), "corr": float(c.iloc[cut:].corr(centre.iloc[cut:]))})
    cen = pd.DataFrame(rows)
    x = O.expanding(20).std().iloc[cut:]
    y = half.iloc[cut:]
    k = float((x * y).sum() / (x * x).sum())
    res = {"centre": rows, "expanding_k_fit": k, "printed_k": 1.25, "corr_half_width": float(x.corr(y)), "rmse_half_width": float(np.sqrt(((k * x - y) ** 2).mean()))}
    alt = {}
    for hh in (63, 126, 252):
        s = O.ewm(halflife=hh, adjust=True).std().iloc[cut:]
        alt[hh] = {"k": float((s * y).sum() / (s * s).sum()), "corr": float(s.corr(y))}
    res["ew_sd_alternatives"] = alt
    print(cen.round(4).to_string())
    print(json.dumps(res, indent=1, default=float)[-600:])
    (HERE / "i6_germany.json").write_text(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
