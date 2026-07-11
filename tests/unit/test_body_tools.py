"""Tests for laap.body.tools unified tool registry API."""

from __future__ import annotations

import laap.body.tools as body_tools


class TestBodyTools:
    def test_get_tool_browser_navigate_is_callable(self):
        fn = body_tools.get_tool("browser_navigate")
        assert callable(fn)

    def test_list_tools_returns_at_least_15(self):
        tools = body_tools.list_tools()
        assert len(tools) >= 15
        for tool in tools:
            assert isinstance(tool, dict)
            assert "name" in tool
            assert "category" in tool
            assert "schema" in tool

    def test_get_tool_schema_run_command(self):
        schema = body_tools.get_tool_schema("run_command")
        assert isinstance(schema, dict)
        assert schema.get("type") == "object"
        assert "properties" in schema
        properties = schema["properties"]
        assert "command" in properties
        assert isinstance(properties["command"], dict)
        assert "type" in properties["command"]
        assert "required" in schema
        assert "command" in schema["required"]

    def test_list_tools_category_filter(self):
        browser_tools = body_tools.list_tools(category="browser")
        names = [t["name"] for t in browser_tools]
        assert any(n.startswith("browser_") for n in names)
        for tool in browser_tools:
            assert tool["category"] == "browser"

    def test_discover_actors_returns_capability_names(self):
        actors = body_tools.discover_actors()
        assert isinstance(actors, list)
        assert "browser_navigate" in actors
        assert "run_command" in actors
        assert "read_file" in actors
