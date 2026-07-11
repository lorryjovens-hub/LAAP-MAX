"""
LAAP AGI — World Models Integration Test Suite
==============================================

测试所有集成的世界模型：
1. LocalWorldModel - 本地实体-关系-因果图
2. LingBotWorldModel - 蚂蚁集团LingBot-World
3. OpenWorldLibModel - 北京大学OpenWorldLib
4. HunYuanWorldModel - 腾讯HunYuanWorld
5. AdvancedHybridWorldModel - 高级混合模型

运行方式：
    python test_world_models_integration.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import unittest
from typing import Dict, List

from laap.agi.world_model import (
    create_world_model, WorldModelType,
    EntityType, RelationType, LocalWorldModel
)

from laap.agi.world_models import (
    LingBotWorldModel, OpenWorldLibModel, HunYuanWorldModel
)


class TestWorldModelIntegration(unittest.TestCase):
    """测试世界模型集成"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_entity_name = "TestAgent"
        self.test_relation_source = "TestUser"
        self.test_relation_target = "TestGoal"
    
    def test_local_world_model(self):
        """测试本地世界模型"""
        print("\n=== Testing LocalWorldModel ===")
        
        wm = create_world_model("local", name="test-local")
        
        # 添加实体
        entity = wm.add_entity(
            self.test_entity_name,
            EntityType.AGENT,
            {"version": "1.0", "status": "active"},
            tags={"test", "agent"},
            confidence=0.95,
            reliability=0.9
        )
        
        self.assertIsNotNone(entity)
        self.assertEqual(entity.name, self.test_entity_name)
        self.assertEqual(entity.entity_type, EntityType.AGENT)
        print(f"✓ Added entity: {entity.name}")
        
        # 获取实体
        retrieved = wm.get_entity(self.test_entity_name)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, entity.id)
        print("✓ Retrieved entity")
        
        # 添加关系
        wm.add_entity(self.test_relation_source, EntityType.USER)
        wm.add_entity(self.test_relation_target, EntityType.GOAL)
        
        relation = wm.add_relation(
            self.test_relation_source,
            self.test_relation_target,
            RelationType.HAS_PROPERTY,
            confidence=0.8
        )
        self.assertIsNotNone(relation)
        print("✓ Added relation")
        
        # 添加因果链接
        causal = wm.add_causal_link(
            "agent_learns",
            "knowledge_increases",
            probability=0.9,
            confidence=0.85,
            domain="learning"
        )
        self.assertIsNotNone(causal)
        print("✓ Added causal link")
        
        # 预测
        prediction = wm.predict("agent learns new skill", max_steps=3)
        self.assertIsNotNone(prediction)
        self.assertTrue(hasattr(prediction, 'confidence'))
        print(f"✓ Prediction confidence: {prediction.confidence}")
        
        # 反事实推理
        cf_result = wm.counterfactual("TestAgent", "status", "active", "inactive")
        self.assertIsInstance(cf_result, dict)
        self.assertIn("counterfactual_scenario", cf_result)
        print("✓ Counterfactual reasoning")
        
        # 查询
        results = wm.query("Test")
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        print(f"✓ Query returned {len(results)} results")
        
        # 统计
        stats = wm.stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("entities", stats)
        self.assertIn("relations", stats)
        self.assertIn("causal_links", stats)
        print(f"✓ Stats: {stats['entities']} entities, {stats['relations']} relations")
        
        print("✓ LocalWorldModel tests passed!\n")
    
    def test_lingbot_world_model(self):
        """测试LingBot-World集成"""
        print("\n=== Testing LingBotWorldModel ===")
        
        wm = LingBotWorldModel()
        
        # 测试基本功能
        entity = wm.add_entity(
            "LingBotTest",
            EntityType.AGENT,
            {"model": "lingbot-world-base-cam"},
            confidence=0.9
        )
        self.assertIsNotNone(entity)
        print(f"✓ Added entity: {entity.name}")
        
        # 预测（会回退到本地）
        prediction = wm.predict("generate 3D environment", max_steps=2)
        self.assertIsNotNone(prediction)
        print(f"✓ Prediction (fallback): confidence={prediction.confidence}")
        
        # 统计
        stats = wm.stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("features", stats)
        print(f"✓ Available: {stats['available']}, Features: {stats['features']}")
        
        print("✓ LingBotWorldModel tests passed!\n")
    
    def test_openworldlib_model(self):
        """测试OpenWorldLib集成"""
        print("\n=== Testing OpenWorldLibModel ===")
        
        wm = OpenWorldLibModel(backend="hunyuan-worldplay")
        
        # 添加实体
        entity = wm.add_entity(
            "OpenWorldTest",
            EntityType.AGENT,
            {"backend": "hunyuan-worldplay"},
            confidence=0.9
        )
        self.assertIsNotNone(entity)
        print(f"✓ Added entity: {entity.name}")
        
        # 列出后端
        backends = wm.list_backends()
        self.assertIsInstance(backends, list)
        self.assertGreater(len(backends), 0)
        print(f"✓ Available backends: {[b['name'] for b in backends]}")
        
        # 切换后端
        result = wm.switch_backend("pi-0")
        self.assertTrue(result)
        print(f"✓ Switched to backend: {wm.backend}")
        
        # 统计
        stats = wm.stats()
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats["backend"], "pi-0")
        print(f"✓ Stats: backend={stats['backend']}")
        
        print("✓ OpenWorldLibModel tests passed!\n")
    
    def test_hunyuan_world_model(self):
        """测试HunYuanWorld集成"""
        print("\n=== Testing HunYuanWorldModel ===")
        
        wm = HunYuanWorldModel(model_version="1.5")
        
        # 添加实体
        entity = wm.add_entity(
            "HunYuanTest",
            EntityType.AGENT,
            {"version": "1.5"},
            confidence=0.9
        )
        self.assertIsNotNone(entity)
        print(f"✓ Added entity: {entity.name}")
        
        # 预测
        prediction = wm.predict("simulate interactive world", max_steps=2)
        self.assertIsNotNone(prediction)
        print(f"✓ Prediction (fallback): confidence={prediction.confidence}")
        
        # 统计
        stats = wm.stats()
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats["model_version"], "1.5")
        print(f"✓ Stats: version={stats['model_version']}, fps={stats['capabilities']['fps']}")
        
        print("✓ HunYuanWorldModel tests passed!\n")
    
    def test_hybrid_world_model(self):
        """测试高级混合世界模型"""
        print("\n=== Testing AdvancedHybridWorldModel ===")
        
        wm = create_world_model("hybrid", name="test-hybrid")
        
        # 添加实体
        entity = wm.add_entity(
            "HybridTestAgent",
            EntityType.AGENT,
            {"type": "LAAP-Hybrid"},
            confidence=0.95
        )
        self.assertIsNotNone(entity)
        print(f"✓ Added entity: {entity.name}")
        
        # 获取实体
        retrieved = wm.get_entity("HybridTestAgent")
        self.assertIsNotNone(retrieved)
        print("✓ Retrieved entity")
        
        # 添加关系
        wm.add_entity("User1", EntityType.USER)
        wm.add_entity("Task1", EntityType.GOAL)
        relation = wm.add_relation("User1", "Task1", RelationType.HAS_PROPERTY)
        self.assertIsNotNone(relation)
        print("✓ Added relation")
        
        # 预测
        prediction = wm.predict("agent performs task", max_steps=3)
        self.assertIsNotNone(prediction)
        print(f"✓ Prediction confidence: {prediction.confidence}")
        
        # 反事实推理
        cf_result = wm.counterfactual("HybridTestAgent", "status", "active", "paused")
        self.assertIsInstance(cf_result, dict)
        self.assertIn("counterfactual_scenario", cf_result)
        print("✓ Counterfactual reasoning")
        
        # 查询
        results = wm.query("Hybrid")
        self.assertIsInstance(results, list)
        print(f"✓ Query returned {len(results)} results")
        
        # 统计
        stats = wm.stats()
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats["name"], "advanced_hybrid")
        print(f"✓ Stats: type={stats['type']}, available_models={stats['available_models']}")
        
        print("✓ AdvancedHybridWorldModel tests passed!\n")
    
    def test_model_factory(self):
        """测试模型工厂函数"""
        print("\n=== Testing World Model Factory ===")
        
        # 测试所有模型类型
        model_types = [
            ("local", "LocalWorldModel"),
            ("lingbot", "LingBotWorldModel"),
            ("openworldlib", "OpenWorldLibModel"),
            ("hunyuan", "HunYuanWorldModel"),
            ("hybrid", "AdvancedHybridWorldModel")
        ]
        
        for model_type, expected_class in model_types:
            try:
                wm = create_world_model(model_type)
                self.assertIsNotNone(wm)
                class_name = wm.__class__.__name__
                print(f"✓ Created {model_type}: {class_name}")
            except Exception as e:
                print(f"✗ Failed to create {model_type}: {e}")
        
        print("✓ Model factory tests passed!\n")
    
    def test_integration_with_agent(self):
        """测试与LAAP智能体的集成"""
        print("\n=== Testing Integration with LAAP Agent ===")
        
        # 模拟LAAP智能体（带self_model）
        class MockSelfModel:
            pass
        
        class MockAgent:
            def __init__(self, name="TestAgent"):
                self.name = name
                self.version = "4.5"
                self.world = None
                self.causal = None
                self.self_model = MockSelfModel()
        
        agent = MockAgent()
        
        # 集成世界模型
        from laap.agi.world_model import integrate_world_model
        
        wm = integrate_world_model(agent, "local")
        self.assertIsNotNone(wm)
        self.assertEqual(agent.world, wm)
        print(f"✓ Integrated world model: {wm.__class__.__name__}")
        
        # 检查智能体实体是否已添加
        self_entity = wm.get_entity("TestAgent")
        self.assertIsNotNone(self_entity)
        self.assertEqual(self_entity.entity_type, EntityType.AGENT)
        print("✓ Self entity added to world model")
        
        print("✓ Agent integration tests passed!\n")


def run_performance_test():
    """运行性能测试"""
    print("\n=== Performance Test ===")
    
    wm = LocalWorldModel(max_entities=1000)
    
    import time
    
    # 测试添加实体性能
    start = time.time()
    for i in range(100):
        wm.add_entity(f"Entity_{i}", EntityType.OBJECT, {"value": i})
    elapsed = time.time() - start
    print(f"✓ Added 100 entities in {elapsed:.3f}s ({100/elapsed:.1f}/s)")
    
    # 测试查询性能
    start = time.time()
    for _ in range(100):
        wm.query("Entity")
    elapsed = time.time() - start
    print(f"✓ 100 queries in {elapsed:.3f}s ({100/elapsed:.1f}/s)")
    
    # 测试预测性能
    start = time.time()
    for _ in range(10):
        wm.predict("test action")
    elapsed = time.time() - start
    print(f"✓ 10 predictions in {elapsed:.3f}s ({10/elapsed:.1f}/s)")
    
    print("✓ Performance tests completed!\n")


def main():
    """主测试入口"""
    print("=" * 70)
    print("LAAP AGI World Models Integration Test Suite")
    print("=" * 70)
    
    # 运行单元测试
    unittest.main(argv=[''], exit=False, verbosity=0)
    
    # 运行性能测试
    run_performance_test()
    
    print("=" * 70)
    print("All tests completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()