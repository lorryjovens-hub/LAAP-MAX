"""ColonyEventBus 单元测试"""

import pytest
from laap.sandbox.colony import ColonyEventBus, ColonyEventType
from laap.sandbox._types import ColonyEvent


def test_subscribe_publish_single_type():
    """subscribe + publish 单一类型事件被接收"""
    bus = ColonyEventBus()
    events_received = []

    def callback(event):
        events_received.append(event)

    bus.subscribe("shared_fact", callback)
    event = ColonyEvent(event_type="shared_fact", source_sandbox="sb-001")
    delivered = bus.publish(event)

    assert delivered == 1
    assert len(events_received) == 1
    assert events_received[0].event_type == "shared_fact"


def test_wildcard_subscribe_receives_all():
    """通配符订阅（`*`）接收所有事件"""
    bus = ColonyEventBus()
    events_received = []

    def callback(event):
        events_received.append(event)

    bus.subscribe("*", callback)
    bus.publish(ColonyEvent(event_type="shared_fact", source_sandbox="sb-001"))
    bus.publish(ColonyEvent(event_type="resource_request", source_sandbox="sb-002"))
    bus.publish(ColonyEvent(event_type="heartbeat", source_sandbox="sb-003"))

    assert len(events_received) == 3
    assert {e.event_type for e in events_received} == {"shared_fact", "resource_request", "heartbeat"}


def test_unsubscribe_removes_callback():
    """unsubscribe 成功移除回调（不再被调用）"""
    bus = ColonyEventBus()
    events_received = []

    def callback(event):
        events_received.append(event)

    bus.subscribe("shared_fact", callback)
    bus.publish(ColonyEvent(event_type="shared_fact"))
    assert len(events_received) == 1

    success = bus.unsubscribe("shared_fact", callback)
    assert success is True

    bus.publish(ColonyEvent(event_type="shared_fact"))
    assert len(events_received) == 1


def test_unsubscribe_nonexistent_callback():
    """unsubscribe 不存在的回调返回 False"""
    bus = ColonyEventBus()

    def callback(event):
        pass

    success = bus.unsubscribe("shared_fact", callback)
    assert success is False


def test_directed_event_only_to_target():
    """定向事件（target_sandbox 指定）只投递给目标"""
    bus = ColonyEventBus()
    sandbox1_events = []
    sandbox2_events = []

    def callback1(event):
        sandbox1_events.append(event)

    def callback2(event):
        sandbox2_events.append(event)

    callback1._sandbox_id = "sb-001"
    callback2._sandbox_id = "sb-002"

    bus.subscribe("colony_task", callback1)
    bus.subscribe("colony_task", callback2)

    event = ColonyEvent(event_type="colony_task", target_sandbox="sb-001")
    bus.publish(event)

    assert len(sandbox1_events) == 1
    assert len(sandbox2_events) == 0


def test_broadcast_event_to_all_subscribers():
    """广播事件（target_sandbox=None）投递给所有订阅者"""
    bus = ColonyEventBus()
    callbacks = []

    for i in range(3):
        events = []

        def cb(event, events=events):
            events.append(event)

        callbacks.append((cb, events))
        bus.subscribe("heartbeat", cb)

    bus.publish(ColonyEvent(event_type="heartbeat"))

    for cb, events in callbacks:
        assert len(events) == 1


def test_sandbox_filter_whitelist():
    """register_sandbox_filter 限制沙箱只能接收白名单事件类型"""
    bus = ColonyEventBus()
    events_received = []

    def callback(event):
        events_received.append(event)

    callback._sandbox_id = "sb-001"

    bus.subscribe("*", callback)
    bus.register_sandbox_filter("sb-001", ["shared_fact", "heartbeat"])

    bus.publish(ColonyEvent(event_type="shared_fact"))
    bus.publish(ColonyEvent(event_type="heartbeat"))
    bus.publish(ColonyEvent(event_type="resource_request"))

    assert len(events_received) == 2
    assert {e.event_type for e in events_received} == {"shared_fact", "heartbeat"}


def test_request_resource_creates_and_broadcasts():
    """request_resource 创建请求并广播"""
    bus = ColonyEventBus()
    events_received = []

    def callback(event):
        events_received.append(event)

    bus.subscribe("resource_request", callback)

    event_id = bus.request_resource("sb-001", "llm_quota", 50, "need more tokens")

    assert len(events_received) == 1
    event = events_received[0]
    assert event.event_type == ColonyEventType.RESOURCE_REQUEST
    assert event.source_sandbox == "sb-001"
    assert event.payload["resource_type"] == "llm_quota"
    assert event.payload["amount"] == 50
    assert event.payload["reason"] == "need more tokens"
    assert event.event_id == event_id


def test_approve_resource_delivers_approved_event():
    """approve_resource 批准后投递 RESOURCE_APPROVED 事件给请求者"""
    bus = ColonyEventBus()
    approved_events = []

    def callback(event):
        approved_events.append(event)

    callback._sandbox_id = "sb-001"
    bus.subscribe("resource_approved", callback)

    event_id = bus.request_resource("sb-001", "llm_quota", 50)
    success = bus.approve_resource(event_id)

    assert success is True
    assert len(approved_events) == 1
    assert approved_events[0].event_type == ColonyEventType.RESOURCE_APPROVED
    assert approved_events[0].target_sandbox == "sb-001"


def test_approve_nonexistent_request():
    """approve_resource 不存在的 event_id 返回 False"""
    bus = ColonyEventBus()
    success = bus.approve_resource("evt-nonexistent")
    assert success is False


def test_reject_resource_delivers_rejected_event():
    """reject_resource 拒绝并投递 RESOURCE_REJECTED"""
    bus = ColonyEventBus()
    rejected_events = []

    def callback(event):
        rejected_events.append(event)

    callback._sandbox_id = "sb-001"
    bus.subscribe("resource_rejected", callback)

    event_id = bus.request_resource("sb-001", "llm_quota", 50)
    success = bus.reject_resource(event_id, reason="quota exceeded")

    assert success is True
    assert len(rejected_events) == 1
    assert rejected_events[0].event_type == ColonyEventType.RESOURCE_REJECTED
    assert rejected_events[0].target_sandbox == "sb-001"
    assert rejected_events[0].payload["reject_reason"] == "quota exceeded"


def test_get_pending_requests():
    """get_pending_requests 返回所有待批准请求"""
    bus = ColonyEventBus()

    event_id1 = bus.request_resource("sb-001", "llm_quota", 50)
    event_id2 = bus.request_resource("sb-002", "memory_mb", 1024)

    pending = bus.get_pending_requests()
    assert len(pending) == 2
    assert {p.event_id for p in pending} == {event_id1, event_id2}


def test_approve_removes_from_pending():
    """approve 后该请求从 pending 中消失"""
    bus = ColonyEventBus()

    event_id = bus.request_resource("sb-001", "llm_quota", 50)
    assert len(bus.get_pending_requests()) == 1

    bus.approve_resource(event_id)
    assert len(bus.get_pending_requests()) == 0


def test_get_history_filter_by_type():
    """get_history 按事件类型过滤"""
    bus = ColonyEventBus()

    for _ in range(3):
        bus.publish(ColonyEvent(event_type="heartbeat"))
        bus.publish(ColonyEvent(event_type="shared_fact"))

    history = bus.get_history(event_type="heartbeat")
    assert len(history) == 3
    assert all(e.event_type == "heartbeat" for e in history)


def test_get_history_filter_by_source():
    """get_history 按 source_sandbox 过滤"""
    bus = ColonyEventBus()

    bus.publish(ColonyEvent(event_type="heartbeat", source_sandbox="sb-001"))
    bus.publish(ColonyEvent(event_type="heartbeat", source_sandbox="sb-002"))
    bus.publish(ColonyEvent(event_type="heartbeat", source_sandbox="sb-001"))

    history = bus.get_history(source_sandbox="sb-001")
    assert len(history) == 2
    assert all(e.source_sandbox == "sb-001" for e in history)


def test_get_history_limit():
    """get_history limit 参数生效"""
    bus = ColonyEventBus()

    for _ in range(100):
        bus.publish(ColonyEvent(event_type="heartbeat"))

    history = bus.get_history(limit=10)
    assert len(history) == 10


def test_callback_exception_does_not_affect_others():
    """回调异常不影响其他订阅者"""
    bus = ColonyEventBus()
    success_count = []

    def bad_callback(event):
        raise ValueError("intentional error")

    def good_callback(event):
        success_count.append(1)

    bus.subscribe("shared_fact", bad_callback)
    bus.subscribe("shared_fact", good_callback)

    delivered = bus.publish(ColonyEvent(event_type="shared_fact"))

    assert delivered == 2
    assert len(success_count) == 1


def test_stats_returns_correct_statistics():
    """stats() 返回正确统计"""
    bus = ColonyEventBus()

    def cb1(event):
        pass

    def cb2(event):
        pass

    def cb3(event):
        pass

    bus.subscribe("heartbeat", cb1)
    bus.subscribe("heartbeat", cb2)
    bus.subscribe("shared_fact", cb3)
    bus.subscribe("*", cb3)
    bus.register_sandbox_filter("sb-001", ["heartbeat"])

    for _ in range(10):
        bus.publish(ColonyEvent(event_type="heartbeat"))

    bus.request_resource("sb-001", "llm_quota", 50)

    stats = bus.stats()
    assert stats["total_subscribers"] == 3
    assert stats["wildcard_subscribers"] == 1
    assert stats["event_types"] == 2
    assert stats["total_events"] == 11
    assert stats["pending_requests"] == 1
    assert stats["sandboxes_with_filters"] == 1


def test_event_history_auto_purges():
    """事件历史超过 MAX_HISTORY 时自动丢弃最旧"""
    bus = ColonyEventBus()

    for i in range(600):
        bus.publish(ColonyEvent(event_type="heartbeat"))

    assert len(bus.get_history(limit=1000)) == bus.MAX_HISTORY
    assert len(bus._event_history) == bus.MAX_HISTORY


def test_isolation_between_buses():
    """隔离性：两个独立的 ColonyEventBus 实例互不影响"""
    bus1 = ColonyEventBus()
    bus2 = ColonyEventBus()

    events_bus1 = []
    events_bus2 = []

    def cb1(event):
        events_bus1.append(event)

    def cb2(event):
        events_bus2.append(event)

    bus1.subscribe("heartbeat", cb1)
    bus2.subscribe("heartbeat", cb2)

    bus1.publish(ColonyEvent(event_type="heartbeat"))

    assert len(events_bus1) == 1
    assert len(events_bus2) == 0