"""
laap_memory/crdt.py — 字段级 CRDT 冲突解决

真正的无冲突数据类型，支持：
- 多值寄存器（Multi-Value Register）：每个字段每设备独立版本
- 字段级合并：不同设备修改不同字段，自动合并
- 冲突解决：同字段冲突时按 (version, timestamp) 决胜
- 与 SyncEngine 集成
"""

from __future__ import annotations

import json
import logging
import time
from typing import Optional

from .models import MemoryEntry, CRDTRegister
from .vault import MemoryVault

log = logging.getLogger("laap-memory.crdt")


class CRDTEngine:
    """字段级 CRDT 冲突解决引擎"""

    def __init__(self, vault: MemoryVault, local_device_id: str = "local"):
        self.vault = vault
        self.local_device_id = local_device_id

    # ── 写入 ──────────────────────────────────────────

    def write_field(self, memory_id: str, field: str, value: str,
                    device_id: str = "") -> CRDTRegister:
        """写入一个字段的寄存器

        每个字段在每个设备上独立版本号。
        """
        device_id = device_id or self.local_device_id

        # 获取当前设备的最新版本
        with self.vault._lock:
            row = self.vault._db.execute("""
                SELECT MAX(version) FROM crdt_registers
                WHERE memory_id = ? AND field = ? AND device_id = ?
            """, (memory_id, field, device_id)).fetchone()

        new_version = (row[0] or 0) + 1

        register = CRDTRegister(
            memory_id=memory_id,
            field=field,
            value=value,
            version=new_version,
            device_id=device_id,
            timestamp=time.time(),
        )
        self.vault.write_register(register)

        # 同步更新主表
        if field == "content":
            with self.vault._lock:
                self.vault._db.execute(
                    "UPDATE memories SET content = ?, version = ? WHERE id = ?",
                    (value, new_version, memory_id)
                )
                self.vault._db.commit()
        elif field == "importance":
            with self.vault._lock:
                self.vault._db.execute(
                    "UPDATE memories SET importance = ?, version = ? WHERE id = ?",
                    (float(value), new_version, memory_id)
                )
                self.vault._db.commit()
        elif field == "tags":
            with self.vault._lock:
                self.vault._db.execute(
                    "UPDATE memories SET tags = ?, version = ? WHERE id = ?",
                    (value, new_version, memory_id)
                )
                self.vault._db.commit()

        return register

    def write_entry(self, entry: MemoryEntry) -> dict[str, CRDTRegister]:
        """通过 CRDT 写入完整记忆条目（字段级合并）"""
        registers = {}
        registers["content"] = self.write_field(entry.id, "content", entry.content, entry.device_id)
        registers["importance"] = self.write_field(entry.id, "importance", str(entry.importance), entry.device_id)
        registers["tags"] = self.write_field(entry.id, "tags", json.dumps(entry.tags), entry.device_id)
        return registers

    # ── 合并 ──────────────────────────────────────────

    def merge_remote(self, remote_registers: list[CRDTRegister]) -> int:
        """合并远程寄存器（字段级 CRDT）

        核心逻辑：
        - 每个字段每个设备独立版本
        - 同字段同设备：版本号高者胜出
        - 不同字段：自动合并
        """
        merged = 0
        for reg in remote_registers:
            with self.vault._lock:
                local = self.vault._db.execute("""
                    SELECT version, value FROM crdt_registers
                    WHERE memory_id = ? AND field = ? AND device_id = ?
                """, (reg.memory_id, reg.field, reg.device_id)).fetchone()

            if local is None or reg.version > local[0]:
                # 远程版本更高，采纳
                self.vault.write_register(reg)
                merged += 1
            elif reg.version == local[0] and reg.timestamp > local[0]:
                # 同版本，较新时间戳胜出
                self.vault.write_register(reg)
                merged += 1

        return merged

    def resolve_entry(self, memory_id: str) -> dict[str, str]:
        """将 CRDT 寄存器合并为最终值（用于读取）"""
        return self.vault.resolve_registers(memory_id)

    def get_entry(self, memory_id: str) -> Optional[MemoryEntry]:
        """通过 CRDT 获取完整记忆条目"""
        # 先从主表获取基本字段
        entry = self.vault.get_by_id(memory_id)
        if not entry:
            return None

        # 用 CRDT 寄存器覆盖可能冲突的字段
        resolved = self.resolve_entry(memory_id)
        if "content" in resolved:
            entry.content = resolved["content"]
        if "importance" in resolved:
            entry.importance = float(resolved["importance"])
        if "tags" in resolved:
            try:
                entry.tags = json.loads(resolved["tags"])
            except (json.JSONDecodeError, TypeError):
                pass
        return entry

    # ── 冲突检测 ──────────────────────────────────────

    def detect_conflicts(self, memory_id: str) -> list[dict]:
        """检测指定记忆的冲突字段

        Returns:
            [{"field": "content", "versions": [{"device_id": ..., "value": ..., "version": ...}]}]
        """
        registers = self.vault.get_registers(memory_id)
        conflicts = []

        for field, regs in registers.items():
            if len(regs) > 1:
                # 检查是否有实际冲突（不同源）
                devices = set(r.device_id for r in regs)
                if len(devices) > 1:
                    versions = sorted(
                        [{"device_id": r.device_id, "value": r.value, "version": r.version}
                         for r in regs],
                        key=lambda x: -x["version"]
                    )
                    conflicts.append({
                        "field": field,
                        "versions": versions,
                    })

        return conflicts

    def stats(self) -> dict:
        """CRDT 统计"""
        with self.vault._lock:
            total = self.vault._db.execute(
                "SELECT COUNT(*) FROM crdt_registers"
            ).fetchone()[0]
            memories = self.vault._db.execute("""
                SELECT COUNT(DISTINCT memory_id) FROM crdt_registers
            """).fetchone()[0]
            conflicted = self.vault._db.execute("""
                SELECT COUNT(DISTINCT memory_id) FROM (
                    SELECT memory_id, field, COUNT(DISTINCT device_id) as dev_count
                    FROM crdt_registers
                    GROUP BY memory_id, field
                    HAVING dev_count > 1
                )
            """).fetchone()[0]

        return {
            "total_registers": total,
            "memories_with_crdt": memories,
            "conflicted_memories": conflicted,
        }