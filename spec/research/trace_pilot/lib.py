"""Paths, fixed dates and inference used by every step of the TRACE pilot. Rules come from plan.md."""
from __future__ import annotations

import json
import math
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sps

HERE = Path(__file__).resolve().parent
SPEC = HERE.parents[1]
sys.path.insert(0, str(SPEC))
sys.dont_write_bytecode = True

# Bond-day aggregates come from licensed TRACE, so they never live in the project folder.
WORK = Path(os.environ.get("TRACE_PILOT_WORK", Path(tempfile.gettempdir()) / "trace_pilot_work"))
WORK.mkdir(parents=True, exist_ok=True)
RESULTS = HERE / "results.json"

SEED = 42
DEV_END = pd.Timestamp("2024-09-30")
HOLD_START = pd.Timestamp("2024-10-01")
HOLD_END = pd.Timestamp("2025-09-30")
HORIZONS = (1, 4, 13)
SPREAD_ISSUERS = ["AAPL", "AMZN", "CMCS", "COST", "CSCO", "GOOG", "IBM", "INTC", "MSFT", "NVDA", "PEP", "RIG"]
BUCKET_EDGES = [1, 3, 7, 15, 200]
BUCKET_NAMES = ["1-3y", "3-7y", "7-15y", "15y+"]
WEBB = np.array([-math.sqrt(1.5), -1.0, -math.sqrt(0.5), math.sqrt(0.5), 1.0, math.sqrt(1.5)])
WCB_DRAWS = 1999


def save_part(key: str, value) -> None:
    """Merge one section into results.json, so each step can be rerun alone."""
    data = json.loads(RESULTS.read_text()) if RESULTS.exists() else {}
    data[key] = value
    RESULTS.write_text(json.dumps(data, indent=1, default=_plain, sort_keys=True))


def _plain(value):
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, (pd.Timestamp,)):
        return str(value.date())
    raise TypeError(type(value))


def demean(values: np.ndarray, groups: np.ndarray) -> np.ndarray:
    """Remove group means from each column. groups holds integer ids 0..K-1."""
    weights = np.bincount(groups).astype(float)
    weights[weights == 0] = 1.0
    if values.ndim == 1:
        return values - (np.bincount(groups, values) / weights)[groups]
    return np.column_stack([demean(values[:, i], groups) for i in range(values.shape[1])])


def absorb(values: np.ndarray, fe: list) -> np.ndarray:
    """Alternating projections over one or two sets of fixed effects."""
    out = values.astype(float).copy()
    if len(fe) == 1:
        return demean(out, fe[0])
    for _ in range(50):
        previous = out.copy()
        for groups in fe:
            out = demean(out, groups)
        if np.nanmax(np.abs(out - previous)) < 1e-10:
            break
    return out


def codes(series) -> np.ndarray:
    return pd.factorize(series)[0]


def _cluster_var(xt: np.ndarray, resid: np.ndarray, sxx: float, groups: np.ndarray) -> float:
    scores = np.bincount(groups, xt * resid)
    return float((scores ** 2).sum() / sxx ** 2)


def fit(frame: pd.DataFrame, y: str, x: str, fe: list, controls: list = None, h: int = 1, seed: int = SEED,
        draws: int = WCB_DRAWS, dk: bool = False) -> dict:
    """Slope of y on x after fixed effects and controls, with the plan's inference.

    Two-way clustering by issuer and by date block of h weeks (CR1, G-1 df) plus a restricted wild cluster bootstrap
    by issuer with Webb weights. With dk=True, Driscoll-Kraay on date moments replaces both, for four-cluster panels.
    Primary p is the larger of the available p-values.
    """
    controls = controls or []
    cols = [y, x, *controls]
    data = frame.dropna(subset=cols)
    if len(data) < 30 or data[x].std() == 0:
        return {"n": int(len(data)), "b": None, "p": 1.0, "ran": False}
    fe_ids = [codes(data[name]) for name in fe]
    matrix = absorb(data[cols].to_numpy(float), fe_ids) if fe_ids else data[cols].to_numpy(float) - data[cols].to_numpy(float).mean(0)
    target, regressor = matrix[:, 0], matrix[:, 1]
    if controls:
        z = matrix[:, 2:]
        coef_x = np.linalg.lstsq(z, regressor, rcond=None)[0]
        coef_y = np.linalg.lstsq(z, target, rcond=None)[0]
        xt, res0 = regressor - z @ coef_x, target - z @ coef_y
    else:
        xt, res0 = regressor, target
    sxx = float((xt * xt).sum())
    if sxx <= 0:
        return {"n": int(len(data)), "b": None, "p": 1.0, "ran": False}
    b = float((xt * res0).sum() / sxx)
    resid = res0 - b * xt
    weeks = pd.Series(data["week"].to_numpy())
    week_index = ((weeks - weeks.min()).dt.days // 7).to_numpy()
    n_weeks = int(weeks.nunique())
    ss_tot, ss_res = float((res0 ** 2).sum()), float((resid ** 2).sum())
    out = {"n": int(len(data)), "weeks": n_weeks, "n_eff_weeks": n_weeks / h, "b": b, "r2_within": 1 - ss_res / ss_tot if ss_tot > 0 else None,
           "n_units": int(data["unit"].nunique()) if "unit" in data else None}
    if dk:
        by_date = np.bincount(week_index, xt * resid)
        lag = max(4, math.ceil(1.5 * h))
        meat = float((by_date ** 2).sum())
        for k in range(1, lag + 1):
            meat += 2 * (1 - k / (lag + 1)) * float((by_date[k:] * by_date[:-k]).sum())
        se = math.sqrt(max(meat, 0)) / sxx
        df = max(n_weeks / h - 2, 1)
        t = b / se if se > 0 else 0.0
        p = float(2 * sps.t.sf(abs(t), df))
        out.update(se=se, t=t, p_cluster=p, p_wcb=None, p=p, method="driscoll_kraay", df=df, mde80=2.8 * se)
        return out
    issuers = codes(data["issuer"])
    blocks = codes(week_index // h)
    pair = codes(pd.Series(issuers) * 100000 + blocks)
    g_i, g_d = issuers.max() + 1, blocks.max() + 1
    v_i = _cluster_var(xt, resid, sxx, issuers) * g_i / max(g_i - 1, 1)
    v_d = _cluster_var(xt, resid, sxx, blocks) * g_d / max(g_d - 1, 1)
    v_p = _cluster_var(xt, resid, sxx, pair) * (pair.max() + 1) / max(pair.max(), 1)
    # The two-way sum can fall below either one-way variance with few blocks. Take the largest, which is conservative.
    v = max(v_i + v_d - v_p, v_i, v_d)
    se = math.sqrt(v)
    df = max(min(g_i, g_d) - 1, 1)
    t = b / se
    p_cluster = float(2 * sps.t.sf(abs(t), df))
    # Restricted wild cluster bootstrap. The null slope gives res0. Each cluster flips with one Webb weight.
    rng = np.random.default_rng(seed)
    a_g = np.bincount(issuers, xt * res0)
    q_g = np.bincount(issuers, xt * xt)
    weights = rng.choice(WEBB, size=(draws, g_i))
    b_star = (weights * a_g).sum(1) / sxx
    scores = weights * a_g - b_star[:, None] * q_g
    se_star = np.sqrt((scores ** 2).sum(1)) / sxx * math.sqrt(g_i / max(g_i - 1, 1))
    t_star = np.divide(b_star, se_star, out=np.zeros_like(b_star), where=se_star > 0)
    t_obs = b / (math.sqrt(_cluster_var(xt, resid, sxx, issuers) * g_i / max(g_i - 1, 1)) or np.inf)
    p_wcb = float((1 + (np.abs(t_star) >= abs(t_obs)).sum()) / (draws + 1))
    out.update(se=se, t=t, df=df, p_cluster=p_cluster, p_wcb=p_wcb, p=max(p_cluster, p_wcb), method="twoway_wcb",
               mde80=2.8 * se, g_issuer=int(g_i), g_date=int(g_d), t_issuer=t_obs)
    return out


def holm(pvalues: dict) -> dict:
    keys = sorted(pvalues, key=lambda k: pvalues[k])
    m = len(keys)
    adjusted, running = {}, 0.0
    for i, key in enumerate(keys):
        running = max(running, min(1.0, (m - i) * pvalues[key]))
        adjusted[key] = running
    return adjusted
