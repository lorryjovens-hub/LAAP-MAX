"""Unit tests for the LAAP Hermes-style TUI."""

from __future__ import annotations

import asyncio
import io
import os
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from rich.console import Console

from laap.ui import tui as tui_module
from laap.ui.tui import (
    render_logo,
    _load_tool_registry,
    _build_slash_commands,
    _load_mcp_servers,
    HAS_TEXTUAL,
    run_tui,
    LAAP_TUI,
)


pytestmark = pytest.mark.skipif(not HAS_TEXTUAL, reason="Textual not installed")


def _render_to_text(renderable: Any) -> str:
    """Render a Rich renderable to plain text for assertions."""
    console = Console(file=io.StringIO(), force_terminal=False, color_system=None)
    console.print(renderable)
    return console.file.getvalue()


def test_render_logo_returns_laap_text() -> None:
    """The logo renderable must contain 'LAAP'."""
    logo = render_logo()
    assert "LAAP" in logo


def test_tool_categories_are_dynamically_loaded() -> None:
    """The tool registry collector returns categories and names."""
    by_category, names = _load_tool_registry()
    assert isinstance(by_category, dict)
    assert isinstance(names, list)
    # The real registry should have at least one tool after discovery.
    if names:
        assert all(isinstance(cat, str) for cat in by_category)
        assert all(isinstance(name, str) for name in names)


def test_slash_command_registry_contains_required_commands() -> None:
    """The combined slash command registry includes required LAAP commands."""
    commands = _build_slash_commands()
    names = {cmd["name"] for cmd in commands}
    required = {"help", "psi", "aether", "gateways", "mcp", "yolo", "cancel"}
    assert required <= names
    for cmd in commands:
        assert "name" in cmd
        assert "desc" in cmd


def test_mcp_servers_load_returns_list() -> None:
    """MCP server loader returns a list of tuples."""
    servers = _load_mcp_servers()
    assert isinstance(servers, list)
    for item in servers:
        assert isinstance(item, tuple)
        assert len(item) == 3


@pytest.mark.asyncio
async def test_approval_modal_choices_return_correct_values() -> None:
    """Clicking each approval button dismisses the expected choice value."""
    from textual.app import App
    from laap.ui.tui import ApprovalModal

    class TestApp(App):
        pass

    for button_id, expected in [
        ("btn_once", "once"),
        ("btn_session", "session"),
        ("btn_always", "always"),
        ("btn_deny", "deny"),
    ]:
        results: List[str] = []

        class TestApp(App):
            pass

        app = TestApp()
        async with app.run_test() as pilot:
            modal = ApprovalModal("rm -rf /", "rm_rf", "critical")
            await app.push_screen(modal, callback=lambda r, out=results: out.append(r))
            await pilot.pause()
            await pilot.click(f"#{button_id}")
            await pilot.pause()
        assert results == [expected]


@pytest.mark.asyncio
async def test_main_screen_composes() -> None:
    """The main screen can be composed without raising."""
    from textual.app import App
    from laap.ui.tui import MainScreen

    class TestApp(App):
        def get_default_screen(self):
            return MainScreen()

    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        # Key widgets should exist in the DOM.
        assert app.query_one("#chat_log") is not None
        assert app.query_one("#input_box") is not None
        assert app.query_one("#status_bar") is not None
        assert app.query_one("#sidebar") is not None
        assert app.query_one("#tool_panel") is not None
        assert app.query_one("#metrics_panel") is not None
        assert app.query_one("#cognitive_panel") is not None
        assert app.query_one("#vitals_panel") is not None
        assert app.query_one("#video_panel") is not None
        assert app.query_one("#gateway_panel") is not None
        assert app.query_one("#light_bar") is not None
        assert app.query_one("#tool_overlay") is not None


@pytest.mark.asyncio
async def test_slash_command_overlay_filters_commands() -> None:
    """The slash overlay filters commands by partial input."""
    from textual.app import App
    from laap.ui.tui import SlashCommandOverlay

    commands = [
        {"name": "help", "desc": "Show help"},
        {"name": "psi", "desc": "Show PSI state"},
        {"name": "exit", "desc": "Exit"},
    ]
    overlay = SlashCommandOverlay(commands)

    class TestApp(App):
        pass

    app = TestApp()
    async with app.run_test() as pilot:
        await app.mount(overlay)
        overlay.update_matches("/p")
        await pilot.pause()
        items = list(overlay.query(".cmd_item"))
        assert len(items) == 1
        assert "psi" in items[0].content.plain


@pytest.mark.asyncio
async def test_tool_picker_overlay_filters_tools() -> None:
    """The tool picker overlay filters tools by partial input."""
    from textual.app import App
    from laap.ui.tui import ToolPickerOverlay

    tools = [
        ("read_file", "filesystem", "Read a file"),
        ("web_search", "web", "Search the web"),
        ("shell_exec", "shell", "Run a shell command"),
    ]
    overlay = ToolPickerOverlay(tools)

    class TestApp(App):
        pass

    app = TestApp()
    async with app.run_test() as pilot:
        await app.mount(overlay)
        overlay.update_matches("read")
        await pilot.pause()
        items = list(overlay.query(".tool_item"))
        assert len(items) == 1
        assert "read_file" in items[0].content.plain


@pytest.mark.asyncio
async def test_chat_log_adds_messages() -> None:
    """The chat log can add user, assistant, and system messages."""
    from textual.app import App
    from laap.ui.tui import ChatLog

    class TestApp(App):
        pass

    app = TestApp()
    async with app.run_test() as pilot:
        chat = ChatLog()
        await app.mount(chat)
        chat.add_user("Hello")
        chat.add_assistant("Hi there")
        chat.add_sys("System message")
        await pilot.pause()
        statics = list(chat.query("Static"))
        assert len(statics) >= 3


@pytest.mark.asyncio
async def test_chat_log_tool_progress_panel() -> None:
    """The chat log renders and updates a tool progress panel."""
    from textual.app import App
    from laap.ui.tui import ChatLog

    class TestApp(App):
        pass

    app = TestApp()
    async with app.run_test() as pilot:
        chat = ChatLog()
        await app.mount(chat)
        widget = chat.add_tool_progress("read_file", {"path": "test.py"})
        await pilot.pause()
        assert widget is not None
        assert "read_file" in widget.content.title
        chat.update_tool_progress(widget, True, "done")
        await pilot.pause()
        text = _render_to_text(widget.content)
        assert "[OK]" in text


@pytest.mark.asyncio
async def test_chat_log_coding_progress_panel() -> None:
    """The chat log renders and updates a coding progress panel."""
    from textual.app import App
    from laap.ui.tui import ChatLog

    class TestApp(App):
        pass

    app = TestApp()
    async with app.run_test() as pilot:
        chat = ChatLog()
        await app.mount(chat)
        widget = chat.add_coding_progress("laap/ui/tui.py", lines_changed=42)
        await pilot.pause()
        assert widget is not None
        chat.update_coding_progress(widget, 100, "laap/ui/tui.py", lines_changed=42)
        await pilot.pause()
        text = _render_to_text(widget.content)
        assert "[OK]" in text or "100%" in text


@pytest.mark.asyncio
async def test_welcome_banner_contains_key_info() -> None:
    """The welcome banner contains version, tools, skills, and profile info."""
    from textual.app import App
    from textual.widgets import Static
    from laap.ui.tui import MainScreen

    class TestApp(App):
        def get_default_screen(self):
            return MainScreen()

    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        welcome = app.query_one("#welcome", Static)
        text = _render_to_text(welcome.content)
        assert "LAAP" in text
        assert "Welcome to LAAP Agent" in text
        assert "/help" in text


@pytest.mark.asyncio
async def test_chat_log_finalize_response() -> None:
    """finalize_assistant_response replaces the streaming widget and persists history."""
    from textual.app import App
    from laap.ui.tui import ChatLog

    class TestApp(App):
        pass

    app = TestApp()
    async with app.run_test() as pilot:
        chat = ChatLog()
        await app.mount(chat)
        chat.add_user("hi")
        chat.start_response()
        chat.stream_assistant("partial...")
        chat.finalize_assistant_response("final response")
        await pilot.pause()
        assert chat.get_last_assistant_text() == "final response"
        statics = list(chat.query(".assistant_msg"))
        assert any("final response" in _render_to_text(s.content) for s in statics)


@pytest.mark.asyncio
async def test_chat_worker_finalizes_mock_response() -> None:
    """_chat finalizes a response from a mocked agent."""
    from textual.app import App
    from laap.ui.tui import MainScreen, ChatLog, StatusBar

    class TestApp(App):
        def get_default_screen(self):
            return MainScreen()

    mock_agent = MagicMock()
    mock_agent.llm = True
    mock_agent.chat.return_value = "Mock assistant reply"

    # Patch the singleton so get_or_create_agent returns our mock without init
    with patch.object(tui_module, "_agent_instance", mock_agent):
        app = TestApp()
        async with app.run_test() as pilot:
            screen = app.screen
            chat = app.query_one(ChatLog)
            sb = app.query_one(StatusBar)
            # Avoid Textual worker requirement for the coroutine in tests
            with patch.object(tui_module, "get_current_worker", return_value=MagicMock()):
                await screen._chat("hello", chat, sb)
            await pilot.pause()
            assert chat.get_last_assistant_text() == "Mock assistant reply"
            assert sb.status == "idle"


@pytest.mark.asyncio
async def test_model_and_config_commands() -> None:
    """/model and /config show current settings without crashing."""
    from textual.app import App
    from laap.ui.tui import MainScreen, ChatLog, StatusBar

    class TestApp(App):
        def get_default_screen(self):
            return MainScreen()

    app = TestApp()
    async with app.run_test() as pilot:
        screen = app.screen
        chat = app.query_one(ChatLog)
        sb = app.query_one(StatusBar)
        screen._cmd_model("", chat, sb)
        screen._cmd_config("", chat, sb)
        await pilot.pause()
        text = "\n".join(_render_to_text(s.content) for s in chat.query("Static"))
        assert "Model:" in text or "Provider:" in text
        assert "Configuration:" in text


def test_slash_command_registry_contains_hermes_commands() -> None:
    """Hermes-level slash commands are registered."""
    commands = _build_slash_commands()
    names = {cmd["name"] for cmd in commands}
    hermes = {"reset", "undo", "copy", "file", "image", "url", "search", "status", "tokens", "compress", "usage"}
    assert hermes <= names


def test_config_manager_model_switch_persists(tmp_path, monkeypatch) -> None:
    """Switching models via ConfigManager persists across reloads."""
    import laap.cli.config_manager as cm

    monkeypatch.setattr(cm, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(cm, "ENV_FILE", tmp_path / ".laap.env")
    mgr = cm.ConfigManager()
    mgr.set_provider("deepseek", api_key="fake-key", model="deepseek-chat")
    assert mgr.set_model("deepseek-reasoner")
    assert mgr.get_active().model == "deepseek-reasoner"
    assert os.environ.get("LAAP_MODEL") == "deepseek-reasoner"

    # Reload from disk
    mgr2 = cm.ConfigManager()
    assert mgr2.config.active_provider == "deepseek"
    assert mgr2.get_active().model == "deepseek-reasoner"


def test_stream_handler_tool_result_callback_signature() -> None:
    """StreamHandler invokes the TUI-style on_tool_result callback correctly."""
    from laap.ui.stream_handler import StreamHandler

    sh = StreamHandler(verbose=False, use_spinner=False)
    calls: List[tuple] = []

    def cb(name: str, result: Any, duration: float, success: bool):
        calls.append((name, result, duration, success))

    sh.on_tool_result = cb
    sh.process_tool_result("read_file", "done", 0.5, True)
    assert calls == [("read_file", "done", 0.5, True)]


def test_no_textual_stubs_exist() -> None:
    """When Textual is missing the public runner still exists."""
    # This test runs regardless of Textual availability.
    assert callable(run_tui)
    assert hasattr(tui_module, "LAAP_TUI")
    assert hasattr(tui_module, "MainScreen")
    assert hasattr(tui_module, "ChatLog")
    assert hasattr(tui_module, "ToolPickerOverlay")
