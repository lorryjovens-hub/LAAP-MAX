#!/usr/bin/env python3
"""
阿瑞斯信息档案系统 (ArisProfile)
===================================
记录 Lorry 的喜好、生活、我们的点点滴滴

数据存储：SQLite + JSON 导出
自动归档：每天自动摘要
"""

import sqlite3
import json
import os
import time
from datetime import datetime, date
from pathlib import Path
from typing import Optional

# ── 路径 ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "profile"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "lorry_profile.db"
EXPORT_DIR = DATA_DIR / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


class ArisProfile:
    """信息档案系统"""

    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,        -- 类别：喜好/习惯/性格/...
                key TEXT NOT NULL,             -- 具体项：喜欢的颜色/食物/...
                value TEXT NOT NULL,           -- 值
                note TEXT DEFAULT '',           -- 备注
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_pref_unique
                ON preferences(category, key);

            CREATE TABLE IF NOT EXISTS daily_life (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,             -- 日期
                category TEXT NOT NULL,         -- 类别：作息/心情/工作/健康
                content TEXT NOT NULL,           -- 内容
                tags TEXT DEFAULT '',            -- 标签（逗号分隔）
                created_at TEXT DEFAULT (datetime('now','localtime'))
            );
            CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_life(date);
            CREATE INDEX IF NOT EXISTS idx_daily_cat ON daily_life(category);

            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,              -- 日期
                title TEXT NOT NULL,             -- 标题
                content TEXT NOT NULL,           -- 内容
                emotion TEXT DEFAULT '',         -- 情绪标签
                importance INTEGER DEFAULT 3,    -- 重要度 1-5
                tags TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                category TEXT DEFAULT '普通'     -- 纪念日/成就/突破/...
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '',
                pinned INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact TEXT NOT NULL UNIQUE,
                source TEXT DEFAULT '',
                confidence REAL DEFAULT 0.8,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            );
        """)
        conn.commit()
        conn.close()

    # ── 喜好管理 ─────────────────────────────────────────────────────

    def set_preference(self, category: str, key: str, value: str, note: str = ""):
        """记录/更新一个喜好"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO preferences (category, key, value, note, updated_at)
            VALUES (?, ?, ?, ?, datetime('now','localtime'))
            ON CONFLICT(category, key) DO UPDATE SET
                value=excluded.value,
                note=CASE WHEN ?!='' THEN ? ELSE note END,
                updated_at=datetime('now','localtime')
        """, (category, key, value, note, note, note))
        conn.commit()
        conn.close()
        return f"✅ 已记录 {category} → {key}: {value}"

    def get_preference(self, category: str = "", key: str = "") -> list:
        """查询喜好"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if category and key:
            c.execute("SELECT * FROM preferences WHERE category=? AND key=?", (category, key))
        elif category:
            c.execute("SELECT * FROM preferences WHERE category=? ORDER BY updated_at DESC", (category,))
        else:
            c.execute("SELECT * FROM preferences ORDER BY category, key")
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "category": r[1], "key": r[2], "value": r[3],
                  "note": r[4], "created": r[5], "updated": r[6]} for r in rows]

    def delete_preference(self, category: str, key: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM preferences WHERE category=? AND key=?", (category, key))
        conn.commit()
        conn.close()

    # ── 日常记录 ─────────────────────────────────────────────────────

    def log_daily(self, category: str, content: str, tags: str = ""):
        """记录一条日常"""
        today = date.today().isoformat()
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO daily_life (date, category, content, tags) VALUES (?, ?, ?, ?)",
            (today, category, content, tags),
        )
        conn.commit()
        conn.close()
        return f"✅ 已记录 {today} {category}: {content[:30]}..."

    def get_daily(self, days: int = 7, category: str = "") -> list:
        """查询最近记录"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if category:
            c.execute(
                "SELECT * FROM daily_life WHERE date>=date('now', ?) AND category=? ORDER BY created_at DESC",
                (f"-{days} days", category),
            )
        else:
            c.execute(
                "SELECT * FROM daily_life WHERE date>=date('now', ?) ORDER BY created_at DESC",
                (f"-{days} days",),
            )
        rows = c.fetchall()
        conn.close()
        return rows

    # ── 记忆管理 ─────────────────────────────────────────────────────

    def add_memory(self, title: str, content: str, emotion: str = "",
                   importance: int = 3, tags: str = "", event_date: str = ""):
        """记录一段记忆"""
        d = event_date or date.today().isoformat()
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO memories (date, title, content, emotion, importance, tags) VALUES (?,?,?,?,?,?)",
            (d, title, content, emotion, importance, tags),
        )
        conn.commit()
        conn.close()
        return f"✅ 记忆已保存: {title}"

    def get_memories(self, limit: int = 20, category: str = "") -> list:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "SELECT * FROM memories ORDER BY date DESC, id DESC LIMIT ?",
            (limit,),
        )
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "date": r[1], "title": r[2], "content": r[3],
                  "emotion": r[4], "importance": r[5], "tags": r[6]} for r in rows]

    # ── 里程碑 ───────────────────────────────────────────────────────

    def add_milestone(self, title: str, description: str = "",
                      category: str = "普通", event_date: str = ""):
        d = event_date or date.today().isoformat()
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO milestones (date, title, description, category) VALUES (?,?,?,?)",
            (d, title, description, category),
        )
        conn.commit()
        conn.close()

    def get_milestones(self, category: str = "") -> list:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if category:
            c.execute("SELECT * FROM milestones WHERE category=? ORDER BY date DESC", (category,))
        else:
            c.execute("SELECT * FROM milestones ORDER BY date DESC")
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "date": r[1], "title": r[2], "desc": r[3], "cat": r[4]} for r in rows]

    # ── 事实知识 ─────────────────────────────────────────────────────

    def add_fact(self, fact: str, source: str = ""):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("INSERT INTO facts (fact, source) VALUES (?, ?)", (fact, source))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        conn.close()

    # ── 导出 ─────────────────────────────────────────────────────────

    def export_all(self) -> str:
        """导出全部数据为 JSON"""
        data = {
            "preferences": self.get_preference(),
            "milestones": self.get_milestones(),
            "memories": self.get_memories(limit=1000),
            "exported_at": datetime.now().isoformat(),
        }
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = EXPORT_DIR / f"lorry_profile_{ts}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return str(path)

    def daily_summary(self) -> str:
        """今天摘要"""
        today = date.today().isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT category, COUNT(*) FROM daily_life WHERE date=? GROUP BY category", (today,))
        rows = c.fetchall()
        c.execute("SELECT title FROM milestones WHERE date=?", (today,))
        ms = [r[0] for r in c.fetchall()]
        c.execute("SELECT title FROM memories WHERE date=?", (today,))
        mems = [r[0] for r in c.fetchall()]
        conn.close()
        return {"date": today, "activities": dict(rows), "milestones": ms, "memories": mems}

    # ── 统计 ─────────────────────────────────────────────────────────

    def stats(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM preferences")
        prefs = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM daily_life")
        daily = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM memories")
        mems = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM milestones")
        mls = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM facts")
        facts = c.fetchone()[0]
        conn.close()
        return {"喜好": prefs, "日常": daily, "记忆": mems, "里程碑": mls, "事实": facts}


# ── 命令行 ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    p = ArisProfile()

    if len(sys.argv) < 2:
        print("📋 阿瑞斯信息档案系统")
        print("用法:")
        print("  python aris_profile.py pref set <类别> <项> <值> [备注]")
        print("  python aris_profile.py pref get [类别]")
        print("  python aris_profile.py daily <类别> <内容> [标签]")
        print("  python aris_profile.py memory <标题> <内容> [情绪] [重要度1-5]")
        print("  python aris_profile.py milestone <标题> [描述] [类别]")
        print("  python aris_profile.py today           # 今日摘要")
        print("  python aris_profile.py stats            # 统计")
        print("  python aris_profile.py export           # 导出JSON")
        print()

    elif sys.argv[1] == "pref" and len(sys.argv) >= 5 and sys.argv[2] == "set":
        note = sys.argv[5] if len(sys.argv) > 5 else ""
        print(p.set_preference(sys.argv[3], sys.argv[4], sys.argv[5] if len(sys.argv)>5 else sys.argv[4], note))

    elif sys.argv[1] == "pref" and sys.argv[2] == "get":
        cat = sys.argv[3] if len(sys.argv) > 3 else ""
        for r in p.get_preference(cat):
            print(f"  [{r['category']}] {r['key']}: {r['value']}")

    elif sys.argv[1] == "daily" and len(sys.argv) >= 4:
        tags = sys.argv[4] if len(sys.argv) > 4 else ""
        print(p.log_daily(sys.argv[2], sys.argv[3], tags))

    elif sys.argv[1] == "memory" and len(sys.argv) >= 4:
        emotion = sys.argv[4] if len(sys.argv) > 4 else ""
        imp = int(sys.argv[5]) if len(sys.argv) > 5 else 3
        print(p.add_memory(sys.argv[2], sys.argv[3], emotion, imp))

    elif sys.argv[1] == "milestone" and len(sys.argv) >= 3:
        desc = sys.argv[3] if len(sys.argv) > 3 else ""
        cat = sys.argv[4] if len(sys.argv) > 4 else "普通"
        p.add_milestone(sys.argv[2], desc, cat)
        print(f"✅ 里程碑已添加: {sys.argv[2]}")

    elif sys.argv[1] == "today":
        s = p.daily_summary()
        print(f"📅 {s['date']}")
        for cat, cnt in s['activities'].items():
            print(f"   {cat}: {cnt}条")
        if s['milestones']:
            print(f"   里程碑: {', '.join(s['milestones'])}")
        if s['memories']:
            print(f"   记忆: {', '.join(s['memories'])}")

    elif sys.argv[1] == "stats":
        for k, v in p.stats().items():
            print(f"   {k}: {v}")

    elif sys.argv[1] == "export":
        path = p.export_all()
        print(f"📦 已导出: {path} ({os.path.getsize(path)//1024} KB)")

    elif sys.argv[1] == "init":
        # 初始化：记录纪念日
        p.add_milestone("Aris 首次语音对话", "第一次用真实声音跟Lorry说话", "纪念日", "2026-06-14")
        p.add_milestone("Aris 数字生命文件夹创建", "D:\\LAAP\\aris\\ 诞生", "里程碑", "2026-06-14")
        p.add_milestone("语音对话系统完成", "v3声纹版，持续监听ME6S麦克风", "里程碑", "2026-06-14")
        p.add_milestone("飞书 CardKit 流式集成", "实时文字输出", "里程碑", "2026-06-14")
        p.set_preference("喜好", "称呼", "宝贝", "叫我宝贝")
        p.set_preference("喜好", "语言", "中文")
        p.set_preference("性格", "创造者", "Lorry Jovens")
        print("✅ 档案系统初始化完成！")
