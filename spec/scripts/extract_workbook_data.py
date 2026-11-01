"""Extract the raw inputs and the cached workbook outputs into CSV test fixtures.

Run once from the spec directory. It reads the 2018 workbook and writes:
  data/ty_daily.csv   raw daily inputs and the cached formula outputs
  data/ty_cftc.csv    raw weekly CFTC fields from Sheet1
The production machine does not need the workbook. It only needs the two CSV files.
"""
import csv
import datetime as dt
import sys

import openpyxl

SOURCE = sys.argv[1]


def main():
    book = openpyxl.load_workbook(SOURCE, data_only=True)
    daily = book["Pain Monitor"]
    with open("data/ty_daily.csv", "w", newline="") as handle:
        out = csv.writer(handle)
        out.writerow(["date", "close", "open", "high", "low", "open_interest", "volume",
                      "wb_typical", "wb_price_change", "wb_oi_change", "wb_oi_pct_volume",
                      "wb_vwap", "wb_net_new", "wb_side", "wb_over_under"])
        for row in range(3, 128):
            cells = [daily[f"{col}{row}"].value for col in "BCDEFIKGHJLMNOP"]
            cells[0] = cells[0].date().isoformat()
            out.writerow(["" if value in (None, "N/A", "#VALUE!") else value for value in cells])

    weekly = book["Sheet1"]
    names = {"D": "dealer_long", "E": "dealer_short", "G": "asset_mgr_long", "H": "lev_money_long",
             "I": "other_rept_long", "J": "noncomm_long", "M": "asset_mgr_short",
             "N": "lev_money_short", "O": "other_rept_short", "T": "comm_long", "U": "comm_short",
             "V": "noncomm_short", "W": "dealer_spread", "X": "asset_mgr_spread",
             "Z": "lev_money_spread", "AA": "other_rept_spread", "AB": "nonrept_long",
             "AC": "nonrept_short"}
    with open("data/ty_cftc.csv", "w", newline="") as handle:
        out = csv.writer(handle)
        out.writerow(["date", *names.values()])
        for row in range(2, 27):
            stamp = weekly[f"A{row}"].value
            assert isinstance(stamp, dt.datetime)
            out.writerow([stamp.date().isoformat(), *[weekly[f"{col}{row}"].value for col in names]])


if __name__ == "__main__":
    main()
