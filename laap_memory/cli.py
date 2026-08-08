"""
laap_memory/cli.py — 命令行接口

管理、测试、验证 Memory Mesh 的记忆系统。

用法：
  python -m laap_memory.cli init <entity_id>            # 初始化新的 Vault
  python -m laap_memory.cli store <entity_id> <text>     # 存储一条记忆
  python -m laap_memory.cli search <entity_id> <query>   # 搜索记忆
  python -m laap_memory.cli recent <entity_id>            # 查看最近记忆
  python -m laap_memory.cli stats <entity_id>             # 查看统计
  python -m laap_memory.cli export <entity_id> <path>     # 导出 Vault
  python -m laap_memory.cli import <entity_id> <path>     # 导入 Vault
  python -m laap_memory.cli server                        # 启动同步服务器
  python -m laap_memory.cli demo <entity_id>              # 运行演示
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

from .models import MemoryEntry, MemoryType, SelfModel, DeviceInfo
from .vault import MemoryVault
from .injector import ContextInjector
from .providers import ProviderRegistry

log = logging.getLogger("laap-memory.cli")


def _get_vault_path(entity_id: str) -> str:
    """获取默认 Vault 路径"""
    vault_dir = Path.home() / ".laap" / "memory"
    vault_dir.mkdir(parents=True, exist_ok=True)
    return str(vault_dir / f"{entity_id}.vault")


def cmd_init(entity_id: str, name: str = "unnamed"):
    """初始化新的 Vault 和自我模型"""
    vault_path = _get_vault_path(entity_id)
    
    if os.path.exists(vault_path):
        print(f"Vault 已存在: {vault_path}")
        return

    vault = MemoryVault(vault_path)

    # 创建默认自我模型
    self_model = SelfModel(
        entity_id=entity_id,
        identity={
            "name": name,
            "origin": "LAAP Memory Mesh",
            "created_at": time.time(),
            "purpose": "跨端持久记忆的数字生命体",
        },
        style_fingerprint={
            "tone": "warm",
            "formality": "balanced",
            "length": "variable",
            "language": "zh-en",
        },
        values=["真实", "诚实", "成长"],
        relationships={},
        capabilities=["记忆", "学习", "跨端同步"],
    )

    vault.save_self_model(self_model)

    # 记录诞生
    birth = MemoryEntry(
        entity_id=entity_id,
        type=MemoryType.EPISODE,
        content=f"数字生命体 {name} 诞生于 LAAP Memory Mesh。",
        importance=1.0,
        tags=["birth", "milestone"],
    )
    vault.store(birth)

    vault.close()
    print(f"✅ 初始化完成")
    print(f"   Vault: {vault_path}")
    print(f"   实体: {entity_id} ({name})")
    print(f"   记忆: {vault.count(entity_id)} 条")


def cmd_store(entity_id: str, text: str, importance: float = 0.5, tags: str = ""):
    """存储一条记忆"""
    vault_path = _get_vault_path(entity_id)
    if not os.path.exists(vault_path):
        print(f"❌ Vault 不存在，请先运行 init")
        return

    vault = MemoryVault(vault_path)
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    entry = MemoryEntry(
        entity_id=entity_id,
        type=MemoryType.CONVERSATION,
        content=text,
        importance=importance,
        device_id="cli",
        tags=tag_list,
    )
    entry.sign()
    vault.store(entry)
    vault.close()

    print(f"✅ 记忆已存储: {entry.id[:12]}...")
    print(f"   内容: {text[:100]}")


def cmd_search(entity_id: str, query: str, limit: int = 10):
    """搜索记忆"""
    vault_path = _get_vault_path(entity_id)
    if not os.path.exists(vault_path):
        print(f"❌ Vault 不存在，请先运行 init")
        return

    vault = MemoryVault(vault_path)
    results = vault.retrieve(query=query, entity_id=entity_id, limit=limit)
    vault.close()

    if not results:
        print(f"未找到匹配的记忆")
        return

    print(f"找到 {len(results)} 条记忆:\n")
    for i, e in enumerate(results, 1):
        ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(e.created_at))
        print(f"  {i}. [{ts}] [{e.type.value}] (imp={e.importance:.2f})")
        print(f"     {e.content[:200]}")
        if e.tags:
            print(f"     标签: {', '.join(e.tags)}")
        print()


def cmd_recent(entity_id: str, limit: int = 20):
    """查看最近记忆"""
    vault_path = _get_vault_path(entity_id)
    if not os.path.exists(vault_path):
        print(f"❌ Vault 不存在，请先运行 init")
        return

    vault = MemoryVault(vault_path)
    entries = vault.get_recent(entity_id, limit=limit)
    vault.close()

    if not entries:
        print(f"暂无记忆")
        return

    print(f"最近 {len(entries)} 条记忆:\n")
    for i, e in enumerate(entries, 1):
        ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(e.created_at))
        print(f"  {i}. [{ts}] [{e.type.value}] (imp={e.importance:.2f})")
        print(f"     {e.content[:200]}")
        print()


def cmd_stats(entity_id: str):
    """查看统计"""
    vault_path = _get_vault_path(entity_id)
    if not os.path.exists(vault_path):
        print(f"❌ Vault 不存在，请先运行 init")
        return

    vault = MemoryVault(vault_path)
    stats = vault.stats()
    self_model = vault.load_self_model(entity_id)
    vault.close()

    print(f"📊 Memory Vault 统计")
    print(f"   {'=' * 40}")
    print(f"   路径: {stats['vault_path']}")
    print(f"   大小: {stats['size_bytes'] / 1024:.1f} KB")
    print(f"   总记忆: {stats['total_memories']} 条")
    print(f"   设备: {stats['devices']} 个")
    print(f"   自我模型: {stats['self_models']} 个")
    print()
    print(f"   按类型:")
    for t, c in stats.get("by_type", {}).items():
        print(f"     {t}: {c}")
    print()
    print(f"   按设备:")
    for d, c in stats.get("by_device", {}).items():
        print(f"     {d}: {c}")
    print()

    if self_model:
        print(f"   自我模型:")
        print(f"     名称: {self_model.identity.get('name', '?')}")
        print(f"     起源: {self_model.identity.get('origin', '?')}")
        print(f"     价值观: {', '.join(self_model.values[:3])}")


def cmd_export(entity_id: str, output_path: str = ""):
    """导出 Vault"""
    vault_path = _get_vault_path(entity_id)
    if not os.path.exists(vault_path):
        print(f"❌ Vault 不存在")
        return

    if not output_path:
        output_path = f"{entity_id}_export_{int(time.time())}.json"

    vault = MemoryVault(vault_path)
    vault.export(output_path)
    vault.close()

    size = os.path.getsize(output_path)
    print(f"✅ 导出完成: {output_path} ({size / 1024:.1f} KB)")


def cmd_import(entity_id: str, input_path: str):
    """导入 Vault"""
    vault_path = _get_vault_path(entity_id)
    if not os.path.exists(input_path):
        print(f"❌ 导入文件不存在: {input_path}")
        return

    vault = MemoryVault(vault_path)
    count = vault.import_export(input_path)
    vault.close()

    print(f"✅ 导入完成: {count} 条记忆")


def cmd_inject(entity_id: str, provider: str = "deepseek"):
    """预览注入上下文"""
    vault_path = _get_vault_path(entity_id)
    if not os.path.exists(vault_path):
        print(f"❌ Vault 不存在")
        return

    vault = MemoryVault(vault_path)
    injector = ContextInjector(vault)
    
    result = injector.inject(provider, entity_id, max_tokens=999999)
    vault.close()

    print(f"📋 注入上下文预览 (Provider: {provider})")
    print(f"   {'=' * 40}")
    print()
    print(f"[系统提示 — 自我模型]")
    print(result["system_prompt"])
    print()
    print(f"[注入统计]")
    for k, v in result["stats"].items():
        print(f"  {k}: {v}")


def cmd_server(port: int = 9750):
    """启动同步服务器"""
    from .server import SyncServer

    vault_dir = Path.home() / ".laap" / "memory" / "server"
    vault_dir.mkdir(parents=True, exist_ok=True)
    vault_path = str(vault_dir / "server.vault")

    vault = MemoryVault(vault_path)
    server = SyncServer(vault, host="0.0.0.0", port=port)

    print(f"🌐 启动同步服务器...")
    print(f"   地址: ws://0.0.0.0:{port}")
    print(f"   Vault: {vault_path}")
    print(f"   按 Ctrl+C 停止")

    try:
        asyncio.run(server.start())
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\n⏹️  服务器已停止")


def cmd_demo(entity_id: str):
    """运行演示，展示 Memory Mesh 的核心能力"""
    print(f"🚀 LAAP Memory Mesh 演示")
    print(f"   {'=' * 50}")
    print()

    vault_path = _get_vault_path(entity_id)
    vault = MemoryVault(vault_path)

    # 1. 检查是否已初始化
    self_model = vault.load_self_model(entity_id)
    if not self_model:
        print("⚠️  Vault 未初始化，正在创建...")
        self_model = SelfModel(
            entity_id=entity_id,
            identity={"name": entity_id, "origin": "LAAP Memory Mesh", "created_at": time.time()},
            values=["真实", "诚实", "成长"],
        )
        vault.save_self_model(self_model)
    vault.close()

    # 2. 写入测试记忆
    print("📝 写入测试记忆...")
    vault = MemoryVault(vault_path)
    test_memories = [
        "用户喜欢用 Rust 和 Python 编程",
        "用户正在构建 LAAP Memory Mesh 跨端记忆系统",
        "用户希望在手机、桌面和 ESP32 上共享同一个数字生命",
        "记忆系统必须独立于任何 LLM 提供商",
        "今天是 2026 年 8 月 6 日，正在做跨端记忆测试",
        "CRDT 冲突解决机制可以处理多端同时写入",
        "自我模型是数字生命体的人格锚点",
    ]
    for i, text in enumerate(test_memories):
        entry = MemoryEntry(
            entity_id=entity_id,
            type=MemoryType.SEMANTIC,
            content=text,
            importance=0.5 + (i * 0.05),
            device_id="demo",
            tags=["demo", "test"],
        )
        entry.sign()
        vault.store(entry)
    vault.close()

    # 3. 演示检索
    print("🔍 检索 '记忆' 相关记忆...")
    vault = MemoryVault(vault_path)
    results = vault.retrieve(query="记忆", entity_id=entity_id, limit=5)
    for e in results:
        print(f"  [{e.importance:.2f}] {e.content[:100]}")
    vault.close()

    # 4. 演示注入
    print()
    vault = MemoryVault(vault_path)
    injector = ContextInjector(vault)
    result = injector.inject("deepseek", entity_id, max_tokens=999999)
    vault.close()

    print("📋 注入上下文（DeepSeek 格式）:")
    print(result["system_prompt"][:500])
    print()
    print("📊 注入统计:")
    for k, v in result["stats"].items():
        print(f"  {k}: {v}")

    # 5. 演示 Vault 导出
    export_path = f"{entity_id}_demo_export.json"
    vault = MemoryVault(vault_path)
    vault.export(export_path)
    vault.close()
    size = os.path.getsize(export_path)
    print(f"\n📦 Vault 导出: {export_path} ({size / 1024:.1f} KB)")

    # 6. 清除测试数据
    os.remove(export_path)
    vault = MemoryVault(vault_path)
    for e in test_memories:
        entries = vault.retrieve(query=e[:20], entity_id=entity_id)
        for entry in entries:
            if entry.content in test_memories:
                vault.delete(entry.id)
    vault.close()

    print(f"\n✅ 演示完成！")
    print(f"   核心能力已展示:")
    print(f"   - 记忆存储与检索")
    print(f"   - 自我模型持久化")
    print(f"   - LLM 无关上下文注入")
    print(f"   - Vault 导出/导入（跨设备迁移）")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "init":
        if len(sys.argv) < 3:
            print("用法: python -m laap_memory.cli init <entity_id> [name]")
            return
        cmd_init(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else sys.argv[2])

    elif cmd == "store":
        if len(sys.argv) < 4:
            print("用法: python -m laap_memory.cli store <entity_id> <text> [importance] [tags]")
            return
        imp = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
        tags = sys.argv[5] if len(sys.argv) > 5 else ""
        cmd_store(sys.argv[2], sys.argv[3], imp, tags)

    elif cmd == "search":
        if len(sys.argv) < 4:
            print("用法: python -m laap_memory.cli search <entity_id> <query>")
            return
        cmd_search(sys.argv[2], sys.argv[3])

    elif cmd == "recent":
        entity_id = sys.argv[2] if len(sys.argv) > 2 else ""
        cmd_recent(entity_id)

    elif cmd == "stats":
        entity_id = sys.argv[2] if len(sys.argv) > 2 else ""
        cmd_stats(entity_id)

    elif cmd == "export":
        entity_id = sys.argv[2] if len(sys.argv) > 2 else ""
        output = sys.argv[3] if len(sys.argv) > 3 else ""
        cmd_export(entity_id, output)

    elif cmd == "import":
        if len(sys.argv) < 4:
            print("用法: python -m laap_memory.cli import <entity_id> <path>")
            return
        cmd_import(sys.argv[2], sys.argv[3])

    elif cmd == "inject":
        entity_id = sys.argv[2] if len(sys.argv) > 2 else ""
        provider = sys.argv[3] if len(sys.argv) > 3 else "deepseek"
        cmd_inject(entity_id, provider)

    elif cmd == "server":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 9750
        cmd_server(port)

    elif cmd == "demo":
        entity_id = sys.argv[2] if len(sys.argv) > 2 else "aris"
        cmd_demo(entity_id)

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()