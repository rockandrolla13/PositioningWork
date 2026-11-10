"""Acceptance tests for the positioning indicators."""
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from posmon import cta, glgarma, indicators as ind
from posmon.data import check_cftc, check_daily, known_at, publish_time
from posmon.stats import newey_west_ols

DATA = Path(__file__).resolve().parents[1] / "data"


def weekly_index(n):
    return pd.date_range("2015-01-06", periods=n, freq="W-TUE")


# ---- I2 ----------------------------------------------------------------------

def test_si_bounds_and_ends():
    net = pd.Series([0.0, 10.0, 5.0, -5.0, 20.0, 7.5], index=weekly_index(6))
    si = ind.sentiment_index(net, 5)
    assert si.iloc[4] == 100.0
    assert si.iloc[3 + 2] == pytest.approx(100.0 * (7.5 + 5.0) / 25.0)
    assert si.dropna().between(0, 100).all()


def test_extreme_counter():
    si = pd.Series([50.0, 95.0, 96.0, 50.0, 5.0, 5.0, 5.0], index=weekly_index(7))
    flags = ind.extreme_flags(si)
    assert flags["counter"].tolist() == [0.0, 1.0, 2.0, 0.0, 1.0, 2.0, 3.0]
    assert flags["d90"].sum() == 2 and flags["d10"].sum() == 3


# ---- I3 ----------------------------------------------------------------------

def test_db_scale_keeps_zero_and_sign():
    net = pd.Series([100.0, -50.0, 25.0, -25.0, 0.0], index=weekly_index(5))
    out = ind.db_scaled(net, 5)
    assert out.iloc[-1] == 0.0
    assert ind.db_scaled(net.iloc[:3], 3).iloc[-1] == pytest.approx(2.5)
    assert ind.db_scaled(net.iloc[:4], 4).iloc[-1] == pytest.approx(-5.0)


# ---- I5 ----------------------------------------------------------------------

def test_filter_keeps_only_moves_with_the_market():
    idx = weekly_index(3)
    nets = {"TY": pd.Series([0.0, -1000.0, -500.0], index=idx)}
    yields = pd.DataFrame({"TY": [200.0, 210.0, 220.0]}, index=idx)
    out = ind.filtered_change(nets, yields, {"TY": 65.0})
    assert out.iloc[1] == pytest.approx(-1000 * 65.0 / 1e6)  # selling as yields rise: kept
    assert out.iloc[2] == 0.0  # buying as yields rise: dropped


def test_filter_accepts_a_weekly_dv01_series():
    idx = weekly_index(3)
    nets = {"TY": pd.Series([0.0, -1000.0, -2000.0], index=idx)}
    yields = pd.DataFrame({"TY": [200.0, 210.0, 220.0]}, index=idx)
    out = ind.filtered_change(nets, yields, {"TY": pd.Series([60.0, 70.0, 80.0], index=idx)})
    assert out.iloc[1] == pytest.approx(-1000 * 70.0 / 1e6)
    assert out.iloc[2] == pytest.approx(-1000 * 80.0 / 1e6)


def test_score_uses_in_sample_weekly_spread_and_no_mean():
    idx = pd.date_range("2010-01-05", periods=120, freq="W-TUE")
    rng = np.random.default_rng(5)
    filtered = pd.Series(rng.normal(0, 3, 120), index=idx)
    level = pd.Series(np.cumsum(rng.normal(0, 8, 120)), index=idx)
    table = ind.filtered_residual(level, filtered, fit_start="2010-01-05", fit_end="2010-12-31", weeks=8)
    in_sample = table["residual"].loc["2010-01-12":"2010-12-31"]
    expected = table["residual_6m"] / (in_sample.std() * math.sqrt(8))
    pd.testing.assert_series_equal(table["score"], expected, check_names=False)
    assert table["score"].iloc[10] > 0.25 or table["signal"].iloc[10] <= 0  # the trim follows the score
    # later data must not change an earlier score
    shorter = ind.filtered_residual(level.iloc[:80], filtered.iloc[:80], fit_start="2010-01-05", fit_end="2010-12-31", weeks=8)
    assert shorter["score"].iloc[70] == pytest.approx(table["score"].iloc[70])


def test_goldman_figures_in_the_reconciliation():
    import json
    path = DATA / "reconcile.json"
    gf = json.loads(path.read_text())["goldman_filter"]
    am = gf["am_other"]
    assert am["corr_score_vs_next_6m"] == pytest.approx(-0.43, abs=0.01)
    assert gf["spec"]["corr_score_vs_next_6m"] == pytest.approx(-0.26, abs=0.01)
    assert gf["lev"]["corr_score_vs_next_6m"] == pytest.approx(-0.18, abs=0.01)
    assert am["score_2019_04_30"] == pytest.approx(-0.67, abs=0.02)
    assert am["pos_hit"] == pytest.approx(0.741, abs=0.01) and am["neg_hit"] == pytest.approx(0.668, abs=0.01)


# ---- I6 ----------------------------------------------------------------------

def test_oai_hits_its_stated_bounds():
    plus = pd.DataFrame({"call_oi": [50.0], "put_oi": [-30.0], "call_v": [50.0], "put_v": [30.0]})
    minus = pd.DataFrame({"call_oi": [-50.0], "put_oi": [30.0], "call_v": [50.0], "put_v": [30.0]})
    assert ind.oai(plus).iloc[0] == pytest.approx(1.0)
    assert ind.oai(minus).iloc[0] == pytest.approx(-1.0)


def test_oai_stays_bounded_on_random_chains():
    random = np.random.default_rng(7)
    volume = random.uniform(0, 1000, 500)
    change = volume * random.uniform(-1, 1, 500)
    delta = random.uniform(0.01, 0.99, 500)
    is_call = random.random(500) > 0.5
    chain = pd.DataFrame({"date": np.repeat(np.arange(50), 10), "abs_delta": delta, "oi_change": change,
                          "volume": volume, "is_call": is_call})
    value = ind.oai(ind.option_components(chain))
    assert value.abs().max() <= 1.0


def test_select_options_uses_three_expiries_and_ten_points():
    chain = pd.DataFrame({"date": [1] * 5, "expiry": [10, 20, 30, 40, 10], "strike": [120.0, 120.0, 120.0, 120.0, 131.0],
                          "forward": [120.0] * 5, "is_call": [True] * 5, "abs_delta": [0.5] * 5,
                          "oi_change": [1.0] * 5, "volume": [1.0] * 5})
    assert len(ind.select_options(chain)) == 3


def test_opi_weights_quiet_days_less():
    parts = pd.DataFrame({"call_oi": [100.0, 0.1], "put_oi": [0.0, 0.0], "call_v": [100.0, 0.1], "put_v": [0.0, 0.0]})
    smooth = ind.opi(parts)
    assert smooth.iloc[1] == pytest.approx(1.0)


def test_opi_band_width_is_the_expanding_sd():
    values = pd.Series(np.sin(np.arange(200) / 5.0), index=pd.bdate_range("2015-01-01", periods=200))
    out = ind.opi_signal(values, band_half_life=63, multiple=0.85)
    width = (out["upper"] - out["lower"]) / (2 * 0.85)
    expected = values.expanding(20).std().shift(1)
    pd.testing.assert_series_equal(width, expected, check_names=False)


def test_opi_signal_direction():
    values = pd.Series(np.r_[np.zeros(40) + np.sin(np.arange(40)) * 0.01, [0.2, -0.2]])
    out = ind.opi_signal(values, band_half_life=10, multiple=0.85)
    assert out["signal"].iloc[-2] == -1.0  # upper breach is a sell
    assert out["signal"].iloc[-1] == 1.0  # lower breach is a buy


def test_normal_share_matches_the_report():
    # The report says a 0.85 band fires about 40 percent of the time.
    assert 2 * (1 - 0.5 * (1 + math.erf(0.85 / math.sqrt(2)))) == pytest.approx(0.395, abs=0.001)


def test_black76_delta():
    assert ind.black76_abs_delta(120, 120, 0.05, 0.25, 0.0, True) == pytest.approx(0.505, abs=0.001)
    assert ind.black76_abs_delta(120, 120, 0.05, 0.25, 0.0, False) == pytest.approx(0.495, abs=0.001)


# ---- I7 ----------------------------------------------------------------------

def test_continuation_formula():
    idx = weekly_index(4)
    out = ind.cftc_continuation(pd.Series([10.0] * 4, index=idx), pd.Series([5.0] * 4, index=idx))
    assert out.iloc[-1] == pytest.approx(20.0 / 60.0)


def test_cross_section_weights_sum_to_one():
    weights = ind.cross_section_weights(pd.Series({"A": 3.0, "B": 1.0, "C": 2.0, "D": 0.0}))
    assert weights.abs().sum() == pytest.approx(1.0)
    assert weights["A"] > 0 and weights["D"] < 0


def test_time_series_weights():
    weights = ind.time_series_weights(pd.Series({"A": 1.0, "B": -1.0}), pd.Series({"A": 0.1, "B": 0.2}))
    assert weights["A"] == pytest.approx(2 / 3)
    assert weights["B"] == pytest.approx(-1 / 3)


# ---- I8 ----------------------------------------------------------------------

def test_response_peak():
    grid = np.linspace(0, 5, 5001)
    peak = grid[np.argmax(cta.response(grid))]
    assert peak == pytest.approx(math.sqrt(2), abs=0.001)
    assert cta.response(0.0) == 0.0


def test_half_life_formula():
    assert cta.half_life(8) == pytest.approx(math.log(0.5) / math.log(7 / 8))


def test_cta_signal_positive_in_uptrend():
    random = np.random.default_rng(1)
    price = pd.Series(100 + np.cumsum(0.1 + random.normal(0, 0.3, 600)))
    assert cta.cta_signal(price).dropna().iloc[-1] > 0


def test_tick_rule():
    trades = pd.DataFrame({"time": pd.to_datetime(["2020-01-02 09:00:01", "2020-01-02 09:00:02",
                                                   "2020-01-02 09:00:03", "2020-01-02 09:01:00"]),
                           "price": [100.0, 100.5, 100.5, 100.0], "size": [1.0, 2.0, 3.0, 4.0]})
    out = cta.tick_rule_imbalance(trades)
    assert out.iloc[0] == 5.0 and out.iloc[1] == -4.0


def test_rolling_beta_recovers_slope():
    random = np.random.default_rng(3)
    signal = pd.Series(random.normal(size=200))
    imbalance = 4000.0 * signal
    out = cta.rolling_proxy(imbalance, signal)
    assert out["beta"].iloc[-1] == pytest.approx(4000.0)
    assert out["correlation"].iloc[-1] == pytest.approx(1.0)


# ---- I10 ---------------------------------------------------------------------

def test_bmi_table_from_the_report():
    # Exhibit 1 of the March 2015 note. Combined and overall must both reproduce.
    factors = pd.DataFrame({"carry": [5.4, -4.4, 6.8, -7.0], "momentum": [-4.6, 6.0, -3.4, -0.7],
                            "equity": [1.7, -7.0, -2.1, -4.8], "cycle": [4.7, 2.2, -1.0, -7.0]},
                           index=["UST", "Bund", "Gilt", "JGB"])
    out = ind.bmi_combine(factors)
    assert out["combined"].round(1).tolist() == [1.8, -0.8, 0.1, -4.9]
    assert out["overall"].tolist() == [0.0, 0.0, 0.0, 0.0]


def test_bmi_same_sign_keeps_signal():
    factors = pd.DataFrame({"a": [4.0, 4.0, 0.0]}, index=["X", "Y", "Z"])
    assert ind.bmi_combine(factors)["overall"].tolist() == [4.0, 4.0, 0.0]


def test_cap_signal_bounds():
    assert ind.cap_signal(50.0) == pytest.approx(10.0)
    assert ind.cap_signal(0.0) == 0.0


def test_bmi_factors_keep_their_dates():
    index = weekly_index(120)
    random = np.random.default_rng(11)
    noise = pd.Series(random.normal(size=120), index=index)
    level = pd.Series(100 + np.cumsum(random.normal(size=120)), index=index)
    for factor in (ind.carry_factor(noise + 3, noise.abs() + 1), ind.momentum_factor(level),
                   ind.equity_factor(noise, noise.shift(1)), ind.business_cycle_factor(noise)):
        assert isinstance(factor, pd.Series)
        assert factor.index.equals(index)
        assert factor.dropna().abs().max() <= 10.0


# ---- I11 ---------------------------------------------------------------------

def test_gegenbauer_first_terms():
    d, u = 0.3, 0.8
    psi = glgarma.gegenbauer_psi(d, u, 3)
    assert psi[1] == pytest.approx(2 * d * u)
    assert psi[2] == pytest.approx(-d + 2 * d * (1 + d) * u * u)


def test_gegenbauer_reduces_to_arfima_when_u_is_one():
    d = 0.2
    # (1 - B)^(-2d) has coefficient 2d at lag one and 2d(2d + 1)/2 at lag two.
    psi = glgarma.gegenbauer_psi(d, 1.0, 3)
    assert psi[1] == pytest.approx(2 * d)
    assert psi[2] == pytest.approx(2 * d * (2 * d + 1) / 2)


def test_generalised_poisson_sums_to_one():
    total = sum(math.exp(glgarma.gp_logpmf(y, 5.0, 0.3)) for y in range(400))
    mean = sum(y * math.exp(glgarma.gp_logpmf(y, 5.0, 0.3)) for y in range(400))
    assert total == pytest.approx(1.0, abs=1e-6)
    assert mean == pytest.approx(5.0, abs=1e-4)


def test_od_filter_runs():
    mu, log_likelihood = glgarma.od_filter(np.array([3, 5, 4, 6, 2]), c=1.2, d=0.2, u=0.7, nu=0.1)
    assert (mu > 0).all() and log_likelihood < 0


def test_od_filter_rejects_an_exploding_draw():
    _, log_likelihood = glgarma.od_filter(np.array([3, 5, 4, 6, 2, 8, 7, 3, 4, 5]), c=1.2, d=0.2, u=0.7, nu=0.1)
    assert log_likelihood == -math.inf


# ---- Statistics --------------------------------------------------------------

def test_newey_west_matches_statsmodels():
    sm = pytest.importorskip("statsmodels.api")
    random = np.random.default_rng(5)
    x = pd.DataFrame({"x": random.normal(size=300)})
    y = pd.Series(1.0 + 0.5 * x["x"] + random.normal(size=300))
    ours = newey_west_ols(y, x, lags=4)
    fit = sm.OLS(y, sm.add_constant(x)).fit(cov_type="HAC", cov_kwds={"maxlags": 4, "use_correction": False})
    assert ours["beta"].values == pytest.approx(fit.params.values)
    assert ours["se"].values == pytest.approx(fit.bse.values, rel=1e-8)


# ---- Data checks -------------------------------------------------------------

def test_publish_time_is_friday_afternoon():
    stamp = publish_time(pd.Timestamp("2017-05-09"))
    assert stamp.weekday() == 4 and stamp.hour == 15 and stamp.minute == 30
    assert stamp.date().isoformat() == "2017-05-12"


def test_known_at_blocks_lookahead():
    report = pd.DataFrame({"x": [1, 2]}, index=pd.to_datetime(["2017-05-02", "2017-05-09"]))
    before = pd.Timestamp("2017-05-12 15:00", tz="America/New_York")
    after = pd.Timestamp("2017-05-12 15:31", tz="America/New_York")
    assert len(known_at(report, before)) == 1 and len(known_at(report, after)) == 2


def test_workbook_cftc_identity_and_gap():
    weekly = pd.read_csv(DATA / "ty_cftc.csv", parse_dates=["date"], index_col="date")
    frame = weekly.assign(open_interest=weekly[["dealer_long", "asset_mgr_long", "lev_money_long", "other_rept_long",
                                                "nonrept_long", "dealer_spread", "asset_mgr_spread",
                                                "lev_money_spread", "other_rept_spread"]].sum(axis=1))
    problems = check_cftc(frame, "tff")
    assert (problems["check"] == "missing_week").sum() == 1
    assert problems[problems["check"] == "missing_week"]["date"].iloc[0].date().isoformat() == "2014-11-18"
    assert (problems["check"] == "long_identity").sum() == 0
    assert (problems["check"] == "short_identity").sum() == 0


@pytest.mark.skipif(not (DATA / "ty_daily.csv").exists(), reason="ty_daily.csv is restricted data and is not in the public repo")
def test_daily_checks_find_workbook_faults():
    daily = pd.read_csv(DATA / "ty_daily.csv", parse_dates=["date"], index_col="date")
    flags = check_daily(daily)
    assert flags["close_outside_range"].sum() == 69
    assert flags["high_equals_low"].sum() == 35
    assert flags["missing_range"].sum() == 19
    assert flags["missing_volume"].sum() == 1
    assert flags["volume_collapse"].sum() > 0


# ---- I13 ---------------------------------------------------------------------

def test_taarss_slope_through_origin_times_r_squared():
    assert ind.taarss([0.5, 1.0, 1.5, 2.0]) == pytest.approx(0.5)  # a perfect line: slope 0.5, R-squared 1
    noisy = [1.0, 0.0, 2.0, 1.0]
    x = np.arange(1.0, 5.0)
    expected = (x * noisy).sum() / (x * x).sum() * np.corrcoef(x, noisy)[0, 1] ** 2
    assert ind.taarss(noisy) == pytest.approx(expected)
    assert ind.taarss([0.0, 0.0, 0.0]) == 0.0


def test_efrom_rebuilds_the_printed_december_2014_level():
    # TAARSS values rebuilt from the drawn flow paths in The Flow Whisperer, 5 January 2015. The chart prints 0.64.
    signals = {"US Treasury": -0.000, "Gold": -0.120, "Corp IG": 0.024, "Senior Loans": -0.376, "Corp HY": -0.012,
               "EM Debt": -0.316, "Defensives": 0.626, "Large Cap": 0.095, "Broad Commodities": -0.072,
               "Domestic Cyclicals": 0.447, "DM": 0.023, "Global Cyclicals": 0.171, "Small Cap": 0.117, "EM": -0.149}
    assert ind.efrom_level(signals) == pytest.approx(0.64, abs=0.005)
    with pytest.raises(ValueError):
        ind.efrom_level({"Gold": 1.0})
