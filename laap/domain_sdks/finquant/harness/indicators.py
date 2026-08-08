"""LAAP FinQuant Domain SDK — Technical indicators harness functions.

Pure-Python implementations of common technical indicators. No
numpy/pandas — only the standard library. Each indicator is exposed as a
module-level helper used by the ``compute_indicators`` aggregator.

Harness functions exposed:

- ``finquant.indicators.compute``       — Compute a list of named indicators.
- ``finquant.indicators.detect_regime`` — Classify the price regime.

Supported indicators: ``sma``, ``ema``, ``rsi``, ``macd``, ``bbands``, ``atr``.
Each helper takes a list of close prices (and any required parameters)
and returns a list of the same length (with leading ``None`` values where
the indicator is undefined due to insufficient data).
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional

logger = logging.getLogger("laap.domain_sdks.finquant.harness.indicators")


# ── Helpers ───────────────────────────────────────────────────────


def _to_float(v: Any, default: float = 0.0) -> float:
    """Coerce a value to float; return *default* on failure."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _extract_close(data: List[Any]) -> List[float]:
    """Extract a list of close prices from bar-like dicts."""
    out: List[float] = []
    for bar in data:
        if isinstance(bar, dict):
            if "close" in bar:
                out.append(_to_float(bar.get("close")))
            elif "Close" in bar:
                out.append(_to_float(bar.get("Close")))
            else:
                out.append(0.0)
        else:
            # Assume dataclass / object with .close attribute.
            out.append(_to_float(getattr(bar, "close", 0.0)))
    return out


def _extract_ohlcv(data: List[Any]) -> List[Dict[str, float]]:
    """Normalize bar-like entries to dicts with open/high/low/close/volume."""
    out: List[Dict[str, float]] = []
    for bar in data:
        if isinstance(bar, dict):
            out.append({
                "open": _to_float(bar.get("open", bar.get("Open", 0.0))),
                "high": _to_float(bar.get("high", bar.get("High", 0.0))),
                "low": _to_float(bar.get("low", bar.get("Low", 0.0))),
                "close": _to_float(bar.get("close", bar.get("Close", 0.0))),
                "volume": _to_float(bar.get("volume", bar.get("Volume", 0.0))),
            })
        else:
            out.append({
                "open": _to_float(getattr(bar, "open", 0.0)),
                "high": _to_float(getattr(bar, "high", 0.0)),
                "low": _to_float(getattr(bar, "low", 0.0)),
                "close": _to_float(getattr(bar, "close", 0.0)),
                "volume": _to_float(getattr(bar, "volume", 0.0)),
            })
    return out


# ── Indicator implementations ─────────────────────────────────────


def sma(prices: List[float], period: int = 20) -> List[Optional[float]]:
    """Simple moving average. Leading ``period-1`` values are ``None``."""
    if period <= 0:
        return [None] * len(prices)
    out: List[Optional[float]] = [None] * (period - 1)
    if len(prices) < period:
        return [None] * len(prices)
    window_sum = sum(prices[:period])
    out.append(window_sum / period)
    for i in range(period, len(prices)):
        window_sum += prices[i] - prices[i - period]
        out.append(window_sum / period)
    return out


def ema(prices: List[float], period: int = 20) -> List[Optional[float]]:
    """Exponential moving average.

    ``k = 2/(period+1); ema[i] = price[i]*k + ema[i-1]*(1-k)`` seeded with
    the SMA of the first ``period`` prices.
    """
    if period <= 0 or len(prices) < period:
        return [None] * len(prices)
    k = 2.0 / (period + 1.0)
    out: List[Optional[float]] = [None] * (period - 1)
    seed = sum(prices[:period]) / period
    out.append(seed)
    prev = seed
    for i in range(period, len(prices)):
        cur = prices[i] * k + prev * (1.0 - k)
        out.append(cur)
        prev = cur
    return out


def rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
    """Relative Strength Index (Wilder smoothing).

    Leading ``period`` values are ``None``. Returns values in [0, 100].
    """
    if period <= 0 or len(prices) < period + 1:
        return [None] * len(prices)

    gains: List[float] = []
    losses: List[float] = []
    for i in range(1, period + 1):
        change = prices[i] - prices[i - 1]
        gains.append(max(0.0, change))
        losses.append(max(0.0, -change))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    out: List[Optional[float]] = [None] * period
    if avg_loss == 0.0:
        out.append(100.0)
    else:
        rs = avg_gain / avg_loss
        out.append(100.0 - 100.0 / (1.0 + rs))

    for i in range(period + 1, len(prices)):
        change = prices[i] - prices[i - 1]
        gain = max(0.0, change)
        loss = max(0.0, -change)
        # Wilder smoothing
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        if avg_loss == 0.0:
            out.append(100.0)
        else:
            rs = avg_gain / avg_loss
            out.append(100.0 - 100.0 / (1.0 + rs))
    return out


def macd(
    prices: List[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> Dict[str, List[Optional[float]]]:
    """Moving Average Convergence Divergence.

    Returns a dict with ``macd``, ``signal``, and ``histogram`` lists.
    """
    ema_fast = ema(prices, fast)
    ema_slow = ema(prices, slow)

    macd_line: List[Optional[float]] = []
    for i in range(len(prices)):
        if ema_fast[i] is None or ema_slow[i] is None:
            macd_line.append(None)
        else:
            macd_line.append(ema_fast[i] - ema_slow[i])  # type: ignore[operator]

    # Signal line is an EMA of the macd_line, computed only over the
    # non-None segment.
    first_valid = next((i for i, v in enumerate(macd_line) if v is not None), None)
    if first_valid is None:
        return {
            "macd": macd_line,
            "signal": [None] * len(prices),
            "histogram": [None] * len(prices),
        }

    valid_segment = [v for v in macd_line[first_valid:] if v is not None]  # type: ignore[misc]
    signal_valid = ema(valid_segment, signal) if len(valid_segment) >= signal else [None] * len(valid_segment)

    # Re-align signal to the original timeline.
    signal_line: List[Optional[float]] = [None] * len(prices)
    for idx, sig_val in enumerate(signal_valid):
        signal_line[first_valid + idx] = sig_val

    histogram: List[Optional[float]] = []
    for i in range(len(prices)):
        if macd_line[i] is None or signal_line[i] is None:
            histogram.append(None)
        else:
            histogram.append(macd_line[i] - signal_line[i])  # type: ignore[operator]

    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}


def bbands(
    prices: List[float],
    period: int = 20,
    num_std: float = 2.0,
) -> Dict[str, List[Optional[float]]]:
    """Bollinger Bands (SMA ± ``num_std`` * sample standard deviation)."""
    if period <= 0 or len(prices) < period:
        empty = [None] * len(prices)
        return {"upper": empty, "middle": empty, "lower": empty}

    middle = sma(prices, period)
    upper: List[Optional[float]] = [None] * len(prices)
    lower: List[Optional[float]] = [None] * len(prices)

    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1 : i + 1]
        m = middle[i]
        if m is None:
            continue
        var = sum((p - m) ** 2 for p in window) / period
        sd = math.sqrt(var)
        upper[i] = m + num_std * sd
        lower[i] = m - num_std * sd

    return {"upper": upper, "middle": middle, "lower": lower}


def atr(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    period: int = 14,
) -> List[Optional[float]]:
    """Average True Range (Wilder smoothing)."""
    n = len(closes)
    if period <= 0 or n < period + 1 or len(highs) != n or len(lows) != n:
        return [None] * n

    # True range for t = 1..n-1: max(H-L, |H - prevC|, |L - prevC|)
    tr: List[float] = [0.0] * n
    for i in range(1, n):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        tr[i] = max(hl, hc, lc)

    # First ATR = average of TR[1..period]
    first_atr = sum(tr[1 : period + 1]) / period
    out: List[Optional[float]] = [None] * period
    out.append(first_atr)
    prev = first_atr
    for i in range(period + 1, n):
        cur = (prev * (period - 1) + tr[i]) / period
        out.append(cur)
        prev = cur
    return out


# ── Harness functions ─────────────────────────────────────────────


async def compute_indicators(
    data: List[Any],
    indicators: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute a list of named technical indicators over OHLCV bars.

    Args:
        data: List of bar dicts (or dataclasses) with keys
            ``open, high, low, close, volume``.
        indicators: List of dicts ``{"name": "sma", "period": 20}``.

    Returns:
        Dict ``{"indicators": {name: values_list}}``. Indicator names are
        suffixed with parameters when ambiguous (e.g. ``"sma_20"``).
        Failures for individual indicators yield an empty list rather
        than raising.
    """
    if not data or not indicators:
        return {"indicators": {}}

    ohlcv = _extract_ohlcv(data)
    closes = [bar["close"] for bar in ohlcv]
    highs = [bar["high"] for bar in ohlcv]
    lows = [bar["low"] for bar in ohlcv]

    results: Dict[str, Any] = {}

    for spec in indicators:
        if not isinstance(spec, dict):
            continue
        name = spec.get("name", "")
        if not name:
            continue
        period = int(spec.get("period", 0)) if spec.get("period") is not None else 0

        try:
            if name == "sma":
                p = period if period > 0 else 20
                results[f"sma_{p}"] = sma(closes, p)
            elif name == "ema":
                p = period if period > 0 else 20
                results[f"ema_{p}"] = ema(closes, p)
            elif name == "rsi":
                p = period if period > 0 else 14
                results[f"rsi_{p}"] = rsi(closes, p)
            elif name == "macd":
                fast = int(spec.get("fast", 12))
                slow = int(spec.get("slow", 26))
                sig = int(spec.get("signal", 9))
                res = macd(closes, fast=fast, slow=slow, signal=sig)
                results["macd"] = res
            elif name == "bbands":
                p = period if period > 0 else 20
                ns = float(spec.get("num_std", 2.0))
                results[f"bbands_{p}"] = bbands(closes, period=p, num_std=ns)
            elif name == "atr":
                p = period if period > 0 else 14
                results[f"atr_{p}"] = atr(highs, lows, closes, p)
            else:
                logger.warning("Unknown indicator: %s", name)
                results[name] = []
        except Exception as exc:
            logger.warning("Indicator %s failed: %s", name, exc)
            results[name] = []

    return {"indicators": results}


async def detect_regime(data: List[Any], lookback: int = 60) -> Dict[str, Any]:
    """Classify the price regime over the trailing ``lookback`` bars.

    Regime rules (applied to close prices over the window):

    - ``change_pct`` = (last - first) / first
    - ``volatility`` = std(close) / mean(close)   (coefficient of variation)
    - If ``|change_pct| < 0.02``                     → ``"quiet"``
    - Else if ``|change_pct| > 0.05`` and ``volatility < 0.20`` → ``"trending"``
    - Else if ``volatility > 0.30``                  → ``"volatile"``
    - Else                                           → ``"mean_reverting"``

    Confidence is ``1 - normalized_distance_to_nearest_threshold`` in [0, 1].
    """
    closes = _extract_close(data)
    if not closes or lookback <= 0:
        return {
            "regime": "unknown",
            "confidence": 0.0,
            "change_pct": 0.0,
            "volatility": 0.0,
        }

    window = closes[-lookback:] if len(closes) >= lookback else closes
    if len(window) < 2 or window[0] == 0:
        return {
            "regime": "unknown",
            "confidence": 0.0,
            "change_pct": 0.0,
            "volatility": 0.0,
        }

    first = window[0]
    last = window[-1]
    change_pct = (last - first) / first if first != 0 else 0.0

    mean = sum(window) / len(window)
    var = sum((p - mean) ** 2 for p in window) / len(window)
    std = math.sqrt(var)
    volatility = std / mean if mean != 0 else 0.0

    abs_change = abs(change_pct)
    regime = "mean_reverting"
    confidence = 0.5

    if abs_change < 0.02:
        regime = "quiet"
        # Distance to the 0.02 threshold, normalized.
        confidence = 1.0 - (abs_change / 0.02) if 0.02 > 0 else 1.0
    elif abs_change > 0.05 and volatility < 0.20:
        regime = "trending"
        # Closer to the trending ideal (high change, low vol) → higher confidence.
        change_dist = (abs_change - 0.05) / 0.05 if abs_change < 0.10 else 1.0
        vol_dist = (0.20 - volatility) / 0.20 if 0.20 > 0 else 1.0
        confidence = 0.5 + 0.5 * min(change_dist, vol_dist)
    elif volatility > 0.30:
        regime = "volatile"
        confidence = 1.0 - (0.30 / volatility) if volatility > 0 else 1.0
        confidence = max(0.0, min(1.0, confidence))
    else:
        # mean_reverting: confidence in the "neither trending nor volatile" band.
        # Closer to the center of the [0.02, 0.05] change band.
        if abs_change >= 0.02 and abs_change <= 0.05:
            center = 0.035
            confidence = 1.0 - abs(abs_change - center) / 0.015
        else:
            confidence = 0.3

    confidence = max(0.0, min(1.0, confidence))

    return {
        "regime": regime,
        "confidence": confidence,
        "change_pct": change_pct,
        "volatility": volatility,
    }
