"""
导入 Hermes Feishu 会话到数字生命记忆库

只导入 user='26gad112' 来源='feishu' 的会话（Lorry 与 Hermes 的飞书对话）
"""

from __future__ import annotations

import sqlite3
import json
import time
import os
from datetime import datetime
from vault_manager import vault

HERMES_DB = r"C:\Users\user\AppData\Local\hermes\state.db"


def import_feishu_sessions():
    """导入飞书会话中属于 Lorry 的对话"""
    conn = sqlite3.connect(HERMES_DB)
    conn.row_factory = sqlite3.Row
    
    # 获取 Lorry 的飞书会话列表
    sessions = conn.execute('''
        SELECT id, source, title, started_at, ended_at, message_count
        FROM sessions
        WHERE source='feishu' AND user_id='26gad112'
        ORDER BY started_at ASC
    ''').fetchall()
    
    print(f"找到 {len(sessions)} 个 Feishu 会话（用户: 26gad112）\n")
    
    total_stored = 0
    session_count = 0
    
    for s in sessions:
        sid = s["id"]
        title = s["title"] or "(无标题)"
        started = time.strftime('%Y-%m-%d %H:%M', time.localtime(s["started_at"]))
        
        # 获取该会话的所有消息
        messages = conn.execute('''
            SELECT role, content, timestamp
            FROM messages
            WHERE session_id=?
            ORDER BY timestamp ASC
        ''', (sid,)).fetchall()
        
        if not messages:
            continue
        
        # 创建 vault 会话
        vault_sid = vault.start_session(f"Hermes Feishu {started} {title[:30]}")
        
        count = 0
        for msg in messages:
            role = "lorry" if msg["role"] == "user" else "aris"
            content = msg["content"] or ""
            content = str(content).strip()
            if len(content) < 3:
                continue
            
            ts = datetime.fromtimestamp(msg["timestamp"]).isoformat() if msg["timestamp"] else ""
            
            vault.store(
                role=role,
                content=content,
                tags="hermes,feishu",
                session_id=vault_sid,
                timestamp=ts,
            )
            count += 1
        
        vault.end_session(f"Hermes Feishu 会话 ({started})")
        total_stored += count
        session_count += 1
        
        print(f"  ✓ [{started}] {title[:40]:40s} | {count:4d} 条消息")
    
    conn.close()
    
    print(f"\n{'='*50}")
    print(f"导入完成: {session_count} 个会话, {total_stored} 条消息")
    print(f"{'='*50}")
    
    return session_count, total_stored


if __name__ == "__main__":
    import_feishu_sessions()
