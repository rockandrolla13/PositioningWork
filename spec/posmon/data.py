"""CFTC feed, canonical field names, timing rules and data checks."""
from __future__ import annotations

import datetime
import json
import time
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd

BASE_URL = "https://publicreporting.cftc.gov/resource/{dataset}.json"

# Six public datasets. Tested live on 2026-11-01.
DATASETS = {
    ("legacy", "futures"): "6dca-aqww",
    ("legacy", "combined"): "jun7-fc8e",
    ("disaggregated", "futures"): "72hh-3qpy",
    ("disaggregated", "combined"): "kh3c-gbw2",
    ("tff", "futures"): "gpe5-46if",
    ("tff", "combined"): "yw9f-hn96",
}

# Canonical name -> API column. The API spelling is not uniform, so keep this table.
COLUMNS = {
    "tff": {
        "open_interest": "open_interest_all",
        "dealer_long": "dealer_positions_long_all",
        "dealer_short": "dealer_positions_short_all",
        "dealer_spread": "dealer_positions_spread_all",
        "asset_mgr_long": "asset_mgr_positions_long",
        "asset_mgr_short": "asset_mgr_positions_short",
        "asset_mgr_spread": "asset_mgr_positions_spread",
        "lev_money_long": "lev_money_positions_long",
        "lev_money_short": "lev_money_positions_short",
        "lev_money_spread": "lev_money_positions_spread",
        "other_rept_long": "other_rept_positions_long",
        "other_rept_short": "other_rept_positions_short",
        "other_rept_spread": "other_rept_positions_spread",
        "nonrept_long": "nonrept_positions_long_all",
        "nonrept_short": "nonrept_positions_short_all",
    },
    "legacy": {
        "open_interest": "open_interest_all",
        "noncomm_long": "noncomm_positions_long_all",
        "noncomm_short": "noncomm_positions_short_all",
        "noncomm_spread": "noncomm_postions_spread_all",  # the CFTC column really is misspelt
        "comm_long": "comm_positions_long_all",
        "comm_short": "comm_positions_short_all",
        "nonrept_long": "nonrept_positions_long_all",
        "nonrept_short": "nonrept_positions_short_all",
    },
    "disaggregated": {
        "open_interest": "open_interest_all",
        "producer_long": "prod_merc_positions_long",
        "producer_short": "prod_merc_positions_short",
        "swap_long": "swap_positions_long_all",
        "swap_short": "swap__positions_short_all",  # double underscore in the source
        "swap_spread": "swap__positions_spread_all",
        "money_mgr_long": "m_money_positions_long_all",
        "money_mgr_short": "m_money_positions_short_all",
        "money_mgr_spread": "m_money_positions_spread",
        "other_rept_long": "other_rept_positions_long",
        "other_rept_short": "other_rept_positions_short",
        "other_rept_spread": "other_rept_positions_spread",
        "nonrept_long": "nonrept_positions_long_all",
        "nonrept_short": "nonrept_positions_short_all",
    },
}


def fetch_cftc(report: str, code: str, start: str = "1986-01-01", end: str = "2100-01-01",
               basis: str = "futures", retries: int = 3) -> pd.DataFrame:
    """Download one market. Key on the CFTC code, never on the market name."""
    url = BASE_URL.format(dataset=DATASETS[(report, basis)])
    frames, offset, page = [], 0, 5000
    while True:
        query = {"$where": (f"cftc_contract_market_code='{code}' AND "
                            f"report_date_as_yyyy_mm_dd between '{start}T00:00:00.000' "
                            f"and '{end}T00:00:00.000'"),
                 "$order": "report_date_as_yyyy_mm_dd", "$limit": page, "$offset": offset}
        rows = _get_json(url + "?" + urllib.parse.urlencode(query), retries)
        frames.extend(rows)
        if len(rows) < page:
            break
        offset += page
    if not frames:
        raise ValueError(f"no rows for {report}/{basis}/{code}")
    raw = pd.DataFrame(frames)
    out = pd.DataFrame(index=pd.to_datetime(raw["report_date_as_yyyy_mm_dd"]).dt.normalize())
    out.index.name = "report_date"
    for name, column in COLUMNS[report].items():
        if column not in raw:
            raise KeyError(f"{column} missing. The CFTC may have renamed it.")
        out[name] = pd.to_numeric(raw[column].values, errors="coerce")
    out["market_name"] = raw["market_and_exchange_names"].values
    return out[~out.index.duplicated(keep="last")].sort_index()


def _get_json(url: str, retries: int):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return json.load(response)
        except OSError:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    return []


def publish_time(report_date: pd.Timestamp) -> pd.Timestamp:
    """Normal release: the Friday after the report date, at 15:30 New York time.

    Use this only for history. In production, store the time your job first saw the row.
    """
    days = (4 - report_date.weekday()) % 7
    friday = report_date + datetime.timedelta(days=days)
    return pd.Timestamp(year=friday.year, month=friday.month, day=friday.day, hour=15, minute=30,
                        tz="America/New_York")


def known_at(report: pd.DataFrame, decision_time: pd.Timestamp) -> pd.DataFrame:
    """Return only the rows released at or before the decision time."""
    released = report.index.map(publish_time)
    return report[released <= decision_time]


def check_cftc(report: pd.DataFrame, kind: str = "tff") -> pd.DataFrame:
    """Return one row per failed check. An empty frame means the data passed."""
    problems = []
    gaps = report.index.to_series().diff().dt.days
    for stamp, days in gaps[gaps > 8].items():
        problems.append({"date": stamp, "check": "missing_week", "value": days})
    if kind == "tff":
        long_side = ["dealer_long", "asset_mgr_long", "lev_money_long", "other_rept_long", "nonrept_long"]
        short_side = ["dealer_short", "asset_mgr_short", "lev_money_short", "other_rept_short", "nonrept_short"]
        spreads = ["dealer_spread", "asset_mgr_spread", "lev_money_spread", "other_rept_spread"]
    elif kind == "legacy":
        long_side = ["noncomm_long", "comm_long", "nonrept_long"]
        short_side = ["noncomm_short", "comm_short", "nonrept_short"]
        spreads = ["noncomm_spread"]
    else:
        return pd.DataFrame(problems, columns=["date", "check", "value"])
    for name, columns in (("long_identity", long_side), ("short_identity", short_side)):
        gap = report[columns + spreads].sum(axis=1) - report["open_interest"]
        for stamp, value in gap[gap.abs() > 0.5].items():
            problems.append({"date": stamp, "check": name, "value": value})
    return pd.DataFrame(problems, columns=["date", "check", "value"])


def check_daily(daily: pd.DataFrame, median_rows: int = 60, volume_floor: float = 0.2) -> pd.DataFrame:
    """Flag the daily data faults found in the 2018 workbook."""
    flags = pd.DataFrame(index=daily.index)
    flags["close_outside_range"] = (daily["close"] > daily["high"]) | (daily["close"] < daily["low"])
    flags["high_equals_low"] = daily["high"] == daily["low"]
    flags["missing_range"] = daily["high"].isna() | daily["low"].isna()
    flags["missing_volume"] = daily["volume"].isna()
    typical_volume = daily["volume"].rolling(median_rows, min_periods=10).median()
    flags["volume_collapse"] = daily["volume"] < volume_floor * typical_volume
    flags["duplicate_date"] = daily.index.duplicated()
    return flags


def net(long_side: pd.Series, short_side: pd.Series) -> pd.Series:
    return long_side - short_side


def weekly_returns_to_daily_index(series: pd.Series, index: pd.DatetimeIndex) -> pd.Series:
    """Carry the last weekly value onto a daily index."""
    return series.reindex(index.union(series.index)).ffill().reindex(index)


__all__ = ["fetch_cftc", "publish_time", "known_at", "check_cftc", "check_daily", "net",
           "weekly_returns_to_daily_index", "DATASETS", "COLUMNS", "np"]
