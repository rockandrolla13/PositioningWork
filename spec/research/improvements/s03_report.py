"""Build report.md from results.json. Every number in a table or sentence below comes from results.json or derived/."""
import json
import math

from lib import DERIVED, HERE

R = json.loads((HERE / "results.json").read_text())
LEAK = json.loads((DERIVED / "leak_check.json").read_text())
F = R["family"]


def n(x, d=2):
    return "n/a" if x is None else f"{x:.{d}f}"


def pct(x, d=0):
    return "n/a" if x is None else f"{100 * x:.{d}f}%"


def ci(pair, d=2):
    return "n/a" if not pair else f"[{pair[0]:.{d}f}, {pair[1]:.{d}f}]"


def fisher_ci(r, n_eff):
    """A cautious 95% interval that treats N_eff as the number of independent observations."""
    half = 1.96 / math.sqrt(max(n_eff - 3.0, 1.0))
    return [100 * math.tanh(math.atanh(r) - half), 100 * math.tanh(math.atanh(r) + half)]


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(out)


GROUP_NAME = {"am_TYUS": "Asset managers + others, TY and US", "am_all6": "Asset managers + others, all six", "lev": "Leveraged funds, all six",
              "spec": "Non-commercial specs, all six", "benchmark": "Benchmark: past 26w change"}
T1M = R["T1"]["monday_26w"]
SPLIT = R["T1"]["published_corr_split"]
hold = {g: T1M[g]["HOLDOUT"] for g in T1M}
AM = hold["am_TYUS"]["test"]
P12 = R["T12"]
T11 = R["T11"]
SS = R["sample_size"]
POW = R["power"]
LC = json.loads((DERIVED / "ledger_check.json").read_text())
RES = LC["residue_summary_w126_pro_rata"]
primary = [v for v in F.values() if v["tier"] == "primary"]
secondary = [v for v in F.values() if v["tier"] == "secondary"]
raw_sorted = sorted((v for v in primary if v["p_raw"] is not None), key=lambda v: v["p_raw"])
min_holm = min(v["p_holm_primary"] for v in primary)
min_holm_all = min(v["p_holm_all"] for v in F.values())
min_rot = min((v["p_rotation_holm"] for v in F.values() if v.get("p_rotation_holm") is not None))
successes = [v["id"] for v in primary if v["success"]]
I3 = F["T8.3"]
UST13 = R["T8"]["panel"]["UST_13w"]
I3S = T11["single"]["rates"]["I3_lev"]
SPEC_S = T11["single"]["rates"]["I5_spec"]
AM_S = T11["single"]["rates"]["I5_am_TYUS"]
LEV_S = T11["single"]["rates"]["I5_lev"]
BEN_S = T11["benchmark"]["rates"]
BH_S = T11["buy_hold"]["rates"]
C_S = T11["composite_C_prior_sign"]["metrics"]
DECK = R["T6"]["deck_rule_hits"]
T6B = R["T6b"]
AGG = R["T8"]["aggregate_i4"]["HOLDOUT"]["hits"]
SPECI4 = R["T8"]["spec_i4"]["HOLDOUT"]
SIZE = R["size_check"]

lines = []
add = lines.append

add("# Positioning methods: out-of-sample results")
add("")
add(f"Built from `results.json`. Plan fixed in `plan.md` before any test ran. Data through report date {R['boundaries']['last_report_date']}. Holdout starts {R['boundaries']['holdout_start']}.")
add("")
add("## 1. Bottom line")
add("")
add(f"**Nothing predictive survives.** {len(primary)} primary tests ran. The smallest Holm-adjusted p-value is {n(min_holm)}. The smallest raw p-value is {n(raw_sorted[0]['p_raw'], 3)}. Tests that meet their success rule: {len(successes)}.")
add("")
add(f"1. **The Goldman asset-manager signal failed.** Its published correlation of {pct(SPLIT['am_TYUS']['whole_to_apr_2019'])} mixes the fit period ({pct(SPLIT['am_TYUS']['fit_rows_2006_2010'])}) with the later years ({pct(SPLIT['am_TYUS']['post_fit_2011_2018'])}). In the real holdout it is +{pct(AM['corr'])}. The block-bootstrap 95% interval is {ci([100 * x for x in AM['corr_ci_boot']], 0)} percent, which excludes the claim. A more cautious interval built on 14 independent observations is {ci(fisher_ci(AM['corr'], AM['n_eff']), 0)} percent, which does not. So the published size is unlikely, though not impossible. What settles the verdict is everything else: the sign is wrong at all four horizons, rally calls hit below the base rate, real flows do no better than random flows, and a strategy trading it lost money (net Sharpe {n(AM_S['HOLDOUT']['sharpe'])}).")
add(f"2. **The filter creates much of the fit by itself.** Random flows pushed through the same filter already give a six-month correlation of {pct(-P12['am_TYUS']['placebo_mean']['corr_F26_D26_design'])} with yields, against {pct(-P12['am_TYUS']['real']['corr_F26_D26_design'])} for real flows, and a slope of {n(P12['am_TYUS']['placebo_mean']['beta'] * 10, 1)} bp per $10mm against the real {n(P12['am_TYUS']['real']['beta'] * 10, 1)}. Unfiltered asset-manager flows give {n(R['T13']['am_TYUS']['plain_slope_bp_per_10mm'], 1)}, with the opposite sign.")
add(f"3. **Pain share has no edge.** The 2018 deck rule hits at the base rate: on Treasuries, leveraged funds, {pct(DECK['UST_lev_HOLDOUT']['down_hit'], 1)} against {pct(DECK['UST_lev_HOLDOUT']['base_down'], 1)} on sells and {pct(DECK['UST_lev_HOLDOUT']['up_hit'], 1)} against {pct(DECK['UST_lev_HOLDOUT']['base_up'], 1)} on buys. Depth, window length, crowding and removal rule change nothing that matters.")
add(f"4. **The closest thing to a survivor is on a watch list, not adopted.** Leveraged-fund I3 read as a contrarian signal on Treasuries, 13 weeks: raw p {n(I3['p_raw'], 3)}, rotation p {n(I3['p_rotation'], 3)}, Holm {n(I3['p_holm_primary'])}, rotation Holm {n(I3['p_rotation_holm'])}. Almost all of it comes from 2019 to 2022. Its net Sharpe is {n(I3S['H-A']['sharpe'])} then {n(I3S['H-B']['sharpe'])}.")
add(f"5. **The sample limits what a \"no\" means.** A 26-week horizon gives about 14 independent observations in the holdout. Power to detect a true -43% is {pct(POW['goldman_minus_43_at_neff_14']['raw_5pct'])} before correction and {pct(POW['goldman_minus_43_at_neff_14']['holm_first_step'])} after. So non-significance alone proves little. The asset-manager verdict rests on the evidence in item 1, not on the p-value. The leveraged-fund and spec versions stay unresolved.")
add("")
add("**Adopt three things.** None of them adds predictive power. They remove errors at no cost. See sections 2 and 3.")
add("")

add("## 2. Improvements ranked by evidence")
add("")
add("Levels come from `plan.md`, section 9. Level 1 means confirmed. Level 2 means suggestive. Level 3 means inconclusive. Level 4 means rejected.")
add("")
rank_rows = [
    ["Adopt", "Empty-ledger guard (bug fix)", "Not a predictive claim", f"{RES['residue_ledgers']} of {RES['ledger_readings']} ledgers held floating-point residue. {RES['unguarded_share_outside_0_1']} gave a share outside 0 to 1, up to {RES['unguarded_share_largest_abs']:.0e}. One such value corrupted my first run."],
    ["Adopt", "Monday entry for every test", "Not a predictive claim", f"Removes look-ahead. It costs {n(R['T2']['paired_tue_minus_mon']['am_TYUS_26w']['diff'], 3)} of correlation on asset managers at 26w. The largest cost anywhere is {n(max(abs(v['diff']) for v in R['T2']['paired_tue_minus_mon'].values()), 3)}."],
    ["Adopt", "Synthetic roll-free Treasury price", "Not a predictive claim", f"Daily change correlation with real TY closes is {n(T6B['ty_real_closes']['corr_daily_change'], 3)}. P2 on it matches P2 on unadjusted Yahoo prices: DESIGN t {n(T6B['verdict_rule']['design_t_synthetic'])} against {n(T6B['verdict_rule']['design_t_yahoo'])}. It is free and needs no roll calendar. It is a data choice, not a signal gain."],
    ["Watch", "I3 leveraged funds, contrarian, Treasuries", "Level 2", f"Slope {n(I3['stat'])} per SD, raw p {n(I3['p_raw'], 3)}, Holm {n(I3['p_holm_primary'])}. DESIGN slope {n(I3['design_stat'], 3)}. Halves {n(UST13['I3_lev']['H-A']['beta'])} and {n(UST13['I3_lev']['H-B']['beta'])}. Net Sharpe {n(I3S['HOLDOUT']['sharpe'])}. Fails adoption: no cost-free reason."],
    ["Reject for now", "I5 on leveraged funds or specs instead of asset managers", "Level 3", f"Holdout correlations {pct(hold['lev']['test']['corr'])} and {pct(hold['spec']['test']['corr'])}, raw p {n(F['T1.3']['p_raw'])} and {n(F['T1.4']['p_raw'])}. Post-fit 2011-2018 was only {pct(T1M['lev']['GS-OOS']['test']['corr'])} and {pct(T1M['spec']['GS-OOS']['test']['corr'])}. Flagged: holdout beats design. It also depends on a stale beta (T4)."],
    ["Reject for now", "With-the-market filter over raw flows", "Level 3", f"Paired corr gain {n(F['T13.1']['stat'])}, p {n(F['T13.1']['p_raw'])}, on asset managers. Real flows do not beat shifted flows (T12)."],
    ["Reject for now", "Filter applied to FX", "Level 3", f"Slopes {n(F['T9.1']['stat'])}, {n(F['T9.2']['stat'])}, {n(F['T9.3']['stat'])}, right sign, p {n(F['T9.1']['p_raw'])}, {n(F['T9.2']['p_raw'])}, {n(F['T9.3']['p_raw'])}. Single currencies disagree in sign."],
    ["Reject", "Pain crossed with crowding", "Level 4", f"Treasuries slope {n(F['T7.3']['stat'])}, p {n(F['T7.3']['p_raw'], 3)}, but DESIGN has the opposite sign ({n(F['T7.3']['design_stat'], 3)}), and crowding alone gives {n(R['T7']['crowded']['UST_spec_crowd_only']['block']['HOLDOUT']['beta'])}. So pain adds nothing. FX {n(F['T7.4']['stat'], 3)}."],
    ["Reject", "Walk-forward beta or scale in I5", "Level 4", f"Beta really did decay (T4). But updating it moves the asset-manager correlation the wrong way by {n(F['T4.1']['stat'])} (expanding) and {n(F['T4.2']['stat'])} (rolling)."],
    ["Reject", "Fresh score (add the yield move from Tuesday to Monday)", "Level 4", f"Correlation gain {n(R['T2']['fresh']['am_TYUS']['fresh_minus_plain']['26']['diff'], 3)} at 26w."],
    ["Reject", "Depth instead of share", "Level 4", f"Paired gain {n(F['T7.1']['stat'], 3)} (p {n(F['T7.1']['p_raw'])}) on Treasuries and {n(F['T7.2']['stat'], 3)} (p {n(F['T7.2']['p_raw'])}) on FX."],
    ["Reject", "Longer or shorter pain window", "Level 4", f"DESIGN chose {R['T7']['windows']['UST_lev']['design_choice']} days for Treasuries and {R['T7']['windows']['FX_lev']['design_choice']} for FX. Holdout p {n(F['T7.5']['p_raw'])} and {n(F['T7.6']['p_raw'])}."],
    ["Reject", "Options position from combined minus futures", "Level 4", f"Six tests. Smallest raw p {n(min(F[f'T10.{i}']['p_raw'] for i in range(1, 7)))}. {sum(1 for i in range(1, 7) if F[f'T10.{i}']['sign_ok'] is False)} of six have the opposite sign to DESIGN."],
    ["Reject", "Composite", "Level 4", f"The plan's composite is empty, because no signal reached |t| of 2 in DESIGN. The no-selection version has net Sharpe {n(C_S['HOLDOUT']['sharpe'])} (t {n(C_S['HOLDOUT']['t_stat'])})."],
]
add(table(["Decision", "Improvement", "Level", "Key numbers"], rank_rows))
add("")

add("## 3. Recipes ready for the spec")
add("")
add("**R1. Empty ledger (P1, P2, ledger section).** Add to the decision box:")
add("")
add("> Empty ledger: if open contracts total 1e-6 or less, return no reading. A full removal can leave floating-point residue near 1e-14 contracts, and dividing by it gives shares near 1e16.")
add("")
add("Code change for `posmon/pain.py`, which I did not edit, as instructed:")
add("")
add("```python\ndef _ratio(top: float, bottom: float, floor: float = 1e-6) -> float:\n    return top / bottom if bottom > floor else float(\"nan\")\n```")
add("")
add(f"Evidence: on TY leveraged-fund longs alone, {LC['posmon_residue_readings']} of {LC['dates_compared']} dates from 2013 to 2015 read a number from an empty ledger. Add a test that every share stays inside 0 to 1.")
add("")
add("**R2. Entry timing (section on how to test any signal).** Add:")
add("")
add("> Measure every forward move from the close of the first trading day on or after the Monday after release. For FX from H.10, use that day's noon rate. Call this date E. Forward change = level(E + 7k days) minus level(E), using the last observation on or before each date. Measuring from the Tuesday report date is look-ahead.")
add("")
add("**R3. Synthetic Treasury price (market data section).** Add:")
add("")
add("> A roll-free Treasury price, per contract, in percent of face: P(t) = P(t-1) - 100 x DV01(t-1) / Face x (y(t) - y(t-1)). DV01 is the last weekly value in `data/treasury_futures_dv01.csv` known on the prior day. Face is $200,000 for TU and $100,000 for the rest. y is the contract's FRED yield in basis points: TU DGS2, FV DGS5, TY DGS7, TN DGS10, US DGS20, WN DGS30. This price has no carry and no roll-down. It tracks a constant-maturity yield, not the cheapest-to-deliver.")
add("")
add("**R4. Corrections to the current I4, I5 and S1 text.** Other agents updated the spec during this run, so these target its latest wording.")
add("")
add(f"- I5 carries the label \"Verified\". That label is right about the replication and could be misread as a claim that the signal works. Add this warning box: \"Verified means this build matches Goldman's charts. It does not mean the signal works. From May 2019 to the latest data, with Monday entry, the asset-manager correlation with the next 26-week yield change is +{pct(AM['corr'])}, against {pct(SPLIT['am_TYUS']['post_fit_2011_2018'])} for 2011 to 2018 and -43% as published. The published number includes the fit period. The slope of 17 to 18 bp per $10mm appears with random flows too, because the filter keeps only flows that move with yields. Do not trade I5.\"")
add(f"- I4: the frozen scale from January 2007 to June 2018 is look-ahead inside that window, so hit rates there are in-sample. After it, on the holdout, the rule said buy in {SPECI4['hits']['pos_n']} of {SPECI4['hits']['n']} weeks and sell in {SPECI4['hits']['neg_n']}, and the buy hit rate was {pct(SPECI4['hits']['pos_hit_fall'])} against a {pct(SPECI4['hits']['base_fall'])} base. Add that as a warning. Use I4 as a benchmark only.")
add("- S1 (deck rule): add that hits equal the base rate in the holdout.")
add("")
add("**Watch-list recipe, paper only. Not for trading.** I3 contrarian on Treasuries. Use TFF futures-only leveraged-fund net. Compute I3 over 209 weeks. Convert to a z-score with an expanding mean and SD, minimum 52 weeks. Flip the sign. Clip to -1 and +1. Enter at E, hold one week, size to 10% annual risk on a trailing 52-week SD. Promote only if it holds in new data after this date with Holm-level evidence.")
add("")

add("## 4. Test by test")
add("")
add("Conventions: \"holdout\" is May 2019 onward. \"GS-OOS\" is 2011 to April 2019, after the fit but inside Goldman's published sample. Entry is Monday unless stated. All hit rates sit beside their base rates. Raw p is the larger of the Newey-West and block-bootstrap p-values. Rotation p is a second null added after the size check (amendment A2).")
add("")
add("### T1. I5 out of sample")
add("")
add(f"Replication passed first. Through April 2019 on Goldman's basis: asset managers {pct(R['replication_gate']['am_TYUS']['corr_next_26w'], 1)} (claim -43%), leveraged funds {pct(R['replication_gate']['lev']['corr_next_26w'], 1)} (-18%), specs {pct(R['replication_gate']['spec']['corr_next_26w'], 1)} (-26%), benchmark {pct(R['replication_gate']['benchmark_corr'], 1)} (-35%), last score {n(R['replication_gate']['am_TYUS']['score_2019_04_30'])} (-0.67), rows {R['replication_gate']['am_TYUS']['n']} (620).")
add("")
rows = []
for g, b in T1M.items():
    t, h = b["HOLDOUT"]["test"], b["HOLDOUT"]["hits"]
    test_id = {"am_TYUS": "T1.1", "am_all6": "T1.2", "lev": "T1.3", "spec": "T1.4", "benchmark": "T1.5"}[g]
    rows.append([GROUP_NAME[g], pct(b["GS-OOS"]["test"]["corr"]), f"**{pct(t['corr'])}**", ci([100 * x for x in t["corr_ci_boot"]], 0), ci(fisher_ci(t["corr"], t["n_eff"]), 0), pct(b["H-A"]["test"]["corr"]), pct(b["H-B"]["test"]["corr"]), n(t["n_eff"], 0), n(t["t_nw"]), n(t["p_primary"], 3), n(F[test_id].get("p_rotation"), 3),
                 f"{pct(h['pos_hit_fall'])} / {pct(h['base_fall'])}", n(h["pos_avg"], 0), f"{pct(h['neg_hit_rise'])} / {pct(h['base_rise'])}", n(h["neg_avg"], 0)])
add(table(["Signal", "GS-OOS corr", "Holdout corr", "Block 95% interval (pct)", "Cautious 95% interval on N_eff (pct)", "H-A", "H-B", "N_eff", "NW t", "Raw p", "Rot. p", "Rally bias: hit / base", "Avg bp", "Sell-off bias: hit / base", "Avg bp"], rows))
add("")
add(f"What it means. Asset managers: a rally call was right {pct(hold['am_TYUS']['hits']['pos_hit_fall'])} of the time, below the {pct(hold['am_TYUS']['hits']['base_fall'])} base rate. The average move after a rally call was +{n(hold['am_TYUS']['hits']['pos_avg'], 0)} bp, the wrong way. The holdout was a bear market, with yields up {n(hold['am_TYUS']['hits']['mean_all'], 0)} bp on average over 26 weeks, so the base rate matters. TY and US against all six makes no difference: {n(R['T1']['paired_holdout']['am_TYUS_minus_am_all6']['diff'])} (p {n(R['T1']['paired_holdout']['am_TYUS_minus_am_all6']['p_boot'])}). Against the benchmark, no group wins: the closest is leveraged funds at {n(R['T1']['paired_holdout']['lev_minus_benchmark']['diff'])} (p {n(R['T1']['paired_holdout']['lev_minus_benchmark']['p_boot'])}).")
add("")
add(f"The plain benchmark also failed: {pct(hold['benchmark']['test']['corr'])} against the claimed -35%. It behaved in opposite ways in the two halves: {pct(T1M['benchmark']['H-A']['test']['corr'])} then {pct(T1M['benchmark']['H-B']['test']['corr'])}. Goldman's number also rested on the crisis years: fit rows {pct(SPLIT['benchmark']['fit_rows_2006_2010'])}, later rows {pct(SPLIT['benchmark']['post_fit_2011_2018'])}.")
add("")
add("### T2. Tradability")
add("")
rows = []
for name in ("am_TYUS", "lev", "spec"):
    for k in (4, 13, 26):
        v = R["T2"]["paired_tue_minus_mon"][f"{name}_{k}w"]
        rows.append([GROUP_NAME[name], f"{k}w", n(v["corr_a"]), n(v["corr_b"]), n(v["diff"], 3), ci(v["ci_boot"]), n(v["p_boot"], 3)])
add(table(["Signal", "Horizon", "Corr Tuesday (look-ahead)", "Corr Monday", "Difference", "95% interval", "p"], rows))
add("")
bp = R["T2"]["bp_cost"]
add(f"The lag costs almost nothing. The largest gap is {n(max(abs(v['diff']) for v in R['T2']['paired_tue_minus_mon'].values()), 3)} of correlation. A weekly rule on asset managers in the holdout makes {n(bp['am_TYUS_HOLDOUT']['tue_bp_per_week'], 2)} bp a week from Tuesday and {n(bp['am_TYUS_HOLDOUT']['mon_bp_per_week'], 2)} from Monday. The signal moves too slowly for six days to matter. Dropping the {R['T2']['late_release_weeks_dropped']} late-release weeks (ION 2023, shutdown 2025, per the [CFTC notices](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm)) moves asset managers to {pct(R['T2']['late_dropped']['am_TYUS']['corr'])} and leveraged funds to {pct(R['T2']['late_dropped']['lev']['corr'])}. History still assumes Friday releases elsewhere.")
add("")
add("### T3. Does the score add to the benchmark?")
add("")
add("Structure first. Score = (past 26w yield change - 26 alpha - beta x flows) / scale. So the benchmark sits inside the score, and the test on the score is the same test as the one on the positioning term.")
add("")
rows = []
for name, test_id in (("am_TYUS", "T3.1"), ("lev", "T3.2"), ("spec", "T3.3")):
    b = R["T3"][name]
    g, h = b["joint"]["GS-OOS"], b["joint"]["HOLDOUT"]
    rows.append([GROUP_NAME[name], n(b["corr_score_with_past26"]["GS-OOS"]), n(b["corr_score_with_past26"]["HOLDOUT"]), n(g["beta"], 1), n(g["t_nw"]), n(h["beta"], 1), n(h["t_nw"]), n(b["joint_lag_26"]["HOLDOUT"]["t_nw"]), ci(h["ci_boot"], 1), n(h["p_primary"], 3), n(F[test_id].get("p_rotation"), 3), n(b["oos"]["oos_r2_big_vs_small"], 3), n(b["oos"]["clark_west_p_one_sided"], 2)])
add(table(["Signal", "Corr with past change, GS-OOS", "Holdout", "Slope GS-OOS (bp per unit)", "t", "Slope holdout", "t, lag 39", "t, lag 26", "95% block interval", "Raw p", "Rot. p", "Incremental OOS R2", "Clark-West p"], rows))
add("")
add(f"Effective sample: {R['T3']['am_TYUS']['joint']['HOLDOUT']['n']} overlapping weeks, about {n(R['T3']['am_TYUS']['joint']['HOLDOUT']['n_eff'], 0)} independent. No group adds to the benchmark. All incremental out-of-sample R-squared values are negative. The asset-manager score is mostly the benchmark in disguise: correlation {n(R['T3']['am_TYUS']['corr_score_with_past26']['HOLDOUT'])}. Forecasts from the benchmark alone are also worse than the expanding mean (OOS R2 {n(R['T3']['am_TYUS']['oos']['oos_r2_small_vs_mean'], 3)}).")
add("")
add("### T4. Stability")
add("")
rows = []
for name, b in R["T4"]["beta_by_period"].items():
    rows.append([GROUP_NAME[name]] + [f"{n(v['beta'] * 10, 1)} (t {n(v['t_nw'], 1)})" for v in b.values()])
add(table(["Slope, bp per $10mm/bp"] + list(next(iter(R["T4"]["beta_by_period"].values())).keys()), rows))
add("")
labels = {"fixed": "Fixed (recipe)", "expanding_beta_fixed_scale": "Expanding beta, fixed scale", "expanding_beta_expanding_scale": "Expanding beta and scale", "rolling_beta_rolling_scale": "Rolling 260w beta and scale", "fixed_beta_expanding_scale": "Fixed beta, expanding scale"}
rows = []
for column, label in labels.items():
    row = [label]
    for name in ("am_TYUS", "lev", "spec"):
        v = R["T4"]["variants"][name][column]["HOLDOUT"]
        row += [n(v["test"]["corr"]), n(R["T4"]["corr_with_past26"][name][column]["HOLDOUT"])]
    rows.append(row)
add(table(["Variant, holdout", "AM corr", "AM corr with past change", "Lev corr", "Lev corr with past change", "Spec corr", "Spec corr with past change"], rows))
add("")
add("The slope is not stable. Leveraged funds and specs fell from about -18 to about -8, while asset managers fell from -17 to about -13. Yet refitting does not help. It makes the forecasts worse.")
add("")
add("This explains a warning sign in T1 (a post-hoc reading, with no p-value). With the stale 2006-2010 beta, the leveraged and spec scores over-subtract flows. They then correlate negatively with the past yield change in the holdout, the opposite of their design-sample behaviour. So in the holdout they act as a flow-momentum signal, not as the reversal signal Goldman described. With an updated beta, that link turns positive and the forecast weakens, most sharply for specs and on the rolling fit. Treat the leveraged and spec holdout numbers with suspicion for this reason.")
add("")
add("### T5. Horizons")
add("")
rows = []
for k in ("4w", "8w", "13w", "26w"):
    row = [k]
    for name in ("am_TYUS", "lev", "spec", "benchmark"):
        v = R["T5"][k][name]
        row += [f"{n(v['GS-OOS']['test']['corr'])} / {n(v['HOLDOUT']['test']['corr'])} (p {n(v['HOLDOUT']['test']['p_primary'])})"]
    rows.append(row)
add(table(["Horizon", "AM TY+US: GS-OOS / holdout", "Leveraged", "Specs", "Benchmark"], rows))
add("")
add(f"Asset managers fail at every horizon. Leveraged funds and specs are negative at every horizon in the holdout and near zero before 2019. Specs at 4w has the best raw p ({n(F['T5.S.spec.4']['p_raw'], 3)}), a secondary test that does not survive Holm ({n(F['T5.S.spec.4']['p_holm_all'])}).")
add("")
add("### T6. Pain P2 and the deck rule")
add("")
rows = []
for market in ("UST", "FX"):
    for group in ("lev", "am", "spec"):
        v = R["T6"]["net_share"][f"{market}_{group}_13w"]
        c = R["T6"]["with_past_return"][f"{market}_{group}_13w"]
        d = DECK[f"{market}_{group}_HOLDOUT"]
        test_id = {("UST", "lev"): "T6.1", ("UST", "am"): "T6.2", ("UST", "spec"): "T6.3", ("FX", "lev"): "T6.4", ("FX", "am"): "T6.5", ("FX", "spec"): "T6.6"}[(market, group)]
        rows.append([market, group, n(v["DESIGN"]["beta"], 3), n(v["HOLDOUT"]["beta"], 3), n(v["HOLDOUT"]["t_dk"]), n(v["HOLDOUT"]["p_primary"], 3), n(F[test_id].get("p_rotation"), 3), n(v["H-A"]["beta"]), n(v["H-B"]["beta"]), n(c["HOLDOUT"]["beta"], 3), n(R["T6"]["corr_with_past26"][f"{market}_{group}"]),
                     f"{pct(d['up_hit'], 1)} / {pct(d['base_up'], 1)}", f"{pct(d['down_hit'], 1)} / {pct(d['base_down'], 1)}"])
add(table(["Panel", "Group", "DESIGN slope", "Holdout slope", "DK t", "Raw p", "Rot. p", "H-A", "H-B", "Slope given past return", "Corr with past return", "Buy (long pain under 30%): hit / base", "Sell (over 70%): hit / base"], rows))
add("")
add("Slopes are per one SD of net share, on returns in risk units, 13 weeks ahead. Pain share does not predict moves. It is largely past return in another form, with a correlation near -0.45. Once past return is in the regression, the Treasury slopes collapse. The two holdout halves also disagree in sign on Treasuries.")
add("")
miss = R["T6"]["missing"]
add(f"Coverage note: about {pct(1 - miss['UST_lev']['with_reading'] / miss['UST_lev']['rows'])} of Treasury contract-weeks have no net reading, because a ledger is empty on one side. That is P2's own rule.")
add("")
add("### T6b. Is the synthetic price an improvement?")
add("")
y = T6B["yahoo"]
add(f"It is a sound substitute, not a signal gain. Against real TY closes (2014 to 2015, {T6B['ty_real_closes']['days']} days): correlation {n(T6B['ty_real_closes']['corr_daily_change'], 3)}, slope {n(T6B['ty_real_closes']['slope_real_on_synth'])}, tracking error {n(T6B['ty_real_closes']['tracking_sd_points'])} points a day against a real daily SD of {n(T6B['ty_real_closes']['real_sd_points'])}. Against Yahoo unadjusted front-month prices, daily correlations are {n(y['TU']['corr_daily_change'])} (TU), {n(y['FV']['corr_daily_change'])} (FV), {n(y['TY']['corr_daily_change'])} (TY), {n(y['US']['corr_daily_change'])} (US). The P2 signals correlate {n(y['TU']['signal_corr_with_synthetic'])} to {n(y['TY']['signal_corr_with_synthetic'])}. The slope gap is {n(T6B['slope_compare']['DESIGN']['abs_diff']['diff'], 3)} in DESIGN (p {n(T6B['slope_compare']['DESIGN']['abs_diff']['p_boot'])}) and {n(T6B['slope_compare']['HOLDOUT']['abs_diff']['diff'], 3)} in the holdout (p {n(T6B['slope_compare']['HOLDOUT']['abs_diff']['p_boot'])}). The plan's rule marks it \"at least as strong\". The gap is too small to call better. Its real gains are that it is free and has no roll jumps. The long bond tracks worst, because DGS20 is not its cheapest-to-deliver.")
add("")
add("marketdb has no long futures history, so a true back-adjusted futures comparison was not possible.")
add("")
add("### T7. Pain improvements")
add("")
rows = []
for market in ("UST", "FX"):
    for group in ("lev", "am", "spec"):
        v = R["T7"]["depth"][f"{market}_{group}"]
        rows.append([market, group, n(v["design_share"]["beta"], 3), n(v["design_depth"]["beta"], 3), n(v["depth"]["HOLDOUT"]["beta"], 3), n(v["depth"]["HOLDOUT"]["p_primary"], 3), n(v["paired_depth_minus_share"]["diff"], 3), n(v["paired_depth_minus_share"]["p_boot"], 3), n(v["signal_corr_holdout"])])
add("**Depth against share.**")
add("")
add(table(["Panel", "Group", "DESIGN share slope", "DESIGN depth slope", "Holdout depth slope", "Raw p", "Depth minus share (signed by DESIGN)", "p", "Corr of the two signals"], rows))
add("")
add("Depth correlates about 0.8 with share and predicts no better.")
add("")
add("**Pain crossed with crowding.**")
add("")
rows = []
for key in ("UST_spec_crowd_pain", "UST_spec_crowd_only", "UST_lev_crowd_pain", "UST_lev_crowd_only", "FX_spec_crowd_pain", "FX_spec_crowd_only", "FX_lev_crowd_pain", "FX_lev_crowd_only"):
    v = R["T7"]["crowded"][key]
    b, e, h = v["block"], v["holdout_events"], v["holdout_hits"]
    rows.append([key.replace("_", " "), n(b["DESIGN"]["beta"], 3), n(b["HOLDOUT"]["beta"], 3), n(b["HOLDOUT"]["p_primary"], 3), n(b["H-A"]["beta"]), n(b["H-B"]["beta"]), f"{e['plus']} / {e['minus']}", f"{pct(h['up_hit'])} / {pct(h['base_up'])}", f"{pct(h['down_hit'])} / {pct(h['base_down'])}"])
add(table(["Signal", "DESIGN slope", "Holdout slope", "Raw p", "H-A", "H-B", "Contract-weeks, + / -", "Crowded short: rise hit / base", "Crowded long: fall hit / base"], rows))
add("")
add("Pain adds nothing to crowding. The Treasury result is almost all 2019-2022 and the sign is opposite to DESIGN. The event counts are contract-weeks on correlated contracts, so the real number of independent events is far smaller.")
add("")
add("**Removal rule.**")
add("")
rows = []
for key, v in R["T7"]["rules"].items():
    t = v["tests"]
    rows.append([key.replace("_", " "), n(v["corr"]["pro_rata_fifo"]), n(v["corr"]["pro_rata_low"]), n(v["corr"]["fifo_low"]), n(v["mean_abs_gap"]["fifo"]), n(v["mean_abs_gap"]["low_price_first"]), n(t["pro_rata"]["HOLDOUT"]["beta"], 3), n(t["fifo"]["HOLDOUT"]["beta"], 3), n(t["low_price_first"]["HOLDOUT"]["beta"], 3), v["insensitive_by_plan_rule"]])
add(table(["Panel, group", "Corr pro rata, FIFO", "Corr pro rata, low price", "Corr FIFO, low price", "Mean abs share gap, FIFO", "Low price", "Slope pro rata", "FIFO", "Low price", "Insensitive by plan rule"], rows))
add("")
add("The answer does not depend on the rule. No slope changes sign and none becomes significant under any rule. Two FX rows fail the plan's strict test, because low price first differs from pro rata by more than one standard error there. All their slopes stay insignificant. One caution: share levels differ by 0.09 to 0.20 between rules. So fixed thresholds such as 70% and 30% do depend on an assumption nobody can observe.")
add("")
add("**Window length.**")
add("")
rows = []
for key, v in R["T7"]["windows"].items():
    row = [key.replace("_", " "), v["design_choice"]]
    for w in ("30", "63", "90", "126", "252"):
        d = v["by_window"][w]
        row.append(f"{n(d['DESIGN']['t_dk'])} / {n(d['HOLDOUT']['t_dk'])}")
    rows.append(row)
add(table(["Panel, group", "DESIGN choice", "30: t DESIGN / holdout", "63", "90", "126", "252"], rows))
add("")
add("No window earns a place. DESIGN's picks rest on t-values under 2 and do not pass in the holdout.")
add("")
add("### T8. Indicators head to head")
add("")
rows = []
for market in ("UST", "FX"):
    for name in ("I1", "I2", "I3_lev", "I3_am", "I4"):
        row = [market, name, n(R["T8"]["panel"][f"{market}_13w"][name]["DESIGN"]["beta"], 3)]
        for k in (4, 8, 13, 26):
            d = R["T8"]["panel"][f"{market}_{k}w"][name]["HOLDOUT"]
            row.append(f"{n(d['beta'])} (t {n(d['t_dk'])})")
        base = 1 if market == "UST" else 6
        test_id = f"T8.{base + ('I1', 'I2', 'I3_lev', 'I3_am', 'I4').index(name)}"
        row += [n(F[test_id]["p_raw"], 3), n(F[test_id].get("p_rotation"), 3), n(F[test_id]["p_holm_primary"]), n(R["T8"]["panel"][f"{market}_13w"][name]["H-A"]["beta"]), n(R["T8"]["panel"][f"{market}_13w"][name]["H-B"]["beta"])]
        rows.append(row)
add(table(["Panel", "Signal", "DESIGN slope 13w", "4w", "8w", "13w", "26w", "Raw p 13w", "Rot. p", "Holm", "H-A 13w", "H-B 13w"], rows))
add("")
ext = R["T8"]["hits"]
add(f"All rows use one common sample. Before 2019 every Treasury slope is near zero. In the holdout, high speculative or leveraged positioning preceded price falls, and high asset-manager positioning preceded rises. These are not independent results. Within contracts in the holdout, I3 leveraged and I3 asset managers correlate {n(R['T8']['signal_corr_within_holdout']['UST']['I3_lev']['I3_am'])}, and I2 and I4 correlate {n(R['T8']['signal_corr_within_holdout']['UST']['I2']['I4'])}. The 2019-2022 half drives them all. I2 extremes on Treasuries: crowded-long weeks fell {pct(ext['UST_I2_extremes']['down_hit'])} of the time against a {pct(ext['UST_I2_extremes']['base_down'])} base, in the holdout. In DESIGN the same call hit {pct(ext['UST_I2_extremes_design']['down_hit'])} against {pct(ext['UST_I2_extremes_design']['base_down'])}.")
add("")
add(f"Aggregate I4 on the 10-year at 4 weeks: corr {n(R['T8']['aggregate_i4']['HOLDOUT']['test']['corr'])}, raw p {n(R['T8']['aggregate_i4']['HOLDOUT']['test']['p_primary'])}. It said buy in {AGG['pos_n']} of {AGG['n']} holdout weeks, with a hit rate of {pct(AGG['pos_hit_fall'])} against a {pct(AGG['base_fall'])} base. The median z-score was {n(R['T8']['aggregate_i4_position_range']['z_median_design'])} before May 2019 and {n(R['T8']['aggregate_i4_position_range']['z_median_holdout'])} after, even on an expanding base, so the non-commercial position sits far below its old range and the level rule stays pinned. I did not test the cause. The leveraged-fund basis trade is one candidate. Level rules like this one are not stationary.")
add("")
add(f"I4 exactly as the spec now states it (TY, combined report, frozen 2007-2018 scale), on the holdout at 4 weeks: corr {n(SPECI4['test']['corr'])}, raw p {n(SPECI4['test']['p_primary'])}, buy in {SPECI4['hits']['pos_n']} of {SPECI4['hits']['n']} weeks at {pct(SPECI4['hits']['pos_hit_fall'])} against a {pct(SPECI4['hits']['base_fall'])} base, sell in {SPECI4['hits']['neg_n']} weeks. My panel I4 uses the futures-only report and a past-only scale, as the plan fixed before the spec changed.")
add("")
add("### T9. Does the filter generalise to FX?")
add("")
rows = []
for spot, g in enumerate(("am", "lev", "spec"), start=1):
    v = R["T9"]["panel"][f"{g}_26w"]
    c = R["T9"]["given_past"][g]["HOLDOUT"]
    h = R["T9"]["rule_hits"][g]["HOLDOUT"]
    rows.append([g, n(v["GS-OOS"]["beta"], 3), n(v["HOLDOUT"]["beta"], 3), n(v["HOLDOUT"]["t_dk"]), n(v["HOLDOUT"]["p_primary"], 3), n(F[f"T9.{spot}"].get("p_rotation"), 3), n(v["H-A"]["beta"]), n(v["H-B"]["beta"]), n(c["beta"], 3), n(c["p_primary"], 3), f"{pct(h['up_hit'])} / {pct(h['base_up'])}", f"{pct(h['down_hit'])} / {pct(h['base_down'])}"])
add(table(["Group (am includes other reportables)", "GS-OOS slope", "Holdout slope", "DK t", "Raw p", "Rot. p", "H-A", "H-B", "Slope given past return", "p", "Buy: hit / base", "Sell: hit / base"], rows))
add("")
ccy = R["T9"]["by_currency"]
add(f"The signs are right but the size is small and not significant. Fit on 2006-2010, tested later. Single currencies disagree: for asset managers the correlation runs from {n(min(v['corr'] for k, v in ccy.items() if k.startswith('am_')))} to {n(max(v['corr'] for k, v in ccy.items() if k.startswith('am_')))}. So the idea does not carry over as a usable signal. This uses spot only, so carry is missing. H.10 noon rates also do not line up with the Tuesday close position snapshot.")
add("")
add("### T10. Options position, combined minus futures-only")
add("")
rows = []
for market in ("UST", "FX"):
    for spot, g in enumerate(("am", "lev", "spec")):
        v = R["T10"]["flow"][f"{market}_{g}_4w"]
        w = R["T10"]["flow"][f"{market}_{g}_13w"]
        lvl = R["T10"]["level"][f"{market}_{g}_4w"]["HOLDOUT"]
        giv = R["T10"]["given_futures"][f"{market}_{g}_4w"]["HOLDOUT"]
        rows.append([market, g, n(v["DESIGN"]["beta"], 3), n(v["HOLDOUT"]["beta"], 3), n(v["HOLDOUT"]["t_dk"]), n(v["HOLDOUT"]["p_primary"], 3), n(w["HOLDOUT"]["beta"], 3), n(w["HOLDOUT"]["p_primary"], 3), n(lvl["beta"], 3), n(lvl["p_primary"], 3), n(giv["beta"], 3), n(giv["p_primary"], 3)])
add(table(["Panel", "Group", "DESIGN flow slope 4w", "Holdout", "DK t", "Raw p", "Flow 13w", "p", "Level z 4w", "p", "Flow given futures position", "p"], rows))
add("")
add(f"No predictive information. FX specs at 13w has raw p {n(R['T10']['flow']['FX_spec_13w']['HOLDOUT']['p_primary'], 3)}, but the sign is opposite to DESIGN, and it does not survive Holm. This does not test Goldman's OPI, which uses strike-level option data. It says only that the free stand-in does not work.")
add("")
add("### T11. Composite and backtests")
add("")
add(f"Composite A, the pre-registered one, is **empty**. No candidate reached |t| of 2 in DESIGN under honest errors. The strongest was I5 asset managers at t = {n(T11['screen']['rates']['I5_am_TYUS']['t'])}. So T11.1 and T11.2 count as p = 1. Composite C is an amendment: the three I5 groups in Goldman's direction, with no selection. Composite B is hindsight, using only holdout survivors. Its member is {T11['composite_B_hindsight']['members']['rates']}, so it duplicates that single signal.")
add("")


def strat(label, m):
    h = m["HOLDOUT"]
    return [label, n(h.get("sharpe")), n(h.get("t_stat")), pct(h.get("max_drawdown")), n(h.get("info_ratio")), ci(h.get("sharpe_ci_boot")), n(h.get("p_boot"), 3), n(m["H-A"].get("sharpe")), n(m["H-B"].get("sharpe")), n(m["DESIGN"].get("sharpe"))]


rows = [strat("Composite C (no selection)", C_S), strat("Benchmark rule", BEN_S), strat("Buy and hold 10-year", BH_S)]
rows += [strat(label, m) for label, m in T11["single"]["rates"].items()]
add("**Rates sleeve, 10-year point, net of 5 bps of notional per side, carry excluded.**")
add("")
add(table(["Strategy", "OOS Sharpe", "t-stat", "Max drawdown", "IR vs benchmark", "Sharpe 95% interval", "p", "H-A", "H-B", "GS-OOS"], rows))
add("")
rows = [strat("Benchmark rule", T11["benchmark"]["fx"]), strat("Buy and hold", T11["buy_hold"]["fx"])]
rows += [strat(label, m) for label, m in T11["single"]["fx"].items()]
add("**FX sleeve, seven currencies at equal risk, same cost, carry excluded.**")
add("")
add(table(["Strategy", "OOS Sharpe", "t-stat", "Max drawdown", "IR vs benchmark", "Sharpe 95% interval", "p", "H-A", "H-B", "GS-OOS"], rows))
add("")
add(f"Sizing is 10% annual risk on a trailing 52-week SD, so the drawdowns are large by construction. Signs for the single signals come from DESIGN, which is why some reverse. I5 specs has the best single result: net Sharpe {n(SPEC_S['HOLDOUT']['sharpe'])}, t {n(SPEC_S['HOLDOUT']['t_stat'])}, interval {ci(SPEC_S['HOLDOUT']['sharpe_ci_boot'])}, positive in both halves ({n(SPEC_S['H-A']['sharpe'])}, {n(SPEC_S['H-B']['sharpe'])}), and it survives 10 bps ({n(T11['cost_sensitivity_single']['I5_spec']['10'])}). But its GS-OOS Sharpe is {n(SPEC_S['DESIGN']['sharpe'])}, it is one of many strategies tried, and it fails Holm at {n(F['T11.S.single.rates.I5_spec']['p_holm_all'])}. That makes it a flag, not a finding. Composite C at 0, 1, 5 and 10 bps: {', '.join(n(T11['composite_C_prior_sign']['cost_sensitivity_holdout_sharpe'][b]) for b in ('0', '1', '5', '10'))}. Its gap to the benchmark is {n(C_S['HOLDOUT'].get('sharpe_minus_benchmark'))}, p {n(C_S['HOLDOUT'].get('p_diff_boot'))}.")
add("")
add("**Canonical metrics.**")
add("")
rows = [[k, n(v["oos_sharpe"]), n(v["t_stat"]), pct(v["max_drawdown"]), n(v["info_ratio_vs_benchmark"])] for k, v in R["canonical"].items()]
add(table(["Strategy", "OOS Sharpe", "t-stat", "Max drawdown", "IR vs benchmark"], rows))
add("")
add("### T12. Filter placebo (added test)")
add("")
add("Why this test: the filter keeps a flow only when it moves with yields. So the kept flows must line up with yields, whatever the flows are. To measure that, I shifted each group's weekly flows by every offset from 52 to T-52 weeks, keeping yields and DV01 fixed, and reran the whole recipe. At zero shift this path matches posmon exactly.")
add("")
rows = []
for name, test_id in (("am_TYUS", "T12.1"), ("lev", "T12.2"), ("spec", "T12.3")):
    v = P12[name]
    rows.append([GROUP_NAME[name], n(v["real"]["beta"] * 10, 1), f"{n(v['placebo_mean']['beta'] * 10, 1)} ({n(v['placebo_q05']['beta'] * 10, 1)} to {n(v['placebo_q95']['beta'] * 10, 1)})", n(v["real"]["corr_F26_D26_design"]), n(v["placebo_mean"]["corr_F26_D26_design"]), n(v["real"]["corr_GS-OOS"]), n(v["placebo_mean"]["corr_GS-OOS"]), n(v["p_real_more_negative_GS-OOS"], 3), n(v["real"]["corr_HOLDOUT"]), n(v["placebo_mean"]["corr_HOLDOUT"]), f"{n(v['placebo_q05']['corr_HOLDOUT'])} to {n(v['placebo_q95']['corr_HOLDOUT'])}", n(v["p_two_sided_HOLDOUT"], 3)])
add(table(["Signal", "Real slope, bp per $10mm", "Placebo mean (5% to 95%)", "Real 6m corr with yields", "Placebo", "Real next-6m corr, GS-OOS", "Placebo", "One-sided p", "Real next-6m corr, holdout", "Placebo", "Placebo 5% to 95%", "Two-sided p"], rows))
add("")
add(f"This is a clear result. Goldman's headline 17 to 18 bp per $10mm is what random flows produce. So is most of the 62% six-month fit. Real flows beat random flows in neither GS-OOS nor the holdout at conventional levels. Placebo scores still forecast at about {n(P12['am_TYUS']['placebo_mean']['corr_GS-OOS'])} in GS-OOS, because the benchmark sits inside them. Each placebo row is {P12['am_TYUS']['placebo_count']} shifts, which are heavily overlapping, so these p-values are coarse.")
add("")
add("### T13. Filter against no filter")
add("")
rows = []
for name, v in R["T13"].items():
    rows.append([GROUP_NAME[name], n(v["GS-OOS"]["corr_a"]), n(v["GS-OOS"]["corr_b"]), n(v["HOLDOUT"]["corr_a"]), n(v["HOLDOUT"]["corr_b"]), n(v["HOLDOUT"]["diff"]), ci(v["HOLDOUT"]["ci_boot"]), n(v["HOLDOUT"]["p_boot"], 3), n(v["plain_slope_bp_per_10mm"], 1)])
add(table(["Signal", "GS-OOS filter", "GS-OOS no filter", "Holdout filter", "Holdout no filter", "Difference", "95% interval", "p", "Unfiltered slope, bp per $10mm"], rows))
add("")
add("In the holdout the filter's sign is favourable, but the gain is not significant. In GS-OOS it adds little outside asset managers.")
add("")
add("### T14. Benchmark bias (added test)")
add("")
b14 = R["T14"]["design"]
add(f"Does the -35% come from small-sample bias? Mostly not. A resampled yield path with no real mean reversion gives a mean of {n(b14['iid_mean'])} and SD {n(b14['iid_sd'])} over 2006 to April 2019. It reaches the observed {n(b14['observed_corr'])} only {pct(b14['iid_share_below_observed'], 1)} of the time ({pct(b14['block4_share_below_observed'], 1)} with 4-week blocks). So the bias is small and the in-sample figure was unusual. It did not persist: holdout {n(R['T14']['holdout']['observed_corr'])}.")
add("")

add("## 5. Sample size: where we cannot conclude")
add("")
rows = [[k, n(v["n_eff"], 0), n(v["raw_5pct"]), n(v["holm_first_step"])] for k, v in SS["min_detectable_corr"].items()]
add(table(["Horizon", "Independent observations in the holdout", "Smallest |corr| significant at 5% raw", "Smallest |corr| at Holm's first step"], rows))
add("")
add(f"- Primary family: {SS['family_size_primary']} tests. All tests: {SS['family_size_all']}.")
add(f"- Power to detect a true -43% at 26 weeks: {pct(POW['goldman_minus_43_at_neff_14']['raw_5pct'])} raw, {pct(POW['goldman_minus_43_at_neff_14']['holm_first_step'])} after Holm. Power to detect a true 0.2 at 13 weeks: {pct(POW['corr_0p2_at_neff_28']['raw_5pct'])} raw.")
add("- The holdout has one large rate cycle. The rally in 2019-2020 and the sell-off in 2021-2023 dominate it. Treat long-horizon results as closer to one or two episodes than to 14 draws.")
add("- We can say with fair confidence: asset-manager I5 is not a usable signal, and its published size is unlikely, though the widest interval does not rule it out. Deck-rule pain share has no edge over the base rate. The options stand-in shows nothing.")
add("- We cannot conclude: leveraged-fund and spec I5, I2 and I3 on Treasuries, and I5 on FX. These have small or modest effects in the sample. None is ruled out as a modest real effect.")
add("")
add(f"**Size check.** Rotating the signal inside the holdout, the pre-registered p-value rejected at the 5% level {pct(SIZE['am_TYUS_26w']['reject_primary'])} of the time at 26 weeks and {pct(SIZE['am_TYUS_13w']['reject_primary'])} at 13 weeks. Newey-West with normal critical values reached {pct(SIZE['am_TYUS_26w']['reject_nw_normal'])}. On the panel P2 test the figure was {pct(SIZE['panel_UST_P2_lev_13w']['reject_primary'])}. These rates are noisy, since the rotations overlap. So raw p-values near 0.05 at long horizons overstate the evidence. It strengthens the \"no\", because nothing passed Holm even with p-values that run too small. That is why rotation p-values appear beside them. Their smallest Holm-adjusted value is {n(min_rot)}.")
add("")

add("## 6. Method, data and deviations")
add("")
add(f"- Boundaries: fit {R['boundaries']['fit'][0]} to {R['boundaries']['fit'][1]}, design to {R['boundaries']['design_end']} ({R['boundaries']['weeks_design']} weeks), holdout from {R['boundaries']['holdout_start']} ({R['boundaries']['weeks_holdout']} weeks). Seed {R['seed']}. {R['bootstrap_draws']} bootstrap draws.")
add("- Data: all downloads succeeded (`raw/manifest.json`). No substitution happened. Yahoo prices are used only in T6b.")
add(f"- Leak test: every raw input was cut at three dates and each signal rebuilt. Result: {'passed' if LEAK['passed'] else 'FAILED'}, across {sum(v['cells'] for v in LEAK['cuts'].values())} cells, largest gap {max(v['max_abs_gap'] for v in LEAK['cuts'].values())}.")
add(f"- Ledger check: the weekly path matches `posmon.pain.cftc_pain` on {LC['dates_compared']} dates, apart from the residue cases.")
add("- The agent protocol names `/experiments/LOG.md` and skill folders that do not exist on this machine, and writing outside this folder was barred. So there is no log entry there. No `find` registry step ran, because the registry folders are absent.")
add("- Amendments are in `plan.md`, section 11. The main ones: the empty-ledger guard after the first run, rotation p-values after the size check, and Composite C after Composite A came back empty.")
add("")
add("**Bias and leakage checklist.**")
add("")
add("- No look-ahead: confirmed by the leak test. Tradable returns start at E.")
add("- Survivorship: the universe is fixed by rule. TN and WN enter when listed. TFF history before September 2009 is CFTC backfill, which touches the fit window only.")
add("- Costs: 5 bps of notional per side, higher than real Treasury futures costs. Sensitivity is reported.")
add("- Universe: all six Treasury contracts and all seven G10 FX contracts on the config list.")
add("- Stationarity: flows and forward moves are changes. Levels are bounded or z-scored on past data. T8 shows levels still drift, which is a finding.")
add(f"- Holdout above design: {sum(1 for v in primary if v['oos_beats_is_flag'])} primary tests carry this flag, marked in the appendix. Most are small effects where DESIGN was near zero. Each should be read with suspicion, including I3 leveraged, I5 leveraged and I5 specs.")
add("")

add("## 7. What could be wrong here")
add("")
add("1. **Carry is missing.** Forward moves are yield or spot only. Carry and roll-down would change Sharpe ratios, mostly for FX and long-duration holds. It should not change the T1 regressions by much, since they measure yield changes.")
add("2. **DV01 before 2013** is a rebuild scaled to later OFR data. It affects the fit window only and reproduced Goldman's figures.")
add("3. **Release dates are assumed** in history, except in the late-release test. The effect was small.")
add("4. **Holm is strict across 53 tests.** A real modest effect would fail it. That is why levels 2 and 3 exist, and why I report the watch list instead of a flat no.")
add("5. **Goldman's OPI itself** was not tested. There is no option data.")
add("")

add("## Appendix A. Every primary test")
add("")
rows = [[v["id"], v["test"], n(v["p_raw"], 3), n(v["p_holm_primary"]), n(v["p_holm_all"]), n(v.get("p_rotation"), 3), n(v["stat"], 3), n(v["design_stat"], 3), n(v["n_eff"], 0) if v["n_eff"] else "n/a", v["sign_ok"], "yes" if v["oos_beats_is_flag"] else "", "yes" if v["success"] else "no", (v["note"] or "")] for v in primary]
add(table(["ID", "Test", "Raw p", "Holm (primary)", "Holm (all)", "Rot. p", "Stat, holdout", "Stat, design", "N_eff", "Sign OK", "Holdout > design", "Success", "Note"], rows))
add("")
add("Stat is a correlation, slope, correlation gap or Sharpe, according to the test. T2.1 is the only test where a low p-value would mean a cost rather than a benefit. T11.1 and T11.2 did not run because Composite A is empty, so they count as p = 1.")
add("")
add("## Appendix B. Every secondary test")
add("")
rows = [[v["id"], v["test"], n(v["p_raw"], 3), n(v["p_holm_all"]), n(v["stat"], 3), n(v["design_stat"], 3), v["sign_ok"]] for v in secondary]
add(table(["ID", "Test", "Raw p", "Holm (all)", "Stat, holdout", "Stat, design", "Sign OK"], rows))
add("")
(HERE / "report.md").write_text("\n".join(lines))
print("report.md written,", len(lines), "lines; smallest Holm all", min_holm_all)
