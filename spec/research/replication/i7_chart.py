"""I7: read Deutsche Bank's Figure 42 (three cumulative-return lines) from the PDF's vector paths.

The lines are stored daily in segments of about 200 points. Axis calibration comes from the tick
labels. Output: raw/i7_chart.csv (local only). Colour map checked against the legend positions.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pdfkit import EVIDENCE, RAW, pymupdf, line_paths, words_in

PDF = EVIDENCE / "local_disk/214-fx-cookbook-a-recipe-for-systematic-investing-in-currency-markets-1.pdf"
PAGE = 28


def read_lines(page, x_lo, x_hi, y_lo, y_hi):
    by_colour = {}
    for colour, width, rect, pts in line_paths(page, min_items=20):
        if rect.x0 >= x_lo - 1 and rect.x1 <= x_hi + 1 and rect.y0 >= y_lo - 1 and rect.y1 <= y_hi + 1:
            by_colour.setdefault(colour, []).append((pts, width))
    return by_colour


def explore():
    doc = pymupdf.open(PDF)
    p = doc[PAGE]
    w = [x for x in p.get_text("words") if x[1] < 340 and x[0] < 300 and x[1] > 150]
    for x in w:
        if any(ch.isdigit() for ch in x[4]) or x[4] in ("Time-series", "Cross-sectional", "Reversal"):
            print(round(x[0], 1), round(x[2], 1), round(x[1], 1), round(x[3], 1), x[4])
    d = read_lines(p, 60, 290, 150, 340)
    for c, v in d.items():
        xy = np.array([q for pts, _ in v for q in pts])
        print(c, len(v), xy.shape, xy[:, 0].min().round(1), xy[:, 0].max().round(1), xy[:, 1].min().round(1), xy[:, 1].max().round(1), xy[0], xy[-1])
    p.get_pixmap(dpi=170, clip=pymupdf.Rect(50, 140, 300, 345)).save(RAW / "i7_fig42.png")


if __name__ == "__main__":
    explore()


def chart_series():
    """Return the three Figure 42 lines as index values on an x-derived business-day calendar."""
    doc = pymupdf.open(PDF)
    p = doc[PAGE]
    d = read_lines(p, 60, 290, 150, 300)
    names = {(0.357, 0.608, 0.835): "ts", (0.754, 0.755, 0.754): "b", (0.267, 0.329, 0.416): "c"}
    # Y axis: label centres 90 at 298.35 and 170 at 188.45.
    y_of = lambda v: 298.35 + (v - 90) * (188.45 - 298.35) / 80.0
    out = {}
    for colour, name in names.items():
        xy = np.array([q for pts, _ in d[colour] for q in pts])
        out[name] = pd.DataFrame({"x": xy[:, 0], "value": 90 + (xy[:, 1] - 298.35) * 80.0 / (188.45 - 298.35)}).drop_duplicates("x", keep="last").sort_values("x")
    return out
