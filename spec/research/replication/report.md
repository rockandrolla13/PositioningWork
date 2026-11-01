# Replication push: verdict by method

Written by the main session from the replication agent's messages, because the harness refused report files from that subagent. Numbers come from `results.json` and `i4_results.json`. Rerun with `run_all.sh`.

"Fitted" means a search chose the value. "Unfitted" means no search touched it.

| Method | Verdict | Key evidence |
|---|---|---|
| I4 | Partial | Base rate 53.6% against 53%, on Tuesday DGS10, June 2009 to January 2018, zero counted as a rally. No position recipe of 63,893 reproduces buy and sell. Closest 59.0% and 45.6%, against 63% and 48%. The main session's reconciliation gives 58.1% and 45.6%, one week apart. |
| I6 | Partial, up from Specified | Band centre correlates 0.9997 and 0.9998. Expanding-SD width 0.9994 and 0.9987. Implied k 0.846 and an unfitted 1.242, against printed 0.85 and 1.25. Raw OPI untested, no strike data. CFTC combined minus futures never beats 0.30. |
| I7 | Partial, up from Specified | Monthly correlation with Figure 42: 0.93, 0.82, 0.80. Weekly tops out at 0.84. COFFEE stays Specified, needs DTCC data. |
| P3 | Verified, with an outside check | The deck's line is legacy `PCT_OPEN`: 80% inside the digitised band on 30 rows of combined data, last value 1.00. From 50 variants. |
| P2 | Specified | The corrected formula is 52% inside the band and reads 0.26 where the deck prints 1.00. So the deck does not verify it. |
| I10 | Partial | Rules hold on 342 live values, with 1 exception. Span 17 gives the wrong UST momentum sign on a proxy index. |
| I8 | Partial | Signals past 1.5 rule out an average of the response. A sum fits better, mean gap 0.31 against 1.10, on yield proxies, from 16 variants. |
| P1 | Specified | The one-page note prints no output value. |
| I9 | Not reproducible | Rests on Citi's private flows and hidden weights. |
| I11 | Specified | Stan, NumPyro, JAX and PyMC are not installed. Needs CmdStan and 40 forms on 136 series. |

Unresolved in I4: Tuesday DGS10 spans -0.84 to +0.69, while Goldman's chart spans -0.93 to +0.76.

Faults in the Deutsche Bank source: Figure 40's cross-sectional turnover line equals Figure 41's reversal line point for point. Figure 42 prints a reversal Sharpe of 0.25, while its text and bar say 0.22.
