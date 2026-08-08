"""LAAP FinQuant Domain SDK — Risk analytics harness functions.

Pure-Python implementations of value-at-risk, stress testing, and
position-sizing (Kelly criterion). No numpy/pandas/scipy — only the
standard library (``math``, ``random``, ``statistics``).

Harness functions exposed:

- ``finquant.risk.var``            — Value-at-Risk (historical / parametric / Monte Carlo).
- ``finquant.risk.stress_test``    — Scenario-based portfolio stress testing.
- ``finquant.risk.kelly_criterion`` — Kelly optimal position sizing.
"""

from __future__ import annotations

import logging
import math
import random
from typing import Any, Dict, List, Optional

logger = logging.getLogger("laap.domain_sdks.finquant.harness.risk")


# ── Helpers ───────────────────────────────────────────────────────


def _mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: List[float], ddof: int = 1) -> float:
    n = len(values)
    if n <= ddof:
        return 0.0
    m = _mean(values)
    var = sum((v - m) ** 2 for v in values) / (n - ddof)
    return math.sqrt(var)


def _percentile(sorted_values: List[float], pct: float) -> float:
    """Linear-interpolation percentile on an already-sorted list. ``pct`` in [0,1]."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    if pct <= 0.0:
        return sorted_values[0]
    if pct >= 1.0:
        return sorted_values[-1]
    k = pct * (len(sorted_values) - 1)
    lo = int(math.floor(k))
    hi = int(math.ceil(k))
    if lo == hi:
        return sorted_values[lo]
    frac = k - lo
    return sorted_values[lo] * (1.0 - frac) + sorted_values[hi] * frac


# ── Scenario shocks (sector-weighted) ─────────────────────────────

# Each scenario maps sector → shock_pct (decimal). The ``"default"`` key
# applies to any sector without an explicit entry.
_SCENARIO_SHOCKS: Dict[str, Dict[str, float]] = {
    "2008_crisis": {
        "financials": -0.35,
        "tech": -0.25,
        "energy": -0.20,
        "consumer": -0.18,
        "industrial": -0.22,
        "default": -0.15,
    },
    "2020_covid": {
        "energy": -0.40,
        "financials": -0.20,
        "tech": -0.05,
        "consumer": -0.12,
        "industrial": -0.18,
        "healthcare": -0.08,
        "default": -0.15,
    },
    "2022_rate_hike": {
        "tech": -0.30,
        "financials": -0.10,
        "energy": 0.10,
        "consumer": -0.15,
        "default": -0.12,
    },
    "flash_crash": {
        "default": -0.10,
    },
}

_DEFAULT_SCENARIOS: List[str] = [
    "2008_crisis",
    "2020_covid",
    "2022_rate_hike",
    "flash_crash",
]


# ── Harness functions ─────────────────────────────────────────────


async def compute_var(
    returns: List[float],
    method: str = "historical",
    confidence: float = 0.95,
    horizon: int = 1,
) -> Dict[str, Any]:
    """Value-at-Risk (VaR) and Conditional VaR (CVaR).

    Args:
        returns: List of periodic portfolio returns (decimals).
        method: One of ``"historical"``, ``"parametric"``, ``"monte_carlo"``.
        confidence: Confidence level in (0, 1) — e.g. 0.95 for 95% VaR.
        horizon: Time horizon in periods. VaR is scaled by ``sqrt(horizon)``.

    Returns:
        Dict with ``var``, ``cvar``, ``method``, ``confidence``, ``horizon``.
        All values are returned as positive numbers representing the loss
        magnitude. On insufficient data returns zeros.
    """
    if not returns or len(returns) < 2 or confidence <= 0 or confidence >= 1:
        return {
            "var": 0.0,
            "cvar": 0.0,
            "method": method,
            "confidence": confidence,
            "horizon": horizon,
        }

    # Filter NaNs / non-finite.
    cleaned = [r for r in returns if isinstance(r, (int, float)) and math.isfinite(r)]
    if len(cleaned) < 2:
        return {
            "var": 0.0,
            "cvar": 0.0,
            "method": method,
            "confidence": confidence,
            "horizon": horizon,
        }

    m = _mean(cleaned)
    s = _std(cleaned, ddof=1)
    scale = math.sqrt(horizon) if horizon > 0 else 1.0

    var_value = 0.0
    cvar_value = 0.0

    if method == "historical":
        sorted_returns = sorted(cleaned)
        # Loss-tail percentile: VaR at 95% = the 5th-percentile return (a loss).
        pct = 1.0 - confidence
        var_return = _percentile(sorted_returns, pct)
        var_value = -var_return  # express as positive loss
        tail = [r for r in sorted_returns if r <= var_return]
        if tail:
            cvar_value = -(_mean(tail))
        else:
            cvar_value = var_value
        # Scale for horizon.
        var_value *= scale
        cvar_value *= scale
    elif method == "parametric":
        # z-scores for common confidence levels.
        z_map = {0.90: 1.282, 0.95: 1.645, 0.99: 2.326}
        z = z_map.get(confidence)
        if z is None:
            # Generic approximation: invert the standard normal CDF via a
            # rational approximation (Abramowitz & Stegun 26.2.23).
            p = 1.0 - confidence
            z = _inv_norm_cdf(p)
        var_return = m - z * s
        var_value = -var_return
        # CVaR (parametric) = mean - (phi(z) / (1 - confidence)) * std
        # where phi is the standard normal PDF. Use an approximation.
        if s > 0:
            pdf_z = math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)
            cvar_return = m - (pdf_z / (1.0 - confidence)) * s
            cvar_value = -cvar_return
        else:
            cvar_value = var_value
        var_value *= scale
        cvar_value *= scale
    elif method == "monte_carlo":
        rng = random.Random(42)
        if s <= 0:
            # No variance — simulate around the mean only.
            simulated = [m + rng.gauss(0.0, 1e-9) for _ in range(10000)]
        else:
            simulated = [rng.gauss(m, s) for _ in range(10000)]
        simulated.sort()
        pct = 1.0 - confidence
        var_return = _percentile(simulated, pct)
        var_value = -var_return
        tail = [r for r in simulated if r <= var_return]
        if tail:
            cvar_value = -(_mean(tail))
        else:
            cvar_value = var_value
        var_value *= scale
        cvar_value *= scale
    else:
        logger.warning("Unknown VaR method: %s", method)
        return {
            "var": 0.0,
            "cvar": 0.0,
            "method": method,
            "confidence": confidence,
            "horizon": horizon,
        }

    return {
        "var": var_value,
        "cvar": cvar_value,
        "method": method,
        "confidence": confidence,
        "horizon": horizon,
    }


def _inv_norm_cdf(p: float) -> float:
    """Approximate inverse standard-normal CDF (Abramowitz & Stegun 26.2.23).

    Accurate to ~1e-4. *p* is a lower-tail probability in (0, 1).
    """
    if p <= 0.0:
        return -10.0
    if p >= 1.0:
        return 10.0
    # Coefficients
    c0 = 2.515517
    c1 = 0.802853
    c2 = 0.010328
    d1 = 1.432788
    d2 = 0.189269
    d3 = 0.001308
    t = math.sqrt(-2.0 * math.log(p))
    numerator = c0 + c1 * t + c2 * t * t
    denominator = 1.0 + d1 * t + d2 * t * t + d3 * t * t * t
    return -(t - numerator / denominator)


async def stress_test(
    positions: List[Dict[str, Any]],
    scenarios: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Apply sector-weighted scenario shocks to a portfolio.

    Args:
        positions: List of dicts ``{"symbol", "quantity", "market_value", "sector"}``.
        scenarios: Scenario names to run. Defaults to all four built-in
            scenarios.

    Returns:
        Dict ``{"scenarios": [...], "worst_case": {"name", "pnl"}}``.
        Each scenario entry is ``{"name", "pnl", "pct_loss"}``.
    """
    if not positions:
        return {"scenarios": [], "worst_case": {"name": "", "pnl": 0.0}}

    scenario_names = scenarios if scenarios else list(_DEFAULT_SCENARIOS)

    total_value = 0.0
    for pos in positions:
        try:
            total_value += float(pos.get("market_value", 0.0))
        except (TypeError, ValueError):
            continue

    if total_value <= 0:
        return {"scenarios": [], "worst_case": {"name": "", "pnl": 0.0}}

    results: List[Dict[str, Any]] = []
    worst_case = {"name": "", "pnl": 0.0}
    worst_pnl = None

    for name in scenario_names:
        shocks = _SCENARIO_SHOCKS.get(name)
        if shocks is None:
            logger.warning("Unknown stress scenario: %s", name)
            continue

        pnl = 0.0
        for pos in positions:
            try:
                mv = float(pos.get("market_value", 0.0))
            except (TypeError, ValueError):
                continue
            sector = (pos.get("sector") or "default").lower()
            shock = shocks.get(sector, shocks.get("default", 0.0))
            pnl += mv * shock

        pct_loss = -pnl / total_value if total_value > 0 else 0.0
        results.append({
            "name": name,
            "pnl": pnl,
            "pct_loss": pct_loss,
        })

        if worst_pnl is None or pnl < worst_pnl:
            worst_pnl = pnl
            worst_case = {"name": name, "pnl": pnl}

    return {"scenarios": results, "worst_case": worst_case}


async def kelly_criterion(
    win_prob: float,
    win_loss_ratio: float,
    fraction: float = 0.5,
) -> Dict[str, Any]:
    """Kelly criterion optimal position sizing.

    Args:
        win_prob: Probability of a winning trade, in (0, 1).
        win_loss_ratio: Ratio of average win to average loss (> 0).
        fraction: Fractional Kelly multiplier in [0, 1] (default 0.5).

    Returns:
        Dict with ``kelly_fraction`` (clamped to [0, 1]), ``suggested_size``
        (``kelly_fraction * fraction``), ``full_kelly``, ``fractional``.

    Raises:
        ValueError: If ``win_prob`` not in (0, 1) or ``win_loss_ratio`` <= 0.
    """
    if not (0.0 < win_prob < 1.0):
        raise ValueError(f"win_prob must be in (0, 1); got {win_prob}")
    if win_loss_ratio <= 0:
        raise ValueError(f"win_loss_ratio must be > 0; got {win_loss_ratio}")

    # Full Kelly: f* = p - (1 - p) / b
    f = win_prob - (1.0 - win_prob) / win_loss_ratio
    # Clamp to [0, 1] — never bet more than 100% or take a negative bet.
    f_clamped = max(0.0, min(1.0, f))
    frac = max(0.0, min(1.0, fraction))
    suggested = f_clamped * frac

    return {
        "kelly_fraction": f_clamped,
        "suggested_size": suggested,
        "full_kelly": f,
        "fractional": frac,
    }
