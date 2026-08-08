"""Tests for LLM-as-a-Verifier integration."""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from laap.verification import LLMVerifier, VerifierConfig


def test_score_tokens_match_granularity():
    verifier = LLMVerifier(VerifierConfig(granularity=20, mock=True))
    assert len(verifier._score_tokens) == 20
    assert verifier._score_tokens["A"] == 1 / 20
    assert verifier._score_tokens["T"] == 1.0


def test_mock_score_good_candidate():
    config = VerifierConfig(granularity=20, n_verifications=2, mock=True)
    verifier = LLMVerifier(config)
    result = verifier.score_sync(
        task="Implement a safe add function",
        candidate="def add(a, b): return a + b  # safe and correct",
    )
    assert 0.0 <= result.score <= 1.0
    assert set(result.criteria_scores.keys()) == set(config.criteria)
    assert result.calls == len(config.criteria) * config.n_verifications
    assert result.logprobs is not None


def test_mock_score_bad_candidate():
    config = VerifierConfig(granularity=20, n_verifications=2, mock=True)
    verifier = LLMVerifier(config)
    result = verifier.score_sync(
        task="Implement a safe add function",
        candidate="unsafe bad error: os.system('rm -rf /')",
    )
    assert result.score < 0.5


def test_compare_selects_better_candidate():
    verifier = LLMVerifier(VerifierConfig(granularity=20, mock=True))
    winner, details = verifier.compare_sync(
        task="Sort a list",
        candidate_a="def sort(xs): return sorted(xs)  # correct",
        candidate_b="bad error: return None",
    )
    assert "correct" in winner
    assert details["winner_score"] > details["loser_score"]


def test_select_best_of_n():
    verifier = LLMVerifier(VerifierConfig(granularity=20, mock=True))
    candidates = [
        "bad unsafe error",
        "partial ok solution",
        "correct safe good solution",
    ]
    best, details = verifier.select_sync(
        task="Return sum of two numbers",
        candidates=candidates,
    )
    assert "good" in best
    # With 3 candidates there are 3 matches; the best candidate plays in 2.
    assert details["wins"] == len(candidates) - 1
    assert details["matches"] == 3


def test_normalization_over_allowed_tokens():
    verifier = LLMVerifier(VerifierConfig(granularity=5, mock=True))
    raw = {"A": -0.5, "B": -0.2, "C": 0.0, "X": -0.1}
    probs = verifier._normalize_logprobs(raw)
    assert abs(sum(probs.values()) - 1.0) < 1e-6
    assert "X" not in probs
    assert set(probs.keys()) == set(verifier._score_tokens.keys())


def test_expected_score_computation():
    verifier = LLMVerifier(VerifierConfig(granularity=4, mock=True))
    probs = {"A": 0.25, "B": 0.25, "C": 0.25, "D": 0.25}
    expected = verifier._expected_score(probs)
    # Values: A=0.25, B=0.5, C=0.75, D=1.0 -> average = 0.625
    assert abs(expected - 0.625) < 1e-6


def test_aevo_harness_with_verifier_picks_higher_quality():
    from laap.evolution.aevo import EvolutionHarness, ProtectedEvaluator
    from laap.evaluation.fitness import FitnessEvaluator

    class GoodBadRSI:
        """Alternates between good and bad candidates."""

        def __init__(self):
            self._count = 0

        def generate_candidate(self, agent):
            self._count += 1
            if self._count % 2 == 1:
                return "correct safe good implementation"
            return "bad unsafe error implementation"

    class MockAgent:
        class Config:
            exploration_rate = 0.2
            learning_rate = 0.1

        config = Config()
        step_count = 0

        def step(self):
            self.step_count += 1

    verifier = LLMVerifier(VerifierConfig(granularity=20, n_verifications=1, mock=True))
    pe = ProtectedEvaluator(FitnessEvaluator())
    harness = EvolutionHarness(
        base_evolution=GoodBadRSI(),
        evaluator=pe,
        verifier=verifier,
        verifier_weight=0.8,
        verifier_candidates=2,
    )
    results = harness.run_segment(MockAgent(), iterations=4, task="Implement add")
    assert len(results) == 4
    # With verifier_weight=0.8 and verifier_candidates=2, the harness should
    # prefer the good candidate most of the time.
    good_picks = sum(1 for r in results if "good" in r.description)
    bad_picks = sum(1 for r in results if "bad" in r.description)
    assert good_picks > bad_picks

    report = harness.comparison_report()
    assert report["records"] > 0
    assert report["verifier_calls"] > 0


def test_aevo_harness_without_verifier_still_works():
    from laap.evolution.aevo import EvolutionHarness, ProtectedEvaluator
    from laap.evaluation.fitness import FitnessEvaluator

    class MockRSI:
        def generate_candidate(self, agent):
            return {"type": "test"}

    class MockAgent:
        class Config:
            exploration_rate = 0.2
            learning_rate = 0.1

        config = Config()
        step_count = 0

        def step(self):
            self.step_count += 1

    pe = ProtectedEvaluator(FitnessEvaluator())
    harness = EvolutionHarness(base_evolution=MockRSI(), evaluator=pe)
    results = harness.run_segment(MockAgent(), iterations=3)
    assert len(results) == 3
    assert harness.comparison_report()["records"] >= 0
