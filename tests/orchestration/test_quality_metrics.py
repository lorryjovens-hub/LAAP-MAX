"""Tests for :mod:`laap.orchestration.quality_metrics` (M6 E4)."""

from __future__ import annotations

import json
import os

import pytest

from laap.orchestration.quality_metrics import QualityMetrics


def test_record_and_pass_at_k() -> None:
    """Record 10 results (7 success), verify pass@1 = 0.7."""
    qm = QualityMetrics()

    for i in range(7):
        qm.record_task_result(
            task_id=f"success_{i}",
            success=True,
            latency_ms=100.0,
            quality_score=0.9,
        )
    for i in range(3):
        qm.record_task_result(
            task_id=f"fail_{i}",
            success=False,
            latency_ms=200.0,
            quality_score=0.3,
        )

    assert qm.compute_pass_at_k(1) == pytest.approx(0.7)


def test_pass_at_k_groups_retries() -> None:
    """pass@k groups by task_id and checks the last k attempts."""
    qm = QualityMetrics()

    # task_a: fail, fail, success → pass@3 = passed
    qm.record_task_result("task_a", success=False, latency_ms=10.0, quality_score=0.1)
    qm.record_task_result("task_a", success=False, latency_ms=10.0, quality_score=0.1)
    qm.record_task_result("task_a", success=True, latency_ms=10.0, quality_score=0.9)
    # task_b: fail, fail, fail → not passed
    qm.record_task_result("task_b", success=False, latency_ms=10.0, quality_score=0.1)
    qm.record_task_result("task_b", success=False, latency_ms=10.0, quality_score=0.1)
    qm.record_task_result("task_b", success=False, latency_ms=10.0, quality_score=0.1)

    # pass@1 across all 6 attempts = 1/6
    assert qm.compute_pass_at_k(1) == pytest.approx(1.0 / 6.0)
    # pass@3 grouped by task = 1/2 (task_a passed, task_b did not)
    assert qm.compute_pass_at_k(3) == pytest.approx(0.5)


def test_pass_at_k_empty_returns_zero() -> None:
    """pass@k with no results returns 0.0."""
    qm = QualityMetrics()
    assert qm.compute_pass_at_k(1) == 0.0
    assert qm.compute_pass_at_k(5) == 0.0


def test_pass_at_k_invalid_k_raises() -> None:
    """k < 1 raises ValueError."""
    qm = QualityMetrics()
    with pytest.raises(ValueError):
        qm.compute_pass_at_k(0)


def test_transfer_metrics() -> None:
    """Record ID and OOD results, verify transfer computation."""
    qm = QualityMetrics()

    # ID domain ("python"): 8/10 success
    for i in range(8):
        qm.record_task_result(
            task_id=f"id_ok_{i}",
            success=True,
            latency_ms=100.0,
            quality_score=0.9,
            domain="python",
        )
    for i in range(2):
        qm.record_task_result(
            task_id=f"id_fail_{i}",
            success=False,
            latency_ms=150.0,
            quality_score=0.4,
            domain="python",
        )

    # OOD domain ("rust"): 4/10 success
    for i in range(4):
        qm.record_task_result(
            task_id=f"ood_ok_{i}",
            success=True,
            latency_ms=200.0,
            quality_score=0.7,
            domain="rust",
        )
    for i in range(6):
        qm.record_task_result(
            task_id=f"ood_fail_{i}",
            success=False,
            latency_ms=250.0,
            quality_score=0.2,
            domain="rust",
        )

    transfer = qm.compute_transfer("python", "rust")
    assert transfer["id_pass_rate"] == pytest.approx(0.8)
    assert transfer["ood_pass_rate"] == pytest.approx(0.4)
    assert transfer["transfer_ratio"] == pytest.approx(0.5)  # 0.4 / 0.8
    assert transfer["id_samples"] == 10.0
    assert transfer["ood_samples"] == 10.0


def test_transfer_metrics_missing_domain() -> None:
    """Transfer with an unknown domain returns 0.0 rates."""
    qm = QualityMetrics()
    qm.record_task_result("t1", success=True, latency_ms=10.0, quality_score=0.9,
                          domain="python")
    transfer = qm.compute_transfer("python", "rust")
    assert transfer["id_pass_rate"] == pytest.approx(1.0)
    assert transfer["ood_pass_rate"] == pytest.approx(0.0)
    assert transfer["transfer_ratio"] == pytest.approx(0.0)


def test_export_results(tmp_path) -> None:
    """Export to a tmp file, verify structure and on-disk content."""
    qm = QualityMetrics()

    qm.record_task_result(
        task_id="t1", success=True, latency_ms=100.0, quality_score=0.9
    )
    qm.record_task_result(
        task_id="t2", success=False, latency_ms=200.0, quality_score=0.3
    )

    export_path = str(tmp_path / "quality.json")
    result = qm.export_results(export_path)

    # Returned dict has the expected structure.
    assert "results" in result
    assert "summary" in result
    assert result["summary"]["total_tasks"] == 2
    assert len(result["results"]) == 2

    # File on disk matches the returned dict.
    assert os.path.exists(export_path)
    with open(export_path, encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["summary"]["total_tasks"] == 2
    assert len(loaded["results"]) == 2
    assert {r["task_id"] for r in loaded["results"]} == {"t1", "t2"}


def test_generate_trend_report() -> None:
    """Trend report returns cumulative time-series of the right shape."""
    qm = QualityMetrics()
    # Empty case.
    empty = qm.generate_trend_report()
    assert empty == {
        "timestamps": [],
        "success_rate": [],
        "avg_latency_ms": [],
        "avg_quality_score": [],
    }

    # Record three results.
    qm.record_task_result("t1", success=True, latency_ms=100.0, quality_score=0.8)
    qm.record_task_result("t2", success=False, latency_ms=200.0, quality_score=0.4)
    qm.record_task_result("t3", success=True, latency_ms=300.0, quality_score=1.0)

    trend = qm.generate_trend_report()
    assert len(trend["timestamps"]) == 3
    assert len(trend["success_rate"]) == 3
    assert len(trend["avg_latency_ms"]) == 3
    assert len(trend["avg_quality_score"]) == 3
    # Cumulative success rate: 1/1, 1/2, 2/3.
    assert trend["success_rate"][0] == pytest.approx(1.0)
    assert trend["success_rate"][1] == pytest.approx(0.5)
    assert trend["success_rate"][2] == pytest.approx(2.0 / 3.0)
    # Cumulative avg latency: 100, 150, 200.
    assert trend["avg_latency_ms"][0] == pytest.approx(100.0)
    assert trend["avg_latency_ms"][1] == pytest.approx(150.0)
    assert trend["avg_latency_ms"][2] == pytest.approx(200.0)
