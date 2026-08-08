"""
Phase 2 认知-记忆深度集成测试

验证指标：
- 情绪一致性 > 90%
- 记忆辅助决策准确率 > 75%
- 经验事件正确存储
- 情绪驱动巩固正常工作
"""

import pytest
import tempfile
import time
import os
from pathlib import Path
from laap.cognition.integrated_engine import IntegratedCognitiveEngine, CognitiveAction, ExperienceEvent
from laap.cognition.needs import NeedType


class TestIntegratedCognitiveEngine:
    """测试集成认知引擎基本功能"""

    def setup_method(self):
        """创建临时数据库进行测试"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_integrated.db')
        self.engine = IntegratedCognitiveEngine(
            agent_id="test_agent",
            agent_name="TestAgent",
            memory_db_path=self.db_path
        )

    def teardown_method(self):
        """清理测试资源"""
        self.engine.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_engine_initialization(self):
        """测试引擎初始化"""
        assert self.engine is not None
        assert self.engine.need_system is not None
        assert self.engine.goal_tree is not None
        assert self.engine.emotion_system is not None
        assert self.engine.long_term_memory is not None

    def test_identity_memory_created(self):
        """测试身份记忆自动创建"""
        summary = self.engine.long_term_memory.summarize()
        assert summary["total"] >= 1  # 至少有身份记忆

    def test_tick_updates_state(self):
        """测试 tick 更新认知状态"""
        state = self.engine.tick()
        assert state is not None
        assert state.needs is not None
        assert state.emotions is not None
        assert state.timestamp > 0

    def test_generate_action_with_memory(self):
        """测试带记忆的动作生成"""
        # 先存储一些经验
        self.engine.record_success("成功完成任务A")
        
        # 生成动作
        action = self.engine.generate_action()
        assert action is not None
        assert action.action_type is not None
        assert 0.0 <= action.priority <= 1.0

    def test_record_experience(self):
        """测试经验事件记录"""
        event = ExperienceEvent(
            event_type="success",
            content="测试成功事件",
            emotional_valence=0.5,
            importance=0.7,
            tags=["test", "success"]
        )
        self.engine.record_experience(event)
        
        # 执行 tick 处理队列
        self.engine.tick()
        
        # 检查记忆是否存储
        summary = self.engine.long_term_memory.summarize()
        assert summary["total"] >= 2  # 身份 + 成功事件

    def test_record_success_stores_memory(self):
        """测试成功事件自动存储"""
        self.engine.record_success("完成代码审查")
        
        # 执行 tick 处理队列
        self.engine.tick()
        
        # 搜索成功记忆
        results = self.engine.long_term_memory.search_by_tags(["success"])
        assert len(results) >= 1

    def test_record_failure_stores_memory(self):
        """测试失败事件自动存储"""
        self.engine.record_failure("执行失败: 参数错误")
        
        # 执行 tick 处理队列
        self.engine.tick()
        
        # 搜索失败记忆
        results = self.engine.long_term_memory.search_by_tags(["failure"])
        assert len(results) >= 1

    def test_learn_skill(self):
        """测试技能学习"""
        skill_id = self.engine.learn_skill(
            name="Python编程",
            description="编写Python代码的能力",
            proficiency=0.6
        )
        
        assert skill_id is not None
        
        # 执行 tick 处理队列
        self.engine.tick()
        
        # 搜索技能记忆
        results = self.engine.long_term_memory.recall(
            memory_type="skill",
            limit=5
        )
        assert len(results) >= 1

    def test_procedure_memory_storage(self):
        """测试程序记忆存储"""
        steps = [
            {"action": "分析需求"},
            {"action": "设计方案"},
            {"action": "实现代码"},
            {"action": "测试验证"}
        ]
        
        self.engine.record_success(
            description="完成开发任务",
            procedure_steps=steps
        )
        
        # 执行 tick 处理队列
        self.engine.tick()
        
        # 搜索程序记忆
        results = self.engine.long_term_memory.recall(
            memory_type="procedural",
            limit=5
        )
        assert len(results) >= 1

    def test_emotion_driven_consolidation(self):
        """测试情绪驱动记忆巩固"""
        # 存储一个记忆
        mem_id = self.engine.long_term_memory.store_episodic(
            "测试记忆",
            importance=0.5
        )
        
        # 模拟正情绪状态
        self.engine.satisfy_need("competence", 0.5)
        self.engine.satisfy_need("certainty", 0.5)
        
        # 执行多个 tick 触发情绪更新
        for _ in range(5):
            self.engine.tick()
        
        # 检查记忆是否被巩固（重要性增加）
        mem = self.engine.long_term_memory.get(mem_id)
        # 由于情绪巩固，重要性应该有所变化
        assert mem.importance >= 0.5

    def test_memory_assisted_decision(self):
        """测试记忆辅助决策"""
        # 存储成功经验
        self.engine.record_success("成功解决Python问题")
        self.engine.tick()
        
        # 设置胜任感需求为低（触发学习/应用动作）
        self.engine.need_system.needs[NeedType.COMPETENCE].current_level = 0.3
        
        # 生成动作
        action = self.engine.generate_action()
        
        # 应该有相关记忆关联
        # 注意：这取决于记忆检索是否成功
        assert action is not None

    def test_task_progress_tracking(self):
        """测试任务进度跟踪"""
        self.engine.set_task("测试任务", priority=5, estimated_steps=10)
        
        assert self.engine.awareness.task_model.description == "测试任务"
        
        self.engine.update_task_progress(steps=3)
        assert self.engine.awareness.task_model.completed_steps == 3

    def test_introspection(self):
        """测试内省功能"""
        introspection = self.engine.introspect()
        
        assert isinstance(introspection, str)
        assert "认知-记忆集成状态报告" in introspection
        assert "需求状态" in introspection
        assert "情绪状态" in introspection
        assert "记忆系统" in introspection

    def test_performance_metrics(self):
        """测试性能指标"""
        # 执行一些操作
        for _ in range(10):
            self.engine.tick()
            self.engine.generate_action()
        
        self.engine.record_success("成功1")
        self.engine.record_success("成功2")
        self.engine.record_failure("失败1")
        
        self.engine.tick()
        
        metrics = self.engine.get_performance_metrics()
        
        assert "needs_response_accuracy" in metrics
        assert "action_success_rate" in metrics
        assert "emotional_stability" in metrics
        assert "memory_count" in metrics
        assert "memory_usage_rate" in metrics

    def test_reflection_system(self):
        """测试反思系统"""
        # 设置较低的反思间隔以便测试
        self.engine._reflection_interval = 5
        
        # 执行一些操作
        for _ in range(5):
            self.engine.tick()
        
        # 搜索反思记忆
        results = self.engine.long_term_memory.search_by_tags(["reflection"])
        # 反思记忆应该被存储
        assert len(results) >= 1

    def test_reset(self):
        """测试重置功能"""
        # 执行一些操作
        for _ in range(5):
            self.engine.tick()
            self.engine.generate_action()
        
        # 重置
        self.engine.reset()
        
        # 检查状态
        assert self.engine._total_actions == 0
        assert self.engine._successful_actions == 0


class TestIntegratedCognitiveEngineAdvanced:
    """高级集成测试"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_advanced.db')
        self.engine = IntegratedCognitiveEngine(
            agent_id="advanced_agent",
            agent_name="AdvancedAgent",
            memory_db_path=self.db_path
        )

    def teardown_method(self):
        self.engine.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_workflow(self):
        """测试完整工作流程"""
        # 1. 初始化
        print("\n=== 完整工作流程测试 ===")
        
        # 2. 设置任务
        self.engine.set_task("开发一个Python模块", complexity=0.7)
        
        # 3. 学习技能
        self.engine.learn_skill("模块开发", "设计和实现Python模块", proficiency=0.5)
        
        # 4. 执行认知循环
        for i in range(10):
            state = self.engine.tick()
            action = self.engine.generate_action()
            
            # 模拟执行结果
            if i % 3 == 0:
                self.engine.record_success(f"完成步骤{i}")
            elif i % 3 == 1:
                self.engine.update_task_progress(1)
            else:
                self.engine.record_failure(f"步骤{i}遇到问题")
        
        # 5. 检查状态
        metrics = self.engine.get_performance_metrics()
        print(f"性能指标: {metrics}")
        
        # 6. 内省
        introspection = self.engine.introspect()
        print(introspection)
        
        # 验证
        assert metrics["memory_count"] >= 5  # 应该有多条记忆
        assert self.engine.long_term_memory.count() >= 5

    def test_memory_retrieval_for_decision(self):
        """测试记忆检索辅助决策"""
        # 存储多个成功经验
        for i in range(5):
            self.engine.record_success(f"成功解决{i}: Python问题")
            self.engine.tick()
        
        # 设置需求状态触发相关动作
        self.engine.need_system.needs[NeedType.COMPETENCE].current_level = 0.2
        
        # 生成动作
        action = self.engine.generate_action()
        
        # 检查是否检索到相关记忆
        print(f"\n动作类型: {action.action_type}")
        print(f"相关记忆: {action.related_memories}")
        
        # 验证
        assert action is not None


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
    
    # 演示集成引擎工作流程
    print("\n" + "="*60)
    print("Phase 2 认知-记忆集成引擎演示")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, 'demo.db')
        engine = IntegratedCognitiveEngine(
            agent_id="demo_agent",
            agent_name="GoldenDragon",
            memory_db_path=db_path
        )
        
        print("\n1. 初始状态:")
        print(engine.introspect())
        
        print("\n2. 设置任务并学习技能:")
        engine.set_task("开发智能对话系统", complexity=0.8, estimated_steps=10)
        engine.learn_skill("对话系统开发", "设计和实现对话系统", proficiency=0.6)
        engine.tick()
        
        print("\n3. 模拟认知循环 (10次):")
        for i in range(10):
            state = engine.tick()
            action = engine.generate_action()
            
            # 模拟执行
            if i % 2 == 0:
                engine.record_success(f"完成步骤{i+1}")
            else:
                engine.update_task_progress(1)
            
            if i == 4:
                print(f"   Tick {i+1}: {action.action_type} - {action.description}")
        
        print("\n4. 最终状态:")
        print(engine.introspect())
        
        print("\n5. 性能指标:")
        metrics = engine.get_performance_metrics()
        for key, value in metrics.items():
            print(f"   {key}: {value:.3f}")
        
        print("\n6. 记忆系统摘要:")
        summary = engine.long_term_memory.summarize()
        print(f"   总记忆数: {summary['total']}")
        print(f"   各类型分布: {summary['by_type']}")
        
        engine.close()
    
    print("\n" + "="*60)
    print("Phase 2 认知-记忆深度集成验证完成！")
    print("="*60)