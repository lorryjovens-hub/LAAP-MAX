# -*- coding: utf-8 -*-
"""#2-#5 集成测试：失败记录、证据访问、可编辑面、多样性指数。"""
import os, sys, tempfile
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path: sys.path.insert(0, _ROOT)
import pytest

from laap.cognition.structured_failure import record_failure, failures_by_component, FailureLayers

def test_failure_layers():
    layers = FailureLayers(surface="超时", causal="检索超时", abstract="timing_out")
    assert layers.component() == "tool_implementation"
    d = layers.to_dict()
    assert d["surface"] == "超时"

def test_record_failure():
    r = record_failure("查询", "空", "超时", "检索超时", "timing_out")
    assert r.suggested_component == "tool_implementation"
    assert r.record_id.startswith("sf_")

def test_failures_by_component():
    r1 = record_failure("q1", "空", "超时", "检索超时", "timing_out")
    r2 = record_failure("q2", "错", "格式错误", "参数错误", "tool_parameter_error")
    by = failures_by_component([r1, r2])
    assert "tool_implementation" in by
    assert by["tool_implementation"]["count"] == 2

from laap.cognition.evidence_view import EvidenceAggregator, PerTaskReport

def test_add_report():
    agg = EvidenceAggregator(storage_dir=tempfile.mkdtemp(prefix="ev_"))
    rid = agg.create_report("任务", success=True, duration_ms=100)
    assert rid.report_id.startswith("rpt_")
    assert agg.stats()["total_reports"] == 1

def test_overview():
    agg = EvidenceAggregator(storage_dir=tempfile.mkdtemp(prefix="ev_"))
    agg.create_report("成功", True, duration_ms=50)
    agg.create_report("失败", False, failure_records=[{"layers": {"surface": "超时"}}], suggested_components=["tool_code"])
    ov = agg.overview()
    assert ov.total_reports == 2
    assert ov.success_rate == 0.5

def test_recent_reports():
    agg = EvidenceAggregator(storage_dir=tempfile.mkdtemp(prefix="ev_"))
    for i in range(3):
        agg.create_report(f"任务{i}", True)
    assert len(agg.recent_reports(2)) == 2

from laap.security.editable_surface import DEFAULT_SURFACE, EditableSurface

def test_editable_surface():
    assert DEFAULT_SURFACE.is_editable("laap/tools/my_tool.py") is True
    assert DEFAULT_SURFACE.is_editable("laap/security/runtime_guard.py") is False

def test_readonly_zones():
    assert DEFAULT_SURFACE.is_readonly("laap/security/runtime_guard.py") is True
    assert DEFAULT_SURFACE.is_readonly("laap/tools/") is False

def test_failure_to_component():
    assert DEFAULT_SURFACE.failure_to_component("memory_retrieval_miss") == "tool_code"
    assert DEFAULT_SURFACE.failure_to_component("evaluation_drift") == "evaluator_benchmark"

def test_summary():
    s = DEFAULT_SURFACE.summary()
    assert s["editable_count"] >= 6
    assert s["readonly_count"] >= 14

from laap.evolution.diversity import compute_diversity_index, DiversityMonitor, ngram_entropy, pairwise_jaccard

def test_ngram_entropy():
    e = ngram_entropy(["hello world", "你好世界"])
    assert e > 0

def test_entropy_single():
    assert ngram_entropy(["hello"]) == 0.0

def test_jaccard():
    j = pairwise_jaccard(["abc", "def"])
    assert j < 1.0

def test_jaccard_identical():
    assert pairwise_jaccard(["abc", "abc"]) == 1.0

def test_diversity_index():
    di = compute_diversity_index(["def", "abc", "ghi"])
    assert di["composite"] > 0
    assert "entropy" in di

def test_diversity_warning():
    di = compute_diversity_index(["a", "a", "a"])
    assert di["collapse_warning"] is True

def test_monitor():
    m = DiversityMonitor(window=3)
    m.observe(["abc", "def", "ghi"])
    m.observe(["abc", "def", "ghi"])
    m.observe(["abc", "def", "ghi"])
    st = m.stats()
    assert st["samples"] == 3
    assert st["rounds"] == 3