"""Unit tests for the lightweight LAAP MCP client/server stack."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from typing import Any, Dict

import pytest

from laap.mcp.base import MCPMessage
from laap.mcp.client import MCPClient
from laap.mcp.config import MCPConfig
from laap.mcp.server import MCPServer
from laap.mcp.transports import InMemoryTransport
from laap.tools.base import ToolResult
from laap.tools.tool_registry import register_tool


# ── helpers ──────────────────────────────────────────────────────────


@pytest.fixture
def sample_tool():
    """Register a simple tool and clean it up after the test."""
    name = "test_mcp_greet"

    @register_tool(name=name, category="test")
    def greet(who: str, greeting: str = "hello") -> ToolResult:
        return ToolResult(success=True, output=f"{greeting}, {who}!")

    yield name
    from laap.tools.tool_registry import TOOL_REGISTRY
    TOOL_REGISTRY.pop(name, None)


async def _run_roundtrip(sample_tool: str):
    """Create a server/client pair and exercise the protocol."""
    server_transport, client_transport = InMemoryTransport.create_pair()
    server = MCPServer(server_transport)
    client = MCPClient(client_transport)

    await server.start()
    try:
        init = await client.initialize()
        assert init.get("protocolVersion") == "2024-11-05"
        assert init["serverInfo"]["name"] == "laap-mcp"

        tools = await client.list_tools()
        names = {t["name"] for t in tools}
        assert sample_tool in names

        result = await client.call_tool(sample_tool, {"who": "MCP", "greeting": "hi"})
        content = result.get("content", [])
        assert content
        text = json.loads(content[0]["text"])
        assert text["success"] is True
        assert text["output"] == "hi, MCP!"
    finally:
        await client.close()
        await server.stop()


# ── tests ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mcp_message_roundtrip(sample_tool: str):
    """MCPServer + MCPClient over InMemoryTransport can initialize, list and call tools."""
    await _run_roundtrip(sample_tool)


@pytest.mark.asyncio
async def test_server_handles_unknown_method():
    """The server returns a JSON-RPC method-not-found error."""
    server_transport, client_transport = InMemoryTransport.create_pair()
    server = MCPServer(server_transport)
    client = MCPClient(client_transport)
    await server.start()
    try:
        response = await client._request("foo/bar", {})
        assert response.error is not None
        assert response.error["code"] == -32601
        assert "foo/bar" in response.error["message"]
    finally:
        await client.close()
        await server.stop()


@pytest.mark.asyncio
async def test_server_tool_not_found():
    """tools/call raises when the tool is not registered."""
    server_transport, client_transport = InMemoryTransport.create_pair()
    server = MCPServer(server_transport)
    client = MCPClient(client_transport)
    await server.start()
    try:
        with pytest.raises(RuntimeError, match="Tool 'nonexistent_tool' not found"):
            await client.call_tool("nonexistent_tool", {})
    finally:
        await client.close()
        await server.stop()


@pytest.mark.asyncio
async def test_in_memory_transport_pair():
    """InMemoryTransport pairs route messages bidirectionally."""
    a, b = InMemoryTransport.create_pair()
    msg = MCPMessage(id="1", method="ping", params={})
    await a.send(msg)
    received = await b.receive()
    assert received is not None
    assert received.method == "ping"
    assert received.id == "1"
    await a.close()
    await b.close()


def test_mcp_config_load_from_file():
    """MCPConfig loads mcpServers entries from a JSON file."""
    config_data = {
        "mcpServers": {
            "test-server": {
                "command": "python",
                "args": ["-m", "laap.mcp_server"],
                "env": {"FOO": "bar"},
            }
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "mcp_config.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        config = MCPConfig.load_from_file(path)
        assert config.server_names() == ["test-server"]
        entry = config.get_server_config("test-server")
        assert entry["command"] == "python"
        assert entry["args"] == ["-m", "laap.mcp_server"]
        assert entry["env"]["FOO"] == "bar"


def test_mcp_config_load_from_dict():
    """MCPConfig can be constructed directly from a dict."""
    config = MCPConfig.load_from_dict({
        "mcpServers": {
            "sse-server": {
                "transport": "sse",
                "url": "http://127.0.0.1:8766/sse",
            }
        }
    })
    assert config.server_names() == ["sse-server"]
    entry = config.get_server_config("sse-server")
    assert entry["transport"] == "sse"
    assert entry["url"] == "http://127.0.0.1:8766/sse"


def test_mcp_config_missing_server_returns_none():
    """get_server_config/get_client return None for unknown servers."""
    config = MCPConfig.load_from_dict({"mcpServers": {}})
    assert config.get_server_config("missing") is None
    assert config.get_client("missing") is None


@pytest.mark.asyncio
async def test_server_handles_ping():
    """ping returns an empty result."""
    server_transport, client_transport = InMemoryTransport.create_pair()
    server = MCPServer(server_transport)
    client = MCPClient(client_transport)
    await server.start()
    try:
        response = await client._request("ping", {})
        assert response.error is None
        assert response.result == {}
    finally:
        await client.close()
        await server.stop()


@pytest.mark.asyncio
async def test_server_handles_resources_and_prompts():
    """resources/list, prompts/list return empty collections."""
    server_transport, client_transport = InMemoryTransport.create_pair()
    server = MCPServer(server_transport)
    client = MCPClient(client_transport)
    await server.start()
    try:
        resources = await client._request("resources/list", {})
        assert resources.error is None
        assert resources.result.get("resources") == []

        templates = await client._request("resources/templates/list", {})
        assert templates.error is None
        assert templates.result.get("resourceTemplates") == []

        prompts = await client._request("prompts/list", {})
        assert prompts.error is None
        assert prompts.result.get("prompts") == []

        missing_prompt = await client._request("prompts/get", {"name": "missing"})
        assert missing_prompt.error is not None
        assert missing_prompt.error["code"] == -32602
    finally:
        await client.close()
        await server.stop()


@pytest.mark.asyncio
async def test_server_ignores_initialized_notification():
    """notifications/initialized does not produce a response."""
    server_transport, client_transport = InMemoryTransport.create_pair()
    server = MCPServer(server_transport)
    await server.start()
    try:
        await server_transport.send(
            MCPMessage(id="n1", method="notifications/initialized", params={})
        )
        # Give the server a moment to process the notification.
        await asyncio.sleep(0.05)
        # No response should have been written back.
        assert client_transport._send.empty()
    finally:
        await server.stop()
