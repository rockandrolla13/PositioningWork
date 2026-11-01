"""Command line for the two jobs a production machine runs.

  python -m posmon.cli fetch --report tff --code 043602 --start 2006-01-01 --out store/tff_043602.csv
  python -m posmon.cli p1 --daily store/ty_daily.csv --multiplier 1000 --out out/p1_ty.csv
  python -m posmon.cli p2 --weekly store/tff_043602.csv --field lev_money_long --daily store/ty_daily.csv --out out/p2.csv
  python -m posmon.cli si --report store/legacy_043602.csv --long noncomm_long --short noncomm_short --out out/si.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .data import check_cftc, check_daily, fetch_cftc
from .indicators import db_scaled, extreme_flags, sentiment_index
from .ledger import RemovalRule
from .pain import cftc_pain, ms_pain_monitor, typical_price


def _read(path: str) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=[0], index_col=0)


def _write(frame: pd.DataFrame, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path)
    print(f"wrote {path}: {len(frame)} rows")


def fetch(args) -> None:
    report = fetch_cftc(args.report, args.code, args.start, args.end, args.basis)
    problems = check_cftc(report, args.report)
    if len(problems):
        print(problems.to_string())
    _write(report, args.out)


def p1(args) -> None:
    daily = _read(args.daily)
    flags = check_daily(daily)
    print("data flags:", flags.sum().to_dict())
    vwap = daily["vwap"] if "vwap" in daily else typical_price(daily["high"], daily["low"], daily["close"])
    rows = []
    for end in range(args.window + 1, len(daily) + 1):
        part = daily.iloc[:end]
        result = ms_pain_monitor(part["close"], vwap.iloc[:end], part["open_interest"], args.multiplier, args.fx, args.window,
                                 RemovalRule(args.rule))
        rows.append({k: v for k, v in result.items() if not k.endswith("book")})
    _write(pd.DataFrame(rows).set_index("as_of"), args.out)


def p2(args) -> None:
    daily = _read(args.daily)
    weekly = _read(args.weekly)
    _write(cftc_pain(weekly[args.field], daily["close"], args.window, RemovalRule(args.rule), args.side, not args.replay), args.out)


def si(args) -> None:
    report = _read(args.report)
    net = report[args.long] - report[args.short]
    table = extreme_flags(sentiment_index(net, args.weeks))
    table.insert(0, "si", sentiment_index(net, args.weeks))
    table.insert(0, "net", net)
    table["db_scaled"] = db_scaled(net)
    _write(table, args.out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(required=True)
    one = sub.add_parser("fetch")
    one.add_argument("--report", required=True, choices=["tff", "legacy", "disaggregated"])
    one.add_argument("--code", required=True)
    one.add_argument("--start", default="1986-01-01")
    one.add_argument("--end", default="2100-01-01")
    one.add_argument("--basis", default="futures", choices=["futures", "combined"])
    one.add_argument("--out", required=True)
    one.set_defaults(run=fetch)
    two = sub.add_parser("p1")
    two.add_argument("--daily", required=True)
    two.add_argument("--multiplier", type=float, required=True)
    two.add_argument("--fx", type=float, default=1.0)
    two.add_argument("--window", type=int, default=30)
    two.add_argument("--rule", default="pro_rata")
    two.add_argument("--out", required=True)
    two.set_defaults(run=p1)
    three = sub.add_parser("p2")
    three.add_argument("--weekly", required=True)
    three.add_argument("--field", required=True)
    three.add_argument("--daily", required=True)
    three.add_argument("--window", type=int, default=126)
    three.add_argument("--rule", default="pro_rata")
    three.add_argument("--side", default="long", choices=["long", "short"])
    three.add_argument("--replay", action="store_true", help="ignore the release rule, to match old output")
    three.add_argument("--out", required=True)
    three.set_defaults(run=p2)
    four = sub.add_parser("si")
    four.add_argument("--report", required=True)
    four.add_argument("--long", required=True)
    four.add_argument("--short", required=True)
    four.add_argument("--weeks", type=int, default=156)
    four.add_argument("--out", required=True)
    four.set_defaults(run=si)
    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
