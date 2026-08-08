"""
laap_memory/sync.py — CRDT 同步引擎

跨设备记忆同步的核心机制。

同步协议：
  每个记忆条目有 (id, version, device_id, device_priority) 四元组。
  冲突解决规则：
    1. 高 version 胜出
    2. 同 version：低 device_priority 胜出（priority 越小越优先）
    3. 同 version 同 priority：新 created_at 胜出
  删除采用墓碑（tombstone）机制。

同步流程：
  PULL  → 请求对端新增记忆
  PUSH  → 发送本地新增记忆
  MERGE → 双方合并冲突
"""

from __future__ import annotations

import json
import logging
import time
from typing import Optional

from .models import MemoryEntry, DeviceInfo
from .vault import MemoryVault

log = logging.getLogger("laap-memory.sync")


class SyncEngine:
    """同步引擎——管理跨设备记忆合并"""

    def __init__(self, vault: MemoryVault, local_device: DeviceInfo):
        self.vault = vault
        self.device = local_device
        self.vault.register_device(local_device)

    # ── 核心冲突解决 ──────────────────────────────────

    def resolve_conflict(self, local: MemoryEntry, remote: MemoryEntry) -> MemoryEntry:
        """解决两条记忆之间的冲突，返回胜出的条目

        规则：
        1. version 高者胜出
        2. version 相同：device_priority 低者胜出（数值越小优先级越高）
        3. 版本和优先级都相同：created_at 新者胜出
        """
        if remote.version > local.version:
            return remote
        if remote.version < local.version:
            return local

        # 同 version：比较 device_priority
        local_prio = self._get_device_priority(local.device_id)
        remote_prio = self._get_device_priority(remote.device_id)

        if remote_prio < local_prio:
            return remote
        if remote_prio > local_prio:
            return local

        # 同优先级：比较时间戳
        return remote if remote.created_at >= local.created_at else local

    def _get_device_priority(self, device_id: str) -> int:
        """获取设备优先级（默认 100）"""
        if device_id == self.device.device_id:
            return self.device.priority
        devices = self.vault.get_devices()
        for d in devices:
            if d.device_id == device_id:
                return d.priority
        return 100

    # ── 增量同步 ──────────────────────────────────────

    def pull_remote(self, remote_vault: MemoryVault,
                    entity_id: str, since_version: int = 0,
                    limit: int = 1000) -> list[MemoryEntry]:
        """从远程 Vault 拉取新增记忆，自动合并冲突

        Args:
            remote_vault: 远程 Vault 实例
            entity_id: 实体 ID
            since_version: 拉取版本号大于此值的记忆
            limit: 最大拉取条数

        Returns:
            合并后的新记忆列表
        """
        remote_entries = remote_vault.get_newer_than(entity_id, since_version, limit)
        merged = []

        for remote_entry in remote_entries:
            local = self.vault.get_by_id(remote_entry.id)
            if local is None:
                # 本地没有，直接存储
                self.vault.store(remote_entry, sign=False)
                merged.append(remote_entry)
            else:
                # 有冲突，解决
                winner = self.resolve_conflict(local, remote_entry)
                if winner.id != local.id or winner.version != local.version:
                    # 远程胜出，更新本地
                    winner.version = max(local.version, remote.version) + 1
                    self.vault.store(winner, sign=False)
                    merged.append(winner)

        # 更新同步状态
        max_version = max((e.version for e in remote_entries), default=since_version)
        if max_version > since_version:
            self.vault.update_sync_state(remote_vault.path, max_version)

        return merged

    def push_to_remote(self, remote_vault: MemoryVault,
                       entity_id: str, since_version: int = 0,
                       limit: int = 1000) -> int:
        """将本地新增记忆推送到远程 Vault

        Returns:
            推送的记忆条数
        """
        local_entries = self.vault.get_newer_than(entity_id, since_version, limit)
        pushed = 0

        for local_entry in local_entries:
            remote = remote_vault.get_by_id(local_entry.id)
            if remote is None:
                remote_vault.store(local_entry, sign=False)
                pushed += 1
            else:
                winner = self.resolve_conflict(local_entry, remote)
                if winner.id == local_entry.id:
                    # 本地胜出，更新远程
                    winner.version = max(local_entry.version, remote.version) + 1
                    remote_vault.store(winner, sign=False)
                    pushed += 1

        return pushed

    def sync(self, remote_vault: MemoryVault, entity_id: str) -> dict:
        """双向同步：先拉后推

        Returns:
            同步统计
        """
        sync_state = self.vault.get_sync_state(remote_vault.path)
        since_version = sync_state.get("last_version", 0)

        # 先拉取远程新增
        pulled = self.pull_remote(remote_vault, entity_id, since_version)
        # 再推送本地新增
        pushed = self.push_to_remote(remote_vault, entity_id, since_version)

        # 更新最终同步状态
        local_max = max(
            (e.version for e in self.vault.get_newer_than(entity_id, since_version, 1)),
            default=0
        )
        remote_max = max(
            (e.version for e in remote_vault.get_newer_than(entity_id, since_version, 1)),
            default=0
        )
        final_version = max(local_max, remote_max)
        self.vault.update_sync_state(remote_vault.path, final_version)
        remote_vault.update_sync_state(self.vault.path, final_version)

        return {
            "pulled": len(pulled),
            "pushed": pushed,
            "final_version": final_version,
            "duration_ms": 0,
        }

    # ── 导出/导入同步（文件传输） ──────────────────────

    def export_for_sync(self, entity_id: str, output_path: str,
                        since_version: int = 0) -> str:
        """导出增量记忆用于文件传输同步

        生成一个轻量化的 JSON 文件，只包含新增记忆。
        """
        entries = self.vault.get_newer_than(entity_id, since_version)
        data = {
            "version": 2,
            "sync_type": "incremental",
            "source_device": self.device.device_id,
            "entity_id": entity_id,
            "exported_at": time.time(),
            "since_version": since_version,
            "memories": [e.to_dict() for e in entries],
        }
        path = str(output_path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, default=str)
        return path

    def import_sync_file(self, input_path: str) -> dict:
        """导入同步文件，合并记忆

        Returns:
            合并统计
        """
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        remote_device_id = data.get("source_device", "unknown")
        entries = [MemoryEntry.from_dict(m) for m in data.get("memories", [])]

        merged_count = 0
        for entry in entries:
            local = self.vault.get_by_id(entry.id)
            if local is None:
                self.vault.store(entry, sign=False)
                merged_count += 1
            else:
                winner = self.resolve_conflict(local, entry)
                if winner.id != local.id or winner.version != local.version:
                    winner.version = max(local.version, entry.version) + 1
                    self.vault.store(winner, sign=False)
                    merged_count += 1

        return {
            "source_device": remote_device_id,
            "entries_received": len(entries),
            "merged": merged_count,
        }