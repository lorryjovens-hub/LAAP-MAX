"""Unit tests for laap.api.websocket WebSocketManager."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock

import pytest

from laap.api.websocket import (
    ClientConnection,
    WebSocketManager,
    get_websocket_manager,
)


@pytest.fixture
def manager():
    """Fresh WebSocketManager per test."""
    return WebSocketManager()


@pytest.fixture
def mock_ws():
    """Mock starlette WebSocket with async accept/send/receive."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.receive_text = AsyncMock()
    return ws


class TestWebSocketManagerConnect:
    """connect / disconnect 测试。"""

    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self, manager, mock_ws):
        """显式 client_id 时 connect 返回该 id 并调用 accept。"""
        cid = await manager.connect(mock_ws, client_id="test-1")
        assert cid == "test-1"
        mock_ws.accept.assert_called_once()
        assert "test-1" in manager._connections

    @pytest.mark.asyncio
    async def test_connect_generates_client_id(self, manager, mock_ws):
        """未提供 client_id 时自动生成 uuid。"""
        cid = await manager.connect(mock_ws)
        assert cid and len(cid) > 0
        mock_ws.accept.assert_called_once()
        assert cid in manager._connections

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self, manager, mock_ws):
        """disconnect 后连接应被移除。"""
        await manager.connect(mock_ws, client_id="test-2")
        assert "test-2" in manager._connections
        await manager.disconnect("test-2")
        assert "test-2" not in manager._connections

    @pytest.mark.asyncio
    async def test_disconnect_unknown_client_is_noop(self, manager):
        """disconnect 不存在的 client_id 不应抛错。"""
        await manager.disconnect("nonexistent")  # should not raise


class TestWebSocketManagerBroadcast:
    """broadcast 推送测试。"""

    @pytest.mark.asyncio
    async def test_broadcast_to_all_when_no_subscriptions(self, manager, mock_ws):
        """两个未订阅客户端应都收到广播。"""
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.send_text = AsyncMock()
        await manager.connect(mock_ws, "c1")
        await manager.connect(ws2, "c2")

        count = await manager.broadcast("psi_state", {"mood": "happy"})
        assert count == 2
        mock_ws.send_text.assert_called_once()
        ws2.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_message_format(self, manager, mock_ws):
        """广播消息应包含 type / payload / timestamp 字段。"""
        await manager.connect(mock_ws, "c1")
        await manager.broadcast("psi_state", {"mood": "happy"})

        sent_raw = mock_ws.send_text.call_args.args[0]
        msg = json.loads(sent_raw)
        assert msg["type"] == "psi_state"
        assert msg["payload"] == {"mood": "happy"}
        assert "timestamp" in msg

    @pytest.mark.asyncio
    async def test_broadcast_filters_unsubscribed_events(self, manager, mock_ws):
        """订阅过滤：仅订阅事件被推送，未订阅事件被跳过。"""
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.send_text = AsyncMock()
        await manager.connect(mock_ws, "c1")
        await manager.connect(ws2, "c2")

        # c1 订阅 psi_state；c2 订阅 memory_update
        await manager.subscribe("c1", ["psi_state"])
        await manager.subscribe("c2", ["memory_update"])

        # 推送 psi_state，仅 c1 接收
        count = await manager.broadcast("psi_state", {"mood": "happy"})
        assert count == 1
        mock_ws.send_text.assert_called_once()
        ws2.send_text.assert_not_called()

        # 推送 memory_update，仅 c2 接收
        mock_ws.send_text.reset_mock()
        ws2.send_text.reset_mock()
        count = await manager.broadcast("memory_update", {"key": "v"})
        assert count == 1
        ws2.send_text.assert_called_once()
        mock_ws.send_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_dead_client_cleaned_up(self, manager, mock_ws):
        """send_text 失败时该连接应被清理。"""
        await manager.connect(mock_ws, "dead")
        mock_ws.send_text.side_effect = Exception("connection closed")

        count = await manager.broadcast("event", {"x": 1})
        assert count == 0
        assert "dead" not in manager._connections

    @pytest.mark.asyncio
    async def test_broadcast_single_failure_does_not_block_others(
        self, manager, mock_ws
    ):
        """单连接失败不应阻塞其他连接推送。"""
        ws_ok = AsyncMock()
        ws_ok.accept = AsyncMock()
        ws_ok.send_text = AsyncMock()
        await manager.connect(mock_ws, "dead")
        await manager.connect(ws_ok, "alive")
        mock_ws.send_text.side_effect = Exception("connection closed")

        count = await manager.broadcast("event", {"x": 1})
        assert count == 1  # alive 客户端仍成功
        ws_ok.send_text.assert_called_once()
        assert "dead" not in manager._connections
        assert "alive" in manager._connections

    @pytest.mark.asyncio
    async def test_broadcast_no_connections_returns_zero(self, manager):
        """无连接时 broadcast 返回 0。"""
        count = await manager.broadcast("event", {"x": 1})
        assert count == 0


class TestWebSocketManagerSubscribe:
    """subscribe 测试。"""

    @pytest.mark.asyncio
    async def test_subscribe_unknown_client_returns_false(self, manager):
        """订阅不存在的 client_id 返回 False。"""
        ok = await manager.subscribe("unknown", ["event"])
        assert ok is False

    @pytest.mark.asyncio
    async def test_subscribe_adds_to_subscriptions(self, manager, mock_ws):
        """订阅应加入 client.subscriptions。"""
        await manager.connect(mock_ws, "c1")
        ok = await manager.subscribe("c1", ["psi_state", "memory_update"])
        assert ok is True
        conn = manager._connections["c1"]
        assert "psi_state" in conn.subscriptions
        assert "memory_update" in conn.subscriptions


class TestHandleConnection:
    """handle_connection 生命周期测试。"""

    @pytest.mark.asyncio
    async def test_handle_connection_subscribe_message(self, manager, mock_ws):
        """客户端发 subscribe 消息后应返回 subscribed 确认。"""
        mock_ws.receive_text.side_effect = [
            json.dumps({"subscribe": ["psi_state"]}),
            Exception("disconnect"),  # 模拟断开
        ]
        await manager.handle_connection(mock_ws, "test-handle")
        sent = [c.args[0] for c in mock_ws.send_text.call_args_list]
        assert any("subscribed" in s for s in sent)

    @pytest.mark.asyncio
    async def test_handle_connection_ping_pong(self, manager, mock_ws):
        """ping 消息应返回 pong。"""
        mock_ws.receive_text.side_effect = [
            json.dumps({"ping": "hello"}),
            Exception("disconnect"),
        ]
        await manager.handle_connection(mock_ws, "ping-test")
        sent = [c.args[0] for c in mock_ws.send_text.call_args_list]
        assert any("pong" in s for s in sent)

    @pytest.mark.asyncio
    async def test_handle_connection_invalid_json(self, manager, mock_ws):
        """非法 JSON 应返回 invalid json 错误。"""
        mock_ws.receive_text.side_effect = [
            "not json",
            Exception("disconnect"),
        ]
        await manager.handle_connection(mock_ws, "bad-json")
        sent = [c.args[0] for c in mock_ws.send_text.call_args_list]
        assert any("invalid json" in s for s in sent)

    @pytest.mark.asyncio
    async def test_handle_connection_unsubscribe(self, manager, mock_ws):
        """unsubscribe 消息应从 subscriptions 移除并返回确认。"""
        mock_ws.receive_text.side_effect = [
            json.dumps({"subscribe": ["psi_state", "memory_update"]}),
            json.dumps({"unsubscribe": ["psi_state"]}),
            Exception("disconnect"),
        ]
        await manager.handle_connection(mock_ws, "unsub-test")
        # handle_connection 退出后 client 已被 disconnect 移除，
        # 仅验证 unsubscribed 确认消息已发送
        sent = [c.args[0] for c in mock_ws.send_text.call_args_list]
        assert any("unsubscribed" in s for s in sent)

    @pytest.mark.asyncio
    async def test_handle_connection_cleans_up_on_exit(self, manager, mock_ws):
        """连接断开后应从 _connections 移除。"""
        mock_ws.receive_text.side_effect = [Exception("disconnect")]
        await manager.handle_connection(mock_ws, "cleanup-test")
        assert "cleanup-test" not in manager._connections

    @pytest.mark.asyncio
    async def test_handle_connection_unknown_message_no_reply(self, manager, mock_ws):
        """未知消息（无 subscribe/unsubscribe/ping）不应触发回复。"""
        mock_ws.receive_text.side_effect = [
            json.dumps({"unknown_action": True}),
            Exception("disconnect"),
        ]
        await manager.handle_connection(mock_ws, "unknown-test")
        sent = [c.args[0] for c in mock_ws.send_text.call_args_list]
        assert len(sent) == 0


class TestStatsAndSingleton:
    """stats 与单例测试。"""

    @pytest.mark.asyncio
    async def test_stats_returns_correct_dict(self, manager, mock_ws):
        """stats 返回正确的连接数与 client_ids 列表。"""
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.send_text = AsyncMock()
        await manager.connect(mock_ws, "c1")
        await manager.connect(ws2, "c2")

        stats = manager.stats()
        assert stats["total_connections"] == 2
        assert set(stats["client_ids"]) == {"c1", "c2"}

    def test_stats_empty_manager(self, manager):
        """无连接时 stats 返回 0。"""
        stats = manager.stats()
        assert stats["total_connections"] == 0
        assert stats["client_ids"] == []

    def test_get_websocket_manager_singleton(self, monkeypatch):
        """get_websocket_manager 返回同一实例（单例模式）。"""
        # 重置模块级 _manager 以隔离测试
        import laap.api.websocket as ws_module

        monkeypatch.setattr(ws_module, "_manager", None)

        m1 = get_websocket_manager()
        m2 = get_websocket_manager()
        assert m1 is m2
        assert isinstance(m1, WebSocketManager)


class TestClientConnection:
    """ClientConnection.send_json 测试。"""

    @pytest.mark.asyncio
    async def test_send_json_returns_true_on_success(self):
        """send_json 成功时返回 True。"""
        ws = AsyncMock()
        ws.send_text = AsyncMock()
        conn = ClientConnection(client_id="c1", websocket=ws)
        ok = await conn.send_json({"type": "test"})
        assert ok is True
        ws.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_json_returns_false_on_exception(self):
        """send_json 异常时返回 False 不抛错。"""
        ws = AsyncMock()
        ws.send_text = AsyncMock(side_effect=Exception("closed"))
        conn = ClientConnection(client_id="c1", websocket=ws)
        ok = await conn.send_json({"type": "test"})
        assert ok is False
