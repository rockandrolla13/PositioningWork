"""Bond reference data from public sources only: coupon and maturity from OpenFIGI, issue size from SEC filings.

Nothing here is copied from TRACE except the list of CUSIPs, which are public identifiers.
Rerun skips anything already cached in raw/.
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
import os
from pathlib import Path

import marketdb
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
SEC = RAW / "sec_cache"
FIGI_FILE = RAW / "openfigi.json"
UA = os.environ["SEC_USER_AGENT"]  # the SEC requires a contact in the user agent
FORMS = "FWP,424B2,424B5,424B3,8-K"


def universe() -> pd.DataFrame:
    con = marketdb.connect()
    return con.sql("""SELECT cusip, any_value(company_symbol) AS issuer, count(*) AS n_c
        FROM trace WHERE company_symbol IS NOT NULL AND company_symbol <> 'JPM' AND cntra_mp_id = 'C'
        GROUP BY 1 ORDER BY 1""").df()


def fetch_figi(cusips: list) -> dict:
    done = json.loads(FIGI_FILE.read_text()) if FIGI_FILE.exists() else {}
    todo = [c for c in cusips if c not in done]
    for start in range(0, len(todo), 10):
        batch = todo[start:start + 10]
        body = json.dumps([{"idType": "ID_CUSIP", "idValue": c} for c in batch]).encode()
        request = urllib.request.Request("https://api.openfigi.com/v3/mapping", body,
                                         {"Content-Type": "application/json"})
        for attempt in range(6):
            try:
                out = json.load(urllib.request.urlopen(request, timeout=30))
                break
            except urllib.error.HTTPError as error:
                if error.code != 429:
                    raise
                time.sleep(65)
        for cusip, row in zip(batch, out):
            done[cusip] = row.get("data", [])
        FIGI_FILE.write_text(json.dumps(done))
        time.sleep(2.6)  # 25 requests a minute without a key
    return done


def parse_figi(records: list) -> dict:
    """OpenFIGI tickers read 'AAPL 3 11/13/27', 'AAPL 4.65 02/23/46', or 'IBM F 02/05/26' for a floater."""
    for record in records:
        match = re.match(r"^(\S+)\s+(\S+)\s+(\d\d)/(\d\d)/(\d\d)\b", record.get("ticker") or "")
        if match:
            coupon = match.group(2)
            year = int(match.group(5))
            year += 1900 if year > 60 else 2000  # no bond here matures after 2060 by this rule alone
            return {"ticker": record["ticker"], "name": record.get("name"),
                    "coupon": None if coupon.upper().startswith("F") else float(re.sub(r"[^0-9.]", "", coupon) or "nan"),
                    "is_floater": coupon.upper().startswith("F"),
                    "maturity": f"{year}-{match.group(3)}-{match.group(4)}"}
    return {"ticker": None, "name": None, "coupon": None, "is_floater": None, "maturity": None}


def get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(5):
        try:
            time.sleep(0.15)
            return urllib.request.urlopen(request, timeout=40).read()
        except Exception:  # the SEC throttles with 403 and 503, so wait and retry
            time.sleep(3 + 5 * attempt)
    return b""


CIK = {"AAPL": "0000320193", "AMZN": "0001018724", "CMCS": "0001166691", "COST": "0000909832", "CSCO": "0000858877",
       "GOOG": "0001652044", "IBM": "0000051143", "INTC": "0000050863", "MSFT": "0000789019", "NVDA": "0001045810",
       "PEP": "0000077476", "RIG": "0001451505"}


def search(params: dict) -> list:
    raw = get("https://efts.sec.gov/LATEST/search-index?" + urllib.parse.urlencode(params))
    try:
        hits = json.loads(raw)["hits"]["hits"]
    except Exception:
        return []
    return [{"id": h["_id"], "form": h["_source"].get("form"), "date": h["_source"].get("file_date"),
             "ciks": h["_source"].get("ciks")} for h in hits]


def sec_hits(cusip: str, issuer: str, coupon: float | None, maturity: str | None) -> list:
    """Filings naming the CUSIP in either print form, then, for the issuer's own filings, the coupon and due year."""
    path = SEC / f"hits_{cusip}.json"
    if path.exists():
        return json.loads(path.read_text())
    rows = []
    for phrase in (f'"{cusip}"', f'"{cusip[:6]} {cusip[6:]}"'):
        rows += search({"q": phrase, "forms": FORMS})
    if not rows and coupon is not None and maturity and issuer in CIK:
        year = maturity[:4]
        for text in (f"{coupon:.3f}%", f"{coupon:.2f}%"):
            rows += search({"q": f'"{text} Notes due {year}"', "forms": FORMS, "ciks": CIK[issuer]})
            rows += search({"q": f'"{text} Senior Notes due {year}"', "forms": FORMS, "ciks": CIK[issuer]})
    seen, unique = set(), []
    for row in rows:
        if row["id"] not in seen:
            seen.add(row["id"])
            unique.append(row)
    path.write_text(json.dumps(unique))
    return unique


def filing_text(hit: dict) -> str:
    accession, name = hit["id"].split(":")
    path = SEC / f"{accession}_{name}.txt"
    if path.exists():
        return path.read_text()
    cik = str(int(hit["ciks"][0]))
    raw = get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-', '')}/{name}")
    text = re.sub(r"(?s)<(script|style).*?</\1>", " ", raw.decode("utf8", "ignore"))
    text = re.sub(r"<[^>]+>", " ", text).replace("&nbsp;", " ").replace("&#160;", " ").replace("&#xa0;", " ")
    text = re.sub(r"\s+", " ", text)
    path.write_text(text)
    return text


AMOUNT = re.compile(r"(?:U\.?S\.?)?\$\s?([0-9][0-9,\.]*)\s*(million|billion)?", re.I)
LABEL = re.compile(r"(aggregate principal amount|principal amount|size|amount offered|offering amount|face amount)", re.I)
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]


def to_usd(number: str, unit: str | None) -> float | None:
    try:
        value = float(number.rstrip(".,").replace(",", ""))
    except ValueError:
        return None
    if unit:
        value *= 1e6 if unit.lower() == "million" else 1e9
    if not 5e7 <= value <= 2e10 or value % 1e6:
        return None  # a real tranche is a round number of millions
    return value


def tranche_amount(text: str, cusip: str, coupon: float | None, maturity: str | None) -> tuple:
    """Find the size printed for this tranche. Returns (usd, rule) or (None, reason). Three rules, tried in order."""
    if coupon is None or not maturity:
        return None, "no_terms"
    year, month, day = maturity.split("-")
    # Rule 1: cover line, as in "$1,000,000,000 4.421% Notes due 2026".
    coupons = "|".join(sorted({re.escape(f"{coupon:.3f}"), re.escape(f"{coupon:.2f}"), re.escape(f"{coupon:g}")}, key=len, reverse=True))
    cover = re.search(r"\$\s?([0-9][0-9,\.]*)\s*(million|billion)?\s+(?:aggregate principal amount of\s+)?(?:(?:our|the)\s+)?(?:" + coupons
                      + r")0*\s?%[^$]{0,60}?due\s+(?:[A-Z][a-z]+\s+(?:\d+,\s+)?)?" + year, text)
    if cover:
        value = to_usd(cover.group(1), cover.group(2))
        if value:
            return value, "cover_line"
    # Rule 2: term block, a size label within 500 characters before "Maturity ... date", in a block that carries the coupon.
    date_text = f"{MONTHS[int(month) - 1]} {int(day)}, {year}"
    for match in re.finditer(r"Maturity[^$]{0,40}?" + re.escape(date_text), text):
        block = text[max(0, match.start() - 500):match.start()]
        labels = list(LABEL.finditer(block))
        for label in reversed(labels):
            amount = AMOUNT.search(block[label.end():label.end() + 80])
            if amount:
                value = to_usd(amount.group(1), amount.group(2))
                if value:
                    return value, "term_block"
    # Rule 3: a block starting at the "x.xxx% Notes due year" title, with the first size label after it.
    title = re.search(r"(?:" + coupons + r")0*\s?%[^$]{0,40}?(?:Notes|Debentures)[^$]{0,20}?due\s+(?:[A-Z][a-z]+\s+(?:\d+,\s+)?)?" + year, text)
    if title:
        tail = text[title.end():title.end() + 500]
        label = LABEL.search(tail)
        if label:
            amount = AMOUNT.search(tail[label.end():label.end() + 80])
            if amount:
                value = to_usd(amount.group(1), amount.group(2))
                if value:
                    return value, "title_block"
    return None, "no_match"


def main() -> None:
    table = universe()
    figi = fetch_figi(list(table.cusip))
    parsed = pd.DataFrame([{"cusip": c, **parse_figi(figi.get(c, []))} for c in table.cusip])
    table = table.merge(parsed, on="cusip")
    rows = []
    for number, row in enumerate(table.itertuples()):
        found = {}
        for hit in sec_hits(row.cusip, row.issuer, row.coupon, row.maturity):
            if hit["form"] not in ("FWP", "424B2", "424B5", "424B3"):
                continue
            text = filing_text(hit)
            value, rule = tranche_amount(text, row.cusip, row.coupon, row.maturity)
            if value:
                # Several filings describe one deal, so one amount per calendar month counts once.
                found.setdefault(hit["date"][:7], []).append((value, hit["id"], hit["form"], hit["date"], rule))
        deals = []
        for month, entries in sorted(found.items()):
            entries.sort(key=lambda e: (e[2] != "FWP", e[3]))
            deals.append(entries[0])
        rows.append({"cusip": row.cusip, "n_deals": len(deals),
                     "issue_amounts": json.dumps([d[0] for d in deals]),
                     "issue_dates": json.dumps([d[3] for d in deals]),
                     "amount_outstanding_usd": float(sum(d[0] for d in deals)) if deals else None,
                     "source_id": deals[0][1] if deals else None,
                     "rule": deals[0][4] if deals else None})
        if number % 25 == 0:
            print(number, row.cusip, row.ticker, rows[-1]["amount_outstanding_usd"], flush=True)
    table = table.merge(pd.DataFrame(rows), on="cusip")
    table.drop(columns=["n_c"]).to_csv(HERE / "bond_reference.csv", index=False)
    print(table[["amount_outstanding_usd", "maturity"]].notna().groupby(table.issuer).sum())
    print(table.amount_outstanding_usd.describe())


if __name__ == "__main__":
    main()
