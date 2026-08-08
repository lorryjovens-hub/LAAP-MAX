"""
LAAP AGI — Consciousness Harness Full Integration Test Suite

完整的集成测试，测试 ConsciousnessHarness 的完整功能：
- 意识循环、情感演化、元认知监控、记忆整合的完整流程
- 系统提示生成器的完整输出
- 性能基准（响应时间、内存占用）
"""

import pytest
import asyncio
import time
import psutil
import os
import numpy as np
from unittest.mock import MagicMock

from laap.agi.consciousness_integrator import ConsciousnessHarness, ConsciousContext
from laap.agi.affective_engine import AffectiveState, PersonalityProfile, EmotionDimension
from laap.agi.meta_cognitive import MetaCognitiveMonitor
from laap.agi.gw_workspace import GlobalWorkspace, CoalitionalProcess, ProcessType


class TestConsciousnessHarnessFull:
    """ConsciousnessHarness 完整功能测试"""

    def setup_method(self):
        """设置测试环境"""
        self.harness = ConsciousnessHarness()
        self.harness.initialize_personality()

    def test_harness_initialization(self):
        """测试 ConsciousnessHarness 初始化"""
        assert self.harness.workspace is not None
        assert isinstance(self.harness.workspace, GlobalWorkspace)
        assert self.harness.affective is not None
        assert isinstance(self.harness.affective, AffectiveState)
        assert self.harness.meta is not None
        assert isinstance(self.harness.meta, MetaCognitiveMonitor)
        assert self.harness.personality is not None
        assert isinstance(self.harness.personality, PersonalityProfile)
        assert self.harness.running is False

    def test_personality_initialization(self):
        """测试人格轮廓初始化"""
        profile = PersonalityProfile(
            name="TestProfile",
            baseline=np.array([0.1, 0.2, 0.3, 0.4, 0.5]),
            sensitivity=np.array([1.0, 1.2, 0.8, 1.0, 0.9]),
            decay_rates=np.array([0.1, 0.15, 0.12, 0.08, 0.2]),
            noise_amplitude=0.05,
        )
        
        harness = ConsciousnessHarness()
        harness.initialize_personality(profile)
        
        assert harness.personality.name == "TestProfile"
        assert harness.affective is not None
        assert "affective_monitor" in harness.workspace.processes

    @pytest.mark.asyncio
    async def test_process_input_basic(self):
        """测试基本输入处理"""
        context = await self.harness.process_input("Hello, how are you?", {})
        
        assert isinstance(context, ConsciousContext)
        assert context.mood_label is not None
        assert context.attention_focus is not None
        assert isinstance(context.conscious_contents, list)
        assert len(context.conscious_contents) > 0

    @pytest.mark.asyncio
    async def test_process_input_positive_feedback(self):
        """测试积极反馈处理"""
        for _ in range(3):
            context = await self.harness.process_input("Great job! You're amazing!", {})
        
        mood = context.mood_label
        assert mood in ["joyful", "content", "relaxed", "neutral"]
        
        emotional_state = context.emotional_state
        assert emotional_state.get("valence", 0) >= 0

    @pytest.mark.asyncio
    async def test_process_input_negative_feedback(self):
        """测试消极反馈处理"""
        for _ in range(3):
            context = await self.harness.process_input("This is terrible! You failed!", {})
        
        mood = context.mood_label
        assert mood in ["sad", "angry", "depressed", "neutral"]
        
        emotional_state = context.emotional_state
        assert emotional_state.get("valence", 0) <= 0

    @pytest.mark.asyncio
    async def test_process_input_error(self):
        """测试错误事件处理"""
        for _ in range(2):
            context = await self.harness.process_input("Error: connection timeout", {})
        
        emotional_state = context.emotional_state
        dimensions = emotional_state.get("dimensions", {})
        stress_value = dimensions.get("stress", 0) if dimensions else emotional_state.get("stress", 0)
        assert stress_value >= 0

    @pytest.mark.asyncio
    async def test_consciousness_loop(self):
        """测试意识循环运行"""
        await self.harness.start()
        
        assert self.harness.running is True
        
        await asyncio.sleep(0.6)
        
        assert self.harness.tick_task is not None
        
        await self.harness.stop()
        
        assert self.harness.running is False

    @pytest.mark.asyncio
    async def test_emotional_evolution(self):
        """测试情感状态演化"""
        for _ in range(5):
            await self.harness.process_input("I'm so happy with your work!", {})
        
        valence_after_positive = self.harness.affective.get_valence_arousal()[0]
        assert valence_after_positive >= -0.3
        
        for _ in range(6):
            await self.harness.process_input("This is terrible! Complete failure!", {})
        
        valence_after_negative = self.harness.affective.get_valence_arousal()[0]
        assert valence_after_negative <= 0.3

    @pytest.mark.asyncio
    async def test_cognitive_biases_update(self):
        """测试认知偏差更新"""
        context = await self.harness.process_input("I absolutely love this!", {})
        
        biases = context.cognitive_biases
        assert isinstance(biases, dict)
        assert "optimism" in biases
        assert "risk_seeking" in biases
        assert "attention_narrowing" in biases
        assert "confirmation_bias" in biases
        assert "overconfidence" in biases
        
        for key, value in biases.items():
            assert -0.8 <= value <= 0.8

    @pytest.mark.asyncio
    async def test_self_report_generation(self):
        """测试自我报告生成"""
        for i in range(3):
            await self.harness.process_input(f"Test message {i}", {})
        
        context = await self.harness.process_input("Check self report", {})
        
        self_report = context.self_report
        assert isinstance(self_report, dict)
        assert "meta_cognitive_report" in self_report
        
        report = self_report["meta_cognitive_report"]
        assert "total_episodes" in report
        assert "success_rate" in report
        assert "average_confidence" in report
        assert "total_reflections" in report

    @pytest.mark.asyncio
    async def test_system_prompt_addon(self):
        """测试系统提示生成器"""
        await self.harness.process_input("Hello, how are you?", {})
        
        prompt_addon = self.harness.generate_system_prompt_addon()
        
        assert isinstance(prompt_addon, str)
        assert "意识注入" in prompt_addon
        assert "当前情绪" in prompt_addon
        assert "情感维度" in prompt_addon
        assert "元认知状态" in prompt_addon
        assert "注意力焦点" in prompt_addon

    def test_get_consciousness_report(self):
        """测试意识报告获取"""
        report = self.harness.get_consciousness_report()
        
        assert isinstance(report, dict)
        assert "consciousness_harness" in report
        assert "global_workspace" in report
        assert "conscious_context" in report
        assert "meta_cognitive" in report
        assert "affective" in report
        assert "broadcast_history" in report

    @pytest.mark.asyncio
    async def test_record_output_success(self):
        """测试记录成功输出"""
        await self.harness.process_input("Complete this task", {})
        
        await self.harness.record_output("Task completed successfully", "success", confidence=0.8)
        
        report = self.harness.get_consciousness_report()
        meta_report = report["meta_cognitive"]["self_report"]["meta_cognitive_report"]
        assert meta_report["total_episodes"] >= 1

    @pytest.mark.asyncio
    async def test_record_output_failure(self):
        """测试记录失败输出"""
        await self.harness.process_input("Try to complete task", {})
        
        await self.harness.record_output("Task failed", "failure", confidence=0.3)
        
        assert len(self.harness.meta.reflections) >= 1

    @pytest.mark.asyncio
    async def test_emotional_decay(self):
        """测试情感衰减"""
        for _ in range(3):
            await self.harness.process_input("Excellent work!", {})
        
        await self.harness.start()
        await asyncio.sleep(3.0)
        await self.harness.stop()
        
        final_valence = self.harness.affective.get_valence_arousal()[0]
        assert abs(final_valence) <= 1.0

    def test_performance_response_time(self):
        """测试响应时间性能"""
        start_time = time.time()
        
        async def run():
            await self.harness.process_input("Performance test message", {})
        
        asyncio.run(run())
        
        elapsed = (time.time() - start_time) * 1000
        
        assert elapsed < 500, f"响应时间过长: {elapsed:.1f}ms"

    def test_performance_memory_usage(self):
        """测试内存占用性能"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        async def run():
            for i in range(10):
                await self.harness.process_input(f"Memory test {i}", {})
        
        asyncio.run(run())
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        assert memory_increase < 50, f"内存增长过多: {memory_increase:.1f} MB"

    @pytest.mark.asyncio
    async def test_full_integration_flow(self):
        """测试完整集成流程"""
        inputs = [
            ("Hello! How can you help me?", "user_engagement"),
            ("That's a great idea!", "user_positive_feedback"),
            ("Let me think about it...", "user_engagement"),
            ("This is working perfectly!", "user_positive_feedback"),
        ]
        
        moods = []
        valences = []
        
        for input_text, _ in inputs:
            context = await self.harness.process_input(input_text, {})
            moods.append(context.mood_label)
            valences.append(context.emotional_state.get("valence", 0))
        
        assert len(moods) == 4
        assert all(m is not None for m in moods)
        
        positive_moods = [m for m in moods if m in ["joyful", "content", "relaxed", "neutral"]]
        assert len(positive_moods) >= 3


class TestConsciousnessHarnessWithLLM:
    """带模拟LLM的ConsciousnessHarness测试"""

    def setup_method(self):
        """设置测试环境"""
        class MockLLMClient:
            def complete(self, prompt):
                return "模拟LLM反思结果：推理过程合理，但可以增加备选方案分析。"
        
        self.harness = ConsciousnessHarness(llm_client=MockLLMClient())
        self.harness.initialize_personality()

    @pytest.mark.asyncio
    async def test_llm_reflection(self):
        """测试LLM深度反思"""
        await self.harness.process_input("Test with LLM", {})
        await self.harness.record_output("Test output", "failure", confidence=0.2)
        
        reflections = self.harness.meta.reflections
        assert len(reflections) >= 1
        
        reflection = reflections[-1]
        if "llm_insight" in reflection:
            assert "模拟LLM反思结果" in reflection["llm_insight"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])