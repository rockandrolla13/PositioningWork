"""Loaders and shared helpers. Raw files are parsed as data only; nothing under raw/ is imported."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
WORK = HERE / "work"
SPEC_ROOT = HERE.parent.parent
if str(SPEC_ROOT) not in sys.path:
    sys.path.insert(0, str(SPEC_ROOT))

ISHARES = ["LQD", "HYG", "IGSB", "IGIB", "USIG", "USHY", "FALN", "EMB", "LQDH", "HYGH", "SHYG"]
SSGA = ["JNK", "SJNK", "SPSB", "SPIB", "SPLB"]
GROUP = {"LQD": "IG", "IGSB": "IG", "IGIB": "IG", "USIG": "IG", "SPSB": "IG", "SPIB": "IG", "SPLB": "IG", "LQDH": "IGH",
         "HYG": "HY", "JNK": "HY", "USHY": "HY", "FALN": "HY", "SHYG": "HY", "SJNK": "HY", "HYGH": "HYH", "EMB": "EM"}
# Constant credit carry used to turn excess return into an implied spread change, in percent a year.
# These are round long-run OAS levels. They set an intercept only. M7 checks them against OAS.
CARRY = {"IG": 1.3, "IGH": 1.3, "HY": 4.0, "HYH": 4.0, "EM": 3.0}
# Effective duration used when an archived fund file gives none. Stated, not estimated.
DEFAULT_DURATION = {"LQD": 8.4, "IGSB": 2.7, "IGIB": 6.2, "USIG": 6.9, "SPSB": 1.9, "SPIB": 4.3, "SPLB": 13.0,
                    "HYG": 3.9, "JNK": 3.9, "USHY": 3.6, "FALN": 5.5, "SHYG": 2.0, "SJNK": 2.2, "EMB": 7.5,
                    "LQDH": 0.2, "HYGH": 0.2}


def load_ishares(ticker: str) -> pd.DataFrame:
    """Daily NAV, ex-dividend amount and shares outstanding from the issuer's own feed."""
    data = json.loads((RAW / "ishares" / f"{ticker}.json").read_text())
    frame = pd.DataFrame({"date": pd.to_datetime([str(x) for x in data["asof"]], format="%Y%m%d"),
                          "nav": pd.to_numeric(data["nav"], errors="coerce"),
                          "div": pd.to_numeric(data["exDividends"], errors="coerce"),
                          "so": pd.to_numeric(data["sharesOutstanding"], errors="coerce")})
    return frame.drop_duplicates("date").set_index("date").sort_index()


def load_ssga(ticker: str) -> pd.DataFrame:
    raw = pd.read_excel(RAW / "ssga" / f"{ticker}.xlsx", header=None)
    start = raw.index[raw[0].astype(str).str.strip() == "Date"][0]
    body = raw.iloc[start + 1:, :4].copy()
    body.columns = ["date", "nav", "so", "tna"]
    body["date"] = pd.to_datetime(body["date"], errors="coerce", format="%d-%b-%Y")
    body = body.dropna(subset=["date"]).drop_duplicates("date").set_index("date").sort_index()
    return body.apply(pd.to_numeric, errors="coerce")


def load_yahoo(ticker: str) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    data = json.loads((RAW / "yahoo" / f"{ticker}.json").read_text())["chart"]["result"][0]
    quote = data["indicators"]["quote"][0]
    dates = pd.to_datetime(data["timestamp"], unit="s").normalize()
    frame = pd.DataFrame({"open": quote["open"], "high": quote["high"], "low": quote["low"], "close": quote["close"],
                          "volume": quote["volume"], "adjclose": data["indicators"]["adjclose"][0]["adjclose"]},
                         index=dates)
    frame = frame[~frame.index.duplicated(keep="last")].dropna(subset=["close"])
    events = data.get("events", {})
    dividends = pd.Series({pd.to_datetime(v["date"], unit="s").normalize(): v["amount"]
                           for v in events.get("dividends", {}).values()}, dtype=float).sort_index()
    splits = pd.Series({pd.to_datetime(v["date"], unit="s").normalize(): v["numerator"] / v["denominator"]
                        for v in events.get("splits", {}).values()}, dtype=float).sort_index()
    return frame, dividends, splits


def load_fred(series: str) -> pd.Series:
    frame = pd.read_csv(RAW / "fred" / f"{series}.csv", na_values=[".", ""])
    frame.columns = ["date", "value"]
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.set_index("date")["value"].astype(float)


def load_finra(ticker: str) -> pd.DataFrame:
    rows = json.loads((RAW / "finra" / f"{ticker}.json").read_text())
    frame = pd.DataFrame(rows)
    frame["settle"] = pd.to_datetime(frame["settlementDate"])
    frame = frame.sort_values("settle").drop_duplicates("settle", keep="last").set_index("settle")
    return frame[["currentShortPositionQuantity", "averageDailyVolumeQuantity", "daysToCoverQuantity", "stockSplitFlag"]]\
        .rename(columns={"currentShortPositionQuantity": "si", "averageDailyVolumeQuantity": "adv",
                         "daysToCoverQuantity": "dtc", "stockSplitFlag": "split"})


def treasury_curve() -> pd.DataFrame:
    tenors = {"DTB3": 0.25, "DGS1": 1, "DGS2": 2, "DGS3": 3, "DGS5": 5, "DGS7": 7, "DGS10": 10, "DGS20": 20, "DGS30": 30}
    frame = pd.DataFrame({years: load_fred(series) for series, years in tenors.items()})
    return frame.sort_index().ffill(limit=5)


def matched_hedge(duration: pd.Series, curve: pd.DataFrame) -> pd.DataFrame:
    """Daily total return of a Treasury position with the given modified duration.

    Each day I pick the maturity m whose par bond has that duration. Return = carry - D x change in yield at m.
    D is in years and the yields in percent. Yields are read off the par curve by linear interpolation.
    """
    days = duration.index
    grid = curve.reindex(curve.index.union(days)).ffill().reindex(days)
    tenors = grid.columns.values.astype(float)
    values = grid.values / 100.0
    ret = np.full(len(days), np.nan)
    maturity = np.full(len(days), np.nan)
    level = np.full(len(days), np.nan)
    for i, (d_years, row) in enumerate(zip(duration.values, values)):
        good = ~np.isnan(row)
        if good.sum() < 3 or not np.isfinite(d_years):
            continue
        m = max(0.25, d_years)
        for _ in range(4):
            y = float(np.interp(m, tenors[good], row[good]))
            inner = 1.0 - d_years * y
            if inner <= 0.02 or y <= 0:
                m = 30.0 if y > 0 else max(0.25, d_years)
                break
            m = float(np.clip(-np.log(inner) / (2.0 * np.log(1.0 + y / 2.0)), 0.25, 30.0))
        maturity[i] = m
        level[i] = float(np.interp(m, tenors[good], row[good]))
        if i and np.isfinite(maturity[i - 1]):
            prior = values[i - 1]
            ok = ~np.isnan(prior)
            if ok.sum() >= 3:
                m0 = maturity[i - 1]
                y0 = float(np.interp(m0, tenors[ok], prior[ok]))
                y1 = float(np.interp(m0, tenors[good], row[good]))
                elapsed = (days[i] - days[i - 1]).days
                ret[i] = y0 * elapsed / 365.0 - duration.values[i - 1] * (y1 - y0)
    return pd.DataFrame({"ret": ret, "maturity": maturity, "yield": level}, index=days)


def holm(pvalues: dict) -> dict:
    """Holm step-down adjusted p-values. Missing values stay out of the count."""
    keys = [key for key, value in pvalues.items() if value == value]
    keys.sort(key=lambda key: pvalues[key])
    total = len(keys)
    out, running = {}, 0.0
    for rank, key in enumerate(keys):
        running = max(running, min(1.0, (total - rank) * pvalues[key]))
        out[key] = running
    return out
