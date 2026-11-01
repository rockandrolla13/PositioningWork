"""Shared helpers for reading bank PDFs. Text passes through a filter that drops recipient lines.

Nothing here prints or stores a recipient name or an "exclusive use" line.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import pymupdf

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "evidence"
HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"

_BLOCK = re.compile(r"exclusive|prepared for|for the use of|@[a-z0-9.-]+\.[a-z]{2,}|downloaded by|this copy|"
                    r"licensed to|delivered to|sent to|recipient", re.I)


def safe_text(page) -> str:
    """Page text with any line that may name a recipient removed."""
    return "\n".join(line for line in page.get_text().splitlines() if not _BLOCK.search(line))


def line_paths(page, min_items=1):
    """Every stroked path on a page as (colour, width, rect, [(x, y), ...])."""
    out = []
    for d in page.get_drawings():
        if d.get("color") is None:
            continue
        pts = []
        for item in d["items"]:
            if item[0] == "l":
                if not pts or (pts[-1][0] != item[1].x or pts[-1][1] != item[1].y):
                    pts.append((item[1].x, item[1].y))
                pts.append((item[2].x, item[2].y))
            elif item[0] == "c":
                if not pts:
                    pts.append((item[1].x, item[1].y))
                pts.append((item[4].x, item[4].y))
        if len(pts) >= min_items:
            out.append((tuple(round(c, 3) for c in d["color"]), d.get("width"), d["rect"], pts))
    return out


def fill_rects(page):
    """Every filled path as (colour, rect). Bar charts are usually these."""
    out = []
    for d in page.get_drawings():
        if d.get("fill") is not None:
            out.append((tuple(round(c, 3) for c in d["fill"]), d["rect"], len(d["items"])))
    return out


def page_summary(page):
    """Counts of stroked paths by colour, so a chart can be found before reading it."""
    rows = []
    for colour, width, rect, pts in line_paths(page):
        rows.append({"colour": colour, "width": round(width or 0, 2), "n": len(pts), "x0": round(rect.x0, 1), "x1": round(rect.x1, 1),
                     "y0": round(rect.y0, 1), "y1": round(rect.y1, 1)})
    return pd.DataFrame(rows)


def words_in(page, x0, y0, x1, y1):
    """Words inside a box, as (x_mid, y_mid, text). For axis labels only."""
    out = []
    for w in page.get_text("words"):
        if x0 <= w[0] and w[2] <= x1 and y0 <= w[1] and w[3] <= y1:
            out.append(((w[0] + w[2]) / 2, (w[1] + w[3]) / 2, w[4]))
    return out
