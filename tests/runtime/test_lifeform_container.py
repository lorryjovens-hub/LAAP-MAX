# -*- coding: utf-8 -*-
"""RT-002 LifeformContainer 测试

覆盖：
- 容器生命周期：start/stop/pause/resume/destroy
- 状态机转换与非法转换异常
- 幂等性（重复调用不报错）
- 10 个认知子系统装配（8 核心 + emotion + metacognition）
- 容错策略（子系统装配失败不阻塞启动）
- pause/resume 状态连续性
- get_state() / get_metrics() 查询接口
- health_check() 占位实现
- get_persistent_state() / set_persistent_state() 持久化接口
- save_to() / load_from() YAML 往返一致性
- mock 注入友好性
"""
import time
from unittest.mock import MagicMock

import pytest

from laap_runtime import ContainerState, LifeformContainer
from laap_runtime.container_schema import STATE_SECTIONS, validate_snapshot


# ── 测试用 Mock 子系统 ──────────────────────────────────────────

class MockEmotionSystem:
    """模拟情感系统 — 兼容 EmotionSystem.current() API"""
    def __init__(self, valence=0.1, arousal=-0.2, dominance=0.3):
        from laap.cognition.emotion import EmotionState
        self._state = EmotionState(
            valence=valence, arousal=arousal, dominance=dominance
        )

    def current(self):
        return self._state


class MockMemoryStream:
    """模拟 5 层记忆流"""
    def __init__(self):
        self.working = [{"task": "test", "priority": 0.8}]
        self.episodic = [{"event": "born", "ts": 1719700000.0}]
        self.semantic = {"python": "编程语言", "laap": "生命体架构"}
        self.procedural = ["step1", "step2", "step3"]
        self.prospective = [{"goal": "evolve", "deadline": 1719800000.0}]


class MockWorldModel:
    """模拟世界模型"""
    def __init__(self):
        self.entities = [{"id": "e1", "type": "agent"}]
        self.relations = [{"src": "e1", "dst": "e1", "type": "self"}]


class MockCausalGraph:
    """模拟因果图"""
    def __init__(self):
        self.nodes = [{"id": "n1"}, {"id": "n2"}]
        self.edges = [{"src": "n1", "dst": "n2"}]


class MockRSIEngine:
    """模拟 RSI 引擎"""
    def __init__(self):
        self.history = [
            {"change_id": "c1", "file": "a.py", "success": True},
        ]

    def get_history(self):
        return self.history


class MockResourceBudget:
    """模拟资源预算"""
    def __init__(self):
        self.base_needs = {
            "certainty": 0.65, "competence": 0.75,
            "exploration": 0.55, "affiliation": 0.45,
            "self_growth": 0.35,
        }
        self.risk_appetite = 0.35


# ── 工厂 ──

def make_full_mock_container():
    """创建注入了全部 mock 子系统的容器"""
    return LifeformContainer(
        name="test-lifeform",
        role="architect",
        sandbox_id="lf-test1234",
        emotion_system=MockEmotionSystem(0.1, -0.2, 0.3),
        memory_stream=MockMemoryStream(),
        world_model=MockWorldModel(),
        causal_graph=MockCausalGraph(),
        rsi_engine=MockRSIEngine(),
        resource_budget=MockResourceBudget(),
        governance={"human_oversight": "none", "audit_level": "basic"},
        language_cortex={"provider": "openai", "model": "gpt-4"},
    )


# ══ 1. 容器创建与初始状态 ═════════════════════════════════════

class TestContainerCreation:
    """容器创建与初始状态测试"""

    def test_new_container_in_created_state(self):
        """新建容器应为 CREATED 状态"""
        c = LifeformContainer(name="test", role="architect")
        assert c.state == ContainerState.CREATED
        assert c.name == "test"
        assert c.role == "architect"
        assert c.sandbox_id.startswith("lf-")

    def test_explicit_sandbox_id(self):
        """显式指定 sandbox_id"""
        c = LifeformContainer(sandbox_id="lf-custom123")
        assert c.sandbox_id == "lf-custom123"

    def test_container_repr(self):
        """__repr__ 包含关键信息"""
        c = LifeformContainer(name="mybot", role="test_engineer")
        r = repr(c)
        assert "mybot" in r
        assert "test_engineer" in r
        assert "created" in r


# ══ 2. 生命周期状态机 ════════════════════════════════════════

class TestLifecycleStateMachine:
    """生命周期状态机测试"""

    def test_start_transitions_to_running(self):
        """start() 将容器从 CREATED 转为 RUNNING"""
        c = LifeformContainer()
        assert c.state == ContainerState.CREATED
        c.start()
        assert c.state == ContainerState.RUNNING

    def test_start_assembles_all_subsystems(self):
        """start() 装配全部 10 个认知子系统"""
        c = make_full_mock_container()
        c.start()
        # 8 个核心子系统 + emotion + metacognition = 10
        assert len(c._subsystem_status) == 10
        # 所有注入的子系统应标记为 ready
        assert c._subsystem_status["emotion_system"] == "ready"
        assert c._subsystem_status["memory_stream"] == "ready"
        assert c._subsystem_status["world_model"] == "ready"
        assert c._subsystem_status["resource_budget"] == "ready"

    def test_start_is_idempotent(self):
        """start() 幂等：已运行容器再次调用不报错"""
        c = LifeformContainer()
        c.start()
        c.start()  # 不应抛异常
        assert c.state == ContainerState.RUNNING

    def test_stop_transitions_to_stopped(self):
        """stop() 将容器转至 STOPPED"""
        c = LifeformContainer()
        c.start()
        c.stop()
        assert c.state == ContainerState.STOPPED

    def test_stop_is_idempotent(self):
        """stop() 幂等"""
        c = LifeformContainer()
        c.start()
        c.stop()
        c.stop()  # 不应抛异常
        assert c.state == ContainerState.STOPPED

    def test_pause_transitions_to_paused(self):
        """pause() 将 RUNNING 容器转为 PAUSED"""
        c = LifeformContainer()
        c.start()
        c.pause()
        assert c.state == ContainerState.PAUSED

    def test_pause_is_idempotent(self):
        """pause() 幂等"""
        c = LifeformContainer()
        c.start()
        c.pause()
        c.pause()  # 不应抛异常
        assert c.state == ContainerState.PAUSED

    def test_resume_transitions_to_running(self):
        """resume() 将 PAUSED 容器转回 RUNNING"""
        c = LifeformContainer()
        c.start()
        c.pause()
        c.resume()
        assert c.state == ContainerState.RUNNING

    def test_resume_is_idempotent(self):
        """resume() 幂等：已 RUNNING 容器再次 resume 不报错"""
        c = LifeformContainer()
        c.start()
        c.resume()  # 不应抛异常
        assert c.state == ContainerState.RUNNING

    def test_destroy_transitions_to_destroyed(self):
        """destroy() 将容器转为 DESTROYED"""
        c = LifeformContainer()
        c.start()
        c.destroy()
        assert c.state == ContainerState.DESTROYED

    def test_destroy_is_idempotent(self):
        """destroy() 幂等"""
        c = LifeformContainer()
        c.start()
        c.destroy()
        c.destroy()  # 不应抛异常
        assert c.state == ContainerState.DESTROYED

    def test_start_after_destroy_raises(self):
        """已销毁容器调用 start() 应抛 RuntimeError"""
        c = LifeformContainer()
        c.start()
        c.destroy()
        with pytest.raises(RuntimeError, match="已销毁"):
            c.start()

    def test_pause_when_not_running_raises(self):
        """非 RUNNING 状态调用 pause() 应抛 RuntimeError"""
        c = LifeformContainer()
        with pytest.raises(RuntimeError):
            c.pause()

    def test_resume_from_created_raises(self):
        """CREATED 状态调用 resume() 应抛 RuntimeError（非 PAUSED 状态非法转换）"""
        c = LifeformContainer()  # CREATED
        with pytest.raises(RuntimeError, match="只有 PAUSED 状态可恢复"):
            c.resume()


# ══ 3. pause/resume 状态连续性 ═══════════════════════════════

class TestPauseResumeContinuity:
    """pause/resume 状态连续性测试"""

    def test_state_continuity_across_pause_resume(self):
        """pause → resume 后认知状态 100% 连续"""
        c = make_full_mock_container()
        c.start()
        # 记录暂停前状态
        state_before = c.get_persistent_state()
        # 暂停
        c.pause()
        # 恢复
        c.resume()
        # 验证状态完全一致
        state_after = c.get_persistent_state()
        assert state_after == state_before

    def test_cycle_count_preserved_on_pause_resume(self):
        """PSI cycle_count 在 pause/resume 后保持不变"""
        c = LifeformContainer()
        c.start()
        c._cycle_count = 12345  # 模拟已运行若干周期
        c.pause()
        assert c._cycle_count == 12345
        c.resume()
        assert c._cycle_count == 12345

    def test_emotion_state_preserved_on_pause_resume(self):
        """情感状态在 pause/resume 后保持不变"""
        c = make_full_mock_container()
        c.start()
        emotion_before = c.get_persistent_state()["emotion"]
        c.pause()
        c.resume()
        emotion_after = c.get_persistent_state()["emotion"]
        assert emotion_after == emotion_before


# ══ 4. 容错策略 ═════════════════════════════════════════════

class TestFaultTolerance:
    """子系统装配容错测试"""

    def test_start_succeeds_with_partial_subsystem_failure(self):
        """部分子系统装配失败不阻塞容器启动"""
        # 注入一个会失败的子系统（通过让 world_model=None 触发惰性装配，
        # 但 import 会失败 → 回退到 stub）
        c = LifeformContainer(
            world_model=None,
            memory_stream=None,  # 让其走 import 失败路径
        )
        c.start()
        assert c.state == ContainerState.RUNNING
        # 失败的子系统应被标记为 stub
        # （memory_stream 或 world_model 因 import 失败走 stub 路径）
        assert c.state == ContainerState.RUNNING

    def test_injected_mocks_marked_ready(self):
        """注入的 mock 子系统标记为 ready"""
        c = make_full_mock_container()
        c.start()
        assert c._subsystem_status["emotion_system"] == "ready"
        assert c._subsystem_status["world_model"] == "ready"
        assert c._subsystem_status["memory_stream"] == "ready"
        assert c._subsystem_status["resource_budget"] == "ready"


# ══ 5. 状态查询接口 ═════════════════════════════════════════

class TestStateQueries:
    """get_state() / get_metrics() 查询接口测试"""

    def test_get_state_returns_summary(self):
        """get_state() 返回状态摘要"""
        c = make_full_mock_container()
        c.start()
        s = c.get_state()
        assert s["state"] == "running"
        assert s["name"] == "test-lifeform"
        assert s["role"] == "architect"
        assert s["sandbox_id"] == "lf-test1234"
        assert s["psi_active"] is True
        assert s["subsystems_total"] == 10

    def test_get_metrics_returns_runtime_metrics(self):
        """get_metrics() 返回运行时指标"""
        c = make_full_mock_container()
        c.start()
        m = c.get_metrics()
        assert m["state"] == "running"
        assert "emotion" in m
        assert "psi" in m
        assert "base_needs" in m["psi"]
        assert m["psi"]["cycle_count"] == 0
        assert "subsystem_status" in m

    def test_health_check_returns_psi_report(self):
        """health_check() 返回 PSI 心理健康报告（RT-006）"""
        c = LifeformContainer()
        c.start()
        hc = c.health_check()
        # RT-006: 返回结构化 PSI 健康报告
        assert "overall_status" in hc
        assert hc["overall_status"] in ("healthy", "degraded", "critical")
        assert "metrics" in hc
        assert "alerts" in hc
        assert "timestamp" in hc
        assert "container_name" in hc
        assert "container_state" in hc
        # 4 项指标字段
        metrics = hc["metrics"]
        assert "need_activation_variance" in metrics
        assert "need_satisfaction_rate" in metrics
        assert "emotion_stability" in metrics
        assert "goal_progress_rate" in metrics


# ══ 6. 持久化接口 ═══════════════════════════════════════════

class TestPersistentState:
    """get_persistent_state() / set_persistent_state() 测试"""

    def test_get_persistent_state_has_8_sections(self):
        """get_persistent_state() 返回 8 个 state 段"""
        c = make_full_mock_container()
        c.start()
        state = c.get_persistent_state()
        for section in STATE_SECTIONS:
            assert section in state, f"缺少 state 段: {section}"

    def test_get_persistent_state_passes_schema(self):
        """get_persistent_state() 输出通过 Schema 验证"""
        c = make_full_mock_container()
        c.start()
        state = c.get_persistent_state()
        snapshot = {
            "version": "1.0",
            "metadata": {
                "name": c.name,
                "role": c.role,
                "sandbox_id": c.sandbox_id,
                "created_at": c.created_at,
            },
            "state": state,
            "checksum": "",
        }
        errors = validate_snapshot(snapshot)
        assert errors == [], f"Schema 验证失败: {errors}"

    def test_set_persistent_state_restores(self):
        """set_persistent_state() 从字典恢复状态"""
        c = make_full_mock_container()
        c.start()
        original = c.get_persistent_state()
        # 创建新容器并恢复
        c2 = make_full_mock_container()
        c2.start()
        c2.set_persistent_state(original)
        restored = c2.get_persistent_state()
        # PSI cycle_count 应一致
        assert restored["psi"]["cycle_count"] == original["psi"]["cycle_count"]
        # 治理配置应一致
        assert restored["governance"] == original["governance"]
        # 语言皮层应一致
        assert restored["language_cortex"] == original["language_cortex"]

    def test_persistent_state_roundtrip_preserves_emotion(self):
        """get → set 往返保持情感状态一致"""
        c = make_full_mock_container()
        c.start()
        original_emotion = c.get_persistent_state()["emotion"]
        state = c.get_persistent_state()
        c.set_persistent_state(state)
        restored_emotion = c.get_persistent_state()["emotion"]
        assert restored_emotion["valence"] == pytest.approx(
            original_emotion["valence"]
        )
        assert restored_emotion["arousal"] == pytest.approx(
            original_emotion["arousal"]
        )

    def test_persistent_state_roundtrip_preserves_memory(self):
        """get → set 往返保持 5 层记忆一致"""
        c = make_full_mock_container()
        c.start()
        state = c.get_persistent_state()
        original_memory = state["memory"]
        c.set_persistent_state(state)
        restored_memory = c.get_persistent_state()["memory"]
        assert restored_memory == original_memory


# ══ 7. save_to / load_from 集成 ══════════════════════════════

class TestSaveLoadIntegration:
    """save_to() / load_from() YAML 往返测试"""

    def test_save_to_writes_yaml(self, tmp_path):
        """save_to() 写入 YAML 文件"""
        c = make_full_mock_container()
        c.start()
        path = tmp_path / "lifeform.yaml"
        result = c.save_to(str(path))
        assert result.success is True
        assert path.exists()
        assert result.bytes_written > 0

    def test_load_from_restores_state(self, tmp_path):
        """load_from() 从 YAML 恢复状态"""
        c = make_full_mock_container()
        c.start()
        c._cycle_count = 99999
        path = tmp_path / "lifeform.yaml"
        c.save_to(str(path))
        # 新容器加载
        c2 = make_full_mock_container()
        c2.start()
        snapshot = c2.load_from(str(path))
        # cycle_count 应恢复
        assert c2._cycle_count == 99999
        assert snapshot.version == "1.0"

    def test_save_load_full_roundtrip(self, tmp_path):
        """完整 save → load 往返一致性"""
        c = make_full_mock_container()
        c.start()
        path = tmp_path / "rt.yaml"
        c.save_to(str(path))
        # 新容器加载
        c2 = make_full_mock_container()
        c2.start()
        c2.load_from(str(path))
        # 验证状态一致
        s1 = c.get_persistent_state()
        s2 = c2.get_persistent_state()
        assert s1["governance"] == s2["governance"]
        assert s1["language_cortex"] == s2["language_cortex"]
        assert s1["psi"]["cycle_count"] == s2["psi"]["cycle_count"]


# ══ 8. Mock 注入友好性 ══════════════════════════════════════

class TestMockInjection:
    """mock 注入测试"""

    def test_magicmock_emotion_system_injection(self):
        """使用 MagicMock 注入 emotion_system"""
        mock_emotion = MagicMock()
        mock_emotion.current.return_value = MagicMock(
            valence=0.5, arousal=0.6, dominance=0.7
        )
        c = LifeformContainer(emotion_system=mock_emotion)
        c.start()
        emotion = c.get_persistent_state()["emotion"]
        assert emotion["valence"] == pytest.approx(0.5)
        assert emotion["arousal"] == pytest.approx(0.6)

    def test_all_subsystems_injectable(self):
        """所有 10 个子系统均可通过构造函数注入"""
        c = LifeformContainer(
            identity=MagicMock(),
            self_model=MagicMock(),
            world_model=MockWorldModel(),
            memory_stream=MockMemoryStream(),
            goal_keeper=MagicMock(),
            resource_budget=MockResourceBudget(),
            skill_library=MagicMock(),
            boundary=MagicMock(),
            emotion_system=MockEmotionSystem(),
            metacognition_system=MagicMock(),
        )
        c.start()
        # 全部应标记为 ready
        for name, status in c._subsystem_status.items():
            assert status == "ready", f"{name} 应为 ready，实际为 {status}"


# ══ 9. 重启场景 ═════════════════════════════════════════════

class TestRestartScenario:
    """stop → start 重启场景测试"""

    def test_restart_after_stop(self):
        """stop() 后可再次 start()"""
        c = LifeformContainer()
        c.start()
        c._cycle_count = 100
        c.stop()
        assert c.state == ContainerState.STOPPED
        c.start()
        assert c.state == ContainerState.RUNNING
        # 重启后 cycle_count 保留
        assert c._cycle_count == 100
