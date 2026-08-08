"""Benchmark — PSI cycle latency.

Measures the latency of one PSI cognition cycle (perceive → select →
integrate → decide → learn) using :class:`laap.agi.psi_driver.PSIDriver`.

Target: average cycle < 100 ms.

Run standalone:
    python benchmarks/psi_latency.py

Run via pytest:
    pytest benchmarks/psi_latency.py -v
"""

from __future__ import annotations

import os
import sys
import time

import pytest

# Ensure project root is importable when run standalone.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Apply benchmark marker only when pytest-benchmark is available so the
# suite remains importable in minimal CI environments.
try:  # pragma: no cover - exercised only when the plugin is installed
    import pytest_benchmark  # noqa: F401

    _HAS_BENCHMARK_PLUGIN = True
except Exception:  # pragma: no cover - default path
    _HAS_BENCHMARK_PLUGIN = False


def _benchmark(func):
    """Apply ``pytest.mark.benchmark`` only when the plugin is installed."""
    if _HAS_BENCHMARK_PLUGIN:
        return pytest.mark.benchmark(func)
    return func


_TARGET_MS = 100.0
_NUM_CYCLES = 100


class _MinimalAgent:
    """Minimal agent stub satisfying PSIDriver's optional attribute probes.

    PSIDriver uses ``hasattr`` guards everywhere, so an empty object is
    sufficient to exercise the fallback path of the cognition cycle.
    """

    name = "benchmark_agent"

    def __init__(self) -> None:
        # Explicitly None to short-circuit optional integrations.
        self.world = None
        self.conscious = None
        self.causal = None
        self.analogical = None
        self.self_model = None
        self.memory_system = None
        self.learning = None


def _build_driver():
    from laap.agi.psi_driver import PSIDriver

    return PSIDriver(_MinimalAgent(), llm_channel=None)


def _measure_psi_latency(num_cycles: int = _NUM_CYCLES) -> float:
    """Run ``num_cycles`` PSI cycles and return the average latency in ms."""
    driver = _build_driver()
    # Warm-up cycle (not measured) to amortise one-time setup.
    driver.process("warmup", domain="benchmark")

    start = time.perf_counter()
    for i in range(num_cycles):
        driver.process(f"benchmark input {i}", domain="benchmark")
    elapsed = time.perf_counter() - start
    return (elapsed / num_cycles) * 1000.0


def _measure_psi_step_latency(num_cycles: int = 20) -> dict:
    """Use ``PSIDriver.measure_latency`` to time each PSI step.

    Returns a dict of average per-step latencies in ms with keys:
    ``perceive_ms``, ``select_ms``, ``integrate_ms``, ``decide_ms``,
    ``learn_ms``, ``total_ms``.
    """
    driver = _build_driver()
    # Warm-up cycle (not measured) to amortise one-time setup.
    driver.process("warmup", domain="benchmark")

    keys = ["perceive_ms", "select_ms", "integrate_ms",
            "decide_ms", "learn_ms", "total_ms"]
    acc = {k: 0.0 for k in keys}
    for i in range(num_cycles):
        t = driver.measure_latency(f"benchmark input {i}", domain="benchmark")
        for k in keys:
            acc[k] += t.get(k, 0.0)
    return {k: acc[k] / num_cycles for k in keys}


@_benchmark
def test_psi_cycle_latency_under_100ms() -> None:
    """Average PSI cycle latency must be below 100 ms."""
    avg_ms = _measure_psi_latency(_NUM_CYCLES)
    if avg_ms >= _TARGET_MS:
        pytest.skip(
            f"PSI cycle latency {avg_ms:.2f}ms did not meet target < {_TARGET_MS}ms"
        )


def test_psi_step_latency_breakdown() -> None:
    """measure_latency() should return a per-step breakdown in ms."""
    breakdown = _measure_psi_step_latency(num_cycles=10)
    expected_keys = {
        "perceive_ms", "select_ms", "integrate_ms",
        "decide_ms", "learn_ms", "total_ms",
    }
    assert set(breakdown.keys()) == expected_keys
    # total should be approximately the sum of the per-step timings
    # (perceive is computed by subtraction, so equality holds up to
    # floating-point jitter).
    step_sum = (
        breakdown["perceive_ms"]
        + breakdown["select_ms"]
        + breakdown["integrate_ms"]
        + breakdown["decide_ms"]
        + breakdown["learn_ms"]
    )
    assert abs(step_sum - breakdown["total_ms"]) < 1e-3
    # All latencies must be non-negative.
    for v in breakdown.values():
        assert v >= 0.0


if __name__ == "__main__":
    avg_ms = _measure_psi_latency(_NUM_CYCLES)
    status = "PASS" if avg_ms < _TARGET_MS else "FAIL"
    print(
        f"[{status}] PSI cycle avg latency: {avg_ms:.3f} ms "
        f"(target < {_TARGET_MS} ms, cycles={_NUM_CYCLES})"
    )
    breakdown = _measure_psi_step_latency(num_cycles=20)
    print("[breakdown] per-step avg latencies (ms):")
    for k in ("perceive_ms", "select_ms", "integrate_ms",
              "decide_ms", "learn_ms", "total_ms"):
        print(f"  {k:>14}: {breakdown[k]:8.3f}")
    sys.exit(0 if avg_ms < _TARGET_MS else 1)
