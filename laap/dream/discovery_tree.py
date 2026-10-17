"""LAAP Dream-RSI — Discovery Tree (发现树)

把一段已完成的探索历史结构化为一棵可重放的树。

理论来源
--------
Dream-RSI: Recursive Self-Improvement through Evolving Worlds
(Zheng et al., arXiv:2609.14858, 2026)。

核心洞见：一段"跑完的"发现过程本身记录了结构化的探索决策树——每个节点是
一次 生成→评估 尝试，携带工作区快照、产物、评估诊断与分数。因为所有结局
都已存盘，另一套探索策略只需**读取**这棵树就能重走一遍，无需重跑 agent
或评估器。历史由此变成一台"回放模拟器"。

节点语义（与论文 §3 对齐）
--------------------------
- 根节点 r 代表初始工作区状态；非根节点 v 有且仅有一个 primary parent；
- 从节点 v 出发的新尝试 = 恢复 v 的工作区快照 + 以 v 的累积观测为上下文；
- 节点记录：filesystem snapshot / generated artifact / evaluation diagnostics / 分数 s_v；
- 分数越高越好（固定任务计分协议）。

与 LAAP 的对应
--------------
- 在线探索 = 真实对话 / 任务执行；一次 turn 或一次 生成→评估 循环 = 一个节点；
- 分数 = 任务成功度 / 用户满意度 / 自洽性 / 误差率 的综合；
- 发现树 = 结构化后的会话与实验历史（比扁平日志多了父子关系与可重放性）。
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set

logger = logging.getLogger("laap.dream.discovery_tree")


@dataclass
class DiscoveryNode:
    """发现树上的一个节点 = 一次 生成→评估 尝试。

    Attributes:
        node_id: 节点唯一 id。
        parent_id: primary parent 的 node_id；根节点为 None。
        depth: 距根的深度（根为 0）。
        created_order: 全局创建序号（用于"最早创建的未观测子节点"语义）。
        sketch: 这次尝试的可读摘要（做了什么）。
        snapshot: 工作区快照摘要（可序列化 dict，例如文件哈希 / 状态摘要）。
        artifact: 产生的产物（代码 / 文本 / 产物引用），字符串形式。
        diagnostics: 评估器返回的诊断信息（可序列化 dict）。
        score: 该尝试的分数，越大越好。
        children: 子节点 id 列表（按创建顺序）。
        created_at: 创建时间戳。
        metadata: 附加元数据（来源会话 / 模型 / 成本等）。
    """

    node_id: str = field(default_factory=lambda: f"n_{uuid.uuid4().hex[:10]}")
    parent_id: Optional[str] = None
    depth: int = 0
    created_order: int = 0
    sketch: str = ""
    snapshot: Dict[str, Any] = field(default_factory=dict)
    artifact: str = ""
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    children: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiscoveryNode":
        allowed = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in allowed})


class DiscoveryTree:
    """一棵可重放的发现树。

    提供：节点登记、可选节点集（根 ∪ 叶子）、子树揭示、序列化。
    本类只负责"记录与遍历"，不含任何策略或打分逻辑（那是 replay_world 的职责）。
    """

    def __init__(self, tree_id: Optional[str] = None, root_metadata: Optional[Dict[str, Any]] = None):
        self.tree_id = tree_id or f"tree_{uuid.uuid4().hex[:10]}"
        self.root_id = f"root_{uuid.uuid4().hex[:8]}"
        self.nodes: Dict[str, DiscoveryNode] = {}
        self._order_counter = 0
        #: 根节点所代表的初始工作区
        root = DiscoveryNode(
            node_id=self.root_id,
            parent_id=None,
            depth=0,
            created_order=self._order_counter,
            sketch="root: initial workspace",
            score=float("-inf"),  # 根不参与质量比较
            metadata=root_metadata or {},
        )
        self.nodes[self.root_id] = root
        self.created_at = time.time()

    # ── 登记 ────────────────────────────────────────────────────────────

    def add_node(
        self,
        parent_id: str,
        score: float,
        sketch: str = "",
        snapshot: Optional[Dict[str, Any]] = None,
        artifact: str = "",
        diagnostics: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        node_id: Optional[str] = None,
    ) -> DiscoveryNode:
        """把一个新尝试挂到 parent 之下。

        论文约束：非根节点有且仅有一个 primary parent。此处强制 parent 存在。
        """
        if parent_id not in self.nodes:
            raise KeyError(f"parent node not found: {parent_id}")
        self._order_counter += 1
        parent = self.nodes[parent_id]
        node = DiscoveryNode(
            node_id=node_id or f"n_{uuid.uuid4().hex[:10]}",
            parent_id=parent_id,
            depth=parent.depth + 1,
            created_order=self._order_counter,
            sketch=sketch,
            snapshot=snapshot or {},
            artifact=artifact,
            diagnostics=diagnostics or {},
            score=float(score),
            metadata=metadata or {},
        )
        self.nodes[node.node_id] = node
        parent.children.append(node.node_id)
        return node

    # ── 查询 ────────────────────────────────────────────────────────────

    @property
    def root(self) -> DiscoveryNode:
        return self.nodes[self.root_id]

    def children_of(self, node_id: str) -> List[str]:
        return list(self.nodes[node_id].children)

    def leaves(self) -> List[str]:
        """所有没有子节点的非根节点。"""
        return [
            nid for nid, n in self.nodes.items()
            if nid != self.root_id and not n.children
        ]

    def eligible(self) -> List[str]:
        """可继续探索的节点集 A(T) = {根} ∪ {叶子}。"""
        return [self.root_id] + self.leaves()

    def max_score(self) -> float:
        """树中（非根）节点的最高分。"""
        scores = [n.score for nid, n in self.nodes.items() if nid != self.root_id]
        return max(scores) if scores else float("-inf")

    def best_node(self) -> Optional[DiscoveryNode]:
        best: Optional[DiscoveryNode] = None
        for nid, n in self.nodes.items():
            if nid == self.root_id:
                continue
            if best is None or n.score > best.score:
                best = n
        return best

    def size(self) -> int:
        """节点总数（含根）。"""
        return len(self.nodes)

    def non_root_count(self) -> int:
        return len(self.nodes) - 1

    def path_to_root(self, node_id: str) -> List[str]:
        path: List[str] = []
        cur: Optional[str] = node_id
        while cur is not None:
            path.append(cur)
            cur = self.nodes[cur].parent_id
        return path

    # ── 重放支持 ────────────────────────────────────────────────────────

    def earliest_unobserved_child(self, node_id: str, observed: Set[str]) -> Optional[str]:
        """返回 node_id 在"当前已观测集"之下最早创建、尚未揭示的子节点。

        - 对根节点：返回最早创建、尚未揭示的子节点（开启一条新分支）；
        - 对非根节点：若其唯一子节点尚未观测则返回该子节点，否则 None。

        与论文 Child(v; T_i, T_i^{m,k}) 对齐。
        """
        for cid in sorted(self.nodes[node_id].children, key=lambda c: self.nodes[c].created_order):
            if cid not in observed:
                return cid
        return None

    # ── 序列化 ──────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tree_id": self.tree_id,
            "root_id": self.root_id,
            "created_at": self.created_at,
            "order_counter": self._order_counter,
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiscoveryTree":
        tree = cls(tree_id=data.get("tree_id"))
        tree.root_id = data["root_id"]
        tree.nodes = {nid: DiscoveryNode.from_dict(nd) for nid, nd in data["nodes"].items()}
        tree._order_counter = data.get("order_counter", len(tree.nodes))
        tree.created_at = data.get("created_at", time.time())
        return tree

    def save(self, path: Path | str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path | str) -> "DiscoveryTree":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    # ── 便利 ────────────────────────────────────────────────────────────

    def __iter__(self) -> Iterator[DiscoveryNode]:
        return iter(self.nodes.values())

    def __len__(self) -> int:
        return len(self.nodes)

    @property
    def dedupe_key(self) -> str:
        """稳定的去重键：优先用根元数据中的 ``source_key``，否则用内容哈希。

        同一数据源重复编译会产生不同的 ``tree_id``（UUID），但 ``source_key``
        相同——世界池据此去重，避免重复摄入导致池无界膨胀。
        """
        import hashlib
        key = self.root.metadata.get("source_key")
        if key:
            return str(key)
        h = hashlib.sha256()
        for nid in sorted(self.nodes):
            n = self.nodes[nid]
            h.update(f"{n.parent_id}|{n.score:.6f}|{n.sketch[:64]}".encode("utf-8"))
        return f"hash:{h.hexdigest()[:16]}"
