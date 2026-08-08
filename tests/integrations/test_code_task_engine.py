"""C2 Harness Code Task Engine tests."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from laap.integrations.harnessx.code_task_engine import (
    CodeTask,
    CodeTaskResult,
    HarnessCodeTaskEngine,
    submit_execution_result,
)


# ─── CodeTask dataclass ──────────────────────────────────────────────────

def test_code_task_has_unique_id():
    """Each CodeTask should have a unique id."""
    t1 = CodeTask(description="task 1")
    t2 = CodeTask(description="task 2")
    assert t1.task_id != t2.task_id
    assert t1.task_id.startswith("code_task_")


def test_code_task_default_whitelist():
    """Default whitelist should include laap/tools/."""
    task = CodeTask(description="test")
    assert "laap/tools/" in task.whitelist_dirs
    assert "laap/security/" in task.blacklist_dirs


# ─── CodeTaskResult ──────────────────────────────────────────────────────

def test_code_task_result_to_dict():
    """CodeTaskResult.to_dict should produce JSON-serializable dict."""
    r = CodeTaskResult(
        task_id="test-1",
        passed=True,
        pass_at_1=1.0,
        pass_at_5=1.0,
        pass_at_10=1.0,
        final_output="done",
    )
    d = r.to_dict()
    assert d["task_id"] == "test-1"
    assert d["passed"] is True
    assert d["pass_at_1"] == 1.0


# ─── HarnessCodeTaskEngine ───────────────────────────────────────────────

def test_engine_init_defaults():
    """Engine should init with sensible defaults."""
    engine = HarnessCodeTaskEngine()
    assert engine.runtime is None
    assert engine.psi_driver is None
    stats = engine.stats()
    assert stats["total_tasks"] == 0
    assert stats["runtime_available"] is False


def test_engine_fallback_to_code_evolution(tmp_path):
    """Engine should fall back to CodeEvolutionEngine when runtime is unavailable."""
    # Create a minimal whitelisted file
    tools_dir = tmp_path / "laap" / "tools"
    tools_dir.mkdir(parents=True)
    (tools_dir / "stub.py").write_text(
        'def foo(a, b, c):\n'
        '    r = 0\n'
        '    for i in range(a):\n'
        '        for j in range(b):\n'
        '            for k in range(c):\n'
        '                if i > 0 and j > 0:\n'
        '                    r += 1\n'
        '    return r\n',
        encoding="utf-8",
    )
    engine = HarnessCodeTaskEngine(
        runtime=None,  # no runtime
        repo_root=str(tmp_path),
    )
    task = CodeTask(
        description="analyze stub",
        repo_path="laap/tools/",
        max_steps=1,
    )
    result = asyncio.run(engine.execute(task))
    assert result.task_id == task.task_id
    # Should not have runtime error
    assert result.error == "" or "no improvements" in result.error


def test_engine_stats_tracks_results(tmp_path):
    """Engine stats should reflect executed tasks."""
    engine = HarnessCodeTaskEngine(repo_root=str(tmp_path))
    # Manually append a result
    engine._results.append(CodeTaskResult(task_id="t1", passed=True))
    engine._results.append(CodeTaskResult(task_id="t2", passed=False))
    stats = engine.stats()
    assert stats["total_tasks"] == 2
    assert stats["passed"] == 1
    assert stats["failed"] == 1
    assert stats["pass_rate"] == 0.5


# ─── submit_execution_result ─────────────────────────────────────────────

def test_submit_execution_result_with_psi_driver():
    """submit_execution_result should call psi_driver.learn if available."""
    class MockPSI:
        def __init__(self):
            self.learned = None

        def learn(self, payload):
            self.learned = payload

    psi = MockPSI()
    result = CodeTaskResult(task_id="t1", passed=True, pass_at_1=1.0)
    ok = submit_execution_result(result, psi_driver=psi)
    assert ok
    assert psi.learned is not None
    assert psi.learned["task_id"] == "t1"
    assert psi.learned["passed"] is True


def test_submit_execution_result_no_psi_returns_true_or_false_gracefully():
    """Without psi_driver, should attempt CognitiveBus and return bool."""
    result = CodeTaskResult(task_id="t2", passed=False)
    # Just ensure it doesn't raise
    ok = submit_execution_result(result, psi_driver=None)
    assert isinstance(ok, bool)
