"""LAAPKernel 多 Sandbox 路由测试（Task 14）"""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional
from unittest.mock import Mock, MagicMock, patch

import pytest

from laap_brain.kernel import LAAPKernel


class MockSandbox:
    """模拟 CognitiveSandbox 用于测试"""

    def __init__(self, sandbox_id: str, name: str = "Test", role: str = "test"):
        self.sandbox_id = sandbox_id
        self.name = name
        self.role = role
        self.resource_budget = Mock()
        self.resource_budget.get_effective_degradation.return_value = "NORMAL"

        self.world_model = Mock()
        self.world_model.stats.return_value = {"model_type": "local", "entities": 10}

        self.self_model = Mock()
        self.self_model.stats.return_value = {"name": name, "efficacy": 0.8}

    def set_cached(self):
        """将资源状态设置为 CACHED"""
        self.resource_budget.get_effective_degradation.return_value = "CACHED"


class TestKernelMultiSandbox:
    """LAAPKernel 多 Sandbox 路由测试用例"""

    def setup_method(self):
        """每个测试方法前创建 kernel 实例"""
        self.kernel = LAAPKernel(model="test-model")
        self.kernel.initialize()

    # ═══ 基础注册/注销测试 ═══

    def test_register_sandbox_success(self):
        """register_sandbox() 注册 sandbox 成功"""
        sandbox = MockSandbox("sandbox-001")
        self.kernel.register_sandbox(sandbox)

        assert self.kernel.get_sandbox("sandbox-001") == sandbox

    def test_unregister_sandbox_success(self):
        """unregister_sandbox() 取消注册成功"""
        sandbox = MockSandbox("sandbox-002")
        self.kernel.register_sandbox(sandbox)

        result = self.kernel.unregister_sandbox("sandbox-002")
        assert result is True
        assert self.kernel.get_sandbox("sandbox-002") is None

    def test_unregister_sandbox_nonexistent(self):
        """unregister_sandbox() 不存在的 ID 返回 False"""
        result = self.kernel.unregister_sandbox("nonexistent-id")
        assert result is False

    def test_get_sandbox_exists(self):
        """get_sandbox() 获取已注册的 sandbox"""
        sandbox = MockSandbox("sandbox-003", name="TestAgent", role="developer")
        self.kernel.register_sandbox(sandbox)

        retrieved = self.kernel.get_sandbox("sandbox-003")
        assert retrieved is not None
        assert retrieved.sandbox_id == "sandbox-003"
        assert retrieved.name == "TestAgent"
        assert retrieved.role == "developer"

    def test_get_sandbox_nonexistent(self):
        """get_sandbox() 不存在的 ID 返回 None"""
        assert self.kernel.get_sandbox("nonexistent-id") is None

    # ═══ run_interaction 路由测试 ═══

    def test_run_interaction_no_sandbox_backward_compatible(self):
        """run_interaction() 不传 sandbox_id 走默认路径（向后兼容）"""
        result = self.kernel.run_interaction("Hello", mode_override="llm")

        assert "response" in result
        assert result["mode"] == "llm"
        assert result["sandbox_id"] is None

    def test_run_interaction_with_sandbox(self):
        """run_interaction(sandbox_id=...) 路由到指定 sandbox"""
        sandbox = MockSandbox("sandbox-004")
        self.kernel.register_sandbox(sandbox)

        def mock_llm_fn(text):
            return f"LLM response to: {text}"

        self.kernel.set_llm_chat_fn(mock_llm_fn)

        result = self.kernel.run_interaction(
            "Analyze this code", mode_override="v5", sandbox_id="sandbox-004"
        )

        assert result["sandbox_id"] == "sandbox-004"
        assert "psi" in result
        assert result["mode"] == "v5"

    def test_run_interaction_sandbox_cached(self):
        """sandbox 资源降级到 CACHED 时返回空响应"""
        sandbox = MockSandbox("sandbox-005")
        sandbox.set_cached()
        self.kernel.register_sandbox(sandbox)

        result = self.kernel.run_interaction(
            "Hello", mode_override="v5", sandbox_id="sandbox-005"
        )

        assert result["response"] == ""
        assert result["sandbox_id"] == "sandbox-005"
        assert result.get("error") == "sandbox_cached"

    def test_run_interaction_two_sandboxes_isolated(self):
        """两个 sandbox 并行运行，状态隔离"""
        sandbox_a = MockSandbox("sandbox-a", name="AgentA", role="engineer")
        sandbox_b = MockSandbox("sandbox-b", name="AgentB", role="designer")

        sandbox_a.world_model.stats.return_value = {"entities": 100}
        sandbox_b.world_model.stats.return_value = {"entities": 50}

        self.kernel.register_sandbox(sandbox_a)
        self.kernel.register_sandbox(sandbox_b)

        def mock_llm_fn(text):
            return f"Response: {text}"

        self.kernel.set_llm_chat_fn(mock_llm_fn)

        result_a = self.kernel.run_interaction(
            "Task for A", mode_override="v5", sandbox_id="sandbox-a"
        )
        result_b = self.kernel.run_interaction(
            "Task for B", mode_override="v5", sandbox_id="sandbox-b"
        )

        assert result_a["sandbox_id"] == "sandbox-a"
        assert result_b["sandbox_id"] == "sandbox-b"

        assert "sandbox" in result_a.get("psi", {})
        assert "sandbox" in result_b.get("psi", {})

        assert result_a["psi"]["sandbox"]["name"] == "AgentA"
        assert result_b["psi"]["sandbox"]["name"] == "AgentB"

    # ═══ PSI 阶段回调 sandbox 路由测试 ═══

    def test_psi_perceive_uses_sandbox_world_model(self):
        """PSI 阶段回调使用 sandbox 的 world_model"""
        sandbox = MockSandbox("sandbox-006")
        sandbox.world_model.stats.return_value = {"entities": 42}
        self.kernel.register_sandbox(sandbox)

        context = {"sandbox": sandbox, "sandbox_id": "sandbox-006"}
        result = self.kernel._psi_perceive("test input", context)

        assert result.get("sandbox_id") == "sandbox-006"
        assert "world_model_stats" in result
        assert result["world_model_stats"]["entities"] == 42

    def test_psi_select_uses_sandbox_self_model(self):
        """PSI 阶段回调使用 sandbox 的 self_model"""
        sandbox = MockSandbox("sandbox-007", name="SelfTestAgent")
        sandbox.self_model.stats.return_value = {"name": "SelfTestAgent", "efficacy": 0.9}
        self.kernel.register_sandbox(sandbox)

        context = {"sandbox": sandbox, "sandbox_id": "sandbox-007"}
        perceived = {"summary": "test", "has_code": False, "has_question": False, "load": 0.1}
        result = self.kernel._psi_select(perceived, context)

        assert result.get("sandbox_id") == "sandbox-007"
        assert "self_model_stats" in result
        assert result["self_model_stats"]["name"] == "SelfTestAgent"

    def test_psi_integrate_uses_sandbox(self):
        """PSI integrate 阶段使用 sandbox"""
        sandbox = MockSandbox("sandbox-008")
        self.kernel.register_sandbox(sandbox)

        context = {"sandbox": sandbox, "sandbox_id": "sandbox-008"}
        perceived = {}
        selected = {"focus": "code", "confidence": 0.8}
        result = self.kernel._psi_integrate(perceived, selected, context)

        assert result.get("sandbox_id") == "sandbox-008"
        assert result.get("world_model_insight") == "sandbox_world_model_used"

    def test_psi_learn_uses_sandbox(self):
        """PSI learn 阶段使用 sandbox"""
        sandbox = MockSandbox("sandbox-009")
        self.kernel.register_sandbox(sandbox)

        context = {"sandbox": sandbox, "sandbox_id": "sandbox-009"}
        action_result = {"response": "success response"}
        result = self.kernel._psi_learn(action_result, context)

        assert result.get("sandbox_id") == "sandbox-009"
        assert result.get("self_model_updated") is True

    # ═══ get_status 返回 sandbox 列表 ═══

    def test_get_status_returns_sandbox_list(self):
        """get_status() 返回 sandbox 列表"""
        sandbox1 = MockSandbox("sandbox-010", name="Alpha", role="leader")
        sandbox2 = MockSandbox("sandbox-011", name="Beta", role="follower")

        self.kernel.register_sandbox(sandbox1)
        self.kernel.register_sandbox(sandbox2)

        status = self.kernel.get_status()

        assert "sandboxes" in status
        assert len(status["sandboxes"]) == 2

        sandbox_ids = {sb["sandbox_id"] for sb in status["sandboxes"]}
        assert "sandbox-010" in sandbox_ids
        assert "sandbox-011" in sandbox_ids

        names = {sb["name"] for sb in status["sandboxes"]}
        assert "Alpha" in names
        assert "Beta" in names

    # ═══ 线程安全测试 ═══

    def test_concurrent_register_get_sandbox(self):
        """线程安全：并发注册/获取 sandbox 不冲突"""
        num_threads = 10
        num_sandboxes_per_thread = 10
        errors = []

        def register_sandboxes(thread_id):
            try:
                for i in range(num_sandboxes_per_thread):
                    sandbox_id = f"sandbox-thread{thread_id}-{i}"
                    sandbox = MockSandbox(sandbox_id)
                    self.kernel.register_sandbox(sandbox)

                    # 立即获取验证
                    retrieved = self.kernel.get_sandbox(sandbox_id)
                    if retrieved is None:
                        errors.append(f"Thread {thread_id}: sandbox {sandbox_id} not found")
                    elif retrieved.sandbox_id != sandbox_id:
                        errors.append(f"Thread {thread_id}: sandbox ID mismatch")
            except Exception as e:
                errors.append(f"Thread {thread_id} exception: {e}")

        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=register_sandboxes, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 验证所有 sandbox 都已注册
        status = self.kernel.get_status()
        assert len(status["sandboxes"]) == num_threads * num_sandboxes_per_thread
        assert len(errors) == 0, f"Errors occurred: {errors}"

    def test_concurrent_unregister_sandbox(self):
        """线程安全：并发注销 sandbox"""
        num_sandboxes = 20
        errors = []

        for i in range(num_sandboxes):
            sandbox = MockSandbox(f"sandbox-concurrent-{i}")
            self.kernel.register_sandbox(sandbox)

        def unregister_sandboxes(start_idx):
            try:
                for i in range(start_idx, start_idx + 5):
                    sandbox_id = f"sandbox-concurrent-{i}"
                    result = self.kernel.unregister_sandbox(sandbox_id)
                    if not result:
                        errors.append(f"Failed to unregister {sandbox_id}")
            except Exception as e:
                errors.append(f"Exception unregistering: {e}")

        threads = []
        for i in range(0, num_sandboxes, 5):
            t = threading.Thread(target=unregister_sandboxes, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors occurred: {errors}"
        status = self.kernel.get_status()
        assert len(status["sandboxes"]) == 0

    # ═══ _route_to_sandbox 测试 ═══

    def test_route_to_sandbox_success(self):
        """_route_to_sandbox 成功路由到 sandbox"""
        sandbox = MockSandbox("sandbox-route-01", name="RouterTest", role="router")
        sandbox.world_model.stats.return_value = {"model_type": "local", "size": 1000}
        sandbox.self_model.stats.return_value = {"name": "RouterTest", "level": 5}
        self.kernel.register_sandbox(sandbox)

        psi_input = {"phases": {}, "response": ""}
        result = self.kernel._route_to_sandbox("sandbox-route-01", psi_input)

        assert "sandbox" in result
        assert result["sandbox"]["sandbox_id"] == "sandbox-route-01"
        assert result["sandbox"]["name"] == "RouterTest"
        assert result["sandbox"]["role"] == "router"

        assert "world_model" in result
        assert "self_model" in result

    def test_route_to_sandbox_nonexistent(self):
        """_route_to_sandbox 路由到不存在的 sandbox 返回原始输入"""
        psi_input = {"phases": {}, "response": "original"}
        result = self.kernel._route_to_sandbox("nonexistent", psi_input)

        assert result == psi_input

    # ═══ register_sandbox 异常处理 ═══

    def test_register_sandbox_missing_id(self):
        """register_sandbox 缺少 sandbox_id 属性抛出异常"""
        invalid_sandbox = Mock()
        del invalid_sandbox.sandbox_id

        with pytest.raises(ValueError, match="必须有 sandbox_id 属性"):
            self.kernel.register_sandbox(invalid_sandbox)

    # ═══ LLM 模式不使用 sandbox ═══

    def test_run_interaction_llm_mode_ignores_sandbox(self):
        """LLM 模式不使用 sandbox 路由"""
        sandbox = MockSandbox("sandbox-llm-test")
        self.kernel.register_sandbox(sandbox)

        def mock_llm_fn(text):
            return f"LLM: {text}"

        self.kernel.set_llm_chat_fn(mock_llm_fn)

        result = self.kernel.run_interaction(
            "Hello", mode_override="llm", sandbox_id="sandbox-llm-test"
        )

        assert result["mode"] == "llm"
        assert result["sandbox_id"] == "sandbox-llm-test"
        assert "psi" not in result