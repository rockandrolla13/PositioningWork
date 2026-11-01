"""I7: test tranching, carry and sign choices on a fixed chart date map (12 Oct 1992 to 10 Dec 2018).

N-week windows hold the mean of the last N weekly single-tranche portfolios ("all tranched weekly").
Printed targets come from the Figure 40 and 41 bars. No weights or scales are fitted.
Writes i7_results.json and raw/i7_tranche.csv.
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

import cache
from i7_align import corr, mapped
from i7_chart import chart_series
from i7_rebuild import build, load_data, run, sr

HERE = Path(__file__).resolve().parent
START, END = "1992-10-12", "2018-12-10"
# Bars read from the PDF's vector rectangles (Sharpe with cost, weekly effective turnover).
PRINTED = {"ts": {"1W": (0.400, 16.66), "2W": (0.350, 13.07), "1M": (0.332, 9.96), "3M": (0.305, 5.58)},
           "cs": {"1W": (0.082, 56.4), "2W": (0.193, 42.4), "1M": (0.159, 25.8), "3M": (-0.127, 9.4)},
           "rev": {"1W": (0.223, 56.4), "2W": (0.242, 42.4), "1M": (0.140, 25.8), "3M": (-0.072, 9.4)}}
LEGEND = {"ts": 0.33, "cs": 0.25, "rev": 0.25}
N_WEEKS = {"1W": 1, "2W": 2, "1M": 4, "3M": 13}
LINE = {"ts": "ts", "cs": "b", "rev": "c"}


def blue_bars():
    """Sharpe without cost, from the polygons that draw the blue bars."""
    from i7_chart import PDF
    from pdfkit import pymupdf
    page = pymupdf.open(PDF)[27]
    axes = {"ts": (250.7, 205.3), "cs": (394.0, 272.25), "rev": (589.8, 245.0)}
    out = {}
    for d in page.get_drawings():
        f = d.get("fill")
        r = d["rect"]
        if f is None or abs(f[0] - 0.357) > 0.01 or r.x0 < 330 or len(d["items"]) != 4:
            continue
        key = "ts" if r.y0 < 260 else ("cs" if r.y0 < 430 else "rev")
        zero, per = axes[key]
        vals = {}
        for item, name in zip(sorted(d["items"], key=lambda it: it[1].x0), N_WEEKS):
            rr = item[1]
            top = rr.y0 if abs(rr.y1 - zero) < abs(rr.y0 - zero) else rr.y1
            vals[name] = round((zero - top) / per, 3)
        out[key] = vals
    return out


def main():
    path = HERE / "raw" / "i7_data.pkl"
    if not path.exists():
        pickle.dump(load_data(), open(path, "wb"))
    data = pickle.load(open(path, "rb"))
    lines = chart_series()
    charts = {k: mapped(lines[LINE[k]], START, END) for k in LINE}
    spot, total = data["spot"], data["total"]
    gross = blue_bars()
    print("printed gross Sharpe", gross)
    rows = []

    def evaluate(kind, label, returns, n, **kw):
        w = build(kind, data, returns=returns, **kw)
        w = w.rolling(n, min_periods=1).mean()
        # After tranching the weights no longer sum to 100%. That is the construction, so leave them.
        pnl, turn = run(w, returns, kw.pop("lag", 6) if False else 6)
        chart = charts[kind]
        name = {1: "1W", 2: "2W", 4: "1M", 13: "3M"}[n]
        row = {"kind": kind, "variant": label, "window": name, "corr_w": corr(chart, pnl, "W-FRI"), "corr_m": corr(chart, pnl, "ME"), "corr_q": corr(chart, pnl, "QE"),
               "sharpe_1999": sr(pnl), "vol_1999": float(pnl.loc["1999-06":"2018"].std() * np.sqrt(252)), "turn_week_pct": float(turn.loc["1999-06":"2018"].mean() * 5 * 100),
               "printed_net": PRINTED[kind][name][0], "printed_turn": PRINTED[kind][name][1], "printed_gross": gross.get(kind, {}).get(name)}
        rows.append(row)
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()}, flush=True)

    for kind in ("ts", "cs", "rev"):
        for n in (1, 2, 4, 13):
            evaluate(kind, "spot", spot, n)
            evaluate(kind, "total", total, n)
    # One assumption at a time, on the weekly window, with carry in.
    for days in (21, 42, 63, 126):
        evaluate("ts", f"total vol{days}", total, 1, vol_days=days)
    evaluate("ts", "total cap15", total, 1, cap=0.15)
    evaluate("cs", "total no beta", total, 1, beta_on=False)
    evaluate("cs", "total quote orientation", total, 1, flip=True)
    evaluate("rev", "total quote orientation", total, 1, flip=True)
    evaluate("rev", "total vol252", total, 1, rev_vol=252)
    evaluate("rev", "total vol63", total, 1, rev_vol=63)
    frame = pd.DataFrame(rows)
    frame.to_csv(HERE / "raw" / "i7_tranche.csv", index=False)
    chart_sr = {}
    for k, c in charts.items():
        wk = np.log(c.resample("W-FRI").last()).diff().dropna()
        chart_sr[k] = {"sharpe_all": float(wk.mean() / wk.std() * np.sqrt(52)), "sharpe_1999": float(wk.loc["1999-06":].mean() / wk.loc["1999-06":].std() * np.sqrt(52)),
                       "vol_1999": float(wk.loc["1999-06":].std() * np.sqrt(52))}
    # Stability: first half and second half correlations of the base recipes.
    halves = {}
    for kind, returns in (("ts", total), ("cs", total), ("rev", total)):
        pnl, _ = run(build(kind, data, returns=returns), returns, 6)
        halves[kind] = {"1999-2008": corr(charts[kind].loc[:"2008-12-31"], pnl, "ME"), "2009-2018": corr(charts[kind].loc["2009":], pnl, "ME", cut="2009-01-01"),
                        "1993-1998 (no EUR)": corr(charts[kind].loc[:"1998-12-31"], pnl, "ME", cut="1993-03-01")}
    print(halves)
    print(chart_sr)
    (HERE / "i7_results.json").write_text(json.dumps({"date_map": [START, END], "variants_run": len(frame), "rows": rows, "chart_stats": chart_sr, "halves": halves,
                                                      "printed_legend_sharpe": LEGEND, "printed_net_turnover": PRINTED, "printed_gross": gross,
                                                      "note_turnover_copy": "Figure 40's cross-sectional turnover line equals Figure 41's reversal line point for point."}, indent=1, default=float))
    return frame


if __name__ == "__main__":
    main()
