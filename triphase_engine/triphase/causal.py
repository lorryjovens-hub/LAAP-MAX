"""triphase.causal — Causal Tensor Engine 因果张量引擎核心。

三层架构（对应 Pearl 因果阶梯）：

- L1   关联层  : ``ComplexMultilinearRegressor`` 复多线性回归核
                 y ≈ Σ_r λ_r Π_k ⟨a_k^r, x_k⟩，Wirtinger 梯度训练；
                 ``complex_cp_als`` 复数 CP 分解（复数域 Kruskal
                 唯一性条件更宽松 → 因子可识别）。
- L2   干预层  : ``LinearSCM.intervene`` —— do-算子 = 图手术 +
                 前向重算，解析可算、无需重采样。
- L3   反事实层: ``LinearSCM.counterfactual`` —— 溯因（闭式解
                 u = x − Wx）→ 干预 → 预测。
- 结构层       : ``InvarianceScreener`` —— 跨环境系数不变性检验，
                 输出三值因果边 {存在 / 未决 / 排除}。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np

from .core import Trit, circular_dispersion

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 复数 CP 分解（参考实现：显式 Khatri-Rao + 复最小二乘，小中等规模适用）
# ---------------------------------------------------------------------------

def _khatri_rao(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """逐列 Kronecker 积：(I×R, J×R) → (I·J × R)。"""
    if a.shape[1] != b.shape[1]:
        raise ValueError("Khatri-Rao 要求列数一致")
    return np.einsum("ir,jr->ijr", a, b).reshape(a.shape[0] * b.shape[0], -1)


def complex_cp_als(
    X: np.ndarray,
    rank: int,
    n_iter: int = 300,
    tol: float = 1e-8,
    reg: float = 1e-8,
    rng: Optional[np.random.Generator] = None,
) -> tuple[np.ndarray, list[np.ndarray], float]:
    """三阶复张量 CP-ALS。返回 (weights, factors, final_relative_error)。"""
    if X.ndim != 3:
        raise ValueError("当前实现支持三阶张量")
    rng = rng or np.random.default_rng(0)
    dims = X.shape
    factors = [
        rng.standard_normal((d, rank)) + 1j * rng.standard_normal((d, rank))
        for d in dims
    ]
    weights = np.ones(rank, dtype=complex)

    def unfold(X: np.ndarray, mode: int) -> np.ndarray:
        return np.moveaxis(X, mode, 0).reshape(dims[mode], -1)

    prev_err = np.inf
    rel_err = np.inf
    for it in range(n_iter):
        for mode in range(3):
            others = [factors[m] for m in range(3) if m != mode]
            # mode-n 展开的列按其余模态的自然顺序排列 → Khatri-Rao 同序
            kr = _khatri_rao(others[0], others[1])          # (Πd_others × R)
            P = (weights[None, :] * kr).T                    # 吸收权重
            G = P @ P.conj().T + reg * np.eye(rank)
            factors[mode] = np.linalg.solve(G, P @ unfold(X, mode).conj().T).conj().T
            if mode < 2:  # 最后一个 mode 吸收尺度，避免退化
                norms = np.linalg.norm(factors[mode], axis=0)
                norms[norms < 1e-12] = 1.0
                factors[mode] /= norms
                weights *= norms
        # 重构误差
        rec = np.einsum(
            "r,ir,jr,kr->ijk", weights, factors[0], factors[1], factors[2]
        )
        rel_err = float(np.linalg.norm(X - rec) / (np.linalg.norm(X) + 1e-12))
        if abs(prev_err - rel_err) < tol:
            logger.debug("CP-ALS 第 %d 次迭代收敛 rel_err=%.2e", it, rel_err)
            break
        prev_err = rel_err
    return weights, factors, rel_err


# ---------------------------------------------------------------------------
# 复多线性回归核：y_n ≈ Σ_r λ_r Π_k ⟨a_k^r, x_{n,k}⟩
# ---------------------------------------------------------------------------

class ComplexMultilinearRegressor:
    """复数因子机形式的多线性回归。

    原生表示 k 阶交互（低秩假设下参数量 O(k·d·r)），
    复数系数同时编码交互的幅度与相位（协同 / 拮抗）。
    """

    def __init__(
        self,
        rank: int = 4,
        lr: float = 0.02,
        momentum: float = 0.9,
        weight_decay: float = 1e-5,
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        if rank <= 0:
            raise ValueError("rank 必须为正")
        self.rank = rank
        self.lr = lr
        self.momentum = momentum
        self.weight_decay = weight_decay
        self.rng = rng or np.random.default_rng(0)
        self.factors: list[np.ndarray] = []   # A_k: (rank, d_k)
        self.lam: Optional[np.ndarray] = None  # λ: (rank,)
        self.bias: complex = 0.0
        self.loss_history: list[float] = []

    # ---- 前向 ----

    def _modal_scores(self, X: list[np.ndarray]) -> np.ndarray:
        """s[n,k,r] = ⟨a_k^r, x_{n,k}⟩，返回 (n, k, r)。"""
        return np.stack([X[k] @ self.factors[k].T for k in range(len(X))], axis=1)

    def predict(self, X: list[np.ndarray]) -> np.ndarray:
        s = self._modal_scores(X)                    # (n, k, r)
        return self.bias + (self.lam[None, :] * np.prod(s, axis=1)).sum(axis=1)

    # ---- 训练（Wirtinger 梯度 + 动量） ----

    def fit(self, X: list[np.ndarray], y: np.ndarray, epochs: int = 500,
            verbose: bool = False) -> "ComplexMultilinearRegressor":
        if not X:
            raise ValueError("至少需要一个模态")
        n = X[0].shape[0]
        if any(x.shape[0] != n for x in X):
            raise ValueError("各模态样本数不一致")
        y = np.asarray(y, dtype=complex)

        if not self.factors:
            scale = 0.1
            self.factors = [
                scale * (self.rng.standard_normal((self.rank, x.shape[1]))
                         + 1j * self.rng.standard_normal((self.rank, x.shape[1])))
                for x in X
            ]
            self.lam = np.ones(self.rank, dtype=complex)

        v_fac = [np.zeros_like(f) for f in self.factors]
        v_lam = np.zeros_like(self.lam)

        for ep in range(epochs):
            s = self._modal_scores(X)                # (n, k, r)
            prod_all = np.prod(s, axis=1)            # (n, r)
            y_hat = self.bias + (self.lam[None, :] * prod_all).sum(axis=1)
            resid = y_hat - y                        # (n,)
            loss = float(np.mean(np.abs(resid) ** 2))
            self.loss_history.append(loss)

            k_modes = len(X)
            # λ 梯度
            g_lam = np.conj(prod_all).T @ resid / n + self.weight_decay * self.lam
            # 因子梯度（Wirtinger 约定）：
            # ∂ŷ_n/∂A_k[r,d] = λ_r · x[n,k,d] · Π_{j≠k} s[n,j,r]
            # g_k[r,d] = Σ_n resid_n · conj(∂ŷ_n/∂A_k[r,d])
            for k in range(k_modes):
                others = np.prod(np.delete(s, k, axis=1), axis=1)   # (n, r)
                M = resid[:, None] * np.conj(others)                # (n, r)
                g = np.conj(self.lam)[:, None] * (M.T @ np.conj(X[k])) / n
                g += self.weight_decay * self.factors[k]
                v_fac[k] = self.momentum * v_fac[k] + (1 - self.momentum) * g
                self.factors[k] -= self.lr * v_fac[k]

            v_lam = self.momentum * v_lam + (1 - self.momentum) * g_lam
            self.lam -= self.lr * v_lam
            self.bias -= self.lr * complex(resid.mean())

            if verbose and ep % 100 == 0:
                logger.info("epoch %d loss=%.6f", ep, loss)
        return self


# ---------------------------------------------------------------------------
# 复线性结构因果模型（L2 干预 / L3 反事实）
# ---------------------------------------------------------------------------

@dataclass
class Interventions:
    values: dict[str, complex] = field(default_factory=dict)


class LinearSCM:
    """x_j = Σ_{i∈pa(j)} w_ij·x_i + u_j（复系数）。

    - do-算子：切断入边、固定边界值、按拓扑序前向重算（解析）；
    - 溯因：u = x − Wx 闭式解；
    - 反事实 = 固定 u（保持个体相位）+ do（翻转控制相位）。
    """

    def __init__(self, nodes: Sequence[str], parents: dict[str, list[str]]) -> None:
        self.nodes = list(nodes)
        self.parents = {n: list(parents.get(n, [])) for n in self.nodes}
        self._order = self._topological_order()
        self.W: Optional[np.ndarray] = None   # W[j, i] = w_ij
        self._idx = {n: i for i, n in enumerate(self.nodes)}

    def _topological_order(self) -> list[str]:
        order, visited, stack = [], set(), set()

        def visit(n: str) -> None:
            if n in visited:
                return
            if n in stack:
                raise ValueError(f"因果图含环（经过 {n}），SCM 要求 DAG")
            stack.add(n)
            for p in self.parents.get(n, []):
                visit(p)
            stack.discard(n)
            visited.add(n)
            order.append(n)

        for n in self.nodes:
            visit(n)
        return order

    def fit(self, data: dict[str, np.ndarray], reg: float = 1e-8) -> "LinearSCM":
        n_nodes = len(self.nodes)
        self.W = np.zeros((n_nodes, n_nodes), dtype=complex)
        for j, node in enumerate(self.nodes):
            pa = self.parents[node]
            if not pa:
                continue
            Xp = np.stack([np.asarray(data[p], dtype=complex) for p in pa], axis=1)
            yj = np.asarray(data[node], dtype=complex)
            G = Xp.conj().T @ Xp + reg * np.eye(len(pa))
            w = np.linalg.solve(G, Xp.conj().T @ yj)
            for coef, p in zip(w, pa):
                self.W[j, self._idx[p]] = coef
        return self

    def _require_fitted(self) -> np.ndarray:
        if self.W is None:
            raise RuntimeError("SCM 尚未 fit")
        return self.W

    def abduct(self, obs: dict[str, complex]) -> dict[str, complex]:
        """溯因：由观测反解外生噪声 u = x − Wx。"""
        W = self._require_fitted()
        x = np.array([obs[n] for n in self.nodes], dtype=complex)
        u = x - W @ x
        return {n: u[i] for i, n in enumerate(self.nodes)}

    def intervene(
        self,
        do: dict[str, complex],
        noise: Optional[dict[str, complex]] = None,
    ) -> dict[str, complex]:
        """干预：do-手术 + 前向重算。未给定噪声时取 0（总体平均预测）。"""
        W = self._require_fitted()
        x = np.zeros(len(self.nodes), dtype=complex)
        for n in self._order:
            i = self._idx[n]
            if n in do:
                x[i] = do[n]                     # 切断入边，固定边界值
            else:
                u = noise.get(n, 0.0) if noise else 0.0
                x[i] = (W[i] @ x) + u
        return {n: x[i] for i, n in enumerate(self.nodes)}

    def counterfactual(
        self,
        obs: dict[str, complex],
        do: dict[str, complex],
    ) -> dict[str, complex]:
        """L3 反事实：溯因 → 干预 → 预测（保持个体噪声不变）。"""
        u = self.abduct(obs)
        return self.intervene(do=do, noise=u)


# ---------------------------------------------------------------------------
# 结构层：跨环境不变性因果筛选（三值输出）
# ---------------------------------------------------------------------------

@dataclass
class CandidateVerdict:
    feature: str
    trit: Trit
    coef_magnitudes: list[float]
    coef_phases: list[float]
    mag_spread: float        # 模长变异系数
    phase_dispersion: float  # 相位圆方差


class InvarianceScreener:
    """不变性因果筛选：在多个环境/干预下，系数（模长与相位）都保持
    不变的候选晋级为因果边（POS）；波动剧烈的排除（NEG，防复捞）；
    介于其间保持未决（NEUTRAL）。
    """

    def __init__(self, mag_cv_pos: float = 0.15, mag_cv_neg: float = 0.5,
                 phase_disp_pos: float = 0.1, phase_disp_neg: float = 0.4,
                 reg: float = 1e-8) -> None:
        self.mag_cv_pos, self.mag_cv_neg = mag_cv_pos, mag_cv_neg
        self.phase_disp_pos, self.phase_disp_neg = phase_disp_pos, phase_disp_neg
        self.reg = reg

    def _fit_env(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        G = X.conj().T @ X + self.reg * np.eye(X.shape[1])
        return np.linalg.solve(G, X.conj().T @ y)

    def screen(
        self,
        envs: Sequence[dict[str, np.ndarray]],
        target: str,
        candidates: Sequence[str],
    ) -> list[CandidateVerdict]:
        if len(envs) < 2:
            raise ValueError("不变性检验至少需要两个环境")
        verdicts = []
        for cand in candidates:
            mags, phases = [], []
            for env in envs:
                others = [c for c in candidates if c != cand]
                cols = [np.asarray(env[c], dtype=complex) for c in ([cand] + others)]
                X = np.stack(cols, axis=1)
                y = np.asarray(env[target], dtype=complex)
                w = self._fit_env(X, y)
                mags.append(abs(w[0]))
                phases.append(float(np.angle(w[0])))
            mags_arr = np.asarray(mags)
            mean_mag = mags_arr.mean()
            mag_cv = float(mags_arr.std() / (mean_mag + 1e-12))
            phase_disp = circular_dispersion(phases)

            stable = mag_cv < self.mag_cv_pos and phase_disp < self.phase_disp_pos
            unstable = mag_cv > self.mag_cv_neg or phase_disp > self.phase_disp_neg
            trit = Trit.POS if stable else (Trit.NEG if unstable else Trit.NEUTRAL)
            verdicts.append(CandidateVerdict(
                feature=cand, trit=trit,
                coef_magnitudes=mags, coef_phases=phases,
                mag_spread=mag_cv, phase_dispersion=phase_disp,
            ))
        return verdicts
