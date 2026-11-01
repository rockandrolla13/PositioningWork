# TRACE customer flow pilot: test plan

Written on 2026-11-01, before any test ran.
At this point I had looked at data availability and data quality only: columns, null shares, duplicate rows, largest trades, and contra party documentation.
I had computed no flow signal, no ledger, no spread change and no forward relation.
Anything added after a result was seen goes in "Changes after results" at the end, with the reason.

## Question

Does cumulative customer flow in single bonds show accumulation or decumulation?
Does that flow lead spread changes over 1, 4 and 13 weeks?
A clear "no" or "too thin to say" is a valid result.

## Scope limits that hold for every sentence in the report

1. `trace` is a 15-issuer panel. This study uses at most 12 issuers once JPM, MS and VBLF drop out (see below). These issuers are large and mostly tech. No result describes the bond market.
2. TRACE here is not point-in-time. Execution time is not public availability. Sizes are uncapped here, while public TRACE caps them at $5 million in real time. So nothing here shows what a live user could have seen.
3. The table has no trade status, modifier or dissemination flag. Cancels, corrections and agency flags cannot be checked directly.
4. No trade or placement follows from this work.

## Data rules

- Raw TRACE rows and bond-day aggregates stay outside the project folder. The work folder comes from `TRACE_PILOT_WORK`. Only statistics reach `results.json`.
- Excluded issuers: JPM (structured notes), NULL `company_symbol` (data defect), MS and VBLF (every customer yield is NULL, so no spread exists). MS and VBLF stay in the flow descriptives only.
- Contra party meaning comes from the FINRA historic file layout, saved in `raw/docs/`. C = customer. D = inter-dealer. A = non-member affiliate. T = ATS (alternative trading system). Results are shown for C alone (primary), C+A, and C+A+T.
- Inter-dealer double counts are removed by `NOT (cntra_mp_id='D' AND rpt_side_cd='B')`. Inter-dealer rows are used only as a yield reference and as a control in the sign proof.
- Sign: for contra C, dealer sale S = customer buy, and dealer buy B = customer sell. This must pass test T00 before any other test counts.
- Quantity: `entrd_vol_qt` is assumed to be par in dollars. The warehouse does not record units. I check this against SEC deal sizes.

### Cleaning, fixed in advance

1. Drop prices outside (1, 300].
2. Drop any customer trade above $250 million par. These are issuer or error prints. The largest rows match the sizes of whole tranches, such as $2.5 billion dealer buys at about the reoffer price.
3. Exact duplicate rows on bond, timestamp, price, yield, size, side and contra: remove extras at $1 million and above, keep extras below. Small repeats look like bunched retail allocations. Large repeats look like double reports. Sensitivity runs: remove all, and remove none.
4. New-issue window: drop customer flow for the first 5 trading days of a bond's life and the first 5 trading days after any SEC-dated reopening. T0 measures whether this matters. A bond's first print counts as its birth only if it comes after the first 5 trading days of the panel.
5. Yield: cast to number, keep 0.1 to 40, and drop a print more than 200 bp from the bond's centred 11-day median yield. This filter sees neighbouring days. It is cleaning, it never touches flow, and its effect is measured by the share of rows removed.
6. Remaining maturity must be at least 1 year. Floaters drop out.

### Bond reference data (gaps in marketdb)

marketdb holds no maturity, coupon or amount outstanding.
- Maturity and coupon: OpenFIGI tickers such as "AAPL 3 11/13/27", looked up by CUSIP.
- Amount outstanding: SEC full-text search for the CUSIP in FWP and 424B filings, reading the tranche size. Reopenings add up across distinct filing months. Tenders, calls and buybacks are not seen, so this is amount issued, an upper bound on amount outstanding. Bonds issued before 2001, or with no parsed filing, have no value.
- Flow scale for bonds without a value: the bond's own trailing 26-week average weekly customer volume, multiplied by the panel median ratio of amount to that volume. This uses past data only. Results are reported on all bonds and on the bonds with a filing value.

### Spread

- Spread = daily yield minus the FRED constant-maturity Treasury, interpolated linearly to the bond's remaining maturity. The series run 1 month to 30 years. Same date.
- `yld_pt` may be a yield to call for premium bonds, so this is a G-spread style measure and not an OAS.
- Level on a day, to limit bid-ask bounce: the mean of the volume-weighted customer buy yield and the volume-weighted customer sell yield, when both exist. Otherwise the volume-weighted inter-dealer yield. Otherwise missing. One-sided customer yields never set a level.
- Weekly level: the last valid daily level in the Friday-ending week, at most 2 trading days old.

### Timing

- Weeks end on Friday. A flow signal for week t uses trades up to Thursday of week t.
- The forward spread change starts at the Friday level of week t and ends at the Friday level h weeks later. A one-day gap separates the last flow from the first level, so a print in the signal never sets the starting level.
- Forward spread changes never cross the boundary between development and holdout. A development row must end on or before 2024-09-30.

### Market adjustment

For bond b in maturity bucket k and week t, adjusted change = own change minus the median change of bonds in bucket k from all other issuers.
Buckets, by remaining maturity: 1-3, 3-7, 7-15 and 15+ years.
BAMLC0A0CM, the ICE IG OAS, is a check only. FRED limits it to about 3 years.

## Sample split

- Development: 2023-05-30 to 2024-09-30. Set-up, sign checks, standard deviations for scaling.
- **Holdout: 2024-10-01 to 2025-09-30, fixed now. All verdicts rest on this window.** It has 52 weeks. So 13-week results have at most 4 independent windows.
- The first 13 weeks of flow form a warm-up for the 13-week flow and ledger measures.

## Measures

- **M1** net customer buying in par divided by amount outstanding. Tested as flow over the past 4 weeks (M1_4) and past 13 weeks (M1_13). The level since the start is reported in T0 only, because it depends on the start date and has a unit root by construction.
- **M2** `posmon.indicators.taarss` on cumulative M1 in percent of amount outstanding, per calendar month, zero at prior month-end. Published per bond for the last complete month, and it enters from the first Friday after month-end. Needs 10 trading days with any trade in the month. Days without customer flow carry the cumulative level.
- **M3** lot ledger with `posmon.build_ledger` semantics, pro rata removal, one lot per day of positive net flow, entry at that day's volume-weighted customer spread. A wider current spread means a customer lot is under water. Pain share = open par under water / open par. Pain depth = open-weighted mean of (current spread - entry) on under-water lots, in bp. Unmatched sells have no lot, because the starting position is unknown. Coverage = open par / amount outstanding. A faster incremental version is used for speed and must match `build_ledger` on sample bonds to within 1e-6.
- **M4** sentiment index and scaled DB position need a 156 or 209 week window. The panel has about 122 weeks. So M4 is not built, and the report says so.
- Levels: bond, issuer (amount-weighted across bonds) and issuer x bucket. The "bucket" level is the maturity bucket pooled across issuers.

## Standardisation

Each signal is divided by its pooled standard deviation on development data, so coefficients read as bp per 1 development SD.

## Tests

### T00. Sign proof (gate)

For each bond-day with both sides: VWAP(rpt side S) minus VWAP(rpt side B), for each contra. Same for yields.
Pass rule: for contra C, mean price gap above zero, yield gap below zero, share of bond-days with the expected sign above 60%, and all 14 issuers with data have the same sign in price.
Also reported: the gap for A, T and D. D is a control, where both sides describe one trade.

### T0. Descriptive sanity (no p-values, not in the family)

- Issuer flow in stated events: April 2025, the new issue months, and the largest flow months.
- Flow persistence: lag-1, lag-4 and lag-13 autocorrelation of weekly flow, by bond, with a placebo from randomly signing the flow.
- New issue contamination: customer flow in the first 5 days of a bond's life against amount issued, on both sides.
- Size distribution, duplicates and effect of each cleaning rule.

### T1. Flow leads spread changes

Designs:
- **Time series (TS):** adjusted spread change on signal with unit fixed effects.
- **Cross section (CS):** raw spread change on signal with date and bucket fixed effects, so only differences within a week and bucket count.

Levels: bond, issuer, bucket. Horizons: 1, 4, 13 weeks. Signals: M1_4 and M2.
At the bucket level CS means four buckets a week. It is reported but counts as low power from the start.

### T2. Benchmarks

Each T1 row is repeated with past 4-week spread change and spread level as controls. Each benchmark is also run alone.
A signal beats a benchmark if the signal stays beyond |t| = 2 with controls, and if its within-R-squared exceeds that of each benchmark run alone.
Market or sector moves enter through the adjusted spread change in TS and date fixed effects in CS.

### T3. Pain

Bond level. Pain share and pain depth against later adjusted spread change (TS), and against later net customer selling over the same horizon. Horizons: 1, 4, 13 weeks. Bond fixed effects. Ledger warm-up 26 weeks. Coverage below 0.5% of amount outstanding drops out. The panel with SEC amounts only is the main sample if SEC coverage exceeds half the bonds. Otherwise all bonds use the fallback scale.

### T4. Contemporaneous pressure against lead

Same-week flow (Monday to Friday) on same-week spread change (prior Friday to this Friday), against next-week and next 4-week changes. Bond and issuer level.
Claim "pressure larger than lead" needs |contemporaneous| above |lead| with a pairs bootstrap by issuer whose 95% interval on the difference excludes zero.
Reversal check: the sign of the contemporaneous slope and the lead slope.
Bounce check: repeat with inter-dealer yield levels only. This one matters, because customer buys print at the offer.

## Inference

- All panels: two-way clustering by issuer and by date block of h weeks (CR1 with G-1 degrees of freedom where G = min clusters), plus a restricted wild cluster bootstrap by issuer with Webb six-point weights and 1,999 draws.
- Issuer and bucket panels use the same method. Bucket series with four clusters use Driscoll-Kraay Newey-West on date moments with lag max(4, ceil(1.5 h)) and t(df = N/h - 2), since four clusters cannot support a cluster method.
- **Primary p = the larger of the cluster t p-value and the wild bootstrap p-value.** Naive errors are never reported as evidence.
- Number of issuers is 12, which is few. The wild bootstrap is there for this reason. It can still over-reject when one issuer dominates, so I also report leave-one-issuer-out ranges.
- Effective sample: weeks / h, reported beside each row. Also issuers with the same sign out of 12.
- Power: the smallest effect detectable at 80% power, 2.8 x SE, in bp per SD, for each row.

## Multiple-testing family

Holm across the holdout primary p-values of:
- T1: 2 signals x 3 horizons x 3 levels x 2 designs = 36 tests.
- T3: 2 pain measures x 3 horizons x 2 targets = 12 tests.

Total 48. A test that cannot run counts as p = 1.
T2 and T4 are read against their own rules and stay outside the family. T1 on alternative contra sets and cleaning runs are reported but stay outside.

## Placebos

Run on the bond-level T1 and T3 holdout rows.
1. **Circular shift:** each bond's signal shifts by its own random offset of at least 13 weeks inside its holdout span. 499 draws. The placebo p is the share of draws with |b| at or above the actual one.
2. **Shuffle:** week labels permuted within issuer. 499 draws.

## Success rule for a predictive claim

A signal counts as leading only if all of these hold in the holdout:
1. Holm-adjusted p below 0.05.
2. Same sign in development.
3. Circular shift placebo p below 0.05.
4. Beyond |t| = 2 with T2 controls.
5. At least 9 of 12 issuers show the same sign.
6. Sign unchanged under C+A and C+A+T, and with SEC-amount bonds only.

If rule 1 fails but raw p is below 0.05 and the sign matches, the label is "suggestive, not established".
Otherwise the label is "no evidence".
If the standard error is so large that the smallest detectable effect exceeds 25% of that horizon's SD of adjusted spread change, the label adds "too thin to say".

## Hit rates

Top and bottom development-quintile signals against the sign of the later adjusted spread change, always beside the base rate of that sign.

## Refinements made after writing the code, before any test ran

These came from writing the panel code. No forward relation had been computed.

1. Level dates vary by bond, so "flow up to Thursday" would let a Thursday print set a Thursday level. The flow signal now ends one trading day before each bond's own level day. M1_4 is the prior 20 trading days and M1_13 the prior 65. This enforces the one-day gap in every row.
2. At the bucket level, the same-bucket adjustment would remove everything. So the bucket-level adjusted change is the bucket change minus the equal-weighted mean across buckets in that week.
3. The wild bootstrap does not re-estimate fixed effects in each draw. The slope in a draw uses x after the fixed effects are removed, so it is unaffected, and only the residual used for its standard error is approximate.
4. Sign proof result, seen before the plan's tests: contra T has a median gap of zero, like D, which supports treating ATS trades as dealer-like. The plan still reports C+A+T, as stated.

## Changes after results

The first full run gave a smallest Holm p of 0.29. No row passed. I then made these changes, and the family stayed at the same 48 tests.

1. **Two-way variance floor.** Some t-values looked too large, for example 21 with controls. The two-way formula subtracts a term and can fall below either one-way variance when date blocks are few. The variance is now the largest of the two-way and the two one-way values. This only makes errors larger. Smallest Holm p moved from 0.29 to 0.67.
2. **M2 entry date.** The code entered M2 at a bond's first level after month-end. The plan says the first Friday after month-end. Stragglers formed noisy issuer rows from one bond. The code now follows the plan, and a bond with no level in that week has no M2 for that month.
3. **Added descriptives, no p-values in the family:** net flow by day since issue, each bond-month's trend against its own reshuffle, and the largest bond-day share of the largest weeks.
4. **Added robustness, outside the family:** within-week rank signals, and M1_13 at bond level. M1_13 was named under Measures but left out of the family count, so it is reported here only.
5. **T3 sample.** SEC amounts cover more than half the bonds, so T3 used SEC-amount bonds as the plan's rule says.

Not done from the plan: T0 matches flow to dated events only for April 2025 and new issues. marketdb holds no ratings or news, so I did not test ratings changes or issuer news.
