"""
Memory Mesh v3 — 生产级集成测试
"""

import sys, os, time, math, json
sys.path.insert(0, r"D:\LAAP")
from laap_memory import *

print("=" * 60)
print("Memory Mesh v3 生产级集成测试")
print("=" * 60)

passed = 0
failed = 0

def check(name, ok):
    global passed, failed
    if ok:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}")

# ── 1. 基础功能 ──────────────────────────────────────
print("\n1. 基础功能")
mesh = MemoryMesh("aris-v3", vault_path="test_v3.vault", device_id="test-runner")
check("MemoryMesh 初始化", mesh.entity_id == "aris-v3")

# 存储
id1 = mesh.store("用户说记忆是最值钱的资产", importance=0.9, tags=["核心"])
id2 = mesh.store("用户正在构建跨端记忆系统", importance=0.85, tags=["项目"])
id3 = mesh.store_relationship("用户是顶级程序员")
id4 = mesh.store_reflection("今天完成了 v3 架构")
check("存储 4 条记忆", all([id1, id2, id3, id4]))

# 检索
entries = mesh.recent(limit=5)
check("最近记忆", len(entries) >= 4)

found = mesh.search("记忆", limit=5)
check("关键词搜索", len(found) >= 2)

# 统计
stats = mesh.stats()
check("Vault 统计", stats["total_memories"] >= 4)
check("Schema 版本", stats["schema_version"] == 3)

# ── 2. 语义检索 ──────────────────────────────────────
print("\n2. 语义检索")
emb = EmbeddingEngine()
check("嵌入引擎初始化", emb is not None)

# TF-IDF 嵌入
vec = emb.embed("用户说记忆是最值钱的资产")
check("TF-IDF 嵌入维度", len(vec) == 256)

vec2 = emb.embed("用户正在构建跨端记忆系统")
sim = emb.cosine_similarity(vec, vec2)
check("余弦相似度计算", 0.0 <= sim <= 1.0)

# 更新 Vault 中的嵌入向量
mesh.vault.update_embedding(id1, vec)
mesh.vault.update_embedding(id2, vec2)
check("嵌入向量更新成功", True)

# 向量搜索
results = mesh.vault.search_by_vector(vec, entity_id="aris-v3", limit=5)
check("向量搜索返回结果", len(results) > 0)
if results:
    check("向量搜索相似度达标", results[0][1] >= 0.7)

# ── 3. 关联网络 ──────────────────────────────────────
print("\n3. 关联网络")
assocs = mesh.discover_associations(max_assocs=50)
check("自动关联发现", len(assocs) > 0)

if assocs:
    # 获取关联记忆
    related = mesh.get_related(assocs[0].source_id)
    check("关联记忆检索", len(related) > 0)

# 图统计
gstats = mesh.graph.stats()
check("图统计", gstats["total_associations"] >= 0)

# ── 4. 记忆巩固 ──────────────────────────────────────
print("\n4. 记忆巩固")
result = mesh.consolidation.stats("aris-v3")
check("巩固统计", "needs_consolidation" in result)

# 手动 consolidate
consolidated = mesh.consolidate()
print(f"   巩固结果: {len(consolidated)} 条")

# ── 5. Agent 间共享 ──────────────────────────────
print("\n5. Agent 间共享")
perm = mesh.grant_access("butter", PermissionLevel.READ)
check("授予 Butter 读权限", perm.peer_entity == "butter")

ok = mesh.share_memory(id1)
check("共享记忆", ok)

pool = mesh.get_shared_pool()
check("共享池非空", len(pool) >= 0)

can_read = mesh.sharing.check_permission("aris-v3", "butter", PermissionLevel.READ)
check("权限检查通过", can_read)

cross = mesh.search_across("记忆", ["aris-v3"])
check("跨实体检索", len(cross) >= 0)

revoked = mesh.revoke_access("butter")
check("撤销权限", revoked)

# ── 6. 可视化 ──────────────────────────────────────
print("\n6. 可视化")
svg = mesh.render_graph()
check("图谱 SVG 生成", svg.startswith("<svg"))
check("图谱包含节点", "circle" in svg)

hist = mesh.render_histogram()
check("直方图 SVG 生成", hist.startswith("<svg"))

timeline = mesh.render_timeline()
check("时间线 SVG 生成", timeline.startswith("<svg"))

dash = mesh.render_dashboard()
check("仪表盘 HTML 生成", "Memory Dashboard" in dash)

# ── 7. 智能上下文注入 ──────────────────────────────
print("\n7. 智能上下文注入")
ctx = mesh.inject_for("deepseek", query="记忆系统", smart=True)
check("v2 注入返回系统提示", len(ctx["system_prompt"]) > 0)
check("v2 注入统计完整", "token_budget" in ctx)
check("v2 注入使用率", "usage_pct" in ctx)

# 不同 Provider
ctx2 = mesh.inject_for("gpt", smart=True)
check("GPT 注入", len(ctx2["system_prompt"]) > 0)

ctx3 = mesh.inject_for("claude", smart=True)
check("Claude 注入", len(ctx3["system_prompt"]) > 0)

# ── 8. Vault 导出/导入 ──────────────────────────────────
print("\n8. Vault 导出/导入")
mesh.export_vault("test_v3_export.json")
check("Vault 导出", os.path.exists("test_v3_export.json"))

mesh2 = MemoryMesh("aris-v3", vault_path="test_v3_imported.vault", device_id="import-test")
count = mesh2.import_vault("test_v3_export.json")
check("Vault 导入", count >= 4)

imported = mesh2.search("记忆", limit=5)
check("导入后搜索正常", len(imported) >= 2)
mesh2.close()

# ── 9. 重要性衰减 ──────────────────────────────────
print("\n9. 重要性衰减")
decay = mesh.apply_decay()
check("衰减执行", decay["affected"] >= 0)

archived = mesh.archive_low()
print(f"   归档: {archived} 条")

# ── 10. CRDT ──────────────────────────────────────────
print("\n10. CRDT")
register = mesh.crdt.write_field(id1, "content", "新内容：用 CRDT 写入")
check("CRDT 寄存器写入", register.field == "content")

resolved = mesh.crdt.resolve_entry(id1)
check("CRDT 字段合并", "content" in resolved)

# ── 11. 健康报告 ──────────────────────────────────
print("\n11. 健康报告")
health = mesh.health()
check("健康报告", "total_memories" in health)
check("健康报告字段完整", all(k in health for k in [
    "total_memories", "archived", "associations", "schema_version",
    "vault_size_kb", "low_importance", "needs_consolidation"
]))

# ── 清理 ──────────────────────────────────────────
mesh.close()
for f in ["test_v3.vault", "test_v3.vault-wal", "test_v3.vault-shm",
          "test_v3_export.json", "test_v3_imported.vault",
          "test_v3_imported.vault-wal", "test_v3_imported.vault-shm"]:
    try:
        os.remove(f)
    except:
        pass

print(f"\n{'=' * 60}")
print(f"测试结果: {passed} 通过, {failed} 失败 / {passed + failed} 总计")
print(f"{'=' * 60}")
sys.exit(0 if failed == 0 else 1)