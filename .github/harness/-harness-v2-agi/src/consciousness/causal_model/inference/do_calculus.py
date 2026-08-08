"""Do-演算 - 因果干预的形式化推理

实现 Pearl 的 do-calculus 三规则：
1. 插入/删除观察：如果 Y 与 Z 在给定 X 和 W 时条件独立，则 P(y|do(x), z, w) = P(y|do(x), w)
2. 行动/观察交换：如果 Y 与 Z 在给定 do(X) 和 W 时条件独立，则 P(y|do(x), do(z), w) = P(y|do(x), z, w)
3. 插入/删除行动：如果 Y 与 Z 在给定 do(X) 和 W 时条件独立，且 Z 不影响 X，则 P(y|do(x), do(z), w) = P(y|do(x), w)

这是 Harness 从"相关性"进化到"因果性"的数学核心。
"""

from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from scipy.stats import beta as beta_dist, norm

from src.consciousness.causal_model.graphs.causal_graph import CausalGraph, EdgeType
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DoCalculus:
    """
    Harness 的 Do-演算引擎

    将"如果我们把按钮颜色从蓝色改为红色，转化率会怎样"
    转化为可计算的因果查询：P(转化率 | do(按钮颜色=红色))
    """

    def __init__(self, graph: CausalGraph):
        self.graph = graph

    def query(
        self,
        target: str,
        intervention: Dict[str, str],
        evidence: Optional[Dict[str, str]] = None,
    ) -> float:
        """
        执行因果查询：P(target | do(intervention), evidence)

        Args:
            target: 目标变量（如 "conversion_rate"）
            intervention: 干预变量赋值（如 {"button_color": "red"}）
            evidence: 观察证据（如 {"user_type": "new"}）

        Returns:
            目标变量的期望值（概率或数值）
        """
        logger.info(f"[DoCalculus] 查询: P({target} | do({intervention}), {evidence})")

        # 1. 识别干预变量
        treatment_vars = list(intervention.keys())

        # 2. 找到需要调整的后门路径
        adjustment_set = self._find_adjustment_set(treatment_vars, target)

        # 3. 应用 do-calculus 简化查询
        simplified = self._apply_do_calculus(treatment_vars, target, adjustment_set)

        # 4. 使用观测数据估计因果效应（简化：基于边的强度加权）
        effect = self._estimate_causal_effect(
            treatment_vars, target, intervention, adjustment_set
        )

        logger.info(f"[DoCalculus] 因果效应估计: {effect:.4f}")
        return effect

    def counterfactual(
        self,
        target: str,
        intervention: Dict[str, str],
        factual_evidence: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        反事实推理："如果当时做了 X，结果会怎样"

        三步法（Pearl）：
        1. 溯因（Abduction）：用证据更新外生变量（Task D2.1: 贝叶斯共轭先验后验）
        2. 行动（Action）：修改干预变量
        3. 预测（Prediction）：预测结果（Task D2.2: 含不确定性传播）

        Task D2.2: 返回的 ``treatment_effect`` 字段含 95% 置信区间：
        - ``point_estimate``: 点估计 (counterfactual - factual)
        - ``ci_lower`` / ``ci_upper``: 基于 posterior std_error 的 95% CI
        - ``std_error``: 反事实预测的标准误
        """
        logger.info(f"[DoCalculus] 反事实: {target} 如果 {intervention} (实际: {factual_evidence})")

        # 1. 溯因：用共轭先验做贝叶斯后验更新
        posterior = self._abduction(factual_evidence)

        # 2. 行动：在后验状态下应用干预（do-operation）
        modified_state = self._action(posterior, intervention)

        # 3. 预测：预测目标变量（含不确定性传播）
        cf_mean, cf_std_error = self._prediction_with_uncertainty(modified_state, target)

        # 对比实际结果
        factual_value = self._get_factual_value(target, factual_evidence)

        point_estimate = cf_mean - factual_value
        # 95% CI: point_estimate ± 1.96 * std_error
        margin = 1.96 * cf_std_error

        return {
            "factual": factual_value,
            "counterfactual": cf_mean,
            "treatment_effect": {
                "point_estimate": point_estimate,
                "ci_lower": point_estimate - margin,
                "ci_upper": point_estimate + margin,
                "std_error": cf_std_error,
            },
            "confidence": 0.75,  # 反事实置信度通常较低
        }

    def _find_adjustment_set(
        self,
        treatment_vars: List[str],
        target: str,
    ) -> Set[str]:
        """找到满足后门准则的最小调整集"""
        # 简化实现：找到所有混杂因子
        confounders = set()
        for treatment in treatment_vars:
            confounders |= self.graph.identify_confounders(treatment, target)

        # 验证后门准则
        for treatment in treatment_vars:
            if not self.graph.is_valid_backdoor_set(treatment, target, confounders):
                logger.warning(f"[DoCalculus] 后门准则不满足，可能需要工具变量")

        return confounders

    def _apply_do_calculus(
        self,
        treatment_vars: List[str],
        target: str,
        adjustment_set: Set[str],
    ) -> str:
        """应用 do-calculus 规则简化查询"""
        # 简化：将 do(x) 转化为 P(y|x, 调整集) * P(调整集)
        # 实际实现需要完整的条件独立性测试
        return f"P({target} | {', '.join(treatment_vars)}, {', '.join(adjustment_set)})"

    def _estimate_causal_effect(
        self,
        treatment_vars: List[str],
        target: str,
        intervention: Dict[str, str],
        adjustment_set: Set[str],
    ) -> float:
        """基于因果图结构估计因果效应"""
        # 找到所有从 treatment 到 target 的因果路径
        total_effect = 0.0

        for treatment in treatment_vars:
            paths = self.graph.find_paths(treatment, target)

            for path in paths:
                # 路径效应 = 路径上所有边强度的乘积
                path_effect = 1.0
                for i in range(len(path) - 1):
                    source, dest = path[i], path[i + 1]
                    # 找到对应的边强度
                    for edge in self.graph.edges.get(source, []):
                        if edge.target == dest:
                            path_effect *= edge.strength
                            break

                total_effect += path_effect

        # 归一化
        return min(total_effect, 1.0)

    def _abduction(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Task D2.1: 溯因 — 用共轭先验做贝叶斯后验更新

        替代原"证据值直接赋值"策略，对每个证据变量建模后验分布：

        - 二值变量：``Beta(α=1+successes, β=1+failures)`` 共轭先验
          posterior mean = α / (α + β)
          95% CI: ``beta_dist(α, β).ppf([0.025, 0.975])``

        - 数值变量：Normal 后验（简化 Normal-InverseGamma）
          posterior = ``norm(sample_mean, sample_std / sqrt(n))``
          95% CI: ``norm(mean, se).ppf([0.025, 0.975])``

        支持的证据格式（向后兼容原标量调用）：
        - ``{"var": {"successes": 10, "failures": 5}}``  二值变量
        - ``{"var": {"samples": [0.1, 0.2, 0.3]}}``        数值变量
        - ``{"var": [0.1, 0.2, 0.3]}``                     数值变量（列表）
        - ``{"var": "0.5"}`` / ``{"var": 0.5}``            标量（单点数值观察）
        - ``{"var": "red"}``                               非数值（回退 0.5）

        Returns:
            每个变量映射到后验参数 dict:
            ``{mean, variance, ci_lower, ci_upper, std_error, value}``
            其中 ``value=mean`` 用于向后兼容 ``_action`` / ``_prediction``
            的标量提取（通过 ``_state_value``）。
        """
        posterior: Dict[str, Dict[str, float]] = {}
        for var, raw in evidence.items():
            posterior[var] = self._compute_posterior(raw)
        return posterior

    def _compute_posterior(self, raw: Any) -> Dict[str, float]:
        """对单个证据计算后验分布参数"""
        parsed = self._parse_evidence(raw)
        if parsed["kind"] == "binary":
            return self._beta_posterior(parsed["successes"], parsed["failures"])
        return self._normal_posterior(parsed["samples"])

    def _beta_posterior(
        self, successes: float, failures: float
    ) -> Dict[str, float]:
        """Beta(1+s, 1+f) 共轭先验后验

        posterior mean = (1+s) / (2+s+f)
        95% CI 由 ``scipy.stats.beta.ppf`` 计算。
        """
        alpha = 1.0 + successes
        beta_param = 1.0 + failures
        dist = beta_dist(alpha, beta_param)
        mean = alpha / (alpha + beta_param)
        variance = (alpha * beta_param) / (
            (alpha + beta_param) ** 2 * (alpha + beta_param + 1.0)
        )
        ci_lower = float(dist.ppf(0.025))
        ci_upper = float(dist.ppf(0.975))
        std_error = float(np.sqrt(variance))
        return {
            "mean": float(mean),
            "variance": float(variance),
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "std_error": std_error,
            "value": float(mean),
        }

    def _normal_posterior(self, samples: List[float]) -> Dict[str, float]:
        """Normal 后验（简化 Normal-InverseGamma）

        posterior = norm(sample_mean, sample_std / sqrt(n))
        方差用样本方差（ddof=1）；n=1 时方差为 0，CI 退化为宽区间。
        """
        n = len(samples)
        if n == 0:
            return {
                "mean": 0.5,
                "variance": 0.25,
                "ci_lower": 0.0,
                "ci_upper": 1.0,
                "std_error": 0.5,
                "value": 0.5,
            }
        arr = np.asarray(samples, dtype=float)
        mean = float(arr.mean())
        sample_var = float(arr.var(ddof=1)) if n > 1 else 0.0
        std_error = float(np.sqrt(sample_var / n)) if sample_var > 0 else 0.0
        variance = std_error ** 2
        if std_error > 0:
            dist = norm(mean, std_error)
            ci_lower = float(dist.ppf(0.025))
            ci_upper = float(dist.ppf(0.975))
        else:
            # 单点观察无方差信息：用宽 CI（±0.1）
            ci_lower = mean - 0.1
            ci_upper = mean + 0.1
        return {
            "mean": mean,
            "variance": variance,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "std_error": std_error,
            "value": mean,
        }

    def _parse_evidence(self, raw: Any) -> Dict[str, Any]:
        """解析证据值为统一格式 ``{kind: binary|numeric, ...}``

        - dict 含 ``successes``/``failures`` → binary
        - dict 含 ``samples`` 或 list/tuple → numeric
        - bool → binary（单次伯努利）
        - 标量（字符串/数字）→ numeric 单点观察（保持原 ``float(v)`` 行为）
        - 非数值字符串 → numeric 回退 0.5
        """
        if isinstance(raw, bool):
            return {
                "kind": "binary",
                "successes": 1.0 if raw else 0.0,
                "failures": 0.0 if raw else 1.0,
            }
        if isinstance(raw, dict):
            if "successes" in raw and "failures" in raw:
                return {
                    "kind": "binary",
                    "successes": float(raw["successes"]),
                    "failures": float(raw["failures"]),
                }
            if "samples" in raw:
                return {
                    "kind": "numeric",
                    "samples": [float(x) for x in raw["samples"]],
                }
        if isinstance(raw, (list, tuple)):
            return {
                "kind": "numeric",
                "samples": [float(x) for x in raw],
            }
        # 标量（字符串/数字）：作为单点数值观察
        try:
            val = float(raw)
            return {"kind": "numeric", "samples": [val]}
        except (TypeError, ValueError):
            # 非数值字符串（如 "red"）：回退到 0.5
            return {"kind": "numeric", "samples": [0.5]}

    def _action(
        self, state: Dict[str, Any], intervention: Dict[str, str]
    ) -> Dict[str, Any]:
        """行动：修改干预变量（do-operation）

        干预 = 点质量分布（variance=0, std_error=0），
        覆盖对应变量的后验，表示"设定为固定值"。
        """
        new_state = state.copy()
        for k, v in intervention.items():
            parsed = self._parse_evidence(v)
            if parsed["kind"] == "binary":
                val = parsed["successes"]
            else:
                val = parsed["samples"][0] if parsed["samples"] else 0.5
            new_state[k] = {
                "mean": val,
                "variance": 0.0,
                "ci_lower": val,
                "ci_upper": val,
                "std_error": 0.0,
                "value": val,
            }
        return new_state

    def _prediction(self, state: Dict[str, Any], target: str) -> float:
        """预测：基于状态预测目标变量（点估计，向后兼容）"""
        mean, _ = self._prediction_with_uncertainty(state, target)
        return mean

    def _prediction_with_uncertainty(
        self, state: Dict[str, Any], target: str
    ) -> Tuple[float, float]:
        """预测：返回 ``(mean, std_error)``

        目标变量的预测 = 父节点后验均值的平均
        预测的 std_error = ``sqrt(sum(parent_std_error^2)) / n``
        （独立变量均值的方差 = sum(var_i) / n^2）
        """
        parents = self.graph.parents(target)
        if not parents:
            return (0.5, 0.1)
        values = [self._state_value(state.get(p, 0.5)) for p in parents]
        ses = [self._state_std_error(state.get(p, 0.5)) for p in parents]
        n = len(parents)
        mean = sum(values) / n
        combined_se = (
            float(np.sqrt(sum(se ** 2 for se in ses))) / n if n > 0 else 0.1
        )
        return (mean, combined_se)

    def _state_value(self, entry: Any) -> float:
        """从 state 条目提取标量值（支持 posterior dict 或 plain float）"""
        if isinstance(entry, dict):
            return float(entry.get("mean", entry.get("value", 0.5)))
        try:
            return float(entry)
        except (TypeError, ValueError):
            return 0.5

    def _state_std_error(self, entry: Any) -> float:
        """从 state 条目提取标准误（支持 posterior dict 或 plain float）"""
        if isinstance(entry, dict):
            return float(entry.get("std_error", 0.0))
        # plain float: 无不确定性
        return 0.0

    def _get_factual_value(self, target: str, evidence: Dict[str, Any]) -> float:
        """获取实际观察值（支持 dict / list / 标量证据）"""
        raw = evidence.get(target, 0.5)
        if isinstance(raw, bool):
            return 1.0 if raw else 0.0
        if isinstance(raw, dict):
            if "successes" in raw and "failures" in raw:
                alpha = 1.0 + float(raw["successes"])
                beta_param = 1.0 + float(raw["failures"])
                return alpha / (alpha + beta_param)
            if "samples" in raw and raw["samples"]:
                return float(np.mean(raw["samples"]))
            return 0.5
        if isinstance(raw, (list, tuple)) and raw:
            return float(np.mean(raw))
        try:
            return float(raw)
        except (TypeError, ValueError):
            return 0.5
