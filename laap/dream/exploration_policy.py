"""LAAP Dream-RSI — Exploration Policy (可执行探索策略)

Dream-RSI 的关键约束：**只有探索策略的代码会变**，底层模型、评估器、执行接口
保持固定（Zheng et al., arXiv:2609.14858, 2026 §3）。

本模块把"探索策略"显式化、可编程化、可变异化：

- ``PolicyParams``  —— 策略的参数化表征（可序列化、可变异）；
- ``ExplorationPolicy`` —— 可执行策略：``select_batch(view, workers) -> List[node_id]``，
  决定"从哪些节点继续探索、开几条新分支、各并行多少、何时停"；
- ``PolicyDevelopmentAgent`` —— 策略开发智能体：读取回放反馈，产出 M 个候选策略
  （模板化变异 + 可选 LLM 改写）；
- ``LLMPolicyDeveloper`` —— LLM 策略开发桥：把回放反馈结构化后交给 LLM，
  由它改写策略结构（策略名 + 参数），对应论文的 LLM-based policy-development agent。

设计约束
--------
- 无 emoji；dataclass + type hints + docstring；
- 决策只读 ``ObservedView``，不触碰未揭示信息（回放不泄露）；
- 策略可选地"自适应"：性能上升期收缩探索开销，停滞期加大投入；
- 所有变异与选择都可审计（参数快照 + 来源）。
"""

from __future__ import annotations

import json
import logging
import math
import random
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple

from laap.dream.replay_world import ObservedView, ReplayResult

logger = logging.getLogger("laap.dream.exploration_policy")


# ══════════════════════════════════════════════════════════════════════
# 参数表征
# ══════════════════════════════════════════════════════════════════════

#: 可命名的策略结构（论文所说 executable policy code 的"逻辑模板"维度）。
#: LLM 可在这些结构间选择并调参，从而改写策略行为而不只是扰动数值。
STRATEGIES: tuple[str, ...] = (
    "balanced",          # 均衡：按优先级混合开新分支与精化
    "depth_first",       # 深度优先：优先精化最深的高分叶子
    "breadth_first",     # 广度优先：优先从根开新分支
    "score_greedy",      # 贪分：只精化最高分叶子
    "novelty_seeking",   # 求新：优先未访问节点
    "adaptive",          # 自适应：根据进展在以上之间切换
    "probe_then_focus",  # 先探测再聚焦：前 P 轮广开分支，之后只精化高分叶子
)


@dataclass
class PolicyParams:
    """探索策略的参数化表征。

    Attributes:
        strategy: 策略结构名（见 ``STRATEGIES``）。决定优先级函数与批次组成。
        parallel_width: 每轮最大并行尝试数（受 worker 数 W 上限约束）。
        explore_ratio: 批次中分配给"开启新分支"（从根出发）的比例。
        score_weight: 节点分数的权重（越大越偏 exploit 高分节点）。
        depth_penalty: 每深一层扣的分（抑制过深追索）。
        depth_bonus: 每深一层加的奖励（鼓励深挖，用于 depth_first）。
        novelty_bonus: 未被访问节点的加成（鼓励覆盖新方向）。
        branch_cap: 从根出发的最大分支数。
        min_score_to_continue: 低于此分的叶子不再续探（None = 无阈值）。
        stop_after_rounds: 超过此轮数后不再发起批次（0 = 不早停）。
        adaptive: 是否启用阶段自适应（上升期收缩、停滞期扩张）。
        adapt_window: 自适应观测窗口（最近多少轮）。
        adapt_gain: 自适应强度。
    """

    strategy: str = "balanced"
    parallel_width: int = 4
    explore_ratio: float = 0.25
    score_weight: float = 1.0
    depth_penalty: float = 0.05
    depth_bonus: float = 0.0
    novelty_bonus: float = 0.10
    branch_cap: int = 8
    min_score_to_continue: Optional[float] = None
    stop_after_rounds: int = 0
    #: probe_then_focus 策略的探测轮数 P
    probe_rounds: int = 4
    adaptive: bool = False
    adapt_window: int = 4
    adapt_gain: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyParams":
        allowed = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in allowed})

    def clamp(self) -> "PolicyParams":
        """把参数夹到合法区间（防止变异越界）。"""
        if self.strategy not in STRATEGIES:
            self.strategy = "balanced"
        self.parallel_width = int(max(1, min(64, self.parallel_width)))
        self.explore_ratio = float(max(0.0, min(1.0, self.explore_ratio)))
        self.score_weight = float(max(0.0, min(10.0, self.score_weight)))
        self.depth_penalty = float(max(0.0, min(5.0, self.depth_penalty)))
        self.depth_bonus = float(max(0.0, min(5.0, self.depth_bonus)))
        self.novelty_bonus = float(max(0.0, min(5.0, self.novelty_bonus)))
        self.branch_cap = int(max(1, min(64, self.branch_cap)))
        if self.min_score_to_continue is not None:
            if not math.isfinite(self.min_score_to_continue):
                self.min_score_to_continue = None
        self.stop_after_rounds = int(max(0, self.stop_after_rounds))
        self.probe_rounds = int(max(0, self.probe_rounds))
        self.adapt_gain = float(max(0.0, min(2.0, self.adapt_gain)))
        return self


# ══════════════════════════════════════════════════════════════════════
# 可执行策略
# ══════════════════════════════════════════════════════════════════════

class ExplorationPolicy:
    """可执行探索策略。

    决策接口（在线与离线共用）::

        select_batch(view: ObservedView, workers: int) -> List[str]

    返回的是一批"起始节点"——它们既是继续探索的位置，也决定了本轮并行度。
    """

    def __init__(self, params: Optional[PolicyParams] = None,
                 name: Optional[str] = None, generation: int = 0,
                 parent_name: str = "", origin: str = "manual"):
        self.params = (params or PolicyParams()).clamp()
        self.name = name or f"pol_{uuid.uuid4().hex[:8]}"
        self.generation = generation
        self.parent_name = parent_name
        self.origin = origin  # manual / mutation / feedback / llm
        #: 本轮 rollout 内的访问计数（replay/rollout 开始时重置）
        self._visits: Dict[str, int] = {}
        #: 自适应历史：最近若干轮的最高分（用于判断进展是否停滞）
        self._score_history: List[float] = []

    # ── 生命周期 ────────────────────────────────────────────────────────

    def reset(self) -> None:
        """开始一轮新的 rollout/replay 前重置每轮状态。"""
        self._visits = {}
        self._score_history = []

    # ── 决策 ────────────────────────────────────────────────────────────

    def select_batch(self, view: ObservedView, workers: int) -> List[str]:
        """选择下一批起始节点（按 ``params.strategy`` 分派）。"""
        p = self.params

        # 早停
        if p.stop_after_rounds and len(self._score_history) >= p.stop_after_rounds:
            return []

        width = min(workers, p.parallel_width)
        if width <= 0:
            return []

        eligible = view.eligible()
        root_id = view.root_id
        leaves = [n for n in eligible if n != root_id]

        # ── 策略自适应：根据进展在结构间切换（对应论文"上升期收缩、停滞期扩张"）──
        strategy = p.strategy
        explore_ratio = p.explore_ratio
        if strategy == "adaptive" or p.adaptive:
            explore_ratio, strategy = self._adapt(view, leaves, explore_ratio, strategy)

        # ── 叶子优先级（按策略选不同权重）──
        def priority(nid: str) -> float:
            nd = view.node(nid)
            s = 0.0 if nd.score == float("-inf") else nd.score
            novelty = p.novelty_bonus * (1.0 / (1.0 + self._visits.get(nid, 0)))
            depth_term = p.depth_bonus * nd.depth - p.depth_penalty * nd.depth
            return p.score_weight * s + depth_term + novelty

        leaves.sort(key=priority, reverse=True)

        if strategy == "novelty_seeking":
            leaves.sort(key=lambda n: self._visits.get(n, 0))
        elif strategy == "depth_first":
            leaves.sort(key=lambda n: view.node(n).depth, reverse=True)

        # probe_then_focus：前 P 轮探测（广开分支），之后专注高分叶子
        focus_mode = False
        if strategy == "probe_then_focus":
            if len(self._score_history) >= p.probe_rounds:
                focus_mode = True
                leaves.sort(key=priority, reverse=True)

        # 过滤：低于续探阈值的叶子剔除
        if p.min_score_to_continue is not None:
            leaves = [n for n in leaves
                      if (view.node(n).score >= p.min_score_to_continue
                          or self._visits.get(n, 0) == 0)]

        # 是否还能从根开新分支
        root_children = view.children_of(root_id)
        can_open_branch = len(root_children) < p.branch_cap

        # ── 批次组成（按策略）──
        batch: List[str] = []
        if strategy == "breadth_first":
            # 优先从根开新分支
            if can_open_branch:
                batch.append(root_id)
            batch.extend(leaves[: max(0, width - len(batch))])
        elif strategy == "score_greedy":
            batch = leaves[:width]
            if not batch and can_open_branch:
                batch = [root_id]
        elif strategy == "probe_then_focus":
            if focus_mode:
                # 聚焦：只精化高分叶子（不再开新分支）
                batch = leaves[:width]
                if not batch and can_open_branch:
                    batch = [root_id]
            else:
                # 探测：广开分支
                if can_open_branch:
                    batch.append(root_id)
                batch.extend(leaves[: max(0, width - len(batch))])
        else:
            # balanced / depth_first / novelty_seeking / adaptive
            n_explore = int(round(width * explore_ratio)) if can_open_branch else 0
            n_exploit = width - n_explore
            if n_explore > 0:
                batch.extend([root_id] * n_explore)
            batch.extend(leaves[:n_exploit])
            if can_open_branch and len(batch) < width:
                batch.append(root_id)

        # 兜底：若叶子和根都没得选，返回根一次（开启首条分支）
        if not batch and can_open_branch:
            batch = [root_id]

        # 去重、限幅、记录访问
        seen = set()
        clean: List[str] = []
        for nid in batch:
            if nid not in seen:
                seen.add(nid)
                clean.append(nid)
        clean = clean[:width]
        for nid in clean:
            self._visits[nid] = self._visits.get(nid, 0) + 1
        return clean

    def _adapt(self, view: ObservedView, leaves: List[str],
               explore_ratio: float, strategy: str) -> Tuple[float, str]:
        """阶段自适应：进展停滞 → 扩张探索；持续上升 → 收缩探索。

        对应论文 §4 的发现：学到的策略在性能上升期主动收缩探索开销，
        进展停滞时再加大投入。
        """
        p = self.params
        if len(self._score_history) < p.adapt_window:
            return explore_ratio, strategy
        recent = self._score_history[-p.adapt_window:]
        improving = (recent[-1] - recent[0]) > 1e-9
        if improving:
            # 上升期：收缩探索，把算力压在已知高价值方向上
            explore_ratio = max(0.0, explore_ratio * max(0.0, 1.0 - p.adapt_gain))
            if strategy in ("breadth_first", "novelty_seeking"):
                strategy = "score_greedy"
        else:
            # 停滞期：加大投入，重启探索
            explore_ratio = min(1.0, explore_ratio * (1.0 + p.adapt_gain))
            if strategy in ("score_greedy", "depth_first"):
                strategy = "breadth_first"
        return explore_ratio, strategy

    # ── 反馈记账（自适应用） ────────────────────────────────────────────

    def observe_round(self, best_score_so_far: float) -> None:
        """每轮结束后记录当前最优分（自适应决策依据）。"""
        self._score_history.append(best_score_so_far)

    # ── 变异 ────────────────────────────────────────────────────────────

    def mutate(self, rng: Optional[random.Random] = None,
               severity: float = 0.3, generation: Optional[int] = None) -> "ExplorationPolicy":
        """参数扰动生成子策略（dreaming 的候选来源之一）。"""
        r = rng or random
        p = PolicyParams.from_dict(self.params.to_dict())

        def jitter(cur: float, scale: float, lo: float, hi: float) -> float:
            delta = r.gauss(0.0, severity * scale)
            return max(lo, min(hi, cur + delta))

        p.parallel_width = int(round(jitter(p.parallel_width, 3.0, 1, 32)))
        p.explore_ratio = jitter(p.explore_ratio, 0.2, 0.0, 1.0)
        p.score_weight = jitter(p.score_weight, 0.5, 0.0, 5.0)
        p.depth_penalty = jitter(p.depth_penalty, 0.05, 0.0, 1.0)
        p.novelty_bonus = jitter(p.novelty_bonus, 0.1, 0.0, 1.0)
        p.branch_cap = int(round(jitter(p.branch_cap, 2.0, 1, 32)))
        # 25% 概率切换策略结构（这是"改写策略代码"的模板化形式）
        if r.random() < 0.25:
            p.strategy = r.choice(list(STRATEGIES))
        if r.random() < 0.3:
            p.probe_rounds = int(max(0, min(30, p.probe_rounds + int(r.gauss(0, 2)))))
        if r.random() < 0.2:
            p.adaptive = not p.adaptive

        return ExplorationPolicy(
            params=p.clamp(),
            generation=(generation if generation is not None else self.generation + 1),
            parent_name=self.name,
            origin="mutation",
        )

    # ── 序列化 ──────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "generation": self.generation,
            "parent_name": self.parent_name,
            "origin": self.origin,
            "params": self.params.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExplorationPolicy":
        return cls(
            params=PolicyParams.from_dict(data.get("params", {})),
            name=data.get("name"),
            generation=data.get("generation", 0),
            parent_name=data.get("parent_name", ""),
            origin=data.get("origin", "manual"),
        )

    def to_source(self) -> str:
        """把策略表征为可读的"策略代码"（论文所说 executable policy code 的审计形态）。"""
        p = self.params
        return (
            f"# ExplorationPolicy {self.name} (gen={self.generation}, origin={self.origin})\n"
            f"def select_batch(view, workers):\n"
            f"    strategy = {p.strategy!r}\n"
            f"    probe_rounds = {p.probe_rounds}\n"
            f"    width = min(workers, {p.parallel_width})\n"
            f"    explore_ratio = {p.explore_ratio:.4f}\n"
            f"    score_weight = {p.score_weight:.4f}\n"
            f"    depth_penalty = {p.depth_penalty:.4f}\n"
            f"    depth_bonus = {p.depth_bonus:.4f}\n"
            f"    novelty_bonus = {p.novelty_bonus:.4f}\n"
            f"    branch_cap = {p.branch_cap}\n"
            f"    adaptive = {p.adaptive}\n"
            f"    # ... 见 ExplorationPolicy.select_batch 的完整逻辑\n"
        )

    def __repr__(self) -> str:
        p = self.params
        return (f"ExplorationPolicy({self.name} gen{self.generation} "
                f"{p.strategy} w={p.parallel_width} ex={p.explore_ratio:.2f} "
                f"sw={p.score_weight:.2f} nov={p.novelty_bonus:.2f})")


# ══════════════════════════════════════════════════════════════════════
# 回放反馈提炼（策略开发智能体的输入）
# ══════════════════════════════════════════════════════════════════════

def summarize_replays(results: List[ReplayResult],
                      beta_cost: float = 0.01,
                      beta_parallel: float = 0.05) -> Dict[str, Any]:
    """把一组回放结果提炼为紧凑的行为反馈（供策略开发智能体阅读）。

    返回的字段描述"策略**怎么做**的"，而非"发现了什么"——这与论文
    "回放不作为文字建议注入"的反直觉发现保持一致：反馈关于策略行为，
    而不是把历史结局当文字提示。
    """
    if not results:
        return {"worlds": 0}
    n = len(results)
    qualities = [0.0 if r.best_score == float("-inf") else r.best_score for r in results]
    revealed = [r.revealed_nodes for r in results]
    rounds = [r.rounds_completed for r in results]
    wasted = [sum(1 for rd in r.rounds if not rd.revealed) for r in results]
    scores = [r.score for r in results]
    avg_quality = sum(qualities) / n
    avg_cost = beta_cost * sum(revealed) / n
    avg_rounds = sum(rounds) / n
    avg_parallel = (sum(revealed) / max(1, sum(rounds)))
    avg_wasted = sum(wasted) / n
    return {
        "worlds": n,
        "avg_quality": round(avg_quality, 4),
        "avg_cost": round(avg_cost, 4),
        "avg_rounds": round(avg_rounds, 3),
        "avg_revealed": round(sum(revealed) / n, 3),
        "avg_parallel": round(avg_parallel, 3),
        "avg_wasted_rounds": round(avg_wasted, 3),
        "avg_score": round(sum(scores) / n, 4),
        "cost_ratio": round(avg_cost / max(1e-9, abs(avg_quality)), 4),
        "reasons": list({r.terminated_reason for r in results}),
    }


# ══════════════════════════════════════════════════════════════════════
# LLM 策略开发桥（论文的 LLM-based policy-development agent）
# ══════════════════════════════════════════════════════════════════════

_LLM_SYSTEM_PROMPT = """You are a policy-development agent for a discovery system.

You are given:
  1. the CURRENT exploration policy (strategy name + numeric params);
  2. aggregated FEEDBACK from replaying that policy over a fixed pool of past
     discovery trees (the replay world pool).

Your job: propose IMPROVED exploration policies. You may change BOTH the
strategy structure and the numeric parameters.

Available strategies (the `strategy` field):
  - balanced        : mix opening new branches and refining, weighted by params
  - depth_first     : prefer refining the deepest high-score leaves
  - breadth_first   : prefer opening new branches from the root
  - score_greedy    : only refine the highest-scoring leaves
  - novelty_seeking : prefer least-visited nodes
  - adaptive        : switch between the above based on progress

Parameters (all optional; ranges in parentheses):
  parallel_width (1-32), explore_ratio (0-1), score_weight (0-10),
  depth_penalty (0-5), depth_bonus (0-5), novelty_bonus (0-5),
  branch_cap (1-32), stop_after_rounds (0-100), adaptive (bool),
  adapt_gain (0-2).

Guidance:
  - If avg_cost / quality is high, reduce wasted exploration (lower
    explore_ratio or strictly prune dead ends).
  - If quality is stuck, increase exploration (higher explore_ratio or use
    novelty_seeking / breadth_first).
  - High avg_wasted_rounds means the policy keeps selecting dead-end leaves:
    prefer breadth_first or lower parallel_width on deep refine.

Return ONLY a JSON array (no prose) of 1-4 objects, each:
  {"strategy": "...", "params": {...}, "reason": "..."}
"""


class LLMPolicyDeveloper:
    """用 LLM 改写探索策略（论文的 LLM-based policy-development agent）。

    ``llm_fn(prompt: str) -> str`` 应返回模型文本；本类负责构造提示、
    解析 JSON、并转为 ``ExplorationPolicy``。解析失败自动降级为空列表
    （调用方会退回模板变异）。

    安全性：LLM 只能提议"策略名 + 参数"，不能注入任意代码；所有参数
    经 ``PolicyParams.clamp()`` 夹到合法区间；提议过程与结果均可审计。
    """

    def __init__(self, llm_fn: Callable[[str], str],
                 system_prompt: str = _LLM_SYSTEM_PROMPT):
        self._llm = llm_fn
        self._system = system_prompt

    def propose(self, base: ExplorationPolicy,
                feedback: Dict[str, Any]) -> List[ExplorationPolicy]:
        prompt = self._build_prompt(base, feedback)
        try:
            raw = self._llm(prompt)
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM policy dev call failed: %s", exc)
            return []
        return self._parse(raw, base)

    def _build_prompt(self, base: ExplorationPolicy,
                      feedback: Dict[str, Any]) -> str:
        return (
            f"{self._system}\n\n"
            f"CURRENT POLICY:\n{json.dumps(base.to_dict(), ensure_ascii=False)}\n\n"
            f"FEEDBACK (aggregated over the replay world pool):\n"
            f"{json.dumps(feedback, ensure_ascii=False)}\n\n"
            f"Propose improved policies as a JSON array:"
        )

    def _parse(self, raw: str, base: ExplorationPolicy) -> List[ExplorationPolicy]:
        text = raw.strip()
        # 容错：剥掉可能的 markdown 代码栅栏
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
        # 取第一个 JSON 数组
        start, end = text.find("["), text.rfind("]")
        if start == -1 or end == -1 or end < start:
            logger.debug("LLM response had no JSON array")
            return []
        try:
            items = json.loads(text[start:end + 1])
        except json.JSONDecodeError as exc:
            logger.debug("LLM JSON parse failed: %s", exc)
            return []
        if not isinstance(items, list):
            return []

        out: List[ExplorationPolicy] = []
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            params = PolicyParams.from_dict(base.params.to_dict())
            # 应用 LLM 提议
            for k, v in (item.get("params") or {}).items():
                if hasattr(params, k):
                    setattr(params, k, v)
            if item.get("strategy"):
                params.strategy = str(item["strategy"])
            out.append(ExplorationPolicy(
                params=params.clamp(),
                name=f"{base.name}_llm{i}",
                generation=base.generation + 1,
                parent_name=base.name,
                origin="llm",
            ))
        logger.info("LLMPolicyDeveloper proposed %d candidates", len(out))
        return out


# ══════════════════════════════════════════════════════════════════════
# 策略开发智能体
# ══════════════════════════════════════════════════════════════════════

class PolicyDevelopmentAgent:
    """在回放反馈上产出候选策略（离线 dreaming 的"梦者"）。

    三条产出途径（可叠加）：
    1. 模板化变异（零依赖，默认）；
    2. 反馈驱动的定向调整；
    3. LLM 改写：可传入 ``llm_fn``（纯文本 LLM）或 ``llm_propose_fn``
       （自定义高级接口），对应论文的 LLM-based policy-development agent。
       LLM 缺失或失败时自动降级到模板变异。
    """

    def __init__(self, seed: int = 0,
                 llm_propose_fn: Optional[Callable[[ExplorationPolicy, Dict[str, Any]], List[ExplorationPolicy]]] = None,
                 llm_fn: Optional[Callable[[str], str]] = None):
        self._rng = random.Random(seed)
        self._llm_propose_fn = llm_propose_fn
        # 纯文本 LLM → 包成 LLMPolicyDeveloper
        self._llm_dev = LLMPolicyDeveloper(llm_fn) if llm_fn is not None else None

    def propose(self, base: ExplorationPolicy, feedback: Dict[str, Any],
                count: int) -> List[ExplorationPolicy]:
        """产出候选策略（含 base 本身，保证候选集含当前策略）。

        候选来源（按优先级）：
          1. base（保证单调不退化）
          2. 系统性策略扫描（回放免费，值得穷举策略结构 × 并行度）
          3. LLM 改写（若接入）
          4. 反馈驱动定向调整
          5. 模板化变异补足
        """
        candidates: List[ExplorationPolicy] = [base]

        # 系统性扫描：策略结构 × 并行度（零成本复用回放）
        candidates.extend(self._systematic_sweep(base))

        # 高级 LLM 接口
        if self._llm_propose_fn is not None:
            try:
                llm_out = self._llm_propose_fn(base, feedback) or []
                candidates.extend(llm_out)
            except Exception as exc:  # noqa: BLE001
                logger.warning("llm_propose_fn failed: %s", exc)

        # 纯文本 LLM 接口
        if self._llm_dev is not None:
            try:
                candidates.extend(self._llm_dev.propose(base, feedback))
            except Exception as exc:  # noqa: BLE001
                logger.warning("LLMPolicyDeveloper failed: %s", exc)

        # 反馈驱动的定向变异
        tuned = self._feedback_tuned(base, feedback)
        if tuned is not None:
            candidates.append(tuned)

        # 模板化变异补足
        while len(candidates) < count:
            candidates.append(base.mutate(self._rng, severity=0.3))

        # 去重（按策略名）
        seen = set()
        unique: List[ExplorationPolicy] = []
        for c in candidates:
            if c.name not in seen:
                seen.add(c.name)
                unique.append(c)
        return unique[:count]

    def _systematic_sweep(self, base: ExplorationPolicy,
                          widths: Tuple[int, ...] = (1, 2, 3, 4, 6)) -> List[ExplorationPolicy]:
        """系统性扫描：每个策略结构 × 若干并行度。

        回放不调 LLM、不重跑环境，成本近乎零；因此值得把策略空间
        廉价地扫一遍——这正是 Dream-RSI "一次昂贵在线探索支撑大量
        近零成本评估"的直接党现。
        """
        out: List[ExplorationPolicy] = []
        for s in STRATEGIES:
            for w in widths:
                p = PolicyParams.from_dict(base.params.to_dict())
                p.strategy = s
                p.parallel_width = w
                out.append(ExplorationPolicy(
                    params=p.clamp(), generation=base.generation + 1,
                    parent_name=base.name, origin="sweep",
                    name=f"sweep_{s}_w{w}"))
        return out

    def _feedback_tuned(self, base: ExplorationPolicy,
                        feedback: Dict[str, Any]) -> Optional[ExplorationPolicy]:
        """依据回放反馈做定向调整。

        - 若成本占比过高 → 收紧 parallel_width / explore_ratio；
        - 若并行奖励偏低 → 提高 parallel_width；
        - 若质量长期不涨 → 提高 novelty_bonus（鼓励新方向）。
        """
        p = PolicyParams.from_dict(base.params.to_dict())
        changed = False

        avg_cost = feedback.get("avg_cost", 0.0)
        avg_quality = feedback.get("avg_quality", 0.0)
        improving = feedback.get("improving", True)

        if avg_cost > 0 and avg_quality > 0 and avg_cost > 0.5 * abs(avg_quality):
            p.parallel_width = max(1, int(p.parallel_width * 0.8))
            p.explore_ratio = max(0.0, p.explore_ratio * 0.8)
            changed = True
        if not improving:
            p.novelty_bonus = min(2.0, p.novelty_bonus + 0.15)
            p.explore_ratio = min(1.0, p.explore_ratio + 0.1)
            p.adaptive = True
            changed = True

        if not changed:
            return None
        return ExplorationPolicy(
            params=p.clamp(), generation=base.generation + 1,
            parent_name=base.name, origin="feedback",
        )


# ══════════════════════════════════════════════════════════════════════
# 默认基线策略（对应论文的 parallel refining baseline）
# ══════════════════════════════════════════════════════════════════════

def default_parallel_refining_policy() -> ExplorationPolicy:
    """论文中的初始基线：并行开启多个独立探索工作区，各自反复精化当前候选。"""
    return ExplorationPolicy(
        params=PolicyParams(
            strategy="balanced",
            parallel_width=4,
            explore_ratio=0.25,
            score_weight=1.0,
            depth_penalty=0.05,
            novelty_bonus=0.10,
            branch_cap=8,
            adaptive=False,
        ),
        name="parallel_refining_v1",
        generation=0,
        origin="manual",
    )
