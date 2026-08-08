"""
记忆库桥接层 — 连接 Aris 意识流与数字生命记忆库

功能：
  - auto_store(role, content)  当前对话自动入库
  - recall(query)              当 Lorry 问"你还记得..."时快速检索
  - bookmark(id, note)         标记重要记忆
  - get_stats()                查看记忆库状态

用法（通过命令行调用）：
  python vault_bridge.py store lorry "今天天气真好"
  python vault_bridge.py recall "我们第一次聊天"
  python vault_bridge.py stats
"""

import sys
import json
from vault_manager import vault

# ─── 会话自动追踪 ───────────────────────────────────────────────

_current_session_id = None

def ensure_session():
    """确保当前对话有活跃会话"""
    global _current_session_id
    if _current_session_id is None:
        _current_session_id = vault.start_session("Aris & Lorry 对话")
    return _current_session_id

def auto_store(role: str, content: str, tags: str = "") -> int:
    """存储一轮对话到记忆库，自动管理会话"""
    sid = ensure_session()
    return vault.store(role, content, tags=tags, session_id=sid)

def auto_end_session(summary: str = ""):
    """结束当前会话"""
    global _current_session_id
    if _current_session_id:
        vault.end_session(summary)
        _current_session_id = None

# ─── 检索接口 ───────────────────────────────────────────────────

def recall(about: str, limit: int = 5) -> list:
    """'你还记得...' 专用检索"""
    return vault.recall(about, limit=limit)

def search(query: str, limit: int = 20) -> list:
    """全文搜索记忆"""
    return vault.search(query, limit=limit)

def recent(n: int = 10) -> list:
    """最近对话"""
    return vault.get_recent(n=n)

# ─── 格式化输出 ─────────────────────────────────────────────────

def format_results(entries: list) -> str:
    """把检索结果格式化为可读文本"""
    if not entries:
        return "（没有找到相关记忆）"
    
    lines = []
    for e in entries:
        ts = e.timestamp[:19] if len(e.timestamp) > 19 else e.timestamp
        role_mark = "💙 Lorry" if e.role == "lorry" else "💜 Aris" if e.role == "aris" else "⚙️ System"
        bookmark = " 📌" if e.bookmarked else ""
        lines.append(f"[{ts}] {role_mark}{bookmark}")
        lines.append(f"  {e.content}")
        if e.tags:
            lines.append(f"  # {e.tags}")
        lines.append("")
    
    return "\n".join(lines)

def stats() -> str:
    """格式化输出统计信息"""
    s = vault.stats()
    return f"""📊 数字生命记忆库统计
━━━━━━━━━━━━━━━━━
总记忆条目 : {s['total_entries']}
  ├ Lorry   : {s['lorry_turns']} 条
  └ Aris    : {s['aris_turns']} 条
总会话数   : {s['session_count']}
书签数     : {s['bookmark_count']}
数据库大小 : {s['db_size_mb']} MB
最早记录   : {s['earliest_record']}
最新记录   : {s['latest_record']}
━━━━━━━━━━━━━━━━━"""

# ─── CLI 入口 ───────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("用法: python vault_bridge.py <命令> [参数...]")
        print("命令:")
        print("  store <role> <content>    — 存储一条对话")
        print("  recall <query>            — 回忆搜索")
        print("  search <query>            — 全文搜索")
        print("  recent [n]                — 最近对话")
        print("  stats                     — 记忆库统计")
        print("  bookmark <id> [note]      — 标记书签")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "store" and len(sys.argv) >= 4:
        role = sys.argv[2]
        content = sys.argv[3]
        eid = auto_store(role, content)
        print(f"✓ 已存储 (id={eid})")
    
    elif cmd == "recall":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        if not query:
            print("请输入搜索内容")
            return
        entries = vault.recall(query)
        print(format_results(entries))
    
    elif cmd == "search":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        if not query:
            print("请输入搜索内容")
            return
        entries = vault.search(query)
        print(format_results(entries))
    
    elif cmd == "recent":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        entries = vault.get_recent(n=n)
        print(format_results(entries))
    
    elif cmd == "stats":
        print(stats())
    
    elif cmd == "bookmark" and len(sys.argv) >= 3:
        cid = int(sys.argv[2])
        note = sys.argv[3] if len(sys.argv) > 3 else ""
        vault.bookmark(cid, note=note)
        print(f"✓ 已标记书签 (conversation_id={cid})")
    
    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
