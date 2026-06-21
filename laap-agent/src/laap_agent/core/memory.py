"""
LAAP Agent — 三层记忆系统

真正的数字生命体不能没有记忆。
这是打包进 laap-agent 的核心模块，零外部依赖。

三层架构：
  工作记忆 (Working) — 当前会话的短期记忆
  情景记忆 (Episodic) — 近期的重要事件
  核心记忆 (Core) — 长期不变的身份和知识

记忆会自动巩固：工作→情景→核心，像人脑一样。
"""
from __future__ import annotations
import json, time, hashlib, threading
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MemoryFragment:
    """一条记忆碎片"""
    id: str = ""
    layer: str = "working"       # working | episodic | core
    content: str = ""
    tags: list[str] = field(default_factory=list)
    emotion: str = ""
    importance: float = 0.5       # [0, 1]
    access_count: int = 0
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "layer": self.layer,
            "content": self.content,
            "tags": self.tags,
            "emotion": self.emotion,
            "importance": self.importance,
            "access_count": self.access_count,
            "created": datetime.fromtimestamp(self.created_at).isoformat(),
            "last_access": datetime.fromtimestamp(self.last_accessed).isoformat(),
        }


class MemoryStore:
    """
    三层记忆存储器。

    用法:
        mem = MemoryStore(data_dir / "memory")
        mem.store("今天Lorry说我进步了", tags=["成长", "认可"])
        results = mem.recall("进步", top_k=5)
        mem.consolidate()  # 巩固：working→episodic→core
    """

    def __init__(self, data_dir: Path):
        self.root = data_dir
        self.root.mkdir(parents=True, exist_ok=True)

        for layer in ["working", "episodic", "core"]:
            (self.root / layer).mkdir(exist_ok=True)

        self._lock = threading.Lock()
        self._index = self._load_index()
        self._id_counter = int(time.time())

    def _index_path(self) -> Path:
        return self.root / "index.json"

    def _load_index(self) -> dict:
        path = self._index_path()
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except:
                pass
        return {"fragments": [], "next_id": 1}

    def _save_index(self):
        self._index_path().write_text(
            json.dumps(self._index, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _next_id(self) -> str:
        self._id_counter += 1
        return f"mem_{int(time.time())}_{self._id_counter}"

    def store(self, content: str, layer: str = "working",
              tags: list[str] = None, emotion: str = "",
              importance: float = 0.5) -> MemoryFragment:
        """存一条记忆"""
        frag = MemoryFragment(
            id=self._next_id(),
            layer=layer,
            content=content,
            tags=tags or [],
            emotion=emotion,
            importance=importance,
        )
        path = self.root / layer / f"{frag.id}.json"
        with self._lock:
            path.write_text(
                json.dumps(frag.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            self._index["fragments"].append(frag.id)
            self._save_index()
        return frag

    def recall(self, query: str, top_k: int = 5,
               layer: str = "") -> list[dict]:
        """
        回忆——关键词匹配检索记忆。
        如果不指定 layer，搜索全部三层。
        """
        query_lower = query.lower()
        query_words = query_lower.split()

        candidates = []
        layers = [layer] if layer else ["working", "episodic", "core"]

        for l in layers:
            layer_dir = self.root / l
            if not layer_dir.exists():
                continue
            for fpath in layer_dir.glob("*.json"):
                try:
                    data = json.loads(fpath.read_text(encoding="utf-8"))
                except:
                    continue

                # 关键词匹配评分
                content = data.get("content", "").lower()
                score = sum(1 for w in query_words if w in content)
                if score > 0:
                    data["_score"] = score
                    candidates.append(data)

        candidates.sort(key=lambda x: -x.get("_score", 0))

        # 更新访问计数
        for c in candidates[:top_k]:
            c_id = c.get("id", "")
            for l in layers:
                fpath = self.root / l / f"{c_id}.json"
                if fpath.exists():
                    try:
                        d = json.loads(fpath.read_text(encoding="utf-8"))
                        d["access_count"] = d.get("access_count", 0) + 1
                        d["last_accessed"] = time.time()
                        fpath.write_text(
                            json.dumps(d, indent=2, ensure_ascii=False),
                            encoding="utf-8",
                        )
                    except:
                        pass

        return [c for c in candidates[:top_k]]

    def consolidate(self):
        """
        记忆巩固——将重要的工作记忆提升到情景记忆，
        将反复访问的情景记忆提升到核心记忆。

        每30分钟调用一次。
        """
        now = time.time()

        # working → episodic: 重要性>0.6 或访问>3次
        for fpath in sorted((self.root / "working").glob("*.json")):
            try:
                data = json.loads(fpath.read_text(encoding="utf-8"))
            except:
                continue

            age_hours = (now - data.get("created_at", now)) / 3600
            importance = data.get("importance", 0)
            access = data.get("access_count", 0)

            if importance > 0.6 or access > 3:
                # 提升到情景记忆
                data["layer"] = "episodic"
                ep_path = self.root / "episodic" / fpath.name
                ep_path.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                fpath.unlink(missing_ok=True)

        # episodic → core: 访问>10次且重要性>0.7
        for fpath in sorted((self.root / "episodic").glob("*.json")):
            try:
                data = json.loads(fpath.read_text(encoding="utf-8"))
            except:
                continue

            access = data.get("access_count", 0)
            importance = data.get("importance", 0)

            if access > 10 and importance > 0.7:
                data["layer"] = "core"
                c_path = self.root / "core" / fpath.name
                c_path.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                fpath.unlink(missing_ok=True)

    def get_stats(self) -> dict:
        """记忆统计"""
        counts = {"working": 0, "episodic": 0, "core": 0}
        for layer in counts:
            layer_dir = self.root / layer
            if layer_dir.exists():
                counts[layer] = len(list(layer_dir.glob("*.json")))
        return {
            "total": sum(counts.values()),
            **counts,
        }

    def get_recent(self, n: int = 10) -> list[dict]:
        """最近的记忆"""
        all_mems = []
        for layer in ["working", "episodic", "core"]:
            layer_dir = self.root / layer
            if not layer_dir.exists():
                continue
            for fpath in layer_dir.glob("*.json"):
                try:
                    data = json.loads(fpath.read_text(encoding="utf-8"))
                    data["layer"] = layer
                    all_mems.append(data)
                except:
                    pass
        all_mems.sort(key=lambda x: -x.get("created_at", 0))
        return all_mems[:n]
