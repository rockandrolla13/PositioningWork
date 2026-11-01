"""I11: the building blocks of the Yan, Chan and Peters long-memory count model.

The paper samples the posterior with Stan. This module gives the deterministic parts,
so a Stan or NumPyro program can be checked against them.
"""
from __future__ import annotations

import math

import numpy as np


def gegenbauer_psi(d: float, u: float, terms: int) -> np.ndarray:
    """Coefficients of (1 - 2uB + B^2)^(-d). ARFIMA is the special case u = 1."""
    psi = np.zeros(terms)
    psi[0] = 1.0
    if terms > 1:
        psi[1] = 2.0 * d * u
    for j in range(2, terms):
        psi[j] = 2.0 * u * ((d - 1.0) / j + 1.0) * psi[j - 1] - (2.0 * (d - 1.0) / j + 1.0) * psi[j - 2]
    return psi


def gp_logpmf(y: int, mu: float, nu: float) -> float:
    """Generalised Poisson. The mean is mu and the variance is mu / (1 - nu)^2."""
    lam = mu * (1.0 - nu)
    inner = lam + nu * y
    if lam <= 0 or inner <= 0:
        return -math.inf
    return math.log(lam) + (y - 1) * math.log(inner) - inner - math.lgamma(y + 1)


def od_filter(y: np.ndarray, c: float, d: float, u: float, nu: float = 0.0, terms: int = 100) -> tuple:
    """Observation-driven GLGARMA(0, d, 0) with Pearson residual errors.

    log mu_t = c + sum over j >= 1 of psi_{j-1} * e_{t-j}, where e_t = (y_t - mu_t) / sqrt(mu_t).
    Returns the mean path and the Generalised Poisson log likelihood.
    The recursion can explode for poor parameter draws. It then returns minus infinity.
    """
    psi = gegenbauer_psi(d, u, terms)
    mu = np.zeros(len(y))
    errors = np.zeros(len(y))
    log_likelihood = 0.0
    for t, value in enumerate(y):
        reach = min(t, terms)
        history = sum(psi[j] * errors[t - 1 - j] for j in range(reach))
        if abs(c + history) > 30.0:  # the recursion has blown up, so a sampler must reject this draw
            return mu, -math.inf
        mu[t] = math.exp(c + history)
        errors[t] = (value - mu[t]) / math.sqrt(mu[t])
        log_likelihood += gp_logpmf(int(value), mu[t], nu)
    return mu, log_likelihood


def forecast_scores(actual: np.ndarray, forecast: np.ndarray, history_last: float | None = None) -> dict:
    """MAE, RMSE, MAPE and MASE over the forecast block, as the paper defines them."""
    actual = np.asarray(actual, dtype=float)
    forecast = np.asarray(forecast, dtype=float)
    error = actual - forecast
    naive = np.mean(np.abs(np.diff(actual)))
    return {"mae": float(np.mean(np.abs(error))), "rmse": float(np.sqrt(np.mean(error ** 2))),
            "mape": float(np.mean(np.abs(error / actual)) * 100.0), "mase": float(np.mean(np.abs(error / naive)))}
