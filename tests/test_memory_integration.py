"""
LAAP AGI — UnifiedMemory Integration Test Suite

测试 UnifiedMemory 与 ConsciousnessHarness 的集成：
- 记忆编码、检索、整合的完整流程
- 梦境生成功能
- 记忆与意识系统的协同工作
"""

import pytest
import asyncio
import time

from laap.agi.unified_memory import UnifiedMemory
from laap.agi.memory_system import MemoryType, MemoryPriority
from laap.agi.consciousness_integrator import ConsciousnessHarness


class TestMemoryIntegration:
    """UnifiedMemory 与 ConsciousnessHarness 集成测试"""

    def setup_method(self):
        """设置测试环境"""
        self.memory = UnifiedMemory()
        self.harness = ConsciousnessHarness()
        self.harness.initialize_personality()

    def test_memory_working_memory_basic(self):
        """测试工作记忆基本功能"""
        for i in range(5):
            self.memory.add_to_working_memory(f"Task {i}", source_type="task")
        
        assert len(self.memory.working_memory) == 5
        
        contents = [item["content"] for item in self.memory.working_memory]
        assert all(f"Task {i}" in contents for i in range(5))

    def test_memory_working_memory_capacity(self):
        """测试工作记忆容量限制"""
        for i in range(10):
            self.memory.add_to_working_memory(f"Item {i}")
        
        assert len(self.memory.working_memory) == 7
        
        contents = [item["content"] for item in self.memory.working_memory]
        assert "Item 0" not in contents
        assert "Item 9" in contents

    def test_memory_encode_experience(self):
        """测试记忆编码经验"""
        result = self.memory.encode_experience(
            "Learning Python programming with great enthusiasm",
            emotional_valence=0.8,
            emotional_arousal=0.6,
            priority=MemoryPriority.IMPORTANT,
            context_triggers=["coding", "learning", "python"],
        )
        
        assert "episode_id" in result
        assert result["encoded_concepts"] > 0
        assert result["triggered_skills"] == 1
        
        assert len(self.memory.episodic_memory.episodes) == 1
        assert len(self.memory.semantic_memory.concepts) >= 1
        assert len(self.memory.working_memory) >= 1

    def test_memory_encode_concept(self):
        """测试记忆编码概念"""
        self.memory.encode_concept(
            "artificial_intelligence",
            "The simulation of human intelligence processes by machines",
            category="technology",
            attributes={"complex": True, "evolving": True},
            related_concepts=["machine_learning", "neural_network"],
        )
        
        assert "artificial_intelligence" in self.memory.semantic_memory.concepts
        
        concept = self.memory.semantic_memory.retrieve_concept("artificial_intelligence")
        assert concept["category"] == "technology"
        assert concept["attributes"]["complex"] == True

    def test_memory_encode_skill(self):
        """测试记忆编码技能"""
        self.memory.encode_skill(
            "skill_data_analysis",
            "Data Analysis",
            ["Collect data", "Clean data", "Analyze data", "Visualize results"],
            context_triggers=["data", "analysis", "statistics"],
            domain="data_science",
            initial_proficiency=0.8,
        )
        
        assert "skill_data_analysis" in self.memory.procedural_memory.skills
        
        skill = self.memory.procedural_memory.skills["skill_data_analysis"]
        assert skill["name"] == "Data Analysis"
        assert skill["domain"] == "data_science"
        assert skill["proficiency"] == 0.8

    def test_memory_query(self):
        """测试记忆查询功能"""
        self.memory.encode_experience("Machine learning with Python", emotional_valence=0.5)
        self.memory.encode_concept("python", "A programming language", category="tool")
        self.memory.encode_skill(
            "skill_python", 
            "Python Programming", 
            ["Learn basics", "Practice"],
            context_triggers=["python", "programming"]
        )
        
        results = self.memory.query("python")
        
        assert len(results) >= 2
        
        types_found = set(r["type"] for r in results)
        assert "episodic" in types_found or "semantic" in types_found

    def test_memory_query_filtered(self):
        """测试过滤查询"""
        self.memory.encode_experience("Meeting with team", emotional_valence=0.3)
        self.memory.encode_concept("meeting", "A gathering for discussion", category="event")
        
        results = self.memory.query("meeting", include_types=[MemoryType.EPISODIC])
        
        assert all(r["type"] == "episodic" for r in results)

    def test_memory_retrieve_context(self):
        """测试上下文检索"""
        self.memory.encode_experience(
            "Successfully solved a difficult coding problem",
            emotional_valence=0.8,
            emotional_arousal=0.7,
        )
        self.memory.encode_concept("problem_solving", "Finding solutions", category="skill")
        self.memory.encode_skill("skill_debugging", "Debugging", ["Identify", "Fix"])
        
        context = self.memory.retrieve_context(
            "I need to solve a coding problem",
            emotional_valence=0.6,
            emotional_arousal=0.5,
        )
        
        assert len(context) >= 1
        
        types_found = set(r["type"] for r in context)
        assert "episodic" in types_found or "semantic" in types_found

    def test_memory_generate_prompt(self):
        """测试记忆提示生成"""
        self.memory.encode_experience("Previous project experience with machine learning")
        self.memory.encode_concept("machine_learning", "A subset of AI", category="technology")
        self.memory.encode_skill("skill_ml", "Machine Learning", ["Train model", "Evaluate"])
        
        prompt = self.memory.generate_memory_prompt("machine learning project")
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        
        assert any(section in prompt for section in [
            "Relevant Experiences",
            "Relevant Concepts",
            "Relevant Skills",
            "Current Context",
        ])

    def test_memory_consolidation(self):
        """测试记忆整合"""
        self.memory.encode_experience("Learning to bake bread", emotional_valence=0.7)
        self.memory.encode_experience("Daily tea ritual", emotional_valence=0.3)
        
        result = self.memory.consolidate()
        
        assert result["consolidation_count"] == 1
        assert result["was_consolidated"] is True
        
        result2 = self.memory.consolidate()
        assert result2["was_consolidated"] is False

    def test_memory_dream_generation(self):
        """测试梦境生成功能"""
        self.memory.encode_experience("Dream test: flying through clouds", emotional_valence=0.8)
        self.memory.encode_experience("Dream test: exploring ancient ruins", emotional_valence=0.6)
        
        self.memory.consolidate()
        
        dreams = self.memory.get_dream_report(recent_count=2)
        
        assert len(dreams) >= 1
        assert "Dream:" in dreams[0]

    def test_memory_get_recent_episodes(self):
        """测试获取近期经验"""
        for i in range(5):
            self.memory.encode_experience(f"Recent experience {i}")
            time.sleep(0.01)
        
        recent = self.memory.get_recent_episodes(hours=1.0)
        
        assert len(recent) == 5
        assert recent[0]["content"] == "Recent experience 4"

    def test_memory_get_related_concepts(self):
        """测试获取相关概念"""
        self.memory.encode_concept("cat", "A small animal", category="animal")
        self.memory.encode_concept("dog", "A medium animal", category="animal")
        self.memory.encode_concept("animal", "Living creature", category="biology")
        
        self.memory.semantic_memory.encode_fact("cat", "is_a", "animal")
        self.memory.semantic_memory.encode_fact("dog", "is_a", "animal")
        
        related = self.memory.get_related_concepts("cat")
        
        assert len(related) >= 1
        
        related_ids = [r["id"] for r in related]
        assert "animal" in related_ids

    def test_memory_get_relevant_skills(self):
        """测试获取相关技能"""
        self.memory.encode_skill(
            "skill_python_dev",
            "Python Development",
            ["Design", "Code", "Test"],
            context_triggers=["python", "coding", "development"],
            domain="software",
        )
        
        skills = self.memory.get_relevant_skills("I need to develop a Python application")
        
        assert len(skills) >= 1
        assert skills[0]["id"] == "Python Development"

    def test_memory_summary(self):
        """测试记忆摘要"""
        self.memory.encode_experience("Test experience")
        self.memory.encode_concept("test_concept", "A test")
        self.memory.encode_skill("test_skill", "Test Skill", ["Step 1"])
        self.memory.consolidate()
        
        summary = self.memory.get_memory_summary()
        
        assert summary["episodic_memory_count"] == 1
        assert summary["semantic_memory_count"] >= 1
        assert summary["procedural_memory_count"] >= 1
        assert summary["consolidation_count"] == 1
        assert "emotional_state" in summary


class TestMemoryConsciousnessIntegration:
    """UnifiedMemory 与 ConsciousnessHarness 协同测试"""

    def setup_method(self):
        """设置测试环境"""
        self.memory = UnifiedMemory()
        self.harness = ConsciousnessHarness()
        self.harness.initialize_personality()

    @pytest.mark.asyncio
    async def test_memory_influences_emotion(self):
        """测试记忆影响情感状态"""
        self.memory.encode_experience(
            "Previous success experience with coding",
            emotional_valence=0.8,
            emotional_arousal=0.6,
        )
        
        for _ in range(3):
            await self.harness.process_input("Let's do some coding!", {})
        
        context = await self.harness.process_input("Remember when we succeeded?", {})
        
        assert context.emotional_state.get("valence", 0) >= -0.2

    @pytest.mark.asyncio
    async def test_emotional_memory_retrieval(self):
        """测试情感记忆检索"""
        self.memory.encode_experience(
            "A very happy moment with friends",
            emotional_valence=0.9,
            emotional_arousal=0.7,
        )
        self.memory.encode_experience(
            "A sad moment of failure",
            emotional_valence=-0.8,
            emotional_arousal=0.5,
        )
        
        await self.harness.process_input("I'm feeling happy today", {})
        
        happy_context = self.memory.retrieve_context(
            "happy memories",
            emotional_valence=0.5,
            emotional_arousal=0.5,
        )
        
        assert len(happy_context) >= 1

    @pytest.mark.asyncio
    async def test_learning_flow(self):
        """测试完整学习流程"""
        experiences = [
            ("Learning basic Python syntax", 0.6, 0.4),
            ("Solving first programming problem", 0.7, 0.5),
            ("Debugging first error", 0.3, 0.6),
            ("Successfully completing project", 0.9, 0.8),
        ]
        
        for content, valence, arousal in experiences:
            self.memory.encode_experience(content, emotional_valence=valence, emotional_arousal=arousal)
        
        self.memory.consolidate()
        
        results = self.memory.query("python learning")
        assert len(results) >= 2
        
        summary = self.memory.get_memory_summary()
        assert summary["episodic_memory_count"] == 4
        assert summary["consolidation_count"] >= 1

    @pytest.mark.asyncio
    async def test_memory_prompt_in_consciousness(self):
        """测试记忆提示在意识系统中的使用"""
        self.memory.encode_experience("Previous task: building a web application")
        self.memory.encode_concept("web_development", "Creating websites", category="skill")
        self.memory.encode_skill("skill_web_dev", "Web Development", ["Design", "Code", "Deploy"])
        
        await self.harness.process_input("What was our previous project?", {})
        
        memory_prompt = self.memory.generate_memory_prompt("previous project")
        
        assert "Relevant Experiences" in memory_prompt
        assert "web application" in memory_prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
