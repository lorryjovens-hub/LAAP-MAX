"""Tests for the LAAP plugin manager."""
from __future__ import annotations

import pytest

from laap.plugins import PluginContext, PluginManager
from laap.plugins.registry import PluginRegistry
from laap.tools.tool_registry import TOOL_REGISTRY, get_tool


def _write_plugin(base, name, entrypoint_code, manifest_extra=None):
    """Helper to create a plugin directory with plugin.yaml and main.py."""
    plugin_dir = base / name
    plugin_dir.mkdir(parents=True)
    manifest = {
        "name": name,
        "version": "0.1.0",
        "description": "test plugin",
        "entrypoint": "main",
        "dependencies": [],
    }
    if manifest_extra:
        manifest.update(manifest_extra)

    import yaml

    (plugin_dir / "plugin.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    (plugin_dir / "main.py").write_text(entrypoint_code, encoding="utf-8")
    return plugin_dir


@pytest.fixture(autouse=True)
def _clear_tool_registry():
    """Remove plugin-registered tools before and after each test."""
    before = set(TOOL_REGISTRY.keys())
    yield
    after = set(TOOL_REGISTRY.keys())
    for name in after - before:
        TOOL_REGISTRY.pop(name, None)


class TestPluginRegistry:
    def test_register_and_get(self):
        from laap.plugins.plugin import Plugin

        registry = PluginRegistry()
        plugin = Plugin(name="p1", version="1.0.0")
        registry.register(plugin)
        assert registry.get("p1") is plugin

    def test_list_plugins(self):
        from laap.plugins.plugin import Plugin

        registry = PluginRegistry()
        registry.register(Plugin(name="p1"))
        registry.register(Plugin(name="p2"))
        names = {p.name for p in registry.list_plugins()}
        assert names == {"p1", "p2"}

    def test_enable_disable(self):
        from laap.plugins.plugin import Plugin

        registry = PluginRegistry()
        registry.register(Plugin(name="p1", enabled=True))
        assert registry.disable("p1") is True
        assert registry.get("p1").enabled is False
        assert registry.enable("p1") is True
        assert registry.get("p1").enabled is True
        assert registry.disable("missing") is False


class TestPluginManager:
    def test_load_mock_plugin_registers_tool(self, tmp_path):
        plugin_dir = _write_plugin(
            tmp_path,
            "mock_plugin",
            '''
from laap.tools.tool_registry import register_tool

def mock_tool(message: str = "hello") -> str:
    return f"mock: {message}"

def activate(context):
    register_tool("mock_tool", mock_tool, category="plugin")

def deactivate():
    pass
''',
        )

        manager = PluginManager(str(tmp_path))
        result = manager.load(str(plugin_dir))

        assert result is True
        assert manager.registry.get("mock_plugin") is not None
        assert manager.registry.get("mock_plugin").enabled is True
        assert get_tool("mock_tool") is not None

    def test_load_all_isolates_failure(self, tmp_path):
        _write_plugin(
            tmp_path,
            "good_plugin",
            '''
from laap.tools.tool_registry import register_tool

def good_tool() -> str:
    return "good"

def activate(context):
    register_tool("good_tool", good_tool, category="plugin")
''',
        )
        _write_plugin(
            tmp_path,
            "bad_plugin",
            '''
def activate(context):
    raise RuntimeError("boom")
''',
        )

        manager = PluginManager(str(tmp_path))
        results = manager.load_all()

        assert results == {"good_plugin": True, "bad_plugin": False}
        assert manager.registry.get("good_plugin").enabled is True
        assert manager.registry.get("bad_plugin").enabled is False
        assert get_tool("good_tool") is not None

    def test_unload_calls_deactivate(self, tmp_path):
        plugin_dir = _write_plugin(
            tmp_path,
            "unloadable_plugin",
            '''
state = {"active": True}

def activate(context):
    state["active"] = True

def deactivate():
    state["active"] = False
''',
        )

        manager = PluginManager(str(tmp_path))
        assert manager.load(str(plugin_dir)) is True
        assert "unloadable_plugin" in {p.name for p in manager.list_plugins()}

        assert manager.unload("unloadable_plugin") is True
        assert manager.registry.get("unloadable_plugin") is None

    def test_unload_unknown_plugin_returns_false(self, tmp_path):
        manager = PluginManager(str(tmp_path))
        assert manager.unload("nonexistent") is False

    def test_load_missing_manifest_returns_false(self, tmp_path):
        empty_dir = tmp_path / "empty_plugin"
        empty_dir.mkdir()
        manager = PluginManager(str(tmp_path))
        assert manager.load(str(empty_dir)) is False

    def test_load_missing_dependency_marks_disabled(self, tmp_path):
        plugin_dir = _write_plugin(
            tmp_path,
            "needy_plugin",
            '''
def activate(context):
    pass
''',
            manifest_extra={"dependencies": ["this_module_does_not_exist_12345"]},
        )

        manager = PluginManager(str(tmp_path))
        result = manager.load(str(plugin_dir))

        assert result is False
        assert manager.registry.get("needy_plugin").enabled is False
