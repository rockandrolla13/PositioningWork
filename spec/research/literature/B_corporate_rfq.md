# B. Corporate bonds traded by RFQ and over the counter

Literature review, theme B of five. Compiled 2026-11-01.

## The answer first

1. Flow can predict bond returns, but only some flow. Order flow from well-connected clients predicted returns for 30 days. Order flow from poorly connected clients reversed within 30 days (Czech and Pinter, entry 1).
2. Under-water positions matter, but the measured evidence is for insurers. Their losses against book value change how they trade and how much a flow shock moves spreads (Fang, entry 2, and Ellul and colleagues, entry 5).
3. Noise can create false signals. Measurement error in trade prices and one-sided return filters inflate bond factor results. Most of 108 published signals lose significance after correction (Dickerson and colleagues, entry 4).

The biggest gap: I found no paper that tests whether RFQ inquiry imbalance by client, side and size predicts bond returns. That test looks open.

## How to read each entry

- **Tier 1** is a peer-reviewed journal. **Tier 2** is a working paper or preprint. **Tier 3** is industry or official material.
- **Verified** names the record I checked. "Crossref" means the DOI record matched authors, title and year.
- **Read** says what I actually read. "Abstract" means only the abstract. "Part text" means I read the abstract and passages of the paper, not all of it.
- **Means for us** is my own inference, not a finding of the paper.
- "Not read" under data or method means the part I read did not state it.

## Ranked entries (30)

### Flow and information

**1. Czech, R. and Pinter, G. (2020). Informed Trading and the Dynamics of Client-Dealer Connections in Corporate Bond Markets. Bank of England Staff Working Paper 895.**
- DOI: 10.2139/ssrn.3744325. Stable URL: https://ideas.repec.org/p/boe/boeewp/0895.html
- Verified: Crossref, RePEc, and the PDF in the LSE CFM discussion paper series. Tier 2. Read: part text of the December 2020 version.
- Data: FCA ZEN transaction reports with both counterparty identities and a buyer-seller flag. UK sample, September 2011 to December 2017, 2,533,529 observations, about 2,900 bonds. A separate dataset extends the test to COVID-19.
- Method: same-client, same-day comparisons across bonds. Long-short deciles on client order flow.
- Finding: one more dealer raises client performance by about 3 bps over five days. The top-minus-bottom spread on high-connection flow is 6.8 bps at 5 days, 10.3 at 10 and 17.1 at 30. Low-connection flow predicts returns for 5 to 10 days, then fully reverses by 30.
- Means for us: split RFQ flow by client breadth. Do not treat all client flow as one signal. Count how many dealers a client uses, which a single dealer sees only in part.

**2. Fang, C. (2024, draft April 2025). Unrealized Trading Gains. Working paper.**
- DOI: 10.2139/ssrn.4973722. Draft: https://www.hec.ca/finance/Fichier/Fang_Unrealized.pdf
- Verified: Crossref and the author's draft. Tier 2. Read: part text of the April 2025 draft.
- Data: NAIC Schedule D holdings (Part 1) and transactions (Parts 3 and 4) with book values. Crisis samples are the global financial crisis and February to April 2020.
- Method: compares insurers trading the same bond at the same time. Flow-induced trading (FIT) from mutual fund outflows is the demand shock. Unrealized loss equals book value minus market value.
- Finding: flow-induced selling of 1% of amount outstanding raises the yield spread by 0.747 percentage points. One standard deviation more peer unrealized loss raises the remaining effect by 103%. The bond's own unrealized loss was not statistically important in that regression. The estimated shadow cost of regulatory capital in crises is $0.81 on average.
- Means for us: this is the best template for "pain". It measures loss against an entry level and links it to trading and price impact. For insurers the entry level is book value, not last trade price. Losses on similar bonds can matter more than losses on the bond itself.

**3. Geilen, M. (2026). Corporate Bond Dealers and Price Discovery. Working paper.**
- DOI: 10.2139/ssrn.6781998 (a second version is 10.2139/ssrn.6990060).
- Verified: Crossref for both versions. Tier 2. Read: abstract.
- Data: dealer axes, meaning non-binding indicative buy and sell interests. Sample dates not read.
- Method: return predictability from axes, with controls for inventory and liquidity.
- Finding: bonds with high dealer buy interest earn higher later excess returns, and bonds with high sell interest underperform. The effect is strongest in high yield. Returns persist rather than reverse, which the author reads as information, not inventory pressure.
- Means for us: dealer interest and client interest are different signals. Test RFQ flow alongside axes where we can get axes. This paper is new and has not been through peer review.

**4. Dickerson, A., Robotti, C. and Rossetti, G. (2026). The Corporate Bond Factor Replication Crisis. Working paper.**
- DOI: 10.2139/ssrn.6088966. Related earlier title: Noisy Prices and Return-based Anomalies in Corporate Bonds, 10.2139/ssrn.4575879.
- Verified: Crossref for both. Tier 2. Read: abstract of the 2026 paper. For the 2023 paper I read only a search-result summary, because the Crossref record held no abstract and the PDF did not download.
- Data: TRACE transaction prices. A "factor zoo" of 108 signals in nine clusters.
- Method: corrects a correlated errors-in-variables bias, where price error enters both the signal and the return. Also removes one-sided return filtering that uses future information.
- Finding: the majority of documented factors lose significant bond CAPM alpha after correction. The authors release error-corrected TRACE data and code through Open Bond Asset Pricing.
- Means for us: never build the entry level and the forward return from the same noisy print. Skip a period between signal and return. Use benchmark prices for marks. Backtest with the corrected data as well as our own.

**5. Ellul, A., Jotikasthira, C., Lundblad, C. and Wang, Y. (2015). Is Historical Cost Accounting a Panacea? Market Stress, Incentive Distortions, and Gains Trading. Journal of Finance 70(6), 2489-2538.**
- DOI: 10.1111/jofi.12357. Verified: Crossref. Tier 1. Read: abstract.
- Data: US insurers during the financial crisis. Method: exploits accounting differences across life and property-casualty insurers and across states.
- Finding: insurers with less market value recognition sell fewer downgraded asset-backed securities. To repair capital they instead sell unrelated bonds with high unrealized gains, and that passes shocks across markets.
- Means for us: stress can lead an investor to sell winners, not losers. So a pain index built only on losers can miss the selling. Track gains as well as losses by client type.

**6. Jurkatis, S., Schrimpf, A., Todorov, K. and Vause, N. (2023). Relationship Discounts in Corporate Bond Trading. Bank of England Staff Working Paper 1,049.**
- DOI: 10.2139/ssrn.4301416. PDF: https://www.bankofengland.co.uk/-/media/boe/files/working-paper/2023/relationship-discounts-in-corporate-bond-trading.pdf
- Verified: Crossref and the Bank of England PDF. Tier 2. Read: part text.
- Data: MiFID II transaction reports held by the FCA, from January 2018, with both counterparties named. Insurers account for less than 9% of volume in the sample.
- Method: regressions of costs on relationship strength. Clients count as informed if their past trades, over a 180-day window and scaled by volatility, predict returns.
- Finding: the top 1% of relationship clients pay costs 51% below the median client. Liquidity provision and client profitability explain the discount. The authors find no evidence that information extraction from order flow does.
- Means for us: the informed-client score is directly usable on RFQ data. Client level also includes a price effect, so control for relationship when we use the level as an entry price.

**7. Kargar, M., Lester, B., Plante, S. and Weill, P.-O. (2023). Sequential Search for Corporate Bonds. NBER Working Paper 31904.**
- DOI: 10.3386/w31904. Also Philadelphia Fed WP 25-08, 10.21799/frbp.wp.2025.08.
- Verified: Crossref and NBER PDF. Tier 2. Read: part text.
- Data: all MarketAxess inquiries and dealer replies, January 3, 2017 to March 31, 2021, matched to TRACE.
- Method: follows repeated customer attempts after a failed inquiry.
- Finding: inquiries fail about 30% of the time. Failure is about 14% for the most connected customers on a fairly liquid purchase and over 50% for the least connected on harder trades. A transaction takes two to three days to complete after a failed attempt.
- Means for us: this is the closest published use of RFQ records. A single order can appear as several inquiries, so we must merge repeats before we count flow. Failed inquiries carry unfilled demand that TRACE cannot see.

**8. Cai, F., Han, S., Li, D. and Li, Y. (2019). Institutional Herding and Its Price Impact: Evidence from the Corporate Bond Market. Journal of Financial Economics 131(1), 139-167.**
- DOI: 10.1016/j.jfineco.2018.07.012. Verified: Crossref and RePEc. Tier 1. Read: abstract and the data section of the FEDS 2016-091 version.
- Data: Thomson Reuters Lipper eMAXX quarterly holdings, 1998:Q3 to 2014:Q3.
- Method: herding measures from changes in holdings, with later price effects.
- Finding: herding is much higher than in equities. Sell herding is stronger and more persistent than buy herding. Buy herding helps price discovery. Sell herding causes large but temporary price distortions, mostly in speculative-grade, small and illiquid bonds and in the crisis.
- Means for us: expect asymmetry. Build buy and sell crowding as two signals. Crowded selling in illiquid high yield looks like a contrarian setup, not a momentum one.

**9. Anand, A., Jotikasthira, C. and Venkataraman, K. (2021). Mutual Fund Trading Style and Bond Market Fragility. Review of Financial Studies 34(6), 2993-3044.**
- DOI: 10.1093/rfs/hhaa120. Verified: Crossref. Tier 1. Read: abstract.
- Data: corporate bond mutual funds. Sample dates not read. Method: classifies each fund by how it responds to signals of large dealer inventories.
- Finding: style is persistent and most funds demand liquidity. A subset earns positive alpha by supplying liquidity during sustained customer selling, and those funds keep their style under outflows and stress.
- Means for us: classify clients by behaviour, not just sector. A client's history of supplying or demanding liquidity tells us how to read its flow.

**10. Friewald, N. and Nagler, F. (2024). Dealer Inventory and the Cross-Section of Corporate Bond Returns. Economics Letters 239, 111710.**
- DOI: 10.1016/j.econlet.2024.111710. Also CEPR DP 19399, 10.2139/ssrn.4755158.
- Verified: RePEc record and the Bocconi repository, which both name the authors and DOI. Tier 1. Read: abstract.
- Data: US corporate bonds. Sample dates not read. Method: a bond-level measure of exposure to inventory risk, sorted into portfolios.
- Finding: the high-minus-low portfolio earns a risk-adjusted 21 bps per week. The premium rises in crises, when hedging supply is low, and with credit risk.
- Means for us: customer selling becomes dealer inventory, so one-sided flow should earn a premium to whoever absorbs it. This is the main control for any flow signal. Weekly returns of this size may not survive costs, and entry 4 applies.

**11. Jiang, H. and Sun, Z. (2013 draft). Understanding the Illiquidity of Corporate Bonds: The Arrival of Public News. Working paper.**
- URL: https://cba.lmu.edu/media/lmucollegeofbusinessadministration/undergrad/05_Sun.pdf
- Verified: PDF title page only. Crossref did not return it. I found no journal version. Tier 2. Read: part text.
- Data: Enhanced TRACE direction data with firm news. Method: daily signed dollar volume and news-day interactions.
- Finding: on news days volume rises 21%, short-term reversal falls 42% and the price impact of order flow falls 28%. Large buys go with higher later returns and small buys with lower later returns. Neither predicts on news days.
- Means for us: condition on size and on public news. Flow on news days carries less private information. Treat this as weak evidence, because it is an old draft with no journal record that I could find.

**12. Goyal, A., Nozawa, Y. and Qiu, Y. (FINRA lists October 2025, SSRN record 2026). On the Drivers of Corporate Bond Lending. Working paper.**
- DOI: 10.2139/ssrn.7392021. Verified: Crossref and FINRA's list of independent academic studies. Tier 2. Read: both abstract versions.
- Data and method: securities lending linked to TRACE. Variance decomposition of lending.
- Finding: short sellers in bonds are mainly dealers. Lending rises with customer buying pressure. Market making accounts for 66% of lending variation, and customer speculation never exceeds 50% even in special bonds.
- Means for us: do not import equity short-interest logic. High bond lending can mean customers are buying, which reverses the usual reading.

**13. Hendershott, T., Kozhan, R. and Raman, V. (Crossref date 2018). Short Selling and Price Discovery in Corporate Bonds. Journal of Financial and Quantitative Analysis 55(1), 77-115.**
- DOI: 10.1017/s0022109018001539. Verified: Crossref. Tier 1. Read: abstract.
- Finding: short selling forecasts bond returns, mostly in high yield and after Lehman. It predicts in the shorted bond and in other bonds of the same issuer. Short selling rises after buying order imbalances, so short sellers trade against pressure as well as on information. Information flows from stocks to bonds, not the reverse.
- Means for us: read with entry 12. Aggregate flow signals to the issuer as well as the bond. Include past stock returns as a control.

**14. Jacobsen, S., Venkataraman, K. and Xu, D. (2025, revised January 2026). Illiquidity Meets Intelligence: AI-Driven Price Discovery in Corporate Bonds. Working paper.**
- DOI: 10.2139/ssrn.5297667. Verified: Crossref and FINRA's list. Tier 2. Read: abstract on the FINRA page.
- Data: corporate bond transactions and MarketAxess CP+ quotes. Method: price discovery regressions.
- Finding: CP+ predicts future trade prices better than the last trade. Its updates reflect market-wide moves and bond-specific non-public information from the RFQ process.
- Means for us: RFQ information already leaks into a vendor reference price. Any RFQ signal must beat CP+ or a similar mark. CP+ may also be a better entry and mark price than the last trade.

**15. Comerton-Forde, C., Ford, B., Foucault, T. and Jurkatis, S. (2025). Investors as a Liquidity Backstop in Corporate Bond Markets. HEC Paris Research Paper.**
- DOI: 10.2139/ssrn.5229934. Verified: Crossref and FINRA's list. Tier 2. Read: abstract on the FINRA page.
- Finding: where investors stopped providing liquidity in March 2020, transaction costs rose 38%. Dealers relying on flexible-mandate investors such as hedge funds are more resilient. Discounts for past liquidity services are two-thirds of relationship discounts.
- Means for us: a client's sell can be liquidity it supplies to a dealer, not its own view. A signed flow signal should try to separate the two.

### Fire sales and forced selling

**16. Ellul, A., Jotikasthira, C. and Lundblad, C. (2011). Regulatory Pressure and Fire Sales in the Corporate Bond Market. Journal of Financial Economics 101(3), 596-620.**
- DOI: 10.1016/j.jfineco.2011.03.020. Verified: Crossref and RePEc. Tier 1. Read: abstract, published and SSRN versions.
- Data: insurer transactions, 2001 to 2005. Method: compares constrained and unconstrained insurers around downgrades.
- Finding: more constrained insurers sell downgraded bonds more often. Bonds with a high probability of forced selling show price falls and later reversals. Effects grow when insurers are distressed and buyer capital is scarce.
- Means for us: the event trigger is rating plus holder constraint, not the downgrade alone. Forced selling implies a reversal that a positioning signal could trade.

**17. Choi, J., Hoseinzade, S., Shin, S. and Tehranian, H. (2020). Corporate Bond Mutual Funds and Asset Fire Sales. Journal of Financial Economics 138(2), 432-457.**
- DOI: 10.1016/j.jfineco.2020.05.006. Verified: Crossref and RePEc. Tier 1. Read: abstract.
- Method: same-issuer bonds held by funds with different outflows, which removes issuer news.
- Finding: little evidence that redemptions drive fire-sale price pressure once issuer information is controlled. Funds hold liquidity cushions and sell liquid assets first, even in 2008.
- Means for us: fund outflow alone is a weak bond-level signal. Selling also lands on the liquid bonds, not the weakest. Compare within issuer so that we do not mistake credit news for pressure.

**18. Falato, A., Hortacsu, A., Li, D. and Shin, C. (2021). Fire-Sale Spillovers in Debt Markets. Journal of Finance 76(6), 3055-3102.**
- DOI: 10.1111/jofi.13078. Verified: Crossref. Tier 1. Read: abstract of the SSRN version, 10.2139/ssrn.2887822.
- Method: a spillover measure across funds holding the same assets, with regression discontinuity, instrument and placebo tests.
- Finding: one standard deviation more spillover lowers peer fund returns by 45 bps and flows by 90 bps, and adds 2 percentage points to the chance of a large bond price drop.
- Means for us: measure overlap across holders. Risk comes from who else holds the bond, and not only from the client we see.

**19. Goldstein, I., Jiang, H. and Ng, D. (2017). Investor Flows and Fragility in Corporate Bond Funds. Journal of Financial Economics 126(3), 592-613.**
- DOI: 10.1016/j.jfineco.2016.11.007. Verified: Crossref and RePEc. Tier 1. Read: abstract, published and SSRN versions.
- Data: corporate bond funds, 1992 to 2014 (SSRN abstract). Method: flow-performance regressions.
- Finding: flows are concave. Outflows respond to bad performance more than inflows respond to good performance. The effect grows with fund asset illiquidity and market illiquidity.
- Means for us: under-water funds are the ones whose end investors leave. Pain should feed through fund performance and flow, and it should be non-linear on the downside.

**20. Coppola, A. (2025). In Safe Hands: The Financial and Real Impact of Investor Composition over the Credit Cycle. Review of Financial Studies 38(8), 2275-2325.**
- DOI: 10.1093/rfs/hhaf017. Verified: Crossref and the June 2024 draft. Tier 1. Read: abstract and data section of the draft.
- Data: security-level holdings of insurers, plus Morningstar for funds and ETFs. Method: within-firm ownership variation with a shift-share instrument.
- Finding: raising insurer holdings by half a bond's size causes 20% shallower drawdowns in downturns.
- Means for us: scale any pain or crowding measure by holder type. The same selling means more in a fund-held bond than in an insurer-held one.

**21. Chaudhary, M., Fu, J. Z. and Li, J. (2026). Corporate Bond Multipliers: Substitutes Matter. Review of Financial Studies, forthcoming.**
- DOI: 10.1093/rfs/hhag082. Working paper: 10.2139/ssrn.4292266. Verified: Crossref. Tier 1. Read: SSRN abstract only.
- Finding: with heterogeneous substitution, security-level multipliers are essentially zero, an order of magnitude below naive estimates. Portfolio multipliers are much larger and rise with aggregation. They are larger for high yield, long maturity and high arbitrage risk bonds.
- Means for us: test flow at sector, rating and maturity bucket level, not only by CUSIP. Single-bond pressure may just move to close substitutes.

### RFQ and electronic trading

**22. O'Hara, M. and Zhou, X. (2021). The Electronic Evolution of Corporate Bond Dealers. Journal of Financial Economics 140(2), 368-390.**
- DOI: 10.1016/j.jfineco.2021.01.001. Verified: Crossref. Tier 1. Read: abstract.
- Data: proprietary MarketAxess data with regulatory TRACE. Method: compares electronic RFQ and voice trading.
- Finding: electronic trading was still fairly small and segmented in their data, but it affects costs and execution quality across electronic, voice and interdealer trading.
- Means for us: RFQ data is a selected slice of flow. Measure platform share by bond and period. Otherwise growth in platform use looks like growth in demand.

**23. Hendershott, T., Livdan, D. and Schurhoff, N. (2021). All-to-All Liquidity in Corporate Bonds. Swiss Finance Institute Research Paper 21-43.**
- URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3895270
- Verified: the SSRN page in search results and the October 2021 PDF. No Crossref match. Tier 2. Read: part text.
- Data: MarketAxess RFQ data, 2014 to 2018. Method: auction model of dealer bidding.
- Finding: Open Trading wins 12% of trades, split into 2% investor-to-investor, 3% dealers with new clients and 7% new liquidity providers. Price improvement reaches over 2 bps by the end of 2018. Average dealer bids per RFQ fall from 5 to 3.
- Means for us: "client" on a platform may be a quasi-dealer. Filter these liquidity providers out of positioning measures, or their inventory trades will look like views.

**24. Li, J., O'Hara, M., Rapp, A. and Zhou, X. (2023, draft February 2025). Bond Market Illiquidity: Is Portfolio Trading the Solution? Working paper.**
- DOI: 10.2139/ssrn.4495516. PDF hosted by HBS. Verified: Crossref and PDF. Tier 2. Read: part text.
- Data: regulatory TRACE with dealer identities. 8,710 portfolio trades, of which 1,269 fall in the first half of 2020. Average par is about $50 million and 85 bonds.
- Method: refines a TRACE identification method and compares costs with single-bond trades.
- Finding: by end 2021 about 70% of traded US corporate bonds had been in portfolio trades, which were 5% to 7% of volume. Costs improve in normal times. The benefit reverses for the largest portfolios. In early 2020 portfolio trades cost 57 to 73 bps more than single-bond trades.
- Means for us: basket trades do not express a view on each bond. Tag them and exclude them, or give them less weight. Their price is also not a clean entry level per bond.

**25. Meli, J. and Todorova, Z. (2022). Portfolio Trading in Corporate Bond Markets. Working paper.**
- DOI: 10.2139/ssrn.4295453. Related published paper: Portfolio Trading and Corporate Bond ETFs, Financial Management (2026), 10.1111/fima.70044.
- Verified: Crossref for both, plus the March 2023 draft. Tier 2 (the related article is Tier 1). Read: part text of the draft and the published abstract.
- Data: a proprietary Barclays inquiry set used to train a clustering algorithm on TRACE. Over 12,000 investment grade portfolio trades and about 1 million bond lines.
- Finding: portfolio trading rises from about 1% of investment grade volume in 2018 to 7% in 2021. It cuts costs by over 40%, most for the least liquid bonds. ETFs help dealers price and hedge. The authors are at Barclays, so they have an industry position.
- Means for us: dealers hedge baskets with ETFs, so client flow may show up in ETF flow. Link this to theme work on credit ETFs.

### Dealers, immediacy and stress

**26. Bessembinder, H., Jacobsen, S., Maxwell, W. and Venkataraman, K. (2018). Capital Commitment and Illiquidity in Corporate Bonds. Journal of Finance 73(4), 1615-1661.**
- DOI: 10.1111/jofi.12694. Verified: Crossref. Tier 1. Read: abstract.
- Data: US corporate bonds, 2006 to 2016.
- Finding: average trade costs did not rise notably over time. Dealer capital commitment, turnover, block frequency and trade size fell, driven by bank-affiliated dealers. Nonbank dealers increased their commitment.
- Means for us: signal strength may vary by regime. Dealers now absorb less, so one-sided client flow may need to find other clients. Do not assume a constant relation across 2006 to today.

**27. Dick-Nielsen, J. and Rossi, M. (2019). The Cost of Immediacy for Corporate Bonds. Review of Financial Studies 32(1), 1-41.**
- DOI: 10.1093/rfs/hhy080. Verified: Crossref and RePEc. Tier 1. Read: abstract.
- Method: index exclusions as a natural experiment with uninformed sellers.
- Finding: the cost of immediacy more than doubled after 2008. Dealers revert from target inventory faster after the crisis.
- Means for us: index exclusions give a clean test of uninformed flow. Use them to separate the price effect of pressure from the effect of information in our indicator.

**28. O'Hara, M. and Zhou, X. (2021). Anatomy of a Liquidity Crisis: Corporate Bonds in the COVID-19 Crisis. Journal of Financial Economics 142(1), 46-68.**
- DOI: 10.1016/j.jfineco.2021.05.052. Verified: Crossref. Tier 1. Read: abstract.
- Finding: before the Fed acted, volume moved to liquid bonds, costs soared and trade-size pricing inverted. Dealers, particularly non-primary dealers, switched from buying to selling, so inventories fell. Customer-to-customer electronic trading rose, at very high cost.
- Means for us: normal rules break in stress. Larger trades can stop being cheaper, and RFQ flow can shift towards liquid bonds. The indicator needs a stress regime, and its level prices will be poor marks there.

**29. Feldhutter, P. (2012). The Same Bond at Different Prices: Identifying Search Frictions and Selling Pressures. Review of Financial Studies 25(4), 1155-1206.**
- DOI: 10.1093/rfs/hhr093. Verified: Crossref and RePEc. Tier 1. Read: abstract.
- Method: a model of OTC trade with search frictions. The measure is the gap between prices paid by small and large traders.
- Finding: the gap identifies periods with many forced sellers, including the GM and Ford downgrade of 2005 and the subprime crisis.
- Means for us: this gives a pain measure that RFQ size and level data can compute directly. Entry 28 warns that size pricing can invert in a crisis, which is what the measure looks for.

### Momentum

**30. Jostova, G., Nikolova, S., Philipov, A. and Stahel, C. (2013). Momentum in Corporate Bond Returns. Review of Financial Studies 26(7), 1649-1693.**
- DOI: 10.1093/rfs/hht022. Verified: Crossref. Tier 1. Read: SSRN abstract, 10.2139/ssrn.1651853.
- Data: 81,491 US corporate bonds with transaction and dealer-quote data, 1973 to 2011.
- Finding: momentum averages 59 bps per month from 1991 to 2011, and 192 bps in non-investment grade. It comes from non-investment grade bonds.
- Means for us: use as the classic control. Entry 4 and the 2023 Dickerson paper dispute that such return-based profits survive noise correction, so treat the size with care.

## Supporting records, checked but not ranked

I confirmed each of these on Crossref. The note says what I read.

- Kondor, P. and Pinter, G. (2022). Clients' Connections. Journal of Finance 77(1), 505-544. 10.1111/jofi.13087. Abstract. UK gilts, not corporate bonds. It is the source of the connections measure in entry 1.
- Pinter, G., Wang, C. and Zou, J. (2024). Size Discount and Size Penalty. Review of Financial Studies 37(7), 2156-2190. 10.1093/rfs/hhae007. Abstract. Costs rise with size within a client, and the effect is larger for corporate bonds.
- Hendershott, T. and Madhavan, A. (2015). Click or Call? Journal of Finance 70(1), 419-447. 10.1111/jofi.12164. Abstract. One-sided electronic auctions work even in inactive bonds.
- Hendershott, T., Li, D., Livdan, D., Schurhoff, N. and Venkataraman, K. (2026). Quote Competition in Corporate Bonds. Journal of Finance 81(4), 2165-2216. 10.1111/jofi.70048. Abstract. Dealers advertise quotes to manage inventory.
- Hendershott, T., Li, D., Livdan, D. and Schurhoff, N. (2020). Relationship Trading in Over-the-Counter Markets. Journal of Finance 75(2), 683-734. 10.1111/jofi.12864. Abstract. One third of insurers use a single dealer.
- Kargar, M., Lester, B., Lindsay, D., Liu, S., Weill, P.-O. and Zuniga, D. (2021). Corporate Bond Liquidity during the COVID-19 Crisis. Review of Financial Studies 34(11), 5352-5401. 10.1093/rfs/hhab063. Abstract. Willingness to pay for immediacy rose about 200 bps.
- Ambrose, B., Cai, N. and Helwege, J. (2008). Forced Selling of Fallen Angels. Journal of Fixed Income 18(1), 72-85. 10.3905/jfi.2008.708844. Abstract. No wholesale liquidation of fallen angels by insurers.
- Bao, J., O'Hara, M. and Zhou, X. (2018). The Volcker Rule and Corporate Bond Market Making in Times of Stress. Journal of Financial Economics 130(1), 95-113. 10.1016/j.jfineco.2018.06.001. Abstract.
- Adrian, T., Boyarchenko, N. and Shachar, O. (2017). Dealer Balance Sheets and Bond Liquidity Provision. Journal of Monetary Economics 89, 92-109. 10.1016/j.jmoneco.2017.03.011. Abstract.
- Choi, J., Shachar, O. and Shin, S. (2019). Dealer Liquidity Provision and the Breakdown of the Law of One Price. Management Science 65(9), 4100-4122. 10.1287/mnsc.2017.3011. Abstract. Dealers supply less liquidity as they suffer losses. An earlier version with Choi and Shachar only is 10.2139/ssrn.2344342.
- Giannetti, M. and Jotikasthira, C. (2024). Bond Price Fragility and the Structure of the Mutual Fund Industry. Review of Financial Studies 37(7), 2063-2109. 10.1093/rfs/hhad095. Abstract. Ownership concentration limits exposure to flow-induced fire sales.
- Kim, M. and Randall, O. (2023). Short of Cash? Convex Corporate Bond Selling by Mutual Funds and Price Fragility. 10.2139/ssrn.4585667. Abstract. Price pressure is convex in the aggregate cash shortfall.
- Bretscher, L., Schmid, L., Sen, I. and Sharma, V. (2025). Institutional Corporate Bond Pricing. Review of Financial Studies 39(3), 605-660. 10.1093/rfs/hhaf067. Abstract. Insurers are inelastic and mutual funds elastic.
- Koijen, R. and Yogo, M. (2023). Understanding the Ownership Structure of Corporate Bonds. American Economic Review: Insights 5(1), 73-91. 10.1257/aeri.20210550. Abstract. Insurers are the largest institutional holders and hold leveraged low-beta portfolios.
- Han, S. and Zhou, X. (2014). Informed Bond Trading, Corporate Yield Spreads, and Corporate Default Prediction. Management Science 60(3), 675-694. 10.1287/mnsc.2013.1768. Abstract. Information asymmetry explains yield spreads and helps forecast defaults.
- Ronen, T. and Zhou, X. (2013). Trade and Information in the Corporate Bond Market. Journal of Financial Markets 16(1), 61-103. 10.1016/j.finmar.2012.09.003. Abstract. Stock leads disappear once institutional trade dominance is accounted for.
- Bali, T., Subrahmanyam, A. and Wen, Q. (2021). Long-term Reversals in the Corporate Bond Market. Journal of Financial Economics 139(2), 656-677. 10.1016/j.jfineco.2020.08.007. Abstract. Reversals are driven by long-term losers.
- Dickerson, A., Mueller, P. and Robotti, C. (2023). Priced Risk in Corporate Bonds. Journal of Financial Economics 150(2), 103707. 10.1016/j.jfineco.2023.103707. Abstract. Bond CAPM is not beaten by published factors.
- Dick-Nielsen, J., Feldhutter, P., Pedersen, L. and Stolborg, C. (2023). Corporate Bond Factors: Replication Failures and a New Framework. 10.2139/ssrn.4586652. Abstract.

## Synthesis

### Where findings agree

1. **Selling pressure reverses.** Insurer forced selling, sell herding and flow-driven fund pressure all show a price fall followed by recovery (entries 16, 8, Dannhauser and Hoseinzade 2021, 10.1093/rfs/hhab031, abstract read).
2. **Stress changes the rules.** Dealers step back, costs jump and normal price patterns break (entries 26, 27, 28, Bao and colleagues).
3. **Who holds the bond matters.** Insurers and funds behave differently, and overlap across holders spreads shocks (entries 18, 20, Bretscher and colleagues).
4. **Illiquid and high yield bonds show the largest effects.** This holds for herding, momentum, short selling and axes (entries 8, 30, 13, 3). It is also where price noise and costs are highest, so entry 4 applies most there.

### Where findings conflict, and why

1. **Do fund outflows cause fire sales?** Choi and colleagues (17) find little pressure. Falato and colleagues (18), Fang (2) and Kim and Randall find real effects. A likely reason is that entry 17 compares same-issuer bonds, which removes issuer news. Sample also differs, since Fang looks only at crises. Chaudhary and colleagues (21) offer a possible bridge, with effects near zero by bond and larger by portfolio. That bridge is my reading.
2. **Are insurers forced sellers?** Ellul and colleagues (16) find fire sales. Ambrose and colleagues find no wholesale liquidation. These may both hold, since entry 16 focuses on the bonds and insurers most exposed to regulatory selling.
3. **Do dealer signals show information or pressure?** Friewald and Nagler (10) read inventory returns as pay for risk. Geilen (3) finds axes predict without reversal and reads this as information. The two papers use different data, inventory against intent, and could both be right.
4. **Does bond short selling show information?** Hendershott and colleagues (13) say yes, partly. Goyal and colleagues (12) say it mostly reflects dealers meeting customer buying. The second view rests on a decomposition of lending.
5. **Is momentum or reversal real?** Jostova and colleagues (30) and Bali and colleagues say yes. The Dickerson papers (4) say that noise and return filters explain much of it. The later work directly tests the earlier method, so I give it more weight until it passes peer review or fails it.
6. **Do dealers learn from client flow?** Jurkatis and colleagues (6) find no link between discounts and information extraction. Jacobsen and colleagues (14) and Geilen (3) find RFQ and client information in prices and axes. These answer different questions, one about pricing a client and the other about using information.

### Gaps

1. **RFQ flow and returns.** I found no paper testing client-side RFQ imbalance as a return or spread predictor. Published RFQ work studies costs and search (7, 22, 23).
2. **Entry levels outside insurers.** Insurers report book value, so they are measurable. I found no paper that estimates cost basis for funds or hedge funds in bonds and tests its effect.
3. **Disposition effect.** I found no corporate bond test. Searches returned only equity and insurer work. A search-result summary of a later Fang draft (September 2025) says fund unrealized losses do not have the same effect as insurer losses. I did not read that passage, so treat it as a lead.
4. **Ongoing corrected tests.** Most flow results predate the noise corrections in entry 4. I found none redone with corrected data.

### What this means for measuring entry levels and pain

These are my inferences, not findings.

1. Price alone misleads, because bonds pull to par and carry coupon. Measure under-water in spread or in excess return as well as in price. Andreani and colleagues show why the rate part must be removed.
2. RFQ data starts at the date our data starts. Positions held before then have unknown cost. Use holdings data for the opening position where possible, and mark the rest as unknown.
3. We see only one window of a client's trading. Clients split flow across dealers (entry 1) and platforms (entry 22). So our cost basis is partial and our measured net position may be wrong in sign.
4. Filled trades and failed inquiries are different objects. Only fills set an entry level. Failed inquiries may still signal demand (entry 7).
5. Each holder type has a different "pain" reference. Insurers look at book value (2, 5). Funds face performance-driven flows (19). This suggests separate indices.

### What breaks

1. Basket trades pollute single-bond flow (24, 25).
2. Quasi-dealers on all-to-all venues look like clients (23).
3. Client sells may be liquidity supplied to dealers (15).
4. Repeated inquiries double count a single order (7).
5. CP+ and similar marks may already hold the RFQ signal (14).

## Data problems

1. **Size caps.** Public TRACE shows investment grade trades above $5 million as "5MM+" and non-investment grade above $1 million as "1MM+" (FINRA reporting timeframes page). Aggregated uncapped volume is in daily reports. So public data hides block size and understates signed flow. Enhanced TRACE reports uncapped size, but Meli and Todorova note a 6-month delay in their version.
2. **Side and client.** Regulatory TRACE gives a buy-sell flag from the dealer's view and a customer or interdealer flag (Li and colleagues). It does not name the client (Czech and Pinter, Jurkatis and colleagues). Enhanced TRACE provides direction (Jiang and Sun).
3. **Academic TRACE.** It has uncapped quantity, buy or sell, principal or agency, and masked dealer IDs. It has a 36-month lag and is limited to higher education institutions (FINRA data sheet). Rule 144A trades are included.
4. **Errors and double counting.** Dick-Nielsen (2009, 10.3905/jfi.2009.19.2.043) reports 7.7% of TRACE reports are errors, up to 18% in some cases. The 2013 note (10.2139/ssrn.2337908) deletes almost 35% of raw 2007 Enhanced transactions, including agency and interdealer double counts. Use this filter before signing flow.
5. **Return construction.** Andreani, Palhares and Richardson (2024, Review of Accounting Studies 29(4), 3887-3906, 10.1007/s11142-023-09777-6) warn that subtracting a Treasury bill return contaminates credit returns. They also note that TRACE coverage differs from index coverage and that prices differ in quality.
6. **Bias in factors.** See entry 4. Measurement error in the signal and the return are correlated, and one-sided filters use future data.
7. **A retracted paper.** Crossref marks Bai, Bali and Wen (2019), Common Risk Factors in the Cross-Section of Corporate Bond Returns, Journal of Financial Economics 131(3), as retracted (10.1016/j.jfineco.2018.08.002, notice 10.1016/j.jfineco.2023.103721). Do not use it as a control or as a citation. I did not read the reasons in the notice.
8. **Portfolio trade flag.** TRACE reports carry a portfolio modifier only from May 15, 2023, for two-party baskets of at least 10 issues at one agreed price (FINRA Notice 22-12). Earlier work must infer these trades with an algorithm (24, 25).

## Data with side or client type

No public dataset I found gives client type at trade level. The nearest options are these.

| Source | Side | Client | Access, as I found it |
|---|---|---|---|
| Public TRACE | Not confirmed | No | Public, size capped |
| Enhanced TRACE | Yes | No | Delayed. Licence terms not checked |
| Academic TRACE | Yes | No, masked dealer only | Academics only, 36-month lag |
| Regulatory TRACE | Yes | No, named dealer | Provided by FINRA to some researchers |
| FCA ZEN and MiFID II | Yes | Yes, both parties | Held by the FCA. Not public |
| NAIC Schedule D Parts 3 and 4 | Yes, by purchase or sale | Yes, insurer, with book value | Filed by insurers. Access terms not checked |
| eMAXX, Morningstar holdings | Inferred from changes | Yes | Vendor, periodic holdings |
| SEC Form N-PORT | Inferred from changes | Yes, funds | Public at quarter end, 60-day lag. Search summaries only. A 2026 SEC proposal may change this. Cost basis not confirmed |
| NY Fed FR 2004 | Net positions | Primary dealers, aggregate | Published weekly in aggregate. Search summary only |

## Seed leads: what I found

- **Confirmed and used:** Bessembinder and colleagues, Hendershott and Madhavan, O'Hara and Zhou (two papers), Kargar and colleagues, Goldstein and colleagues, Ellul and colleagues, Feldhutter, Dick-Nielsen and Rossi, Meli and Todorova, Jostova and colleagues, Dickerson and colleagues, Bali and colleagues.
- **Corrected:** "Choi and Shachar" exists as a 2013 SSRN paper, and the journal version adds Shin (Management Science 2019).
- **Not found, left out:** "Li, Nguyen, Pham and Wei". Crossref and web searches found no such paper. The portfolio trading paper I did find is Li, O'Hara, Rapp and Zhou (entry 24), which may be what the lead meant.
- **Confirmed but out of scope:** Coval and Stafford (2007, Journal of Financial Economics 86(2), 479-512, 10.1016/j.jfineco.2006.09.007) is an equity paper. I confirmed the record only and did not read it for this review.

## Search strings

Web searches (WebSearch, standard and extended):

- corporate bond RFQ data customer order flow predicts returns dealer request for quote MarketAxess working paper 2024 2025
- signed order flow corporate bonds TRACE predict bond returns customer buy sell imbalance cross-section working paper
- portfolio trading corporate bonds liquidity dealer balance sheet paper Meli Todorova, Li Nguyen Pham Wei, Sommer Pasquali 2024 2025
- all-to-all corporate bond trading Open Trading MarketAxess electronic trading RFQ paper Hendershott Livdan Schurhoff
- corporate bond disposition effect unrealized losses mutual funds insurers cost basis holdings under water selling reference price working paper
- corporate bond short-term reversal illiquidity price pressure customer selling dealer TRACE mutual funds positioning underwater bonds 2024 2025
- bond mutual fund or insurer trades signed flow predict corporate bond returns, RFQ inquiry imbalance signal credit
- FINRA TRACE dissemination caps, Academic TRACE, portfolio trade modifier, FR 2004, Form N-PORT queries

Records: about 90 Crossref bibliographic queries by author and title, plus DOI lookups. Abstracts came from Crossref, OpenAlex and RePEc. I also read FINRA's list of independent academic studies and followed citations in the papers I read.

## Limits of this search

- OpenAlex topic searches returned rate-limit errors (HTTP 429) on every try. So topic discovery rests on web search, Crossref and citation following. I may have missed recent working papers. The "no paper found" statements in Gaps mean only that these searches found none.
- SSRN pages refused direct download (HTTP 403). I relied on Crossref and RePEc for their abstracts.
- Most Tier 1 entries are abstract only. Where I give no number, I did not read one.

## What I excluded

- Equity-only flow and fire sale papers, and index CDS and swap RFQ papers, as outside this theme.
- Municipal bond and CLO papers, such as Hendershott and colleagues (2024) on CLOs, except as analogies.
- ETF-focused papers, since another theme covers them, apart from links noted above.
- arXiv market making papers on RFQ hit ratios, seen in search results only. They study dealer pricing, not whether client flow predicts returns.
- Bond-to-stock papers on TRACE and corporate disclosure, as off topic.
- Wei and Zhou (2016, 10.1111/fima.12123) and Kedia and Zhou (2014, 10.1016/j.finmar.2013.07.002). The records exist, but I read no abstract, so I state no finding.
- Any paper I could not match to a real record.
