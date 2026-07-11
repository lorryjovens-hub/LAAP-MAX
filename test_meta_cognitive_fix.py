from laap.agi.meta_cognitive import MetaCognitiveMonitor

# 创建元认知监控器
monitor = MetaCognitiveMonitor()

# 测试初始化状态
report = monitor.get_self_report()
print('=== 初始状态测试 ===')
total_episodes = report["meta_cognitive_report"]["total_episodes"]
success_rate = report["meta_cognitive_report"]["success_rate"]
avg_confidence = report["meta_cognitive_report"]["average_confidence"]
print(f"总片段数: {total_episodes}")
print(f"成功率: {success_rate}")
print(f"平均置信度: {avg_confidence}")

# 验证初始状态
assert total_episodes == 0, f"Expected 0 episodes, got {total_episodes}"
assert success_rate == 0.5, f"Expected 0.5 success_rate, got {success_rate}"
assert avg_confidence == 0.5, f"Expected 0.5 average_confidence, got {avg_confidence}"
print("✅ 初始状态验证通过")

# 测试认知片段
print()
print('=== 认知片段测试 ===')
episode_id = monitor.start_episode('test context')
monitor.record_reasoning('Step 1: analyze the problem')
monitor.record_reasoning('Step 2: consider alternatives')
monitor.record_action('solve problem', 'success', confidence=0.85)
episode = monitor.end_episode()

report = monitor.get_self_report()
total_episodes = report["meta_cognitive_report"]["total_episodes"]
success_rate = report["meta_cognitive_report"]["success_rate"]
avg_confidence = report["meta_cognitive_report"]["average_confidence"]
total_reflections = report["meta_cognitive_report"]["total_reflections"]
print(f"总片段数: {total_episodes}")
print(f"成功率: {success_rate}")
print(f"平均置信度: {avg_confidence}")
print(f"总反思次数: {total_reflections}")

# 验证片段后状态
assert total_episodes == 1, f"Expected 1 episode, got {total_episodes}"
assert success_rate == 1.0, f"Expected 1.0 success_rate, got {success_rate}"
assert avg_confidence > 0.5, f"Expected confidence > 0.5, got {avg_confidence}"
print("✅ 认知片段测试通过")

print()
print("=== 元认知监控器初始化修复完成 ===")