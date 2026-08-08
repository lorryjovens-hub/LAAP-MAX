# -*- coding: utf-8 -*-
"""元认知系统测试"""
import pytest
from laap.cognition.metacognition import (
    MetacognitionSystem, ReflectionReport, Anomaly, AnomalyType,
    Improvement, ImprovementType,
)


def test_reflect_success():
    mc = MetacognitionSystem()
    report = mc.reflect(
        task={"task_id": "t1", "description": "测试任务"},
        outcome={
            "success": True,
            "time_spent_sec": 30,
            "decisions": [{"action": "step1", "actual_outcome": {"benefit": "ok"}}],
        },
    )
    assert report.outcome_success is True
    assert report.task_id == "t1"
    assert len(report.lessons_learned) > 0
    assert report.confidence > 0.5


def test_reflect_failure():
    mc = MetacognitionSystem()
    report = mc.reflect(
        task={"task_id": "t2", "description": "失败任务"},
        outcome={
            "success": False,
            "error": "参数错误",
            "time_spent_sec": 120,
            "decisions": [
                {"action": "step1", "actual_outcome": {"failed": True, "reason": "无效参数"}}
            ],
        },
    )
    assert report.outcome_success is False
    assert any("参数错误" in l for l in report.lessons_learned)


def test_monitor_detects_oscillation():
    mc = MetacognitionSystem()
    task_id = "t3"
    # 模拟决策震荡
    for action in ["A", "B", "A", "B", "A"]:
        anomaly = mc.monitor_cognition({
            "task_id": task_id,
            "current_action": action,
        })
    assert anomaly is not None
    assert anomaly.anomaly_type == AnomalyType.OSCILLATION


def test_monitor_detects_overconfidence():
    mc = MetacognitionSystem()
    anomaly = mc.monitor_cognition({
        "task_id": "t4",
        "confidence": 0.95,
    })
    assert anomaly is not None
    assert anomaly.anomaly_type == AnomalyType.OVERCONFIDENCE


def test_monitor_detects_underconfidence():
    mc = MetacognitionSystem()
    anomaly = mc.monitor_cognition({
        "task_id": "t5",
        "confidence": 0.1,
    })
    assert anomaly is not None
    assert anomaly.anomaly_type == AnomalyType.UNDERCONFIDENCE


def test_suggest_improvement_after_failures():
    mc = MetacognitionSystem()
    # 制造多次失败
    for i in range(6):
        mc.reflect(
            task={"task_id": f"f{i}", "description": "失败"},
            outcome={"success": False, "error": "err"},
        )
    imp = mc.suggest_improvement()
    assert imp is not None
    assert imp.improvement_type == ImprovementType.STRATEGY_CHANGE
    assert imp.priority == "high"


def test_suggest_improvement_no_history():
    mc = MetacognitionSystem()
    assert mc.suggest_improvement() is None


def test_get_history_filtered():
    mc = MetacognitionSystem()
    mc.reflect(task={"task_id": "t1", "description": "a"}, outcome={"success": True})
    mc.reflect(task={"task_id": "t2", "description": "b"}, outcome={"success": False})
    history = mc.get_history(task_id="t1")
    assert len(history) == 1
    assert history[0].task_id == "t1"
