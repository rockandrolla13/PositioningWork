"""I6: read Goldman's OPI line and its thresholds from Exhibit 3, then test everything that needs no option data.

Tests: band recipe from the line itself, signal counts against the printed 189 and 261, hit rates against
DGS10, the printed 4 to 14 December signal, and a CFTC proxy for delta-adjusted option positions.
Writes i6_results.json. The chart series stays in raw/.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

import cache
from pdfkit import EVIDENCE, line_paths, pymupdf

HERE = Path(__file__).resolve().parent
PDF = EVIDENCE / "drive/positioning/Options_implied_position_indicator.pdf"
X0, X1 = 71.7, 276.6     # Exhibit 3
X0_DATA, X1_DATA = X0, X1
UST = {"TU": "042601", "FV": "044601", "TY": "043602", "TN": "043607", "US": "020601", "WN": "020604"}


def inventory():
    page = pymupdf.open(PDF)[2]
    rows = {}
    for c, w, r, pts in line_paths(page):
        if r.x1 <= X1 + 2 and r.x0 >= X0 - 2 and r.y1 < 515:
            rows.setdefault((c, round(w or 0, 2)), []).append((len(pts), r.y0, r.y1))
    for k, v in sorted(rows.items(), key=lambda kv: -sum(x[0] for x in kv[1])):
        print(k, "paths", len(v), "points", sum(x[0] for x in v), "y", round(min(x[1] for x in v), 1), round(max(x[2] for x in v), 1))
    for w in page.get_text("words"):
        if w[0] < 70 and 380 < w[1] < 515 and any(ch.isdigit() for ch in w[4]):
            print(round((w[1] + w[3]) / 2, 2), w[4])


def read(colour, tol=0.01):
    page = pymupdf.open(PDF)[2]
    paths = []
    for c, w, r, p in line_paths(page):
        if abs(c[0] - colour[0]) < tol and abs(c[1] - colour[1]) < tol and abs(c[2] - colour[2]) < tol and r.x1 <= X1 + 2 and r.x0 >= X0 - 2 and r.y1 < 515:
            paths.append(np.array(p))
    xy = np.vstack(paths)
    value = (452.34 - xy[:, 1]) * 0.20 / (507.72 - 396.98)     # 0.00 at 452.34. -0.10 at 507.72. 0.10 at 396.98.
    return pd.Series(value, index=np.round(xy[:, 0], 3)).groupby(level=0).last().sort_index()


def to_dates(s, last, first="2010-01-04"):
    """Place a chart line on bond-market days. Date is linear in x, because x values are pixel-snapped."""
    days = cache.fred("DGS10").dropna().loc[first:last].index
    x = X0_DATA + (X1_DATA - X0_DATA) * np.arange(len(days)) / (len(days) - 1)
    return pd.Series(np.interp(x, s.index.values, s.values), index=days)


def ew_bands(opi, half_life, k, lag, adjust=False):
    m = opi.ewm(halflife=half_life, adjust=adjust).mean()
    sd = opi.ewm(halflife=half_life, adjust=adjust).std()
    if lag:
        m, sd = m.shift(1), sd.shift(1)
    return m + k * sd, m - k * sd


def main():
    opi_x, up_x, low_x = read((0.0, 0.176, 0.325)), read((0.745, 0.196, 0.196)), read((0.027, 0.522, 0.286))
    dx = np.diff(opi_x.index.values)
    print("points", len(opi_x), len(up_x), len(low_x), "dx median", np.median(dx), "max", dx.max(), "share near median", np.mean(np.abs(dx - np.median(dx)) < 0.005))
    global X0_DATA, X1_DATA
    X0_DATA, X1_DATA = opi_x.index.min(), opi_x.index.max()
    opi, up, low = opi_x, up_x, low_x
    print("first opi", round(opi.iloc[0], 4), "last opi", round(opi.iloc[-1], 4), "x range", X0_DATA, X1_DATA)
    out = {"points_opi": len(opi_x), "printed": {"sell_n": 189, "buy_n": 261, "sell_hit": 0.640, "buy_hit": 0.732, "all_hit": 0.693, "sell_mean": 0.10, "buy_mean": -0.12, "sell_sd": 0.24, "buy_sd": 0.20}}
    d10 = cache.fred("DGS10").dropna()
    rows = []
    for last in pd.date_range("2019-01-02", "2019-01-17", freq="B"):
        o, u, l = to_dates(opi, last), to_dates(up, last), to_dates(low, last)
        sell, buy = o > u, o < l
        ahead = (d10.shift(-20) - d10).reindex(o.index)
        ok = ahead.notna()
        dec = o.loc["2018-12-01":"2018-12-20"][buy.loc["2018-12-01":"2018-12-20"]]
        rows.append({"last": last.date().isoformat(), "n_sell": int((sell & ok).sum()), "n_buy": int((buy & ok).sum()), "sell_all": int(sell.sum()), "buy_all": int(buy.sum()),
                     "hit_sell": float((ahead[sell & ok] > 0).mean()), "hit_buy": float((ahead[buy & ok] < 0).mean()), "hit_sell_ge": float((ahead[sell & ok] >= 0).mean()), "hit_buy_le": float((ahead[buy & ok] <= 0).mean()),
                     "mean_sell": float(ahead[sell & ok].mean()), "mean_buy": float(ahead[buy & ok].mean()), "sd_sell": float(ahead[sell & ok].std()), "sd_buy": float(ahead[buy & ok].std()),
                     "dec_buy_first": dec.index[0].date().isoformat() if len(dec) else None, "dec_buy_last": dec.index[-1].date().isoformat() if len(dec) else None, "n_dec": len(dec)})
    table = pd.DataFrame(rows)
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 30)
    print(table.round(3).to_string())
    out["date_map_table"] = rows
    # Pick the map that puts the printed December buy signal on 4 to 14 December. This uses only the printed dates.
    table["dec_gap"] = [abs((pd.Timestamp(a) - pd.Timestamp("2018-12-04")).days) + abs((pd.Timestamp(b) - pd.Timestamp("2018-12-14")).days) if a else 99 for a, b in zip(table.dec_buy_first, table.dec_buy_last)]
    last = pd.Timestamp(table.sort_values("dec_gap").iloc[0]["last"])
    print("chosen last date", last.date())
    o, u, l = to_dates(opi, last), to_dates(up, last), to_dates(low, last)
    # Band recipe.
    rows = []
    for h, k, lag, adj in itertools.product((21, 42, 63, 65, 84, 126), (0.85,), (True, False), (False, True)):
        bu, bl = ew_bands(o, h, k, lag, adj)
        cut = "2011-01-01"
        rows.append({"half_life": h, "k": k, "lag": lag, "adjust": adj, "rmse_upper": float(np.sqrt(((bu - u).loc[cut:] ** 2).mean())), "rmse_lower": float(np.sqrt(((bl - l).loc[cut:] ** 2).mean())),
                     "corr_upper": float(bu.loc[cut:].corr(u.loc[cut:])), "corr_lower": float(bl.loc[cut:].corr(l.loc[cut:]))})
    bands = pd.DataFrame(rows).sort_values("rmse_upper")
    print(bands.round(4).to_string())
    out["band_grid"] = rows
    centre, half = (u + l) / 2, (u - l) / 2
    best = bands.iloc[0]
    m = o.ewm(halflife=best.half_life, adjust=bool(best.adjust)).mean()
    sd = o.ewm(halflife=best.half_life, adjust=bool(best.adjust)).std()
    if best.lag:
        m, sd = m.shift(1), sd.shift(1)
    out["implied_k"] = float((half / sd).loc["2011":].median())
    out["implied_k_iqr"] = [float((half / sd).loc["2011":].quantile(q)) for q in (0.25, 0.75)]
    out["centre_rmse"] = float(np.sqrt(((centre - m).loc["2011":] ** 2).mean()))
    print("implied k median", out["implied_k"], out["implied_k_iqr"], "centre rmse", out["centre_rmse"], "OPI sd", float(o.std()))
    # Signal statistics on the final map, whole sample and the printed split.
    ahead = (d10.shift(-20) - d10).reindex(o.index)
    sell, buy = (o > u), (o < l)
    stats = {}
    for name, mask in (("all", ahead.notna()), ("2010-2015", ahead.notna() & (o.index <= "2015-12-31")), ("2016+", ahead.notna() & (o.index >= "2016-01-01"))):
        s, b = sell & mask, buy & mask
        stats[name] = {"n_sell": int(s.sum()), "n_buy": int(b.sum()), "hit_sell": float((ahead[s] > 0).mean()), "hit_buy": float((ahead[b] < 0).mean()), "hit_all": float(((ahead[s] > 0).sum() + (ahead[b] < 0).sum()) / (s.sum() + b.sum())),
                       "mean_sell": float(ahead[s].mean()), "mean_buy": float(ahead[b].mean()), "median_sell": float(ahead[s].median()), "median_buy": float(ahead[b].median()), "sd_sell": float(ahead[s].std()), "sd_buy": float(ahead[b].std()),
                       "uncond_selloff": float((ahead[mask] > 0).mean())}
    print(json.dumps(stats, indent=1))
    out["stats"] = stats
    out["chosen_last"] = last.date().isoformat()
    # CFTC proxy for delta-adjusted option positions.
    rows = []
    for report, group, net_of in (("legacy", "noncomm", lambda t: t.noncomm_long - t.noncomm_short), ("tff", "lev", lambda t: t.lev_money_long - t.lev_money_short),
                                  ("tff", "am", lambda t: t.asset_mgr_long - t.asset_mgr_short), ("tff", "dealer", lambda t: t.dealer_long - t.dealer_short)):
        for contract in ("TY", "all"):
            members = ("TY",) if contract == "TY" else tuple(UST)
            total = None
            for k in members:
                f, c = cache.cftc(report, UST[k], "futures"), cache.cftc(report, UST[k], "combined")
                gap = (net_of(c) - net_of(f)).dropna()
                total = gap if total is None else total.add(gap, fill_value=0.0)
            wk = o.reindex(total.index, method="ffill").loc["2010-06-01":"2019-01-08"]
            flow = total.diff().ewm(halflife=5, adjust=False).mean().reindex(wk.index)
            flow_oi = (total.diff() / cache.cftc(report, UST["TY"], "combined").open_interest).ewm(halflife=5, adjust=False).mean().reindex(wk.index)
            level_chg = total.diff(13).reindex(wk.index)
            for name, x in (("ema flow", flow), ("ema flow / OI", flow_oi), ("13w change", level_chg), ("level", total.reindex(wk.index))):
                rows.append({"report": report, "group": group, "contract": contract, "proxy": name, "corr": float(x.corr(wk)), "corr_lag4w": float(x.shift(4).corr(wk)), "n": int(x.notna().sum())})
    proxy = pd.DataFrame(rows).sort_values("corr", key=np.abs, ascending=False)
    print(proxy.head(12).round(3).to_string())
    out["proxy_rows"] = rows
    (HERE / "i6_results.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
