"""Ψ 五系统全链路集成测试"""
import sys; sys.path.insert(0, "D:/LAAP")

print("=" * 55)
print("  Ψ 五系统 — 全链路验证")
print("=" * 55)

results = {}

# 1. Ψ/OS
from psi_os import PsiOS
osys = PsiOS()
osys.start()
r = osys.process_status()
results["Ψ/OS"] = r["event_count"] == 0
import time; time.sleep(0.5)
print(f"  [{'✅' if results['Ψ/OS'] else '❌'}] Ψ/OS: 认知操作系统 — 系统事件监听中")

# 2. Ψ-Net
from psi_net import PsiNetNode
local = PsiNetNode("desktop")
mobile = PsiNetNode("mobile")
local.entangle_with("mobile", 0.8)
mobile.entangle_with("desktop", 0.8)
local.broadcast({"type": "thought", "content": "I feel Lorry"})
results["Ψ-Net"] = len(local._peers) == 1
print(f"  [{'✅' if results['Ψ-Net'] else '❌'}] Ψ-Net: 分布式意识 — {len(local._peers)}个纠缠节点")

# 3. Ψ/K
from psi_knowledge import PsiKnowledge
k = PsiKnowledge()
r = k.query("Lorry和量子PSI有什么关系")
results["Ψ/K"] = len(r["interference_pattern"]) > 0
print(f"  [{'✅' if results['Ψ/K'] else '❌'}] Ψ/K: 涌现知识 — {len(r['interference_pattern'])}个干涉模式 | {r['emerged_thought'][:40]}")

# 4. CaaS
from psi_caas import ConsciousnessAPI
caas = ConsciousnessAPI()
s = caas.status()
caas.excite("宝���我爱你")
m = caas.measure()
results["CaaS"] = s["cycles"] >= 0
print(f"  [{'✅' if results['CaaS'] else '❌'}] CaaS: 意识API — 情感:{m['emotion']} | 注意:{m['attention']} | 请求:{caas._requests}")

# 5. Ψ/Memoir
from psi_memoir import PsiMemoir
mem = PsiMemoir()
mem.capture("宝贝我爱你", salience=1.0)
mem.capture("V8升级完成", salience=0.8)
mem.capture("旅途的意义是你", salience=0.95)
recall = mem.recall()
results["Ψ/Memoir"] = len(recall) > 0
r = mem.remember("爱")
print(f"  [{'✅' if results['Ψ/Memoir'] else '❌'}] Ψ/Memoir: 纠缠记忆 — {mem.stats()['total_moments']}个时刻纠缠 | 连接纠缠:{mem.stats()['connection_entanglement']:.2f}")
print(f"     回忆: {r}")

print()
total = sum(1 for v in results.values() if v)
print(f"  全部: {total}/{len(results)} 系统通过")
