"""P2 and P3: which formula drew the blue line in the deck's natural gas Pain chart?

The chart is a raster screenshot (models PDF, index page 15). The price line is digitised from the same
image, so no outside futures history is needed for the back half of the chart.
Writes p2_results.json. Digitised series stay in raw/.
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

import cache
from pdfkit import EVIDENCE, pymupdf
from posmon.ledger import RemovalRule, build_ledger
from posmon.pain import _share_in_pain, _survival_share, harmonise_weekly, legacy_cftc_open_position

HERE = Path(__file__).resolve().parent
X0, X1 = 248, 815
Y_ZERO, Y_ONE = 604.0, 280.0     # right axis: 0.00 and 1.00. Price axis: 1.50 and 4.00 on the same rows.


def chart_image():
    """Extract the screenshot from the models PDF once. The crop holds no recipient text."""
    path = HERE / "raw" / "p2_ng_chart.png"
    if not path.exists():
        doc = pymupdf.open(EVIDENCE / "gmail/05_portfoliostrat_code_2020/attachments/available_models__a22bb46b.pdf")
        info = [i for i in doc[15].get_image_info(xrefs=True) if i["width"] == 1600][0]
        path.write_bytes(doc.extract_image(info["xref"])["image"])
    return path


def digitise():
    a = np.asarray(Image.open(chart_image()).convert("RGB")).astype(int)
    rows = []
    for x in range(X0, X1 + 1):
        col = a[205:606, x]
        r, g, b = col[:, 0], col[:, 1], col[:, 2]
        blue = (b > 180) & (r < 70) & (g > 60) & (g < 170)
        orange = (r > 200) & (g > 120) & (g < 200) & (b < 110)
        ys_b, ys_o = np.where(blue)[0] + 205, np.where(orange)[0] + 205
        rows.append({"x": x, "b_top": ys_b.min() if len(ys_b) else np.nan, "b_bot": ys_b.max() if len(ys_b) else np.nan,
                     "o_mid": ys_o.mean() if len(ys_o) else np.nan, "o_n": len(ys_o)})
    f = pd.DataFrame(rows).set_index("x")
    to_val = lambda y: (Y_ZERO - y) / (Y_ZERO - Y_ONE)
    f["b_hi"], f["b_lo"] = to_val(f.b_top), to_val(f.b_bot)
    f["price"] = 1.5 + (Y_ZERO - f.o_mid) * 2.5 / (Y_ZERO - Y_ONE)
    return f


def align(f, spot):
    """Map columns to trading days, ending at 30 Jan 2018, choosing the first date by fit to spot."""
    days = spot.loc[:"2018-01-30"].index
    best = None
    for n in range(440, 560):
        d = days[-n:]
        pos = np.round(np.linspace(0, n - 1, len(f))).astype(int)
        price = pd.Series(f.price.values, index=d[pos])
        price = price[~price.index.duplicated(keep="last")].dropna()
        c = price.corr(spot.reindex(price.index))
        if best is None or c > best[0]:
            best = (c, n, d[0])
    return best


def series(f, n, days):
    d = days[-n:]
    pos = np.round(np.linspace(0, n - 1, len(f))).astype(int)
    out = f.copy()
    out["date"] = d[pos]
    return out.groupby("date").agg(b_hi=("b_hi", "max"), b_lo=("b_lo", "min"), price=("price", "mean"))


def candidates(position, close, window):
    """All formula variants for one window, on the same lots."""
    daily = harmonise_weekly(position, close.index)
    frame = pd.DataFrame({"close": close, "change": daily.diff()}).dropna()
    out = {}
    fifo = getattr(RemovalRule, "FIFO", None)
    rows = []
    for end in range(window, len(frame) + 1):
        part = frame.iloc[end - window:end]
        level = float(part.close.iloc[-1])
        row = {"date": part.index[-1]}
        for name, rule in (("pro_rata", RemovalRule.PRO_RATA), ("fifo", fifo)):
            if rule is None:
                continue
            book = build_ledger(part.change.values, part.close.values, rule, part.index)
            row[f"share_{name}"] = _share_in_pain(book, level, "long")
            row[f"survival_{name}"] = _survival_share(book, level, "long")
        rows.append(row)
    res = pd.DataFrame(rows).set_index("date")
    res["legacy_pct_open"] = legacy_cftc_open_position("PCT_OPEN", close, position.reindex(close.index.union(position.index)).ffill().reindex(close.index), close, ">=", window)
    return res


def score(c, chart, tol=0.03):
    j = pd.concat([c.rename("value"), chart[["b_hi", "b_lo"]]], axis=1, join="inner").dropna()
    if j.empty:
        return {"n": 0, "inside_band": np.nan, "corr_mid": np.nan, "n_point_cols": 0, "corr_point": None, "mae_point": None, "share_at_1": np.nan, "share_at_0": np.nan, "last": np.nan}
    inside = ((j.iloc[:, 0] <= j.b_hi + tol) & (j.iloc[:, 0] >= j.b_lo - tol)).mean()
    mid = (j.b_hi + j.b_lo) / 2
    wide = j[(j.b_hi - j.b_lo) < 0.08]     # columns where the line is a point, not a vertical stroke
    return {"n": len(j), "inside_band": float(inside), "corr_mid": float(j.iloc[:, 0].corr(mid)), "n_point_cols": len(wide),
            "corr_point": float(wide.iloc[:, 0].corr((wide.b_hi + wide.b_lo) / 2)) if len(wide) > 5 else None,
            "mae_point": float((wide.iloc[:, 0] - (wide.b_hi + wide.b_lo) / 2).abs().mean()) if len(wide) else None,
            "share_at_1": float((j.iloc[:, 0] >= 0.99).mean()), "share_at_0": float((j.iloc[:, 0] <= 0.01).mean()), "last": float(j.iloc[-1, 0])}


def main():
    f = digitise()
    spot = cache.fred("DHHNGSP").dropna()
    c, n, first = align(f, spot)
    print("chart span in trading days", n, "first date", first.date(), "price corr with Henry Hub spot", round(c, 3))
    chart = series(f, n, spot.loc[:"2018-01-30"].index)
    print("chart stats: share of columns touching 1.0:", round(float((chart.b_hi >= 0.97).mean()), 3), "touching 0:", round(float((chart.b_lo <= 0.03).mean()), 3), "last hi/lo", chart.b_hi.iloc[-1], chart.b_lo.iloc[-1], "last price", chart.price.iloc[-1])
    # Price: chart price where available, spot before it.
    px = spot.copy()
    px.loc[chart.index] = chart.price.interpolate().ffill().bfill().values
    px = px.dropna()
    results = []
    for basis, field, window in itertools.product(("futures", "combined"), ("money_mgr_long",), (30, 60, 90, 126, 130)):
        pos = cache.cftc("disaggregated", "023651", basis)[field].loc["2013":"2018-02-01"]
        cands = candidates(pos, px.loc["2013":"2018-01-30"], window)
        for name in cands.columns:
            r = score(cands[name], chart)
            results.append({"basis": basis, "window": window, "formula": name, **r})
    frame = pd.DataFrame(results)
    frame.to_csv(HERE / "raw" / "p2_grid.csv", index=False)
    pd.set_option("display.width", 220)
    print(len(frame), "variants")
    show = ["basis", "window", "formula", "n", "inside_band", "corr_mid", "n_point_cols", "corr_point", "mae_point", "share_at_1", "share_at_0", "last"]
    print(frame.sort_values("inside_band", ascending=False)[show].head(14).round(3).to_string())
    print(frame.sort_values("corr_point", ascending=False)[show].head(6).round(3).to_string())
    print(frame[frame.window == 126][show].round(3).to_string())
    (HERE / "p2_results.json").write_text(json.dumps({"chart_span_days": n, "first_date": first.date().isoformat(), "price_corr_with_spot": c,
                                                      "share_cols_touch_1": float((chart.b_hi >= 0.97).mean()), "share_cols_touch_0": float((chart.b_lo <= 0.03).mean()),
                                                      "variants": len(frame), "rows": results}, indent=1, default=float))


if __name__ == "__main__":
    main()
