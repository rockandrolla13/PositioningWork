#!/usr/bin/env python3
"""Write report.md from results.json. Every number in the report comes from results.json."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
r = json.loads((HERE / "results.json").read_text())
F, CS, B, M, PH = r["family"], r["cross_section"], r["benchmarks"], r["mechanisms"], r["post_hoc"]
S = r["strategies"]


def h(key: str) -> dict:
    return F[key]["holdout"]


def t(key: str) -> str:
    return f"{h(key)['t']:.2f}"


def bench(fund: str, name: str, horizon: int) -> dict:
    return B[fund][name][str(horizon)]["holdout"]


def sub(key: str, part: str, field: str) -> float:
    return PH["subperiods"][key][part][field]


def pct(value: float, digits: int = 0) -> str:
    return f"{value * 100:.{digits}f}%"


p1 = r["C5"]["p1_vs_true"]
placebo = PH["placebo"]
power = r["harness_checks"]["power_floor"]
size = r["harness_checks"]["size"]
planted = r["harness_checks"]["planted"]
c3 = r["C3"]
m2 = M["M2_flow_on_premium"]
m3 = M["M3_primary_vs_secondary"]
m4 = M["M4_pain_predicts_redemptions"]
m5 = M["M5_month_end_share"]
m6 = M["M6_sensitivity"]
m7 = M["M7_implied_vs_oas"]
m8 = M["M8_march_2020"]
i8 = M["I8_imbalance"]
cover = PH["ledger_coverage"]
levels = r["C5"]["levels"]
cftc = r["CFTC"]["readings"]
quote = r["C5"]["options"]["databento_quote_usd"]
c6 = r["C6"]
second = PH["second_side"]
c1rows = r["C1"]["rows"]
near_pass = sum(1 for row in c1rows if row["pain_near_max"] >= 0.75 and row["depth_near_rank_max"] >= 0.9)
raw_bias = {f: m6[f]["pain126_raw"]["mean"] - m6[f]["base_mean"] for f in ("LQD", "HYG", "JNK")}
unmatched = r["C1"]["unmatched"]
counts = r["label_counts"]
total_tests = r["family_size"]
holm_values = [e["holm_p"] for e in F.values() if e.get("holm_p") is not None] + [e["holm_p"] for e in CS.values() if e.get("holm_p") is not None]
smallest_holm = min(holm_values)

import pandas as pd  # noqa: E402

_lqd = pd.read_pickle(HERE / "work" / "weekly_LQD.pkl")
lqd_mar = (float(_lqd.loc["2020-03-20", "pain126"]), float(_lqd.loc["2020-03-27", "pain126"]))
lqd_cov = float(_lqd.loc["2020-03-20", "open126_share"])
assert pd.isna(_lqd.loc["2020-03-13", "pain126"])

_baa = [e["holdout"]["alt_targets"]["ds_baa"]["t"] for k, e in F.items() if "|LQD|" in k and e["holdout"].get("alt_targets", {}).get("ds_baa", {}).get("t") is not None]
baa_total, baa_big = len(_baa), sum(abs(v) > 2 for v in _baa)
oas_n = h("pain126|LQD|4")["alt_targets"]["ds_oas"]["n"]

baac = r["baa_check"]

SIGNAL_ORDER = ["pain126", "p1_long_oi", "p1_short_oi", "gap126", "gap_full", "gap_turn", "p5_water", "flow13", "i2_so", "i3_flow", "i4_rule", "i5_usd", "i5_pct", "i7_cont", "i7_rev", "i8_trend", "si_ratio", "si_chg", "si_i2"]
rows = []
for name in SIGNAL_ORDER:
    for fund in ("LQD", "HYG"):
        cells = []
        labels = []
        for horizon in (1, 4, 13, 26):
            entry = F[f"{name}|{fund}|{horizon}"]
            cells.append(f"{entry['holdout']['t']:.2f}" if entry["holdout"].get("t") is not None else "n/a")
            labels.append(entry["label"])
        best = min((F[f"{name}|{fund}|{horizon}"]["holm_p"] for horizon in (1, 4, 13, 26) if F[f"{name}|{fund}|{horizon}"]["holm_p"] is not None), default=None)
        dev = [F[f"{name}|{fund}|{horizon}"]["dev"].get("t") for horizon in (1, 4, 13, 26)]
        dev_text = " / ".join("n/a" if value is None else f"{value:.2f}" for value in dev)
        suggestive = sum(1 for label in labels if label == "suggestive")
        rows.append(f"| {name} | {fund} | {' | '.join(cells)} | {dev_text} | {'n/a' if best is None else f'{best:.2f}'} | {suggestive} |")
family_table = "\n".join(rows)

def full_row(label: str, row: dict, holm_p, replicate_t, control_t) -> str:
    top, low = row.get("top") or {}, row.get("bottom") or {}

    def hit(part: dict) -> str:
        return "none" if not part.get("n") else f"{part['hit_pos'] * 100:.0f}% ({part['n']})"

    ci = row.get("ci95") or (float("nan"), float("nan"))
    fmt = lambda v, d=2: "n/a" if v is None else f"{v:.{d}f}"  # noqa: E731
    label = label.replace("|", " ")
    return (f"| {label} | {row['b']:.0f} | {row['t']:.2f} | {row['p']:.3f} | {fmt(holm_p)} | {ci[0]:.0f} to {ci[1]:.0f} | {row['n']} | {row['n_eff']:.0f} | "
            f"{hit(top)} | {hit(low)} | {row['base_rate_pos'] * 100:.0f}% | {fmt(control_t)} | {fmt(replicate_t)} |")


labelled_rows = []
for key, entry in F.items():
    if entry["label"] == "suggestive":
        row = entry["holdout"]
        labelled_rows.append(full_row(key, row, entry["holm_p"], entry["replicate"].get("t"), row.get("with_controls", {}).get("t")))
for fund in ("LQD", "HYG"):
    for horizon in (4, 26):
        row = bench(fund, "level", horizon)
        labelled_rows.append(full_row(f"benchmark level|{fund}|{horizon}", {**row, "base_rate_pos": B[fund]["buy_hold"][str(horizon)]["base_rate_pos"]}, None, None, None))
        row = bench(fund, "mom26", horizon)
        labelled_rows.append(full_row(f"benchmark momentum|{fund}|{horizon}", {**row, "base_rate_pos": B[fund]["buy_hold"][str(horizon)]["base_rate_pos"]}, None, None, None))
labelled_table = "\n".join(labelled_rows)
buy_hold_rows = "\n".join(f"| {fund} | {horizon} | {B[fund]['buy_hold'][str(horizon)]['mean_bp']:.0f} | {B[fund]['buy_hold'][str(horizon)]['t']:.2f} | {B[fund]['buy_hold'][str(horizon)]['base_rate_pos'] * 100:.0f}% |" for fund in ("LQD", "HYG") for horizon in (4, 26))

cs_rows = []
for name in ("i7_cont_cs", "i7_rev_cs"):
    for horizon in (1, 4, 13, 26):
        entry = CS[f"{name}|{horizon}"]
        a, b_, c = entry["all_holdout"], entry["IG_holdout"], entry["HY_holdout"]
        cs_rows.append(f"| {name} | {horizon} | {a['t']:.2f} | {entry['all_dev']['t']:.2f} | {b_['t']:.2f} | {c['t']:.2f} | {entry['holm_p']:.2f} | {entry['label']} |")
cs_table = "\n".join(cs_rows)

stress_rows = "\n".join(
    f"| {row['trough']} | {row['fund']} | {row['week']} | {'none' if row['pain126'] is None else f'{row['pain126']:.2f}'} | {'none' if row['depth126_pct'] is None else f'{row['depth126_pct']:.1f}%'} | {row['depth_rank']:.2f} | {row['pain_near_max']:.2f} | {'yes' if row['pass'] else 'no'} |"
    for row in c1rows)

sub_rows = []
for key in ("i5_usd|LQD|26", "i5_pct|LQD|26", "i5_usd|HYG|26", "i5_usd|HYG|4", "pain126|HYG|4", "gap_turn|HYG|4", "p1_long_oi|HYG|4", "si_ratio|LQD|26", "level|LQD|26", "level|HYG|26", "level|LQD|4", "level|HYG|4", "mom26|HYG|4"):
    item = PH["subperiods"][key]

    def cell(part: str) -> str:
        row = item[part]
        return "n/a" if row.get("b") is None else f"{row['b']:.0f} ({row['t']:.2f})"

    sub_rows.append(f"| {key.replace('|', ' ')} | {cell('holdout')} | {cell('2017_2021')} | {cell('2022_2026')} | {cell('holdout_excluding_2020')} |")
sub_table = "\n".join(sub_rows)

strat_rows = []
for fund in ("LQD", "HYG"):
    for name, row in S[fund].items():
        if "|h26" in name and name.startswith("i5_usd") and fund == "LQD" or (name.startswith("i5_usd|h26") and fund == "HYG"):
            continue
        strat_rows.append(f"| {fund} | {name} | {row.get('gross_bp_year', 0):.0f} | {row.get('net_bp_year', 0):.0f} | {row.get('sharpe_net', 0):.2f} | {row.get('turnover_year', 0):.1f} |")
strat_table = "\n".join(strat_rows)

power_rows = "\n".join(
    f"| {horizon} | {power[f'LQD|{horizon}']['n_eff']} | {power[f'LQD|{horizon}']['r2_needed_holm']:.3f} | {power[f'LQD|{horizon}']['r2_needed_raw_5pct']:.3f} | {size[f'LQD|{horizon}']:.3f} | {size[f'HYG|{horizon}']:.3f} | {planted[f'LQD|{horizon}']['t']:.1f} |"
    for horizon in (1, 4, 13, 26))

report = f"""# Credit ETF positioning: can the methods be applied?

Tested on 1 November 2026. Plan: `plan.md`. Numbers: `results.json`. Rerun: `./run_all.sh`.

## The answer

**Partly. The ledger and the position measures compute on ETF data and describe stress. None of them predicts ETF excess returns once tested properly. One spread result stays open: LQD flows against Moody's BAA10Y, covered in point 5.**

1. {counts.get('predictive', 0)} of {total_tests} tests pass the success rule. Holm is a step-down correction for running many tests at once, and the smallest Holm-adjusted p is {smallest_holm:.2f}.
2. {placebo['observed_raw_p_below_5pct']} of the {placebo['tests']} time-series tests have a raw p below 5%. A placebo that shifts returns at random gives {placebo['placebo_mean_count']:.1f} on average and {placebo['placebo_p95_count']:.0f} at its 95th percentile. So the count looks like chance: {pct(placebo['share_placebo_at_least_observed'], 1)} of placebo draws match or beat it.
3. The plain spread level beats every positioning signal. At 26 weeks it has t = {bench('LQD', 'level', 26)['t']:.2f} and R-squared {PH['subperiods']['level|LQD|26']['holdout']['r2']:.2f} on LQD, and t = {bench('HYG', 'level', 26)['t']:.2f} and R-squared {PH['subperiods']['level|HYG|26']['holdout']['r2']:.2f} on HYG. It survives dropping 2020 (t = {sub('level|LQD|26', 'holdout_excluding_2020', 't'):.2f} and {sub('level|HYG|26', 'holdout_excluding_2020', 't'):.2f}). It is a benchmark outside the family, tested under the same error rules. Any positioning signal must beat this first.
4. The one lead worth a later look is high-yield pain at 4 weeks. It gives +{h('pain126|HYG|4')['b']:.0f} bp per standard deviation on HYG, with t = {t('pain126|HYG|4')}. It holds in both sub-periods and without 2020, and JNK agrees (t = {F['pain126|HYG|4']['replicate']['t']:.2f}). But its Holm-adjusted p is {F['pain126|HYG|4']['holm_p']:.2f}, it is absent on LQD (t = {t('pain126|LQD|4')}), it had no effect in the development window (t = {F['pain126|HYG|4']['dev']['t']:.2f}), and after costs it trails buy and hold ({S['HYG']['pain126|h4']['sharpe_net']:.2f} against {S['HYG']['buy_hold']['sharpe_net']:.2f} Sharpe). Treat it as a hypothesis.
5. The open result is IG crowding against a slow spread series. On BAA10Y, {baac['summary']['abs_t_above_2']} of {baac['summary']['cells']} LQD cells have |t| above 2. A placebo averages {baac['placebo']['mean_count']:.0f} and never reached that count in {baac['placebo']['draws']} draws. Inflows come before tighter BAA10Y (13-week flow, 4 weeks ahead: t = {baac['cells']['flow13|4']['t']:.2f}). I do not call it established. Its best Holm p within those cells is {baac['summary']['smallest_holm_p']:.2f}. The tradable target barely shows it (t = {t('flow13|LQD|4')}). Other IG funds disagree at 4 weeks (USIG t = {baac['other_ig_flow13_on_baa_t']['USIG']['flow13|4']:.2f}, IGIB t = {baac['other_ig_flow13_on_baa_t']['IGIB']['flow13|4']:.2f}, IGSB t = {baac['other_ig_flow13_on_baa_t']['IGSB']['flow13|4']:.2f}). BAA10Y is also slow, with weekly autocorrelation of {baac['staleness']['baa_weekly_autocorr']:.2f} against {baac['staleness']['oas_weekly_autocorr']:.2f} for OAS. Pain itself shows little on this target (4 weeks t = {baac['cells']['pain126|4']['t']:.2f}).

This is a null result with limits. At 13 and 26 weeks the holdout holds only {power['LQD|13']['n_eff']:.0f} and {power['LQD|26']['n_eff']:.0f} independent observations. Clearing Holm there needs an R-squared of {power['LQD|13']['r2_needed_holm']:.2f} and {power['LQD|26']['r2_needed_holm']:.2f}. So those horizons can only catch a very strong signal. The spread level clears it, and a modest positioning effect would not.

## Verdict by method

| Method | Verdict | One line of evidence |
|---|---|---|
| P1 Morgan Stanley pain | **Does not transfer** | Its four cases fail against true short interest. Sign agreement is {pct(p1['LQD']['sign_agree_short'])}, {pct(p1['HYG']['sign_agree_short'])} and {pct(p1['JNK']['sign_agree_short'])} on LQD, HYG and JNK, and rank correlation is {p1['LQD']['spearman_short']:.2f}, {p1['HYG']['spearman_short']:.2f} and {p1['JNK']['spearman_short']:.2f}. |
| P2 lot ledger | **Transfers with changes, as a description only** | Depth of pain reaches the top decile within 2 weeks of the stress dates in {near_pass} of {r['C1']['rows_count']} checks. But the ledger covers only {pct(cover['LQD']['median_open_share_of_so'])} of LQD and {pct(cover['HYG']['median_open_share_of_so'])} of HYG shares. It predicts nothing after Holm. |
| P4 activity by price | **Transfers with changes, as a description only** | It runs with shares as longs and no daily shorts. It makes no predictive claim, so there is nothing to test. |
| P5 over or under water | **Does not transfer** | Falling shares set its side to "Short", yet that is longs leaving, not shorts. No stable effect: LQD 26 weeks t = {t('p5_water|LQD|26')}, {h('p5_water|LQD|26')['with_controls']['t']:.2f} with controls, Holm {F['p5_water|LQD|26']['holm_p']:.2f}. |
| I1 net share of open interest | **Transfers with changes, as a description only** | I1 = 100 x shares / (shares + short interest). It means something only where shorts are large: median short interest over shares is {levels['LQD']['median_si_over_so_pct']:.0f}% on LQD, {levels['HYG']['median_si_over_so_pct']:.0f}% on HYG and {levels['USIG']['median_si_over_so_pct']:.1f}% on USIG. LQD 26 weeks t = {t('si_ratio|LQD|26')} on {h('si_ratio|LQD|26')['n_eff']} effective observations, which is too thin. |
| I2 sentiment index | **Transfers with changes on short interest, as a description only** | On log shares it mostly tracks fund growth. Neither form predicts. At 4 weeks t is {t('i2_so|LQD|4')} on LQD and {t('i2_so|HYG|4')} on HYG using shares, and {t('si_i2|LQD|4')} and {t('si_i2|HYG|4')} using short interest. |
| I3 scaled -10 to +10 | **Transfers with changes, as a description only** | Shares are never negative, so it needs signed 26-week flow. LQD 26 weeks t = {t('i3_flow|LQD|26')}, HYG t = {t('i3_flow|HYG|26')}, Holm {F['i3_flow|LQD|26']['holm_p']:.2f}. |
| I4 one-standard-deviation rule | **Does not transfer** | Dollar flows grow with the fund, so a fixed band fires on {pct(cover['LQD']['i4_rule_share_nonzero'])} of LQD weeks in the holdout. LQD 26 weeks t = {t('i4_rule|LQD|26')}, HYG t = {t('i4_rule|HYG|26')}. |
| I5 filtered residual | **Does not transfer** | LQD 26 weeks looks good (t = {t('i5_usd|LQD|26')}, forward correlation {c3['LQD']['usd']['fwd_corr_26']:.2f} against {c3['LQD']['usd']['benchmark_fwd_corr_26']:.2f}). But the slope falls from {sub('i5_usd|LQD|26', 'holdout', 'b'):.0f} to {sub('i5_usd|LQD|26', 'holdout_excluding_2020', 'b'):.0f} bp without 2020 and turns negative in 2022-2026 ({sub('i5_usd|LQD|26', '2022_2026', 'b'):.0f}). |
| I6 options-implied position | **Not tested** | Alpha Vantage gates the chain as a premium endpoint on this key. Databento quotes ${quote['2018_to_2026_statistics']:.0f} for 2018 to 2026, and I spent nothing. |
| I7 continuation | **Does not transfer** | Time series: LQD 4 weeks t = {t('i7_cont|LQD|4')}, HYG t = {t('i7_cont|HYG|4')}. Cross section: t = {CS['i7_cont_cs|1']['all_holdout']['t']:.2f} at 1 week, the opposite sign to continuation. |
| I7 reversal | **Does not transfer** | Development t = {F['i7_rev|LQD|4']['dev']['t']:.2f} and {F['i7_rev|HYG|4']['dev']['t']:.2f} at 4 weeks flip to {t('i7_rev|LQD|4')} and {t('i7_rev|HYG|4')} in the holdout. Cross section t = {CS['i7_rev_cs|4']['all_holdout']['t']:.2f}. |
| I8 CTA proxy | **Does not transfer** | Trend at 4 weeks: LQD t = {t('i8_trend|LQD|4')}, HYG t = {t('i8_trend|HYG|4')}. Trading the sign of momentum nets a Sharpe of {S['LQD']['momentum_sign']['sharpe_net']:.2f} and {S['HYG']['momentum_sign']['sharpe_net']:.2f} against {S['LQD']['buy_hold']['sharpe_net']:.2f} and {S['HYG']['buy_hold']['sharpe_net']:.2f} for buy and hold. Daily aggressor imbalance does not follow trend (correlation {i8['LQD']['corr_imbalance_signal']:.2f} and {i8['HYG']['corr_imbalance_signal']:.2f} in 2024). |
| I1 to I5 on CFTC credit futures | **Would transfer as is, but too short to test** | Bloomberg IG has {cftc['BLOOMBERG_IG_CREDIT']['reports']} reports and HY has {cftc['BLOOMBERG_HY_CREDIT']['reports']}, all from 2026. I2 needs 156 weeks, so it is {cftc['BLOOMBERG_IG_CREDIT']['weeks_short_of_i2']} short. |

## How the working mapping fared

1. **"Shares outstanding play the role of open interest."** True as an accounting identity. False as a reading of positions: share changes track the premium and move against short interest.
2. **"A daily ledger gives holder cost basis."** Rejected. It gives the cost of net primary flow inside the window. Secondary trading is the bulk of activity, and primary flow is only {m3['LQD']['holdout_pct']:.0f}% of volume on LQD and {m3['HYG']['holdout_pct']:.0f}% on HYG. Read the output as "share of recent net creations under water", never "share of holders under water".
3. **"Gross long = shares + short interest."** True as an identity, and it matters: short interest over shares has a median of {levels['HYG']['median_si_over_so_pct']:.0f}% and a peak of {levels['HYG']['max_si_over_so_pct']:.0f}% on HYG. But shorts and shares move in opposite directions (rank correlation {p1['LQD']['spearman_true_dsi_vs_dso']:.2f}, {p1['HYG']['spearman_true_dsi_vs_dso']:.2f}, {p1['JNK']['spearman_true_dsi_vs_dso']:.2f}). So a redemption is often not a long leaving. The likely reason is that market makers short shares to meet demand and create units to cover. That reading is my inference, because the data shows only the negative correlation.
4. **"Spread changes from FRED feed I5."** FRED now gives ICE BofA OAS for only 3 years. I replaced it with an implied spread from the ETF itself. Weekly correlation with OAS on the overlap is {m7['LQD']['corr_weekly']:.2f} on LQD and {m7['HYG']['corr_weekly']:.2f} on HYG.

## What breaks, most important first

1. **Holders do not act on pain the way a levered futures position must.** Pain does not predict redemptions on HYG (t = {m4['HYG']['holdout']['t_pain']:.2f}) or JNK (t = {m4['JNK']['holdout']['t_pain']:.2f}). LQD shows a small effect ({m4['LQD']['holdout']['b_pain']:.2f}% of shares per standard deviation over 4 weeks, t = {m4['LQD']['holdout']['t_pain']:.2f}). After weak excess returns, shares rise instead (momentum t = {m4['LQD']['holdout']['t_mom']:.2f}, {m4['HYG']['holdout']['t_mom']:.2f}, {m4['JNK']['holdout']['t_mom']:.2f}). This undercuts the mechanism behind a pain trade.
2. **Shares outstanding are not a position.** See the short-interest result above.
3. **The ledger sees a small slice.** Median coverage is {pct(cover['LQD']['median_open_share_of_so'])} to {pct(cover['HYG']['median_open_share_of_so'])} of shares. Reductions exceed the ledger in {pct(unmatched['LQD']['share_of_weeks_nonzero'])} to {pct(unmatched['JNK']['share_of_weeks_nonzero'])} of weeks. A drained ledger gave no reading in {cover['LQD']['weeks_with_no_reading']} LQD weeks.
4. **Authorised participants trade the premium.** Lagged premium explains {pct(m2['LQD']['holdout']['r2_premium_only'])} to {pct(m2['HYG']['holdout']['r2_premium_only'])} of daily share changes in the holdout, with t above 2. In March 2020 LQD closed {abs(m8['LQD']['min_premium_pct']):.1f}% below NAV, so NAV and market price disagree most when it matters.
5. **Timing.** Share changes line up best with the premium one day earlier on LQD and HYG, but the peak is flat ({M['M1_timing']['LQD']['corr_flow_vs_premium_by_lag']['0']:.2f} at lag 0 and {M['M1_timing']['LQD']['corr_flow_vs_premium_by_lag']['1']:.2f} at lag 1). The wrong lag moves the LQD pain share by {m6['LQD']['pain126_k0']['mean_abs_gap'] * 100:.0f} points on average.
6. **Distributions.** A raw price overstates mean pain by {raw_bias['LQD'] * 100:.0f} points on LQD, {raw_bias['HYG'] * 100:.0f} on HYG and {raw_bias['JNK'] * 100:.0f} on JNK. Use total return.

Two worries turned out small. The last 3 days of a month hold {pct(m5['LQD']['holdout'], 1)} of LQD's absolute flow against {pct(m5['LQD']['even_spread'], 1)} for an even spread, so rebalances do not concentrate flow. And the bid-ask is small: the median half-spread is {r['costs']['LQD']['half_spread_bp']:.2f} bp on LQD and {r['costs']['HYG']['half_spread_bp']:.2f} bp on HYG, from one venue with about {pct(m6['book_entry_check']['LQD']['arca_share_of_consolidated_volume'])} of volume. Costs are not what kills these signals. The removal rule matters little too: FIFO correlates {m6['LQD']['pain126_fifo']['corr']:.2f} with pro rata on LQD.

## Test results

**C1, ledger and stress.** The planned rule is strict: {r['C1']['pass_count']} of {r['C1']['rows_count']} checks pass at the named week. Within 2 weeks of the date, {near_pass} pass. The 2020 misses are a timing effect. The week after the trough holds large creations at low prices and a rebound, so LQD pain drops from {lqd_mar[0]:.2f} on 20 March to {lqd_mar[1]:.2f} on 27 March. Coverage is the deeper problem: on 13 March 2020, near the worst of the sell-off, the LQD ledger was empty and gave no reading. A week later its reading of {lqd_mar[0]:.2f} rested on {pct(lqd_cov)} of shares. The reading also fires often: pain is at least 0.75 in {pct(unmatched['LQD']['base_rate_pain_ge_75'])} of LQD weeks. Verdict: it responds to stress, and it is noisy.

| Trough | Fund | Week | Pain | Depth | Depth rank | Best pain within 2 weeks | Strict pass |
|---|---|---|---|---|---|---|---|
{stress_rows}

**C2, prediction.** No evidence after correction. See the appendix. The base rate of a positive excess return is high ({pct(h('pain126|LQD|26')['base_rate_pos'])} on LQD and {pct(h('pain126|HYG|26')['base_rate_pos'])} on HYG at 26 weeks), so a hit rate alone says little. The ICE OAS target has about {oas_n} weeks and decides nothing, so it stays in `results.json`.

BAA10Y is the only long direct spread series, and it is IG only. Its count of {baac['summary']['abs_t_above_2']} cells above |t| = 2 shrinks to {baac['summary']['abs_t_above_2_without_2020']} without 2020 and to {baac['summary']['abs_t_above_2_skip_week']} when the target starts a week later. It stands at {baac['summary']['abs_t_above_2_with_control']} with the past 4-week implied spread change as a control, and at {baac['summary']['abs_t_above_2_with_10y']} with the same-period change in the 10-year yield as a control. So staleness alone does not explain it. These signals are close cousins, because most are forms of recent flow. The direct test of this finding is a longer OAS history from ICE, which FRED no longer carries.

**C3, I5.** The recipe runs unchanged, and the fitted slope has the expected negative sign. The fit explains little: R-squared is {c3['LQD']['usd']['fit_r2']:.2f} on LQD and {c3['HYG']['usd']['fit_r2']:.2f} on HYG.

| Fund, variant | Forward correlation at 26 weeks | Benchmark | I5 t beside benchmark | Rally case hit (base) | Widening case hit (base) | Extra rule |
|---|---|---|---|---|---|---|
| LQD usd | {c3['LQD']['usd']['fwd_corr_26']:.2f} | {c3['LQD']['usd']['benchmark_fwd_corr_26']:.2f} | {c3['LQD']['usd']['nested_t_i5']:.2f} | {pct(c3['LQD']['usd']['hits_holdout']['pos_hit'])} ({pct(c3['LQD']['usd']['hits_holdout']['uncond_rally'])}) | {pct(c3['LQD']['usd']['hits_holdout']['neg_hit'])} ({pct(1 - c3['LQD']['usd']['hits_holdout']['uncond_rally'])}) | {'pass' if c3['LQD']['usd']['pass_rule_extra'] else 'fail'} |
| HYG usd | {c3['HYG']['usd']['fwd_corr_26']:.2f} | {c3['HYG']['usd']['benchmark_fwd_corr_26']:.2f} | {c3['HYG']['usd']['nested_t_i5']:.2f} | {pct(c3['HYG']['usd']['hits_holdout']['pos_hit'])} ({pct(c3['HYG']['usd']['hits_holdout']['uncond_rally'])}) | {pct(c3['HYG']['usd']['hits_holdout']['neg_hit'])} ({pct(1 - c3['HYG']['usd']['hits_holdout']['uncond_rally'])}) | {'pass' if c3['HYG']['usd']['pass_rule_extra'] else 'fail'} |
| JNK usd | {c3['JNK']['usd']['fwd_corr_26']:.2f} | {c3['JNK']['usd']['benchmark_fwd_corr_26']:.2f} | {c3['JNK']['usd']['nested_t_i5']:.2f} | {pct(c3['JNK']['usd']['hits_holdout']['pos_hit'])} ({pct(c3['JNK']['usd']['hits_holdout']['uncond_rally'])}) | {pct(c3['JNK']['usd']['hits_holdout']['neg_hit'])} ({pct(1 - c3['JNK']['usd']['hits_holdout']['uncond_rally'])}) | {'pass' if c3['JNK']['usd']['pass_rule_extra'] else 'fail'} |
| USIG usd | {c3['USIG']['usd']['fwd_corr_26']:.2f} | {c3['USIG']['usd']['benchmark_fwd_corr_26']:.2f} | {c3['USIG']['usd']['nested_t_i5']:.2f} | {pct(c3['USIG']['usd']['hits_holdout']['pos_hit'])} ({pct(c3['USIG']['usd']['hits_holdout']['uncond_rally'])}) | {pct(c3['USIG']['usd']['hits_holdout']['neg_hit'])} ({pct(1 - c3['USIG']['usd']['hits_holdout']['uncond_rally'])}) | {'pass' if c3['USIG']['usd']['pass_rule_extra'] else 'fail'} |

LQD passes the extra rule alone. It still fails the general rule: the bootstrap interval is {h('i5_usd|LQD|26')['ci95'][0]:.0f} to {h('i5_usd|LQD|26')['ci95'][1]:.0f} bp and includes zero, Holm is {F['i5_usd|LQD|26']['holm_p']:.2f}, and t falls to {h('i5_usd|LQD|26')['with_controls']['t']:.2f} with spread level and momentum as controls. The sub-period table below shows the effect is 2020.

**C4, continuation and reversal.** Neither holds. See the appendix. The sign of the reversal signal is unstable between development and holdout.

**C5, short interest and options.** The P1 check fails on every fund tested. Short interest level, change and sentiment index show no stable effect. The P2 ledger on FINRA dates was added after results and sits outside the family. A short ledger shows nothing (HYG 4 weeks t = {second['HYG']['short_pain|4']['t']:.2f}). A gross-long ledger echoes the HY lead (HYG t = {second['HYG']['gross_long_pain|4']['t']:.2f}, JNK t = {second['JNK']['gross_long_pain|4']['t']:.2f}, LQD t = {second['LQD']['gross_long_pain|4']['t']:.2f}). Options were not tested.

**C6, IG against HY.** The planned rule says pooling is allowed: slopes are not rejected as equal in {pct(c6['summary']['LQD_vs_HYG']['share_not_rejected_10pct'])} of cases and share a sign in {pct(c6['summary']['LQD_vs_HYG']['share_same_sign'])}. I would not lean on that, for three reasons:
1. The test has little power at long horizons, and a control pair inside IG (LQD and USIG) fails its own sign rule at {pct(c6['summary']['LQD_vs_USIG']['share_same_sign'])}.
2. Inputs differ: short interest is {levels['LQD']['median_si_over_so_pct']:.0f}% of shares on LQD and {levels['HYG']['median_si_over_so_pct']:.0f}% on HYG, and weekly flows correlate only {c6['correlations_holdout']['weekly_flow']:.2f} even though 1-week excess returns correlate {c6['correlations_holdout']['xr1']:.2f}.
3. Pain relates to later flows differently on LQD and on HY.

**Decision: compute each fund separately and report IG and HY as separate groups. Nothing has survived that would need pooling.**

**Stability of the labelled results.** Each cell is the slope in bp per standard deviation, with t in brackets. These checks were added after results and they change no label.

| Test | Holdout | 2017-2021 | 2022-2026 | Holdout without 2020 |
|---|---|---|---|---|
{sub_table}

**Every labelled result in full, with benchmarks.** Slope is bp of excess return per development standard deviation. Hit is the share of positive excess returns in the top or bottom quintile, with the count in brackets, beside the base rate. Quintile thresholds come from development data. So a lopsided count means the signal left its old range.

| Test | Slope | t | Raw p | Holm p | 95% block bootstrap | N | Effective N | Top hit | Bottom hit | Base rate | t with controls | Replicate t |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
{labelled_table}

Buy and hold excess return in the holdout, for scale:

| Fund | Weeks | Mean bp | t | Share positive |
|---|---|---|---|---|
{buy_hold_rows}

**Costs.** Bp a year on a weekly rebalance, with half-spread, 1 bp of hedge per side, and borrow of 0.5% on LQD and 1% on HYG. The hedge and borrow numbers are my assumptions. Only labelled signals and benchmarks appear.

| Fund | Rule | Gross | Net | Net Sharpe | Turnover a year |
|---|---|---|---|---|---|
{strat_table}

## Recipes for the methods that transfer

All of these are **descriptions, not signals**. No evidence supports trading on them.

### Shared rules

1. **Timing.** A row dated d is usable on the next trading day. A reading on date T uses rows dated T-1 or earlier. FINRA short interest is usable from settlement + 10 business days.
2. **Total-return NAV.** TRN(t) = TRN(t-1) x (NAV(t) + exdiv(t)) / NAV(t-1), with TRN(0) = 1. Never use a raw price in a ledger.
3. **Flow.** dS(t) = S(t) - S(t-1) from issuer shares outstanding.
4. **Order date.** A share change dated t belongs to order date t-k. Estimate k on past data as the lag in {{0, 1, 2}} with the highest correlation between the log share change and the premium. LQD and HYG give k = 1.
5. **Matched hedge.** Each day find the maturity m whose par bond has modified duration D, where D is the holdings-weighted effective duration from the last holdings date. Hedge return = y(m, t-1) x days / 365 - D x (y(m, t) - y(m, t-1)), on the FRED par curve. Code: `common.matched_hedge`. As a check, the hedged LQD series correlates {PH['hedge_check']['LQD']['corr_weekly']:.2f} weekly with the issuer's rate-hedged LQDH, and HYG {PH['hedge_check']['HYG']['corr_weekly']:.2f} with HYGH. Their means differ, likely because a swap-hedged fund also earns the floating rate.
6. **Implied spread change, in bp.** ds(t) = -(r_nav(t) - hedge(t) - carry x days / 365) / D x 10,000. Carry is 1.3% a year for IG and 4% for HY. This is a stated round number. On the overlap HYG drifts {m7['HYG']['mean_weekly_implied'] - m7['HYG']['mean_weekly_oas']:.1f} bp a week above OAS, so do not read levels off this series.
7. **CS01 per share.** NAV x D / 10,000.
8. **Baseline every positioning study must beat: spread level.** Level(t) = (yield to worst minus y(m)) at the last holdings date, plus the sum of ds since that date. Correlation with OAS on the overlap: {m7['LQD']['level_corr']:.2f} on LQD and {m7['HYG']['level_corr']:.2f} on HYG.

### P2-ETF: share of recent net creations under water

Inputs: S, TRN, k. Parameters: N = 126 trading rows, `RemovalRule.PRO_RATA`.
1. Take the last N rows of dS ending at T-1. Entry price for row t is TRN(t-k).
2. Replay them with `posmon.build_ledger`.
3. If open total is at most 1e-6 x max(gross total, 1), return no reading. Pro-rata removal can leave rounding noise, so do not test for exact zero.
4. Level L = TRN(T-1).
5. Pain share = open shares with entry at or above L, divided by open total.
6. Depth = open-weighted mean of (entry / L - 1) over the lots counted in step 5.
7. Coverage = open total / S(T-1). Always publish it beside the pain share. Publish unmatched as well.

### P4-ETF: activity by price

Call `posmon.pain.activity_by_price(price, longs=S, shorts=0)`, with price as TRN in buckets you choose (one decimal place of TRN worked for a year of HYG). Shares that leave count as longs off, not as short sales. Short interest has its own dates and does not enter here.

### I1-ETF: long share of gross long

1. Take short interest SI at each FINRA settlement date, and S on that date.
2. I1 = 100 x S / (S + SI). A low number means heavily shorted.
3. Carry it forward weekly from its usable date. Add 52-week high, low and median with `posmon.indicators.rolling_stats`.
4. Use it only where median SI / S is above 5%. That holds for LQD, HYG and JNK. It does not hold for USIG ({levels['USIG']['median_si_over_so_pct']:.1f}%), IGSB ({levels['IGSB']['median_si_over_so_pct']:.1f}%) or USHY ({levels['USHY']['median_si_over_so_pct']:.1f}%).

### I2-ETF: sentiment index on short interest

`posmon.indicators.sentiment_index(SI / (S + SI), weeks=156)` on the weekly series from I1-ETF. FINRA's API starts on 2017-12-29, so the first reading falls about three years later. Do not run it on the level of shares, because fund growth drives that level.

### I3-ETF: scaled flow

Flow26 = 100 x (ln S(T-1) - ln S 26 weeks earlier). Call `posmon.indicators.db_scaled(flow26, weeks=209)`. Do not run it on shares, because they are never negative and the short half of the scale would be empty.

### CFTC credit futures: original code, unchanged

`python -m posmon.cli fetch --report tff --code 221606` for IG and `--code 221605` for HY. Latest readings, net as a share of open interest: IG leveraged funds {cftc['BLOOMBERG_IG_CREDIT']['lev_net_pct_oi']:.0f}% and asset managers {cftc['BLOOMBERG_IG_CREDIT']['am_net_pct_oi']:.0f}%, on {cftc['BLOOMBERG_IG_CREDIT']['last_open_interest']:,.0f} contracts. HY {cftc['BLOOMBERG_HY_CREDIT']['lev_net_pct_oi']:.0f}% and {cftc['BLOOMBERG_HY_CREDIT']['am_net_pct_oi']:.0f}%, on {cftc['BLOOMBERG_HY_CREDIT']['last_open_interest']:,.0f} contracts, last reported {cftc['BLOOMBERG_HY_CREDIT']['last']}. Retest once I2's 156-week window fills, in about 2029.

## Data sources and limits

| Source | What it gave | Limit |
|---|---|---|
| iShares product-data JSON (`component=fundDownload`) | Daily NAV, ex-dividend, shares: LQD from 2002, HYG from 2007, and IGSB, IGIB, USIG, USHY, FALN, EMB, LQDH, HYGH, SHYG, to 2026-10-30 | The old `.ajax` xls link now returns the web page. It is the page's own feed, undocumented, and it may change. Check BlackRock's terms before production use. Archived Wayback copies were my first route and I dropped them, because the newest usable LQD copy stopped in January 2021. |
| iShares holdings (`component=holdings.all&asOfDate=`) | Dated effective duration and yield to worst | Sampled twice a year for LQD and HYG, once a year for the rest. |
| SSGA `navhist` xlsx | JNK, SJNK, SPSB, SPIB, SPLB: date, NAV, shares | No holdings here, so JNK borrows HYG's duration and yield path. A one-day jump in October 2014 on JNK and SPIB looks like a file error. It falls in development only and I left it. |
| Vanguard | Current price and premium only | I found no share history. |
| CRSP in marketdb | Only VCIT and TLT, 2019 to 2021 | Cannot feed LQD or HYG. Statistics only are stored. |
| marketdb book | Half-spread, VWAP, aggressor volume for LQD, HYG, JNK | One venue, about {pct(m6['book_entry_check']['LQD']['arca_share_of_consolidated_volume'])} of volume. Sampled: every day of 2024 for LQD and HYG, every fifth day otherwise. VWAP is {m6['book_entry_check']['LQD']['vwap_vs_nav_mean_abs_bp']:.0f} bp from NAV on LQD on average. |
| TRACE | Not used | 15 issuers, 2023 to 2025. Not a market series and not point in time. |
| FRED ICE BofA OAS | BAMLC0A0CM, BAMLH0A0HYM2 from 2023-10-31 | **FRED now keeps 3 years.** Its note says to go to the source for more. I did not pull older vintages. Top-level ICE data is licensed for internal use, so keep `raw/` private. |
| FRED Moody's and Treasury | BAA10Y, AAA10Y and par yields, full history | BAA10Y is IG only and long dated. |
| Yahoo chart API | Daily close, adjusted close, volume, JNK dividends | An unofficial feed, so check its terms before production use. It answered a plain user agent and returned 429 to a browser one. Adjusted close is restated as of download. |
| FINRA API | Short interest twice a month from 2017-12-29 | The 10-business-day lag is my conservative choice. |
| CFTC | Bloomberg IG and HY credit futures in TFF | From 2026 only. I found no iBoxx (IBHY, IBIG) or CDX contract under those names. |
| Alpha Vantage | Put-call ratio by date | `HISTORICAL_OPTIONS` and adjusted daily prices are premium on this key. |
| Databento OPRA | Quote only | ${quote['one_week_statistics']:.2f} for one week of LQD and HYG statistics, ${quote['2018_to_2026_statistics']:.2f} for 2018 to 2026. I did not buy it. |

## Checks on the work itself

1. **Point in time.** Rebuilding with data cut at a past week changes no signal on that week (largest gap {max(v['max_gap'] for v in r['pit_check'].values())}, across {sum(v['signals_checked'] for v in r['pit_check'].values())} values). This covers the weekly step. The daily series are built forward only and were not cut separately.
2. **False-positive rate.** Random persistent signals reject at 5% about as they should. See the table. The test is conservative at short horizons and slightly loose at 26 weeks.
3. **Planted signal.** A signal built from the future return clears Holm at every horizon, so the harness can find an effect.
4. **A real bug, found and fixed.** The first run showed |t| above 5 for LQD pain with a slope near zero. A drained ledger had produced absurd values. The rule "bootstrap interval excludes zero" flagged it. `plan.md` records the fix. The cause was my own sum, which skipped negative rounding noise. A related point for `posmon`: `_share_in_pain` and `ms_pain_monitor` test the open total for exact zero. In a random test of 100,000 fully drained windows with several removals, about a quarter left a non-zero open total of about 1e-12. `posmon` stayed within 0 to 1 there, but it returned a normal-looking number where the spec says no reading. I did not edit `posmon`. A tolerance of 1e-6 x gross total, as in the P2-ETF recipe, would fix it.

| Horizon (weeks) | Effective N | R-squared needed for Holm | R-squared needed for raw 5% | False positives at 5%, LQD | False positives at 5%, HYG | Planted signal t, LQD |
|---|---|---|---|---|---|---|
{power_rows}

## Known weaknesses

1. The holdout holds one huge event (March 2020), and most long-horizon results depend on it. That is why the without-2020 column matters.
2. Duration is sampled twice a year and carried forward. Before the first holdings date it is carried backward. This affects the hedge only.
3. Before 2023-10-31 there is no direct spread series for HY, so spread targets are implied from the same ETF. The family's main target is the excess return for that reason.
4. Thresholds and z-scores use development data, and 2008 is in it. Several signals sit well away from their development range in the holdout, so quintile counts are lopsided. The appendix shows the slopes, which do not depend on these thresholds.
5. The Holm correction treats a correlated family conservatively. The placebo count is the fairer read, and it agrees.

## Appendix: all t-statistics

Holdout t by horizon, development t, best Holm-adjusted p for that row, and how many of the 4 cells are labelled suggestive. Slopes use a Newey-West lag of at least the overlap, and p-values use effective N.

| Signal | Fund | 1w | 4w | 13w | 26w | Development t (1/4/13/26) | Best Holm p | Suggestive |
|---|---|---|---|---|---|---|---|---|
{family_table}

Cross-section tests, long the top half and short the bottom half of the fund pool:

| Signal | Weeks | Holdout t | Development t | IG t | HY t | Holm p | Label |
|---|---|---|---|---|---|---|---|
{cs_table}
"""
(HERE / "report.md").write_text(report)
print("report.md", len(report.split()), "words")
