# -*- coding: utf-8 -*-
"""RT-005 意识-身体双层分离架构测试

覆盖:
- RT-005.2  MindLayer 创建与状态
- RT-005.1  MindLayer serialize/deserialize 往返一致性
- RT-005.4  BodyLayer 抽象 + PC/Mobile/Edge 三种实现
- RT-005.3  BodyLayer 传感器/执行器/工具链接口
- RT-005.5  MigrationBusNode MIGRATE 消息类型扩展
- RT-005.6  request_migration 发起迁移
- RT-005.7  receive_migration 接收并恢复
- RT-005.8  迁移后源端 PAUSED / 目标端 RUNNING
- RT-005.9  迁移延迟 < 2 秒
- MindLayer 与 BodyLayer 绑定/解绑
- 错误处理（未知目标、未激活身体、缺失能力）
"""
import time

import pytest

from laap_runtime.body_layer import (
    BodyLayer,
    BodyType,
    Capability,
    EdgeBody,
    MobileBody,
    PCBody,
    create_body,
)
from laap_runtime.migration_bus import (
    MIGRATE_ACK_MSG_TYPE,
    MIGRATE_MSG_TYPE,
    MIGRATE_NACK_MSG_TYPE,
    MigrationBusNode,
)
from laap_runtime.mind_layer import (
    MindLayer,
    MindState,
    MigrationResult,
)


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def _clear_inproc_registry():
    """每个测试前后清空进程内注册表，避免相互影响"""
    MigrationBusNode.clear_inproc_registry()
    yield
    MigrationBusNode.clear_inproc_registry()


@pytest.fixture
def populated_mind() -> MindLayer:
    """构造一个有丰富认知状态的 MindLayer"""
    mind = MindLayer("aris", role="architect", sandbox_id="src-001")
    mind.increment_cycle("coding")
    mind.increment_cycle("coding")
    mind.increment_cycle("design")
    mind.update_emotion(valence=0.6, arousal=0.4, dominance=0.8)
    mind.add_episodic_memory({"event": "designed module", "ts": 1000.0})
    mind.add_episodic_memory({"event": "wrote tests", "ts": 2000.0})
    mind.memory_system.semantic = {
        "python": "编程语言",
        "laap": "生命体架构",
    }
    mind.memory_system.procedural = ["step1", "step2", "step3"]
    mind.add_causal_node({"id": "n1", "type": "event"})
    mind.causal_graph.edges.append({"src": "n1", "dst": "n1", "w": 0.9})
    mind.world_model.entities = [{"id": "e1", "type": "agent"}]
    mind.psi_state["risk_appetite"] = 0.65
    return mind


# ═══════════════════════════════════════════════════════════════
# RT-005.2 MindLayer 创建与状态
# ═══════════════════════════════════════════════════════════════

class TestMindLayerCreation:
    """MindLayer 创建与基本状态测试"""

    def test_mind_layer_initial_state_is_running(self):
        """新建 MindLayer 默认状态为 RUNNING"""
        mind = MindLayer("test-mind")
        assert mind.state == MindState.RUNNING
        assert mind.psi_state["cycle_count"] == 0

    def test_mind_layer_has_all_cognitive_components(self):
        """MindLayer 包含 PSI + 5 层记忆 + 因果图 + 世界模型"""
        mind = MindLayer("test-mind")
        # PSI
        assert "base_needs" in mind.psi_state
        assert "risk_appetite" in mind.psi_state
        assert "cycle_count" in mind.psi_state
        assert "last_domain" in mind.psi_state
        # Emotion (PAD)
        assert hasattr(mind.emotion_system, "valence")
        assert hasattr(mind.emotion_system, "arousal")
        assert hasattr(mind.emotion_system, "dominance")
        # 5 层记忆
        assert hasattr(mind.memory_system, "working")
        assert hasattr(mind.memory_system, "episodic")
        assert hasattr(mind.memory_system, "semantic")
        assert hasattr(mind.memory_system, "procedural")
        assert hasattr(mind.memory_system, "prospective")
        # 因果图
        assert hasattr(mind.causal_graph, "nodes")
        assert hasattr(mind.causal_graph, "edges")
        # 世界模型
        assert hasattr(mind.world_model, "entities")
        assert hasattr(mind.world_model, "relations")

    def test_mind_layer_state_transitions(self):
        """MindLayer 状态可切换: RUNNING → MIGRATING → PAUSED / RESUMED"""
        mind = MindLayer("test-mind")
        assert mind.state == MindState.RUNNING

        mind.mark_migrating()
        assert mind.state == MindState.MIGRATING

        mind.pause()
        assert mind.state == MindState.PAUSED

        mind.mark_resumed()
        assert mind.state == MindState.RESUMED

        mind.resume()
        assert mind.state == MindState.RUNNING


# ═══════════════════════════════════════════════════════════════
# RT-005.1 serialize/deserialize 往返一致性
# ═══════════════════════════════════════════════════════════════

class TestMindLayerSerialization:
    """MindLayer 序列化往返测试"""

    def test_serialize_returns_yaml_string(self):
        """serialize 返回非空 YAML 字符串"""
        mind = MindLayer("test-mind")
        state_str = mind.serialize()
        assert isinstance(state_str, str)
        assert len(state_str) > 0
        # YAML 应包含关键字段
        assert "psi" in state_str
        assert "emotion" in state_str
        assert "memory" in state_str
        assert "causal" in state_str
        assert "world_model" in state_str

    def test_serialize_deserialize_roundtrip_preserves_state(
        self, populated_mind: MindLayer
    ):
        """序列化→反序列化后认知状态 100% 一致"""
        src = populated_mind
        state_str = src.serialize()

        tgt = MindLayer("target")
        tgt.deserialize(state_str)

        # PSI 状态一致
        assert tgt.psi_state["cycle_count"] == src.psi_state["cycle_count"]
        assert tgt.psi_state["last_domain"] == src.psi_state["last_domain"]
        assert tgt.psi_state["risk_appetite"] == src.psi_state["risk_appetite"]
        assert (
            tgt.psi_state["base_needs"]
            == src.psi_state["base_needs"]
        )
        # Emotion 一致
        assert tgt.emotion_system.valence == src.emotion_system.valence
        assert tgt.emotion_system.arousal == src.emotion_system.arousal
        assert tgt.emotion_system.dominance == src.emotion_system.dominance
        # 5 层记忆一致
        assert tgt.memory_system.episodic == src.memory_system.episodic
        assert tgt.memory_system.semantic == src.memory_system.semantic
        assert tgt.memory_system.procedural == src.memory_system.procedural
        # 因果图一致
        assert tgt.causal_graph.nodes == src.causal_graph.nodes
        assert tgt.causal_graph.edges == src.causal_graph.edges
        # 世界模型一致
        assert tgt.world_model.entities == src.world_model.entities

    def test_deserialize_preserves_semantic_memory_content(
        self, populated_mind: MindLayer
    ):
        """反序列化保留语义记忆的具体内容"""
        src = populated_mind
        state_str = src.serialize()
        tgt = MindLayer("target")
        tgt.deserialize(state_str)

        assert tgt.memory_system.semantic["python"] == "编程语言"
        assert tgt.memory_system.semantic["laap"] == "生命体架构"


# ═══════════════════════════════════════════════════════════════
# RT-005.3 / RT-005.4 BodyLayer 测试
# ═══════════════════════════════════════════════════════════════

class TestBodyLayer:
    """BodyLayer 抽象与三种具体实现测试"""

    def test_pc_body_has_full_capabilities(self):
        """PCBody 具备完整传感器/执行器/工具链"""
        body = PCBody()
        assert body.body_type == BodyType.PC
        # 传感器
        sensors = body.list_sensors()
        sensor_names = {c.name for c in sensors}
        assert "keyboard" in sensor_names
        assert "mouse" in sensor_names
        assert "screen_capture" in sensor_names
        # 执行器
        actuators = body.list_actuators()
        actuator_names = {c.name for c in actuators}
        assert "display" in actuator_names
        assert "speaker" in actuator_names
        # 工具
        tools = body.list_tools()
        tool_names = {c.name for c in tools}
        assert "shell" in tool_names
        assert "python_exec" in tool_names
        assert "http_client" in tool_names

    def test_mobile_body_has_mobile_specific_capabilities(self):
        """MobileBody 具备移动端专属传感器/执行器"""
        body = MobileBody()
        assert body.body_type == BodyType.MOBILE
        sensor_names = {c.name for c in body.list_sensors()}
        assert "gps" in sensor_names
        assert "accelerometer" in sensor_names
        assert "camera" in sensor_names
        actuator_names = {c.name for c in body.list_actuators()}
        assert "vibrator" in actuator_names
        assert "notification" in actuator_names

    def test_edge_body_has_minimal_capabilities(self):
        """EdgeBody 具备边缘设备最小能力集"""
        body = EdgeBody()
        assert body.body_type == BodyType.EDGE
        sensor_names = {c.name for c in body.list_sensors()}
        assert "temperature" in sensor_names
        assert "gpio_in" in sensor_names
        tool_names = {c.name for c in body.list_tools()}
        assert "mqtt_client" in tool_names
        # Edge 能力数量应少于 PC
        pc = PCBody()
        assert len(body.capabilities) < len(pc.capabilities)

    def test_body_sensor_input_returns_reading(self):
        """sensor_input 返回 SensorReading"""
        body = PCBody()
        reading = body.sensor_input("keyboard", mock_value="hello")
        assert reading.sensor == "keyboard"
        assert reading.value == "hello"
        assert reading.timestamp > 0

    def test_body_actuator_output_returns_command(self):
        """actuator_output 返回 ActuatorCommand"""
        body = MobileBody()
        cmd = body.actuator_output("vibrator", command="pulse")
        assert cmd.actuator == "vibrator"
        assert cmd.command == "pulse"

    def test_body_toolchain_invoke_returns_result(self):
        """toolchain_invoke 返回 ToolchainResult"""
        body = PCBody()
        result = body.toolchain_invoke("shell", mock_output="done")
        assert result.tool == "shell"
        assert result.success is True
        assert result.output == "done"

    def test_body_raises_on_missing_capability(self):
        """调用不存在的能力抛出 KeyError"""
        body = PCBody()
        with pytest.raises(KeyError):
            body.sensor_input("nonexistent_sensor")
        with pytest.raises(KeyError):
            body.actuator_output("nonexistent_actuator", "cmd")
        with pytest.raises(KeyError):
            body.toolchain_invoke("nonexistent_tool")

    def test_body_raises_when_deactivated(self):
        """停用的身体调用方法抛出 RuntimeError"""
        body = PCBody()
        body.deactivate()
        with pytest.raises(RuntimeError):
            body.sensor_input("keyboard")
        body.activate()
        # 重新激活后正常工作
        reading = body.sensor_input("keyboard")
        assert reading.sensor == "keyboard"

    def test_create_body_factory(self):
        """create_body 工厂函数正确创建三种身体"""
        pc = create_body(BodyType.PC)
        assert isinstance(pc, PCBody)
        mobile = create_body(BodyType.MOBILE)
        assert isinstance(mobile, MobileBody)
        edge = create_body(BodyType.EDGE)
        assert isinstance(edge, EdgeBody)
        with pytest.raises(ValueError):
            create_body(BodyType.UNKNOWN)


# ═══════════════════════════════════════════════════════════════
# RT-005.5 MigrationBusNode MIGRATE 消息类型
# ═══════════════════════════════════════════════════════════════

class TestMigrationBusNode:
    """MigrationBusNode 扩展测试"""

    def test_migrate_message_type_constant_exists(self):
        """MIGRATE 消息类型常量已定义"""
        assert MIGRATE_MSG_TYPE == "migrate"
        assert MIGRATE_ACK_MSG_TYPE == "migrate_ack"
        assert MIGRATE_NACK_MSG_TYPE == "migrate_nack"

    def test_migration_bus_node_inproc_registry(self):
        """进程内注册表支持节点查找"""
        bus_a = MigrationBusNode("node-a", display_name="A")
        bus_b = MigrationBusNode("node-b", display_name="B")
        # 注册表自动注册
        assert MigrationBusNode.get_inproc("node-a") is bus_a
        assert MigrationBusNode.get_inproc("node-b") is bus_b

    def test_send_migration_to_unknown_target_fails(self):
        """向未知目标发送迁移返回 False"""
        bus = MigrationBusNode("lonely-node")
        result = bus.send_migration("nonexistent", "state_str")
        assert result is False
        assert bus._migrations_failed == 1


# ═══════════════════════════════════════════════════════════════
# RT-005.6 / RT-005.7 / RT-005.8 端到端迁移测试
# ═══════════════════════════════════════════════════════════════

class TestEndToEndMigration:
    """端到端迁移流程测试"""

    def test_request_migration_direct(self, populated_mind: MindLayer):
        """直连迁移（无总线）：源 PAUSED，目标 RUNNING，状态一致"""
        target = MindLayer("target-mind", sandbox_id="tgt-001")
        result = populated_mind.request_migration(target)

        assert result.success is True
        assert populated_mind.state == MindState.PAUSED
        assert target.state == MindState.RUNNING
        # 状态一致
        assert target.psi_state["cycle_count"] == 3
        assert target.psi_state["last_domain"] == "design"
        assert target.emotion_system.valence == 0.6
        assert len(target.memory_system.episodic) == 2

    def test_request_migration_via_bus(self, populated_mind: MindLayer):
        """通过 MigrationBusNode 迁移：MIGRATE 消息投递成功"""
        bus_src = MigrationBusNode("src-bus", display_name="源总线")
        bus_tgt = MigrationBusNode("tgt-bus", display_name="目标总线")

        target = MindLayer("target-mind", sandbox_id="tgt-bus-001")
        # 目标 MindLayer 绑定目标总线（使 request_migration 可定位目标）
        target.bind_bus(bus_tgt)
        # 目标总线绑定目标 MindLayer 的接收回调
        bus_tgt.on_migration_received(target.receive_migration)

        result = populated_mind.request_migration(
            target, bus=bus_src
        )

        assert result.success is True
        assert populated_mind.state == MindState.PAUSED
        assert target.state == MindState.RUNNING
        # 状态一致
        assert target.psi_state["cycle_count"] == 3
        assert target.psi_state["risk_appetite"] == 0.65
        assert target.memory_system.semantic["python"] == "编程语言"
        # 总线统计
        assert bus_src._migrations_sent == 1
        assert bus_tgt._migrations_received == 1

    def test_receive_migration_restores_state(self, populated_mind: MindLayer):
        """receive_migration 恢复目标状态"""
        target = MindLayer("target-mind")
        state_str = populated_mind.serialize()

        success = target.receive_migration(state_str, source_id="src")
        assert success is True
        assert target.state == MindState.RESUMED
        assert target.psi_state["cycle_count"] == 3
        assert len(target.memory_system.episodic) == 2

    def test_source_paused_after_migration(self, populated_mind: MindLayer):
        """迁移后源端进入 PAUSED 状态"""
        target = MindLayer("target")
        populated_mind.request_migration(target)
        assert populated_mind.state == MindState.PAUSED

    def test_target_running_after_migration(self, populated_mind: MindLayer):
        """迁移后目标端进入 RUNNING 状态"""
        target = MindLayer("target")
        populated_mind.request_migration(target)
        assert target.state == MindState.RUNNING


# ═══════════════════════════════════════════════════════════════
# RT-005.9 性能：迁移延迟 < 2 秒
# ═══════════════════════════════════════════════════════════════

class TestMigrationPerformance:
    """迁移性能测试"""

    def test_migration_latency_under_2_seconds(self, populated_mind: MindLayer):
        """PC → 手机迁移延迟 < 2 秒"""
        # 模拟 PC → 手机的迁移（不同 Body 类型）
        target = MindLayer("mobile-target", sandbox_id="mobile-001")

        result = populated_mind.request_migration(target)

        assert result.success is True
        assert result.latency_ms < 2000.0, (
            f"迁移延迟 {result.latency_ms:.2f} ms 超过 2000 ms"
        )

    def test_migration_state_bytes_nonzero(self, populated_mind: MindLayer):
        """迁移传输的状态字节数非零"""
        target = MindLayer("target")
        result = populated_mind.request_migration(target)
        assert result.success is True
        assert result.state_bytes > 0
        assert result.migration_id.startswith("mig-")


# ═══════════════════════════════════════════════════════════════
# MindLayer 与 BodyLayer 绑定
# ═══════════════════════════════════════════════════════════════

class TestMindBodyBinding:
    """意识层与身体层绑定测试"""

    def test_mind_attach_detach_body(self):
        """MindLayer 可绑定/解绑 BodyLayer"""
        mind = MindLayer("test-mind")
        body = PCBody()

        mind.attach_body(body)
        assert mind.body is body

        detached = mind.detach_body()
        assert detached is body
        assert mind.body is None

    def test_body_bind_mind双向绑定(self):
        """BodyLayer.bind_mind 建立双向绑定"""
        mind = MindLayer("test-mind")
        body = MobileBody()

        body.bind_mind(mind)
        assert body.mind is mind
        assert mind.body is body

        # 解绑
        body.unbind_mind()
        assert body.mind is None
        assert mind.body is None

    def test_migration_preserves_mind_independent_of_body(self):
        """迁移意识层不影响身体层绑定关系"""
        src_mind = MindLayer("src", sandbox_id="s1")
        src_body = PCBody()
        src_mind.attach_body(src_body)

        tgt_mind = MindLayer("tgt", sandbox_id="t1")
        tgt_body = MobileBody()
        tgt_mind.attach_body(tgt_body)

        # 迁移前：源绑定 PC，目标绑定 Mobile
        assert src_mind.body is src_body
        assert tgt_mind.body is tgt_body

        src_mind.request_migration(tgt_mind)

        # 迁移后：意识状态已转移，但身体绑定关系不变
        assert tgt_mind.psi_state["cycle_count"] == src_mind.psi_state["cycle_count"]
        # 身体绑定未改变（迁移的是意识状态，不是身体）
        assert src_mind.body is src_body
        assert tgt_mind.body is tgt_body


# ═══════════════════════════════════════════════════════════════
# 真实场景：PC → 手机 → 边缘 多跳迁移
# ═══════════════════════════════════════════════════════════════

class TestMultiHopMigration:
    """多跳迁移测试：PC → 手机 → 边缘"""

    def test_pc_to_mobile_to_edge_state_continuity(
        self, populated_mind: MindLayer
    ):
        """PC → 手机 → 边缘多跳迁移后认知状态保持连续"""
        original_cycle = populated_mind.psi_state["cycle_count"]
        original_emotion = populated_mind.emotion_system.valence
        original_episodic_count = len(populated_mind.memory_system.episodic)

        # 第一跳：PC → 手机
        mobile_mind = MindLayer("mobile-mind", sandbox_id="mobile-001")
        mobile_body = MobileBody()
        mobile_mind.attach_body(mobile_body)
        result1 = populated_mind.request_migration(mobile_mind)
        assert result1.success is True
        assert populated_mind.state == MindState.PAUSED
        assert mobile_mind.state == MindState.RUNNING

        # 验证第一跳后状态
        assert mobile_mind.psi_state["cycle_count"] == original_cycle
        assert mobile_mind.emotion_system.valence == original_emotion

        # 在手机端继续认知活动
        mobile_mind.increment_cycle("mobile-task")
        mobile_mind.add_episodic_memory({"event": "on mobile", "ts": 3000.0})

        # 第二跳：手机 → 边缘
        edge_mind = MindLayer("edge-mind", sandbox_id="edge-001")
        edge_body = EdgeBody()
        edge_mind.attach_body(edge_body)
        result2 = mobile_mind.request_migration(edge_mind)
        assert result2.success is True
        assert mobile_mind.state == MindState.PAUSED
        assert edge_mind.state == MindState.RUNNING

        # 验证第二跳后状态：包含第一跳后新增的认知
        assert edge_mind.psi_state["cycle_count"] == original_cycle + 1
        assert edge_mind.psi_state["last_domain"] == "mobile-task"
        assert len(edge_mind.memory_system.episodic) == original_episodic_count + 1
        # 原始状态保留
        assert edge_mind.emotion_system.valence == original_emotion
        assert edge_mind.memory_system.semantic["python"] == "编程语言"

    def test_multi_hop_migration_total_latency(self, populated_mind: MindLayer):
        """两跳迁移总延迟 < 2 秒"""
        mobile_mind = MindLayer("mobile-mind", sandbox_id="m-2")
        edge_mind = MindLayer("edge-mind", sandbox_id="e-2")

        start = time.perf_counter()
        r1 = populated_mind.request_migration(mobile_mind)
        r2 = mobile_mind.request_migration(edge_mind)
        total_ms = (time.perf_counter() - start) * 1000

        assert r1.success and r2.success
        assert total_ms < 2000.0, f"两跳总延迟 {total_ms:.2f} ms 超过 2000 ms"


# ═══════════════════════════════════════════════════════════════
# 错误处理
# ═══════════════════════════════════════════════════════════════

class TestErrorHandling:
    """错误处理测试"""

    def test_migrate_in_callback_exception_isolated(self, populated_mind: MindLayer):
        """迁移接收回调异常不影响迁移结果记录"""
        target = MindLayer("target")
        # 注册会抛异常的回调
        target._on_migrate_in = lambda s: (_ for _ in ()).throw(
            RuntimeError("callback boom")
        )
        # 直连迁移（不走 bus 回调路径）
        result = populated_mind.request_migration(target)
        # 迁移仍成功（回调异常被隔离）
        assert result.success is True
        assert target.psi_state["cycle_count"] == 3

    def test_send_migration_no_callback_returns_false(self, populated_mind: MindLayer):
        """目标总线未绑定接收回调时 send_migration 返回 False"""
        bus_src = MigrationBusNode("src-x")
        MigrationBusNode("tgt-x")  # 目标节点存在但未绑定回调
        target = MindLayer("target-x", sandbox_id="tgt-x")

        result = bus_src.send_migration(
            target_node_id="tgt-x",
            state_str=populated_mind.serialize(),
            source_id="src-x",
        )
        assert result is False
