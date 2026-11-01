#!/usr/bin/env python3
"""Daily statistics from the marketdb book: VWAP, signed volume, half-spread. No raw rows are stored.

One symbol-day takes about 6 seconds, so this samples: all of 2024 for LQD and HYG, every fifth day otherwise.
Output: work/book_daily.csv. A rerun skips symbol-days already done.
"""
from __future__ import annotations

import multiprocessing as mp
import os
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "work" / "book_daily.csv"
COLUMNS = ["symbol", "date", "vwap", "volume", "signed_volume", "n_trades", "spread", "mid", "close_last_30m_signed"]


def worker(jobs: list) -> list:
    import marketdb

    con = marketdb.connect(verify=False)
    rows = []
    for symbol, day in jobs:
        trades = con.execute(
            """SELECT sum(price*size)/nullif(sum(size),0) AS vwap, sum(size) AS volume,
                      sum(CASE side WHEN 'B' THEN CAST(size AS BIGINT) WHEN 'A' THEN -CAST(size AS BIGINT) ELSE 0 END) AS signed,
                      count(*) AS n,
                      sum(CASE WHEN extract(hour FROM ts_event)*60 + extract(minute FROM ts_event) >=
                                    (SELECT max(extract(hour FROM ts_event)*60 + extract(minute FROM ts_event))
                                     FROM db_book WHERE symbol=? AND trade_date=? AND action='T') - 30
                               THEN (CASE side WHEN 'B' THEN CAST(size AS BIGINT) WHEN 'A' THEN -CAST(size AS BIGINT) ELSE 0 END)
                               ELSE 0 END) AS signed_30
               FROM db_book WHERE symbol=? AND trade_date=? AND action='T'""",
            [symbol, day, symbol, day]).fetchone()
        quotes = con.execute(
            """SELECT median(ask_px_00-bid_px_00) AS spread, median((ask_px_00+bid_px_00)/2) AS mid
               FROM db_book WHERE symbol=? AND trade_date=? AND bid_px_00>0 AND ask_px_00>bid_px_00""",
            [symbol, day]).fetchone()
        rows.append([symbol, str(day), trades[0], trades[1], trades[2], trades[3], quotes[0], quotes[1], trades[4]])
    con.close()
    return rows


def main() -> None:
    import marketdb

    OUT.parent.mkdir(exist_ok=True)
    con = marketdb.connect(verify=False)
    coverage = con.sql("""SELECT DISTINCT symbol, trade_date FROM book_coverage
                          WHERE symbol IN ('LQD','HYG','JNK') AND trade_date >= DATE '2023-05-30'""").df()
    con.close()
    coverage["trade_date"] = pd.to_datetime(coverage["trade_date"]).dt.date
    jobs = []
    for symbol, group in coverage.groupby("symbol"):
        days = sorted(group["trade_date"])
        for index, day in enumerate(days):
            in_2024 = symbol in ("LQD", "HYG") and day.year == 2024
            if in_2024 or index % 5 == 0:
                jobs.append((symbol, day))
    done = set()
    if OUT.exists():
        old = pd.read_csv(OUT)
        done = set(zip(old["symbol"], old["date"]))
    else:
        pd.DataFrame(columns=COLUMNS).to_csv(OUT, index=False)
    jobs = [job for job in jobs if (job[0], str(job[1])) not in done]
    print("jobs", len(jobs), flush=True)
    chunks = [jobs[i:i + 12] for i in range(0, len(jobs), 12)]
    with mp.Pool(int(os.environ.get("BOOK_WORKERS", "3"))) as pool:
        for rows in pool.imap_unordered(worker, chunks):
            pd.DataFrame(rows, columns=COLUMNS).to_csv(OUT, mode="a", header=False, index=False)
            print("wrote", len(rows), flush=True)


if __name__ == "__main__":
    main()
