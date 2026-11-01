"""Print every number report.md quotes, from results.json and the work-folder panels. It reads only and writes nothing."""
from __future__ import annotations

import json

import lib
import pandas as pd


def main() -> None:
    d = json.loads(lib.RESULTS.read_text())
    rows = d["t1_t2"]
    print("family size", d["family"]["size"], "smallest raw", min(d["family"]["raw"].values()), "smallest Holm", min(d["family"]["holm"].values()))
    labels = pd.Series([r["verdict"]["label"] for r in rows + d["t3"]]).value_counts()
    print(labels.to_string())
    beat = 0
    for r in rows:
        h, c = r["hold"], r["hold_controls"]
        if h.get("b") is None:
            continue
        r2 = h.get("r2_within") or 0
        if c.get("t") is not None and abs(c["t"]) > 2 and r2 > (r["bench_past4"].get("r2_within") or 0) and r2 > (r["bench_level"].get("r2_within") or 0):
            beat += 1
            print("beats benchmarks:", r["signal"], r["level"], r["design"], r["h"], "b", h["b"], "ctrl t", c["t"])
    print("T1 rows beating both benchmarks", beat, "of", len(rows))
    print("sign match dev/hold T1", sum(1 for r in rows if r["dev"].get("b") and r["hold"].get("b") and r["dev"]["b"] * r["hold"]["b"] > 0), "of", len(rows))
    for level in ("bond", "issuer", "bucket"):
        for h in lib.HORIZONS:
            mde = [r["hold"]["mde80"] for r in rows if r["level"] == level and r["h"] == h and r["hold"].get("mde80")]
            print("mde", level, h, round(min(mde), 2), round(max(mde), 2))
    for name in ("C", "C_A", "C_A_T"):
        p = pd.read_parquet(lib.WORK / f"weekly_{name}.parquet")
        last = p.sort_values("week").groupby("cusip").tail(1)
        print(name, "net since start, % of scale, panel", round(last["cum_level"].sum() / last["scale"].sum() * 100, 2))
    print(json.dumps(d["hit_rates"][:3]))
    print(json.dumps(d["ledger_coverage"]))
    print(json.dumps(d["t0"]["new_issues"]))


if __name__ == "__main__":
    main()
