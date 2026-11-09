# Credit spread dispersion: spec

Source: `scrap dispersion.xls`, Google Drive, last saved 6 January 2006.
The `Dispersion versus Basis.xls` workbook is out of scope.

## 1. What it measures

The measure gives one number for how spread out a basket's credit spreads are on one date.
It works in log terms, so it ignores the overall spread level.

## 2. Inputs

| Name | Type | Rule |
|---|---|---|
| `s` | vector of N spreads, in bp | Each value must be > 0. N ≥ 4 (needed for kurtosis). |
| `ref` | scalar, in bp | Reference level. Default: `mean(s)`. |

## 3. Formula

For each issuer i:

```
g_i = ln( s_i / ref )
```

Outputs, all computed over the N values of `g`:

| Output | Definition | Excel |
|---|---|---|
| `level` | mean of g | `AVERAGE` |
| `dispersion` | sample standard deviation of g (divides by N−1) | `STDEV` |
| `skew` | adjusted sample skewness of g | `SKEW` |
| `kurt` | adjusted sample excess kurtosis of g | `KURT` |

`skew` and `kurt` must match Excel. In Python, use `scipy.stats.skew(g, bias=False)` and `scipy.stats.kurtosis(g, bias=False)`.

## 4. Properties the code must keep

1. **Scale invariance.** If every spread is multiplied by k > 0, then `dispersion`, `skew` and `kurt` stay the same. `level` moves by ln(k), but only when `ref` is held fixed.
2. **Additive shocks compress.** Adding c > 0 bp to every spread lowers `dispersion`. Tight names gain more in log terms than wide ones.
3. **The default reference is an arithmetic mean, not a geometric mean.** With `ref = mean(s)`, `level` is ≤ 0 (Jensen's inequality, which says the mean of the logs is at most the log of the mean). It equals 0 only when all spreads are equal.
   With this reference, `−level` is Theil's L index, also called the mean log deviation. It measures inequality of the spreads.
4. **`dispersion` does not depend on `ref`.** Changing `ref` shifts every g_i by the same amount. So `dispersion` equals sd(ln s).

## 5. Stress tests (from the source sheet)

The sheet applies three shocks to the spreads. It keeps `ref` fixed at the unshocked mean.

| Shock | New spreads |
|---|---|
| `x1.1` | `1.1 · s` |
| `+10bp` | `s + 10` |
| `x0.9` | `0.9 · s` |

## 6. Test vector

These are the 31 spreads in the sheet, cells `F8:F38`:

```
216.5, 195, 61, 540, 59, 82, 30, 65, 90, 55, 66, 48, 59, 126, 73, 87,
69, 71, 70, 105, 68, 50, 34, 107, 107, 258, 79, 33, 118, 87, 76
```

Expected outputs, with `ref = mean(s)` of the unshocked spreads (about 99.24 bp). Python and Excel agree to at least 12 decimal places.

| Shock | level | dispersion | skew | kurt |
|---|---|---|---|---|
| none | −0.221093 | 0.603785 | 1.113314 | 2.270941 |
| x1.1 | −0.125782 | 0.603785 | 1.113314 | 2.270941 |
| +10bp | −0.091288 | 0.546770 | 1.324849 | 2.777305 |
| x0.9 | −0.326453 | 0.603785 | 1.113314 | 2.270941 |

## 7. Edge cases

1. A spread ≤ 0 makes the log undefined. Raise an error. Do not drop the name silently.
2. Missing spreads: drop them, and report N used.
3. N < 4: return `dispersion` and `skew` only if N allows. Return NaN for the rest.

## 8. Known defect in the source

The row labels in column D sit one row off.
`D5` says "st.dev" but row 5 computes `SKEW`.
`D6` says "skew" but row 6 computes `KURT`.
`D7` says "tails" but row 7 computes `STDEV`.
The formulas are correct. Only the labels are wrong.

## 9. Open questions

1. Weights. The sheet weights every name equally. Should names be weighted by notional or index weight?
2. Reference. Should `ref` be the basket mean, the median, or the geometric mean? The geometric mean makes `level` exactly 0.
3. Alternatives. See `../literature/F_spread_dispersion.md` for other dispersion measures.
