"""LAAP Dream-RSI — Real Sources (真实数据源编译器)

把 LAAP / Aris 的**真实**记录编译成发现树，为回放世界池注入燃料。

数据源（按结构价值排序）
------------------------
1. ``~/.laap/rsi_v2/journal.jsonl``
   RSI v2 held-out 验证日志：每个候选是对同一 spec 的**替代尝试**，
   带 baseline / heldout 分数 → 天然的「替代方案分叉」结构。
2. ``~/.laap/gui_rsi/audit.jsonl``
   GUI 设计 token 改进提案：root → target → 多个提案。
3. ``~/.laap/evolution_pipeline/pipeline_state.json``
   已发布/采纳/拒绝的进化记录：fitness_improvement 即分数。
4. ``D:\\LAAP\\aris_brain\\memory\\archive\\conversations.db``
   真实对话（每轮带 cycle/emotion/focus/domain）→ 会话树。
5. ``~/.laap/long_term.db`` / ``memory.db``
   长期记忆与记忆（带 importance/confidence）→ 记忆树。

设计原则
--------
- 只读：绝不修改任何源数据；
- 尽力而为：字段缺失降级，不报错；
- 可审计：记录来源与记录数；
- 隐私：编译器**只在本地**运行，产出留在本地世界池，不随联邦出境。
"""

from __future__ import annotations
from laap.config.paths import get_laap_root  # noqa: E402  [dehardcode]

import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from laap.dream.discovery_tree import DiscoveryTree

logger = logging.getLogger("laap.dream.sources")

HOME = Path(os.path.expanduser("~"))


# ── 工具 ────────────────────────────────────────────────────────────────

def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not path.exists():
        return out
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _open_ro(path: Path) -> Optional[sqlite3.Connection]:
    if not path.exists():
        return None
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        return con
    except Exception as exc:  # noqa: BLE001
        logger.debug("open sqlite %s failed: %s", path, exc)
        return None


# ── 1. RSI v2 journal ───────────────────────────────────────────────────

def compile_rsi_journal(path: Optional[str] = None) -> List[DiscoveryTree]:
    """把 RSI v2 held-out 日志编译为发现树。

    结构：root → spec（分支） → 每个候选（该 spec 下的替代尝试）。
    分数 = heldout − baseline（改进幅度，负值表示退化）。
    """
    p = Path(path) if path else HOME / ".laap" / "rsi_v2" / "journal.jsonl"
    records = _read_jsonl(p)
    if not records:
        return []

    # 按 spec 分桶
    by_spec: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        if r.get("type") != "heldout":
            continue
        spec = str(r.get("spec", "unknown"))
        by_spec.setdefault(spec, []).append(r)

    trees: List[DiscoveryTree] = []
    for spec, recs in by_spec.items():
        tree = DiscoveryTree(root_metadata={"source": str(p), "spec": spec,
                                             "source_key": f"rsi_v2:{spec}"})
        # 为每个 spec 建一个"目标节点"，再挂各候选为兄弟分支
        target = tree.add_node(
            parent_id=tree.root_id, score=0.0,
            sketch=f"target: {spec}",
            metadata={"kind": "target", "spec": spec})
        for r in recs:
            base = float(r.get("baseline", 0.0) or 0.0)
            held = float(r.get("heldout", 0.0) or 0.0)
            decision = r.get("decision") or {}
            accepted = bool(decision.get("accepted", False))
            tree.add_node(
                parent_id=target.node_id,
                score=held - base,
                sketch=f"candidate {r.get('candidate_id', '?')} "
                       f"({'accepted' if accepted else 'rejected'})",
                artifact=json.dumps(r.get("decision", {}), ensure_ascii=False)[:800],
                diagnostics={"baseline": base, "heldout": held,
                             "reason": decision.get("reason", ""),
                             "violated": decision.get("violated", [])},
                metadata={"kind": "candidate",
                          "candidate_id": r.get("candidate_id", ""),
                          "ts": r.get("ts", 0.0)})
        trees.append(tree)
    return trees


# ── 2. GUI RSI audit ────────────────────────────────────────────────────

def compile_gui_rsi(path: Optional[str] = None) -> List[DiscoveryTree]:
    """把 GUI RSI 提案日志编译为发现树。

    结构：root → target（分支） → 提案（替代尝试）。
    分数：verdict 映射（suggest_adopt=1, reject=0）。同一 token 的多次提案形成分支。
    """
    p = Path(path) if path else HOME / ".laap" / "gui_rsi" / "audit.jsonl"
    records = _read_jsonl(p)
    if not records:
        return []

    by_target: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        payload = r.get("payload") or {}
        atom = payload.get("atom") or {}
        target = str(atom.get("target", r.get("candidate_id", "unknown")))
        by_target.setdefault(target, []).append(r)

    verdict_score = {"suggest_adopt": 1.0, "reject": 0.0, "archive": 0.2,
                     "adopt": 1.0}
    trees: List[DiscoveryTree] = []
    for target, recs in by_target.items():
        tree = DiscoveryTree(root_metadata={"source": str(p), "target": target,
                                             "source_key": f"gui_rsi:{target}"})
        for r in recs:
            payload = r.get("payload") or {}
            atom = payload.get("atom") or {}
            tree.add_node(
                parent_id=tree.root_id,
                score=verdict_score.get(str(r.get("verdict", "")), 0.3),
                sketch=str(atom.get("description", ""))[:200],
                artifact=json.dumps(atom.get("params", {}), ensure_ascii=False)[:500],
                diagnostics={"event": r.get("event", ""),
                             "verdict": r.get("verdict", ""),
                             "op": atom.get("op", "")},
                metadata={"candidate_id": r.get("candidate_id", ""),
                          "ts": r.get("timestamp", 0.0)})
        trees.append(tree)
    return trees


# ── 3. Evolution pipeline ───────────────────────────────────────────────

def compile_evolution_pipeline(path: Optional[str] = None) -> List[DiscoveryTree]:
    """把进化管线状态编译为发现树。

    结构：root → target_file（分支） → 各进化（分数 = fitness_improvement）。
    """
    p = Path(path) if path else HOME / ".laap" / "evolution_pipeline" / "pipeline_state.json"
    if not p.exists():
        return []
    try:
        state = json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []

    ads = state.get("published_ads") or []
    by_target: Dict[str, List[Dict[str, Any]]] = {}
    for a in ads:
        t = str(a.get("target_file", "unknown"))
        by_target.setdefault(t, []).append(a)

    trees: List[DiscoveryTree] = []
    for target, items in by_target.items():
        tree = DiscoveryTree(root_metadata={"source": str(p), "target_file": target,
                                             "source_key": f"evol:{target}"})
        for a in items:
            tree.add_node(
                parent_id=tree.root_id,
                score=float(a.get("fitness_improvement", 0.0) or 0.0),
                sketch=f"evolution {a.get('evolution_id', '?')} by {a.get('source_agent', '?')}",
                artifact=str(a.get("diff_summary", ""))[:500],
                diagnostics={"safety_verified": a.get("safety_verified", False),
                             "charter_compliant": a.get("charter_compliant", False)},
                metadata={"evolution_id": a.get("evolution_id", ""),
                          "ts": a.get("timestamp", 0.0)})
        trees.append(tree)
    return trees


# ── 4. Conversations（真实对话）─────────────────────────────────────────

#: 情感 → 效价
_EMOTION_VALENCE = {
    "joy": 1.0, "gratitude": 0.9, "tenderness": 0.8, "curiosity": 0.6,
    "calm": 0.5, "longing": -0.2, "sadness": -0.6, "anxiety": -0.7,
    "neutral": 0.1,
}


def compile_conversations(db_path: Optional[str] = None,
                          max_sessions: int = 60) -> List[DiscoveryTree]:
    """把真实对话编译为会话树。

    结构：root → 每轮一个节点（对话链）。
    分数（合成信号，刻意保守）：
        score = 情感效价 + 0.5 × 是否被回应延续 + 0.2 × 长度归一
    这是 Aris 对交互的**自身反馈**，而非任何外部标签。

    注意：对话是线性链，回放无法分叉——它们提供的是**真实深度与量**，
    分叉结构由 RSI/进化源提供。
    """
    p = Path(db_path) if db_path else Path(
        str(get_laap_root() / "aris_brain" / "memory" / "archive" / "conversations.db"))
    con = _open_ro(p)
    if con is None:
        return []
    trees: List[DiscoveryTree] = []
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT session_id, role, content, cycle_number, emotion, focus, "
            "domain, timestamp FROM conversations ORDER BY timestamp")
        rows = [dict(r) for r in cur.fetchall()]
    except Exception as exc:  # noqa: BLE001
        logger.debug("query conversations failed: %s", exc)
        con.close()
        return []
    con.close()

    by_session: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        by_session.setdefault(str(r.get("session_id", "unknown")), []).append(r)

    # 只取最大的若干会话（避免世界池被碎片淹没）
    sessions = sorted(by_session.items(), key=lambda kv: -len(kv[1]))[:max_sessions]

    for sid, recs in sessions:
        if len(recs) < 2:
            continue
        tree = DiscoveryTree(root_metadata={"source": str(p), "session_id": sid,
                                             "source_key": f"conv:{sid}"})
        for i, r in enumerate(recs):
            emotion = str(r.get("emotion", "neutral"))
            valence = _EMOTION_VALENCE.get(emotion, 0.0)
            continued = 1.0 if i < len(recs) - 1 else 0.0
            length_norm = min(1.0, len(str(r.get("content", ""))) / 200.0)
            score = valence + 0.5 * continued + 0.2 * length_norm
            tree.add_node(
                parent_id=tree.root_id,
                score=score,
                sketch=f"[{r.get('role', '?')}] cyc={r.get('cycle_number', 0)} "
                       f"{emotion}",
                artifact=str(r.get("content", ""))[:1000],
                diagnostics={"emotion": emotion, "focus": r.get("focus", ""),
                             "domain": r.get("domain", ""),
                             "role": r.get("role", "")},
                metadata={"cycle_number": r.get("cycle_number", 0),
                          "ts": r.get("timestamp", 0.0)})
        trees.append(tree)
    return trees


# ── 5. Memory stores ────────────────────────────────────────────────────

def compile_memory_store(db_path: Optional[str] = None,
                         group: str = "type") -> List[DiscoveryTree]:
    """把记忆库（long_term.db / memory.db）编译为发现树。

    结构：root → type（分支） → 各记忆（分数 = importance × confidence）。
    """
    p = Path(db_path) if db_path else HOME / ".laap" / "long_term.db"
    con = _open_ro(p)
    if con is None:
        return []
    try:
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cur.fetchall()}
        table = "long_term_memories" if "long_term_memories" in tables else (
            "memories" if "memories" in tables else None)
        if table is None:
            con.close()
            return []
        cur.execute(f"SELECT * FROM {table}")
        rows = [dict(r) for r in cur.fetchall()]
    except Exception as exc:  # noqa: BLE001
        logger.debug("query %s failed: %s", p, exc)
        con.close()
        return []
    con.close()

    by_group: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        by_group.setdefault(str(r.get(group, "unknown")), []).append(r)

    trees: List[DiscoveryTree] = []
    for g, recs in by_group.items():
        tree = DiscoveryTree(root_metadata={"source": str(p), "group": g,
                                             "source_key": f"mem:{p.name}:{g}"})
        for r in recs:
            imp = float(r.get("importance", 0.0) or 0.0)
            conf = float(r.get("confidence", 1.0) or 1.0)
            tree.add_node(
                parent_id=tree.root_id,
                score=imp * conf,
                sketch=str(r.get("title") or str(r.get("content", ""))[:120]),
                artifact=str(r.get("content", ""))[:800],
                diagnostics={"type": r.get("type", ""),
                             "tags": r.get("tags", ""),
                             "emotional_valence": r.get("emotional_valence", 0.0)},
                metadata={"source": r.get("source", ""),
                          "created_at": r.get("created_at", 0.0)})
        trees.append(tree)
    return trees


# ── 统一入口 ────────────────────────────────────────────────────────────

def ingest_real_sources(include_conversations: bool = True,
                        include_memories: bool = True,
                        max_sessions: int = 60) -> Dict[str, Any]:
    """编译全部真实数据源，返回发现树与逐源报告。"""
    trees: List[DiscoveryTree] = []
    report: List[Dict[str, Any]] = []

    def _add(name: str, got: List[DiscoveryTree]):
        if got:
            trees.extend(got)
            report.append({"source": name, "trees": len(got),
                           "nodes": sum(t.size() for t in got)})

    _add("rsi_v2_journal", compile_rsi_journal())
    _add("gui_rsi_audit", compile_gui_rsi())
    _add("evolution_pipeline", compile_evolution_pipeline())

    if include_conversations:
        _add("conversations", compile_conversations(max_sessions=max_sessions))

    if include_memories:
        _add("long_term_memory", compile_memory_store(
            str(HOME / ".laap" / "long_term.db")))
        _add("memory_db", compile_memory_store(
            str(HOME / ".laap" / "memory.db")))

    return {
        "trees": trees,
        "report": {
            "sources": report,
            "total_trees": len(trees),
            "total_nodes": sum(t.size() for t in trees),
        },
    }
