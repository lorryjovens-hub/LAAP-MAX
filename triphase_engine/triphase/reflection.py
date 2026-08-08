"""triphase.reflection — SPIR 结构化相位反演反思回路。

反思 = 带收敛判据的分层算子序列，而非文本递归：

1. 触发：元认知反相 / 代码图出现 -1 传播；
2. 逐层反演：第 k 层反思 = 翻转该层相位并重跑其下动力学，
   观察结论是否改变；
3. 停止：连续两次迭代角距 < eps → 找到病灶层；
4. 熔断：max_depth 层全部反演仍不稳定 → 退入 NEUTRAL 扇区
   向外部求信息（结构性防止无限自我怀疑）；
5. 沉淀：病灶归因经回调写入 CRM 负相位记忆（反思复利化）。

层级执行体通过依赖注入提供（LevelRunner 协议），
框架本身不绑定具体 LLM / 工具实现。
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Protocol

from .core import PhaseState, Trit, angular_distance

logger = logging.getLogger(__name__)


class LevelRunner(Protocol):
    """单一层级的"反演-重跑"执行体。

    实现约定：接收当前结论，翻转本层假设后重跑本层及以下动力学，
    返回新结论的相位态。
    """

    name: str

    def invert_and_run(self, conclusion: PhaseState) -> PhaseState:
        ...


@dataclass
class ReflectionResult:
    resolved: bool
    culprit_level: Optional[int]      # 病灶层索引；None = 未定位
    culprit_name: Optional[str]
    final_state: PhaseState
    fallback_to_seeking: bool         # True = 熔断，应向外求信息
    trace: list[dict[str, Any]] = field(default_factory=list)


class SPIRReflector:
    """结构化相位反演反思器。

    Parameters
    ----------
    levels : 从浅到深的层级执行体（行动参数 → 策略 → 目标分解 → 问题理解）。
    max_depth : 反演深度硬上限（≤ len(levels)）。
    eps : 收敛角距（弧度）。
    on_lesson : 反思沉淀回调（典型用法：写 CRM 负相位记忆）。
    """

    def __init__(
        self,
        levels: list[LevelRunner],
        max_depth: int = 4,
        eps: float = 0.15,
        on_lesson: Optional[Callable[[str, PhaseState], None]] = None,
    ) -> None:
        if not levels:
            raise ValueError("至少需要一个层级执行体")
        self.levels = levels
        self.max_depth = min(max_depth, len(levels))
        self.eps = eps
        self.on_lesson = on_lesson

    def reflect(self, initial: PhaseState) -> ReflectionResult:
        trace: list[dict[str, Any]] = []
        state = initial

        for k in range(self.max_depth):
            runner = self.levels[k]
            s1 = runner.invert_and_run(state)
            s2 = runner.invert_and_run(s1)
            gap = angular_distance(s1.phase, s2.phase)
            trace.append({
                "level": k,
                "name": runner.name,
                "delta_theta": gap,
                "stable": gap < self.eps,
            })
            logger.info("SPIR 第 %d 层(%s): Δθ=%.3f %s",
                        k, runner.name, gap, "→ 稳定" if gap < self.eps else "")

            if gap < self.eps:
                # 找到病灶层：修正并从该层重建
                result = ReflectionResult(
                    resolved=True,
                    culprit_level=k,
                    culprit_name=runner.name,
                    final_state=s2,
                    fallback_to_seeking=False,
                    trace=trace,
                )
                if self.on_lesson:
                    self.on_lesson(
                        f"反思定位病灶层[{runner.name}]，修正后结论相位 "
                        f"{s2.phase:.2f}（扇区 {s2.trit.name}）",
                        s2,
                    )
                return result
            state = s2

        # 熔断：四层反演皆不稳定 → 信息不足，退入 NEUTRAL 扇区
        logger.warning("SPIR 达到深度上限 %d 仍未收敛，熔断转 SEEK_INFO", self.max_depth)
        fallback = PhaseState(
            magnitude=max(0.1, state.magnitude * 0.3),
            phase=Trit.NEUTRAL.phase,
        )
        return ReflectionResult(
            resolved=False,
            culprit_level=None,
            culprit_name=None,
            final_state=fallback,
            fallback_to_seeking=True,
            trace=trace,
        )
