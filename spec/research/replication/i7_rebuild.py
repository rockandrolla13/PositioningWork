"""I7: rebuild Deutsche Bank's three CFTC portfolios from public data and compare with Figure 42.

Data: CFTC legacy futures-only, FRED H.10 spot, FRED OECD 3-month rates for carry.
USD/RUB is missing, because H.10 does not carry it. Changes one assumption at a time and counts them.
Writes i7_results.json. The chart series stays in raw/.
"""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

import cache
from i7_chart import chart_series

HERE = Path(__file__).resolve().parent
CODES = {"EUR": "099741", "AUD": "232741", "GBP": "096742", "CAD": "090741", "JPY": "097741", "NZD": "112741", "CHF": "092741",
         "BRL": "102741", "MXN": "095741", "RUB": "089741"}
# series, 1 if quoted USD per foreign unit, else -1.
SPOT = {"EUR": ("DEXUSEU", 1), "AUD": ("DEXUSAL", 1), "GBP": ("DEXUSUK", 1), "CAD": ("DEXCAUS", -1), "JPY": ("DEXJPUS", -1),
        "NZD": ("DEXUSNZ", 1), "CHF": ("DEXSZUS", -1), "BRL": ("DEXBZUS", -1), "MXN": ("DEXMXUS", -1)}
RATE = {"EUR": "IR3TIB01EZM156N", "AUD": "IR3TIB01AUM156N", "GBP": "IR3TIB01GBM156N", "CAD": "IR3TIB01CAM156N", "JPY": "IR3TIB01JPM156N",
        "NZD": "IR3TIB01NZM156N", "CHF": "IR3TIB01CHM156N", "MXN": "IR3TIB01MXM156N", "BRL": "INTDSRBRM193N"}
USD_RATE = "IR3TIB01USM156N"
FLIP = {"CAD", "JPY", "CHF", "BRL", "MXN"}


def positions():
    longs, shorts, net = {}, {}, {}
    for k, code in CODES.items():
        r = cache.cftc("legacy", code, "futures")
        if k == "EUR":
            r = r[r.index >= "1999-01-01"]     # earlier rows on this code are the ECU. FRED no longer serves daily DEM.
        longs[k], shorts[k] = r.noncomm_long, r.noncomm_short
    return pd.DataFrame(longs).sort_index(), pd.DataFrame(shorts).sort_index()


def usdrub():
    """Bank of Russia official USD/RUB (public feed, kept in raw/cbr). Roubles per dollar."""
    path = HERE / "raw" / "cbr" / "usdrub.xml"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        url = "https://www.cbr.ru/scripts/XML_dynamic.asp?date_req1=01/01/1998&date_req2=31/12/2019&VAL_NM_RQ=R01235"
        path.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read())
    text = path.read_text(encoding="windows-1251")
    rows = re.findall(r'<Record Date="(\d\d\.\d\d\.\d{4})"[^>]*><Nominal>(\d+)</Nominal><Value>([\d,]+)</Value>', text)
    s = pd.Series({pd.to_datetime(d, dayfirst=True): float(v.replace(",", ".")) / int(n) for d, n, v in rows}).sort_index()
    return s


def spot_returns():
    out = {}
    r = (1 / usdrub()).pct_change()
    out["RUB"] = r.where(r.abs() < 0.25)
    for k, (series, sign) in SPOT.items():
        s = cache.fred(series).dropna()
        r = s.pct_change() if sign == 1 else (1 / s).pct_change()
        out[k] = r.where(r.abs() < 0.25)    # BRL and MXN regime breaks stay out of the vol estimate only if extreme
    return pd.DataFrame(out).sort_index()


def carry_returns(index):
    us = cache.fred(USD_RATE).dropna()
    out = {}
    for k in CODES:
        try:
            r = cache.fred(RATE[k]).dropna()
        except Exception:
            print("no carry series for", k)
            continue
        diff = (r.reindex(index, method="ffill") - us.reindex(index, method="ffill")) / 100.0 / 252.0
        out[k] = diff
    return pd.DataFrame(out).reindex(index).fillna(0.0)


def cont_signal(longs, shorts, weeks=4):
    L, S = longs.rolling(weeks).sum(), shorts.rolling(weeks).sum()
    return (L - S) / (L + S)


def rev_signal(longs, shorts, returns, vol_days=126, windows=(4, 8, 13)):
    net = longs - shorts
    z = [(net - net.rolling(n).mean()) / net.rolling(n).std() for n in windows]
    avg = sum(z) / len(z)
    vol = returns.rolling(vol_days, min_periods=vol_days // 2).std()
    return -avg / vol.reindex(avg.index, method="ffill")


def cap_weights(w, cap):
    w = w.copy()
    for _ in range(8):
        total = w.abs().sum()
        if total == 0:
            break
        w = w / total
        over = w.abs() > cap + 1e-12
        if not over.any():
            break
        fixed = over
        excess = w[fixed].abs().sum() - cap * fixed.sum()
        w[fixed] = np.sign(w[fixed]) * cap
        free = ~fixed & (w != 0)
        if not free.any():
            break
        w[free] = w[free] * (1 + excess / w[free].abs().sum())
    return w


def ts_weights(sig_row, vol_row, cap=None):
    ok = sig_row.notna() & vol_row.notna() & (vol_row > 0)
    w = pd.Series(0.0, index=sig_row.index)
    if not ok.any():
        return w
    inv = 1 / vol_row[ok]
    w[ok] = np.sign(sig_row[ok]) * inv / inv.sum()
    return cap_weights(w, cap) if cap else w


def cs_weights(sig_row, flip=False, beta=None):
    s = sig_row.dropna().copy()
    w = pd.Series(0.0, index=sig_row.index)
    if len(s) < 4:
        return w
    if flip:     # rank in market-quote orientation
        s[[k for k in s.index if k in FLIP]] *= -1
    order = s.sort_values(ascending=False).index
    half = len(order) // 2
    long_side, short_side = order[:half], order[-half:]
    w[long_side], w[short_side] = 1 / (2 * half), -1 / (2 * half)
    if flip:     # back to foreign-currency orientation
        w[[k for k in w.index if k in FLIP]] *= -1
    if beta is not None:
        b = beta.reindex(w.index).fillna(0.0)
        if (b * b).sum() > 0:
            w = w - b * (w * b).sum() / (b * b).sum()
            total = w.abs().sum()
            w = w / total if total else w
    return w


def rolling_pc1_beta(returns, window=252):
    """Beta of each currency on the first principal component, refreshed every 21 days."""
    betas = {}
    dates = returns.index[window::21]
    for d in dates:
        x = returns.loc[:d].iloc[-window:].dropna(axis=1, thresh=int(window * 0.8)).fillna(0.0)
        if x.shape[1] < 3:
            continue
        u, s, vt = np.linalg.svd(x - x.mean(), full_matrices=False)
        pc = (x - x.mean()).values @ vt[0]
        if vt[0].sum() < 0:
            pc = -pc
        b = {c: np.cov(x[c].values, pc)[0, 1] / pc.var(ddof=1) for c in x.columns}
        betas[d] = b
    return pd.DataFrame(betas).T


def run(weights_by_report, returns, lag_days=6, cost_bps=0.0):
    """weights_by_report is indexed by report date. Lag 6 means Monday's close after release, so P&L starts Tuesday."""
    dates = returns.index
    w = pd.DataFrame(np.nan, index=dates, columns=returns.columns)
    for t, row in weights_by_report.iterrows():
        eff = t + pd.Timedelta(days=lag_days)
        pos = dates.searchsorted(eff)
        if pos < len(dates):
            w.iloc[pos] = row.reindex(returns.columns).values    # by label: column order can differ
    w = w.ffill().shift(1).fillna(0.0)
    gross = (w * returns.fillna(0.0)).sum(axis=1)
    turn = w.diff().abs().sum(axis=1).fillna(0.0)
    return gross - turn * cost_bps / 1e4, turn


def compare(pnl, line, end_date, start_cut="1999-06-01"):
    """Correlate returns over chart bins. Each bin's date comes from a linear x-to-date map."""
    x = line["x"].values
    total_days = (pd.Timestamp(end_date) - pd.Timestamp("2000-01-01")).days
    span_years = (x.max() - x.min()) / 8.025
    start = pd.Timestamp(end_date) - pd.Timedelta(days=span_years * 365.25)
    dates = start + pd.to_timedelta((x - x.min()) / (x.max() - x.min()) * span_years * 365.25, unit="D")
    chart = pd.Series(line["value"].values, index=dates)
    idx = (1 + pnl).cumprod()
    out = {}
    for name, freq in (("weekly", "W-FRI"), ("monthly", "ME"), ("quarterly", "QE")):
        c = np.log(chart.resample(freq).last()).diff()
        m = np.log(idx.resample(freq).last()).diff()
        j = pd.concat([c, m], axis=1, keys=["c", "m"]).dropna().loc[start_cut:]
        out[name] = float(j.c.corr(j.m))
    return out, chart


def sr(p, cut="1999-06-01", end="2018-12-31"):
    p = p.loc[cut:end]
    return float(p.mean() / p.std() * np.sqrt(252))


def build(kind, data, returns=None, vol_days=252, cap=None, flip=False, beta_on=True, windows=(4, 8, 13), rev_vol=126, cont_weeks=4):
    """Weights per report date for one portfolio. Foreign currency long means a positive weight."""
    longs, shorts, beta = data["longs"], data["shorts"], data["beta"]
    returns = data["total"] if returns is None else returns
    vol = returns.rolling(vol_days, min_periods=vol_days // 2).std()
    sig = cont_signal(longs, shorts, cont_weeks) if kind in ("ts", "cs") else rev_signal(longs, shorts, returns, rev_vol, windows)
    rows = {}
    for t, row in sig.loc["1992-09-01":].iterrows():
        have = returns.loc[:t].iloc[-5:].notna().any()
        r = row.where(have)
        if kind == "ts":
            rows[t] = ts_weights(r, vol.reindex([t], method="ffill").iloc[0], cap)
        else:
            b = beta.loc[:t].iloc[-1] if kind == "cs" and beta_on and len(beta.loc[:t]) else None
            rows[t] = cs_weights(r, flip, b)
    return pd.DataFrame(rows).T


def load_data():
    longs, shorts = positions()
    spot = spot_returns()
    carry = carry_returns(spot.index)
    total = spot.add(carry.reindex(spot.index), fill_value=0.0).where(spot.notna())
    return {"longs": longs, "shorts": shorts, "spot": spot, "carry": carry, "total": total, "beta": rolling_pc1_beta(spot.fillna(0.0))}


def main():
    data = load_data()
    spot, total = data["spot"], data["total"]
    lines = chart_series()
    results = {"chart_final": {k: float(v.value.iloc[-1]) for k, v in lines.items()}}
    # Base recipe.
    variants = []

    def score(name, kind, line_key, lag=6, returns=total, cost=0.0, **kw):
        w = build(kind, data, returns=returns, **kw)
        pnl, turn = run(w, returns, lag, cost)
        best = None
        for end in pd.date_range("2018-10-01", "2019-01-15", freq="7D"):
            c, _ = compare(pnl, lines[line_key], end)
            if best is None or c["monthly"] > best[0]["monthly"]:
                best = (c, end)
        row = {"variant": name, "kind": kind, "line": line_key, "sharpe": sr(pnl), "vol": float(pnl.loc["1999-06":"2018"].std() * np.sqrt(252)),
               "turnover_week": float(turn.loc["1999-06":"2018"].mean() * 5), "end_date": best[1].date().isoformat(), **{f"corr_{k}": v for k, v in best[0].items()},
               "ann_return": float(pnl.loc["1999-06":"2018"].mean() * 252)}
        variants.append(row)
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()}, flush=True)
        return pnl

    pd.set_option("display.width", 200)
    # Which grey and dark line is which is known from the legend: b = cross-sectional, c = reversal.
    score("ts base", "ts", "ts")
    score("ts spot only", "ts", "ts", returns=spot)
    score("ts cap15", "ts", "ts", cap=0.15)
    score("ts vol63", "ts", "ts", vol_days=63)
    score("ts vol126", "ts", "ts", vol_days=126)
    score("ts lag3 (Friday)", "ts", "ts", lag=3)
    score("ts lag7", "ts", "ts", lag=7)
    score("ts lag10", "ts", "ts", lag=10)
    score("cs base beta on", "cs", "b")
    score("cs no beta", "cs", "b", beta_on=False)
    score("cs quote orientation", "cs", "b", flip=True)
    score("cs quote orientation no beta", "cs", "b", flip=True, beta_on=False)
    score("cs spot only", "cs", "b", returns=spot)
    score("cs lag3", "cs", "b", lag=3)
    score("rev base", "rev", "c")
    score("rev quote orientation", "rev", "c", flip=True)
    score("rev spot only", "rev", "c", returns=spot)
    score("rev lag3", "rev", "c", lag=3)
    score("rev vol252", "rev", "c", rev_vol=252)
    score("rev windows 4,9,13", "rev", "c", windows=(4, 9, 13))
    frame = pd.DataFrame(variants)
    frame.to_csv(HERE / "raw" / "i7_variants.csv", index=False)
    (HERE / "i7_results.json").write_text(json.dumps({"variants": variants, "chart_final": results["chart_final"], "printed_sharpe": {"ts": 0.33, "cs": 0.25, "rev": 0.25, "rev_text_net": 0.22}}, indent=1))


if __name__ == "__main__":
    main()
