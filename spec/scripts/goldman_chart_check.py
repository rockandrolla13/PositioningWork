"""Compare this build of I5 with the weekly series drawn in Goldman's own PDF charts.

Usage, from the spec directory: python scripts/goldman_chart_check.py PATH_TO_GOLDMAN_PDF
Writes data/goldman_chart_check.json. It stores only comparison statistics, never the chart series.
It needs pymupdf and scipy, and it needs internet access for the CFTC and FRED data.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pymupdf
from scipy.optimize import nnls

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import reconcile_live as rl  # noqa: E402
from posmon.data import fetch_cftc  # noqa: E402

DARK, LIGHT = (0.0, 0.204, 0.373), (0.651, 0.812, 0.929)
# name: page, x range, y range, colour, y calibration, weeks per x point, date of the last point.
# The last dates come from aligning each chart's yield line with DGS10, and the z lines with this build.
CHARTS = {
    "am_6m": (1, (73.2, 276.3), (523.1, 642.1), LIGHT, (642.1, -60, 523.1, 100), 32.85 / 104.36, "2019-04-23"),
    "lev_6m": (1, (335.9, 539.0), (523.1, 642.1), LIGHT, (642.1, -150, 523.1, 150), 32.85 / 104.36, "2019-04-23"),
    "am_z": (2, (69.0, 278.6), (484.5, 600.2), DARK, (600.2, -2.5, 484.5, 2.5), 35.27 / 104.36, "2019-04-30"),
    "spec_z": (2, (327.9, 541.3), (482.6, 597.8), DARK, (597.8, -3, 482.6, 3), 35.98 / 104.36, "2019-04-23"),
}


def read_chart(doc, page, x_range, y_range, colour, y_cal, per_week, last):
    paths = []
    for drawing in doc[page].get_drawings():
        c, r = drawing.get("color"), drawing["rect"]
        if c is None or abs(c[0] - colour[0]) > 0.01 or abs(c[1] - colour[1]) > 0.01 or len(drawing["items"]) < 2:
            continue
        if not (x_range[0] - 1 <= r.x0 and r.x1 <= x_range[1] + 1 and y_range[0] - 3 <= r.y0 and r.y1 <= y_range[1] + 3):
            continue
        points = []
        for item in drawing["items"]:
            if item[0] == "l":
                if not points:
                    points.append((item[1].x, item[1].y))
                points.append((item[2].x, item[2].y))
        if points:
            paths.append(points)
    paths.sort(key=lambda p: p[0][0])
    xy = np.array([p for path in paths for p in path])
    y0, v0, y1, v1 = y_cal
    values = v0 + (xy[:, 1] - y0) * (v1 - v0) / (y1 - y0)
    weeks_back = np.round((xy[-1, 0] - xy[:, 0]) / per_week).astype(int)
    series = pd.Series(values, index=[pd.Timestamp(last) - pd.Timedelta(weeks=int(w)) for w in weeks_back])
    return series[~series.index.duplicated(keep="last")].sort_index()


def corr(a, b):
    common = a.index.intersection(b.dropna().index)
    return float(a.loc[common].corr(b.loc[common]))


def weekly_from_sum(chart, mine, index):
    """Undo the 26-week sum, starting from this build's values for the first 26 weeks."""
    step = chart.reindex(index).diff()
    weekly = pd.Series(np.nan, index=index)
    for i, date in enumerate(index):
        if i >= 26 and pd.notna(step.loc[date]):
            base = weekly.iloc[i - 26] if pd.notna(weekly.iloc[i - 26]) else mine.iloc[i - 26]
            weekly.iloc[i] = step.loc[date] + base
    return weekly


def main():
    doc = pymupdf.open(sys.argv[1])
    chart = {name: read_chart(doc, *spec) for name, spec in CHARTS.items()}
    combined, level = rl.goldman_series("combined")
    futures, _ = rl.goldman_series("futures")
    index = level.index
    out = {
        "lev_corr_combined": corr(chart["lev_6m"], combined["lev"]["filtered"].rolling(26).sum()),
        "lev_corr_futures": corr(chart["lev_6m"], futures["lev"]["filtered"].rolling(26).sum()),
        "am_corr_combined": corr(chart["am_6m"], combined["am_other"]["filtered"].rolling(26).sum()),
        "am_corr_futures": corr(chart["am_6m"], futures["am_other"]["filtered"].rolling(26).sum()),
    }
    for name, key in (("am_z", "am_other"), ("spec_z", "spec")):
        table = combined[key]["table"]
        common = chart[name].index.intersection(table["residual_6m"].dropna().index)
        slope, intercept = np.polyfit(table["residual_6m"].loc[common], chart[name].loc[common], 1)
        out[name] = {"corr": corr(chart[name], table["score"]), "implied_scale": float(1 / slope),
                     "implied_mean": float(-intercept / slope), "rule_scale": float(table["scale"].iloc[0]),
                     "mean_abs_gap": float((chart[name].loc[common] - table["score"].loc[common]).abs().mean())}
    # Fit weights per contract on the rebuilt weekly series. Weights near the real DV01 confirm the build.
    yields = pd.DataFrame({k: rl.fred(v, "2006-01-01", "2019-12-31") for k, v in rl.YIELD.items()}).ffill() * 100.0
    tff = {k: fetch_cftc("tff", c, "2006-01-01", "2019-05-07", basis="combined") for k, c in rl.UST.items()}
    dv01 = rl.dv01_series().reindex(index, method="ffill")
    groups = {"lev": ("lev_6m", lambda t: t.lev_money_long - t.lev_money_short),
              "am_other": ("am_6m", lambda t: t.asset_mgr_long - t.asset_mgr_short + t.other_rept_long - t.other_rept_short)}
    out["weights"] = {}
    for name, (chart_name, net_of) in groups.items():
        cells = {}
        for contract, report in tff.items():
            change = net_of(report).reindex(index).diff()
            move = yields[contract].reindex(index, method="ffill").diff()
            cells[contract] = (change.where(np.sign(change) == -np.sign(move), 0.0).fillna(0.0)) / 1e6
        cells = pd.DataFrame(cells)
        weekly = weekly_from_sum(chart[chart_name], combined[name]["filtered"], index)
        out["weights"][name] = {}
        for start, end in (("2006", "2010"), ("2011", "2015"), ("2016", "2019")):
            mask = weekly.notna() & (index >= start) & (index <= f"{end}-12-31")
            weights, _ = nnls(cells[mask].values, weekly[mask].values)
            fit = cells[mask].values @ weights
            r2 = 1 - ((weekly[mask] - fit) ** 2).sum() / ((weekly[mask] - weekly[mask].mean()) ** 2).sum()
            out["weights"][name][f"{start}-{end}"] = {"r2": float(r2), **dict(zip(cells.columns, map(float, weights)))}
    means = {f"{a}-{b}": dv01.loc[a:f"{b}-12-31"].mean().to_dict() for a, b in (("2006", "2010"), ("2011", "2015"), ("2016", "2019"))}
    out["real_dv01"] = means
    Path("data/goldman_chart_check.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k not in ("weights", "real_dv01")}, indent=1))


if __name__ == "__main__":
    main()
