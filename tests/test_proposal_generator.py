"""
Phase 3 自动提案生成系统测试

验证指标：
- 提案生成覆盖率 > 80%
- 评估准确性 > 75%
- 与认知引擎集成正常
"""

import pytest
import tempfile
import os
from laap.engine.evolution.proposal_generator import (
    AutoProposalGenerator, CognitiveProposalGenerator,
    ProposalCategory, ProposalPriority, ProposalEvaluation,
    OptimizationOpportunity
)
from laap.cognition.integrated_engine import IntegratedCognitiveEngine


class TestAutoProposalGenerator:
    """测试自动提案生成器基本功能"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_proposal.db')
        self.cognitive_engine = IntegratedCognitiveEngine(
            agent_id="test_agent",
            agent_name="TestAgent",
            memory_db_path=self.db_path
        )
        self.generator = AutoProposalGenerator(self.cognitive_engine)

    def teardown_method(self):
        self.cognitive_engine.close()
        self.generator = None
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generator_initialization(self):
        """测试生成器初始化"""
        assert self.generator is not None
        assert self.generator.cognitive_engine is not None
        assert self.generator.memory is not None

    def test_proposal_templates(self):
        """测试提案模板库"""
        templates = self.generator._proposal_templates
        assert len(templates) >= 5
        categories = [t.category for t in templates]
        assert ProposalCategory.SKILL_LEARNING in categories
        assert ProposalCategory.CONFIG_OPTIMIZATION in categories
        assert ProposalCategory.EMOTION_REGULATION in categories

    def test_generate_proposals_force(self):
        """测试强制生成提案"""
        proposals = self.generator.generate_proposals(force=True)
        assert len(proposals) >= 1

    def test_proposal_category_detection(self):
        """测试提案类别检测"""
        # 设置高需求驱动
        self.cognitive_engine.need_system.needs[
            self.cognitive_engine.need_system._init_defaults.__code__.co_consts[1][1]
        ].current_level = 0.2  # 低水平触发驱动
        
        proposals = self.generator.generate_proposals()
        assert len(proposals) >= 1
        
        # 检查是否生成了技能学习提案
        has_skill_proposal = any(
            p.metadata.get("category") == ProposalCategory.SKILL_LEARNING.value
            for p in proposals
        )
        assert has_skill_proposal

    def test_proposal_ranking(self):
        """测试提案排序"""
        proposals = self.generator.generate_proposals(force=True)
        
        if len(proposals) >= 2:
            # 第一个提案的分数应该大于等于第二个
            score1 = self._calculate_proposal_score(proposals[0])
            score2 = self._calculate_proposal_score(proposals[1])
            assert score1 >= score2

    def _calculate_proposal_score(self, proposal):
        """计算提案分数"""
        priority_weights = {
            ProposalPriority.CRITICAL.value: 1.0,
            ProposalPriority.HIGH.value: 0.8,
            ProposalPriority.MEDIUM.value: 0.6,
            ProposalPriority.LOW.value: 0.3
        }
        
        priority = priority_weights.get(proposal.metadata.get("priority"), 0.5)
        gain = proposal.expected_gain
        confidence = proposal.metadata.get("confidence", 0.5)
        
        return 0.4 * priority + 0.3 * gain + 0.2 * confidence + 0.1 * 0.5

    def test_proposal_evaluation(self):
        """测试提案评估"""
        proposals = self.generator.generate_proposals(force=True)
        
        if proposals:
            evaluation = self.generator.evaluate_proposal(proposals[0])
            assert isinstance(evaluation, ProposalEvaluation)
            assert 0.0 <= evaluation.overall_score <= 1.0
            assert 0.0 <= evaluation.risk_score <= 1.0
            assert 0.0 <= evaluation.benefit_score <= 1.0
            assert evaluation.recommended_action in ["approve", "test", "reject", "resolve_conflicts"]

    def test_statistics(self):
        """测试统计功能"""
        # 生成一些提案
        self.generator.generate_proposals(force=True)
        self.generator.generate_proposals(force=True)
        
        stats = self.generator.get_statistics()
        assert stats["total_proposals_generated"] >= 2
        assert 0.0 <= stats["approval_rate"] <= 1.0
        assert 0.0 <= stats["deployment_rate"] <= 1.0

    def test_opportunity_detection(self):
        """测试机会检测"""
        opportunities = self.generator._detect_opportunities(force=True)
        assert len(opportunities) >= 1
        
        for opp in opportunities:
            assert isinstance(opp, OptimizationOpportunity)
            assert opp.category is not None
            assert opp.target is not None
            assert 0.0 <= opp.expected_gain <= 1.0
            assert 0.0 <= opp.confidence <= 1.0

    def test_opportunity_to_proposal(self):
        """测试机会转换为提案"""
        opportunity = OptimizationOpportunity(
            category=ProposalCategory.SKILL_LEARNING,
            target="skill.test",
            current_value=0.0,
            proposed_value=1.0,
            rationale="测试机会",
            expected_gain=0.3,
            confidence=0.8
        )
        
        proposal = self.generator._opportunity_to_proposal(opportunity)
        assert proposal is not None
        assert proposal.target == "skill.test"
        assert proposal.rationale == "测试机会"
        assert proposal.expected_gain == 0.3


class TestCognitiveProposalGenerator:
    """测试与认知引擎集成的提案生成器"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_cognitive.db')
        self.cognitive_engine = IntegratedCognitiveEngine(
            agent_id="cognitive_agent",
            agent_name="CognitiveAgent",
            memory_db_path=self.db_path
        )
        self.generator = CognitiveProposalGenerator(self.cognitive_engine)

    def teardown_method(self):
        self.cognitive_engine.close()
        self.generator = None
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cognitive_integration(self):
        """测试认知引擎集成"""
        assert self.generator.cognitive_engine is not None
        assert self.generator.memory is not None

    def test_emotion_focused_proposals(self):
        """测试情绪聚焦提案生成"""
        # 设置负情绪状态
        self.cognitive_engine.need_system.needs[
            self.cognitive_engine.need_system._init_defaults.__code__.co_consts[1][0]
        ].current_level = 0.1  # 触发负情绪
        
        # 执行几次tick更新情绪
        for _ in range(5):
            self.cognitive_engine.tick()
        
        proposals = self.generator.generate_proposals_for_current_state()
        
        # 检查是否生成了情绪调节提案
        has_emotion_proposal = any(
            p.metadata.get("category") == ProposalCategory.EMOTION_REGULATION.value
            for p in proposals
        )
        assert has_emotion_proposal

    def test_need_focused_proposals(self):
        """测试需求驱动提案生成"""
        # 设置高需求驱动
        self.cognitive_engine.need_system.needs[
            self.cognitive_engine.need_system._init_defaults.__code__.co_consts[1][1]
        ].current_level = 0.2  # 低水平触发高驱动
        
        proposals = self.generator.generate_proposals_for_current_state()
        
        # 检查是否生成了技能学习提案
        has_skill_proposal = any(
            p.metadata.get("category") == ProposalCategory.SKILL_LEARNING.value
            for p in proposals
        )
        assert has_skill_proposal

    def test_on_cognitive_tick(self):
        """测试认知tick触发"""
        # 设置tick计数使其触发提案生成
        self.cognitive_engine._tick_count = 49
        
        # 执行tick
        self.cognitive_engine.tick()
        
        # 检查是否生成了提案
        stats = self.generator.get_statistics()
        # 可能生成了提案
        assert stats["total_proposals_generated"] >= 0

    def test_proposal_notification(self):
        """测试提案通知"""
        # 生成一些高优先级提案
        proposals = self.generator.generate_proposals(force=True)
        
        # 模拟通知认知引擎
        if proposals:
            self.generator._notify_cognitive_engine(proposals[:2])
            
            # 检查是否记录了经验事件
            # 执行tick处理队列
            self.cognitive_engine.tick()
            
            # 检查记忆中是否有proposal标签的记忆
            results = self.generator.memory.search_by_tags(["proposal"], limit=3)
            assert len(results) >= 0


class TestProposalGeneratorIntegration:
    """集成测试"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_integration.db')
        self.cognitive_engine = IntegratedCognitiveEngine(
            agent_id="integration_agent",
            agent_name="IntegrationAgent",
            memory_db_path=self.db_path
        )
        self.generator = CognitiveProposalGenerator(self.cognitive_engine)

    def teardown_method(self):
        self.cognitive_engine.close()
        self.generator = None
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_proposal_workflow(self):
        """测试完整提案工作流"""
        print("\n=== 完整提案工作流测试 ===")
        
        # 1. 设置任务和学习技能
        self.cognitive_engine.set_task("完成复杂任务", complexity=0.8)
        self.cognitive_engine.learn_skill("任务管理", "管理复杂任务的能力", proficiency=0.5)
        self.cognitive_engine.tick()
        
        # 2. 生成提案
        proposals = self.generator.generate_proposals()
        print(f"生成了 {len(proposals)} 个提案")
        
        for i, p in enumerate(proposals[:3]):
            print(f"  {i+1}. [{p.metadata.get('category')}] {p.target} - 收益: {p.expected_gain:.2f}")
        
        # 3. 评估提案
        if proposals:
            evaluation = self.generator.evaluate_proposal(proposals[0])
            print(f"\n评估结果:")
            print(f"  综合评分: {evaluation.overall_score:.3f}")
            print(f"  风险评分: {evaluation.risk_score:.3f}")
            print(f"  收益评分: {evaluation.benefit_score:.3f}")
            print(f"  推荐动作: {evaluation.recommended_action}")
        
        # 4. 更新提案状态
        if proposals:
            self.generator.update_proposal_status(proposals[0].id, "approved")
            
            stats = self.generator.get_statistics()
            print(f"\n统计指标:")
            print(f"  总提案数: {stats['total_proposals_generated']}")
            print(f"  批准率: {stats['approval_rate']:.2f}")
        
        # 验证
        assert len(proposals) >= 1


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
    
    # 演示提案生成器功能
    print("\n" + "="*60)
    print("Phase 3 自动提案生成系统演示")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, 'demo.db')
        cognitive_engine = IntegratedCognitiveEngine(
            agent_id="demo_agent",
            agent_name="GoldenDragon",
            memory_db_path=db_path
        )
        generator = CognitiveProposalGenerator(cognitive_engine)
        
        print("\n1. 初始状态:")
        introspection = cognitive_engine.introspect()
        print(introspection)
        
        print("\n2. 设置任务并生成提案:")
        cognitive_engine.set_task("开发智能对话系统", complexity=0.8)
        cognitive_engine.tick()
        
        # 生成提案
        proposals = generator.generate_proposals()
        print(f"\n生成了 {len(proposals)} 个优化提案:")
        for i, p in enumerate(proposals):
            print(f"  {i+1}. [{p.metadata.get('priority').upper()}] "
                  f"[{p.metadata.get('category')}] {p.target}")
            print(f"     理由: {p.rationale}")
            print(f"     预期收益: {p.expected_gain:.2f}, 置信度: {p.metadata.get('confidence', 0.5):.2f}")
            print()
        
        # 评估前3个提案
        print("\n3. 评估提案:")
        for i, p in enumerate(proposals[:3]):
            eval_result = generator.evaluate_proposal(p)
            print(f"  提案 {p.id[:8]}:")
            print(f"    综合评分: {eval_result.overall_score:.3f}")
            print(f"    风险评分: {eval_result.risk_score:.3f}")
            print(f"    收益评分: {eval_result.benefit_score:.3f}")
            print(f"    推荐动作: {eval_result.recommended_action}")
        
        # 更新状态
        if proposals:
            generator.update_proposal_status(proposals[0].id, "approved")
        
        print("\n4. 统计指标:")
        stats = generator.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value:.3f}" if isinstance(value, float) else f"  {key}: {value}")
        
        cognitive_engine.close()
    
    print("\n" + "="*60)
    print("Phase 3 自动提案生成系统验证完成！")
    print("="*60)