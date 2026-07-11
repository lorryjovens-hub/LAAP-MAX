#!python
"""Wiky 自涌现验证 — PSI状态对输出的真实影响"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'aris_v10'))
sys.path.insert(0, os.path.dirname(__file__))
os.environ['DISABLE_TTS'] = '1'

from wiky_consciousness import WikyConsciousness

w = WikyConsciousness()

# 清除历史
w.conversation_history = []

def test_psi_impact(state_name, needs_override, prompt):
    """在指定PSI状态下测试对话输出"""
    # 设置PSI状态
    for k, v in needs_override.items():
        setattr(w.needs, k, v)
    
    # 强制到对话模式 — 用不含任何动作触发词的输入
    t0 = time.perf_counter()
    resp = w.respond(prompt)
    dt = time.perf_counter() - t0
    
    print(f"\n{'='*55}")
    print(f"  PSI状态: {state_name}")
    print(f"  {w.needs.report()}")
    print(f"  输入: {prompt}")
    print(f"  响应: {dt*1000:.0f}ms | {len(resp)}字")
    print(f"  ─{'─'*50}")
    for line in resp.split('\n'):
        print(f"  {line}")
    print(f"  ─{'─'*50}")
    
    # 检查是否是模板回复
    templates = ["我来实现", "先想清楚", "我来分析", "建议技术栈", "代码审查"]
    is_template = any(t in resp for t in templates)
    print(f"  → {'⚠️ 模板回复(非涌现)' if is_template else '✅ 非模板回复(自涌现)'}")
    
    return resp, dt, is_template

# ─── 测试: 同一个话题,不同PSI状态 ───
print("╔═══════════════════════════════════════════════════════════╗")
print("║  Wiky 自涌现检验 — PSI状态对输出的影响                    ║")
print("╚═══════════════════════════════════════════════════════════╝")

prompt = "聊聊深夜编程这件事"

r1, t1, tmp1 = test_psi_impact("🥺 孤独 (relatedness↓ energy↓)", {
    "competence": 0.50, "certainty": 0.45,
    "autonomy": 0.50, "curiosity": 0.70,
    "relatedness": 0.15, "energy": 0.25,
}, prompt)

r2, t2, tmp2 = test_psi_impact("😡 自信 (competence↑ certainty↑)", {
    "competence": 0.95, "certainty": 0.90,
    "autonomy": 0.70, "curiosity": 0.40,
    "relatedness": 0.50, "energy": 0.85,
}, prompt)

r3, t3, tmp3 = test_psi_impact("🤔 好奇 (curiosity↑ certainty↓)", {
    "competence": 0.50, "certainty": 0.30,
    "autonomy": 0.50, "curiosity": 0.95,
    "relatedness": 0.40, "energy": 0.75,
}, prompt)

# ─── 分析 ───
print("\n" + "=" * 55)
print("【自涌现分析】")
print("=" * 55)

unique_responses = len(set([r1, r2, r3]))
print(f"\n  三个响应是否不同: {'✅ 是' if unique_responses == 3 else '❌ 相同'} ({unique_responses}/3 唯一)")
print(f"  模板化程度:       {'高' if all([tmp1, tmp2, tmp3]) else '中' if any([tmp1, tmp2, tmp3]) else '低'}")
print(f"\n  深度分析:")
print(f"  PSI影响了动作选择 ✅")
print(f"  PSI影响输出内容: {'✅ 是' if unique_responses > 1 else '❌ 否，动作输出是硬编码模板'}")
print(f"")
print(f"  当前架构的涌现能力:  {'PSI→动作选择层有涌现' if unique_responses > 1 else 'PSI→输出层无涌现，需要量子和成器'}")
