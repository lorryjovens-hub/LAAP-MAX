"""Tests for IsolationLevel enum ordering and sandbox branch behavior.

Regression coverage for the sandbox enumeration comparison inversion bug:
previously IsolationLevel used string values, and lexicographic comparison
caused MAXIMUM ("maximum") and STRICT ("strict") to be treated as *below*
STANDARD ("standard") because 'm' < 's' and 't' < 's' in ASCII.
"""
import platform
from pathlib import Path

import pytest

from laap.shell.sandbox import IsolationLevel, Sandbox, SandboxConfig


LEVELS_ASC = [
    IsolationLevel.NONE,
    IsolationLevel.BASIC,
    IsolationLevel.STANDARD,
    IsolationLevel.STRICT,
    IsolationLevel.MAXIMUM,
]


class TestEnumOrdering:
    def test_values_are_integers(self):
        for level in LEVELS_ASC:
            assert isinstance(level.value, int), f"{level.name}.value must be int"
            assert isinstance(int(level), int)

    def test_expected_integer_values(self):
        assert IsolationLevel.NONE.value == 0
        assert IsolationLevel.BASIC.value == 1
        assert IsolationLevel.STANDARD.value == 2
        assert IsolationLevel.STRICT.value == 3
        assert IsolationLevel.MAXIMUM.value == 4

    def test_strict_ordering_none_to_maximum(self):
        for lower, upper in zip(LEVELS_ASC, LEVELS_ASC[1:]):
            assert lower.value < upper.value, f"{lower.name} should be < {upper.name}"

    def test_maximum_greater_than_standard(self):
        # The core regression: MAXIMUM must rank above STANDARD.
        assert IsolationLevel.MAXIMUM.value > IsolationLevel.STANDARD.value

    def test_strict_greater_than_standard(self):
        assert IsolationLevel.STRICT.value > IsolationLevel.STANDARD.value

    def test_enum_names_preserved(self):
        assert IsolationLevel.NONE.name == "NONE"
        assert IsolationLevel.BASIC.name == "BASIC"
        assert IsolationLevel.STANDARD.name == "STANDARD"
        assert IsolationLevel.STRICT.name == "STRICT"
        assert IsolationLevel.MAXIMUM.name == "MAXIMUM"


class TestStandardThresholdBranch:
    """validate() runs the allowlist check when level.value >= STANDARD.value."""

    @pytest.mark.parametrize("level", [
        IsolationLevel.STANDARD,
        IsolationLevel.STRICT,
        IsolationLevel.MAXIMUM,
    ])
    def test_standard_or_above_meets_standard_threshold(self, level):
        assert level.value >= IsolationLevel.STANDARD.value

    @pytest.mark.parametrize("level", [
        IsolationLevel.NONE,
        IsolationLevel.BASIC,
    ])
    def test_below_standard_does_not_meet_standard_threshold(self, level):
        assert level.value < IsolationLevel.STANDARD.value


class TestStrictThresholdBranch:
    """get_command_prefix / create_temp_workspace gate on STRICT threshold."""

    @pytest.mark.parametrize("level", [
        IsolationLevel.STRICT,
        IsolationLevel.MAXIMUM,
    ])
    def test_strict_or_above_meets_strict_threshold(self, level):
        assert level.value >= IsolationLevel.STRICT.value
        # The "below STRICT" check used by create_temp_workspace must be False.
        assert not (level.value < IsolationLevel.STRICT.value)

    @pytest.mark.parametrize("level", [
        IsolationLevel.NONE,
        IsolationLevel.BASIC,
        IsolationLevel.STANDARD,
    ])
    def test_below_strict_does_not_meet_strict_threshold(self, level):
        assert level.value < IsolationLevel.STRICT.value


class TestMaximumTriggersAllChecks:
    """MAXIMUM must NOT skip any safety check (the original bug)."""

    def test_maximum_meets_standard_threshold(self):
        assert IsolationLevel.MAXIMUM.value >= IsolationLevel.STANDARD.value

    def test_maximum_meets_strict_threshold(self):
        assert IsolationLevel.MAXIMUM.value >= IsolationLevel.STRICT.value

    def test_maximum_does_not_skip_temp_workspace(self):
        # create_temp_workspace returns None only when level.value < STRICT.value.
        # MAXIMUM must NOT return None.
        assert not (IsolationLevel.MAXIMUM.value < IsolationLevel.STRICT.value)
        sandbox = Sandbox(SandboxConfig(level=IsolationLevel.MAXIMUM))
        tmp = sandbox.create_temp_workspace()
        try:
            assert tmp is not None, "MAXIMUM must create an isolated temp workspace"
            assert Path(tmp).exists()
        finally:
            if tmp:
                try:
                    Path(tmp).rmdir()
                except OSError:
                    pass

    def test_maximum_command_prefix_on_linux(self):
        sandbox = Sandbox(SandboxConfig(level=IsolationLevel.MAXIMUM))
        prefix = sandbox.get_command_prefix()
        if sandbox._os_type == "Linux":
            assert prefix and prefix[0] == "unshare"
        else:
            assert prefix == []


class TestStrictNotMistakenAsBelowStandard:
    """STRICT must NOT be flagged as below STANDARD (the original bug)."""

    def test_strict_meets_standard_threshold(self):
        assert IsolationLevel.STRICT.value >= IsolationLevel.STANDARD.value

    def test_strict_meets_strict_threshold(self):
        assert IsolationLevel.STRICT.value >= IsolationLevel.STRICT.value
        assert not (IsolationLevel.STRICT.value < IsolationLevel.STRICT.value)

    def test_strict_creates_temp_workspace(self):
        sandbox = Sandbox(SandboxConfig(level=IsolationLevel.STRICT))
        tmp = sandbox.create_temp_workspace()
        try:
            assert tmp is not None, "STRICT must create an isolated temp workspace"
        finally:
            if tmp:
                try:
                    Path(tmp).rmdir()
                except OSError:
                    pass


class TestNoneSkipsChecks:
    """NONE must skip all gated checks."""

    def test_none_below_standard_threshold(self):
        assert IsolationLevel.NONE.value < IsolationLevel.STANDARD.value

    def test_none_below_strict_threshold(self):
        assert IsolationLevel.NONE.value < IsolationLevel.STRICT.value

    def test_none_no_temp_workspace(self):
        sandbox = Sandbox(SandboxConfig(level=IsolationLevel.NONE))
        assert sandbox.create_temp_workspace() is None

    def test_none_no_command_prefix(self):
        sandbox = Sandbox(SandboxConfig(level=IsolationLevel.NONE))
        assert sandbox.get_command_prefix() == []


class TestSandboxBehaviorAcrossLevels:
    """End-to-end behavior of Sandbox methods across all 5 levels."""

    def test_temp_workspace_only_at_strict_or_above(self):
        for level in LEVELS_ASC:
            sandbox = Sandbox(SandboxConfig(level=level))
            tmp = sandbox.create_temp_workspace()
            try:
                if level.value >= IsolationLevel.STRICT.value:
                    assert tmp is not None, f"{level.name} should create workspace"
                else:
                    assert tmp is None, f"{level.name} should NOT create workspace"
            finally:
                if tmp:
                    try:
                        Path(tmp).rmdir()
                    except OSError:
                        pass

    def test_command_prefix_only_strict_or_above_on_linux(self):
        for level in LEVELS_ASC:
            sandbox = Sandbox(SandboxConfig(level=level))
            prefix = sandbox.get_command_prefix()
            if sandbox._os_type == "Linux" and level.value >= IsolationLevel.STRICT.value:
                assert prefix and prefix[0] == "unshare"
            else:
                assert prefix == []

    def test_validate_maxmium_allows_allowlisted_command(self):
        # Sanity: MAXIMUM should still validate a normal allowed command.
        cwd_dir = str(Path(__file__).parent)
        sandbox = Sandbox(SandboxConfig(level=IsolationLevel.MAXIMUM,
                                       allowed_paths=[cwd_dir]))
        allowed, _ = sandbox.validate("ls", cwd=cwd_dir)
        assert allowed

    def test_status_reports_level_for_all_levels(self):
        for level in LEVELS_ASC:
            sandbox = Sandbox(SandboxConfig(level=level))
            status = sandbox.status
            assert status["level"] == level.value
