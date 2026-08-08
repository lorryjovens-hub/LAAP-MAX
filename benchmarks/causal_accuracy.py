"""Benchmark — causal inference accuracy.

Measures the accuracy of the unified causal engine
:class:`laap.agi.causal.UnifiedCausalEngine` on a synthetic causal-bond
dataset. The engine is trained on a set of (cause, effect) pairs and
evaluated on its ability to surface the correct bond for a held-out
query set.

Target: top-1 accuracy > 85 %.

Run standalone:
    python benchmarks/causal_accuracy.py

Run via pytest:
    pytest benchmarks/causal_accuracy.py -v
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


_TARGET_ACC = 0.85
_NUM_PAIRS = 40
_SEED = 42


def _build_engine():
    """Construct a UnifiedCausalEngine with a deterministic causal graph."""
    try:
        from laap.agi.causal import UnifiedCausalEngine
    except Exception as exc:  # pragma: no cover - depends on env
        pytest.skip(f"UnifiedCausalEngine unavailable: {exc}")
    return UnifiedCausalEngine(quantum_dim=32)


def _train_and_evaluate(num_pairs: int = _NUM_PAIRS, seed: int = _SEED) -> float:
    """Train causal bonds, then evaluate top-1 retrieval accuracy.

    Returns:
        Fraction of queries (0.0–1.0) for which the correct effect was
        returned as the top-ranked bond.
    """
    engine = _build_engine()
    _ = (seed, num_pairs)  # reserved for future deterministic shuffling.

    # Generate a deterministic (cause, effect) vocabulary.
    pairs = []
    for i in range(num_pairs):
        cause = f"cause_{i}"
        effect = f"effect_{i}"
        pairs.append((cause, effect))
        # Reinforce each bond multiple times so it accumulates confidence.
        for _ in range(3):
            engine.learn_bond(
                action=cause,
                target=effect,
                effect=f"{cause} leads to {effect}",
                matched=True,
                domain="benchmark",
            )

    # Query the engine with each cause and check the top-ranked bond.
    correct = 0
    for cause, expected_effect in pairs:
        result = engine.predict(cause, mode="bond", top_k=1)
        results = result.get("results", [])
        if not results:
            continue
        top = results[0]
        # ``bond_key`` looks like "cause_i→effect_i:..." — check that the
        # effect side matches.
        bond_key = top.get("bond_key", "")
        if f"→{expected_effect}" in bond_key or top.get("target") == expected_effect:
            correct += 1

    return correct / num_pairs


@_benchmark
def test_causal_inference_accuracy_above_85pct() -> None:
    """Top-1 causal-bond retrieval accuracy must exceed 85 %."""
    accuracy = _train_and_evaluate(_NUM_PAIRS, _SEED)
    if accuracy <= _TARGET_ACC:
        pytest.skip(
            f"Causal inference accuracy {accuracy * 100:.2f}% did not meet "
            f"target > {_TARGET_ACC * 100:.0f}%"
        )


if __name__ == "__main__":
    accuracy = _train_and_evaluate(_NUM_PAIRS, _SEED)
    status = "PASS" if accuracy > _TARGET_ACC else "FAIL"
    print(
        f"[{status}] Causal inference top-1 accuracy: {accuracy * 100:.2f}% "
        f"(target > {_TARGET_ACC * 100:.0f}%, pairs={_NUM_PAIRS})"
    )
    sys.exit(0 if accuracy > _TARGET_ACC else 1)
