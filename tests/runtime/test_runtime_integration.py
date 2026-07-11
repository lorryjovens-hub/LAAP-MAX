# -*- coding: utf-8 -*-
"""RT-009 Runtime 端到端集成测试

覆盖 RT-001 ~ RT-008 全部模块的关键交互路径：
- 生命体全生命周期：创建 → 持久化 → 暂停 → 迁移 → 恢复 → 销毁
- 多生命体并发场景：Hive + SocialProtocol + CognitiveScheduler 协同
- 故障注入：节点宕机、网络分区、资源耗尽触发扩容
- 性能基准：PSI 循环延迟、迁移延迟、调度公平性

要求：
- 至少 15 个测试用例
- 使用真实 LifeformContainer / MindLayer / BodyLayer / LifeNetwork
- mock-friendly：故障注入使用 mock 替代真实网络失败
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from laap_runtime import (
    BodyType,
    CognitiveAutoscaler,
    CognitiveScheduler,
    ContainerState,
    FairScheduler,
    Hive,
    LifeNetwork,
    LifeNode,
    LifeformContainer,
    LifeformRole,
    MindLayer,
    MindState,
    MigrationBusNode,
    MobileBody,
    PCBody,
    ScalingDecision,
    create_body,
)


# ═══════════════════════════════════════════════════════════════
# 轻量 Mock 子系统（避免依赖完整 laap 内部模块）
# ═══════════════════════════════════════════════════════════════

class MockEmotionSystem:
    """兼容 LifeformContainer 情感提取的轻量 mock"""

    def __init__(self, valence: float = 0.0, arousal: float = 0.0,
                 dominance: float = 0.0) -> None:
        self.valence = float(valence)
        self.arousal = float(arousal)
        self.dominance = float(dominance)

    def current(self) -> "MockEmotionSystem":
        return self


class MockMemoryStream:
    """兼容 5 层记忆提取的轻量 mock"""

    def __init__(self) -> None:
        self.working: list = []
        self.episodic: list = []
        self.semantic: dict = {}
        self.procedural: list = []
        self.prospective: list = []

    def get_layer(self, name: str):
        return getattr(self, name, None)


class MockWorldModel:
    """兼容世界模型提取的轻量 mock"""

    def __init__(self) -> None:
        self.entities: list = []
        self.relations: list = []

    def to_dict(self) -> dict:
        return {"entities": list(self.entities), "relations": list(self.relations)}


class MockCausalGraph:
    """兼容因果图提取的轻量 mock"""

    def __init__(self) -> None:
        self.nodes: list = []
        self.edges: list = []

    def to_dict(self) -> dict:
        return {"nodes": list(self.nodes), "edges": list(self.edges)}


class MockRSIEngine:
    """兼容 RSI 历史提取的轻量 mock"""

    def __init__(self) -> None:
        self.history: list = []

    def get_history(self) -> list:
        return self.history


class MockResourceBudget:
    """兼容 PSI 需求提取的轻量 mock"""

    def __init__(self) -> None:
        self.base_needs = {
            "certainty": 0.6,
            "competence": 0.7,
            "exploration": 0.5,
            "affiliation": 0.4,
            "self_growth": 0.3,
        }
        self.risk_appetite = 0.3


# ═══════════════════════════════════════════════════════════════
# 工厂函数
# ═══════════════════════════════════════════════════════════════

def build_container(
    name: str,
    role: str = "general",
    sandbox_id: str = "",
    arousal: float = 0.0,
) -> LifeformContainer:
    """构造一个注入轻量 mock 子系统的 LifeformContainer"""
    return LifeformContainer(
        name=name,
        role=role,
        sandbox_id=sandbox_id or f"lf-{name}",
        emotion_system=MockEmotionSystem(arousal=arousal),
        memory_stream=MockMemoryStream(),
        world_model=MockWorldModel(),
        causal_graph=MockCausalGraph(),
        rsi_engine=MockRSIEngine(),
        resource_budget=MockResourceBudget(),
    )


def build_mind(name: str, role: str = "general",
               sandbox_id: str = "") -> MindLayer:
    """构造一个带有简单认知状态的 MindLayer"""
    mind = MindLayer(name, role=role, sandbox_id=sandbox_id or f"mind-{name}")
    mind.increment_cycle("integration")
    mind.add_episodic_memory({"event": f"{name}-born"})
    mind.memory_system.semantic["project"] = "RT-009"
    return mind


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def network() -> LifeNetwork:
    """返回空的分布式网络"""
    return LifeNetwork(network_id="rt009-net")


@pytest.fixture(autouse=True)
def _clear_migration_bus_registry():
    """每个测试前清空 MigrationBusNode 进程内注册表"""
    MigrationBusNode.clear_inproc_registry()
    yield
    MigrationBusNode.clear_inproc_registry()


# ═══════════════════════════════════════════════════════════════
# RT-009.1 全生命周期测试
# ═══════════════════════════════════════════════════════════════

class TestFullLifecycle:
    """创建 → 持久化 → 暂停 → 迁移 → 恢复 → 销毁"""

    def test_create_and_start_container(self):
        """创建并启动 LifeformContainer"""
        c = build_container("aris", "architect")
        assert c.state == ContainerState.CREATED
        c.start()
        assert c.state == ContainerState.RUNNING
        assert len(c._subsystem_status) == 10

    def test_persist_and_reload_container(self, tmp_path):
        """容器状态可持久化到 YAML 并重新加载"""
        c = build_container("aris", "architect")
        c.start()
        c._cycle_count = 123
        path = tmp_path / "aris.yaml"
        result = c.save_to(str(path))
        assert result.success is True
        assert path.exists()

        c2 = build_container("aris", "architect")
        c2.start()
        c2.load_from(str(path))
        assert c2._cycle_count == 123

    def test_pause_resume_preserves_state(self):
        """暂停后恢复，认知状态 100% 连续"""
        c = build_container("aris", "architect")
        c.start()
        c._cycle_count = 77
        c.memory_stream.working.append({"task": "design"})
        before = c.get_persistent_state()

        c.pause()
        assert c.state == ContainerState.PAUSED
        c.resume()
        assert c.state == ContainerState.RUNNING

        after = c.get_persistent_state()
        assert after == before

    def test_migrate_across_network_nodes_and_resume(self, network, tmp_path):
        """通过网络将生命体迁移到备用节点并恢复运行"""
        # 源容器：真实 LifeformContainer
        src = build_container("aris", "architect", sandbox_id="aris-009")
        src.start()
        src._cycle_count = 55
        path = tmp_path / "aris-rt009.yaml"
        src.save_to(str(path))
        src.pause()

        # 用 MindLayer 作为认知快照注册到网络
        mind = build_mind("aris", "architect", sandbox_id="aris-009")
        mind.psi_state["cycle_count"] = 55
        body = PCBody("pc-source")
        body.bind_mind(mind)

        network.register_node(
            LifeNode("node-src", "127.0.0.1:11501", 0.8, 0.2, role="hybrid")
        )
        network.register_node(
            LifeNode("node-dst", "127.0.0.1:11502", 0.7, 0.3, role="hybrid")
        )
        network.register_lifeform("aris", "node-src", mind)

        report = network.migrate("aris", "node-src", "node-dst")
        assert report.success is True
        assert report.state_consistent is True
        assert network.lookup_lifeform("aris").node_id == "node-dst"

        # 目标容器从同一份 YAML 恢复并继续运行
        dst = build_container("aris", "architect", sandbox_id="aris-009")
        dst.start()
        dst.load_from(str(path))
        dst.resume()
        assert dst.state == ContainerState.RUNNING
        assert dst._cycle_count == 55

    def test_destroy_releases_subsystems(self):
        """销毁后容器进入 DESTROYED 并释放子系统引用"""
        c = build_container("aris", "architect")
        c.start()
        c.destroy()
        assert c.state == ContainerState.DESTROYED
        assert c.identity is None
        assert c.memory_stream is None
        # 幂等
        c.destroy()
        assert c.state == ContainerState.DESTROYED


# ═══════════════════════════════════════════════════════════════
# RT-009.2 多生命体并发场景测试
# ═══════════════════════════════════════════════════════════════

class TestMultiLifeformConcurrency:
    """3 生命体协同：无死锁、无饥饿"""

    def test_three_lifeform_hive_task_assignment_and_scheduling(self):
        """3 生命体加入 Hive 分配任务，并在调度器中获得服务"""
        hive = Hive(hive_id="rt009-hive")
        scheduler = CognitiveScheduler()

        front = build_container("frontend-1", "frontend")
        back = build_container("backend-1", "backend")
        tester = build_container("tester-1", "tester")
        for c in (front, back, tester):
            c.start()

        hive.join("fe-1", front, LifeformRole.FRONTEND)
        hive.join("be-1", back, LifeformRole.BACKEND)
        hive.join("te-1", tester, LifeformRole.TESTER)

        scheduler.register_container("fe-1", container=front)
        scheduler.register_container("be-1", container=back)
        scheduler.register_container("te-1", container=tester)

        # 架构师（权力最高）分配任务
        assignment = hive.assign_task(
            {"task_id": "T-101", "description": "实现登录页"},
            assignee_id="fe-1",
        )
        assert assignment.assignee_id == "fe-1"
        assert len(hive.get_assignments()) == 1

        # 模拟多轮公平调度，每个生命体都应获得服务
        for _ in range(30):
            nxt = scheduler.schedule_next()
            assert nxt is not None
            scheduler.record_service(nxt, 0.01)

        stats = scheduler.get_fairness_stats()
        counts = [
            stats["containers"][cid]["served_count"]
            for cid in ("fe-1", "be-1", "te-1")
        ]
        assert all(c > 0 for c in counts)
        assert min(counts) / max(counts) >= 0.8

    def test_three_lifeform_trust_cooperation_and_psi_compatibility(self):
        """信任成功提升、协作可行，高 arousal 触发 PSI 退避"""
        hive = Hive()
        front = build_container("frontend-1", "frontend")
        back = build_container("backend-1", "backend")
        excited = build_container("tester-1", "tester", arousal=0.85)
        for c in (front, back, excited):
            c.start()

        hive.join("fe-1", front, LifeformRole.FRONTEND)
        hive.join("be-1", back, LifeformRole.BACKEND)
        hive.join("ex-1", excited, LifeformRole.TESTER)

        # 成功交互提升信任
        hive.record_interaction("fe-1", "be-1", True)
        assert hive.get_trust("fe-1", "be-1") > 0.3
        assert hive.can_cooperate("fe-1", "be-1") is True

        ok, _ = hive.cooperate("fe-1", "be-1", {"task_id": "T-1"})
        assert ok is True

        # 高 arousal 成员无法与他人直接协作
        assert hive.psi_compatibility("fe-1", "ex-1") is False
        assert hive.can_cooperate("fe-1", "ex-1") is False

    def test_three_lifeform_negotiation_respects_power_and_psi(self):
        """协商结果受权力与 PSI 状态共同影响"""
        hive = Hive()
        arch = build_container("arch-1", "architect")
        back = build_container("backend-1", "backend")
        for c in (arch, back):
            c.start()

        hive.join("arch-1", arch, LifeformRole.ARCHITECT)
        hive.join("be-1", back, LifeformRole.BACKEND)

        # 建筑师权力高于后端，且初始信任 >= 0.2，应接受
        result = hive.negotiate(
            {"term": "使用新的 API 规范"},
            proposer_id="arch-1",
            responder_id="be-1",
        )
        assert result.outcome.name == "ACCEPTED"

        # 将后端 arousal 调高，协商应被延后
        back.emotion_system.arousal = 0.9
        result2 = hive.negotiate(
            {"term": "加班完成需求"},
            proposer_id="arch-1",
            responder_id="be-1",
        )
        assert result2.outcome.name == "DEFERRED"


# ═══════════════════════════════════════════════════════════════
# RT-009.3 故障注入测试
# ═══════════════════════════════════════════════════════════════

class TestFaultInjection:
    """节点宕机、网络分区、资源耗尽"""

    def test_node_failure_then_recover_on_backup_node(self, network):
        """源节点宕机（unregister_node）后，生命体可在备用节点恢复"""
        network.register_node(
            LifeNode("node-src", "127.0.0.1:11501", 0.8, 0.2, role="hybrid")
        )
        network.register_node(
            LifeNode("node-backup", "127.0.0.1:11502", 0.7, 0.3, role="hybrid")
        )

        mind = build_mind("aris", "architect", sandbox_id="aris-009")
        mind.psi_state["cycle_count"] = 99
        network.register_lifeform("aris", "node-src", mind)

        # 模拟源节点宕机
        assert network.unregister_node("node-src") is True
        assert network.get_node("node-src") is None

        # 使用最后已知的认知快照在备用节点恢复
        snapshot = network.lookup_lifeform("aris").snapshot
        network.unregister_lifeform("aris")
        network.register_lifeform("aris", "node-backup", snapshot)

        location = network.lookup_lifeform("aris")
        assert location.node_id == "node-backup"
        recovered = location.snapshot
        assert recovered.psi_state["cycle_count"] == 99
        assert recovered.state == MindState.RUNNING

    def test_network_partition_blocks_migration_then_recovers(self):
        """网络分区阻止迁移，分区恢复后迁移成功"""
        src_bus = MigrationBusNode("src-bus")
        dst_bus = MigrationBusNode("dst-bus")
        MigrationBusNode.register_inproc(src_bus)
        MigrationBusNode.register_inproc(dst_bus)

        src_mind = build_mind("aris", "architect")
        dst_mind = MindLayer("aris-backup", role="architect")
        src_mind.bind_bus(src_bus)
        dst_mind.bind_bus(dst_bus)
        dst_bus.on_migration_received(dst_mind.receive_migration)

        # 模拟网络分区：迁移总线投递失败
        with patch.object(src_bus, "send_migration", return_value=False):
            result = src_mind.request_migration(dst_mind, bus=src_bus)
            assert result.success is False
            assert src_mind.state == MindState.RUNNING

        # 分区恢复：真实投递成功
        result2 = src_mind.request_migration(dst_mind, bus=src_bus)
        assert result2.success is True
        assert result2.latency_ms < 2000.0
        assert src_mind.state == MindState.PAUSED
        assert dst_mind.state == MindState.RUNNING

    def test_resource_exhaustion_triggers_scale_up(self):
        """高 CPU 负载触发 CognitiveAutoscaler 扩容"""
        scheduler = CognitiveScheduler()
        scheduler.register_container("c1")
        autoscaler = CognitiveAutoscaler()

        autoscaler.monitor(
            "c1",
            {"cpu_load": 0.9, "memory_load": 0.3, "attention_queue_length": 0},
        )
        assert autoscaler.evaluate("c1") == ScalingDecision.SCALE_UP

        decision, details = autoscaler.apply("c1", scheduler)
        assert decision == ScalingDecision.SCALE_UP
        assert details["reason"] == "高负载触发扩容"

        cap = autoscaler.get_capacity("c1")
        assert cap["working_memory"] > 7
        assert cap["broadcast_rate"] > 10.0

    def test_idle_resource_scale_down_compresses_memory(self):
        """长期空闲触发缩容并压缩情景记忆"""
        scheduler = CognitiveScheduler()
        scheduler.register_container("c1")
        for i in range(10):
            scheduler.store_episodic_memory("c1", {"idx": i})

        autoscaler = CognitiveAutoscaler()
        now = time.monotonic()
        # 模拟已连续空闲超过 30 分钟
        autoscaler.monitor(
            "c1",
            {
                "cpu_load": 0.1,
                "memory_load": 0.1,
                "attention_queue_length": 0,
                "timestamp": now + 31 * 60,
            },
        )
        assert autoscaler.evaluate("c1") == ScalingDecision.SCALE_DOWN

        decision, details = autoscaler.apply("c1", scheduler)
        assert decision == ScalingDecision.SCALE_DOWN
        assert details.get("episodic_evicted", 0) > 0
        assert scheduler.get_memory_usage("c1")["episodic_count"] < 10


# ═══════════════════════════════════════════════════════════════
# RT-009.4 性能基准测试
# ═══════════════════════════════════════════════════════════════

class TestPerformanceBenchmarks:
    """PSI 循环延迟、迁移延迟、调度公平性"""

    def test_psi_loop_latency_under_100ms(self):
        """LifeformContainer PSI 相关调用平均延迟 < 100 ms"""
        c = build_container("aris", "architect")
        c.start()
        c._cycle_count = 1000

        iterations = 20
        start = time.perf_counter()
        for _ in range(iterations):
            c.get_persistent_state()
        avg_ms = (time.perf_counter() - start) / iterations * 1000
        assert avg_ms < 100.0, f"PSI 循环平均延迟 {avg_ms:.2f} ms 超过 100 ms"

    def test_migration_latency_under_2s(self):
        """MindLayer 热迁移延迟 < 2 秒"""
        src = build_mind("aris", "architect")
        dst = MindLayer("aris-backup", role="architect")
        src.increment_cycle("migration")
        src.add_episodic_memory({"event": "pre-migration"})

        result = src.request_migration(dst)
        assert result.success is True
        assert result.latency_ms < 2000.0, (
            f"迁移延迟 {result.latency_ms:.2f} ms 超过 2 s"
        )
        assert dst.psi_state["cycle_count"] == src.psi_state["cycle_count"]

    def test_scheduler_fairness_diff_under_20_percent(self):
        """3 并发容器公平调度，响应时间差异 < 20%"""
        fs = FairScheduler(slice_time=0.01)
        for cid in ("c1", "c2", "c3"):
            fs.register_container(cid)

        for _ in range(30):
            nxt = fs.pick_next()
            assert nxt is not None
            fs.record_service(nxt, 0.01)

        stats = fs.get_fairness_stats()
        fairness = stats.get("_fairness", {})
        diff_ratio = fairness.get("response_time_diff_ratio", 0.0)
        assert diff_ratio < 0.2, (
            f"调度公平性差异 {diff_ratio * 100:.1f}% 超过 20%"
        )


# ═══════════════════════════════════════════════════════════════
# RT-009.5 覆盖率补测 / 跨模块集成边角
# ═══════════════════════════════════════════════════════════════

class TestCrossModuleIntegration:
    """补充覆盖 BodyLayer、Scheduler 配额、广播限流等集成点"""

    def test_mind_body_binding_and_migration_capabilities(self):
        """MindLayer 可在 PCBody 与 MobileBody 之间迁移，能力集随之变化"""
        mind = MindLayer("aris", role="architect")
        pc = PCBody("pc-1")
        mobile = MobileBody("mobile-1")

        pc.bind_mind(mind)
        assert pc.has_capability("keyboard") is True
        assert pc.mind is mind
        assert mind.body is pc

        mind.detach_body()
        mobile.bind_mind(mind)
        assert mobile.has_capability("touch") is True
        assert mobile.has_capability("keyboard") is False
        assert create_body(BodyType.MOBILE, "factory-mobile").body_type == BodyType.MOBILE

    def test_scheduler_memory_quota_and_broadcast_throttle(self):
        """CognitiveScheduler 独立管理多容器记忆配额与广播限流"""
        scheduler = CognitiveScheduler()
        scheduler.register_container("alpha")
        scheduler.register_container("beta")

        # 工作记忆上限 7，超限触发 LRU
        for i in range(10):
            scheduler.store_working_memory("alpha", f"k{i}", i)
        usage = scheduler.get_memory_usage("alpha")
        assert usage["working_count"] == 7

        # beta 令牌被清空后广播应被丢弃
        scheduler.broadcaster.force_set_tokens("beta", 0.0)
        assert scheduler.try_broadcast("beta") is False
        stats = scheduler.get_broadcast_stats("beta")
        assert stats["dropped"] >= 1

    def test_lifenetwork_route_task_integrated_with_nodes(self, network):
        """网络路由策略在真实节点配置下返回合理决策"""
        network.register_node(
            LifeNode("evo", "a", 0.9, 0.2, role="evolution")
        )
        network.register_node(
            LifeNode("svc", "b", 0.5, 0.4, role="service", organization="org-a")
        )
        network.register_node(
            LifeNode("edge", "c", 0.4, 0.2, is_edge=True)
        )

        evo_decision = network.route_task("evolution")
        assert evo_decision.node is not None
        assert evo_decision.node.node_id == "evo"

        svc_decision = network.route_task(
            "service", constraints={"preferred_organization": "org-a"}
        )
        assert svc_decision.node is not None
        assert svc_decision.node.node_id == "svc"

        edge_decision = network.route_task("edge")
        assert edge_decision.node is not None
        assert edge_decision.node.is_edge is True

    def test_magicmock_member_in_hive_and_scheduler(self):
        """Hive 与 Scheduler 对 MagicMock 成员保持友好"""
        hive = Hive()
        mock_member = MagicMock()
        mock_member.get_metrics.return_value = {"emotion": {"arousal": 0.2}}
        hive.join("mock-1", mock_member, LifeformRole.OPS)
        assert hive.get_power("mock-1") == pytest.approx(0.8)

        scheduler = CognitiveScheduler()
        scheduler.register_container("mock-1", container=mock_member)
        scheduler.submit_attention("mock-1", "certainty", 0.9)
        focus = scheduler.acquire_focus()
        assert focus is not None
        assert focus.container_id == "mock-1"
