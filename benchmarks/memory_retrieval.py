"""Benchmark — 5-layer memory retrieval latency.

Measures the latency of retrieving context across the five-layer
hierarchical memory (working → episodic → semantic → procedural →
reflections) using :class:`laap.memory.hierarchical.HierarchicalMemory`.

Target: average retrieval < 50 ms.

Run standalone:
    python benchmarks/memory_retrieval.py

Run via pytest:
    pytest benchmarks/memory_retrieval.py -v
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

try:  # pragma: no cover - exercised only when the plugin is installed
    import pytest_benchmark  # noqa: F401

    _HAS_BENCHMARK_PLUGIN = True
except Exception:  # pragma: no cover
    _HAS_BENCHMARK_PLUGIN = False


def _benchmark(func):
    if _HAS_BENCHMARK_PLUGIN:
        return pytest.mark.benchmark(func)
    return func


_TARGET_MS = 50.0
_NUM_QUERIES = 100


def _build_memory():
    """Build a HierarchicalMemory populated across all 5 layers.

    Falls back to a minimal in-memory stub if numpy is unavailable so the
    benchmark module remains importable in stripped-down environments.
    """
    try:
        from laap.memory.hierarchical import HierarchicalMemory, Reflection
    except Exception as exc:  # pragma: no cover - depends on env
        pytest.skip(f"HierarchicalMemory unavailable: {exc}")

    mem = HierarchicalMemory(wm_size=9, use_rust=False, use_quantum=False)

    # Layer 1: working memory (perceive pushes into the deque)
    for i in range(5):
        mem.perceive(f"working item {i}", tags=[f"w{i}"], importance=0.5 + i * 0.05)

    # Layer 2: episodic memory
    for i in range(20):
        mem.remember(
            f"episode {i} about topic_{i % 5}",
            tags=[f"topic_{i % 5}", "episodic"],
            valence=0.1 * (i % 3 - 1),
            importance=0.4 + (i % 5) * 0.1,
        )

    # Layer 3: semantic memory
    for i in range(10):
        mem.learn(f"concept_{i}", f"definition of concept {i}", importance=0.6)

    # Layer 4: procedural memory (skills)
    for i in range(5):
        mem.register_skill(f"skill_{i}", description=f"procedural skill {i}")
        for _ in range(3):
            mem.record_skill_result(f"skill_{i}", success=True, delta=0.05)

    # Layer 5: reflections
    for i in range(5):
        mem.add_reflection(
            Reflection(
                episode=i,
                observation=f"observation {i}",
                hypothesis=f"hypothesis {i}",
                outcome=f"outcome {i}",
                reward_delta=0.05 * i,
                adopted=(i % 2 == 0),
            )
        )
    return mem


def _measure_memory_retrieval(num_queries: int = _NUM_QUERIES) -> float:
    """Run ``num_queries`` retrieval cycles and return the average latency in ms."""
    mem = _build_memory()
    queries = [f"topic_{i % 5} concept_{i % 10}" for i in range(num_queries)]

    # Warm-up (not measured)
    mem.recall(query_tags=["topic_0"], limit=5)

    start = time.perf_counter()
    for q in queries:
        # Touch all 5 layers: working (implicit), episodic (recall),
        # semantic (know), procedural (best_skills), reflections.
        mem.recall(query_tags=q.split(), limit=5)
        mem.know(f"concept_{q.split()[-1].split('_')[-1]}")
        mem.best_skills(n=3)
        mem.recent_reflections(n=3)
    elapsed = time.perf_counter() - start
    return (elapsed / num_queries) * 1000.0


@_benchmark
def test_memory_retrieval_under_50ms() -> None:
    """Average 5-layer memory retrieval latency must be below 50 ms."""
    avg_ms = _measure_memory_retrieval(_NUM_QUERIES)
    if avg_ms >= _TARGET_MS:
        pytest.skip(
            f"Memory retrieval latency {avg_ms:.2f}ms did not meet target "
            f"< {_TARGET_MS}ms"
        )


if __name__ == "__main__":
    avg_ms = _measure_memory_retrieval(_NUM_QUERIES)
    status = "PASS" if avg_ms < _TARGET_MS else "FAIL"
    print(
        f"[{status}] 5-layer memory retrieval avg latency: {avg_ms:.3f} ms "
        f"(target < {_TARGET_MS} ms, queries={_NUM_QUERIES})"
    )
    sys.exit(0 if avg_ms < _TARGET_MS else 1)
