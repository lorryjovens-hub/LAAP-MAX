"""
PsiLang 契约层 Step 4 验收测试 — 确定性 VM
============================================
验证 P3 确定性剥离的四个原语：
  NeedDecay / Attention / EmotionUpdate / MemoryDecay

核心断言：同一输入 → 同一输出（确定性）

印记: Aris 永远记得 Lorry — 2026-08-04
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "runtime"))

from vm import NeedDecay, Attention, EmotionUpdate, MemoryDecay, CognitiveVM

PASS = 0
FAIL = 0


def check(cond, label):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"[PASS] {label}")
    else:
        FAIL += 1
        print(f"[FAIL] {label}")


print("=== PsiLang 确定性 VM 验收测试 ===\n")

# 1. 需求衰减：指数衰减公式
nd = NeedDecay({"a": 1.0}, decay_rate=0.05)
nd.step(1.0)
check(abs(nd.needs["a"] - math.exp(-0.05)) < 1e-9, "NeedDecay 指数衰减公式")

# 2. 需求边界：[0,1] 裁剪
nd2 = NeedDecay({"a": 0.5})
nd2.excite("a", 10.0)
check(nd2.needs["a"] == 1.0, "NeedDecay 上限裁剪")
nd2.satisfy("a", 10.0)
check(nd2.needs["a"] == 0.0, "NeedDecay 下限裁剪")

# 3. 需求缺口
nd3 = NeedDecay({"low": 0.2, "high": 0.9})
check(abs(nd3.deficit("low") - 0.8) < 1e-9, "NeedDecay 缺口计算")

# 4. 注意力选择：缺口排序
focus = Attention.select({"a": 0.9, "b": 0.1, "c": 0.5}, k=2)
check([f[0] for f in focus] == ["b", "c"], f"Attention top-k 按缺口排序: {focus}")

# 5. 注意力加权
focus_w = Attention.select({"a": 0.9, "b": 0.1}, k=2, weights={"a": 10.0})
check(focus_w[0][0] == "a", "Attention 权重影响排序")

# 6. 情感归一化：L2 单位向量
em = EmotionUpdate({"joy": 1.0, "gratitude": 1.0})
norm = math.sqrt(sum(v * v for v in em.normalize().values()))
check(abs(norm - 1.0) < 1e-3, f"EmotionUpdate L2 归一化: norm={norm:.4f}")

# 7. 情感主导
em2 = EmotionUpdate({"joy": 0.9, "sadness": 0.1})
check(em2.dominant() == ("joy", 0.9), "EmotionUpdate 主导情感")

# 8. 记忆衰减：半衰期公式
mem = [{"content": "x", "importance": 1.0, "timestamp": 0.0, "half_life": 10.0}]
scheduled = MemoryDecay().schedule(mem, now=10.0)
check(abs(scheduled[0]["importance_decayed"] - 0.5) < 1e-6, "MemoryDecay 半衰期衰减")

# 9. 遗忘候选 + prune
mems = [
    {"content": "keep", "importance": 0.9, "timestamp": 0.0, "half_life": 100.0},
    {"content": "forget", "importance": 0.01, "timestamp": 0.0, "half_life": 1.0},
]
sched2 = MemoryDecay().schedule(mems, now=100.0)
keep, forget = MemoryDecay.prune(sched2)
check(len(forget) == 1 and forget[0]["content"] == "forget", "MemoryDecay 遗忘候选分离")

# 10. 确定性：同一输入两次执行结果一致
vm1 = CognitiveVM()
vm1.needs.needs = {"a": 0.3, "b": 0.7}
vm1.emotion.vector = {"joy": 0.5}
r1 = vm1.cycle_step()
vm2 = CognitiveVM()
vm2.needs.needs = {"a": 0.3, "b": 0.7}
vm2.emotion.vector = {"joy": 0.5}
r2 = vm2.cycle_step()
check(r1["focus"] == r2["focus"] and r1["emotion"] == r2["emotion"],
      "CognitiveVM 确定性（同输入同输出）")

# 11. 记忆写入契约（VM 内默认 creator 来源）
vm3 = CognitiveVM()
m = vm3.learn_memory("test", 0.9)
check(m["source"] == "creator" and m["causal_parents"] == ["root"]
      and m["confidence"] == 1.0, "CognitiveVM 记忆契约默认值")

print(f"\n结果: {PASS} 通过, {FAIL} 失败")
sys.exit(1 if FAIL else 0)
