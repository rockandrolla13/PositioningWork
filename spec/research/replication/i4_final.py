"""I4 summary tests. Scale check on the unconditional curve, printed-rate fit inside the shape-pinned sample,
and how many variants reach the printed rates. Writes i4_results.json."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import cache
from i4_search import forward_change, kde, positions, rates
from i4_shape import score, targets

HERE = Path(__file__).resolve().parent


def main():
    out = {}
    g1, c1 = targets("ex1")
    g2, c2 = targets("ex2")
    change = forward_change(0)
    # 1. Does a stretch of the yield change fit better? Exhibit 1's range is wider than Tuesday DGS10 by about 10%.
    rows = []
    for k in np.arange(0.90, 1.21, 0.02):
        for start in ("2006-06-13", "2009-01-01", "2009-06-01", "2010-01-01"):
            for end in ("2018-01-31", "2018-06-30", "2018-12-31"):
                x = (change.loc[start:end].dropna() * k).values
                rows.append({"k": round(k, 2), "start": start, "end": end, "rmse_ex1": float(np.sqrt(np.mean((kde(x, g1) - c1["uncond"]) ** 2))),
                             "rmse_ex2": float(np.sqrt(np.mean((kde(x, g2) - c2["uncond"]) ** 2))), "n": len(x)})
    f = pd.DataFrame(rows).sort_values("rmse_ex1")
    print(f.head(8).round(3).to_string())
    print(f[f.k == 1.0].head(6).round(3).to_string())
    out["uncond_scale_best"] = f.iloc[0].to_dict()
    out["uncond_k1_best"] = f[f.k == 1.0].iloc[0].to_dict()
    # 2. Range facts.
    x = change.loc["2009-06-01":"2018-12-31"].dropna()
    out["chart_range_ex1"] = [-0.934, 0.758]
    out["tuesday_dgs10_range_2009_06"] = [float(x.min()), float(x.max())]
    # 3. Base rate on the pinned sample, ties both ways.
    out["base_rate_pinned"] = {"sample": "2009-06-02 to 2018-01-30", "rally_strict": float((change.loc["2009-06-01":"2018-01-31"].dropna() < 0).mean()),
                               "rally_with_ties": float((change.loc["2009-06-01":"2018-01-31"].dropna() <= 0).mean())}
    # 4. Printed-rate matches inside the pinned sample.
    pos = positions()
    rows = []
    for key, p in pos.items():
        if key[0] != "spec":
            continue
        for start in ("2009-01-01", "2009-06-01", "2010-01-01"):
            for end in ("2018-01-31", "2018-06-30", "2018-12-31"):
                r = score(p, change, start, end, g1, c1)
                if r:
                    rows.append({"basis": key[1], "contracts": key[2], "weight": key[3], "start": start, "end": end, **r,
                                 "rate_gap": max(abs(r["base"] - .53), abs(r["buy"] - .63), abs(r["sell"] - .48))})
    g = pd.DataFrame(rows).sort_values("rate_gap")
    pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)
    print("Inside the pinned sample", len(g))
    print(g.head(10).round(3).to_string())
    out["pinned_grid_size"] = len(g)
    out["pinned_best"] = g.iloc[0].to_dict()
    # 5. Search totals across all scripts, for the overfit warning.
    grid = pd.read_csv(HERE / "raw" / "i4_grid.csv")
    out["grid_rates_total"] = len(grid)
    out["grid_rates_within_1pt"] = int((grid.gap_rates < 0.01).sum())
    out["grid_rates_within_1pt_and_range_ok"] = int(((grid.gap_rates < 0.01) & (grid.gap_range < 0.03)).sum())
    out["grid_rates_within_2pt_and_range_ok"] = int(((grid.gap_rates < 0.02) & (grid.gap_range < 0.03)).sum())
    shape = pd.read_csv(HERE / "raw" / "i4_shape_grid.csv")
    roll = pd.read_csv(HERE / "raw" / "i4_rolling_grid.csv")
    uncond = pd.read_csv(HERE / "raw" / "i4_uncond_grid.csv")
    out["shape_variants"] = len(shape)
    out["rolling_variants"] = len(roll)
    out["uncond_variants"] = len(uncond)
    out["best_uncond_by_dow"] = uncond.sort_values("rmse").groupby("series").head(1).sort_values("rmse")[["series", "start", "end", "rmse", "rally", "rally_le"]].round(3).to_dict("records")
    out["best_cond_rmse_full_sample"] = float(shape.rm_cond.min())
    out["best_cond_rmse_rolling"] = float(roll.rm_cond.min())
    out["best_cond_rmse_lev_full_sample"] = float(shape.lev_rm_cond.min())
    out["best_cond_rmse_lev_rolling"] = float(roll.lev_rm_cond.min())
    (HERE / "i4_results.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({k: out[k] for k in ("grid_rates_total", "grid_rates_within_1pt", "grid_rates_within_1pt_and_range_ok", "grid_rates_within_2pt_and_range_ok", "best_cond_rmse_full_sample", "best_cond_rmse_rolling", "best_cond_rmse_lev_full_sample", "best_cond_rmse_lev_rolling", "base_rate_pinned", "tuesday_dgs10_range_2009_06")}, indent=1))


if __name__ == "__main__":
    main()
