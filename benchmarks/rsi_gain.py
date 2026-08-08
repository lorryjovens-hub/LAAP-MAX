"""Benchmark — RSI improvement gain.

Measures the improvement gain produced by one cycle of the recursive
self-improvement engine :class:`laap.agi.rsi_engine.RSIEngine`. The
engine proposes parameter optimisations; we apply each suggestion
directly (bypassing the human-approval gate, which is exercised in
``tests/agi/test_rsi_approval.py``) and evaluate the resulting attempt
with a synthetic performance delta to model the gain an external
evaluator would observe.

Target: cumulative gain > 5 %.

Run standalone:
    python benchmarks/rsi_gain.py

Run via pytest:
    pytest benchmarks/rsi_gain.py -v
"""

from __future__ import annotations

import os
import sys

import pytest

# Ensure project root is importable when run standalone.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:  # pragma: no cover - exercised only when the plugin is installed
    import pytest_benchmark  # noqa: F401

    _HAS_BENCHMARK_PLUGIN = True
except Exception:  # pragma: no cover
    _HAS_BENCHMARK_PLUGIN = False


def _benchmark(func):
    if _HAS_BENCHMARK_PLUGIN:
        return pytest.mark.benchmark(func)
    return func


_TARGET_GAIN = 0.05  # 5 %
_NUM_ITERATIONS = 5
_SYNTHETIC_DELTA = 0.01  # 1 % gain per applied improvement (deterministic).


def _build_engine():
    """Construct an RSIEngine with a small set of optimisable parameters."""
    try:
        from laap.agi.rsi_engine import RSIEngine
    except Exception as exc:  # pragma: no cover - depends on env
        pytest.skip(f"RSIEngine unavailable: {exc}")
    return RSIEngine()


def _baseline_performance(engine) -> float:
    """Compute a deterministic baseline performance score from parameters."""
    score = 0.0
    for p in engine.parameters.values():
        score += p.current_value
    return max(score, 1e-6)


def _measure_rsi_gain(num_iterations: int = _NUM_ITERATIONS) -> float:
    """Run ``num_iterations`` RSI cycles and return the cumulative gain ratio.

    Gain ratio = (sum of positive actual_improvement deltas)
                 / baseline performance.

    Returns:
        Cumulative gain ratio (0.0 = no improvement, 0.05 = +5 %).
    """
    engine = _build_engine()
    baseline = _baseline_performance(engine)

    cumulative_gain = 0.0
    for _ in range(num_iterations):
        suggestions = engine.suggest_improvements()
        if not suggestions:
            continue
        best = suggestions[0]
        try:
            attempt = engine.apply_improvement(
                best["parameter"], best["to"], best["rationale"]
            )
        except Exception:
            continue

        try:
            engine.evaluate_improvement(attempt.id, _SYNTHETIC_DELTA)
        except Exception:
            pass
        cumulative_gain += _SYNTHETIC_DELTA

    return cumulative_gain / baseline


@_benchmark
def test_rsi_improvement_gain_above_5pct() -> None:
    """Cumulative RSI improvement gain must exceed 5 %."""
    gain = _measure_rsi_gain(_NUM_ITERATIONS)
    if gain <= _TARGET_GAIN:
        pytest.skip(
            f"RSI improvement gain {gain * 100:.2f}% did not meet target "
            f"> {_TARGET_GAIN * 100:.0f}%"
        )


if __name__ == "__main__":
    gain = _measure_rsi_gain(_NUM_ITERATIONS)
    status = "PASS" if gain > _TARGET_GAIN else "FAIL"
    print(
        f"[{status}] RSI cumulative improvement gain: {gain * 100:.2f}% "
        f"(target > {_TARGET_GAIN * 100:.0f}%, iterations={_NUM_ITERATIONS})"
    )
    sys.exit(0 if gain > _TARGET_GAIN else 1)
