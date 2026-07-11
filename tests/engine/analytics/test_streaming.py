"""Streaming analytics tests."""
import pytest


def test_count_min_sketch():
    """Count-Min Sketch test

    Skip 条件: laap.engine.analytics.streaming 模块不可用时跳过 (ImportError)。
    恢复条件: 模块已可用时正常执行；仅 import 失败才 skip，其他异常照常上报。
    """
    try:
        from laap.engine.analytics.streaming import CountMinSketch
    except ImportError:
        pytest.skip("CountMinSketch not available: laap.engine.analytics.streaming 不可导入")
    cms = CountMinSketch(width=100, depth=5)
    for _ in range(1000):
        cms.add("item_a")
    est = cms.estimate("item_a")
    assert est >= 900


def test_hyperloglog():
    """HyperLogLog cardinality estimation.

    Skip 条件: laap.engine.analytics.streaming 模块不可用时跳过 (ImportError)。
    恢复条件: 模块已可用时正常执行；仅 import 失败才 skip，其他异常照常上报。
    """
    try:
        from laap.engine.analytics.streaming import HyperLogLog
    except ImportError:
        pytest.skip("HyperLogLog not available: laap.engine.analytics.streaming 不可导入")
    hll = HyperLogLog(precision=10)
    for i in range(10000):
        hll.add(f"unique_item_{i}")
    est = hll.estimate()
    assert est > 0
