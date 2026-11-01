"""I8: JPMorgan CTA proxy, with the Baz et al. trend signal it cites."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

PAIRS = ((8, 24), (16, 48), (32, 96))


def half_life(time_scale: float) -> float:
    return math.log(0.5) / math.log(1.0 - 1.0 / time_scale)


def response(y):
    """Position size from trend strength. It peaks near y = sqrt(2), then falls back to zero."""
    return y * np.exp(-(y ** 2) / 4.0) / 0.89


def trend_strength(price: pd.Series, short: int, long: int) -> pd.Series:
    fast = price.ewm(halflife=half_life(short), adjust=False).mean()
    slow = price.ewm(halflife=half_life(long), adjust=False).mean()
    scaled = (fast - slow) / price.rolling(63, min_periods=63).std()
    return scaled / scaled.rolling(252, min_periods=252).std()


def cta_signal(price: pd.Series) -> pd.Series:
    """Equal-weight average of the response across the three time-scale pairs."""
    return pd.concat([response(trend_strength(price, s, l)) for s, l in PAIRS], axis=1).mean(axis=1, skipna=False)


def tick_rule_imbalance(trades: pd.DataFrame) -> pd.Series:
    """Signed contracts per minute. Columns: time, price, size. A zero tick keeps the last sign.

    The JPMorgan report does not state its classifier. This is a stated default.
    """
    ordered = trades.sort_values("time")
    sign = np.sign(ordered["price"].diff()).replace(0.0, np.nan).ffill().fillna(0.0)
    signed = sign * ordered["size"]
    return signed.groupby(ordered["time"].dt.floor("min")).sum()


def rolling_proxy(imbalance: pd.Series, signal: pd.Series, window: int = 21) -> pd.DataFrame:
    """Rolling correlation and beta between imbalance and signal, one sample per day.

    Pass only the minutes inside the chosen execution windows, summed per day.
    """
    frame = pd.DataFrame({"imbalance": imbalance, "signal": signal}).dropna()
    correlation = frame["imbalance"].rolling(window).corr(frame["signal"])
    beta = frame["imbalance"].rolling(window).cov(frame["signal"]) / frame["signal"].rolling(window).var()
    zero_mean_z = beta / np.sqrt((beta ** 2).expanding(min_periods=window).mean())
    return pd.DataFrame({"correlation": correlation, "beta": beta, "beta_z_zero_mean": zero_mean_z})


def pick_execution_minutes(minute_imbalance: pd.DataFrame, signal: pd.Series, top: int = 5) -> list:
    """Rank minutes of the day by how strongly imbalance follows the signal.

    minute_imbalance has dates in rows and minutes of the day in columns. Calibrate on past data only.
    """
    scores = {minute: minute_imbalance[minute].corr(signal.reindex(minute_imbalance.index))
              for minute in minute_imbalance.columns}
    return [m for m, _ in sorted(scores.items(), key=lambda item: -(item[1] if item[1] == item[1] else -9))[:top]]
