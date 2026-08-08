"""LAAP FinQuant Domain SDK — Harness functions package.

This subpackage exposes the deterministic, token-free computations that
the FinQuant cognitive actors invoke via tool-calls. Every function is
async and pure-Python (no numpy/pandas/scipy hard dependencies).

Modules:

- ``market_data``  — ``finquant.data.get_ohlcv``
- ``indicators``   — ``finquant.indicators.compute`` / ``detect_regime``
- ``risk``         — ``finquant.risk.var`` / ``stress_test`` / ``kelly_criterion``
- ``factors``      — ``finquant.factors.fama_french`` / ``cointegration``
- ``statistics``   — ``finquant.statistics.zscore_test`` / ``adf_test`` /
                     ``sharpe_ratio`` / ``sortino_ratio`` / ``max_drawdown``
- ``backtest``     — ``finquant.backtest.run``

Use :func:`register_all` to register every FinQuant harness function
into a :class:`laap.domain_sdk.HarnessFunctionRegistry`.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, List, Tuple

from laap.domain_sdks.finquant.harness.backtest import run_backtest
from laap.domain_sdks.finquant.harness.factors import (
    cointegration_test,
    fama_french,
)
from laap.domain_sdks.finquant.harness.indicators import (
    compute_indicators,
    detect_regime,
)
from laap.domain_sdks.finquant.harness.market_data import get_ohlcv
from laap.domain_sdks.finquant.harness.risk import (
    compute_var,
    kelly_criterion,
    stress_test,
)
from laap.domain_sdks.finquant.harness.statistics import (
    adf_test,
    max_drawdown,
    sharpe_ratio,
    sortino_ratio,
    zscore_test,
)

logger = logging.getLogger("laap.domain_sdks.finquant.harness")

# ── (name, fn, description) registry manifest ─────────────────────
#
# Each tuple maps a harness function name to its implementation and a
# human-readable description (used as the LLM tool-call description).

HARNESS_FUNCTIONS: List[Tuple[str, Callable[..., Any], str]] = [
    (
        "finquant.data.get_ohlcv",
        get_ohlcv,
        "Fetch historical OHLCV bars for symbols via auto-selected connector.",
    ),
    (
        "finquant.indicators.compute",
        compute_indicators,
        "Compute technical indicators (sma, ema, rsi, macd, bbands, atr) over OHLCV bars.",
    ),
    (
        "finquant.indicators.detect_regime",
        detect_regime,
        "Classify the price regime (trending / volatile / quiet / mean_reverting).",
    ),
    (
        "finquant.risk.var",
        compute_var,
        "Value-at-Risk (historical / parametric / Monte Carlo) with CVaR.",
    ),
    (
        "finquant.risk.stress_test",
        stress_test,
        "Apply sector-weighted historical scenario shocks to a portfolio.",
    ),
    (
        "finquant.risk.kelly_criterion",
        kelly_criterion,
        "Kelly criterion optimal position sizing (full and fractional).",
    ),
    (
        "finquant.factors.fama_french",
        fama_french,
        "Fama-French 3-factor or 5-factor OLS regression with manual OLS.",
    ),
    (
        "finquant.factors.cointegration",
        cointegration_test,
        "Engle-Granger two-step cointegration test with ADF and half-life.",
    ),
    (
        "finquant.statistics.zscore_test",
        zscore_test,
        "Rolling z-score significance test (|z| > 2 threshold).",
    ),
    (
        "finquant.statistics.adf_test",
        adf_test,
        "Augmented Dickey-Fuller unit-root test with MacKinnon p-values.",
    ),
    (
        "finquant.statistics.sharpe_ratio",
        sharpe_ratio,
        "Annualized Sharpe ratio from a return series.",
    ),
    (
        "finquant.statistics.sortino_ratio",
        sortino_ratio,
        "Annualized Sortino ratio using downside deviation.",
    ),
    (
        "finquant.statistics.max_drawdown",
        max_drawdown,
        "Peak-to-trough maximum drawdown of an equity curve.",
    ),
    (
        "finquant.backtest.run",
        run_backtest,
        "Run an event-driven backtest over OHLCV bars with SMA-crossover default.",
    ),
]


def register_all(registry: Any) -> None:
    """Register every FinQuant harness function into *registry*.

    Args:
        registry: A :class:`laap.domain_sdk.HarnessFunctionRegistry`
            (or any object exposing a compatible ``register`` method).
    """
    for name, fn, description in HARNESS_FUNCTIONS:
        try:
            registry.register(
                name,
                fn=fn,
                zero_token=True,
                description=description,
            )
        except Exception as exc:  # pragma: no cover — defensive
            logger.error("Failed to register harness function %s: %s", name, exc)


__all__ = [
    # Harness functions
    "get_ohlcv",
    "compute_indicators",
    "detect_regime",
    "compute_var",
    "stress_test",
    "kelly_criterion",
    "fama_french",
    "cointegration_test",
    "zscore_test",
    "adf_test",
    "sharpe_ratio",
    "sortino_ratio",
    "max_drawdown",
    "run_backtest",
    # Registry helpers
    "HARNESS_FUNCTIONS",
    "register_all",
]
