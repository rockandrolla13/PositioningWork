"""I7: pin the chart's x-to-date map, then inspect carry. Prints a table for each line."""
from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from i7_chart import chart_series
from i7_rebuild import build, load_data, run, sr

HERE = Path(__file__).resolve().parent


def mapped(line, start, end):
    x = line["x"].values
    frac = (x - x.min()) / (x.max() - x.min())
    days = pd.bdate_range(start, end)
    # Business-day positions, because Excel's category axis has no weekend gaps.
    pos = np.clip(np.round(frac * (len(days) - 1)).astype(int), 0, len(days) - 1)
    s = pd.Series(line["value"].values, index=days[pos])
    return s[~s.index.duplicated(keep="last")]


def corr(chart, pnl, freq, cut="1999-06-01"):
    idx = (1 + pnl).cumprod()
    a = np.log(chart.resample(freq).last()).diff()
    b = np.log(idx.resample(freq).last()).diff()
    j = pd.concat([a, b], axis=1, keys=["a", "b"]).dropna().loc[cut:]
    return float(j.a.corr(j.b))


def main():
    data = load_data()
    pickle.dump(data, open(HERE / "raw" / "i7_data.pkl", "wb"))
    lines = chart_series()
    spot = data["spot"]
    pnl = {"ts": run(build("ts", data, returns=spot), spot, 6)[0], "b": run(build("cs", data, returns=spot), spot, 6)[0], "c": run(build("rev", data, returns=spot), spot, 6)[0]}
    rows = []
    for start in pd.date_range("1992-04-01", "1993-04-01", freq="14D"):
        for end in pd.date_range("2018-07-01", "2019-01-15", freq="14D"):
            rows.append({"start": start, "end": end, **{k: corr(mapped(lines[k], start, end), pnl[k], "W-FRI") for k in pnl}})
    f = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    for k in pnl:
        print(k, f.sort_values(k, ascending=False).head(3).round(3).to_string())
    f["avg"] = f[["ts", "b", "c"]].mean(axis=1)
    print(f.sort_values("avg", ascending=False).head(5).round(3).to_string())
    best = f.sort_values("avg", ascending=False).iloc[0]
    # Finer search around the best.
    rows = []
    for start in pd.date_range(best.start - pd.Timedelta(days=16), best.start + pd.Timedelta(days=16), freq="2D"):
        for end in pd.date_range(best.end - pd.Timedelta(days=16), best.end + pd.Timedelta(days=16), freq="2D"):
            rows.append({"start": start, "end": end, **{k: corr(mapped(lines[k], start, end), pnl[k], "W-FRI") for k in pnl}})
    g = pd.DataFrame(rows)
    g["avg"] = g[["ts", "b", "c"]].mean(axis=1)
    print(g.sort_values("avg", ascending=False).head(5).round(3).to_string())
    best = g.sort_values("avg", ascending=False).iloc[0]
    print("best", best.start.date(), best.end.date())
    for k in pnl:
        m = mapped(lines[k], best.start, best.end)
        print(k, {freq: round(corr(m, pnl[k], freq), 3) for freq in ("W-FRI", "ME", "QE")}, "SR", round(sr(pnl[k]), 3),
              "chart SR 1999+", round(float(np.log(m.resample("W-FRI").last()).diff().loc["1999-06":].mean() / np.log(m.resample("W-FRI").last()).diff().loc["1999-06":].std() * np.sqrt(52)), 3),
              "vol chart", round(float(np.log(m.resample("W-FRI").last()).diff().loc["1999-06":].std() * np.sqrt(52)), 4), "vol mine", round(float(pnl[k].loc["1999-06":].std() * np.sqrt(252)), 4))
    carry = data["carry"]
    print("carry annualised, mean by decade, %")
    print((carry * 252 * 100).groupby(carry.index.year // 5 * 5).mean().round(2).to_string())


if __name__ == "__main__":
    main()
