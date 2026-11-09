# Theme F: other ways to measure credit spread dispersion

Search date: 9 November 2026.

Baseline, from `../dispersion/SPEC.md`: g_i = ln(s_i / mean(s)). Dispersion is the sample stdev of g_i. Skew and excess kurtosis of g_i come with it.

## Bottom line

1. **Our measure is a known statistic.** It is the "variance of logs" from the inequality literature. Dividing by mean(s) only shifts the logs, so its stdev equals sd(ln s). The mean of g_i is minus Theil's L index (the mean log deviation). So the sheet already computes a second inequality index.
2. **The log scale is well supported.** Spread volatility rises in proportion to spread level (DTS, Ben Dor et al. 2007). Gilchrist and Zakrajšek (2012) take logs because spreads are highly skewed. No paper found uses our exact formula, though.
3. **The common alternative is a percentile range of spread levels.** Examples are the 75th minus 25th percentile (NY Fed distress index, Gilchrist, Sim and Zakrajšek) and the 95th minus 5th (Ferreira). These are in basis points, so they rise when all spreads widen. Ours does not. Running both separates "everything widened" from "names pulled apart". Spread dispersion moves with the cycle. Ferreira finds it does not lead the cycle.
4. **Our measure has two weak spots.** One distressed outlier moves mean(s) and shifts every g_i. The moment-based skew and kurtosis are also fragile. Foster and Ok (1999) show variance of logs can rank two distributions opposite to the Gini or Theil index, mainly through the upper tail. In credit, that tail holds the distressed names. Robust swaps exist: Q_n or IQR of ln s for scale, Bowley and Moors for shape, and the median as `ref`.
5. **Index markets price dispersion directly.** Longstaff and Rajan find the stdev of the 125 CDX spreads raises tranche-implied loss risk, holding the index level fixed (t = 10.3). Re-running that regression with our log measure is a cheap first test.

## How to read each entry

- **Tier 1:** peer-reviewed journal. **Tier 2:** working paper or preprint. **Tier 3:** industry or official report.
- **Read** states what was read. "Abstract" means the full paper was not read, so method and data fields are limited to what the abstract states.
- **Means for us** lines are inference. They are not findings of the papers.
- Every DOI below was checked against Crossref on 9 November 2026, twice. Every URL was opened.

## Why a log, relative measure
### 1. Ben Dor, Dynkin, Hyman, Houweling, van Leeuwen and Penninga (2007)

- **Citation:** Ben Dor, A., Dynkin, L., Hyman, J., Houweling, P., van Leeuwen, E., and Penninga, O. (2007). DTS (Duration Times Spread). *Journal of Portfolio Management*, 33(2), 77–100.
- **DOI:** 10.3905/jpm.2007.674795
- **Verified:** Crossref. **Tier:** 1. **Read:** CFA Institute Digest summary and search abstracts only. The publisher page needs a login.
- **Measure:** Relative spread change, Δs/s, and DTS = spread duration × spread. Not a cross-sectional dispersion measure.
- **Data and sample:** Lehman Brothers Credit and High Yield indices, monthly, September 1989 to January 2005 (185 months). A Baa comparison uses 1980–2005.
- **Key finding:** Spread changes are proportional to spread level, not parallel. Both systematic and idiosyncratic spread volatility rise linearly with spread level. Relative spread volatility is more stable over time than absolute volatility.
- **Means for us:** If Δs/s has stable volatility, then Δ ln s does too. That is the theoretical reason our log measure stays comparable across regimes while a basis-point stdev does not. A follow-up exists: Ben Dor, Dynkin, Hyman and Polbennikov (2026), "Twenty Years of Duration Times Spread (DTS)", *Journal of Fixed Income* 36(2), 89–115, DOI 10.3905/jfi.2026.018. I confirmed it in Crossref but could not read it. (Inference.)
### 2. Ben Dor, Dynkin, Hyman and Polbennikov (2026)

- **Citation:** Ben Dor, A., Dynkin, L., Hyman, J. and Polbennikov, S. (2026). Twenty Years of Duration Times Spread (DTS). *Journal of Fixed Income* 36(2), 89–115.
- **DOI:** 10.3905/jfi.2026.018
- **Verified:** Crossref (published online 5 August 2026). Abstract via Semantic Scholar. **Tier:** 1. **Read:** abstract.
- **Measure:** DTS as in entry 1. The review covers refinements for term structure, very low-spread bonds, mispriced securities and market beta.
- **Data and sample:** Review of the authors' work across US corporates, emerging-market debt, sovereigns and CDS.
- **Key finding:** The abstract calls DTS a durable first-order framework across crisis periods. It flags very low-spread bonds as needing a targeted refinement.
- **Means for us:** The low-spread problem in DTS is the same problem your measure has. At very tight spreads, ln(s) stretches small bp differences. A floor or offset, such as ln(s + c), may be worth testing. (Inference. I did not read how the review handles it.)
### 3. Gilchrist and Zakrajšek (2012)

- **Citation:** Gilchrist, S., and Zakrajšek, E. (2012). Credit spreads and business cycle fluctuations. *American Economic Review*, 102(4), 1692–1720.
- **DOI:** 10.1257/aer.102.4.1692
- **Verified:** Crossref. **Tier:** 1. **Read:** abstract plus Section 4 of NBER WP 17021.
- **Measure:** Not a dispersion measure. The authors regress ln S (log bond spread) on distance-to-default and bond characteristics. The residual drives the excess bond premium.
- **Data and sample:** U.S. nonfinancial corporate bonds, 1973 onward, from secondary-market prices.
- **Key finding:** The GZ spread index predicts activity. Most of that power comes from the excess bond premium. Footnote 6 states the reason for logs: "Taking logs of credit spreads provides a useful transformation to control for heteroscedasticity, given that the distribution of credit spreads is highly skewed."
- **Means for us:** This is direct academic support for working with ln s. The regression residual is also a "rating- and fundamentals-adjusted" log spread. Its cross-sectional stdev would be a residual-dispersion measure. (Inference.)
### 4. Foster and Ok (1999)

- **Citation:** Foster, J. E. and Ok, E. A. (1999). Lorenz Dominance and the Variance of Logarithms. *Econometrica* 67(4), 901–907.
- **DOI:** 10.1111/1468-0262.00057
- **Verified:** Crossref. Abstract summary from IDEAS/RePEc, https://ideas.repec.org/a/ecm/emetrp/v67y1999i4p901-908.html. **Tier:** 1. **Read:** abstract summary.
- **Measure:** Variance of logarithms, Var(ln x), as an inequality index.
- **Data and sample:** Theory.
- **Key finding:** The variance of logs can contradict Lorenz dominance. The disagreement can be very large and occurs with non-negligible probability.
- **Means for us:** Your measure is exactly the stdev of ln(s). It can say "less dispersed" when every Lorenz-based measure (Gini, Theil, CV) says "more dispersed." This happens mainly through the upper tail. In credit, that is the distressed tail you care about most. Report the Gini or Theil T alongside it. (Inference.)

## Percentile and level measures used by researchers and central banks
### 5. Ferreira (2024)

- **Citation:** Ferreira, T. R. T. (2024). Cross-sectional financial conditions, business cycles and the lending channel. *Journal of Monetary Economics*, 147, 103597. Working-paper version: Federal Reserve Board IFDP 1335 (2022).
- **DOI:** 10.1016/j.jmoneco.2024.103597 (IFDP: 10.17016/IFDP.2022.1335)
- **Verified:** Crossref (both DOIs). **Tier:** 1. **Read:** IFDP version (full PDF), abstract plus Sections 2–3.2.
- **Measure:** The paper transforms each spread X (in percent) as x = 100·log(1 + X/100). Dispersion is the 95th minus 5th percentile of x across firms. Skewness is (x95 − x50) − (x50 − x5). Moments are unweighted and computed separately for financial and nonfinancial firms.
- **Data and sample:** U.S. corporate bond yields from Lehman/Warga and Merrill Lynch, 1973–2020, quarterly. Spreads are measured against maturity-matched Treasury yields.
- **Key finding:** The dispersion of returns and all three moments of credit spreads are countercyclical. They move with GDP growth at about zero lag rather than leading it. The skewness of financial-firm stock returns is the best predictor of activity.
- **Means for us:** Its "log" spread is nearly the raw spread, because log(1 + X/100) ≈ X/100 for small X. So its 95–5 range behaves like a level range in percentage points. It is not scale-invariant like ours. The 95–5 range and the quantile-based skew are a robust alternative to our sample stdev and moment-based skew. (Inference.)
### 6. Gilchrist, Sim and Zakrajšek (2014)

- **Citation:** Gilchrist, S., Sim, J. W., and Zakrajšek, E. (2014). Uncertainty, financial frictions, and investment dynamics. NBER Working Paper 20038.
- **DOI:** 10.3386/w20038
- **Verified:** Crossref. **Tier:** 2. **Read:** abstract, introduction, Section 5.3, Data Appendix A.1.
- **Measure:** Two measures. The first is the cross-sectional standard deviation of credit spreads, STD(S), used in the model-versus-data table. The second is the interquartile range of bond spreads, plotted in Figure A-1.
- **Data and sample:** Senior unsecured bonds of U.S. nonfinancial firms, 1973:M1–2012:M9. The sample has 385,062 observations, 6,725 bonds, and 1,164 firms.
- **Key finding:** The median spread and the IQR of spreads are both countercyclical. The IQR "tends to lead the business cycle" and jumps in financial distress. The model reproduces countercyclical spread dispersion only when uncertainty or capital-liquidity shocks drive the cycle. Technology shocks alone make dispersion procyclical.
- **Means for us:** This is the closest academic use of spread dispersion as a macro signal. It uses spread levels in percentage points, not logs. Their IQR will rise with the general spread level. Our log stdev isolates relative dispersion. The two should be compared in a level-heavy widening such as 2008. (Inference.)
### 7. Boyarchenko, Crump, Kovner and Shachar (2025)

- **Citation:** Boyarchenko, N., Crump, R. K., Kovner, A., and Shachar, O. (2025). Corporate bond market distress. *Journal of Monetary Economics*, 152, 103765. Earlier version: FRBNY Staff Report 957.
- **DOI:** 10.1016/j.jmoneco.2025.103765
- **Verified:** Crossref. **Tier:** 1. **Read:** Staff Report version (revised September 2024), abstract, Section 2, Appendix A.3.
- **Measure:** For duration-matched spreads and default-adjusted spreads, the index includes the cross-sectional interquartile range of bond-week spreads (75th minus 25th percentile). This sits next to an average spread and a time-series spread volatility.
- **Data and sample:** TRACE trades and ICE-BAML quotes for U.S. corporate bonds, 2005 onward, weekly.
- **Key finding:** The Corporate Bond Market Distress Index (CMDI) combines these and other metrics. It predicts future market-functioning measures and real activity beyond credit spreads. Spread IQR rises in broad distress. Time-series spread volatility normalises faster than IQR.
- **Means for us:** An official-sector index treats spread IQR as a core distress input. That supports tracking a dispersion series. Their IQR is in spread units, not logs. (Inference.)
### 8. Okimoto and Takaoka (2022)

- **Citation:** Okimoto, T., and Takaoka, S. (2022). The credit spread curve distribution and economic fluctuations in Japan. *Journal of International Money and Finance*, 122, 102582. Working paper: RIETI DP 20-E-030 (2020).
- **DOI:** 10.1016/j.jimonfin.2021.102582
- **Verified:** Crossref. **Tier:** 1. **Read:** RIETI version, abstract and Sections 1–3.
- **Measure:** Monthly deciles 1–9 of the firm-level spread distribution, for 1-year spreads and the 7-year minus 1-year slope. Separately, "corporate bond market uncertainty" is the cross-sectional volatility of spreads over the previous six months. That variable switches between regimes in a smooth-transition regression.
- **Data and sample:** Japanese corporate bonds, firm-level spreads, April 2004 to March 2019.
- **Key finding:** Upper deciles (lower credit quality) predict Japanese activity better than the government yield curve or a spread index. Predictive power is stronger when spread dispersion is low. The authors use deciles partly because one issuer (TEPCO in 2011) distorted the arithmetic average.
- **Means for us:** Two lessons. First, the upper tail of the distribution carries the signal, so a 90th-percentile series of g_i adds information. Second, outliers move mean-based measures. Our g_i uses mean(s) as its anchor, so one blown-out name shifts every g_i. A median anchor would be more robust. (Inference.)
### 9. Kozlowski and Ebsim (2020)

- **Citation:** Kozlowski, J. and Ebsim, M. (2020). Corporate Bond Spreads and the Pandemic III: Variance across Sectors and Firms. Federal Reserve Bank of St. Louis, On the Economy blog, 11 May 2020.
- **URL:** https://www.stlouisfed.org/on-the-economy/2020/may/corporate-bond-spreads-pandemic-variance-sectors-firms
- **Verified:** Page opened. **Tier:** 3. **Read:** full.
- **Measure:** Variance of daily bond spreads, split into across-sector, across-firm-within-sector and across-bond-within-firm parts. The post does not say if spreads are in levels or logs.
- **Data and sample:** TRACE and Mergent FISD, January to April 2020.
- **Key finding:** Across-sector variance was only 11–13% of the total. The within-firm share rose from 18% to 42% in the March 2020 stress, before the Fed's interventions.
- **Means for us:** Variance of logs decomposes additively into between-group and within-group parts, just like this. So you can split your σ² into sector, rating and residual pieces. (Inference.) The rise in within-firm dispersion is a warning: if you use one spread per issuer, the choice of bond matters in stress.
### 10. Board of Governors of the Federal Reserve System (2025)

- **Citation:** Board of Governors of the Federal Reserve System (2025). Financial Stability Report, November 2025. Section 1, Asset Valuations.
- **URL:** https://www.federalreserve.gov/publications/november-2025-financial-stability-report-asset-valuations.htm
- **Verified:** Page opened. **Tier:** 3. **Read:** full section.
- **Measure:** ICE BofA option-adjusted spreads for the triple-B index (C0A4) and the high-yield index (H0A0). Excess bond premium. Leveraged-loan discounted spreads. Each is compared with its own historical median or distribution.
- **Data and sample:** Index data to late October 2025.
- **Key finding:** Triple-B spreads were about 0.7 percentage points and high-yield spreads about 1.6 percentage points below their historical medians.
- **Means for us:** The Fed's flagship stability report uses no issuer-level dispersion measure. Its cross-rating view is two index levels, triple-B and high yield, set side by side. A HY/BBB ratio is the implied decompression gauge. (Inference.) Your measure fills a gap in what is published.
### 11. Holló, Kremer and Lo Duca (2012)

- **Citation:** Holló, D., Kremer, M. and Lo Duca, M. (2012). CISS – A Composite Indicator of Systemic Stress in the Financial System. ECB Working Paper No. 1426.
- **DOI:** 10.2139/ssrn.2018792
- **Verified:** Crossref. Full PDF opened at https://www.ecb.europa.eu/pub/pdf/scpwps/ecbwp1426.pdf. **Tier:** 2. **Read:** indicator list and transformation section.
- **Measure:** The bond-market sub-index uses the yield spread of A-rated non-financial corporates over government bonds. The financial-intermediary sub-index uses the spread of A-rated financial over non-financial corporates. Each raw indicator is converted to its empirical CDF (an order-statistic rank) before aggregation.
- **Data and sample:** Euro-area market data, weekly.
- **Key finding:** CISS does not use cross-sectional spread dispersion. It uses spread levels and one sector spread gap.
- **Means for us:** Two things carry over. First, the financial-minus-non-financial spread is a two-bucket decompression measure. Second, the empirical-CDF transform is a scale-free way to put your dispersion series on a 0–1 stress scale. (Inference.) The absence of a dispersion input in the ECB's flagship index is itself a finding.
### 12. Chiţu, Gori and Gürkaynak (ECB Working Paper 3235)

- **Citation:** Chiţu, L., Gori, S. and Gürkaynak, R. S. External finance premium: market finance versus bank finance. ECB Working Paper Series No. 3235.
- **URL:** https://www.ecb.europa.eu/pub/pdf/scpwps/ecb.wp3235~15af105d53.en.pdf
- **Verified:** PDF opened. Year not printed on the pages I read. The paper cites 2025 and 2026 work, so it is 2026 or later. **Tier:** 2. **Read:** abstract and R² tables (skimmed).
- **Measure:** R² of fixed-effect regressions of bond spreads. This splits cross-sectional spread variance into country or state, firm and time parts.
- **Data and sample:** Micro-level corporate bond spreads and bank loan spreads, United States and euro area.
- **Key finding:** Issuer country or state explains very little of the variance of corporate bond spreads. Firm fixed effects explain about 40% in both regions. Bank loan spreads, by contrast, are set at country level.
- **Means for us:** Country is not a big driver of cross-sectional bond spread dispersion in either region. A pooled US-plus-Europe dispersion measure need not be split by country. (Inference.)
### 13. Eisenband (2024), citing S&P Global Ratings distress ratio

- **Citation:** Eisenband, M. C. (2024). Distressed Debt Levels Are Very Disconnected from Default Activity – That's a First. FTI Consulting, 4 April 2024.
- **URL:** https://www.fticonsulting.com/en/japan/insights/articles/distressed-debt-levels-very-disconnected-from-default-activity-thats-first
- **Verified:** Page opened. Chart credited to S&P Global Ratings Credit Research. The S&P primary pages returned HTTP 403. **Tier:** 3. **Read:** full.
- **Measure:** Distress ratio = share of speculative-grade securities whose yield (lower of yield-to-maturity and yield-to-worst) is more than 1,000bp over a comparable Treasury.
- **Data and sample:** US speculative-grade market, S&P data, about 25 years.
- **Key finding:** The US distress ratio was about 6.0%, against a long-term average of about 12%. It peaked at 9.2% in March 2023. It led defaults around sudden shocks such as 2008 and 2020. In normal periods it moved with defaults, without a clear lead. Its gap from default activity since early 2023 was the widest in 25 years.
- **Means for us:** This is a right-tail share with a fixed threshold. It is not scale-free. A market-wide widening raises it even if relative dispersion is flat. It answers "how much mass is near default." Your measure answers "how unequal are spreads." They are complements. A scale-free version is the share of names with g_i above a cut-off, such as ln 3. (Inference.) A 2015 S&P Global Market Intelligence note applied the same rule to the iBoxx $ Liquid High Yield Index (157 of 985 names, 16%). I saw that only in a search snippet because the page returned HTTP 403.

## Robust statistics for the same job
### 14. Rousseeuw and Croux (1993)

- **Citation:** Rousseeuw, P. J. and Croux, C. (1993). Alternatives to the Median Absolute Deviation. *Journal of the American Statistical Association* 88(424), 1273–1283.
- **DOI:** 10.1080/01621459.1993.10476408
- **Verified:** Crossref. Abstract via OpenAlex. **Tier:** 1. **Read:** abstract.
- **Measure:** MAD_n = 1.4826·med|x_i − med x|. S_n = 1.1926·med_i med_j |x_i − x_j|. Q_n = 0.25 quantile of the pairwise distances |x_i − x_j|.
- **Data and sample:** Theory and simulation.
- **Key finding:** All three have a 50% breakdown point. Gaussian efficiency is 37% for MAD, 58% for S_n and 82% for Q_n. S_n and Q_n need no location estimate and do not assume symmetry.
- **Means for us:** Q_n of ln(s_i) is a drop-in robust replacement for your stdev. It stays scale-free. One defaulted name at 5,000bp cannot move it. Q_n's 82% efficiency means little loss when there is no outlier. (Inference.) It is my top recommendation as a companion series.
### 15. Moors (1988)

- **Citation:** Moors, J. J. A. (1988). A Quantile Alternative for Kurtosis. *Journal of the Royal Statistical Society Series D (The Statistician)* 37(1), 25 (start page per Crossref).
- **DOI:** 10.2307/2348376
- **Verified:** Crossref. Abstract via OpenAlex. **Tier:** 1. **Read:** abstract.
- **Measure:** Octile-based kurtosis: [(E7 − E5) + (E3 − E1)] / (E6 − E2), where E_k is the k-th octile.
- **Data and sample:** Theory.
- **Key finding:** The measure exists when moments do not. Extreme tails do not influence it. It is simple to compute.
- **Means for us:** Use it in place of moment excess kurtosis of g_i. Moment kurtosis with N = 125 is dominated by one or two names. (Inference.)
### 16. Kim and White (2004)

- **Citation:** Kim, T.-H. and White, H. (2004). On more robust estimation of skewness and kurtosis. *Finance Research Letters* 1(1), 56–73.
- **DOI:** 10.1016/S1544-6123(03)00003-5
- **Verified:** Crossref. Content from EconPapers and eScholarship records via search summaries. **Tier:** 1. **Read:** summary only, not the abstract or paper.
- **Measure:** Reviews quantile-based skewness (Bowley's quartile measure and Hinkley's generalisation) and quantile-based kurtosis (Moors and others). Compares them with moment estimators by Monte Carlo.
- **Data and sample:** Simulation, plus daily S&P 500 returns.
- **Key finding:** Conventional skewness and kurtosis are non-robust averages. On S&P 500 data, robust measures suggest negative skew and excess kurtosis "may have been accepted too readily."
- **Means for us:** Direct support for swapping your moment skew and kurtosis of g_i for Bowley-type and Moors-type measures. The quantile skew of ln(s) is still scale-free. (Inference.)
### 17. Hinkley (1975)

- **Citation:** Hinkley, D. V. (1975). On power transformations to symmetry. *Biometrika* 62(1), 101–111.
- **DOI:** 10.1093/biomet/62.1.101
- **Verified:** Crossref. Abstract via OpenAlex. **Tier:** 1. **Read:** abstract.
- **Measure:** Picks a power transform x^λ that makes the distribution symmetric, using equal-tailed order statistics. Source of the generalised quantile skewness [(Q(1−p) − Q(0.5)) − (Q(0.5) − Q(p))] / [Q(1−p) − Q(p)].
- **Data and sample:** Theory, with exponential and gamma examples.
- **Key finding:** Simple order-statistic estimates can choose a symmetrising transform.
- **Means for us:** The log is the λ → 0 member of the power family. Ask whether spreads need λ = 0 or something else. If the log over-corrects at tight spreads, a fitted λ (or ln(s + c)) is a principled fix. (Inference.)
### 18. Cowell and Flachaire (2007)

- **Citation:** Cowell, F. A. and Flachaire, E. (2007). Income distribution and inequality measurement: The problem of extreme values. *Journal of Econometrics* 141(2), 1044–1072.
- **DOI:** 10.1016/j.jeconom.2007.01.001
- **Verified:** Crossref. Abstract summaries from LSE Research Online and EconPapers via search. **Tier:** 1. **Read:** abstract summary.
- **Measure:** Generalised entropy (Theil-family) and related inequality indices, with bootstrap inference.
- **Data and sample:** Simulation on heavy-tailed income-type distributions.
- **Key finding:** Inequality indices behave badly with extreme values, mostly when the upper tail is heavy. Standard bootstrap inference can fail. Semiparametric modelling of the upper tail (for example a Pareto fit) helps a lot.
- **Means for us:** High-yield spreads have a heavy upper tail. So the Gini, Theil and CV of spreads inherit this problem. The log transform tames it, which is a point in your measure's favour. If you add a Lorenz-consistent index, fit the top tail or trim it, and do not trust a naive bootstrap. (Inference.)

## Index, correlation and factor views of dispersion
### 19. Longstaff and Rajan (2006, 2008)

- **Citation:** Longstaff, F. A. and Rajan, A. (2008). An Empirical Analysis of the Pricing of Collateralized Debt Obligations. *Journal of Finance* 63(2), 529–563. Working-paper version: NBER Working Paper 12210 (2006).
- **DOI:** 10.1111/j.1540-6261.2008.01330.x (journal). 10.3386/w12210 (NBER WP).
- **Verified:** Both DOIs on Crossref. NBER PDF opened at https://www.nber.org/system/files/working_papers/w12210/w12210.pdf. **Tier:** 1. **Read:** abstract and Section 6.8 of the 2006 working paper. I did not check if Section 6.8 survives in the journal version.
- **Measure:** Dispersion = cross-sectional standard deviation of CDS spread levels for the 125 CDX names. Regression: implied stdev of the loss distribution = a + b·CDX + c·Dispersion.
- **Data and sample:** CDX.NA.IG index and tranches, October 2003 to October 2005, 435 days. Citigroup data.
- **Key finding:** Both the index level and dispersion are significant (t = 18.95 and 10.30, R² = 0.681). The dispersion coefficient is positive. Higher dispersion means a wider implied loss distribution at the same index level. On average, firm-specific risk is about 65% of the index spread.
- **Means for us:** This is the cleanest market-pricing evidence that dispersion is a state variable beyond the index level. They use a level stdev, which mixes level and shape. Your log stdev isolates shape. Running their regression with your measure in place of theirs would show which version tranche markets price. (Inference.)
### 20. Collin-Dufresne, Goldstein and Martin (2001)

- **Citation:** Collin-Dufresne, P., Goldstein, R. S., and Martin, J. S. (2001). The determinants of credit spread changes. *Journal of Finance*, 56(6), 2177–2207.
- **DOI:** 10.1111/0022-1082.00402
- **Verified:** Crossref. **Tier:** 1. **Read:** abstract.
- **Measure:** Not a dispersion statistic. The authors regress spread changes on theory-based variables, then run principal components on the residuals.
- **Data and sample:** Dealer quotes and transaction prices on straight U.S. industrial bonds.
- **Key finding:** Theory variables explain little of spread changes. The residuals are highly cross-correlated and driven mostly by one common factor. That factor is not explained by macro or liquidity proxies.
- **Means for us:** Dispersion of residuals after removing the first common factor is a cleaner "idiosyncratic" measure than raw dispersion. Our g_i removes only a common scale (the mean). It does not remove differences in factor loadings. (Inference.)
### 21. Nozawa (2017)

- **Citation:** Nozawa, Y. (2017). What drives the cross-section of credit spreads? A variance decomposition approach. *Journal of Finance*, 72(5), 2045–2072.
- **DOI:** 10.1111/jofi.12524
- **Verified:** Crossref. **Tier:** 1. **Read:** abstract.
- **Measure:** The cross-sectional variance of credit spreads, split into expected-return and expected-credit-loss parts. The split uses a log-linearized pricing identity and a VAR.
- **Data and sample:** Micro-level U.S. corporate bond data, 1973–2011.
- **Key finding:** Expected returns explain about as much of the cross-sectional variance of spreads as expected credit losses do. Most time-series variation in the market-portfolio spread reflects risk premia.
- **Means for us:** The cross-sectional variance of spreads is not just a default-risk spread. About half reflects differences in expected returns. A rise in our dispersion may signal a repricing of risk premia, not only a change in default risk. (Inference, based on the abstract only.)
### 22. Christoffersen, Jacobs, Jin and Langlois (2018)

- **Citation:** Christoffersen, P., Jacobs, K., Jin, X., and Langlois, H. (2018). Dynamic dependence and diversification in corporate credit. *Review of Finance*, 22(2), 521–560. Crossref lists the issue date as 2017 (online).
- **DOI:** 10.1093/rof/rfx034
- **Verified:** Crossref. **Tier:** 1. **Read:** abstract.
- **Measure:** Dynamic copula correlation and tail dependence of CDS and equity for 215 firms. Not a dispersion statistic.
- **Data and sample:** CDS spreads and equity returns for 215 firms. The abstract covers the 2007 and 2011 episodes.
- **Key finding:** Credit dependence and tail dependence vary over time and persist. They jumped in July/August 2007 and August 2011 and stayed high. CDS correlation dynamics help explain credit spreads.
- **Means for us:** This is the correlation side of the dispersion–correlation link. High correlation of spread changes should coincide with low dispersion of log-spread changes. We could test that inverse link on our data. (Inference.)
### 23. Kitwiwattanachai and Pearson (2015)

- **Citation:** Kitwiwattanachai, C., and Pearson, N. D. (2015). Inferring correlations of asset values and distances-to-default from CDS spreads: A structural model approach. *Review of Asset Pricing Studies*, 5(1), 112–154.
- **DOI:** 10.1093/rapstu/rav001
- **Verified:** Crossref. **Tier:** 1. **Read:** abstract (RePEc).
- **Measure:** Correlations of changes in distance-to-default, inferred from single-name CDS spreads in a structural model with a random default boundary.
- **Data and sample:** Single-name CDS. The abstract does not give the sample.
- **Key finding:** CDS-implied correlations are higher than equity correlations. That fits a randomly varying default boundary. Funding-liquidity conditions affect the correlations.
- **Means for us:** This offers a model-based way to turn a CDS cross-section into a correlation number. It complements a model-free dispersion statistic. (Inference.)
### 24. Collin-Dufresne, Goldstein and Yang (2012)

- **Citation:** Collin-Dufresne, P., Goldstein, R. S., and Yang, F. (2012). On the relative pricing of long-maturity index options and collateralized debt obligations. *Journal of Finance*, 67(6), 1983–2014.
- **DOI:** 10.1111/j.1540-6261.2012.01779.x
- **Verified:** Crossref. **Tier:** 1. **Read:** abstract.
- **Measure:** A structural model. It takes market dynamics from S&P 500 index options and idiosyncratic dynamics from the term structure of credit spreads. It then prices CDX tranches.
- **Data and sample:** Long-dated S&P 500 index options and CDX tranche prices, before and during the 2007–2009 crisis.
- **Key finding:** All tranches price well out of sample before the crisis. During the crisis, senior tranches price correctly only if the model includes a catastrophic jump.
- **Means for us:** This splits portfolio credit risk into a systematic part and an idiosyncratic part, which drives dispersion. Tranche-implied correlation is the market price of the "low dispersion, everyone defaults together" scenario. (Inference.)
### 25. Junge and Trolle (2013)

- **Citation:** Junge, B. and Trolle, A. B. (2013). Liquidity Risk in Credit Default Swap Markets. SSRN working paper.
- **DOI:** 10.2139/ssrn.2371374
- **Verified:** Crossref, with abstract. **Tier:** 2. **Read:** abstract.
- **Measure:** CDS market illiquidity = aggregate deviation of credit index levels from their no-arbitrage values implied by the constituents' CDS spreads.
- **Data and sample:** CDS indices and constituents (details not read).
- **Key finding:** Liquidity risk is priced in the cross-section of CDS returns. It accounts for 24% of CDS spreads on average.
- **Means for us:** The index-to-intrinsic basis is a liquidity measure, not a dispersion measure. It should be a control when you test dispersion against index returns. (Inference.)
- **Also in:** `C_cdx_futures.md`.
### 26. Boyarchenko, Gupta, Steele and Yen (2018)

- **Citation:** Boyarchenko, N., Gupta, P., Steele, N. and Yen, J. (2018). Trends in Credit Basis Spreads. Federal Reserve Bank of New York *Economic Policy Review* 24(2), October 2018.
- **URL:** https://www.newyorkfed.org/medialibrary/media/research/epr/2018/epr_2018_trends-in-credit-basis-spreads_boyarchenko.pdf
- **Verified:** PDF opened. **Tier:** 3. **Read:** Sections 1.3 and 2.1.
- **Measure:** CDX-CDS basis = absolute difference between the CDX index spread and the spread implied by the replicating single-name portfolio. Idiosyncratic risk is proxied by the share of names changed at each roll, the upgrade/downgrade ratio and idiosyncratic equity volatility.
- **Data and sample:** CDX.NA.IG and CDX.NA.HY on-the-run, through Q1 2016. JPMorgan, Markit and CRSP data.
- **Key finding:** The basis widened in late 2015 and early 2016. Idiosyncratic risk was high in high yield but normal in investment grade. Funding costs from tighter balance sheets were a more persistent driver.
- **Means for us:** Their idiosyncratic-risk proxies are not spread dispersion. Your measure would be a direct, market-based alternative for that test. (Inference.) Note the definitional wobble: the text calls the arbitrage leg "equal-weighted," while entry 13 uses duration weights.
### 27. Bai and Shachar (2015)

- **Citation:** Bai, J. and Shachar, O. (2015). The Effects of Entering and Exiting a Credit Default Swap Index. Federal Reserve Bank of New York, Liberty Street Economics, 30 March 2015.
- **URL:** https://libertystreeteconomics.newyorkfed.org/2015/03/the-effects-of-entering-and-exiting-a-credit-default-swap-index
- **Verified:** Page opened. **Tier:** 3. **Read:** full.
- **Measure:** Index intrinsic value = duration-weighted average of constituent spreads. Index skew = index spread minus intrinsic.
- **Data and sample:** CDX.NA.IG constituents.
- **Key finding:** Names entering the index see their CDS spreads rise by about 12bp over seven business days. Exits show no significant effect.
- **Means for us:** Duration weighting gives wide names less weight, because their risky duration is shorter. So with high dispersion, the intrinsic spread falls below the simple mean. The gap between the equal-weighted mean and intrinsic is a by-product dispersion gauge. (Inference, not tested in the post.) Index inclusion effects also mean constituent spreads are not a clean sample.

## Complements from outside the spread cross-section
### 28. Güntay and Hackbarth (2010)

- **Citation:** Güntay, L., and Hackbarth, D. (2010). Corporate bond credit spreads and forecast dispersion. *Journal of Banking & Finance*, 34(10), 2328–2345.
- **DOI:** 10.1016/j.jbankfin.2010.02.019
- **Verified:** Crossref and author PDF. **Tier:** 1. **Read:** abstract, introduction, Section 2 (data).
- **Measure:** Analyst forecast dispersion is the standard deviation of the latest quarterly EPS forecasts, divided by the stock price. It requires at least two analysts.
- **Data and sample:** Lehman Fixed Income Database, January 1987 to March 1998. The final sample has 16,004 bond-quarters, 1,389 bonds, and 382 issuers.
- **Key finding:** Higher forecast dispersion means higher spreads. A one-stdev rise adds 19 bp against a 100 bp average. Dispersion alone explains about 23% of the cross-sectional variation in spreads. Changes in dispersion predict changes in spreads. A high-minus-low dispersion bond portfolio earns more than 100 bp a year.
- **Means for us:** This measures disagreement about each issuer, not spread differences across issuers. An average of firm-level forecast dispersion across our names would complement our log-spread stdev as a "belief" signal. (Inference.)
### 29. Buraschi, Trojani and Vedolin (2014)

- **Citation:** Buraschi, A., Trojani, F., and Vedolin, A. (2014). Economic uncertainty, disagreement, and credit markets. *Management Science*, 60(5), 1281–1296.
- **DOI:** 10.1287/mnsc.2013.1815
- **Verified:** Crossref. **Tier:** 1. **Read:** abstract.
- **Measure:** Bottom-up proxies of aggregate belief dispersion, built from forecaster disagreement.
- **Data and sample:** U.S. corporate bond and stock returns. The abstract does not state the period.
- **Key finding:** In the model, credit spreads and their volatility rise with belief heterogeneity. Empirically, exposure to aggregate disagreement shocks explains risk premia on corporate bonds and stocks.
- **Means for us:** Aggregate disagreement is a candidate driver of our dispersion series. We could test whether our log-spread stdev co-moves with a disagreement index. (Inference.)
### 30. Campbell and Taksler (2003)

- **Citation:** Campbell, J. Y., and Taksler, G. B. (2003). Equity volatility and corporate bond yields. *Journal of Finance*, 58(6), 2321–2350.
- **DOI:** 10.1046/j.1540-6261.2003.00607.x
- **Verified:** Crossref. **Tier:** 1. **Read:** abstract.
- **Measure:** Firm-level idiosyncratic equity volatility as a driver of bond yields. Not a spread-dispersion statistic.
- **Data and sample:** U.S. corporate bond panel, late 1990s.
- **Key finding:** Idiosyncratic equity volatility explains as much cross-sectional variation in yields as credit ratings do. A rising trend in idiosyncratic volatility helps explain higher yields in that period.
- **Means for us:** Cross-sectional dispersion of log spreads should co-move with dispersion in idiosyncratic equity volatility. Equity data could serve as a cross-check or as a fill-in where spread quotes are stale. (Inference.)

## Same-bond price dispersion (a liquidity measure, not ours)
### 31. Jankowitsch, Nashikkar and Subrahmanyam (2011)

- **Citation:** Jankowitsch, R., Nashikkar, A., and Subrahmanyam, M. G. (2011). Price dispersion in OTC markets: A new measure of liquidity. *Journal of Banking & Finance*, 35(2), 343–357.
- **DOI:** 10.1016/j.jbankfin.2010.08.016
- **Verified:** Crossref. **Tier:** 1. **Read:** RePEc abstract and authors' Bank of Canada conference slides (2010).
- **Measure:** For bond i on day t, the volume-weighted root mean squared difference between each trade price p and the Markit consensus price m. In formula form: d = sqrt( Σ_j V_j (p_j − m)² / Σ_j V_j ).
- **Data and sample:** TRACE trades, Markit quotes, and Bloomberg data, October 2004 to October 2006. The sample has 1,800 bonds and 3.9 million trades.
- **Key finding:** The average price dispersion is 49.9 bp, against an average bid-ask spread of 35.9 bp. Bid-ask spreads do not capture it. It relates to bond characteristics and trading activity.
- **Means for us:** This is a different concept. It measures dispersion across trades in one bond, which signals illiquidity. It is useful as a data-quality filter for which issuers to include, not as a substitute for our measure. (Inference.)
### 32. Feldhütter (2012)

- **Citation:** Feldhütter, P. (2012). The same bond at different prices: Identifying search frictions and selling pressures. *Review of Financial Studies*, 25(4), 1155–1206.
- **DOI:** 10.1093/rfs/hhr093
- **Verified:** Crossref. **Tier:** 1. **Read:** abstract (RePEc).
- **Measure:** The gap between prices small traders pay and prices large traders pay for the same bond.
- **Data and sample:** U.S. corporate bonds (TRACE). The paper studies the 2005 GM and Ford downgrades and the subprime crisis.
- **Key finding:** A structural OTC search model shows the gap signals liquidity crises, meaning episodes with many forced sellers.
- **Means for us:** Same-bond dispersion again. It helps separate a fire-sale-driven widening from a credit-driven widening in our issuer set. (Inference.)
- **Also in:** `B_corporate_rfq.md`.

## Formula crib (inference, for the spec)

- Baseline: σ_g = sd(ln s_i). Mean of g_i = −MLD (Theil L).
- If spreads are lognormal: CV² = exp(σ²) − 1, and ln(mean s) − mean(ln s) ≈ σ²/2.
- Robust scale: Q_n(ln s_i), or IQR(ln s_i) / 1.349.
- Robust shape: Bowley (Hinkley) skew and Moors kurtosis of ln s_i.
- Tail share, scale-free: share of names with ln(s_i / median s) > k.
- Tail share, absolute: distress ratio, the share of names with s_i > 1,000bp.
- Lorenz-consistent check: Gini(s_i) or Theil T(s_i).
- Level-based comparison: 95th minus 5th percentile of s_i, in bp.

## Located but left out

- Mansi, Maxwell and Miller (2011), *Review of Accounting Studies*, DOI 10.1007/s11142-010-9127-2. No text could be read.
- Ying et al. (2025), "Belief dispersion in credit markets: Evidence from CDS-Bond basis", *Finance Research Letters*, DOI 10.1016/j.frl.2025.108076. No text could be read.
- Friewald, Jankowitsch and Subrahmanyam (2012), *JFE*, DOI 10.1016/j.jfineco.2012.02.001. No text could be read.
- Gilchrist, Yankov and Zakrajšek (2009), *JME*, DOI 10.1016/j.jmoneco.2009.03.017. DOI verified, content not read.
- Amato and Gyntelberg (2005, BIS Quarterly Review), Bloomberg Intelligence (2022) "Crossover dispersion", Fridson (2021) on distress. Pages blocked.
- No IMF or BIS issuer-level spread dispersion indicator turned up. That is a search result, not proof that none exists.
