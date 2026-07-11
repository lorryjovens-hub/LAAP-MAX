"""Unit tests for the Hermes-style LAAP CLI foundation."""

from __future__ import annotations

from typing import Any, List

import pytest
from rich.console import Console

from laap.cli.commands import resolve, COMMAND_REGISTRY
from laap.cli.hermes_cli import (
    APPROVAL_CHOICES,
    HermesMessage,
    HermesStyleCLI,
    TOOL_PROGRESS_MODES,
)
from laap.store.session_manager import FileSessionStore, SessionManager


class CollectingConsole(Console):
    """Console that captures output to a string buffer for tests."""

    def __init__(self) -> None:
        super().__init__(
            force_terminal=True,
            color_system="truecolor",
            record=True,
        )
        self._captured: List[str] = []

    def print(self, *args: Any, **kwargs: Any) -> None:
        text = " ".join(str(a) for a in args)
        self._captured.append(text)
        super().print(*args, **kwargs)

    @property
    def output(self) -> str:
        return "\n".join(self._captured)


def make_cli(tmp_path: Any, inputs: List[str] | None = None) -> HermesStyleCLI:
    """Create a HermesStyleCLI wired to a temp store and scripted input."""
    inputs = inputs or []
    input_iter = iter(inputs)

    def fake_input(prompt: str = "") -> str:
        try:
            return next(input_iter)
        except StopIteration:
            raise EOFError()

    store = FileSessionStore(str(tmp_path))
    console = CollectingConsole()
    return HermesStyleCLI(
        session_id="test_session",
        console=console,
        session_manager=SessionManager(store),
        input_fn=fake_input,
        progress_mode="new",
    )


# ── Command registry ──


@pytest.mark.parametrize(
    "name,expected",
    [
        ("help", "help"),
        ("h", "help"),
        ("?", "help"),
        ("new", "new"),
        ("clear", "new"),
        ("history", "history"),
        ("hist", "history"),
        ("save", "save"),
        ("load", "load"),
        ("sessions", "sessions"),
        ("snapshots", "sessions"),
        ("resume", "resume"),
        ("branch", "branch"),
        ("fork", "branch"),
        ("tools", "tools"),
        ("models", "models"),
        ("config", "config"),
        ("exit", "exit"),
        ("quit", "exit"),
        ("bye", "exit"),
        ("unknown", None),
    ],
)
def test_command_registry_resolves_slash_commands(name: str, expected: str | None) -> None:
    """The central registry resolves canonical names and aliases."""
    assert resolve(name) == expected


def test_required_hermes_commands_are_registered() -> None:
    """All required Hermes slash commands exist in the registry."""
    required = {"help", "new", "history", "save", "load", "sessions",
                "resume", "branch", "tools", "models", "config", "exit"}
    registered = {cmd["name"] for cmd in COMMAND_REGISTRY}
    assert required <= registered


# ── Session persistence ──


def test_session_save_and_load_roundtrip(tmp_path: Any) -> None:
    """Messages saved via /save can be loaded back with /load."""
    cli = make_cli(tmp_path)
    cli.messages = [
        HermesMessage(role="user", content="hello"),
        HermesMessage(role="assistant", content="Echo: hello"),
    ]

    cli.save_session("roundtrip")
    loaded_cli = make_cli(tmp_path)
    assert loaded_cli.load_session("roundtrip") is True

    assert len(loaded_cli.messages) == 2
    assert loaded_cli.messages[0].role == "user"
    assert loaded_cli.messages[0].content == "hello"
    assert loaded_cli.messages[1].role == "assistant"
    assert loaded_cli.messages[1].content == "Echo: hello"
    assert loaded_cli.session_id == "roundtrip"


def test_load_missing_session_returns_false(tmp_path: Any) -> None:
    """Loading a non-existent session returns False without raising."""
    cli = make_cli(tmp_path)
    assert cli.load_session("does_not_exist") is False


def test_sessions_command_lists_saved_sessions(tmp_path: Any) -> None:
    """/sessions lists sessions persisted in the store."""
    cli = make_cli(tmp_path)
    cli.save_session("alpha")
    cli.save_session("beta")

    sessions = cli.list_sessions()
    names = {s.session_id for s in sessions}
    assert {"alpha", "beta"} <= names


# ── Approval callback ──


@pytest.mark.parametrize("choice,expected_allowed,expected_decision", [
    ("y", True, "y"),
    ("yes", True, "y"),
    ("once", True, "once"),
    ("session", True, "session"),
    ("always", True, "always"),
    ("n", False, "n"),
    ("", False, "n"),
    ("bogus", False, "n"),
])
def test_approval_callback_returns_correct_choices(
    tmp_path: Any,
    choice: str,
    expected_allowed: bool,
    expected_decision: str,
) -> None:
    """handle_approval maps user input to the correct (allowed, decision) pair."""
    cli = make_cli(tmp_path, inputs=[choice])
    allowed, decision = cli.handle_approval(
        tool_name="dangerous_tool",
        arguments={"cmd": "rm -rf /"},
        dangerous_score=0.9,
    )
    assert allowed is expected_allowed
    assert decision == expected_decision


def test_session_approval_persists_across_calls(tmp_path: Any) -> None:
    """Choosing 'session' causes subsequent calls to auto-approve."""
    cli = make_cli(tmp_path, inputs=["session"])
    allowed, decision = cli.handle_approval("tool_a", {})
    assert allowed is True
    assert decision == "session"

    # Second call should be auto-approved without consuming input.
    allowed2, decision2 = cli.handle_approval("tool_a", {})
    assert allowed2 is True
    assert decision2 == "session"


def test_always_approval_persists_across_calls(tmp_path: Any) -> None:
    """Choosing 'always' causes subsequent calls to auto-approve."""
    cli = make_cli(tmp_path, inputs=["always"])
    allowed, decision = cli.handle_approval("tool_b", {})
    assert allowed is True
    assert decision == "always"

    allowed2, decision2 = cli.handle_approval("tool_b", {})
    assert allowed2 is True
    assert decision2 == "always"


def test_progress_mode_off_denies_approval(tmp_path: Any) -> None:
    """When progress mode is 'off', approval is denied immediately."""
    store = FileSessionStore(str(tmp_path))
    cli = HermesStyleCLI(
        session_id="test_session",
        session_manager=SessionManager(store),
        progress_mode="off",
        input_fn=lambda _: "y",
    )
    allowed, decision = cli.handle_approval("tool_c", {})
    assert allowed is False
    assert decision == "n"


# ── REPL dispatch ──


def test_dispatch_exit_sets_running_false(tmp_path: Any) -> None:
    """Dispatching /exit stops the REPL."""
    cli = make_cli(tmp_path)
    assert cli.running is True
    cli.dispatch("/exit")
    assert cli.running is False


def test_dispatch_unknown_command_warns(tmp_path: Any) -> None:
    """Dispatching an unknown slash command logs a warning."""
    cli = make_cli(tmp_path)
    cli.dispatch("/notacommand")
    assert "Unknown command" in cli.console.output
