"""The Pain methods: P1 Morgan Stanley, P2 CFTC corrected, P3 legacy port, P4 activity, P5 workbook."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .data import publish_time
from .ledger import Ledger, RemovalRule, build_ledger

# ---------------------------------------------------------------------------
# Prices
# ---------------------------------------------------------------------------


def typical_price(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Average of high, low and close. Missing inputs are skipped, as Excel AVERAGE does."""
    return pd.concat([high, low, close], axis=1).mean(axis=1, skipna=True)


def vwap_from_bars(bars: pd.DataFrame) -> pd.Series:
    """Daily VWAP from intraday bars with columns date, price and volume."""
    value = (bars["price"] * bars["volume"]).groupby(bars["date"]).sum()
    return value / bars["volume"].groupby(bars["date"]).sum()


def back_adjust(front: pd.Series, gaps: pd.Series) -> pd.Series:
    """Difference back-adjustment.

    gaps holds (new contract - old contract) at each roll close, indexed by the roll date.
    Prices strictly before a roll date move by that gap. The latest price never moves.
    """
    adjusted = front.astype(float).copy()
    for roll_date, gap in gaps.items():
        adjusted.loc[adjusted.index < roll_date] += gap
    return adjusted


# ---------------------------------------------------------------------------
# P1: Morgan Stanley Pain Trade Monitor
# ---------------------------------------------------------------------------


def classify_changes(close: pd.Series, open_interest: pd.Series) -> pd.DataFrame:
    """Turn price and open-interest changes into signed long and short changes."""
    price_change = close.diff()
    oi_change = open_interest.diff()
    up, down = price_change > 0, price_change < 0
    rise, fall = oi_change > 0, oi_change < 0
    frame = pd.DataFrame({"price_change": price_change, "oi_change": oi_change}, index=close.index)
    frame["long_change"] = 0.0
    frame["short_change"] = 0.0
    frame.loc[up & rise, "long_change"] = oi_change[up & rise]  # new longs
    frame.loc[down & fall, "long_change"] = oi_change[down & fall]  # longs taken off
    frame.loc[down & rise, "short_change"] = oi_change[down & rise]  # new shorts
    frame.loc[up & fall, "short_change"] = oi_change[up & fall]  # shorts covered
    frame["case"] = "none"
    frame.loc[up & rise, "case"] = "new_long"
    frame.loc[down & fall, "case"] = "long_off"
    frame.loc[down & rise, "case"] = "new_short"
    frame.loc[up & fall, "case"] = "short_cover"
    frame.loc[price_change.isna() | oi_change.isna(), "case"] = "first_row"
    return frame


def ms_pain_monitor(
    close: pd.Series,
    vwap: pd.Series,
    open_interest: pd.Series,
    multiplier: float,
    fx_to_usd: float = 1.0,
    window: int = 30,
    rule: RemovalRule = RemovalRule.PRO_RATA,
    as_of=None,
) -> dict:
    """Compute one as-of reading of the Morgan Stanley monitor.

    The window holds `window` daily changes, so it needs window + 1 rows of levels.
    A long lot is offside when its entry is above the as-of close.
    A short lot is offside when its entry is below the as-of close.
    """
    as_of = close.index[-1] if as_of is None else as_of
    classified = classify_changes(close.loc[:as_of], open_interest.loc[:as_of])
    if len(classified) < window + 1:
        raise ValueError(f"need {window + 1} rows, got {len(classified)}")
    tail = classified.iloc[-window:]
    entries = vwap.reindex(tail.index)
    long_book = build_ledger(tail["long_change"].values, entries.values, rule, tail.index)
    short_book = build_ledger(tail["short_change"].values, entries.values, rule, tail.index)
    level = float(close.loc[as_of])
    oi_now = float(open_interest.loc[as_of])

    def notional(lots) -> float:
        return sum(lot.open * lot.entry * multiplier * fx_to_usd for lot in lots)

    long_off = [lot for lot in long_book.lots if lot.entry > level]
    short_off = [lot for lot in short_book.lots if lot.entry < level]
    long_off_qty = sum(lot.open for lot in long_off)
    short_off_qty = sum(lot.open for lot in short_off)
    return {
        "as_of": as_of,
        "close": level,
        "open_interest": oi_now,
        "long_open": long_book.open_total,
        "short_open": short_book.open_total,
        "long_offside": long_off_qty,
        "short_offside": short_off_qty,
        "long_offside_pct_new": _ratio(long_off_qty, long_book.open_total),
        "short_offside_pct_new": _ratio(short_off_qty, short_book.open_total),
        "long_offside_pct_oi": long_off_qty / oi_now,
        "short_offside_pct_oi": short_off_qty / oi_now,
        "long_offside_usd": notional(long_off),
        "short_offside_usd": notional(short_off),
        "long_unmatched": long_book.unmatched,
        "short_unmatched": short_book.unmatched,
        "long_book": long_book,
        "short_book": short_book,
    }


def rank_monitor(readings: dict, side: str = "long") -> pd.DataFrame:
    """Rank contracts by the offside share of total open interest. Larger comes first."""
    column = f"{side}_offside_pct_oi"
    rows = [{"contract": name, column: value[column], f"{side}_offside_usd": value[f"{side}_offside_usd"]}
            for name, value in readings.items()]
    return pd.DataFrame(rows).sort_values(column, ascending=False).reset_index(drop=True)


def _ratio(top: float, bottom: float, floor: float = 1e-6) -> float:
    """A full removal can leave floating-point residue near 1e-14 contracts. Treat that as an empty ledger."""
    return top / bottom if bottom > floor else float("nan")


# ---------------------------------------------------------------------------
# P2: PortfolioStrat method, corrected
# ---------------------------------------------------------------------------


def harmonise_weekly(position: pd.Series, trading_days: pd.DatetimeIndex) -> pd.Series:
    """Spread a weekly CFTC field onto trading days. A change lands on its report date.

    A report date that is not a trading day moves to the next trading day.
    """
    union = trading_days.union(position.index)
    return position.reindex(union).ffill().reindex(trading_days)


def cftc_pain(
    position: pd.Series,
    close: pd.Series,
    window: int = 126,
    rule: RemovalRule = RemovalRule.PRO_RATA,
    side: str = "long",
    respect_release: bool = True,
) -> pd.DataFrame:
    """Roll the ledger over one CFTC field and return one row per as-of date.

    With respect_release, an as-of date sees only reports released on or before it.
    Set it to False only to reconcile with old output, which used reports from their report date.

    share_in_pain: open contracts entered at or beyond the close, as a share of all open contracts.
    For a long field, beyond means at or above. For a short field, it means at or below.
    pct_open_code: the same price test, but open divided by gross. This is what PCT_OPEN returns.
    """
    daily = harmonise_weekly(position, close.index)
    frame = pd.DataFrame({"close": close, "change": daily.diff()}).dropna()
    released = pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns]")
    for report_date in position.index:
        spot = frame.index.searchsorted(report_date)
        if spot < len(frame.index):
            released.iloc[spot] = publish_time(report_date).tz_localize(None).normalize()
    rows = []
    for end in range(window, len(frame) + 1):
        part = frame.iloc[end - window:end]
        changes = part["change"]
        if respect_release:
            changes = changes.where(~(released.iloc[end - window:end] > part.index[-1]), 0.0)
        book = build_ledger(changes.values, part["close"].values, rule, part.index)
        level = float(part["close"].iloc[-1])
        rows.append({"date": part.index[-1], "close": level, "open": book.open_total,
                     "gross": book.gross_total, "unmatched": book.unmatched,
                     "share_in_pain": _share_in_pain(book, level, side),
                     "pct_open_code": _survival_share(book, level, side)})
    return pd.DataFrame(rows).set_index("date")


def _share_in_pain(book: Ledger, level: float, side: str) -> float:
    held = book.open_above(level) if side == "long" else book.open_below(level)
    return _ratio(held, book.open_total)


def _survival_share(book: Ledger, level: float, side: str) -> float:
    if side == "long":
        lots = [lot for lot in book.lots if lot.entry >= level]
    else:
        lots = [lot for lot in book.lots if lot.entry <= level]
    gross = sum(lot.gross for lot in lots)
    return sum(lot.open for lot in lots) / gross if gross else 0.0


def threshold_position(signal: pd.Series, sell_above: float = 0.70, buy_below: float = 0.30) -> pd.Series:
    """Deck rule for NG. Sell above 70 percent. Buy below 30 percent. Hold the last signal between."""
    position = pd.Series(np.nan, index=signal.index)
    position[signal > sell_above] = -1.0
    position[signal < buy_below] = 1.0
    return position.ffill().fillna(0.0)


# ---------------------------------------------------------------------------
# P3: exact port of the legacy function, defects included
# ---------------------------------------------------------------------------


def legacy_position_per_strike(position_changes, prices) -> dict:
    """Port of _calculate_position_per_strike (functions.py lines 1015 to 1050). Do not fix it."""
    net_position = 0
    bucket_count = 10
    min_price = min(prices)
    max_price = max(prices)
    bucket_width = (max_price - min_price) / float(bucket_count)
    positions = [{"price": min_price + float(i) * bucket_width, "gross": 0, "liquidated": 0}
                 for i in range(bucket_count)]
    for px, ch in zip(prices, position_changes):
        which_bucket = int(math.floor((px - min_price) / bucket_width))
        if px == max_price:
            which_bucket -= 1
        if ch > 0:
            net_position += ch
            positions[which_bucket]["gross"] += ch
        elif ch < 0 < net_position:
            for p in positions:
                to_liquidate = 0
                if p["gross"] > p["liquidated"] and net_position > 0:
                    potential = p["gross"] - p["liquidated"]
                    to_liquidate = min(potential / net_position * ch * -1, potential)
                    p["liquidated"] += to_liquidate
                net_position = max(0, net_position - to_liquidate)
    positions.sort(key=lambda x: x["price"])
    return {"prices": [x["price"] for x in positions],
            "open": [x["gross"] - x["liquidated"] for x in positions],
            "gross": [x["gross"] for x in positions],
            "closed": [x["liquidated"] for x in positions]}


def legacy_cftc_open_position(field: str, prices: pd.Series, positions: pd.Series, level,
                              condition: str = "==", window: int = 30) -> pd.Series:
    """Port of f_cftc_open_position (functions.py lines 961 to 1011). Do not fix it."""
    field = str(field).strip().upper()
    if field not in ("OPEN", "GROSS", "CLOSED", "PCT_OPEN"):
        raise ValueError(field)
    if condition not in ("==", ">=", "<="):
        raise ValueError(condition)
    levels = level if isinstance(level, pd.Series) else pd.Series(float(level), index=prices.index)
    frame = pd.DataFrame({"prices": prices, "position_changes": positions - positions.shift(1),
                          "levels": levels}).dropna()

    def one(part: pd.DataFrame) -> float:
        book = legacy_position_per_strike(part["position_changes"].values, part["prices"].values)
        last = part["levels"].iloc[-1]
        zipped_open = list(zip(book["prices"], book["open"]))
        zipped_gross = list(zip(book["prices"], book["gross"]))
        if condition == "==":
            if field == "PCT_OPEN":
                remaining = np.interp(last, book["prices"], book["open"])
                gross = np.interp(last, book["prices"], book["gross"])
                return remaining / gross if gross else 0.0
            return float(np.interp(last, book["prices"], book[field.lower()]))
        if condition == ">=":
            if field == "PCT_OPEN":
                remaining = sum(z[1] if z[0] >= last else 0.0 for z in zipped_open)
                gross = sum(z[1] if z[0] >= last else 0.0 for z in zipped_gross)
                return float(remaining) / float(gross) if gross else 0.0
            return float(sum(x if x >= last else 0.0 for x in book[field.lower()]))  # compares size to price
        if field == "PCT_OPEN":
            remaining = sum(z[1] if z[0] <= last else 0.0 for z in zipped_open)
            gross = sum(z[1] if z[0] <= last else 0.0 for z in zipped_gross)
            return float(remaining) / float(gross) if gross else 0.0
        return float(sum(x if x <= last else 0.0 for x in book[field.lower()]))  # compares size to price

    results = [one(frame.iloc[i:i + window]) for i in range(len(frame) - window + 1)]
    return pd.Series(results, index=frame.index[window - 1:])


def legacy_ladder(position_changes, prices, current_price, ratios) -> pd.DataFrame:
    """Rebuild the deck ladder chart with the legacy OPEN >= path and with a correct price test."""
    book = legacy_position_per_strike(position_changes, prices)
    rows = []
    for ratio in ratios:
        level = ratio * current_price
        wrong = sum(x if x >= level else 0.0 for x in book["open"])
        right = sum(o for p, o in zip(book["prices"], book["open"]) if p >= level)
        rows.append({"ratio": ratio, "level": level, "legacy_open": wrong, "correct_open": right})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# P4: activity by trade price (the email exchange of June 2015)
# ---------------------------------------------------------------------------


def activity_by_price(price, longs, shorts) -> pd.DataFrame:
    """Place every change at the price of the day it happened. Entry and exit are not matched."""
    frame = pd.DataFrame({"price": price, "long_chg": pd.Series(longs).diff(),
                          "short_chg": pd.Series(shorts).diff()}).dropna()
    out = pd.DataFrame({
        "price": frame["price"],
        "longs_added": frame["long_chg"].clip(lower=0),
        "longs_off": (-frame["long_chg"]).clip(lower=0),
        "shorts_added": frame["short_chg"].clip(lower=0),
        "shorts_off": (-frame["short_chg"]).clip(lower=0),
    }).groupby("price").sum()
    out["buys"] = out["longs_added"] + out["shorts_off"]
    out["sells"] = out["shorts_added"] + out["longs_off"]
    out["longs_net"] = out["longs_added"] - out["longs_off"]
    out["shorts_net"] = out["shorts_added"] - out["shorts_off"]
    return out


# ---------------------------------------------------------------------------
# P5: the 2018 workbook sheet
# ---------------------------------------------------------------------------


def workbook_over_under(daily: pd.DataFrame, vwap_rows: int = 30, net_rows: int = 29) -> pd.DataFrame:
    """Rebuild columns G to P of the "Pain Monitor" sheet.

    The sheet calls M a VWAP. It is a rolling volume-weighted mean of typical price.
    A missing volume counts as zero, as SUMPRODUCT and SUM treat text.
    """
    out = pd.DataFrame(index=daily.index)
    out["typical"] = typical_price(daily["high"], daily["low"], daily["close"])
    out["price_change"] = out["typical"].diff()
    out["oi_change"] = daily["open_interest"].diff()
    volume = daily["volume"].fillna(0.0)
    out["oi_pct_volume"] = out["oi_change"] / daily["volume"]
    value = (volume * out["typical"]).rolling(vwap_rows, min_periods=1).sum()
    out["vwap"] = value / volume.rolling(vwap_rows, min_periods=1).sum()
    out.loc[out.index[0], "vwap"] = np.nan  # the sheet starts this column on its second row
    out["net_new"] = out["oi_change"].rolling(net_rows, min_periods=1).sum()
    out["side"] = np.where(out["net_new"] > 0, "Long", "Short")
    out.loc[out.index[0], "side"] = None
    out["over_under"] = out["typical"] - out["vwap"]
    out["underwater"] = ((out["side"] == "Long") & (out["over_under"] < 0)) | (
        (out["side"] == "Short") & (out["over_under"] > 0))
    return out
