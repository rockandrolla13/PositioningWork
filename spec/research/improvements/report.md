# Positioning methods: out-of-sample results

Built from `results.json`. Plan fixed in `plan.md` before any test ran. Data through report date 2026-10-27. Holdout starts 2019-05-07.

## 1. Bottom line

**Nothing predictive survives.** 53 primary tests ran. The smallest Holm-adjusted p-value is 1.00. The smallest raw p-value is 0.030. Tests that meet their success rule: 0.

1. **The Goldman asset-manager signal failed.** Its published correlation of -43% mixes the fit period (-64%) with the later years (-27%). In the real holdout it is +4%. The block-bootstrap 95% interval is [-19, 19] percent, which excludes the claim. A more cautious interval built on 14 independent observations is [-50, 56] percent, which does not. So the published size is unlikely, though not impossible. What settles the verdict is everything else: the sign is wrong at all four horizons, rally calls hit below the base rate, real flows do no better than random flows, and a strategy trading it lost money (net Sharpe -0.54).
2. **The filter creates much of the fit by itself.** Random flows pushed through the same filter already give a six-month correlation of 47% with yields, against 62% for real flows, and a slope of -18.3 bp per $10mm against the real -17.2. Unfiltered asset-manager flows give 2.9, with the opposite sign.
3. **Pain share has no edge.** The 2018 deck rule hits at the base rate: on Treasuries, leveraged funds, 60.2% against 60.2% on sells and 39.5% against 39.8% on buys. Depth, window length, crowding and removal rule change nothing that matters.
4. **The closest thing to a survivor is on a watch list, not adopted.** Leveraged-fund I3 read as a contrarian signal on Treasuries, 13 weeks: raw p 0.044, rotation p 0.003, Holm 1.00, rotation Holm 0.12. Almost all of it comes from 2019 to 2022. Its net Sharpe is 1.01 then -0.52.
5. **The sample limits what a "no" means.** A 26-week horizon gives about 14 independent observations in the holdout. Power to detect a true -43% is 33% before correction and 4% after. So non-significance alone proves little. The asset-manager verdict rests on the evidence in item 1, not on the p-value. The leveraged-fund and spec versions stay unresolved.

**Adopt three things.** None of them adds predictive power. They remove errors at no cost. See sections 2 and 3.

## 2. Improvements ranked by evidence

Levels come from `plan.md`, section 9. Level 1 means confirmed. Level 2 means suggestive. Level 3 means inconclusive. Level 4 means rejected.

| Decision | Improvement | Level | Key numbers |
|---|---|---|---|
| Adopt | Empty-ledger guard (bug fix) | Not a predictive claim | 634 of 80956 ledgers held floating-point residue. 94 gave a share outside 0 to 1, up to 2e+31. One such value corrupted my first run. |
| Adopt | Monday entry for every test | Not a predictive claim | Removes look-ahead. It costs 0.010 of correlation on asset managers at 26w. The largest cost anywhere is 0.036. |
| Adopt | Synthetic roll-free Treasury price | Not a predictive claim | Daily change correlation with real TY closes is 0.945. P2 on it matches P2 on unadjusted Yahoo prices: DESIGN t -1.09 against -1.04. It is free and needs no roll calendar. It is a data choice, not a signal gain. |
| Watch | I3 leveraged funds, contrarian, Treasuries | Level 2 | Slope -0.48 per SD, raw p 0.044, Holm 1.00. DESIGN slope -0.045. Halves -0.72 and -0.13. Net Sharpe 0.27. Fails adoption: no cost-free reason. |
| Reject for now | I5 on leveraged funds or specs instead of asset managers | Level 3 | Holdout correlations -31% and -22%, raw p 0.12 and 0.22. Post-fit 2011-2018 was only -5% and -11%. Flagged: holdout beats design. It also depends on a stale beta (T4). |
| Reject for now | With-the-market filter over raw flows | Level 3 | Paired corr gain -0.12, p 0.58, on asset managers. Real flows do not beat shifted flows (T12). |
| Reject for now | Filter applied to FX | Level 3 | Slopes 0.10, 0.11, 0.10, right sign, p 0.41, 0.26, 0.21. Single currencies disagree in sign. |
| Reject | Pain crossed with crowding | Level 4 | Treasuries slope 0.20, p 0.071, but DESIGN has the opposite sign (-0.023), and crowding alone gives 0.21. So pain adds nothing. FX 0.008. |
| Reject | Walk-forward beta or scale in I5 | Level 4 | Beta really did decay (T4). But updating it moves the asset-manager correlation the wrong way by 0.05 (expanding) and 0.14 (rolling). |
| Reject | Fresh score (add the yield move from Tuesday to Monday) | Level 4 | Correlation gain -0.005 at 26w. |
| Reject | Depth instead of share | Level 4 | Paired gain 0.017 (p 0.88) on Treasuries and -0.005 (p 0.83) on FX. |
| Reject | Longer or shorter pain window | Level 4 | DESIGN chose 252 days for Treasuries and 63 for FX. Holdout p 0.26 and 0.25. |
| Reject | Options position from combined minus futures | Level 4 | Six tests. Smallest raw p 0.14. 4 of six have the opposite sign to DESIGN. |
| Reject | Composite | Level 4 | The plan's composite is empty, because no signal reached |t| of 2 in DESIGN. The no-selection version has net Sharpe 0.23 (t 0.63). |

## 3. Recipes ready for the spec

**R1. Empty ledger (P1, P2, ledger section).** Add to the decision box:

> Empty ledger: if open contracts total 1e-6 or less, return no reading. A full removal can leave floating-point residue near 1e-14 contracts, and dividing by it gives shares near 1e16.

Code change for `posmon/pain.py`, which I did not edit, as instructed:

```python
def _ratio(top: float, bottom: float, floor: float = 1e-6) -> float:
    return top / bottom if bottom > floor else float("nan")
```

Evidence: on TY leveraged-fund longs alone, 7 of 130 dates from 2013 to 2015 read a number from an empty ledger. Add a test that every share stays inside 0 to 1.

**R2. Entry timing (section on how to test any signal).** Add:

> Measure every forward move from the close of the first trading day on or after the Monday after release. For FX from H.10, use that day's noon rate. Call this date E. Forward change = level(E + 7k days) minus level(E), using the last observation on or before each date. Measuring from the Tuesday report date is look-ahead.

**R3. Synthetic Treasury price (market data section).** Add:

> A roll-free Treasury price, per contract, in percent of face: P(t) = P(t-1) - 100 x DV01(t-1) / Face x (y(t) - y(t-1)). DV01 is the last weekly value in `data/treasury_futures_dv01.csv` known on the prior day. Face is $200,000 for TU and $100,000 for the rest. y is the contract's FRED yield in basis points: TU DGS2, FV DGS5, TY DGS7, TN DGS10, US DGS20, WN DGS30. This price has no carry and no roll-down. It tracks a constant-maturity yield, not the cheapest-to-deliver.

**R4. Corrections to the current I4, I5 and S1 text.** Other agents updated the spec during this run, so these target its latest wording.

- I5 carries the label "Verified". That label is right about the replication and could be misread as a claim that the signal works. Add this warning box: "Verified means this build matches Goldman's charts. It does not mean the signal works. From May 2019 to the latest data, with Monday entry, the asset-manager correlation with the next 26-week yield change is +4%, against -27% for 2011 to 2018 and -43% as published. The published number includes the fit period. The slope of 17 to 18 bp per $10mm appears with random flows too, because the filter keeps only flows that move with yields. Do not trade I5."
- I4: the frozen scale from January 2007 to June 2018 is look-ahead inside that window, so hit rates there are in-sample. After it, on the holdout, the rule said buy in 282 of 386 weeks and sell in 18, and the buy hit rate was 43% against a 43% base. Add that as a warning. Use I4 as a benchmark only.
- S1 (deck rule): add that hits equal the base rate in the holdout.

**Watch-list recipe, paper only. Not for trading.** I3 contrarian on Treasuries. Use TFF futures-only leveraged-fund net. Compute I3 over 209 weeks. Convert to a z-score with an expanding mean and SD, minimum 52 weeks. Flip the sign. Clip to -1 and +1. Enter at E, hold one week, size to 10% annual risk on a trailing 52-week SD. Promote only if it holds in new data after this date with Holm-level evidence.

## 4. Test by test

Conventions: "holdout" is May 2019 onward. "GS-OOS" is 2011 to April 2019, after the fit but inside Goldman's published sample. Entry is Monday unless stated. All hit rates sit beside their base rates. Raw p is the larger of the Newey-West and block-bootstrap p-values. Rotation p is a second null added after the size check (amendment A2).

### T1. I5 out of sample

Replication passed first. Through April 2019 on Goldman's basis: asset managers -43.2% (claim -43%), leveraged funds -18.8% (-18%), specs -25.8% (-26%), benchmark -35.3% (-35%), last score -0.66 (-0.67), rows 621 (620).

| Signal | GS-OOS corr | Holdout corr | Block 95% interval (pct) | Cautious 95% interval on N_eff (pct) | H-A | H-B | N_eff | NW t | Raw p | Rot. p | Rally bias: hit / base | Avg bp | Sell-off bias: hit / base | Avg bp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Asset managers + others, TY and US | -27% | **4%** | [-19, 19] | [-50, 56] | 9% | -4% | 14 | 0.39 | 0.801 | 0.869 | 30% / 39% | 30 | 57% / 61% | 19 |
| Asset managers + others, all six | -33% | **-1%** | [-23, 27] | [-54, 53] | -10% | 34% | 14 | -0.07 | 0.995 | 0.987 | 37% / 39% | 15 | 65% / 61% | 30 |
| Leveraged funds, all six | -5% | **-31%** | [-57, 0] | [-72, 27] | -35% | -28% | 14 | -1.69 | 0.117 | 0.208 | 54% / 39% | -8 | 72% / 61% | 40 |
| Non-commercial specs, all six | -11% | **-22%** | [-50, 12] | [-67, 35] | -26% | -20% | 14 | -1.28 | 0.225 | 0.198 | 49% / 39% | 4 | 67% / 61% | 34 |
| Benchmark: past 26w change | -15% | **14%** | [-34, 39] | [-42, 62] | 27% | -33% | 14 | 0.80 | 0.625 | 0.658 | 38% / 39% | 26 | 56% / 61% | 3 |

What it means. Asset managers: a rally call was right 30% of the time, below the 39% base rate. The average move after a rally call was +30 bp, the wrong way. The holdout was a bear market, with yields up 20 bp on average over 26 weeks, so the base rate matters. TY and US against all six makes no difference: 0.05 (p 0.88). Against the benchmark, no group wins: the closest is leveraged funds at -0.45 (p 0.20).

The plain benchmark also failed: 14% against the claimed -35%. It behaved in opposite ways in the two halves: 27% then -33%. Goldman's number also rested on the crisis years: fit rows -61%, later rows -16%.

### T2. Tradability

| Signal | Horizon | Corr Tuesday (look-ahead) | Corr Monday | Difference | 95% interval | p |
|---|---|---|---|---|---|---|
| Asset managers + others, TY and US | 4w | 0.10 | 0.09 | 0.011 | [-0.05, 0.07] | 0.740 |
| Asset managers + others, TY and US | 13w | 0.09 | 0.08 | 0.010 | [-0.03, 0.04] | 0.580 |
| Asset managers + others, TY and US | 26w | 0.05 | 0.04 | 0.010 | [-0.02, 0.03] | 0.391 |
| Leveraged funds, all six | 4w | -0.18 | -0.17 | -0.015 | [-0.07, 0.04] | 0.603 |
| Leveraged funds, all six | 13w | -0.24 | -0.21 | -0.026 | [-0.05, 0.01] | 0.158 |
| Leveraged funds, all six | 26w | -0.33 | -0.31 | -0.020 | [-0.04, 0.00] | 0.070 |
| Non-commercial specs, all six | 4w | -0.22 | -0.20 | -0.022 | [-0.08, 0.03] | 0.434 |
| Non-commercial specs, all six | 13w | -0.24 | -0.20 | -0.036 | [-0.06, -0.00] | 0.040 |
| Non-commercial specs, all six | 26w | -0.24 | -0.22 | -0.021 | [-0.05, 0.01] | 0.234 |

The lag costs almost nothing. The largest gap is 0.036 of correlation. A weekly rule on asset managers in the holdout makes -0.76 bp a week from Tuesday and -0.68 from Monday. The signal moves too slowly for six days to matter. Dropping the 20 late-release weeks (ION 2023, shutdown 2025, per the [CFTC notices](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm)) moves asset managers to 3% and leveraged funds to -31%. History still assumes Friday releases elsewhere.

### T3. Does the score add to the benchmark?

Structure first. Score = (past 26w yield change - 26 alpha - beta x flows) / scale. So the benchmark sits inside the score, and the test on the score is the same test as the one on the positioning term.

| Signal | Corr with past change, GS-OOS | Holdout | Slope GS-OOS (bp per unit) | t | Slope holdout | t, lag 39 | t, lag 26 | 95% block interval | Raw p | Rot. p | Incremental OOS R2 | Clark-West p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Asset managers + others, TY and US | 0.79 | 0.69 | -27.1 | -1.86 | -6.9 | -0.57 | -0.54 | [-41.3, 19.8] | 0.644 | 0.684 | -0.051 | 0.32 |
| Leveraged funds, all six | 0.31 | -0.36 | -0.3 | -0.03 | -10.4 | -1.78 | -1.78 | [-25.8, 1.2] | 0.102 | 0.198 | -0.048 | 0.74 |
| Non-commercial specs, all six | 0.22 | -0.35 | -4.8 | -0.47 | -12.2 | -1.09 | -1.16 | [-39.8, 10.6] | 0.300 | 0.240 | -0.012 | 0.42 |

Effective sample: 364 overlapping weeks, about 14 independent. No group adds to the benchmark. All incremental out-of-sample R-squared values are negative. The asset-manager score is mostly the benchmark in disguise: correlation 0.69. Forecasts from the benchmark alone are also worse than the expanding mean (OOS R2 -0.049).

### T4. Stability

| Slope, bp per $10mm/bp | 2006-2010 | 2011-2015 | 2016-Apr2019 | May2019-2022 | 2023-end |
|---|---|---|---|---|---|
| Asset managers + others, TY and US | -17.2 (t -7.6) | -14.9 (t -10.4) | -10.6 (t -9.0) | -12.7 (t -4.3) | -12.6 (t -7.9) |
| Leveraged funds, all six | -18.3 (t -10.5) | -12.3 (t -14.6) | -7.5 (t -8.2) | -8.0 (t -8.9) | -7.6 (t -11.4) |
| Non-commercial specs, all six | -18.1 (t -9.5) | -12.4 (t -13.0) | -6.7 (t -8.6) | -8.2 (t -9.7) | -9.2 (t -12.3) |

| Variant, holdout | AM corr | AM corr with past change | Lev corr | Lev corr with past change | Spec corr | Spec corr with past change |
|---|---|---|---|---|---|---|
| Fixed (recipe) | 0.04 | 0.69 | -0.31 | -0.36 | -0.22 | -0.35 |
| Expanding beta, fixed scale | 0.08 | 0.79 | -0.26 | 0.14 | -0.08 | 0.46 |
| Expanding beta and scale | 0.09 | 0.79 | -0.27 | 0.14 | -0.08 | 0.46 |
| Rolling 260w beta and scale | 0.18 | 0.85 | -0.14 | 0.47 | 0.08 | 0.72 |
| Fixed beta, expanding scale | 0.04 | 0.69 | -0.31 | -0.36 | -0.23 | -0.36 |

The slope is not stable. Leveraged funds and specs fell from about -18 to about -8, while asset managers fell from -17 to about -13. Yet refitting does not help. It makes the forecasts worse.

This explains a warning sign in T1 (a post-hoc reading, with no p-value). With the stale 2006-2010 beta, the leveraged and spec scores over-subtract flows. They then correlate negatively with the past yield change in the holdout, the opposite of their design-sample behaviour. So in the holdout they act as a flow-momentum signal, not as the reversal signal Goldman described. With an updated beta, that link turns positive and the forecast weakens, most sharply for specs and on the rolling fit. Treat the leveraged and spec holdout numbers with suspicion for this reason.

### T5. Horizons

| Horizon | AM TY+US: GS-OOS / holdout | Leveraged | Specs | Benchmark |
|---|---|---|---|---|
| 4w | -0.09 / 0.09 (p 0.40) | 0.01 / -0.17 (p 0.07) | -0.02 / -0.20 (p 0.01) | 0.02 / 0.03 (p 0.80) |
| 8w | -0.13 / 0.08 (p 0.50) | -0.03 / -0.20 (p 0.07) | -0.08 / -0.20 (p 0.08) | -0.00 / 0.02 (p 0.91) |
| 13w | -0.18 / 0.08 (p 0.50) | -0.05 / -0.21 (p 0.11) | -0.11 / -0.20 (p 0.16) | -0.05 / 0.06 (p 0.78) |
| 26w | -0.27 / 0.04 (p 0.80) | -0.05 / -0.31 (p 0.12) | -0.11 / -0.22 (p 0.22) | -0.15 / 0.14 (p 0.63) |

Asset managers fail at every horizon. Leveraged funds and specs are negative at every horizon in the holdout and near zero before 2019. Specs at 4w has the best raw p (0.015), a secondary test that does not survive Holm (1.00).

### T6. Pain P2 and the deck rule

| Panel | Group | DESIGN slope | Holdout slope | DK t | Raw p | Rot. p | H-A | H-B | Slope given past return | Corr with past return | Buy (long pain under 30%): hit / base | Sell (over 70%): hit / base |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| UST | lev | -0.101 | -0.122 | -0.82 | 0.455 | 0.470 | -0.38 | 0.16 | 0.035 | -0.45 | 39.5% / 39.8% | 60.2% / 60.2% |
| UST | am | -0.045 | -0.143 | -0.92 | 0.379 | 0.350 | -0.39 | 0.12 | 0.047 | -0.45 | 41.9% / 39.8% | 62.7% / 60.2% |
| UST | spec | -0.081 | -0.130 | -0.89 | 0.413 | 0.369 | -0.40 | 0.16 | 0.029 | -0.44 | 39.1% / 39.8% | 62.0% / 60.2% |
| FX | lev | -0.062 | 0.076 | 1.34 | 0.192 | 0.134 | 0.01 | 0.15 | 0.040 | -0.43 | 47.1% / 48.4% | 48.4% / 51.3% |
| FX | am | -0.061 | 0.089 | 1.39 | 0.175 | 0.178 | 0.04 | 0.17 | 0.057 | -0.46 | 49.5% / 48.4% | 51.7% / 51.3% |
| FX | spec | -0.060 | 0.092 | 1.59 | 0.125 | 0.126 | 0.04 | 0.16 | 0.058 | -0.44 | 47.2% / 48.4% | 50.8% / 51.3% |

Slopes are per one SD of net share, on returns in risk units, 13 weeks ahead. Pain share does not predict moves. It is largely past return in another form, with a correlation near -0.45. Once past return is in the regression, the Treasury slopes collapse. The two holdout halves also disagree in sign on Treasuries.

Coverage note: about 17% of Treasury contract-weeks have no net reading, because a ledger is empty on one side. That is P2's own rule.

### T6b. Is the synthetic price an improvement?

It is a sound substitute, not a signal gain. Against real TY closes (2014 to 2015, 124 days): correlation 0.945, slope 0.98, tracking error 0.11 points a day against a real daily SD of 0.35. Against Yahoo unadjusted front-month prices, daily correlations are 0.89 (TU), 0.93 (FV), 0.94 (TY), 0.93 (US). The P2 signals correlate 0.85 to 0.95. The slope gap is -0.004 in DESIGN (p 0.72) and -0.013 in the holdout (p 0.35). The plan's rule marks it "at least as strong". The gap is too small to call better. Its real gains are that it is free and has no roll jumps. The long bond tracks worst, because DGS20 is not its cheapest-to-deliver.

marketdb has no long futures history, so a true back-adjusted futures comparison was not possible.

### T7. Pain improvements

**Depth against share.**

| Panel | Group | DESIGN share slope | DESIGN depth slope | Holdout depth slope | Raw p | Depth minus share (signed by DESIGN) | p | Corr of the two signals |
|---|---|---|---|---|---|---|---|---|
| UST | lev | -0.101 | -0.152 | -0.139 | 0.478 | 0.017 | 0.879 | 0.79 |
| UST | am | -0.045 | -0.076 | -0.204 | 0.308 | 0.062 | 0.360 | 0.79 |
| UST | spec | -0.081 | -0.124 | -0.147 | 0.444 | 0.017 | 0.863 | 0.79 |
| FX | lev | -0.062 | -0.086 | 0.081 | 0.307 | -0.005 | 0.829 | 0.79 |
| FX | am | -0.061 | -0.005 | 0.119 | 0.111 | -0.029 | 0.320 | 0.82 |
| FX | spec | -0.060 | -0.075 | 0.108 | 0.152 | -0.016 | 0.567 | 0.81 |

Depth correlates about 0.8 with share and predicts no better.

**Pain crossed with crowding.**

| Signal | DESIGN slope | Holdout slope | Raw p | H-A | H-B | Contract-weeks, + / - | Crowded short: rise hit / base | Crowded long: fall hit / base |
|---|---|---|---|---|---|---|---|---|
| UST spec crowd pain | -0.023 | 0.201 | 0.071 | 0.39 | -0.02 | 138 / 83 | 49% / 40% | 79% / 60% |
| UST spec crowd only | -0.062 | 0.212 | 0.075 | 0.31 | 0.04 | 383 / 141 | 47% / 40% | 75% / 60% |
| UST lev crowd pain | 0.056 | 0.195 | 0.225 | 0.36 | -0.06 | 275 / 124 | 40% / 40% | 62% / 60% |
| UST lev crowd only | 0.061 | 0.291 | 0.080 | 0.43 | 0.07 | 570 / 170 | 46% / 40% | 65% / 60% |
| FX spec crowd pain | -0.008 | 0.008 | 0.791 | -0.06 | 0.05 | 76 / 66 | 48% / 48% | 42% / 51% |
| FX spec crowd only | -0.041 | 0.082 | 0.144 | -0.03 | 0.17 | 261 / 222 | 59% / 48% | 51% / 51% |
| FX lev crowd pain | 0.024 | -0.013 | 0.666 | -0.07 | 0.06 | 72 / 76 | 34% / 48% | 39% / 51% |
| FX lev crowd only | 0.023 | 0.010 | 0.865 | -0.08 | 0.10 | 151 / 161 | 42% / 48% | 48% / 51% |

Pain adds nothing to crowding. The Treasury result is almost all 2019-2022 and the sign is opposite to DESIGN. The event counts are contract-weeks on correlated contracts, so the real number of independent events is far smaller.

**Removal rule.**

| Panel, group | Corr pro rata, FIFO | Corr pro rata, low price | Corr FIFO, low price | Mean abs share gap, FIFO | Low price | Slope pro rata | FIFO | Low price | Insensitive by plan rule |
|---|---|---|---|---|---|---|---|---|---|
| UST lev | 0.97 | 0.96 | 0.92 | 0.09 | 0.14 | -0.122 | -0.115 | -0.096 | True |
| UST am | 0.97 | 0.96 | 0.93 | 0.09 | 0.14 | -0.143 | -0.144 | -0.139 | True |
| UST spec | 0.97 | 0.95 | 0.92 | 0.10 | 0.16 | -0.130 | -0.134 | -0.113 | True |
| FX lev | 0.96 | 0.94 | 0.89 | 0.12 | 0.20 | 0.076 | 0.065 | 0.049 | False |
| FX am | 0.97 | 0.95 | 0.92 | 0.10 | 0.16 | 0.089 | 0.086 | 0.084 | True |
| FX spec | 0.96 | 0.94 | 0.90 | 0.11 | 0.18 | 0.092 | 0.083 | 0.071 | False |

The answer does not depend on the rule. No slope changes sign and none becomes significant under any rule. Two FX rows fail the plan's strict test, because low price first differs from pro rata by more than one standard error there. All their slopes stay insignificant. One caution: share levels differ by 0.09 to 0.20 between rules. So fixed thresholds such as 70% and 30% do depend on an assumption nobody can observe.

**Window length.**

| Panel, group | DESIGN choice | 30: t DESIGN / holdout | 63 | 90 | 126 | 252 |
|---|---|---|---|---|---|---|
| UST lev | 252 | -0.84 / -0.87 | -1.08 / -1.02 | -1.25 / -0.89 | -1.37 / -0.82 | -1.50 / -1.21 |
| UST am | 252 | -0.55 / -1.15 | -0.39 / -1.22 | -0.41 / -1.01 | -0.58 / -0.92 | -0.77 / -1.15 |
| UST spec | 63 | -0.77 / -1.11 | -1.17 / -1.05 | -1.12 / -0.98 | -1.12 / -0.89 | -1.11 / -1.02 |
| FX lev | 63 | -0.86 / 0.78 | -0.98 / 1.18 | -0.96 / 1.25 | -0.89 / 1.34 | -0.91 / 1.59 |
| FX am | 30 | -1.50 / 0.96 | -1.27 / 1.31 | -1.06 / 1.28 | -0.89 / 1.39 | -1.16 / 1.76 |
| FX spec | 63 | -0.94 / 0.67 | -1.06 / 1.20 | -1.05 / 1.26 | -0.93 / 1.59 | -0.94 / 1.52 |

No window earns a place. DESIGN's picks rest on t-values under 2 and do not pass in the holdout.

### T8. Indicators head to head

| Panel | Signal | DESIGN slope 13w | 4w | 8w | 13w | 26w | Raw p 13w | Rot. p | Holm | H-A 13w | H-B 13w |
|---|---|---|---|---|---|---|---|---|---|---|---|
| UST | I1 | -0.003 | -0.10 (t -1.38) | -0.18 (t -1.44) | -0.26 (t -1.42) | -0.46 (t -1.30) | 0.177 | 0.361 | 1.00 | -0.32 | -0.01 |
| UST | I2 | 0.007 | -0.11 (t -2.02) | -0.21 (t -2.29) | -0.30 (t -2.29) | -0.49 (t -1.82) | 0.030 | 0.122 | 1.00 | -0.37 | -0.11 |
| UST | I3_lev | -0.045 | -0.22 (t -2.37) | -0.34 (t -2.07) | -0.48 (t -2.11) | -0.79 (t -2.59) | 0.044 | 0.003 | 1.00 | -0.72 | -0.13 |
| UST | I3_am | 0.017 | 0.16 (t 1.90) | 0.26 (t 1.82) | 0.40 (t 1.92) | 0.72 (t 2.30) | 0.065 | 0.088 | 1.00 | 0.60 | 0.10 |
| UST | I4 | 0.008 | -0.13 (t -2.29) | -0.22 (t -2.14) | -0.32 (t -2.02) | -0.53 (t -1.75) | 0.053 | 0.054 | 1.00 | -0.40 | -0.07 |
| FX | I1 | -0.011 | -0.09 (t -2.08) | -0.09 (t -1.68) | -0.09 (t -1.35) | -0.05 (t -0.58) | 0.200 | 0.225 | 1.00 | 0.02 | -0.21 |
| FX | I2 | 0.010 | -0.08 (t -1.96) | -0.10 (t -1.87) | -0.11 (t -1.67) | -0.08 (t -1.03) | 0.118 | 0.205 | 1.00 | 0.03 | -0.23 |
| FX | I3_lev | -0.033 | -0.06 (t -1.74) | -0.06 (t -1.34) | -0.06 (t -0.92) | -0.02 (t -0.25) | 0.370 | 0.544 | 1.00 | 0.02 | -0.16 |
| FX | I3_am | -0.042 | -0.06 (t -1.13) | -0.07 (t -1.01) | -0.09 (t -1.04) | -0.04 (t -0.38) | 0.310 | 0.259 | 1.00 | 0.05 | -0.27 |
| FX | I4 | -0.002 | -0.08 (t -1.80) | -0.09 (t -1.64) | -0.10 (t -1.45) | -0.06 (t -0.65) | 0.185 | 0.239 | 1.00 | 0.03 | -0.23 |

All rows use one common sample. Before 2019 every Treasury slope is near zero. In the holdout, high speculative or leveraged positioning preceded price falls, and high asset-manager positioning preceded rises. These are not independent results. Within contracts in the holdout, I3 leveraged and I3 asset managers correlate -0.91, and I2 and I4 correlate 0.84. The 2019-2022 half drives them all. I2 extremes on Treasuries: crowded-long weeks fell 75% of the time against a 60% base, in the holdout. In DESIGN the same call hit 45% against 50%.

Aggregate I4 on the 10-year at 4 weeks: corr 0.16, raw p 0.15. It said buy in 366 of 386 holdout weeks, with a hit rate of 42% against a 43% base. The median z-score was -0.98 before May 2019 and -2.09 after, even on an expanding base, so the non-commercial position sits far below its old range and the level rule stays pinned. I did not test the cause. The leveraged-fund basis trade is one candidate. Level rules like this one are not stationary.

I4 exactly as the spec now states it (TY, combined report, frozen 2007-2018 scale), on the holdout at 4 weeks: corr -0.06, raw p 0.44, buy in 282 of 386 weeks at 43% against a 43% base, sell in 18 weeks. My panel I4 uses the futures-only report and a past-only scale, as the plan fixed before the spec changed.

### T9. Does the filter generalise to FX?

| Group (am includes other reportables) | GS-OOS slope | Holdout slope | DK t | Raw p | Rot. p | H-A | H-B | Slope given past return | p | Buy: hit / base | Sell: hit / base |
|---|---|---|---|---|---|---|---|---|---|---|---|
| am | -0.019 | 0.103 | 0.86 | 0.409 | 0.535 | 0.37 | -0.13 | 0.113 | 0.250 | 50% / 49% | 53% / 51% |
| lev | 0.034 | 0.107 | 1.20 | 0.256 | 0.438 | 0.11 | 0.22 | 0.153 | 0.122 | 54% / 49% | 53% / 51% |
| spec | 0.052 | 0.096 | 1.32 | 0.213 | 0.374 | 0.18 | 0.08 | 0.103 | 0.324 | 49% / 49% | 51% / 51% |

The signs are right but the size is small and not significant. Fit on 2006-2010, tested later. Single currencies disagree: for asset managers the correlation runs from -0.29 to 0.29. So the idea does not carry over as a usable signal. This uses spot only, so carry is missing. H.10 noon rates also do not line up with the Tuesday close position snapshot.

### T10. Options position, combined minus futures-only

| Panel | Group | DESIGN flow slope 4w | Holdout | DK t | Raw p | Flow 13w | p | Level z 4w | p | Flow given futures position | p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| UST | am | -0.025 | 0.019 | 0.48 | 0.631 | 0.007 | 0.844 | 0.062 | 0.098 | 0.024 | 0.570 |
| UST | lev | 0.042 | -0.020 | -0.34 | 0.732 | -0.014 | 0.747 | -0.101 | 0.051 | -0.023 | 0.697 |
| UST | spec | 0.063 | -0.003 | -0.06 | 0.956 | 0.016 | 0.828 | -0.073 | 0.133 | -0.006 | 0.900 |
| FX | am | 0.025 | 0.015 | 0.65 | 0.516 | -0.005 | 0.886 | 0.026 | 0.300 | 0.013 | 0.576 |
| FX | lev | 0.001 | 0.016 | 0.52 | 0.619 | -0.050 | 0.333 | -0.041 | 0.254 | 0.010 | 0.747 |
| FX | spec | 0.043 | -0.051 | -1.50 | 0.139 | -0.112 | 0.024 | -0.062 | 0.096 | -0.052 | 0.128 |

No predictive information. FX specs at 13w has raw p 0.024, but the sign is opposite to DESIGN, and it does not survive Holm. This does not test Goldman's OPI, which uses strike-level option data. It says only that the free stand-in does not work.

### T11. Composite and backtests

Composite A, the pre-registered one, is **empty**. No candidate reached |t| of 2 in DESIGN under honest errors. The strongest was I5 asset managers at t = -1.58. So T11.1 and T11.2 count as p = 1. Composite C is an amendment: the three I5 groups in Goldman's direction, with no selection. Composite B is hindsight, using only holdout survivors. Its member is ['I3_lev'], so it duplicates that single signal.

**Rates sleeve, 10-year point, net of 5 bps of notional per side, carry excluded.**

| Strategy | OOS Sharpe | t-stat | Max drawdown | IR vs benchmark | Sharpe 95% interval | p | H-A | H-B | GS-OOS |
|---|---|---|---|---|---|---|---|---|---|
| Composite C (no selection) | 0.23 | 0.63 | -12% | 0.34 | [-0.55, 0.97] | 0.555 | 0.43 | 0.03 | 0.19 |
| Benchmark rule | -0.27 | -0.73 | -47% | n/a | [-1.10, 0.73] | 0.604 | -0.95 | 0.66 | -0.49 |
| Buy and hold 10-year | -0.35 | -0.97 | -63% | -0.09 | [-1.13, 0.41] | 0.372 | -0.22 | -0.53 | 0.05 |
| I5_am_TYUS | -0.54 | -1.48 | -50% | -0.27 | [-1.16, 0.16] | 0.124 | -1.00 | 0.01 | 0.42 |
| I5_lev | 0.17 | 0.46 | -35% | 0.27 | [-0.77, 1.04] | 0.743 | 0.70 | -0.53 | -0.02 |
| I5_spec | 0.76 | 2.07 | -13% | 0.61 | [-0.03, 1.44] | 0.059 | 0.87 | 0.63 | -0.04 |
| I1 | 0.17 | 0.45 | -39% | 0.28 | [-0.71, 1.02] | 0.716 | -0.18 | 0.52 | -0.56 |
| I2 | 0.32 | 0.88 | -26% | 0.37 | [-0.65, 1.21] | 0.540 | 0.26 | 0.41 | -0.21 |
| I3_lev | 0.27 | 0.74 | -26% | 0.34 | [-0.45, 0.90] | 0.447 | 1.01 | -0.52 | 0.20 |
| I3_am | 0.00 | 0.01 | -34% | 0.21 | [-0.67, 0.64] | 0.996 | 0.63 | -0.54 | 0.30 |
| I4 | 0.09 | 0.24 | -41% | 0.24 | [-0.84, 1.03] | 0.876 | -0.28 | 0.49 | -0.36 |
| P2_lev | 0.30 | 0.81 | -18% | 0.33 | [-0.54, 0.97] | 0.456 | 0.50 | 0.06 | -0.46 |
| P2_am | 0.40 | 1.09 | -13% | 0.38 | [-0.22, 0.91] | 0.197 | 0.73 | -0.04 | -0.69 |
| P2_spec | 0.48 | 1.33 | -17% | 0.44 | [-0.26, 1.14] | 0.196 | 0.52 | 0.44 | -0.22 |
| OPT_am | -0.52 | -1.43 | -57% | -0.13 | [-1.41, 0.39] | 0.288 | -0.55 | -0.51 | -0.08 |
| OPT_lev | -0.64 | -1.76 | -65% | -0.24 | [-1.48, 0.22] | 0.146 | -0.43 | -1.01 | -0.28 |
| OPT_spec | -0.64 | -1.76 | -53% | -0.22 | [-1.40, 0.24] | 0.146 | -0.52 | -0.88 | -0.34 |

**FX sleeve, seven currencies at equal risk, same cost, carry excluded.**

| Strategy | OOS Sharpe | t-stat | Max drawdown | IR vs benchmark | Sharpe 95% interval | p | H-A | H-B | GS-OOS |
|---|---|---|---|---|---|---|---|---|---|
| Benchmark rule | 0.35 | 0.94 | -22% | n/a | [-0.36, 1.08] | 0.324 | -0.29 | 1.14 | -0.28 |
| Buy and hold | -0.26 | -0.72 | -31% | -0.54 | [-0.86, 0.33] | 0.396 | -0.42 | -0.08 | -0.52 |
| I1 | -0.35 | -0.96 | -15% | -0.39 | [-0.97, 0.25] | 0.229 | -0.03 | -0.74 | -0.01 |
| I2 | -0.68 | -1.85 | -21% | -0.53 | [-1.21, -0.13] | 0.019 | -0.21 | -1.17 | -0.13 |
| I3_lev | 0.11 | 0.30 | -4% | -0.33 | [-0.33, 0.56] | 0.641 | 0.15 | 0.07 | -0.02 |
| I3_am | 0.37 | 1.00 | -10% | -0.14 | [-0.31, 1.08] | 0.290 | -0.13 | 0.98 | 0.04 |
| I4 | -0.50 | -1.38 | -15% | -0.45 | [-1.11, 0.06] | 0.083 | -0.12 | -0.92 | -0.10 |
| P2_lev | -0.51 | -1.38 | -20% | -0.48 | [-1.20, 0.04] | 0.073 | -0.45 | -0.59 | -0.82 |
| P2_am | -0.33 | -0.92 | -13% | -0.39 | [-0.95, 0.19] | 0.212 | -0.16 | -0.54 | -0.63 |
| P2_spec | -0.51 | -1.40 | -19% | -0.48 | [-1.16, -0.02] | 0.043 | -0.47 | -0.57 | -0.53 |
| OPT_am | -0.37 | -1.02 | -10% | -0.49 | [-1.09, 0.12] | 0.163 | -0.41 | -0.34 | -0.50 |
| OPT_lev | -0.30 | -0.81 | -10% | -0.44 | [-0.87, 0.16] | 0.212 | -0.15 | -0.49 | -0.11 |
| OPT_spec | -0.66 | -1.80 | -18% | -0.60 | [-1.28, -0.03] | 0.040 | -0.61 | -0.76 | 0.10 |
| I5FX_am | 0.25 | 0.69 | -12% | -0.13 | [-0.42, 0.96] | 0.422 | -0.24 | 1.11 | 0.43 |
| I5FX_lev | 0.21 | 0.57 | -21% | -0.35 | [-0.57, 0.94] | 0.587 | -0.20 | 0.80 | -0.69 |
| I5FX_spec | -0.31 | -0.84 | -21% | -0.88 | [-1.01, 0.39] | 0.379 | -0.27 | -0.46 | -0.64 |

Sizing is 10% annual risk on a trailing 52-week SD, so the drawdowns are large by construction. Signs for the single signals come from DESIGN, which is why some reverse. I5 specs has the best single result: net Sharpe 0.76, t 2.07, interval [-0.03, 1.44], positive in both halves (0.87, 0.63), and it survives 10 bps (0.64). But its GS-OOS Sharpe is -0.04, it is one of many strategies tried, and it fails Holm at 1.00. That makes it a flag, not a finding. Composite C at 0, 1, 5 and 10 bps: 0.35, 0.32, 0.23, 0.11. Its gap to the benchmark is 0.50, p 0.49.

**Canonical metrics.**

| Strategy | OOS Sharpe | t-stat | Max drawdown | IR vs benchmark |
|---|---|---|---|---|
| I5_am_TYUS | -0.54 | -1.48 | -50% | -0.27 |
| I5_lev | 0.17 | 0.46 | -35% | 0.27 |
| I5_spec | 0.76 | 2.07 | -13% | 0.61 |
| benchmark_rates | -0.27 | -0.73 | -47% | n/a |
| buy_hold_rates | -0.35 | -0.97 | -63% | -0.09 |

### T12. Filter placebo (added test)

Why this test: the filter keeps a flow only when it moves with yields. So the kept flows must line up with yields, whatever the flows are. To measure that, I shifted each group's weekly flows by every offset from 52 to T-52 weeks, keeping yields and DV01 fixed, and reran the whole recipe. At zero shift this path matches posmon exactly.

| Signal | Real slope, bp per $10mm | Placebo mean (5% to 95%) | Real 6m corr with yields | Placebo | Real next-6m corr, GS-OOS | Placebo | One-sided p | Real next-6m corr, holdout | Placebo | Placebo 5% to 95% | Two-sided p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Asset managers + others, TY and US | -17.2 | -18.3 (-23.5 to -12.4) | -0.62 | -0.47 | -0.27 | -0.12 | 0.136 | 0.04 | 0.03 | -0.28 to 0.31 | 0.961 |
| Leveraged funds, all six | -18.3 | -15.3 (-21.6 to -10.2) | -0.49 | -0.51 | -0.05 | -0.11 | 0.676 | -0.31 | -0.03 | -0.39 to 0.26 | 0.223 |
| Non-commercial specs, all six | -18.1 | -15.5 (-20.9 to -11.7) | -0.64 | -0.56 | -0.11 | -0.12 | 0.528 | -0.22 | -0.02 | -0.36 to 0.22 | 0.293 |

This is a clear result. Goldman's headline 17 to 18 bp per $10mm is what random flows produce. So is most of the 62% six-month fit. Real flows beat random flows in neither GS-OOS nor the holdout at conventional levels. Placebo scores still forecast at about -0.12 in GS-OOS, because the benchmark sits inside them. Each placebo row is 960 shifts, which are heavily overlapping, so these p-values are coarse.

### T13. Filter against no filter

| Signal | GS-OOS filter | GS-OOS no filter | Holdout filter | Holdout no filter | Difference | 95% interval | p | Unfiltered slope, bp per $10mm |
|---|---|---|---|---|---|---|---|---|
| Asset managers + others, TY and US | -0.27 | -0.15 | 0.04 | 0.16 | -0.12 | [-0.38, 0.29] | 0.577 | 2.9 |
| Leveraged funds, all six | -0.05 | -0.07 | -0.31 | -0.01 | -0.30 | [-0.67, 0.17] | 0.237 | -9.7 |
| Non-commercial specs, all six | -0.11 | -0.11 | -0.22 | 0.09 | -0.31 | [-0.72, 0.29] | 0.356 | -8.4 |

In the holdout the filter's sign is favourable, but the gain is not significant. In GS-OOS it adds little outside asset managers.

### T14. Benchmark bias (added test)

Does the -35% come from small-sample bias? Mostly not. A resampled yield path with no real mean reversion gives a mean of -0.05 and SD 0.16 over 2006 to April 2019. It reaches the observed -0.35 only 2.5% of the time (3.0% with 4-week blocks). So the bias is small and the in-sample figure was unusual. It did not persist: holdout 0.03.

## 5. Sample size: where we cannot conclude

| Horizon | Independent observations in the holdout | Smallest |corr| significant at 5% raw | Smallest |corr| at Holm's first step |
|---|---|---|---|
| 26w | 14 | 0.53 | 0.78 |
| 13w | 28 | 0.37 | 0.59 |
| 8w | 46 | 0.29 | 0.48 |
| 4w | 91 | 0.21 | 0.34 |

- Primary family: 53 tests. All tests: 266.
- Power to detect a true -43% at 26 weeks: 33% raw, 4% after Holm. Power to detect a true 0.2 at 13 weeks: 17% raw.
- The holdout has one large rate cycle. The rally in 2019-2020 and the sell-off in 2021-2023 dominate it. Treat long-horizon results as closer to one or two episodes than to 14 draws.
- We can say with fair confidence: asset-manager I5 is not a usable signal, and its published size is unlikely, though the widest interval does not rule it out. Deck-rule pain share has no edge over the base rate. The options stand-in shows nothing.
- We cannot conclude: leveraged-fund and spec I5, I2 and I3 on Treasuries, and I5 on FX. These have small or modest effects in the sample. None is ruled out as a modest real effect.

**Size check.** Rotating the signal inside the holdout, the pre-registered p-value rejected at the 5% level 19% of the time at 26 weeks and 10% at 13 weeks. Newey-West with normal critical values reached 25%. On the panel P2 test the figure was 5%. These rates are noisy, since the rotations overlap. So raw p-values near 0.05 at long horizons overstate the evidence. It strengthens the "no", because nothing passed Holm even with p-values that run too small. That is why rotation p-values appear beside them. Their smallest Holm-adjusted value is 0.12.

## 6. Method, data and deviations

- Boundaries: fit 2006-06-13 to 2010-12-31, design to 2019-04-30 (673 weeks), holdout from 2019-05-07 (391 weeks). Seed 42. 5000 bootstrap draws.
- Data: all downloads succeeded (`raw/manifest.json`). No substitution happened. Yahoo prices are used only in T6b.
- Leak test: every raw input was cut at three dates and each signal rebuilt. Result: passed, across 134562 cells, largest gap 0.0.
- Ledger check: the weekly path matches `posmon.pain.cftc_pain` on 130 dates, apart from the residue cases.
- The agent protocol names `/experiments/LOG.md` and skill folders that do not exist on this machine, and writing outside this folder was barred. So there is no log entry there. No `find` registry step ran, because the registry folders are absent.
- Amendments are in `plan.md`, section 11. The main ones: the empty-ledger guard after the first run, rotation p-values after the size check, and Composite C after Composite A came back empty.

**Bias and leakage checklist.**

- No look-ahead: confirmed by the leak test. Tradable returns start at E.
- Survivorship: the universe is fixed by rule. TN and WN enter when listed. TFF history before September 2009 is CFTC backfill, which touches the fit window only.
- Costs: 5 bps of notional per side, higher than real Treasury futures costs. Sensitivity is reported.
- Universe: all six Treasury contracts and all seven G10 FX contracts on the config list.
- Stationarity: flows and forward moves are changes. Levels are bounded or z-scored on past data. T8 shows levels still drift, which is a finding.
- Holdout above design: 19 primary tests carry this flag, marked in the appendix. Most are small effects where DESIGN was near zero. Each should be read with suspicion, including I3 leveraged, I5 leveraged and I5 specs.

## 7. What could be wrong here

1. **Carry is missing.** Forward moves are yield or spot only. Carry and roll-down would change Sharpe ratios, mostly for FX and long-duration holds. It should not change the T1 regressions by much, since they measure yield changes.
2. **DV01 before 2013** is a rebuild scaled to later OFR data. It affects the fit window only and reproduced Goldman's figures.
3. **Release dates are assumed** in history, except in the late-release test. The effect was small.
4. **Holm is strict across 53 tests.** A real modest effect would fail it. That is why levels 2 and 3 exist, and why I report the watch list instead of a flat no.
5. **Goldman's OPI itself** was not tested. There is no option data.

## Appendix A. Every primary test

| ID | Test | Raw p | Holm (primary) | Holm (all) | Rot. p | Stat, holdout | Stat, design | N_eff | Sign OK | Holdout > design | Success | Note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T1.1 | I5 am_TYUS, 26w, Monday entry, slope of forward DGS10 on score | 0.801 | 1.00 | 1.00 | 0.869 | 0.040 | -0.265 | 14 | False |  | no |  |
| T1.2 | I5 am_all6, 26w, Monday entry, slope of forward DGS10 on score | 0.995 | 1.00 | 1.00 | 0.987 | -0.007 | -0.326 | 14 | True |  | no |  |
| T1.3 | I5 lev, 26w, Monday entry, slope of forward DGS10 on score | 0.117 | 1.00 | 1.00 | 0.208 | -0.306 | -0.053 | 14 | True | yes | no |  |
| T1.4 | I5 spec, 26w, Monday entry, slope of forward DGS10 on score | 0.225 | 1.00 | 1.00 | 0.198 | -0.224 | -0.114 | 14 | True | yes | no |  |
| T1.5 | Benchmark: past 26w change, 26w, Monday entry | 0.625 | 1.00 | 1.00 | 0.658 | 0.140 | -0.153 | 14 | False |  | no |  |
| T2.1 | Lag cost am_TYUS 26w: corr(Tuesday) minus corr(Monday) | 0.391 | 1.00 | 1.00 | n/a | 0.010 | n/a | 14 | True |  | no | not costly |
| T5.1 | I5 am_TYUS at 4w | 0.401 | 1.00 | 1.00 | 0.372 | 0.085 | -0.089 | 96 | False |  | no |  |
| T5.2 | I5 am_TYUS at 8w | 0.503 | 1.00 | 1.00 | 0.526 | 0.076 | -0.131 | 48 | False |  | no |  |
| T5.3 | I5 am_TYUS at 13w | 0.502 | 1.00 | 1.00 | 0.653 | 0.077 | -0.179 | 29 | False |  | no |  |
| T3.1 | I5 am_TYUS adds to benchmark, 26w | 0.644 | 1.00 | 1.00 | 0.684 | -6.905 | -27.093 | 14 | True |  | no | oos_r2_incremental=-0.051 |
| T3.2 | I5 lev adds to benchmark, 26w | 0.102 | 1.00 | 1.00 | 0.198 | -10.442 | -0.269 | 14 | True | yes | no | oos_r2_incremental=-0.048 |
| T3.3 | I5 spec adds to benchmark, 26w | 0.300 | 1.00 | 1.00 | 0.240 | -12.153 | -4.791 | 14 | True | yes | no | oos_r2_incremental=-0.012 |
| T4.1 | expanding_beta_expanding_scale minus fixed, am_TYUS, 26w, corr difference | 0.346 | 1.00 | 1.00 | n/a | 0.048 | n/a | 14 | False |  | no |  |
| T4.2 | rolling_beta_rolling_scale minus fixed, am_TYUS, 26w, corr difference | 0.143 | 1.00 | 1.00 | n/a | 0.139 | n/a | 14 | False |  | no |  |
| T6.1 | P2 net share, lev, UST, 13w | 0.455 | 1.00 | 1.00 | 0.470 | -0.122 | -0.101 | 29 | True | yes | no |  |
| T6.7 | P2 lev given past return, UST, 13w | 0.673 | 1.00 | 1.00 | 0.858 | 0.035 | -0.109 | 29 | False |  | no |  |
| T6.2 | P2 net share, am, UST, 13w | 0.379 | 1.00 | 1.00 | 0.350 | -0.143 | -0.045 | 29 | True | yes | no |  |
| T6.3 | P2 net share, spec, UST, 13w | 0.413 | 1.00 | 1.00 | 0.369 | -0.130 | -0.081 | 29 | True | yes | no |  |
| T6.4 | P2 net share, lev, FX, 13w | 0.192 | 1.00 | 1.00 | 0.134 | 0.076 | -0.062 | 29 | False |  | no |  |
| T6.8 | P2 lev given past return, FX, 13w | 0.439 | 1.00 | 1.00 | 0.443 | 0.040 | -0.033 | 29 | False |  | no |  |
| T6.5 | P2 net share, am, FX, 13w | 0.175 | 1.00 | 1.00 | 0.178 | 0.089 | -0.061 | 29 | False |  | no |  |
| T6.6 | P2 net share, spec, FX, 13w | 0.125 | 1.00 | 1.00 | 0.126 | 0.092 | -0.060 | 29 | False |  | no |  |
| T7.1 | Depth minus share, lev, UST, 13w, signed by DESIGN | 0.879 | 1.00 | 1.00 | n/a | 0.017 | n/a | 29 | True |  | no |  |
| T7.2 | Depth minus share, lev, FX, 13w, signed by DESIGN | 0.829 | 1.00 | 1.00 | n/a | -0.005 | n/a | 29 | False |  | no |  |
| T7.3 | Crowded pain, spec, UST, 13w | 0.071 | 1.00 | 1.00 | 0.060 | 0.201 | -0.023 | 29 | False |  | no | events plus 138, minus 83 |
| T7.4 | Crowded pain, spec, FX, 13w | 0.791 | 1.00 | 1.00 | 0.877 | 0.008 | -0.008 | 29 | False |  | no | events plus 76, minus 66 |
| T7.5 | Design-chosen window (252), lev, UST, 13w | 0.256 | 1.00 | 1.00 | 0.251 | -0.193 | -0.113 | 29 | True | yes | no | window 252 |
| T7.6 | Design-chosen window (63), lev, FX, 13w | 0.248 | 1.00 | 1.00 | 0.169 | 0.058 | -0.064 | 29 | False |  | no | window 63 |
| T8.1 | I1, UST, 13w, common sample | 0.177 | 1.00 | 1.00 | 0.361 | -0.265 | -0.003 | 29 | True | yes | no |  |
| T8.2 | I2, UST, 13w, common sample | 0.030 | 1.00 | 1.00 | 0.122 | -0.304 | 0.007 | 29 | False |  | no |  |
| T8.3 | I3_lev, UST, 13w, common sample | 0.044 | 1.00 | 1.00 | 0.003 | -0.482 | -0.045 | 29 | True | yes | no |  |
| T8.4 | I3_am, UST, 13w, common sample | 0.065 | 1.00 | 1.00 | 0.088 | 0.400 | 0.017 | 29 | True | yes | no |  |
| T8.5 | I4, UST, 13w, common sample | 0.053 | 1.00 | 1.00 | 0.054 | -0.324 | 0.008 | 29 | False |  | no |  |
| T8.6 | I1, FX, 13w, common sample | 0.200 | 1.00 | 1.00 | 0.225 | -0.090 | -0.011 | 29 | True | yes | no |  |
| T8.7 | I2, FX, 13w, common sample | 0.118 | 1.00 | 1.00 | 0.205 | -0.107 | 0.010 | 29 | False |  | no |  |
| T8.8 | I3_lev, FX, 13w, common sample | 0.370 | 1.00 | 1.00 | 0.544 | -0.056 | -0.033 | 29 | True | yes | no |  |
| T8.9 | I3_am, FX, 13w, common sample | 0.310 | 1.00 | 1.00 | 0.259 | -0.095 | -0.042 | 29 | True | yes | no |  |
| T8.10 | I4, FX, 13w, common sample | 0.185 | 1.00 | 1.00 | 0.239 | -0.098 | -0.002 | 29 | True | yes | no |  |
| T9.1 | FX I5, am, 26w, fit FIT | 0.409 | 1.00 | 1.00 | 0.535 | 0.103 | -0.019 | 14 | True |  | no |  |
| T9.2 | FX I5, lev, 26w, fit FIT | 0.256 | 1.00 | 1.00 | 0.438 | 0.107 | 0.034 | 14 | True | yes | no |  |
| T9.3 | FX I5, spec, 26w, fit FIT | 0.213 | 1.00 | 1.00 | 0.374 | 0.096 | 0.052 | 14 | True | yes | no |  |
| T10.1 | Option flow, am, UST, 4w | 0.631 | 1.00 | 1.00 | 0.599 | 0.019 | -0.025 | 96 | False |  | no |  |
| T10.2 | Option flow, lev, UST, 4w | 0.732 | 1.00 | 1.00 | 0.708 | -0.020 | 0.042 | 96 | False |  | no |  |
| T10.3 | Option flow, spec, UST, 4w | 0.956 | 1.00 | 1.00 | 0.964 | -0.003 | 0.063 | 96 | False |  | no |  |
| T10.4 | Option flow, am, FX, 4w | 0.516 | 1.00 | 1.00 | 0.643 | 0.015 | 0.025 | 96 | True |  | no |  |
| T10.5 | Option flow, lev, FX, 4w | 0.619 | 1.00 | 1.00 | 0.703 | 0.016 | 0.001 | 96 | True | yes | no |  |
| T10.6 | Option flow, spec, FX, 4w | 0.139 | 1.00 | 1.00 | 0.216 | -0.051 | 0.043 | 96 | False |  | no |  |
| T12.1 | Filter placebo, am_TYUS: real flows vs shifted flows, 26w corr | 0.961 | 1.00 | 1.00 | n/a | 0.007 | -0.148 | n/a | False |  | no |  |
| T12.2 | Filter placebo, lev: real flows vs shifted flows, 26w corr | 0.223 | 1.00 | 1.00 | n/a | -0.274 | 0.054 | n/a | True |  | no |  |
| T12.3 | Filter placebo, spec: real flows vs shifted flows, 26w corr | 0.293 | 1.00 | 1.00 | n/a | -0.203 | 0.001 | n/a | True |  | no |  |
| T13.1 | Filter minus no filter, am_TYUS, 26w, corr difference | 0.577 | 1.00 | 1.00 | n/a | -0.118 | -0.115 | 14 | True | yes | no |  |
| T11.1 | Composite A net Sharpe | n/a | 1.00 | 1.00 | n/a | n/a | n/a | n/a | False |  | no |  |
| T11.2 | Composite A minus benchmark Sharpe | n/a | 1.00 | 1.00 | n/a | n/a | n/a | n/a | False |  | no |  |

Stat is a correlation, slope, correlation gap or Sharpe, according to the test. T2.1 is the only test where a low p-value would mean a cost rather than a benefit. T11.1 and T11.2 did not run because Composite A is empty, so they count as p = 1.

## Appendix B. Every secondary test

| ID | Test | Raw p | Holm (all) | Stat, holdout | Stat, design | Sign OK |
|---|---|---|---|---|---|---|
| T1.S.tue.am_TYUS | am_TYUS, 26w, Tuesday entry (look-ahead) | 0.744 | 1.00 | 0.049 | n/a | False |
| T1.S.tue.am_all6 | am_all6, 26w, Tuesday entry (look-ahead) | 0.998 | 1.00 | -0.003 | n/a | True |
| T1.S.tue.lev | lev, 26w, Tuesday entry (look-ahead) | 0.097 | 1.00 | -0.326 | n/a | True |
| T1.S.tue.spec | spec, 26w, Tuesday entry (look-ahead) | 0.181 | 1.00 | -0.246 | n/a | True |
| T1.S.tue.benchmark | benchmark, 26w, Tuesday entry (look-ahead) | 0.610 | 1.00 | 0.146 | n/a | False |
| T1.S.TYUS_vs_all6 | am_TYUS minus am_all6 corr | 0.881 | 1.00 | 0.047 | n/a | None |
| T1.S.am_TYUS_vs_bench | am_TYUS corr minus benchmark corr, 26w | 0.637 | 1.00 | -0.100 | n/a | True |
| T1.S.am_all6_vs_bench | am_all6 corr minus benchmark corr, 26w | 0.708 | 1.00 | -0.146 | n/a | True |
| T1.S.lev_vs_bench | lev corr minus benchmark corr, 26w | 0.203 | 1.00 | -0.445 | n/a | True |
| T1.S.spec_vs_bench | spec corr minus benchmark corr, 26w | 0.323 | 1.00 | -0.363 | n/a | True |
| T2.S.lag.am_TYUS.4 | Lag cost am_TYUS 4w: corr(Tuesday) minus corr(Monday) | 0.740 | 1.00 | 0.011 | n/a | True |
| T2.S.lag.am_TYUS.13 | Lag cost am_TYUS 13w: corr(Tuesday) minus corr(Monday) | 0.580 | 1.00 | 0.010 | n/a | True |
| T2.S.lag.am_all6.4 | Lag cost am_all6 4w: corr(Tuesday) minus corr(Monday) | 0.915 | 1.00 | -0.002 | n/a | True |
| T2.S.lag.am_all6.13 | Lag cost am_all6 13w: corr(Tuesday) minus corr(Monday) | 0.826 | 1.00 | 0.004 | n/a | True |
| T2.S.lag.am_all6.26 | Lag cost am_all6 26w: corr(Tuesday) minus corr(Monday) | 0.558 | 1.00 | 0.006 | n/a | True |
| T2.S.lag.lev.4 | Lag cost lev 4w: corr(Tuesday) minus corr(Monday) | 0.603 | 1.00 | -0.015 | n/a | True |
| T2.S.lag.lev.13 | Lag cost lev 13w: corr(Tuesday) minus corr(Monday) | 0.158 | 1.00 | -0.026 | n/a | True |
| T2.S.lag.lev.26 | Lag cost lev 26w: corr(Tuesday) minus corr(Monday) | 0.070 | 1.00 | -0.020 | n/a | True |
| T2.S.lag.spec.4 | Lag cost spec 4w: corr(Tuesday) minus corr(Monday) | 0.434 | 1.00 | -0.022 | n/a | True |
| T2.S.lag.spec.13 | Lag cost spec 13w: corr(Tuesday) minus corr(Monday) | 0.040 | 1.00 | -0.036 | n/a | True |
| T2.S.lag.spec.26 | Lag cost spec 26w: corr(Tuesday) minus corr(Monday) | 0.234 | 1.00 | -0.021 | n/a | True |
| T2.S.late.am_TYUS | am_TYUS, 26w, late-release weeks dropped | 0.909 | 1.00 | 0.032 | n/a | False |
| T2.S.late.am_all6 | am_all6, 26w, late-release weeks dropped | 0.842 | 1.00 | -0.028 | n/a | True |
| T2.S.late.lev | lev, 26w, late-release weeks dropped | 0.127 | 1.00 | -0.305 | n/a | True |
| T2.S.late.spec | spec, 26w, late-release weeks dropped | 0.236 | 1.00 | -0.222 | n/a | True |
| T2.S.late.benchmark | benchmark, 26w, late-release weeks dropped | 0.627 | 1.00 | 0.144 | n/a | False |
| T2.S.fresh.am_TYUS.4 | Fresh am_TYUS minus plain, 4w, corr difference | 0.779 | 1.00 | 0.004 | n/a | False |
| T2.S.fresh.am_TYUS.13 | Fresh am_TYUS minus plain, 13w, corr difference | 0.555 | 1.00 | -0.006 | n/a | True |
| T2.S.fresh.am_TYUS.26 | Fresh am_TYUS minus plain, 26w, corr difference | 0.522 | 1.00 | -0.005 | n/a | True |
| T2.S.fresh.lev.4 | Fresh lev minus plain, 4w, corr difference | 0.703 | 1.00 | 0.003 | n/a | False |
| T2.S.fresh.lev.13 | Fresh lev minus plain, 13w, corr difference | 0.511 | 1.00 | -0.004 | n/a | True |
| T2.S.fresh.lev.26 | Fresh lev minus plain, 26w, corr difference | 0.317 | 1.00 | -0.005 | n/a | True |
| T2.S.fresh.spec.4 | Fresh spec minus plain, 4w, corr difference | 0.662 | 1.00 | 0.006 | n/a | False |
| T2.S.fresh.spec.13 | Fresh spec minus plain, 13w, corr difference | 0.581 | 1.00 | -0.006 | n/a | True |
| T2.S.fresh.spec.26 | Fresh spec minus plain, 26w, corr difference | 0.436 | 1.00 | -0.005 | n/a | True |
| T5.S.am_all6.4 | am_all6 at 4w | 0.941 | 1.00 | -0.006 | -0.145 | True |
| T5.S.lev.4 | lev at 4w | 0.069 | 1.00 | -0.168 | 0.005 | True |
| T5.S.spec.4 | spec at 4w | 0.015 | 1.00 | -0.196 | -0.015 | True |
| T5.S.benchmark.4 | benchmark at 4w | 0.796 | 1.00 | 0.032 | 0.021 | False |
| T5.S.am_all6.8 | am_all6 at 8w | 0.978 | 1.00 | 0.005 | -0.208 | False |
| T5.S.lev.8 | lev at 8w | 0.075 | 1.00 | -0.197 | -0.029 | True |
| T5.S.spec.8 | spec at 8w | 0.076 | 1.00 | -0.195 | -0.080 | True |
| T5.S.benchmark.8 | benchmark at 8w | 0.911 | 1.00 | 0.021 | -0.000 | False |
| T5.S.am_all6.13 | am_all6 at 13w | 0.996 | 1.00 | 0.001 | -0.280 | False |
| T5.S.lev.13 | lev at 13w | 0.114 | 1.00 | -0.214 | -0.046 | True |
| T5.S.spec.13 | spec at 13w | 0.163 | 1.00 | -0.200 | -0.114 | True |
| T5.S.benchmark.13 | benchmark at 13w | 0.775 | 1.00 | 0.056 | -0.051 | False |
| T4.S.lev.expanding_beta_expanding_scale | expanding_beta_expanding_scale minus fixed, lev, 26w, corr difference | 0.769 | 1.00 | 0.040 | n/a | False |
| T4.S.lev.rolling_beta_rolling_scale | rolling_beta_rolling_scale minus fixed, lev, 26w, corr difference | 0.400 | 1.00 | 0.165 | n/a | False |
| T4.S.spec.expanding_beta_expanding_scale | expanding_beta_expanding_scale minus fixed, spec, 26w, corr difference | 0.460 | 1.00 | 0.147 | n/a | False |
| T4.S.spec.rolling_beta_rolling_scale | rolling_beta_rolling_scale minus fixed, spec, 26w, corr difference | 0.248 | 1.00 | 0.303 | n/a | False |
| T6.S.UST.lev.4 | P2 net share, lev, UST, 4w | 0.093 | 1.00 | -0.171 | -0.029 | True |
| T6.S.UST.lev.26 | P2 net share, lev, UST, 26w | 0.476 | 1.00 | -0.108 | -0.030 | True |
| T6.S.UST.am.4 | P2 net share, am, UST, 4w | 0.066 | 1.00 | -0.193 | -0.018 | True |
| T6.S.UST.am.26 | P2 net share, am, UST, 26w | 0.527 | 1.00 | -0.112 | 0.014 | False |
| T6.S.past.UST.am | P2 am given past return, UST, 13w | 0.570 | 1.00 | 0.047 | -0.039 | False |
| T6.S.UST.spec.4 | P2 net share, spec, UST, 4w | 0.054 | 1.00 | -0.175 | -0.026 | True |
| T6.S.UST.spec.26 | P2 net share, spec, UST, 26w | 0.313 | 1.00 | -0.187 | -0.004 | True |
| T6.S.past.UST.spec | P2 spec given past return, UST, 13w | 0.726 | 1.00 | 0.029 | -0.086 | False |
| T6.S.FX.lev.4 | P2 net share, lev, FX, 4w | 0.623 | 1.00 | 0.021 | -0.025 | False |
| T6.S.FX.lev.26 | P2 net share, lev, FX, 26w | 0.297 | 1.00 | 0.083 | -0.053 | False |
| T6.S.FX.am.4 | P2 net share, am, FX, 4w | 0.644 | 1.00 | 0.021 | -0.040 | False |
| T6.S.FX.am.26 | P2 net share, am, FX, 26w | 0.216 | 1.00 | 0.109 | -0.043 | False |
| T6.S.past.FX.am | P2 am given past return, FX, 13w | 0.256 | 1.00 | 0.057 | -0.044 | False |
| T6.S.FX.spec.4 | P2 net share, spec, FX, 4w | 0.809 | 1.00 | 0.010 | -0.037 | False |
| T6.S.FX.spec.26 | P2 net share, spec, FX, 26w | 0.250 | 1.00 | 0.095 | -0.049 | False |
| T6.S.past.FX.spec | P2 spec given past return, FX, 13w | 0.283 | 1.00 | 0.058 | -0.024 | False |
| T6b.S.1 | P2 lev on synthetic minus P2 lev on Yahoo, TU FV TY US, 13w | 0.347 | 1.00 | -0.013 | n/a | None |
| T7.S.depthslope.UST.lev | Depth slope, lev, UST, 13w | 0.478 | 1.00 | -0.139 | -0.152 | True |
| T7.S.depth.UST.am | Depth minus share, am, UST, 13w, signed by DESIGN | 0.360 | 1.00 | 0.062 | n/a | True |
| T7.S.depthslope.UST.am | Depth slope, am, UST, 13w | 0.308 | 1.00 | -0.204 | -0.076 | True |
| T7.S.depth.UST.spec | Depth minus share, spec, UST, 13w, signed by DESIGN | 0.863 | 1.00 | 0.017 | n/a | True |
| T7.S.depthslope.UST.spec | Depth slope, spec, UST, 13w | 0.444 | 1.00 | -0.147 | -0.124 | True |
| T7.S.depthslope.FX.lev | Depth slope, lev, FX, 13w | 0.307 | 1.00 | 0.081 | -0.086 | False |
| T7.S.depth.FX.am | Depth minus share, am, FX, 13w, signed by DESIGN | 0.320 | 1.00 | -0.029 | n/a | False |
| T7.S.depthslope.FX.am | Depth slope, am, FX, 13w | 0.111 | 1.00 | 0.119 | -0.005 | False |
| T7.S.depth.FX.spec | Depth minus share, spec, FX, 13w, signed by DESIGN | 0.567 | 1.00 | -0.016 | n/a | False |
| T7.S.depthslope.FX.spec | Depth slope, spec, FX, 13w | 0.152 | 1.00 | 0.108 | -0.075 | False |
| T7.S.crowd_only.UST.spec | crowd_only, spec, UST, 13w | 0.075 | 1.00 | 0.212 | -0.062 | False |
| T7.S.crowd_pain.UST.lev | crowd_pain, lev, UST, 13w | 0.225 | 1.00 | 0.195 | 0.056 | True |
| T7.S.crowd_only.UST.lev | crowd_only, lev, UST, 13w | 0.080 | 1.00 | 0.291 | 0.061 | True |
| T7.S.crowd_only.FX.spec | crowd_only, spec, FX, 13w | 0.144 | 1.00 | 0.082 | -0.041 | False |
| T7.S.crowd_pain.FX.lev | crowd_pain, lev, FX, 13w | 0.666 | 1.00 | -0.013 | 0.024 | False |
| T7.S.crowd_only.FX.lev | crowd_only, lev, FX, 13w | 0.865 | 1.00 | 0.010 | 0.023 | True |
| T7.S.window.UST.am | Design-chosen window (252), am, UST, 13w | 0.288 | 1.00 | -0.198 | -0.060 | True |
| T7.S.window.UST.spec | Design-chosen window (63), spec, UST, 13w | 0.303 | 1.00 | -0.137 | -0.077 | True |
| T7.S.window.FX.am | Design-chosen window (30), am, FX, 13w | 0.348 | 1.00 | 0.052 | -0.083 | False |
| T7.S.window.FX.spec | Design-chosen window (63), spec, FX, 13w | 0.242 | 1.00 | 0.061 | -0.063 | False |
| T7.S.rule.UST.lev.fifo | pro_rata minus fifo slope, lev, UST, 13w | 0.811 | 1.00 | -0.007 | n/a | None |
| T7.S.rule.UST.lev.low_price_first | pro_rata minus low_price_first slope, lev, UST, 13w | 0.551 | 1.00 | -0.025 | n/a | None |
| T7.S.rule.UST.am.fifo | pro_rata minus fifo slope, am, UST, 13w | 0.879 | 1.00 | 0.002 | n/a | None |
| T7.S.rule.UST.am.low_price_first | pro_rata minus low_price_first slope, am, UST, 13w | 0.897 | 1.00 | -0.004 | n/a | None |
| T7.S.rule.UST.spec.fifo | pro_rata minus fifo slope, spec, UST, 13w | 0.749 | 1.00 | 0.004 | n/a | None |
| T7.S.rule.UST.spec.low_price_first | pro_rata minus low_price_first slope, spec, UST, 13w | 0.428 | 1.00 | -0.017 | n/a | None |
| T7.S.rule.FX.lev.fifo | pro_rata minus fifo slope, lev, FX, 13w | 0.588 | 1.00 | 0.011 | n/a | None |
| T7.S.rule.FX.lev.low_price_first | pro_rata minus low_price_first slope, lev, FX, 13w | 0.012 | 1.00 | 0.027 | n/a | None |
| T7.S.rule.FX.am.fifo | pro_rata minus fifo slope, am, FX, 13w | 0.813 | 1.00 | 0.003 | n/a | None |
| T7.S.rule.FX.am.low_price_first | pro_rata minus low_price_first slope, am, FX, 13w | 0.740 | 1.00 | 0.005 | n/a | None |
| T7.S.rule.FX.spec.fifo | pro_rata minus fifo slope, spec, FX, 13w | 0.627 | 1.00 | 0.010 | n/a | None |
| T7.S.rule.FX.spec.low_price_first | pro_rata minus low_price_first slope, spec, FX, 13w | 0.117 | 1.00 | 0.021 | n/a | None |
| T8.S.UST.I1.4 | I1, UST, 4w, common sample | 0.180 | 1.00 | -0.096 | -0.011 | True |
| T8.S.UST.I2.4 | I2, UST, 4w, common sample | 0.046 | 1.00 | -0.113 | -0.004 | True |
| T8.S.UST.I3_lev.4 | I3_lev, UST, 4w, common sample | 0.020 | 1.00 | -0.222 | -0.021 | True |
| T8.S.UST.I3_am.4 | I3_am, UST, 4w, common sample | 0.061 | 1.00 | 0.162 | 0.005 | True |
| T8.S.UST.I4.4 | I4, UST, 4w, common sample | 0.024 | 1.00 | -0.130 | 0.001 | False |
| T8.S.UST.I1.8 | I1, UST, 8w, common sample | 0.178 | 1.00 | -0.177 | -0.006 | True |
| T8.S.UST.I2.8 | I2, UST, 8w, common sample | 0.027 | 1.00 | -0.208 | 0.008 | False |
| T8.S.UST.I3_lev.8 | I3_lev, UST, 8w, common sample | 0.044 | 1.00 | -0.336 | -0.036 | True |
| T8.S.UST.I3_am.8 | I3_am, UST, 8w, common sample | 0.075 | 1.00 | 0.261 | 0.010 | True |
| T8.S.UST.I4.8 | I4, UST, 8w, common sample | 0.038 | 1.00 | -0.223 | 0.009 | False |
| T8.S.UST.I1.26 | I1, UST, 26w, common sample | 0.229 | 1.00 | -0.461 | 0.014 | False |
| T8.S.UST.I2.26 | I2, UST, 26w, common sample | 0.094 | 1.00 | -0.495 | -0.030 | True |
| T8.S.UST.I3_lev.26 | I3_lev, UST, 26w, common sample | 0.024 | 1.00 | -0.788 | 0.003 | False |
| T8.S.UST.I3_am.26 | I3_am, UST, 26w, common sample | 0.040 | 1.00 | 0.720 | -0.037 | False |
| T8.S.UST.I4.26 | I4, UST, 26w, common sample | 0.106 | 1.00 | -0.525 | 0.010 | False |
| T8.S.FX.I1.4 | I1, FX, 4w, common sample | 0.040 | 1.00 | -0.085 | -0.008 | True |
| T8.S.FX.I2.4 | I2, FX, 4w, common sample | 0.053 | 1.00 | -0.084 | 0.008 | False |
| T8.S.FX.I3_lev.4 | I3_lev, FX, 4w, common sample | 0.089 | 1.00 | -0.064 | -0.013 | True |
| T8.S.FX.I3_am.4 | I3_am, FX, 4w, common sample | 0.260 | 1.00 | -0.056 | -0.006 | True |
| T8.S.FX.I4.4 | I4, FX, 4w, common sample | 0.079 | 1.00 | -0.075 | 0.003 | False |
| T8.S.FX.I1.8 | I1, FX, 8w, common sample | 0.112 | 1.00 | -0.092 | -0.005 | True |
| T8.S.FX.I2.8 | I2, FX, 8w, common sample | 0.073 | 1.00 | -0.099 | 0.016 | False |
| T8.S.FX.I3_lev.8 | I3_lev, FX, 8w, common sample | 0.200 | 1.00 | -0.060 | -0.023 | True |
| T8.S.FX.I3_am.8 | I3_am, FX, 8w, common sample | 0.317 | 1.00 | -0.072 | -0.016 | True |
| T8.S.FX.I4.8 | I4, FX, 8w, common sample | 0.132 | 1.00 | -0.089 | 0.006 | False |
| T8.S.FX.I1.26 | I1, FX, 26w, common sample | 0.588 | 1.00 | -0.045 | -0.017 | True |
| T8.S.FX.I2.26 | I2, FX, 26w, common sample | 0.333 | 1.00 | -0.084 | 0.014 | False |
| T8.S.FX.I3_lev.26 | I3_lev, FX, 26w, common sample | 0.822 | 1.00 | -0.020 | -0.047 | True |
| T8.S.FX.I3_am.26 | I3_am, FX, 26w, common sample | 0.712 | 1.00 | -0.040 | -0.060 | True |
| T8.S.FX.I4.26 | I4, FX, 26w, common sample | 0.573 | 1.00 | -0.056 | -0.010 | True |
| T8.S.specI4 | I4 as now in the spec (TY, combined, frozen 2007-2018 scale), 4w | 0.444 | 1.00 | -0.056 | 0.091 | None |
| T8.S.aggI4 | Aggregate I4 z-score on 10-year, 4w | 0.150 | 1.00 | 0.161 | 0.013 | None |
| T9.S.am.13 | FX I5, am, 13w | 0.996 | 1.00 | -0.000 | -0.013 | False |
| T9.S.past.am | FX I5 am given past return, 26w | 0.250 | 1.00 | 0.113 | -0.008 | True |
| T9.S.ccy.am.EC | FX I5 am, EC alone, 26w | 0.606 | 1.00 | 0.073 | n/a | True |
| T9.S.ccy.am.JY | FX I5 am, JY alone, 26w | 0.133 | 1.00 | 0.276 | n/a | True |
| T9.S.ccy.am.BP | FX I5 am, BP alone, 26w | 0.044 | 1.00 | 0.496 | n/a | True |
| T9.S.ccy.am.AD | FX I5 am, AD alone, 26w | 0.010 | 1.00 | -0.351 | n/a | False |
| T9.S.ccy.am.CD | FX I5 am, CD alone, 26w | 0.046 | 1.00 | -0.252 | n/a | False |
| T9.S.ccy.am.SF | FX I5 am, SF alone, 26w | 0.029 | 1.00 | 0.363 | n/a | True |
| T9.S.ccy.am.NE | FX I5 am, NE alone, 26w | 0.402 | 1.00 | 0.102 | n/a | True |
| T9.S.lev.13 | FX I5, lev, 13w | 0.287 | 1.00 | 0.117 | 0.014 | True |
| T9.S.past.lev | FX I5 lev given past return, 26w | 0.122 | 1.00 | 0.153 | 0.058 | True |
| T9.S.ccy.lev.EC | FX I5 lev, EC alone, 26w | 0.850 | 1.00 | 0.063 | n/a | True |
| T9.S.ccy.lev.JY | FX I5 lev, JY alone, 26w | 0.634 | 1.00 | 0.100 | n/a | True |
| T9.S.ccy.lev.BP | FX I5 lev, BP alone, 26w | 0.781 | 1.00 | 0.063 | n/a | True |
| T9.S.ccy.lev.AD | FX I5 lev, AD alone, 26w | 0.209 | 1.00 | 0.314 | n/a | True |
| T9.S.ccy.lev.CD | FX I5 lev, CD alone, 26w | 0.563 | 1.00 | 0.247 | n/a | True |
| T9.S.ccy.lev.SF | FX I5 lev, SF alone, 26w | 0.152 | 1.00 | 0.221 | n/a | True |
| T9.S.ccy.lev.NE | FX I5 lev, NE alone, 26w | 0.027 | 1.00 | 0.601 | n/a | True |
| T9.S.spec.13 | FX I5, spec, 13w | 0.554 | 1.00 | 0.056 | 0.015 | True |
| T9.S.past.spec | FX I5 spec given past return, 26w | 0.324 | 1.00 | 0.103 | 0.076 | True |
| T9.S.ccy.spec.EC | FX I5 spec, EC alone, 26w | 0.458 | 1.00 | 0.273 | n/a | True |
| T9.S.ccy.spec.JY | FX I5 spec, JY alone, 26w | 0.153 | 1.00 | 0.298 | n/a | True |
| T9.S.ccy.spec.BP | FX I5 spec, BP alone, 26w | 0.534 | 1.00 | 0.136 | n/a | True |
| T9.S.ccy.spec.AD | FX I5 spec, AD alone, 26w | 0.577 | 1.00 | -0.111 | n/a | False |
| T9.S.ccy.spec.CD | FX I5 spec, CD alone, 26w | 0.154 | 1.00 | -0.466 | n/a | False |
| T9.S.ccy.spec.SF | FX I5 spec, SF alone, 26w | 0.045 | 1.00 | 0.369 | n/a | True |
| T9.S.ccy.spec.NE | FX I5 spec, NE alone, 26w | 0.581 | 1.00 | 0.136 | n/a | True |
| T9.S.bench | FX past 26w return as a predictor, 26w | 0.898 | 1.00 | -0.019 | 0.046 | None |
| T10.S.flow.UST.am.13 | Option flow, am, UST, 13w | 0.844 | 1.00 | 0.007 | -0.017 | False |
| T10.S.level.UST.am | Option level z, am, UST, 4w | 0.098 | 1.00 | 0.062 | 0.004 | True |
| T10.S.given.UST.am | Option flow given futures position, am, UST, 4w | 0.570 | 1.00 | 0.024 | -0.025 | False |
| T10.S.flow.UST.lev.13 | Option flow, lev, UST, 13w | 0.747 | 1.00 | -0.014 | 0.023 | False |
| T10.S.level.UST.lev | Option level z, lev, UST, 4w | 0.051 | 1.00 | -0.101 | 0.029 | False |
| T10.S.given.UST.lev | Option flow given futures position, lev, UST, 4w | 0.697 | 1.00 | -0.023 | 0.042 | False |
| T10.S.flow.UST.spec.13 | Option flow, spec, UST, 13w | 0.828 | 1.00 | 0.016 | 0.033 | True |
| T10.S.level.UST.spec | Option level z, spec, UST, 4w | 0.133 | 1.00 | -0.073 | 0.022 | False |
| T10.S.given.UST.spec | Option flow given futures position, spec, UST, 4w | 0.900 | 1.00 | -0.006 | 0.063 | False |
| T10.S.flow.FX.am.13 | Option flow, am, FX, 13w | 0.886 | 1.00 | -0.005 | 0.031 | False |
| T10.S.level.FX.am | Option level z, am, FX, 4w | 0.300 | 1.00 | 0.026 | 0.030 | True |
| T10.S.given.FX.am | Option flow given futures position, am, FX, 4w | 0.576 | 1.00 | 0.013 | 0.025 | True |
| T10.S.flow.FX.lev.13 | Option flow, lev, FX, 13w | 0.333 | 1.00 | -0.050 | 0.001 | False |
| T10.S.level.FX.lev | Option level z, lev, FX, 4w | 0.254 | 1.00 | -0.041 | 0.001 | False |
| T10.S.given.FX.lev | Option flow given futures position, lev, FX, 4w | 0.747 | 1.00 | 0.010 | 0.002 | True |
| T10.S.flow.FX.spec.13 | Option flow, spec, FX, 13w | 0.024 | 1.00 | -0.112 | 0.023 | False |
| T10.S.level.FX.spec | Option level z, spec, FX, 4w | 0.096 | 1.00 | -0.062 | 0.019 | False |
| T10.S.given.FX.spec | Option flow given futures position, spec, FX, 4w | 0.128 | 1.00 | -0.052 | 0.043 | False |
| T13.S.lev | Filter minus no filter, lev, 26w, corr difference | 0.237 | 1.00 | -0.296 | 0.017 | True |
| T13.S.spec | Filter minus no filter, spec, 26w, corr difference | 0.356 | 1.00 | -0.309 | -0.002 | True |
| T11.S.C | Composite C (three I5 groups, prior sign), net Sharpe | 0.555 | 1.00 | 0.231 | 0.193 | True |
| T11.S.C_vs_bench | Composite C minus benchmark Sharpe | 0.486 | 1.00 | 0.499 | n/a | True |
| T11.S.single.rates.I5_am_TYUS | Single I5_am_TYUS, rates, net Sharpe | 0.124 | 1.00 | -0.542 | 0.424 | False |
| T11.S.single.rates.I5_lev | Single I5_lev, rates, net Sharpe | 0.743 | 1.00 | 0.169 | -0.017 | True |
| T11.S.single.rates.I5_spec | Single I5_spec, rates, net Sharpe | 0.059 | 1.00 | 0.758 | -0.044 | True |
| T11.S.single.rates.I1 | Single I1, rates, net Sharpe | 0.716 | 1.00 | 0.165 | -0.559 | True |
| T11.S.single.rates.I2 | Single I2, rates, net Sharpe | 0.540 | 1.00 | 0.322 | -0.208 | True |
| T11.S.single.rates.I3_lev | Single I3_lev, rates, net Sharpe | 0.447 | 1.00 | 0.272 | 0.204 | True |
| T11.S.single.rates.I3_am | Single I3_am, rates, net Sharpe | 0.996 | 1.00 | 0.004 | 0.297 | True |
| T11.S.single.rates.I4 | Single I4, rates, net Sharpe | 0.876 | 1.00 | 0.088 | -0.365 | True |
| T11.S.single.rates.P2_lev | Single P2_lev, rates, net Sharpe | 0.456 | 1.00 | 0.297 | -0.456 | True |
| T11.S.single.rates.P2_am | Single P2_am, rates, net Sharpe | 0.197 | 1.00 | 0.398 | -0.689 | True |
| T11.S.single.rates.P2_spec | Single P2_spec, rates, net Sharpe | 0.196 | 1.00 | 0.485 | -0.217 | True |
| T11.S.single.rates.OPT_am | Single OPT_am, rates, net Sharpe | 0.288 | 1.00 | -0.525 | -0.080 | False |
| T11.S.single.rates.OPT_lev | Single OPT_lev, rates, net Sharpe | 0.146 | 1.00 | -0.643 | -0.282 | False |
| T11.S.single.rates.OPT_spec | Single OPT_spec, rates, net Sharpe | 0.146 | 1.00 | -0.642 | -0.340 | False |
| T11.S.single.fx.I1 | Single I1, fx, net Sharpe | 0.229 | 1.00 | -0.351 | -0.007 | False |
| T11.S.single.fx.I2 | Single I2, fx, net Sharpe | 0.019 | 1.00 | -0.677 | -0.126 | False |
| T11.S.single.fx.I3_lev | Single I3_lev, fx, net Sharpe | 0.641 | 1.00 | 0.109 | -0.016 | True |
| T11.S.single.fx.I3_am | Single I3_am, fx, net Sharpe | 0.290 | 1.00 | 0.367 | 0.036 | True |
| T11.S.single.fx.I4 | Single I4, fx, net Sharpe | 0.083 | 1.00 | -0.504 | -0.100 | False |
| T11.S.single.fx.P2_lev | Single P2_lev, fx, net Sharpe | 0.073 | 1.00 | -0.507 | -0.816 | False |
| T11.S.single.fx.P2_am | Single P2_am, fx, net Sharpe | 0.212 | 1.00 | -0.335 | -0.629 | False |
| T11.S.single.fx.P2_spec | Single P2_spec, fx, net Sharpe | 0.043 | 1.00 | -0.514 | -0.533 | False |
| T11.S.single.fx.OPT_am | Single OPT_am, fx, net Sharpe | 0.163 | 1.00 | -0.372 | -0.498 | False |
| T11.S.single.fx.OPT_lev | Single OPT_lev, fx, net Sharpe | 0.212 | 1.00 | -0.298 | -0.109 | False |
| T11.S.single.fx.OPT_spec | Single OPT_spec, fx, net Sharpe | 0.040 | 1.00 | -0.660 | 0.105 | False |
| T11.S.single.fx.I5FX_am | Single I5FX_am, fx, net Sharpe | 0.422 | 1.00 | 0.252 | 0.430 | True |
| T11.S.single.fx.I5FX_lev | Single I5FX_lev, fx, net Sharpe | 0.587 | 1.00 | 0.210 | -0.692 | True |
| T11.S.single.fx.I5FX_spec | Single I5FX_spec, fx, net Sharpe | 0.379 | 1.00 | -0.306 | -0.645 | False |
| T11.S.bench.rates | Benchmark strategy, rates, net Sharpe | 0.604 | 1.00 | -0.268 | -0.488 | False |
| T11.S.bench.fx | Benchmark strategy, fx, net Sharpe | 0.324 | 1.00 | 0.346 | -0.278 | True |
| T11.S.bench.both | Benchmark strategy, both, net Sharpe | 0.998 | 1.00 | -0.025 | -0.547 | False |
