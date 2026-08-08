"""Pytest collection hooks for the benchmarks package.

The M2 D3 benchmark modules are named ``psi_latency.py``, ``memory_retrieval.py``,
``causal_accuracy.py`` and ``rsi_gain.py`` — they do not match pytest's default
``test_*.py`` / ``*_test.py`` file pattern, so we register an explicit
``pytest_collect_file`` hook here to make them discoverable via
``pytest benchmarks/``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# File basenames that should be collected as pytest modules despite not
# matching the default ``test_*.py`` / ``*_test.py`` pattern.
_BENCHMARK_FILES = {
    "psi_latency.py",
    "memory_retrieval.py",
    "causal_accuracy.py",
    "rsi_gain.py",
}


def pytest_collect_file(parent, file_path: Path):
    """Collect the M2 D3 benchmark modules as pytest test modules."""
    if file_path.name in _BENCHMARK_FILES:
        return pytest.Module.from_parent(parent, path=file_path)
    return None
