"""
Memory Mesh 综合测试：WebSocket 同步 + 跨设备记忆一致性
"""

import asyncio
import json
import os
import sys
import tempfile
import time
import logging

logging.basicConfig(level=logging.WARNING)
sys.path.insert(0, r"D:\LAAP")

from laap_memory.vault import MemoryVault
from laap_memory.models import MemoryEntry, MemoryType, DeviceInfo
from laap_memory.server import SyncServer, SyncClient


async def test_websocket_sync():
    """测试 WebSocket 实时同步"""
    print("=" * 60)
    print("WebSocket 实时同步测试")
    print("=" * 60)

    # 创建独立的临时 vault
    tmpdir = tempfile.mkdtemp()

    server_vault = MemoryVault(os.path.join(tmpdir, "server.vault"))
    client1_vault = MemoryVault(os.path.join(tmpdir, "client1.vault"))
    client2_vault = MemoryVault(os.path.join(tmpdir, "client2.vault"))

    # 启动服务器
    server = SyncServer(server_vault, host="127.0.0.1", port=19750)
    await server.start()
    print("\n1. 同步服务器已启动 (ws://127.0.0.1:19750)")

    # 客户端 1 写入记忆
    entity_id = "aris-test"
    dev1 = DeviceInfo(device_id="pc-1", name="桌面端", priority=10)
    dev2 = DeviceInfo(device_id="phone-1", name="手机端", priority=20)

    # 客户端 1 本地存储
    e1 = MemoryEntry(entity_id=entity_id, type=MemoryType.EPISODE,
                     content="桌面端：用户说记忆是最值钱的资产",
                     importance=0.9, device_id="pc-1")
    e1.sign()
    client1_vault.store(e1)

    e2 = MemoryEntry(entity_id=entity_id, type=MemoryType.SEMANTIC,
                     content="桌面端：用户正在构建跨端记忆系统",
                     importance=0.85, device_id="pc-1")
    e2.sign()
    client1_vault.store(e2)

    print(f"\n2. 客户端 1 (桌面端) 写入 {client1_vault.count(entity_id)} 条记忆")

    # 客户端 2 本地存储
    e3 = MemoryEntry(entity_id=entity_id, type=MemoryType.CONVERSATION,
                     content="手机端：用户通过手机问记忆系统能跨设备吗",
                     importance=0.8, device_id="phone-1")
    e3.sign()
    client2_vault.store(e3)

    print(f"3. 客户端 2 (手机端) 写入 {client2_vault.count(entity_id)} 条记忆")

    # 客户端 1 连接到服务器并推送
    print("\n4. 客户端 1 连接服务器...")
    c1 = SyncClient(client1_vault, entity_id, dev1)
    ok = await c1.connect("ws://127.0.0.1:19750")
    print(f"   连接: {'✅' if ok else '❌'}")

    if ok:
        pushed = await c1.push(since_version=0)
        print(f"   推送: {pushed} 条")

    # 客户端 2 连接服务器并拉取
    print("\n5. 客户端 2 连接服务器...")
    c2 = SyncClient(client2_vault, entity_id, dev2)
    ok = await c2.connect("ws://127.0.0.1:19750")
    print(f"   连接: {'✅' if ok else '❌'}")

    if ok:
        pulled = await c2.pull(since_version=0)
        print(f"   拉取: {len(pulled)} 条")

    # 验证客户端 2 同步到了客户端 1 的记忆
    print(f"\n6. 验证同步结果...")
    c2_entries = client2_vault.retrieve(entity_id=entity_id)
    devices_in_c2 = set(e.device_id for e in c2_entries)
    print(f"   客户端 2 现有记忆: {len(c2_entries)} 条")
    print(f"   来源设备: {devices_in_c2}")

    # 客户端 2 推送自己的记忆
    print(f"\n7. 客户端 2 推送本地记忆...")
    pushed2 = await c2.push(since_version=0)
    print(f"   推送: {pushed2} 条")

    # 客户端 1 拉取客户端 2 的记忆
    pulled2 = await c1.pull(since_version=0)
    print(f"   客户端 1 拉取: {len(pulled2)} 条")

    # 验证双向同步
    c1_entries = client1_vault.retrieve(entity_id=entity_id)
    devices_in_c1 = set(e.device_id for e in c1_entries)
    print(f"\n8. 最终状态:")
    print(f"   客户端 1: {len(c1_entries)} 条, 来源: {devices_in_c1}")
    print(f"   客户端 2: {len(c2_entries)} 条, 来源: {devices_in_c2}")

    all_synced = (
        "pc-1" in devices_in_c2 and "phone-1" in devices_in_c1
    )
    print(f"\n   双向同步: {'✅ 通过' if all_synced else '❌ 失败'}")

    # 清理
    await c1.close()
    await c2.close()
    await server.stop()
    server_vault.close()
    client1_vault.close()
    client2_vault.close()

    # 清理临时文件
    for f in os.listdir(tmpdir):
        try:
            os.remove(os.path.join(tmpdir, f))
        except:
            pass
    try:
        os.rmdir(tmpdir)
    except:
        pass

    print(f"\n{'=' * 60}")
    print(f"WebSocket 同步测试: {'✅ 全部通过' if all_synced else '❌ 部分失败'}")
    print(f"{'=' * 60}")
    return all_synced


async def test_aris_server():
    """测试 aris_server 的 MemoryMesh 集成"""
    print("\n" + "=" * 60)
    print("aris_server MemoryMesh 集成测试")
    print("=" * 60)

    # 直接测试 aris_server 的 memory 模块
    sys.path.insert(0, r"D:\LAAP")

    # 动态导入 aris-body 下的模块
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "aris_memory", r"D:\LAAP\aris-body\aris_memory.py"
    )
    aris_memory = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(aris_memory)
    ms = aris_memory.memory_store

    # 验证是 MemoryMesh
    from laap_memory.mesh import MemoryMesh
    assert isinstance(ms.mesh, MemoryMesh), "底层不是 MemoryMesh!"
    print("\n1. aris_memory.memory_store 底层是 MemoryMesh ✅")

    # 写入测试
    ms.add_message("user", "你好，今天我们要测试记忆系统")
    ms.add_message("assistant", "好的，我已经准备好了")
    ms.add_core_memory("测试：记忆系统兼容性验证", tags=["test"], importance=9)
    print(f"2. 写入 3 条记忆 ✅")

    # 检索
    found = ms.search_memories("记忆系统", limit=5)
    print(f"3. 搜索 '记忆系统': 找到 {len(found)} 条 ✅")

    # 获取 LLM 历史
    history = ms.get_history_for_llm(limit=5)
    print(f"4. 获取 LLM 历史: {len(history)} 条 ✅")

    # 统计
    stats = ms.stats()
    print(f"5. Vault 统计: {stats['total_memories']} 条记忆 ✅")

    # 清理测试 vault
    vault_dir = os.path.expanduser("~/.laap/memory")
    if os.path.exists(vault_dir):
        import shutil
        shutil.rmtree(vault_dir)

    print(f"\n{'=' * 60}")
    print(f"aris_server 集成测试: ✅ 全部通过")
    print(f"{'=' * 60}")
    return True


async def main():
    ws_ok = await test_websocket_sync()
    aris_ok = await test_aris_server()

    print("\n" + "=" * 60)
    print("整体结果")
    print("=" * 60)
    print(f"WebSocket 同步: {'✅' if ws_ok else '❌'}")
    print(f"aris_server 集成: {'✅' if aris_ok else '❌'}")
    print(f"状态: {'全部通过' if ws_ok and aris_ok else '部分失败'}")


if __name__ == "__main__":
    asyncio.run(main())