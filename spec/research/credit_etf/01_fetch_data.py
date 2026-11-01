#!/usr/bin/env python3
"""Download every public input into raw/. Reruns skip files that exist; --refresh downloads again.

Downloaded files are data only. No file under raw/ is ever imported or executed.

Sources and what happened to each are written to raw/fetch_log.json.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

ISHARES = {
    "LQD": ("239566", "ishares-iboxx-investment-grade-corporate-bond-etf"),
    "HYG": ("239565", "ishares-iboxx-high-yield-corporate-bond-etf"),
    "IGSB": ("239451", "ishares-1-5-year-investment-grade-corporate-bond-etf"),
    "IGIB": ("239463", "ishares-5-10-year-investment-grade-corporate-bond-etf"),
    "USIG": ("239460", "ishares-broad-usd-investment-grade-corporate-bond-etf"),
    "USHY": ("291299", "ishares-broad-usd-high-yield-corporate-bond-etf"),
    "FALN": ("283855", "ishares-fallen-angels-usd-bond-etf"),
    "EMB": ("239572", "ishares-j-p-morgan-usd-emerging-markets-bond-etf"),
    "LQDH": ("264542", "ishares-interest-rate-hedged-corporate-bond-etf"),
    "HYGH": ("264544", "ishares-interest-rate-hedged-high-yield-bond-etf"),
    "SHYG": ("258100", "ishares-0-5-year-high-yield-corporate-bond-etf"),
}
SSGA = ["JNK", "SJNK", "SPSB", "SPIB", "SPLB"]
PRICE_TICKERS = list(ISHARES) + SSGA + ["VCIT", "VCSH"]
FRED = ["BAMLC0A0CM", "BAMLH0A0HYM2", "BAA10Y", "AAA10Y", "DTB3", "DGS1", "DGS2", "DGS3", "DGS5", "DGS7", "DGS10",
        "DGS20", "DGS30"]
CFTC_DATASETS = {"tff_fut": "gpe5-46if", "tff_combined": "yw9f-hn96", "legacy_fut": "6dca-aqww"}
CFTC_CODES = {"221605": "BLOOMBERG_HY_CREDIT", "221606": "BLOOMBERG_IG_CREDIT"}

LOG: dict = {}


def get(url: str, timeout: int = 90, headers: dict | None = None, data: bytes | None = None, tries: int = 3) -> bytes:
    last = None
    for attempt in range(tries):
        try:
            request = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except Exception as error:  # noqa: BLE001 - logged and retried
            last = error
            time.sleep(4 * (attempt + 1))
    raise RuntimeError(f"{url[:120]} failed: {last}")


def save(path: Path, blob: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(blob)


API = ("https://www.ishares.com/varnish-api/blk-one01-product-data/product-data/api/v2/get-product-data?"
       "appSubType=ISHARES&appType=PRODUCT_PAGE&locale=en_US&portfolioId={pid}&targetSite=us-ishares"
       "&userType=individual&excludeContent=true&includeConfig=true&component={component}")
API_HEADERS = {"Accept": "application/json", "x-application-id": "pp-ui-csr", "User-Agent": "Mozilla/5.0"}


def fetch_ishares(refresh: bool) -> None:
    """The old .ajax download link now answers with the product page. The page's own JSON feed has the same file."""
    for ticker, (pid, _) in ISHARES.items():
        out = RAW / "ishares" / f"{ticker}.json"
        if out.exists() and not refresh:
            LOG[f"ishares/{ticker}"] = {"status": "cached"}
            continue
        try:
            blob = get(API.format(pid=pid, component="fundDownload"), timeout=120, headers=API_HEADERS)
            containers = json.loads(blob)["componentsByNameMap"]["fundDownload"]["containersByNameMap"]
            points = containers["historical"]["dataPointsByNameMap"]
            slim = {name: points[name]["value"] for name in ("asof", "exDividends", "nav", "sharesOutstanding")}
            save(out, json.dumps(slim).encode())
            LOG[f"ishares/{ticker}"] = {"status": "live", "rows": len(slim["asof"]), "first": slim["asof"][-1],
                                        "last": slim["asof"][0]}
        except Exception as error:  # noqa: BLE001
            LOG[f"ishares/{ticker}"] = {"status": "failed", "error": str(error)[:200]}
        print(ticker, LOG[f"ishares/{ticker}"], flush=True)
        time.sleep(1)


def holdings_duration(pid: str, date: str) -> dict | None:
    """Market-value weighted effective duration of the bond holdings on one date. Only the summary is kept."""
    url = API.format(pid=pid, component="holdings.all") + f"&asOfDate={date}"
    blob = get(url, timeout=120, headers=API_HEADERS, tries=2)
    payload = json.loads(blob)["componentsByNameMap"]["holdings"]["containersByNameMap"]["all"]["dataPointsByNameMap"]
    names = {key.lower(): key for key in payload}
    weight_key = next((names[k] for k in ("holdingpercent", "weight", "percentofnetassets") if k in names), None)
    duration_key = next((names[k] for k in ("effectiveduration", "duration", "modifiedduration") if k in names), None)
    if weight_key is None or duration_key is None:
        return {"date": date, "columns": sorted(payload)[:60]}
    weights, durations = payload[weight_key]["value"], payload[duration_key]["value"]
    pairs = [(float(w), float(d)) for w, d in zip(weights, durations)
             if isinstance(w, (int, float)) and isinstance(d, (int, float))]
    if not pairs:
        return {"date": date, "lines": 0}
    total = sum(w for w, _ in pairs)
    summary = {"date": date, "lines": len(pairs), "weight": total, "duration": sum(w * d for w, d in pairs) / total}
    if "yieldtoworst" in names:
        yields = [(float(w), float(y)) for w, y in zip(weights, payload[names["yieldtoworst"]]["value"])
                  if isinstance(w, (int, float)) and isinstance(y, (int, float))]
        if yields:
            summary["ytw"] = sum(w * y for w, y in yields) / sum(w for w, _ in yields)
    return summary


def fetch_duration_points(refresh: bool) -> None:
    """Twice-yearly holdings for the primary funds, once a year for the others, then the latest month-end."""
    out = RAW / "ishares" / "duration_points.json"
    table = json.loads(out.read_text()) if out.exists() and not refresh else {}
    for ticker, (pid, _) in ISHARES.items():
        points = table.setdefault(ticker, {})
        months = ["0630", "1231"] if ticker in ("LQD", "HYG") else ["1231"]
        dates = [f"{year}{suffix}" for year in range(2007, 2026) for suffix in months] + ["20260930"]
        for date in dates:
            if date in points:
                continue
            for back in range(0, 4):
                stamp = (pd.Timestamp(date) - pd.Timedelta(days=back)).strftime("%Y%m%d")
                if pd.Timestamp(stamp).weekday() >= 5:
                    continue
                try:
                    result = holdings_duration(pid, stamp)
                except Exception as error:  # noqa: BLE001
                    result = {"error": str(error)[:80]}
                time.sleep(0.5)
                if result and result.get("duration"):
                    points[date] = result
                    break
                points[date] = result
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(table, indent=0))
        good = [p for p in points.values() if p and p.get("duration")]
        LOG[f"duration/{ticker}"] = {"points": len(good)}
        print(ticker, "duration points", len(good), flush=True)


def fetch_ssga(refresh: bool) -> None:
    for ticker in SSGA:
        out = RAW / "ssga" / f"{ticker}.xlsx"
        if out.exists() and not refresh:
            LOG[f"ssga/{ticker}"] = {"status": "cached"}
            continue
        url = f"https://www.ssga.com/us/en/intermediary/library-content/products/fund-data/etfs/us/navhist-us-en-{ticker.lower()}.xlsx"
        try:
            save(out, get(url))
            LOG[f"ssga/{ticker}"] = {"status": "live", "url": url}
        except Exception as error:  # noqa: BLE001
            LOG[f"ssga/{ticker}"] = {"status": "failed", "error": str(error)[:200]}


def fetch_prices(refresh: bool) -> None:
    for ticker in PRICE_TICKERS:
        out = RAW / "yahoo" / f"{ticker}.json"
        if out.exists() and not refresh:
            LOG[f"yahoo/{ticker}"] = {"status": "cached"}
            continue
        url = (f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?period1=946684800&period2=1798761600"
               "&interval=1d&events=div%7Csplit")
        try:
            save(out, get(url, timeout=40, tries=2, headers={"User-Agent": "Mozilla/5.0"}))
            LOG[f"yahoo/{ticker}"] = {"status": "live"}
        except Exception as error:  # noqa: BLE001
            LOG[f"yahoo/{ticker}"] = {"status": "failed", "error": str(error)[:200]}
        time.sleep(2)


def fetch_fred(refresh: bool) -> None:
    for series in FRED:
        out = RAW / "fred" / f"{series}.csv"
        if out.exists() and not refresh:
            LOG[f"fred/{series}"] = {"status": "cached"}
            continue
        try:
            # FRED stalls on a browser user agent and answers a plain one.
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
            save(out, get(url, timeout=40, tries=2, headers={"User-Agent": "curl/8.5.0"}))
            lines = out.read_text().strip().splitlines()
            LOG[f"fred/{series}"] = {"status": "live", "first": lines[1][:10], "last": lines[-1][:10]}
        except Exception as error:  # noqa: BLE001
            LOG[f"fred/{series}"] = {"status": "failed", "error": str(error)[:200]}
        time.sleep(1)


def fetch_finra(refresh: bool) -> None:
    url = "https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest"
    for ticker in PRICE_TICKERS:
        out = RAW / "finra" / f"{ticker}.json"
        if out.exists() and not refresh:
            LOG[f"finra/{ticker}"] = {"status": "cached"}
            continue
        body = {"limit": 5000, "compareFilters": [{"compareType": "EQUAL", "fieldName": "symbolCode", "fieldValue": ticker}]}
        try:
            blob = get(url, headers={"Content-Type": "application/json", "Accept": "application/json"},
                       data=json.dumps(body).encode())
            save(out, blob)
            rows = json.loads(blob)
            dates = sorted(row["settlementDate"] for row in rows)
            LOG[f"finra/{ticker}"] = {"status": "live", "rows": len(rows), "first": dates[0], "last": dates[-1]}
        except Exception as error:  # noqa: BLE001
            LOG[f"finra/{ticker}"] = {"status": "failed", "error": str(error)[:200]}
        time.sleep(0.5)


def fetch_cftc(refresh: bool) -> None:
    for name, dataset in CFTC_DATASETS.items():
        for code, label in CFTC_CODES.items():
            out = RAW / "cftc" / f"{name}_{label}.json"
            if out.exists() and not refresh:
                LOG[f"cftc/{name}/{label}"] = {"status": "cached"}
                continue
            query = {"cftc_contract_market_code": code, "$limit": "5000", "$order": "report_date_as_yyyy_mm_dd"}
            url = f"https://publicreporting.cftc.gov/resource/{dataset}.json?" + urllib.parse.urlencode(query)
            try:
                blob = get(url)
                save(out, blob)
                LOG[f"cftc/{name}/{label}"] = {"status": "live", "rows": len(json.loads(blob))}
            except Exception as error:  # noqa: BLE001
                LOG[f"cftc/{name}/{label}"] = {"status": "failed", "error": str(error)[:200]}
    # Every contract name that could be a credit index, so an absence is a checked absence.
    out = RAW / "cftc" / "name_search.json"
    if not out.exists() or refresh:
        where = " OR ".join(f"upper(market_and_exchange_names) like '%{word}%'" for word in
                            ["IBOXX", "IBHY", "IBIG", "CDX", "CREDIT FUT", "HIGH YIELD", "INVESTMENT GRADE", "CBOE", "CORPORATE"])
        query = {"$select": "market_and_exchange_names,cftc_contract_market_code,count(*) as n,"
                            "min(report_date_as_yyyy_mm_dd) as first,max(report_date_as_yyyy_mm_dd) as last",
                 "$where": where, "$group": "market_and_exchange_names,cftc_contract_market_code", "$limit": "200"}
        url = "https://publicreporting.cftc.gov/resource/gpe5-46if.json?" + urllib.parse.urlencode(query)
        try:
            save(out, get(url))
            LOG["cftc/name_search"] = {"status": "live"}
        except Exception as error:  # noqa: BLE001
            LOG["cftc/name_search"] = {"status": "failed", "error": str(error)[:200]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    RAW.mkdir(exist_ok=True)
    for step in (fetch_fred, fetch_ssga, fetch_finra, fetch_cftc, fetch_prices, fetch_ishares, fetch_duration_points):
        print("step", step.__name__, flush=True)
        step(args.refresh)
        (RAW / "fetch_log.json").write_text(json.dumps(LOG, indent=1, sort_keys=True))
    print("done")


if __name__ == "__main__":
    main()
