"""Unit tests for the LAAP standalone agent CLI."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from laap.standalone import cli


def test_cli_parse_task_argument() -> None:
    """The CLI parses the --task argument and defaults."""
    args = cli.parse_args(["--task", "read README.md"])

    assert args.task == "read README.md"
    assert args.local_model == "http://localhost:11434"
    assert args.remote_fallback is False
    assert args.no_interactive is False


def test_cli_task_implies_non_interactive() -> None:
    """When --task is given the main entry point treats the session as one-shot."""
    args = cli.parse_args(["--task", "search TODO"])
    # The parser itself does not flip the flag; main() does.  Ensure the raw
    # parsed values are sufficient to detect one-shot mode.
    assert args.task is not None


def test_cli_one_shot_mode_runs_without_hanging() -> None:
    """One-shot mode processes the task and exits without blocking."""
    mock_agent = MagicMock()
    mock_agent.process = AsyncMock(
        return_value={"response": "mocked tool result"}
    )
    mock_agent.session_summary = MagicMock(
        return_value={
            "total_tokens": 0,
            "local_tokens": 0,
            "remote_tokens": 0,
            "estimated_cost_usd": 0.0,
        }
    )

    def factory(_args) -> MagicMock:
        return mock_agent

    exit_code = cli.main(["--task", "read README.md"], agent_factory=factory)

    assert exit_code == 0
    mock_agent.process.assert_awaited_once_with("read README.md")
    mock_agent.session_summary.assert_called_once()


def test_cli_parse_local_model_and_remote_fallback() -> None:
    """The CLI accepts a custom local model URL and remote fallback flag."""
    args = cli.parse_args(
        ["--task", "run tests", "--local-model", "http://ollama:11434", "--remote-fallback"]
    )

    assert args.task == "run tests"
    assert args.local_model == "http://ollama:11434"
    assert args.remote_fallback is True
