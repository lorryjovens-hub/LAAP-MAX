"""LAAP FinQuant Domain SDK — Statistical harness functions.

Pure-Python statistical computations used by the FinQuant harness layer.
All functions are deterministic, token-free, and avoid numpy/pandas/scipy
dependencies — only the standard library is used.

Harness functions exposed (registered under ``finquant.statistics.*``):

- ``finquant.statistics.zscore_test``      — Rolling z-score significance test.
- ``finquant.statistics.adf_test``          — Augmented Dickey-Fuller unit-root test.
- ``finquant.statistics.sharpe_ratio``      — Annualized Sharpe ratio.
- ``finquant.statistics.sortino_ratio``     — Annualized Sortino ratio.
- ``finquant.statistics.max_drawdown``      — Peak-to-trough drawdown.

Sync helper variants (``*_sync``) are exposed for reuse by other harness
modules (backtest, factors) that already run inside an event loop and
cannot ``await`` an async coroutine without recursion.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("laap.domain_sdks.finquant.harness.statistics")


# ── Internal helpers ──────────────────────────────────────────────


def _mean(values: List[float]) -> float:
    """Arithmetic mean. Returns 0.0 for empty input."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def _variance(values: List[float], ddof: int = 0) -> float:
    """Population (ddof=0) or sample (ddof=1) variance. 0.0 for empty input."""
    n = len(values)
    if n <= ddof:
        return 0.0
    m = _mean(values)
    return sum((v - m) ** 2 for v in values) / (n - ddof)


def _std(values: List[float], ddof: int = 0) -> float:
    """Standard deviation (population by default)."""
    return math.sqrt(_variance(values, ddof=ddof))


def _percentile(sorted_values: List[float], pct: float) -> float:
    """Linear-interpolation percentile on an already-sorted list.

    ``pct`` is in [0, 1]. Returns 0.0 for empty input.
    """
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    if pct <= 0.0:
        return sorted_values[0]
    if pct >= 1.0:
        return sorted_values[-1]
    # Linear interpolation between adjacent order statistics.
    k = pct * (len(sorted_values) - 1)
    lo = int(math.floor(k))
    hi = int(math.ceil(k))
    if lo == hi:
        return sorted_values[lo]
    frac = k - lo
    return sorted_values[lo] * (1.0 - frac) + sorted_values[hi] * frac


# ── OLS regression helper (used by adf_test) ──────────────────────


def _ols_regression(X: List[List[float]], y: List[float]) -> Tuple[List[float], List[float], float]:
    """Ordinary least squares via normal equations.

    Solves ``beta = (X^T X)^-1 X^T y`` using Gaussian elimination.
    Returns (coefficients, residuals, r_squared).

    Args:
        X: Design matrix as list of rows (each row is a list of features).
        y: Dependent variable observations.

    Returns:
        Tuple of (betas, residuals, r_squared). On singular matrix or
        shape mismatch, returns zero-length lists / 0.0.
    """
    n = len(y)
    if n == 0 or len(X) != n:
        return [], [], 0.0
    k = len(X[0]) if X else 0
    if k == 0:
        return [], [], 0.0

    # X^T X  (k x k)
    XtX = [[0.0] * k for _ in range(k)]
    for i in range(k):
        for j in range(k):
            s = 0.0
            for r in range(n):
                s += X[r][i] * X[r][j]
            XtX[i][j] = s

    # X^T y  (k)
    Xty = [0.0] * k
    for i in range(k):
        s = 0.0
        for r in range(n):
            s += X[r][i] * y[r]
        Xty[i] = s

    betas = _solve_linear_system(XtX, Xty)
    if not betas:
        # Singular — fall back to zero coefficients so callers can degrade gracefully.
        betas = [0.0] * k

    # Predictions and residuals
    residuals = []
    for r in range(n):
        pred = sum(X[r][j] * betas[j] for j in range(k))
        residuals.append(y[r] - pred)

    # R^2 = 1 - SS_res / SS_tot
    y_mean = _mean(y)
    ss_res = sum((res) ** 2 for res in residuals)
    ss_tot = sum((yi - y_mean) ** 2 for yi in y)
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    return betas, residuals, r_squared


def _solve_linear_system(A: List[List[float]], b: List[float]) -> List[float]:
    """Solve ``A x = b`` via Gaussian elimination with partial pivoting.

    Returns an empty list if the matrix is singular.
    """
    n = len(A)
    if n == 0 or len(b) != n:
        return []
    # Build augmented matrix [A | b]
    M = [list(A[i]) + [b[i]] for i in range(n)]

    for col in range(n):
        # Partial pivot: find row with max |A[row][col]|
        pivot_row = col
        max_abs = abs(M[col][col])
        for r in range(col + 1, n):
            if abs(M[r][col]) > max_abs:
                max_abs = abs(M[r][col])
                pivot_row = r
        if max_abs < 1e-12:
            return []  # singular
        if pivot_row != col:
            M[col], M[pivot_row] = M[pivot_row], M[col]

        # Eliminate below
        pivot = M[col][col]
        for r in range(col + 1, n):
            factor = M[r][col] / pivot
            if factor == 0.0:
                continue
            for c in range(col, n + 1):
                M[r][c] -= factor * M[col][c]

    # Back-substitution
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = M[i][n]
        for j in range(i + 1, n):
            s -= M[i][j] * x[j]
        x[i] = s / M[i][i]
    return x


def _t_statistic(coef: float, resid_std: float, XtX_inv_diag: float, n: int, k: int) -> float:
    """Compute t-statistic for an OLS coefficient.

    Args:
        coef: The estimated coefficient.
        resid_std: Standard error of the regression residuals.
        XtX_inv_diag: Diagonal element of (X^T X)^-1 corresponding to the coef.
        n: Number of observations.
        k: Number of regressors.

    Returns:
        t-statistic. Returns 0.0 if undefined.
    """
    if n <= k or resid_std <= 0 or XtX_inv_diag <= 0:
        return 0.0
    se = resid_std * math.sqrt(XtX_inv_diag)
    if se == 0.0:
        return 0.0
    return coef / se


def _matrix_inverse(A: List[List[float]]) -> List[List[float]]:
    """Invert a square matrix via Gauss-Jordan elimination.

    Returns an empty list if A is singular.
    """
    n = len(A)
    if n == 0:
        return []
    # Augment with identity
    M = [list(A[i]) + [1.0 if j == i else 0.0 for j in range(n)] for i in range(n)]

    for col in range(n):
        pivot_row = col
        max_abs = abs(M[col][col])
        for r in range(col + 1, n):
            if abs(M[r][col]) > max_abs:
                max_abs = abs(M[r][col])
                pivot_row = r
        if max_abs < 1e-12:
            return []
        if pivot_row != col:
            M[col], M[pivot_row] = M[pivot_row], M[col]

        pivot = M[col][col]
        for c in range(2 * n):
            M[col][c] /= pivot

        for r in range(n):
            if r == col:
                continue
            factor = M[r][col]
            if factor == 0.0:
                continue
            for c in range(2 * n):
                M[r][c] -= factor * M[col][c]

    return [row[n:] for row in M]


# ── Sync helper variants (used by backtest / factors internally) ──


def adf_test_sync(series: List[float], max_lag: int = 1) -> Dict[str, Any]:
    """Synchronous Augmented Dickey-Fuller test (Engle-Granger variant).

    Implements the ADF regression::

        delta_y_t = alpha + beta * y_{t-1} + sum_{i=1..lag} gamma_i * delta_y_{t-i} + e_t

    The ADF statistic is the t-statistic on ``beta`` (coefficient of the
    lagged level). MacKinnon (1994) approximate critical values are used
    to derive a one-sided p-value.

    Args:
        series: Time series of floats (must have length > max_lag + 2).
        max_lag: Number of lagged differences to include.

    Returns:
        Dict with ``adf_statistic``, ``p_value``, ``is_stationary``, ``lag``.
    """
    n = len(series)
    # Need at least max_lag + 3 points to form one observation.
    if n < max_lag + 3 or max_lag < 0:
        return {
            "adf_statistic": 0.0,
            "p_value": 1.0,
            "is_stationary": False,
            "lag": max_lag,
        }

    # First differences delta_y_t = y_t - y_{t-1}
    delta = [series[i] - series[i - 1] for i in range(1, n)]

    # Build regression rows. The first usable observation is t = max_lag + 1
    # (so that we have y_{t-1} and delta_y_{t-1} ... delta_y_{t-lag}).
    X: List[List[float]] = []
    y: List[float] = []
    for t in range(max_lag, len(delta)):
        # y_{t-1} = series[t]   (since delta[t] corresponds to series[t+1] - series[t])
        y_lag1 = series[t]
        row: List[float] = [y_lag1]
        for lag in range(1, max_lag + 1):
            row.append(delta[t - lag])
        row.append(1.0)  # constant term
        X.append(row)
        y.append(delta[t])

    if len(X) < 2:
        return {
            "adf_statistic": 0.0,
            "p_value": 1.0,
            "is_stationary": False,
            "lag": max_lag,
        }

    betas, residuals, _ = _ols_regression(X, y)
    if not betas:
        return {
            "adf_statistic": 0.0,
            "p_value": 1.0,
            "is_stationary": False,
            "lag": max_lag,
        }

    # The coefficient on y_{t-1} is the first beta.
    beta = betas[0]

    # Residual standard error: sqrt(SSR / (n - k))
    n_obs = len(y)
    k_params = len(betas)
    ssr = sum(r * r for r in residuals)
    resid_var = ssr / (n_obs - k_params) if n_obs > k_params else 0.0
    resid_std = math.sqrt(resid_var) if resid_var > 0 else 0.0

    # Compute (X^T X)^-1 diagonal for the standard error of beta.
    XtX = [[0.0] * k_params for _ in range(k_params)]
    for i in range(k_params):
        for j in range(k_params):
            s = 0.0
            for r in range(n_obs):
                s += X[r][i] * X[r][j]
            XtX[i][j] = s
    XtX_inv = _matrix_inverse(XtX)
    if not XtX_inv:
        adf_stat = 0.0
    else:
        se = resid_std * math.sqrt(XtX_inv[0][0]) if resid_std > 0 and XtX_inv[0][0] > 0 else 0.0
        adf_stat = beta / se if se > 0 else 0.0

    # MacKinnon (1994) approximate critical values for the ADF t-statistic
    # (one-sided, asymptotic). 1%: -3.43, 5%: -2.86, 10%: -2.57.
    if adf_stat < -3.43:
        p_value = 0.01
    elif adf_stat < -2.86:
        p_value = 0.05
    elif adf_stat < -2.57:
        p_value = 0.10
    else:
        p_value = 1.0

    return {
        "adf_statistic": adf_stat,
        "p_value": p_value,
        "is_stationary": p_value < 0.05,
        "lag": max_lag,
    }


def _sharpe_sync(returns: List[float], risk_free_rate: float = 0.0, annualization: int = 252) -> Dict[str, Any]:
    """Synchronous Sharpe ratio computation."""
    if not returns or len(returns) < 2 or annualization <= 0:
        return {"sharpe": 0.0, "annualization": annualization, "risk_free_rate": risk_free_rate}
    rf_period = risk_free_rate / annualization
    excess = [r - rf_period for r in returns]
    mean_excess = _mean(excess)
    std_excess = _std(excess, ddof=1)
    if std_excess == 0.0:
        return {"sharpe": 0.0, "annualization": annualization, "risk_free_rate": risk_free_rate}
    sharpe = (mean_excess / std_excess) * math.sqrt(annualization)
    return {"sharpe": sharpe, "annualization": annualization, "risk_free_rate": risk_free_rate}


def _sortino_sync(returns: List[float], risk_free_rate: float = 0.0, annualization: int = 252) -> Dict[str, Any]:
    """Synchronous Sortino ratio computation."""
    if not returns or len(returns) < 2 or annualization <= 0:
        return {"sortino": 0.0, "annualization": annualization, "downside_std": 0.0}
    rf_period = risk_free_rate / annualization
    excess = [r - rf_period for r in returns]
    mean_excess = _mean(excess)
    downside = [min(0.0, r - rf_period) for r in returns]
    downside_var = _mean([d * d for d in downside])  # population-style downside variance
    downside_std = math.sqrt(downside_var) if downside_var > 0 else 0.0
    if downside_std == 0.0:
        return {"sortino": 0.0, "annualization": annualization, "downside_std": 0.0}
    sortino = (mean_excess / downside_std) * math.sqrt(annualization)
    return {"sortino": sortino, "annualization": annualization, "downside_std": downside_std}


def _max_dd_sync(equity_curve: List[float]) -> Dict[str, Any]:
    """Synchronous max drawdown computation."""
    if not equity_curve:
        return {
            "max_drawdown": 0.0,
            "peak_idx": 0,
            "trough_idx": 0,
            "peak_value": 0.0,
            "trough_value": 0.0,
        }

    peak_idx = 0
    peak_value = equity_curve[0]
    max_dd = 0.0
    max_dd_peak_idx = 0
    max_dd_trough_idx = 0
    max_dd_peak_value = peak_value
    max_dd_trough_value = peak_value

    for i, v in enumerate(equity_curve):
        if v > peak_value:
            peak_value = v
            peak_idx = i
        if peak_value > 0:
            dd = (peak_value - v) / peak_value
        else:
            dd = 0.0
        if dd > max_dd:
            max_dd = dd
            max_dd_peak_idx = peak_idx
            max_dd_trough_idx = i
            max_dd_peak_value = peak_value
            max_dd_trough_value = v

    return {
        "max_drawdown": max_dd,
        "peak_idx": max_dd_peak_idx,
        "trough_idx": max_dd_trough_idx,
        "peak_value": max_dd_peak_value,
        "trough_value": max_dd_trough_value,
    }


# ── Harness functions (async) ─────────────────────────────────────


async def zscore_test(values: List[float], window: int = 20) -> Dict[str, Any]:
    """Rolling z-score significance test on the last ``window`` values.

    Args:
        values: List of numeric observations.
        window: Rolling window size (default 20).

    Returns:
        Dict with ``zscore`` (last point), ``is_significant`` (|z| > 2),
        ``mean``, ``std``, ``window``.
    """
    if not values or window <= 0:
        return {
            "zscore": 0.0,
            "is_significant": False,
            "mean": 0.0,
            "std": 0.0,
            "window": window,
        }

    sample = values[-window:] if len(values) >= window else values
    if len(sample) < 2:
        return {
            "zscore": 0.0,
            "is_significant": False,
            "mean": sample[0] if sample else 0.0,
            "std": 0.0,
            "window": window,
        }

    m = _mean(sample)
    s = _std(sample, ddof=1)
    last = sample[-1]
    if s == 0.0:
        z = 0.0
    else:
        z = (last - m) / s
    return {
        "zscore": z,
        "is_significant": abs(z) > 2.0,
        "mean": m,
        "std": s,
        "window": window,
    }


async def adf_test(series: List[float], max_lag: int = 1) -> Dict[str, Any]:
    """Augmented Dickey-Fuller unit-root test.

    See :func:`adf_test_sync` for implementation details. This is the
    async harness wrapper.
    """
    return adf_test_sync(series, max_lag=max_lag)


async def sharpe_ratio(
    returns: List[float],
    risk_free_rate: float = 0.0,
    annualization: int = 252,
) -> Dict[str, Any]:
    """Annualized Sharpe ratio.

    ``Sharpe = (mean(r) - rf/period) / std(r) * sqrt(annualization)``.
    """
    return _sharpe_sync(returns, risk_free_rate=risk_free_rate, annualization=annualization)


async def sortino_ratio(
    returns: List[float],
    risk_free_rate: float = 0.0,
    annualization: int = 252,
) -> Dict[str, Any]:
    """Annualized Sortino ratio (uses downside deviation only)."""
    return _sortino_sync(returns, risk_free_rate=risk_free_rate, annualization=annualization)


async def max_drawdown(equity_curve: List[float]) -> Dict[str, Any]:
    """Peak-to-trough maximum drawdown of an equity curve."""
    return _max_dd_sync(equity_curve)
