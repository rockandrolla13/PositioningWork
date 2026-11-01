# Literature review D: positioning and pain indicators

Theme: the theory and evidence behind positioning and "pain" indicators, used as the comparison set for the Pain Monitor.
Prepared 2026-11-01. It holds 30 entries, best first.

## The answers first

1. **Do academics find the same decay?** Yes, in equities. Published signals keep about half their performance after publication. I found no study that tests post-publication decay in CFTC positioning signals. So our 0 of 53 has no direct academic match.
2. **Is our 0 of 53 proof of decay?** No. With about 14 independent observations, the test can barely see an effect of the size the literature would predict. See "Test design" below.
3. **How do academics measure cost basis?** Three ways. They weight past prices by volume turnover, or they build it from fund holdings, or they read book values from insurer filings. I found no paper that estimates cost basis from open interest or CFTC data. Our method has no published validation.
4. **What makes losses force selling?** I found no evidence that a loss alone is enough. The evidence points to a loss combined with a binding limit: a leverage limit, a regulatory capital limit, or investor outflows from an illiquid fund.
5. **Is there a better cost-basis method than ours?** Possibly, and it is cheap to test. Our ledger moves only on net position changes. Grinblatt and Han also retire old lots with trading volume. An splits gains from losses. See "Cost-basis options" below.

## How to read the entries

- **Read** says what I actually read. "Abstract" means the abstract only. "Text" means I also read passages of the paper.
- **Tier**: 1 is a peer-reviewed journal, 2 is a working paper or preprint, 3 is industry or official.
- **Year**: Crossref often gives the online date. Where it differs, I give the year of the journal volume.
- The credit line in each entry is my own inference unless it says otherwise. No entry below tests a credit positioning indicator.

## A. Cost basis and the disposition effect

### 1. Grinblatt and Han (2005)
Grinblatt, M., and B. Han. "Prospect theory, mental accounting, and momentum." Journal of Financial Economics 78(2), 311-339.
- DOI: 10.1016/j.jfineco.2004.10.006
- Verified: Crossref. Tier 1.
- Read: RePEc abstract of the journal version. Text of NBER working paper 8734, the earlier version.
- Data: NYSE and AMEX stocks, weekly, July 1962 to December 1996, 1,799 weeks (working paper).
- Method: the reference price is a weighted sum of past prices. The weight on week t-n is the turnover that week, multiplied by (1 minus turnover) for every later week. They truncate at five years. This treats every share as equally likely to trade. Fama-MacBeth regressions test returns on the gain measure.
- Finding: the aggregate unrealized gain variable appears to generate momentum profits. Past returns have no predictive power for the cross-section once it is controlled for. At 1% weekly turnover the implied holding period is about 2 years.
- For credit: this is the standard estimator. Its removal rule matches our pro-rata rule, but it retires lots using volume, not only net changes.

### 2. An (2016)
An, L. "Asset Pricing When Traders Sell Extreme Winners and Losers." Review of Financial Studies 29(3), 823-861.
- DOI: 10.1093/rfs/hhv060
- Verified: Crossref and RePEc. Tier 1.
- Read: abstract. Text of the December 2013 draft, titled "The V-shaped Disposition Effect."
- Data: US stocks over about forty years (draft).
- Method: splits the overhang into a gain part and a loss part, using daily prices lagged 10 trading days. The combined measure in the draft is Gain minus 0.2 times Loss.
- Finding: stocks with large unrealized gains and large unrealized losses both outperform next month. Monthly alpha is 0.5% to 1%, with a Sharpe ratio of 1.5. The measure subsumes the capital gains overhang. The loss side predicts returns in the opposite direction to momentum.
- For credit: pain may not be one-directional. Test large gains and large losses as separate signals, not a single signed score.

### 3. Frazzini (2006)
Frazzini, A. "The Disposition Effect and Underreaction to News." Journal of Finance 61(4), 2017-2046.
- DOI: 10.1111/j.1540-6261.2006.00896.x
- Verified: Crossref. Tier 1.
- Read: abstract and text (author PDF).
- Data: mutual fund holdings and US stocks, 1980 to 2002.
- Method: builds a reference price for each stock from actual fund holdings, using first-in-first-out matching.
- Finding: drift after news is largest when the capital gain and the news have the same sign. An event strategy earns monthly alphas above 200 basis points. A footnote says LIFO, highest-in-first-out, last trade price, last buy price and averages of past prices do not alter the main results.
- For credit: holdings beat volume as a source where they exist. The removal rule may matter little, which we can test because our ledger already has three rules.

### 4. Riley, Summers and Duxbury (2020)
Riley, C., B. Summers, and D. Duxbury. "Capital Gains Overhang with a Dynamic Reference Point." Management Science 66(10), 4726-4745.
- DOI: 10.1287/mnsc.2019.3404
- Verified: Crossref. Tier 1.
- Read: abstract.
- Data: experiments on real stock price paths, 6 months to 5 years, plus US equity returns.
- Method: replaces the fixed purchase price with a mix of salient points in the price path, with weights taken from the experiment.
- Finding: the composite overhang predicts returns and future volume better than the traditional one.
- For credit: entry price may not be the only anchor. Recent highs and lows in spread could be added and tested.

### 5. Ben-David and Hirshleifer (2012)
Ben-David, I., and D. Hirshleifer. "Are Investors Really Reluctant to Realize Their Losses? Trading Responses to Past Returns and the Disposition Effect." Review of Financial Studies 25(8), 2485-2532.
- DOI: 10.1093/rfs/hhs077
- Verified: Crossref. Tier 1.
- Read: abstract.
- Data: investor-level trading (the abstract does not name the sample).
- Method: selling probability as a function of profit.
- Finding: the selling schedule is V-shaped. At short holding periods, investors sell big losers more readily than small losers. There is little evidence of a jump in selling at zero profit.
- For credit: do not assume a sharp trigger at the entry price. "Under water" may not be a meaningful threshold.

### 6. Cici (2012)
Cici, G. "The Prevalence of the Disposition Effect in Mutual Funds' Trades." Journal of Financial and Quantitative Analysis 47(4), 795-820.
- DOI: 10.1017/s0022109012000348
- Verified: Crossref. Tier 1.
- Read: abstract.
- Data: US equity mutual funds.
- Method: compares realization of gains and losses across funds and over time.
- Finding: funds on average prefer to realize losses over gains. A substantial fraction still shows the disposition effect. Learning has reduced it over time, which the author reads as research influencing practice. Funds with outflows and team management sell more winners than losers.
- For credit: professional investors may not behave as the retail evidence implies. This effect itself appears to have weakened over time.

### 7. Hincapié-Salazar and Agudelo (2020)
Hincapié-Salazar, J., and D. Agudelo. "Is the disposition effect in bonds as strong as in stocks? Evidence from an emerging market." Global Finance Journal 46, 100508.
- DOI: 10.1016/j.gfj.2019.100508
- Verified: Crossref and RePEc. Tier 1.
- Read: abstract.
- Data: proprietary transactions with investor IDs from one emerging market exchange that trades stocks and bonds.
- Method: Odean's (1998) measure, applied to treasury bonds and stocks.
- Finding: there is some disposition effect in treasury bonds, but much lower than in stocks. Local individuals and family offices show it. Long-term institutions, brokerage firms and foreign investors do not. The authors call this the first such evidence in a fixed-income market.
- For credit: this is the closest direct test I found, and it points against us. The holders who dominate US credit may not show this bias.

## B. Credit: when real losses change bond trading

### 8. Fang (2024, working paper)
Fang, C. "Unrealized Trading Gains." SSRN working paper.
- DOI: 10.2139/ssrn.4973722
- Verified: Crossref record and author PDF. Tier 2.
- Read: abstract and text of the April 2025 version. A September 2025 version exists, but I could not retrieve it.
- Data: insurer book values and holdings from NAIC filings, FISD, TRACE. Crisis windows December 2007 to June 2009 and February to April 2020.
- Method: compares different insurers trading the same bond at the same time. This removes confounds such as momentum.
- Finding: insurers with more unrealized losses provide less liquidity against fund fire sales. At the bond level, the price impact of flow-induced selling is -0.406 percentage points of yield spread per 1% of amount outstanding. One standard deviation more peer unrealized loss adds a further -0.420, or 103%. The bond's own unrealized loss has no statistically important effect. The shadow cost of regulatory capital is $0.81 on average.
- For credit: this is the best template we have. It uses a measured cost basis, not an estimate. Losses here reduce buying, which is a different channel from forced selling.

### 9. Ellul, Jotikasthira, Lundblad and Wang (2015)
Ellul, A., C. Jotikasthira, C. Lundblad, and Y. Wang. "Is Historical Cost Accounting a Panacea? Market Stress, Incentive Distortions, and Gains Trading." Journal of Finance 70(6), 2489-2538.
- DOI: 10.1111/jofi.12357
- Verified: Crossref. Tier 1.
- Read: journal abstract and the abstract of the December 2011 draft.
- Data: insurer transactions and positions during the financial crisis.
- Method: uses differences in accounting treatment between life and property and casualty insurers, and across US states.
- Finding: insurers with less market-value recognition avoid selling downgraded asset-backed securities. They instead sell unrelated bonds with high unrealized gains, which transmits shocks across markets.
- For credit: under stress, some holders sell their winners and keep their losers. A pain indicator that assumes losers get sold could have the wrong sign for insurers.

## C. What makes losses force selling

### 10. Kang, Rouwenhorst and Tang (2020)
Kang, W., K. G. Rouwenhorst, and K. Tang. "A Tale of Two Premiums: The Role of Hedgers and Speculators in Commodity Futures Markets." Journal of Finance 75(1), 377-417.
- DOI: 10.1111/jofi.12845
- Verified: Crossref. Tier 1.
- Read: journal abstract. Text of the December 2016 draft. The numbers below come from the draft and may differ in print.
- Data: 26 commodity futures markets, weekly CFTC reports, January 1994 to about October 2014.
- Method: splits position changes into short-term liquidity demand and long-term hedging demand. Portfolio sorts and panel regressions follow. Capital loss appears to be built from last week's net position and the return, so it needs no entry price. The equation did not extract cleanly from the PDF, so check it before copying it.
- Finding: the two components predict returns with opposite signs. The sort earns 67 basis points over the 20 days after the report. After a large hedger capital loss, the return impact of a given position change more than doubles, from 8.9 to 21.2 basis points. The results hold in both halves of the sample. The draft reports no out-of-sample test, based on a word search.
- For credit: this is the closest published analogue to a pain signal. Its weekly loss measure is a simple benchmark for our ledger. The level of positioning mixes two opposing signals.

### 11. Bian, He, Shue and Zhou (2018, working paper)
Bian, J., Z. He, K. Shue, and H. Zhou. "Leverage-Induced Fire Sales and Stock Market Crashes." NBER Working Paper 25040.
- DOI: 10.3386/w25040
- Verified: Crossref and NBER. Tier 2.
- Read: abstract.
- Data: account-level brokerage and shadow-financed margin accounts, China, 2015 crash.
- Method: stock-date and account fixed effects, relating selling to distance from the leverage limit.
- Finding: investors sell heavily as leverage nears the limit. Stocks held by accounts near limits see selling pressure and abnormal price declines, which later reverse.
- For credit: the trigger is distance to a limit, not the size of the loss. The expected return signature is a decline, then a reversal.

### 12. Brunnermeier and Pedersen (2009)
Brunnermeier, M., and L. Pedersen. "Market Liquidity and Funding Liquidity." Review of Financial Studies 22(6), 2201-2238.
- DOI: 10.1093/rfs/hhn098
- Verified: Crossref. Tier 1.
- Read: abstract.
- Data: none. This is a theory paper.
- Method: a model linking trader funding to market liquidity.
- Finding: under certain conditions margins are destabilizing, and the two liquidities reinforce each other into spirals. It predicts speculators' capital drives liquidity and risk premiums.
- For credit: pain should matter most when funding and volatility are stressed. It implies a conditional test, not an unconditional one.

### 13. Siriwardane (2019)
Siriwardane, E. "Limited Investment Capital and Credit Spreads." Journal of Finance 74(5), 2303-2347.
- DOI: 10.1111/jofi.12777
- Verified: Crossref. Tier 1.
- Read: abstract.
- Data: proprietary credit default swap positions.
- Method: measures capital shocks at protection sellers as their CDS portfolio margin payments.
- Finding: seller capital shocks explain 12% of the time-series variation in weekly spread changes. Standard credit factors explain 18%. The shocks carry information beyond institution-wide constraints.
- For credit: this is the strongest direct evidence for credit. Mark-to-market losses on positions do move spreads. Note that it uses real positions and a weekly horizon, and its result is about spread changes.

### 14. Goldstein, Jiang and Ng (2017)
Goldstein, I., H. Jiang, and D. Ng. "Investor flows and fragility in corporate bond funds." Journal of Financial Economics 126(3), 592-613.
- DOI: 10.1016/j.jfineco.2016.11.007
- Verified: Crossref and RePEc. Tier 1.
- Read: RePEc abstract.
- Data: corporate bond mutual funds.
- Method: flow-to-performance regressions.
- Finding: the relation is concave, because outflows respond more to bad performance than inflows do to good. The effect is stronger when funds hold more illiquid assets and when market illiquidity is high.
- For credit: fund losses transmit to selling through investors, not through a manager's entry price. Fund performance and illiquidity may be better inputs than cost basis.

### 15. Choi, Hoseinzade, Shin and Tehranian (2020)
Choi, J., S. Hoseinzade, S. Shin, and H. Tehranian. "Corporate bond mutual funds and asset fire sales." Journal of Financial Economics 138(2), 432-457.
- DOI: 10.1016/j.jfineco.2020.05.006
- Verified: Crossref and RePEc. Tier 1.
- Read: RePEc abstract.
- Data: corporate bond fund holdings, including the 2008 crisis.
- Method: compares same-issuer bonds held by funds with different outflows, which controls for issuer news.
- Finding: little evidence that redemptions cause fire-sale price pressure. Funds keep liquidity cushions and selectively trade liquid assets.
- For credit: this conflicts with the forced-selling story. Issuer news may account for apparent fire sales, so a pain test needs to control for it.

## D. Positioning and open interest as predictors

### 16. De Roon, Nijman and Veld (2000)
De Roon, F., T. Nijman, and C. Veld. "Hedging Pressure Effects in Futures Markets." Journal of Finance 55(3), 1437-1456.
- DOI: 10.1111/0022-1082.00253
- Verified: Crossref. Tier 1.
- Read: abstract.
- Data: 20 futures markets across financial, agricultural, mineral and currency groups.
- Method: a model and regressions of returns on own-market and cross-market hedging pressure.
- Finding: own and within-group cross hedging pressure both affect futures returns after controlling for systematic risk.
- For credit: pressure from related markets may matter. An index-level signal could use rates or equity positions as well.

### 17. Sanders, Irwin and Merrin (2007)
Sanders, D., S. Irwin, and R. Merrin. "Smart Money? The Forecasting Ability of CFTC Large Traders." Proceedings of the NCCC-134 Conference, Chicago.
- URL: https://farmdoc.illinois.edu/assets/meetings/nccc134/conf_2007/pdf/confp01-07.pdf
- Verified: conference paper PDF. A search listing shows a journal title with "in Agricultural Futures Markets" added, but I could not confirm the journal record, so I cite only the conference paper. Tier 2.
- Read: abstract and introduction.
- Data: agricultural futures, weekly CFTC data, 1992 to 2006.
- Method: bivariate Granger causality.
- Finding: very little evidence that positions lead returns. Substantial evidence that traders respond to price. Non-commercial traders tend to follow trends. The authors say the results generally do not support using this data to predict markets.
- For credit: a negative result on plain positioning, predating our test by over a decade. Prices may lead our positions, so check the lead-lag direction first.

### 18. Hong and Yogo (2012)
Hong, H., and M. Yogo. "What does futures market interest tell us about the macroeconomy and asset prices?" Journal of Financial Economics 105(3), 473-490.
- DOI: 10.1016/j.jfineco.2012.04.005
- Verified: Crossref and RePEc. Tier 1.
- Read: RePEc abstract. Text of NBER working paper 16712.
- Data: commodities from 1966, other futures from 1984 (working paper).
- Method: predictive regressions on open interest growth, with controls including basis, hedging imbalance and past returns.
- Finding: in the working paper, one standard deviation more commodity open interest raises expected commodity returns by 0.72% per month, with a t-statistic of 2.47. It also predicts bond returns and the short rate. The effect is weaker in currency, bond and stock markets. The working paper has no out-of-sample test, based on a word search.
- For credit: open interest may carry information without any entry price, so it makes a useful baseline. The evidence is weakest outside commodities and has no out-of-sample support.

### 19. Huang, Li, Wang and Zhou (2020)
Huang, D., J. Li, L. Wang, and G. Zhou. "Time series momentum: Is it there?" Journal of Financial Economics 135(3), 774-794.
- DOI: 10.1016/j.jfineco.2019.08.004
- Verified: Crossref. Tier 1.
- Read: abstract.
- Data: a large cross-section of assets.
- Method: asset-by-asset regressions in and out of sample, plus parametric and nonparametric bootstraps.
- Finding: little evidence of predictability asset by asset. The large pooled t-statistic falls below the bootstrap critical values. Strategy profit looks similar to one using only historical means.
- For credit: pooling raises power, but pooled t-statistics can mislead. Any pooled pain test should use a bootstrap.

## E. Crowding and forced unwinds

### 20. Lou and Polk (2022)
Lou, D., and C. Polk. "Comomentum: Inferring Arbitrage Activity from Return Correlations." Review of Financial Studies 35(7), 3272-3302.
- DOI: 10.1093/rfs/hhab117
- Verified: Crossref. Tier 1.
- Read: abstract.
- Data: US stocks.
- Method: measures crowding by the abnormal high-frequency return correlation among momentum stocks.
- Finding: when comomentum is low, momentum is stabilizing. When it is high, momentum stocks strongly revert.
- For credit: crowding can be inferred from returns alone, with no position data. Such a measure could condition our signal.

### 21. Barroso, Edelen and Karehnke (2022)
Barroso, P., R. Edelen, and P. Karehnke. "Crowding and Tail Risk in Momentum Returns." Journal of Financial and Quantitative Analysis 57(4), 1313-1342.
- DOI: 10.1017/s0022109021000624
- Verified: Crossref. Tier 1.
- Read: abstract.
- Data: institutional holdings and momentum returns.
- Method: a crowding model and empirical crash-risk tests.
- Finding: the relation between holdings-based crowding proxies and expected crash risk is generally negative. The authors cast theoretical and empirical doubt on crowding as a stand-alone source of tail risk.
- For credit: high positioning alone may not predict a crash. This supports testing crowding only together with a trigger.

## F. Replication, decay and multiple testing

### 22. McLean and Pontiff (2016)
McLean, R. D., and J. Pontiff. "Does Academic Research Destroy Stock Return Predictability?" Journal of Finance 71(1), 5-32.
- DOI: 10.1111/jofi.12365
- Verified: Crossref. Tier 1.
- Read: abstract.
- Data: 97 predictors of US stock returns.
- Method: compares in-sample, post-sample and post-publication returns.
- Finding: returns are 26% lower out of sample and 58% lower after publication. The 26% is an upper bound on data mining. Declines are larger for signals with higher in-sample returns.
- For credit: plan on keeping about half of a backtest's return. A sell-side backtest may deserve a bigger haircut.

### 23. Falck, Rej and Thesmar (2022)
Falck, A., A. Rej, and D. Thesmar. "When do systematic strategies decay?" Quantitative Finance 22(11), 1955-1969.
- DOI: 10.1080/14697688.2022.2098810
- Verified: Crossref and arXiv 2105.01380. Tier 1.
- Read: short journal abstract. Text of the arXiv version, "Why and how systematic strategies decay."
- Data: a large set of published stock anomalies.
- Method: predicts each signal's Sharpe decay from ex-ante characteristics.
- Finding: Sharpe ratios fall by about one half after publication. Publication year alone explains 30% of the variance in decay. Each later year adds 5 percentage points of decay. Signal complexity and sensitivity to outliers add another 15%. Arbitrage-related variables have marginal power.
- For credit: our signal has many construction steps, so these results point to above-average decay risk. Simpler versions deserve a test.

### 24. Hou, Xue and Zhang (2020)
Hou, K., C. Xue, and L. Zhang. "Replicating Anomalies." Review of Financial Studies 33(5), 2019-2133.
- DOI: 10.1093/rfs/hhy131
- Verified: Crossref. Tier 1.
- Read: abstract.
- Data: 452 equity anomalies.
- Method: NYSE breakpoints and value weights to reduce the effect of microcaps.
- Finding: 65% fail at a t-value of 1.96. 82% fail at 2.78. Replicated effects are much smaller than first reported.
- For credit: results depend on how much weight illiquid names get. Liquid-only tests may be the honest ones.

### 25. Jensen, Kelly and Pedersen (2023)
Jensen, T., B. Kelly, and L. Pedersen. "Is There a Replication Crisis in Finance?" Journal of Finance 78(5), 2465-2518.
- DOI: 10.1111/jofi.13249
- Verified: Crossref. Tier 1.
- Read: abstract.
- Data: factors in 93 countries.
- Method: a Bayesian model of factor replication.
- Finding: most factors replicate, cluster into 13 themes, and work out of sample. Evidence strengthens with many factors, rather than weakens.
- For credit: treat our 53 tests as one or a few themes. A shrinkage model suits correlated tests better than counting passes.

### 26. Harvey and Liu (2020)
Harvey, C., and Y. Liu. "False (and Missed) Discoveries in Financial Economics." Journal of Finance 75(5), 2503-2553.
- DOI: 10.1111/jofi.12951
- Verified: Crossref. Tier 1.
- Read: abstract.
- Data: fund and factor selection applications.
- Method: a double bootstrap that calibrates both false positives and misses.
- Finding: it sets t-statistic hurdles tied to a chosen false discovery rate. Current methods lack power to detect outperforming managers.
- For credit: a failed test is not proof of no effect. We should report our chance of a miss, not only of a false alarm.

### 27. Goyal, Welch and Zafirov (2024)
Goyal, A., I. Welch, and A. Zafirov. "A Comprehensive 2022 Look at the Empirical Performance of Equity Premium Prediction." Review of Financial Studies 37(11), 3490-3557.
- DOI: 10.1093/rfs/hhae044
- Verified: Crossref and RePEc. Tier 1.
- Read: RePEc abstract.
- Data: 29 variables from 26 papers plus the original 17, with samples ending in 2021.
- Method: in-sample and out-of-sample tests.
- Finding: more than one-third of the new variables lose significance even in sample. Half of the rest perform poorly out of sample. A small number still work.
- For credit: this is the closest match to our exercise, a time-series predictor over a few market-wide episodes. Our result is common in this setting.

### 28. Inoue and Kilian (2005)
Inoue, A., and L. Kilian. "In-Sample or Out-of-Sample Tests of Predictability: Which One Should We Use?" Econometric Reviews 23(4), 371-402.
- DOI: 10.1081/etc-200040785
- Verified: Crossref and RePEc. Tier 1.
- Read: RePEc abstract.
- Data: none reported in the abstract. It is an econometric analysis.
- Method: analysis of why the two kinds of test disagree.
- Finding: data mining, misspecification and structural change do not plausibly explain the gap. The authors explain it by the higher power of in-sample tests in many situations. They conclude in-sample results are typically more credible.
- For credit: a failed out-of-sample split can reflect low power alone. The 2019 split should not be our only test.

### 29. Hjalmarsson (2010)
Hjalmarsson, E. "Predicting Global Stock Returns." Journal of Financial and Quantitative Analysis 45(1), 49-80.
- DOI: 10.1017/s0022109009990469
- Verified: Crossref and Federal Reserve IFDP 933. Tier 1.
- Read: abstract of the IFDP version.
- Data: over 20,000 monthly observations from 40 markets.
- Method: panel predictive regressions with a robust estimator.
- Finding: the standard fixed-effects estimator suffers severe size distortions in typical return regressions. The short rate and term spread are fairly robust predictors in developed markets. Dividend and earnings yields are not.
- For credit: pooling many contracts is a known route to more power, but standard panel inference is unsafe here.

### 30. Boudoukh, Richardson and Whitelaw (2008)
Boudoukh, J., M. Richardson, and R. Whitelaw. "The Myth of Long-Horizon Predictability." Review of Financial Studies 21(4), 1577-1605.
- DOI: 10.1093/rfs/hhl042
- Verified: Crossref and NBER. Tier 1.
- Read: abstract of NBER working paper 11841.
- Data: stock returns and persistent predictors such as dividend yields.
- Method: analytical correlation of estimators across horizons under the null.
- Finding: estimators are almost perfectly correlated across horizons. For dividend yield levels the correlation is 99% between 1 and 2 years, and 94% between 1 and 5 years. Coefficients and R-squared grow with horizon even with no predictability.
- For credit: a position-based signal is persistent, so 4, 13 and 26-week results are not separate evidence. Rising strength with horizon proves little.

## Synthesis

### Where findings agree

1. **Decay is normal.** Equity signals lose about half after publication (entries 22, 23). Time-series predictors fare poorly when samples are extended (27).
2. **Losses matter through constraints.** Leverage limits, regulatory capital and margin all show effects when real data on positions or limits exist (8, 10, 11, 13).
3. **Forced flows reverse.** Declines followed by reversals appear in the margin account evidence (11). The Coval and Stafford fund evidence listed below is consistent with this.

### Where findings conflict, and why

1. **Do positions predict returns?** Hedging pressure works in risk-premium tests (10, 16). Granger tests find almost nothing (17). The likely reason is that the level mixes hedging and liquidity demand with opposite signs (10). This is my reading, and neither side tests it against the other.
2. **Does overhang explain momentum?** Grinblatt and Han say yes (1). An says the loss side goes the other way (2). They differ in whether gains and losses are pooled.
3. **Do bond fund redemptions cause fire sales?** Fragility evidence suggests they could (14). Choi and coauthors find little price pressure once they control for issuer news (15). Choi and coauthors attribute the gap to issuer-level controls and to fund liquidity management.
4. **Do holders sell losers or winners under stress?** Levered accounts sell as limits approach (11). Insurers sell winners and keep losers (9). So the holder type sets the sign. We cannot see holder type in open interest.
5. **Is there a replication crisis?** Hou and coauthors say yes (24). Jensen and coauthors say no (25). They differ in portfolio weighting and in the statistical model, and that may account for the gap. Neither abstract tests the other's method.

### Cost-basis options

These are my inferences from the papers and from `spec/posmon/ledger.py`. In that file, lots change only when the net position changes. A week with no net change leaves all lots untouched.

1. **Add volume-based retirement.** Grinblatt and Han decay every lot by turnover each week. Our rule has no such decay. If contracts change hands without a net change, our entry estimates grow stale. Test this first, because it changes the signal most.
2. **Split gains from losses.** An's result is cheap to test. Our signed pain score pools them.
3. **Compare with a no-ledger benchmark.** Kang and coauthors appear to use last week's position times the return. If this matches our signal, the ledger adds nothing.
4. **Test the removal rule, then stop tuning it.** Frazzini found rule choice does not alter his main results. We have three rules ready to compare.
5. **Use measured cost basis in credit.** Insurer book values in NAIC filings are real, as Fang shows. They have no price-estimation error, though they cover only insurers.

### What makes losses force selling

The evidence supports four conditions. I have not seen them tested together.

1. The holder has a binding limit (11, 12, 13).
2. Funding or liquidity is already stressed (12, 14).
3. The holder cannot hide the loss. Book-value holders can hold on, and they sell other bonds instead (8, 9).
4. Funds face redemptions and hold illiquid assets (14). Their liquidity buffers can absorb this (15).

A crowded position alone is not enough (21). Being under water may not be a threshold (5).

### Test design

Why our test is weak. This arithmetic is mine. With 14 independent observations, t = 2 needs a mean of about 0.53 standard deviations per observation. Suppose a signal just cleared that bar in sample and then lost half, as entry 22 suggests. Its expected t would then be about 1, and one test would pass about 17% of the time. The 53 tests share the same few episodes, so they are not 53 chances. Zero passes therefore cannot separate decay from low power.

How to get more power:

1. **Test at short horizons.** Use weekly, non-overlapping returns. Long horizons add little independent evidence with a persistent signal (30). The strongest related results are weekly (10, 13).
2. **Pool across contracts.** Use a bootstrap and a robust estimator, as standard panel inference and pooled t-statistics mislead (19, 29). Cross-contract correlation limits the gain in credit, because credit contracts move together.
3. **Change the outcome.** Test price impact and reversal, or spread changes, instead of the level of return (8, 11, 13).
4. **Test interactions.** Ask whether the effect grows when losses and constraints coincide (8, 10). This uses cross-sectional variation at each date.
5. **Report whole-sample and split results together.** In-sample tests have more power (28). The split still guards against overfitting (27). Fix one primary signal in advance and report a miss rate (26), with a shrinkage model across correlated tests (25).

### Gaps

1. No paper I found estimates cost basis from open interest or CFTC data. Nor did I find a check of such estimates against true positions.
2. I found no post-publication test of CFTC positioning signals. Kang and coauthors and Hong and Yogo stop in 2014 or earlier, and the published version was not checked for later data.
3. I found no study of the disposition effect in US corporate bond funds or in credit index futures. The only direct bond test is treasuries in one emerging market (7).
4. I did not find a check of estimated cost basis against account-level truth in any asset class. Goetzmann and Massa use account data to test the model's implications, but that is a different exercise.
5. Entries 8, 10 and 18 are the main sources for loss or open interest effects with numbers. All three sets of numbers come from working papers or drafts, not from the journal text.

## Verified but cut to stay within 30

All confirmed on Crossref. I read the abstract of each, except where noted.

- Odean (1998), Journal of Finance, 10.1111/0022-1082.00072. The original disposition test, 10,000 brokerage accounts.
- Barberis and Xiong (2009), Journal of Finance, 10.1111/j.1540-6261.2009.01448.x. Realized gain and loss preferences predict the effect more reliably than annual ones.
- Bessembinder (1992), Review of Financial Studies, 10.1093/rfs/5.4.637. Currency and agricultural futures returns vary with hedgers' net holdings.
- Basu and Miffre (2013), Journal of Banking and Finance, 10.1016/j.jbankfin.2013.02.031. Long-short hedging pressure portfolios are priced, and premiums rise with volatility.
- Moskowitz, Ooi and Pedersen (2012), Journal of Financial Economics, 10.1016/j.jfineco.2011.11.003. Speculators profit from time series momentum at hedgers' expense. Entry 19 disputes the evidence.
- Yu, Chen, Wang and Zhang (2023), Economic Modelling, 10.1016/j.econmod.2023.106214. A hedging pressure momentum index predicts oil futures, with out-of-sample R-squared of 0.946%, using data from 1994 to June 2021. Shows that a small positive result is possible, in one market only.
- Khandani and Lo (2011), Journal of Financial Markets, 10.1016/j.finmar.2010.07.005. The August 2007 quant unwind and a withdrawal of market-making capital.
- Brown, Howard and Lundblad (2022), Review of Financial Studies, 10.1093/rfs/hhab107. Hedge fund crowding helps explain drawdowns.
- Sias, Turtle and Zykaj (2016), Management Science, 10.1287/mnsc.2014.2131. Hedge fund demand shocks are positively related to later returns, including in stress.
- Harvey, Liu and Zhu (2016), Review of Financial Studies, 10.1093/rfs/hhv059. A new factor needs a t-statistic above 3.0.
- Bailey and López de Prado (2014), Journal of Portfolio Management, 10.3905/jpm.2014.40.5.094. The deflated Sharpe ratio corrects for selection bias and non-normality.
- Birru (2015), Review of Financial Studies, 10.1093/rfs/hhv007. The disposition effect may slow news, but not enough to explain momentum.
- Coval and Shumway (2005), Journal of Finance, 10.1111/j.1540-6261.2005.00723.x. Loss-averse Chicago Board of Trade traders take more afternoon risk, and those prices reverse faster.
- Eom (2018), Finance Research Letters, 10.1016/j.frl.2018.02.004. Korean index futures show the effect only below a critical point, and the opposite above it.
- Coval and Stafford (2007), Journal of Financial Economics, 10.1016/j.jfineco.2006.09.007. Outflow-driven fund trades create price pressure, and liquidity providers earn returns.
- Ellul, Jotikasthira and Lundblad (2011), Journal of Financial Economics, 10.1016/j.jfineco.2011.03.020. Regulatory selling of downgraded bonds causes declines and reversals.
- Jiang, Li, Sun and Wang (2022), Journal of Financial Economics, 10.1016/j.jfineco.2021.05.022. A bond-level fragility measure from fund illiquidity predicts volatility and March 2020 returns.
- Barth and Kahn (2025), Journal of Monetary Economics, 10.1016/j.jmoneco.2025.103823. I read the 2021 OFR version only. The basis trade unwind was likely a consequence, not the main cause, of the March 2020 stress. Large basis traders sold $91 to $105 billion.
- Du, Nesmith and Heppe (2025), FEDS 2025-082, 10.17016/feds.2025.082. Speculators rushed out in 2008, but there was no such risk flow in COVID. Positioning behavior differs across crises.
- Zhong and Wang (2018), Journal of Empirical Finance, 10.1016/j.jempfin.2018.02.005. Prospect theory values predict US corporate bond returns, especially junk, and loss aversion matters most. It works from the return distribution, not from cost basis.
- Mitchell and Pulvino (2012), Journal of Financial Economics, 10.1016/j.jfineco.2011.09.002. A sudden loss of prime broker leverage in 2008 left arbitrageurs unable to hold similar assets at similar prices.
- Greenwood and Thesmar (2011), Journal of Financial Economics, 10.1016/j.jfineco.2011.06.003. Ownership concentration and correlated liquidity shocks make an asset fragile, and fragility predicts volatility.
- Goetzmann and Massa (2008), Journal of Portfolio Management, 10.3905/jpm.2008.701622. I read the NBER 9499 abstract. Account data links disposition-prone trading to prices.

## Search strings

Web search, mostly extended mode:

1. `disposition effect corporate bond mutual funds capital gains overhang reference price bond returns`
2. `CFTC positioning hedging pressure futures return predictability out-of-sample post-publication decay 2022 2023 2024 2025`
3. `estimating investor cost basis futures open interest average entry price positions profit and loss predict returns academic paper`
4. `"disposition effect" "corporate bond" OR "bond funds" OR "bond mutual funds" paper reference point unrealized losses bond trading institutional`
5. `insurance companies selling bonds unrealized gains losses book value reference point corporate bond prices paper 2023 2024 2025 SSRN`
6. `disposition effect futures market cost basis open interest "capital gains overhang" commodity futures momentum study`
7. `bond fund managers disposition effect sell winners hold losers corporate bond mutual fund holdings cost basis "unrealized" fragility returns 2024`
8. `forced selling losses margin conditions trader positions futures CFTC "stop-loss" OR "loss" positions return reversal speculators losses predict liquidation paper`
9. `Treasury futures hedge fund basis trade leverage unwinding March 2020 margin spiral asset managers CFTC TFF positioning paper`
10. `commodity futures factors anomalies replication out-of-sample post-publication hedging pressure factor performance decline multiple testing`
11. `speculators net position CFTC currency OR Treasury futures predicts returns no predictive power contemporaneous Commitments of Traders test Granger study results`
12. `capital gains overhang recent evidence decline attenuated momentum disposition effect 2022 2023 2024 2025 institutional holdings cost basis estimated versus actual reference price accuracy`

Crossref bibliographic queries, from 2017 onward: `disposition effect bond funds fixed income`, `capital gains overhang corporate bonds`, `bond reference price anchoring investors selling`, `disposition effect futures market traders positions`, `commitments of traders positioning predict returns currency bond equity futures`, `hedging pressure commodity futures out-of-sample`, `crowded positions futures forced liquidation margin`, `open interest return predictability futures`. I also ran title lookups for every named paper.

## Limits of this search

1. OpenAlex and Semantic Scholar hit rate limits for most of the session. I used Crossref for existence, and RePEc, NBER and author PDFs for abstracts. Citation following in both directions was therefore partial, done through reference lists in the papers I read and through search. Recent work may be missed.
2. I did not open SSRN pages. SSRN items are confirmed by Crossref record only.
3. Web search result summaries were used only to find papers. No finding above rests on one.

## What I excluded, and why

1. **Unverified:** a Korean-language journal paper reporting a strong effect in bond funds (korfin.org). A search summary described it, but I did not read it or confirm its record.
2. **Unread:** the journal version of Sanders, Irwin and Merrin, and the September 2025 Fang draft. A search summary described a Fang finding on mutual funds, which I could not read, so it is left out.
3. **Metadata only, no findings read:** Locke and Mann (2005), 10.1016/j.jfineco.2004.01.004, and Robe and Roberts (2024), 10.1016/j.jcomm.2024.100389.
4. **Out of theme:** Hollstein and coauthors (2021), which studies business cycle predictors of commodity spot markets, not positions. Bhardwaj, Gorton and Rouwenhorst (NBER 21243) found the commodity basis result holds up out of sample, which is a useful counterexample to decay, but it is not about positions.
5. **Low relevance or quality:** retail explainers on margin calls and crypto liquidation, broker pages, and commentary on unrealized bond losses.
6. **Seed lead replaced:** Barber and Odean (2008) is confirmed (10.1093/rfs/hhm079). It concerns attention-driven retail buying, so it does not bear on this question.
