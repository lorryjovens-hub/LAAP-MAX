# -*- coding: utf-8 -*-
"""RT-003 CognitiveScheduler 测试

覆盖：
- CognitiveResource 枚举（RT-003.1）
- AttentionPriorityQueue 注意力优先级队列（RT-003.2）
- MemoryQuotaManager 记忆配额管理（RT-003.3）
- TokenBucketBroadcaster 广播限流（RT-003.4）
- PSIUrgencyMapper PSI 紧迫度映射（RT-003.5）
- FairScheduler 多容器公平调度（RT-003.6）
- CrossContainerCoordinator 跨容器协调（RT-003.7）
- CognitiveScheduler 主类集成测试（RT-003 全流程）
- mock-friendly：无需真实 LifeformContainer
- 与 MigrationBusNode 集成测试

验证标准:
- 高紧迫度 PSI 需求优先获得焦点
- 工作记忆 ≤ 7 项、情景可配、语义无上限
- 每秒广播 ≤ 10 条
- 3 并发无饥饿（响应时间差异 < 20%）
"""
import time
from unittest.mock import MagicMock

import pytest

from laap_runtime.cognitive_scheduler import (
    AttentionPriorityQueue,
    AttentionRequest,
    CognitiveResource,
    CognitiveScheduler,
    CrossContainerCoordinator,
    FairScheduler,
    MemoryQuotaManager,
    PSIUrgencyMapper,
    TokenBucketBroadcaster,
)


# ═══════════════════════════════════════════════════════════════
# RT-003.1 CognitiveResource 枚举测试
# ═══════════════════════════════════════════════════════════════

class TestCognitiveResourceEnum:
    """CognitiveResource 枚举测试"""

    def test_enum_has_four_resources(self):
        """枚举应包含 4 种认知资源类型"""
        assert CognitiveResource.ATTENTION.value == "attention"
        assert CognitiveResource.MEMORY.value == "memory"
        assert CognitiveResource.BROADCAST.value == "broadcast"
        assert CognitiveResource.PSI_URGENCY.value == "psi_urgency"

    def test_enum_is_str_enum(self):
        """枚举应继承 str 以便 JSON 序列化"""
        assert isinstance(CognitiveResource.ATTENTION, str)
        assert CognitiveResource("attention") is CognitiveResource.ATTENTION


# ═══════════════════════════════════════════════════════════════
# RT-003.2 AttentionPriorityQueue 测试
# ═══════════════════════════════════════════════════════════════

class TestAttentionPriorityQueue:
    """注意力优先级队列测试"""

    def test_high_urgency_gets_focus_first(self):
        """高紧迫度 PSI 需求优先获得焦点"""
        q = AttentionPriorityQueue()
        q.submit(urgency=0.3, container_id="c1", need_name="low")
        q.submit(urgency=0.9, container_id="c2", need_name="high")
        q.submit(urgency=0.5, container_id="c3", need_name="mid")
        focused = q.acquire_focus()
        assert focused is not None
        assert focused.urgency == 0.9
        assert focused.container_id == "c2"
        assert focused.need_name == "high"

    def test_fifo_order_for_same_urgency(self):
        """相同紧迫度时按 FIFO 顺序出队"""
        q = AttentionPriorityQueue()
        q.submit(urgency=0.5, container_id="c1", need_name="n1")
        q.submit(urgency=0.5, container_id="c2", need_name="n2")
        q.submit(urgency=0.5, container_id="c3", need_name="n3")
        first = q.acquire_focus()
        second = q.acquire_focus()
        third = q.acquire_focus()
        assert first.container_id == "c1"
        assert second.container_id == "c2"
        assert third.container_id == "c3"

    def test_empty_queue_returns_none(self):
        """空队列 acquire_focus / peek_focus 返回 None"""
        q = AttentionPriorityQueue()
        assert q.acquire_focus() is None
        assert q.peek_focus() is None
        assert q.is_empty()
        assert len(q) == 0

    def test_urgency_out_of_range_clamped(self):
        """urgency 超出 [0,1] 范围应被截断"""
        q = AttentionPriorityQueue()
        req_high = q.submit(urgency=2.5, container_id="c1")
        req_low = q.submit(urgency=-0.5, container_id="c2")
        assert req_high.urgency == 1.0
        assert req_low.urgency == 0.0

    def test_peek_does_not_remove(self):
        """peek_focus 不移除元素"""
        q = AttentionPriorityQueue()
        q.submit(urgency=0.8, container_id="c1")
        assert len(q) == 1
        peeked = q.peek_focus()
        assert peeked is not None
        assert peeked.container_id == "c1"
        assert len(q) == 1  # 仍在队列中

    def test_clear_resets_queue(self):
        """clear 清空队列并重置计数器"""
        q = AttentionPriorityQueue()
        q.submit(urgency=0.5, container_id="c1")
        q.submit(urgency=0.6, container_id="c2")
        q.clear()
        assert q.is_empty()
        # 重置后序号应从 0 开始
        req = q.submit(urgency=0.5, container_id="c3")
        assert req.sequence == 0


# ═══════════════════════════════════════════════════════════════
# RT-003.3 MemoryQuotaManager 测试
# ═══════════════════════════════════════════════════════════════

class TestMemoryQuotaManager:
    """记忆容量配额管理测试"""

    def test_working_memory_default_limit_is_seven(self):
        """工作记忆默认上限为 7（Miller's Law）"""
        mgr = MemoryQuotaManager()
        assert mgr.working_limit == 7

    def test_working_memory_lru_eviction_when_full(self):
        """工作记忆满时触发 LRU 淘汰"""
        mgr = MemoryQuotaManager(working_limit=3)
        mgr.store_working("c1", "k1", "v1")
        mgr.store_working("c1", "k2", "v2")
        mgr.store_working("c1", "k3", "v3")
        # 访问 k1 使其变为最近使用
        mgr.get_working("c1", "k1")
        # 写入 k4 应淘汰 k2（最久未访问）
        evicted = mgr.store_working("c1", "k4", "v4")
        assert evicted == "v2"
        # k1 仍在
        assert mgr.get_working("c1", "k1") == "v1"
        # k2 已被淘汰
        assert mgr.get_working("c1", "k2") is None

    def test_episodic_memory_configurable_limit(self):
        """情景记忆上限可配置"""
        mgr = MemoryQuotaManager(episodic_limit=5)
        assert mgr.episodic_limit == 5
        # 填充 5 条
        for i in range(5):
            mgr.store_episodic("c1", {"event": f"e{i}"})
        # 第 6 条应触发 FIFO 淘汰
        evicted = mgr.store_episodic("c1", {"event": "e5"})
        assert evicted == {"event": "e0"}
        # 队列应有 5 条
        eps = mgr.get_episodic("c1")
        assert len(eps) == 5
        assert eps[0] == {"event": "e1"}
        assert eps[-1] == {"event": "e5"}

    def test_semantic_memory_unlimited(self):
        """语义记忆无上限"""
        mgr = MemoryQuotaManager()
        # 写入大量条目
        for i in range(1000):
            mgr.store_semantic("c1", f"k{i}", f"v{i}")
        usage = mgr.get_usage("c1")
        assert usage["semantic_count"] == 1000
        assert usage["semantic_limit"] is None  # 无上限

    def test_memory_usage_query(self):
        """get_usage 返回正确的使用情况"""
        mgr = MemoryQuotaManager(working_limit=7, episodic_limit=1000)
        mgr.store_working("c1", "k1", "v1")
        mgr.store_working("c1", "k2", "v2")
        mgr.store_episodic("c1", "e1")
        mgr.store_episodic("c1", "e2")
        mgr.store_semantic("c1", "sk1", "sv1")
        usage = mgr.get_usage("c1")
        assert usage["working_count"] == 2
        assert usage["working_limit"] == 7
        assert usage["episodic_count"] == 2
        assert usage["episodic_limit"] == 1000
        assert usage["semantic_count"] == 1
        assert usage["semantic_limit"] is None

    def test_invalid_memory_limits_raise(self):
        """非法的上限应抛出 ValueError"""
        with pytest.raises(ValueError):
            MemoryQuotaManager(working_limit=0)
        with pytest.raises(ValueError):
            MemoryQuotaManager(working_limit=-1)
        with pytest.raises(ValueError):
            MemoryQuotaManager(episodic_limit=0)

    def test_each_container_has_independent_storage(self):
        """每个容器有独立的记忆存储"""
        mgr = MemoryQuotaManager()
        mgr.store_working("c1", "k", "v1")
        mgr.store_working("c2", "k", "v2")
        assert mgr.get_working("c1", "k") == "v1"
        assert mgr.get_working("c2", "k") == "v2"


# ═══════════════════════════════════════════════════════════════
# RT-003.4 TokenBucketBroadcaster 测试
# ═══════════════════════════════════════════════════════════════

class TestTokenBucketBroadcaster:
    """广播带宽限流测试"""

    def test_default_rate_is_ten_per_second(self):
        """默认限流速率为每秒 10 条"""
        b = TokenBucketBroadcaster()
        assert b.rate == 10.0
        assert b.capacity == 10

    def test_allows_burst_up_to_capacity(self):
        """令牌桶允许突发至 capacity 条"""
        b = TokenBucketBroadcaster(rate=10.0, capacity=10)
        # 初始满桶，前 10 条应全部放行
        for i in range(10):
            assert b.try_broadcast("c1") is True, f"第 {i+1} 条应放行"
        # 第 11 条应被限流（令牌耗尽）
        assert b.try_broadcast("c1") is False
        stats = b.get_stats("c1")
        assert stats["allowed"] == 10
        assert stats["dropped"] == 1

    def test_throttle_when_tokens_exhausted(self):
        """令牌不足时丢弃广播"""
        b = TokenBucketBroadcaster(rate=10.0, capacity=2)
        # 前 2 条放行
        assert b.try_broadcast("c1") is True
        assert b.try_broadcast("c1") is True
        # 第 3-5 条被丢弃
        for _ in range(3):
            assert b.try_broadcast("c1") is False
        stats = b.get_stats("c1")
        assert stats["allowed"] == 2
        assert stats["dropped"] == 3

    def test_token_refill_over_time(self):
        """令牌按时间填充"""
        b = TokenBucketBroadcaster(rate=100.0, capacity=1)
        # 用尽令牌
        assert b.try_broadcast("c1") is True
        assert b.try_broadcast("c1") is False
        # 等待令牌填充（rate=100/s，10ms 即可填充 1 个）
        time.sleep(0.05)
        # 应至少填充 1 个令牌
        assert b.try_broadcast("c1") is True

    def test_invalid_rate_raises(self):
        """非法 rate / capacity 抛出 ValueError"""
        with pytest.raises(ValueError):
            TokenBucketBroadcaster(rate=0)
        with pytest.raises(ValueError):
            TokenBucketBroadcaster(rate=-1)
        with pytest.raises(ValueError):
            TokenBucketBroadcaster(capacity=0)

    def test_force_set_tokens_for_testing(self):
        """force_set_tokens 可手动设置令牌数（测试用）"""
        b = TokenBucketBroadcaster(rate=10.0, capacity=10)
        b.force_set_tokens("c1", 0.0)
        assert b.try_broadcast("c1") is False
        b.force_set_tokens("c1", 5.0)
        # 应能放行 5 条
        for _ in range(5):
            assert b.try_broadcast("c1") is True
        assert b.try_broadcast("c1") is False

    def test_each_container_has_independent_bucket(self):
        """每个容器有独立的令牌桶"""
        b = TokenBucketBroadcaster(rate=10.0, capacity=2)
        # c1 用尽
        b.try_broadcast("c1")
        b.try_broadcast("c1")
        assert b.try_broadcast("c1") is False
        # c2 仍满桶
        assert b.try_broadcast("c2") is True
        assert b.try_broadcast("c2") is True


# ═══════════════════════════════════════════════════════════════
# RT-003.5 PSIUrgencyMapper 测试
# ═══════════════════════════════════════════════════════════════

class TestPSIUrgencyMapper:
    """PSI 紧迫度优先级映射测试"""

    def test_step_mode_thresholds(self):
        """step 模式按阈值分档映射"""
        m = PSIUrgencyMapper(mode="step")
        # < 0.4 → low (0.2)
        assert m.map(0.1) == PSIUrgencyMapper.URGENCY_LOW
        assert m.map(0.3) == PSIUrgencyMapper.URGENCY_LOW
        # 0.4-0.6 → medium (0.5)
        assert m.map(0.4) == PSIUrgencyMapper.URGENCY_MEDIUM
        assert m.map(0.5) == PSIUrgencyMapper.URGENCY_MEDIUM
        # 0.6-0.8 → high (0.7)
        assert m.map(0.6) == PSIUrgencyMapper.URGENCY_HIGH
        assert m.map(0.75) == PSIUrgencyMapper.URGENCY_HIGH
        # >= 0.8 → critical (0.95)
        assert m.map(0.8) == PSIUrgencyMapper.URGENCY_CRITICAL
        assert m.map(1.0) == PSIUrgencyMapper.URGENCY_CRITICAL

    def test_linear_mode_identity_mapping(self):
        """linear 模式 urgency == activation"""
        m = PSIUrgencyMapper(mode="linear")
        assert m.map(0.0) == 0.0
        assert abs(m.map(0.5) - 0.5) < 1e-9
        assert m.map(1.0) == 1.0

    def test_get_most_urgent_need(self):
        """get_most_urgent 返回最紧迫的需求"""
        m = PSIUrgencyMapper(mode="linear")
        needs = {
            "certainty": 0.3,
            "competence": 0.9,  # 最紧迫
            "exploration": 0.5,
        }
        name, urgency = m.get_most_urgent(needs)
        assert name == "competence"
        assert abs(urgency - 0.9) < 1e-9

    def test_get_most_urgent_empty_needs(self):
        """空 needs 列表返回 ("", 0.0)"""
        m = PSIUrgencyMapper()
        name, urgency = m.get_most_urgent({})
        assert name == ""
        assert urgency == 0.0

    def test_activation_out_of_range_clamped(self):
        """activation 越界被截断到 [0,1]"""
        m = PSIUrgencyMapper(mode="linear")
        assert m.map(-0.5) == 0.0
        assert m.map(2.0) == 1.0

    def test_invalid_threshold_order_raises(self):
        """非法阈值顺序抛出 ValueError"""
        with pytest.raises(ValueError):
            PSIUrgencyMapper(
                threshold_medium=0.7,
                threshold_high=0.5,  # medium > high 非法
                threshold_critical=0.9,
            )

    def test_invalid_mode_raises(self):
        """非法 mode 抛出 ValueError"""
        with pytest.raises(ValueError):
            PSIUrgencyMapper(mode="invalid")


# ═══════════════════════════════════════════════════════════════
# RT-003.6 FairScheduler 测试
# ═══════════════════════════════════════════════════════════════

class TestFairScheduler:
    """多容器公平调度测试"""

    def test_picks_lowest_vrtime_first(self):
        """选择 vrtime 最小的容器"""
        fs = FairScheduler()
        fs.register_container("c1")
        fs.register_container("c2")
        fs.register_container("c3")
        # c1 已服务，vrtime 增加
        fs.record_service("c1", 0.1)
        # 应选 vrtime=0 的容器（c2 或 c3，按字典序选 c2）
        assert fs.pick_next() == "c2"

    def test_vrtime_increases_after_service(self):
        """服务后 vrtime 增加"""
        fs = FairScheduler()
        fs.register_container("c1")
        fs.record_service("c1", 0.1)
        stats = fs.get_fairness_stats()
        assert stats["containers"]["c1"]["vrtime"] > 0
        assert stats["containers"]["c1"]["served_count"] == 1

    def test_no_starvation_three_containers(self):
        """3 个容器并发时无饥饿（响应时间差异 < 20%）"""
        fs = FairScheduler(slice_time=0.01)
        fs.register_container("c1")
        fs.register_container("c2")
        fs.register_container("c3")
        # 模拟 30 次调度，每次时间相同
        for _ in range(30):
            cid = fs.pick_next()
            assert cid is not None
            fs.record_service(cid, 0.01)
        stats = fs.get_fairness_stats()
        served = [stats["containers"][c]["served_count"]
                  for c in ("c1", "c2", "c3")]
        # 每个容器应被调度 10 次左右（差异 ≤ 1）
        assert max(served) - min(served) <= 1
        # 响应时间差异应 < 20%
        fairness = stats["_fairness"]
        assert fairness["response_time_diff_ratio"] < 0.2

    def test_weighted_scheduler_gives_more_to_heavier(self):
        """高权重容器获得更多调度机会"""
        fs = FairScheduler(slice_time=0.01)
        fs.register_container("c1", weight=1.0)
        fs.register_container("c2", weight=2.0)  # 双倍权重
        # 模拟 30 次调度
        for _ in range(30):
            cid = fs.pick_next()
            fs.record_service(cid, 0.01)
        stats = fs.get_fairness_stats()
        served_c1 = stats["containers"]["c1"]["served_count"]
        served_c2 = stats["containers"]["c2"]["served_count"]
        # c2 应获得更多调度机会
        assert served_c2 >= served_c1

    def test_unregister_container(self):
        """注销容器后不再被调度"""
        fs = FairScheduler()
        fs.register_container("c1")
        fs.register_container("c2")
        fs.unregister_container("c1")
        assert fs.registered_count == 1
        # 仅 c2 可选
        for _ in range(5):
            assert fs.pick_next() == "c2"

    def test_empty_scheduler_returns_none(self):
        """无注册容器时 pick_next 返回 None"""
        fs = FairScheduler()
        assert fs.pick_next() is None

    def test_invalid_slice_time_raises(self):
        """非法 slice_time 抛出 ValueError"""
        with pytest.raises(ValueError):
            FairScheduler(slice_time=0)
        with pytest.raises(ValueError):
            FairScheduler(slice_time=-0.1)

    def test_invalid_weight_raises(self):
        """非法 weight 抛出 ValueError"""
        fs = FairScheduler()
        with pytest.raises(ValueError):
            fs.register_container("c1", weight=0)
        with pytest.raises(ValueError):
            fs.register_container("c1", weight=-1.0)


# ═══════════════════════════════════════════════════════════════
# RT-003.7 CrossContainerCoordinator 测试
# ═══════════════════════════════════════════════════════════════

class TestCrossContainerCoordinator:
    """跨容器协调测试"""

    def test_report_and_get_pressure(self):
        """压力上报与查询"""
        coord = CrossContainerCoordinator(bus_node=None)
        coord.report_pressure("c1", 0.7)
        assert coord.get_pressure("c1") == 0.7
        coord.report_pressure("c1", 0.9)
        assert coord.get_pressure("c1") == 0.9

    def test_pressure_clamped_to_range(self):
        """压力越界被截断"""
        coord = CrossContainerCoordinator()
        coord.report_pressure("c1", 2.0)
        assert coord.get_pressure("c1") == 1.0
        coord.report_pressure("c1", -1.0)
        assert coord.get_pressure("c1") == 0.0

    def test_coordinate_weights_adjusts_scheduler(self):
        """coordinate_weights 根据压力调整调度权重"""
        fs = FairScheduler()
        fs.register_container("c1")
        fs.register_container("c2")
        coord = CrossContainerCoordinator(bus_node=None)
        # c1 压力高，c2 压力低
        coord.report_pressure("c1", 0.8)
        coord.report_pressure("c2", 0.1)
        weights = coord.coordinate_fairness_weights(fs)
        # c1 权重应高于 c2
        assert weights["c1"] > weights["c2"]
        assert fs.containers["c1"].weight == weights["c1"]
        assert fs.containers["c2"].weight == weights["c2"]

    def test_coordinator_with_mock_bus_node(self):
        """与 mock bus_node 集成（mock-friendly）"""
        mock_bus = MagicMock()
        mock_bus._broadcast = MagicMock()
        coord = CrossContainerCoordinator(bus_node=mock_bus)
        fs = FairScheduler()
        fs.register_container("c1")
        coord.report_pressure("c1", 0.5)
        coord.coordinate_fairness_weights(fs)
        # 应调用 _broadcast
        assert mock_bus._broadcast.called

    def test_coordinator_without_bus_node_works(self):
        """无 bus_node 时仍可工作（仅本地协调）"""
        coord = CrossContainerCoordinator(bus_node=None)
        fs = FairScheduler()
        fs.register_container("c1")
        coord.report_pressure("c1", 0.5)
        weights = coord.coordinate_fairness_weights(fs)
        assert "c1" in weights
        stats = coord.get_stats()
        assert stats["has_bus_node"] is False


# ═══════════════════════════════════════════════════════════════
# CognitiveScheduler 主类集成测试
# ═══════════════════════════════════════════════════════════════

class TestCognitiveSchedulerIntegration:
    """CognitiveScheduler 主类集成测试"""

    def test_register_container(self):
        """注册容器到调度器"""
        sched = CognitiveScheduler()
        sched.register_container("c1", container=None)
        assert "c1" in sched.registered_containers
        assert sched.stats()["registered_containers"] == 1

    def test_register_invalid_container_id_raises(self):
        """空 container_id 抛出 ValueError"""
        sched = CognitiveScheduler()
        with pytest.raises(ValueError):
            sched.register_container("")

    def test_submit_attention_uses_psi_urgency_mapping(self):
        """submit_attention 通过 PSI 紧迫度映射入队"""
        sched = CognitiveScheduler(urgency_mode="linear")
        sched.register_container("c1")
        # activation=0.9 → urgency=0.9（线性模式）
        req = sched.submit_attention(
            container_id="c1",
            need_name="certainty",
            activation=0.9,
        )
        assert req.urgency == pytest.approx(0.9)
        assert req.container_id == "c1"
        assert req.need_name == "certainty"
        assert sched.attention_queue_size == 1

    def test_high_activation_gets_focus_first(self):
        """高激活值的需求优先获得焦点（验收标准 2）"""
        sched = CognitiveScheduler(urgency_mode="linear")
        sched.register_container("c1")
        sched.register_container("c2")
        sched.submit_attention("c1", "low", activation=0.1)
        sched.submit_attention("c2", "high", activation=0.95)
        focused = sched.acquire_focus()
        assert focused is not None
        assert focused.container_id == "c2"
        assert focused.need_name == "high"

    def test_working_memory_limit_enforced(self):
        """工作记忆上限 ≤ 7（验收标准 3）"""
        sched = CognitiveScheduler()
        assert sched.working_memory_limit == 7
        sched.register_container("c1")
        # 写入 7 条
        for i in range(7):
            sched.store_working_memory("c1", f"k{i}", f"v{i}")
        # 第 8 条应触发淘汰
        evicted = sched.store_working_memory("c1", "k7", "v7")
        assert evicted == "v0"  # FIFO 头部被淘汰
        # 仍为 7 条
        usage = sched.get_memory_usage("c1")
        assert usage["working_count"] == 7

    def test_episodic_memory_configurable(self):
        """情景记忆上限可配置"""
        sched = CognitiveScheduler(episodic_memory_limit=3)
        assert sched.episodic_memory_limit == 3
        sched.register_container("c1")
        for i in range(3):
            sched.store_episodic_memory("c1", {"i": i})
        evicted = sched.store_episodic_memory("c1", {"i": 3})
        assert evicted == {"i": 0}

    def test_semantic_memory_unlimited(self):
        """语义记忆无上限"""
        sched = CognitiveScheduler()
        sched.register_container("c1")
        for i in range(100):
            sched.store_semantic_memory("c1", f"k{i}", f"v{i}")
        usage = sched.get_memory_usage("c1")
        assert usage["semantic_count"] == 100
        assert usage["semantic_limit"] is None

    def test_broadcast_throttle_under_ten_per_second(self):
        """广播限流每秒 ≤ 10 条（验收标准 4）"""
        sched = CognitiveScheduler(
            broadcast_rate=10.0,
            broadcast_capacity=10,
        )
        sched.register_container("c1")
        # 前 10 条放行
        allowed = sum(1 for _ in range(10) if sched.try_broadcast("c1"))
        assert allowed == 10
        # 第 11 条被限流
        assert sched.try_broadcast("c1") is False
        stats = sched.get_broadcast_stats("c1")
        assert stats["allowed"] == 10
        assert stats["dropped"] == 1

    def test_fairness_three_containers_no_starvation(self):
        """3 个生命体并发无饥饿（响应时间差异 < 20%）（验收标准 5）"""
        sched = CognitiveScheduler(slice_time=0.01)
        sched.register_container("c1")
        sched.register_container("c2")
        sched.register_container("c3")
        # 模拟 30 次调度
        for _ in range(30):
            cid = sched.schedule_next()
            assert cid is not None
            sched.record_service(cid, 0.01)
        stats = sched.get_fairness_stats()
        served = [stats["containers"][c]["served_count"]
                  for c in ("c1", "c2", "c3")]
        # 服务次数差异 ≤ 1
        assert max(served) - min(served) <= 1
        # 响应时间差异 < 20%
        assert stats["_fairness"]["response_time_diff_ratio"] < 0.2

    def test_coordinate_weights_integration(self):
        """跨容器协调权重调整"""
        sched = CognitiveScheduler()
        sched.register_container("c1")
        sched.register_container("c2")
        sched.report_pressure("c1", 0.9)
        sched.report_pressure("c2", 0.1)
        weights = sched.coordinate_weights()
        assert weights["c1"] > weights["c2"]

    def test_stats_returns_all_components(self):
        """stats 返回所有组件状态"""
        sched = CognitiveScheduler()
        sched.register_container("c1")
        stats = sched.stats()
        assert "registered_containers" in stats
        assert "attention_queue_size" in stats
        assert "memory_quota" in stats
        assert "broadcast" in stats
        assert "fair_scheduler" in stats
        assert "coordinator" in stats

    def test_repr_contains_key_info(self):
        """__repr__ 包含关键信息"""
        sched = CognitiveScheduler()
        sched.register_container("c1")
        r = repr(sched)
        assert "CognitiveScheduler" in r
        assert "containers=1" in r


# ═══════════════════════════════════════════════════════════════
# Mock-friendly 与 MigrationBusNode 集成测试
# ═══════════════════════════════════════════════════════════════

class TestMockFriendlyAndBusIntegration:
    """mock 友好性与 MigrationBusNode 集成测试"""

    def test_scheduler_works_without_real_container(self):
        """调度器无需真实 LifeformContainer 即可工作"""
        sched = CognitiveScheduler()
        # container 参数可为 None 或任意 mock 对象
        sched.register_container("c1", container=None)
        sched.register_container("c2", container=MagicMock())
        # 完整工作流
        sched.submit_attention("c1", "need1", activation=0.5)
        sched.submit_attention("c2", "need2", activation=0.9)
        focused = sched.acquire_focus()
        assert focused.container_id == "c2"
        sched.store_working_memory("c1", "k", "v")
        sched.try_broadcast("c1")
        sched.record_service("c1", 0.01)

    def test_scheduler_with_migration_bus_node(self):
        """与 MigrationBusNode 集成（mock-friendly）"""
        # 使用 MagicMock 而非真实 MigrationBusNode（避免依赖网络）
        mock_bus = MagicMock()
        mock_bus._broadcast = MagicMock()
        sched = CognitiveScheduler(bus_node=mock_bus)
        sched.register_container("c1")
        sched.register_container("c2")
        sched.report_pressure("c1", 0.8)
        sched.coordinate_weights()
        # 应通过 bus_node 广播压力信息
        assert mock_bus._broadcast.called

    def test_full_workflow_attention_memory_broadcast_fairness(self):
        """完整工作流：注意力 + 记忆 + 广播 + 公平调度"""
        sched = CognitiveScheduler(
            working_memory_limit=7,
            episodic_memory_limit=1000,
            broadcast_rate=10.0,
            broadcast_capacity=10,
            urgency_mode="step",
        )
        # 注册 3 个容器
        for i in range(3):
            sched.register_container(f"c{i}")
        # 提交注意力请求
        sched.submit_attention("c0", "certainty", 0.3)   # low
        sched.submit_attention("c1", "competence", 0.7)  # high
        sched.submit_attention("c2", "exploration", 0.9) # critical
        # 验证焦点顺序
        first = sched.acquire_focus()
        assert first.urgency == PSIUrgencyMapper.URGENCY_CRITICAL
        second = sched.acquire_focus()
        assert second.urgency == PSIUrgencyMapper.URGENCY_HIGH
        third = sched.acquire_focus()
        assert third.urgency == PSIUrgencyMapper.URGENCY_LOW
        # 记忆操作
        for i in range(7):
            sched.store_working_memory("c0", f"k{i}", f"v{i}")
        # 第 8 条触发淘汰
        evicted = sched.store_working_memory("c0", "k7", "v7")
        assert evicted == "v0"
        # 广播限流
        for _ in range(10):
            assert sched.try_broadcast("c0") is True
        assert sched.try_broadcast("c0") is False
        # 公平调度
        for _ in range(9):
            cid = sched.schedule_next()
            sched.record_service(cid, 0.01)
        stats = sched.get_fairness_stats()
        # 每个容器应被调度 3 次
        served = [stats["containers"][c]["served_count"]
                  for c in ("c0", "c1", "c2")]
        assert max(served) - min(served) <= 1

    def test_unregister_container_stops_scheduling(self):
        """注销容器后不再被调度"""
        sched = CognitiveScheduler()
        sched.register_container("c1")
        sched.register_container("c2")
        sched.unregister_container("c1")
        assert "c1" not in sched.registered_containers
        # 仅 c2 被调度
        for _ in range(5):
            assert sched.schedule_next() == "c2"
