"""
API 测试: POST /rsi/approve/{change_id}

覆盖:
  - 正确 token 返回 200 并应用变更
  - 错误 token 返回 400
"""
from __future__ import annotations

import pytest

from laap.agi.rsi_engine import RSIMetaEngine


def _get_client_and_engine():
    """获取 FastAPI TestClient 并将 server 模块的 rsi_engine 替换为全新实例。"""
    pytest.importorskip("fastapi")
    try:
        from fastapi.testclient import TestClient
        import laap.api.server as server_mod
    except Exception as exc:  # pragma: no cover - server 依赖缺失时跳过
        pytest.skip(f"无法导入 API server: {exc}")

    fresh_engine = RSIMetaEngine()
    server_mod.rsi_engine = fresh_engine
    return TestClient(server_mod.app), fresh_engine


class TestRSIApprovalAPI:
    def test_approve_change_endpoint_success(self):
        """正确的 approval_token 审批成功并应用参数变更。"""
        client, engine = _get_client_and_engine()
        change_id = "api_chg_1"
        pending = engine.request_approval(
            change_id, "exploration_rate", 0.25, "API 审批测试"
        )

        resp = client.post(
            f"/rsi/approve/{change_id}",
            json={"approval_token": pending.approval_token},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "approved"
        assert data["change_id"] == change_id
        assert data["attempt"]["target"] == "exploration_rate"
        assert engine.get_parameter("exploration_rate").current_value == pytest.approx(0.25)

    def test_approve_change_endpoint_wrong_token(self):
        """错误的 approval_token 返回 400 且不应用变更。"""
        client, engine = _get_client_and_engine()
        change_id = "api_chg_2"
        original = engine.get_parameter("exploration_rate").current_value
        engine.request_approval(change_id, "exploration_rate", 0.25)

        resp = client.post(
            f"/rsi/approve/{change_id}",
            json={"approval_token": "bad-token"},
        )

        assert resp.status_code == 400
        assert "token" in resp.json()["detail"].lower()
        assert engine.get_parameter("exploration_rate").current_value == original
