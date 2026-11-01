"""Draw every figure in the specification from tested code. Run from the spec directory."""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from posmon.data import fetch_cftc  # noqa: E402
from posmon.indicators import sentiment_index  # noqa: E402
from posmon.ledger import RemovalRule, bucket_lots, build_ledger  # noqa: E402
from posmon.pain import legacy_position_per_strike, ms_pain_monitor, typical_price  # noqa: E402

LONG, SHORT, GOOD_LINE, BAD = "#2a78d6", "#eb6834", "#1baf7a", "#d03b3b"
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.5, "pdf.fonttype": 42, "axes.edgecolor": MUTED, "axes.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 10, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
    "axes.labelcolor": MUTED, "legend.frameon": False, "figure.dpi": 150, "savefig.bbox": "tight",
    "hatch.linewidth": 0.5,
})


def note(ax, text, xy, xytext, color=INK):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=8, color=color, va="center",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6, shrinkA=0, shrinkB=2))


def fig_ledger():
    close = pd.Series([100, 101, 102, 101.2, 100.5, 101.5, 100.8, 101.3], dtype=float)
    vwap = pd.Series([100, 100.6, 101.6, 101.7, 100.9, 101.0, 101.2, 101.1], dtype=float)
    oi = pd.Series([1000, 1100, 1160, 1210, 1170, 1150, 1190, 1180], dtype=float)
    out = ms_pain_monitor(close, vwap, oi, multiplier=1000.0, window=7)
    labels = ["", "new longs\n+100", "new longs\n+60", "new shorts\n+50", "longs off\n−40", "shorts covered\n−20",
              "new shorts\n+40", "shorts covered\n−10"]
    colors = [MUTED, LONG, LONG, SHORT, LONG, SHORT, SHORT, SHORT]
    figure, (left, right) = plt.subplots(1, 2, figsize=(7.2, 3.15), gridspec_kw={"width_ratios": [1.15, 1]})
    left.plot(close.index, close.values, color=MUTED, lw=1.2, zorder=1)
    for day in close.index[1:]:
        filled = labels[day].startswith("new")
        left.scatter(day, close[day], s=38, zorder=2, edgecolor=colors[day], linewidth=1.3,
                     facecolor=colors[day] if filled else SURFACE)
        spot = {1: (-0.12, 0.0, "right", "center"), 2: (0.0, 0.14, "center", "bottom"), 3: (0.14, 0.0, "left", "center"),
                4: (0.0, -0.14, "center", "top"), 5: (0.0, 0.14, "center", "bottom"), 6: (0.0, -0.14, "center", "top"),
                7: (0.0, 0.14, "center", "bottom")}[day]
        left.text(day + spot[0], close[day] + spot[1], labels[day], ha=spot[2], va=spot[3], fontsize=6.8, color=INK)
    left.set_ylim(99.4, 102.9)
    left.set_xlim(-0.3, 7.7)
    left.set_xlabel("Day")
    left.set_ylabel("Close")
    left.set_title("Step 1. Each day's change gets one label")
    left.grid(axis="y", color=GRID, lw=0.5)

    right.axhline(101.3, color=INK, lw=0.9, zorder=3)
    right.text(-200, 101.325, "as-of close 101.3", fontsize=7.5, va="bottom", ha="left")
    for side, book, color, sign in (("long", out["long_book"], LONG, 1), ("short", out["short_book"], SHORT, -1)):
        for lot in book.lots:
            right.barh(lot.entry, sign * lot.open, height=0.17, color=color, zorder=2)
            right.barh(lot.entry, sign * (lot.gross - lot.open), left=sign * lot.open, height=0.17,
                       facecolor="none", edgecolor=color, hatch="////", lw=0.5, zorder=2)
            offside = lot.entry > 101.3 if side == "long" else lot.entry < 101.3
            text = f"{lot.open:.1f} at {lot.entry:.1f}" + (" offside" if offside else "")
            right.text(sign * (lot.gross + 5), lot.entry, text, fontsize=7, va="center",
                       ha="left" if sign > 0 else "right", color=BAD if offside else INK)
    right.axvline(0, color=MUTED, lw=0.6)
    right.set_xlim(-205, 172)
    right.set_ylim(100.2, 102.1)
    right.set_xticks([-100, -50, 0, 50, 100])
    right.set_xticklabels(["100", "50", "0", "50", "100"])
    right.set_xlabel("Shorts (left), longs (right), contracts")
    right.set_ylabel("Entry price")
    right.set_title("Step 2. Lots at entry price after removals")
    right.text(168, 100.27, "solid = still open, hatched = removed", fontsize=7, ha="right", color=MUTED,
               bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.5), zorder=5)
    figure.tight_layout()
    figure.savefig("figures/ledger.pdf")


def fig_rules():
    changes, prices = [20, 20, 20, -30], [110, 100, 105, 102]
    level = 107.0
    cases = [("Pro rata (default)\nMS 2014, 2015 emails", RemovalRule.PRO_RATA),
             ("FIFO\n2018 deck, page 16", RemovalRule.FIFO),
             ("Low price first\n2018 function text", RemovalRule.LOW_PRICE_FIRST)]
    figure, axes = plt.subplots(1, 4, figsize=(7.2, 2.5), sharey=True, sharex=True)
    for ax, (title, rule) in zip(axes, cases):
        book = build_ledger(changes, prices, rule)
        for lot in book.lots:
            ax.barh(lot.entry, lot.open, height=3, color=LONG)
            ax.barh(lot.entry, lot.gross - lot.open, left=lot.open, height=3, facecolor="none", edgecolor=LONG,
                    hatch="////", lw=0.5)
        share = book.open_above(level) / book.open_total
        ax.set_title(title, fontsize=7.6)
        ax.text(0.5, 90.2, f"removed {book.removed:.0f}\n{share:.0%} in pain", fontsize=8, ha="left", va="bottom")
    legacy = legacy_position_per_strike([20, 20, 20, -30, 0], [110, 100, 105, 102, 100])
    held = [(p, g, o) for p, g, o in zip(legacy["prices"], legacy["gross"], legacy["open"]) if g]
    ax = axes[3]
    for (price, gross, open_now), entry in zip(held, (100.0, 105.0, 110.0)):
        ax.barh(entry, open_now, height=3, color=BAD)
        ax.barh(entry, gross - open_now, left=open_now, height=3, facecolor="none", edgecolor=BAD, hatch="////", lw=0.5)
    pain = sum(o for p, _, o in held if p >= level) / sum(o for _, _, o in held)
    ax.set_title("Legacy code (defect)\nremoves too much", fontsize=7.6)
    ax.text(0.5, 90.2, f"removed {sum(legacy['closed']):.1f}\n{pain:.0%} in pain", fontsize=8, ha="left", va="bottom", color=BAD)
    for ax in axes:
        ax.axhline(level, color=INK, lw=0.9)
        ax.set_xlim(0, 22)
        ax.set_ylim(89.5, 112.5)
        ax.set_yticks([100, 105, 110])
        ax.set_xlabel("Contracts")
    axes[0].set_ylabel("Entry price")
    axes[0].text(0.4, 107.3, "close 107", fontsize=7.5, va="bottom")
    figure.tight_layout()
    figure.savefig("figures/rules.pdf")


def fig_ladder():
    data = json.loads(Path("data/reconcile.json").read_text())["natural_gas_ladder"]
    ratios = np.array(data["ratios"])
    figure, ax = plt.subplots(figsize=(7.2, 2.7))
    ax.step(ratios, np.array(data["legacy_open"]) / 1000, where="mid", color=BAD, lw=1.8, label="Legacy OPEN >= path")
    ax.step(ratios, np.array(data["correct_open"]) / 1000, where="mid", color=LONG, lw=1.8, label="Correct price test")
    ax.scatter([0.5, 1.5], [69, 69], marker="D", s=26, facecolor=SURFACE, edgecolor=INK, zorder=4,
               label="Deck bars, read by eye")
    ax.set_xlim(0.45, 1.55)
    ax.set_ylim(0, 84)
    ax.set_xticks(ratios)
    ax.set_xlabel("Entry price as a multiple of the current price")
    ax.set_ylabel("Open money-manager longs,\nthousand contracts")
    ax.grid(axis="y", color=GRID, lw=0.5)
    ax.legend(loc="upper center", ncol=3, fontsize=8, bbox_to_anchor=(0.5, 1.17))
    note(ax, "A flat line is the sign of the defect.\nIt counts lots that pass a size test, not a price test.",
         (1.25, 69.3), (0.80, 79))
    note(ax, "The line stays above zero only because\nthe rebuild uses cash prices, which spiked to $6.24.",
         (1.35, 22.2), (0.93, 9.5))
    figure.tight_layout()
    figure.savefig("figures/ladder.pdf")


def fig_si():
    report = fetch_cftc("legacy", "042601", "2012-01-01", "2016-08-01")
    net = (report.noncomm_long - report.noncomm_short) / 1000.0
    si = sentiment_index(net, 156)
    low = net.rolling(156, min_periods=156).min()
    high = net.rolling(156, min_periods=156).max()
    start = pd.Timestamp("2015-01-01")
    figure, (top, bottom) = plt.subplots(2, 1, figsize=(7.2, 3.4), sharex=True, gridspec_kw={"height_ratios": [1.15, 1]})
    top.plot(net.loc[start:], color=INK, lw=1.2)
    top.plot(high.loc[start:], color=MUTED, lw=0.8, ls="--")
    top.plot(low.loc[start:], color=MUTED, lw=0.8, ls="--")
    top.set_title("Step 1. Net speculative position in 2-year futures, with its 3-year high and low")
    top.set_ylabel("Thousand contracts")
    top.grid(axis="y", color=GRID, lw=0.5)
    stamp = pd.Timestamp("2016-07-12")
    bottom.plot(si.loc[start:], color=LONG, lw=1.3)
    bottom.axhspan(90, 100, color=SHORT, alpha=0.12, lw=0)
    bottom.axhspan(0, 10, color=LONG, alpha=0.12, lw=0)
    bottom.scatter([stamp], [si.loc[stamp]], s=28, color=INK, zorder=3)
    note(bottom, f"12 Jul 2016: {si.loc[stamp]:.1f}\nGoldman prints 64", (stamp, si.loc[stamp]),
         (pd.Timestamp("2015-12-20"), 92))
    zero = si.loc["2016-05-15":"2016-06-20"]
    zero = zero[zero == 0].index[0]
    note(bottom, "Zero: a new\n3-year low", (zero, 0), (pd.Timestamp("2016-02-20"), 62))
    bottom.set_title("Step 2. Where today sits between them: the sentiment index")
    bottom.set_ylabel("Index, 0 to 100")
    bottom.set_ylim(-4, 104)
    bottom.grid(axis="y", color=GRID, lw=0.5)
    figure.tight_layout()
    figure.savefig("figures/si.pdf")


def fig_ty():
    daily = pd.read_csv("data/ty_daily.csv", parse_dates=["date"], index_col="date")
    tp = typical_price(daily["high"], daily["low"], daily["close"])
    out = ms_pain_monitor(daily["close"], tp, daily["open_interest"], multiplier=1000.0, window=30)
    low, high = tp.iloc[-30:].min(), tp.iloc[-30:].max()
    figure, ax = plt.subplots(figsize=(7.2, 2.9))
    height = (high - low) / 10 * 0.8
    for book, color, sign in ((out["long_book"], LONG, 1), (out["short_book"], SHORT, -1)):
        for edge, gross, removed, open_now in bucket_lots(book, low, high):
            centre = edge + (high - low) / 20
            ax.barh(centre, sign * open_now / 1000, height=height, color=color)
            ax.barh(centre, sign * removed / 1000, left=sign * open_now / 1000, height=height, facecolor="none",
                    edgecolor=color, hatch="////", lw=0.5)
    ax.axhline(out["close"], color=INK, lw=0.9)
    ax.axvline(0, color=MUTED, lw=0.6)
    ax.text(ax.get_xlim()[1], out["close"] + 0.04, f"close {out['close']:.3f}", ha="right", va="bottom", fontsize=8)
    ax.set_xlabel("Shorts (left), longs (right), thousand contracts.  Solid = open.  Hatched = removed.")
    ax.set_ylabel("Entry price (bucket centre)")
    limit = ax.get_xlim()
    ax.text(limit[1], low - 0.02, f"{out['long_offside_pct_new']:.0%} of new longs offside: the lots above the line",
            ha="right", va="bottom", fontsize=8, color=LONG)
    ax.text(limit[0] + 1, high + 0.25, f"{out['short_offside_pct_new']:.0%} of new shorts offside:\nevery open short lot\nis below the line",
            ha="left", va="top", fontsize=8, color=SHORT)
    figure.tight_layout()
    figure.savefig("figures/ty_ladder.pdf")


if __name__ == "__main__":
    Path("figures").mkdir(exist_ok=True)
    fig_ledger()
    fig_rules()
    fig_ladder()
    fig_si()
    fig_ty()
    print("figures done")
