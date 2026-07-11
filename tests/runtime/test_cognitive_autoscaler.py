# -*- coding: utf-8 -*-
"""RT-007 CognitiveAutoscaler 测试

覆盖：
- ScalingPolicy 数据类配置与校验（RT-007.1）
- CognitiveAutoscaler 类骨架与接口（RT-007.2）
- 扩容逻辑：注意力焦点 / 工作记忆 / 广播带宽扩展（RT-007.3）
- 缩容逻辑：注意力焦点 / 情景记忆压缩 / 广播频率降低（RT-007.4）
- 与 CognitiveScheduler 集成，配额动态调整（RT-007.5）
- mock-friendly：可直接使用 MagicMock 替代 CognitiveScheduler
"""
import time
from unittest.mock import MagicMock

import pytest

from laap_runtime.cognitive_autoscaler import (
    CognitiveAutoscaler,
    LoadMetric,
    ScalingDecision,
    ScalingPolicy,
)
from laap_runtime.cognitive_scheduler import CognitiveScheduler


# ═══════════════════════════════════════════════════════════════
# RT-007.1 ScalingPolicy / LoadMetric 测试
# ═══════════════════════════════════════════════════════════════

class TestScalingPolicy:
    """ScalingPolicy 配置测试"""

    def test_default_policy_values(self):
        """默认策略值应符合 RT-007 规范"""
        p = ScalingPolicy()
        assert p.attention_focus_capacity_default == 5
        assert p.attention_focus_capacity_max == 20
        assert p.working_memory_default == 7
        assert p.working_memory_max == 21
        assert p.broadcast_rate_default == 10.0
        assert p.broadcast_rate_max == 50.0
        assert p.load_threshold_high == 0.8
        assert p.load_threshold_low == 0.2
        assert p.idle_duration_sec == 30 * 60
        assert p.episodic_eviction_ratio == 0.2

    def test_invalid_threshold_order_raises(self):
        """阈值顺序非法时应抛出 ValueError"""
        with pytest.raises(ValueError):
            ScalingPolicy(load_threshold_low=0.9, load_threshold_high=0.1)

    def test_invalid_capacity_bounds_raise(self):
        """默认容量超过最大容量时应抛出 ValueError"""
        with pytest.raises(ValueError):
            ScalingPolicy(
                attention_focus_capacity_default=25,
                attention_focus_capacity_max=20,
            )
        with pytest.raises(ValueError):
            ScalingPolicy(working_memory_default=10, working_memory_max=7)

    def test_invalid_eviction_ratio_raises(self):
        """淘汰比例越界时应抛出 ValueError"""
        with pytest.raises(ValueError):
            ScalingPolicy(episodic_eviction_ratio=1.5)
        with pytest.raises(ValueError):
            ScalingPolicy(episodic_eviction_ratio=-0.1)


class TestLoadMetric:
    """LoadMetric 数据结构测试"""

    def test_is_idle_only_depends_on_cpu_and_memory(self):
        """空闲判定仅依赖 CPU/内存使用率"""
        m = LoadMetric(
            attention_queue_length=100, cpu_load=0.1, memory_load=0.1
        )
        assert m.is_idle(0.2, 0.2) is True

    def test_is_idle_false_when_cpu_high(self):
        """CPU 高于阈值时不应判定为空闲"""
        m = LoadMetric(cpu_load=0.3, memory_load=0.1)
        assert m.is_idle(0.2, 0.2) is False


# ═══════════════════════════════════════════════════════════════
# RT-007.2 CognitiveAutoscaler 骨架与监控测试
# ═══════════════════════════════════════════════════════════════

class TestCognitiveAutoscalerSkeleton:
    """CognitiveAutoscaler 类骨架测试"""

    def test_autoscaler_uses_default_policy(self):
        """未传入策略时应使用默认策略"""
        autoscaler = CognitiveAutoscaler()
        assert isinstance(autoscaler.policy, ScalingPolicy)
        assert autoscaler.policy.attention_focus_capacity_default == 5

    def test_autoscaler_accepts_custom_policy(self):
        """应能使用自定义策略"""
        policy = ScalingPolicy(attention_focus_capacity_default=3)
        autoscaler = CognitiveAutoscaler(policy=policy)
        assert autoscaler.policy is policy

    def test_monitor_accepts_dict(self):
        """monitor 接受 dict 形式负载指标"""
        autoscaler = CognitiveAutoscaler()
        metric = autoscaler.monitor("c1", {
            "attention_queue_length": 5,
            "cpu_load": 0.5,
            "memory_load": 0.5,
        })
        assert metric.attention_queue_length == 5
        assert metric.cpu_load == pytest.approx(0.5)

    def test_monitor_accepts_load_metric_object(self):
        """monitor 接受 LoadMetric 对象"""
        autoscaler = CognitiveAutoscaler()
        metric = LoadMetric(cpu_load=0.4, memory_load=0.3)
        returned = autoscaler.monitor("c1", metric)
        assert returned is metric

    def test_monitor_clamps_out_of_range_values(self):
        """越界负载值应被截断"""
        autoscaler = CognitiveAutoscaler()
        metric = autoscaler.monitor("c1", {
            "attention_queue_length": -3,
            "cpu_load": 1.5,
            "memory_load": -0.2,
        })
        assert metric.attention_queue_length == 0
        assert metric.cpu_load == pytest.approx(1.0)
        assert metric.memory_load == pytest.approx(0.0)

    def test_empty_container_id_raises(self):
        """空容器 ID 应抛出 ValueError"""
        autoscaler = CognitiveAutoscaler()
        with pytest.raises(ValueError):
            autoscaler.monitor("", {"cpu_load": 0.5})
        with pytest.raises(ValueError):
            autoscaler.evaluate("")

    def test_get_capacity_returns_defaults(self):
        """get_capacity 返回默认容量"""
        autoscaler = CognitiveAutoscaler()
        cap = autoscaler.get_capacity("c1")
        assert cap["attention"] == 5
        assert cap["working_memory"] == 7
        assert cap["broadcast_rate"] == pytest.approx(10.0)
        assert cap["broadcast_capacity"] == 10

    def test_evaluate_returns_maintain_without_metrics(self):
        """无历史指标时默认保持当前配置"""
        autoscaler = CognitiveAutoscaler()
        assert autoscaler.evaluate("c1") is ScalingDecision.MAINTAIN


# ═══════════════════════════════════════════════════════════════
# RT-007.3 扩容逻辑测试
# ═══════════════════════════════════════════════════════════════

class TestScaleUpLogic:
    """扩容决策与执行测试"""

    def test_scale_up_when_attention_queue_exceeds_threshold(self):
        """注意力队列长度超过 default*2 时触发扩容"""
        autoscaler = CognitiveAutoscaler()
        # default=5, threshold=10
        autoscaler.monitor("c1", {
            "attention_queue_length": 11,
            "cpu_load": 0.3,
            "memory_load": 0.3,
        })
        assert autoscaler.evaluate("c1") is ScalingDecision.SCALE_UP

    def test_scale_up_when_cpu_load_high(self):
        """CPU 使用率超过 80% 时触发扩容"""
        autoscaler = CognitiveAutoscaler()
        autoscaler.monitor("c1", {
            "attention_queue_length": 2,
            "cpu_load": 0.85,
            "memory_load": 0.3,
        })
        assert autoscaler.evaluate("c1") is ScalingDecision.SCALE_UP

    def test_scale_up_when_memory_load_high(self):
        """内存使用率超过 80% 时触发扩容"""
        autoscaler = CognitiveAutoscaler()
        autoscaler.monitor("c1", {
            "attention_queue_length": 2,
            "cpu_load": 0.3,
            "memory_load": 0.9,
        })
        assert autoscaler.evaluate("c1") is ScalingDecision.SCALE_UP

    def test_exact_attention_threshold_does_not_scale_up(self):
        """队列长度等于阈值时不应扩容"""
        autoscaler = CognitiveAutoscaler()
        autoscaler.monitor("c1", {
            "attention_queue_length": 10,
            "cpu_load": 0.3,
            "memory_load": 0.3,
        })
        assert autoscaler.evaluate("c1") is ScalingDecision.MAINTAIN

    def test_apply_scale_up_increases_capacities(self):
        """扩容后注意力焦点、工作记忆、广播带宽均增加"""
        autoscaler = CognitiveAutoscaler()
        scheduler = CognitiveScheduler()
        autoscaler.monitor("c1", {
            "attention_queue_length": 12,
            "cpu_load": 0.5,
            "memory_load": 0.5,
        })
        decision, details = autoscaler.apply("c1", scheduler)
        assert decision is ScalingDecision.SCALE_UP
        cap = autoscaler.get_capacity("c1")
        assert cap["attention"] == 7
        assert cap["working_memory"] == 9
        assert cap["broadcast_rate"] == pytest.approx(15.0)
        assert details["new_capacity"] == cap

    def test_apply_scale_up_syncs_scheduler_quotas(self):
        """扩容后 CognitiveScheduler 的配额应同步更新"""
        autoscaler = CognitiveAutoscaler()
        scheduler = CognitiveScheduler()
        autoscaler.monitor("c1", {
            "attention_queue_length": 12,
            "cpu_load": 0.5,
            "memory_load": 0.5,
        })
        autoscaler.apply("c1", scheduler)
        assert scheduler.working_memory_limit == 9
        assert scheduler.broadcaster.rate == pytest.approx(15.0)
        assert scheduler.broadcaster.capacity == 15

    def test_scale_up_respects_maximum_caps(self):
        """扩容不应超过策略配置的最大容量"""
        policy = ScalingPolicy(
            attention_focus_capacity_max=6,
            working_memory_max=9,
            broadcast_rate_max=12.0,
        )
        autoscaler = CognitiveAutoscaler(policy=policy)
        scheduler = CognitiveScheduler()
        # 连续触发两次扩容
        for _ in range(2):
            autoscaler.monitor("c1", {
                "attention_queue_length": 20,
                "cpu_load": 0.9,
                "memory_load": 0.9,
            })
            autoscaler.apply("c1", scheduler)
        cap = autoscaler.get_capacity("c1")
        assert cap["attention"] == 6
        assert cap["working_memory"] == 9
        assert cap["broadcast_rate"] == pytest.approx(12.0)


# ═══════════════════════════════════════════════════════════════
# RT-007.4 缩容逻辑测试
# ═══════════════════════════════════════════════════════════════

class TestScaleDownLogic:
    """缩容决策与执行测试"""

    def _make_idle_metric(self, timestamp: float) -> dict:
        """构造低负载指标"""
        return {
            "attention_queue_length": 0,
            "cpu_load": 0.1,
            "memory_load": 0.1,
            "timestamp": timestamp,
        }

    def test_maintain_when_idle_but_not_long_enough(self):
        """空闲但未达到持续时长时不缩容"""
        autoscaler = CognitiveAutoscaler()
        now = time.monotonic()
        autoscaler.monitor("c1", self._make_idle_metric(now))
        autoscaler.monitor(
            "c1",
            self._make_idle_metric(now + autoscaler.policy.idle_duration_sec - 1),
        )
        assert autoscaler.evaluate("c1") is ScalingDecision.MAINTAIN

    def test_scale_down_after_long_idle(self):
        """长期空闲后触发缩容"""
        autoscaler = CognitiveAutoscaler()
        now = time.monotonic()
        autoscaler.monitor("c1", {
            "attention_queue_length": 12,
            "cpu_load": 0.5,
            "memory_load": 0.5,
            "timestamp": now,
        })
        autoscaler.monitor(
            "c1",
            self._make_idle_metric(now + autoscaler.policy.idle_duration_sec + 1),
        )
        assert autoscaler.evaluate("c1") is ScalingDecision.SCALE_DOWN

    def test_apply_scale_down_reduces_capacities(self):
        """缩容后容量应降低"""
        policy = ScalingPolicy(idle_duration_sec=1)
        autoscaler = CognitiveAutoscaler(policy=policy)
        scheduler = CognitiveScheduler()
        now = time.monotonic()
        # 先扩容
        autoscaler.monitor("c1", {
            "attention_queue_length": 12,
            "cpu_load": 0.5,
            "memory_load": 0.5,
            "timestamp": now,
        })
        autoscaler.apply("c1", scheduler)
        # 再空闲缩容
        autoscaler.monitor(
            "c1",
            self._make_idle_metric(now + policy.idle_duration_sec + 1),
        )
        decision, details = autoscaler.apply("c1", scheduler)
        assert decision is ScalingDecision.SCALE_DOWN
        cap = autoscaler.get_capacity("c1")
        assert cap["attention"] == 5
        assert cap["working_memory"] == 7
        assert cap["broadcast_rate"] == pytest.approx(10.0)
        assert "episodic_evicted" in details

    def test_apply_scale_down_compresses_episodic_memory(self):
        """缩容时应按策略比例压缩情景记忆"""
        policy = ScalingPolicy(
            idle_duration_sec=1,
            episodic_eviction_ratio=0.2,
        )
        autoscaler = CognitiveAutoscaler(policy=policy)
        scheduler = CognitiveScheduler()
        scheduler.register_container("c1")
        # 填充 10 条情景记忆
        for i in range(10):
            scheduler.store_episodic_memory("c1", {"event": i})

        now = time.monotonic()
        autoscaler.monitor("c1", {
            "attention_queue_length": 12,
            "cpu_load": 0.5,
            "memory_load": 0.5,
            "timestamp": now,
        })
        autoscaler.apply("c1", scheduler)

        autoscaler.monitor(
            "c1",
            self._make_idle_metric(now + policy.idle_duration_sec + 1),
        )
        decision, details = autoscaler.apply("c1", scheduler)
        assert decision is ScalingDecision.SCALE_DOWN
        assert details["episodic_evicted"] == 2  # 20% of 10
        assert len(scheduler.memory_quota.get_episodic("c1")) == 8

    def test_apply_scale_down_with_custom_eviction_ratio(self):
        """缩容时应支持自定义情景记忆淘汰比例"""
        policy = ScalingPolicy(
            idle_duration_sec=1,
            episodic_eviction_ratio=0.3,
        )
        autoscaler = CognitiveAutoscaler(policy=policy)
        scheduler = CognitiveScheduler()
        scheduler.register_container("c1")
        for i in range(10):
            scheduler.store_episodic_memory("c1", {"event": i})

        now = time.monotonic()
        autoscaler.monitor("c1", {
            "attention_queue_length": 12,
            "cpu_load": 0.5,
            "memory_load": 0.5,
            "timestamp": now,
        })
        autoscaler.apply("c1", scheduler)
        autoscaler.monitor(
            "c1",
            self._make_idle_metric(now + policy.idle_duration_sec + 1),
        )
        _, details = autoscaler.apply("c1", scheduler)
        assert details["episodic_evicted"] == 3  # 30% of 10

    def test_scale_down_respects_default_minimums(self):
        """缩容不应低于默认容量"""
        policy = ScalingPolicy(idle_duration_sec=1)
        autoscaler = CognitiveAutoscaler(policy=policy)
        scheduler = CognitiveScheduler()
        now = time.monotonic()
        autoscaler.monitor("c1", {
            "attention_queue_length": 12,
            "cpu_load": 0.5,
            "memory_load": 0.5,
            "timestamp": now,
        })
        autoscaler.apply("c1", scheduler)
        # 立即再次缩容（容量未超过默认，但仍会尝试压缩记忆）
        autoscaler.monitor(
            "c1",
            self._make_idle_metric(now + policy.idle_duration_sec + 1),
        )
        autoscaler.apply("c1", scheduler)
        cap = autoscaler.get_capacity("c1")
        assert cap["attention"] >= policy.attention_focus_capacity_default
        assert cap["working_memory"] >= policy.working_memory_default
        assert cap["broadcast_rate"] >= policy.broadcast_rate_default


# ═══════════════════════════════════════════════════════════════
# RT-007.5 CognitiveScheduler 集成与 mock-friendly 测试
# ═══════════════════════════════════════════════════════════════

class TestSchedulerIntegration:
    """与 CognitiveScheduler 集成测试"""

    def test_apply_registers_container_on_scheduler(self):
        """apply 会自动将容器注册到 CognitiveScheduler"""
        autoscaler = CognitiveAutoscaler()
        scheduler = CognitiveScheduler()
        autoscaler.monitor("c1", {
            "attention_queue_length": 12,
            "cpu_load": 0.5,
            "memory_load": 0.5,
        })
        autoscaler.apply("c1", scheduler)
        assert "c1" in scheduler.registered_containers

    def test_apply_with_mock_scheduler_does_not_raise(self):
        """mock-friendly：MagicMock 作为 scheduler 不抛异常"""
        autoscaler = CognitiveAutoscaler()
        mock_scheduler = MagicMock()
        autoscaler.monitor("c1", {
            "attention_queue_length": 12,
            "cpu_load": 0.5,
            "memory_load": 0.5,
        })
        decision, details = autoscaler.apply("c1", mock_scheduler)
        assert decision is ScalingDecision.SCALE_UP
        assert mock_scheduler.register_container.called

    def test_scheduler_quotas_updated_after_scale_cycle(self):
        """一次扩缩循环后 scheduler 配额与扩缩容器一致"""
        policy = ScalingPolicy(idle_duration_sec=1)
        autoscaler = CognitiveAutoscaler(policy=policy)
        scheduler = CognitiveScheduler()
        now = time.monotonic()
        # 扩容
        autoscaler.monitor("c1", {
            "attention_queue_length": 12,
            "cpu_load": 0.5,
            "memory_load": 0.5,
            "timestamp": now,
        })
        autoscaler.apply("c1", scheduler)
        assert scheduler.working_memory_limit == 9
        assert scheduler.broadcaster.rate == pytest.approx(15.0)
        # 缩容
        autoscaler.monitor(
            "c1",
            {
                "attention_queue_length": 0,
                "cpu_load": 0.1,
                "memory_load": 0.1,
                "timestamp": now + policy.idle_duration_sec + 1,
            },
        )
        autoscaler.apply("c1", scheduler)
        assert scheduler.working_memory_limit == 7
        assert scheduler.broadcaster.rate == pytest.approx(10.0)


# ═══════════════════════════════════════════════════════════════
# 决策日志与统计测试
# ═══════════════════════════════════════════════════════════════

class TestDecisionLog:
    """决策日志与统计测试"""

    def test_get_decision_log_records_scale_decisions(self):
        """get_decision_log 应记录每次扩缩容决策"""
        autoscaler = CognitiveAutoscaler()
        scheduler = CognitiveScheduler()
        autoscaler.monitor("c1", {
            "attention_queue_length": 12,
            "cpu_load": 0.5,
            "memory_load": 0.5,
        })
        autoscaler.apply("c1", scheduler)
        logs = autoscaler.get_decision_log("c1")
        assert len(logs) == 1
        assert logs[0]["decision"] == ScalingDecision.SCALE_UP.value
        assert "old_capacity" in logs[0]
        assert "new_capacity" in logs[0]

    def test_get_decision_log_returns_copy(self):
        """get_decision_log 返回的是副本，外部修改不影响内部"""
        autoscaler = CognitiveAutoscaler()
        scheduler = CognitiveScheduler()
        autoscaler.monitor("c1", {"attention_queue_length": 12})
        autoscaler.apply("c1", scheduler)
        logs = autoscaler.get_decision_log("c1")
        logs.clear()
        assert len(autoscaler.get_decision_log("c1")) == 1

    def test_stats_returns_summary(self):
        """stats 返回扩缩容器整体统计"""
        autoscaler = CognitiveAutoscaler()
        scheduler = CognitiveScheduler()
        autoscaler.monitor("c1", {"attention_queue_length": 12})
        autoscaler.apply("c1", scheduler)
        summary = autoscaler.stats()
        assert "c1" in summary["tracked_containers"]
        assert summary["container_count"] == 1
        assert summary["capacities"]["c1"]["attention"] == 7
