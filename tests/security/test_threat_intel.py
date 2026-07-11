# -*- coding: utf-8 -*-
"""威胁情报同步总线测试"""
from datetime import datetime, timedelta

import pytest
from laap.security.threat_intel import (
    ThreatIntelBus, ThreatPattern, ThreatType, ThreatSeverity,
    ThreatStatus, ThreatIntelEvent,
)


@pytest.fixture
def bus():
    return ThreatIntelBus(node_id="node_test")


@pytest.fixture
def sample_threat():
    return ThreatPattern(
        threat_type=ThreatType.INJECTION_ATTACK,
        severity=ThreatSeverity.HIGH,
        name="SQL 注入尝试",
        description="检测到恶意 SQL 注入模式",
        detection_rule={"regex": r"'.*OR.*1=1"},
        mitigation={"action": "block", "alert": True},
    )


class TestThreatPattern:
    def test_default_threat_id_generated(self):
        t = ThreatPattern()
        assert t.threat_id.startswith("threat_")

    def test_default_status(self):
        t = ThreatPattern()
        assert t.status == ThreatStatus.DETECTED


class TestThreatIntelBus:
    def test_broadcast_threat(self, bus, sample_threat):
        event = bus.broadcast_threat(sample_threat)
        assert event.threat.threat_id == sample_threat.threat_id
        assert event.broadcast_by == "node_test"
        assert bus.stats["broadcast_count"] == 1

    def test_broadcast_updates_local_threats(self, bus, sample_threat):
        bus.broadcast_threat(sample_threat)
        assert sample_threat.threat_id in bus._local_threats

    def test_broadcast_updates_detection_rules(self, bus, sample_threat):
        bus.broadcast_threat(sample_threat)
        rules = bus.get_detection_rules()
        assert sample_threat.threat_id in rules

    def test_receive_threat_success(self, bus, sample_threat):
        event = ThreatIntelEvent(threat=sample_threat, broadcast_by="other_node")
        success = bus.receive_threat(event)
        assert success is True
        assert bus.stats["received_count"] == 1

    def test_receive_threat_expired(self, bus, sample_threat):
        event = ThreatIntelEvent(
            threat=sample_threat,
            broadcast_by="other_node",
            broadcast_at=datetime.utcnow() - timedelta(seconds=120),
            ttl=60,
        )
        success = bus.receive_threat(event)
        assert success is False

    def test_receive_threat_duplicate(self, bus, sample_threat):
        event = ThreatIntelEvent(threat=sample_threat, broadcast_by="other_node")
        bus.receive_threat(event)
        success = bus.receive_threat(event)
        assert success is False

    def test_subscribe_callback(self, bus, sample_threat):
        received = []
        unsub = bus.subscribe(lambda t: received.append(t))
        bus.broadcast_threat(sample_threat)
        assert len(received) == 1
        unsub()
        bus.broadcast_threat(sample_threat)
        assert len(received) == 1  # 取消订阅后不再收到

    def test_register_mitigation_handler(self, bus, sample_threat):
        bus.broadcast_threat(sample_threat)
        bus.register_mitigation_handler(
            ThreatType.INJECTION_ATTACK,
            lambda t: True,
        )
        success = bus.mitigate_threat(sample_threat.threat_id)
        assert success is True
        assert bus.stats["mitigated_count"] == 1

    def test_mitigate_no_handler(self, bus, sample_threat):
        bus.broadcast_threat(sample_threat)
        success = bus.mitigate_threat(sample_threat.threat_id)
        assert success is False

    def test_mitigate_nonexistent(self, bus):
        success = bus.mitigate_threat("nonexistent")
        assert success is False

    def test_mark_false_positive(self, bus, sample_threat):
        bus.broadcast_threat(sample_threat)
        success = bus.mark_false_positive(sample_threat.threat_id)
        assert success is True
        assert bus.stats["false_positive_count"] == 1

    def test_list_threats_filter(self, bus, sample_threat):
        bus.broadcast_threat(sample_threat)
        another = ThreatPattern(
            threat_type=ThreatType.PATH_TRAVERSAL,
            severity=ThreatSeverity.LOW,
            name="路径遍历",
        )
        bus.broadcast_threat(another)
        # 按类型过滤
        injections = bus.list_threats(threat_type=ThreatType.INJECTION_ATTACK)
        assert len(injections) == 1
        assert injections[0].threat_type == ThreatType.INJECTION_ATTACK
        # 按严重程度过滤
        highs = bus.list_threats(severity=ThreatSeverity.HIGH)
        assert len(highs) == 1

    def test_get_threat(self, bus, sample_threat):
        bus.broadcast_threat(sample_threat)
        found = bus.get_threat(sample_threat.threat_id)
        assert found is not None
        assert found.name == "SQL 注入尝试"

    def test_get_threat_not_found(self, bus):
        assert bus.get_threat("nonexistent") is None


class TestImmuneIntegration:
    def test_integrate_with_immune_add_rule(self, bus, sample_threat):
        class FakeDetector:
            def __init__(self):
                self.rules = {}
            def add_rule(self, rule_id, rule):
                self.rules[rule_id] = rule

        detector = FakeDetector()
        bus.broadcast_threat(sample_threat)
        bus.integrate_with_immune(detector)
        assert sample_threat.threat_id in detector.rules

    def test_integrate_with_immune_register_pattern(self, bus, sample_threat):
        class FakeDetector:
            def __init__(self):
                self.patterns = []
            def register_pattern(self, pattern):
                self.patterns.append(pattern)

        detector = FakeDetector()
        bus.broadcast_threat(sample_threat)
        bus.integrate_with_immune(detector)
        assert len(detector.patterns) == 1

    def test_integrate_with_immune_fallback(self, bus, sample_threat):
        class FakeDetector:
            pass  # 无 add_rule/register_pattern 方法

        detector = FakeDetector()
        bus.broadcast_threat(sample_threat)
        bus.integrate_with_immune(detector)
        assert hasattr(detector, "patterns")
        assert sample_threat.threat_id in detector.patterns


class TestMultiNodeSync:
    def test_multi_node_sync(self, sample_threat):
        """模拟多节点同步场景"""
        node_a = ThreatIntelBus(node_id="node_a")
        node_b = ThreatIntelBus(node_id="node_b")
        node_c = ThreatIntelBus(node_id="node_c")
        # node_a 检测到威胁
        event = node_a.broadcast_threat(sample_threat)
        # 广播到 node_b 和 node_c
        node_b.receive_threat(event)
        node_c.receive_threat(event)
        # 验证所有节点都有该威胁
        assert node_b.get_threat(sample_threat.threat_id) is not None
        assert node_c.get_threat(sample_threat.threat_id) is not None
        # 验证检测规则已同步
        assert sample_threat.threat_id in node_b.get_detection_rules()
        assert sample_threat.threat_id in node_c.get_detection_rules()
