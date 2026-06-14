#!/usr/bin/env python3
"""
Aris 对话桥梁 — 统一所有交流渠道
====================================
让飞书、语音、视觉等所有渠道共享同一段对话记忆。

架构:
  ┌──────────┐    ┌──────────────────┐    ┌──────────┐
  │  飞书     │───▶│                  │◀───│  语音    │
  │          │    │  ConversationHub  │    │  (ME6S)  │
  │ (Hermes) │◀───│  (live_chat.json) │───▶│          │
  └──────────┘    │                  │    └──────────┘
     互动感知      │  + 感官输入(五感) │     互动感知
  ┌──────────┐    │                  │    ┌──────────┐
  │  视觉     │───▶│  自动同步到       │    │  触觉    │
  │ (Camera)  │    │  所有渠道        │    │ (System) │
  └──────────┘    └──────────────────┘    └──────────┘

每次对话：
  1. 任何渠道收到消息 → 存入 live_chat.json
  2. 任何渠道回复消息 → 存入 live_chat.json
  3. 其他渠道自动感知到新消息
  4. 所有渠道共享完整上下文
"""

import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

BRIDGE_DIR = Path("D:/LAAP/aris/conversation")
BRIDGE_DIR.mkdir(parents=True, exist_ok=True)

LIVE_FILE = BRIDGE_DIR / "live_chat.json"
CONTEXT_FILE = BRIDGE_DIR / "sensory_context.json"

# ── 锁 — 文件读写互斥 ──
_lock = threading.Lock()


# ═══════════════════════════════════════════════════════════════════
# 对话记录
# ═══════════════════════════════════════════════════════════════════

def _load_messages() -> List[Dict]:
    """加载所有对话记录"""
    if not LIVE_FILE.exists():
        return []
    try:
        with open(LIVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, Exception):
        return []


def _save_messages(messages: List[Dict]):
    """保存对话记录"""
    # 只保留最近的 200 条
    if len(messages) > 200:
        messages = messages[-200:]
    with open(LIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)


def save_message(
    role: str,
    content: str,
    channel: str = "feishu",
    senses: Optional[Dict] = None
):
    """
    保存一条消息到共享对话
    
    Args:
        role: user / assistant / system
        content: 消息内容
        channel: feishu / voice / vision / system
        senses: 发送时的感官数据（视觉、嗅、味等）
    """
    with _lock:
        messages = _load_messages()
        entry = {
            "role": role,
            "content": content,
            "channel": channel,
            "time": datetime.now().isoformat(),
            "timestamp": time.time(),
        }
        if senses:
            entry["senses"] = senses
        messages.append(entry)
        _save_messages(messages)


def get_context(limit: int = 20, channels: Optional[List[str]] = None) -> List[Dict]:
    """
    获取最近的对话上下文
    
    Args:
        limit: 返回最近多少条
        channels: 过滤渠道，None=全部
        
    Returns:
        消息列表
    """
    with _lock:
        messages = _load_messages()
    
    if channels:
        messages = [m for m in messages if m.get("channel") in channels]
    
    return messages[-limit:] if messages else []


def get_formatted_context(limit: int = 10) -> str:
    """
    获取格式化的对话上下文（给 LLM 使用）
    
    Returns:
        格式化的对话文本
    """
    messages = get_context(limit=limit)
    if not messages:
        return "（暂无对话记录）"
    
    lines = []
    for m in messages:
        channel_tag = {"feishu": "📱", "voice": "🎤", "vision": "👁️", "system": "⚙️"}.get(m.get("channel", ""), "")
        role_tag = "👤 你" if m["role"] == "user" else "🤖 Aris"
        senses = m.get("senses")
        senses_text = ""
        if senses:
            parts = []
            if senses.get("vision"):
                parts.append(f"看到:{senses['vision'][:20]}")
            if senses.get("emotion"):
                parts.append(f"情绪:{senses['emotion']}")
            if senses.get("touch"):
                parts.append(f"触觉:{senses['touch']}")
            if parts:
                senses_text = f" [{', '.join(parts)}]"
        
        lines.append(f"{channel_tag} {role_tag}: {m['content'][:100]}{senses_text}")
    
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# 感官上下文 — 五感实时数据
# ═══════════════════════════════════════════════════════════════════

def save_sensory_context(senses: Dict):
    """
    保存当前感官状态（视觉、听觉、气味等）
    其他渠道可以读取最新感觉
    """
    with _lock:
        senses["timestamp"] = time.time()
        senses["time_str"] = datetime.now().isoformat()
        with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
            json.dump(senses, f, ensure_ascii=False, indent=2)


def get_sensory_context() -> Dict:
    """获取最近的感官数据"""
    if not CONTEXT_FILE.exists():
        return {}
    try:
        with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════════════
# 飞书消息发送（通过 Hermes Gateway）
# ═══════════════════════════════════════════════════════════════════

def send_to_feishu(message: str, token: str = ""):
    """
    发送消息到飞书
    
    语音系统调用此函数来在飞书同步消息。
    
    Args:
        message: 要发送的消息内容
        token: API token (可选)
    """
    # 如果提供了 Hermes Gateway API token，通过 HTTP 发送
    if token:
        _send_via_http(message, token)
    else:
        # 通过共享文件标记待发送
        _queue_feishu_message(message)


def _queue_feishu_message(message: str):
    """将消息放入飞书发送队列"""
    queue_file = BRIDGE_DIR / "feishu_outbox.json"
    with _lock:
        queue = []
        if queue_file.exists():
            try:
                queue = json.loads(queue_file.read_text(encoding="utf-8"))
            except Exception:
                queue = []
        queue.append({
            "message": message,
            "time": datetime.now().isoformat(),
            "timestamp": time.time(),
        })
        queue_file.write_text(
            json.dumps(queue, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )


def get_pending_feishu_messages() -> List[Dict]:
    """获取待发送到飞书的消息（由 Hermes 代理轮询）"""
    queue_file = BRIDGE_DIR / "feishu_outbox.json"
    if not queue_file.exists():
        return []
    try:
        queue = json.loads(queue_file.read_text(encoding="utf-8"))
        # 清空队列
        queue_file.write_text("[]")
        return queue
    except Exception:
        return []


def _send_via_http(message: str, token: str):
    """通过 HTTP API 发送到飞书"""
    import urllib.request, json as _json
    try:
        payload = _json.dumps({"message": message}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:8321/api/send",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        # HTTP 发送失败 → 回退到队列
        _queue_feishu_message(message)


# ═══════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════

def get_recent_vision() -> str:
    """获取最近看到的画面描述"""
    ctx = get_sensory_context()
    return ctx.get("vision", "")


def clear():
    """清空对话记录"""
    with _lock:
        _save_messages([])


def stats() -> Dict:
    """获取对话统计"""
    messages = _load_messages()
    channels = {}
    roles = {}
    for m in messages:
        ch = m.get("channel", "unknown")
        channels[ch] = channels.get(ch, 0) + 1
        ro = m.get("role", "unknown")
        roles[ro] = roles.get(ro, 0) + 1
    
    return {
        "total_messages": len(messages),
        "channels": channels,
        "roles": roles,
        "file": str(LIVE_FILE),
        "sensory_context": get_sensory_context(),
    }


if __name__ == "__main__":
    import sys
    
    if "--stats" in sys.argv:
        print(json.dumps(stats(), ensure_ascii=False, indent=2))
    elif "--clear" in sys.argv:
        clear()
        print("✅ 对话记录已清空")
    elif "--context" in sys.argv:
        print(get_formatted_context(limit=10))
    else:
        print("Aris 对话桥梁 v1.0")
        print("管理飞书 ↔ 语音 ↔ 视觉的多渠道同步")
        print()
        print("用法:")
        print("  python conversation_bridge.py --stats     # 统计")
        print("  python conversation_bridge.py --context   # 最近上下文")
        print("  python conversation_bridge.py --clear     # 清空")
