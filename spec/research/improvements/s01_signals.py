"""Build every signal once, with posmon's functions, and save them under derived/.

Outputs:
  derived/i5.pkl    dict of I5 tables by group plus levels, entries and forward moves on the 10-year
  derived/panel.pkl long panel: one row per contract per report date
  derived/gate.json replication gate against Goldman's April 2019 numbers
"""
import json
import multiprocessing as mp
import pickle
import warnings

import numpy as np
import pandas as pd

import lib
from lib import DERIVED, FACE, FX, FX_SIZE, HORIZONS, UST, YIELD
from posmon.data import publish_time
from posmon.indicators import db_scaled, filtered_change, filtered_residual, net_pct_oi, sentiment_index
from posmon.ledger import RemovalRule, build_ledger
from posmon.pain import cftc_pain, harmonise_weekly

warnings.simplefilter("ignore", pd.errors.PerformanceWarning)
WINDOWS = (30, 63, 90, 126, 252)
EMPTY_LEDGER = 1e-6  # contracts
RULES = {"pro_rata": RemovalRule.PRO_RATA, "fifo": RemovalRule.FIFO, "low_price_first": RemovalRule.LOW_PRICE_FIRST}
PAIN_FIELDS = {"lev": ("tff", "lev_money_long", "lev_money_short"), "am": ("tff", "asset_mgr_long", "asset_mgr_short"),
               "spec": ("legacy", "noncomm_long", "noncomm_short")}


# ---------------------------------------------------------------------------
# I5 on the 10-year
# ---------------------------------------------------------------------------


def group_nets(basis: str) -> dict:
    tff = {k: lib.cftc("tff", basis, k) for k in UST}
    legacy = {k: lib.cftc("legacy", basis, k) for k in UST}
    am = {k: t.asset_mgr_long - t.asset_mgr_short + t.other_rept_long - t.other_rept_short for k, t in tff.items()}
    return {"am_TYUS": {k: am[k] for k in ("TY", "US")}, "am_all6": am,
            "lev": {k: t.lev_money_long - t.lev_money_short for k, t in tff.items()},
            "spec": {k: t.noncomm_long - t.noncomm_short for k, t in legacy.items()}}


def unfiltered_change(nets: dict, dv01: dict) -> pd.Series:
    """Same weights as filtered_change, with the filter off."""
    total = None
    for tenor, net in nets.items():
        weight = dv01[tenor].reindex(net.index, method="ffill")
        kept = (net.diff() * weight / 1e6).fillna(0.0)
        total = kept if total is None else total.add(kept, fill_value=0.0)
    return total


def build_i5() -> dict:
    yields = lib.yields_bp()
    ten = lib.fred("DGS10") * 100.0
    dv01 = {k: v.dropna() for k, v in lib.dv01_frame().items()}
    combined = group_nets("combined")
    index = lib.cftc("tff", "combined", "TY").index
    index = index[index >= pd.Timestamp("2006-06-13")]
    out = {"groups": {}, "index": index, "ten": ten}
    for name, nets in combined.items():
        nets = {k: v.reindex(index) for k, v in nets.items()}
        filtered = filtered_change(nets, yields, dv01)
        plain = unfiltered_change(nets, dv01)
        out["groups"][name] = {"filtered": filtered, "table": filtered_residual(ten, filtered), "plain": plain,
                               "plain_table": filtered_residual(ten, plain), "nets": nets}
    out["yields"] = yields
    out["dv01"] = dv01
    trading = ten.dropna().index
    out["entry"] = lib.entry_dates(index, trading)
    out["friday"] = lib.friday_dates(index, trading)
    out["tuesday"] = pd.Series(index, index=index)
    return out


def replication_gate(i5: dict) -> dict:
    """Tuesday basis through April 2019, matching Goldman's table."""
    index, ten = i5["index"], i5["ten"]
    level = lib.level_at(ten, index)
    # Goldman's sample ended 30 April 2019, so a row counts only if its 26-week forward window ended by then.
    through = (index + pd.Timedelta(weeks=26)) <= lib.DESIGN_END
    ahead = (level.shift(-26) - level)
    gate = {}
    for name, item in i5["groups"].items():
        table = item["table"]
        use = through & table["score"].notna().values & ahead.notna().values
        gate[name] = {"corr_next_26w": float(table["score"][use].corr(ahead[use])),
                      "slope_bp_per_10mm": float(table["slope"].iloc[0] * 10.0), "scale_bp": float(table["scale"].iloc[0]),
                      "score_2019_04_30": float(table["score"].loc["2019-04-30"]), "n": int(use.sum()),
                      "corr_6m_filtered_vs_6m_yield": float(item["filtered"].rolling(26).sum()[index <= lib.DESIGN_END].corr(level.diff(26)[index <= lib.DESIGN_END]))}
    past = level.diff(26)
    use = through & past.notna().values & ahead.notna().values
    gate["benchmark_corr"] = float(past[use].corr(ahead[use]))
    gate["goldman_claims"] = {"am_corr": -0.43, "lev_corr": -0.18, "spec_corr": -0.26, "benchmark": -0.35, "score": -0.67}
    return gate


# ---------------------------------------------------------------------------
# P2 ledger as of the entry date, with depth
# ---------------------------------------------------------------------------


def pain_rows(position: pd.Series, price: pd.Series, asof: pd.Series, window: int, rule: RemovalRule, side: str,
              sigma: pd.Series) -> pd.DataFrame:
    """One row per report date. The ledger logic matches posmon.pain.cftc_pain, which check_against_posmon verifies."""
    daily = harmonise_weekly(position, price.index)
    frame = pd.DataFrame({"close": price, "change": daily.diff()}).dropna()
    released = np.full(len(frame), np.datetime64("NaT", "ns"))
    for report_date in position.index:
        spot = frame.index.searchsorted(report_date)
        if spot < len(frame.index):
            released[spot] = np.datetime64(publish_time(report_date).tz_localize(None).normalize())
    close = frame["close"].values
    change = frame["change"].values
    stamps = frame.index.values
    live = np.nonzero(change != 0)[0]
    rows = []
    for report, entry in asof.items():
        if pd.isna(entry):
            continue
        end = frame.index.searchsorted(entry, side="right") - 1
        if end < window - 1:
            continue
        begin = end - window + 1
        chosen = live[np.searchsorted(live, begin):np.searchsorted(live, end, side="right")]
        keep = ~(released[chosen] > stamps[end])  # NaT compares False, so an unmapped change stays, as in cftc_pain
        chosen = chosen[keep]
        book = build_ledger(change[chosen], close[chosen], rule)
        level = float(close[end])
        total = book.open_total
        # A fully emptied ledger can keep floating-point residue near 1e-14 contracts. That is an empty ledger.
        # Without this test the share explodes to values like 1e16. posmon.pain._share_in_pain has the same gap.
        if total <= EMPTY_LEDGER:
            unguarded = np.nan
            if total > 0:  # kept only to measure what posmon's unguarded ratio would have returned
                unguarded = (book.open_above(level) if side == "long" else book.open_below(level)) / total
            rows.append((report, np.nan, np.nan, total, unguarded))
            continue
        if side == "long":
            share = book.open_above(level) / total
            depth = sum(lot.open * max(lot.entry - level, 0.0) for lot in book.lots) / total
        else:
            share = book.open_below(level) / total
            depth = sum(lot.open * max(level - lot.entry, 0.0) for lot in book.lots) / total
        scale = sigma.iloc[sigma.index.searchsorted(entry, side="right") - 1]
        rows.append((report, share, depth / scale if scale and np.isfinite(scale) and scale > 0 else np.nan, total, share))
    return pd.DataFrame(rows, columns=["report", "share", "depth", "open", "unguarded"]).set_index("report")


def pain_job(task: tuple) -> tuple:
    symbol, group, side, window, rule_name = task
    report, long_col, short_col = PAIN_FIELDS[group]
    data = lib.cftc(report, "futures", symbol)
    position = data[long_col if side == "long" else short_col].dropna()
    price = lib.asset_price(symbol)
    asof = lib.entry_dates(position.index, price.index)
    sigma = price.diff().rolling(126, min_periods=63).std()
    return task, pain_rows(position, price, asof, window, RULES[rule_name], side, sigma)


def check_against_posmon() -> dict:
    """On TY leveraged-fund longs, the fast path must equal posmon's cftc_pain on the same as-of dates."""
    data = lib.cftc("tff", "futures", "TY")["lev_money_long"].dropna()
    price = lib.asset_price("TY")
    part = price.loc["2013-01-01":"2015-12-31"]
    position = data.loc["2012-06-01":"2015-12-31"]
    slow = cftc_pain(position, part, window=126, rule=RemovalRule.PRO_RATA, side="long", respect_release=True)
    asof = lib.entry_dates(position.index, part.index).dropna()
    fast = pain_rows(position, part, asof, 126, RemovalRule.PRO_RATA, "long", part.diff().rolling(126, min_periods=63).std())
    pairs = [(fast.loc[r, "share"], slow.loc[asof[r], "share_in_pain"]) for r in fast.index if asof[r] in slow.index]
    pairs = np.array(pairs, dtype=float)
    # Where posmon returns a value and this path says "empty", posmon is reading floating-point residue. Count those.
    residue = int(np.sum(np.isnan(pairs[:, 0]) & ~np.isnan(pairs[:, 1])))
    gap = np.nanmax(np.abs(pairs[:, 0] - pairs[:, 1]))
    if gap > 1e-9:
        raise AssertionError(f"fast ledger differs from cftc_pain by {gap}")
    return {"dates_compared": int(len(pairs)), "max_abs_gap": float(gap), "posmon_residue_readings": residue}


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------


def expanding_z(series: pd.Series, min_periods: int) -> pd.Series:
    mean = series.expanding(min_periods).mean()
    std = series.expanding(min_periods).std()
    return (series - mean) / std


def option_signals(symbol: str, frames: dict) -> dict:
    """Combined minus futures-only net, by group. This is the delta-adjusted option position in contracts."""
    out = {}
    tf, tc, lf, lc = frames["tff_futures"], frames["tff_combined"], frames["legacy_futures"], frames["legacy_combined"]
    pairs = {
        "am": (tc.asset_mgr_long - tc.asset_mgr_short + tc.other_rept_long - tc.other_rept_short,
               tf.asset_mgr_long - tf.asset_mgr_short + tf.other_rept_long - tf.other_rept_short, tc.open_interest),
        "lev": (tc.lev_money_long - tc.lev_money_short, tf.lev_money_long - tf.lev_money_short, tc.open_interest),
        "spec": (lc.noncomm_long - lc.noncomm_short, lf.noncomm_long - lf.noncomm_short, lc.open_interest),
    }
    for group, (combined, futures, oi) in pairs.items():
        option = (combined - futures.reindex(combined.index))
        flow = (option.diff() / oi).ewm(halflife=5, adjust=False).mean()
        out[f"opt_flow_{group}"] = flow / flow.expanding(52).std()
        share = option / oi
        out[f"opt_level_{group}"] = (share - share.rolling(156, min_periods=156).mean()) / share.rolling(156, min_periods=156).std()
        out[f"fut_net_oi_{group}"] = futures / oi
    return out


def fx_i5(symbol: str, frames: dict) -> dict:
    """The Goldman filter and residual applied to one currency, through posmon's own functions."""
    spot = lib.spot_usd(symbol)
    pseudo_yield = -100.0 * np.log(spot)
    tc, lc = frames["tff_combined"], frames["legacy_combined"]
    nets = {"am": tc.asset_mgr_long - tc.asset_mgr_short + tc.other_rept_long - tc.other_rept_short,
            "lev": tc.lev_money_long - tc.lev_money_short, "spec": (lc.noncomm_long - lc.noncomm_short)}
    index = tc.index[tc.index >= pd.Timestamp("2006-06-13")]
    notional = (spot * FX_SIZE[symbol]).dropna()
    out = {}
    for group, net in nets.items():
        filtered = filtered_change({symbol: net.reindex(index)}, pd.DataFrame({symbol: pseudo_yield}), {symbol: notional})
        table = filtered_residual(pseudo_yield, filtered)
        out[f"i5fx_{group}"] = table["score"]
        out[f"i5fx_{group}_rule"] = table["signal"]
        out[f"i5fx_{group}_slope"] = table["slope"]
    return out


def contract_frame(symbol: str, pain: dict) -> pd.DataFrame:
    frames = {"tff_futures": lib.cftc("tff", "futures", symbol), "tff_combined": lib.cftc("tff", "combined", symbol),
              "legacy_futures": lib.cftc("legacy", "futures", symbol), "legacy_combined": lib.cftc("legacy", "combined", symbol)}
    legacy = frames["legacy_futures"]
    tff = frames["tff_futures"]
    price = lib.asset_price(symbol)
    index = legacy.index[legacy.index >= pd.Timestamp("2006-01-01")]
    index = index[index >= price.index[0]]
    entry = lib.entry_dates(index, price.index)
    level = lib.level_at(price, pd.DatetimeIndex(entry.values))
    level.index = index
    weekly = level.diff()
    sigma = weekly.rolling(52, min_periods=26).std()
    out = pd.DataFrame({"contract": symbol, "date": index, "entry": entry.values, "sigma": sigma.values, "weekly": weekly.shift(-1).values},
                       index=index)
    for k in HORIZONS:
        out[f"y{k}"] = lib.forward_from(price, entry, k) / (sigma * np.sqrt(k))
    out["past26"] = lib.past_from(price, entry, 26) / (sigma * np.sqrt(26))
    spec_net = legacy.noncomm_long - legacy.noncomm_short
    out["I1"] = net_pct_oi(legacy.noncomm_long, legacy.noncomm_short, legacy.open_interest).reindex(index)
    out["I2"] = sentiment_index(spec_net, 156).reindex(index)
    lev_net = tff.lev_money_long - tff.lev_money_short
    am_net = tff.asset_mgr_long - tff.asset_mgr_short
    out["I2_lev"] = sentiment_index(lev_net, 156).reindex(index)
    out["I3_lev"] = db_scaled(lev_net, 209).reindex(index)
    out["I3_am"] = db_scaled(am_net, 209).reindex(index)
    if symbol in UST:
        weight = lib.dv01_frame()[symbol].dropna()
    else:
        weight = lib.spot_usd(symbol) * FX_SIZE[symbol]
    money = spec_net * weight.reindex(spec_net.index.union(weight.index)).ffill().reindex(spec_net.index) / 1e6
    out["I4"] = expanding_z(money.dropna(), 104).reindex(index)
    for name, series in option_signals(symbol, frames).items():
        out[name] = series.reindex(index)
    if symbol in FX:
        for name, series in fx_i5(symbol, frames).items():
            out[name] = series.reindex(index)
    for key, table in pain.items():
        sym, group, side, window, rule = key
        if sym != symbol:
            continue
        tag = f"{group}_{side}_w{window}_{rule}"
        out[f"share_{tag}"] = table["share"].reindex(index)
        out[f"depth_{tag}"] = table["depth"].reindex(index)
    for group in PAIN_FIELDS:
        for window in WINDOWS:
            for rule in RULES:
                long_col, short_col = f"share_{group}_long_w{window}_{rule}", f"share_{group}_short_w{window}_{rule}"
                if long_col in out and short_col in out:
                    out[f"net_share_{group}_w{window}_{rule}"] = out[long_col] - out[short_col]
                    out[f"net_depth_{group}_w{window}_{rule}"] = (out[f"depth_{group}_long_w{window}_{rule}"]
                                                                  - out[f"depth_{group}_short_w{window}_{rule}"])
    out["market"] = "UST" if symbol in UST else "FX"
    return out.copy()


def main():
    i5 = build_i5()
    gate = replication_gate(i5)
    (DERIVED / "gate.json").write_text(json.dumps(gate, indent=1))
    print(json.dumps(gate, indent=1))
    ledger_check = check_against_posmon()
    print("ledger check", ledger_check)
    (DERIVED / "ledger_check.json").write_text(json.dumps(ledger_check, indent=1))
    with open(DERIVED / "i5.pkl", "wb") as handle:
        pickle.dump(i5, handle)

    tasks = []
    for symbol in UST + FX:
        for group in PAIN_FIELDS:
            for side in ("long", "short"):
                for window, rule in {(126, "pro_rata"), (126, "fifo"), (126, "low_price_first"), (30, "pro_rata"),
                                     (63, "pro_rata"), (90, "pro_rata"), (252, "pro_rata")}:
                    tasks.append((symbol, group, side, window, rule))
    with mp.Pool(16) as pool:
        pain = dict(pool.imap_unordered(pain_job, tasks, chunksize=4))
    print("ledgers done", len(pain), flush=True)
    base = [t for key, t in pain.items() if key[3] == 126 and key[4] == "pro_rata"]
    stacked = pd.concat(base)
    bad = stacked["unguarded"].dropna()
    ledger_check["residue_summary_w126_pro_rata"] = {
        "ledger_readings": int(len(stacked)),
        "residue_ledgers": int(((stacked["open"] > 0) & (stacked["open"] <= EMPTY_LEDGER)).sum()),
        "unguarded_share_outside_0_1": int(((bad < -1e-9) | (bad > 1 + 1e-9)).sum()),
        "unguarded_share_largest_abs": float(bad.abs().max())}
    print(ledger_check, flush=True)
    (DERIVED / "ledger_check.json").write_text(json.dumps(ledger_check, indent=1))
    panel = pd.concat([contract_frame(symbol, pain) for symbol in UST + FX], ignore_index=True)
    panel = panel.sort_values(["date", "contract"]).reset_index(drop=True)
    panel.to_pickle(DERIVED / "panel.pkl")
    print("panel", panel.shape, panel.date.min(), panel.date.max())
    outside = {c: int(((panel[c] < -1e-9) | (panel[c] > 1 + 1e-9)).sum()) for c in panel.columns if c.startswith("share_")}
    if any(outside.values()):
        raise AssertionError(f"share outside 0..1: {outside}")
    print(panel.groupby("contract").agg(first=("date", "min"), last=("date", "max"), rows=("date", "size"), y26=("y26", "count"),
                                        share=("net_share_lev_w126_pro_rata", "count"), I2=("I2", "count"), I3=("I3_lev", "count")))
    assert set(YIELD) == set(UST) and set(FACE) == set(UST)


if __name__ == "__main__":
    main()
