"""ResourceBudget 测试用例"""

import pytest

from laap.sandbox.resource_budget import (
    DegradationLevel,
    ResourceBudget,
    ResourceType,
)


class TestResourceBudget:
    """ResourceBudget 测试类"""

    def test_initial_state_all_v5(self):
        """测试1: 初始状态：所有资源降级为 V5"""
        budget = ResourceBudget("test-sandbox")
        for rt in ResourceType:
            assert budget.get_degradation_level(rt) == DegradationLevel.V5

    def test_check_returns_true_when_budget_sufficient(self):
        """测试2: check 返回 True（预算充足）"""
        budget = ResourceBudget("test-sandbox", llm_calls_per_hour=10)
        assert budget.check(ResourceType.LLM_CALLS_PER_HOUR, 5) is True
        assert budget.check(ResourceType.LLM_CALLS_PER_HOUR, 10) is True

    def test_consume_successfully_consumes_budget(self):
        """测试3: consume 成功消耗预算"""
        budget = ResourceBudget("test-sandbox", llm_calls_per_hour=10)
        assert budget.consume(ResourceType.LLM_CALLS_PER_HOUR, 5) is True
        assert budget.consume(ResourceType.LLM_CALLS_PER_HOUR, 3) is True
        stats = budget.stats()
        assert stats["consumed"]["llm_calls_per_hour"] == 8

    def test_llm_calls_exhaust_triggers_degradation_to_llm(self):
        """测试4: LLM 调用预算耗尽后触发降级到 LLM"""
        budget = ResourceBudget("test-sandbox", llm_calls_per_hour=3)
        assert budget.consume(ResourceType.LLM_CALLS_PER_HOUR) is True
        assert budget.consume(ResourceType.LLM_CALLS_PER_HOUR) is True
        assert budget.consume(ResourceType.LLM_CALLS_PER_HOUR) is True
        assert budget.consume(ResourceType.LLM_CALLS_PER_HOUR) is False
        assert budget.get_degradation_level(ResourceType.LLM_CALLS_PER_HOUR) == DegradationLevel.LLM

    def test_llm_degradation_then_exhaust_triggers_cached(self):
        """测试5: LLM 降级后再耗尽，触发降级到 CACHED"""
        budget = ResourceBudget("test-sandbox", llm_calls_per_hour=2)
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR)
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR)
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR)
        assert budget.get_degradation_level(ResourceType.LLM_CALLS_PER_HOUR) == DegradationLevel.LLM
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR)
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR)
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR)
        assert budget.get_degradation_level(ResourceType.LLM_CALLS_PER_HOUR) == DegradationLevel.CACHED

    def test_cached_state_consume_returns_false(self):
        """测试6: CACHED 状态下 consume 直接返回 False"""
        budget = ResourceBudget("test-sandbox", llm_calls_per_hour=1)
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR)
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR)
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR)
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR)
        assert budget.get_degradation_level(ResourceType.LLM_CALLS_PER_HOUR) == DegradationLevel.CACHED
        assert budget.consume(ResourceType.LLM_CALLS_PER_HOUR) is False
        assert budget.check(ResourceType.LLM_CALLS_PER_HOUR) is False

    def test_cpu_time_window_exhaust_triggers_degradation(self):
        """测试7: CPU 时间窗口耗尽触发降级"""
        budget = ResourceBudget("test-sandbox", cpu_seconds_per_min=5)
        assert budget.consume(ResourceType.CPU_SECONDS_PER_MIN, 5) is True
        assert budget.consume(ResourceType.CPU_SECONDS_PER_MIN, 1) is False
        assert budget.get_degradation_level(ResourceType.CPU_SECONDS_PER_MIN) == DegradationLevel.LLM

    def test_time_window_reset_degradation_bounces_back(self):
        """测试8: 时间窗口重置后降级回弹到 V5"""
        budget = ResourceBudget("test-sandbox", cpu_seconds_per_min=2, inference_time_sec=2)
        budget.consume(ResourceType.CPU_SECONDS_PER_MIN, 2)
        budget.consume(ResourceType.CPU_SECONDS_PER_MIN, 1)
        assert budget.get_degradation_level(ResourceType.CPU_SECONDS_PER_MIN) == DegradationLevel.LLM
        budget.reset_window(ResourceType.CPU_SECONDS_PER_MIN)
        assert budget.get_degradation_level(ResourceType.CPU_SECONDS_PER_MIN) == DegradationLevel.V5
        assert budget.consume(ResourceType.CPU_SECONDS_PER_MIN, 2) is True

    def test_reset_window_single_resource(self):
        """测试9: reset_window(rt) 只重置该资源"""
        budget = ResourceBudget("test-sandbox", llm_calls_per_hour=2, cpu_seconds_per_min=2)
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR, 2)
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR, 1)
        budget.consume(ResourceType.CPU_SECONDS_PER_MIN, 2)
        budget.consume(ResourceType.CPU_SECONDS_PER_MIN, 1)
        assert budget.get_degradation_level(ResourceType.LLM_CALLS_PER_HOUR) == DegradationLevel.LLM
        assert budget.get_degradation_level(ResourceType.CPU_SECONDS_PER_MIN) == DegradationLevel.LLM
        budget.reset_window(ResourceType.LLM_CALLS_PER_HOUR)
        assert budget.get_degradation_level(ResourceType.LLM_CALLS_PER_HOUR) == DegradationLevel.V5
        assert budget.get_degradation_level(ResourceType.CPU_SECONDS_PER_MIN) == DegradationLevel.LLM

    def test_reset_window_all_resources(self):
        """测试10: reset_window() 重置全部"""
        budget = ResourceBudget("test-sandbox", llm_calls_per_hour=2, cpu_seconds_per_min=2)
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR, 2)
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR, 1)
        budget.consume(ResourceType.CPU_SECONDS_PER_MIN, 2)
        budget.consume(ResourceType.CPU_SECONDS_PER_MIN, 1)
        assert budget.get_degradation_level(ResourceType.LLM_CALLS_PER_HOUR) == DegradationLevel.LLM
        assert budget.get_degradation_level(ResourceType.CPU_SECONDS_PER_MIN) == DegradationLevel.LLM
        budget.reset_window()
        for rt in ResourceType:
            assert budget.get_degradation_level(rt) == DegradationLevel.V5

    def test_get_effective_degradation_returns_most_restrictive(self):
        """测试11: get_effective_degradation 返回最受限等级"""
        budget = ResourceBudget("test-sandbox", llm_calls_per_hour=2, cpu_seconds_per_min=5)
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR, 2)
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR, 1)
        assert budget.get_degradation_level(ResourceType.LLM_CALLS_PER_HOUR) == DegradationLevel.LLM
        assert budget.get_degradation_level(ResourceType.CPU_SECONDS_PER_MIN) == DegradationLevel.V5
        assert budget.get_effective_degradation() == DegradationLevel.LLM
        budget.consume(ResourceType.CPU_SECONDS_PER_MIN, 5)
        budget.consume(ResourceType.CPU_SECONDS_PER_MIN, 1)
        budget.consume(ResourceType.CPU_SECONDS_PER_MIN, 5)
        budget.consume(ResourceType.CPU_SECONDS_PER_MIN, 1)
        assert budget.get_degradation_level(ResourceType.CPU_SECONDS_PER_MIN) == DegradationLevel.CACHED
        assert budget.get_effective_degradation() == DegradationLevel.CACHED

    def test_memory_mb_special_handling(self):
        """测试12: MEMORY_MB 特殊处理（瞬时值）"""
        budget = ResourceBudget("test-sandbox", memory_mb=1024)
        assert budget.consume(ResourceType.MEMORY_MB, 512) is True
        stats = budget.stats()
        assert stats["consumed"]["memory_mb"] == 512
        assert budget.consume(ResourceType.MEMORY_MB, 1024) is True
        stats = budget.stats()
        assert stats["consumed"]["memory_mb"] == 1024
        assert budget.consume(ResourceType.MEMORY_MB, 2048) is False
        assert budget.get_degradation_level(ResourceType.MEMORY_MB) == DegradationLevel.LLM

    def test_degradation_history_records_correctly(self):
        """测试13: _degradation_history 记录正确"""
        budget = ResourceBudget("test-sandbox", llm_calls_per_hour=2)
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR, 2)
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR, 1)
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR, 1)
        history = budget._degradation_history
        assert len(history) >= 1
        assert history[-1]["resource"] == "llm_calls_per_hour"
        assert "old_level" in history[-1]
        assert "new_level" in history[-1]
        assert "timestamp" in history[-1]

    def test_stats_returns_correct_statistics(self):
        """测试14: stats() 返回正确统计"""
        budget = ResourceBudget("test-sandbox", llm_calls_per_hour=10, cpu_seconds_per_min=30)
        budget.consume(ResourceType.LLM_CALLS_PER_HOUR, 3)
        budget.consume(ResourceType.CPU_SECONDS_PER_MIN, 15)
        stats = budget.stats()
        assert stats["sandbox_id"] == "test-sandbox"
        assert stats["limits"]["llm_calls_per_hour"] == 10
        assert stats["consumed"]["llm_calls_per_hour"] == 3
        assert stats["consumed"]["cpu_seconds_per_min"] == 15
        assert stats["effective_degradation"] == "v5"
        assert "degradation_history_count" in stats

    def test_isolation_two_instances_independent(self):
        """测试15: 隔离性：两个 ResourceBudget 实例互不影响"""
        budget1 = ResourceBudget("sandbox-1", llm_calls_per_hour=2)
        budget2 = ResourceBudget("sandbox-2", llm_calls_per_hour=2)
        budget1.consume(ResourceType.LLM_CALLS_PER_HOUR, 2)
        budget1.consume(ResourceType.LLM_CALLS_PER_HOUR, 1)
        assert budget1.get_degradation_level(ResourceType.LLM_CALLS_PER_HOUR) == DegradationLevel.LLM
        assert budget2.get_degradation_level(ResourceType.LLM_CALLS_PER_HOUR) == DegradationLevel.V5
        assert budget2.consume(ResourceType.LLM_CALLS_PER_HOUR) is True
        budget1.consume(ResourceType.LLM_CALLS_PER_HOUR, 2)
        budget1.consume(ResourceType.LLM_CALLS_PER_HOUR, 1)
        assert budget1.get_degradation_level(ResourceType.LLM_CALLS_PER_HOUR) == DegradationLevel.CACHED
        assert budget1.consume(ResourceType.LLM_CALLS_PER_HOUR) is False

    def test_inference_time_degradation(self):
        """测试16: 推理时间超限触发降级"""
        budget = ResourceBudget("test-sandbox", inference_time_sec=5)
        assert budget.consume(ResourceType.INFERENCE_TIME_SEC, 5) is True
        assert budget.consume(ResourceType.INFERENCE_TIME_SEC, 1) is False
        assert budget.get_degradation_level(ResourceType.INFERENCE_TIME_SEC) == DegradationLevel.LLM

    def test_check_with_large_amount(self):
        """测试17: check 检查大额消耗"""
        budget = ResourceBudget("test-sandbox", llm_calls_per_hour=10)
        assert budget.check(ResourceType.LLM_CALLS_PER_HOUR, 10) is True
        assert budget.check(ResourceType.LLM_CALLS_PER_HOUR, 11) is False

    def test_memory_exceed_triggers_degradation(self):
        """测试18: 内存超限触发降级"""
        budget = ResourceBudget("test-sandbox", memory_mb=512)
        assert budget.consume(ResourceType.MEMORY_MB, 512) is True
        assert budget.consume(ResourceType.MEMORY_MB, 513) is False
        assert budget.get_degradation_level(ResourceType.MEMORY_MB) == DegradationLevel.LLM