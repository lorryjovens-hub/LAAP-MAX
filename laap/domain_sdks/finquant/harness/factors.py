"""LAAP FinQuant Domain SDK — Factor model harness functions.

Pure-Python implementations of Fama-French multifactor regression and
Engle-Granger cointegration testing. OLS regression is implemented
manually via the normal equations (``beta = (X^T X)^-1 X^T y``) with
Gaussian-elimination matrix inversion — no statsmodels / numpy.

Harness functions exposed:

- ``finquant.factors.fama_french``    — 3-factor / 5-factor OLS regression.
- ``finquant.factors.cointegration``  — Engle-Granger cointegration test.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from laap.domain_sdks.finquant.harness.statistics import (
    _matrix_inverse,
    _mean,
    _ols_regression,
    adf_test_sync,
)

logger = logging.getLogger("laap.domain_sdks.finquant.harness.factors")


# ── Helpers ───────────────────────────────────────────────────────


def _truncate_to_shortest(*lists: List[float]) -> Tuple[List[float], ...]:
    """Truncate every list to the length of the shortest one."""
    if not lists:
        return ()
    min_len = min(len(lst) for lst in lists)
    return tuple(lst[:min_len] for lst in lists)


# ── Harness functions ─────────────────────────────────────────────


async def fama_french(
    asset_returns: List[float],
    factor_data: Dict[str, List[float]],
    model: str = "3factor",
) -> Dict[str, Any]:
    """Fama-French multifactor regression via manual OLS.

    Args:
        asset_returns: Excess-return-ready asset returns. ``rf`` is
            subtracted from both the asset and the ``market`` factor
            when ``rf`` is provided.
        factor_data: Dict with keys ``market``, ``smb``, ``hml`` and
            optionally ``rmw``, ``cma``, ``rf``. Each value is a list of
            factor realizations.
        model: ``"3factor"`` (default) or ``"5factor"``.

    Returns:
        Dict with ``betas`` (per factor), ``alpha`` (intercept),
        ``r_squared``, ``residuals``, ``model``.
    """
    if not asset_returns or not factor_data:
        return {
            "betas": {},
            "alpha": 0.0,
            "r_squared": 0.0,
            "residuals": [],
            "model": model,
        }

    market = list(factor_data.get("market", []))
    smb = list(factor_data.get("smb", []))
    hml = list(factor_data.get("hml", []))
    rmw = list(factor_data.get("rmw", []))
    cma = list(factor_data.get("cma", []))
    rf = list(factor_data.get("rf", []))

    if model == "5factor":
        factor_lists = [market, smb, hml, rmw, cma]
        factor_names = ["market", "smb", "hml", "rmw", "cma"]
    else:
        # Default to 3-factor even if model string is unrecognized.
        factor_lists = [market, smb, hml]
        factor_names = ["market", "smb", "hml"]
        if model != "3factor":
            logger.warning("Unknown model '%s'; defaulting to 3factor", model)
            model = "3factor"

    # Subtract risk-free rate from asset returns and market, if provided.
    if rf:
        asset_arr, rf_arr, mkt_arr = _truncate_to_shortest(asset_returns, rf, factor_lists[0])
        excess_asset = [a - r for a, r in zip(asset_arr, rf_arr)]
        excess_mkt = [m - r for m, r in zip(mkt_arr, rf_arr)]
        factor_lists[0] = excess_mkt
        # Truncate remaining factor lists to the same length.
        common_len = len(excess_asset)
        factor_lists = [fl[:common_len] for fl in factor_lists]
        factor_lists[0] = excess_mkt
        y = excess_asset
    else:
        truncated = _truncate_to_shortest(asset_returns, *factor_lists)
        y = list(truncated[0])
        factor_lists = [list(t) for t in truncated[1:]]

    n = len(y)
    if n < len(factor_names) + 2:
        # Not enough observations to estimate parameters reliably.
        return {
            "betas": {name: 0.0 for name in factor_names},
            "alpha": 0.0,
            "r_squared": 0.0,
            "residuals": [],
            "model": model,
        }

    # Build the design matrix X with a leading constant column for the intercept.
    X: List[List[float]] = []
    for i in range(n):
        row: List[float] = [1.0]  # intercept
        for fl in factor_lists:
            row.append(float(fl[i]) if i < len(fl) else 0.0)
        X.append(row)

    betas, residuals, r_squared = _ols_regression(X, y)
    if not betas:
        return {
            "betas": {name: 0.0 for name in factor_names},
            "alpha": 0.0,
            "r_squared": 0.0,
            "residuals": [],
            "model": model,
        }

    alpha = betas[0]
    beta_map = {name: betas[i + 1] for i, name in enumerate(factor_names)}

    return {
        "betas": beta_map,
        "alpha": alpha,
        "r_squared": r_squared,
        "residuals": residuals,
        "model": model,
    }


async def cointegration_test(
    series_a: List[float],
    series_b: List[float],
    method: str = "engle_granger",
) -> Dict[str, Any]:
    """Engle-Granger two-step cointegration test.

    Steps:
        1. OLS regress ``series_a`` on ``series_b`` to obtain the hedge
           ratio and intercept.
        2. Compute the residuals ``a - (intercept + hedge_ratio * b)``.
        3. Run the ADF test on the residuals (via :func:`adf_test_sync`).
        4. Estimate the half-life of mean reversion.
        5. Compute the z-score of the last residual against the residual
           series mean / std.

    Args:
        series_a: Dependent series.
        series_b: Independent series.
        method: Only ``"engle_granger"`` is supported.

    Returns:
        Dict with ``is_cointegrated`` (ADF p < 0.05), ``hedge_ratio``,
        ``intercept``, ``half_life``, ``zscore``, ``adf_pvalue``, ``method``.
    """
    if not series_a or not series_b or method != "engle_granger":
        return {
            "is_cointegrated": False,
            "hedge_ratio": 0.0,
            "intercept": 0.0,
            "half_life": 0.0,
            "zscore": 0.0,
            "adf_pvalue": 1.0,
            "method": method,
        }

    a_trunc, b_trunc = _truncate_to_shortest(series_a, series_b)
    n = len(a_trunc)
    if n < 3:
        return {
            "is_cointegrated": False,
            "hedge_ratio": 0.0,
            "intercept": 0.0,
            "half_life": 0.0,
            "zscore": 0.0,
            "adf_pvalue": 1.0,
            "method": method,
        }

    # Step 1: OLS a = intercept + hedge_ratio * b
    # Closed-form for univariate regression.
    mean_a = _mean(a_trunc)
    mean_b = _mean(b_trunc)
    cov_ab = _mean([(a_trunc[i] - mean_a) * (b_trunc[i] - mean_b) for i in range(n)])
    var_b = _mean([(b_trunc[i] - mean_b) ** 2 for i in range(n)])
    if var_b == 0.0:
        return {
            "is_cointegrated": False,
            "hedge_ratio": 0.0,
            "intercept": mean_a,
            "half_life": 0.0,
            "zscore": 0.0,
            "adf_pvalue": 1.0,
            "method": method,
        }
    hedge_ratio = cov_ab / var_b
    intercept = mean_a - hedge_ratio * mean_b

    # Step 2: residuals
    residuals = [a_trunc[i] - (intercept + hedge_ratio * b_trunc[i]) for i in range(n)]

    # Step 3: ADF on residuals
    adf_result = adf_test_sync(residuals, max_lag=1)
    adf_pvalue = adf_result.get("p_value", 1.0)

    # Step 4: half-life of mean reversion.
    # delta_residuals_t = -revert_speed * residuals_{t-1} + e_t
    # half_life = -ln(2) / ln(1 - revert_speed)   (when revert_speed in (0, 1))
    delta_res = [residuals[i] - residuals[i - 1] for i in range(1, n)]
    lagged_res = residuals[:-1]
    if len(delta_res) >= 2:
        mean_lag = _mean(lagged_res)
        mean_delta = _mean(delta_res)
        cov_lr = _mean([(lagged_res[i] - mean_lag) * (delta_res[i] - mean_delta) for i in range(len(delta_res))])
        var_lr = _mean([(lagged_res[i] - mean_lag) ** 2 for i in range(len(delta_res))])
        revert_speed = -cov_lr / var_lr if var_lr > 0 else 0.0
    else:
        revert_speed = 0.0

    if revert_speed > 0 and revert_speed < 1.0:
        denom = math.log(1.0 - revert_speed)
        half_life = -math.log(2.0) / denom if denom != 0 else 0.0
        # A negative half-life indicates non-mean-reverting — clamp to 0.
        if half_life < 0:
            half_life = 0.0
    else:
        half_life = 0.0

    # Step 5: z-score of the last residual.
    res_mean = _mean(residuals)
    res_var = _mean([(r - res_mean) ** 2 for r in residuals])
    res_std = math.sqrt(res_var) if res_var > 0 else 0.0
    if res_std > 0:
        zscore = (residuals[-1] - res_mean) / res_std
    else:
        zscore = 0.0

    return {
        "is_cointegrated": adf_pvalue < 0.05,
        "hedge_ratio": hedge_ratio,
        "intercept": intercept,
        "half_life": half_life,
        "zscore": zscore,
        "adf_pvalue": adf_pvalue,
        "method": method,
    }
