"""Example LAAP plugin that registers a mock tool."""
from __future__ import annotations

from laap.tools.tool_registry import register_tool


def mock_plugin_tool(message: str = "hello") -> str:
    """A mock tool registered by the example plugin."""
    return f"mock_plugin says: {message}"


def activate(context):
    """Called when the plugin is loaded."""
    register_tool("mock_plugin_tool", mock_plugin_tool, category="plugin")


def deactivate():
    """Called when the plugin is unloaded."""
    pass
