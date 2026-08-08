"""Tests for the restricted sandbox execution in muscle memory."""

import pytest

from laap.engine.memory.muscle import MuscleMemory, safe_exec


class TestSafeExec:
    """Direct tests for ``safe_exec`` sandbox enforcement."""

    def test_safe_code_executes_correctly(self):
        namespace = {}
        safe_exec(
            """
def execute(name):
    return f"hello, {name}"
""",
            namespace,
        )
        assert "execute" in namespace
        assert namespace["execute"]("world") == "hello, world"

    def test_safe_exec_allows_basic_control_flow(self):
        namespace = {}
        safe_exec(
            """
def execute(n):
    total = 0
    for i in range(n):
        total += i
    return total
""",
            namespace,
        )
        assert namespace["execute"](5) == 10

    def test_safe_exec_blocks_import(self):
        with pytest.raises(Exception) as exc_info:
            safe_exec("import os", {})
        assert "Unsafe" in str(exc_info.value)

    def test_safe_exec_blocks_from_import(self):
        with pytest.raises(Exception) as exc_info:
            safe_exec("from os import system", {})
        assert "Unsafe" in str(exc_info.value)

    def test_safe_exec_blocks_dunder_import_call(self):
        with pytest.raises(Exception) as exc_info:
            safe_exec("__import__('os')", {})
        assert "Disallowed call: __import__" in str(exc_info.value)

    def test_safe_exec_blocks_open(self):
        with pytest.raises(Exception) as exc_info:
            safe_exec("open('/etc/passwd')", {})
        assert "Disallowed call: open" in str(exc_info.value)

    def test_safe_exec_blocks_eval(self):
        with pytest.raises(Exception) as exc_info:
            safe_exec("eval('1 + 1')", {})
        assert "Disallowed call: eval" in str(exc_info.value)

    def test_safe_exec_blocks_exec(self):
        with pytest.raises(Exception) as exc_info:
            safe_exec("exec('pass')", {})
        assert "Disallowed call: exec" in str(exc_info.value)

    def test_safe_exec_blocks_compile(self):
        with pytest.raises(Exception) as exc_info:
            safe_exec("compile('pass', '<x>', 'exec')", {})
        assert "Disallowed call: compile" in str(exc_info.value)

    def test_safe_exec_blocks_sandbox_escape_via_dunder(self):
        with pytest.raises(Exception) as exc_info:
            safe_exec("().__class__.__bases__[0].__subclasses__()", {})
        assert "Disallowed attribute access: __class__" in str(exc_info.value)

    def test_safe_exec_blocks_class_definition(self):
        with pytest.raises(Exception) as exc_info:
            safe_exec("class Foo: pass", {})
        assert "Unsafe AST node: ClassDef" in str(exc_info.value)

    def test_safe_exec_blocks_lambda(self):
        with pytest.raises(Exception) as exc_info:
            safe_exec("f = lambda: 1", {})
        assert "Unsafe AST node: Lambda" in str(exc_info.value)


class TestMuscleMemorySafeExecution:
    """Integration tests ensuring muscle memory still works through the sandbox."""

    def test_muscle_memory_execute_hello_world(self):
        mm = MuscleMemory()
        code = """
def execute():
    return "hello world"
"""
        mm.learn("greet", code)
        result = mm.execute("greet")
        assert result == "hello world"

    def test_muscle_memory_execute_with_arguments(self):
        mm = MuscleMemory()
        code = """
def execute(a, b, multiplier=1):
    return (a + b) * multiplier
"""
        mm.learn("add", code)
        assert mm.execute("add", 2, 3) == 5
        assert mm.execute("add", 2, 3, multiplier=10) == 50

    def test_muscle_memory_dangerous_code_is_blocked(self):
        mm = MuscleMemory()
        code = """
import os
def execute():
    return os.system('echo pwned')
"""
        mm.learn("evil", code)
        with pytest.raises(Exception) as exc_info:
            mm.execute("evil")
        assert "Unsafe" in str(exc_info.value)

    def test_muscle_memory_invocation_stats_update(self):
        mm = MuscleMemory()
        code = "def execute(): return 42"
        mm.learn("answer", code)
        for _ in range(5):
            assert mm.execute("answer") == 42
        skill = mm.get_skill("answer")
        assert skill is not None
        assert skill.invocation_count == 5
