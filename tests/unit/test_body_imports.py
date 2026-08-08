"""Tests for laap.body public API imports."""

from __future__ import annotations

import types

import laap.body
from laap.body import (
    BodySystem,
    create_default_body_system,
    gateway,
    llm,
    mcp,
    plugins,
    skills,
    tools,
)
from laap.body.adapters import HermesBodyAdapter


class TestBodyImports:
    """Verify that all public body-layer entries can be imported."""

    def test_public_submodules_are_modules(self):
        for name in ("tools", "llm", "mcp", "skills", "plugins", "gateway"):
            mod = getattr(laap.body, name)
            assert isinstance(mod, types.ModuleType), f"{name} should be a module"

    def test_public_submodules_exposed_in_all(self):
        assert set(["tools", "llm", "mcp", "skills", "plugins", "gateway"]).issubset(
            laap.body.__all__
        )

    def test_create_default_body_system(self):
        body = create_default_body_system()
        assert isinstance(body, BodySystem)
        assert body.tools is tools
        assert body.llm is llm
        assert body.mcp is mcp
        assert body.skills is skills
        assert body.plugins is plugins
        assert body.gateway is gateway
        assert body.config == {}

    def test_create_default_body_system_with_config(self):
        body = create_default_body_system(config={"foo": "bar"})
        assert body.config == {"foo": "bar"}

    def test_hermes_adapter_importable_and_noop(self):
        adapter = HermesBodyAdapter()
        body = adapter.adapt()
        assert isinstance(body, BodySystem)
        assert adapter.status()["available"] is False
