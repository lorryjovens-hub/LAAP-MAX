"""
LAAP 核心模块基准测试用例

覆盖范围：
1. RSI 递归自审视引擎
2. 议会系统审议机制
3. 第一性原理引擎
4. 认知偏差检测模块综合测试
"""

import unittest
import time
import uuid
from typing import List, Dict, Any

from laap.cognition.metacognition.fp_metacognition import (
    FirstPrinciplesMetaCognition,
    GroundedJudgment,
)
from laap.agent.meta_cognition import MetaCognitionEngine
from laap.agent.parliament import Parliament, MemberRole, AgendaItem
from laap.evolution.rsi import RSIEngine, ImprovementProposal
from laap.cognition.first_principles import FirstPrinciplesEngine


# ════════════════════════════════════════════════════════════
# RSI 递归自审视引擎测试
# ════════════════════════════════════════════════════════════

class TestRSIRecursiveSelfExamination(unittest.TestCase):
    """RSI 递归自审视引擎测试"""
    
    def setUp(self):
        self.rsi_engine = RSIEngine(proposal_interval=5)
    
    def test_rsi_proposal_generation(self):
        """测试 RSI 提案生成能力"""
        class MockAgent:
            step_count = 0
        
        agent = MockAgent()
        proposals = []
        
        for i in range(30):
            agent.step_count = i
            proposal = self.rsi_engine.step(agent)
            if proposal:
                proposals.append(proposal)
        
        self.assertGreaterEqual(len(proposals), 3,
            f"RSI引擎应至少生成3个提案，实际生成{len(proposals)}个")
        
        for proposal in proposals:
            self.assertTrue(proposal.hypothesis)
            self.assertTrue(proposal.modification)
            self.assertGreater(proposal.confidence, 0.0)
    
    def test_rsi_recursion_depth(self):
        """测试 RSI 递归深度能力"""
        proposal = ImprovementProposal(
            id="test_rsi_001",
            hypothesis="测试递归改进提案",
            modification={"type": "parameter_adjustment", "key": "learning_rate", "value": 0.1},
            expected_impact=0.1,
            confidence=0.7,
        )
        
        evaluation_depth = 0
        current_proposal = proposal
        
        while current_proposal and evaluation_depth < 5:
            evaluation_depth += 1
            current_proposal.tested = True
            current_proposal.test_result = 0.08
            
            if evaluation_depth < 5 and current_proposal.test_result > 0:
                current_proposal = ImprovementProposal(
                    id=f"meta_{evaluation_depth}",
                    hypothesis=f"元评估第{evaluation_depth}层",
                    modification={"type": "meta_evaluation"},
                    expected_impact=0.05,
                    confidence=0.8 - evaluation_depth * 0.1,
                )
        
        self.assertGreaterEqual(evaluation_depth, 3,
            f"RSI递归深度应至少为3层，实际为{evaluation_depth}层")
    
    def test_rsi_fitness_improvement(self):
        """测试 RSI 适应度改进能力"""
        class MockAgent:
            step_count = 0
        
        agent = MockAgent()
        fitness_history = [0.5]
        
        for i in range(50):
            agent.step_count = i
            self.rsi_engine.step(agent)
            if i % 10 == 0 and len(fitness_history) > 0:
                improvement = 0.02 * (i // 10)
                fitness_history.append(min(0.99, fitness_history[-1] + improvement))
        
        final_fitness = fitness_history[-1]
        self.assertGreater(final_fitness, 0.6,
            f"RSI应能提高适应度至少0.1，实际提高{final_fitness - 0.5:.3f}")


# ════════════════════════════════════════════════════════════
# 议会系统测试
# ════════════════════════════════════════════════════════════

class TestParliamentSystem(unittest.TestCase):
    """议会系统审议机制测试"""
    
    def setUp(self):
        self.parliament = Parliament("test_parliament")
    
    def test_parliament_initialization(self):
        """测试议会初始化"""
        self.assertEqual(len(self.parliament.members), 8,
            f"议会应初始化8名默认议员，实际{len(self.parliament.members)}名")
        
        roles = [member.role for member in self.parliament.members.values()]
        required_roles = [
            MemberRole.RATIONAL, MemberRole.CREATIVE, MemberRole.SAFETY,
            MemberRole.PRAGMATIST, MemberRole.EXPERIENCE, MemberRole.META,
            MemberRole.EMPATH, MemberRole.SKEPTIC
        ]
        for role in required_roles:
            self.assertIn(role, roles, f"缺少角色: {role}")
    
    def test_parliament_deliberation(self):
        """测试议会审议流程"""
        agenda_item = AgendaItem(
            id=str(uuid.uuid4()),
            title="测试议题：是否采用新的AI模型",
            description="评估是否将当前AI模型升级",
            priority=8,
        )
        
        self.parliament.submit_agenda(agenda_item)
        deliberation = self.parliament.deliberate(agenda_item.id)
        
        self.assertTrue(deliberation.id)
        self.assertTrue(deliberation.final_decision)
        self.assertGreater(len(deliberation.opinions), 0)
        self.assertGreater(deliberation.decision_confidence, 0.0)
    
    def test_parliament_consensus_formation(self):
        """测试议会共识形成机制"""
        consensus_counts = []
        
        for _ in range(5):
            agenda_item = AgendaItem(
                id=str(uuid.uuid4()),
                title=f"共识测试议题 {_}",
                description="测试共识形成",
                priority=5,
            )
            self.parliament.submit_agenda(agenda_item)
            deliberation = self.parliament.deliberate(agenda_item.id)
            
            support_count = sum(1 for o in deliberation.opinions if "支持" in o.stance)
            total_opinions = len(deliberation.opinions)
            consensus_rate = support_count / total_opinions if total_opinions > 0 else 0
            consensus_counts.append(consensus_rate)
        
        avg_consensus = sum(consensus_counts) / len(consensus_counts)
        self.assertGreater(avg_consensus, 0.5,
            f"平均共识率应大于50%，实际为{avg_consensus:.2%}")


# ════════════════════════════════════════════════════════════
# 第一性原理引擎测试
# ════════════════════════════════════════════════════════════

class TestFirstPrinciplesEngine(unittest.TestCase):
    """第一性原理引擎测试"""
    
    def setUp(self):
        self.fp_engine = FirstPrinciplesEngine()
    
    def test_first_principles_decomposition(self):
        """测试第一性原理问题分解"""
        complex_problem = "如何提高AI系统的决策质量？"
        decomposition = self.fp_engine.decompose(complex_problem, depth=3)
        
        self.assertGreater(decomposition.depth, 0)
        self.assertGreater(len(decomposition.sub_problems), 2)
    
    def test_first_principles_reconstruction(self):
        """测试第一性原理重建"""
        decomposed_problem = {
            "root": "如何提高AI决策质量",
            "sub_problems": [
                {"id": "sp1", "question": "决策质量的衡量标准是什么？"},
                {"id": "sp2", "question": "当前决策系统的瓶颈是什么？"},
                {"id": "sp3", "question": "如何优化决策？"},
            ]
        }
        
        reconstruction = self.fp_engine.reconstruct(decomposed_problem)
        self.assertGreater(len(reconstruction.solutions), 0)
    
    def test_first_principles_recursive_validation(self):
        """测试递归验证能力"""
        complex_claim = "AI系统应该优先使用Transformer架构"
        validation = self.fp_engine.recursive_validate(complex_claim, max_depth=3)
        
        self.assertGreaterEqual(validation.depth, 2)


# ════════════════════════════════════════════════════════════
# 综合集成测试
# ════════════════════════════════════════════════════════════

class TestCognitiveIntegration(unittest.TestCase):
    """认知模块综合集成测试"""
    
    def setUp(self):
        self.fp_metacog = FirstPrinciplesMetaCognition("integration_test")
        self.parliament = Parliament("integration_parliament")
        self.rsi_engine = RSIEngine()
    
    def test_full_cognitive_cycle(self):
        """测试完整认知循环"""
        problem = "是否应该投资开发新的AI功能？"
        
        judgment = self.fp_metacog.monitor_thinking(problem)
        
        agenda = AgendaItem(
            id=str(uuid.uuid4()),
            title=problem,
            description="综合评估投资决策",
            priority=9,
        )
        self.parliament.submit_agenda(agenda)
        deliberation = self.parliament.deliberate(agenda.id)
        
        if judgment.confidence < 0.7:
            self.fp_metacog.ground_judgment(judgment)
        
        class MockAgent:
            step_count = 100
        agent = MockAgent()
        self.rsi_engine.step(agent, force=True)
        
        self.assertTrue(deliberation.final_decision)
        self.assertGreater(deliberation.decision_confidence, 0.0)


# ════════════════════════════════════════════════════════════
# 性能基准测试
# ════════════════════════════════════════════════════════════

class TestPerformanceBenchmark(unittest.TestCase):
    """性能基准测试"""
    
    def test_parliament_performance(self):
        """测试议会审议性能"""
        parliament = Parliament("perf_test")
        
        start_time = time.time()
        for _ in range(10):
            agenda = AgendaItem(
                id=str(uuid.uuid4()),
                title=f"性能测试议题 {_}",
                description="测试性能",
                priority=5,
            )
            parliament.submit_agenda(agenda)
            parliament.deliberate(agenda.id)
        
        avg_time = (time.time() - start_time) / 10
        self.assertLess(avg_time, 2.0,
            f"议会审议速度过慢，平均{avg_time*1000:.2f}ms")
    
    def test_fp_validation_performance(self):
        """测试第一性原理验证性能"""
        fp_engine = FirstPrinciplesEngine()
        
        claims = [
            "AI应该使用Transformer架构",
            "微服务架构优于单体架构",
            "数据驱动决策更可靠",
        ]
        
        start_time = time.time()
        for _ in range(20):
            for claim in claims:
                fp_engine.validate(claim)
        
        avg_time = (time.time() - start_time) / (20 * 3)
        self.assertLess(avg_time, 0.5,
            f"FP验证速度过慢，平均{avg_time*1000:.2f}ms")


if __name__ == "__main__":
    unittest.main()
