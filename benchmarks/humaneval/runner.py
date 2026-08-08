"""HumanEval benchmark runner — scaffold.

The full HumanEval dataset (164 hand-written programming problems with
unit tests) is released by OpenAI as a JSONL file. Downloading and
distributing it from this repo would balloon the install footprint and
raise licensing concerns; this runner therefore exposes a clean
``run_humaneval`` API that downstream callers can plug a dataset into.

TODO(dataset integration):
    - Vendor or download ``HumanEval.jsonl`` from
      https://github.com/openai/human-eval
    - Convert each task to ``(prompt: str, canonical_tests: str)``
    - Pass them to ``agent_callable(prompt)`` and assert the produced
      code passes ``exec(canonical_tests, globals())``.
    - For now ``run_humaneval`` returns zeros with a ``"stub": True``
      marker so CI can detect a non-integrated run.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("laap.benchmarks.humaneval")


def run_humaneval(
    agent_callable: Callable[[str], str],
    num_samples: int = 10,
) -> dict[str, Any]:
    """Run the HumanEval benchmark against ``agent_callable``.

    Args:
        agent_callable: A function ``prompt -> generated_code``. The
            generated code is expected to complete the prompt so that the
            canonical unit tests pass when the concatenation is exec'd.
        num_samples: Number of completions to sample per task for
            pass@k computation (k ∈ {1, 5, 10}).

    Returns:
        A dict with the keys ``pass@1``, ``pass@5``, ``pass@10``,
        ``num_samples``, ``num_tasks``, and ``stub``.

    TODO: integrate the actual HumanEval dataset. Until then this is a
    scaffold that returns zeros and ``stub=True`` so callers can detect
    a non-integrated run without crashing.
    """
    if not callable(agent_callable):
        raise TypeError("agent_callable must be callable(prompt) -> code")

    if num_samples <= 0:
        raise ValueError("num_samples must be positive")

    logger.warning(
        "run_humaneval: dataset not integrated — returning zeroed stub "
        "metrics. See module docstring for integration TODO."
    )

    return {
        "pass@1": 0.0,
        "pass@5": 0.0,
        "pass@10": 0.0,
        "num_samples": num_samples,
        "num_tasks": 0,
        "stub": True,
    }


def compute_pass_at_k(n: int, c: int, k: int) -> float:
    """Numerically-stable pass@k (Chen et al. 2021, Eq. 1).

    Args:
        n: total samples drawn.
        c: number of samples that passed.
        k: k for pass@k.

    Returns:
        pass@k ∈ [0.0, 1.0]. ``1.0`` if ``n - c < k`` (every k-subset
        is guaranteed to contain a pass), else ``1 - C(n-c, k)/C(n, k)``.
    """
    if n - c < k:
        return 1.0
    if k > n:
        return 0.0
    # 1 - prod_{i=n-c+1}^{n} (1 - k/i)
    result = 1.0
    for i in range(n - c + 1, n + 1):
        result *= 1.0 - k / i
    return 1.0 - result
