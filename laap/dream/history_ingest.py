"""LAAP Dream-RSI — History Ingest (历史编译：把真实记录编译成发现树)

Dream-RSI 的燃料是"已完成的发现历史"。本模块把 LAAP / Aris 的真实记录编译成
``DiscoveryTree``，让回放世界有据可依。

支持三种输入源
--------------
1. **通用 JSONL 轨迹**：每行一条尝试记录（时间戳/输入/动作/结局/分数），
   按 ``parent_id`` 或时间顺序组装为树；
2. **经验库（Experience Library）**：LAAP 的 experience 记录；
3. **预测账本（Prediction Ledger）**：把 PROPOSE→PREDICT→VERIFY 记录
   编译为"每次改进尝试"的树，分数 = 预测是否被证实的收益。

设计原则
--------
- 尽力而为：字段缺失不报错，缺分数按 0 计，缺父子关系按"顺序链"或"根直挂"；
- 无副作用：只读输入、只产出发现树，不修改任何源数据；
- 可审计：编译时记录来源路径与记录数。
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from laap.dream.discovery_tree import DiscoveryTree

logger = logging.getLogger("laap.dream.history_ingest")


@dataclass
class IngestResult:
    """一次历史编译的结果。"""

    source: str = ""
    records: int = 0
    trees: int = 0
    skipped: int = 0
    tree_ids: List[str] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.tree_ids is None:
            self.tree_ids = []

    def to_dict(self) -> Dict[str, Any]:
        return {"source": self.source, "records": self.records,
                "trees": self.trees, "skipped": self.skipped,
                "tree_ids": self.tree_ids}


# ── 通用轨迹 → 发现树 ──────────────────────────────────────────────────

def compile_traces(
    traces: Iterable[Dict[str, Any]],
    *,
    score_key: str = "score",
    parent_key: str = "parent_id",
    id_key: str = "id",
    sketch_key: str = "sketch",
    artifact_key: str = "artifact",
    diagnostics_key: str = "diagnostics",
    source: str = "traces",
    group_key: str = "session_id",
) -> List[DiscoveryTree]:
    """把一组尝试记录编译为若干发现树。

    Args:
        traces: 尝试记录（dict 列表）。
        score_key: 分数字段名。
        parent_key: 父节点字段名（值为源记录的 id）。缺失时按 group 内顺序链挂载。
        id_key: 源记录 id 字段名。
        group_key: 分组字段名（每个 group 一棵树）；缺失则单树。

    Returns:
        DiscoveryTree 列表。
    """
    # 按 group 分桶
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for rec in traces:
        g = str(rec.get(group_key, "__single__"))
        buckets.setdefault(g, []).append(rec)

    trees: List[DiscoveryTree] = []
    for g, recs in buckets.items():
        tree = DiscoveryTree(root_metadata={"source": source, "group": g,
                                             "source_key": f"traces:{source}:{g}"})
        # 源 id -> 树节点 id
        id_map: Dict[str, str] = {}
        prev_node: Optional[str] = None

        for rec in recs:
            src_id = str(rec.get(id_key, ""))
            parent_src = rec.get(parent_key)
            if parent_src is not None and str(parent_src) in id_map:
                parent_node = id_map[str(parent_src)]
            elif parent_src is None and prev_node is not None:
                # 顺序链（把缺失父子关系退化为"上一条的延续"）
                parent_node = prev_node
            else:
                parent_node = tree.root_id

            node = tree.add_node(
                parent_id=parent_node,
                score=float(rec.get(score_key, 0.0) or 0.0),
                sketch=str(rec.get(sketch_key, ""))[:500],
                snapshot=rec.get("snapshot") or {},
                artifact=str(rec.get(artifact_key, ""))[:2000],
                diagnostics=rec.get(diagnostics_key) or {},
                metadata=rec.get("metadata") or {},
            )
            if src_id:
                id_map[src_id] = node.node_id
            prev_node = node.node_id

        trees.append(tree)
    return trees


# ── JSONL 文件 → 发现树 ────────────────────────────────────────────────

def compile_jsonl(path: str | Path, **kwargs) -> List[DiscoveryTree]:
    """从 JSONL 轨迹文件编译发现树。"""
    p = Path(path).expanduser()
    if not p.exists():
        logger.warning("trace file not found: %s", p)
        return []
    records: List[Dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    kwargs.setdefault("source", str(p))
    return compile_traces(records, **kwargs)


# ── 预测账本 → 发现树 ──────────────────────────────────────────────────

def compile_prediction_ledger(ledger_path: str | Path,
                              group_key: str = "target_component") -> Tuple[IngestResult, List[DiscoveryTree]]:
    """把预测账本（predictions.jsonl）编译为发现树。

    每条预测 = 一次"改进尝试"；分数定义：
        VERIFIED  → 相对基线的改善幅度（方向敏感）
        FALSIFIED → 0
        PREDICTED / EXPIRED → 0（尚未证实）

    同一 target_component 的多次改进按时间顺序链成一棵树（改进的谱系）。
    """
    p = Path(ledger_path).expanduser()
    res = IngestResult(source=str(p))
    if not p.exists():
        return res

    records: List[Dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                res.skipped += 1
                continue
            records.append(rec)
            res.records += 1

    # 计算分数
    traces: List[Dict[str, Any]] = []
    for rec in records:
        status = str(rec.get("status", ""))
        base = rec.get("baseline_value")
        actual = rec.get("actual_value")
        score = 0.0
        if status == "verified" and base is not None and actual is not None:
            delta = float(actual) - float(base)
            direction = rec.get("direction", "up")
            score = delta if direction == "up" else -delta
            score = max(0.0, score)
        traces.append({
            "id": rec.get("record_id", ""),
            "parent_id": None,  # 顺序链
            "session_id": str(rec.get(group_key, "ledger")),
            "score": score,
            "sketch": str(rec.get("claim", ""))[:200],
            "artifact": str(rec.get("evidence_path", "")),
            "diagnostics": {"status": status, "metric": rec.get("metric", ""),
                            "verdict_reason": rec.get("verdict_reason", "")},
            "metadata": {"proposal_id": rec.get("proposal_id", ""),
                         "target_component": rec.get(group_key, "")},
        })

    trees = compile_traces(traces, parent_key="parent_id", source=str(p),
                           group_key="session_id")
    res.trees = len(trees)
    res.tree_ids = [t.tree_id for t in trees]
    return res, trees


# ── 经验进化日志（evolution.jsonl）→ 发现树 ─────────────────────────

def compile_evolution_log(path: str | Path,
                          group_key: str = "project") -> Tuple[IngestResult, List[DiscoveryTree]]:
    """把 ``~/.laap/evolution.jsonl`` 编译为发现树。

    每条记录是一次"任务经验凝固"：``task`` / ``capabilities`` / ``methods`` /
    ``aesthetic`` / ``tools`` / ``lessons`` / ``project`` / ``confidence``。

    编译规则：
      - 一个 ``project`` 一棵树，记录按时间顺序链成改进谱系；
      - 分数 = ``confidence``（对这次经验的确信度）；
      - ``lessons`` 拼接为 sketch；``tools``/``methods`` 进 artifact。

    Returns:
        (IngestResult, List[DiscoveryTree])。
    """
    p = Path(path).expanduser()
    res = IngestResult(source=str(p))
    if not p.exists():
        return res, []

    buckets: Dict[str, List[Dict[str, Any]]] = {}
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                res.skipped += 1
                continue
            res.records += 1
            g = str(rec.get(group_key, "unassigned"))
            buckets.setdefault(g, []).append(rec)

    trees: List[DiscoveryTree] = []
    for g, recs in buckets.items():
        recs.sort(key=lambda r: float(r.get("timestamp", 0.0)))
        tree = DiscoveryTree(root_metadata={"source": str(p), "project": g,
                                             "source_key": f"evolution:{g}"})
        prev: Optional[str] = None
        for rec in recs:
            lessons = rec.get("lessons") or []
            sketch = "; ".join(str(x) for x in lessons)[:500] or str(rec.get("task", ""))[:200]
            artifact = "; ".join(
                [str(x) for x in (rec.get("tools") or [])] +
                [str(x) for x in (rec.get("methods") or [])]
            )[:2000]
            node = tree.add_node(
                parent_id=prev or tree.root_id,
                score=float(rec.get("confidence", 0.0) or 0.0),
                sketch=sketch,
                artifact=artifact,
                diagnostics={"capabilities": rec.get("capabilities") or [],
                             "aesthetic": rec.get("aesthetic") or []},
                metadata={"task": rec.get("task", ""),
                          "timestamp": rec.get("timestamp", 0.0)},
            )
            prev = node.node_id
        trees.append(tree)

    res.trees = len(trees)
    res.tree_ids = [t.tree_id for t in trees]
    return res, trees


# ── 统一入口 ────────────────────────────────────────────────────────────

def ingest_all(
    trace_paths: Optional[List[str]] = None,
    ledger_path: Optional[str] = None,
    evolution_path: Optional[str] = None,
) -> Dict[str, Any]:
    """编译所有可用的历史源，返回发现树集合与报告。

    默认路径（若存在）：
        - ``~/.laap/evolution.jsonl``（经验进化日志）
        - ``~/.laap/true_rsi/predictions.jsonl``（预测账本）
    """
    trees: List[DiscoveryTree] = []
    report: Dict[str, Any] = {"sources": []}

    for tp in (trace_paths or []):
        got = compile_jsonl(tp)
        trees.extend(got)
        report["sources"].append({"path": tp, "trees": len(got)})

    # 经验进化日志
    ep = evolution_path or os.path.expanduser("~/.laap/evolution.jsonl")
    if Path(ep).expanduser().exists():
        res, got = compile_evolution_log(ep)
        trees.extend(got)
        report["sources"].append(res.to_dict())

    lp = ledger_path or os.path.expanduser("~/.laap/true_rsi/predictions.jsonl")
    if Path(lp).expanduser().exists():
        res, got = compile_prediction_ledger(lp)
        trees.extend(got)
        report["sources"].append(res.to_dict())

    report["total_trees"] = len(trees)
    report["total_nodes"] = sum(t.size() for t in trees)
    return {"trees": trees, "report": report}
