"""LAAP Dream-RSI — Recursive Self-Improvement through Evolving Worlds

三段闭环（Zheng et al., arXiv:2609.14858, 2026）：

    ① Online Explore   —— 当前策略驱动真实发现，记录结构化发现树；
    ② Build Simulator  —— 发现树冻结为可复用回放世界，并入世界池；
    ③ Dream Improvement —— 策略开发智能体在世界池上"做梦"，产出候选策略，
                            用低成本的 off-policy 回放反馈筛选出最优版本。

被选出的最优策略回到 ① 的在线探索，产出新的发现树，扩充世界池——循环往复。

单调不退化保证
--------------
候选集**始终包含当前策略**，最终选取平均回放分最高者 π_{m*}，因此
V^{m*} ≥ V^0：在固定历史 ℋ_t 上，新策略的回放分不低于当前策略。注意该保证
**只针对历史回放分**，不承诺未来在线表现（论文 §3）。

边界
----
回放只能重排、剪枝、改并行与停止点，不能凭空得知未探索区域的结果，因此必须
周期性回到真实在线探索扩充历史。

LAAP 集成
---------
- ``explore_fn(parent_node, tree) -> dict``：在线"发现智能体"回调（对话/实验/工具调用）；
- ``prediction_ledger``（可选）：把每轮策略更替登记为可证伪预测；
- ``nightly_cycle``：离线 dreaming 的天然调度点。
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from laap.dream.discovery_tree import DiscoveryTree
from laap.dream.replay_world import (
    ObservedView, ReplayConfig, ReplayResult, ReplayWorld, WorldPool,
)
from laap.dream.exploration_policy import (
    ExplorationPolicy, PolicyDevelopmentAgent, PolicyParams,
    default_parallel_refining_policy, summarize_replays, STRATEGIES,
)

logger = logging.getLogger("laap.dream.dream_rsi")

DEFAULT_STATE_PATH = "~/.laap/dream_rsi/state.json"


# ══════════════════════════════════════════════════════════════════════
# 配置与结果
# ══════════════════════════════════════════════════════════════════════

@dataclass
class DreamRSIConfig:
    """Dream-RSI 引擎配置。"""

    #: 在线 rollout 的并行 worker 数 W
    workers: int = 4
    #: 在线 rollout 的决策轮上限 K1
    online_max_rounds: int = 24
    #: 回放轮上限 K2
    replay_max_rounds: int = 64
    #: 每次 dreaming 产出并评估的候选策略版本数 M（含当前策略）
    candidates_per_dream: int = 6
    #: 回放打分的成本系数 β1
    beta_cost: float = 0.01
    #: 回放打分的并行奖励系数 β2
    beta_parallel: float = 0.05
    #: 世界池上限
    max_worlds: int = 200
    #: 状态持久化路径
    state_path: str = DEFAULT_STATE_PATH
    #: 随机种子（保证可复现）
    seed: int = 0
    #: 是否启用 LLM 策略开发（需注入 llm_fn / llm_propose_fn）
    use_llm_policy_dev: bool = False
    #: 是否自动接入真实 LLM（通过 llm_bridge；需 API key）
    use_real_llm: bool = False
    #: 真实 LLM 模型 id
    llm_model: str = "deepseek-flash"
    #: 是否启用反事实世界生成（LLM 想象未探索分支）
    use_counterfactual: bool = False
    #: 反事实节点置信度（分数折扣）
    counterfactual_confidence: float = 0.5
    #: 单棵树最多生成多少反事实节点
    counterfactual_max_per_tree: int = 4
    #: 是否启用跨 agent 策略联邦（只共享策略，不共享经验）
    federation_enabled: bool = False
    #: 联邦共享目录；留空 = 自动发现（LAAPer 社区 / LAN / 本地）
    federation_dir: str = ""
    #: 本 agent 匿名 id
    agent_id: str = "aris"
    #: 本地负载作用域（用于 scope-typed 汇合）
    scope: str = "general"


@dataclass
class DreamReport:
    """一次 dreaming 阶段的报告。"""

    iteration: int = 0
    worlds: int = 0
    base_policy: str = ""
    base_score: float = 0.0
    selected_policy: str = ""
    selected_score: float = 0.0
    candidates_evaluated: int = 0
    scores: Dict[str, float] = field(default_factory=dict)
    monotonic_ok: bool = True    # V_selected >= V_base
    improvement: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DreamIterationResult:
    """一次完整三段闭环的结果。"""

    iteration: int = 0
    tree_id: str = ""
    tree_nodes: int = 0
    tree_best_score: float = 0.0
    pool_size: int = 0
    deployed_policy: str = ""
    deployed_score: float = 0.0
    report: Optional[DreamReport] = None
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["report"] = self.report.to_dict() if self.report else None
        return d


# ══════════════════════════════════════════════════════════════════════
# 主引擎
# ══════════════════════════════════════════════════════════════════════

class DreamRSIEngine:
    """Dream-RSI 三段闭环主引擎。

    典型用法::

        engine = DreamRSIEngine()
        result = engine.step(explore_fn=my_discovery_agent)
        # result.deployed_policy 已可用于下一轮在线探索
    """

    def __init__(self, config: Optional[DreamRSIConfig] = None,
                 policy: Optional[ExplorationPolicy] = None,
                 llm_propose_fn: Optional[Callable] = None,
                 llm_fn: Optional[Callable[[str], str]] = None):
        self.config = config or DreamRSIConfig()
        self.policy = policy or default_parallel_refining_policy()
        self.pool = WorldPool(max_worlds=self.config.max_worlds)
        # 自动接入真实 LLM（若配置要求且尚未显式传入）
        if llm_fn is None and llm_propose_fn is None and self.config.use_real_llm:
            try:
                from laap.dream.llm_bridge import make_llm_fn
                llm_fn = make_llm_fn(model=self.config.llm_model)
                if llm_fn is not None:
                    self.config.use_llm_policy_dev = True
            except Exception as exc:  # noqa: BLE001
                logger.warning("real LLM bridge unavailable: %s", exc)
                llm_fn = None
        self.dev_agent = PolicyDevelopmentAgent(
            seed=self.config.seed,
            llm_propose_fn=llm_propose_fn if self.config.use_llm_policy_dev else None,
            llm_fn=llm_fn if self.config.use_llm_policy_dev else None,
        )
        self.iteration = 0
        self.history: List[DreamIterationResult] = []
        self._replay_cfg = ReplayConfig(
            workers=self.config.workers,
            max_rounds=self.config.replay_max_rounds,
            beta_cost=self.config.beta_cost,
            beta_parallel=self.config.beta_parallel,
        )

    # ── ① 在线探索 ──────────────────────────────────────────────────────

    def online_rollout(self, explore_fn: Callable[[Any, DiscoveryTree], Dict[str, Any]],
                       max_rounds: Optional[int] = None) -> DiscoveryTree:
        """当前策略驱动真实探索，记录一棵结构化发现树。

        Args:
            explore_fn: 发现智能体回调。签名 ``(parent_node, tree) -> dict``，
                返回新尝试的结局，至少含 ``score``，可选 ``sketch`` /
                ``snapshot`` / ``artifact`` / ``diagnostics`` / ``metadata``。
            max_rounds: 决策轮上限（默认取配置 K1）。

        Returns:
            构建好的 DiscoveryTree。
        """
        K1 = max_rounds or self.config.online_max_rounds
        W = self.config.workers
        tree = DiscoveryTree()
        self.policy.reset()

        for k in range(K1):
            view = ObservedView(tree, set(tree.nodes.keys()))  # 在线：全树可见
            batch = self.policy.select_batch(view, W)
            if not batch:
                break
            for nid in batch:
                parent = tree.nodes[nid]
                try:
                    outcome = explore_fn(parent, tree) or {}
                except Exception as exc:  # noqa: BLE001
                    logger.warning("explore_fn failed at node %s: %s", nid, exc)
                    outcome = {"score": 0.0, "sketch": f"error: {exc}",
                               "diagnostics": {"error": str(exc)}}
                tree.add_node(
                    parent_id=nid,
                    score=float(outcome.get("score", 0.0)),
                    sketch=str(outcome.get("sketch", "")),
                    snapshot=outcome.get("snapshot") or {},
                    artifact=str(outcome.get("artifact", "")),
                    diagnostics=outcome.get("diagnostics") or {},
                    metadata=outcome.get("metadata") or {},
                )
            self.policy.observe_round(tree.max_score())

        logger.info("[Dream-RSI] online rollout done: tree=%s nodes=%d best=%.4f",
                    tree.tree_id, tree.size(), tree.max_score())
        return tree

    # ── ② 构建回放模拟器 ────────────────────────────────────────────────

    def construct_simulator(self, tree: DiscoveryTree) -> ReplayWorld:
        """把发现树冻结为一台回放世界，并入世界池。"""
        world = self.pool.add_tree(tree)
        logger.info("[Dream-RSI] simulator built: %s (pool=%d)",
                    world.world_id, len(self.pool))
        return world

    # ── ③ 做梦式策略改进 ────────────────────────────────────────────────

    def dream_improve(self, base_policy: Optional[ExplorationPolicy] = None,
                      candidates: Optional[int] = None) -> Tuple[ExplorationPolicy, DreamReport]:
        """在世界池上做低成本 off-policy 评估，产出并选出最优策略。

        候选集**始终包含当前策略**，故 V_selected ≥ V_base（历史回放分单调不退化）。
        """
        if not self.pool.worlds:
            raise RuntimeError("world pool is empty; run construct_simulator first")

        base = base_policy or self.policy
        M = candidates or self.config.candidates_per_dream
        report = DreamReport(iteration=self.iteration, worlds=len(self.pool),
                             base_policy=base.name)

        def eval_policy(pol: ExplorationPolicy) -> Tuple[float, List[ReplayResult]]:
            results = [w.replay(pol, self._replay_cfg) for w in self.pool.worlds]
            avg = sum(r.score for r in results) / max(1, len(results))
            return avg, results

        # 评估当前策略
        base_score, _ = eval_policy(base)
        report.base_score = base_score
        report.scores[base.name] = base_score

        current = base
        evaluated: List[ExplorationPolicy] = [base]
        max_eval = max(M, len(STRATEGIES) * 6)  # 允许系统性扫描全评

        # 联邦候选：其他 agent 学到的策略（仅作候选，需本地回放验证）
        fed_candidates: List[ExplorationPolicy] = []
        if self.config.federation_enabled:
            try:
                from laap.dream.federation import AdaptationStore, merge_adaptations, _anonymize
                store = (AdaptationStore(self.config.federation_dir)
                         if self.config.federation_dir
                         else AdaptationStore.discover())
                mine = _anonymize(self.config.agent_id)
                foreign = store.load_all(exclude_agent=mine)
                fed_candidates = merge_adaptations(
                    base, foreign, local_scope=self.config.scope,
                    max_candidates=12)
                if fed_candidates:
                    logger.info("[Dream-RSI] %d federated candidates from %d adaptations (%s)",
                                len(fed_candidates), len(foreign),
                                getattr(store, "channel_kind", "local"))
            except Exception as exc:  # noqa: BLE001
                logger.warning("federation merge failed: %s", exc)

        # 先评估联邦候选（它们可能直接优于本地基线）
        for cand in fed_candidates:
            if cand.name in report.scores:
                continue
            score, _ = eval_policy(cand)
            report.scores[cand.name] = score
            evaluated.append(cand)

        for m in range(max(0, M - 1)):
            # 产出反馈
            _, cur_results = eval_policy(current)
            feedback = self._build_feedback(cur_results, report)
            proposed = self.dev_agent.propose(
                current, feedback, count=max(8, max_eval - len(evaluated)))
            for cand in proposed:
                if cand.name in report.scores:
                    continue
                if len(evaluated) >= max_eval:
                    break
                score, _ = eval_policy(cand)
                report.scores[cand.name] = score
                evaluated.append(cand)
            # 选当前最优，作为下一轮修订的起点
            best_now = max(evaluated,
                           key=lambda p: report.scores.get(p.name, float("-inf")))
            current = best_now
            if len(evaluated) >= max_eval:
                break

        # 最终选取：平均回放分最高者
        selected = max(evaluated, key=lambda p: report.scores.get(p.name, float("-inf")))
        report.selected_policy = selected.name
        report.selected_score = report.scores.get(selected.name, 0.0)
        report.candidates_evaluated = len(evaluated)
        report.monotonic_ok = report.selected_score >= base_score - 1e-9
        report.improvement = report.selected_score - base_score

        if not report.monotonic_ok:
            # 理论保证不该发生；若发生，退回当前策略以守护单调性
            logger.error("[Dream-RSI] monotonicity violated! fallback to base policy")
            selected = base
            report.selected_policy = base.name
            report.selected_score = base_score
            report.monotonic_ok = True
            report.improvement = 0.0

        logger.info("[Dream-RSI] dream done: base=%.4f selected=%.4f (%s) Δ=%.4f",
                    base_score, report.selected_score,
                    report.selected_policy, report.improvement)
        return selected, report

    def _build_feedback(self, results: List[ReplayResult],
                        report: DreamReport) -> Dict[str, Any]:
        """从回放结果提炼反馈信号，供策略开发智能体定向调整。"""
        if not results:
            return {"avg_quality": 0.0, "avg_cost": 0.0, "improving": True}
        fb = summarize_replays(results, self.config.beta_cost,
                               self.config.beta_parallel)
        # 是否仍在改进：用当前策略与基线策略的平均分比较
        cur_avg = fb.get("avg_score", 0.0)
        fb["base_score"] = report.base_score
        fb["current_score"] = cur_avg
        fb["improving"] = cur_avg > report.base_score + 1e-9
        return fb

    # ── 完整三段闭环 ────────────────────────────────────────────────────

    def step(self, explore_fn: Callable[[Any, DiscoveryTree], Dict[str, Any]],
             ) -> DreamIterationResult:
        """跑一次完整三段闭环。"""
        t0 = time.time()
        self.iteration += 1

        # ① 在线探索
        tree = self.online_rollout(explore_fn)
        # ② 构建回放世界
        self.construct_simulator(tree)
        # ③ 做梦式策略改进
        deployed, report = self.dream_improve(base_policy=self.policy)
        self.policy = deployed

        result = DreamIterationResult(
            iteration=self.iteration,
            tree_id=tree.tree_id,
            tree_nodes=tree.size(),
            tree_best_score=tree.max_score(),
            pool_size=len(self.pool),
            deployed_policy=deployed.name,
            deployed_score=report.selected_score,
            report=report,
            duration_ms=(time.time() - t0) * 1000,
        )
        self.history.append(result)

        # ④ 联邦导出：把学到的策略（仅参数 + 聚合统计）广播到共享目录
        if self.config.federation_enabled and report.improvement > 0:
            self._publish_adaptation(deployed, report)
        return result

    def _publish_adaptation(self, policy: ExplorationPolicy,
                            report: DreamReport) -> None:
        """把本轮学到的策略导出为可共享改编（不含原始经验）。"""
        try:
            from laap.dream.federation import AdaptationStore, export_adaptation
            store = (AdaptationStore(self.config.federation_dir)
                     if self.config.federation_dir
                     else AdaptationStore.discover())
            adapt = export_adaptation(
                policy,
                agent_id=self.config.agent_id,
                scope=self.config.scope,
                evidence_worlds=report.worlds,
                evidence_score=report.selected_score,
                baseline_score=report.base_score,
                notes=f"iteration {self.iteration}, cand {report.candidates_evaluated}",
            )
            store.publish(adapt)
        except Exception as exc:  # noqa: BLE001
            logger.warning("federation publish failed: %s", exc)

    # ── 慢循环：元做梦（双时间尺度）─────────────────────────────────────

    def meta_dream(self, rounds: int = 8,
                   meta_params: Optional[Any] = None) -> Tuple[Any, Any]:
        """慢循环：调优做梦程序本身（MetaSkill-Evolve 式双时间尺度）。

        内层用 inner worlds 选策略；元目标在 **held-out worlds** 上评估
        泛化能力——防止直接刷回放分。

        Returns:
            (best_meta_params, MetaReport)。
        """
        from laap.dream.meta_dream import MetaDreamer, MetaParams, default_meta_params
        if not self.pool.worlds:
            raise RuntimeError("world pool is empty; run online_rollout first")
        meta0 = meta_params or getattr(self, "_meta_params", None) or default_meta_params()
        md = MetaDreamer(workers=self.config.workers, seed=self.config.seed)
        best, report = md.improve(self.policy, self.pool,
                                  meta0=meta0, rounds=rounds)
        # 把学到的元配置应用到引擎
        self._meta_params = best
        self.config.beta_cost = best.beta_cost
        self.config.beta_parallel = best.beta_parallel
        self.config.replay_max_rounds = best.replay_max_rounds
        self.config.candidates_per_dream = best.candidates_per_dream
        self._replay_cfg = best.to_replay_config(self.config.workers)
        return best, report

    # ── 反事实世界生成 ──────────────────────────────────────────────

    def expand_counterfactuals(self, max_trees: int = 4) -> Any:
        """用 LLM 为世界池中的叶子生成反事实分支（结构性地突破"回放不能发明"）。

        合成节点带置信折扣、可溯源；失败一律降级为空报告。
        """
        from laap.dream.counterfactual import (
            CounterfactualGenerator, CounterfactualConfig, CounterfactualReport,
        )
        rep = CounterfactualReport(confidence=self.config.counterfactual_confidence)
        if not self.config.use_counterfactual or not self.pool.worlds:
            return rep
        try:
            from laap.dream.llm_bridge import make_llm_fn
            llm = make_llm_fn(model=self.config.llm_model)
            if llm is None:
                return rep
            cfg = CounterfactualConfig(
                enabled=True,
                confidence=self.config.counterfactual_confidence,
                max_nodes_per_tree=self.config.counterfactual_max_per_tree,
            )
            gen = CounterfactualGenerator(llm, cfg)
            # 选取叶子最少（最需要想象）的若干世界，控制成本
            worlds = sorted(self.pool.worlds,
                            key=lambda w: len(w.tree.leaves()))[:max_trees]
            for w in worlds:
                r = gen.expand(w.tree)
                rep.trees_processed += 1
                rep.leaves_expanded += r.leaves_expanded
                rep.synthetic_nodes += r.synthetic_nodes
                rep.errors.extend(r.errors)
            logger.info("[Dream-RSI] counterfactual: %d synthetic nodes over %d trees",
                        rep.synthetic_nodes, rep.trees_processed)
        except Exception as exc:  # noqa: BLE001
            rep.errors.append(f"{type(exc).__name__}: {exc}")
        return rep

    def run(self, explore_fn: Callable[[Any, DiscoveryTree], Dict[str, Any]],
            iterations: int) -> List[DreamIterationResult]:
        """连续跑若干轮三段闭环（对应论文的多轮递归发现）。"""
        out = []
        for _ in range(iterations):
            out.append(self.step(explore_fn))
        return out

    # ── 持久化 ──────────────────────────────────────────────────────────

    def save_state(self, path: Optional[str] = None) -> str:
        p = Path(path or self.config.state_path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "iteration": self.iteration,
            "policy": self.policy.to_dict(),
            "pool": self.pool.to_dict(),
            "config": asdict(self.config),
            "history": [h.to_dict() for h in self.history[-50:]],
            "saved_at": time.time(),
        }
        p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("[Dream-RSI] state saved to %s", p)
        return str(p)

    def load_state(self, path: Optional[str] = None) -> bool:
        p = Path(path or self.config.state_path).expanduser()
        if not p.exists():
            return False
        state = json.loads(p.read_text(encoding="utf-8"))
        self.iteration = state.get("iteration", 0)
        self.policy = ExplorationPolicy.from_dict(state["policy"])
        self.pool = WorldPool.from_dict(state["pool"])
        return True

    def stats(self) -> Dict[str, Any]:
        return {
            "iteration": self.iteration,
            "policy": self.policy.to_dict(),
            "pool": self.pool.stats(),
            "history_len": len(self.history),
            "last_improvement": (self.history[-1].report.improvement
                                 if self.history and self.history[-1].report else 0.0),
        }
