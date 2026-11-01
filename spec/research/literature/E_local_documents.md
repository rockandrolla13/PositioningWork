# E. The user's own documents on positioning, ETF flows, RFQs and credit signals

Theme five of five. Written 2026-11-01. No web search. Nothing here was sent outside the laptop.

## 1. The answer first

1. **No local document tests positioning or pain on corporate bonds, credit ETFs, credit futures or CDX.** Every credit document is a framework, a spec, a chart pack or an equity result carried over by analogy. No document mentions a credit future.
2. **ContraFlow reports no evidence.** It is a framework with an assumed performance table. Its table is inconsistent with itself, and its flow decomposition does not add up. Do not cite it as support.
3. **The real evidence is thin and points to temporary pressure.** Dannhauser and Hoseinzade (2021) is the one peer-reviewed result on ETF pressure in bonds that I found in the folder. It finds extra spread widening of 8.5 to 11.3 bps for LQD bonds, and 4.0 to 14.8 bps per 1% of ETF pressure. The effect fades within about 4 months. It covers one episode, the 2013 Taper Tantrum.
4. **The RFQ data sits on the work machine, not here.** The specs assume one dealer's view of anonymous RFQs. They carry no client ID, so nobody's entry price can be tracked. A pain measure on RFQs can only be a proxy for the group of RFQs that dealer saw.
5. **Flow direction is unsettled across the user's own documents.** One group expects flow to continue, another expects it to reverse. The horizon may reconcile them. No document tests that on credit.

## 2. Scope and how far each document was read

**Count.** 42 documents are summarised below, plus the wiki pages in section 7. The Quant Credit folder holds 389 files. Section 11 lists what was left out and why.

**Read in full.**
- ContraFlow, DataDrivenFlowETF and the text of "Why Do ETF Flows Move Prices".
- Both anonymous RFQ specs and combined_strategies_data_requirements.csv.
- credit_bmi_v2, contraflowsimple and contraflowwithcomovement.
- All wiki concept pages named in the brief that exist.

**Read in part.**
- "Tactical Asset Allocation from ETF Flows": introduction, flow mechanics, anomalies, method and the main result tables. I did not read every segment rotation table.
- Dannhauser and Hoseinzade: abstract, introduction, key tables and conclusion.
- DB 2018 "When the World Goes Passive": summary and strategy sections.
- `rfq-clock-signals/main.md`: front matter, data section, clock section and side weights. I did not read every family.
- Each other document is marked with what I read.

**Not read.**
- The ETF Flow Risk-o-Meter report, because another agent covers it. A copy also sits in both zips.

**Archives.** I extracted the two named zips into a new scratch folder and treated them as data. Nothing was run. Both zips hold the same set of files, with 6 distinct titles.

**Marks on the files.** Several bank PDFs carry exclusive-use marks naming other people. This file does not reproduce those names or any analyst contact details. Treat the bank material as restricted. Keep this file inside the private folder.

## 3. ContraFlow: framework only

- **Path:** `/media/ak/10E1026C4FA6006E/GitRepos/ETFFlow/ContraFlow.pdf`, markdown in `ETFFlow/markdown/ContraFlow.md`
- **Type:** industry note, or possibly internal. The header says "Optiver Credit Team". I cannot confirm that authorship. The PDF metadata names no author, and the note has no references.
- **Date:** 13 August 2025.
- **Method:** a recipe. Measure ETF flow per bond, split it into four parts, risk-adjust it, rank it inside sector and rating buckets, go long outflows and short inflows, and apply neutrality limits.
- **Data:** none used. The note lists what would be needed: daily ETF holdings, TRACE and dealer prices, ratings, index compositions, amount outstanding and corporate actions.

**Plain verdict: it reports no evidence.** There is no sample, no backtest, no test statistic and no citation. Section 7.1 is headed "Historical Performance Metrics", but its table is labelled "Expected Value". The text says the figures come "based on the equity ETF contraflow strategy adaptation". The heading promises history and the table holds assumptions.

### Internal consistency checks, all from my own reading

1. **Performance table does not hold together.** It gives return of 4 to 6%, Sharpe of 0.8 to 1.2 and monthly volatility of 3 to 5%. Monthly volatility of 3 to 5% is 10.4 to 17.3% a year. That implies a Sharpe of 0.23 to 0.58, not 0.8 to 1.2. To reach the stated Sharpe, monthly volatility would need to be about 1.0 to 2.2%.
2. **Attribution has no source.** It assigns 40% of alpha to index reconstitution, 30% to credit migration, 20% to weight changes and 10% to allocation. The DB equity note gives Sharpe ratios of 0.82, 0.51 and 0.30 for three components. It has no credit migration component, so the 30% is unsupported.
3. **The decomposition is not an identity.** Equation 9 says total flow equals the sum of four parts. It fails in four ways:
   - Total flow uses a lookback of 90 to 180 days, while the parts use one period.
   - Even with one period, allocation plus weight flow double-counts the cross term, Δw times ΔAUM.
   - An index entrant has Δw equal to its full weight, so weight flow already holds it and index flow adds it again.
   - Credit flow is added on top with no sign rule. The magnitude α is undefined.
4. **Index exits are always zero.** Equation 11 multiplies by weight at time t. A bond that has left the index has zero weight at t, so its exit flow is zero. That is the case the strategy most needs.
5. **Flow is contaminated by price.** Weight times AUM is a market value, so a rally looks like an inflow. ΔAUM includes returns, so allocation flow is not net new money. The signal may therefore carry a mechanical short-momentum exposure. DB avoids this by using shares outstanding for allocation.
6. **Short leg is broken by a percentile slip.** Algorithm 3 takes the top ⌊n × P_high⌋ bonds as shorts. With P_high at the stated 90th percentile, that is the top 90% of the bucket. It overlaps the long leg. Equations 26 and 27 also compare a rank to a percentile.
7. **Execution undoes the signal.** Section 6.2 shorts corporate bond ETFs for short exposure and buys ETFs for illiquid longs. An ETF holds the whole basket, so it carries no bond-level signal. It also holds the outflow bonds meant to be long.
8. **"Arbitrage" and "sustainable" are asserted.** Neither is shown. The note never discusses transaction costs or capacity. It has only a turnover limit, set at 50% a month.
9. **Timing is mixed.** The algorithm is called daily, the lookback is 90 to 180 days, and rebalancing is at month end. Pseudocode uses 90 days.
10. **Mechanism ignores how bond ETFs work.** My own comment: "forced buying" assumes full replication. Dannhauser and Hoseinzade discuss representative sampling and manager discretion over redemption baskets, which weakens a bond-by-bond reading.

**What it means for us.** Use it only as a checklist of data fields and neutrality controls. The usable idea is the equity decomposition behind it, done correctly. Section 4.1 gives the correct form.

## 4. Flow evidence

### 4.1 Why Do ETF Flows Move Prices?

- **Path:** `ETFFlow/Why Do ETF Flows Move Prices.pdf`. A duplicate sits in Quant Credit.
- **Type:** bank research, Deutsche Bank Quantitative Strategy.
- **Date:** 9 May 2019.
- **Method:** each month, sort Russell 3000 stocks into deciles within sector on six-month ETF flow. Go long the largest outflows and short the largest inflows, equal weight and dollar neutral. Flow is the change in dollars held by ETFs scaled by market cap.
- **Data:** Compustat, S&P, Russell, Axioma, IHS Markit. January 2006 to December 2018. Equities only.
- **Findings:**
  - Total flow long-short Sharpe is 1.29.
  - Index reconstitution alone gives 0.82, weight reconstitution 0.51 and allocation 0.30.
  - Flow variance shares are 29% allocation, 45% index and 25% weight.
  - Weight reconstitution reached 39% of variance in the last two years, as non-cap-weighted ETFs grew to close to 14% of ETF assets.
- **Limits:**
  - Backtested. The report's general disclaimer says performance excludes costs unless stated.
  - Footnote 2 says short-term allocation effects were not examined. So the low allocation Sharpe holds only at the six-month window.
  - The conclusion warns that performance depends on assets tracking the strategy. That is a crowding warning.
- **The useful part is the formula.** On page 3, allocation flow is the prior ownership share times the change in shares outstanding. Reconstitution flow is shares outstanding times the change in ownership share. The two sum exactly. The index and weight cases are mutually exclusive, keyed on prior weight or current weight being zero.
- **For us:** a bond version should use par held over par outstanding, which removes price. ETF allocation flow would use shares outstanding. Everything about predictive power is equity evidence until tested.

### 4.2 What Happens When the World Goes Passive?

- **Path:** inside both zips as `378375ed_ea78_4ddf_9411_dbdd5362ff06_604.pdf`.
- **Type:** bank research, Deutsche Bank. **Date:** 16 July 2018.
- **Method:** the same sort on 12-month flow, plus an event study around index changes.
- **Data:** proprietary ETF holdings for Russell 3000. January 2006 to December 2017. 387,225 firm-months.
- **Findings:**
  - Long-short Sharpe is 1.28, and 1.67 since January 2009.
  - Return before 2009, when ETFs were small, was -3%.
  - $1 grows to $3.48 in the largest-outflow decile and to $1.40 in the largest-inflow decile.
  - The chart labels Sharpe of 1.28, 1.16 and 0.20. By position these match total, reconstitution and allocation flow, so treat that mapping as my reading.
  - Information coefficient lasts about five months. Average holding is about four months.
  - In the event study, large positive flow lags by 9% (t = 1.81) and large negative flow leads by 11% (t = 2.36) over the next year. The report calls both "reliable", but 1.81 is weak.
  - Return differences start after the third month.
- **For us:** the horizon is months, not days. The short-side weakness dominates, which is hard to harvest in bonds.

### 4.3 Data-Driven Trade Flow Decomposition

- **Path:** `ETFFlow/DataDrivenFlowETF.pdf`
- **Type:** peer-reviewed conference paper, ICAIF 2025, ACM. **Date:** November 2025.
- **Method:** 16 features for each trade, counting trades and notional by direction, market and timing around the trade. PCA, then k-means++ on a 14-day sliding window. Conditional order imbalances are turned into factor-mimicking portfolios, orthogonal to Fama-French five, momentum and order imbalance.
- **Data:** LOBSTER NASDAQ trades, SPY and constituents, 2018 to 2021. Calibration on 2017. Returns from CRSP.
- **Findings:**
  - Best Sharpe is 1.91 (K = 2, cluster 1).
  - Only 2 of the 20 cluster portfolios are significant after Bonferroni correction: 1.91 at 1% and 1.52 at 5%.
  - Calibrated neighbourhood is 707 microseconds. Five components explain over 90% of variance.
  - Lag-1 autocorrelation of order imbalance is 0.276.
  - The paper reports no transaction cost result. It also says it did not run a GRS test.
- **For us:** a 707 microsecond window has no meaning in bonds. RFQ timestamps may be whole seconds. Only the principle transfers: flow near the ETF and flow in the basket may carry different information. Family F06 in the RFQ clock paper already adapts the rule-based version.

### 4.4 The Unintended Consequences of Corporate Bond ETFs

- **Path:** `Quant Credit/Research Platform/hhab031.pdf`
- **Type:** peer-reviewed, Review of Financial Studies, advance access March 2021.
- **Method:** three same-issuer comparisons of yield spread changes during the Taper Tantrum. The first is LQD inclusion. The second is a trade-based ETF selling pressure measure. The third is a hypothetical arbitrage exposure from fund weights. Issuer fixed effects are used.
- **Data:** ETF and mutual fund holdings and flows, CRSP, TRACE. Episode runs 21 May to 18 September 2013. Monthly outcomes run August 2013 to May 2014.
- **Findings:**
  - ETF flow volatility is 1.4 percentage points higher than active mutual funds, a 37% increase.
  - ETF flow-performance sensitivity is more than double that of mutual funds. The authors read this as positive feedback trading.
  - LQD shares outstanding fell 22.9%. End-of-day discounts reached 87 bps, yet average daily deviation was 0.1 bps.
  - LQD bonds widened 11.3 bps more in August and 8.5 bps more in September than same-issuer non-LQD bonds. That is 10.1% and 7.6% of the pre-episode spread.
  - The difference is insignificant after November.
  - In the trade-based setting, a 1% rise in pressure adds 4.0 bps a month after the episode, with a price effect as high as 20.35 bps at peak. In the arbitrage setting, it adds 14.8 bps.
  - The authors find ETF outflows pass through to bond selling one for one.
- **Limits:** one episode. The authors also note that in COVID the APs let ETFs trade at large discounts for long periods.
- **For us:**
  - This is the strongest local support for a pressure-then-reversal story in bonds.
  - It supports measuring pressure from ETF redemption and from fund weights.
  - It suggests holding horizons of months. A 10-day label would see only the pressure phase.
  - It warns that stress can sit in the ETF discount rather than in the bonds. A pain measure on ETF holders may be cleaner than one on bonds.

### 4.5 Tactical Asset Allocation from ETF Flows

- **Path:** `Quant Credit/Research Platform/Tactical Asset Allocation (TAA) from ETF Flows.pdf`
- **Type:** bank research, Deutsche Bank. **Date:** 14 May 2014.
- **Method:**
  - Net cash flow is the change in shares outstanding times NAV. Shares outstanding carry a one-day lag in practice.
  - Cumulative flow is scaled to AUM.
  - The score is the slope of a regression through the origin times the R² of the fitted line. So only steep and steady flow scores high.
  - Allocate by positive scores, and go to cash when all are negative.
- **Data:** US-listed long-only ETFs, 2007 to Q1 2014, Bloomberg and FactSet.
- **Findings:**
  - The quarterly asset class rotation returned 9.82% with 9.97% volatility, Sharpe 0.99, drawdown -21.6%. Two momentum comparators had Sharpe 0.59 and 0.74.
  - A related table gives Sharpe 1.11 against 0.42 for 60/40 and 0.35 for 50/30/20.
  - The report excludes costs and says their effect should not be large.
  - The authors say the approach "comes more from experience" than from quant method.
- **Flow anomalies it lists, which matter for us:**
  - Create-to-lend looks like an inflow but is bearish.
  - Create or redeem to cover looks like an outflow but ends a bearish view.
  - Rebalancing produces an inflow then a matching outflow around index dates.
  - Model trading produces lumps.
- **For us:**
  - The sign is flow continuation, which is opposite to contraflow. The level and horizon differ: asset class and months, against single security and six to twelve months.
  - Create-to-lend matters for HYG and LQD, which are shorted as hedges. Raw ETF flow can have the wrong sign, so short interest should be checked alongside it.
  - The slope-times-R² idea is a cheap steady-flow filter.

### 4.6 Related bank and academic items, read in part

| Document | Path under Quant Credit | Type, date | What I read and found | Meaning for us |
|---|---|---|---|---|
| The Flow Whisperer, June and August 2016 | zips, `0900b8c08b37dc81`, `0900b8c08b7e5e5b` | Bank, monthly | Headers only. Live portfolios since 14 May 2014. Monthly recommendations list IG and HY sleeves | A live record may exist. I did not extract it |
| US ETF Insights, EFRoM portfolios | `Research Platform/0900b8c08b403162.pdf` | Bank, 9 June 2016 | Header only. Uses the signal another agent covers | Pass to the EFRoM review |
| Happy birthday reversion | zips, `341b683e` | Bank, 22 March 2022 | Header only. Equity residual reversal | Not relevant |
| Arbitrage Comovement (Shim) | `ssrn-3287912.pdf` | Working paper, 29 May 2020 | Abstract. Stocks comove with an ETF by weight and price impact, not fundamentals. Over-reaction follows for high-sensitivity stocks | Equity evidence. Likely origin of the user's Λ term |
| ETF flows and the index effect (Howard) | `Research Platform/ssrn-4875607.pdf` | Working paper, June 2024 | Abstract. Australian natural experiment. Index-addition abnormal return rose 5.86%, from 2.37% to 8.23% | Equity evidence that ETF flow causes index effects |
| ETF Activity and Informational Efficiency (Glosten et al.) | `ssrn-2846157.pdf` | Paper, 19 June 2019 | Title page only | Listed for completeness |
| Hidden liquidity, Pan dissertation | `The Trading Dynamics of Corporate Bonds and Bond ETFs.pdf` | PhD thesis, May 2024 | Abstract. Bond ETFs show more hidden and dark trading than equity ETFs | Lit ETF volume understates demand. Signed ETF volume is weak |
| Developments in credit market liquidity | `Research Platform/citi-developments-in-credit-market-liquidity-fimsa-011118.pdf` | Bank slides to SEC FIMSAC, 11 January 2018 | Partly read. Top 50 stocks about 60,430 trades a day at about $19,728. Top 50 IG about 23 a day and HY about 16, at about $1.7mn. Credit needs discretionary capital. RFQ sits between streamed quotes and negotiated trades | Why stock-style flow windows fail. Figures read from chart text |

### 4.7 The user's own ETF flow notes

| Document | Path under Quant Credit | Date | Content | Consistency and use |
|---|---|---|---|---|
| Fixed-Income ETF-Flow (Contra)flow | `Research Platform/contraflowsimple.pdf` | 10 June 2025 | Six-month par flow per bond, duration-adjusted version, allocation and reconstitution split, decile long-short inside rating and sector | Spec only, no results. "Theorem 1" is stated without proof, and it fails. The flow includes price change, while the parts hold only P × ΔQ. The revaluation term is missing |
| Adding the arbitrage comovement effects | `Research Platform/contraflowwithcomovement.pdf`, also `a62ec896...pdf` | 10 June 2025 | Adds a term for premium, concentration and price impact. Seven hypotheses | Spec only, no results. It correctly rejects its own multiplicative form and moves to a signed premium term. It lists its own weaknesses well: 10+ parameters, stale prices, holdings lag. Its turnover figures are unsourced |
| Xantium business plan | `61444f23-caee-47ed-9bb0-ecd48e95c54b.pdf` | 11 April 2024 | ETF basis, create-to-lend, block trades, CDS index against ETF, index vol against ETF vol | Plan, no results. Assumes ETF flows have medium-term momentum, which sits against contraflow |

## 5. RFQ specs: what data the user expects

### 5.1 The two anonymous specs

- **Paths:** `Quant Credit/anonymous_rfq_alpha_prediction_only_spec.md`, and `anonymous_rfq_alpha_feature_research_spec_from_quantcraft.md`. A copy of the second is in `MechanicalAlpha`.
- **Type:** the user's own specs. **Date:** file dates are 24 August 2026 by timestamp. No results.
- **Viewpoint:** a single dealer who answers RFQs. The specs say "your quote" and "your current responder horizon". Client identity is absent by design. Client toxicity and fill prediction are excluded as targets.

**RFQ fields assumed.**

| Field | Symbol | Status in the spec |
|---|---|---|
| RFQ ID | `rfq_id` | Required in prediction spec |
| Timestamp | `t` | Required |
| Bond ID, ISIN or internal | `i` | Required |
| Side, dealer perspective | `side_t` | Required. +1 means the client sells to the dealer |
| Size, notional or quantity | `size_t` | Required |
| Venue | `venue_t` | Preferred |
| Protocol: single, list, firm, indicative | `protocol_t` | Preferred |
| The dealer's own quote | `Q_t` | Optional |
| Fill flag | `fill_t` | Optional |
| Number of dealers asked | `n_dealers_t` | Optional |

**Bond fields assumed.**
- Required: fair value `FV` marked at or before RFQ time, spread duration, issuer, sector, rating, maturity.
- Preferred: spread (OAS, G-spread or z-spread), clean price, rate duration, liquidity score, ADV or typical RFQ size.

**Public factor vector.** CDX IG and HY, Treasury 2, 5 and 10 year, LQD, HYG, JNK, issuer equity, VIX, MOVE. ETF premium or discount is used if available. News, sentiment and event flags are optional.

**Targets.**
- Fair value return, spread-implied return `-D × ΔS`, and return net of factors.
- Horizons are 30 minutes, 2 hours, 1, 3, 5 and 10 days. The prediction spec emphasises 5 days.

**Rules.**
- Rolling features use strictly earlier RFQs.
- Validation is time-blocked, with an embargo at least as long as the horizon.
- Buckets run from ISIN through issuer and sector × rating × maturity, up to venue, liquidity and nearest-neighbour sets.
- Clocks are calendar, RFQ count, notional and EWMA.

**Prediction spec features (24).**
- Flow level: `FlowAlpha` as -(q - 0.5) with q an EWMA sell share, `FlowLogOddsAlpha`, `CottonFlowAlpha` scaled by local win-curve width.
- Activity: `IntensityZ`, `SignedIntensityAlpha`, `SignedNotionalAlpha`, `SizeFlowGap`, `RepeatAlpha`, `DormantWakeupAlpha`.
- Spillover: `IssuerFlowAlpha`, `NeighborFlowAlpha`, `GroupFlowAlpha`, `CurveFlowAlpha`.
- State: `LiquidityConditionedFlowAlpha`, `FlowAccelerationAlpha`, `FlowReversalAlpha` as exhaustion of extreme flow.
- Value and cross-asset: `RVAlpha`, `FlowConfirmedRV`, `CrossAssetLead`, `ETFAlpha`.
- Markouts and events: `MarkoutMomentum`, `MarkoutReversalAlpha`, `EventFlowAlpha`, `EventIntensityAlpha`.

**Feature research spec.** It adds 20 operators adapted from DB Quantcraft papers:
- clock seasonality
- lag-vantage-horizon triplets
- variance-ratio and low-vol reversal
- risk-appetite conditioned reversal
- issuer curve PCA momentum and curve-to-level spillover
- curve residuals, and carry and roll adjustment
- news and sentiment
- covariance regimes
- flow confirmation and exhaustion

The spec admits the source papers are not RFQ papers.

**Checks from my reading.** The Cotton algebra, the sign logic and the exhaustion formula are consistent. These points are not:

1. **Look-ahead in `MarkoutMomentum`.** It averages `FV(u + h0) - FV(u)` over all u < t. For u later than t - h0, the return uses marks after t. The spec's rules do not catch this. The sum must stop at u + h0 ≤ t.
2. **Cotton needs fields called optional.** Win-curve width needs `Q_t` and `fill_t`. Section 35 names Cotton flow among the likely best features. Section 2.1 calls these fields optional, and the RFQ clock spec does not confirm the meaning of the quote column.
3. **"Cotton" has no citation.** I found no source in these specs or the wiki. Treat it as unverified naming.
4. **Horizon too short for the evidence.** The maximum label is 10 days. The bond evidence reverts over about four months, and the equity signal lasts about five months. The specs would see only the pressure phase and could call it "information alpha".
5. **The default sign assumes informed flow.** `FlowAlpha` assumes sellers are right. Contraflow and pain ideas assume the opposite. The experiments do test both, which is good, but the name fixes a prior.
6. **Labels are marks, not trades.** The target is change in fair value. Neither spec has a cost-based promotion gate. The prediction spec mentions turnover only. The Dickerson warning on bid-ask bounce applies, per the wiki note.
7. **No stock measure.** Every feature is a flow over a window. Nothing builds an inventory or an entry price. So neither spec contains a positioning or pain feature as such.

### 5.2 Predictive Flow Signals on RFQ Clocks

- **Path:** `GitRepos/MechanicalAlpha/rfq-clock-signals/main.md` and `spec.md`
- **Type:** the user's own design document with an implementation spec. **Date:** spec generated 28 September 2026. `main.pdf` runs to 122 pages.
- **Content:** 20 families and 51 named signals on six clocks: count, trade, volume, risk, price move and calendar. It states plainly: "There are no results here." It also states that no family has a direct source.
- **Useful construction:** side weights measured from past data, so that a normal buy and sell mix reads as zero.

**Best local description of the actual data.** It names two tables on the work computer, `rfq_events` and `credit_event_bars`.

| Field | Column | Status |
|---|---|---|
| Arrival time | `inquiry_timestamp`, read as seconds | Available, precision open |
| Bond | `isin` | Available |
| Customer side | `inquiry_side`, flipped to customer view | Available |
| Requested notional | `inquiry_quantity` | Available |
| Requested risk | notional × CR01 or DV01 dated before the RFQ | Available |
| Executed flag | `traded_flag` | Available |
| Execution price | `price` where traded | Available |
| Lifecycle ID | `rfq_lifecycle_id` | Available |
| Best quote | `quote_price_at_initiation` | Meaning unknown |
| Executed quantity | not read by the producer | Open |
| Dealers asked, dealers answered, firm-up, latency | none | **Not available** |
| Composite mid and spread | `fv_price`, bar `mid_hat`, `spread_hat` | Open |
| Issuer, sector, rating, duration bucket | unknown table | Open |

The spec's memory target is sized at 8 million RFQs. I treat that as a design figure, not a data count.

**Three conflicts for the lead to settle.**

1. **Sign.** The anonymous specs use dealer view, with +1 for client sells. The RFQ clock spec uses customer view, with +1 for customer buys. POE uses +1 for market maker buys. Mixing these flips every signal.
2. **Availability.** `ForcedFlowCredit/docs/04-data.md` and `LLMWikiGeneration/research/FEATURE-SPEC-forced-sale-pressure.md` both say RFQ data is not available. The RFQ clock spec says it exists on the work computer. The likely reading is that these documents describe different machines. The laptop has no RFQ data that I found.
3. **Dealer count.** The specs and `MechanicalAlpha/event_table.md` list number of dealers. The RFQ clock spec says it is not available. So competition controls may not be computable.

**Why this matters for pain.** The document itself warns that one dealer's fills show that dealer's success rate, not market fills. It also warns that anonymous data cannot fully remove repeat requests. So:

- An RFQ panel is a sample of inquiries that one dealer received. It is not market flow.
- An inquiry is not a trade. Marín et al. report a 5.6% hit rate in their dealer's data, though on government bonds.
- With no client ID, a holder's entry price cannot be built. The best proxy is a signed, notional-weighted average RFQ price per bond or issuer, marked to fair value. That is a new measure with no local support.
- TRACE gives prints, and Enhanced TRACE gives buy and sell flags. Pairing TRACE with RFQs, as POE sketches, is the route to a market-wide check.

### 5.3 Other RFQ documents

| Document | Path | Type, date | Method, data, findings | Meaning for us |
|---|---|---|---|---|
| Behaviour of dealers and clients (Fermanian, Guéant, Pu) | `Quant Credit/The behavior of dealers and clients on the European.pdf` | Paper, arXiv version March 2017 | Model of quotes and client reservation prices. Bloomberg FIT RFQs to one large European dealer, 2014 to 2015. 209,069 buy and 272,189 sell, so 43.4% buys. Requested dealers number two to six. A requested dealer answers about 40% of the time | Only local RFQ data with counts. Side mix is not 50/50 |
| Mid-price estimation (Guéant, Pu) | `Quant Credit/Mid-price estimation for European corporate bonds.pdf` | Paper, March 2019 | Abstract and framework. Particle filter on D2C trades, D2D trades and traded-away RFQs, which are censored observations | A fair value route for marks. Traded-away RFQs carry information |
| Causal Interventions in MD2C (Marín et al.) | `Quant Credit/2506.18147v1.pdf` | arXiv, June 2025 | Graph model of the RFQ process. BBVA European government bond RFQs: 102,437 with 5,738 hits. No client variable used. Client intent, such as price discovery, is a hidden confounder | Inquiries mix real demand and price discovery |
| RL for Corporate Bond Trading (Atkins et al.) | `Quant Credit/2406.12983v1.pdf` | Working paper, 2024 | Abstract only. Data-driven quoting | Quoting, not our topic |
| Algorithmic Pricing, Factor Flow, Fill Curves | `Quant Credit/mainPOE.pdf` | Internal-style framework, May 2025, group author | Factor flow sums β × side × notional over a window, per category and side. Uses OWIC and BWIC categories, closed RFQs and TRACE-RFQ pairing. No results | **Closest local object to a positioning stock.** It is signed risk accumulated by factor and bucket |
| Unified Framework: Factor Flow and Fill Curves | `Quant Credit/FillCurveV2.pdf` | Draft, 30 May 2025 | Same ideas, marked as a draft with mistakes and not for distribution | Do not redistribute. Use `mainPOE` as the reference |
| Dynamic Risk-Adaptive Pricing | `Quant Credit/MainCLVersionMay28th.pdf` | Framework, 28 May 2025 | Summary only | Same family |
| ETF create and redeem RFQ simulation | `Quant Credit/CapArb/etf_rfq_simulation.py` | The user's code | First 80 of 462 lines, not run. Synthetic: 20 bonds, 3 ETFs, 5 days, random inputs | No evidence |
| Detecting toxic flow (Cartea et al.) | `Quant Credit/Detecting toxic flow.pdf` | Peer-reviewed, Quantitative Finance 2026 | Abstract. FX broker data, online neural network | Method only |

## 6. Credit signals and positioning data

### 6.1 credit_bmi_v2

- **Path:** `Quant Credit/credit_bmi_v2.pdf`, with a near-duplicate `credit_bmi_v2 (1).pdf`.
- **Type:** methodology note, no author, likely the user's own. **Date:** 9 June 2026.
- **Method:** rebuilds the Morgan Stanley Credit-BMI. Point-in-time factors, expanding z-scores mapped to -10 to +10, shrinkage weights, horizons of 1 week, 1 month and 3 months. Adds PC1 of spread changes, a crisis gate on momentum, a dead zone at ±1 and a drawdown stop. Validation is walk-forward and costed, with IG and HY separate.
- **Data:** none used. **Results:** none. Table 2 is "expected" relevance.
- **Numbers quoted:** hit rates of 67% and 62% for the model and 55% and 51% for LIBOR-OIS, all attributed to source notes. I did not trace them to the Morgan Stanley report.
- **Positioning content:** none directly. Credit-ETF primary flows and TRACE bid-ask are "secondary, higher-noise confirmations". Sentiment flips sign at extreme z-scores.
- **Consistency issue:** the note says that as λ goes to 1, equation 3 collapses to equal weight. It actually gives weights proportional to each factor's correlation with the target. It equals equal weight only if those correlations are all the same.
- **For us:** a good design for gating and horizons. It gives the structure for any pain score.

### 6.2 Deutsche Bank Macro Credit Trades

- **Path:** `Quant Credit/Work_Quant (1)/1574b3c6_68dd_11eb_8fc9_3e217c25b0c2_604 (1).pdf`
- **Type:** bank research. **Date:** 1 March 2021.
- **Content:**
  - Figures 22 to 33 chart **CDS index positioning** for iTraxx Main, Crossover, Financials, CDX IG and CDX HY. Series are recent and full history, labelled "Net client positions", source Deutsche Bank and DTCC.
  - Compares CDS index, credit ETF and OIS moves.
  - LQD implied vol was 9.3, rank 94.4%. HYG was 9.8, rank 76.2%.
  - Refers to a monitor with CDS and TRS positioning and volumes.
- **Limits:** charts only, with no definition and no test.
- **For us:** this is the only local document with actual CDX positioning. It shows the approach: net client positions built from DTCC swap reports. The team should check what public DTCC data can reproduce. No entry prices or pain are given.

### 6.3 Deutsche Bank Investor Positioning and Flows

- **Path:** `Quant Credit/Work_Quant (1)/investor positioning 4th of march (1).pdf`, also `Investor Positioning 26th f Feb (1).pdf` and three `ChartPack` files in the same style.
- **Type:** bank research chart pack. **Date:** 5 March 2021. I did not check the ChartPack dates.
- **Findings from summary pages:**
  - CTA bond allocation at the 4th percentile.
  - Credit funds lost $2.4bn in the week, with IG -$0.9bn, HY -$1.3bn and EM -$0.1bn.
  - Bond funds saw outflows of over $270bn after the taper tantrum.
- **Limits:** descriptive. Credit appears as fund flows only.
- **For us:** a template for a multi-investor dashboard. It does not offer a credit-specific CTA or leveraged position.

### 6.4 Forced flow and basket specs

| Document | Path under GitRepos | Type, date | Content | Meaning for us |
|---|---|---|---|---|
| ForcedFlowCredit | `ForcedFlowCredit/README.md`, `docs/00`, `01`, `04` | The user's spec. "Nothing has been measured" | Forced Sale Pressure = ownership share × exclusion probability. Primary event is the index minimum-maturity rule, not fallen angels. Warns on pull-to-par and on using holdings as of date with real lag. Notes that ETF-only ownership undercounts index funds | Best local design for a bond ownership measure. Uses par holdings. Ownership against illiquidity is its key test. Inherits the 1% misquote, see section 7 |
| Forced sale pressure feature | `LLMWikiGeneration/research/FEATURE-SPEC-forced-sale-pressure.md` | The user's spec, 9 August 2026 | Earlier form of the above | Same |
| Basket vs HY ETF kill test | `StatArbCredit/Docs/credit_rv_basket_vs_etf_spec_v0_1.md` | The user's spec | Does bond residual cheapness survive an ETF hedge and costs over 5, 10 and 20 days? Fields include bid-ask, ADV, quote age, ETF borrow | The right executability gate for any ETF or bond pain signal. Results not read |
| bond_alpha | `MechanicalAlpha/bond_alpha/README.md` | The user's scaffold | Tape fields `cusip, ts, price, par_volume, side_flag, contra_party_type`. Sources WRDS TRACE, FINRA public TRACE and synthetic. Public volumes capped at $5MM+ IG and $1MM+ HY | Size caps bias TRACE flow in public data |
| FlowCode | `FlowCode/spec/SPEC.md` | The user's spec | First 90 of 368 lines. Credit P&L, range position, retail imbalance using an equity sub-penny rule | Equity retail rule does not transfer |
| FundamentalQuantmental | `FundamentalQuantmental/README.md`, `research/combined_framework_spec.md` | The user's repo | Uses WRDS TRACE and Compustat for HY fundamentals. Grep shows no RFQ or positioning content | Holds TRACE panel code. Not a flow study |
| creditmacro | `creditmacro/docs/SPEC_AND_STATE.md` | The user's repo | Grep shows no RFQ or positioning match | None |
| Bridge note | `Quant Credit/credit_spread_stat_arb_architecture_bridge_v0_1.pdf` | Note, June 2026 | Grep only. Says effective volume may be inferred from RFQs and fill rates | Minor |

### 6.5 CDS and basis papers

These are in `Quant Credit/CapArb/`. I read title pages and abstracts only.

- **Kim, Li, Zhang, Journal of Empirical Finance 2016.** The residual CDS-bond basis negatively predicts bond excess returns, with 1.79% abnormal return at 20 days.
- **Choi, Shachar, Shin, Management Science 2019.** Dealer liquidity provision and the CDS-bond basis. Title only.
- **Others on capital structure arbitrage and CDS determinants.** Listed in section 11.

For us, the basis is a candidate stress measure alongside positioning. It is not a positioning measure. Dealer capacity links it to who can absorb flow. These should go to the CDX theme.

## 7. Wiki notes, traced back to source

Treat the wiki as notes. I checked its claims against the sources I could read. These do not survive.

1. **The "1% traded" claim is wrong in meaning.** `concepts/bond-liquidity`, `analyses/etf-contraflow-corporate-bonds` and `ForcedFlowCredit/docs/00-thesis.md` say about 1% of TRACE-eligible bonds traded on a given day in 2012. Fermanian et al., citing MarketAxess, say 38% of 37,000 bonds did not trade even once in 2012, and only 1% traded **every day**. Those are different facts. The cited source does not support "1% on a given day".
2. **The ContraFlow source page misdescribes the note.**
   - `sources/optiver-2025-corporate-bond-etf-contraflow` lists "Residual flows" as the fourth component. The note's fourth is credit migration.
   - It claims z-score normalisation and transaction cost considerations. The note has neither.
   - It lists "Index reconstitution flows have strongest predictive power" and "capacity-constrained" as key claims. The note assumes the first and never mentions the second.
   - "Optiver Internal Research" as venue is unconfirmed.
3. **`concepts/etf-flows` lists ContraFlow as key research.** It is not evidence.
4. **`analyses/etf-contraflow-corporate-bonds` has unsourced numbers.** Bid-ask of 50 to 200 bps and the "why index reconstitution dominates" list have no source. It says timing is predictable and also "harder to front-run", which pull against each other. It does correctly ask whether anyone has published bond contraflow results. Locally, nobody has.
5. **`concepts/rfq-markets` has unsourced numbers.** "Optimal: 3-5 dealers" and "about 1M ISINs" have no source I could find on the page. Do not cite them.
6. **`sources/chao-2019-etf-flows-prices` overstates one line.** It says allocation flows have "minimal systematic price impact". The report says allocation is weak but additive, with Sharpe 0.30, and did not test short horizons.
7. **Traced and correct:** the 29%, 45%, 25% split, Sharpe 1.29, 209,069 and 272,189 RFQs, the six-dealer limit and the censored traded-away treatment. The TAARSS description matches the 2014 report.
8. **Not traced, because I did not have the source open:**
   - `sources/dickerson-2024-bond-pitfalls`: reversal premium falls from 0.90% to about zero after correcting bid-ask bounce. This matters for any RFQ or TRACE reversal claim, so another agent should verify it.
   - `sources/huber-2026-information-flows-trading-networks`: larger insurer dealer networks earn about 7 bps a month around credit events.
   - `sources/ms-2018-04-16-credit-bmi-update`: score mapping and threshold rule.
   - `sources/kalev-2025-lietf-trading-behavior-during-u-s`: equity leveraged ETFs, not credit.
9. **Thin pages:** `etf-flow-anomalies`, `etf-flow-tactical-asset-allocation`, `etf-creation-redemption-arbitrage`, `dealer-networks` and `cds-momentum` are short stubs. `etf-creation-redemption-arbitrage` rests only on the user's Xantium plan. `disposition-effect` rests on an FX paper and a hedging book, so there is no credit evidence for it locally.

## 8. What this means by instrument

| Instrument | What the local documents support | What is missing |
|---|---|---|
| **Corporate bonds on RFQ** | Field list, side-weight baseline, anonymity limits, factor flow as a stock, Dannhauser for pressure and reversal in months | Any test. Holder entry prices. Market-wide flow. Dealer count. Labels beyond 10 days. A cost gate |
| **Credit ETFs** | Clean flow formula from shares outstanding and NAV. A one-day lag. Anomalies such as create-to-lend. Evidence of positive feedback and one-for-one pass-through. Holder pain can be approximated from flow and NAV, which is my inference | Any credit ETF test of pain. Short interest and premium data handling. Sector results |
| **Credit futures** | Nothing. No local document mentions them | Everything |
| **CDX and iTraxx** | DTCC net client position charts. CDS index against ETF comparison. Basis papers. Use as a public factor in RFQ specs | Definition of the DTCC measure. Any predictive test. Entry price logic |

**Practical reading for the lead.**

1. Build ETF holder pain first. It is the only version where flow, price and date are all public.
2. Use ETF flow only after screening create-to-lend and rebalance lumps.
3. Compare with the bond-level pressure in the Dannhauser form as a check on mechanism.
4. Test horizons out to at least six months.
5. Treat anything on RFQs as a work-machine task. Use bucket-level measures, because single-bond flow is sparse and one dealer's sample is biased.

## 9. Academic references these documents cite

All are **cited, not verified**. I did not check them against the originals, unless the row says the PDF is local.

| Reference | Cited in | Why it looks relevant |
|---|---|---|
| Ben-David, Franzoni, Moussawi, "Do ETFs Increase Volatility?", Journal of Finance | DB 2019, Dannhauser | ETF trading demand passing into underlying |
| Falato, Goldstein, Hortaçsu (2020), corporate bond funds in COVID | Dannhauser | Fund outflows and stress |
| Goldstein, Jiang, Ng (2017), corporate bond fund fragility | Dannhauser | Flow fragility |
| Cella, Ellul, Giannetti (2013) | Dannhauser | Investor horizons and price pressure |
| Manconi, Massa, Yasuda (2012) | Dannhauser | Forced selling across holders |
| Frazzini, Lamont, "Dumb Money" | DB 2018, DB 2019 | Flows predicting low returns |
| Glosten, Nallareddy, Zou, ETF activity and efficiency | DB 2019. PDF local, title read | ETF trading and information |
| Israeli, Lee, Sridharan (2017), dark side of ETFs | DB 2019 | ETF ownership and liquidity |
| Wermers, Xue (2015), intraday ETF trading | DB 2019 | Intraday ETF trading and volatility |
| Chao et al. (2018a, 2018b), Deutsche Bank | DB 2019. 2018a local, read in part | Origin of the contraflow measure |
| Lu, Reinert, Cucuringu (2024), trade co-occurrence, Quantitative Finance | Petit, RFQ clock | Basis of co-occurrence flow |
| Chordia, Subrahmanyam (2004), order imbalance and returns, JFE | Petit | Order imbalance predicts returns |
| Cont, Cucuringu, Zhang (2023), cross-impact of order flow imbalance | Petit | Cross-impact |
| Sitaru, Calinescu, Cucuringu (2023), order flow decomposition | Petit | Decomposed flow |
| Collin-Dufresne, Goldstein, Martin (2001) | credit_bmi_v2 | Spread changes and a common residual factor |
| Dickerson, Robotti, Rossetti (2024), bond strategy pitfalls | Wiki, ForcedFlowCredit | Bid-ask bounce and look-ahead |
| Bergault and Guéant, RFQ arrival rates and imbalance | RFQ clock paper | Side asymmetry in RFQ models |
| Andersen, Bondarenko (2013), order flow toxicity | RFQ clock paper | Volume-time one-sidedness |
| Huber, Watts, Zhu (2026), Journal of Accounting and Economics | Wiki | Dealer networks and informed trading |
| Shim (2020), Arbitrage Comovement | Local PDF, abstract read | Comovement from arbitrage |

## 10. Limits of this review

- Numbers from bank charts come from text extraction. Chart labels may be misaligned. I flagged the ones I was unsure of.
- I did not check bank reports for later corrections.
- The dates of the two anonymous specs come from file timestamps, which may not match when they were written.
- I searched many PDFs by keyword first. A document that uses different words could have been missed.
- `MechanicalAlpha` holds further alpha lists that I did not open: `Corporate_Bond_20_Alphas_Technical_REVIEWED.pdf`, `bond_alpha_factors.md`, `twenty_signals.md` and `ofi_feature_construction_reference.pdf`. They are likely worth a look for the RFQ theme.

## 11. Rest of the Quant Credit folder

The folder holds 389 files, with 310 PDFs converted including zip copies and excluding `FX Work`. Keyword scan covered RFQ, positioning, crowding, flows, CDX, CDS, TRACE, creation and redemption.

**Files with a problem.**
- `Research Platform/Global Rates Insights_ Filtering CFTC positioning data for a signal(1).pdf` is 286 bytes and is not a valid PDF. It would have been directly relevant. The user would need to re-download it.
- `credit_bmi_v2 (1).pdf` differs from `credit_bmi_v2.pdf` at byte level. I read only the main file, so the second may be another version.

**Not relevant to this theme, by title or data.**
- `combined_strategies_data_requirements.csv` and `strategies_data_requirements.csv`: lists of DB FX and macro models and Morgan Stanley screens. The frequency and fidelity columns are generic. Nothing on flows, RFQs or positioning. A "Risk Sentiment Variable" row names 11 barometers, without detail.
- `FX Work/`, `VRP-.../`, `Screening Models/`, `Factors/`, `Missing Papers/`.
- Most of `Work_Quant (1)/`, which is FX, rates and equity quant research.
- `signal_design.tex`, `full_signal_design_cleaned.tex`, `Research Platform/fixed_document.tex`: no match for the topic words.
- `Use Cases 1`, `Use Cases 2`, `SystematicCreditUseCases`: research platform use cases. CDX features as a spread input. "Positioning" means spread percentile, not investor positions.
- Other zips, listed but not extracted:
  - `Screening Models-...zip`: 14 files, matching the extracted folder by name.
  - `VRP-...zip`: 12 files, no topic names.
  - `Work_Quant (1)-...zip`: 135 files. Its topic names, such as the positioning and OFR papers, match the extracted folder.
  - `iCloud Photos (3).zip` and `(4).zip`: 378 and 2 entries, no topic names. I did not open them.
  - `Work_Quant (1)/portfoliostrat-...zip`: 1,408 files of a web application, with CDS pricer code and a `us_etfs.tsv`. No RFQ or positioning names.

**Possibly useful and not read beyond a header.**
- `Work_Quant (1)/IG & HY Strategy/19b1f580...pdf`: EM Debt Technicals Monitor, 2 March 2021, with "lightened positioning".
- `Work_Quant (1)/72d00fea...pdf`: CEEMEA weekly with positioning sections.
- `Research Platform/e10b5396...pdf`: BofA Flow Show, 29 January 2021, weekly flows including HY and IG.
- `Work_Quant (1)/OFRwp-19_04_cross-asset-market-order-flow-liquidity-and-price-discovery (1).pdf`: OFR working paper.
- `Work_Quant (1)/CASTELLOBRANCO_JONATHAS_01461378 (1).pdf`: MSc thesis on ETF market making.
- `CapArb/`: about 15 papers on CDS, equity and capital structure arbitrage.
- `The determinants of CDS spreads_ evidence from.pdf` and `s11147-017-9134-6.pdf`, which appear to be the same paper by word count.
- `Measuring changes in credit risk_ The case of CDS event studies.pdf`.
