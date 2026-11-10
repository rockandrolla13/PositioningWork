"""Acceptance tests for the Pain methods. Every expected number has a stated origin."""
import math
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from posmon.ledger import RemovalRule, build_ledger, bucket_lots
from posmon.pain import (activity_by_price, classify_changes, cftc_pain, harmonise_weekly, legacy_cftc_open_position,
                         legacy_ladder, legacy_position_per_strike, ms_pain_monitor, rank_monitor, threshold_position,
                         typical_price, workbook_over_under, back_adjust)

DATA = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def daily():
    if not (DATA / "ty_daily.csv").exists():
        pytest.skip("ty_daily.csv is restricted data and is not in the public repo")
    return pd.read_csv(DATA / "ty_daily.csv", parse_dates=["date"], index_col="date")


@pytest.fixture(scope="module")
def weekly():
    return pd.read_csv(DATA / "ty_cftc.csv", parse_dates=["date"], index_col="date")


def toy_market():
    close = pd.Series([100, 101, 102, 101.2, 100.5, 101.5, 100.8, 101.3], dtype=float)
    vwap = pd.Series([100, 100.6, 101.6, 101.7, 100.9, 101.0, 101.2, 101.1], dtype=float)
    oi = pd.Series([1000, 1100, 1160, 1210, 1170, 1150, 1190, 1180], dtype=float)
    return close, vwap, oi


# ---- P1 --------------------------------------------------------------------

def test_p1_classification_table():
    close, _, oi = toy_market()
    frame = classify_changes(close, oi)
    assert frame["case"].tolist() == ["first_row", "new_long", "new_long", "new_short", "long_off", "short_cover",
                                      "new_short", "short_cover"]


def test_p1_zero_price_change_is_not_classified():
    frame = classify_changes(pd.Series([100.0, 100.0]), pd.Series([10.0, 20.0]))
    assert frame["case"].iloc[1] == "none" and frame["long_change"].iloc[1] == 0


def test_p1_hand_worked_toy():
    close, vwap, oi = toy_market()
    out = ms_pain_monitor(close, vwap, oi, multiplier=1000.0, window=7)
    assert [round(lot.open, 3) for lot in out["long_book"].lots] == [75.0, 45.0]
    assert [round(lot.open, 3) for lot in out["short_book"].lots] == [25.714, 34.286]
    assert out["long_offside"] == pytest.approx(45.0)
    assert out["short_offside"] == pytest.approx(240.0 / 7.0)
    assert out["long_offside_pct_new"] == pytest.approx(0.375)
    assert out["short_offside_pct_new"] == pytest.approx(4.0 / 7.0)
    assert out["long_offside_pct_oi"] == pytest.approx(45.0 / 1180.0)
    assert out["long_offside_usd"] == pytest.approx(45.0 * 101.6 * 1000.0)


def test_p1_needs_full_window():
    close, vwap, oi = toy_market()
    with pytest.raises(ValueError):
        ms_pain_monitor(close, vwap, oi, multiplier=1.0, window=8)


def test_p1_ty_regression(daily):
    tp = typical_price(daily["high"], daily["low"], daily["close"])
    out = ms_pain_monitor(daily["close"], tp, daily["open_interest"], multiplier=1000.0, window=30)
    assert out["long_open"] == pytest.approx(90152.0)
    assert out["short_open"] == pytest.approx(9996.0)
    assert out["long_offside_pct_new"] == pytest.approx(0.29657, abs=1e-4)
    assert out["short_offside_pct_new"] == pytest.approx(1.0)
    assert out["long_unmatched"] == pytest.approx(49683.0)


def test_p1_ranking():
    table = rank_monitor({"A": {"long_offside_pct_oi": 0.01, "long_offside_usd": 5.0},
                          "B": {"long_offside_pct_oi": 0.03, "long_offside_usd": 1.0}})
    assert table["contract"].tolist() == ["B", "A"]


# ---- Ledger rules ------------------------------------------------------------

@pytest.mark.parametrize("rule", list(RemovalRule))
def test_ledger_removes_exactly_what_was_asked(rule):
    book = build_ledger([20, 20, 20, -30], [100, 105, 110, 102], rule)
    assert book.removed == pytest.approx(30.0)
    assert book.open_total == pytest.approx(30.0)


def test_pro_rata_takes_the_same_share():
    book = build_ledger([20, 20, 20, -30], [100, 105, 110, 102], RemovalRule.PRO_RATA)
    assert [lot.open for lot in book.lots] == pytest.approx([10.0, 10.0, 10.0])


def test_fifo_takes_oldest_first():
    book = build_ledger([20, 20, 20, -30], [110, 100, 105, 102], RemovalRule.FIFO)
    assert [lot.open for lot in book.lots] == pytest.approx([0.0, 10.0, 20.0])


def test_low_price_first():
    book = build_ledger([20, 20, 20, -30], [110, 100, 105, 102], RemovalRule.LOW_PRICE_FIRST)
    assert [lot.open for lot in book.lots] == pytest.approx([20.0, 0.0, 10.0])


def test_excess_reduction_is_recorded():
    book = build_ledger([10, -25], [100, 101], RemovalRule.PRO_RATA)
    assert book.open_total == 0 and book.removed == 10 and book.unmatched == 15


def test_reduction_before_any_lot_is_unmatched():
    book = build_ledger([-5, 10], [100, 101])
    assert book.unmatched == 5 and book.open_total == 10


def test_buckets_put_top_price_in_last_bucket():
    book = build_ledger([1, 1], [100, 110])
    rows = bucket_lots(book, 100, 110)
    assert rows[0][1] == 1 and rows[9][1] == 1


def test_buckets_reject_flat_window():
    with pytest.raises(ValueError):
        bucket_lots(build_ledger([1], [100]), 100, 100)


# ---- P2 ----------------------------------------------------------------------

def test_p2_weekly_change_lands_on_report_date(daily, weekly):
    series = harmonise_weekly(weekly["asset_mgr_long"], daily.index)
    change = series.diff().dropna()
    assert change.loc["2014-08-05"] == pytest.approx(960597 - 960664)
    assert change.loc["2014-08-06"] == 0


def test_p2_release_rule_hides_the_latest_report(daily, weekly):
    # 22 Jan 2015 is a Thursday. The 20 Jan report comes out on 23 Jan, so it must not count.
    live = cftc_pain(weekly["lev_money_long"], daily["close"], window=90, side="long").iloc[-1]
    replay = cftc_pain(weekly["lev_money_long"], daily["close"], window=90, side="long", respect_release=False).iloc[-1]
    assert live["share_in_pain"] == pytest.approx(0.0)
    assert replay["share_in_pain"] == pytest.approx(0.26176, abs=1e-4)
    assert live["gross"] < replay["gross"]


def test_p2_share_definitions_differ():
    days = pd.date_range("2020-01-01", periods=5, freq="B")
    close = pd.Series([100.0, 105.0, 110.0, 102.0, 104.0], index=days)
    position = pd.Series([0.0, 20.0, 40.0, 20.0, 20.0], index=days)
    out = cftc_pain(position, close, window=4, side="long", respect_release=False).iloc[-1]
    # Lots: 20 at 105 and 20 at 110, then a 20 cut leaves 10 and 10. Close is 104.
    assert out["open"] == pytest.approx(20.0)
    assert out["share_in_pain"] == pytest.approx(1.0)
    assert out["pct_open_code"] == pytest.approx(0.5)


def test_p2_ty_regression(daily, weekly):
    out = cftc_pain(weekly["lev_money_long"], daily["close"], window=90, side="long", respect_release=False).iloc[-1]
    assert out["gross"] == pytest.approx(147591.0)
    assert out["open"] == pytest.approx(52912.0)
    assert out["unmatched"] == pytest.approx(73907.0)
    assert out["share_in_pain"] == pytest.approx(0.26176, abs=1e-4)
    assert out["pct_open_code"] == pytest.approx(1.0)


def test_p2_window_can_empty_out(daily, weekly):
    out = cftc_pain(weekly["asset_mgr_long"], daily["close"], window=60, side="long", respect_release=False).iloc[-1]
    assert out["open"] == pytest.approx(0.0)
    assert out["share_in_pain"] != out["share_in_pain"]  # NaN: no open lots, so no reading


def test_threshold_rule_holds_between_bands():
    signal = pd.Series([0.5, 0.8, 0.5, 0.2, 0.5])
    assert threshold_position(signal).tolist() == [0.0, -1.0, -1.0, 1.0, 1.0]


def test_back_adjust_keeps_latest_price():
    days = pd.date_range("2020-01-01", periods=4, freq="B")
    front = pd.Series([100.0, 101.0, 99.0, 100.0], index=days)
    adjusted = back_adjust(front, pd.Series({days[2]: -1.5}))
    assert adjusted.tolist() == [98.5, 99.5, 99.0, 100.0]


# ---- P3 ----------------------------------------------------------------------

def test_p3_over_removal_is_reproduced():
    book = legacy_position_per_strike([20, 20, 20, -30, 0], [100, 105, 110, 102, 100])
    assert sum(book["closed"]) == pytest.approx(37.789, abs=1e-3)
    shares = [c / g for c, g in zip(book["closed"], book["gross"]) if g]
    assert [round(s, 2) for s in shares] == [0.50, 0.60, 0.79]


def test_p3_two_level_case():
    book = legacy_position_per_strike([10, 10, -5, 0], [100, 110, 105, 100])
    assert sum(book["closed"]) == pytest.approx(5.357, abs=1e-3)


def test_p3_quantity_compared_to_price():
    book = legacy_ladder([50, 50], [100, 110], 105.0, [0.4, 2.0])
    assert book["legacy_open"].tolist() == [50.0 * 2, 0.0]  # no bucket holds 210 contracts
    book = legacy_ladder([500, 500], [100, 110], 105.0, [2.0])
    assert book["legacy_open"].iloc[0] == 1000.0  # both buckets pass though no lot sits above 210
    assert book["correct_open"].iloc[0] == 0.0


def test_p3_rolling_function_runs():
    days = pd.date_range("2020-01-01", periods=6, freq="B")
    close = pd.Series([100.0, 105.0, 110.0, 102.0, 100.0, 101.0], index=days)
    position = pd.Series([0.0, 20.0, 40.0, 60.0, 30.0, 30.0], index=days)
    out = legacy_cftc_open_position("PCT_OPEN", close, position, close, ">=", window=5)
    assert len(out) == 1 and 0.0 <= out.iloc[0] <= 1.0


def test_p3_flat_window_raises():
    with pytest.raises((ZeroDivisionError, ValueError)):
        legacy_position_per_strike([1.0, 1.0], [100.0, 100.0])


# ---- P4 ----------------------------------------------------------------------

def test_p4_email_example():
    price = [100.0, 105.0, 110.0, 105.0, 110.0]
    longs = [0.0, 6.0, 6.0, 3.0, 0.0]
    table = activity_by_price(pd.Series(price), pd.Series(longs), pd.Series(longs))
    assert table.loc[105.0, "longs_added"] == 6 and table.loc[105.0, "longs_off"] == 3
    assert table.loc[110.0, "longs_off"] == 3
    assert table.loc[105.0, "buys"] == 9 and table.loc[105.0, "sells"] == 9
    assert table.loc[110.0, "buys"] == 3 and table.loc[110.0, "sells"] == 3


def test_p4_entry_matched_block_of_mary_sheet():
    # Pain Monitor block of the Google Sheet: entry 105, initiated 6, liquidated 6.
    book = build_ledger([6, 0, -3, -3], [105, 110, 105, 110])
    assert len(book.lots) == 1 and book.lots[0].entry == 105
    assert book.removed == 6 and book.open_total == 0


# ---- P5 ----------------------------------------------------------------------

def test_p5_matches_every_cached_cell(daily):
    out = workbook_over_under(daily)
    pairs = {"typical": "wb_typical", "price_change": "wb_price_change", "oi_change": "wb_oi_change",
             "oi_pct_volume": "wb_oi_pct_volume", "vwap": "wb_vwap", "net_new": "wb_net_new",
             "over_under": "wb_over_under"}
    for ours, theirs in pairs.items():
        both = out[ours].notna() & daily[theirs].notna()
        assert both.sum() >= 123
        assert np.abs(out.loc[both, ours] - daily.loc[both, theirs]).max() < 1e-9, ours
    assert (out["side"].iloc[1:] == daily["wb_side"].iloc[1:]).all()


def test_p5_last_row(daily):
    last = workbook_over_under(daily).iloc[-1]
    assert last["vwap"] == pytest.approx(128.69852085176623)
    assert last["net_new"] == 47968
    assert last["over_under"] == pytest.approx(0.2389791482337671)


def test_empty_ledger_residue_gives_no_reading():
    from posmon.pain import _ratio
    assert math.isnan(_ratio(1.0e-15, 2.0e-14))
    assert math.isnan(_ratio(0.0, 0.0))
    assert _ratio(5.0, 10.0) == 0.5
