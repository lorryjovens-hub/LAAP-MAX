"""
LAAP AGI — Consciousness Harness Demo

演示如何使用 ConsciousnessHarness 集成到 AGIAgent 中，展示：
1. 意识循环（Consciousness Loop）
2. 情感状态（Affective State）
3. 元认知监控（Meta-Cognitive Monitoring）
4. 全局工作空间（Global Workspace）
5. 统一记忆系统（Unified Memory）
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def print_separator(title):
    """打印分隔符"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_agi_agent_integration():
    """演示 AGIAgent 集成 ConsciousnessHarness"""
    print_separator("1. AGIAgent 初始化与意识系统集成")

    from laap.agi.core import AGIAgent, create_agi_agent

    agent = AGIAgent(name="ConsciousDemo", state_dir=None, enable_all=True)

    print(f"✅ AGIAgent 初始化完成")
    print(f"   - 模块数量: {agent._module_count()}")
    print(f"   - ConsciousnessHarness: {'已加载' if agent.consciousness_harness else '未加载'}")
    print(f"   - UnifiedMemory: {'已加载' if agent.unified_memory else '未加载'}")

    return agent


def demo_consciousness_loop(agent):
    """演示意识循环处理"""
    print_separator("2. 意识循环处理（Consciousness Loop）")

    interactions = [
        ("Hello! How are you today?", "chat"),
        ("I'm feeling great! You're amazing!", "chat"),
        ("Can you help me solve a problem?", "help_request"),
        ("That didn't work. Please try again.", "feedback"),
    ]

    for user_msg, domain in interactions:
        print(f"\n📥 用户输入: '{user_msg}'")
        print(f"   领域: {domain}")

        result = agent.process_interaction(
            user_message=user_msg,
            domain=domain,
        )

        if "consciousness_harness" in result:
            ch = result["consciousness_harness"]
            print(f"   🧠 情绪: {ch['mood']}")
            print(f"   🎯 注意力焦点: {ch['attention_focus']}")
            print(f"   💭 效价: {ch['emotional_state'].get('valence', 0):.2f}")
            print(f"   ⚡ 唤醒度: {ch['emotional_state'].get('arousal', 0):.2f}")


def demo_system_prompt_addon(agent):
    """演示系统提示附加内容生成"""
    print_separator("3. 意识系统提示附加内容（System Prompt Addon）")

    result = agent.process_interaction(
        user_message="What should I do next?",
        domain="decision_making",
    )

    if "consciousness_prompt_addon" in result:
        print("\n📝 意识系统提示附加内容:")
        print(result["consciousness_prompt_addon"])


def demo_unified_memory(agent):
    """演示统一记忆系统"""
    print_separator("4. 统一记忆系统（Unified Memory）")

    print("\n📚 编码经验到记忆系统:")
    experiences = [
        ("Learning Python programming basics", 0.5, 0.3),
        ("Understanding machine learning concepts", 0.4, 0.4),
        ("Successfully solving a complex problem", 0.7, 0.5),
        ("Failed to complete a task due to error", -0.3, 0.4),
    ]

    for content, valence, arousal in experiences:
        result = agent.unified_memory.encode_experience(
            content=content,
            emotional_valence=valence,
            emotional_arousal=arousal,
        )
        print(f"   - {content[:40]}... -> episode_id: {result['episode_id'][:8]}")

    print("\n🔍 查询记忆:")
    query_results = agent.unified_memory.query("learning")
    for i, result in enumerate(query_results[:3], 1):
        print(f"   {i}. [{result['type']}] {result['content'][:50]}...")

    print("\n💾 记忆摘要:")
    memory_summary = agent.unified_memory.get_memory_summary()
    for key, value in memory_summary.items():
        print(f"   - {key}: {value}")


def demo_affective_state(agent):
    """演示情感状态变化"""
    print_separator("5. 情感状态动态演化（Affective State）")

    events = [
        ("user_positive_feedback", "用户正面反馈"),
        ("task_success", "任务成功"),
        ("user_negative_feedback", "用户负面反馈"),
        ("task_failure", "任务失败"),
        ("learning_progress", "学习进展"),
    ]

    from laap.agi.affective_engine import AffectiveEventProcessor
    import numpy as np

    for event_type, description in events:
        stimulus = AffectiveEventProcessor.process_event(event_type)
        agent.consciousness_harness.affective.update(external_stimulus=stimulus, dt=0.2)

        mood = agent.consciousness_harness.affective.compute_mood()
        valence, arousal = agent.consciousness_harness.affective.get_valence_arousal()
        dominant_dim, dominant_val = agent.consciousness_harness.affective.get_dominant_emotion()

        print(f"\n   📅 {description}")
        print(f"      - 情绪: {mood}")
        print(f"      - 效价: {valence:.2f}, 唤醒度: {arousal:.2f}")
        print(f"      - 主导情感维度: {dominant_dim.name} ({dominant_val:.2f})")


def demo_meta_cognitive_monitor(agent):
    """演示元认知监控"""
    print_separator("6. 元认知监控（Meta-Cognitive Monitoring）")

    agent.consciousness_harness.meta.start_episode(context="决策分析")
    agent.consciousness_harness.meta.record_reasoning("分析问题背景")
    agent.consciousness_harness.meta.record_reasoning("评估可用选项")
    agent.consciousness_harness.meta.record_reasoning("选择最优方案")
    agent.consciousness_harness.meta.record_action(
        action="执行方案A",
        outcome="success",
        confidence=0.85,
    )
    episode = agent.consciousness_harness.meta.end_episode()

    print(f"\n📋 认知片段:")
    print(f"   - ID: {episode.episode_id}")
    print(f"   - 推理步骤: {len(episode.reasoning_trace)}")
    print(f"   - 置信度: {episode.confidence:.2f}")
    print(f"   - 耗时: {episode.duration_ms:.1f}ms")

    self_report = agent.consciousness_harness.meta.get_self_report()
    print(f"\n📊 自我报告:")
    report = self_report["meta_cognitive_report"]
    print(f"   - 总片段数: {report['total_episodes']}")
    print(f"   - 成功率: {report['success_rate']:.0%}")
    print(f"   - 平均置信度: {report['average_confidence']:.0%}")
    print(f"   - 总反思次数: {report['total_reflections']}")


def demo_global_workspace(agent):
    """演示全局工作空间"""
    print_separator("7. 全局工作空间（Global Workspace）")

    workspace = agent.consciousness_harness.workspace

    print(f"\n🏢 工作空间状态:")
    print(f"   - 容量: {workspace.capacity}")
    print(f"   - 竞争阈值: {workspace.competition_threshold}")
    print(f"   - 当前进程数: {len(workspace.processes)}")
    print(f"   - 当前意识内容: {len(workspace.workspace_contents)}")

    print(f"\n📋 当前注册的进程:")
    for process_id, process in workspace.processes.items():
        print(f"   - {process_id}: {process.process_type.name}")


def demo_get_state(agent):
    """演示获取完整状态"""
    print_separator("8. 获取完整 Agent 状态")

    state = agent.get_state()

    print(f"\n📊 Agent 基本信息:")
    print(f"   - 名称: {state['agent']}")
    print(f"   - 版本: {state['version']}")
    print(f"   - 总交互次数: {state['total_interactions']}")
    print(f"   - 模块数量: {state['modules']}")

    print(f"\n🧠 意识系统状态:")
    if "consciousness_harness" in state:
        ch = state["consciousness_harness"]
        print(f"   - 运行状态: {ch['consciousness_harness']['running']}")
        print(f"   - 人格: {ch['consciousness_harness']['personality']}")
        print(f"   - 工作空间内容数: {ch['global_workspace']['current_contents_count']}")
        print(f"   - 当前情绪: {ch['conscious_context']['mood_label']}")
        print(f"   - 元认知报告: {ch['meta_cognitive']['total_episodes']} 个认知片段")

    print(f"\n💾 统一记忆状态:")
    if "unified_memory" in state:
        um = state["unified_memory"]
        print(f"   - 工作记忆大小: {um['working_memory_size']}")
        print(f"   - 情景记忆数: {um['episodic_memory_count']}")
        print(f"   - 语义记忆数: {um['semantic_memory_count']}")
        print(f"   - 程序记忆数: {um['procedural_memory_count']}")


def demo_health_check(agent):
    """演示健康检查"""
    print_separator("9. 健康检查（Health Check）")

    health = agent.health_check()

    print(f"\n✅ 整体健康状态: {'健康' if health['healthy'] else '存在问题'}")
    print(f"   - Agent: {health['agent']}")
    print(f"   - 版本: {health['version']}")
    print(f"   - 运行时间: {health['uptime_hours']:.1f} 小时")

    print(f"\n🔧 关键模块状态:")
    key_modules = ["consciousness_harness", "unified_memory", "world_model", "self_model", "cognitive_bus"]
    for mod_name in key_modules:
        if mod_name in health["modules"]:
            mod = health["modules"][mod_name]
            status = mod["status"] if isinstance(mod, dict) else mod
            print(f"   - {mod_name}: {status}")


def main():
    """主演示函数"""
    print("🧠 LAAP AGI — Consciousness Harness 演示")
    print("=========================================")

    try:
        agent = demo_agi_agent_integration()
        demo_consciousness_loop(agent)
        demo_system_prompt_addon(agent)
        demo_unified_memory(agent)
        demo_affective_state(agent)
        demo_meta_cognitive_monitor(agent)
        demo_global_workspace(agent)
        demo_get_state(agent)
        demo_health_check(agent)

        print_separator("演示完成！")
        print("\n🎉 Consciousness Harness 已成功集成到 LAAP AGI 系统中！")
        print("\n关键特性:")
        print("  1. 全局工作空间理论 — 竞争-广播机制")
        print("  2. 情感引擎 — 多维情感状态动态演化")
        print("  3. 元认知监控器 — 实时推理分析与偏差检测")
        print("  4. 统一记忆系统 — 工作/情景/语义/程序记忆集成")
        print("  5. 意识上下文构建 — 多维度状态整合")

    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())