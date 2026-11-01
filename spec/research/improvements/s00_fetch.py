"""Download every raw input into raw/ and write raw/manifest.json. A failure is recorded, never replaced.

Run from anywhere:  python research/improvements/s00_fetch.py
"""
import datetime
import hashlib
import io
import json
import shutil
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SPEC = HERE.parents[1]
sys.path.insert(0, str(SPEC))
from posmon.data import fetch_cftc  # noqa: E402

RAW = HERE / "raw"
RAW.mkdir(exist_ok=True)

UST = {"TU": "042601", "FV": "044601", "TY": "043602", "TN": "043607", "US": "020601", "WN": "020604"}
FX = {"EC": "099741", "JY": "097741", "BP": "096742", "AD": "232741", "CD": "090741", "SF": "092741", "NE": "112741"}
FRED = ["DGS2", "DGS5", "DGS7", "DGS10", "DGS20", "DGS30", "DEXUSEU", "DEXJPUS", "DEXUSUK", "DEXUSAL", "DEXCAUS",
        "DEXSZUS", "DEXUSNZ"]
YAHOO = {"TU": "ZT=F", "FV": "ZF=F", "TY": "ZN=F", "US": "ZB=F"}
ANNOUNCE = "https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm"
AGENT = {"User-Agent": "Mozilla/5.0"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def note(manifest, name, path=None, frame=None, error=None):
    row = {"name": name, "fetched_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    if error is not None:
        row.update(status="failed", error=str(error))
        print("FAILED", name, error)
    else:
        row.update(status="ok", file=str(Path(path).name), sha256=sha(path))
        if frame is not None:
            row.update(rows=int(len(frame)), first=str(frame.index[0])[:10], last=str(frame.index[-1])[:10])
    manifest.append(row)


def get_cftc(manifest):
    for market, codes in (("UST", UST), ("FX", FX)):
        for symbol, code in codes.items():
            for report, start in (("legacy", "2000-01-01"), ("tff", "2006-01-01")):
                for basis in ("futures", "combined"):
                    name = f"cftc_{report}_{basis}_{symbol}"
                    path = RAW / f"{name}.csv"
                    try:
                        frame = fetch_cftc(report, code, start=start, basis=basis)
                        frame.to_csv(path)
                        note(manifest, name, path, frame)
                    except Exception as error:  # noqa: BLE001 - recorded in the manifest, then reported as not run
                        note(manifest, name, error=error)
            print(market, symbol, "done", flush=True)


def get_fred(manifest):
    for series in FRED:
        path = RAW / f"fred_{series}.csv"
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}&cosd=2000-01-01"
        try:
            for attempt in range(4):
                try:
                    text = urllib.request.urlopen(urllib.request.Request(url, headers=AGENT), timeout=60).read().decode()
                    break
                except OSError:
                    if attempt == 3:
                        raise
                    time.sleep(2 ** attempt)
            path.write_text(text)
            frame = pd.read_csv(io.StringIO(text), parse_dates=["observation_date"], index_col="observation_date")
            note(manifest, f"fred_{series}", path, frame)
        except Exception as error:  # noqa: BLE001
            note(manifest, f"fred_{series}", error=error)
    print("FRED done", flush=True)


def get_yahoo(manifest):
    for symbol, ticker in YAHOO.items():
        path = RAW / f"yahoo_{symbol}.csv"
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?period1=946684800&period2=4102444800&interval=1d"
        try:
            payload = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=AGENT), timeout=60))
            result = payload["chart"]["result"][0]
            stamps = pd.to_datetime(result["timestamp"], unit="s").normalize()
            close = result["indicators"]["quote"][0]["close"]
            frame = pd.DataFrame({"close": close}, index=stamps).dropna()
            frame = frame[~frame.index.duplicated(keep="last")]
            frame.index.name = "date"
            frame.to_csv(path)
            note(manifest, f"yahoo_{symbol}", path, frame)
        except Exception as error:  # noqa: BLE001
            note(manifest, f"yahoo_{symbol}", error=error)
    print("Yahoo done", flush=True)


def get_other(manifest):
    path = RAW / "cftc_special_announcements.html"
    try:
        path.write_bytes(urllib.request.urlopen(urllib.request.Request(ANNOUNCE, headers=AGENT), timeout=60).read())
        note(manifest, "cftc_special_announcements", path)
    except Exception as error:  # noqa: BLE001
        note(manifest, "cftc_special_announcements", error=error)
    # Copies of the project's own inputs, so a later change elsewhere cannot alter a rerun without showing up here.
    for name in ("treasury_futures_dv01.csv", "ty_daily.csv"):
        target = RAW / f"project_{name}"
        shutil.copyfile(SPEC / "data" / name, target)
        note(manifest, f"project_{name}", target)


def main():
    manifest = []
    get_cftc(manifest)
    get_fred(manifest)
    get_yahoo(manifest)
    get_other(manifest)
    (RAW / "manifest.json").write_text(json.dumps(manifest, indent=1))
    failed = [row["name"] for row in manifest if row["status"] != "ok"]
    print("files", len(manifest), "failed", failed)


if __name__ == "__main__":
    main()
