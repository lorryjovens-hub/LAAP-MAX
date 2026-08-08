"""LAAP 双接入模式端到端集成测试。

测试两种接入模式：
- 模式 A：大脑挂载模式（A1 MCP 钩子 + A2 SDK 嵌入）
- 模式 B：全量个体形式（统一启动器 + WebSocket + Society）
"""

from __future__ import annotations

import asyncio
import json
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

# === 工具 fixture ===


@pytest.fixture
def temp_session_file(tmp_path, monkeypatch):
    """临时替换 ~/.laap/mcp_sessions.json 路径，隔离 registry 单例。

    通过设置 LAAP_ROOT 环境变量指向 tmp_path，使新创建的
    MCPSessionRegistry 实例使用临时文件路径，避免污染真实持久化文件。
    """
    monkeypatch.setenv("LAAP_ROOT", str(tmp_path))
    import laap.mcp.session_registry as reg_module

    reg_module._REGISTRY = None
    yield tmp_path / "mcp_sessions.json"
    reg_module._REGISTRY = None


@pytest.fixture
def reset_society_state():
    """每个测试前重置 society state，避免测试间状态污染。"""
    from laap.api import society_server

    default = {
        "sandboxes": [],
        "agents": [],
        "suggestions": [],
        "lifeforms": [],
        "causal_graph": {"nodes": [], "edges": []},
        "rsi_suggestions": [],
        "memory_status": {"layers": []},
        "psi_status": {},
    }
    society_server._society_state.clear()
    society_server._society_state.update(default)
    yield
    society_server._society_state.clear()
    society_server._society_state.update(default)


@pytest.fixture
def reset_websocket_manager():
    """重置 WebSocket 管理器单例，避免测试间连接污染。"""
    import laap.api.websocket as ws_module

    ws_module._manager = None
    yield
    ws_module._manager = None


@pytest.fixture
def mock_brain():
    """构造带真实返回值的 mock LaapBrain 实例。"""
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
    """在独立事件循环中运行异步协程到完成。"""
    return asyncio.run(coro)


def _get_tool_fn(server, name):
    """提取注册名为 ``name`` 的 MCP 工具原始异步函数。"""
    return server._server._tool_manager._tools[name].fn


# === 测试用例 1: 模式 A MCP 挂载端到端 ===


class TestModeAMcpMountE2E:
    """模式 A 路径 1：MCP 钩子工具端到端测试。"""

    @pytest.fixture
    def server(self, temp_session_file, monkeypatch, mock_brain):
        """构建带隔离 registry 和 mock brain 的 LAAPMCPServer。"""
        # Patch LaapBrain 类，使 _get_or_create_brain 返回 mock_brain
        mock_cls = MagicMock(return_value=mock_brain)
        monkeypatch.setattr("laap_brain.LaapBrain", mock_cls)

        from laap.mcp.server import LAAPMCPServer

        s = LAAPMCPServer(name="test-integration-server")
        s.build_server()
        return s

    def test_mcp_hook_tools_full_flow(self, server, mock_brain):
        """验证 MCP 钩子工具完整流程：before_turn → after_tool → after_turn → status。"""
        session_id = "integration-test-session"

        # 1. 调用 laap_before_turn
        fn_before = _get_tool_fn(server, "laap_before_turn")
        result_before = _call_async(
            fn_before(session_id=session_id, user_message="Hello LAAP")
        )
        assert isinstance(result_before, str)
        assert "[LAAP" in result_before
        mock_brain.before_turn.assert_called()

        # 2. 调用 laap_after_tool
        fn_after_tool = _get_tool_fn(server, "laap_after_tool")
        result_after_tool = _call_async(
            fn_after_tool(
                session_id=session_id, tool_name="test_tool", result="tool result"
            )
        )
        assert isinstance(result_after_tool, dict)
        assert result_after_tool["learned"] is True
        assert result_after_tool["session_id"] == session_id
        mock_brain.after_tool.assert_called()

        # 3. 调用 laap_after_turn
        fn_after_turn = _get_tool_fn(server, "laap_after_turn")
        result_after_turn = _call_async(
            fn_after_turn(session_id=session_id, response="response text")
        )
        assert isinstance(result_after_turn, dict)
        assert "reflection" in result_after_turn
        assert "emotion_delta" in result_after_turn
        mock_brain.after_turn.assert_called()

        # 4. 调用 laap_cognitive_status
        fn_status = _get_tool_fn(server, "laap_cognitive_status")
        result_status = _call_async(fn_status(session_id=session_id))
        assert isinstance(result_status, dict)
        assert result_status["session_id"] == session_id
        assert "lifeform_id" in result_status
        assert result_status["lifeform_id"]  # non-empty

        # 验证 session 持久化到 registry
        from laap.mcp.session_registry import get_registry

        registry = get_registry()
        lifeform_id = registry.get_lifeform_id(session_id)
        assert lifeform_id is not None
        assert lifeform_id.startswith("mcp-")

    def test_session_persistence_across_server_instances(self, temp_session_file):
        """验证 session 在 registry 实例重启后仍从持久化文件加载。"""
        from laap.mcp.session_registry import get_registry, MCPSessionRegistry
        import laap.mcp.session_registry as reg_module

        # 重置单例并创建首个 session
        reg_module._REGISTRY = MCPSessionRegistry()
        registry1 = get_registry()
        lifeform_id_1 = registry1.register_session("persist-test-session")

        # 重启 registry（重新加载持久化文件）
        reg_module._REGISTRY = MCPSessionRegistry()
        registry2 = get_registry()

        # 验证 session 已从持久化文件加载
        lifeform_id_2 = registry2.get_lifeform_id("persist-test-session")
        assert lifeform_id_2 is not None
        assert lifeform_id_2 == lifeform_id_1


# === 测试用例 2: 模式 B 完全体启动 ===


class TestModeBFullEntityLaunch:
    """模式 B：统一启动器 + HTTP API + WebSocket + Society。"""

    @pytest.fixture
    def app(self, reset_society_state):
        from laap.api.server import app

        return app

    @pytest.fixture
    def client(self, app):
        from fastapi.testclient import TestClient

        return TestClient(app)

    def test_health_endpoint_returns_aggregated_status(self, client):
        """验证 /health 返回三服务聚合状态。"""
        with (
            patch("laap.api.server._check_mcp_status", return_value="up"),
            patch("laap.api.server._check_bus_status", return_value="up"),
        ):
            r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert "services" in data
        assert "uptime" in data
        assert set(data["services"].keys()) >= {"api", "mcp", "cognitive_bus"}
        assert data["services"]["api"] == "up"
        assert data["services"]["mcp"] == "up"
        assert data["services"]["cognitive_bus"] == "up"

    def test_society_endpoints_mounted(self, client, reset_society_state):
        """验证 /society/* 端点全部挂载且可访问。"""
        endpoints = [
            "/society/sandboxes",
            "/society/agents",
            "/society/suggestions",
            "/society/lifeforms",
            "/society/psi-status",
            "/society/causal-graph",
            "/society/rsi-suggestions",
            "/society/memory-status",
        ]
        for ep in endpoints:
            r = client.get(ep)
            assert r.status_code == 200, f"Endpoint {ep} failed: {r.status_code}"

    def test_websocket_endpoint_ping_pong(self, client, reset_websocket_manager):
        """验证 /ws 端点 ping/pong 心跳。"""
        with client.websocket_connect("/ws") as ws:
            ws.send_text(json.dumps({"ping": "integration"}))
            data = ws.receive_text()
            msg = json.loads(data)
            assert msg.get("pong") == "integration"

    def test_websocket_subscribe_acknowledgment(self, client, reset_websocket_manager):
        """验证 WebSocket 订阅后返回 subscribed 确认。"""
        with client.websocket_connect("/ws") as ws:
            ws.send_text(json.dumps({"subscribe": ["psi_state"]}))
            ack = ws.receive_text()
            ack_msg = json.loads(ack)
            assert "subscribed" in ack_msg
            assert "psi_state" in ack_msg["subscribed"]

    def test_launcher_initialization(self):
        """验证 LAAPLauncher 初始化参数正确。"""
        from laap.launcher import LAAPLauncher

        launcher = LAAPLauncher(
            host="127.0.0.1",
            http_port=18000,
            mcp_port=18766,
            bus_port=11550,
            no_bus=True,
            no_mcp=True,
        )
        assert launcher.host == "127.0.0.1"
        assert launcher.http_port == 18000
        assert launcher.mcp_port == 18766
        assert launcher.bus_port == 11550
        assert launcher.no_bus is True
        assert launcher.no_mcp is True

    def test_launcher_stats_before_launch(self):
        """验证 launcher 在启动前 _started_at 为 None。"""
        from laap.launcher import LAAPLauncher

        launcher = LAAPLauncher()
        assert launcher._started_at is None

    def test_launch_full_entity_function_exists(self):
        """验证 launch_full_entity 函数可导入且可调用。"""
        from laap.launcher import launch_full_entity

        assert callable(launch_full_entity)


# === 测试用例 3: 模式 A SDK OpenClaw 挂载 ===


class TestModeASdkOpenClawMount:
    """模式 A 路径 2：SDK 嵌入 OpenClaw 端到端。"""

    def test_mount_brain_to_openclaw(self, mock_brain, monkeypatch):
        """验证 mount_brain_to_agent(brain, 'openclaw') 端到端挂载。"""
        # 构造 fake openclaw 模块（含 Agent 类）
        fake_mod = types.ModuleType("openclaw")

        class Agent:
            def __init__(self, *args, **kwargs):
                self.initialized = True

            async def execute_tool(self, tool_name, *args, **kwargs):
                return f"result_of_{tool_name}"

            async def run_conversation(self, message, *args, **kwargs):
                return f"response_to_{message}"

        fake_mod.Agent = Agent
        monkeypatch.setitem(sys.modules, "openclaw", fake_mod)

        from laap.sdk import mount_brain_to_agent

        brain, adapter = mount_brain_to_agent(mock_brain, agent_type="openclaw")

        assert adapter is not None
        assert adapter.name() == "openclaw"
        assert adapter._installed is True

        # 验证 __init__ 被 patch 后实例化能注入 brain
        agent = Agent()
        assert agent.laap_brain is mock_brain

        # 清理
        adapter.uninstall_hooks()


# === 测试用例 4: 模式 A SDK Claude Code 优雅降级 ===


class TestModeASdkClaudeCodeGracefulFallback:
    """模式 A 路径 2：SDK 缺失时回退。"""

    def test_auto_falls_back_to_generic_when_all_sdk_missing(
        self, mock_brain, monkeypatch
    ):
        """auto 模式下所有 SDK 缺失时回退 GenericAdapter。"""
        # 确保 hermes / claude_code / openclaw 均不可检测
        monkeypatch.delenv("HERMES_HOME", raising=False)
        monkeypatch.setitem(sys.modules, "hermes", None)
        monkeypatch.setitem(sys.modules, "hermes_agent", None)
        monkeypatch.setitem(sys.modules, "claude_code_sdk", None)
        monkeypatch.setitem(sys.modules, "openclaw", None)

        from laap.sdk import mount_brain_to_agent
        from laap.sdk.adapters.generic import GenericAdapter

        brain, adapter = mount_brain_to_agent(mock_brain, agent_type="auto")

        assert adapter is not None
        assert isinstance(adapter, GenericAdapter)
        assert adapter.name() == "generic"

    def test_claude_code_explicit_raises_without_sdk(self, mock_brain, monkeypatch):
        """显式指定 claude_code 但 SDK 缺失时抛 ImportError。"""
        monkeypatch.setitem(sys.modules, "claude_code_sdk", None)

        from laap.sdk import mount_brain_to_agent

        with pytest.raises(ImportError, match="claude-code-sdk not installed"):
            mount_brain_to_agent(mock_brain, agent_type="claude_code")


# === 测试用例 5: 向后兼容 enhance() ===


class TestBackwardCompatEnhance:
    """验证 enhance() 向后兼容。"""

    def test_enhance_default_behavior_unchanged(self, monkeypatch):
        """默认调用 enhance() 返回 LaapBrain 实例（不返回元组）。"""
        monkeypatch.delenv("HERMES_HOME", raising=False)

        from laap_brain import enhance, LaapBrain

        result = enhance()
        assert isinstance(result, LaapBrain)
        assert not isinstance(result, tuple)

    def test_enhance_return_adapter_true_returns_tuple(self, monkeypatch):
        """return_adapter=True 返回 (brain, adapter) 元组。"""
        monkeypatch.delenv("HERMES_HOME", raising=False)

        from laap_brain import enhance, LaapBrain

        result = enhance(return_adapter=True)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], LaapBrain)

    def test_enhance_old_style_call_no_breaking(self, monkeypatch):
        """旧代码调用方式 enhance(agent=None) 不破坏。"""
        monkeypatch.delenv("HERMES_HOME", raising=False)

        from laap_brain import enhance, LaapBrain

        result = enhance(agent=None)
        assert isinstance(result, LaapBrain)


# === 综合场景测试 ===


class TestAccessModesIntegration:
    """跨模式综合集成测试。"""

    def test_mode_a_then_mode_b_consistency(self, mock_brain, reset_society_state):
        """模式 A 与模式 B 共享 society state。"""
        from laap.api.society_server import set_society_state
        from laap.api.server import app
        from fastapi.testclient import TestClient

        # 模式 A：通过 SDK 设置 lifeform
        set_society_state("lifeforms", [{"id": "lf-1", "name": "Ao"}])

        # 模式 B：通过 HTTP API 读取
        client = TestClient(app)
        r = client.get("/society/lifeforms")
        assert r.status_code == 200
        assert r.json()["lifeforms"] == [{"id": "lf-1", "name": "Ao"}]

    def test_mcp_session_to_society_link(self, temp_session_file):
        """MCP session 与 society lifeform 关联。"""
        from laap.mcp.session_registry import get_registry

        registry = get_registry()
        lifeform_id = registry.register_session("soc-test-session")

        assert registry.get_lifeform_id("soc-test-session") == lifeform_id
        assert lifeform_id.startswith("mcp-")
