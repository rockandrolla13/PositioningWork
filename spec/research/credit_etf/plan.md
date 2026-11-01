# Credit ETF positioning: test plan

Written on 2026-11-01, before any test ran. At this point I had looked at data availability only.
No signal, ledger reading or forward return had been computed.
Anything added after a result was seen goes in the section "Changes after results" at the end, with the reason.

## Question

Do the positioning and Pain Monitor methods in `positioning_spec.tex` work on US credit ETFs?
Each method gets a verdict: transfers as is, transfers with changes, or does not transfer.

## Working mapping under test

| Futures idea | ETF analogue | Doubt to test |
|---|---|---|
| Open interest | Shares outstanding | Net of shorts, moved by authorised participants |
| Daily position change | Creations minus redemptions | Reported with a lag, driven by arbitrage |
| Entry at VWAP | NAV or VWAP on the creation day | Secondary trades change holders with no share change |
| Long minus short | Shares outstanding = gross long - short interest | Short interest is twice a month and lagged |
| DV01 | CS01 = NAV x spread duration / 10,000 per share | Duration history is thin |
| Market move | Spread change | ICE BofA OAS has only 3 years on FRED |

## Data rules

1. Shares outstanding and NAV dated d are published on d+1 at the earliest. A signal on Friday uses only rows dated Thursday or earlier.
2. The forward return starts at the Friday close. So a one-day gap separates the last input from the first return.
3. FINRA short interest is usable from settlement date + 10 business days. FINRA's schedule is about 8 to 9, so this is conservative.
4. CFTC data follows the spec: usable from the Friday after the Tuesday report.
5. All returns use dividend-adjusted prices. The ledger uses a total-return price, so a distribution is not a loss.
6. Duration points are taken from archived fund files where they exist. Before the first point I carry the first point backward. This touches the hedge ratio only, never a signal, and it is flagged.
7. CRSP raw rows stay out of this folder. Only statistics from CRSP go in `results.json`.
8. FRED limits the ICE BofA OAS to 3 years. I respect that limit, and I do not pull older vintages. Long-history targets use the ETF excess return and Moody's BAA10Y.

## Targets

- `xr(h)`: ETF total return from close over h weeks, minus a duration-matched Treasury return built from FRED par yields.
- `ds_impl(h)`: implied spread change in bp, equal to -(xr - carry) / spread duration.
- `ds_baa(h)`: change in BAA10Y in bp, for IG only.
- `ds_oas(h)`: change in ICE BofA OAS in bp, available from 2023-10-31 only. This window is too short to decide anything, so it is reported as a check.
- Horizons: 1, 4, 13 and 26 weeks.

## Sample split

- **Development: first available date to 2016-12-31.** Parameters, z-score means and z-score standard deviations come from here.
- **Holdout: 2017-01-01 to the last common date.** All verdicts rest on this window.
- **Short interest has a later start (2017-12-29).** Its development window runs to 2021-12-31, and its holdout runs from 2022-01-01.
- Primary funds: LQD for IG and HYG for HY.
- Replication funds, outside the Holm family: JNK, USIG, IGIB, IGSB, USHY.

## Inference rules, fixed in advance

- Weekly regression: y(t,h) = a + b z(t) + e, with z standardised on development data only.
- Newey-West lag = max(4, ceil(1.5 h)). This is always at least the overlap.
- p-values use a t distribution with degrees of freedom equal to effective N - 2. Effective N = N / h.
- Circular block bootstrap with block = max(8, 2h) weeks and 2,000 draws gives a 95% interval for b.
- Hit rates use top and bottom quintile thresholds fixed on development data. Each hit rate sits beside its base rate.
- Holm correction runs across the whole family of tests: every signal x horizon x primary fund.
- Benchmarks: buy and hold, plain 26-week momentum, spread level, and the past 26-week spread change. They are reported beside the signals and sit outside the family.

## Success rule for a predictive claim

A signal counts as predictive only if all of these hold:
1. Holm-adjusted p below 0.05 in the holdout.
2. The bootstrap 95% interval excludes zero.
3. The sign in the holdout matches the sign in development.
4. The replication fund in the same group has the same sign.
5. The slope stays beyond |t| = 2 with momentum and spread level as controls.

If 1 fails but the raw p is below 0.05 and the sign matches, the label is "suggestive, not established".
Otherwise the label is "no evidence".

## Tests

### C1. Lot ledger and pain share for LQD and HYG (JNK as replication)

Build the ledger from daily share changes with `posmon.build_ledger`, rule `pro_rata`, 126 trading days, on total-return NAV.

Pass rule: at each stress trough the pain share is at least 0.75 and the mean depth of pain is in the top decile of the fund's own history.
Stress troughs checked: 2020-03-23, 2022-10-20 and 2008-12-12 (HYG, JNK), 2015-2016 HY 2016-02-11, 2013-09-05 (LQD), and 2025-04-08.
The ledger's own `check()` must also pass at every date.

### C2. Do pain, depth and crowding predict `xr` or spread change at 1, 4, 13, 26 weeks?

Signals:
- `pain126`: P2 `share_in_pain` over 126 days.
- `p1_long_oi`: P1 long offside share of shares outstanding over 30 days.
- `p1_short_oi`: P1 short offside share of shares outstanding over 30 days.
- `gap126`: mean open-lot cost divided by price, minus 1, over 126 days.
- `gap_full`: the same on a since-inception ledger.
- `gap_turn`: the same on a reference price weighted by volume turnover. This tests the case where secondary trading resets cost basis.
- `p5_water`: P5 signed over or under water, as a percent of the 30-row mean.
- `flow13`: 13-week flow as a share of shares outstanding.
- `i2_so`: I2 on log shares outstanding, 156 weeks.
- `i3_flow`: I3 on 26-week flow, 209 weeks.
- `i4_rule`: I4 one-standard-deviation rule on CS01-weighted 13-week flow, using development mean and sd.

### C3. I5 flow filter

Recipe under test: keep a weekly share change only when it goes with the market (redeeming as spreads widen, creating as spreads tighten).
Weight it by CS01. Regress the weekly spread change on it over the fixed window 2008-01-01 to 2016-12-31.
Sum the residual over 26 weeks. Divide by the in-sample weekly residual sd x sqrt(26). A large positive score means spreads widened more than positioning implies, so a tightening bias.

Variants:
- `i5_usd`: dollar CS01, through `posmon.filtered_change` and `posmon.filtered_residual` unchanged.
- `i5_pct`: the same with flow scaled by shares outstanding, because fund assets grew many times over.

Benchmark: plain past 26-week spread change.

Pass rule, on top of the general rule:
- In the holdout the I5 score has a stronger forward correlation than the benchmark at 26 weeks.
- The score has |t| above 2 with the benchmark as a control.
- Each hit rate beats its base rate by at least 5 points.

### C4. Flow continuation against reversal (I7)

- `i7_cont`: four-week creations minus redemptions over their sum.
- `i7_rev`: minus the mean z-score of shares outstanding over 4, 8 and 13 weeks, over 126-day return volatility.

Run each one as a time series on LQD and HYG. Then run each as a cross section across the ETF pool, long the top half and short the bottom half on a volatility-scaled excess return.
Rule: continuation means a positive slope on `i7_cont`. Reversal means a positive slope on `i7_rev`. The general success rule applies.

I8 trend (`posmon.cta.cta_signal`) goes in this block, against plain momentum. The minute-level imbalance half of I8 runs only if time remains, on 2023 onward.

### C5. Short interest and options

- `si_ratio`: short interest / (shares outstanding + short interest). This is the ETF form of I1.
- `si_chg`: change in `si_ratio` over about 13 weeks.
- `si_i2`: I2 on `si_ratio`, 156 weeks.

P1 classification check: over each FINRA interval, compare the short change P1 attributes with the true change in short interest. Pass rule: rank correlation at least 0.3 and sign agreement at least 60%.

I6 needs per-contract open interest and delta. Run it only if the data can be had with no spending. Otherwise report the quoted cost and mark it not tested.

### C6. Do IG and HY behave alike?

For each signal and horizon, test equal slopes for LQD and HYG with a two-equation Newey-West Wald test.
Decision rule: pool only if equality is not rejected at 10% in at least 75% of cases and the slopes share a sign in at least 75% of cases. Otherwise run the groups separately.

### Mechanism checks, reported whether or not they help

- M1: timing. Correlate share change at t with premium and return at t-2 to t+1, on development data only. The offset chosen here sets the entry date for the ledger.
- M2: how much of daily flow lagged premium explains.
- M3: primary flow as a share of secondary volume.
- M4: does pain predict further redemptions over 4 weeks? This tests whether unleveraged holders act on pain.
- M5: share of absolute flow in the last 3 days of a month, against the 14% an even spread gives.
- M6: sensitivity of pain share to removal rule (FIFO, lowest price first), entry price (NAV, close, Databento VWAP from 2023), and total return against raw price.
- M7: implied spread against OAS, correlation on the 3-year overlap.
- M8: true daily creations versus the secondary tape, using VWAP and close against NAV in March 2020.

### CFTC

Bloomberg IG and HY credit futures (codes 221606 and 221605) on CBOT have reports from 2026 only.
Run I1 and P2 once as a reading. No predictive test is possible, and I will say so.
Cboe iBoxx futures: search the CFTC names and report the result.

## Costs

ETF half-spread comes from the marketdb book, 2023 onward. Before that I assume the same value and say so.
Hedge assumption: 1 bp of price per side. Short-side borrow assumption: 1% a year for HYG and JNK, and 0.5% for LQD.
Any signal that passes gets a net-of-cost long and short test beside buy and hold.

## Verdict rule

- **Transfers as is:** the formula runs unchanged on the mapped data, the inputs mean what the method assumes, and any predictive claim passes the success rule.
- **Transfers with changes:** it works once changed as stated, as a description or a predictor. The report states which.
- **Does not transfer:** the mapped input does not mean what the method needs, or the data cannot support it, or the test shows no evidence of the claim that makes the method useful.

## Changes after results

Data-source changes, made before any predictive test ran:
- The iShares `.ajax` download link now answers with the product page. I found the page's own JSON feed, which holds the same daily NAV, ex-dividend and share history. It replaces the file named in the brief.
- Rule 6 first named archived fund files as the duration source. The issuer's holdings feed honours past dates, so duration and yield to worst now come from dated holdings. JNK has no such feed and borrows HYG's path.
- Spread level is holdings yield to worst minus the matched Treasury, rolled forward by the implied spread change.

Bug fixed after the first full run:
- A 126-day ledger can drain to rounding noise. That produced absurd pain shares and a false |t| above 5 for LQD. The spec says an empty ledger gives no reading, so such weeks now give no reading.

Checks added after results, in `post_hoc` in `results.json`. They can only weaken a claim and they change no label:
- Sub-periods 2017-2021 and 2022-2026, and the holdout without 2020, for each labelled result and for the benchmarks.
- A placebo that shifts forward returns by a random offset, to count how many raw p below 5% chance gives across the correlated family.
- The synthetic hedge against the issuer's own rate-hedged funds LQDH and HYGH.
- The share of the fund the 126-day ledger covers.
- The true change in short interest against the change in shares outstanding.
- P2 ledgers on FINRA dates, one on short interest and one on gross long.
- A closer look at BAA10Y, in `06_baa_check.py`. BAA10Y was a secondary target in this plan, outside the family. When the report first counted its cells, 30 of 76 LQD cells had |t| above 2. That needed explaining before I could write "no spread effect".
