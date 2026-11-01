"""Regression and evaluation helpers shared by the indicator tests."""
from __future__ import annotations

import numpy as np
import pandas as pd


def newey_west_ols(y: pd.Series, x: pd.DataFrame, lags: int) -> pd.DataFrame:
    """OLS with Bartlett-kernel Newey-West standard errors. A constant is added."""
    frame = pd.concat([y.rename("__y__"), x], axis=1).dropna()
    design = np.column_stack([np.ones(len(frame)), frame[x.columns].values])
    target = frame["__y__"].values
    xtx_inverse = np.linalg.inv(design.T @ design)
    beta = xtx_inverse @ design.T @ target
    residual = target - design @ beta
    moments = design * residual[:, None]
    meat = moments.T @ moments
    for lag in range(1, lags + 1):
        weight = 1.0 - lag / (lags + 1.0)
        cross = moments[lag:].T @ moments[:-lag]
        meat += weight * (cross + cross.T)
    covariance = xtx_inverse @ meat @ xtx_inverse
    errors = np.sqrt(np.diag(covariance))
    return pd.DataFrame({"beta": beta, "se": errors, "t": beta / errors}, index=["const", *x.columns])


def si_regression(returns_ahead: pd.Series, si: pd.Series, d90=None, d10=None, lags: int | None = None,
                  horizon: int = 1) -> pd.DataFrame:
    """Baseline regression, plus the extreme dummies when they are given."""
    x = pd.DataFrame({"si": si})
    if d90 is not None:
        x["d90"] = d90
        x["d10"] = d10
    return newey_west_ols(returns_ahead, x, lags if lags is not None else horizon)


def forward_change(level: pd.Series, periods: int) -> pd.Series:
    return level.shift(-periods) - level


def reversal_hits(signal: pd.Series, yield_change_ahead: pd.Series) -> dict:
    """signal +1 expects a rally (yield falls). signal -1 expects a sell-off (yield rises)."""
    usable = signal.notna() & yield_change_ahead.notna()
    buys = usable & (signal > 0)
    sells = usable & (signal < 0)
    return {"unconditional_rally": float((yield_change_ahead[usable] < 0).mean()),
            "buy_hit": float((yield_change_ahead[buys] < 0).mean()), "buy_count": int(buys.sum()),
            "sell_hit": float((yield_change_ahead[sells] > 0).mean()), "sell_count": int(sells.sum())}
