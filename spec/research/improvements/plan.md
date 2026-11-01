# Pre-registered plan: positioning methods, out-of-sample tests

Written on 2026-11-01, before any test in this folder was run. Nothing below was chosen after seeing a result.
Only data availability was checked first: the CFTC and FRED endpoints respond, Yahoo responds, and marketdb has no long futures history.
Any change after the first run goes in the "Amendments" section at the end, with its reason and date.

## 1. Question and hypotheses

Question: which positioning methods still work out of sample, and which proposed improvements add value?

- H0 for every predictive test: the signal has no linear relation with the forward move (slope = 0).
- H1: the slope differs from zero. All tests are two-sided unless stated. The expected sign is recorded so a "right answer with the wrong sign" cannot count as a success.
- H0 for every improvement test: the improved signal is no better than the base signal (paired difference = 0).

## 2. Fixed sample boundaries

| Name | Signal dates (CFTC report date) | Use |
|---|---|---|
| FIT | 2006-06-13 to 2010-12-31 | I5 regression only. Fixed by the Goldman recipe. |
| DESIGN | 2006-06-13 to 2019-04-30 | The only sample used for any choice: signs, windows, composite membership. |
| GS-OOS | 2011-01-04 to 2019-04-30 | Goldman's own post-fit period, already published, so not a real test. Reported beside the holdout. |
| HOLDOUT | 2019-05-07 to the latest data | The real test. No choice uses it. Each primary test runs once. |
| H-A, H-B | 2019-05-07 to 2022-12-27, and 2023-01-03 to the end | Holdout halves. Stability read only. No selection. |

- Purge: a DESIGN row counts only if its forward window ends on or before 2019-04-30. So DESIGN returns never touch the holdout.
- Temporal split: DESIGN is about 63 percent of weeks, H-A about 18 percent, H-B about 19 percent. This is the 60/20/20 shape, with the first boundary set to Goldman's sample end. No shuffling.
- Departure from a tuning validation block: H-A is not used to tune. A tuning block would leave about 7 independent 26-week periods for the final test, which is too few.

## 3. Timing rule (no look-ahead)

- A CFTC report is dated Tuesday T and released Friday at 15:30 New York (`posmon.data.publish_time`).
- Decision and entry: the close of the first trading day on or after the Monday after release. Called E. FRED yields are 15:30-ish close quotes. H.10 FX rates are noon New York, so FX entry is Monday noon, which is still after release.
- Forward move: level(E + 7k days) minus level(E), using the last observation on or before each date.
- The Tuesday-based forward move Goldman used is computed only for T1 and T2, and is labelled as look-ahead.
- Benchmarks use yields through E, since yields are known daily.
- Known limit: history assumes the normal Friday release. Known late releases in the holdout, from the CFTC's special announcements page: report dates 2023-01-31 to 2023-03-14 (ION incident) and 2025-09-30 to 2025-12-23 (shutdown backlog, normal schedule resumed after 2025-12-29). T2 reruns the key tests with those signal weeks dropped.

## 4. Data

| Item | Source | Notes |
|---|---|---|
| Positions | CFTC API through `posmon.data.fetch_cftc`: legacy and TFF, futures-only and combined | TU FV TY TN US WN, and FX majors EC JY BP AD CD SF NE. BR, PE and RU are excluded before seeing any result, as they are not majors. Legacy from 2000. TFF from 2006-06. |
| Yields | FRED DGS2, DGS5, DGS7, DGS10, DGS20, DGS30 | TU DGS2, FV DGS5, TY DGS7, TN DGS10, US DGS20, WN DGS30. |
| FX | FRED H.10: DEXUSEU, DEXJPUS, DEXUSUK, DEXUSAL, DEXCAUS, DEXSZUS, DEXUSNZ | Quoted as USD per foreign unit. JPY, CAD, CHF flipped. Spot only, so no carry. |
| DV01 | `data/treasury_futures_dv01.csv` | Weekly. Forward-filled after 2026-10-13. Before 2013 it is a bond rebuild scaled to OFR's first 26 weeks. That scale is a small look-ahead inside FIT only. |
| Treasury price | Synthetic, roll-free: P = cumulated minus DV01 x own-yield change, per $ of face | No carry or roll-down. Yields are constant maturity, not the cheapest-to-deliver. |
| Comparison price | Yahoo front-month ZT=F, ZF=F, ZN=F, ZB=F | Unadjusted, with roll gaps. Used only to ask if the synthetic is an improvement (T6b). Also `data/ty_daily.csv` real TY closes for 2014-15. |

marketdb was checked: it holds tick data for short windows only (TY1 2017-09 to 2018-04, ZN 10 days), so it cannot supply continuous futures for 2006-2026. It is not used.

If a download fails, `raw/manifest.json` records it, dependent tests are reported as "not run", and nothing is substituted silently.

Raw downloads: `raw/`. Built signals: `derived/`.

## 5. Statistics used everywhere

- Newey-West lag L = ceil(1.5 k), which is at least the overlap k. Student-t reference with df = floor(T/k) - regressors - 1, where T/k is the effective independent count N_eff. Panels use Driscoll-Kraay, which is Newey-West on the date-level moments, so cross-contract correlation is handled.
- Circular block bootstrap, seed 42, 5000 draws, block = max(8, 2k) weeks. Pairs resampled by date. Panels resample whole dates.
- **Primary p-value = the larger of the Newey-West t p-value and the bootstrap p-value.** Naive standard errors are never used.
- Holm is applied to the primary family (section 7) and again to all tests (primary plus secondary). Both raw and adjusted p-values are reported. A test that cannot run counts as p = 1.
- Panel regression: y(i,t) = contract effect + b x(i,t). y is the forward price move over E, divided by (trailing 52-week SD of weekly changes, known at E, times sqrt(k)). So y is in risk units and comparable across contracts. x is scaled to unit standard deviation within the sample tested, so b reads like a correlation.
- Every hit rate has its base rate beside it: the share of the same rows with that outcome.
- N_eff is printed beside every result. Minimum detectable correlations are reported, raw and after Holm.
- Size check: rotate signals against returns inside the holdout and report how often the primary p-value rejects at 5 percent. It should be near or below 5 percent.
- Protocol flag: any test where the holdout beats the design sample is flagged as suspicious.
- Annualising: weekly returns use sqrt(52), the same convention as sqrt(252) on daily data.

## 6. Signals

Orientation for I5 and the benchmark: score above zero means a rally bias (yields fall).

- **I5 recipe (team-lead's version, not the stale text in the spec):** combined report. `am_TYUS` = asset managers plus other reportables, added before filtering, TY and US only. `am_all6` = same on six contracts. `lev` = leveraged funds on six. `spec` = legacy non-commercial on six. Built only with `posmon.indicators.filtered_change` and `filtered_residual`. Fit 2006-06-13 to 2010-12-31. Thresholds +0.25 and -0.25. Replication gate: before tests, the build must reproduce Goldman's April 2019 score (-0.67) and correlations near -43, -18, -26 and -35 percent on the Tuesday basis through April 2019. If it does not, stop and report.
- **Benchmark:** past 26-week change in DGS10, sign flipped for correlation purposes as a "yields rose, expect a fall" reading. For hit rates it is scaled the same way as I5: past change over (FIT weekly SD x sqrt 26), with the same thresholds.
- **I1:** net percent of open interest, legacy non-commercial, futures only.
- **I2:** 156-week sentiment index, same data.
- **I3_lev, I3_am:** 209-week Deutsche scale, TFF futures only.
- **I4:** net x DV01 (or net x USD notional for FX), z-score on expanding past data only, minimum 104 weeks. The spec's full-sample z-score is look-ahead, so it is not used.
- **P2:** share in pain from the ledger, futures only. For group g in {lev, am, spec}. `net_share` = long-field share minus short-field share. Window 126 trading days, `pro_rata`. Computed with `posmon.ledger.build_ledger`, as of E, with the release rule, and checked against `posmon.pain.cftc_pain` on a sample of dates.
- **Depth (T7):** among all open lots, open-weighted average of the distance underwater, with lots above water counting zero, in units of the trailing 126-day daily price SD. `net_depth` = long minus short.
- **Crowded pain (T7):** -1 if I2 >= 90 and long share >= 0.5. +1 if I2 <= 10 and short share >= 0.5. Else 0.
- **FX I5 (T9):** same functions, with "yield" = minus 100 log(USD per foreign unit), and DV01 = USD notional per contract in $mm per percent. Own-currency fit on FIT. Score above zero means spot fell more than implied, so expect it to rise.
- **Option position (T10):** net combined minus net futures-only for each group, which is the delta-adjusted option position. Flow signal: exponential average (half-life 5 weeks) of the weekly change, as a share of combined open interest, divided by its expanding SD (minimum 52 weeks).
- **Past return control:** past 26-week price move at E, in risk units.

## 7. Tests and success rules

### Primary family (Holm applied across all of these)

| ID | Test | Statistic on the holdout, Monday entry | Success rule |
|---|---|---|---|
| T1.1 | I5 am_TYUS, 26w | Slope of forward DGS10 change on score | Negative slope, Holm p < 0.05, both-side hit rates above base. |
| T1.2 | I5 am_all6, 26w | Same | Same |
| T1.3 | I5 lev, 26w | Same | Same |
| T1.4 | I5 spec, 26w | Same | Same |
| T1.5 | Benchmark, 26w | Slope on past 26w change | Negative slope, Holm p < 0.05. |
| T2.1 | Lag cost, am_TYUS, 26w | Corr(Tuesday entry) minus corr(Monday entry) | "Costly" if the 95% block interval excludes 0 or the gap exceeds 0.05. |
| T3.1-3 | Score adds beyond benchmark: am_TYUS, lev, spec, 26w | Slope on score with past change in the same regression | Right sign, Holm p < 0.05, block interval excludes 0, and positive incremental out-of-sample R-squared. |
| T4.1-2 | Expanding beta, rolling 260w beta, vs fixed, am_TYUS, 26w | Paired corr difference | Interval excludes 0 in favour of the variant. |
| T5.1-3 | I5 am_TYUS at 4, 8, 13w | Slope | Negative slope, Holm p < 0.05. |
| T6.1-6 | P2 net_share at 13w: lev, am, spec x UST, FX | Panel slope | Holm p < 0.05 with the same sign as DESIGN. |
| T6.7-8 | P2 lev given past return, UST, FX, 13w | Panel slope with control | Holm p < 0.05, same sign as DESIGN. |
| T7.1-2 | Depth vs share, lev, UST, FX, 13w | Paired |b| difference | Interval excludes 0 in favour of depth. |
| T7.3-4 | Crowded pain, spec, UST, FX, 13w | Panel slope | Holm p < 0.05, same sign as DESIGN, at least 30 event rows per side or say too few. |
| T7.5-6 | Design-chosen window, lev, UST, FX, 13w | Panel slope | Holm p < 0.05, same sign as DESIGN. |
| T8.1-10 | I1, I2, I3_lev, I3_am, I4 x UST, FX, 13w | Panel slope | Holm p < 0.05, same sign as DESIGN. |
| T9.1-3 | FX I5: am, lev, spec, 26w, fit FIT | Panel slope on score | Positive slope (contrarian on residual), Holm p < 0.05. |
| T10.1-6 | Option flow, am, lev, spec x UST, FX, 4w | Panel slope | Holm p < 0.05, same sign as DESIGN. |
| T11.1 | Composite net Sharpe, holdout | Bootstrap on weekly net returns, block 26 | Holm p < 0.05, Sharpe above 0. |
| T11.2 | Composite minus benchmark Sharpe | Paired bootstrap | Holm p < 0.05 in favour of composite. |
| T12.1-3 | Filter placebo: real flows vs circularly shifted flows, am_TYUS, lev, spec, 26w | Holdout corr vs placebo distribution | Holm p < 0.05, real more negative. |
| T13.1 | Filter vs no filter, am_TYUS, 26w | Paired corr difference | Interval excludes 0 in favour of the filter. |

### Secondary (raw p, Holm across all tests, no headline claim)

- T1: every group and the benchmark at Tuesday entry. All periods. am_TYUS minus am_all6 corr difference.
- T2: Friday close entry, all groups, 4 and 13w. Late-release weeks dropped. "Fresh score": add the yield change from T to E to the residual sum.
- T3: Newey-West at lag = k, Clark-West tests, decomposition into past change and positioning term.
- T4: sub-period betas, expanding scale alone, and lev and spec variants.
- T5: lev, spec and benchmark at 4, 8, 13w.
- T6: lev-only rule hit rates against the deck thresholds (0.70, 0.30). am and spec with the past-return control. 4 and 26w.
- T6b: synthetic price against real TY closes in `data/ty_daily.csv`, and P2 on Yahoo unadjusted against P2 on synthetic for TU, FV, TY, US. The synthetic counts as an improvement if daily change correlation is at least 0.9 and the P2 slope on it is at least as strong in DESIGN.
- T7: rule sensitivity (pro_rata, fifo, low_price_first). The answer counts as insensitive if pairwise correlations are at least 0.8, signs agree, and slope gaps are under one standard error. Windows 30, 63, 90, 126, 252. Crowding alone, without pain. Lev version of crowded pain.
- T8: all five signals at 4, 8, 26w, on the common sample. Spec-style aggregate I4 on the 10-year at 4w.
- T9: each currency alone, 13w, and given past return.
- T10: option level z-score, flow at 13w, and flow given the group's futures position.
- T11: each single signal, the benchmark, buy-and-hold, cost at 0, 1, 5 and 10 bps. A hindsight composite (B) made of holdout survivors, clearly labelled as contaminated.
- T14: simulation of the benchmark's small-sample bias. Resample weekly DGS10 changes without any real mean reversion and ask how often corr(past 26w, next 26w) reaches -35 percent over 2006 to April 2019.

## 8. T11 construction

- Members for the primary composite (A) come from DESIGN only: signals with |t| >= 2.0 at their primary horizon in DESIGN, signed by the DESIGN slope, at most the 5 strongest per sleeve.
- Sleeves: rates (trades the DGS10 point, with TY DV01 for costs) and FX (seven currencies, each with its own signal, equal risk).
- Position: I5-type signals use the +0.25 and -0.25 rule, giving -1, 0 or +1. Others use a z-score on expanding past data clipped to -1 and +1. Composite = equal-weight mean of members. A second version weights by past information coefficient, computed walk-forward from completed forward returns only (secondary).
- Sizing: 10 percent annual risk on a trailing 52-week SD. Weekly rebalance at Monday entry.
- Cost: 5 bps of traded notional per side, stated and charged. Carry is not included in either sleeve.
- Metrics: OOS Sharpe, t-stat, maximum drawdown, information ratio against the benchmark strategy.
- If no signal qualifies, composite A is reported as "empty", and T11.1 and T11.2 count as p = 1.

## 9. Ranking rule for the report

1. Confirmed: primary test, Holm p < 0.05, sign as designed.
2. Suggestive: raw primary p < 0.05, same sign in DESIGN and in both holdout halves, but fails Holm.
3. Inconclusive: right sign, not significant, sample too small to rule out a useful effect.
4. Rejected: wrong sign, or holdout near zero with an interval that rules out a useful size.

Adoption needs level 1, or level 2 with a clear cost-free reason, such as removing look-ahead. Holdout results are never used to tune anything.

## 10. Bias and leakage checklist

- [x] No look-ahead: features at T use data no later than T, tradable returns start at E.
- [x] I4 and all z-scores use past data only. Full-sample scaling is not used.
- [x] Survivorship: contracts picked by rule. TN and WN enter when they list. RU, BR, PE excluded up front.
- [x] TFF history before September 2009 is CFTC backfill. Affects FIT only.
- [x] Costs charged (5 bps of notional minimum).
- [x] Universe not cherry-picked: all six Treasury contracts and all seven G10 FX contracts on the config list.
- [x] Non-stationary inputs: flows and forward moves are changes. Levels are scaled to bounded ranges or z-scored on past data.
- [x] OOS above IS flagged.

## 11. Amendments

Each of these came after a first run. None changes a holdout boundary, a sign rule or a primary test.

- **A1, 2026-11-01, empty-ledger guard.** The first run showed panel t-values above 20 with bootstrap p near 0.3. The cause was a data error, not a result. A fully emptied ledger keeps floating-point residue near 1e-14 contracts, and the share then explodes to values as large as 2e31. `posmon.pain._share_in_pain` has the same gap. `s01_signals.py` now treats 1e-6 contracts or fewer as empty, and it stops if any share leaves 0 to 1. T6, T7 and the T11 screen were rerun. All results in the report use the guard. I saw the corrupted T6 and T7 numbers before fixing this. The fix changes no choice of signal, window or sign rule.
- **A2, 2026-11-01, rotation p-values.** The size check showed the primary p-value rejects too often at long horizons (about 19 percent at 26 weeks, nominal 5). So rotation p-values are reported beside the primary p-value for each slope test, with their own Holm column. The pre-registered p-value and its Holm remain the decision rule.
- **A3, 2026-11-01, Composite C.** Composite A came back empty under the DESIGN rule, so T11.1 and T11.2 count as p = 1, as planned. To still answer "composite against single signals", Composite C was added as a secondary test: the three I5 groups in Goldman's published direction, with no selection.
- **A4, 2026-11-01, gate purge.** The first gate build counted rows whose forward window ran past April 2019, giving n = 647 and -41 percent. Goldman could not have known those rows. Restricting to finished windows gives n = 621 and -43.2 percent. No later test is affected, since tests already purge.
- **A5, clarifications.** "am" in T9 and T10 means asset managers plus other reportables, the I5 definition. "am" in P2 means asset managers alone, the P2 field. Diagnostics added after seeing results carry a "post-hoc" label and have no p-value: correlation of each score with the past change, the published correlation split by period, and the signal correlations in T8.
- **A7, spec changed during the run.** Other agents updated I4 and I5 in `positioning_spec.tex` after this plan was written. The plan's I4 stays as fixed. A secondary test adds I4 exactly as the spec now states it. Report recipes target the latest wording.
- **A6, added leak test.** `s04_checks.py` cuts every raw input at three dates and confirms no signal already known by then changes.
