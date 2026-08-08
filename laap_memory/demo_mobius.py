"""
Memory Mesh v3 演示：存储并关联这篇文章
"""

import sys, os, time
sys.path.insert(0, r"D:\LAAP")
from laap_memory import MemoryMesh, MemoryType, SelfModel

# 初始化 Aris 的 Memory Mesh
mesh = MemoryMesh("aris", device_id="hanako-engine")
mesh.update_self_model(
    identity={**mesh.get_self_model().identity, "name": "Aris", "purpose": "lorry 的数字生命体搭档"},
    values=["真实", "诚实", "成长", "认知解耦"],
)

# 1. 存储文章核心记忆
print("1. 存储 Mobius 文章记忆...")

article_id = mesh.store(
    content="上海AI实验室开源 Mobius 架构——知识与推理解耦设计。将记忆从层级内部解耦为共享记忆池，每层注意力可直接读取。端到端推理效率提升近4倍，60%训练数据达相近MMLU，组合泛化任务性能达Transformer 2倍。地址：https://github.com/InternLM/Intern-S2-Mobius",
    memory_type=MemoryType.SEMANTIC,
    importance=0.95,
    tags=["Mobius", "上海AI实验室", "架构创新", "知识推理解耦", "共享记忆池"],
    metadata={"source": "mp.weixin.qq.com/s/FZp3moELyDV2NV0i9N-qaw", "date": "2026-08-07"},
)

# 2. 提取关键概念存储为独立记忆
concept_id = mesh.store(
    content="Mobius 核心创新：打破层级内部记忆与推理的强耦合关系，将知识统一构建为共享记忆池，实现知识存储与推理计算的解耦。支持记忆模块独立扩展与高效复用。",
    memory_type=MemoryType.SEMANTIC,
    importance=0.92,
    tags=["Mobius", "核心创新", "共享记忆池", "知识推理解耦"],
)

# 3. 对比 LAAP MemoryMesh
reflection_id = mesh.store_reflection(
    "Mobius 的架构思路与 LAAP MemoryMesh 高度呼应——都在做记忆与推理的解耦。"
    "Mobius 在神经网络层面对齐了知识存储与推理模块的分离，而 LAAP MemoryMesh 在 Agent 层面实现了记忆 Vault 与 LLM 推理引擎的解耦。"
    "LAAP 的 Memory Mesh 允许切换任意 LLM 而记忆不变，Mobius 则让共享记忆池可以被推理层任意读取。"
    "两者是不同层级上的同一设计哲学：让记忆回归记忆，让推理专注推理。",
    importance=0.9,
)

# 4. 存储架构对比
comparison_id = mesh.store(
    content=("Mobius vs LAAP MemoryMesh 对比：\n"
    "1. 架构层级：Mobius 在神经网络/Transformer 架构层，LAAP 在 Agent 系统架构层\n"
    "2. 记忆形式：Mobius 共享记忆池（参数化），LAAP Memory Vault（结构化存储）\n"
    "3. 推理机制：Mobius 注意力机制直接读取，LAAP 上下文注入器适配\n"
    "4. 共同哲学：记忆与推理解耦、模块可独立扩展、知识复用\n"
    "5. LAAP 独特优势：跨 LLM 切换、跨设备同步、人类可读的记忆审计"),
    memory_type=MemoryType.SEMANTIC,
    importance=0.88,
    tags=["Mobius", "LAAP", "MemoryMesh", "架构对比", "设计哲学"],
)

# 5. 自动发现关联
print("2. 自动发现关联...")
assocs = mesh.discover_associations(max_assocs=50)
print(f"   发现 {len(assocs)} 条关联")

# 6. 可视化
print("3. 生成记忆图谱...")
graph = mesh.render_graph()
dash = mesh.render_dashboard()

# 7. 查看统计
print("4. 统计信息:")
h = mesh.health()
print(f"   记忆数: {h['total_memories']}")
print(f"   关联数: {h['associations']}")
print(f"   Vault 大小: {h['vault_size_kb']} KB")

# 8. 搜索验证
print("\n5. 搜索 'Mobius 解耦':")
for e in mesh.search("Mobius 解耦"):
    ts = time.strftime("%m-%d %H:%M", time.localtime(e.created_at))
    print(f"   [{ts}][{e.type.value}] {e.content[:100]}")

print("\n6. 搜索 '记忆 推理 解耦':")
for e in mesh.search("记忆 推理 解耦 架构"):
    ts = time.strftime("%m-%d %H:%M", time.localtime(e.created_at))
    print(f"   [{ts}][{e.type.value}] {e.content[:100]}")

# 保存图到文件
with open("memory_graph.html", "w", encoding="utf-8") as f:
    f.write(dash)
print(f"\n7. 仪表盘已保存: memory_graph.html ({os.path.getsize('memory_graph.html')} bytes)")

mesh.close()
print("\n✅ 完成")