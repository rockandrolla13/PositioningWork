"""Cached access to public data. Raw files live in raw/ and are read as data only."""
from __future__ import annotations

import io
import sys
import urllib.request
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SPEC = HERE.parents[1]
sys.path.insert(0, str(SPEC))
from posmon.data import fetch_cftc  # noqa: E402

RAW = HERE / "raw"
(RAW / "cftc").mkdir(parents=True, exist_ok=True)
(RAW / "fred").mkdir(parents=True, exist_ok=True)


def cftc(report: str, code: str, basis: str = "futures") -> pd.DataFrame:
    path = RAW / "cftc" / f"{report}_{basis}_{code}.csv"
    if not path.exists():
        fetch_cftc(report, code, "1986-01-01", "2100-01-01", basis=basis).to_csv(path)
    return pd.read_csv(path, parse_dates=["report_date"], index_col="report_date")


def fred(series: str) -> pd.Series:
    path = RAW / "fred" / f"{series}.csv"
    if not path.exists():
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
        path.write_text(urllib.request.urlopen(url, timeout=90).read().decode())
    frame = pd.read_csv(path, parse_dates=["observation_date"], index_col="observation_date")
    return pd.to_numeric(frame[series], errors="coerce")


def dv01() -> pd.DataFrame:
    long = pd.read_csv(SPEC / "data" / "treasury_futures_dv01.csv", parse_dates=["date"])
    return long.pivot(index="date", columns="contract", values="dv01_usd")
