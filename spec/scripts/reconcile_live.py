"""Rebuild published numbers from public data. Writes data/reconcile.json.

Run from the spec directory:  python scripts/reconcile_live.py
It needs internet access to publicreporting.cftc.gov and fred.stlouisfed.org.
"""
import io
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from posmon.data import check_cftc, fetch_cftc  # noqa: E402
from posmon.indicators import (db_scaled, filtered_change, filtered_residual, forward_stats,  # noqa: E402
                               one_sd_rule, sentiment_index)
from posmon.pain import harmonise_weekly, legacy_ladder  # noqa: E402
from posmon.stats import forward_change, reversal_hits  # noqa: E402

UST = {"TU": "042601", "FV": "044601", "TY": "043602", "TN": "043607", "US": "020601", "WN": "020604"}
# The yield that decides "with the market" for each contract. Goldman's charts fix these choices.
YIELD = {"TU": "DGS2", "FV": "DGS5", "TY": "DGS7", "TN": "DGS10", "US": "DGS20", "WN": "DGS30"}
# Goldman's asset manager series loads only on these contracts. Its other series use all six.
AM_CONTRACTS = ("TY", "US")


def dv01_series():
    """Weekly dollars per basis point per contract, from data/treasury_futures_dv01.csv."""
    long = pd.read_csv("data/treasury_futures_dv01.csv", parse_dates=["date"])
    return long.pivot(index="date", columns="contract", values="dv01_usd")


def fred(series, start, end):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}&cosd={start}&coed={end}"
    text = urllib.request.urlopen(url, timeout=60).read().decode()
    frame = pd.read_csv(io.StringIO(text), parse_dates=["observation_date"], index_col="observation_date")
    return pd.to_numeric(frame[series], errors="coerce")


def legacy_net(code, start, end, basis="futures"):
    report = fetch_cftc("legacy", code, start=start, end=end, basis=basis)
    return report.noncomm_long - report.noncomm_short, report


def workbook_vs_api():
    weekly = pd.read_csv("data/ty_cftc.csv", parse_dates=["date"], index_col="date")
    daily = pd.read_csv("data/ty_daily.csv", parse_dates=["date"], index_col="date")
    tff = fetch_cftc("tff", "043602", "2014-07-01", "2015-02-01")
    legacy = fetch_cftc("legacy", "043602", "2014-07-01", "2015-02-01")
    pairs = [(c, tff) for c in ("dealer_long", "dealer_short", "asset_mgr_long", "asset_mgr_short", "lev_money_long",
                                "lev_money_short", "other_rept_long", "other_rept_short", "nonrept_long",
                                "nonrept_short")] + [(c, legacy) for c in ("noncomm_long", "noncomm_short",
                                                                           "comm_long", "comm_short")]
    mismatch = 0
    cells = 0
    for column, source in pairs:
        joined = pd.concat([weekly[column], source[column]], axis=1, join="inner")
        mismatch += int((joined.iloc[:, 0] != joined.iloc[:, 1]).sum())
        cells += len(joined)
    oi = pd.concat([daily["open_interest"], tff["open_interest"]], axis=1, join="inner").dropna()
    return {"cells_compared": cells, "cells_different": mismatch, "oi_dates": len(oi),
            "oi_different": int((oi.iloc[:, 0] != oi.iloc[:, 1]).sum()),
            "api_dates_missing_from_workbook": [d.date().isoformat() for d in tff.index.difference(weekly.index)
                                                if weekly.index[0] <= d <= weekly.index[-1]],
            "tff_identity_failures": len(check_cftc(tff, "tff")), "legacy_identity_failures": len(check_cftc(legacy, "legacy"))}


def goldman_si():
    out = {}
    net, _ = legacy_net("099741", "2006-01-01", "2012-12-31")
    si = sentiment_index(net, 156)
    out["eur_2012_07_24"] = float(si.loc["2012-07-24"])
    out["eur_zero_weeks_may_2012"] = int((si.loc["2012-05-01":"2012-06-30"] == 0).sum())
    for label, code in (("2y", "042601"), ("5y", "044601"), ("10y", "043602")):
        net, _ = legacy_net(code, "2012-01-01", "2016-12-31")
        si = sentiment_index(net, 156)
        out[f"{label}_2016_07_12"] = float(si.loc["2016-07-12"])
        out[f"{label}_zero_weeks_may_jun_2016"] = int((si.loc["2016-05-15":"2016-06-20"] == 0).sum())
    return out


def deutsche_rates():
    out = {}
    for label, code in (("TY", "043602"), ("WN", "020604"), ("FV", "044601"), ("US", "020601"), ("ED", "132741")):
        net, report = legacy_net(code, "2017-04-01", "2017-05-20")
        out[label] = {"net": int(net.loc["2017-05-09"]),
                      "change": int(net.loc["2017-05-09"] - net.loc["2017-05-02"]),
                      "pct_oi": float(100 * net.loc["2017-05-09"] / report.open_interest.loc["2017-05-09"])}
    return out


def deutsche_scaled():
    chart = {"EUR": ("099741", -3.0, 10.0), "JPY": ("097741", -0.3, -5.7), "GBP": ("096742", -1.2, -6.5),
             "CHF": ("092741", -2.3, -1.5), "AUD": ("232741", 2.7, -0.5), "NZD": ("112741", -4.5, -3.9),
             "CAD": ("090741", -8.2, -5.2), "MXN": ("095741", 6.5, 5.4), "2Y": ("042601", 2.0, 6.8),
             "5Y": ("044601", -4.8, 6.8), "10Y": ("043602", -2.1, 3.9)}
    rows, errors = {}, []
    for label, (code, lev_read, am_read) in chart.items():
        report = fetch_cftc("tff", code, "2013-05-09", "2017-05-09")
        lev = float(db_scaled(report.lev_money_long - report.lev_money_short, len(report)).iloc[-1])
        am = float(db_scaled(report.asset_mgr_long - report.asset_mgr_short, len(report)).iloc[-1])
        rows[label] = {"lev": lev, "lev_read": lev_read, "am": am, "am_read": am_read}
        errors += [abs(lev - lev_read), abs(am - am_read)]
    return {"rows": rows, "mean_abs_error": float(np.mean(errors)), "max_abs_error": float(np.max(errors)),
            "weeks": len(report)}


def goldman_series(basis="combined"):
    """Build the three Goldman filtered series and their residual tables."""
    yields = pd.DataFrame({k: fred(v, "2006-01-01", "2019-12-31") for k, v in YIELD.items()}).ffill() * 100.0
    ten_year = fred("DGS10", "2006-01-01", "2019-12-31").ffill() * 100.0
    tff = {k: fetch_cftc("tff", c, "2006-01-01", "2019-05-07", basis=basis) for k, c in UST.items()}
    legacy = {k: fetch_cftc("legacy", c, "2006-01-01", "2019-05-07", basis=basis) for k, c in UST.items()}
    groups = {
        "am_other": {k: tff[k].asset_mgr_long - tff[k].asset_mgr_short + tff[k].other_rept_long - tff[k].other_rept_short
                     for k in AM_CONTRACTS},
        "lev": {k: t.lev_money_long - t.lev_money_short for k, t in tff.items()},
        "spec": {k: t.noncomm_long - t.noncomm_short for k, t in legacy.items()},
    }
    index = tff["TY"].index
    level = ten_year.reindex(index, method="ffill")
    dv01 = {k: v.dropna() for k, v in dv01_series().items()}
    out = {}
    for name, nets in groups.items():
        nets = {k: v.reindex(index) for k, v in nets.items()}
        filtered = filtered_change(nets, yields, dv01)
        out[name] = {"filtered": filtered, "table": filtered_residual(ten_year, filtered)}
    return out, level


def goldman_filter():
    series, level = goldman_series()
    results = {}
    for name, item in series.items():
        filtered, table = item["filtered"], item["table"]
        ahead = level.shift(-26) - level
        usable = table["score"].notna() & ahead.notna()
        results[name] = {
            "bp_per_10mm": float(table["slope"].iloc[0] * 10.0),
            "scale_bp": float(table["scale"].iloc[0]),
            "filtered_sd": float(filtered.std()),
            "corr_6m_filtered_vs_yield": float(filtered.rolling(26).sum().corr(level.diff(26))),
            "corr_score_vs_next_6m": float(table["score"][usable].corr(ahead[usable])),
            "score_2019_04_30": float(table["score"].loc["2019-04-30"]),
            **forward_stats(level, table["signal"]),
        }
    usable = level.diff(26).notna() & level.shift(-26).notna()
    results["outright_corr"] = float(level.diff(26)[usable].corr((level.shift(-26) - level)[usable]))
    return results


def goldman_one_sd():
    """Base rate on the sample pinned by Goldman's Exhibit 1, and the closest position recipe found.

    Sample: Tuesday DGS10, June 2009 to January 2018, with a zero change counted as a rally.
    Position: net non-commercial contracts summed over TU, FV, TY and US, combined report. It is not pinned.
    """
    start, end = "2009-06-01", "2018-01-31"
    yields = fred("DGS10", "2009-05-01", "2018-03-31").ffill() * 100.0
    parts = [legacy_net(UST[k], start, end, basis="combined")[0] for k in ("TU", "FV", "TY", "US")]
    position = pd.concat(parts, axis=1).sum(axis=1)
    level = yields.reindex(position.index, method="ffill")
    full = yields.reindex(pd.date_range(start, "2018-03-31", freq="W-TUE"), method="ffill")
    ahead = (full.shift(-4) - full).reindex(position.index)
    signal = one_sd_rule(position)
    usable = ahead.notna()
    return {"unconditional_rally": float((ahead[usable] <= 0).mean()), "n": int(usable.sum()),
            "buy_hit": float((ahead[usable & (signal > 0)] <= 0).mean()), "buy_count": int((usable & (signal > 0)).sum()),
            "sell_hit": float((ahead[usable & (signal < 0)] > 0).mean()), "sell_count": int((usable & (signal < 0)).sum())}


def natural_gas_ladder():
    spot = fred("DHHNGSP", "2015-06-01", "2018-03-01").dropna()
    report = fetch_cftc("disaggregated", "023651", "2015-06-01", "2018-03-01")
    as_of = pd.Timestamp("2018-01-30")
    trading_days = spot.loc[:as_of].index
    ratios = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
    frame = pd.DataFrame({"price": spot.loc[:as_of],
                          "change": harmonise_weekly(report["money_mgr_long"], trading_days).diff()}).dropna().iloc[-126:]
    ladder = legacy_ladder(frame["change"].values, frame["price"].values, 3.19, ratios)
    return {"ratios": ratios, "legacy_open": ladder["legacy_open"].round(0).tolist(),
            "correct_open": ladder["correct_open"].round(0).tolist(),
            "spot_low": float(frame["price"].min()), "spot_high": float(frame["price"].max())}


def market_history():
    rows = {}
    for label, code in (("Eurodollar", "132741"), ("SOFR 3M", "134741"), ("NG", "023651"), ("TY", "043602")):
        report = fetch_cftc("legacy", code)
        rows[label] = {"code": code, "first": report.index[0].date().isoformat(), "last": report.index[-1].date().isoformat(),
                       "first_name": report.market_name.iloc[0], "last_name": report.market_name.iloc[-1]}
    return rows


def main():
    result = {}
    for name, job in (("workbook_vs_api", workbook_vs_api), ("goldman_si", goldman_si), ("deutsche_rates", deutsche_rates),
                      ("deutsche_scaled", deutsche_scaled), ("goldman_filter", goldman_filter),
                      ("goldman_one_sd", goldman_one_sd), ("natural_gas_ladder", natural_gas_ladder),
                      ("market_history", market_history)):
        result[name] = job()
        print(name, "done")
    Path("data/reconcile.json").write_text(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    main()
