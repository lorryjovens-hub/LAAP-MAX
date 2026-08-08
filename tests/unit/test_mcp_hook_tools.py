"""Unit tests for LAAP MCP hook tools (Task 1).

Tests the 4 cognitive hook tools (laap_before_turn / laap_after_tool /
laap_after_turn / laap_cognitive_status) and the session registry.

LaapBrain is mocked to avoid starting the real PSI cognitive cycle.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
from unittest.mock import MagicMock

import pytest

from laap.mcp.server import LAAPMCPServer
from laap.mcp.session_registry import MCPSessionRegistry

# ── helpers ──────────────────────────────────────────────────────────


def _make_mock_brain():
    """Create a mock LaapBrain with realistic return values."""
    brain = MagicMock()
    brain.id = "mock-brain-001"
    brain.name = "LAAP-Brain-mock"
    brain.before_turn.return_value = "[LAAP Brain State]\n  Mode: intuitive"
    brain.after_tool.return_value = None
    brain.after_turn.return_value = None
    brain.status.return_value = {
        "version": "3.1",
        "mode": "intuitive",
        "turns": 1,
        "tools": 0,
        "biases_corrected": 0,
        "deliberations": 0,
        "skills": 6,
        "avg_gap": 0.0,
        "cortex": {
            "pfc_activation": 0.55,
            "limbic_activation": 0.5,
            "salience_signal": 0.3,
            "dmn_activation": 0.1,
            "attention_breadth": 0.5,
            "cognitive_load": 0.05,
            "integration_level": 0.7,
            "avg_gap": 0.0,
        },
        "has_native": False,
        "uptime_s": 1,
    }
    brain.to_dict.return_value = brain.status.return_value
    return brain


def _call_async(coro):
    """Run an async coroutine to completion in a fresh event loop."""
    return asyncio.run(coro)


def _get_tool_fn(server, name):
    """Extract the raw async function registered for ``name``."""
    tool = server._server._tool_manager._tools[name]
    return tool.fn


# ── fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def isolated_registry(tmp_path, monkeypatch):
    """Replace the session registry singleton with a temp-file-backed one."""
    reg = MCPSessionRegistry(file_path=str(tmp_path / "mcp_sessions.json"))
    from laap.mcp import session_registry as sr_mod

    monkeypatch.setattr(sr_mod, "get_registry", lambda: reg)
    monkeypatch.setattr("laap.mcp.server.get_registry", lambda: reg)
    return reg


@pytest.fixture
def created_brains(monkeypatch):
    """Patch LaapBrain so _get_or_create_brain returns mock brains.

    Returns a list that accumulates every mock brain created, so tests can
    assert identity / count.
    """
    created = []

    def _factory(*args, **kwargs):
        brain = _make_mock_brain()
        created.append(brain)
        return brain

    mock_cls = MagicMock(side_effect=_factory)
    monkeypatch.setattr("laap_brain.LaapBrain", mock_cls)
    return created


@pytest.fixture
def server(isolated_registry, created_brains):
    """Build a LAAPMCPServer with isolated registry and mocked brain."""
    s = LAAPMCPServer(name="test-hook-server")
    s.build_server()
    return s


# ── 1. laap_before_turn returns formatted string block ────────────────


class TestLaapBeforeTurn:
    """Tests for the laap_before_turn hook tool."""

    def test_laap_before_turn_returns_string_block(self, server):
        """Returned string must contain the LAAP cognitive context header."""
        fn = _get_tool_fn(server, "laap_before_turn")
        result = _call_async(fn(session_id="ses-001", user_message="hello world"))

        assert isinstance(result, str)
        assert "[LAAP Cognitive Context]" in result
        assert "Session: ses-001" in result
        assert "Lifeform:" in result
        assert "Needs:" in result
        assert "Emotion:" in result
        assert "Goals:" in result
        assert "Recent Memory:" in result

    def test_laap_before_turn_creates_session(self, server, isolated_registry):
        """First call registers the session and persists it to disk."""
        fn = _get_tool_fn(server, "laap_before_turn")
        _call_async(fn(session_id="ses-persist-001", user_message="hi"))

        # lifeform_id is registered in-memory
        lifeform_id = isolated_registry.get_lifeform_id("ses-persist-001")
        assert lifeform_id is not None
        assert lifeform_id.startswith("mcp-")

        # and persisted to the JSON file
        assert os.path.exists(isolated_registry.file_path)
        with open(isolated_registry.file_path, "r", encoding="utf-8") as f:
            persisted = json.load(f)
        assert "ses-persist-001" in persisted
        assert persisted["ses-persist-001"] == lifeform_id


# ── 2. laap_after_tool returns learned dict ───────────────────────────


def test_laap_after_tool_returns_learned_dict(server, created_brains):
    """laap_after_tool must return {'learned': True, ...} and call brain.after_tool."""
    fn = _get_tool_fn(server, "laap_after_tool")
    result = _call_async(
        fn(session_id="ses-tool-001", tool_name="read_file", result="file content")
    )

    assert isinstance(result, dict)
    assert result["learned"] is True
    assert "memory_id" in result
    assert result["session_id"] == "ses-tool-001"

    # Verify brain.after_tool was invoked
    assert len(created_brains) >= 1
    brain = created_brains[-1]
    brain.after_tool.assert_called_once_with("read_file", "file content")


# ── 3. laap_after_turn returns reflection dict ────────────────────────


def test_laap_after_turn_returns_reflection_dict(server, created_brains):
    """laap_after_turn must return reflection + emotion_delta dict."""
    fn = _get_tool_fn(server, "laap_after_turn")
    result = _call_async(fn(session_id="ses-turn-001", response="assistant reply text"))

    assert isinstance(result, dict)
    assert "reflection" in result
    assert "emotion_delta" in result
    assert result["session_id"] == "ses-turn-001"
    assert isinstance(result["emotion_delta"], dict)

    # Verify brain.after_turn was invoked
    brain = created_brains[-1]
    brain.after_turn.assert_called_once_with("assistant reply text")


# ── 4. laap_cognitive_status returns full dict ───────────────────────


def test_laap_cognitive_status_returns_dict(server):
    """laap_cognitive_status must return session_id + lifeform_id + cognitive fields."""
    fn = _get_tool_fn(server, "laap_cognitive_status")
    result = _call_async(fn(session_id="ses-status-001"))

    assert isinstance(result, dict)
    assert result["session_id"] == "ses-status-001"
    assert "lifeform_id" in result
    assert result["lifeform_id"]  # non-empty
    assert "needs" in result
    assert "emotion" in result
    assert "goals" in result
    assert "recent_memory" in result
    assert "uptime" in result


# ── 5. brain is cached per session ───────────────────────────────────


def test_brain_cached_per_session(server, created_brains):
    """Same session_id must yield the same LaapBrain instance."""
    b1 = server._get_or_create_brain("ses-cache-001")
    b2 = server._get_or_create_brain("ses-cache-001")
    assert b1 is b2


# ── 6. different sessions get different brains ───────────────────────


def test_different_sessions_different_brains(server, created_brains):
    """Different session_ids must yield different LaapBrain instances."""
    b1 = server._get_or_create_brain("ses-diff-001")
    b2 = server._get_or_create_brain("ses-diff-002")
    assert b1 is not b2


# ── 7. error handling returns graceful string ─────────────────────────


def test_error_handling_returns_graceful_string(
    isolated_registry, monkeypatch, tmp_path
):
    """When LaapBrain.before_turn raises, laap_before_turn must not propagate.

    Instead it should return ``[LAAP Error] <message>``.
    """
    # Patch LaapBrain so its before_turn raises.
    failing_brain = MagicMock()
    failing_brain.before_turn.side_effect = RuntimeError("brain offline")
    failing_brain.status.return_value = {
        "cortex": {},
        "mode": "x",
        "skills": 0,
        "avg_gap": 0,
        "turns": 0,
        "tools": 0,
        "biases_corrected": 0,
        "uptime_s": 0,
    }
    mock_cls = MagicMock(return_value=failing_brain)
    monkeypatch.setattr("laap_brain.LaapBrain", mock_cls)

    s = LAAPMCPServer(name="test-err-server")
    s.build_server()
    fn = _get_tool_fn(s, "laap_before_turn")

    # Must NOT raise
    result = _call_async(fn(session_id="ses-err-001", user_message="boom"))

    assert isinstance(result, str)
    assert result.startswith("[LAAP Error]")
    assert "brain offline" in result


# ── 8. MCPSessionRegistry unit tests ─────────────────────────────────


class TestMCPSessionRegistry:
    """Direct tests for the session registry persistence layer."""

    def test_register_generates_lifeform_id(self, tmp_path):
        reg = MCPSessionRegistry(file_path=str(tmp_path / "s.json"))
        lf = reg.register_session("abcdef1234567890")
        assert lf == "mcp-abcdef12"

    def test_register_persists_to_disk(self, tmp_path):
        path = str(tmp_path / "s.json")
        reg = MCPSessionRegistry(file_path=path)
        reg.register_session("ses-xyz")
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["ses-xyz"] == "mcp-ses-xyz"

    def test_register_returns_existing(self, tmp_path):
        reg = MCPSessionRegistry(file_path=str(tmp_path / "s.json"))
        lf1 = reg.register_session("ses-1")
        lf2 = reg.register_session("ses-1")
        assert lf1 == lf2

    def test_register_explicit_lifeform_id(self, tmp_path):
        reg = MCPSessionRegistry(file_path=str(tmp_path / "s.json"))
        lf = reg.register_session("ses-2", lifeform_id="custom-lf")
        assert lf == "custom-lf"

    def test_load_persisted_sessions(self, tmp_path):
        path = str(tmp_path / "s.json")
        reg1 = MCPSessionRegistry(file_path=path)
        reg1.register_session("ses-load")
        # New instance should load from disk
        reg2 = MCPSessionRegistry(file_path=path)
        assert reg2.get_lifeform_id("ses-load") == "mcp-ses-load"

    def test_list_sessions(self, tmp_path):
        reg = MCPSessionRegistry(file_path=str(tmp_path / "s.json"))
        reg.register_session("a")
        reg.register_session("b")
        sessions = reg.list_sessions()
        assert "a" in sessions
        assert "b" in sessions
