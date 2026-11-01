"""I4: does a ten-year pull starting 25 November 2008 fit? Tuesday change on that date equals the chart's low.

Writes i4_tenyear.json. Counts every variant. Chooses nothing on Exhibit 2, which stays an unfitted check.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

import cache
from i4_search import forward_change, kde, positions
from i4_shape import score, targets

HERE = Path(__file__).resolve().parent


def main():
    g1, c1 = targets("ex1")
    g2, c2 = targets("ex2")
    change = forward_change(0)
    rows = []
    starts = ["2008-11-25", "2008-12-02", "2009-01-06", "2009-06-02"]
    ends = ["2018-06-26", "2018-09-25", "2018-10-30", "2018-11-27", "2018-12-18", "2019-01-08"]
    for s, e in itertools.product(starts, ends):
        x = change.loc[s:e].dropna()
        rows.append({"start": s, "end": e, "n": len(x), "min": x.min(), "max": x.max(), "rally_strict": float((x < 0).mean()), "rally_le": float((x <= 0).mean()),
                     "rmse_ex1": float(np.sqrt(np.mean((kde(x.values, g1) - c1["uncond"]) ** 2))), "rmse_ex2": float(np.sqrt(np.mean((kde(x.values, g2) - c2["uncond"]) ** 2)))})
    u = pd.DataFrame(rows)
    pd.set_option("display.width", 240); pd.set_option("display.max_columns", 30)
    print(u.round(3).to_string())
    pos = positions()
    rows = []
    for key, s, e in itertools.product([k for k in pos if k[0] == "spec"], starts, ends):
        r = score(pos[key], change, s, e, g1, c1)
        if r is None:
            continue
        lev = score(pos[("lev",) + key[1:]], change, s, e, g2, c2)
        rows.append({"basis": key[1], "contracts": key[2], "weight": key[3], "start": s, "end": e, **r, "rate_gap": max(abs(r["base"] - .53), abs(r["buy"] - .63), abs(r["sell"] - .48)),
                     "lev_rm_cond": lev["rm_cond"] if lev else np.nan})
    g = pd.DataFrame(rows).sort_values("rate_gap")
    print(len(g), "variants")
    print(g.head(10).round(3).to_string())
    print(g.sort_values("rm_cond").head(5).round(3).to_string())
    (HERE / "i4_tenyear.json").write_text(json.dumps({"uncond": u.to_dict("records"), "variants": len(g), "best_by_rates": g.head(5).to_dict("records"), "best_by_shape": g.sort_values("rm_cond").head(3).to_dict("records")}, indent=1, default=float))


if __name__ == "__main__":
    main()
