# -*- coding: utf-8 -*-
"""TaskExecutor 自主任务执行引擎测试。"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest
from laap.orchestration.task_executor import TaskExecutor, TaskStep, StepStatus


def test_decompose_search():
    exe = TaskExecutor()
    steps = exe._decompose("搜索 AI 的最新进展")
    assert len(steps) >= 2


def test_decompose_code():
    exe = TaskExecutor()
    steps = exe._decompose("写一个 Python 排序函数")
    assert len(steps) >= 2


def test_execute_success():
    class MockTool:
        def execute(self, **kwargs):
            return "done"
    reg = type("R", (), {"get_tool": lambda s, n: MockTool()})()
    exe = TaskExecutor(tool_registry=reg, max_retries=0)
    steps = [{"name": "s1", "description": "x", "action": "t", "args": {}}]
    r = exe.execute("测试", steps=steps)
    assert r.status == "done"
    assert r.steps[0].status == StepStatus.DONE


def test_retry_on_failure():
    call_count = [0]
    class FailableTool:
        def execute(self, **kwargs):
            call_count[0] += 1
            if call_count[0] < 2:
                raise RuntimeError("第一次失败")
            return "成功了"

    reg = type("R", (), {"get_tool": lambda s, n: FailableTool()})()
    exe = TaskExecutor(tool_registry=reg, max_retries=2, step_timeout_sec=10)
    steps = [{"name": "重试", "description": "重试测试", "action": "t", "args": {}}]
    r = exe.execute("重试任务", steps=steps)
    assert r.status == "done"
    assert r.steps[0].retries >= 1


def test_alternatives():
    step = TaskStep(name="主", description="主方案", action="t", args={},
                    alternatives=["备选"])
    class RecoveryTool:
        def execute(self, **kwargs):
            return "替代方案成功"

    reg = type("R", (), {"get_tool": lambda s, n: RecoveryTool()})()
    exe = TaskExecutor(tool_registry=reg, max_retries=0, step_timeout_sec=10)
    assert exe._try_alternatives(step)


def test_stats():
    class MockTool:
        def execute(self, **kwargs):
            return "ok"
    reg = type("R", (), {"get_tool": lambda s, n: MockTool()})()
    exe = TaskExecutor(tool_registry=reg, max_retries=0)
    steps = [{"name": "s1", "description": "x", "action": "t", "args": {}}]
    exe.execute("任务1", steps=steps)
    exe.execute("任务2", steps=steps)
    s = exe.stats()
    assert s["total"] == 2
    assert s["done"] == 2
    assert s["success_rate"] == 1.0


def test_record_query():
    class MockTool:
        def execute(self, **kwargs):
            return "ok"
    reg = type("R", (), {"get_tool": lambda s, n: MockTool()})()
    exe = TaskExecutor(tool_registry=reg, max_retries=0)
    steps = [{"name": "s1", "description": "x", "action": "t", "args": {}}]
    r = exe.execute("任务", steps=steps)
    assert exe.get_execution(r.task_id) is not None
    assert len(exe.recent(10)) == 1