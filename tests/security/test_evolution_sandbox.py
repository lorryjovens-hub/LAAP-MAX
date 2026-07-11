# -*- coding: utf-8 -*-
"""内生演化沙箱测试"""
import pytest
from laap.security.evolution_sandbox import (
    EvolutionSandbox, SandboxResourceLimit, SandboxResult, VersionSnapshot,
)
from laap.security.zones import SafetyZone, ZoneManager


@pytest.fixture
def sandbox():
    """创建临时沙箱实例"""
    sb = EvolutionSandbox(resource_limit=SandboxResourceLimit(
        execution_timeout_sec=10, memory_mb=256
    ))
    yield sb
    sb.cleanup()


class TestSandboxResourceLimit:
    def test_defaults(self):
        limit = SandboxResourceLimit()
        assert limit.cpu_quota == "1.0"
        assert limit.memory_mb == 512
        assert limit.execution_timeout_sec == 300


class TestEvolutionSandbox:
    def test_execute_simple_code_success(self, sandbox):
        code = "print('hello world')"
        result = sandbox.execute_in_sandbox(code)
        assert result.success is True
        assert result.exit_code == 0
        assert "hello world" in result.stdout

    def test_execute_failing_code(self, sandbox):
        code = "import sys; sys.exit(1)"
        result = sandbox.execute_in_sandbox(code)
        assert result.success is False
        assert result.exit_code == 1

    def test_execute_with_tests(self, sandbox):
        code = "def add(a, b):\n    return a + b\n"
        tests = """
from subject import add
def test_add():
    assert add(1, 2) == 3
"""
        result = sandbox.execute_in_sandbox(code, tests=tests)
        assert result.success is True

    def test_execute_with_failing_tests(self, sandbox):
        code = "def add(a, b):\n    return a - b\n"  # 错误实现
        tests = """
from subject import add
def test_add():
    assert add(1, 2) == 3
"""
        result = sandbox.execute_in_sandbox(code, tests=tests)
        assert result.success is False

    def test_execution_timeout(self, sandbox):
        # 设置极短超时
        sandbox._resource_limit.execution_timeout_sec = 1
        code = "import time; time.sleep(10)"
        result = sandbox.execute_in_sandbox(code)
        assert result.success is False
        assert result.error == "timeout"

    def test_sandbox_id_generated(self, sandbox):
        result = sandbox.execute_in_sandbox("x = 1")
        assert result.sandbox_id.startswith("sandbox_")

    def test_sandbox_id_explicit(self, sandbox):
        result = sandbox.execute_in_sandbox("x = 1", sandbox_id="my_test")
        assert result.sandbox_id == "my_test"

    def test_metrics_collected(self, sandbox):
        result = sandbox.execute_in_sandbox("print('test')")
        assert "execution_time_sec" in result.metrics
        assert result.metrics["execution_time_sec"] >= 0


class TestSnapshotRollback:
    def test_create_snapshot(self, sandbox):
        snap = sandbox.create_snapshot("sb1", files={"a.py": "x = 1"})
        assert snap.snapshot_id.startswith("snap_")
        assert snap.sandbox_id == "sb1"
        assert "a.py" in snap.code_state

    def test_rollback_success(self, sandbox):
        # 先执行一次代码
        sandbox.execute_in_sandbox("x = 1", sandbox_id="sb1")
        # 创建快照
        snap = sandbox.create_snapshot("sb1")
        # 回滚
        success = sandbox.rollback(snap.snapshot_id)
        assert success is True

    def test_rollback_nonexistent(self, sandbox):
        success = sandbox.rollback("nonexistent_snap")
        assert success is False

    def test_get_snapshots(self, sandbox):
        sandbox.execute_in_sandbox("x = 1", sandbox_id="sb1")
        snap1 = sandbox.create_snapshot("sb1")
        snap2 = sandbox.create_snapshot("sb1")
        snapshots = sandbox.get_snapshots("sb1")
        assert len(snapshots) >= 2


class TestAuditLog:
    def test_audit_log_recorded(self, sandbox):
        sandbox.execute_in_sandbox("print('test')")
        logs = sandbox.get_audit_log()
        assert len(logs) >= 1
        assert "execute" in logs[0]["action"]

    def test_audit_log_contains_rollback(self, sandbox):
        sandbox._resource_limit.execution_timeout_sec = 1
        sandbox.execute_in_sandbox("import time; time.sleep(10)")
        logs = sandbox.get_audit_log()
        actions = [l["action"] for l in logs]
        assert "auto_rollback" in actions
