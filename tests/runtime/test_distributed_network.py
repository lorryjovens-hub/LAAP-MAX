# -*- coding: utf-8 -*-
"""RT-008 全域分布式生命网络测试

覆盖:
- RT-008.1 LifeNode 抽象与字段校验
- RT-008.2 LifeNetwork 节点/生命体注册注销
- RT-008.3 生命路由协议（evolution/service/edge）
- RT-008.4 联邦协作与敏感资源隔离
- RT-008.5 边缘节点托管
- RT-008.6 全域生命注册与发现（< 1 秒）
- RT-008.7 3 节点协同迁移场景
"""
import time

import pytest

from laap_runtime.distributed_network import (
    EDGE_CAPACITY_THRESHOLD,
    EVOLUTION_LOAD_THRESHOLD,
    SERVICE_LOAD_THRESHOLD,
    FederationError,
    LifeNetwork,
    LifeNode,
    LifeformLocation,
    LifeformNotFoundError,
    MigrationReport,
    NetworkError,
    NodeNotFoundError,
    RouteDecision,
    SensitiveResourceError,
    SharedResource,
)
from laap_runtime.mind_layer import MindLayer, MindState


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def network() -> LifeNetwork:
    """返回空的分布式网络"""
    return LifeNetwork(network_id="test-net")


@pytest.fixture
def populated_mind() -> MindLayer:
    """构造一个有丰富认知状态的 MindLayer"""
    mind = MindLayer("aris", role="architect", sandbox_id="aris-001")
    mind.increment_cycle("coding")
    mind.increment_cycle("design")
    mind.update_emotion(valence=0.6, arousal=0.4, dominance=0.8)
    mind.add_episodic_memory({"event": "designed module", "ts": 1000.0})
    mind.memory_system.semantic = {
        "python": "编程语言",
        "laap": "生命体架构",
    }
    mind.add_causal_node({"id": "n1", "type": "event"})
    mind.world_model.entities = [{"id": "e1", "type": "agent"}]
    return mind


@pytest.fixture
def three_node_network(network: LifeNetwork) -> LifeNetwork:
    """构造 3 节点网络：A（高算力进化）、B（服务）、C（边缘）"""
    network.register_node(
        LifeNode(
            node_id="node-a",
            address="127.0.0.1:11501",
            compute_capacity=0.9,
            current_load=0.3,
            organization="org-evolve",
            is_edge=False,
            role="evolution",
        )
    )
    network.register_node(
        LifeNode(
            node_id="node-b",
            address="127.0.0.1:11502",
            compute_capacity=0.5,
            current_load=0.4,
            organization="org-service",
            is_edge=False,
            role="service",
        )
    )
    network.register_node(
        LifeNode(
            node_id="node-c",
            address="127.0.0.1:11503",
            compute_capacity=0.4,
            current_load=0.2,
            organization="org-edge",
            is_edge=True,
            role="hybrid",
        )
    )
    return network


# ═══════════════════════════════════════════════════════════════
# RT-008.1 LifeNode 抽象
# ═══════════════════════════════════════════════════════════════

class TestLifeNode:
    """LifeNode 数据类测试"""

    def test_life_node_fields(self):
        """LifeNode 字段正确保存与规范化"""
        node = LifeNode(
            node_id="n1",
            address="127.0.0.1:10001",
            compute_capacity=0.8,
            current_load=0.5,
            organization="org-1",
            is_edge=True,
            role="hybrid",
        )
        assert node.node_id == "n1"
        assert node.address == "127.0.0.1:10001"
        assert node.compute_capacity == pytest.approx(0.8)
        assert node.current_load == pytest.approx(0.5)
        assert node.organization == "org-1"
        assert node.is_edge is True
        assert node.role == "hybrid"
        assert node.available_compute == pytest.approx(0.4)

    def test_life_node_clamps_values(self):
        """LifeNode 自动将负载与算力 clamp 到 [0, 1]"""
        node = LifeNode(
            node_id="n1",
            address="a",
            compute_capacity=1.5,
            current_load=-0.3,
        )
        assert node.compute_capacity == pytest.approx(1.0)
        assert node.current_load == pytest.approx(0.0)

    def test_life_node_rejects_invalid_role(self):
        """无效角色应抛出 ValueError"""
        with pytest.raises(ValueError):
            LifeNode(node_id="n1", address="a", role="invalid")


# ═══════════════════════════════════════════════════════════════
# RT-008.2 LifeNetwork 基础管理
# ═══════════════════════════════════════════════════════════════

class TestLifeNetworkBasic:
    """节点与生命体基础管理测试"""

    def test_register_and_list_nodes(self, network: LifeNetwork):
        """注册节点后可通过 list_nodes 查询"""
        node = LifeNode(node_id="n1", address="a", organization="o1")
        network.register_node(node)
        assert network.node_count == 1
        assert network.get_node("n1") is node
        assert len(network.list_nodes(organization="o1")) == 1
        assert len(network.list_nodes(organization="o2")) == 0

    def test_unregister_node(self, network: LifeNetwork):
        """注销节点后不可再查询"""
        network.register_node(LifeNode(node_id="n1", address="a"))
        assert network.unregister_node("n1") is True
        assert network.get_node("n1") is None
        assert network.unregister_node("n1") is False

    def test_register_lifeform_and_lookup(self, network: LifeNetwork):
        """注册生命体后可跨节点查找"""
        network.register_node(LifeNode(node_id="n1", address="a"))
        mind = MindLayer("lf", sandbox_id="lf-1")
        location = network.register_lifeform("lf-1", "n1", mind)
        assert isinstance(location, LifeformLocation)
        assert location.lifeform_id == "lf-1"
        assert location.node_id == "n1"

        found = network.lookup_lifeform("lf-1")
        assert found.lifeform_id == "lf-1"
        assert found.node_id == "n1"
        assert network.list_lifeforms_on_node("n1") == ["lf-1"]

    def test_lookup_unknown_lifeform_raises(self, network: LifeNetwork):
        """查找未注册生命体应抛出 LifeformNotFoundError"""
        with pytest.raises(LifeformNotFoundError):
            network.lookup_lifeform("unknown")

    def test_register_lifeform_to_unknown_node_raises(self, network: LifeNetwork):
        """向不存在节点注册生命体应抛出 NodeNotFoundError"""
        with pytest.raises(NodeNotFoundError):
            network.register_lifeform("lf", "missing", None)


# ═══════════════════════════════════════════════════════════════
# RT-008.3 生命路由协议
# ═══════════════════════════════════════════════════════════════

class TestRouting:
    """路由策略测试"""

    def test_route_evolution_prefers_high_compute(self,
                                                   three_node_network: LifeNetwork):
        """进化任务应选择算力最高且负载 < 0.7 的节点"""
        decision = three_node_network.route_task("evolution")
        assert isinstance(decision, RouteDecision)
        assert decision.node is not None
        assert decision.node.node_id == "node-a"
        assert decision.node.current_load < EVOLUTION_LOAD_THRESHOLD

    def test_route_evolution_skips_overloaded_nodes(self,
                                                    network: LifeNetwork):
        """进化任务跳过超载节点"""
        network.register_node(
            LifeNode(
                node_id="high-cap",
                address="a",
                compute_capacity=0.9,
                current_load=0.9,
                role="evolution",
            )
        )
        network.register_node(
            LifeNode(
                node_id="low-cap",
                address="b",
                compute_capacity=0.4,
                current_load=0.3,
                role="evolution",
            )
        )
        decision = network.route_task("evolution")
        assert decision.node is not None
        assert decision.node.node_id == "low-cap"

    def test_route_service_prefers_low_load_and_same_org(self,
                                                         three_node_network: LifeNetwork):
        """服务任务应选择低负载节点，并优先同组织"""
        decision = three_node_network.route_task(
            "service", constraints={"preferred_organization": "org-service"}
        )
        assert decision.node is not None
        assert decision.node.node_id == "node-b"
        assert decision.node.current_load < SERVICE_LOAD_THRESHOLD

    def test_route_edge_requires_edge_node(self,
                                           three_node_network: LifeNetwork):
        """边缘任务必须选择边缘节点且算力 > 0.2"""
        decision = three_node_network.route_task("edge")
        assert decision.node is not None
        assert decision.node.is_edge is True
        assert decision.node.compute_capacity > EDGE_CAPACITY_THRESHOLD
        assert decision.node.node_id == "node-c"

    def test_route_edge_rejects_low_capacity(self, network: LifeNetwork):
        """算力不足的边缘节点不应被选中"""
        network.register_node(
            LifeNode(
                node_id="weak-edge",
                address="a",
                compute_capacity=0.1,
                is_edge=True,
            )
        )
        decision = network.route_task("edge")
        assert decision.node is None


# ═══════════════════════════════════════════════════════════════
# RT-008.4 联邦协作
# ═══════════════════════════════════════════════════════════════

class TestFederation:
    """联邦协作测试"""

    def test_create_federation(self, network: LifeNetwork):
        """创建联邦并列出成员"""
        fid = network.create_federation(["org-a", "org-b"])
        assert fid.startswith("fed-")
        assert network.list_federations()[fid] == ["org-a", "org-b"]

    def test_create_federation_requires_two_organizations(self,
                                                          network: LifeNetwork):
        """单组织无法创建联邦"""
        with pytest.raises(ValueError):
            network.create_federation(["org-a"])

    def test_share_resource_within_federation(self, network: LifeNetwork):
        """同一联邦内的组织可共享非敏感资源"""
        network.create_federation(["org-a", "org-b"])
        shared = network.share_resource(
            "org-a", "org-b", "public-model-card",
            {"description": "模型公开信息"},
        )
        assert isinstance(shared, SharedResource)
        assert shared.resource_key == "public-model-card"
        assert network.get_shared_resource(
            "org-a", "org-b", "public-model-card"
        ) is shared

    def test_share_sensitive_resource_blocked(self, network: LifeNetwork):
        """敏感资源（psi/emotion 等）禁止跨组织共享"""
        network.create_federation(["org-a", "org-b"])
        with pytest.raises(SensitiveResourceError):
            network.share_resource(
                "org-a", "org-b", "psi-state",
                {"psi": {"base_needs": {}}},
            )

    def test_share_across_non_federated_organizations_fails(self,
                                                            network: LifeNetwork):
        """非联邦成员间无法共享资源"""
        with pytest.raises(FederationError):
            network.share_resource(
                "org-a", "org-b", "public-model-card", {}
            )


# ═══════════════════════════════════════════════════════════════
# RT-008.5 边缘节点托管
# ═══════════════════════════════════════════════════════════════

class TestEdgeHosting:
    """边缘节点托管测试"""

    def test_host_on_edge_success(self, network: LifeNetwork):
        """满足条件的边缘节点可托管生命体"""
        network.register_node(
            LifeNode(
                node_id="edge-1",
                address="a",
                compute_capacity=0.5,
                is_edge=True,
            )
        )
        location = network.host_on_edge("lf-edge", "edge-1")
        assert location.node_id == "edge-1"
        assert network.lookup_lifeform("lf-edge").node_id == "edge-1"

    def test_host_on_edge_rejects_non_edge(self, network: LifeNetwork):
        """非边缘节点不能用于边缘托管"""
        network.register_node(
            LifeNode(node_id="cloud-1", address="a", compute_capacity=0.9)
        )
        with pytest.raises(NetworkError):
            network.host_on_edge("lf", "cloud-1")

    def test_host_on_edge_rejects_low_capacity(self, network: LifeNetwork):
        """算力不足的边缘节点不能托管"""
        network.register_node(
            LifeNode(
                node_id="weak-edge",
                address="a",
                compute_capacity=0.1,
                is_edge=True,
            )
        )
        with pytest.raises(NetworkError):
            network.host_on_edge("lf", "weak-edge")


# ═══════════════════════════════════════════════════════════════
# RT-008.6 / RT-008.7 注册发现与 3 节点迁移
# ═══════════════════════════════════════════════════════════════

class TestMigration:
    """跨节点迁移测试"""

    def test_migrate_preserves_state(self,
                                     three_node_network: LifeNetwork,
                                     populated_mind: MindLayer):
        """迁移后认知状态 100% 一致"""
        three_node_network.register_lifeform(
            "aris", "node-a", populated_mind
        )
        report = three_node_network.migrate("aris", "node-a", "node-b")
        assert isinstance(report, MigrationReport)
        assert report.success is True
        assert report.state_consistent is True

        location = three_node_network.lookup_lifeform("aris")
        assert location.node_id == "node-b"
        target_mind = location.snapshot
        assert isinstance(target_mind, MindLayer)
        assert target_mind.name == "aris"
        assert target_mind.psi_state == populated_mind.psi_state
        assert target_mind.emotion_system.to_dict() == populated_mind.emotion_system.to_dict()
        assert target_mind.memory_system.to_dict() == populated_mind.memory_system.to_dict()

    def test_three_node_cascade_migration(self,
                                          three_node_network: LifeNetwork,
                                          populated_mind: MindLayer):
        """生命体可从 A 迁移到 B 再到 C，状态保持一致"""
        three_node_network.register_lifeform("aris", "node-a", populated_mind)

        # A -> B
        report_ab = three_node_network.migrate("aris", "node-a", "node-b")
        assert report_ab.success and report_ab.state_consistent

        # B -> C
        report_bc = three_node_network.migrate("aris", "node-b", "node-c")
        assert report_bc.success and report_bc.state_consistent

        final = three_node_network.lookup_lifeform("aris")
        assert final.node_id == "node-c"
        final_mind = final.snapshot
        assert isinstance(final_mind, MindLayer)
        assert final_mind.psi_state["cycle_count"] == populated_mind.psi_state["cycle_count"]
        assert final_mind.state == MindState.RUNNING

    def test_migrate_unknown_lifeform_fails(self,
                                            three_node_network: LifeNetwork):
        """迁移未注册生命体应失败"""
        report = three_node_network.migrate("unknown", "node-a", "node-b")
        assert report.success is False
        assert "unknown" in report.error or "未注册" in report.error

    def test_lookup_latency_under_one_second(self,
                                             three_node_network: LifeNetwork,
                                             populated_mind: MindLayer):
        """全域查找特定身份生命体 < 1 秒"""
        three_node_network.register_lifeform("aris", "node-a", populated_mind)
        start = time.perf_counter()
        location = three_node_network.lookup_lifeform("aris")
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert location is not None
        assert elapsed_ms < 1000.0


# ═══════════════════════════════════════════════════════════════
# 综合统计
# ═══════════════════════════════════════════════════════════════

class TestStats:
    """网络统计测试"""

    def test_stats_report(self, three_node_network: LifeNetwork,
                          populated_mind: MindLayer):
        """统计报告包含关键指标"""
        three_node_network.register_lifeform("aris", "node-a", populated_mind)
        stats = three_node_network.stats()
        assert stats["network_id"] == "test-net"
        assert stats["node_count"] == 3
        assert stats["lifeform_count"] == 1
        assert any(n["node_id"] == "node-a" for n in stats["nodes"])
