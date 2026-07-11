"""Unit tests for the aggregated /health endpoint (Task 12)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture
def app():
    from laap.api.server import app

    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestHealthAggregation:
    def test_health_returns_200_when_all_up(self, client):
        # Mock both checks to return "up"
        with (
            patch("laap.api.server._check_mcp_status", return_value="up"),
            patch("laap.api.server._check_bus_status", return_value="up"),
        ):
            r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert data["services"]["api"] == "up"
        assert data["services"]["mcp"] == "up"
        assert data["services"]["cognitive_bus"] == "up"
        assert "uptime" in data
        assert isinstance(data["uptime"], (int, float))

    def test_health_returns_200_degraded_when_bus_down(self, client):
        with (
            patch("laap.api.server._check_mcp_status", return_value="up"),
            patch("laap.api.server._check_bus_status", return_value="down"),
        ):
            r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "degraded"
        assert data["services"]["cognitive_bus"] == "down"

    def test_health_returns_200_degraded_when_mcp_down(self, client):
        with (
            patch("laap.api.server._check_mcp_status", return_value="down"),
            patch("laap.api.server._check_bus_status", return_value="up"),
        ):
            r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "degraded"
        assert data["services"]["mcp"] == "down"

    def test_health_returns_503_when_all_down(self, client):
        with (
            patch("laap.api.server._check_mcp_status", return_value="down"),
            patch("laap.api.server._check_bus_status", return_value="down"),
        ):
            r = client.get("/health")
        assert r.status_code == 503
        data = r.json()
        assert data["status"] == "unavailable"

    def test_health_response_contains_uptime(self, client):
        with (
            patch("laap.api.server._check_mcp_status", return_value="up"),
            patch("laap.api.server._check_bus_status", return_value="up"),
        ):
            r = client.get("/health")
        assert "uptime" in r.json()
        assert r.json()["uptime"] >= 0

    def test_health_response_contains_services_dict(self, client):
        with (
            patch("laap.api.server._check_mcp_status", return_value="up"),
            patch("laap.api.server._check_bus_status", return_value="up"),
        ):
            r = client.get("/health")
        services = r.json()["services"]
        assert "api" in services
        assert "mcp" in services
        assert "cognitive_bus" in services
