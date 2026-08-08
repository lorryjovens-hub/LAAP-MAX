"""triphase.pipeline — PGTP 相位门控省 Token 管线。

三相门控（Phase 0）：
- POS    : 需要大模型推理 → 全量通道；
- NEUTRAL: 确定性步骤（参数完备的工具调用 / 格式转换）→ 绕过 LLM；
- NEG    : 缓存命中或负相位抗体命中 → 短路返回，不再探索。

上下文装配（Phase 1）：相位亲和度精确注入 + 负相位一行式警告
（用 ~10 token 替代一次完整的失败探索，~数千 token）。

token 估算约定：混合语料按 ~3 字符/token 粗估，仅用于预算核算。
"""

from __future__ import annotations

import hashlib
import logging
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

import numpy as np

from .core import Trit
from .memory import ComplexResonantMemory

logger = logging.getLogger(__name__)

CHARS_PER_TOKEN = 3  # 估算约定


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / CHARS_PER_TOKEN))


class StepKind(Enum):
    REASONING = "reasoning"     # 需要综合判断
    TOOL_CALL = "tool_call"     # 工具调用
    FORMAT = "format"           # 格式转换
    LOOKUP = "lookup"           # 检索


@dataclass
class Step:
    name: str
    kind: StepKind
    params: Optional[dict[str, Any]] = None      # 完备参数 → 可确定性执行
    query_vector: Optional[np.ndarray] = None    # 语义查询（复向量）
    payload: Any = None

    @property
    def is_deterministic(self) -> bool:
        return self.kind in (StepKind.TOOL_CALL, StepKind.FORMAT) and self.params is not None

    @property
    def cache_key(self) -> str:
        raw = f"{self.kind.value}:{self.name}:{sorted((self.params or {}).items())}"
        return hashlib.sha1(raw.encode()).hexdigest()


@dataclass
class RouteDecision:
    route: Trit
    reason: str
    cached_result: Any = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class PipelineStats:
    steps_total: int = 0
    llm_calls: int = 0
    bypassed: int = 0
    short_circuited: int = 0
    estimated_tokens_spent: int = 0
    estimated_tokens_saved: int = 0

    @property
    def llm_call_ratio(self) -> float:
        return self.llm_calls / self.steps_total if self.steps_total else 0.0


class TokenPipeline:
    """省 token 主管线。

    Parameters
    ----------
    memory : CRM 实例（负相位抗体 + 状态沉淀共用）。
    deterministic_executor : NEUTRAL 通道的执行体（直接调工具，不过 LLM）。
    assumed_full_context_tokens : 无管线时每步的假设上下文成本（核算节省额）。
    """

    def __init__(
        self,
        memory: ComplexResonantMemory,
        deterministic_executor: Optional[Callable[[Step], Any]] = None,
        assumed_full_context_tokens: int = 2000,
    ) -> None:
        self.memory = memory
        self.executor = deterministic_executor
        self.assumed_full_context_tokens = assumed_full_context_tokens
        self._cache: dict[str, Any] = {}
        self.stats = PipelineStats()

    # ------------------------------------------------------------ Phase 0

    def route(self, step: Step) -> RouteDecision:
        self.stats.steps_total += 1

        # 1) 精确缓存命中 → 短路
        if step.cache_key in self._cache:
            self.stats.short_circuited += 1
            self.stats.estimated_tokens_saved += self.assumed_full_context_tokens
            return RouteDecision(Trit.NEG, "缓存命中，短路返回",
                                 cached_result=self._cache[step.cache_key])

        # 2) 负相位抗体：与已证伪路径高亲和 → 短路并返回警告
        if step.query_vector is not None:
            warns = self.memory.warnings(step.query_vector)
            if warns:
                self.stats.short_circuited += 1
                self.stats.estimated_tokens_saved += self.assumed_full_context_tokens
                logger.info("步骤 %s 命中 %d 条负相位抗体，短路", step.name, len(warns))
                return RouteDecision(Trit.NEG, "负相位记忆命中（此路不通）",
                                     cached_result=None, warnings=warns)

        # 3) 确定性步骤 → 绕过 LLM
        if step.is_deterministic and self.executor is not None:
            self.stats.bypassed += 1
            self.stats.estimated_tokens_saved += self.assumed_full_context_tokens
            return RouteDecision(Trit.NEUTRAL, "确定性步骤，绕过 LLM 直接执行")

        # 4) 需要推理 → 全量通道
        self.stats.llm_calls += 1
        return RouteDecision(Trit.POS, "需要大模型推理")

    # ------------------------------------------------------------ Phase 1

    def assemble_context(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        token_budget: int = 1500,
    ) -> tuple[str, int]:
        """相位亲和度装配：结构摘要 + 负相位警告，预算内精确注入。

        返回 (context_text, used_tokens)。
        """
        results = self.memory.retrieve(query_vector, top_k=top_k)
        parts: list[str] = []
        used = 0

        # 负相位警告优先注入（最高 token 性价比）
        for w in self.memory.warnings(query_vector):
            cost = estimate_tokens(w)
            if used + cost > token_budget:
                break
            parts.append(w)
            used += cost

        # 正相位记忆摘要（降序，预算耗尽即止）
        for r in results:
            if r.item.state is Trit.NEG:
                continue
            line = f"[MEM {r.item.state.name}] {r.item.payload}"
            cost = estimate_tokens(line)
            if used + cost > token_budget:
                break
            parts.append(line)
            used += cost

        self.stats.estimated_tokens_spent += used
        return "\n".join(parts), used

    # ------------------------------------------------------------ Phase 3

    def record_outcome(self, step: Step, outcome: Any,
                       vector: np.ndarray, success: bool) -> None:
        """状态沉淀：写入 CRM 并驱动三值巩固。历史永不以原文重进 context。"""
        item = self.memory.store(
            vector=vector,
            payload=f"{step.name} → {str(outcome)[:120]}",
            key=f"outcome:{step.cache_key}",
        )
        self.memory.consolidate(item.key, evidence=0.6 if success else -0.8)
        if success:
            self._cache[step.cache_key] = outcome
