"""LAAP — EWC 权重桥：持续学习免遗忘（AGI 路线 P2-B）。

背景
----
侦察发现：
- `laap/cognition/ewc.py`：完整的弹性权重巩固实现（Kirkpatrick 2017），
  含 before_learning / compute_fisher / ewc_penalty / after_learning 四阶段；
- `laap/training/orchestrator.py`：TrainingOrchestrator（RL 训练编排层），
  管理并行 rollout 的生命周期；
- 两者之间没有连接——EWC 是独立实验室，未参与训练流程。

本桥接器实现：
1. 在训练开始前冻结 Fisher 信息（重要参数锚点）；
2. 训练过程中 EWC 惩罚项约束重要参数变化；
3. 训练完成后更新参数重要性估计。

设计约束
--------
- 零新第三方依赖；
- 全部降级：EWC 不可用时训练照常进行（无惩罚项）；
- 兼容 RuntimeGuard 行为日志。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("laap.training.ewc_bridge")


class EWCBridge:
    """EWC 权重桥：训练流程中接入弹性权重巩固。

    用法::

        bridge = EWCBridge(ewc=ewc_instance)
        bridge.before_training()          # 冻结 Fisher
        ... 训练循环 ...
        bridge.apply_penalty(new_params)  # 每步约束
        bridge.after_training(new_params) # 巩固
    """

    def __init__(self, ewc: Optional[Any] = None) -> None:
        self._ewc = ewc
        self._active = ewc is not None
        self._penalty_history: list = []

    def before_training(self) -> Dict[str, Any]:
        """训练前准备：冻结当前参数、计算 Fisher 信息矩阵。

        Returns:
            {"status": "ok"} 或 {"status": "skipped", "reason": "..."}
        """
        if not self._ewc:
            return {"status": "skipped", "reason": "ewc_unavailable"}
        try:
            self._ewc.before_learning()
            self._ewc.compute_fisher()
            logger.info(f"[EWCBridge] Fisher 已计算，task#{self._ewc.task_count}")
            return {"status": "ok", "task_count": self._ewc.task_count}
        except Exception as e:
            self._active = False
            logger.warning(f"[EWCBridge] before_training 失败: {e}")
            return {"status": "error", "reason": str(e)[:200]}

    def apply_penalty(self, new_params: Dict[str, Any]) -> Dict[str, Any]:
        """训练过程中应用 EWC 惩罚。

        Args:
            new_params: 新参数字典（形如 {name: value}）。

        Returns:
            {"penalty": float, "constrained": int, "params": dict}
        """
        if not self._ewc or not self._active:
            return {"penalty": 0.0, "constrained": 0, "params": new_params}
        try:
            result = self._ewc.after_learning(new_params)
            penalty = result.get("penalty", 0.0)
            constrained = result.get("constrained_params", {})
            self._penalty_history.append(penalty)
            return {
                "penalty": round(penalty, 4),
                "constrained": len(constrained),
                "params": constrained,
            }
        except Exception as e:
            logger.warning(f"[EWCBridge] apply_penalty 失败: {e}")
            return {"penalty": 0.0, "constrained": 0, "params": new_params}

    def after_training(self, new_params: Dict[str, Any]) -> Dict[str, Any]:
        """训练后巩固：更新参数重要性估计。

        Returns:
            {"status": "ok", "penalty_avg": float}
        """
        result = self.apply_penalty(new_params)
        avg_penalty = (
            round(sum(self._penalty_history) / len(self._penalty_history), 4)
            if self._penalty_history
            else 0.0
        )
        logger.info(
            f"[EWCBridge] 训练完成，平均惩罚={avg_penalty}，"
            f"记录数={len(self._penalty_history)}"
        )
        return {
            "status": "ok",
            "penalty_avg": avg_penalty,
            "penalty_samples": len(self._penalty_history),
            **result,
        }

    # ── 查询 ────────────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        avg_p = (
            round(sum(self._penalty_history) / len(self._penalty_history), 4)
            if self._penalty_history
            else 0.0
        )
        return {
            "active": self._active,
            "ewc_available": self._ewc is not None,
            "penalty_samples": len(self._penalty_history),
            "avg_penalty": avg_p,
            "ewc_task_count": getattr(self._ewc, "task_count", 0) if self._ewc else 0,
        }

    def reset(self) -> None:
        """重置惩罚历史（新任务开始前）。"""
        self._penalty_history = []


def create_ewc_bridge(
    brain=None, unity=None, cortex=None, **kwargs
) -> EWCBridge:
    """工厂函数：创建 EWC 实例并包装为桥接器。

    全部降级：EWC 不可用时返回无操作桥接器。
    """
    try:
        from laap.cognition.ewc import ElasticWeightConsolidation

        ewc = ElasticWeightConsolidation(
            brain=brain, unity=unity, cortex=cortex, **kwargs
        )
        logger.info("[EWCBridge] EWC 实例已创建")
        return EWCBridge(ewc=ewc)
    except Exception as e:
        logger.warning(f"[EWCBridge] EWC 创建失败，降级为空桥接器: {e}")
        return EWCBridge(ewc=None)