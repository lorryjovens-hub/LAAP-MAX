# -*- coding: utf-8 -*-
"""RSICoordinator 进化协调器测试。"""
import os, sys, time
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path: sys.path.insert(0, _ROOT)
import pytest
from laap.evolution.rsi_coordinator import (
    RSICoordinator, CodebaseSensor, TaskDecomposer, EvolveTask,
)


# ── 感知层 ───────────────────────────────────────────────────────────────

def test_recent_changes_detects_self():
    """传感器应检测到最近的 Python 改动（含本文件）。"""
    sensor = CodebaseSensor(window_hours=48)
    changes = sensor.recent_changes()
    assert len(changes) >= 1
    # 本测试文件应该在列表里
    assert any("test_rsi_coordinator" in c.path for c in changes)


def test_git_status_runs():
    sensor = CodebaseSensor()
    s = sensor.git_status()
    assert "ok" in s


def test_conflict_detection():
    """同目录多文件改动应触发冲突提示。"""
    # 构造假改动
    fake = []
    for i in range(4):
        fake.append(type("C", (), {
            "path": f"laap/tools/_conflict_{i}.py", "mtime": time.time(),
            "size": 10, "age_hours": 0.1})())
    sensor = CodebaseSensor()
    conflicts = sensor.detect_conflicts(fake)
    assert len(conflicts) >= 1
    assert conflicts[0]["dir"] == "laap/tools"


def test_full_report_structure():
    sensor = CodebaseSensor(window_hours=48)
    r = sensor.full_report()
    assert "recent_changes" in r
    assert "git" in r
    assert "conflicts" in r
    assert "ledger" in r


# ── 拆解层 ───────────────────────────────────────────────────────────────

def test_decompose_with_targets():
    tasks = TaskDecomposer.decompose("进化", ["laap/tools/a.py", "laap/tools/b.py"])
    assert len(tasks) == 2
    assert all(t.target for t in tasks)


def test_decompose_no_targets():
    tasks = TaskDecomposer.decompose("分析", [])
    assert len(tasks) == 1
    assert "分析" in tasks[0].name


# ── 协调器 ───────────────────────────────────────────────────────────────

def test_coordinate_full_pipeline():
    """完整管线：感知→拆解→执行→合并→汇报。"""
    coord = RSICoordinator()  # 无执行器，演示拆解
    r = coord.coordinate("进化测试", ["laap/tools/a.py", "laap/tools/b.py"])
    assert r.summary
    assert len(r.tasks) == 2
    assert "拆解" in r.summary
    assert r.duration_ms > 0


def test_coordinate_with_task_runner():
    """自定义 runner 执行子任务。"""
    def runner(task):
        if "a.py" in task.target:
            return True, "成功"
        return False, "失败"
    coord = RSICoordinator(task_runner=runner)
    r = coord.coordinate("测试", ["laap/tools/a.py", "laap/tools/b.py"])
    assert r.task_results[0]["status"] == "done"
    assert r.task_results[1]["status"] == "failed"
    assert "完成 1" in r.summary


def test_coordinate_with_executor():
    """TaskExecutor 执行子任务。"""
    from laap.orchestration.task_executor import TaskExecutor

    class MockTool:
        def execute(self, **kwargs):
            return "ok"
    reg = type("R", (), {"get_tool": lambda s, n: MockTool()})()
    coord = RSICoordinator(executor=TaskExecutor(tool_registry=reg, max_retries=0))
    r = coord.coordinate("测试", ["laap/tools/x.py"])
    assert r.task_results[0]["status"] == "done"


def test_merge_conflicts():
    """同目录多任务应被标记为合并冲突。"""
    tasks = [
        EvolveTask(name="a", target="laap/tools/a.py"),
        EvolveTask(name="b", target="laap/tools/b.py"),
    ]
    conflicts = RSICoordinator._merge_conflicts(tasks)
    assert len(conflicts) == 1
    assert conflicts[0]["count"] == 2


def test_stats():
    coord = RSICoordinator(task_runner=lambda t: (True, "ok"))
    coord.coordinate("任务1", ["laap/tools/a.py"])
    coord.coordinate("任务2", ["laap/tools/b.py"])
    s = coord.stats()
    assert s["total_runs"] == 2
    assert s["total_tasks"] == 2
    assert s["task_success_rate"] == 1.0


def test_recent():
    coord = RSICoordinator()
    coord.coordinate("任务", ["laap/tools/a.py"])
    assert len(coord.recent(5)) == 1