#!/usr/bin/env python3
"""Build one daily and one weekly panel per fund. Every weekly signal uses rows dated before its week-end date.

Weekly date W is the last trading day of the week. Inputs stop at the trading day before W (T+1 publication).
Forward returns start at the close of W. Output goes to work/.
"""
from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd

from common import (CARRY, DEFAULT_DURATION, GROUP, ISHARES, RAW, SSGA, WORK, load_finra, load_fred, load_ishares,
                    load_ssga, load_yahoo, matched_hedge, treasury_curve)
from posmon.cta import cta_signal
from posmon.indicators import (cftc_continuation, cftc_reversal, db_scaled, filtered_change, filtered_residual,
                               sentiment_index)
from posmon.ledger import RemovalRule, build_ledger
from posmon.pain import classify_changes, ms_pain_monitor, workbook_over_under

warnings.filterwarnings("ignore", category=RuntimeWarning)
DEV_END = pd.Timestamp("2016-12-31")
FIT_START, FIT_END = "2008-01-01", "2016-12-31"
SI_LAG_DAYS = 10


def daily_panel(ticker: str, curve: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Merge fund file and market file on market trading days, then add returns and the hedge."""
    prices, dividends, splits = load_yahoo(ticker)
    facts: dict = {}
    if ticker in ISHARES:
        fund = load_ishares(ticker)
        issuer_div = fund["div"].where(fund["div"] > 0)
    else:
        fund = load_ssga(ticker)
        issuer_div = pd.Series(dtype=float)
    frame = prices.copy()
    frame = frame.join(fund[["nav", "so"]], how="left")
    frame = frame[frame.index >= fund["so"].dropna().index.min()]
    facts["fund_first"] = str(fund.index.min().date())
    facts["fund_last"] = str(fund["so"].dropna().index.max().date())
    facts["market_rows"] = int(len(frame))
    facts["nav_missing"] = int(frame["nav"].isna().sum())
    facts["so_missing"] = int(frame["so"].isna().sum())
    facts["so_changed_share"] = float((frame["so"].dropna().diff().dropna() != 0).mean())
    facts["splits"] = {str(k.date()): float(v) for k, v in splits.items()}
    # Stop where the fund file stops. A forward fill past the file's end would invent flat flows.
    frame = frame[frame.index <= fund["so"].dropna().index.max()].copy()
    # Yahoo prices are split adjusted, while fund files record what was published that day.
    # Put NAV and shares on the same footing as Yahoo for any split in the sample.
    for stamp, factor in splits.items():
        early = frame.index < stamp
        ratio = (frame["close"][early].tail(40) / frame["nav"][early].tail(40)).median()
        if abs(ratio - 1.0) > 0.05:  # NAV is on the old basis
            frame.loc[early, "nav"] /= factor
            frame.loc[early, "so"] *= factor
    frame["nav"] = frame["nav"].ffill(limit=3)
    frame["so"] = frame["so"].ffill(limit=3)
    div = issuer_div.reindex(frame.index) if len(issuer_div) else pd.Series(np.nan, index=frame.index)
    if div.notna().sum() < 5:
        div = dividends.reindex(frame.index)
        facts["dividend_source"] = "yahoo"
    else:
        facts["dividend_source"] = "issuer"
    frame["div"] = div.fillna(0.0)
    # Total-return NAV. The same factor adjusts high, low and close for P5.
    frame["ret_nav"] = (frame["nav"] + frame["div"]) / frame["nav"].shift(1) - 1.0
    frame["trn"] = (1.0 + frame["ret_nav"].fillna(0.0)).cumprod()
    factor = frame["adjclose"] / frame["close"]
    frame["trc"] = frame["adjclose"]
    frame["trh"], frame["trl"] = frame["high"] * factor, frame["low"] * factor
    frame["premium"] = frame["close"] / frame["nav"] - 1.0
    frame["flow"] = frame["so"].diff()
    frame["flow_pct"] = np.log(frame["so"]).diff()
    frame["turnover"] = (frame["volume"] / frame["so"]).clip(upper=1.0)
    # Hedge. Duration is a stated number held fixed. See plan.md rule 6.
    duration = pd.Series(DEFAULT_DURATION.get(ticker, np.nan), index=frame.index, dtype=float)
    # JNK has no holdings feed here. Its index is close to HYG's, so it borrows HYG's duration path. Flagged in the report.
    points = duration_points("HYG" if ticker == "JNK" else ticker)
    if points:
        known = pd.Series(points).sort_index()
        known.index = pd.to_datetime(known.index)
        step = known.reindex(frame.index.union(known.index)).ffill().bfill().reindex(frame.index)
        duration = step
    facts["duration_points"] = {str(k): v for k, v in points.items()}
    hedge = matched_hedge(duration, curve)
    frame["duration"] = duration
    frame["hedge_ret"] = hedge["ret"]
    frame["hedge_y"] = hedge["yield"]
    frame["hedge_m"] = hedge["maturity"]
    frame["hedge_idx"] = (1.0 + frame["hedge_ret"].fillna(0.0)).cumprod()
    frame["ret_close"] = frame["trc"].pct_change()
    frame["xr_close"] = frame["ret_close"] - frame["hedge_ret"]
    frame["xr_nav"] = frame["ret_nav"] - frame["hedge_ret"]
    carry = CARRY.get(GROUP.get(ticker, "IG"), 1.3) / 100.0
    # Implied spread change in bp. Hedged funds carry no duration, so this stays undefined for them.
    use = duration.where(duration >= 1.0)
    elapsed = pd.Series(frame.index, index=frame.index).diff().dt.days
    frame["ds_impl"] = -(frame["xr_nav"] - carry * elapsed / 365.0) / use * 1e4
    frame["s_impl"] = frame["ds_impl"].fillna(0.0).cumsum()
    trailing = frame["div"].rolling(252, min_periods=120).sum()
    frame["dist_spread"] = (trailing / frame["nav"] - frame["hedge_y"]) * 1e4
    # Spread level: holdings yield to worst minus the matched Treasury at each holdings date, rolled forward
    # by the implied spread change. With no holdings file, the distribution yield spread stands in.
    frame["level"] = frame["dist_spread"]
    anchors = ytw_points("HYG" if ticker == "JNK" else ticker)
    if anchors:
        anchor = pd.Series(anchors).sort_index()
        anchor.index = pd.to_datetime(anchor.index)
        anchor = anchor[anchor.index.isin(frame.index) | (anchor.index >= frame.index[0])]
        spread = {}
        for stamp, ytw in anchor.items():
            row = frame.index.searchsorted(stamp, side="right") - 1
            if row < 0:
                continue
            spread[frame.index[row]] = ytw * 100.0 - frame["hedge_y"].iloc[row] * 1e4 - frame["s_impl"].iloc[row]
        offset = pd.Series(spread).reindex(frame.index).ffill()
        frame["level"] = (offset + frame["s_impl"]).where(offset.notna(), frame["dist_spread"])
        facts["level_source"] = "holdings yield to worst"
        facts["ytw_points"] = {k: v for k, v in anchors.items()}
    else:
        facts["level_source"] = "distribution yield"
    return frame, facts


def duration_points(ticker: str) -> dict:
    """Effective duration read from every saved copy of a fund file, by snapshot date."""
    log_path = RAW / "ishares" / "duration_points.json"
    if not log_path.exists():
        return {}
    table = json.loads(log_path.read_text()).get(ticker, {})
    return {row["date"]: float(row["duration"]) for row in table.values() if row and row.get("duration")}


def ytw_points(ticker: str) -> dict:
    log_path = RAW / "ishares" / "duration_points.json"
    if not log_path.exists():
        return {}
    table = json.loads(log_path.read_text()).get(ticker, {})
    return {row["date"]: float(row["ytw"]) for row in table.values() if row and row.get("ytw") is not None and row.get("duration")}


def choose_offset(frame: pd.DataFrame) -> dict:
    """M1: which day's premium does a share change respond to? Development data only."""
    dev = frame[frame.index <= DEV_END]
    table = {}
    for lag in range(-1, 4):
        table[lag] = float(dev["flow_pct"].corr(dev["premium"].shift(lag)))
    candidates = {lag: table[lag] for lag in (0, 1, 2)}
    best = max(candidates, key=lambda key: candidates[key] if candidates[key] == candidates[key] else -9)
    return {"corr_flow_vs_premium_by_lag": table, "offset": int(best)}


def ledger_readings(changes: np.ndarray, entries: np.ndarray, levels: np.ndarray, rows: np.ndarray, window: int,
                    rule: RemovalRule = RemovalRule.PRO_RATA) -> pd.DataFrame:
    """One ledger per as-of row, rebuilt from empty over the last `window` daily changes."""
    out = []
    for end in rows:
        start = end - window + 1
        if start < 1:
            out.append((np.nan, np.nan, np.nan, np.nan, np.nan))
            continue
        book = build_ledger(changes[start:end + 1], entries[start:end + 1], rule)
        level = levels[end]
        total = book.open_total
        # Pro-rata removal can drain a window to rounding noise. The spec says an empty ledger gives no reading.
        if total <= 1e-6 * max(book.gross_total, 1.0) or not np.isfinite(level):
            out.append((np.nan, np.nan, np.nan, 0.0, book.unmatched))
            continue
        held = [lot for lot in book.lots if lot.entry >= level and lot.open > 0]
        pain = sum(lot.open for lot in held) / total
        mean_cost = sum(lot.open * lot.entry for lot in book.lots) / total
        depth = (sum(lot.open * (lot.entry / level - 1.0) for lot in held) / sum(lot.open for lot in held)
                 if held else 0.0)
        out.append((pain, mean_cost / level - 1.0, depth, total, book.unmatched))
    return pd.DataFrame(out, columns=["pain", "gap", "depth", "open", "unmatched"])


def full_ledger_gap(so: np.ndarray, entries: np.ndarray, levels: np.ndarray) -> np.ndarray:
    """Since-inception ledger with pro-rata removal. Pro-rata removal leaves mean cost unchanged."""
    gap = np.full(len(so), np.nan)
    start = np.flatnonzero(np.isfinite(so) & np.isfinite(entries))
    if not len(start):
        return gap
    first = start[0]
    held, cost = so[first], entries[first]
    for i in range(first + 1, len(so)):
        if np.isfinite(so[i]) and np.isfinite(so[i - 1]):
            change = so[i] - so[i - 1]
            if change > 0 and np.isfinite(entries[i]):
                cost = (held * cost + change * entries[i]) / (held + change)
            held = so[i]
        if np.isfinite(levels[i]):
            gap[i] = cost / levels[i] - 1.0
    return gap


def turnover_reference(turnover: np.ndarray, price: np.ndarray) -> np.ndarray:
    """Grinblatt-Han style reference price. Each day's volume resets that share of the cost basis."""
    reference = np.full(len(price), np.nan)
    current = np.nan
    for i, (v, p) in enumerate(zip(turnover, price)):
        if not np.isfinite(p):
            reference[i] = current
            continue
        if not np.isfinite(current):
            current = p
        elif np.isfinite(v):
            current = v * p + (1.0 - v) * current
        reference[i] = current
    return reference


def weekly_panel(frame: pd.DataFrame, ticker: str, offset: int) -> pd.DataFrame:
    days = frame.index
    locator = pd.Series(np.arange(len(days)), index=days)
    weeks = pd.Series(days, index=days).groupby(days.to_period("W-FRI")).last().values
    weeks = pd.DatetimeIndex(weeks)
    weeks = weeks[locator.loc[weeks].values >= 1]
    cut = locator.loc[weeks].values - 1  # the last row a signal on W may use
    week = pd.DataFrame(index=weeks)
    week["input_date"] = days[cut]

    flow = frame["flow"].values
    entry = frame["trn"].shift(offset).values
    level = frame["trn"].values
    readings = ledger_readings(flow, entry, level, cut, 126)
    readings.index = weeks
    week["pain126"], week["gap126"], week["depth126"] = readings["pain"], readings["gap"], readings["depth"]
    week["unmatched126"] = readings["unmatched"]
    week["open126_share"] = readings["open"].values / frame["so"].values[cut]
    for name, rule in (("fifo", RemovalRule.FIFO), ("low", RemovalRule.LOW_PRICE_FIRST)):
        alt = ledger_readings(flow, entry, level, cut, 126, rule)
        week[f"pain126_{name}"] = alt["pain"].values
    close_entry = frame["trc"].shift(offset).values
    week["pain126_close"] = ledger_readings(flow, close_entry, frame["trc"].values, cut, 126)["pain"].values
    raw_nav = frame["nav"].values
    week["pain126_raw"] = ledger_readings(flow, frame["nav"].shift(offset).values, raw_nav, cut, 126)["pain"].values
    week["pain126_k0"] = ledger_readings(flow, frame["trn"].values, level, cut, 126)["pain"].values

    gap_full = full_ledger_gap(frame["so"].values, entry, level)
    week["gap_full"] = gap_full[cut]
    reference = turnover_reference(frame["turnover"].values, frame["trc"].values)
    week["gap_turn"] = reference[cut] / frame["trc"].values[cut] - 1.0

    # P1, unchanged. Close and entry are total-return NAV. Share count is moved to its order date.
    aligned = frame["so"].shift(-offset).ffill()
    p1 = []
    for row in cut:
        stamp = days[row]
        if row < 31 or not np.isfinite(frame["trn"].iloc[row]) or not np.isfinite(aligned.iloc[row]):
            p1.append((np.nan, np.nan, np.nan, np.nan))
            continue
        tail = slice(max(0, row - 60), row + 1)
        reading = ms_pain_monitor(frame["trn"].iloc[tail], frame["trn"].iloc[tail], aligned.iloc[tail], 1.0, window=30)
        p1.append((reading["long_offside_pct_oi"], reading["short_offside_pct_oi"], reading["long_offside_pct_new"],
                   reading["short_offside_pct_new"]))
        assert reading["as_of"] == stamp
    p1 = pd.DataFrame(p1, index=weeks, columns=["p1_long_oi", "p1_short_oi", "p1_long_new", "p1_short_new"])
    week = week.join(p1)

    # P5, unchanged. Typical price and volume on total-return prices.
    book = pd.DataFrame({"high": frame["trh"], "low": frame["trl"], "close": frame["trc"],
                         "open_interest": frame["so"], "volume": frame["volume"]})
    water = workbook_over_under(book)
    sign = np.where(water["side"] == "Long", 1.0, -1.0)
    water_pct = -(sign * water["over_under"] / water["vwap"]) * 100.0  # higher means more under water
    week["p5_water"] = water_pct.values[cut]
    week["p5_underwater"] = water["underwater"].astype(float).values[cut]

    # Position series as of the input row.
    so = pd.Series(frame["so"].values[cut], index=weeks)
    nav = pd.Series(frame["nav"].values[cut], index=weeks)
    duration = pd.Series(frame["duration"].values[cut], index=weeks)
    week["so"], week["nav"], week["duration"] = so, nav, duration
    logso = np.log(so)
    week["flow4"] = logso.diff(4) * 100.0
    week["flow13"] = logso.diff(13) * 100.0
    week["flow26"] = logso.diff(26) * 100.0
    week["i2_so"] = sentiment_index(logso, 156)
    week["i3_flow"] = db_scaled(week["flow26"], 209)
    cs01 = so.diff() * nav * duration / 1e4 / 1e6  # $mm per bp
    week["cs01_flow"] = cs01
    week["cs01_flow13"] = cs01.rolling(13, min_periods=13).sum()

    # I5, unchanged code. Market move is the implied spread, from NAV. Both variants are scored by posmon.
    spread = pd.Series(frame["s_impl"].values[cut], index=weeks)
    week["s_impl"] = spread
    week["past26"] = spread.diff(26)
    has_duration = duration.notna().all() and duration.min() >= 1.0
    filt_start = max(pd.Timestamp(FIT_START), weeks[0])
    enough = (weeks <= pd.Timestamp(FIT_END)).sum() - (weeks < filt_start).sum()
    if has_duration and enough >= 104:
        spreads = pd.DataFrame({ticker: spread})
        filtered = filtered_change({ticker: so}, spreads, {ticker: nav * duration / 1e4})
        i5 = filtered_residual(spread, filtered, fit_start=str(filt_start.date()), fit_end=FIT_END)
        week["filtered_usd"], week["i5_usd"], week["i5_usd_signal"] = filtered, i5["score"], i5["signal"]
        week["i5_usd_slope"], week["i5_usd_scale"] = i5["slope"], i5["scale"]
        filtered_pct = filtered_change({ticker: logso * 1e6}, spreads, {ticker: duration})
        i5b = filtered_residual(spread, filtered_pct, fit_start=str(filt_start.date()), fit_end=FIT_END)
        week["filtered_pct"], week["i5_pct"], week["i5_pct_signal"] = filtered_pct, i5b["score"], i5b["signal"]
        week["i5_pct_slope"], week["i5_pct_scale"] = i5b["slope"], i5b["scale"]

    # I7, unchanged code. Weekly creations and redemptions.
    positive = frame["flow"].clip(lower=0.0).fillna(0.0).cumsum().values
    negative = (-frame["flow"]).clip(lower=0.0).fillna(0.0).cumsum().values
    creations = pd.Series(positive[cut], index=weeks).diff()
    redemptions = pd.Series(negative[cut], index=weeks).diff()
    week["i7_cont"] = cftc_continuation(creations, redemptions, 4)
    lagged_returns = frame["ret_close"].shift(1)
    week["i7_rev"] = cftc_reversal(so, lagged_returns)

    # I8 trend signal, and plain momentum.
    week["i8_trend"] = cta_signal(frame["trc"]).shift(1).reindex(weeks)
    xr_index = (1.0 + frame["xr_close"].fillna(0.0)).cumprod()
    week["mom26"] = np.log(pd.Series(xr_index.values[cut], index=weeks)).diff(26) * 1e4
    week["level"] = frame["level"].values[cut]

    # Forward targets start at the close of W.
    trc = frame["trc"].reindex(weeks)
    hedge = frame["hedge_idx"].reindex(weeks)
    carry = CARRY.get(GROUP.get(ticker, "IG"), 1.3) / 100.0
    for horizon in (1, 4, 13, 26):
        total = trc.shift(-horizon) / trc - 1.0
        hedged = hedge.shift(-horizon) / hedge - 1.0
        week[f"xr{horizon}"] = (total - hedged) * 1e4
        week[f"tr{horizon}"] = total * 1e4
        if has_duration:
            week[f"ds{horizon}"] = -((total - hedged) - carry * horizon / 52.0) / duration * 1e4
        fwd = logso.shift(-horizon) - logso
        week[f"fwdflow{horizon}"] = fwd * 100.0
    week["sigma26"] = frame["xr_close"].rolling(126, min_periods=100).std().values[cut] * np.sqrt(5) * 1e4
    return week


def add_short_interest(week: pd.DataFrame, frame: pd.DataFrame, ticker: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """FINRA short interest, usable from settlement + 10 business days."""
    path = RAW / "finra" / f"{ticker}.json"
    empty = pd.DataFrame()
    if not path.exists():
        return week, empty
    si = load_finra(ticker)
    si = si[si["si"] > 0]
    si["so"] = frame["so"].reindex(frame.index.union(si.index)).ffill().reindex(si.index)
    si = si.dropna(subset=["so"])
    if si.empty:
        return week, empty
    si["ratio"] = si["si"] / (si["so"] + si["si"])
    si["usable"] = si.index + pd.offsets.BDay(SI_LAG_DAYS)
    frame_cut = pd.merge_asof(pd.DataFrame({"input_date": week["input_date"].values}, index=week.index).reset_index(),
                              si.reset_index()[["usable", "ratio", "si", "settle"]].sort_values("usable"),
                              left_on="input_date", right_on="usable", direction="backward").set_index("index")
    week["si_ratio"] = frame_cut["ratio"]
    week["si_settle"] = frame_cut["settle"]
    week["si_chg"] = week["si_ratio"].diff(13) * 100.0
    week["si_i2"] = sentiment_index(week["si_ratio"], 156)
    week["i1_net_pct"] = 100.0 * (1.0 - week["si_ratio"])
    return week, si


def p1_vs_short_interest(frame: pd.DataFrame, si: pd.DataFrame, offset: int) -> dict:
    """C5: does P1's short attribution match the true change in short interest over each FINRA interval?"""
    if si.empty:
        return {}
    aligned = frame["so"].shift(-offset).ffill()
    classified = classify_changes(frame["trn"], aligned)
    keys = si.index
    position = np.searchsorted(frame.index, keys, side="right") - 1
    rows = []
    for a, b, key_a, key_b in zip(position[:-1], position[1:], keys[:-1], keys[1:]):
        if a < 0 or b <= a:
            continue
        part = classified.iloc[a + 1:b + 1]
        rows.append({"settle": key_b, "true_ds": si.loc[key_b, "si"] - si.loc[key_a, "si"],
                     "p1_ds": part["short_change"].sum(), "p1_dl": part["long_change"].sum(),
                     "true_dl": (si.loc[key_b, "si"] + si.loc[key_b, "so"]) - (si.loc[key_a, "si"] + si.loc[key_a, "so"]),
                     "new_short_days": int((part["case"] == "new_short").sum()), "days": len(part)})
    table = pd.DataFrame(rows).set_index("settle")
    moved = table[table["p1_ds"] != 0]
    true_dso = table["true_dl"] - table["true_ds"]
    return {"intervals": int(len(table)),
            "spearman_true_dsi_vs_dso": float(table["true_ds"].corr(true_dso, method="spearman")),
            "share_si_up_when_so_down": float((table["true_ds"][true_dso < 0] > 0).mean()),
            "share_si_up_when_so_up": float((table["true_ds"][true_dso > 0] > 0).mean()),
            "spearman_short": float(table["p1_ds"].corr(table["true_ds"], method="spearman")),
            "spearman_short_nonzero": float(moved["p1_ds"].corr(moved["true_ds"], method="spearman")),
            "sign_agree_short": float((np.sign(moved["p1_ds"]) == np.sign(moved["true_ds"])).mean()),
            "base_rate_true_short_rises": float((table["true_ds"] > 0).mean()),
            "spearman_long": float(table["p1_dl"].corr(table["true_dl"], method="spearman")),
            "sign_agree_long": float((np.sign(table["p1_dl"]) == np.sign(table["true_dl"])).mean()),
            "size_ratio_abs_p1_to_true": float(table["p1_ds"].abs().sum() / table["true_ds"].abs().sum())}


def main() -> None:
    WORK.mkdir(exist_ok=True)
    curve = treasury_curve()
    facts: dict = {}
    for ticker in ISHARES + SSGA:
        have = (RAW / "ishares" / f"{ticker}.json").exists() or (RAW / "ssga" / f"{ticker}.xlsx").exists()
        if not have or not (RAW / "yahoo" / f"{ticker}.json").exists():
            facts[ticker] = {"status": "missing"}
            print(ticker, "missing", flush=True)
            continue
        frame, info = daily_panel(ticker, curve)
        timing = choose_offset(frame)
        week = weekly_panel(frame, ticker, timing["offset"])
        week, si = add_short_interest(week, frame, ticker)
        info["timing"] = timing
        info["p1_vs_short_interest"] = p1_vs_short_interest(frame, si, timing["offset"])
        info["status"] = "ok"
        info["first_week"], info["last_week"] = str(week.index[0].date()), str(week.index[-1].date())
        frame.to_pickle(WORK / f"daily_{ticker}.pkl")
        week.to_pickle(WORK / f"weekly_{ticker}.pkl")
        si.to_pickle(WORK / f"si_{ticker}.pkl")
        facts[ticker] = info
        print(ticker, info["fund_first"], info["fund_last"], "offset", timing["offset"], "rows", len(frame), flush=True)
    (WORK / "panel_facts.json").write_text(json.dumps(facts, indent=1, default=str))


if __name__ == "__main__":
    main()
