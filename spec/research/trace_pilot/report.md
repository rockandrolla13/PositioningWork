# TRACE customer flow pilot: report

Saved by the main session from the pilot agent's two messages, because the harness refused report files from that subagent. Full tables are in `results.json`. Rerun with `run_all.sh`, with `TRACE_PILOT_WORK` set to a folder outside the project.

## The answer

**No. Customer flow in single bonds does not show a usable lead on spreads in this sample.**

- None of the 48 planned tests passes. The smallest Holm-adjusted p is 0.67.
- At bond level the sample has fair power for small effects, about 0.2 to 1 bp per SD of flow, against a weekly adjusted spread move SD of 12 bp. So a large bond-level lead on these bonds is unlikely.
- At issuer level and at 13 weeks it is too thin to say: 12 issuers, and at most 4 independent 13-week windows in the holdout.
- No steady accumulation: a bond-month's flow trend beats its own reshuffled order 11.1% of the time, against 10% by chance.
- This covers 12 large issuers, mostly tech. It says nothing about the bond market as a whole.

Closest to a signal: one-week continuation. Buying over the past 4 weeks goes with tighter spreads next week, -0.13 bp per SD over time and -0.21 bp across bonds, with the same sign in development. Primary p is 0.09 and 0.11. Top flow quintile tightens 51.3% against a 50.0% base rate. Median customer buy and sell yields differ by 3.2 bp, far above this effect.

## Data findings

1. Primary allocations are in this TRACE. First-5-day customer buys reach a median 107% of the tranche, and hold 44% of lifetime customer volume. Net flow after day 5 is near zero, so a 5-day mask looks sufficient.
2. The side convention is proven: dealer sale to contra C is a customer buy.
3. ATS trades (contra T) behave like inter-dealer trades. Affiliates (A) sit between C and D.
4. The lot ledger covers only about 2% of amount issued, so it does not describe holders.

| Contra | Bond-days | Mean price gap, S minus B | Median | Days S above B |
|---|---|---|---|---|
| C | 113,288 | +0.245 | +0.142 | 88.1% |
| A | 32,424 | +0.097 | +0.063 | 67.9% |
| T | 50,368 | -0.012 | 0.000 | 9.4% |
| D (control) | 142,284 | +0.003 | 0.000 | 27.9% |

## Sample and gaps

- 308 bonds, 12 issuers, 123 weeks, 28,338 bond-weeks. Lost: JPM (structured notes), MS and VBLF (no yields).
- Maturity and coupon from OpenFIGI: 353 of 369 bonds. Amount from SEC term sheets: 245 of 369 bonds, 71% of rows. The rest use a weak volume scale (AMZN, MSFT and RIG most).
- Amount means amount issued, not outstanding. Quantity is inferred to be par.
- Not point-in-time. Sizes are uncapped, so a live user could not see these flows. No status, modifier or dissemination field, so cancels and agency trades can't be removed. The TRACE product is unconfirmed.
- Spread check: panel median weekly change correlates 0.85 with ICE IG OAS change over 100 weeks.
- Cleaning: 23 customer trades above $250 million dropped. Exact duplicates are 197,618 of 1.42 million customer rows. The rule choice changes no verdict.

## Results by test

- **T0, sanity.** Flow does not persist: median autocorrelation -0.04, -0.03, +0.01 at lags 1, 4, 13. April 2025 shows no customer rush.
- **T1, lead.** 36 rows, holdout 2024-10-01 to 2025-09-30. None passes. One placebo row is clear (p 0.006) but the issuer bootstrap gives 0.113 on the same row, and I trust the bootstrap more.
- **T2, benchmarks.** 0 of 36 beat both. Flow explains at most 1.3% of variance in every bond and issuer row. The spread level bar is partly mechanical at 13 weeks.
- **T3, pain.** Nothing passes. Best is pain share against later selling, raw p 0.014, Holm 0.67: higher pain goes with slightly less selling, and controls remove it (t -0.7). Pain against spread is probably mechanical.
- **M4.** Not built. 123 weeks is too short for 156 and 209 week windows.
- **T4, same-week pressure.** About -0.55 bp per 1% of amount, and it does not reverse. Later slopes keep the same sign, so this leans away from pure liquidity pressure, but it is not established.

## What breaks

Twelve issuers. Few clusters, with errors floored once after results. A 29% volume-scale share. G-spread style measure, not OAS. Customer does not mean holder. Short-sample fixed effects can bias slopes, mostly at 13 weeks. Not point-in-time.

## Recipe worth keeping

No measure is worth keeping as a predictor. Do not build M2 or M3 into a monitor from this data. Keep M1 as a description only:

1. Drop prices outside 1 to 300 and trades above $250 million.
2. Keep contra C. Keep A on a separate line. Leave T and D out.
3. Customer buy = dealer sale. Check the S price exceeds the B price on most bond-days.
4. Zero flow for the first 5 trading days of a bond's life and after any reopening.
5. Sum over 20 trading days. Divide by amount, and note amount issued can overstate amount outstanding.
6. Read spreads from the mean of customer buy and sell yields, or inter-dealer if one side is missing. Never a one-sided yield.
7. State that it is not point-in-time, and that sizes above $5 million were hidden in real time.

To settle the open part, the sample needs far more issuers, more years, and amount outstanding from a reference file.
