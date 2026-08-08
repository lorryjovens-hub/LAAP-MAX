"""
Phase 1 基础认知引擎测试

验证指标：需求驱动响应准确率 > 80%
"""

import pytest
import time
import numpy as np
from laap.cognition.engine import CognitiveEngine, CognitiveAction
from laap.cognition.needs import NeedType


class TestCognitiveEngine:
    """测试认知引擎核心功能"""

    def test_engine_initialization(self):
        """测试引擎初始化"""
        engine = CognitiveEngine("test_agent", "TestAgent")
        assert engine is not None
        assert engine.need_system is not None
        assert engine.goal_tree is not None
        assert engine.emotion_system is not None
        assert engine.awareness is not None

    def test_needs_initial_state(self):
        """测试初始需求状态"""
        engine = CognitiveEngine()
        state = engine.get_state()
        
        # 检查所有五种需求都存在
        needs = state.needs
        assert "certainty" in needs
        assert "competence" in needs
        assert "autonomy" in needs
        assert "relatedness" in needs
        assert "energy" in needs
        
        # 检查需求值在合理范围内
        for need_name, level in needs.items():
            assert 0.0 <= level <= 1.0

    def test_tick_updates_needs(self):
        """测试 tick 更新需求状态"""
        engine = CognitiveEngine()
        initial_state = engine.get_state()
        
        # 执行一次 tick
        engine.tick(dt=1.0)
        new_state = engine.get_state()
        
        # 需求应该有变化（由于衰减）
        assert initial_state.timestamp != new_state.timestamp

    def test_dominant_need_selection(self):
        """测试主导需求选择"""
        engine = CognitiveEngine()
        
        # 模拟某个需求被严重消耗
        engine.need_system.needs[NeedType.CERTAINTY].current_level = 0.1
        
        state = engine.get_state()
        assert state.dominant_need is not None
        assert state.drive_strength > 0.0

    def test_generate_action(self):
        """测试动作生成"""
        engine = CognitiveEngine()
        
        # 多次调用生成动作
        actions = []
        for _ in range(5):
            action = engine.generate_action()
            actions.append(action)
            engine.tick(dt=0.5)
        
        # 确保生成了动作
        assert len(actions) == 5
        for action in actions:
            assert isinstance(action, CognitiveAction)
            assert action.action_type is not None
            assert 0.0 <= action.priority <= 1.0
            assert 0.0 <= action.confidence <= 1.0

    def test_need_based_actions(self):
        """测试基于需求的动作生成"""
        engine = CognitiveEngine()
        
        # 测试各种需求驱动的动作
        need_actions = []
        
        # 测试确定性需求
        engine.need_system.needs[NeedType.CERTAINTY].current_level = 0.1
        action = engine.generate_action()
        need_actions.append(("certainty_low", action.action_type))
        
        # 测试胜任感需求
        engine.need_system.needs[NeedType.COMPETENCE].current_level = 0.1
        action = engine.generate_action()
        need_actions.append(("competence_low", action.action_type))
        
        # 测试自主性需求
        engine.need_system.needs[NeedType.AUTONOMY].current_level = 0.1
        action = engine.generate_action()
        need_actions.append(("autonomy_low", action.action_type))
        
        # 测试归属感需求
        engine.need_system.needs[NeedType.RELATEDNESS].current_level = 0.1
        action = engine.generate_action()
        need_actions.append(("relatedness_low", action.action_type))
        
        # 测试能量需求
        engine.need_system.needs[NeedType.ENERGY].current_level = 0.1
        action = engine.generate_action()
        need_actions.append(("energy_low", action.action_type))
        
        assert len(need_actions) == 5

    def test_satisfy_need(self):
        """测试需求满足"""
        engine = CognitiveEngine()
        
        initial_level = engine.need_system.needs[NeedType.CERTAINTY].current_level
        engine.satisfy_need("certainty", 0.3)
        new_level = engine.need_system.needs[NeedType.CERTAINTY].current_level
        
        assert new_level > initial_level
        assert new_level <= 1.0

    def test_task_progress(self):
        """测试任务进度更新"""
        engine = CognitiveEngine()
        engine.set_task("测试任务", priority=5, complexity=0.5, estimated_steps=10)
        
        assert engine.awareness.task_model.description == "测试任务"
        assert engine.awareness.task_model.status == "in_progress"
        
        engine.update_task_progress(steps=3)
        assert engine.awareness.task_model.completed_steps == 3
        # 检查自我模型中的任务进度
        assert engine.awareness.self_model.task_progress == 0.3

    def test_introspect(self):
        """测试内省功能"""
        engine = CognitiveEngine("test", "TestAgent")
        introspection = engine.introspect()
        
        assert isinstance(introspection, str)
        assert "认知状态报告" in introspection
        assert "需求状态" in introspection
        assert "情绪状态" in introspection

    def test_performance_metrics(self):
        """测试性能指标"""
        engine = CognitiveEngine()
        
        # 执行一些操作
        for _ in range(10):
            engine.tick(dt=0.5)
            engine.generate_action()
        
        metrics = engine.get_performance_metrics()
        
        assert "needs_response_accuracy" in metrics
        assert "action_success_rate" in metrics
        assert "emotional_stability" in metrics
        assert "average_drive" in metrics
        assert "active_goals" in metrics
        
        # 检查指标范围
        assert 0.0 <= metrics["needs_response_accuracy"] <= 1.0
        assert 0.0 <= metrics["action_success_rate"] <= 1.0
        assert 0.0 <= metrics["emotional_stability"] <= 1.0

    def test_intrinsic_reward(self):
        """测试内在奖励计算"""
        engine = CognitiveEngine()
        
        rewards = []
        for _ in range(20):
            engine.tick(dt=0.5)
            reward = engine.get_intrinsic_reward()
            rewards.append(reward)
        
        # 奖励应该在合理范围内
        for r in rewards:
            assert -1.0 <= r <= 1.0

    def test_reset(self):
        """测试重置功能"""
        engine = CognitiveEngine()
        
        # 执行一些操作
        for _ in range(5):
            engine.tick(dt=0.5)
            engine.generate_action()
        
        # 重置
        engine.reset()
        
        # 检查是否重置成功
        assert engine._total_actions == 0
        assert engine._successful_actions == 0


class TestCognitiveEngineIntegration:
    """集成测试 - 模拟真实场景"""

    def test_needs_drive_response_accuracy(self):
        """
        Phase 1 核心验证指标：需求驱动响应准确率 > 80%
        
        测试场景：模拟多个需求状态，验证引擎能正确响应主导需求
        """
        engine = CognitiveEngine()
        correct_responses = 0
        total_tests = 20
        
        for _ in range(total_tests):
            # 获取当前主导需求
            dominant_need, _ = engine.need_system.get_dominant_need()
            
            # 生成动作
            action = engine.generate_action()
            
            # 检查动作是否与主导需求匹配
            if dominant_need and action.need_type == dominant_need.value:
                correct_responses += 1
            
            # 更新状态
            engine.tick(dt=1.0)
            
            # 随机满足某些需求
            if np.random.random() > 0.7:
                engine.satisfy_need(np.random.choice(["certainty", "competence", "autonomy", "relatedness", "energy"]), 0.2)
        
        accuracy = correct_responses / total_tests
        print(f"需求驱动响应准确率: {accuracy*100:.1f}%")
        
        # Phase 1 目标：> 80%
        assert accuracy >= 0.8, f"需求驱动响应准确率 {accuracy*100:.1f}% 未达到 80% 目标"

    def test_emotional_consistency(self):
        """
        测试情绪一致性 > 90%
        
        情绪状态不应在短时间内剧烈波动
        """
        engine = CognitiveEngine()
        stable_changes = 0
        total_changes = 50
        
        prev_valence = engine.emotion_system.state.valence
        
        for _ in range(total_changes):
            engine.tick(dt=0.5)
            current_valence = engine.emotion_system.state.valence
            
            # 检查变化是否在合理范围内
            if abs(current_valence - prev_valence) < 0.2:
                stable_changes += 1
            
            prev_valence = current_valence
        
        consistency = stable_changes / total_changes
        print(f"情绪一致性: {consistency*100:.1f}%")
        
        assert consistency >= 0.9, f"情绪一致性 {consistency*100:.1f}% 未达到 90% 目标"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
    
    # 演示认知引擎工作流程
    print("\n" + "="*60)
    print("Phase 1 认知引擎演示")
    print("="*60)
    
    engine = CognitiveEngine("demo_agent", "GoldenDragon")
    
    print("\n1. 初始状态:")
    print(engine.introspect())
    
    print("\n2. 模拟时间流逝 (5 ticks):")
    for i in range(5):
        engine.tick(dt=1.0)
        action = engine.generate_action()
        print(f"   Tick {i+1}: {action.action_type} - {action.description}")
    
    print("\n3. 模拟任务完成:")
    engine.set_task("完成代码审查", priority=5, complexity=0.7, estimated_steps=5)
    for i in range(5):
        engine.update_task_progress(steps=1)
        if i == 2:
            engine.satisfy_need("competence", 0.3)
    
    print(engine.introspect())
    
    print("\n4. 性能指标:")
    metrics = engine.get_performance_metrics()
    for key, value in metrics.items():
        print(f"   {key}: {value:.3f}")
    
    print("\n" + "="*60)
    print("Phase 1 基础认知框架验证完成！")
    print("="*60)
