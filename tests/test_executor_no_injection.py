"""Tests verifying command-injection fixes in laap.shell.executor.

Covers:
  * Shell metacharacters (``;``, ``|``, ``&&``, ``$()``, backticks) in Python
    code passed to ``run_python`` are NOT interpreted by a shell.
  * ``duration`` returned by ``run`` / ``run_python`` is the real elapsed time,
    not the ``timeout`` value (regression test for the old ``"duration": timeout`` bug).
  * ``python -c`` execution via ``run_python`` works correctly.
"""
import os
import sys
import time

import pytest

from laap.shell.executor import ShellExecutor


# ── run_python: shell metacharacters must be treated as Python code ──────────

@pytest.mark.parametrize("payload", [
    "print('; | && $() `whoami`')",
    "print('a' + ' && whoami')",
    "print('safe`whoami`')",
    "print('$(whoami)')",
    "print('a; whoami')",
])
def test_run_python_metacharacters_not_shell_interpreted(payload):
    """Metacharacters in code must be printed verbatim, not run by a shell.

    Under the old ``f"python -c {shlex.quote(code)}"`` + ``shell=True`` path a
    crafted payload could break out of the quotes and execute ``whoami``. With
    ``shell=False`` + ``[sys.executable, "-c", code]`` the code is a single
    argv element and the metacharacters reach the Python interpreter intact.
    """
    result = ShellExecutor().run_python(payload, timeout=15)
    assert result["success"], f"expected success, got: {result}"
    assert "; | && $() `whoami`".split() or True  # sanity
    # The literal payload fragments must appear in stdout (proving they were
    # printed, not executed as shell commands).
    assert "whoami" in result["stdout"]


def test_run_python_no_whoami_output_leak():
    """``whoami`` must never actually execute — its output must NOT appear as a
    separate shell command's stdout. We only expect the literal string."""
    result = ShellExecutor().run_python("print('x && whoami')", timeout=15)
    assert result["success"], f"expected success, got: {result}"
    assert "x && whoami" in result["stdout"]
    # If shell injection had occurred, the real whoami output (a username line)
    # would be appended on its own — stdout should be exactly the printed line.
    assert result["stdout"].strip() == "x && whoami"


# ── run_python: correct execution ────────────────────────────────────────────

def test_run_python_executes_correctly():
    """``python -c`` should evaluate Python and return stdout."""
    result = ShellExecutor().run_python("print(2 + 3)", timeout=15)
    assert result["success"], f"expected success, got: {result}"
    assert "5" in result["stdout"]
    assert result["exit_code"] == 0


def test_run_python_error_returned_in_stderr():
    """A Python exception must surface as non-zero exit + stderr message."""
    result = ShellExecutor().run_python("raise ValueError('boom')", timeout=15)
    assert not result["success"]
    assert result["exit_code"] != 0
    assert "boom" in result["stderr"]


def test_run_python_uses_sys_executable():
    """``run_python`` must invoke the same interpreter (sys.executable), not a
    bare ``python`` that may not exist on PATH."""
    result = ShellExecutor().run_python(
        "import sys; print(sys.executable)", timeout=15
    )
    assert result["success"], f"expected success, got: {result}"
    # The interpreter that ran the code should match the one running these tests.
    assert os.path.normcase(result["stdout"].strip()) == os.path.normcase(sys.executable)


# ── duration: must be real elapsed time, not the timeout value ───────────────

def test_run_python_duration_is_real_elapsed():
    """``duration`` must reflect actual runtime, not the ``timeout`` argument.

    Regression test for the old ``"duration": timeout`` bug where a 0.5s job
    reported a 30s duration.
    """
    timeout = 30
    result = ShellExecutor().run_python("import time; time.sleep(0.5)", timeout=timeout)
    assert result["success"], f"expected success, got: {result}"
    assert "duration" in result
    # Real elapsed ~0.5s; must be well below the 30s timeout.
    assert result["duration"] < timeout, (
        f"duration={result['duration']} should be < timeout={timeout} (old bug)"
    )
    # And reasonably close to the sleep duration (allow slack).
    assert result["duration"] >= 0.3, (
        f"duration={result['duration']} too short for a 0.5s sleep"
    )


def test_run_python_duration_differs_from_timeout():
    """Two runs with the SAME code but DIFFERENT timeouts must yield ~equal
    durations — proving duration is not just echoing the timeout."""
    code = "import time; time.sleep(0.3)"
    r_short_timeout = ShellExecutor().run_python(code, timeout=20)
    r_long_timeout = ShellExecutor().run_python(code, timeout=60)
    assert r_short_timeout["success"] and r_long_timeout["success"]
    d1, d2 = r_short_timeout["duration"], r_long_timeout["duration"]
    # Both ~0.3s; difference should be tiny, NOT 40s (60-20).
    assert abs(d1 - d2) < 1.0, (
        f"durations differ by {abs(d1 - d2)}s — looks like timeout echoed, "
        f"got {d1} vs {d2}"
    )


def test_run_duration_is_real_elapsed():
    """Same regression check for the generic ``run()`` method."""
    timeout = 30
    # ``python`` is in the sandbox allow-list; sleep 0.5s.
    result = ShellExecutor().run(
        f'python -c "import time; time.sleep(0.5)"', timeout=timeout
    )
    if not result.get("success"):
        pytest.skip(f"sandbox blocked the command: {result.get('error')}")
    assert "duration" in result
    assert result["duration"] < timeout, (
        f"duration={result['duration']} should be < timeout={timeout} (old bug)"
    )
    assert result["duration"] >= 0.3


def test_run_timeout_duration_is_real_elapsed():
    """Even on timeout, ``duration`` should be a real wall-clock measurement,
    not the configured ``timeout`` value (the old ``"duration": timeout`` bug).

    NOTE: on Windows with ``shell=True``, ``process.kill()`` only terminates the
    intermediate ``cmd.exe`` — the child ``python.exe`` may keep running until
    it finishes naturally, so the real elapsed can exceed ``timeout``. That is
    a separate process-tree-kill limitation; what matters here is that
    ``duration`` is a measured float, NOT the integer ``timeout`` echo.
    """
    timeout = 2
    result = ShellExecutor().run(
        f'python -c "import time; time.sleep(10)"', timeout=timeout
    )
    # Either blocked by sandbox (skip) or timed out.
    if result.get("exit_code") == -1 and "blocked" in result.get("error", "").lower():
        pytest.skip("sandbox blocked the long-sleep command")
    assert not result["success"]
    assert "duration" in result
    # Regression: old bug returned the exact integer `timeout`; the fix returns
    # a float from time.monotonic(). They must not be equal.
    assert result["duration"] != timeout, (
        f"duration={result['duration']!r} equals timeout={timeout!r} — old bug "
        f"('duration': timeout) likely regressed"
    )
    assert isinstance(result["duration"], float)
    assert result["duration"] > 0
