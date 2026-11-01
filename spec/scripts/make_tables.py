"""Write LaTeX numbers and tables from tested code. Run from the spec directory."""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from posmon.data import check_daily  # noqa: E402
from posmon.ledger import RemovalRule  # noqa: E402
from posmon.pain import (cftc_pain, classify_changes, legacy_position_per_strike, ms_pain_monitor,  # noqa: E402
                         typical_price, workbook_over_under)

GEN = Path("generated")
GEN.mkdir(exist_ok=True)
macros = {}


def num(name, value, digits=0, comma=True):
    text = f"{value:,.{digits}f}" if comma else f"{value:.{digits}f}"
    macros[name] = text.replace("-", "$-$")


def percent(name, value, digits=1):
    macros[name] = f"{100 * value:.{digits}f}\\%".replace("-", "$-$")


def toy_tables():
    close = pd.Series([100, 101, 102, 101.2, 100.5, 101.5, 100.8, 101.3], dtype=float)
    vwap = pd.Series([100, 100.6, 101.6, 101.7, 100.9, 101.0, 101.2, 101.1], dtype=float)
    oi = pd.Series([1000, 1100, 1160, 1210, 1170, 1150, 1190, 1180], dtype=float)
    frame = classify_changes(close, oi)
    words = {"first_row": "start row", "new_long": "new longs", "long_off": "longs taken off", "new_short": "new shorts",
             "short_cover": "shorts covered", "none": "no label"}
    lines = []
    for day in frame.index:
        row = frame.loc[day]
        dp = "" if pd.isna(row.price_change) else f"{row.price_change:+.1f}".replace("-", "$-$")
        doi = "" if pd.isna(row.oi_change) else f"{row.oi_change:+.0f}".replace("-", "$-$")
        lines.append(f"{day} & {close[day]:.1f} & {vwap[day]:.1f} & {oi[day]:,.0f} & {dp} & {doi} & {words[row.case]} \\\\")
    (GEN / "p1_toy.tex").write_text("\n".join(lines) + "\n")
    out = ms_pain_monitor(close, vwap, oi, multiplier=1000.0, window=7)
    percent("ToyLongNew", out["long_offside_pct_new"])
    percent("ToyShortNew", out["short_offside_pct_new"])
    percent("ToyLongOI", out["long_offside_pct_oi"], 2)
    percent("ToyShortOI", out["short_offside_pct_oi"], 2)
    num("ToyLongUSD", out["long_offside_usd"])
    num("ToyShortUSD", out["short_offside_usd"])
    num("ToyShortOff", out["short_offside"], 3)


def real_data_values():
    daily = pd.read_csv("data/ty_daily.csv", parse_dates=["date"], index_col="date")
    weekly = pd.read_csv("data/ty_cftc.csv", parse_dates=["date"], index_col="date")
    tp = typical_price(daily["high"], daily["low"], daily["close"])
    p1 = ms_pain_monitor(daily["close"], tp, daily["open_interest"], multiplier=1000.0, window=30)
    num("TyLongOpen", p1["long_open"])
    num("TyShortOpen", p1["short_open"])
    num("TyLongOff", p1["long_offside"], 1)
    num("TyShortOff", p1["short_offside"], 1)
    percent("TyLongNew", p1["long_offside_pct_new"], 2)
    percent("TyShortNew", p1["short_offside_pct_new"], 2)
    percent("TyLongOI", p1["long_offside_pct_oi"], 3)
    percent("TyShortOI", p1["short_offside_pct_oi"], 3)
    num("TyLongUSD", p1["long_offside_usd"] / 1e6)
    num("TyShortUSD", p1["short_offside_usd"] / 1e6)
    num("TyLongUnmatched", p1["long_unmatched"])
    num("TyShortUnmatched", p1["short_unmatched"])
    p2 = cftc_pain(weekly["lev_money_long"], daily["close"], window=90, side="long", respect_release=False).iloc[-1]
    live = cftc_pain(weekly["lev_money_long"], daily["close"], window=90, side="long").iloc[-1]
    percent("PtwoLive", live["share_in_pain"], 2)
    num("PtwoGross", p2["gross"])
    num("PtwoOpen", p2["open"])
    num("PtwoUnmatched", p2["unmatched"])
    percent("PtwoShare", p2["share_in_pain"], 2)
    percent("PtwoCode", p2["pct_open_code"], 2)
    p5 = workbook_over_under(daily).iloc[-1]
    num("WbVwap", p5["vwap"], 6, False)
    num("WbNet", p5["net_new"])
    num("WbOver", p5["over_under"], 6, False)
    macros["WbSide"] = p5["side"]
    flags = check_daily(daily)
    num("QcOutside", flags["close_outside_range"].sum())
    num("QcEqual", flags["high_equals_low"].sum())
    num("QcMissingRange", flags["missing_range"].sum())
    num("QcMissingVolume", flags["missing_volume"].sum())
    num("QcCollapse", (daily["volume"] < 200000).sum())
    num("QcRows", len(daily))
    legacy = legacy_position_per_strike([20, 20, 20, -30, 0], [100, 105, 110, 102, 100])
    num("LegacyRemoved", sum(legacy["closed"]), 2)


def reconcile_values():
    data = json.loads(Path("data/reconcile.json").read_text())
    wb = data["workbook_vs_api"]
    num("ApiCells", wb["cells_compared"])
    num("ApiDiff", wb["cells_different"])
    num("ApiOiDates", wb["oi_dates"])
    num("ApiOiDiff", wb["oi_different"])
    si = data["goldman_si"]
    num("SiEur", si["eur_2012_07_24"], 2)
    num("SiEurZero", si["eur_zero_weeks_may_2012"])
    num("SiTwo", si["2y_2016_07_12"], 1)
    num("SiTwoZero", si["2y_zero_weeks_may_jun_2016"])
    num("SiTen", si["10y_2016_07_12"], 1)
    rates = data["deutsche_rates"]
    for key, name in (("TY", "Ty"), ("WN", "Wn"), ("FV", "Fv"), ("US", "Us"), ("ED", "Ed")):
        num(f"Db{name}Net", rates[key]["net"])
        num(f"Db{name}Chg", rates[key]["change"])
        num(f"Db{name}Pct", rates[key]["pct_oi"], 1)
    scaled = data["deutsche_scaled"]
    num("DbScaledMae", scaled["mean_abs_error"], 2)
    num("DbScaledMax", scaled["max_abs_error"], 2)
    num("DbScaledWeeks", scaled["weeks"])
    gf = data["goldman_filter"]
    for key, name in (("am_other", "Am"), ("lev", "Lev"), ("spec", "Spec")):
        row = gf[key]
        num(f"Gf{name}Slope", row["bp_per_10mm"], 1)
        percent(f"Gf{name}Corr", row["corr_6m_filtered_vs_yield"], 0)
        percent(f"Gf{name}Fwd", row["corr_score_vs_next_6m"], 0)
    am = gf["am_other"]
    num("GfTotal", am["total"])
    percent("GfUncond", am["uncond_rally"])
    num("GfUncondAvg", am["uncond_avg"], 1)
    num("GfPosN", am["pos_n"])
    percent("GfPosHit", am["pos_hit"])
    num("GfPosAvg", am["pos_avg"], 1)
    num("GfNegN", am["neg_n"])
    percent("GfNegHit", am["neg_hit"])
    num("GfNegAvg", am["neg_avg"], 1)
    num("GfLast", am["score_2019_04_30"], 2)
    percent("GfOutright", gf["outright_corr"], 0)
    num("GfVolRatio", am["filtered_sd"] / gf["spec"]["filtered_sd"], 2)
    num("GfQuarter", 0.25 * am["scale_bp"], 1)
    chart_values()
    sd = data["goldman_one_sd"]
    percent("SdRally", sd["unconditional_rally"])
    percent("SdBuy", sd["buy_hit"])
    percent("SdSell", sd["sell_hit"])
    ladder = data["natural_gas_ladder"]
    num("NgLegacy", ladder["legacy_open"][-1])
    num("NgCorrectLow", ladder["correct_open"][0])
    num("NgCorrectHigh", ladder["correct_open"][-1])
    num("NgSpotHigh", ladder["spot_high"], 2)
    lines = []
    for label, row in scaled["rows"].items():
        lines.append(f"{label} & {row['lev_read']:+.1f} & {row['lev']:+.1f} & {row['am_read']:+.1f} & {row['am']:+.1f} \\\\"
                     .replace("-", "$-$"))
    (GEN / "db_scaled.tex").write_text("\n".join(lines) + "\n")


def chart_values():
    """Statistics from the comparison with Goldman's own charts. Written by scripts/goldman_chart_check.py."""
    chart = json.loads(Path("data/goldman_chart_check.json").read_text())
    percent("GfChartLev", chart["lev_corr_combined"], 2)
    percent("GfChartLevFut", chart["lev_corr_futures"], 2)
    percent("GfChartAm", chart["am_corr_combined"], 2)
    percent("GfChartAmFut", chart["am_corr_futures"], 2)
    percent("GfChartAmZ", chart["am_z"]["corr"], 2)
    percent("GfChartSpecZ", chart["spec_z"]["corr"], 2)
    num("GfImplAm", chart["am_z"]["implied_scale"], 1)
    num("GfImplSpec", chart["spec_z"]["implied_scale"], 1)
    num("GfScaleAm", chart["am_z"]["rule_scale"], 1)
    num("GfScaleSpec", chart["spec_z"]["rule_scale"], 1)
    order = ["TU", "FV", "TY", "TN", "US", "WN"]
    lines = []
    for period in chart["real_dv01"]:
        real = chart["real_dv01"][period]
        listed = {k: real[k] == real[k] for k in order}
        def row(values):
            return " & ".join(f"{values[k]:.0f}" if listed[k] else "--" for k in order)
        label = period.replace("-", "--")
        lines.append(f"{label} & Real DV01 & {row(real)} \\\\")
        lines.append(f" & Fitted, leveraged funds & {row(chart['weights']['lev'][period])} \\\\")
        lines.append(f" & Fitted, asset managers & {row(chart['weights']['am_other'][period])} \\\\")
    (GEN / "gf_weights.tex").write_text("\n".join(lines) + "\n")


def write_macros():
    text = "\n".join(f"\\newcommand{{\\{name}}}{{{value}}}" for name, value in sorted(macros.items()))
    (GEN / "numbers.tex").write_text(text + "\n")


if __name__ == "__main__":
    _ = RemovalRule
    toy_tables()
    real_data_values()
    reconcile_values()
    write_macros()
    print(len(macros), "macros written")
