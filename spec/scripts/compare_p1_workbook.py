"""Compare P1 with the workbook reading of it (P5) on the workbook's TY data. Run from the spec directory."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from posmon.pain import ms_pain_monitor, typical_price, workbook_over_under  # noqa: E402

daily = pd.read_csv("data/ty_daily.csv", parse_dates=["date"], index_col="date")
typical = typical_price(daily.high, daily.low, daily.close)
book = workbook_over_under(daily)
rows = []
for i in range(31, len(daily) + 1):
    part = daily.iloc[:i]
    out = ms_pain_monitor(part.close, typical.iloc[:i], part.open_interest, multiplier=1000.0, window=30)
    row = book.iloc[i - 1]
    rows.append({"date": part.index[-1], "side": row.side, "gap": row.over_under, "net": row.net_new, "long": out["long_open"],
                 "short": out["short_open"], "long_off": out["long_offside"], "short_off": out["short_offside"]})
table = pd.DataFrame(rows).set_index("date")
side = np.where(table.side == "Long", 1, -1)
under = ((table.side == "Long") & (table.gap < 0)) | ((table.side == "Short") & (table.gap > 0))
share = pd.Series(np.where(side > 0, table.long_off / table.long.replace(0, np.nan),
                           table.short_off / table.short.replace(0, np.nan)), index=table.index)
print("days", len(table))
print("larger P1 book equals workbook side: %.1f%%" % (100 * (np.sign(table.long - table.short) == side).mean()))
print("workbook under water %.1f%%, P1 majority offside %.1f%%, agree %.1f%%"
      % (100 * under.mean(), 100 * (share > 0.5).mean(), 100 * (under == (share > 0.5)).mean()))
print("correlation of signed gap with P1 offside share: %.2f" % pd.Series(-table.gap * side, index=table.index).corr(share))
print("side changes in the workbook: %d" % (table.side != table.side.shift()).iloc[1:].sum())
