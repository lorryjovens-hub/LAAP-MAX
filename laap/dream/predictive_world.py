"""LAAP Dream-RSI — Predictive World (预测世界模型)

把 ``replay_world`` 从"回放已记录的历史"升级为"**预判后果再决定把预算花在哪**"。

为什么要有这个模块
------------------
原来的 ``ExplorationPolicy.select_batch`` 用启发式优先级排序::

    priority = score_weight * score + depth_bonus*depth - depth_penalty*depth + novelty

这是**搜索**：挑"看起来最好的节点"。但每一轮的真实成本是固定的——回放要揭示
一个节点、在线要跑一次真实评估。在预算受限时，真正该问的问题不是"哪个最好"，
而是"**把这一次昂贵反馈押在哪个候选上，期望收益最高**"。

这正是 RSI-Anything (Cui et al., arXiv:2610.13912, 2026) 的立论：世界模型的作用
是 *"action-candidate filtering to maximize the sample efficiency of rare,
expensive ground-truth calls"*。他们的代码修复实验在 coder 固定、候选预算不变的
前提下，仅靠"选哪个"就把隐藏测试通过率从 26.3% 提到 29.2%。

三步闭环的映射
--------------
============ ==========================================================
论文概念      本模块实现
============ ==========================================================
预演          ``PredictiveWorldModel.predict`` —— 用历史学出的线性模型
              预测"从这个节点续探，下一个子节点会得多少分"，附不确定度
学习          ``fit`` 在 **世界池里除当前世界之外** 的树上训练（真正的
              样本外），并做 ``reliability`` 检查
条件自适应    可靠性不达标 → ``is_reliable=False`` → 选择器自动退回启发式
              （对应论文的 "conditional world-model adaptation"）
留用          ``RetentionGate`` —— 新策略必须在**留出世界**上、固定预算
              下胜过在任者，且不得在任一世界崩盘，才被接受
============ ==========================================================

为什么用岭回归而不是神经网络
----------------------------
需要的是"在几十到几百个样本上不崩、可解释、可复现、零依赖"的预测器。岭回归
有闭式解（10×10 正规方程，纯 Python 可解），在特征线性可分性尚可的结构化表格
数据上表现稳定，且**残差标准差天然就是不确定度**——直接可用于 UCB 式选择。
神经网络在这个数据量级上只会过拟合。

耦合更新的隐患（论文的 coupled-update challenge）
-------------------------------------------------
策略一变，候选分布就变，预测器随之失准。所以本模块不在"策略改进后"继续沿用
旧模型，而是每次 ``fit`` 都重新估计可靠性；不可靠就明确降级，而不是硬用它。
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from laap.dream.discovery_tree import DiscoveryTree, DiscoveryNode
from laap.dream.replay_world import ObservedView, ReplayConfig, ReplayResult, ReplayWorld

logger = logging.getLogger("laap.dream.predictive_world")


# ══════════════════════════════════════════════════════════════════════
# 特征
# ══════════════════════════════════════════════════════════════════════

FEATURE_NAMES: Tuple[str, ...] = (
    "parent_score",      # 节点 v 自身的分数（分支延续性最强信号）
    "parent_depth",      # v 的深度
    "score_trend",       # v.score − parent(v).score（上升还是退化）
    "sibling_mean",      # v 已揭示的、早于目标的那些子节点的平均分
    "sibling_count",     # 同上的个数（0 表示尚未窥见后继）
    "sibling_best",      # 同上里的最高分
    "is_root_child",     # 是否从根直接开的分支（结构上不同）
    "sketch_len",        # log1p(摘要长度) —— 低成本的努力代理
    "artifact_len",      # log1p(产物长度)
    "has_diagnostics",   # 评估器是否给了诊断（信息丰富度代理）
)

N_FEATURES = len(FEATURE_NAMES)


def _safe_score(x: float) -> float:
    """把 −inf / NaN 的根节点分数归零。"""
    if x is None or not isinstance(x, (int, float)):
        return 0.0
    if not math.isfinite(x):
        return 0.0
    return float(x)


def _get_node(tree_or_view: Any, node_id: str) -> DiscoveryNode:
    """兼容 ``DiscoveryTree``（.nodes 字典）与 ``ObservedView``（.node()）两种访问。"""
    fn = getattr(tree_or_view, "node", None)
    if callable(fn):
        return fn(node_id)
    return tree_or_view.nodes[node_id]


def features_for(
    tree_or_view: Any,
    node_id: str,
    prior_siblings: Sequence[str] = (),
) -> List[float]:
    """提取一个节点的特征向量。

    Args:
        tree_or_view: ``DiscoveryTree`` 或 ``ObservedView``（两者都支持 ``node()``）。
        node_id: 目标节点。
        prior_siblings: 该节点**已先行揭示**的兄弟节点 id（严格早于目标），
            用于计算 sibling_* 特征而不泄露未来信息。

    Returns:
        长度 ``N_FEATURES`` 的浮点向量。
    """
    n = _get_node(tree_or_view, node_id)
    parent_id = n.parent_id
    parent = _get_node(tree_or_view, parent_id) if parent_id else None
    p_score = _safe_score(parent.score) if parent is not None else 0.0

    sib_scores = [_safe_score(_get_node(tree_or_view, s).score) for s in prior_siblings]
    sib_mean = sum(sib_scores) / len(sib_scores) if sib_scores else 0.0
    sib_best = max(sib_scores) if sib_scores else 0.0

    return [
        _safe_score(n.score),
        float(n.depth),
        _safe_score(n.score) - p_score,
        sib_mean,
        float(len(sib_scores)),
        sib_best,
        1.0 if parent_id == getattr(tree_or_view, "root_id", None) else 0.0,
        math.log1p(len(n.sketch or "")),
        math.log1p(len(n.artifact or "")),
        1.0 if n.diagnostics else 0.0,
    ]


# ══════════════════════════════════════════════════════════════════════
# 预测结果
# ══════════════════════════════════════════════════════════════════════

@dataclass
class Prediction:
    """对一个候选节点"续探后果"的预判。"""

    node_id: str = ""
    mean: float = 0.0            # 预测的下一个子节点分数
    std: float = 0.0             # 不确定度（残差标准差放大后）
    p_improve: float = 0.0       # 预测子节点分数 > 当前最优 的概率
    support: int = 0             # 参与预测的邻近样本量（此处为训练集规模）
    reliable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id, "mean": round(self.mean, 4),
            "std": round(self.std, 4), "p_improve": round(self.p_improve, 4),
            "support": self.support, "reliable": self.reliable,
        }


@dataclass
class ReliabilityReport:
    """世界模型的可靠性体检（对应论文的 prediction reliability assessment）。"""

    n_train: int = 0
    rmse: float = 0.0            # 样本外均方根误差
    baseline_rmse: float = 0.0   # 只预测训练集均值时的 RMSE
    r2: float = 0.0              # 1 − rmse²/baseline_rmse²
    mae: float = 0.0
    residual_std: float = 0.0
    is_reliable: bool = False
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_train": self.n_train, "rmse": round(self.rmse, 4),
            "baseline_rmse": round(self.baseline_rmse, 4),
            "r2": round(self.r2, 4), "mae": round(self.mae, 4),
            "residual_std": round(self.residual_std, 4),
            "is_reliable": self.is_reliable, "reason": self.reason,
        }


# ══════════════════════════════════════════════════════════════════════
# 岭回归求解（纯 Python，闭式解）
# ══════════════════════════════════════════════════════════════════════

def _solve_normal_equations(A: List[List[float]], b: List[float]) -> List[float]:
    """高斯消元（带部分主元）解 A·x = b。A 为方阵。"""
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-12:
            return [0.0] * n
        M[col], M[piv] = M[piv], M[col]
        pv = M[col][col]
        for r in range(col + 1, n):
            f = M[r][col] / pv
            if f == 0.0:
                continue
            for c in range(col, n + 1):
                M[r][c] -= f * M[col][c]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        s = M[r][n] - sum(M[r][c] * x[c] for c in range(r + 1, n))
        x[r] = s / M[r][r] if abs(M[r][r]) > 1e-12 else 0.0
    return x


def _ridge_fit(X: List[List[float]], y: List[float], lam: float) -> List[float]:
    """岭回归闭式解 (XᵀX + λI)⁻¹Xᵀy，含截距（截距不惩罚）。"""
    n = len(X)
    if n == 0:
        return []
    p = len(X[0])
    # 设计矩阵加一列常 1 作为截距
    Xa = [[1.0] + row for row in X]
    d = p + 1
    XtX = [[0.0] * d for _ in range(d)]
    Xty = [0.0] * d
    for i in range(n):
        row = Xa[i]
        for a in range(d):
            ra = row[a]
            if ra == 0.0:
                continue
            Xty[a] += ra * y[i]
            for b in range(d):
                XtX[a][b] += ra * row[b]
    for a in range(1, d):          # 不惩罚截距
        XtX[a][a] += lam
    return _solve_normal_equations(XtX, Xty)


def _ridge_predict(w: List[float], x: List[float]) -> float:
    if not w:
        return 0.0
    return w[0] + sum(w[i + 1] * x[i] for i in range(len(x)))


# ══════════════════════════════════════════════════════════════════════
# 世界模型
# ══════════════════════════════════════════════════════════════════════

class PredictiveWorldModel:
    """预测"从某节点续探，下一个子节点会得多少分"的线性世界模型。

    训练数据来自**世界池里的其他世界**（样本外），因此对当前正在回放的世界
    是真预测而非记忆。
    """

    def __init__(self, ridge: float = 1.0, min_samples: int = 24,
                 reliability_r2: float = 0.05, uncertainty_scale: float = 1.0,
                 n_folds: int = 4):
        """
        Args:
            ridge: L2 正则强度。
            min_samples: 低于此样本量直接判定不可靠。
            reliability_r2: 样本外 R² 低于此值判定不可靠（退回启发式）。
            uncertainty_scale: 不确定度放大系数（UCB 探索力度）。
            n_folds: 可靠性评估用的**按世界分组**交叉验证折数。
        """
        self.ridge = float(ridge)
        self.min_samples = int(min_samples)
        self.reliability_r2 = float(reliability_r2)
        self.uncertainty_scale = float(uncertainty_scale)
        self.n_folds = max(2, int(n_folds))

        self._w: List[float] = []
        self._residual_std: float = 0.0
        self._report = ReliabilityReport()
        self._train_mean: float = 0.0

    # ── 训练 ────────────────────────────────────────────────────────────

    @staticmethod
    def _samples_from_tree(tree: DiscoveryTree) -> List[Tuple[List[float], float]]:
        """把一棵完整发现树摊平成 (特征, 目标) 样本。

        目标 = 某个被揭示子节点的分数；特征在该子节点**之前**已揭示的信息上计算，
        因此不含未来信息。
        """
        out: List[Tuple[List[float], float]] = []
        for nid, node in tree.nodes.items():
            if not node.children:
                continue
            kids = sorted(node.children, key=lambda c: tree.nodes[c].created_order)
            for i, kid in enumerate(kids):
                prior = kids[:i]
                try:
                    x = features_for(tree, nid, prior_siblings=prior)
                except Exception:  # noqa: BLE001
                    continue
                out.append((x, _safe_score(tree.nodes[kid].score)))
        return out

    def fit(self, worlds: Iterable[Any], exclude_world_id: Optional[str] = None) -> "PredictiveWorldModel":
        """在世界池上训练；``exclude_world_id`` 指定的世界不参与训练（真样本外）。

        可靠性用**按世界分组的 k 折交叉验证**估计：每次拟合都把整棵世界排除在
        训练集外，再预测它。这模拟的正是部署场景——“拿历史去预测一个没见过的
        环境”。按样本序号切割的做法会把同一棵树拆到训练与测试两侧，既泄露又
        因测试集太小而让 R² 剧烈震荡。
        """
        per_world: List[List[Tuple[List[float], float]]] = []
        n_worlds = 0
        for w in worlds:
            # 兼容：裸 DiscoveryTree / ReplayWorld / 任意带 .tree 的包装
            if hasattr(w, "nodes"):
                tree = w
                wid = getattr(w, "tree_id", None)
            else:
                tree = getattr(w, "tree", w)
                wid = getattr(w, "world_id", None) or getattr(tree, "tree_id", None)
            if exclude_world_id is not None and wid == exclude_world_id:
                continue
            n_worlds += 1
            s = self._samples_from_tree(tree)
            if s:
                per_world.append(s)

        all_samples = [smp for ws in per_world for smp in ws]
        n = len(all_samples)
        if n == 0:
            self._w = []
            self._report = ReliabilityReport(
                n_train=0, is_reliable=False, reason="no_training_samples")
            return self

        X = [smp[0] for smp in all_samples]
        y = [smp[1] for smp in all_samples]
        self._train_mean = sum(y) / n

        # 世界 → 样本下标区间
        ranges: List[Tuple[int, int]] = []
        idx = 0
        for ws in per_world:
            ranges.append((idx, idx + len(ws)))
            idx += len(ws)

        k = min(self.n_folds, len(per_world))
        preds: List[Optional[float]] = [None] * n
        self_eval = True
        if k >= 2:
            folds: List[List[int]] = [[] for _ in range(k)]
            for wi, (a, b) in enumerate(ranges):
                folds[wi % k].extend(range(a, b))
            produced = 0
            for fi in range(k):
                te_idx = folds[fi]
                tr_idx = [i for fj in range(k) if fj != fi for i in folds[fj]]
                if not tr_idx or not te_idx:
                    continue
                wf = _ridge_fit([X[i] for i in tr_idx], [y[i] for i in tr_idx], self.ridge)
                for i in te_idx:
                    preds[i] = _ridge_predict(wf, X[i])
                    produced += 1
            self_eval = produced < max(1, n // 2)

        if self_eval:
            # 世界太少：只能自评，此时明确标注不准信
            preds = [_ridge_predict(_ridge_fit(X, y, self.ridge), x) for x in X]

        pairs = [(preds[i], y[i]) for i in range(n) if preds[i] is not None]
        errs = [p - t for p, t in pairs]
        mse = sum(e * e for e in errs) / max(1, len(errs))
        rmse = math.sqrt(mse)
        mae = sum(abs(e) for e in errs) / max(1, len(errs))
        mean_te = sum(t for _, t in pairs) / max(1, len(pairs))
        base_mse = sum((t - mean_te) ** 2 for _, t in pairs) / max(1, len(pairs))
        base_rmse = math.sqrt(base_mse)
        r2 = (1.0 - (rmse * rmse) / base_mse) if base_mse > 1e-12 else 0.0

        # 正式预测用全量拟合；残差标准差用交叉验证误差估计
        self._w = _ridge_fit(X, y, self.ridge)
        self._residual_std = rmse

        reasons = []
        if n < self.min_samples:
            reasons.append(f"n_train({n})<{self.min_samples}")
        if self_eval:
            reasons.append("self_evaluated")
        if r2 < self.reliability_r2:
            reasons.append(f"r2({r2:.3f})<{self.reliability_r2}")
        reliable = len(reasons) == 0

        self._report = ReliabilityReport(
            n_train=n, rmse=rmse, baseline_rmse=base_rmse, r2=r2, mae=mae,
            residual_std=self._residual_std, is_reliable=reliable,
            reason=",".join(reasons) if reasons else "ok",
        )
        logger.info("world model fit: worlds=%d n=%d folds=%d r2=%.3f reliable=%s (%s)",
                    n_worlds, n, k, r2, reliable, self._report.reason)
        return self

    # ── 查询 ────────────────────────────────────────────────────────────

    @property
    def report(self) -> ReliabilityReport:
        return self._report

    @property
    def is_reliable(self) -> bool:
        return self._report.is_reliable

    @property
    def weights(self) -> Dict[str, float]:
        if not self._w:
            return {}
        return {"intercept": round(self._w[0], 4),
                **{FEATURE_NAMES[i]: round(self._w[i + 1], 4)
                   for i in range(min(N_FEATURES, len(self._w) - 1))}}

    def predict(self, view: ObservedView, node_id: str,
                current_best: Optional[float] = None) -> Prediction:
        """预判从 ``node_id`` 续探时，下一个子节点的分数。"""
        if not self._w:
            return Prediction(node_id=node_id, mean=self._train_mean,
                              std=0.0, p_improve=0.0, support=0,
                              reliable=False)
        prior = view.children_of(node_id)
        try:
            x = features_for(view, node_id, prior_siblings=prior)
        except Exception:  # noqa: BLE001
            return Prediction(node_id=node_id, mean=self._train_mean,
                              support=self._report.n_train, reliable=False)
        mean = _ridge_predict(self._w, x)
        std = self._residual_std * self.uncertainty_scale
        if current_best is None:
            cur = view.max_score()
            current_best = 0.0 if cur == float("-inf") else cur
        # 用正态近似估计"超过当前最优"的概率
        if std <= 1e-9:
            p_imp = 1.0 if mean > current_best else 0.0
        else:
            z = (current_best - mean) / (std * math.sqrt(2.0))
            p_imp = 0.5 * (1.0 - math.erf(z))
        return Prediction(node_id=node_id, mean=mean, std=std,
                          p_improve=p_imp, support=self._report.n_train,
                          reliable=self.is_reliable)

    # ── 序列化 ──────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ridge": self.ridge, "min_samples": self.min_samples,
            "reliability_r2": self.reliability_r2,
            "uncertainty_scale": self.uncertainty_scale,
            "n_folds": self.n_folds,
            "weights": self._w, "residual_std": self._residual_std,
            "train_mean": self._train_mean, "report": self._report.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PredictiveWorldModel":
        m = cls(ridge=data.get("ridge", 1.0),
                min_samples=data.get("min_samples", 24),
                reliability_r2=data.get("reliability_r2", 0.05),
                uncertainty_scale=data.get("uncertainty_scale", 1.0),
                n_folds=data.get("n_folds", 4))
        m._w = list(data.get("weights") or [])
        m._residual_std = float(data.get("residual_std", 0.0))
        m._train_mean = float(data.get("train_mean", 0.0))
        rep = data.get("report") or {}
        m._report = ReliabilityReport(**{k: v for k, v in rep.items()
                                         if k in ReliabilityReport.__dataclass_fields__})  # type: ignore[attr-defined]
        return m


# ══════════════════════════════════════════════════════════════════════
# 预演式选择策略
# ══════════════════════════════════════════════════════════════════════

class PredictiveSelectionPolicy:
    """用世界模型的预判来分配"下一批反馈预算"的选择策略。

    与 ``ExplorationPolicy`` 接口兼容（``select_batch(view, workers)``），可直接
    交给 ``ReplayWorld.replay`` 使用。

    打分（UCB 形式）::

        value(v) = pred.mean                      # 预测后果
                 + info_weight * pred.std         # 不确定度奖励（信息价值）
                 + p_improve_weight * pred.p_improve  # 押中超越当前最优的概率
                 - depth_penalty * depth(v)

    当世界模型不可靠时，自动退回给定的 ``fallback`` 策略（默认 balanced
    启发式）——这就是"条件性自适应"，不给不可信的预测买单。
    """

    def __init__(
        self,
        model: Optional[PredictiveWorldModel] = None,
        fallback: Optional[Any] = None,
        name: str = "predictive",
        info_weight: float = 0.5,
        p_improve_weight: float = 1.0,
        depth_penalty: float = 0.02,
        min_value: Optional[float] = None,
        always_explore_root: bool = True,
    ):
        from laap.dream.exploration_policy import ExplorationPolicy, PolicyParams

        self.model = model
        self.name = name
        self.info_weight = float(info_weight)
        self.p_improve_weight = float(p_improve_weight)
        self.depth_penalty = float(depth_penalty)
        self.min_value = min_value
        self.always_explore_root = bool(always_explore_root)
        self.fallback = fallback if fallback is not None else ExplorationPolicy(
            PolicyParams(strategy="balanced"), name=f"{name}_fallback")
        #: 本轮是否发生降级（诊断用）
        self.last_degraded = False
        self.last_predictions: List[Prediction] = []

    # 与 ExplorationPolicy 兼容的生命周期
    def reset(self) -> None:
        self.last_degraded = False
        self.last_predictions = []
        if hasattr(self.fallback, "reset"):
            try:
                self.fallback.reset()
            except Exception:  # noqa: BLE001
                pass

    @property
    def params(self):
        """透传 fallback 的参数，便于统一访问。"""
        return getattr(self.fallback, "params", None)

    def select_batch(self, view: ObservedView, workers: int) -> List[str]:
        if workers <= 0:
            return []
        if self.model is None or not self.model.is_reliable or not self.model._w:
            self.last_degraded = True
            return list(self.fallback.select_batch(view, workers))

        candidates = view.eligible()
        if not candidates:
            return []

        cur = view.max_score()
        current_best = 0.0 if cur == float("-inf") else cur

        scored: List[Tuple[float, str, Prediction]] = []
        preds: List[Prediction] = []
        for nid in candidates:
            pred = self.model.predict(view, nid, current_best=current_best)
            preds.append(pred)
            depth = view.node(nid).depth
            value = (pred.mean
                     + self.info_weight * pred.std
                     + self.p_improve_weight * pred.p_improve
                     - self.depth_penalty * depth)
            scored.append((value, nid, pred))

        self.last_predictions = preds
        scored.sort(key=lambda t: t[0], reverse=True)

        batch: List[str] = []
        for value, nid, _pred in scored:
            if self.min_value is not None and value < self.min_value:
                continue
            if nid not in batch:
                batch.append(nid)
            if len(batch) >= workers:
                break
        return batch

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "kind": "predictive",
            "info_weight": self.info_weight,
            "p_improve_weight": self.p_improve_weight,
            "depth_penalty": self.depth_penalty,
            "min_value": self.min_value,
            "always_explore_root": self.always_explore_root,
            "model": self.model.to_dict() if self.model else None,
        }


# ══════════════════════════════════════════════════════════════════════
# 留用闸门（组件检查 + 兼容性检查）
# ══════════════════════════════════════════════════════════════════════

@dataclass
class RetentionDecision:
    """一次"挑战者 vs 在任者"的留用裁决。"""

    accept: bool = False
    challenger: str = ""
    incumbent: str = ""
    worlds: int = 0
    mean_challenger: float = 0.0
    mean_incumbent: float = 0.0
    delta: float = 0.0
    win_rate: float = 0.0             # 严格胜出的世界占比
    tie_rate: float = 0.0             # 打平的世界占比
    non_inferior_rate: float = 0.0    # 不输（胜 + 平）的世界占比
    worst_regression: float = 0.0     # 最差单世界退化幅度（负值）
    reasons: List[str] = field(default_factory=list)
    per_world: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accept": self.accept, "challenger": self.challenger,
            "incumbent": self.incumbent, "worlds": self.worlds,
            "mean_challenger": round(self.mean_challenger, 4),
            "mean_incumbent": round(self.mean_incumbent, 4),
            "delta": round(self.delta, 4),
            "win_rate": round(self.win_rate, 4),
            "tie_rate": round(self.tie_rate, 4),
            "non_inferior_rate": round(self.non_inferior_rate, 4),
            "worst_regression": round(self.worst_regression, 4),
            "reasons": self.reasons, "per_world": self.per_world,
        }


class RetentionGate:
    """留用闸门：只在**留出世界**上、**固定预算**下接受改进。

    对应 RSI-Anything 的 "component and compatibility checks determine which
    policy–model pair is retained"，以及本项目一贯的谨慎：宁可留旧版，也不让
    一个在平均上略胜、却在某个世界崩盘的新版本进来。

    三条判据：
      1. **增益**：挑战者平均分必须高于在任者 ``min_delta`` 以上；
      2. **一致性**：**不输率**（胜 + 平）不低于 ``min_win_rate``——平局不是输，
         一个处处不输、少数世界大胜的策略应当被接受；
      3. **兼容性**：任一世界退化不得超过 ``tolerance``（防止局部崩盘）。
    """

    def __init__(self, min_delta: float = 0.0, min_win_rate: float = 0.5,
                 tolerance: float = 0.25, tie_eps: float = 1e-9):
        self.min_delta = float(min_delta)
        self.min_win_rate = float(min_win_rate)
        self.tolerance = float(tolerance)
        self.tie_eps = float(tie_eps)

    def evaluate(
        self,
        challenger: Any,
        incumbent: Any,
        worlds: Sequence[Any],
        config: Optional[ReplayConfig] = None,
        max_worlds: int = 0,
    ) -> RetentionDecision:
        cfg = config or ReplayConfig()
        ws = list(worlds)[: max_worlds] if max_worlds else list(worlds)
        dec = RetentionDecision(
            challenger=getattr(challenger, "name", type(challenger).__name__),
            incumbent=getattr(incumbent, "name", type(incumbent).__name__),
            worlds=len(ws),
        )
        if not ws:
            dec.reasons.append("no_worlds")
            return dec

        cs: List[float] = []
        is_: List[float] = []
        for w in ws:
            world = w if isinstance(w, ReplayWorld) else ReplayWorld(w)
            rc: ReplayResult = world.replay(challenger, cfg)
            ri: ReplayResult = world.replay(incumbent, cfg)
            cs.append(rc.score)
            is_.append(ri.score)
            dec.per_world.append({
                "world": world.world_id,
                "challenger": round(rc.score, 4),
                "incumbent": round(ri.score, 4),
                "delta": round(rc.score - ri.score, 4),
            })

        n = len(cs)
        dec.mean_challenger = sum(cs) / n
        dec.mean_incumbent = sum(is_) / n
        dec.delta = dec.mean_challenger - dec.mean_incumbent
        eps = self.tie_eps
        wins = sum(1 for a, b in zip(cs, is_) if a - b > eps)
        ties = sum(1 for a, b in zip(cs, is_) if abs(a - b) <= eps)
        dec.win_rate = wins / n
        dec.tie_rate = ties / n
        dec.non_inferior_rate = (wins + ties) / n
        dec.worst_regression = min((a - b for a, b in zip(cs, is_)), default=0.0)

        if dec.delta < self.min_delta:
            dec.reasons.append(f"delta({dec.delta:.4f})<min_delta({self.min_delta})")
        if dec.non_inferior_rate < self.min_win_rate:
            dec.reasons.append(
                f"non_inferior({dec.non_inferior_rate:.2f})<{self.min_win_rate}")
        if dec.worst_regression < -self.tolerance:
            dec.reasons.append(
                f"worst_regression({dec.worst_regression:.4f})<-{self.tolerance}")

        dec.accept = len(dec.reasons) == 0
        return dec


# ══════════════════════════════════════════════════════════════════════
# 便捷入口：在世界上训练 + 回放 + 留用比较
# ══════════════════════════════════════════════════════════════════════

def build_and_evaluate(
    pool: Any,
    config: Optional[ReplayConfig] = None,
    min_train_worlds: int = 2,
    holdout_worlds: int = 0,
    model_kwargs: Optional[Dict[str, Any]] = None,
    info_weight: float = 0.5,
) -> Dict[str, Any]:
    """完整跑一遍"预演 → 学习 → 留用"。

    Args:
        pool: ``WorldPool``（或任意可迭代的 ReplayWorld 集合）。
        config: 回放配置。
        min_train_worlds: 至少要多少个世界才训练世界模型。
        holdout_worlds: 从池尾留出多少世界做留用评估（0 = 自动取 1/4，至少 1）。
        model_kwargs: 传给 ``PredictiveWorldModel``。
        info_weight: 不确定度奖励权重。

    Returns:
        含可靠性报告、逐世界对照、留用裁决的字典。
    """
    from laap.dream.exploration_policy import ExplorationPolicy, PolicyParams

    worlds = list(pool)
    if len(worlds) < min_train_worlds + 1:
        return {"ok": False, "reason": f"need >= {min_train_worlds + 1} worlds, got {len(worlds)}"}

    k = holdout_worlds or max(1, len(worlds) // 4)
    k = min(k, len(worlds) - min_train_worlds)
    train = worlds[:-k]
    test = worlds[-k:]

    model = PredictiveWorldModel(**(model_kwargs or {})).fit(train)
    challenger = PredictiveSelectionPolicy(model, fallback=ExplorationPolicy(
        PolicyParams(strategy="balanced"), name="balanced_baseline"),
        info_weight=info_weight)
    incumbent = ExplorationPolicy(PolicyParams(strategy="balanced"), name="balanced_baseline")

    gate = RetentionGate()
    dec = gate.evaluate(challenger, incumbent, test, config)

    return {
        "ok": True,
        "train_worlds": len(train),
        "test_worlds": len(test),
        "reliability": model.report.to_dict(),
        "weights": model.weights,
        "retention": dec.to_dict(),
        "degraded_on_test": challenger.last_degraded,
    }
