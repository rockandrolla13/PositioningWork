"""I4: which sample and sampling day reproduce the unconditional curve? This uses no positioning data."""
from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np
import pandas as pd

import cache
from i4_search import kde

HERE = Path(__file__).resolve().parent


def target():
    c = np.load(HERE / "raw" / "i4_curves.npz")
    g1, u1 = c["ex1_x"], c["ex1_uncond"]
    keep = np.isfinite(u1) & (np.abs(g1) > 0.02) & (g1 > -0.92) & (g1 < 0.75)
    return g1[keep], np.maximum(u1[keep], 0)


def main():
    grid, curve = target()
    d = cache.fred("DGS10").dropna()
    s = d.asfreq("D").ffill()
    rows = []
    series = {f"weekly_dow{w}": (s[s.index.dayofweek == w], 4) for w in range(5)}
    series["daily_20d"] = (d, 20)
    series["daily_21d"] = (d, 21)
    series["daily_19d"] = (d, 19)
    series["daily_22d"] = (d, 22)
    series["wavg_fri"] = (cache.fred("WGS10YR").dropna(), 4)
    starts = pd.date_range("2006-06-01", "2012-01-01", freq="MS")
    ends = pd.date_range("2017-06-30", "2019-01-31", freq="ME")
    for name, (y, h) in series.items():
        chg = (y.shift(-h) - y).dropna()
        for start, end in itertools.product(starts, ends):
            x = chg.loc[start:end]
            gap = float(np.sqrt(np.mean((kde(x.values, grid) - curve) ** 2)))
            rows.append({"series": name, "start": start.date().isoformat(), "end": end.date().isoformat(), "n": len(x), "rmse": gap,
                         "min": float(x.min()), "max": float(x.max()), "rally": float((x < 0).mean()), "rally_le": float((x <= 0).mean())})
    frame = pd.DataFrame(rows).sort_values("rmse")
    frame.to_csv(HERE / "raw" / "i4_uncond_grid.csv", index=False)
    pd.set_option("display.width", 200)
    print(len(frame))
    print(frame.head(20).round(3).to_string())
    print(frame.groupby("series").head(2).sort_values("series").round(3).to_string())


if __name__ == "__main__":
    main()
