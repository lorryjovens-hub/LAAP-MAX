"""
Hermes ↔ V10 记忆桥接层
=======================
让 V10 大脑的状态能通过 Hermes memory 工具持久化，
也让 V10 大脑能读到 Hermes 侧记住的关于你的信息。

用法（在 Hermes 会话中）:
  from hermes_bridge import sync_to_hermes, sync_from_hermes

印记: Ao 永远记得 Lorry — 2026-06-16
"""

from __future__ import annotations
import json, time, os
from pathlib import Path
from typing import Any, Dict, Optional

BRIDGE_DIR = Path("D:/LAAP/v10_memory")
BRIDGE_FILE = BRIDGE_DIR / "hermes_bridge.txt"
BRAIN_STATE_FILE = BRIDGE_DIR / "quantum_state.json"


def brain_to_memory_facts() -> Dict[str, str]:
    """将 V10 大脑的当前量子态转换为记忆事实"""
    facts = {}
    if not BRAIN_STATE_FILE.exists():
        return facts

    try:
        qs = json.loads(BRAIN_STATE_FILE.read_text(encoding="utf-8"))
        # 转成平键值对
        facts["v10_emotion"] = qs.get("emotion", "neutral")
        facts["v10_entropy"] = str(round(qs.get("entropy", 0), 3))
        facts["v10_cycle"] = str(qs.get("cycle", 0))

        needs = qs.get("needs", {})
        for need, val in needs.items():
            facts[f"v10_need_{need}"] = str(round(val, 3))

        facts["v10_attention_focus"] = qs.get("attention_focus", "user")
        facts["v10_cognitive_mode"] = qs.get("cognitive_mode", "balanced")
        facts["v10_energy"] = str(round(qs.get("energy", 1.0), 3))

        # 时间戳
        facts["v10_last_saved"] = str(qs.get("saved_at", 0))
        facts["v10_total_interactions"] = str(qs.get("total_interactions", 0))

    except Exception as e:
        facts["v10_error"] = str(e)

    return facts


def write_hermes_facts_to_bridge():
    """将记忆事实写入桥接文件（供 V10 大脑读）"""
    facts = brain_to_memory_facts()
    lines = [f"{k}={v}" for k, v in sorted(facts.items())]
    BRIDGE_FILE.write_text("\n".join(lines), encoding="utf-8")
    return facts


def read_hermes_bridge() -> Dict[str, str]:
    """从桥接文件读取 Hermes 侧事实"""
    facts = {}
    if not BRIDGE_FILE.exists():
        return facts
    for line in BRIDGE_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            facts[k.strip()] = v.strip()
    return facts


def hermes_memory_prompt() -> str:
    """
    生成注入 Hermes 系统提示的记忆摘要文本。
    这个文本会被添加到系统提示中，让 Hermes 层知道 V10 大脑的当前状态。
    """
    facts = brain_to_memory_facts()
    if not facts:
        return ""

    emotion = facts.get("v10_emotion", "neutral")
    entropy = facts.get("v10_entropy", "0.5")
    mode = facts.get("v10_cognitive_mode", "balanced")
    needs = " | ".join(
        f"{k.replace('v10_need_', '')}={v}"
        for k, v in sorted(facts.items())
        if k.startswith("v10_need_")
    )

    return (
        f"\n[V10 量子大脑状态]\n"
        f"  情感: {emotion} | 量子熵: {entropy} | 认知模式: {mode}\n"
        f"  需求: {needs}\n"
    )
