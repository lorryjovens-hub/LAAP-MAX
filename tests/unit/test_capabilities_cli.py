"""Tests for the LAAP --capabilities reporter and CLI flag."""

from __future__ import annotations

import subprocess
import sys

import pytest

from laap.body.capabilities import CapabilitiesReporter


@pytest.fixture
def isolated_reporter(tmp_path) -> CapabilitiesReporter:
    """Return a reporter that does not load real skills/plugins."""
    return CapabilitiesReporter(skills_dir=str(tmp_path / "no_skills"), plugins_dir=str(tmp_path / "no_plugins"))


def test_reporter_returns_non_empty_output(isolated_reporter: CapabilitiesReporter) -> None:
    """The reporter must discover at least tools/providers/gateways."""
    assert isolated_reporter.items
    assert isolated_reporter.to_table()
    assert isolated_reporter.to_markdown()


def test_known_stable_tools_are_marked_stable(isolated_reporter: CapabilitiesReporter) -> None:
    """Core tools used by the agent backfill must be reported as stable."""
    tool_statuses = {
        item["name"]: item["status"]
        for item in isolated_reporter.items
        if item["category"] == "Tools"
    }
    for name in ("read_file", "run_command", "web_search", "browser_navigate"):
        assert tool_statuses.get(name) == "stable", f"{name} should be stable"


def test_placeholder_gateways_are_marked_placeholder(isolated_reporter: CapabilitiesReporter) -> None:
    """Unimplemented gateway platforms must be honestly marked placeholder."""
    gateway_statuses = {
        item["name"]: item["status"]
        for item in isolated_reporter.items
        if item["category"] == "Gateways"
    }
    for name in ("telegram", "discord", "slack", "whatsapp", "sms"):
        assert gateway_statuses.get(name) == "placeholder", f"{name} should be placeholder"


def test_cli_capabilities_flag_prints_table() -> None:
    """`python -m laap --capabilities` must exit 0 and list capabilities."""
    result = subprocess.run(
        [sys.executable, "-m", "laap", "--capabilities"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "Tools" in result.stdout
    assert "read_file" in result.stdout
    assert "Gateways" in result.stdout
