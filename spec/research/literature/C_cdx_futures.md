# Theme C: CDX indices, CDS positioning, and credit futures

Search date: 1 November 2026.

## Bottom line

1. Public data cannot show who holds CDX. Rule 17 CFR 43.4 forbids disclosing swap parties in public trade data. The holder-type papers below all use confidential regulatory data.
2. The only public holder split for any credit derivative is the CFTC Traders in Financial Futures (TFF) report on the CME Bloomberg contracts. It is 8 to 26 weekly reports long. The high yield series has been missing since 15 September 2026.
3. The evidence supports a "pain" idea in CDS. Seller margin payments explain 12% of weekly spread changes (Siriwardane). Margins respond more to tail risk than Value-at-Risk implies, which may amplify large shocks (Capponi and colleagues).
4. Direct evidence that positions forecast CDX spreads is thin. The closest index result is a same-period association (Wang and Zhong).
5. I found no academic paper on credit futures positioning.

## How to read each entry

- **Tier 1:** peer-reviewed journal.
- **Tier 2:** working paper or preprint.
- **Tier 3:** industry or official report.
- **Read** states what I read. "Abstract" means I did not read the full paper, so data and method fields are limited to what the abstract or record states.
- The "Means for us" lines are my inference. They are not findings of the papers.

## Entries, best first

### 1. Coughlan, Lau and Orlov (2022)

- **Citation:** John Coughlan, Madison Lau, Alexei Orlov. "Single-Name and Index CDS Dynamics during the Market Stress of 2020." CFTC Office of the Chief Economist, Staff Papers and Reports 2022-007, October 2022.
- **URL:** https://www.cftc.gov/sites/default/files/2022-10/CDS%20white%20paper%20October%202022_ada.pdf
- **Verified:** PDF on the CFTC site. **Tier:** 3. **Read:** abstract, sections 1 to 4.2, and hedge fund passages.
- **Data and sample:** Confidential Trade Information Warehouse (TIW) positions as of every Friday, 2014 to late 2020. Regulatory swap transactions, mid-2019 to late 2020. Counterparties are classed as dealers, banks, hedge funds, asset managers, insurers, pension funds, and other.
- **Method:** Descriptive position and flow analysis by firm type and product.
- **Key finding:**
  - Standard index gross notional rose from $2.57tn on 3 January 2020 to $5.14tn on 20 March 2020.
  - Dealers accounted for over 85% of the increase.
  - Hedge fund positions went from $262bn to $400bn, then $320bn by 26 June.
  - Hedge funds bought about $80bn of protection net. They were the only major firm type buying net into 20 March, and they sold immediately after.
  - The average one-month position rise over the six prior index rolls was 22%. The March 2020 event coincided with a roll.
  - About 70% to 80% of index CDS was cleared in 2020, citing the Financial Stability Oversight Council.
- **Means for us:** Gross notional is a poor stress gauge because dealer intermediation dominates it. Any position change near 20 March or 20 September must be adjusted for the roll. A text search of the paper found no discussion of forced unwinds, so this episode does not by itself show forced exits.

### 2. Siriwardane (2019)

- **Citation:** Emil N. Siriwardane. "Limited Investment Capital and Credit Spreads." Journal of Finance 74(5), 2303-2347.
- **DOI:** 10.1111/jofi.12777
- **Verified:** Crossref, OpenAlex, RePEc. **Tier:** 1. **Read:** abstract only.
- **Data and sample:** Proprietary CDS data. The abstract gives no dates.
- **Method:** Measures capital shocks at protection sellers as CDS portfolio margin payments, then relates them to weekly spread changes.
- **Key finding:** Seller capital shocks account for 12% of the time-series variation in weekly spread changes. Standard credit factors account for 18%. The shocks carry information independent of institution-wide constraint measures. The abstract infers a high degree of segmentation.
- **Means for us:** This is the closest published precedent for a CDS pain indicator. It works because it measures losses at the actual holders. Public data cannot rebuild it, so we would have to proxy holder losses. I did not read the paper's concentration statistics.

### 3. Capponi, Cheng, Giglio and Haynes (2022)

- **Citation:** Agostino Capponi, Wan-Schwin Allen Cheng, Stefano Giglio, Richard Haynes. "The Collateral Rule: Evidence from the Credit Default Swap Market." Journal of Monetary Economics 126, 58-86.
- **DOI:** 10.1016/j.jmoneco.2021.12.003
- **Verified:** Crossref, OpenAlex, RePEc listing. **Tier:** 1. **Read:** abstract of the CFTC preliminary draft (https://www.cftc.gov/idc/groups/public/@economicanalysis/documents/file/oce_collateral_rule.pdf). I did not read the published version.
- **Data and sample:** CDS portfolios and margins of all participants at ICE Clear Credit, covering 60% of the U.S. market.
- **Method:** Relates margins to portfolio risk and market conditions.
- **Key finding:** Margins are set much more conservatively than a Value-at-Risk rule implies, and they are applied unequally across participants. Extreme tail measures explain margins better than Value-at-Risk. This may create margin spirals that dampen small shocks and amplify large ones.
- **Means for us:** A forced-exit signal should be nonlinear. Small spread moves should score near zero, and large moves should score sharply higher. This is the strongest available support for our levered-holder hypothesis, though the paper studies margins and not exits.

### 4. Wang and Zhong (2022)

- **Citation:** Xinjie Wang, Zhaodong Zhong. "Dealer Inventory, Pricing, and Liquidity in the OTC Derivatives Markets: Evidence from Index CDSs." Journal of Financial Markets 57.
- **DOI:** 10.1016/j.finmar.2020.100617
- **Verified:** OpenAlex, RePEc. **Tier:** 1. **Read:** abstract only.
- **Data and sample:** Position and pricing data on CDS indices. I did not read the source or dates.
- **Method:** Relates changes in spreads, index basis, and bid-ask spreads to dealer net positions.
- **Key finding:** Index spread changes are negatively associated with changes in dealers' net long positions. The effect is stronger after the Volcker Rule. The index basis is also negatively associated with dealer net long positions. Bid-ask spreads and the number of dealers rise when dealer inventory is larger.
- **Means for us:** This is the most direct index evidence on positions and prices. The abstract describes association, not forecasting. Do not cite it as proof that positions predict spreads.

### 5. Boyarchenko, Gupta, Steele and Yen (2018)

- **Citation:** Nina Boyarchenko, Pooja Gupta, Nick Steele, Jacqueline Yen. "Trends in Credit Basis Spreads." Federal Reserve Bank of New York Economic Policy Review 24(2).
- **URL:** https://www.newyorkfed.org/research/epr/2018/epr_2018_trends-in-credit-basis-spreads_boyarchenko
- **Verified:** PDF on the New York Fed site. Crossref search did not return it. **Tier:** 2 (Federal Reserve policy journal, closest fit). **Read:** full relevant sections.
- **Data and sample:** Weekly DTCC position snapshots given to the Federal Reserve Board, covering 75% of TIW trades in a median week. ICE open interest and volume. The focus is the 2015 to 2016 basis widening.
- **Method:** Regressions of basis changes on unfilled open interest. Net positions by institution type. Stylized dealer return on equity calculations.
- **Key finding:**
  - The CDX-CDS basis reached a third of its crisis peak in February 2016.
  - Investment advisors increased CDX protection selling, and greater derivative use seemed to precede fund outflows.
  - Return on equity on the CDS-bond trade falls from 17% to 9% as the assumed leverage ratio rises, with lower values at tighter ratios.
  - A 15% target needed a basis below minus 134 bp at low leverage ratios, and minus 218 bp at a 6% ratio.
  - Margin on the index and single-name legs of the CDX-CDS trade cannot be offset.
- **Means for us:** Index skew measures arbitrage capacity, not just mispricing. Real-money CDX selling is also part of the positioning story, so hedge funds are not the only side to watch.

### 6. Junge and Trolle (working paper, November 2013 version read)

- **Citation:** Benjamin Junge, Anders B. Trolle. "Liquidity Risk in Credit Default Swap Markets." Swiss Finance Institute Research Paper 13-65.
- **DOI:** 10.2139/ssrn.2371374. Crossref lists a second SSRN record, 10.2139/ssrn.2209122.
- **PDF read:** https://www7.uc.cl/economia/finance_uc/docs/conferences/6th/CDSLiq.pdf
- **Verified:** Crossref, RePEc listing, conference PDF. **Tier:** 2. **Read:** abstract and introduction. A later revision exists per listings, and I did not read it.
- **Data and sample:** North American and European investment grade and high yield credit indices, plus single-name CDS portfolios.
- **Method:** Builds an illiquidity measure from the average absolute percentage gap between index levels and theoretical values. Estimates a factor pricing model.
- **Key finding:**
  - Bases reached up to 60 bp for investment grade and 300 bp for high yield at the crisis peak.
  - The measure peaked at 28.84% at the end of December 2008, with daily autocorrelation of 0.95.
  - Of average expected excess returns, 0.55% is due to liquidity risk, 0.29% to expected illiquidity, and 0.57% to market and default risk.
- **Means for us:** This gives a defined skew construction that we can adapt. It needs index and constituent CDS quotes, which are usually licensed. Its high persistence suggests using changes or surprises.

### 7. Collin-Dufresne, Junge and Trolle (2020)

- **Citation:** Pierre Collin-Dufresne, Benjamin Junge, Anders B. Trolle. "Market Structure and Transaction Costs of Index CDSs." Journal of Finance. Crossref year 2020.
- **DOI:** 10.1111/jofi.12953
- **Verified:** Crossref, OpenAlex. **Tier:** 1. **Read:** published abstract, plus parts of the September 2017 draft (https://www.aeaweb.org/conference/2018/preliminary/paper/HA3dNy8B).
- **Data and sample:** Post-Dodd-Frank public trade reports matched to quotes. The draft covers five-year on-the-run CDX.IG and CDX.HY as the core set. The draft sample spans 511 trading days. I did not read its exact dates.
- **Method:** Effective spreads and price impact by trade type and protocol.
- **Key finding:**
  - The market remains two-tiered.
  - Dealer-to-client costs exceed interdealer costs, and the higher, largely permanent price impact of client trades explains the gap.
  - Draft half-spreads for CDX.IG are 0.138 bp for dealer-to-client and 0.098 bp for interdealer. For CDX.HY they are 0.676 bp and 0.494 bp.
  - Public reports cap trade size, typically at $110m for CDX.IG and $100m for CDX.HY in the draft.
- **Means for us:** Client flow appears to carry information, but public tapes do not label who traded. Size caps also censor the largest trades, which are the ones most likely to matter for forced exits.

### 8. Boyarchenko, Costello and Shachar (2019)

- **Citation:** Nina Boyarchenko, Anna M. Costello, Or Shachar. "The Long and Short of It: The Post-Crisis Corporate CDS Market." Federal Reserve Bank of New York Staff Report 879, revised August 2019.
- **URL:** https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr879.pdf
- **Verified:** PDF on the New York Fed site. **Tier:** 2. **Read:** abstract and selected sections.
- **Data and sample:** Supervisory contract-level data. In a median week it captures over 70% of single-name, over 60% of index, and over 85% of tranche contracts in TIW.
- **Method:** Stylized facts on positions and pricing across products.
- **Key finding:** Dealers become net buyers of protection from the second half of 2014. They reduce single-name selling and switch to buying index protection. U.S. counterparties are net sellers in index and index options, and their main index counterparties are European.
- **Means for us:** Dealer sign can flip over regimes, so a fixed reading of "dealer long" is unsafe. Positions across single-name, index, options, and tranches need reading together. U.S.-only data miss much of the other side.

### 9. Choi, Shachar and Shin (2019)

- **Citation:** Jaewon Choi, Or Shachar, Sean Seunghun Shin. "Dealer Liquidity Provision and the Breakdown of the Law of One Price: Evidence from the CDS-Bond Basis." Management Science.
- **DOI:** 10.1287/mnsc.2017.3011
- **Verified:** Crossref, Semantic Scholar. **Tier:** 1. **Read:** abstract. I also read the opening abstract of the earlier version, Choi and Shachar, New York Fed Staff Report 650 (2013).
- **Data and sample:** Corporate bond market, 2005 to 2009.
- **Method:** Dealer liquidity provision against the CDS-bond basis. Post-Lehman bond returns by prior basis arbitrage activity.
- **Key finding:** Dealers usually stabilize the basis but cut back after losses, wider mispricing, or worse funding. Unwinding of basis arbitrage can amplify mispricing. Post-Lehman returns were very low for bonds with strong prior basis arbitrage activity.
- **Means for us:** This is the cleanest evidence in the theme that arbitrageur exit moves prices. It concerns bonds in a crisis, so transfer to CDX is a hypothesis.

### 10. Eisfeldt, Herskovic, Rajan and Siriwardane (record year 2022)

- **Citation:** Andrea L. Eisfeldt, Bernard Herskovic, Sriram Rajan, Emil N. Siriwardane. "OTC Intermediaries." Review of Financial Studies.
- **DOI:** 10.1093/rfs/hhac062
- **Verified:** Crossref, OpenAlex. **Tier:** 1. **Read:** abstract.
- **Data and sample:** Regulatory data on the entire U.S. CDS market, 2010 to 2013.
- **Method:** Calibrated core-periphery network model with heterogeneous dealer capacity.
- **Key finding:** The exit of one dealer can raise credit spreads by 8% to 24%, depending on how well dealers share risk.
- **Means for us:** Dealer capacity is a state variable. A positioning signal may need conditioning on dealer stress, although this is a model calibration and not a test of a signal.

### 11. Mitchell and Pulvino (2012)

- **Citation:** Mark Mitchell, Todd Pulvino. "Arbitrage Crashes and the Speed of Capital." Journal of Financial Economics 104(3), 469-490.
- **DOI:** 10.1016/j.jfineco.2011.09.002
- **Verified:** Crossref, RePEc. **Tier:** 1. **Read:** first part of the abstract.
- **Data and sample:** The 2008 crisis. I did not read further detail.
- **Method:** Studies mispricing around the fall in hedge fund leverage.
- **Key finding:** Prime broker distress suddenly reduced hedge fund leverage. Seemingly long-term financing became short-term, and arbitrageurs could not hold similar assets at similar prices.
- **Means for us:** Funding withdrawal, not just spread loss, can force exits. A pain indicator should allow for a funding input such as hedge fund credit availability.

### 12. Boyarchenko, Eisenbach, Gupta, Shachar and Van Tassel (2020 revision)

- **Citation:** Nina Boyarchenko, Thomas M. Eisenbach, Pooja Gupta, Or Shachar, Peter Van Tassel. "Bank-Intermediated Arbitrage." Federal Reserve Bank of New York Staff Report 858, revised July 2020.
- **URL:** https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr858.pdf
- **DOI of SSRN record:** 10.2139/ssrn.3200041
- **Verified:** PDF on the New York Fed site, Crossref. **Tier:** 2. **Read:** abstract and part of the trade definitions.
- **Data and sample:** Post-crisis prime brokerage matches and basis trades, including CDS-bond and index versus single-name trades.
- **Method:** Hedge fund and prime broker matching, and leverage and return calculations.
- **Key finding:** Regulation passes through to unregulated arbitrageurs. After 2014, hedge funds use more prime brokers, diversify away from GSIB-affiliated brokers, and have more fragile matches. Maximum leverage and implied trade returns are considerably lower despite wider spreads.
- **Means for us:** Skew can stay wide without being a clean opportunity. High skew may reflect low capacity, and that needs separating from a positioning signal.

### 13. Oehmke and Zawadowski (record year 2016)

- **Citation:** Martin Oehmke, Ádám Zawadowski. "The Anatomy of the CDS Market." Review of Financial Studies.
- **DOI:** 10.1093/rfs/hhw068
- **Verified:** Crossref, OpenAlex. **Tier:** 1. **Read:** published abstract, plus parts of the 2013 draft (https://www.aeaweb.org/conference/2013/retrieve.php?pdfid=59).
- **Data and sample:** Single-name corporate CDS. The draft uses 39 months of DTCC data, October 2008 to December 2011, with about 16,520 firm-months.
- **Method:** Relates net notional and volume to bond fragmentation, hedging proxies, speculation proxies, and the basis.
- **Key finding:** CDS markets act as alternative trading venues. Positions and volume are larger for firms with fragmented bonds. Speculative trading concentrates in CDS. Basis trades link markets, compressing the negative basis and reducing bond price impact.
- **Means for us:** Net notional is usable as a size measure but does not reveal direction by holder. These are single-name results, so index use is an extension.

### 14. Bai and Collin-Dufresne (record year 2018)

- **Citation:** Jennie Bai, Pierre Collin-Dufresne. "The CDS-Bond Basis." Financial Management.
- **DOI:** 10.1111/fima.12252
- **Verified:** Crossref, OpenAlex. **Tier:** 1. **Read:** abstract.
- **Data and sample:** Cross-section of bond-level CDS-bond bases. I did not read the dates.
- **Method:** Cross-sectional tests of limits-to-arbitrage explanations.
- **Key finding:** The basis deviates more for bonds with higher frictions in trading liquidity, funding cost, counterparty risk, and collateral quality. The basis is more negative when the bond lending fee is higher, suggesting that arbitrageurs avoid negative basis trades when short interest is high.
- **Means for us:** Friction proxies can condition basis signals. These are bond-level results, not index results.

### 15. Aldasoro and Ehlers (2018)

- **Citation:** Iñaki Aldasoro, Torsten Ehlers. "The Credit Default Swap Market: What a Difference a Decade Makes." BIS Quarterly Review, June 2018.
- **URL:** https://www.bis.org/publications/qr-201806/credit-default-swap-market-what-difference-decade-makes
- **Verified:** BIS page. **Tier:** 3. **Read:** key takeaways and hedge fund passage.
- **Data and sample:** BIS semiannual OTC derivatives statistics, up to end-2017.
- **Method:** Descriptive.
- **Key finding:** Notional fell from $61.2tn at end-2007 to $9.4tn at end-2017. The cleared share rose from 17% to 55%, and the interdealer share fell from 53% to 25%. Hedge fund net protection purchased from dealers fell from about $307bn at end-June 2011 to $15.8bn at end-2017.
- **Means for us:** BIS is a rare public hedge fund counterparty view. It is semiannual, global, and dealer-reported, so it suits regime context and not a trading signal.

### 16. Riggs, Onur, Reiffen and Zhu (2020)

- **Citation:** Lynn Riggs, Esen Onur, David Reiffen, Haoxiang Zhu. "Swap Trading after Dodd-Frank: Evidence from Index CDS." Journal of Financial Economics.
- **DOI:** 10.1016/j.jfineco.2020.03.008
- **Verified:** Crossref, Semantic Scholar. **Tier:** 1. **Read:** abstract.
- **Data and sample:** Message-level data on the two largest dealer-to-customer swap execution facilities for index CDS.
- **Method:** Theoretical model and empirical analysis of trading mechanism choice.
- **Key finding:** A typical customer contacts few dealers. Wider exposure is limited by a winner's curse and relationships. Order size, market conditions, and relationships drive mechanism choice and liquidity provision.
- **Means for us:** Large holders may hide intent and split execution with few dealers. Public volume may therefore understate stress until after the move.

### 17. Loon and Zhong (2016)

- **Citation:** Yee Cheng Loon, Zhaodong Zhong. "Does Dodd-Frank Affect OTC Transaction Costs and Liquidity? Evidence from Real-Time CDS Trade Reports." Journal of Financial Economics 119(3).
- **DOI:** 10.1016/j.jfineco.2016.01.019
- **Verified:** Crossref, RePEc. **Tier:** 1. **Read:** abstract.
- **Data and sample:** Intraday index CDS quotes matched to real-time trade reports.
- **Method:** Effective spreads, price impact, and dispersion by trade type.
- **Key finding:** The average relative effective spread is 0.27% of price, or 2.73% of CDS spread. Liquidity improved after public dissemination began.
- **Means for us:** This confirms that public trade tapes support academic liquidity measures. That gives us a stress and liquidity input even without holder identity.

### 18. Du, Gadgil, Gordy and Vega (2024)

- **Citation:** Wenxin Du, Salil Gadgil, Michael B. Gordy, Clara Vega. "Counterparty Risk and Counterparty Choice in the Credit Default Swap Market." Management Science.
- **DOI:** 10.1287/mnsc.2023.4870
- **Verified:** Crossref, OpenAlex. **Tier:** 1. **Read:** abstract.
- **Data and sample:** Confidential trade repository data on single-name CDS transactions.
- **Method:** Pricing and counterparty choice analysis.
- **Key finding:** Counterparty risk has a modest effect on pricing and a large effect on counterparty choice. Nondealers are more likely to clear during a crisis.
- **Means for us:** Stress may first show up in clearing and counterparty shifts rather than in price. Public cleared-share series may be a low-cost stress input, which is untested.

### 19. Paddrik and Tompaidis (2019)

- **Citation:** Mark Paddrik, Stathis Tompaidis. "Market-Making Costs and Liquidity: Evidence from CDS Markets." Office of Financial Research Working Paper 19-01.
- **URL:** https://www.financialresearch.gov/working-papers/files/OFRwp-19-01_Market-Making-Costs-and-Liquidity-Evidence-from-CDS-Markets.pdf
- **DOI of SSRN record:** 10.2139/ssrn.3351288
- **Verified:** PDF on the OFR site, Crossref. **Tier:** 2. **Read:** abstract.
- **Data and sample:** U.S. single-name CDS, 2010 to 2016.
- **Method:** Stylized model and empirical study of dealer inventory and prices.
- **Key finding:** Dealer-client prices depend progressively more on individual dealer inventories than on aggregate inventory. Client and interdealer volumes fall, and dealer inventories decline.
- **Means for us:** Aggregate dealer positions, the only kind public data could ever show, may miss the pricing channel. This limits what a TFF dealer series can tell us.

### 20. Paddrik and Tompaidis (2026)

- **Citation:** Mark Paddrik, Stathis Tompaidis. "Intermediation Networks and Derivative Market Liquidity: Evidence from Credit Default Swap Markets." Review of Finance. Earlier version: OFR Working Paper 24-01.
- **DOI:** 10.1093/rof/rfag023
- **Verified:** Crossref, OpenAlex, OFR page. Crossref garbles the authors as "Mark, Stathis", and OpenAlex and OFR give the full names. **Tier:** 1. **Read:** abstract.
- **Data and sample:** Proprietary U.S. single-name CDS trades and positions. The OFR version covers 2010 to 2016 per its text.
- **Method:** Reconstructed networks and Shapley value connectivity measures.
- **Key finding:** Connectivity measures are strongly associated with volume, inventory management, execution costs, and bid-ask spreads.
- **Means for us:** Network structure matters, but public data do not reveal it. Treat this as a known omitted variable.

### 21. Haynes and McPhail (2017)

- **Citation:** Richard Haynes, Lihong McPhail. "The Liquidity of Credit Default Index Swap Networks." CFTC Office of the Chief Economist, June 2017.
- **URL:** https://www.cftc.gov/sites/default/files/idc/groups/public/@economicanalysis/documents/file/oce_credit_swap_liquidity.pdf
- **DOI of SSRN record:** 10.2139/ssrn.3378629
- **Verified:** PDF on the CFTC site, Crossref. **Tier:** 3. **Read:** abstract.
- **Data and sample:** Credit index swap trading, May 2014 to September 2016.
- **Method:** Customer network measures against execution cost.
- **Key finding:** Customers who trade with more dealers, or with the most active dealers, pay lower costs. For less liquid indices at least, the improvement grows with trade size.
- **Means for us:** Execution cost differs by holder, so forced exits by narrowly connected holders may cost more. That is an untested extension.

### 22. Siriwardane, Sunderam and Wallen (2025)

- **Citation:** Emil N. Siriwardane, Adi Sunderam, Jonathan Wallen. "Segmented Arbitrage." Journal of Finance.
- **DOI:** 10.1111/jofi.13469
- **Verified:** OpenAlex. Forward citation of Siriwardane (2019). **Tier:** 1. **Read:** abstract.
- **Data and sample:** 32 arbitrage spreads across equity, fixed income, and FX.
- **Method:** Correlation and driver analysis of spreads.
- **Key finding:** Average pairwise correlation is 22%. Funding and balance sheets are both segmented.
- **Means for us:** Do not import a general intermediary stress index and assume it explains CDX. CDX capacity may be local to its own participants.

### 23. Haddad, Moreira and Muir (record year 2020)

- **Citation:** Valentin Haddad, Alan Moreira, Tyler Muir. "When Selling Becomes Viral: Disruptions in Debt Markets in the COVID-19 Crisis and the Fed's Response." Review of Financial Studies.
- **DOI:** 10.1093/rfs/hhaa145
- **Verified:** Crossref (NBER and SSRN records), OpenAlex. **Tier:** 1. **Read:** abstract.
- **Data and sample:** U.S. debt markets, COVID crisis.
- **Method:** Documents price dislocations and the Fed announcement effect.
- **Key finding:** Investment grade bonds traded at a discount to CDS. ETFs traded at a discount to net asset value, more so for safer bonds. The Fed's announcement removed these dislocations. The authors' preferred explanation is an acute liquidity need among specific bond investors.
- **Means for us:** Stress can be led by cash-bond sellers rather than CDX holders. A CDX signal must allow for selling pressure that starts elsewhere.

### 24. Eisfeldt, Herskovic and Liu (2024)

- **Citation:** Andrea L. Eisfeldt, Bernard Herskovic, Shuo Liu. "Interdealer Price Dispersion and Intermediary Capacity." NBER Working Paper 32998.
- **DOI:** 10.3386/w32998
- **Verified:** Crossref, OpenAlex. **Tier:** 2. **Read:** abstract. I did not read the data section.
- **Data and sample:** Not stated in the abstract as read.
- **Method:** Relates interdealer price dispersion to bond prices and basis changes.
- **Key finding:** Higher interdealer dispersion goes with lower bond prices. It explains a substantial part of yield spread changes, the cross-section of bond returns, and basis changes.
- **Means for us:** Dispersion is a candidate capacity signal. We have not confirmed that it can be built from public CDX data.

### 25. Cboe Futures Exchange (2026)

- **Citation:** Cboe Futures Exchange, LLC. Rule Certification, Submission Number CFE-2026-011, letter to the CFTC, 16 March 2026.
- **URL:** https://cdn.cboe.com/resources/regulation/rule_filings/pending/2026/26-011-Credit-Futures-Position-Limits.pdf
- **Verified:** PDF on the Cboe site. **Tier:** 3. **Read:** product, statistics, and rationale sections.
- **Data and sample:** Exchange statistics, 2023 to 2025.
- **Method:** Regulatory filing to revise position limits. The exchange's statements support its own request.
- **Key finding:**
  - IBHY average daily open interest rose from 912 contracts in 2023 to 4,870 in 2025, or about $841m.
  - IBIG rose from 715 to 3,810, or about $540m.
  - Record open interest was about $1.8bn for IBHY (24 November 2025) and about $950m for IBIG (28 August 2025).
  - Cboe says existing position limits may constrain some larger institutions.
- **Means for us:** Cboe has real open interest but no public holder split that I could find. Position limits are also a structural cap on forced-exit size, and they changed in 2026.

## Data table

"Confirmed" means I loaded the source myself and saw the stated content. "Partial" means part of the claim is confirmed.

| Source | What it shows | Side or holder type | History | Cost | Confirmed? |
|---|---|---|---|---|---|
| CFTC TFF, API datasets gpe5-46if and yw9f-hn96 | Weekly long, short, and trader counts for Bloomberg HY (221605), IG (221606), and IG Duration-Hedged (221607) futures | Dealer, Asset Manager, Leveraged Funds, Other Reportable, Nonreportable, plus top 4 and 8 concentration | HY: 24 reports, 31 Mar to 15 Sep 2026. IG: 26 reports, 5 May to 27 Oct 2026. IG Duration-Hedged: 8 reports, 2 Jun to 27 Oct 2026, with gaps | Free | **Confirmed by API query** |
| CFTC COT, Cboe IBHY and IBIG | No such market in TFF or legacy COT. Only VIX and old Bitcoin appear for Cboe since 2018 | None | None | Free | **Confirmed absent.** The reason is not stated. The 20-trader rule is a possible cause |
| Cboe filing CFE-2026-011 | Annual average volume and open interest, plus records | None | 2023 to 2025 | Free | **Confirmed** |
| Cboe market statistics files | Daily contract data, if accessible | None | Launched 2018 per search results | Not confirmed | **Not confirmed.** The CSV path returned 403 to my script |
| CME press release and guide | Launch 17 June 2024. Open interest 6,800 contracts on 4 September 2025 | None | Launch onward | Not confirmed | **Partial.** Read through search results only, because CME blocked my script as scraping and I did not retry |
| CFTC Weekly Swaps Report | Weekly credit gross notional and volume, by cleared status and participant type | Only "SDs and MSPs" against "Other". No hedge fund split | Latest table seen 9 Oct 2026. Report data began under rules from 2013, and I did not confirm the first credit date | Free | **Confirmed** |
| CFTC Entity-Netted Notionals, CDS | Risk-adjusted netted size by sector | Swap Dealer, Bank, Other in the table I read | CDS listing ends Q4 2019 | Free | **Confirmed**. Appears discontinued for CDS |
| Part 43 public trade data, DTCC and others | Price, size, and time of swaps | None. 17 CFR 43.4 bars disclosing party identity | Not confirmed | Not confirmed | **Rule confirmed.** The DTCC site returned 503 to my requests, so I did not confirm files, history, or cost |
| DTCC TIW weekly stock and volume data | Gross and net notional | Dealer and client views not confirmed in public form | ISDA SwapsInfo says a six-month window with a one-month delay. Original weekly data began November 2008 per search results | SwapsInfo is free. CDS Kinetics may be paid | **Partial.** SwapsInfo confirmed. The old DTCC URL returned 404 or redirected |
| ISDA SwapsInfo | Traded notional, cleared share, TIW gross and net notional | Not by holder in the text read | Six-month window for TIW items | Free | **Confirmed** at swapsinfo.org |
| OFR Hedge Fund Monitor (Form PF) | Hedge fund credit gross, long, and short exposure, top 10 share, strategy data, and stress results for spread moves | Qualifying hedge funds only. Credit includes bonds, loans, CDS, and structured credit, so not CDX | Quarterly from Q1 2013, 54 observations to Q2 2026 | Free API | **Confirmed by API query** |
| BIS OTC derivatives statistics | CDS by counterparty sector, including a hedge fund label | Dealer-reported counterparties | Semiannual. Hedge fund figures seen from 2011 in the BIS article | Free | **Partial.** Dataset structure and article confirmed. My series pull failed |
| ICE Clear Credit disclosures | Quarterly clearing resources and margin disclosures | CCP level | Q1 2026 document exists per search results | Free | **Partial.** Search results only. The two URLs I tried returned 404 |
| Confidential TIW and Part 45 data | Full positions and counterparties | All | Used in papers from 2010 or 2014 | Not publicly available | **Confirmed** as described in papers |

### What the TFF numbers show so far

This is my reading of the raw reports. I ran no statistical test.

- **Very few traders:** Total traders ranged from 20 to 25 across all three contracts. The CFTC drops a market from COT below 20 reportable traders, so gaps should be expected.
- **High yield is missing:** It has not appeared since 15 September 2026. It also skipped 14 April 2026. The 20-trader rule is the likely reason, but the CFTC does not state it per contract.
- **High concentration:** On 27 October 2026, the top 4 IG traders held 76.8% of longs and 86.6% of shorts. On 15 September 2026, the top 4 HY traders held 64.6% and 77.0%, on a net basis.
- **Big single-firm effects look likely:** IG dealer net position moved from +3,362 contracts on 5 May to -4,193 on 14 July. This scale suggests a few firms can move the series.
- **Asset managers versus leveraged funds:** In IG on 5 May, asset managers were net short 5,287 and leveraged funds net long 1,980. On 27 October they were net short 2,737 and net long 2,187. This pattern resembles a hedged real-money position against funds. That reading is my inference.
- **Roll spike:** On 8 September 2026, IG open interest was 13,905 against about 7,500 either side, and HY was 7,476 against about 5,000. This may be the quarterly contract roll, but I did not confirm it. Any flow signal must filter this.

## Synthesis

### Where findings agree

1. Intermediary capacity matters for CDS prices. Siriwardane, Eisfeldt and colleagues, and Choi and colleagues reach this by different routes.
2. Arbitrage has become more costly since the crisis, and skew or basis can stay wide (Boyarchenko and colleagues, in both papers).
3. Index CDS is where stress trading concentrates (Coughlan and colleagues, ISDA 2024).
4. Hedge funds move fast and in size. Asset managers can sit on the other side.

### Where findings conflict

1. **Dealer role.** Choi and colleagues find dealers stabilize until losses or funding limits bite, whereas Boyarchenko and colleagues (2019) report that dealers switched to net buying after 2014. These likely differ by period and product, and the sign is not stable across regimes.
2. **Aggregate versus individual inventory.** Wang and Zhong use dealer net positions in index CDS. Paddrik and Tompaidis find single-name prices increasingly depend on individual dealer inventories. The market and sample differ, and I did not read a direct test of both in one setting.
3. **Who was forced in March 2020.** The CFTC paper shows hedge funds as fast net buyers of protection. Haddad and colleagues point to bond investors' liquidity need. On my reading these fit together. Bond sellers may have been the forced side, while CDX hedge funds were not visibly forced in that episode. This cuts against assuming that levered CDX holders are the ones forced out.
4. **Information versus friction.** Collin-Dufresne and colleagues find client trades carry permanent price impact. Siriwardane finds seller capital shocks move spreads. Both can be true, but a flow signal may mix them. A sharp sign reversal after stress would favor friction, which remains untested for CDX.

### Gaps

1. I found no paper testing whether holder positions forecast CDX spreads out of sample.
2. I found no academic study of positioning in CME or Cboe credit futures. Exchange material is the only source I found.
3. I found no study measuring forced unwinds directly in cleared CDX. Evidence links margins to potential spirals, and basis unwinds to bond prices.
4. I found no study of series-roll price effects. The sources cover position spikes and the March and September roll calendar. They are the CFTC paper and the IHS Markit CDS Indices Primer, November 2021 (https://cdn.ihsmarkit.com/www/pdf/1221/CDS-Indices-Primer---2021.pdf). The primer also lists index skew among relative-value trades. I read those parts only.
5. Public holder data for CDX do not exist in anything I could confirm. A positioning indicator for CDX can only use proxies. Examples are skew, cleared totals, and TFF as a small, possibly unrepresentative sample.

## Search strings

**WebSearch:**

- CDX index CDS positioning hedge fund dealer net positions predict spreads paper DTCC Trade Information Warehouse
- CDS-bond basis index skew CDX intrinsic arbitrage Boyarchenko Gupta Steele Yen "Trends in Credit Basis Spreads" OR "CDS-bond basis" dealer capital
- credit futures CFTC Traders in Financial Futures Bloomberg corporate bond index futures CME 2026 commitments of traders Cboe iBoxx IBHY IBIG
- Cboe iBoxx iShares corporate bond index futures IBHY IBIG delisted OR open interest OR CFTC commitments of traders
- index CDS CDX series roll on-the-run price effect liquidity working paper hedge funds dealers concentration swap data repository 2022 2023 2024 2025
- margin calls forced deleveraging credit default swaps cleared CDS variation margin March 2020 hedge funds index CDS unwinds paper
- hedge funds index CDS demand pressure price impact dealer inventory CDX spread predictability working paper 2023 2024 2025 regulatory data
- index CDS positions hedge funds CDX options skew single-name "index basis" OR "index skew" 2022 2023 2024 2025 working paper intermediary constraint arbitrage
- CME credit futures launch June 2024 Bloomberg U.S. Corporate index futures open interest asset managers hedge funds CDX relative value basis analysis
- Further author-title lookups for Shachar, Coughlan, Junge and Trolle, Wang and Zhong, Siriwardane, and Capponi, plus data-source searches for DTCC TIW, Form PF, and ICE Clear Credit

**Other routes:**

- Crossref title and author queries for all seed leads
- OpenAlex DOI lookups
- OpenAlex forward citations of Siriwardane (2019), Collin-Dufresne and colleagues (2020), and Riggs and colleagues (2020)
- Backward citations from the CFTC paper and the 2013 Oehmke and Zawadowski draft

OpenAlex title search hit a rate limit, so forward citations were my main recent-paper route. The search may have missed 2022 to 2026 working papers.

## Excluded

**Could not verify, so left out:**

- **Lee (2011),** cited in the Oehmke and Zawadowski draft as finding that net notional to debt predicts stock prices and CDS spreads. This is the most relevant lead I could not confirm. A search summary described a Columbia thesis with a similar result, but the repository blocked my script and I could not confirm the author or title.
- **Shachar (2011),** "Exposing the Exposed." The draft cites Shachar (2011) on order imbalance and dealer inventories. Crossref and web search did not return the record.
- **Coughlan, Haynes, Lau and Tuckman (2019),** and **Bomfim (2022).** Cited by the CFTC paper. I did not confirm a record or read them.

**Verified, but I did not read enough to state a finding:**

- Chen (2024), Finance Research Letters, DOI 10.1016/j.frl.2024.106176. It looks relevant to CDS index dealer positions. I saw only a search summary of its highlights.
- Onur, Reiffen and Sharma (2024), Journal of Financial Markets, DOI 10.1016/j.finmar.2024.100892. I could not retrieve an abstract.
- Gehde-Trapp, Gündüz and Nasev (2015), DOI 10.1016/j.jbankfin.2015.08.024. I could not retrieve an abstract.

**Read, but outside the core theme or over the entry limit:**

- He, Khorrami and Song (2022), DOI 10.1093/rfs/hhac004. Covers bond dealer inventory, not CDS positioning.
- Hilscher, Pollet and Wilson (2015), DOI 10.1017/s0022109015000228. Finds equity leads CDS, which is a useful warning that CDS flow may not lead.
- Collin-Dufresne, Junge and Trolle, "How Integrated Are Credit and Equity Markets?", OpenAlex lists Journal of Finance, DOI of SSRN record 10.2139/ssrn.3634726. Finds CDX option selling earned more than SPX option selling.
- Daures-Lescourret and Fulop (2022), DOI 10.1016/j.finmar.2022.100718. Studies liquidity around the start of DTCC position dissemination.
- ISDA (November 2024), "CDS Market Dynamics." Used as context. Index CDS was 90% or more of CDS activity and reached 94.1% in 2022, using TIW data.

**Other exclusions:**

- Personal blogs, Substack posts, and student theses, including results that appeared in searches
- Treasury basis-trade papers, because they are not about credit derivatives
