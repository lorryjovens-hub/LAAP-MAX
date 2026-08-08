"""
LAAP AGI — Consciousness Harness Integration Tests

测试 ConsciousnessHarness 和 UnifiedMemory 在 AGIAgent 中的完整集成流程。
"""

import pytest
from unittest.mock import MagicMock, patch
import asyncio


class TestConsciousnessHarnessIntegration:
    """测试 ConsciousnessHarness 集成到 AGIAgent"""

    def test_agi_agent_initializes_consciousness_harness(self):
        """测试 AGIAgent 能够正确初始化 ConsciousnessHarness"""
        from laap.agi.core import AGIAgent, create_agi_agent
        from laap.agi.consciousness_integrator import ConsciousnessHarness

        agent = AGIAgent(name="TestAgent", state_dir=None, enable_all=True)

        assert agent.consciousness_harness is not None
        assert isinstance(agent.consciousness_harness, ConsciousnessHarness)
        assert agent.consciousness_harness.affective is not None
        assert agent.consciousness_harness.meta is not None
        assert agent.consciousness_harness.workspace is not None

    def test_agi_agent_initializes_unified_memory(self):
        """测试 AGIAgent 能够正确初始化 UnifiedMemory"""
        from laap.agi.core import AGIAgent
        from laap.agi.unified_memory import UnifiedMemory

        agent = AGIAgent(name="TestAgent", state_dir=None, enable_all=True)

        assert agent.unified_memory is not None
        assert isinstance(agent.unified_memory, UnifiedMemory)
        assert agent.unified_memory.episodic_memory is not None
        assert agent.unified_memory.semantic_memory is not None
        assert agent.unified_memory.procedural_memory is not None
        assert agent.unified_memory.consolidator is not None

    def test_modules_registered_on_cognitive_bus(self):
        """测试新模块在 CognitiveBus 上注册"""
        from laap.agi.core import AGIAgent

        agent = AGIAgent(name="TestAgent", state_dir=None, enable_all=True)

        assert agent.cognitive_bus is not None

        module_names = [m["name"] for m in agent.cognitive_bus._modules.values()]
        assert "consciousness_harness" in module_names
        assert "unified_memory" in module_names

    def test_module_count_includes_new_modules(self):
        """测试模块计数包含新模块"""
        from laap.agi.core import AGIAgent

        agent = AGIAgent(name="TestAgent", state_dir=None, enable_all=True)

        count = agent._module_count()
        assert count >= 20

    def test_process_interaction_returns_consciousness_data(self):
        """测试 process_interaction 返回意识状态数据"""
        from laap.agi.core import AGIAgent

        agent = AGIAgent(name="TestAgent", state_dir=None, enable_all=True)

        result = agent.process_interaction(
            user_message="Hello, how are you?",
            domain="chat",
        )

        assert "consciousness_harness" in result
        conscious_data = result["consciousness_harness"]
        assert "mood" in conscious_data
        assert "attention_focus" in conscious_data
        assert "emotional_state" in conscious_data
        assert "cognitive_biases" in conscious_data

    def test_process_interaction_returns_prompt_addon(self):
        """测试 process_interaction 生成意识系统提示附加内容"""
        from laap.agi.core import AGIAgent

        agent = AGIAgent(name="TestAgent", state_dir=None, enable_all=True)

        result = agent.process_interaction(
            user_message="What is your current state?",
            domain="general",
        )

        assert "consciousness_prompt_addon" in result
        prompt_addon = result["consciousness_prompt_addon"]
        assert isinstance(prompt_addon, str)
        assert "意识注入" in prompt_addon

    def test_get_state_includes_consciousness_harness(self):
        """测试 get_state 包含 ConsciousnessHarness 状态"""
        from laap.agi.core import AGIAgent

        agent = AGIAgent(name="TestAgent", state_dir=None, enable_all=True)

        state = agent.get_state()

        assert "consciousness_harness" in state
        harness_state = state["consciousness_harness"]
        assert "consciousness_harness" in harness_state
        assert "global_workspace" in harness_state
        assert "conscious_context" in harness_state
        assert "meta_cognitive" in harness_state
        assert "affective" in harness_state

    def test_get_state_includes_unified_memory(self):
        """测试 get_state 包含 UnifiedMemory 状态"""
        from laap.agi.core import AGIAgent

        agent = AGIAgent(name="TestAgent", state_dir=None, enable_all=True)

        state = agent.get_state()

        assert "unified_memory" in state
        memory_state = state["unified_memory"]
        assert "working_memory_size" in memory_state
        assert "episodic_memory_count" in memory_state
        assert "semantic_memory_count" in memory_state
        assert "procedural_memory_count" in memory_state

    def test_unified_memory_encode_experience(self):
        """测试 UnifiedMemory 编码经验"""
        from laap.agi.core import AGIAgent

        agent = AGIAgent(name="TestAgent", state_dir=None, enable_all=True)

        result = agent.unified_memory.encode_experience(
            content="Learning Python programming",
            emotional_valence=0.5,
            emotional_arousal=0.3,
        )

        assert "episode_id" in result
        assert "encoded_concepts" in result
        assert result["encoded_concepts"] > 0

    def test_unified_memory_query(self):
        """测试 UnifiedMemory 查询功能"""
        from laap.agi.core import AGIAgent

        agent = AGIAgent(name="TestAgent", state_dir=None, enable_all=True)

        agent.unified_memory.encode_experience(
            content="Machine learning with Python",
            emotional_valence=0.4,
            emotional_arousal=0.2,
        )

        results = agent.unified_memory.query("python")
        assert isinstance(results, list)

    def test_consciousness_harness_emotional_state(self):
        """测试 ConsciousnessHarness 情感状态变化"""
        from laap.agi.core import AGIAgent

        agent = AGIAgent(name="TestAgent", state_dir=None, enable_all=True)

        result = agent.process_interaction(
            user_message="Great job! You're amazing!",
            domain="chat",
        )

        conscious_data = result["consciousness_harness"]
        mood = conscious_data["mood"]
        assert mood in ["joyful", "content", "relaxed", "neutral"]

    def test_consciousness_harness_negative_emotion(self):
        """测试 ConsciousnessHarness 处理负面情绪"""
        from laap.agi.core import AGIAgent

        agent = AGIAgent(name="TestAgent", state_dir=None, enable_all=True)

        result = agent.process_interaction(
            user_message="This is terrible! You failed!",
            domain="chat",
        )

        conscious_data = result["consciousness_harness"]
        mood = conscious_data["mood"]
        assert mood in ["sad", "angry", "depressed", "neutral"]

    def test_health_check_includes_new_modules(self):
        """测试 health_check 包含新模块"""
        from laap.agi.core import AGIAgent

        agent = AGIAgent(name="TestAgent", state_dir=None, enable_all=True)

        health = agent.health_check()

        assert "modules" in health
        assert "consciousness_harness" in health["modules"]
        assert "unified_memory" in health["modules"]
        assert health["modules"]["consciousness_harness"]["status"] == "active"
        assert health["modules"]["unified_memory"]["status"] == "active"

    def test_create_agi_agent_factory_includes_modules(self):
        """测试 create_agi_agent 工厂函数创建的 agent 包含新模块"""
        from laap.agi.core import create_agi_agent

        agent = create_agi_agent(name="FactoryAgent", state_dir=None)

        assert agent.consciousness_harness is not None
        assert agent.unified_memory is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])