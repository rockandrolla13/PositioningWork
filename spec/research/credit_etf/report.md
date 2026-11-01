# Credit ETF positioning: can the methods be applied?

Tested on 1 November 2026. Plan: `plan.md`. Numbers: `results.json`. Rerun: `./run_all.sh`.

## The answer

**Partly. The ledger and the position measures compute on ETF data and describe stress. None of them predicts ETF excess returns once tested properly. One spread result stays open: LQD flows against Moody's BAA10Y, covered in point 5.**

1. 0 of 160 tests pass the success rule. Holm is a step-down correction for running many tests at once, and the smallest Holm-adjusted p is 0.90.
2. 15 of the 152 time-series tests have a raw p below 5%. A placebo that shifts returns at random gives 6.7 on average and 18 at its 95th percentile. So the count looks like chance: 7.8% of placebo draws match or beat it.
3. The plain spread level beats every positioning signal. At 26 weeks it has t = 5.93 and R-squared 0.32 on LQD, and t = 12.51 and R-squared 0.31 on HYG. It survives dropping 2020 (t = 4.18 and 3.10). It is a benchmark outside the family, tested under the same error rules. Any positioning signal must beat this first.
4. The one lead worth a later look is high-yield pain at 4 weeks. It gives +35 bp per standard deviation on HYG, with t = 2.75. It holds in both sub-periods and without 2020, and JNK agrees (t = 2.16). But its Holm-adjusted p is 1.00, it is absent on LQD (t = 0.12), it had no effect in the development window (t = 0.10), and after costs it trails buy and hold (0.20 against 0.32 Sharpe). Treat it as a hypothesis.
5. The open result is IG crowding against a slow spread series. On BAA10Y, 30 of 76 LQD cells have |t| above 2. A placebo averages 5 and never reached that count in 400 draws. Inflows come before tighter BAA10Y (13-week flow, 4 weeks ahead: t = -3.39). I do not call it established. Its best Holm p within those cells is 0.07. The tradable target barely shows it (t = 1.89). Other IG funds disagree at 4 weeks (USIG t = 2.25, IGIB t = 0.07, IGSB t = -1.07). BAA10Y is also slow, with weekly autocorrelation of 0.27 against 0.02 for OAS. Pain itself shows little on this target (4 weeks t = 1.40).

This is a null result with limits. At 13 and 26 weeks the holdout holds only 38 and 19 independent observations. Clearing Holm there needs an R-squared of 0.30 and 0.55. So those horizons can only catch a very strong signal. The spread level clears it, and a modest positioning effect would not.

## Verdict by method

| Method | Verdict | One line of evidence |
|---|---|---|
| P1 Morgan Stanley pain | **Does not transfer** | Its four cases fail against true short interest. Sign agreement is 41%, 45% and 45% on LQD, HYG and JNK, and rank correlation is -0.27, -0.19 and -0.23. |
| P2 lot ledger | **Transfers with changes, as a description only** | Depth of pain reaches the top decile within 2 weeks of the stress dates in 10 of 14 checks. But the ledger covers only 8% of LQD and 13% of HYG shares. It predicts nothing after Holm. |
| P4 activity by price | **Transfers with changes, as a description only** | It runs with shares as longs and no daily shorts. It makes no predictive claim, so there is nothing to test. |
| P5 over or under water | **Does not transfer** | Falling shares set its side to "Short", yet that is longs leaving, not shorts. No stable effect: LQD 26 weeks t = -1.94, -1.46 with controls, Holm 1.00. |
| I1 net share of open interest | **Transfers with changes, as a description only** | I1 = 100 x shares / (shares + short interest). It means something only where shorts are large: median short interest over shares is 15% on LQD, 39% on HYG and 0.2% on USIG. LQD 26 weeks t = -3.25 on 8.7 effective observations, which is too thin. |
| I2 sentiment index | **Transfers with changes on short interest, as a description only** | On log shares it mostly tracks fund growth. Neither form predicts. At 4 weeks t is 1.69 on LQD and 0.65 on HYG using shares, and 0.62 and 0.13 using short interest. |
| I3 scaled -10 to +10 | **Transfers with changes, as a description only** | Shares are never negative, so it needs signed 26-week flow. LQD 26 weeks t = 2.57, HYG t = 0.01, Holm 1.00. |
| I4 one-standard-deviation rule | **Does not transfer** | Dollar flows grow with the fund, so a fixed band fires on 72% of LQD weeks in the holdout. LQD 26 weeks t = -1.77, HYG t = 0.28. |
| I5 filtered residual | **Does not transfer** | LQD 26 weeks looks good (t = 2.86, forward correlation -0.34 against -0.26). But the slope falls from 103 to 18 bp without 2020 and turns negative in 2022-2026 (-79). |
| I6 options-implied position | **Not tested** | Alpha Vantage gates the chain as a premium endpoint on this key. Databento quotes $163 for 2018 to 2026, and I spent nothing. |
| I7 continuation | **Does not transfer** | Time series: LQD 4 weeks t = 1.75, HYG t = 1.10. Cross section: t = -2.24 at 1 week, the opposite sign to continuation. |
| I7 reversal | **Does not transfer** | Development t = 2.21 and 2.38 at 4 weeks flip to -1.55 and -0.80 in the holdout. Cross section t = 1.05. |
| I8 CTA proxy | **Does not transfer** | Trend at 4 weeks: LQD t = 0.12, HYG t = -1.34. Trading the sign of momentum nets a Sharpe of -0.04 and -0.18 against 0.29 and 0.32 for buy and hold. Daily aggressor imbalance does not follow trend (correlation -0.09 and -0.01 in 2024). |
| I1 to I5 on CFTC credit futures | **Would transfer as is, but too short to test** | Bloomberg IG has 26 reports and HY has 24, all from 2026. I2 needs 156 weeks, so it is 130 short. |

## How the working mapping fared

1. **"Shares outstanding play the role of open interest."** True as an accounting identity. False as a reading of positions: share changes track the premium and move against short interest.
2. **"A daily ledger gives holder cost basis."** Rejected. It gives the cost of net primary flow inside the window. Secondary trading is the bulk of activity, and primary flow is only 12% of volume on LQD and 9% on HYG. Read the output as "share of recent net creations under water", never "share of holders under water".
3. **"Gross long = shares + short interest."** True as an identity, and it matters: short interest over shares has a median of 39% and a peak of 79% on HYG. But shorts and shares move in opposite directions (rank correlation -0.46, -0.38, -0.41). So a redemption is often not a long leaving. The likely reason is that market makers short shares to meet demand and create units to cover. That reading is my inference, because the data shows only the negative correlation.
4. **"Spread changes from FRED feed I5."** FRED now gives ICE BofA OAS for only 3 years. I replaced it with an implied spread from the ETF itself. Weekly correlation with OAS on the overlap is 0.92 on LQD and 0.97 on HYG.

## What breaks, most important first

1. **Holders do not act on pain the way a levered futures position must.** Pain does not predict redemptions on HYG (t = 0.44) or JNK (t = -1.04). LQD shows a small effect (-0.75% of shares per standard deviation over 4 weeks, t = -2.18). After weak excess returns, shares rise instead (momentum t = -3.04, -4.60, -5.15). This undercuts the mechanism behind a pain trade.
2. **Shares outstanding are not a position.** See the short-interest result above.
3. **The ledger sees a small slice.** Median coverage is 8% to 13% of shares. Reductions exceed the ledger in 71% to 78% of weeks. A drained ledger gave no reading in 31 LQD weeks.
4. **Authorised participants trade the premium.** Lagged premium explains 3% to 8% of daily share changes in the holdout, with t above 2. In March 2020 LQD closed 5.1% below NAV, so NAV and market price disagree most when it matters.
5. **Timing.** Share changes line up best with the premium one day earlier on LQD and HYG, but the peak is flat (0.22 at lag 0 and 0.24 at lag 1). The wrong lag moves the LQD pain share by 9 points on average.
6. **Distributions.** A raw price overstates mean pain by 6 points on LQD, 11 on HYG and 14 on JNK. Use total return.

Two worries turned out small. The last 3 days of a month hold 14.0% of LQD's absolute flow against 14.3% for an even spread, so rebalances do not concentrate flow. And the bid-ask is small: the median half-spread is 0.46 bp on LQD and 0.64 bp on HYG, from one venue with about 16% of volume. Costs are not what kills these signals. The removal rule matters little too: FIFO correlates 0.97 with pro rata on LQD.

## Test results

**C1, ledger and stress.** The planned rule is strict: 7 of 14 checks pass at the named week. Within 2 weeks of the date, 10 pass. The 2020 misses are a timing effect. The week after the trough holds large creations at low prices and a rebound, so LQD pain drops from 1.00 on 20 March to 0.05 on 27 March. Coverage is the deeper problem: on 13 March 2020, near the worst of the sell-off, the LQD ledger was empty and gave no reading. A week later its reading of 1.00 rested on 4% of shares. The reading also fires often: pain is at least 0.75 in 17% of LQD weeks. Verdict: it responds to stress, and it is noisy.

| Trough | Fund | Week | Pain | Depth | Depth rank | Best pain within 2 weeks | Strict pass |
|---|---|---|---|---|---|---|---|
| 2008-12-12 | HYG | 2008-12-12 | 0.78 | 16.9% | 0.99 | 0.96 | yes |
| 2008-12-12 | JNK | 2008-12-12 | 0.98 | 27.8% | 0.99 | 1.00 | yes |
| 2013-09-05 | LQD | 2013-09-06 | none | none | 0.00 | 0.00 | no |
| 2016-02-11 | HYG | 2016-02-12 | 1.00 | 5.7% | 0.97 | 1.00 | yes |
| 2016-02-11 | JNK | 2016-02-12 | 1.00 | 3.5% | 0.95 | 1.00 | yes |
| 2020-03-23 | LQD | 2020-03-27 | 0.05 | 1.8% | 0.88 | 1.00 | no |
| 2020-03-23 | HYG | 2020-03-27 | 0.48 | 11.3% | 0.98 | 1.00 | no |
| 2020-03-23 | JNK | 2020-03-27 | 0.05 | 8.8% | 0.98 | 1.00 | no |
| 2022-10-20 | LQD | 2022-10-21 | 1.00 | 4.0% | 0.97 | 1.00 | yes |
| 2022-10-20 | HYG | 2022-10-21 | 0.50 | 0.9% | 0.78 | 0.69 | no |
| 2022-10-20 | JNK | 2022-10-21 | 0.25 | 0.6% | 0.75 | 0.54 | no |
| 2025-04-08 | LQD | 2025-04-11 | 0.98 | 2.8% | 0.94 | 0.98 | yes |
| 2025-04-08 | HYG | 2025-04-11 | 1.00 | 2.6% | 0.92 | 1.00 | yes |
| 2025-04-08 | JNK | 2025-04-11 | none | none | 0.00 | 1.00 | no |

**C2, prediction.** No evidence after correction. See the appendix. The base rate of a positive excess return is high (73% on LQD and 78% on HYG at 26 weeks), so a hit rate alone says little. The ICE OAS target has about 149 weeks and decides nothing, so it stays in `results.json`.

BAA10Y is the only long direct spread series, and it is IG only. Its count of 30 cells above |t| = 2 shrinks to 18 without 2020 and to 21 when the target starts a week later. It stands at 32 with the past 4-week implied spread change as a control, and at 19 with the same-period change in the 10-year yield as a control. So staleness alone does not explain it. These signals are close cousins, because most are forms of recent flow. The direct test of this finding is a longer OAS history from ICE, which FRED no longer carries.

**C3, I5.** The recipe runs unchanged, and the fitted slope has the expected negative sign. The fit explains little: R-squared is 0.07 on LQD and 0.12 on HYG.

| Fund, variant | Forward correlation at 26 weeks | Benchmark | I5 t beside benchmark | Rally case hit (base) | Widening case hit (base) | Extra rule |
|---|---|---|---|---|---|---|
| LQD usd | -0.34 | -0.26 | -3.24 | 78% (61%) | 46% (39%) | pass |
| HYG usd | -0.34 | -0.31 | -2.37 | 62% (47%) | 40% (53%) | fail |
| JNK usd | -0.21 | -0.30 | 0.66 | 42% (48%) | 33% (52%) | fail |
| USIG usd | -0.32 | -0.28 | -2.26 | 68% (65%) | 60% (35%) | fail |

LQD passes the extra rule alone. It still fails the general rule: the bootstrap interval is -15 to 177 bp and includes zero, Holm is 1.00, and t falls to 1.54 with spread level and momentum as controls. The sub-period table below shows the effect is 2020.

**C4, continuation and reversal.** Neither holds. See the appendix. The sign of the reversal signal is unstable between development and holdout.

**C5, short interest and options.** The P1 check fails on every fund tested. Short interest level, change and sentiment index show no stable effect. The P2 ledger on FINRA dates was added after results and sits outside the family. A short ledger shows nothing (HYG 4 weeks t = -0.57). A gross-long ledger echoes the HY lead (HYG t = 2.91, JNK t = 1.65, LQD t = 0.52). Options were not tested.

**C6, IG against HY.** The planned rule says pooling is allowed: slopes are not rejected as equal in 76% of cases and share a sign in 78%. I would not lean on that, for three reasons:
1. The test has little power at long horizons, and a control pair inside IG (LQD and USIG) fails its own sign rule at 59%.
2. Inputs differ: short interest is 15% of shares on LQD and 39% on HYG, and weekly flows correlate only 0.29 even though 1-week excess returns correlate 0.88.
3. Pain relates to later flows differently on LQD and on HY.

**Decision: compute each fund separately and report IG and HY as separate groups. Nothing has survived that would need pooling.**

**Stability of the labelled results.** Each cell is the slope in bp per standard deviation, with t in brackets. These checks were added after results and they change no label.

| Test | Holdout | 2017-2021 | 2022-2026 | Holdout without 2020 |
|---|---|---|---|---|
| i5_usd LQD 26 | 103 (2.86) | 120 (3.11) | -79 (-1.66) | 18 (0.69) |
| i5_pct LQD 26 | 152 (2.61) | 185 (3.14) | -91 (-1.54) | 23 (0.58) |
| i5_usd HYG 26 | 257 (2.18) | 262 (2.03) | 167 (1.00) | -66 (-0.36) |
| i5_usd HYG 4 | 93 (2.18) | 84 (1.82) | 209 (2.62) | 61 (1.49) |
| pain126 HYG 4 | 35 (2.75) | 49 (2.02) | 24 (2.40) | 22 (3.05) |
| gap_turn HYG 4 | 248 (2.82) | 332 (3.37) | 100 (1.40) | 133 (2.55) |
| p1_long_oi HYG 4 | 48 (2.33) | 93 (3.24) | 11 (0.94) | 5 (0.54) |
| si_ratio LQD 26 | -58 (-3.25) | n/a | -58 (-3.25) | -58 (-3.25) |
| level LQD 26 | 480 (5.93) | 547 (5.74) | 357 (6.93) | 331 (4.18) |
| level HYG 26 | 413 (12.51) | 437 (12.23) | 371 (4.51) | 344 (3.10) |
| level LQD 4 | 173 (3.24) | 223 (3.22) | 91 (2.88) | 82 (3.29) |
| level HYG 4 | 156 (6.90) | 159 (5.45) | 157 (3.83) | 167 (4.75) |
| mom26 HYG 4 | -149 (-2.69) | -143 (-2.21) | -180 (-2.43) | -125 (-2.48) |

**Every labelled result in full, with benchmarks.** Slope is bp of excess return per development standard deviation. Hit is the share of positive excess returns in the top or bottom quintile, with the count in brackets, beside the base rate. Quintile thresholds come from development data. So a lopsided count means the signal left its old range.

| Test | Slope | t | Raw p | Holm p | 95% block bootstrap | N | Effective N | Top hit | Bottom hit | Base rate | t with controls | Replicate t |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pain126 HYG 4 | 35 | 2.75 | 0.007 | 1.00 | 14 to 65 | 494 | 124 | 65% (78) | 49% (138) | 62% | 3.01 | 2.16 |
| p1_long_oi HYG 4 | 48 | 2.33 | 0.021 | 1.00 | 5 to 88 | 509 | 127 | 66% (104) | 58% (251) | 62% | 0.35 | 2.24 |
| gap_turn HYG 4 | 248 | 2.82 | 0.006 | 0.90 | 73 to 382 | 509 | 127 | 69% (48) | 100% (1) | 62% | 3.49 | 2.23 |
| flow13 LQD 1 | 8 | 2.00 | 0.046 | 1.00 | 1 to 16 | 512 | 512 | 54% (83) | 53% (223) | 55% | 0.10 | -1.80 |
| i5_usd LQD 13 | 67 | 2.13 | 0.040 | 1.00 | 1 to 161 | 500 | 38 | 85% (105) | 71% (106) | 68% | 0.52 | 1.45 |
| i5_usd LQD 26 | 103 | 2.86 | 0.011 | 1.00 | -15 to 177 | 487 | 19 | 89% (98) | 66% (106) | 72% | 1.54 | 1.98 |
| i5_usd HYG 4 | 93 | 2.18 | 0.031 | 1.00 | -4 to 177 | 509 | 127 | 69% (26) | 87% (31) | 62% | -2.83 | 1.67 |
| i5_usd HYG 26 | 257 | 2.18 | 0.044 | 1.00 | -116 to 456 | 487 | 19 | 100% (26) | 100% (31) | 78% | 0.78 | 0.85 |
| i5_pct LQD 26 | 152 | 2.61 | 0.018 | 1.00 | -19 to 256 | 487 | 19 | 92% (39) | 68% (117) | 72% | 1.59 | 1.69 |
| si_ratio LQD 26 | -58 | -3.25 | 0.015 | 1.00 | -87 to -9 | 226 | 9 | 79% (196) | none | 82% | 0.03 | -0.04 |
| benchmark level LQD 4 | 173 | 3.24 | 0.002 | n/a | 62 to 264 | 509 | 127 | 86% (7) | none | 60% | n/a | n/a |
| benchmark momentum LQD 4 | -82 | -1.74 | 0.085 | n/a | -170 to 6 | 509 | 127 | 70% (57) | 71% (70) | 60% | n/a | n/a |
| benchmark level LQD 26 | 480 | 5.93 | 0.000 | n/a | 282 to 646 | 487 | 19 | 100% (7) | none | 72% | n/a | n/a |
| benchmark momentum LQD 26 | -130 | -1.26 | 0.225 | n/a | -307 to 70 | 487 | 19 | 96% (57) | 87% (70) | 72% | n/a | n/a |
| benchmark level HYG 4 | 156 | 6.90 | 0.000 | n/a | 111 to 210 | 509 | 127 | 89% (9) | 59% (430) | 62% | n/a | n/a |
| benchmark momentum HYG 4 | -149 | -2.69 | 0.008 | n/a | -257 to -26 | 509 | 127 | 95% (19) | 79% (33) | 62% | n/a | n/a |
| benchmark level HYG 26 | 413 | 12.51 | 0.000 | n/a | 302 to 536 | 487 | 19 | 100% (9) | 75% (408) | 78% | n/a | n/a |
| benchmark momentum HYG 26 | -251 | -1.35 | 0.196 | n/a | -539 to 227 | 487 | 19 | 100% (19) | 100% (33) | 78% | n/a | n/a |

Buy and hold excess return in the holdout, for scale:

| Fund | Weeks | Mean bp | t | Share positive |
|---|---|---|---|---|
| LQD | 4 | 18 | 1.37 | 60% |
| LQD | 26 | 112 | 2.24 | 72% |
| HYG | 4 | 22 | 1.53 | 62% |
| HYG | 26 | 144 | 2.41 | 78% |

**Costs.** Bp a year on a weekly rebalance, with half-spread, 1 bp of hedge per side, and borrow of 0.5% on LQD and 1% on HYG. The hedge and borrow numbers are my assumptions. Only labelled signals and benchmarks appear.

| Fund | Rule | Gross | Net | Net Sharpe | Turnover a year |
|---|---|---|---|---|---|
| LQD | buy_hold | 238 | 238 | 0.29 | 0.1 |
| LQD | momentum_sign | -4 | -30 | -0.04 | 8.6 |
| LQD | flow13|h1 | 269 | 234 | 0.30 | 9.0 |
| LQD | i5_usd|h13 | 183 | 166 | 0.23 | 4.7 |
| LQD | i5_pct|h26 | 107 | 89 | 0.13 | 4.1 |
| LQD | si_ratio|h26 | -144 | -191 | -0.49 | 1.9 |
| HYG | buy_hold | 299 | 298 | 0.32 | 0.1 |
| HYG | momentum_sign | -131 | -165 | -0.18 | 6.8 |
| HYG | pain126|h4 | 203 | 134 | 0.20 | 25.4 |
| HYG | p1_long_oi|h4 | -8 | -113 | -0.13 | 34.2 |
| HYG | gap_turn|h4 | 150 | 137 | 0.22 | 8.1 |
| HYG | i5_usd|h4 | -3 | -11 | -0.02 | 1.2 |

## Recipes for the methods that transfer

All of these are **descriptions, not signals**. No evidence supports trading on them.

### Shared rules

1. **Timing.** A row dated d is usable on the next trading day. A reading on date T uses rows dated T-1 or earlier. FINRA short interest is usable from settlement + 10 business days.
2. **Total-return NAV.** TRN(t) = TRN(t-1) x (NAV(t) + exdiv(t)) / NAV(t-1), with TRN(0) = 1. Never use a raw price in a ledger.
3. **Flow.** dS(t) = S(t) - S(t-1) from issuer shares outstanding.
4. **Order date.** A share change dated t belongs to order date t-k. Estimate k on past data as the lag in {0, 1, 2} with the highest correlation between the log share change and the premium. LQD and HYG give k = 1.
5. **Matched hedge.** Each day find the maturity m whose par bond has modified duration D, where D is the holdings-weighted effective duration from the last holdings date. Hedge return = y(m, t-1) x days / 365 - D x (y(m, t) - y(m, t-1)), on the FRED par curve. Code: `common.matched_hedge`. As a check, the hedged LQD series correlates 0.96 weekly with the issuer's rate-hedged LQDH, and HYG 0.97 with HYGH. Their means differ, likely because a swap-hedged fund also earns the floating rate.
6. **Implied spread change, in bp.** ds(t) = -(r_nav(t) - hedge(t) - carry x days / 365) / D x 10,000. Carry is 1.3% a year for IG and 4% for HY. This is a stated round number. On the overlap HYG drifts 1.2 bp a week above OAS, so do not read levels off this series.
7. **CS01 per share.** NAV x D / 10,000.
8. **Baseline every positioning study must beat: spread level.** Level(t) = (yield to worst minus y(m)) at the last holdings date, plus the sum of ds since that date. Correlation with OAS on the overlap: 0.97 on LQD and 0.93 on HYG.

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
4. Use it only where median SI / S is above 5%. That holds for LQD, HYG and JNK. It does not hold for USIG (0.2%), IGSB (0.5%) or USHY (2.8%).

### I2-ETF: sentiment index on short interest

`posmon.indicators.sentiment_index(SI / (S + SI), weeks=156)` on the weekly series from I1-ETF. FINRA's API starts on 2017-12-29, so the first reading falls about three years later. Do not run it on the level of shares, because fund growth drives that level.

### I3-ETF: scaled flow

Flow26 = 100 x (ln S(T-1) - ln S 26 weeks earlier). Call `posmon.indicators.db_scaled(flow26, weeks=209)`. Do not run it on shares, because they are never negative and the short half of the scale would be empty.

### CFTC credit futures: original code, unchanged

`python -m posmon.cli fetch --report tff --code 221606` for IG and `--code 221605` for HY. Latest readings, net as a share of open interest: IG leveraged funds 30% and asset managers -37%, on 7,411 contracts. HY -6% and -10%, on 5,114 contracts, last reported 2026-09-15. Retest once I2's 156-week window fills, in about 2029.

## Data sources and limits

| Source | What it gave | Limit |
|---|---|---|
| iShares product-data JSON (`component=fundDownload`) | Daily NAV, ex-dividend, shares: LQD from 2002, HYG from 2007, and IGSB, IGIB, USIG, USHY, FALN, EMB, LQDH, HYGH, SHYG, to 2026-10-30 | The old `.ajax` xls link now returns the web page. It is the page's own feed, undocumented, and it may change. Check BlackRock's terms before production use. Archived Wayback copies were my first route and I dropped them, because the newest usable LQD copy stopped in January 2021. |
| iShares holdings (`component=holdings.all&asOfDate=`) | Dated effective duration and yield to worst | Sampled twice a year for LQD and HYG, once a year for the rest. |
| SSGA `navhist` xlsx | JNK, SJNK, SPSB, SPIB, SPLB: date, NAV, shares | No holdings here, so JNK borrows HYG's duration and yield path. A one-day jump in October 2014 on JNK and SPIB looks like a file error. It falls in development only and I left it. |
| Vanguard | Current price and premium only | I found no share history. |
| CRSP in marketdb | Only VCIT and TLT, 2019 to 2021 | Cannot feed LQD or HYG. Statistics only are stored. |
| marketdb book | Half-spread, VWAP, aggressor volume for LQD, HYG, JNK | One venue, about 16% of volume. Sampled: every day of 2024 for LQD and HYG, every fifth day otherwise. VWAP is 11 bp from NAV on LQD on average. |
| TRACE | Not used | 15 issuers, 2023 to 2025. Not a market series and not point in time. |
| FRED ICE BofA OAS | BAMLC0A0CM, BAMLH0A0HYM2 from 2023-10-31 | **FRED now keeps 3 years.** Its note says to go to the source for more. I did not pull older vintages. Top-level ICE data is licensed for internal use, so keep `raw/` private. |
| FRED Moody's and Treasury | BAA10Y, AAA10Y and par yields, full history | BAA10Y is IG only and long dated. |
| Yahoo chart API | Daily close, adjusted close, volume, JNK dividends | An unofficial feed, so check its terms before production use. It answered a plain user agent and returned 429 to a browser one. Adjusted close is restated as of download. |
| FINRA API | Short interest twice a month from 2017-12-29 | The 10-business-day lag is my conservative choice. |
| CFTC | Bloomberg IG and HY credit futures in TFF | From 2026 only. I found no iBoxx (IBHY, IBIG) or CDX contract under those names. |
| Alpha Vantage | Put-call ratio by date | `HISTORICAL_OPTIONS` and adjusted daily prices are premium on this key. |
| Databento OPRA | Quote only | $0.93 for one week of LQD and HYG statistics, $162.74 for 2018 to 2026. I did not buy it. |

## Checks on the work itself

1. **Point in time.** Rebuilding with data cut at a past week changes no signal on that week (largest gap 0.0, across 60 values). This covers the weekly step. The daily series are built forward only and were not cut separately.
2. **False-positive rate.** Random persistent signals reject at 5% about as they should. See the table. The test is conservative at short horizons and slightly loose at 26 weeks.
3. **Planted signal.** A signal built from the future return clears Holm at every horizon, so the harness can find an effect.
4. **A real bug, found and fixed.** The first run showed |t| above 5 for LQD pain with a slope near zero. A drained ledger had produced absurd values. The rule "bootstrap interval excludes zero" flagged it. `plan.md` records the fix. The cause was my own sum, which skipped negative rounding noise. A related point for `posmon`: `_share_in_pain` and `ms_pain_monitor` test the open total for exact zero. In a random test of 100,000 fully drained windows with several removals, about a quarter left a non-zero open total of about 1e-12. `posmon` stayed within 0 to 1 there, but it returned a normal-looking number where the spec says no reading. I did not edit `posmon`. A tolerance of 1e-6 x gross total, as in the P2-ETF recipe, would fix it.

| Horizon (weeks) | Effective N | R-squared needed for Holm | R-squared needed for raw 5% | False positives at 5%, LQD | False positives at 5%, HYG | Planted signal t, LQD |
|---|---|---|---|---|---|---|
| 1 | 512.0 | 0.025 | 0.008 | 0.017 | 0.007 | 8.9 |
| 4 | 127.2 | 0.099 | 0.030 | 0.030 | 0.040 | 8.1 |
| 13 | 38.5 | 0.303 | 0.101 | 0.050 | 0.060 | 8.6 |
| 26 | 18.7 | 0.550 | 0.211 | 0.093 | 0.070 | 8.3 |

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
| pain126 | LQD | 0.35 | 0.12 | 0.31 | -0.14 | -1.28 / -1.28 / -0.75 / -1.05 | 1.00 | 0 |
| pain126 | HYG | 1.54 | 2.75 | 1.99 | 1.46 | -0.24 / 0.10 / -0.92 / -0.22 | 1.00 | 1 |
| p1_long_oi | LQD | 0.91 | 1.35 | 1.32 | 1.47 | -1.24 / -2.47 / 0.27 / 0.75 | 1.00 | 0 |
| p1_long_oi | HYG | 0.47 | 2.33 | 2.18 | 1.79 | -0.46 / 0.04 / -1.22 / -0.42 | 1.00 | 1 |
| p1_short_oi | LQD | 1.27 | 0.91 | 1.04 | 1.03 | 1.56 / 2.51 / 2.71 / 3.43 | 1.00 | 0 |
| p1_short_oi | HYG | -0.18 | 0.83 | 1.80 | 0.85 | 0.15 / -0.54 / -1.89 / -3.17 | 1.00 | 0 |
| gap126 | LQD | -0.07 | -0.76 | -1.83 | -1.54 | -0.70 / -0.94 / -0.00 / -1.67 | 1.00 | 0 |
| gap126 | HYG | 0.75 | 1.77 | 0.99 | 0.42 | -0.34 / -0.20 / -1.34 / -0.46 | 1.00 | 0 |
| gap_full | LQD | 0.84 | 0.91 | 0.85 | 1.05 | 1.08 / 1.75 / 2.28 / 2.18 | 1.00 | 0 |
| gap_full | HYG | 1.47 | 1.95 | 1.41 | 1.45 | -0.17 / -0.04 / -0.43 / 0.07 | 1.00 | 0 |
| gap_turn | LQD | 0.57 | 1.13 | 1.12 | 0.47 | -0.48 / 0.14 / 1.00 / 0.86 | 1.00 | 0 |
| gap_turn | HYG | 1.12 | 2.82 | 2.04 | 1.33 | -0.31 / 0.19 / -0.33 / 0.23 | 0.90 | 1 |
| p5_water | LQD | -0.82 | -1.33 | -1.49 | -1.94 | -1.52 / -1.47 / 0.27 / -2.46 | 1.00 | 0 |
| p5_water | HYG | -0.48 | -1.57 | -1.32 | -1.56 | -0.11 / 0.52 / 0.23 / -0.27 | 1.00 | 0 |
| flow13 | LQD | 2.00 | 1.89 | 1.91 | 1.91 | 0.74 / 0.77 / 1.34 / 1.97 | 1.00 | 1 |
| flow13 | HYG | 1.44 | 1.83 | -0.10 | 0.38 | -1.36 / -1.33 / -0.66 / -0.67 | 1.00 | 0 |
| i2_so | LQD | 1.69 | 1.69 | 2.01 | 1.39 | -0.23 / -0.24 / -0.08 / 0.24 | 1.00 | 0 |
| i2_so | HYG | 1.02 | 0.65 | -0.07 | 0.10 | 0.44 / 0.69 / 1.54 / 2.00 | 1.00 | 0 |
| i3_flow | LQD | 1.49 | 1.27 | 2.14 | 2.57 | -0.40 / -0.45 / -0.14 / -0.05 | 1.00 | 0 |
| i3_flow | HYG | 0.57 | 0.08 | -0.12 | 0.01 | 0.41 / 0.48 / 1.44 / 1.16 | 1.00 | 0 |
| i4_rule | LQD | -1.87 | -1.74 | -1.77 | -1.77 | -0.88 / -0.43 / -0.87 / -1.12 | 1.00 | 0 |
| i4_rule | HYG | -0.40 | -1.16 | 0.51 | 0.28 | 0.91 / 1.08 / 0.15 / -1.02 | 1.00 | 0 |
| i5_usd | LQD | 1.70 | 1.95 | 2.13 | 2.86 | -0.17 / 0.28 / 0.24 / 0.47 | 1.00 | 2 |
| i5_usd | HYG | 1.39 | 2.18 | 1.82 | 2.18 | 0.14 / 0.35 / 0.26 / 1.04 | 1.00 | 2 |
| i5_pct | LQD | 1.66 | 1.97 | 1.99 | 2.61 | 0.15 / 0.65 / 0.96 / 0.96 | 1.00 | 1 |
| i5_pct | HYG | 1.52 | 2.42 | 1.75 | 2.04 | -0.29 / -0.23 / -0.50 / 0.04 | 1.00 | 0 |
| i7_cont | LQD | 1.74 | 1.75 | 1.36 | 1.56 | -0.76 / -0.83 / -0.74 / -0.28 | 1.00 | 0 |
| i7_cont | HYG | 0.33 | 1.10 | 1.11 | 0.07 | -1.23 / -1.19 / -1.16 / -0.59 | 1.00 | 0 |
| i7_rev | LQD | -1.61 | -1.55 | -1.80 | -1.27 | 1.63 / 2.21 / 2.51 / 1.69 | 1.00 | 0 |
| i7_rev | HYG | -0.09 | -0.80 | -0.41 | 1.45 | 2.08 / 2.38 / 1.55 / 1.20 | 1.00 | 0 |
| i8_trend | LQD | -0.24 | 0.12 | 0.12 | -0.62 | 0.57 / -0.04 / -0.48 / -1.84 | 1.00 | 0 |
| i8_trend | HYG | -0.84 | -1.34 | -0.94 | -1.04 | 0.48 / 0.62 / 0.94 / 0.22 | 1.00 | 0 |
| si_ratio | LQD | -0.04 | 0.35 | -0.87 | -3.25 | 0.14 / -0.45 / -1.10 / -1.32 | 1.00 | 1 |
| si_ratio | HYG | 0.19 | 0.40 | 0.06 | -0.50 | 0.32 / -0.40 / -0.10 / -0.38 | 1.00 | 0 |
| si_chg | LQD | 0.12 | 0.73 | 0.84 | -0.86 | -0.61 / -1.36 / -1.10 / 0.01 | 1.00 | 0 |
| si_chg | HYG | 0.25 | 1.01 | 0.63 | -0.22 | 0.25 / -0.53 / 0.23 / -0.23 | 1.00 | 0 |
| si_i2 | LQD | 0.07 | 0.62 | 0.03 | -1.51 | -0.74 / -0.18 / -0.80 / 2.30 | 1.00 | 0 |
| si_i2 | HYG | 0.00 | 0.13 | -0.41 | -0.75 | 0.36 / 0.41 / -0.81 / -1.29 | 1.00 | 0 |

Cross-section tests, long the top half and short the bottom half of the fund pool:

| Signal | Weeks | Holdout t | Development t | IG t | HY t | Holm p | Label |
|---|---|---|---|---|---|---|---|
| i7_cont_cs | 1 | -2.24 | -1.40 | -1.48 | -1.54 | 1.00 | suggestive |
| i7_cont_cs | 4 | -1.91 | -1.04 | -1.13 | -0.94 | 1.00 | no_evidence |
| i7_cont_cs | 13 | -0.43 | -0.32 | -0.59 | 0.70 | 1.00 | no_evidence |
| i7_cont_cs | 26 | 0.08 | 0.26 | -0.22 | 1.39 | 1.00 | no_evidence |
| i7_rev_cs | 1 | 0.91 | 0.82 | 0.77 | 1.72 | 1.00 | no_evidence |
| i7_rev_cs | 4 | 1.05 | 0.48 | 1.09 | 0.92 | 1.00 | no_evidence |
| i7_rev_cs | 13 | -1.22 | -0.84 | 0.09 | 0.50 | 1.00 | no_evidence |
| i7_rev_cs | 26 | -1.69 | -1.03 | -0.16 | -0.39 | 1.00 | no_evidence |
