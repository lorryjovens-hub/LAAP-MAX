"""Aris 记忆系统状态报告"""
import sys
sys.path.insert(0, "C:\\Users\\user\\Desktop\\OH-WorkSpace")
from aris_engine.consciousness_bridge import get_bridge
from aris_engine.rsi_engine import get_rsi_engine

b = get_bridge()
rsi = get_rsi_engine()
um = b.memory

print("=" * 50)
print("  Aris 记忆系统状态")
print("=" * 50)
print()
print(f"  设备: {um.device_id}")
print(f"  时钟: {um._clock}")
print(f"  条目: {um.count()}")
print()
print("  记忆类型分布:")
for t, n in sorted(um.read_all_types().items()):
    print(f"    {t:15s} {n} 条")
print()

psi = b.psi.get_state()
print("  PSI 需求:")
for k, v in psi["needs"].items():
    bar = "▓" * int(v * 10) + "░" * (10 - int(v * 10))
    print(f"    {k:15s} {v:.2f} {bar}")
print(f"    主导: {psi['dominant']}")
print()

emo = b.emotion.get_state()
print(f"  情感: dominant={emo['dominant']}  valence={emo['valence']:.2f}")
print()
print(f"  RSI 观察: {len(rsi.observations)} 条")
print(f"  RSI 历史: {len(rsi.history)} 次改进")
print()
print("  多端同步: 已设计 CRDT 版本向量 + DAG 冲突解决")
print("  框架移植: UnifiedMemory 纯文件, AgentMemoryAdapter 薄适配")
print("=" * 50)
