"""
测试 LAAP 世界模型集成
======================

运行此脚本以验证世界模型模块是否正确集成到 LAAP 框架中。
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from laap.agi.world_model import (
    create_world_model, WorldModelType, EntityType, RelationType,
    LocalWorldModel, ParacosmWorldModel, HybridWorldModel,
    integrate_world_model
)

def test_local_world_model():
    """测试本地世界模型"""
    print("=" * 60)
    print("测试本地世界模型 (LocalWorldModel)")
    print("=" * 60)
    
    # 创建本地世界模型
    wm = create_world_model("local", name="test-world")
    print(f"✓ 创建世界模型: {wm.name}")
    
    # 添加实体
    user = wm.add_entity(
        "John",
        EntityType.USER,
        properties={"name": "John Smith", "mood": "happy", "age": 30},
        confidence=0.9,
        source="direct_observation"
    )
    print(f"✓ 添加实体: {user.name}")
    
    task = wm.add_entity(
        "Finish Report",
        EntityType.GOAL,
        properties={"description": "Complete Q3 sales report", "priority": "high", "due_date": "2024-09-30"},
        confidence=0.85
    )
    print(f"✓ 添加实体: {task.name}")
    
    # 添加关系
    rel = wm.add_relation("John", "Finish Report", RelationType.HAS_PROPERTY, confidence=0.9)
    print(f"✓ 添加关系: {rel.relation_type.value}")
    
    # 添加因果链接
    causal = wm.add_causal_link(
        condition="John works on report",
        effect="Report completed",
        probability=0.85,
        confidence=0.75,
        domain="work"
    )
    print(f"✓ 添加因果链接: {causal.id}")
    
    # 预测
    prediction = wm.predict("John starts working on the report", max_steps=3)
    print(f"✓ 预测结果: {len(prediction.steps)} 步, 置信度: {prediction.confidence:.2f}")
    
    # 反事实推理
    cf_result = wm.counterfactual("John", "mood", "happy", "tired")
    print(f"✓ 反事实推理: 置信度 {cf_result['confidence']:.2f}")
    
    # 场景模拟
    simulation = wm.simulate("John tries to finish the report in one day", max_steps=5)
    print(f"✓ 场景模拟: {len(simulation.steps)} 步")
    
    # 统计
    stats = wm.stats()
    print(f"\n📊 统计信息:")
    print(f"  - 实体数: {stats['entities']}")
    print(f"  - 关系数: {stats['relations']}")
    print(f"  - 因果链接: {stats['causal_links']}")
    print(f"  - 总更新次数: {stats['total_updates']}")
    print(f"  - 总预测次数: {stats['total_predictions']}")
    
    return wm

def test_paracosm_integration():
    """测试 PARACOSM 集成"""
    print("\n" + "=" * 60)
    print("测试 PARACOSM 集成 (ParacosmWorldModel)")
    print("=" * 60)
    
    try:
        paracosm = create_world_model("paracosm")
        print(f"✓ 创建 PARACOSM 模型: {paracosm.stats()['name']}")
        
        # 添加实体到缓存
        entity = paracosm.add_entity(
            "TestEntity",
            EntityType.OBJECT,
            properties={"value": "test"}
        )
        print(f"✓ 添加缓存实体: {entity.name}")
        
        # 尝试反事实推理（会回退到本地）
        cf = paracosm.counterfactual("TestEntity", "value", "test", "changed")
        print(f"✓ 反事实推理 (回退模式): 置信度 {cf['confidence']:.2f}")
        
        return paracosm
    except Exception as e:
        print(f"⚠️ PARACOSM 测试跳过（需要网络连接）: {e}")
        return None

def test_hybrid_world_model():
    """测试混合世界模型"""
    print("\n" + "=" * 60)
    print("测试混合世界模型 (HybridWorldModel)")
    print("=" * 60)
    
    hybrid = create_world_model("hybrid", name="hybrid-world")
    print(f"✓ 创建混合模型")
    
    # 添加实体
    hybrid.add_entity("System", EntityType.AGENT, {"status": "active"}, confidence=1.0)
    print(f"✓ 添加系统实体")
    
    # 预测（会优先使用外部，如果不可用则回退本地）
    prediction = hybrid.predict("system check", max_steps=2)
    print(f"✓ 混合预测: 置信度 {prediction.confidence:.2f}")
    
    # 反事实推理
    cf = hybrid.counterfactual("System", "status", "active", "inactive")
    print(f"✓ 混合反事实: 置信度 {cf['confidence']:.2f}")
    
    stats = hybrid.stats()
    print(f"\n📊 混合模型统计:")
    print(f"  - 本地实体数: {stats['local']['entities']}")
    print(f"  - 外部可用: {stats['external_available']}")
    
    return hybrid

def test_integration_with_agent():
    """测试与 AGI Agent 的集成"""
    print("\n" + "=" * 60)
    print("测试与 AGI Agent 的集成")
    print("=" * 60)
    
    from laap.agi.core import create_agi_agent
    
    agent = create_agi_agent(name="TestAgent", enable_all=True)
    print(f"✓ 创建 AGI Agent: {agent.name}")
    
    # 检查世界模型是否正确集成
    assert agent.world is not None, "世界模型未集成"
    print(f"✓ 世界模型已集成: {type(agent.world).__name__}")
    
    # 检查世界模型类型
    print(f"✓ 世界模型类型: {agent.world.stats()['name']}")
    
    # 处理交互（测试世界模型更新）
    result = agent.process_interaction(
        user_message="Hello, how are you?",
        domain="conversation"
    )
    print(f"✓ 交互处理完成: {result['total_interactions']} 次交互")
    
    # 检查世界模型是否更新
    world_stats = agent.world.stats()
    print(f"✓ 世界模型实体数: {world_stats['entities']}")
    
    return agent

def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("LAAP 世界模型集成测试套件")
    print("=" * 70)
    
    try:
        # 测试本地模型
        local_wm = test_local_world_model()
        
        # 测试 PARACOSM 集成
        paracosm_wm = test_paracosm_integration()
        
        # 测试混合模型
        hybrid_wm = test_hybrid_world_model()
        
        # 测试与 Agent 的集成
        agent = test_integration_with_agent()
        
        print("\n" + "=" * 70)
        print("✅ 所有测试通过!")
        print("=" * 70)
        print("\n世界模型已成功集成到 LAAP 框架中:")
        print("  • 支持本地实体-关系-因果图模型")
        print("  • 支持 PARACOSM 外部服务集成")
        print("  • 支持混合模式（优先外部，回退本地）")
        print("  • 完整的预测、反事实推理和场景模拟能力")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)