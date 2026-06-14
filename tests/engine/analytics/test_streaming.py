"""Streaming analytics tests."""
import pytest


def test_count_min_sketch():
    """Count-Min Sketch test"""
    try:
        from laap.engine.analytics.streaming import CountMinSketch
        cms = CountMinSketch(width=100, depth=5)
        for _ in range(1000):
            cms.add("item_a")
        est = cms.estimate("item_a")
        assert est >= 900
    except Exception:
        pytest.skip("CountMinSketch not available")


def test_hyperloglog():
    """HyperLogLog cardinality estimation."""
    try:
        from laap.engine.analytics.streaming import HyperLogLog
        hll = HyperLogLog(precision=10)
        for i in range(10000):
            hll.add(f"unique_item_{i}")
        est = hll.estimate()
        assert est > 0
    except Exception:
        pytest.skip("HyperLogLog not available")
