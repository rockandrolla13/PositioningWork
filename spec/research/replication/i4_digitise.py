"""Digitise the three kernel-density curves in Goldman's Exhibits 1 and 2 (raster images in the PDF).

Each pixel in the plot area shows a mix of the three translucent fills, so its colour says which
curves lie above it. The top of each fill per column gives that curve's height.
Calibration comes from the axis tick marks in the image. The stored image is flipped vertically.
Output: raw/i4_curves.npz (digitised curves, kept local) and printed checks.
"""
from __future__ import annotations

import io

import numpy as np
from PIL import Image

from pdfkit import EVIDENCE, RAW, pymupdf

PDF = EVIDENCE / "drive/positioning/Options_implied_position_indicator.pdf"
# Bit order: unconditional (1), sell (2), buy (4). Colours read from the image's own palette.
PALETTE = {0: (252, 252, 252), 1: (172, 172, 252), 2: (252, 172, 172), 4: (172, 220, 172),
           3: (196, 116, 172), 5: (116, 164, 172), 6: (164, 164, 116), 7: (132, 124, 116)}


def load(xref):
    data = pymupdf.open(PDF).extract_image(xref)
    return np.asarray(Image.open(io.BytesIO(data["image"])).convert("RGB")).astype(float)[::-1]


def _centres(idx):
    return [float(g.mean()) for g in np.split(idx, np.where(np.diff(idx) > 1)[0] + 1) if len(g)]


def axes(img):
    """Find the axis lines, then the tick marks just outside them (grey level below 215)."""
    grey = img.mean(axis=2)
    row = 200 + int(np.argmax((grey[200:] < 150).sum(axis=1)))
    col = 25 + int(np.argmax((grey[:, 25:70] < 150).sum(axis=0)))
    xt = _centres(np.where(grey[row + 2, col:] < 215)[0] + col)
    yt = _centres(np.where(grey[:row, col - 2] < 215)[0])
    return row, col, xt, yt


def digitise(xref, y_labels=(0.0, 0.5, 1.0, 1.5, 2.0), x_labels=(-1.0, -0.5, 0.0, 0.5)):
    img = load(xref)
    row, col, xt, yt = axes(img)
    xt = [t for t in xt if t > col]
    yt = sorted([t for t in yt if t < row + 1], reverse=True)
    h, w, _ = img.shape
    xfit = np.polyfit(xt[:len(x_labels)], x_labels, 1)
    yfit = np.polyfit(yt[:len(y_labels)], y_labels, 1)
    keys = np.array(list(PALETTE))
    colours = np.array([PALETTE[k] for k in keys], float)
    d2 = ((img[:, :, None, :] - colours[None, None]) ** 2).sum(axis=3)
    label = keys[np.argmin(d2, axis=2)]
    label[d2.min(axis=2) > 700] = 0
    legend_c = int(w * 0.80)
    y_cut = int(np.polyval(np.polyfit(y_labels, yt[:len(y_labels)], 1), 1.0))
    grid = np.array([np.polyval(xfit, c) for c in range(w)])
    curves = {}
    for bit, name in ((1, "uncond"), (2, "sell"), (4, "buy")):
        tops = np.full(w, np.nan)
        for c in range(col + 3, w):
            column = label[:row - 1, c]
            rows = np.where((column & bit) > 0)[0]
            if c >= legend_c:
                rows = rows[rows > y_cut]
            if len(rows):
                # Walk up from the axis. A thin border line can break the run, so allow small gaps.
                runs = np.split(rows, np.where(np.diff(rows) > 30)[0] + 1)
                tops[c] = runs[-1][0]
        curves[name] = np.polyval(yfit, tops)
    return grid, curves, dict(row=row, col=col, xt=xt, yt=yt, xfit=xfit.tolist(), yfit=yfit.tolist())


def stats(grid, curve):
    ok = np.isfinite(curve) & (curve > -0.01)
    x, y = grid[ok], np.maximum(curve[ok], 0)
    area = np.trapezoid(y, x)
    below = np.trapezoid(y[x <= 0], x[x <= 0])
    return {"xmin": float(x.min()), "xmax": float(x.max()), "area": float(area), "share_below_zero": float(below / area),
            "peak": float(y.max()), "peak_x": float(x[np.argmax(y)])}


def main():
    store = {}
    for xref, name in ((61, "ex1"), (59, "ex2")):
        grid, curves, info = digitise(xref)
        print(name, info)
        store[f"{name}_x"] = grid
        for key, value in curves.items():
            store[f"{name}_{key}"] = value
            print(" ", key, {k: round(v, 3) for k, v in stats(grid, value).items()})
    np.savez(RAW / "i4_curves.npz", **store)


if __name__ == "__main__":
    main()
