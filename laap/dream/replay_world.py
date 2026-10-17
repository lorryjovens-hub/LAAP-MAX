"""LAAP Dream-RSI — Replay World (回放世界 / 回放模拟器)

把一棵已完成的发现树冻结成一台**可重放的模拟器**：另一套探索策略在这棵树上
"重走"一遍——选择不同的分支子集、不同的顺序、不同的并行分组与不同的停止点。
因为所有结局都已存盘，重走只需读取记录，无需重跑底层 agent 与评估器。

理论来源
--------
Dream-RSI (Zheng et al., arXiv:2609.14858, 2026) §3 "Offline evaluation" 与
"Replay objective"。

回放打分（论文式 1）
----------------------
    V = max_{v∈已揭示} s_v          # 发现质量
        - β1 · N                    # 执行成本（N = 已揭示的非根节点数）
        + β2 · N / max(1, k)        # 并行奖励（每轮平均尝试数，k = 完成轮数）

终止条件：策略选择空批次 / 达到轮上限 K2 / 已揭示全部记录节点。

关键约束
--------
- 回放**只能**重排、剪枝、改并行与停止点，**不能**凭空得知未探索区域的结果；
- 某个方向若历史里只记录了一条延续，则无论策略如何，都只能揭示这一条；
- 根节点每次被选中，揭示"最早创建、尚未揭示"的子节点（开启一条新分支）。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set

from laap.dream.discovery_tree import DiscoveryTree, DiscoveryNode

logger = logging.getLogger("laap.dream.replay_world")


class ObservedView:
    """只暴露"已揭示"节点的只读视图，供策略做决策。

    在线执行时 observed = 全部节点（即完整树）；回放时 observed 随揭示逐步增长。
    策略只通过本视图观察世界，从而保证"回放不泄露未揭示信息"。
    """

    def __init__(self, full_tree: DiscoveryTree, observed: Set[str]):
        self._tree = full_tree
        self._observed = observed

    @property
    def root_id(self) -> str:
        return self._tree.root_id

    def node(self, node_id: str) -> DiscoveryNode:
        return self._tree.nodes[node_id]

    def children_of(self, node_id: str) -> List[str]:
        """仅返回已揭示的子节点。"""
        return [c for c in self._tree.nodes[node_id].children if c in self._observed]

    def observed_children_of(self, node_id: str) -> List[str]:
        return self.children_of(node_id)

    def has_unobserved_children(self, node_id: str) -> bool:
        return any(c not in self._observed for c in self._tree.nodes[node_id].children)

    def leaves(self) -> List[str]:
        """已揭示且（在已揭示子图中）无子节点的非根节点。"""
        out = []
        for nid in self._observed:
            if nid == self.root_id:
                continue
            if not self.children_of(nid):
                out.append(nid)
        return out

    def eligible(self) -> List[str]:
        """可继续探索的已揭示节点集 A = {根} ∪ {已揭示叶子}。"""
        return [self.root_id] + self.leaves()

    def max_score(self) -> float:
        scores = [self._tree.nodes[n].score for n in self._observed if n != self.root_id]
        return max(scores) if scores else float("-inf")

    def size(self) -> int:
        return len(self._observed)

    def non_root_count(self) -> int:
        return max(0, len(self._observed) - 1)

    def is_fully_revealed(self) -> bool:
        return len(self._observed) >= len(self._tree.nodes)

    def __contains__(self, node_id: str) -> bool:
        return node_id in self._observed


@dataclass
class ReplayRound:
    """回放中的一轮决策。"""

    round_index: int = 0
    batch: List[str] = field(default_factory=list)          # 策略选中的起始节点
    revealed: List[str] = field(default_factory=list)        # 本轮新揭示的节点
    view_size_after: int = 0


@dataclass
class ReplayResult:
    """一次"策略 × 世界"回放的完整结果。"""

    policy_name: str = ""
    world_id: str = ""
    rounds: List[ReplayRound] = field(default_factory=list)
    revealed_nodes: int = 0        # N（非根）
    best_score: float = float("-inf")
    terminated_reason: str = ""
    score: float = 0.0             # V

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["rounds"] = [
            {"round_index": r.round_index, "batch": r.batch,
             "revealed": r.revealed, "view_size_after": r.view_size_after}
            for r in self.rounds
        ]
        return d

    @property
    def rounds_completed(self) -> int:
        return len(self.rounds)


@dataclass
class ReplayConfig:
    """回放配置。"""

    #: 并行 worker 数 W（每轮最多选多少个起始节点）
    workers: int = 4
    #: 回放轮上限 K2
    max_rounds: int = 64
    #: 执行成本系数 β1
    beta_cost: float = 0.01
    #: 并行奖励系数 β2
    beta_parallel: float = 0.05
    #: 可选：RISE 式自适应 Roll/Stop 门控（None = 固定 K2）
    #: 注意：门控在每次 replay 开始时被 reset，适用于串行回放。
    stop_gate: Optional[Any] = None


def replay_score(best_score: float, revealed_nodes: int, rounds: int,
                 beta_cost: float, beta_parallel: float) -> float:
    """回放打分公式（论文式 1）。

    V = 质量 - β1·N + β2·N/max(1,k)

    Args:
        best_score: 已揭示节点的最高分。
        revealed_nodes: 已揭示的非根节点数 N。
        rounds: 完成轮数 k。
        beta_cost: 成本系数 β1。
        beta_parallel: 并行奖励系数 β2。

    Returns:
        回放分数 V。
    """
    quality = 0.0 if best_score == float("-inf") else best_score
    cost = beta_cost * revealed_nodes
    parallel = beta_parallel * (revealed_nodes / max(1, rounds)) if revealed_nodes > 0 else 0.0
    return quality - cost + parallel


class ReplayWorld:
    """一棵发现树 + 回放执行语义。

    一台世界的生命周期：构造 → 被若干部策略回放 → 产出 ReplayResult。
    世界本身不可变（记录冻结），只有"被观测的子图"随回放推进。
    """

    def __init__(self, tree: DiscoveryTree, world_id: Optional[str] = None):
        self.tree = tree
        self.world_id = world_id or tree.tree_id

    # ── 回放 ────────────────────────────────────────────────────────────

    def replay(self, policy: Any, config: Optional[ReplayConfig] = None) -> ReplayResult:
        """用给定策略在这棵树上回放一遍。

        Args:
            policy: 任何实现 ``select_batch(view: ObservedView, workers: int) -> List[str]`` 的对象。
            config: 回放配置。

        Returns:
            ReplayResult。
        """
        cfg = config or ReplayConfig()
        tree = self.tree
        observed: Set[str] = {tree.root_id}
        stall_rounds = 0
        result = ReplayResult(
            policy_name=getattr(policy, "name", type(policy).__name__),
            world_id=self.world_id,
        )

        # 回放前重置策略的 per-rollout 状态（论文：replay resets the policy's state）
        if hasattr(policy, "reset"):
            try:
                policy.reset()
            except Exception as exc:  # noqa: BLE001
                logger.debug("policy.reset failed: %s", exc)

        # 自适应停止门控（RISE 式）
        gate = cfg.stop_gate
        if gate is not None:
            try:
                gate.reset()
            except Exception:  # noqa: BLE001
                pass
        round_limit = cfg.max_rounds
        if gate is not None and getattr(gate, "config", None) is not None:
            round_limit = min(round_limit, gate.config.max_rounds)

        for k in range(round_limit):
            view = ObservedView(tree, observed)
            if view.is_fully_revealed():
                result.terminated_reason = "fully_revealed"
                break

            # RISE 式 Roll/Stop：边际收益不足则提前停
            if gate is not None:
                try:
                    if gate.should_stop():
                        result.terminated_reason = (
                            f"adaptive_stop:{gate.stop_reason}")
                        break
                except Exception:  # noqa: BLE001
                    pass

            try:
                batch = list(policy.select_batch(view, cfg.workers) or [])
            except Exception as exc:  # noqa: BLE001
                logger.warning("policy.select_batch failed: %s", exc)
                result.terminated_reason = "policy_error"
                break

            # 过滤：只保留合法且仍在可探索集内的节点，去重、限幅
            eligible = set(view.eligible())
            seen: Set[str] = set()
            clean_batch: List[str] = []
            for nid in batch:
                if nid in eligible and nid not in seen:
                    seen.add(nid)
                    clean_batch.append(nid)
            clean_batch = clean_batch[: cfg.workers]

            if not clean_batch:
                result.terminated_reason = "empty_batch"
                break

            revealed: List[str] = []
            for nid in clean_batch:
                child = tree.earliest_unobserved_child(nid, observed)
                if child is not None:
                    observed.add(child)
                    revealed.append(child)

            result.rounds.append(ReplayRound(
                round_index=k,
                batch=clean_batch,
                revealed=revealed,
                view_size_after=len(observed),
            ))

            # 注意：本轮无揭示**不**终止回放（与论文一致）。若策略反复选中
            # 无记录延续的叶子，只会浪费轮次、压低并行奖励，最终由 K2 轮上限
            # 收敛——这正是回放打分要惩罚的劣质探索行为。
            if not revealed:
                stall_rounds += 1

            # 记录给自适应门控
            if gate is not None:
                try:
                    v_now = ObservedView(tree, observed)
                    gate.observe(v_now.max_score(), v_now.non_root_count())
                except Exception:  # noqa: BLE001
                    pass
        else:
            result.terminated_reason = "round_limit"

        if result.terminated_reason == "" and stall_rounds == len(result.rounds) and stall_rounds > 0:
            result.terminated_reason = "no_recorded_continuation"

        final_view = ObservedView(tree, observed)
        result.revealed_nodes = final_view.non_root_count()
        result.best_score = final_view.max_score()
        result.score = replay_score(
            result.best_score, result.revealed_nodes, result.rounds_completed,
            cfg.beta_cost, cfg.beta_parallel,
        )
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {"world_id": self.world_id, "tree": self.tree.to_dict()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReplayWorld":
        tree = DiscoveryTree.from_dict(data["tree"])
        return cls(tree, world_id=data.get("world_id"))


class WorldPool:
    """世界池：累积的历史发现树集合（论文中的 "simulator pool"）。

    每个在线 rollout 产出的发现树追加为一台新世界；离线 dreaming 阶段在整池世界
    上评估策略。池子随每次在线探索单调增长。
    """

    def __init__(self, max_worlds: int = 200):
        self.max_worlds = max_worlds
        self.worlds: List[ReplayWorld] = []
        self._seen_keys: set = set()

    def add(self, world: ReplayWorld) -> None:
        # 去重：同一数据源重复编译不得重复入池
        key = world.tree.dedupe_key
        if key in self._seen_keys:
            return
        self._seen_keys.add(key)
        self.worlds.append(world)
        if len(self.worlds) > self.max_worlds:
            dropped = self.worlds[: len(self.worlds) - self.max_worlds]
            self.worlds = self.worlds[-self.max_worlds:]
            for w in dropped:
                self._seen_keys.discard(w.tree.dedupe_key)

    def add_tree(self, tree: DiscoveryTree) -> ReplayWorld:
        world = ReplayWorld(tree)
        self.add(world)
        return world

    def __iter__(self):
        return iter(self.worlds)

    def __len__(self) -> int:
        return len(self.worlds)

    def stats(self) -> Dict[str, Any]:
        total_nodes = sum(w.tree.size() for w in self.worlds)
        return {
            "worlds": len(self.worlds),
            "total_nodes": total_nodes,
            "avg_nodes": round(total_nodes / len(self.worlds), 2) if self.worlds else 0.0,
            "unique_keys": len(self._seen_keys),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {"max_worlds": self.max_worlds,
                "worlds": [w.to_dict() for w in self.worlds]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldPool":
        pool = cls(max_worlds=data.get("max_worlds", 200))
        for w in data.get("worlds", []):
            pool.add(ReplayWorld.from_dict(w))
        return pool
