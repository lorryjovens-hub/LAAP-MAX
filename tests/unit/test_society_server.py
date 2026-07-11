"""Unit tests for laap.api.society_server.

Tests cover:
- All 8 REST endpoints under /society/*
- Helper functions set_society_state / get_society_state
- Empty-state and populated-state responses
- Optional query parameters (agent_id)
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from laap.api import society_server
from laap.api.society_server import (
    get_society_state,
    router,
    set_society_state,
)

# ── 默认状态快照 (用于 autouse fixture 在每个测试前重置模块级状态) ──

_DEFAULT_STATE: dict = {
    "sandboxes": [],
    "agents": [],
    "suggestions": [],
    "lifeforms": [],
    "psi_status": {},
    "causal_graph": {"nodes": [], "edges": []},
    "rsi_suggestions": [],
    "memory_status": {"layers": []},
}


@pytest.fixture(autouse=True)
def _reset_society_state():
    """每个测试前重置模块级 ``_society_state``，避免测试间状态污染。"""
    society_server._society_state.clear()
    society_server._society_state.update({k: v for k, v in _DEFAULT_STATE.items()})
    yield


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestSocietyServer:
    def test_list_sandboxes_empty(self, client):
        r = client.get("/society/sandboxes")
        assert r.status_code == 200
        assert r.json() == {"sandboxes": []}

    def test_list_sandboxes_with_data(self, client):
        set_society_state("sandboxes", [{"id": "sb1", "status": "active"}])
        r = client.get("/society/sandboxes")
        assert r.status_code == 200
        assert r.json()["sandboxes"] == [{"id": "sb1", "status": "active"}]

    def test_list_agents(self, client):
        set_society_state("agents", [{"id": "a1"}])
        r = client.get("/society/agents")
        assert r.status_code == 200
        assert "agents" in r.json()

    def test_list_suggestions(self, client):
        r = client.get("/society/suggestions")
        assert r.status_code == 200
        assert "suggestions" in r.json()

    def test_list_lifeforms(self, client):
        r = client.get("/society/lifeforms")
        assert r.status_code == 200
        assert "lifeforms" in r.json()

    def test_get_psi_status_no_agent_id(self, client):
        set_society_state("psi_status", {"a1": {"mood": "happy"}})
        r = client.get("/society/psi-status")
        assert r.status_code == 200
        assert "psi_status" in r.json()

    def test_get_psi_status_with_agent_id(self, client):
        set_society_state("psi_status", {"a1": {"mood": "happy"}})
        r = client.get("/society/psi-status?agent_id=a1")
        assert r.status_code == 200
        assert r.json()["agent_id"] == "a1"
        assert r.json()["psi_status"]["mood"] == "happy"

    def test_get_causal_graph(self, client):
        r = client.get("/society/causal-graph")
        assert r.status_code == 200
        assert "nodes" in r.json()
        assert "edges" in r.json()

    def test_list_rsi_suggestions(self, client):
        r = client.get("/society/rsi-suggestions")
        assert r.status_code == 200
        assert "suggestions" in r.json()

    def test_get_memory_status(self, client):
        r = client.get("/society/memory-status")
        assert r.status_code == 200
        assert "memory_status" in r.json()

    def test_get_society_state_returns_dict(self):
        state = get_society_state()
        assert isinstance(state, dict)

    def test_set_society_state_updates_key(self):
        set_society_state("test_key", {"v": 1})
        assert get_society_state()["test_key"] == {"v": 1}
