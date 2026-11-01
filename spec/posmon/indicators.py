"""Positioning indicators that do not estimate entry prices."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import norm

# ---------------------------------------------------------------------------
# I1: net position as a share of open interest
# ---------------------------------------------------------------------------


def net_pct_oi(long_side: pd.Series, short_side: pd.Series, open_interest: pd.Series) -> pd.Series:
    return 100.0 * (long_side - short_side) / open_interest


def rolling_stats(series: pd.Series, weeks: int = 52) -> pd.DataFrame:
    """The 12-month high, low and median used in the Deutsche Bank sales note."""
    roll = series.rolling(weeks, min_periods=weeks)
    return pd.DataFrame({"high": roll.max(), "low": roll.min(), "median": roll.median()})


# ---------------------------------------------------------------------------
# I2: Goldman Sachs sentiment index
# ---------------------------------------------------------------------------


def sentiment_index(net: pd.Series, weeks: int = 156) -> pd.Series:
    """Scale net position between its rolling low and high. The window includes today."""
    low = net.rolling(weeks, min_periods=weeks).min()
    high = net.rolling(weeks, min_periods=weeks).max()
    return 100.0 * (net - low) / (high - low)


def extreme_flags(si: pd.Series, high: float = 90.0, low: float = 10.0) -> pd.DataFrame:
    """Dummies D90 and D10, and the counter of weeks spent in the current extreme."""
    d90 = (si >= high).astype(float).where(si.notna())
    d10 = (si <= low).astype(float).where(si.notna())
    state = d90.fillna(0) - d10.fillna(0)
    run_id = (state != state.shift()).cumsum()
    counter = state.abs().groupby(run_id).cumsum()
    return pd.DataFrame({"d90": d90, "d10": d10, "counter": counter})


# ---------------------------------------------------------------------------
# I3: Deutsche Bank scaled positioning
# ---------------------------------------------------------------------------


def db_scaled(net: pd.Series, weeks: int = 209) -> pd.Series:
    """Map net contracts to -10..+10 over four years, keeping zero at zero.

    +10 is the largest net long in the window. -10 is the largest net short.
    A window with no net long has no positive scale. The same holds for shorts.
    """
    largest_long = net.rolling(weeks, min_periods=weeks).max().clip(lower=0)
    largest_short = net.rolling(weeks, min_periods=weeks).min().clip(upper=0).abs()
    up = 10.0 * net / largest_long.where(largest_long > 0)
    down = 10.0 * net / largest_short.where(largest_short > 0)
    out = pd.Series(np.where(net > 0, up, np.where(net < 0, down, 0.0)), index=net.index)
    return out.where(largest_long.notna())


# ---------------------------------------------------------------------------
# I4: one-standard-deviation rule on duration-weighted net position
# ---------------------------------------------------------------------------


def dv01_weighted_net(nets: dict, dv01: dict) -> pd.Series:
    """Sum of net contracts times dollars per basis point, in $mm per basis point."""
    frame = pd.DataFrame({key: nets[key] * dv01[key] / 1e6 for key in nets})
    return frame.sum(axis=1, min_count=1)


def one_sd_rule(position: pd.Series, multiple: float = 1.0) -> pd.Series:
    """+1 is a buy signal after a bearish extreme. -1 is a sell signal after a bullish extreme."""
    score = (position - position.mean()) / position.std()
    return pd.Series(np.where(score <= -multiple, 1.0, np.where(score >= multiple, -1.0, 0.0)),
                     index=position.index)


# ---------------------------------------------------------------------------
# I5: Goldman Sachs filtered position and residual
# ---------------------------------------------------------------------------


def filtered_change(nets: dict, yields_bp: pd.DataFrame, dv01) -> pd.Series:
    """Keep a tenor's change only when it moves with the market, then sum in $mm/bp.

    With the market means net selling as yields rise, or net buying as yields fall.
    dv01[tenor] is a fixed number or a weekly series of dollars per contract.
    """
    total = None
    for tenor, net in nets.items():
        change = net.diff()
        move = yields_bp[tenor].reindex(net.index, method="ffill").diff()
        weight = dv01[tenor]
        if isinstance(weight, pd.Series):
            weight = weight.reindex(net.index, method="ffill")
        kept = (change * weight / 1e6).where(np.sign(change) == -np.sign(move), 0.0).fillna(0.0)
        total = kept if total is None else total.add(kept, fill_value=0.0)
    return total


def filtered_residual(yield_10y_bp: pd.Series, filtered: pd.Series, fit_start="2006-06-13",
                      fit_end="2010-12-31", weeks: int = 26, trim: float = 0.25) -> pd.DataFrame:
    """Fit on the in-sample window, sum residuals over six months, and score them.

    A positive score means yields rose by more than positioning implies. That is a rally bias.
    The score divides the six-month sum by the in-sample weekly residual spread times sqrt(weeks).
    It subtracts no mean, and it uses no data after fit_end, so it has no look-ahead after that date.
    """
    level = yield_10y_bp.reindex(filtered.index, method="ffill")
    move = level.diff()
    mask = (filtered.index >= pd.Timestamp(fit_start)) & (filtered.index <= pd.Timestamp(fit_end))
    mask &= move.notna().values
    slope, intercept = np.polyfit(filtered[mask], move[mask], 1)
    residual = move - (intercept + slope * filtered)
    summed = residual.rolling(weeks).sum()
    scale = residual[mask].std() * np.sqrt(weeks)
    score = summed / scale
    signal = pd.Series(np.where(score > trim, 1.0, np.where(score < -trim, -1.0, 0.0)), index=score.index)
    return pd.DataFrame({"slope": slope, "intercept": intercept, "residual": residual, "scale": scale,
                         "residual_6m": summed, "score": score, "signal": signal.where(score.notna())})


def forward_stats(level_bp: pd.Series, signal: pd.Series, weeks: int = 26) -> dict:
    """Hit rates against the change in yield over the next six months."""
    ahead = level_bp.shift(-weeks) - level_bp
    usable = ahead.notna() & signal.notna()
    long_case = usable & (signal > 0)
    short_case = usable & (signal < 0)
    return {"total": int(usable.sum()), "uncond_rally": float((ahead[usable] < 0).mean()),
            "uncond_avg": float(ahead[usable].mean()), "pos_n": int(long_case.sum()),
            "pos_hit": float((ahead[long_case] < 0).mean()), "pos_avg": float(ahead[long_case].mean()),
            "neg_n": int(short_case.sum()), "neg_hit": float((ahead[short_case] > 0).mean()),
            "neg_avg": float(ahead[short_case].mean())}


# ---------------------------------------------------------------------------
# I6: Goldman Sachs options-implied position indicator
# ---------------------------------------------------------------------------


def black76_abs_delta(forward, strike, vol, years, rate, is_call) -> float:
    """Absolute Black-76 delta. The formula for OAI needs positive deltas."""
    d1 = (math.log(forward / strike) + 0.5 * vol * vol * years) / (vol * math.sqrt(years))
    discount = math.exp(-rate * years)
    return discount * (norm.cdf(d1) if is_call else norm.cdf(-d1))


def select_options(chain: pd.DataFrame, half_width: float = 10.0, expiries: int = 3) -> pd.DataFrame:
    """Keep the front three expiries and strikes within 10 points of the forward.

    Columns: date, expiry, strike, is_call, forward, abs_delta, oi_change, volume.
    """
    chain = chain[(chain["strike"] - chain["forward"]).abs() <= half_width].copy()
    ranks = chain.groupby("date")["expiry"].rank(method="dense")
    return chain[ranks <= expiries]


def option_components(chain: pd.DataFrame) -> pd.DataFrame:
    """Compute the four daily delta-weighted sums that feed OAI and OPI."""
    weighted = chain.assign(w_oi=chain["abs_delta"] * chain["oi_change"], w_v=chain["abs_delta"] * chain["volume"])
    calls = weighted[weighted["is_call"]].groupby("date")[["w_oi", "w_v"]].sum()
    puts = weighted[~weighted["is_call"]].groupby("date")[["w_oi", "w_v"]].sum()
    out = pd.DataFrame({"call_oi": calls["w_oi"], "put_oi": puts["w_oi"], "call_v": calls["w_v"], "put_v": puts["w_v"]})
    return out.sort_index().fillna(0.0)


def oai(parts: pd.DataFrame) -> pd.Series:
    return (parts["call_oi"] - parts["put_oi"]) / (parts["call_v"] + parts["put_v"])


def opi(parts: pd.DataFrame, half_life: float = 25.0) -> pd.Series:
    """Smooth each part first. The ratio of averages keeps low-volume days small."""
    ema = parts.ewm(halflife=half_life, adjust=False).mean()
    return (ema["call_oi"] - ema["put_oi"]) / (ema["call_v"] + ema["put_v"])


def opi_signal(indicator: pd.Series, band_half_life: float = 63.0, multiple: float = 0.85,
               min_periods: int = 20) -> pd.DataFrame:
    """Sell above the upper band and buy below the lower band. Bands use yesterday's data.

    The centre is an exponential mean. The half-width is k times the expanding standard deviation.
    Goldman's charts fix this: width correlates 0.9994 and 0.9987, with implied k of 0.846 and 1.242.
    """
    mean = indicator.ewm(halflife=band_half_life, adjust=False).mean().shift(1)
    std = indicator.expanding(min_periods).std().shift(1)
    upper, lower = mean + multiple * std, mean - multiple * std
    signal = pd.Series(np.where(indicator > upper, -1.0, np.where(indicator < lower, 1.0, 0.0)), index=indicator.index)
    return pd.DataFrame({"opi": indicator, "upper": upper, "lower": lower, "signal": signal.where(upper.notna())})


# ---------------------------------------------------------------------------
# I7: Deutsche Bank FX Cookbook signals
# ---------------------------------------------------------------------------


def cftc_continuation(long_side: pd.Series, short_side: pd.Series, weeks: int = 4) -> pd.Series:
    """Four-week sums of longs and shorts, as a share of their total."""
    longs = long_side.rolling(weeks, min_periods=weeks).sum()
    shorts = short_side.rolling(weeks, min_periods=weeks).sum()
    return (longs - shorts) / (longs + shorts)


def cftc_reversal(net: pd.Series, daily_returns: pd.Series, lookbacks=(4, 8, 13), vol_days: int = 126) -> pd.Series:
    """Average z-score over one, two and three months, over six-month volatility, with the sign flipped."""
    scores = [(net - net.rolling(n, min_periods=n).mean()) / net.rolling(n, min_periods=n).std() for n in lookbacks]
    average = pd.concat(scores, axis=1).mean(axis=1, skipna=False)
    volatility = daily_returns.rolling(vol_days, min_periods=vol_days).std()
    return -average / volatility.reindex(average.index, method="ffill")


def coffee_signal(call_notional: pd.Series, put_notional: pd.Series, sum_days: int = 20, vol_days: int = 252) -> pd.Series:
    """Four-week call minus put notional, over the one-year volatility of that measure."""
    imbalance = (call_notional - put_notional).rolling(sum_days, min_periods=sum_days).sum()
    return imbalance / imbalance.rolling(vol_days, min_periods=vol_days).std()


def time_series_weights(signals: pd.Series, vols: pd.Series) -> pd.Series:
    """Sign of the signal times an inverse-volatility share."""
    inverse = 1.0 / vols
    return np.sign(signals) * inverse / inverse.sum()


def cross_section_weights(signals: pd.Series) -> pd.Series:
    """Long the top half and short the bottom half. Absolute weights sum to one."""
    order = signals.sort_values(ascending=False).index
    half = len(order) // 2
    weights = pd.Series(0.0, index=signals.index)
    weights[order[:half]] = 1.0 / (2 * half)
    weights[order[-half:]] = -1.0 / (2 * half)
    return weights


# ---------------------------------------------------------------------------
# I10: Morgan Stanley Bond Market Indicators
# ---------------------------------------------------------------------------


def cap_signal(z_score):
    """Map a score to -10..+10 with the normal cumulative distribution."""
    capped = 10.0 * (2.0 * norm.cdf(z_score) - 1.0)
    return pd.Series(capped, index=z_score.index) if isinstance(z_score, pd.Series) else capped


def expanding_z(series: pd.Series, min_periods: int = 52) -> pd.Series:
    mean = series.expanding(min_periods).mean()
    std = series.expanding(min_periods).std()
    return (series - mean) / std


def carry_factor(slope_2s10s: pd.Series, realised_vol_1y: pd.Series) -> pd.Series:
    """Curve slope over one-year realised volatility, as an expanding z-score, then capped."""
    return cap_signal(expanding_z(slope_2s10s / realised_vol_1y))


def momentum_factor(excess_index: pd.Series, weeks: int = 17, scale: float = 1.0) -> pd.Series:
    """Index at t-1 less its prior moving average, over the moving average of absolute changes.

    No z-score is used. Choose `scale` so the signal volatility matches the other factors.
    """
    lagged = excess_index.shift(1)
    trend = lagged.shift(1).ewm(span=weeks, adjust=False).mean()
    noise = excess_index.diff().abs().shift(1).ewm(span=weeks, adjust=False).mean()
    return cap_signal(scale * (lagged - trend) / noise)


def equity_factor(local_return_3m: pd.Series, em_minus_dm_3m: pd.Series) -> pd.Series:
    """Weak equities mean long duration, so the sign flips."""
    average = (expanding_z(local_return_3m) + expanding_z(em_minus_dm_3m)) / 2.0
    return cap_signal(-average)


def business_cycle_factor(composite_surprise: pd.Series, scale: float = 1.0) -> pd.Series:
    """A positive surprise means short duration. No z-score is used."""
    return cap_signal(-scale * composite_surprise)


def bmi_combine(factors: pd.DataFrame, dead_band: float = 1.5) -> pd.DataFrame:
    """Combine factor rows (markets in rows, factors in columns) for one date.

    A combined signal inside the band becomes zero. A market keeps its signal only if at
    least one other market has the same sign. The published UST row is the test case.
    """
    combined = factors.mean(axis=1)
    banded = combined.where(combined.abs() > dead_band, 0.0)
    overall = banded.copy()
    for market in banded.index:
        others = banded.drop(market)
        same_sign = (np.sign(others) == np.sign(banded[market])).any()
        if banded[market] == 0 or not same_sign:
            overall[market] = 0.0
    return pd.DataFrame({"combined": combined, "banded": banded, "overall": overall})


def bmi_cross_market(overall_a: float, overall_b: float) -> float:
    """Difference of two overall signals, when at least one is live."""
    return overall_a - overall_b if (overall_a != 0 or overall_b != 0) else 0.0


# ---------------------------------------------------------------------------
# I13: Deutsche Bank ETF Flow Risk-o-Meter (EFRoM)
# ---------------------------------------------------------------------------

EFROM_RISK_FACTORS = {"US Treasury": -1.0, "Gold": -1.0, "Corp IG": -0.5, "Senior Loans": 0.5, "Corp HY": 0.5, "EM Debt": 0.5,
                      "Defensives": 0.5, "Large Cap": 0.5, "Broad Commodities": 1.0, "Domestic Cyclicals": 1.0, "DM": 1.0,
                      "Global Cyclicals": 1.0, "Small Cap": 1.5, "EM": 1.5}


def taarss(cumulative_pct_aum) -> float:
    """Flow trend for one segment and one month: slope through the origin times R-squared.

    The input holds cumulative flow in percent of AUM for trading days 1 to n, with the prior month-end at zero.
    The zero anchor itself is not an input. R-squared comes from an ordinary regression with an intercept.
    """
    y = np.asarray(cumulative_pct_aum, dtype=float)
    x = np.arange(1, len(y) + 1, dtype=float)
    slope = float((x * y).sum() / (x * x).sum())
    r_squared = float(np.corrcoef(x, y)[0, 1] ** 2) if y.std() > 0 else 0.0
    return slope * r_squared


def efrom_level(signals: dict, factors: dict = None) -> float:
    """Risk-weighted sum of raw TAARSS values, not z-scores. Every factor needs a signal."""
    factors = EFROM_RISK_FACTORS if factors is None else factors
    missing = set(factors) - set(signals)
    if missing:
        raise ValueError(f"missing segments: {sorted(missing)}")
    return float(sum(signals[name] * weight for name, weight in factors.items()))
