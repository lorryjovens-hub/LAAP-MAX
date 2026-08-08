# -*- coding: utf-8 -*-
"""NightRunner 夜间自动实验调度器测试。"""
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest
from laap.evolution.night_runner import NightRunner, NightReport


def test_outside_window_returns_empty():
    """不在时间窗口内应返回空报告。"""
    runner = NightRunner(window=(23, 23))  # 永远不在窗口
    report = runner.run()
    assert "不在运行窗口" in report.summary
    assert report.proposals_attempted == 0


def test_force_run_ignores_window():
    """force=True 应忽略时间窗口。"""
    runner = NightRunner(window=(23, 23))
    report = runner.run(force=True)
    assert report is not None


def test_no_engine_returns_empty():
    """无引擎时应返回空报告。"""
    runner = NightRunner(window=(0, 23))
    report = runner.run(force=True)
    assert report.proposals_attempted == 0
    assert report.run_id.startswith("night_")


def test_stats_after_run():
    """运行后统计应有记录。"""
    runner = NightRunner(window=(0, 23))
    r1 = runner.run(force=True)
    r2 = runner.run(force=True)
    stats = runner.stats()
    assert stats["total_runs"] == 2
    assert r1.run_id != r2.run_id


def test_morning_report_text():
    """晨报文本不崩溃。"""
    runner = NightRunner(window=(0, 23))
    runner.run(force=True)
    text = runner.morning_report_text()
    assert "夜间实验" in text
    assert "尝试" in text or "没有" in text


def test_morning_report_empty():
    """无记录时返回提示。"""
    runner = NightRunner()
    text = runner.morning_report_text()
    assert "没有夜间运行记录" in text