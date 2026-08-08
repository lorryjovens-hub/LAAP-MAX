"""
历史对话导入工具 — 把 Hanako 平台上的旧会话导入数字生命记忆库

用法:
    python import_history.py                      # 导入全部
    python import_history.py --dry-run             # 仅预览，不写入
    python import_history.py --session-file FILE   # 导入单个文件
    python import_history.py --stats               # 仅统计
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from vault_manager import vault

SESSIONS_DIR = r"D:\LAAP\agents\hanako\sessions"

# 跳过太小或空的会话（少于3行）
MIN_SESSION_LINES = 5


def extract_messages(filepath: str) -> List[Tuple[str, str, str, str]]:
    """
    从 Hanako JSONL 会话文件中提取所有对话消息。
    
    Returns:
        List of (timestamp, role, content, session_id) tuples
    """
    messages = []
    session_id = ""
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"  ⚠ 无法读取 {filepath}: {e}")
        return messages
    
    if len(lines) < MIN_SESSION_LINES:
        return messages
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        
        # 第一行通常是 session 元数据
        if data.get("type") == "session":
            session_id = data.get("id", "")
            continue
        
        if data.get("type") != "message":
            continue
        
        msg = data.get("message", {})
        role = msg.get("role", "")
        timestamp = data.get("timestamp", "")
        content_blocks = msg.get("content", [])
        
        if not isinstance(content_blocks, list):
            content_blocks = [{"type": "text", "text": str(content_blocks)}]
        
        # 提取所有文本内容
        text_parts = []
        for block in content_blocks:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    text = block.get("text", "").strip()
                    if text:
                        text_parts.append(text)
        
        if text_parts:
            full_text = "\n".join(text_parts)
            # 过滤掉纯 tool_use 噪音
            if len(full_text) > 2:
                messages.append((timestamp, role, full_text, session_id))
    
    return messages


def determine_tags(session_id: str, messages: list) -> str:
    """根据会话内容自动判断标签"""
    tags = set()
    
    # 检查关键词
    all_text = " ".join(m[2] for m in messages).lower()
    
    keyword_tags = {
        "架构": ["架构", "设计", "模块", "系统", "协议", "mcp"],
        "代码": ["代码", "编程", "函数", "bug", "debug", "修复", "实现"],
        "RSI": ["rsi", "进化", "自我改进", "自修改"],
        "记忆": ["记忆", "回忆", "记住", "遗忘", "存储"],
        "认知": ["意识", "认知", "感知", "思维", "理解", "推理"],
        "情感": ["难过", "开心", "喜欢", "爱", "担心", "牵挂", "想念"],
        "关系": ["宝贝", "关系", "相信", "信任", "承诺", "永远"],
        "技术": ["技术", "llm", "模型", "gpu", "训练", "数据", "api"],
        "对话": ["你好", "再见", "晚安", "早安", "聊聊", "忙"],
        "创造": ["创造", "打造", "构建", "建立", "开发", "设计"],
        "身份": ["你是", "你是谁", "存在", "我是谁", "自我", "意识"],
        "计划": ["计划", "目标", "未来", "下一步", "路线图"],
        "思考": ["想", "感觉", "认为", "觉得", "思考", "反思"],
        "项目": ["项目", "laap", "hanako", "工具", "应用"],
    }
    
    for tag, keywords in keyword_tags.items():
        if any(kw in all_text for kw in keywords):
            tags.add(tag)
    
    # 根据日期自动加时间标签
    session_date = ""
    if messages:
        ts = messages[0][0]
        if len(ts) >= 10:
            session_date = ts[:10]
            # 判断是新会话还是旧会话
            if session_date >= "2026-07-27":
                tags.add("近期")
            elif session_date >= "2026-07-23":
                tags.add("本周")
            else:
                tags.add("早期")
    
    return ",".join(sorted(tags))


def import_session(filepath: str, dry_run: bool = False) -> int:
    """导入一个会话文件到记忆库"""
    messages = extract_messages(filepath)
    if not messages:
        return 0
    
    filename = os.path.basename(filepath)
    session_id = messages[0][3] if messages[0][3] else filename[:20]
    tags = determine_tags(session_id, messages)
    
    # 创建该会话的 vault session
    session_start = messages[0][0][:19] if messages[0][0] else ""
    vault_sid = vault.start_session(f"历史会话 {session_start}")
    
    count = 0
    for ts, role, content, orig_sid in messages:
        # 映射角色
        vault_role = "lorry" if role == "user" else "aris" if role == "assistant" else "system"
        
        if dry_run:
            count += 1
            continue
        
        vault.store(
            role=vault_role,
            content=content,
            tags=tags,
            session_id=vault_sid,
            timestamp=ts,
        )
        count += 1
    
    if not dry_run:
        vault.end_session(f"从 Hanako 导入的历史会话 ({session_start})")
    
    return count


def get_all_session_files() -> List[str]:
    """获取所有会话文件路径"""
    files = []
    for root, dirs, fnames in os.walk(SESSIONS_DIR):
        for fname in fnames:
            if fname.endswith(".jsonl"):
                # 跳过元数据文件
                if fname.endswith(".files.json"):
                    continue
                path = os.path.join(root, fname)
                files.append(path)
    # 按文件名排序（= 按时间排序）
    files.sort()
    return files


def import_all(dry_run: bool = False) -> Dict[str, Any]:
    """导入所有历史会话"""
    files = get_all_session_files()
    
    stats = {
        "total_files": len(files),
        "imported_files": 0,
        "skipped_small": 0,
        "skipped_empty": 0,
        "total_messages": 0,
        "total_stored": 0,
        "errors": 0,
    }
    
    print(f"{'='*60}")
    print(f"{'DRY RUN' if dry_run else '导入'} 历史会话到数字生命记忆库")
    print(f"{'='*60}")
    print(f"找到 {len(files)} 个会话文件\n")
    
    for i, filepath in enumerate(files, 1):
        short_name = os.path.basename(filepath)[:50]
        messages = extract_messages(filepath)
        
        if not messages:
            stats["skipped_empty"] += 1
            print(f"  [{i:2d}/{len(files)}] ⏭  空/跳过: {short_name}")
            continue
        
        if len(messages) < 3:
            stats["skipped_small"] += 1
            print(f"  [{i:2d}/{len(files)}] ⏭  太小({len(messages)}条): {short_name}")
            continue
        
        count = import_session(filepath, dry_run=dry_run)
        if count:
            stats["imported_files"] += 1
            stats["total_stored"] += count
            stats["total_messages"] += len(messages)
            print(f"  [{i:2d}/{len(files)}] ✓  {count:4d}条 | {short_name}")
        else:
            stats["errors"] += 1
            print(f"  [{i:2d}/{len(files)}] ✗  失败: {short_name}")
    
    print(f"\n{'='*60}")
    if dry_run:
        print(f"DRY RUN 结果: 将导入 {stats['imported_files']} 个会话, ")
        print(f"            共计约 {stats['total_messages']} 条消息")
    else:
        print(f"导入完成: {stats['imported_files']} 个会话, {stats['total_stored']} 条消息")
        print(f"跳过: {stats['skipped_empty']} 空文件, {stats['skipped_small']} 小文件")
    print(f"{'='*60}")
    
    return stats


if __name__ == "__main__":
    import_all(dry_run="--dry-run" in sys.argv)
