"""LAAP — 结构化失败记录（AGI 路线 #2 失败记录规范化）。

三层结构（对应 AHE 经验可观测性）：
1. 表层原因（surface）—— 直接可见的错误表现（"TimeoutError"、"返回空结果"）；
2. 因果机制（causal）—— 深层原因（"召回逻辑未覆盖语义近似"、"工具调用参数错误"）；
3. 抽象行为（abstract）—— 可映射到组件的失败模式（"memory_retrieval_miss"、"tool_parameter_error"）。

与现有 ErrorReflectionFrame 的关系：
- 本模块为轻量包装，不修改现有 ErrorReflectionFrame；
- 新增的 StructuredFailureRecord 可关联到现有 frame_id；
- 抽象行为标签直接映射到 AHE 组件清单（system_prompt / tool_desc / tool_impl / memory_retrieval 等）。
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger("laap.cognition.structured_failure")

# AHE 组件清单（可编辑面映射目标）
COMPONENT_MAP = {
    "memory_retrieval_miss": "memory_retrieval",
    "tool_parameter_error": "tool_implementation",
    "tool_unavailable": "tool_description",
    "context_overflow": "system_prompt",
    "instruction_following": "system_prompt",
    "reasoning_loop": "skill",
    "subagent_failure": "subagent_config",
    "reward_hacking": "tool_implementation",
    "timing_out": "tool_implementation",
    "empty_result": "memory_retrieval",
}


@dataclass
class FailureLayers:
    """三层失败结构。"""

    surface: str = ""  # 表层原因（人可读）
    causal: str = ""  # 因果机制（分析得出）
    abstract: str = ""  # 抽象行为标签（从 COMPONENT_MAP 取）

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)

    def component(self) -> str:
        """映射到 AHE 可编辑组件。"""
        return COMPONENT_MAP.get(self.abstract, "unknown")


@dataclass
class StructuredFailureRecord:
    """结构化失败记录（含三层 + 关联到现有 ErrorReflectionFrame）。"""

    record_id: str = field(default_factory=lambda: f"sf_{uuid.uuid4().hex[:8]}")
    frame_id: str = ""  # 关联的 ErrorReflectionFrame.frame_id
    layers: FailureLayers = field(default_factory=FailureLayers)
    original_query: str = ""
    wrong_answer: str = ""
    context_snapshot: str = ""  # 执行时的上下文快照（关键 token）
    suggested_component: str = ""  # 自动映射的组件
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "frame_id": self.frame_id,
            "layers": self.layers.to_dict(),
            "suggested_component": self.suggested_component or self.layers.component(),
            "original_query": self.original_query[:200],
            "wrong_answer": self.wrong_answer[:200],
            "created_at": self.created_at,
        }


def record_failure(
    original_query: str,
    wrong_answer: str,
    surface: str,
    causal: str,
    abstract: str,
    context_snapshot: str = "",
    frame_id: str = "",
) -> StructuredFailureRecord:
    """创建一条结构化失败记录。

    Args:
        original_query: 触发失败的原始问题。
        wrong_answer: 错误输出。
        surface: 表层原因描述。
        causal: 因果机制分析。
        abstract: 抽象行为标签（见 COMPONENT_MAP）。
        context_snapshot: 执行上下文快照。
        frame_id: 关联的 ErrorReflectionFrame.frame_id。

    Returns:
        StructuredFailureRecord
    """
    layers = FailureLayers(surface=surface, causal=causal, abstract=abstract)
    record = StructuredFailureRecord(
        frame_id=frame_id,
        layers=layers,
        original_query=original_query,
        wrong_answer=wrong_answer,
        context_snapshot=context_snapshot,
        suggested_component=layers.component(),
    )
    logger.info(
        f"[StructuredFailure] {record.record_id}: "
        f"surface={surface[:60]} | causal={causal[:60]} | "
        f"component={record.suggested_component}"
    )
    return record


def failures_by_component(records: List[StructuredFailureRecord]) -> Dict[str, Any]:
    """按组件汇总失败分布。"""
    by_component: Dict[str, list] = {}
    for r in records:
        comp = r.suggested_component or r.layers.component()
        by_component.setdefault(comp, []).append(r.to_dict())
    return {
        comp: {
            "count": len(items),
            "examples": [i["layers"]["surface"] for i in items[:3]],
        }
        for comp, items in sorted(by_component.items(), key=lambda x: -len(x[1]))
    }