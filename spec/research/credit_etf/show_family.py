#!/usr/bin/env python3
"""Print the family of tests from results.json as a table. A reading aid, not part of the pipeline."""
import json
from pathlib import Path

import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_rows", 400)


def num(value, digits=2):
    return None if value is None else round(value, digits)


results = json.loads((Path(__file__).parent / "results.json").read_text())
rows = []
for key, entry in results["family"].items():
    name, fund, horizon = key.split("|")
    hold, dev, rep = entry["holdout"], entry["dev"], entry.get("replicate", {})
    if hold.get("b") is None:
        rows.append({"sig": name, "f": fund, "h": int(horizon), "n": hold.get("n"), "label": entry["label"]})
        continue
    rows.append({"sig": name, "f": fund, "h": int(horizon), "n": hold["n"], "neff": hold["n_eff"], "b": num(hold["b"], 1),
                 "t": num(hold["t"]), "p": num(hold["p"], 3), "holm": num(entry["holm_p"]),
                 "ci": f"{hold['ci95'][0]:.0f},{hold['ci95'][1]:.0f}", "devb": num(dev.get("b"), 1), "devt": num(dev.get("t")),
                 "rep": num(rep.get("b"), 1), "rept": num(rep.get("t")),
                 "ctlt": num(hold.get("with_controls", {}).get("t")), "base": num(hold["base_rate_pos"]),
                 "top": num(hold["top"]["hit_pos"]), "topn": hold["top"]["n"], "bot": num(hold["bottom"]["hit_pos"]),
                 "botn": hold["bottom"]["n"], "label": entry["label"][:5]})
table = pd.DataFrame(rows)
print(table[table.h.isin([4, 26])].to_string())
print(table[table.label.str.startswith("sugg", na=False)].to_string())
print(table.sort_values("p").head(12)[["sig", "f", "h", "b", "t", "p", "holm", "label"]].to_string())
for key, entry in results["cross_section"].items():
    print(key, {p: (num(entry.get(p, {}).get("b")), num(entry.get(p, {}).get("t")), num(entry.get(p, {}).get("p"), 3))
                for p in ("all_holdout", "all_dev", "IG_holdout", "HY_holdout")}, num(entry.get("holm_p")), entry["label"])
print(results["label_counts"], results["family_size"])
