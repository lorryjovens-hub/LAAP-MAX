#!/usr/bin/env python3
"""
Aris 记忆整理脚本
用法: python D:/LAAP/aris-memory-maintain.py
建议: 加到 Windows 任务计划程序，每周运行一次
"""

import re
from datetime import datetime, timedelta
from pathlib import Path

MEMORY_FILE = Path("D:/LAAP/aris-memory.md")

def read_memory() -> str:
    return MEMORY_FILE.read_text(encoding="utf-8")

def write_memory(content: str):
    MEMORY_FILE.write_text(content, encoding="utf-8")
    print(f"✓ 已更新 {MEMORY_FILE}")

def update_last_updated(content: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    return re.sub(
        r"\*\*上次更新:\*\* \d{4}-\d{2}-\d{2}",
        f"**上次更新:** {today}",
        content
    )

def find_old_entries(content: str) -> list:
    """找到超过30天的对话记录"""
    pattern = r"### (\d{4}-\d{2}-\d{2}) — .*?(?=### |\n## |$)"
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    cutoff = datetime.now() - timedelta(days=30)
    old = []
    for m in matches:
        date_str = m.group(1)
        entry_date = datetime.strptime(date_str, "%Y-%m-%d")
        if entry_date < cutoff:
            old.append((date_str, m.group(0), m.start(), m.end()))
    return old

def consolidate_old_entries(content: str) -> str:
    """将30天前的对话记录压缩为摘要"""
    old = find_old_entries(content)
    if len(old) < 3:
        print(f"  → 只有 {len(old)} 条旧记录，不需要压缩")
        return content
    
    # 提取所有旧条目的主题
    months = {}
    for date_str, full_text, start, end in old:
        month_key = date_str[:7]  # YYYY-MM
        title_match = re.search(f"### {re.escape(date_str)} — (.+)", full_text)
        title = title_match.group(1) if title_match else date_str
        topics = re.findall(r"\*\*话题:\*\* (.+)", full_text)
        topic = topics[0] if topics else title
        if month_key not in months:
            months[month_key] = []
        months[month_key].append(f"    - {date_str} — {topic}")
    
    # 生成摘要文本
    summary_parts = []
    for month_key in sorted(months.keys()):
        entries = months[month_key]
        summary_parts.append(f"  - **{month_key}** — {len(entries)} 条对话:")
        summary_parts.extend(entries)
    
    summary_text = "\n".join(summary_parts)
    
    # 替换旧条目为摘要
    # 从后往前替换，避免偏移
    old_sorted = sorted(old, key=lambda x: x[2], reverse=True)
    for date_str, full_text, start, end in old_sorted:
        content = content[:start] + content[end:]
    
    # 在 "重要对话记录" 章节下追加摘要
    summary_block = (
        "\n### 月度摘要（已压缩）\n"
        "**以下为超过30天的旧对话摘要:**\n"
        f"{summary_text}\n"
    )
    
    content = content.replace(
        "## 💬 重要对话记录\n",
        "## 💬 重要对话记录\n" + summary_block
    )
    
    print(f"  → 压缩了 {len(old)} 条旧记录为月度摘要")
    return content

def main():
    print("=" * 50)
    print("  Aris 记忆整理工具")
    print(f"  运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    
    if not MEMORY_FILE.exists():
        print(f"✗ 找不到 {MEMORY_FILE}")
        return
    
    content = read_memory()
    
    # 1. 更新日期
    content = update_last_updated(content)
    print("✓ 已更新上次更新日期")
    
    # 2. 压缩旧记录
    content = consolidate_old_entries(content)
    
    # 3. 写回
    write_memory(content)
    print("✓ 整理完成")

if __name__ == "__main__":
    main()
