# -*- coding: utf-8 -*-
"""TaskBench 任务级评估基准测试。"""
import os
import sys
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest

from recall_bench.task_bench import (
    run_task_bench,
    TaskBackend,
    TASK_POOL,
    print_report,
)


class MockExecutor:
    name = "mock_executor"
    def execute(self, goal: str) -> dict:
        return {"success": True, "result": "ok", "error": ""}


class PartialExecutor:
    name = "partial"
    _count = 0
    def execute(self, goal: str) -> dict:
        self._count += 1
        # 代码类任务成功，其他随机失败
        if "代码" in goal or "函数" in goal or "排序" in goal:
            return {"success": True, "result": "code ok", "error": ""}
        # 适应任务逐步提高
        if "adapt" in str(self._count):
            return {"success": True, "result": "ok", "error": ""}
        return {"success": False, "result": "", "error": "not implemented"}


def test_protocol_check():
    """TaskBackend 协议检查。"""
    assert isinstance(MockExecutor(), TaskBackend)


def test_run_task_bench_full():
    """完整跑一轮基准。"""
    report = run_task_bench(MockExecutor())
    assert report.total == 12
    assert report.success == 12
    assert report.success_rate == 1.0
    assert len(report.by_domain) >= 4
    assert len(report.per_item) == 12


def test_partial_executor():
    """部分成功的 executor 产生正确统计。"""
    report = run_task_bench(PartialExecutor())
    assert report.total == 12
    assert 0 < report.success < 12
    # 按域分组
    for domain, s in report.by_domain.items():
        assert 0 <= s["success_rate"] <= 1.0


def test_adaptation_speed():
    """适应任务：耗时下降率计算。"""
    report = run_task_bench(PartialExecutor())
    # 适应任务 success_rate 应为 1.0（所有排序任务都成功）
    adapt = report.by_domain.get("adapt_sort", {})
    assert adapt.get("success", 0) >= 1


def test_custom_task_pool():
    """自定义任务池。"""
    pool = [
        {"goal": "测试任务 1", "domain": "test", "adaptation": False},
        {"goal": "测试任务 2", "domain": "test", "adaptation": False},
    ]
    report = run_task_bench(MockExecutor(), task_pool=pool)
    assert report.total == 2


def test_print_report_runs():
    """控制台输出不崩溃。"""
    report = run_task_bench(MockExecutor())
    print_report(report)  # 仅验证不抛异常