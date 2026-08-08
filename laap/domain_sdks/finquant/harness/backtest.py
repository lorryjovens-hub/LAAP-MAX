"""LAAP FinQuant Domain SDK — Backtest harness function.

Provides the ``finquant.backtest.run`` harness function — a simple
event-driven backtest loop that processes OHLCV bars, applies a signal
function (with a built-in SMA crossover default), simulates fills with
slippage and commission, and produces an equity curve plus performance
metrics.

This is Phase 1 functionality: it is intentionally lightweight (no
portfolio optimization, no rebalancing logic) and is meant to validate
strategy ideas before they enter the paper-trading stage.

Performance metrics (Sharpe, max drawdown) reuse the sync helpers in
:mod:`laap.domain_sdks.finquant.harness.statistics`.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Callable, Dict, List, Optional

from laap.domain_sdks.finquant.harness.statistics import _max_dd_sync, _sharpe_sync

logger = logging.getLogger("laap.domain_sdks.finquant.harness.backtest")


# ── Helpers ───────────────────────────────────────────────────────


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _extract_close(bars: List[Dict[str, Any]]) -> List[float]:
    """Extract close prices from a list of bar dicts."""
    out: List[float] = []
    for bar in bars:
        if isinstance(bar, dict):
            out.append(_to_float(bar.get("close", bar.get("Close", 0.0))))
        else:
            out.append(_to_float(getattr(bar, "close", 0.0)))
    return out


def _sma(values: List[float], period: int) -> Optional[float]:
    """Simple moving average of the last ``period`` values."""
    if len(values) < period or period <= 0:
        return None
    return sum(values[-period:]) / period


def _default_signal(
    closes: List[float],
    fast: int,
    slow: int,
) -> float:
    """Default SMA-crossover target position size in {-1.0, 0.0, 1.0}.

    - Long (1.0) when fast SMA > slow SMA.
    - Flat (0.0) when fast SMA <= slow SMA (no shorts in Phase 1).
    """
    if len(closes) < slow:
        return 0.0
    fast_sma = _sma(closes, fast)
    slow_sma = _sma(closes, slow)
    if fast_sma is None or slow_sma is None:
        return 0.0
    return 1.0 if fast_sma > slow_sma else 0.0


# ── Harness function ──────────────────────────────────────────────


async def run_backtest(
    strategy: Dict[str, Any],
    bars: List[Dict[str, Any]],
    initial_capital: float = 100_000.0,
    commission: float = 0.001,
    slippage_bps: float = 5.0,
) -> Dict[str, Any]:
    """Run a simple event-driven backtest over OHLCV bars.

    Args:
        strategy: Dict ``{"id": str, "params": {...}, "signal_fn": callable}``.
            If ``signal_fn`` is None, an SMA-crossover default is used with
            ``fast`` (default 10) and ``slow`` (default 20) from ``params``.
        bars: List of bar dicts sorted by timestamp, each with at least
            ``timestamp``, ``symbol``, ``open``, ``high``, ``low``,
            ``close``, ``volume``.
        initial_capital: Starting cash.
        commission: Commission per fill as a fraction of notional (0.001 = 10 bps).
        slippage_bps: Slippage applied to fills in basis points.

    Returns:
        Dict with ``equity_curve`` (list of floats), ``trades`` (list of
        trade dicts), ``metrics`` (total_return, sharpe, max_drawdown,
        num_trades, win_rate), and ``final_value``.
    """
    if not bars or not isinstance(strategy, dict):
        return {
            "equity_curve": [initial_capital],
            "trades": [],
            "metrics": {
                "total_return": 0.0,
                "sharpe": 0.0,
                "max_drawdown": 0.0,
                "num_trades": 0,
                "win_rate": 0.0,
            },
            "final_value": initial_capital,
        }

    params = strategy.get("params") or {}
    signal_fn: Optional[Callable[..., float]] = strategy.get("signal_fn")
    fast = int(params.get("fast", 10))
    slow = int(params.get("slow", 20))

    slippage_mult = 1.0 + (slippage_bps / 10_000.0)  # applied on buys
    slippage_disc = 1.0 - (slippage_bps / 10_000.0)  # applied on sells

    cash = float(initial_capital)
    position_size = 0.0  # shares held
    entry_price = 0.0
    equity_curve: List[float] = [cash]
    trades: List[Dict[str, Any]] = []
    closes: List[float] = []
    bar_returns: List[float] = []

    prev_equity = cash

    for idx, bar in enumerate(bars):
        close = _to_float(bar.get("close", 0.0))
        if close <= 0:
            equity_curve.append(prev_equity)
            continue
        closes.append(close)

        # Determine target position via the strategy signal.
        try:
            if signal_fn is not None:
                target = signal_fn(closes, params)
            else:
                target = _default_signal(closes, fast, slow)
        except Exception as exc:
            logger.warning("signal_fn raised at bar %d: %s", idx, exc)
            target = 0.0

        # Coerce target into {-1, 0, 1} (Phase 1: long/flat only).
        if target is None:
            target = 0.0
        target = 1.0 if target > 0 else 0.0

        current_equity = cash + position_size * close

        # Generate fills when the target changes.
        if target > 0 and position_size == 0.0:
            # Enter long: deploy all cash.
            fill_price = close * slippage_mult
            if fill_price > 0 and cash > 0:
                qty = (cash * (1.0 - commission)) / fill_price
                commission_cost = cash * commission
                cash -= commission_cost
                # Buy qty shares at fill_price; reduce cash by qty * fill_price.
                cash -= qty * fill_price
                position_size = qty
                entry_price = fill_price
        elif target == 0.0 and position_size > 0.0:
            # Exit long.
            fill_price = close * slippage_disc
            proceeds = position_size * fill_price
            commission_cost = proceeds * commission
            cash += proceeds - commission_cost
            # Record a closed trade.
            pnl = (fill_price - entry_price) * position_size - commission_cost
            trades.append({
                "entry_bar": _first_entry_bar(trades, idx),
                "exit_bar": idx,
                "entry_price": entry_price,
                "exit_price": fill_price,
                "quantity": position_size,
                "pnl": pnl,
                "return": (fill_price - entry_price) / entry_price if entry_price > 0 else 0.0,
            })
            position_size = 0.0
            entry_price = 0.0

        # Periodic return based on equity change.
        new_equity = cash + position_size * close
        if prev_equity > 0:
            bar_returns.append((new_equity - prev_equity) / prev_equity)
        else:
            bar_returns.append(0.0)
        prev_equity = new_equity
        equity_curve.append(new_equity)

    # Close any remaining position at the last close.
    if position_size > 0.0 and closes:
        last_close = closes[-1]
        fill_price = last_close * slippage_disc
        proceeds = position_size * fill_price
        commission_cost = proceeds * commission
        cash += proceeds - commission_cost
        pnl = (fill_price - entry_price) * position_size - commission_cost
        trades.append({
            "entry_bar": _first_entry_bar(trades, len(bars) - 1),
            "exit_bar": len(bars) - 1,
            "entry_price": entry_price,
            "exit_price": fill_price,
            "quantity": position_size,
            "pnl": pnl,
            "return": (fill_price - entry_price) / entry_price if entry_price > 0 else 0.0,
        })
        position_size = 0.0
        # Update the last equity curve point.
        equity_curve[-1] = cash

    final_value = cash + position_size * (closes[-1] if closes else 0.0)

    # Metrics.
    total_return = (final_value - initial_capital) / initial_capital if initial_capital > 0 else 0.0
    sharpe_result = _sharpe_sync(bar_returns, risk_free_rate=0.0, annualization=252)
    sharpe = sharpe_result.get("sharpe", 0.0)
    dd_result = _max_dd_sync(equity_curve)
    max_dd = dd_result.get("max_drawdown", 0.0)

    num_trades = len(trades)
    if num_trades > 0:
        wins = sum(1 for t in trades if t.get("pnl", 0.0) > 0)
        win_rate = wins / num_trades
    else:
        win_rate = 0.0

    return {
        "equity_curve": equity_curve,
        "trades": trades,
        "metrics": {
            "total_return": total_return,
            "sharpe": sharpe,
            "max_drawdown": max_dd,
            "num_trades": num_trades,
            "win_rate": win_rate,
        },
        "final_value": final_value,
    }


def _first_entry_bar(trades: List[Dict[str, Any]], default: int) -> int:
    """Return the bar index just after the last recorded exit, or 0."""
    if not trades:
        return 0
    last_exit = trades[-1].get("exit_bar", 0)
    return last_exit + 1
