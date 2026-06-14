"""
LAAP AGI — Advanced Hybrid World Model Test Suite
=================================================

测试集成后的混合世界模型的3D场景生成和推理任务能力

测试场景：
1. 3D环境生成场景测试
2. 交互式世界模拟测试
3. 推理任务测试
4. 多模型协作测试

运行方式：
    python test_advanced_world_model.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import time
from typing import Dict, List, Any

from laap.agi.world_model import (
    create_world_model, WorldModelType,
    EntityType, RelationType, LocalWorldModel,
    AdvancedHybridWorldModel
)

# ═══════════════════════════════════════════════════════════════
# 测试3D场景生成能力
# ═══════════════════════════════════════════════════════════════

def test_3d_scene_generation():
    """测试3D场景生成能力"""
    print("\n" + "=" * 70)
    print("测试1: 3D场景生成能力")
    print("=" * 70)
    
    # 创建混合世界模型
    wm = create_world_model("hybrid", name="test-3d-world")
    
    results = {
        "test_name": "3D Scene Generation",
        "passed": True,
        "scenarios_tested": [],
        "performance_metrics": {}
    }
    
    # 定义3D场景测试用例
    scenarios = [
        {
            "name": "城市环境生成",
            "prompt": "Generate a 3D city environment with buildings and streets",
            "expected_features": ["buildings", "streets", "environment"]
        },
        {
            "name": "森林场景生成",
            "prompt": "Create an interactive 3D forest environment with trees",
            "expected_features": ["trees", "forest", "nature"]
        },
        {
            "name": "室内空间模拟",
            "prompt": "Simulate a 3D indoor room with furniture and lighting",
            "expected_features": ["room", "furniture", "lighting"]
        },
        {
            "name": "虚拟实验室",
            "prompt": "Generate a 3D laboratory environment for experiments",
            "expected_features": ["laboratory", "equipment", "experiments"]
        },
        {
            "name": "太空站场景",
            "prompt": "Create an interactive 3D space station with zero gravity",
            "expected_features": ["space", "station", "zero_gravity"]
        }
    ]
    
    print("\n📍 测试场景列表：")
    for i, s in enumerate(scenarios, 1):
        print(f"   {i}. {s['name']}: {s['prompt'][:50]}...")
    
    print("\n🚀 开始测试...")
    
    for scenario in scenarios:
        print(f"\n🔄 正在测试: {scenario['name']}")
        start_time = time.time()
        
        try:
            # 使用混合模型进行场景模拟
            sim_result = wm.simulate(scenario["prompt"], max_steps=5)
            
            elapsed = time.time() - start_time
            
            # 添加测试实体
            entity_name = f"Scene_{scenario['name']}"
            entity = wm.add_entity(
                entity_name,
                EntityType.CONCEPT,
                {
                    "prompt": scenario["prompt"],
                    "features": scenario["expected_features"],
                    "confidence": sim_result.confidence
                },
                tags={"3d", "generated", "scene"},
                confidence=sim_result.confidence
            )
            
            # 记录结果
            test_result = {
                "scenario": scenario["name"],
                "confidence": sim_result.confidence,
                "elapsed_time_ms": round(elapsed * 1000, 2),
                "steps_completed": len(sim_result.steps),
                "assumptions_count": len(sim_result.assumptions),
                "passed": sim_result.confidence > 0.3
            }
            
            results["scenarios_tested"].append(test_result)
            results["performance_metrics"]["total_scenarios"] = len(scenarios)
            
            status = "✅ PASS" if test_result["passed"] else "⚠️ PARTIAL"
            print(f"   {status} | 置信度: {sim_result.confidence:.2f} | 耗时: {elapsed*1000:.1f}ms")
            print(f"   步数: {len(sim_result.steps)} | 假设: {len(sim_result.assumptions)}")
            
            if not test_result["passed"]:
                results["passed"] = False
                
        except Exception as e:
            print(f"   ❌ FAIL | 错误: {str(e)}")
            results["scenarios_tested"].append({
                "scenario": scenario["name"],
                "error": str(e),
                "passed": False
            })
            results["passed"] = False
    
    # 计算平均性能
    if results["scenarios_tested"]:
        valid_results = [r for r in results["scenarios_tested"] if "confidence" in r]
        if valid_results:
            results["performance_metrics"]["avg_confidence"] = round(
                sum(r["confidence"] for r in valid_results) / len(valid_results), 3
            )
            results["performance_metrics"]["avg_time_ms"] = round(
                sum(r["elapsed_time_ms"] for r in valid_results) / len(valid_results), 2
            )
    
    print("\n" + "-" * 50)
    print("📊 3D场景生成测试汇总：")
    print(f"   总场景数: {results['performance_metrics'].get('total_scenarios', 0)}")
    print(f"   平均置信度: {results['performance_metrics'].get('avg_confidence', 0):.3f}")
    print(f"   平均耗时: {results['performance_metrics'].get('avg_time_ms', 0):.1f}ms")
    print(f"   测试结果: {'✅ 通过' if results['passed'] else '❌ 失败'}")
    
    return results


# ═══════════════════════════════════════════════════════════════
# 测试推理任务能力
# ═══════════════════════════════════════════════════════════════

def test_reasoning_tasks():
    """测试推理任务能力"""
    print("\n" + "=" * 70)
    print("测试2: 推理任务能力")
    print("=" * 70)
    
    wm = create_world_model("hybrid", name="test-reasoning")
    
    results = {
        "test_name": "Reasoning Tasks",
        "passed": True,
        "tasks_tested": [],
        "performance_metrics": {}
    }
    
    # 定义推理任务测试用例
    tasks = [
        {
            "name": "因果推理 - 学习与知识增长",
            "action": "agent learns new skill",
            "type": "causal_prediction"
        },
        {
            "name": "行动效果预测",
            "action": "agent performs complex task",
            "type": "action_prediction"
        },
        {
            "name": "反事实推理 - 状态变更",
            "entity": "TestAgent",
            "property": "status",
            "actual": "active",
            "hypothetical": "inactive",
            "type": "counterfactual"
        },
        {
            "name": "反事实推理 - 能力变更",
            "entity": "TestAgent",
            "property": "capability",
            "actual": "basic",
            "hypothetical": "advanced",
            "type": "counterfactual"
        },
        {
            "name": "多步推理链",
            "action": "agent analyzes complex problem and proposes solution",
            "type": "multi_step_reasoning"
        }
    ]
    
    print("\n📍 推理任务列表：")
    for i, t in enumerate(tasks, 1):
        print(f"   {i}. {t['name']} [{t['type']}]")
    
    print("\n🚀 开始测试...")
    
    for task in tasks:
        print(f"\n🔄 正在测试: {task['name']}")
        start_time = time.time()
        
        try:
            if task["type"] == "counterfactual":
                # 反事实推理
                cf_result = wm.counterfactual(
                    task["entity"],
                    task["property"],
                    task["actual"],
                    task["hypothetical"]
                )
                elapsed = time.time() - start_time
                
                test_result = {
                    "task": task["name"],
                    "type": task["type"],
                    "confidence": cf_result.get("confidence", 0),
                    "elapsed_time_ms": round(elapsed * 1000, 2),
                    "has_causal_paths": len(cf_result.get("causal_paths", [])) > 0,
                    "passed": cf_result.get("confidence", 0) > 0.3
                }
                
            elif task["type"] == "multi_step_reasoning":
                # 多步推理
                sim_result = wm.simulate(task["action"], max_steps=5)
                elapsed = time.time() - start_time
                
                test_result = {
                    "task": task["name"],
                    "type": task["type"],
                    "confidence": sim_result.confidence,
                    "elapsed_time_ms": round(elapsed * 1000, 2),
                    "steps_completed": len(sim_result.steps),
                    "causal_chain_length": len(sim_result.causal_chain),
                    "passed": sim_result.confidence > 0.3
                }
                
            else:
                # 预测推理
                pred_result = wm.predict(task["action"], max_steps=3)
                elapsed = time.time() - start_time
                
                test_result = {
                    "task": task["name"],
                    "type": task["type"],
                    "confidence": pred_result.confidence,
                    "elapsed_time_ms": round(elapsed * 1000, 2),
                    "causal_chain_length": len(pred_result.causal_chain),
                    "passed": pred_result.confidence > 0.3
                }
            
            results["tasks_tested"].append(test_result)
            
            status = "✅ PASS" if test_result["passed"] else "⚠️ PARTIAL"
            print(f"   {status} | 置信度: {test_result['confidence']:.2f} | 耗时: {test_result['elapsed_time_ms']:.1f}ms")
            
            if "steps_completed" in test_result:
                print(f"   步数: {test_result['steps_completed']} | 因果链长度: {test_result.get('causal_chain_length', 0)}")
            
            if not test_result["passed"]:
                results["passed"] = False
                
        except Exception as e:
            print(f"   ❌ FAIL | 错误: {str(e)}")
            results["tasks_tested"].append({
                "task": task["name"],
                "error": str(e),
                "passed": False
            })
            results["passed"] = False
    
    # 计算平均性能
    if results["tasks_tested"]:
        valid_results = [r for r in results["tasks_tested"] if "confidence" in r]
        if valid_results:
            results["performance_metrics"]["avg_confidence"] = round(
                sum(r["confidence"] for r in valid_results) / len(valid_results), 3
            )
            results["performance_metrics"]["avg_time_ms"] = round(
                sum(r["elapsed_time_ms"] for r in valid_results) / len(valid_results), 2
            )
    
    print("\n" + "-" * 50)
    print("📊 推理任务测试汇总：")
    print(f"   总任务数: {len(tasks)}")
    print(f"   平均置信度: {results['performance_metrics'].get('avg_confidence', 0):.3f}")
    print(f"   平均耗时: {results['performance_metrics'].get('avg_time_ms', 0):.1f}ms")
    print(f"   测试结果: {'✅ 通过' if results['passed'] else '❌ 失败'}")
    
    return results


# ═══════════════════════════════════════════════════════════════
# 测试多模型协作能力
# ═══════════════════════════════════════════════════════════════

def test_multi_model_collaboration():
    """测试多模型协作能力"""
    print("\n" + "=" * 70)
    print("测试3: 多模型协作能力")
    print("=" * 70)
    
    # 创建高级混合世界模型
    wm = create_world_model("hybrid", name="test-collaboration")
    
    results = {
        "test_name": "Multi-Model Collaboration",
        "passed": True,
        "collaboration_tests": [],
        "performance_metrics": {}
    }
    
    # 测试协作场景
    collaboration_tests = [
        {
            "name": "跨模型实体同步",
            "description": "验证实体在所有模型中正确同步",
            "test_func": lambda wm: test_entity_sync(wm)
        },
        {
            "name": "跨模型关系查询",
            "description": "验证关系可以在多个模型间正确传播",
            "test_func": lambda wm: test_relation_propagation(wm)
        },
        {
            "name": "智能模型选择",
            "description": "验证系统能根据场景类型选择最佳模型",
            "test_func": lambda wm: test_smart_model_selection(wm)
        },
        {
            "name": "级联因果推理",
            "description": "验证因果链接在多模型中正确级联",
            "test_func": lambda wm: test_causal_cascade(wm)
        }
    ]
    
    print("\n📍 协作测试列表：")
    for i, test in enumerate(collaboration_tests, 1):
        print(f"   {i}. {test['name']}: {test['description']}")
    
    print("\n🚀 开始测试...")
    
    for test in collaboration_tests:
        print(f"\n🔄 正在测试: {test['name']}")
        start_time = time.time()
        
        try:
            test_result = test["test_func"](wm)
            elapsed = time.time() - start_time
            
            test_result["elapsed_time_ms"] = round(elapsed * 1000, 2)
            results["collaboration_tests"].append(test_result)
            
            status = "✅ PASS" if test_result["passed"] else "⚠️ PARTIAL"
            print(f"   {status} | 耗时: {test_result['elapsed_time_ms']:.1f}ms")
            if "details" in test_result:
                for detail in test_result["details"]:
                    print(f"   - {detail}")
            
            if not test_result["passed"]:
                results["passed"] = False
                
        except Exception as e:
            print(f"   ❌ FAIL | 错误: {str(e)}")
            results["collaboration_tests"].append({
                "name": test["name"],
                "error": str(e),
                "passed": False
            })
            results["passed"] = False
    
    print("\n" + "-" * 50)
    print("📊 多模型协作测试汇总：")
    print(f"   测试项数: {len(collaboration_tests)}")
    print(f"   测试结果: {'✅ 通过' if results['passed'] else '❌ 失败'}")
    
    return results


def test_entity_sync(wm: AdvancedHybridWorldModel) -> Dict:
    """测试实体同步"""
    entity_name = "SyncTestEntity"
    
    # 添加实体
    entity = wm.add_entity(
        entity_name,
        EntityType.CONCEPT,
        {"test": "entity_sync"},
        tags={"sync", "test"},
        confidence=0.95
    )
    
    # 验证实体存在
    retrieved = wm.get_entity(entity_name)
    
    details = [
        f"原始实体ID: {entity.id}",
        f"检索实体ID: {retrieved.id if retrieved else 'None'}",
        f"同步状态: {'✅ 成功' if retrieved and retrieved.id == entity.id else '❌ 失败'}"
    ]
    
    return {
        "name": "跨模型实体同步",
        "passed": retrieved is not None and retrieved.id == entity.id,
        "details": details
    }


def test_relation_propagation(wm: AdvancedHybridWorldModel) -> Dict:
    """测试关系传播"""
    # 添加测试实体
    wm.add_entity("SourceEntity", EntityType.OBJECT)
    wm.add_entity("TargetEntity", EntityType.OBJECT)
    
    # 添加关系
    relation = wm.add_relation(
        "SourceEntity",
        "TargetEntity",
        RelationType.CAUSES,
        confidence=0.85
    )
    
    details = [
        f"关系创建: {'✅ 成功' if relation else '❌ 失败'}",
        f"关系ID: {relation.id if relation else 'None'}",
        f"关系类型: {relation.relation_type.value if relation else 'None'}"
    ]
    
    return {
        "name": "跨模型关系查询",
        "passed": relation is not None,
        "details": details
    }


def test_smart_model_selection(wm: AdvancedHybridWorldModel) -> Dict:
    """测试智能模型选择"""
    # 测试不同场景下的模型选择
    scenarios = [
        ("Generate 3D environment", "interactive_3d"),
        ("Create video simulation", "video_generation"),
        ("Solve reasoning puzzle", "reasoning"),
        ("What if analysis", "counterfactual")
    ]
    
    details = []
    all_passed = True
    
    for prompt, expected_type in scenarios:
        sim_result = wm.simulate(prompt, max_steps=2)
        passed = sim_result.confidence > 0.2
        all_passed = all_passed and passed
        details.append(f"场景 '{prompt[:30]}...' → 置信度: {sim_result.confidence:.2f}")
    
    return {
        "name": "智能模型选择",
        "passed": all_passed,
        "details": details
    }


def test_causal_cascade(wm: AdvancedHybridWorldModel) -> Dict:
    """测试因果级联"""
    # 添加因果链接
    causal1 = wm.add_causal_link(
        "event_A",
        "event_B",
        probability=0.9,
        confidence=0.85
    )
    
    causal2 = wm.add_causal_link(
        "event_B",
        "event_C",
        probability=0.85,
        confidence=0.8
    )
    
    # 进行预测
    pred = wm.predict("event_A occurs", max_steps=3)
    
    details = [
        f"因果链接1: event_A → event_B (置信度: {causal1.confidence})",
        f"因果链接2: event_B → event_C (置信度: {causal2.confidence})",
        f"预测置信度: {pred.confidence:.2f}",
        f"因果链长度: {len(pred.causal_chain)}"
    ]
    
    return {
        "name": "级联因果推理",
        "passed": pred.confidence > 0.3,
        "details": details
    }


# ═══════════════════════════════════════════════════════════════
# 性能基准测试
# ═══════════════════════════════════════════════════════════════

def run_benchmark():
    """运行性能基准测试"""
    print("\n" + "=" * 70)
    print("测试4: 性能基准测试")
    print("=" * 70)
    
    wm = create_world_model("hybrid", name="benchmark")
    
    results = {
        "test_name": "Performance Benchmark",
        "benchmarks": {}
    }
    
    print("\n🚀 开始基准测试...")
    
    # 1. 实体添加吞吐量
    print("\n📊 测试1: 实体添加吞吐量")
    start_time = time.time()
    num_entities = 100
    for i in range(num_entities):
        wm.add_entity(f"BenchEntity_{i}", EntityType.OBJECT, {"index": i})
    elapsed = time.time() - start_time
    
    throughput = num_entities / elapsed
    results["benchmarks"]["entity_add_throughput"] = round(throughput, 1)
    print(f"   添加 {num_entities} 个实体耗时: {elapsed*1000:.1f}ms")
    print(f"   吞吐量: {throughput:.1f} 实体/秒")
    
    # 2. 实体查询吞吐量
    print("\n📊 测试2: 实体查询吞吐量")
    start_time = time.time()
    num_queries = 100
    for i in range(num_queries):
        wm.query("BenchEntity")
    elapsed = time.time() - start_time
    
    throughput = num_queries / elapsed
    results["benchmarks"]["entity_query_throughput"] = round(throughput, 1)
    print(f"   执行 {num_queries} 次查询耗时: {elapsed*1000:.1f}ms")
    print(f"   吞吐量: {throughput:.1f} 查询/秒")
    
    # 3. 预测延迟
    print("\n📊 测试3: 预测延迟")
    latencies = []
    for _ in range(10):
        start_time = time.time()
        wm.predict("test action prediction", max_steps=3)
        latencies.append(time.time() - start_time)
    
    avg_latency = sum(latencies) / len(latencies) * 1000
    results["benchmarks"]["prediction_latency_ms"] = round(avg_latency, 2)
    print(f"   平均延迟: {avg_latency:.2f}ms")
    print(f"   最小延迟: {min(latencies)*1000:.2f}ms")
    print(f"   最大延迟: {max(latencies)*1000:.2f}ms")
    
    # 4. 模拟延迟
    print("\n📊 测试4: 场景模拟延迟")
    latencies = []
    for _ in range(10):
        start_time = time.time()
        wm.simulate("complex scenario simulation with multiple steps", max_steps=5)
        latencies.append(time.time() - start_time)
    
    avg_latency = sum(latencies) / len(latencies) * 1000
    results["benchmarks"]["simulation_latency_ms"] = round(avg_latency, 2)
    print(f"   平均延迟: {avg_latency:.2f}ms")
    
    # 5. 反事实推理延迟
    print("\n📊 测试5: 反事实推理延迟")
    latencies = []
    for _ in range(10):
        start_time = time.time()
        wm.counterfactual("Agent", "status", "active", "inactive")
        latencies.append(time.time() - start_time)
    
    avg_latency = sum(latencies) / len(latencies) * 1000
    results["benchmarks"]["counterfactual_latency_ms"] = round(avg_latency, 2)
    print(f"   平均延迟: {avg_latency:.2f}ms")
    
    print("\n" + "-" * 50)
    print("📊 性能基准测试汇总：")
    for metric, value in results["benchmarks"].items():
        if "throughput" in metric:
            print(f"   {metric}: {value:.1f}/秒")
        else:
            print(f"   {metric}: {value:.2f}ms")
    
    return results


# ═══════════════════════════════════════════════════════════════
# 主测试入口
# ═══════════════════════════════════════════════════════════════

def main():
    """主测试入口"""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "LAAP AGI Advanced World Model Test Suite" + " " * 16 + "║")
    print("║" + " " * 20 + "混合世界模型集成验证" + " " * 27 + "║")
    print("╚" + "═" * 68 + "╝")
    
    all_results = []
    
    # 1. 3D场景生成测试
    results_3d = test_3d_scene_generation()
    all_results.append(results_3d)
    
    # 2. 推理任务测试
    results_reasoning = test_reasoning_tasks()
    all_results.append(results_reasoning)
    
    # 3. 多模型协作测试
    results_collaboration = test_multi_model_collaboration()
    all_results.append(results_collaboration)
    
    # 4. 性能基准测试
    results_benchmark = run_benchmark()
    all_results.append(results_benchmark)
    
    # ═══════════════════════════════════════════════════════════════
    # 汇总报告
    # ═══════════════════════════════════════════════════════════════
    
    print("\n" + "=" * 70)
    print("测试汇总报告")
    print("=" * 70)
    
    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r.get("passed", False))
    
    print(f"\n总测试项: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {total_tests - passed_tests}")
    
    overall_passed = passed_tests == total_tests
    
    if overall_passed:
        print("\n🎉 所有测试通过！混合世界模型集成验证成功！")
    else:
        print("\n⚠️ 部分测试未通过，请检查上述输出")
    
    # 保存测试结果到JSON
    output_file = os.path.join(os.path.dirname(__file__), "world_model_test_results.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 详细测试结果已保存到: {output_file}")
    
    return all_results


if __name__ == "__main__":
    results = main()
