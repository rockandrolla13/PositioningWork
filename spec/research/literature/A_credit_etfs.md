# A. Credit ETFs: flows, authorised participants, baskets, premiums and price pressure

Compiled 2026-11-01. 25 ranked entries, best first for our question. A short list of checked side references follows them.

## The answer for our test

Our null result fits this literature. ETF share count is a record of arbitrage and dealer inventory work. It is not a record of investor conviction.

No paper I found tests bond ETF share count, or bond ETF short interest, as a positioning signal for credit returns. So the literature does not directly confirm our 0 of 160. It explains why the null is plausible.

The closest evidence on our share-versus-short-interest pattern has two parts.

1. Evans et al. (entry 2) show that market makers sell ETF shares short first and create the shares later. This work is mostly on equity ETFs.
2. Xiao (entry 11) finds that short interest is higher after redemption days in corporate bond ETFs.

My inference, which no paper states for credit: both make share changes and short interest move opposite ways by construction. Neither move needs to carry a view on credit.

## How to read the "Read" labels

- **Full text:** I opened the PDF or page and read the abstract and the sections I cite. I did not read every page.
- **Abstract:** I read the abstract on the named page.
- **Search excerpt:** SSRN refused direct access. I saw only abstract sentences quoted in a search result. Treat these as weaker. Check the SSRN page before relying on them.

Crossref means I matched the authors, title and year on a Crossref record for that DOI.

---

## Ranked entries

### 1. Dannhauser and Hoseinzade (2021)
- **Citation:** Dannhauser, C. D., and Hoseinzade, S. (2021). The Unintended Consequences of Corporate Bond ETFs: Evidence from the Taper Tantrum. *Review of Financial Studies*.
- **DOI:** 10.1093/rfs/hhab031
- **Verified:** Crossref and Semantic Scholar. Read: abstract.
- **Tier:** 1
- **Data and sample:** Corporate bonds and bond ETFs around the 2013 Taper Tantrum.
- **Method:** Compares yield spread changes of bonds from the same issuer.
- **Finding:** ETFs create flow-induced pressure in turmoil. Redemptions in the largest and most liquid ETFs raise yield spreads for 4 months before reverting. A CFA Institute brief quotes a draft as saying one standard deviation of outflows adds 12.4 bp by September 2013. I did not check that number in the paper.
- **For positioning:** The flow effect is real in one stress episode and it reverses. Test outflows in stress, with a long enough horizon, and do not expect an all-weather signal.

### 2. Evans, Moussawi, Pagano and Sedunov (2026)
- **Citation:** Evans, R. B., Moussawi, R., Pagano, M. S., and Sedunov, J. (2026). Operational Shorting and ETF Liquidity Provision. *Journal of Financial Economics*. Earlier title: ETF Short Interest and Failures-to-Deliver: Naked Short-Selling or Operational Shorting? (SSRN 2017).
- **DOI:** 10.1016/j.jfineco.2026.104241. Working paper: 10.2139/ssrn.2961954.
- **Verified:** Crossref for both. Read: abstract, introduction and the return test sections of the working paper (Wharton Jacobs Levy copy). I could not open the journal version, so the numbers below may differ there.
- **Tier:** 1
- **Data and sample:** US ETFs, 22 March 2004 to 31 December 2016. The return test uses domestic equity ETFs only.
- **Method:** Builds a measure of operational shorting from buy and sell imbalance minus the change in shares outstanding. Regresses future 1-month ETF returns on it.
- **Finding:** ETFs are 10% of US equity market capitalisation, over 20% of short interest and 78% of failures-to-deliver. Market makers can sell new shares into bullish demand and delay the creation. Operational shorting is a major driver of ETF short interest. It does not predict future 1-month ETF returns, unlike directional shorting measures.
- **For positioning:** This is the most direct warning for us. Raw ETF short interest mixes dealer plumbing with real bets. Separate them before testing. The bond ETF case is untested here.

### 3. Brown, Davies and Ringgenberg (2021)
- **Citation:** Brown, D. C., Davies, S. W., and Ringgenberg, M. C. (2021). ETF Arbitrage, Non-Fundamental Demand, and Return Predictability. *Review of Finance*, 25(4), 937-972.
- **DOI:** 10.1093/rof/rfaa027
- **Verified:** Crossref and EconPapers. Read: abstract. I did not read the sample details or any bond subsample.
- **Tier:** 1
- **Data and sample:** ETF primary market activity. I did not read the sample.
- **Method:** Theory plus portfolio sorts on ETF flows.
- **Finding:** Creations and redemptions signal non-fundamental demand. A portfolio short high-flow ETFs and long low-flow ETFs earns 1.1% to 2.0% a month.
- **For positioning:** This is the main positive case for flows. The sign is contrarian and the measure is the change in shares, not the level. Check that our tests allow for that. The result may not carry over to credit.

### 4. Koont, Ma, Pastor and Zeng (2025)
- **Citation:** Koont, N., Ma, Y., Pastor, L., and Zeng, Y. (2025). Steering a Ship in Illiquid Waters: Active Management of Passive Funds. *Review of Financial Studies*. Also NBER WP 30039.
- **DOI:** 10.1093/rfs/hhaf034. NBER: 10.3386/w30039.
- **Verified:** Crossref, NBER page, OpenAlex. Read: abstract, plus the data and liquidity sections of the NBER PDF.
- **Tier:** 1
- **Data and sample:** 118 passive US corporate bond ETFs, 1 January 2017 to 31 December 2020.
- **Method:** Model of basket choice, tested on realised baskets and bond-level liquidity.
- **Finding:** Sponsors steer portfolios through baskets. Baskets hold cash and a subset of index bonds, especially when bonds are illiquid. Cash is 11.6% of creation and 8.2% of redemption baskets on average. One more redemption basket cuts a bond's illiquidity by 7.3% to 15.3% of a standard deviation. Basket inclusion worsens liquidity when creations and redemptions are badly imbalanced, as in COVID.
- **For positioning:** A share change does not map to a pro-rata trade in bonds. Bond-level basket data is closer to true pressure than fund-level share count.

### 5. Shim and Todorov (2021, draft 2022)
- **Citation:** Shim, J. J., and Todorov, K. (2021). ETFs, Illiquid Assets, and Fire Sales. Working paper. A search listing also shows it as BIS Working Paper 975, which I could not open.
- **DOI:** 10.2139/ssrn.3886881
- **Verified:** Crossref. Read: abstract, introduction and basket sections of the 9 May 2022 draft (RSM copy).
- **Tier:** 2
- **Data and sample:** 116 bond ETFs, May 2017 to August 2021. ETF Global for ETFs and Markit for bonds.
- **Method:** Infers baskets from daily holdings. Implied flows match reported flows with a slope of 0.98. Fire-sale model with AP inventory, then tests.
- **Finding:** Baskets are "fractional". Investment-grade ETFs hold about 20% of holdings in baskets. High-yield ETFs hold 25% for creation and 45% for redemption. Treasury ETFs hold about 70%. Smaller basket fractions go with more persistent premiums. Discounts rise with AP inventories. This helps explain why short-maturity investment-grade ETFs had the deepest March 2020 discounts and high-yield ETFs the smallest.
- **For positioning:** Dealer inventory matters more than share count for ETF discounts. A discount can mean dealers are protecting their book, not that investors are bearish.

### 6. Todorov (2021)
- **Citation:** Todorov, K. (2021). The anatomy of bond ETF arbitrage. *BIS Quarterly Review*, March 2021.
- **URL:** https://www.bis.org/publ/qtrpdf/r_qt2103d.htm
- **Verified:** BIS page. Read: full text.
- **Tier:** 3
- **Data and sample:** Bond ETF baskets and holdings, including March to April 2020.
- **Method:** Descriptive analysis.
- **Finding:** Baskets are a small, shifting subset of holdings. For the largest bond ETF, baskets average only 3% of holdings. Creation baskets differ from redemption baskets in duration and liquidity. Tracking error rose above 200 bp for some funds in March to April 2020, against a 0.7 bp historical sector average. Decoupling baskets from holdings can act as a shock absorber.
- **For positioning:** Arbitrage in credit ETFs works through a narrow channel. A fund-level flow can touch few bonds. Note: this is the Todorov piece I could confirm. I found no separate Todorov paper titled on ETF discounts.

### 7. Pan and Zeng (2017)
- **Citation:** Pan, K., and Zeng, Y. (2017). ETF Arbitrage under Liquidity Mismatch. ESRB Working Paper 59. Also SSRN.
- **DOI:** 10.2139/ssrn.2895478. URL: https://www.esrb.europa.eu/pub/pdf/wp/esrb.wp59.en.pdf
- **Verified:** Crossref and the ESRB PDF. Read: abstract and data sections. I found no journal version.
- **Tier:** 2
- **Data and sample:** 33 passive corporate bond ETFs from the two largest issuers, 83% of passive corporate bond ETF assets, 2004 to 2015. Proprietary AP lists and TRACE with dealer identifiers.
- **Method:** Model plus AP-level tests.
- **Finding:** APs are both bond dealers and arbitrageurs, and these roles conflict. When the conflict is small, liquidity mismatch reduces arbitrage capacity. When it grows, inventory motives can distort arbitrage and produce large relative mispricing.
- **For positioning:** Creations and redemptions partly reflect the AP's own bond book. That breaks the reading of share changes as end-investor positioning.

### 8. Liu and Ge (2026)
- **Citation:** Liu, D. D., and Ge, L. (2026). From ETF Baskets to Bond Prices: Creation, Redemption, and Price Pressure. SSRN.
- **DOI:** 10.2139/ssrn.7551378
- **Verified:** Crossref. Read: search excerpt only.
- **Tier:** 2
- **Data and sample:** Not read.
- **Method:** Bond-level links between basket exposure and returns. I did not read the design.
- **Finding:** Basket imbalance is positively associated with bond returns, driven mainly by creations. Larger redemption exposure goes with lower bond returns.
- **For positioning:** This points to a bond-level basket imbalance as the better flow measure. It is very new and not peer reviewed. I could not check whether it is predictive or same-period.

### 9. Agapova, Kaprielyan and Volkov (2025)
- **Citation:** Agapova, A., Kaprielyan, M., and Volkov, N. (2025). ETFs and the price volatility of underlying bonds. *Financial Review*, 60(3), 667-700.
- **DOI:** 10.1111/fire.12426
- **Verified:** Crossref and Semantic Scholar. Read: abstract.
- **Tier:** 1
- **Data and sample:** Corporate bonds with ETF ownership and flows. I did not read the period.
- **Method:** Regressions of volatility and returns on ownership and flows.
- **Finding:** ETF ownership goes with lower bond volatility. Monthly net inflows raise volatility in investment grade and have no effect in high yield. Daily ETF flows correlate negatively with same-day bond returns. The authors read ETFs as a liquidity buffer, not a source of demand pressure as in stock ETFs.
- **For positioning:** This is a partial no-effect result that fits ours. High-yield flows did nothing for volatility, and the daily sign runs against simple flow pressure.

### 10. Rossi, Ruan and Xia (2026 draft)
- **Citation:** Rossi, M., Ruan, Y., and Xia, S. (2026 draft, first posted 2023). Real Effects of Corporate Bond ETF Ownership. Working paper.
- **DOI:** 10.2139/ssrn.4425722. Draft: https://www.shixiangxia.com/publication/rrx/RRX.pdf
- **Verified:** Crossref. Read: abstract and introduction of the 2 April 2026 draft.
- **Tier:** 2
- **Data and sample:** 196 corporate bond ETFs, TRACE, and 17,707 firm-years.
- **Method:** Index rule changes, including the 2009 HYG change, as exogenous shifts in ownership.
- **Finding:** Bonds added to ETFs see an average yield spread fall of about 106 bp. Similar analyses for LQD and IGSB also show significant reductions. Bond returns react negatively to large mutual fund outflows. They find no significant reaction to comparable ETF outflows. They credit in-kind redemption.
- **For positioning:** This is a direct no-effect result on ETF outflows and bond returns. It conflicts with entry 1. Ownership moves spreads in level, but flows may not.

### 11. Xiao (2022)
- **Citation:** Xiao, H. (2022). The Economics of ETF Redemptions. Working paper. SSRN title adds: Liquidity and Fire Sale Risks.
- **DOI:** 10.2139/ssrn.4096222. URL: https://www.aeaweb.org/conference/2023/program/paper/QzSBe3FQ
- **Verified:** Crossref. Read: abstract, introduction and the regression sections of the 29 December 2022 draft.
- **Tier:** 2
- **Data and sample:** 113 corporate bond ETFs, January 2012 to December 2021. Holdings for 104 ETFs from 2014.
- **Method:** Panel regressions of next-day outcomes on a redemption dummy with ETF and date effects.
- **Finding:** The day after a redemption, returns are 2.3 bp lower and spreads 1.3 bp wider. Mispricing is 12.6 bp larger and the short interest rate 1.0 bp larger. These effects last up to a quarter. The price multiplier is 10.5 on redemption days and 2.5 on normal days. Sponsors fill redemption baskets with bonds under price pressure.
- **For positioning:** This is the closest match to our sign pattern. Falling shares go with rising short interest in credit ETFs. The author reads the short interest as arbitrage activity, not a view. One-day timing depends on how share data is dated, so check our own lag.

### 12. Hao, Kim, Sul and Wang (2019)
- **Citation:** Hao, X., Kim, D., Sul, H. K., and Wang, Q. (2019). Underlying Bond Return Predictability by ETF Returns. SSRN.
- **DOI:** 10.2139/ssrn.3570309
- **Verified:** Crossref and Semantic Scholar. Read: abstract.
- **Tier:** 2
- **Data and sample:** Not read.
- **Method:** Monthly tests of ETF returns against NAV, bond and bond fund returns.
- **Finding:** ETF returns predict their own NAV returns and the returns of underlying bonds. Predictability is stronger for illiquid bonds, bonds with less ETF ownership and bonds with less absolute ETF flows. APs matter for passing the information on.
- **For positioning:** The ETF price carries the signal, not the quantity. Predictability is stronger where flows are smaller, which argues against flows as the carrier.

### 13. Haddad, Moreira and Muir (2021)
- **Citation:** Haddad, V., Moreira, A., and Muir, T. (2021). When Selling Becomes Viral: Disruptions in Debt Markets in the COVID-19 Crisis and the Fed's Response. *Review of Financial Studies*. Also NBER WP 27168.
- **DOI:** 10.1093/rfs/hhaa145. NBER: 10.3386/w27168.
- **Verified:** Crossref and NBER page. Read: abstract, plus a keyword scan of the ETF passages in the NBER PDF.
- **Tier:** 1
- **Data and sample:** Corporate bonds, CDS, and bond ETFs including LQD and HYG, 2020.
- **Method:** Event study and basis analysis.
- **Finding:** Liquid bond ETFs traded at a large discount to NAV. The discount was larger for Treasuries, municipals and investment grade than for high yield. The authors read this as investors selling safer assets to raise cash. The Fed's 23 March announcement helped investment grade with almost no effect on high yield. The 9 April announcement helped both.
- **For positioning:** In March 2020 selling was about raising cash, not credit views. Discounts were largest in the safest funds, so a raw discount is not a clean credit signal. Policy events can dominate any position measure.

### 14. Huang, O'Hara, Xue and Zhou (2025)
- **Citation:** Huang, A. G., O'Hara, M., Xue, J., and Zhou, X. (2025). Beyond Creation and Redemption: Principal Trading by Bond ETFs. SSRN.
- **DOI:** 10.2139/ssrn.5760891
- **Verified:** Crossref. Zhou's site lists it as revise and resubmit at the *Journal of Financial Economics*. Read: search excerpt only.
- **Tier:** 2
- **Data and sample:** Daily holdings and shares outstanding. I did not read the period.
- **Method:** Infers principal trades from holdings and shares.
- **Finding:** Principal trades occur on 35% of trading days, more often than creations and redemptions combined. Volume is comparable to primary market activity. These trades reduce tracking error in passive ETFs. They predict future bond returns in active ETFs and add about 25 bp a year.
- **For positioning:** Funds trade bonds a lot with no change in share count. Share count therefore misses much of the bond-market footprint.

### 15. Dannhauser and Karmaziene (2023)
- **Citation:** Dannhauser, C. D., and Karmaziene, E. (2023). The Dealer Warehouse: Corporate Bond ETFs. SSRN.
- **DOI:** 10.2139/ssrn.4613818. Other versions: 10.2139/ssrn.4660537 and 10.2139/ssrn.4676850.
- **Verified:** Crossref and Dannhauser's site. Read: search excerpt only.
- **Tier:** 2
- **Data and sample:** Corporate bond ETF creations and dealer data. I did not read the period.
- **Method:** Bond-level analysis of creation basket inclusion.
- **Finding:** Dealers use the primary market as a warehouse for inventory. Creations use bonds with higher supply or dealer inventory costs. Bonds with more bid-side volume are more likely to enter creation baskets. ETF ownership relates negatively to return volatility.
- **For positioning:** A rise in shares can mean dealers are parking bonds they want to sell. That is the opposite of investors adding credit risk.

### 16. Reilly (2022)
- **Citation:** Reilly, C. (2022). The Hidden Cost of Corporate Bond ETFs. SSRN.
- **DOI:** 10.2139/ssrn.4147882
- **Verified:** Crossref. Read: abstract as quoted on Quantpedia. The author's PDF link was dead.
- **Tier:** 2
- **Data and sample:** Corporate bond ETF creations. I did not read the period.
- **Method:** Returns of bonds delivered in creations.
- **Finding:** APs deliver a subset of bonds that later earn low returns. This costs ETF performance 48 bp a year. The loss is not compensation for risk or illiquidity. It comes from APs using information about future bond values.
- **For positioning:** The informed signal sits in which bonds APs deliver, not in how many shares they create.

### 17. Raddatz (2025)
- **Citation:** Raddatz K., C. E. (2025). Authorized participants' regulatory constraints and limits to ETF arbitrage during market turmoil: Evidence from the dash-for-cash episode. *Journal of Banking and Finance*, 179.
- **DOI:** 10.1016/j.jbankfin.2025.107499
- **Verified:** Crossref and IDEAS. Read: abstract.
- **Tier:** 1
- **Data and sample:** Bond ETFs and APs, March 2020.
- **Method:** Primary market activity against premiums, split by AP capital.
- **Finding:** Regulatory constraints weakened the link between primary market activity and premiums. The weakening was worst where APs had low capital ratios. It was especially strong for ETFs with less liquid bonds and for non-bank-affiliated APs.
- **For positioning:** The meaning of a share change depends on AP balance sheets. Condition on AP capital in stress.

### 18. Dinger, Muller, Rzeznik and Uhrig-Homburg (2025)
- **Citation:** Dinger, J., Muller, M., Rzeznik, A., and Uhrig-Homburg, M. (2025). Same Same But Different: The Risk Profile of Corporate Bond ETFs. SSRN.
- **DOI:** 10.2139/ssrn.5193084. Draft: http://wp.lancs.ac.uk/fofi2026/files/2026/03/FoFI-2026-108-Marcel-Mueller.pdf
- **Verified:** Crossref. Read: abstract and introduction of the December 2025 draft.
- **Tier:** 2
- **Data and sample:** Corporate bond ETFs and their bond portfolios. I did not read the period.
- **Method:** Factor exposures and a structural decomposition.
- **Finding:** ETFs carry lower liquidity risk and higher intermediary risk than their bonds. ETFs respond more to intermediary supply shocks, and the bonds respond more to demand shocks. One standard deviation worse AP balance sheets raises the ETF-NAV gap by nearly 10% of a standard deviation. Realised ETF and NAV returns are nearly identical.
- **For positioning:** ETF prices track dealer capacity more than investor demand. An AP or dealer capital measure may do more than a position measure.

### 19. Chen (2023)
- **Citation:** Chen, J. (2023). ETF Shorting Activity, Return Predictability and Information Efficiency of Underlying Securities. SSRN.
- **DOI:** 10.2139/ssrn.4527115
- **Verified:** Crossref and the University of Melbourne thesis containing the essay. Read: thesis abstract and the sample passage.
- **Tier:** 2
- **Data and sample:** ETF shorting, January 2002 to December 2021 in the market ETF test (153 market equity ETFs). The thesis text never uses the phrase "bond ETF".
- **Method:** Bi-weekly return predictability tests.
- **Finding:** ETF shorting negatively predicts future ETF returns, especially around macro news. It also predicts returns of underlying securities.
- **For positioning:** This is the bullish case for ETF short interest, but only in equities. It conflicts with entry 2 until operational shorting is removed. Do not assume it carries over to credit.

### 20. Ben-Rephael, Choi and Goldstein (2021)
- **Citation:** Ben-Rephael, A., Choi, J., and Goldstein, I. (2021). Mutual fund flows and fluctuations in credit and business cycles. *Journal of Financial Economics*, 139(1), 84-108.
- **DOI:** 10.1016/j.jfineco.2020.07.004
- **Verified:** Crossref and IDEAS. Read: abstract.
- **Tier:** 1
- **Data and sample:** Aggregate mutual fund flows. Not ETF data.
- **Method:** Time-series prediction with intra-family flow shifts towards high-yield funds.
- **Finding:** The measure predicts intermediary balance sheet growth, high-yield issuance share, and downturns of credit spread measures. It also predicts GDP growth and unemployment.
- **For positioning:** This is the strongest flow-based credit signal I found. It uses exchanges within fund families. My reading is that this filters out some liquidity trading and dealer activity, which the abstract does not say. It is a slow-moving credit cycle signal, not a trading signal.

### 21. Fulkerson, Jordan and Riley (2013)
- **Citation:** Fulkerson, J. A., Jordan, S. D., and Riley, T. B. (2013). Predictability in Bond ETF Returns. *Journal of Fixed Income*, 23(3).
- **DOI:** 10.3905/jfi.2013.23.3.050
- **Verified:** Crossref and OpenAlex. Read: abstract.
- **Tier:** 1
- **Data and sample:** Bond ETFs. I did not read the period.
- **Method:** Sorts on premiums and discounts. Long-short portfolio.
- **Finding:** Premiums and discounts persist for up to 30 days. Large-discount ETFs outperform high-premium ETFs over the next 30 days. The long-short alpha is 0.96% a month, about 11.5% a year.
- **For positioning:** The premium or discount is a more promising ETF-level signal than shares. Stale NAVs and trading costs may explain part of this. That caution is mine, not the authors'.

### 22. Dannhauser (2017)
- **Citation:** Dannhauser, C. D. (2017). The impact of innovation: Evidence from corporate bond exchange-traded funds (ETFs). *Journal of Financial Economics*, 125(3), 537-560.
- **DOI:** 10.1016/j.jfineco.2017.06.002
- **Verified:** Crossref and IDEAS. Read: abstract.
- **Tier:** 1
- **Data and sample:** Corporate bonds with ETF ownership. A search summary gives January 2009 to November 2013, which I did not confirm.
- **Method:** Two quasi-natural experiments from changes in ETF eligibility.
- **Finding:** One standard deviation more ETF ownership cuts high-yield spreads by 20.3 bp and investment-grade spreads by 9.2 bp. ETFs reduce liquidity trader participation and have an insignificant or negative effect on individual bond liquidity.
- **For positioning:** ETF ownership shifts bond valuations over the long run. That is a slow level effect, not a signal for next-period returns. A no-liquidity-gain result too.

### 23. Finnerty, Reisel and Zhong (2025)
- **Citation:** Finnerty, J. D., Reisel, N., and Zhong, X. (2025). ETFs, Creation and Redemption Processes, and Bond Liquidity. *Journal of Financial and Quantitative Analysis*, 60(4), 1891-1924.
- **DOI:** 10.1017/S0022109024000346
- **Verified:** Crossref and EconPapers. Read: abstract.
- **Tier:** 1
- **Data and sample:** Daily creation and redemption data, high yield and investment grade.
- **Method:** Bond liquidity around basket inclusion.
- **Finding:** Inclusion in a basket improves bond liquidity in both markets, including under stress, and more for redemptions. Transaction costs and bond inventory management limit arbitrage.
- **For positioning:** Redemptions are not simply bearish pressure. They can improve bond liquidity. That weakens a one-directional reading of share falls.

### 24. Marta (2021 draft)
- **Citation:** Marta, T. (2021 draft, first posted 2019). Fixed Income ETFs, Bond Liquidity, and Stressed Markets. Working paper. SSRN title: Fixed Income ETFs and Bond Liquidity.
- **DOI:** 10.2139/ssrn.3350519. Draft: https://www.aeaweb.org/conference/2022/preliminary/paper/f3fkH253
- **Verified:** Crossref. Read: abstract and sample passages of the August 2021 draft.
- **Tier:** 2
- **Data and sample:** Corporate bonds, April 2010 to April 2020.
- **Method:** Two quasi-natural experiments.
- **Finding:** ETFs lower transaction costs of their bonds. They do not hurt bond liquidity during arbitrage or stress events. ETF trading volume appears to be the transmission mechanism.
- **For positioning:** This is a no-harm result. It conflicts with entries 1, 22 and with Meli and Todorova. ETF volume may tell us more than share count.

### 25. Cai, Chuan, Henry, Shin and Tuzun (2023)
- **Citation:** Cai, F., Chuan, G., Henry, K., Shin, C., and Tuzun, T. (2023). New Insights from N-CEN: Liquidity Management at Open-End Funds and Primary Market Concentration of ETFs. *FEDS Notes*, 11 January 2023.
- **URL:** https://www.federalreserve.gov/econres/notes/feds-notes/new-insights-from-n-cen-liquidity-management-at-open-end-funds-and-pmc-of-etfs-20230111.html
- **Verified:** Federal Reserve page. Read: full text.
- **Tier:** 3
- **Data and sample:** SEC Form N-CEN, fiscal year 2021 in the table.
- **Method:** Descriptive.
- **Finding:** For US corporate bond ETFs the top three APs do 92% of creations and redemptions, and bank APs do 90%. For high yield the top-three share is 95%.
- **For positioning:** A handful of dealer banks produce the share count series. It tells us about those few balance sheets. It is not a wide sample of investors.

---

## Side references checked, not ranked

All were checked on the named record. The findings come from the abstract or page shown.

- **Falato, Goldstein and Hortacsu (2021)**, *Journal of Monetary Economics*, 10.1016/j.jmoneco.2021.07.001. Read: NBER abstract. Large sustained corporate bond fund outflows in COVID, worst for illiquid funds. The Fed programme helped reverse them. Mainly about funds in general.
- **Bhattacharya and O'Hara (2017)**, SSRN, 10.2139/ssrn.2740699. Read: abstract of the 2016 NBER conference draft. Theory only. Market makers learning from ETF prices can spread non-fundamental shocks and cause herding. I found no journal version.
- **Ben-David, Franzoni and Moussawi (2018)**, *Journal of Finance*, 10.1111/jofi.12727. Read: abstract. One standard deviation more ETF ownership goes with 16% higher daily stock volatility. Stocks only.
- **Meli and Todorova (2023)**, *Financial Markets, Institutions and Instruments*, 10.1111/fmii.12171. Read: abstract. High-yield mutual funds use ETFs for liquidity, which lowers high-yield bond liquidity on net. Investment-grade liquidity improves.
- **Aramonte and Avalos (2020)**, BIS Bulletin 6, https://www.bis.org/publ/bisbull06.htm. Read: key takeaways. Steep March 2020 corporate bond ETF discounts, linked to volatility, reduced dealer risk-taking and reaction to policy.
- **Hempel, Kim and Wermers (2022)**, OFR WP 22-01, 10.2139/ssrn.4031881. Read: abstract and sections. Fed ETF purchases eased AP constraints, with spillovers to other ETFs and bonds. Top five APs do 90.1% of US corporate bond ETF activity.
- **D'Amico, Kurakula and Lee (2020)**, Chicago Fed WP 2020-14, 10.21033/wp-2020-14. Read: abstract. ETF price jumps at Fed announcements reflected eligibility more than changes in credit or liquidity risk.
- **Gorbatikov and Sikorskaya (2021)**, SSRN, 10.2139/ssrn.3923503. Read: abstract. AP network diversity lowers mispricing in US equity ETFs.
- **Li and Zhu (2022)**, *Review of Asset Pricing Studies*, 12(4), 960-998. Read: abstract on IDEAS. DOI handle seen: 10.1093/rapstu/raac005. Equity ETF shorting predicts stock underperformance.
- **Madhavan and Sobczyk (2016)**, *Journal of Investment Management*, 14(2). Read: abstract in the journal PDF. A bond ETF's 2008 discounts reflected price discovery while its basket was illiquid.
- **IOSCO (2021)**, Exchange Traded Funds Thematic Note, OR03, https://www.iosco.org/library/pubdocs/pdf/IOSCOPD682.pdf. Read: relevant sections. Survey respondents said AP participation stayed solid in COVID. It calls bond ETF price discovery still debated.
- **Converse, Levy-Yeyati and Williams (2023)**, *Review of Financial Studies*, 10.1093/rfs/hhad014. Read: IFDP abstract. Emerging market bond ETF flows are 2.25 times as sensitive to global conditions as bond mutual fund flows.
- **Nam (2017)**, SSRN, 10.2139/ssrn.3083257. Read: abstract. Corporate bond ETF launches improved bond liquidity, most for low-volume, high-yield and long-term bonds.
- **Jiang, Li and Xiao (2024)**, SSRN, 10.2139/ssrn.4938752. Read: search excerpt only. Issuer stock portfolios predict corporate bond ETF returns, not the reverse.

---

## Synthesis

### Where findings agree

1. **Bond ETF arbitrage is narrow and dealer-driven.** Baskets are small and they change (Todorov, Shim and Todorov, Koont et al.). A few bank APs do almost all of it (Cai et al., Hempel et al.).
2. **AP inventory and capital shape creations and redemptions.** Pan and Zeng, Shim and Todorov, Raddatz, Dannhauser and Karmaziene, and Dinger et al. all point this way. This is the strongest reason to doubt share count as investor positioning.
3. **March 2020 was a cash scramble plus a dealer constraint.** Discounts were deepest in safer funds (Haddad et al., Shim and Todorov). Fed announcements reversed them.
4. **Prices carry more information than quantities.** ETF returns lead bonds (Hao et al.). Premiums predict ETF returns (Fulkerson et al.).

### Where findings conflict, and why

1. **Do ETF flows push bond prices?**
   - Yes, and it reverses after 4 months: Dannhauser and Hoseinzade.
   - No significant reaction: Rossi et al.
   - Buffer, not demand pressure: Agapova et al.
   - Likely reasons: Dannhauser and Hoseinzade study one stress period with same-issuer comparisons. The other two use broader samples and different flow measures. So the effect may exist only when dealers are constrained. That reading is mine and no paper tests it directly.
2. **Do ETFs help bond liquidity?**
   - Help: Marta, Nam, Finnerty et al.
   - Neutral or harm: Dannhauser (2017).
   - Harm in high yield only: Meli and Todorova.
   - Depends on imbalance: Koont et al.
   - Likely reasons: period, identification and liquidity measure differ. Koont et al. and Meli and Todorova offer conditions that may reconcile some of this.
3. **Why were there discounts in March 2020?**
   - Stale NAV and price discovery: Madhavan and Sobczyk's logic, and the view IOSCO reports as debated.
   - Dealer inventory: Shim and Todorov, who argue that stale pricing fails to explain why the safest funds had the deepest discounts.
   - Dealer and capital limits: Raddatz.
4. **Did APs step back?**
   - Yes for constrained APs: Raddatz.
   - No, by industry survey: IOSCO.
   - Survey answers and regressions on AP capital measure different things.
5. **Does ETF short interest predict returns?**
   - Yes in equities: Chen, Li and Zhu.
   - Operational shorting does not: Evans et al.
   - These can both hold if a directional part predicts and an operational part does not. Nobody has tested this split in credit, as far as I found.

### What the literature suggests instead of share count

Papers do not offer this as a recipe for credit. It is my reading, ordered by how much evidence supports it.

1. **Split short interest** into operational and directional parts, using the Evans et al. measure. Test only the directional part.
2. **Use basket data, not shares.** Basket imbalance and redemption exposure at bond level (Liu and Ge, Koont et al., Reilly) sit closer to real pressure.
3. **Condition on dealers.** Add AP capital and dealer inventory (Raddatz, Shim and Todorov, Dinger et al.). Test flow signals only when dealers are constrained (Dannhauser and Hoseinzade).
4. **Use price-based signals.** Test premiums and discounts and ETF lead-lag returns (Fulkerson et al., Hao et al.), with care over stale NAV.
5. **Use a filtered flow for slow credit-cycle views.** Intra-family shifts towards high yield (Ben-Rephael et al.) are the best-supported flow signal. They are not ETF data.

If we test flows again, use changes in shares rather than the level, expect a contrarian sign (Brown et al.), and allow for reversal over months (Dannhauser and Hoseinzade).

### Gaps

1. I found no test of bond ETF share count as a position.
2. I found no direct test of bond ETF short interest against credit returns or spreads. Xiao is the nearest and treats it as an outcome.
3. I found no bond-specific measure of operational shorting.
4. I found no clean test of whether LQD, HYG or JNK flows predict spreads across calm and stress periods.
5. Little work covers ETF discounts in 2022. Xiao mentions June 2022 discounts in passing. Most evidence stops by 2021.
6. Principal trading (Huang et al.) is too new to have been replicated.

---

## Search strings

**WebSearch:**
- Todorov "ETF discounts" OR "bond ETF" arbitrage creation redemption basket corporate bond paper authorized participants March 2020
- do corporate bond ETF flows predict returns or credit spreads price pressure LQD HYG working paper 2023 2024 2025
- authorized participants bond ETFs creation redemption primary market dealers inventory balance sheet 2024 paper Federal Reserve FEDS
- bond ETF ownership corporate bond liquidity spreads yield effect index inclusion no effect empirical paper
- SSRN corporate bond ETF flows return predictability mutual fund flows credit spreads "ETF flows" bond returns reversal empirical
- bond ETF short interest short selling corporate bond ETF shorts price discovery operational shorting Evans Moussawi Pagano Sedunov
- bond ETF premium discount NAV stale price March 2020 price discovery "bond ETFs" NAV informative Federal Reserve SMCCF announcement effect paper
- "From ETF Baskets to Bond Prices" Liu Ge creation redemption price pressure SSRN abstract
- corporate bond ETF demand elasticity price impact flows inelastic bond ETF flows bond returns "bond ETF" 2024 2025 working paper dealer inventory creations
- short selling of bond ETFs credit: "bond ETF" short interest predicts returns OR spreads; ETF shorting informed credit market hedging
- Brown Davies Ringgenberg "ETF arbitrage, non-fundamental demand, and return predictability" share creations predict negative returns Review of Finance
- Converse Levy-Yeyati Williams "How ETFs amplify the global financial cycle in emerging markets"; Dannhauser Karmaziene "Warehousing Corporate Bonds via ETFs" "The Dealer Warehouse" abstract authors
- "bond ETF" flows information market timing institutional investors CDX versus ETF hedging, price discovery corporate bond ETF lead credit default swap index paper 2023 2024 2025 2026
- bond ETF discount 2022 sell-off premium discount fixed income ETFs mispricing bond dealers constrained paper; "ETF" "corporate bonds" fire sale spreads index rebalancing HYG LQD month-end rebalancing price pressure
- Li Zhu "Short Selling ETFs" Review of Asset Pricing Studies abstract; Karmaziene Sokolovski short selling equity ETFs liquidity JFQA
- Dannhauser "The impact of innovation" corporate bond ETFs abstract; Dannhauser Hoseinzade taper tantrum ETF outflows yield spreads abstract
- Bhattacharya O'Hara "Can ETFs Increase Market Fragility" abstract herding information linkages; Pan Zeng "ETF arbitrage under liquidity mismatch" published
- "Beyond Creation and Redemption: Principal Trading by Bond ETFs" Huang O'Hara Xue Zhou
- Dannhauser Karmaziene "The Dealer Warehouse" corporate bond ETFs creations dealer inventory; "Corporate Bond ETFs & Volatility" abstract
- Reilly "The Hidden Cost of Corporate Bond ETFs" abstract; Chen "ETF Shorting Activity, Return Predictability and Information Efficiency of Underlying Securities" abstract
- Ben-Rephael Choi Goldstein "Mutual fund flows and fluctuations in credit and business cycles" abstract
- Raddatz "Authorized participants' regulatory constraints and limits to ETF arbitrage" dash-for-cash abstract

**Record checks:** Crossref bibliographic queries, Semantic Scholar and OpenAlex by DOI, then NBER, RePEc (IDEAS and EconPapers), BIS, ESRB, OFR, Federal Reserve and author pages.

## Excluded, and why

**Found on a record, but I read no abstract or text, so I state no finding:**
- Dannhauser and Karmaziene (2025), Corporate Bond ETFs and Volatility, 10.2139/ssrn.5253685.
- Du (2023), Inventory in Liquidity Transformation, 10.2139/ssrn.4653799.
- Cotelioglu (2024), *Journal of Empirical Finance*, 10.1016/j.jempfin.2024.101520.
- Rhodes and Mason (2023), *Journal of Financial Markets*, 10.1016/j.finmar.2022.100772.
- Korukmez (2025), 10.2139/ssrn.5080567.
- Ma, Xiao and Zeng (2022), *Review of Financial Studies*, 10.1093/rfs/hhac007. It is about mutual funds.
- Pan, Van Ness and Van Ness (2024), 10.2139/ssrn.4765211.
- Karmaziene and Sokolovski (2021), *JFQA*, 10.1017/S0022109021000181. It covers equity ETFs. I saw only a search summary.

**Other exclusions:**
- Dannhauser and Karmaziene (2025), Warehousing Corporate Bonds via ETFs, 10.2139/ssrn.5905083. I saw one search excerpt on creation events and could not tell how it relates to The Dealer Warehouse.
- Cable et al. (2025), arXiv 2504.06289. It is a master's thesis on hedging, and I read only the title pages.
- Municipal bond ETF papers. They are outside corporate credit.
- BlackRock's SEC presentation, the Jane Street note and issuer blogs. They are interested parties, and the SEC site blocked my fetch.
- Trading commentary and flow trackers. They contain no tests.
- A claim on two low-quality sites that BIS research found ETF prices lead NAV by 24 to 48 hours. I could not find it in a BIS document.

**Access limits:** SSRN, ScienceDirect and Oxford refused direct fetches. Entries 8, 14 and 15 rest on search excerpts alone, which is the weakest evidence in this file. Entries 2 and 13 rest partly on working papers, whose numbers may differ from the journal versions.
