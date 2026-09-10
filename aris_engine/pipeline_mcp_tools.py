"""
LAAP 六层管线 MCP 工具 v1.0
============================
将 LAAP Pipeline、GWT、OpsAgent、防幻觉引擎暴露为 MCP 工具。

工具列表:
  laap_pipeline_run          — 执行完整六层认知管线
  laap_pipeline_status       — 查询管线状态
  laap_hallucination_check   — 执行防幻觉三层锁验证
  laap_memory_retrieve       — 检索记忆（带权重）
  laap_memory_maintenance    — 触发记忆维护周期
  laap_gwt_snapshot          — 获取全局工作空间快照
  laap_gwt_submit            — 提交信息块到 GWT
  laap_ops_health_check      — 执行健康检查
  laap_ops_maintenance       — 执行完整运维维护周期
  laap_ops_auto_heal         — 自动修复故障

用法:
  这些工具通过 MCP 协议自动注册到 Hanako 运行时。
"""

import json
import time
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger("laap.mcp_tools")

# 懒加载 — 避免循环导入
_pipeline = None
_gwt = None
_ops = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        from laap_pipeline import get_laap_pipeline
        _pipeline = get_laap_pipeline()
    return _pipeline


def _get_gwt():
    global _gwt
    if _gwt is None:
        from global_workspace import get_global_workspace
        _gwt = get_global_workspace()
    return _gwt


def _get_ops():
    global _ops
    if _ops is None:
        from ops_agent import get_ops_agent
        _ops = get_ops_agent()
    return _ops


# ════════════════════════════════════════════════════════════
# MCP 工具函数
# ════════════════════════════════════════════════════════════

async def laap_pipeline_run(
    user_input: str,
    context: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    执行完整六层认知管线。

    Args:
        user_input: 用户输入文本
        context: 额外上下文 (DID, 会话历史等)

    Returns:
        dict: {
            success: bool,
            output_text: str,
            confidence: float,
            reasoning_trace: str,
            phase_trace: list,
            memory_retrieved: int,
            attention_focus: str,
            hallucination_passed: bool,
            total_latency_ms: float,
            correlation_id: str,
        }
    """
    pipeline = _get_pipeline()
    result = await pipeline.run(user_input, context)

    return {
        "success": result.success,
        "output_text": result.output_text[:500],
        "confidence": round(result.confidence, 3),
        "reasoning_trace": result.reasoning_trace[:300],
        "phase_trace": [
            {"layer": p["layer"], "phase": p["phase"], "latency_ms": round(p["ms"], 1)}
            for p in result.phase_trace
        ],
        "memory_retrieved": len(result.memory_retrieved),
        "attention_focus": result.attention_focus,
        "dominant_motivation": max(result.motivation_state, key=result.motivation_state.get)
            if result.motivation_state else "unknown",
        "hallucination_passed": (
            result.hallucination_result.passed
            if result.hallucination_result else True
        ),
        "hallucination_verdict": (
            result.hallucination_result.verdict.value
            if result.hallucination_result else "skipped"
        ),
        "total_latency_ms": round(result.total_latency_ms, 1),
        "correlation_id": result.correlation_id,
        "warnings": result.warnings,
    }


async def laap_pipeline_status() -> Dict[str, Any]:
    """查询六层管线运行状态"""
    pipeline = _get_pipeline()
    summary = pipeline.get_summary()
    bus_stats = pipeline.get_bus_stats()
    mem_stats = pipeline.get_memory_stats()

    return {
        "phase": summary["phase"],
        "interactions": summary["interactions"],
        "layer_latencies": summary["layer_latencies"],
        "bus": {
            "published": bus_stats["published"],
            "delivered": bus_stats["delivered"],
            "errors": bus_stats["errors"],
            "history_size": bus_stats["history_size"],
        },
        "memory": mem_stats,
        "gwt": _get_gwt().get_stats(),
        "ops": _get_ops().get_status_summary(),
    }


async def laap_hallucination_check(
    claim: str,
    context: str = "",
    reasoning_steps: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    执行防幻觉三层锁验证。

    Args:
        claim: 待验证的断言
        context: 上下文信息
        reasoning_steps: 推理链步骤 [{"content": ..., "step_type": ...}, ...]

    Returns:
        dict: {verdict, passed, confidence, lock_results, fix_suggestions, latency_ms}
    """
    from anti_hallucination_pipeline import AntiHallucinationPipeline, ReasoningStep

    pipeline = AntiHallucinationPipeline()

    # 构建推理链
    chain = None
    if reasoning_steps:
        chain = [
            ReasoningStep(
                step_id=s.get("step_id", f"step_{i}"),
                content=s["content"],
                step_type=s.get("step_type", "inference"),
                depends_on=s.get("depends_on", []),
                confidence=s.get("confidence", 0.5),
            )
            for i, s in enumerate(reasoning_steps)
        ]

    result = await pipeline.verify(claim=claim, reasoning_chain=chain, context=context)

    return {
        "verdict": result.verdict.value,
        "passed": result.passed,
        "confidence": round(result.confidence, 3),
        "lock_results": [
            {
                "name": lr.lock_name,
                "status": lr.status.value,
                "passed": lr.passed,
                "details": lr.details[:200],
                "conflicts": lr.conflicts[:3],
                "latency_ms": round(lr.latency_ms, 1),
            }
            for lr in result.lock_results
        ],
        "fix_suggestions": result.fix_suggestions[:5],
        "total_latency_ms": round(result.total_latency_ms, 1),
    }


async def laap_memory_retrieve(
    query: str,
    top_k: int = 10,
    min_weight: float = 0.0,
) -> Dict[str, Any]:
    """
    检索记忆（带权重信息）。

    Args:
        query: 检索查询
        top_k: 返回数量
        min_weight: 最低权重阈值

    Returns:
        dict: {results: [{id, content, weight, tier, access_count, ...}], count, stats}
    """
    from memory_weight_engine import get_memory_weight_engine

    engine = get_memory_weight_engine()
    results = engine.retrieve(query=query, top_k=top_k, min_weight=min_weight)
    stats = engine.get_stats()

    return {
        "results": [
            {
                "id": w.memory_id,
                "content": w.content[:200],
                "weight": round(w.weight, 3),
                "tier": w.tier.value,
                "access_count": w.access_count,
                "emotion_intensity": round(w.emotion_intensity, 2),
                "tags": w.tags[:5],
                "is_forgotten": w.is_forgotten,
            }
            for w in results
        ],
        "count": len(results),
        "stats": {
            "total_memories": stats.total_memories,
            "avg_weight": round(stats.avg_weight, 3),
            "forgotten_count": stats.forgotten_count,
            "consolidation_count": stats.consolidation_count,
        },
    }


async def laap_memory_maintenance() -> Dict[str, Any]:
    """触发记忆维护周期（衰减 + 归纳 + 遗忘）"""
    from memory_weight_engine import get_memory_weight_engine

    engine = get_memory_weight_engine()
    result = await engine.maintenance_cycle()
    return result


async def laap_gwt_snapshot() -> Dict[str, Any]:
    """获取全局工作空间当前快照"""
    gwt = _get_gwt()
    snap = gwt.get_snapshot()

    return {
        "total_slots": snap.total_slots,
        "occupied_slots": snap.occupied_slots,
        "primary_goal": snap.primary_goal.value,
        "active_goals": [g.value for g in snap.active_goals],
        "dominant_motivation": snap.dominant_motivation,
        "weights": snap.weights,
        "chunks": [
            {
                "id": c["id"][:8],
                "source": c["source"],
                "content": c["content"],
                "score": round(c["score"], 3),
                "priority": c["priority"],
                "goal": c["goal"],
            }
            for c in snap.chunks[:10]
        ],
        "cycle_count": snap.cycle_count,
        "preemptions": snap.preemptions,
    }


async def laap_gwt_submit(
    content: str,
    source: str = "perception",
    relevance: float = 0.5,
    urgency: float = 0.0,
    novelty: float = 0.3,
    confidence: float = 0.5,
    priority: str = "medium",
) -> Dict[str, Any]:
    """
    提交信息块到全局工作空间。

    Args:
        content: 信息内容
        source: 来源 (perception|memory|reasoning|motivation|emotion|external|security|system)
        relevance: 相关性 0-1
        urgency: 紧急性 0-1
        novelty: 新颖性 0-1
        confidence: 可信度 0-1
        priority: 优先级 (low|medium|high|critical)

    Returns:
        dict: {chunk_id, submitted}
    """
    from global_workspace import InfoChunk, ChunkSource, ChunkPriority

    gwt = _get_gwt()
    chunk = InfoChunk(
        source=ChunkSource(source),
        content=content[:200],
        full_content=content,
        relevance=relevance,
        urgency=urgency,
        novelty=novelty,
        confidence=confidence,
        priority=ChunkPriority(priority),
    )
    chunk_id = gwt.submit(chunk)

    return {
        "chunk_id": chunk_id,
        "submitted": True,
        "pending_candidates": len(gwt._pending),
    }


async def laap_ops_health_check() -> Dict[str, Any]:
    """执行全系统健康检查"""
    from ops_agent import HealthStatus
    ops = _get_ops()
    report = await ops.health_check()

    return {
        "overall_health": report.overall_health.value,
        "active_alerts": report.active_alerts[:10],
        "components": [
            {
                "name": c.component,
                "status": c.status.value,
                "health": c.health.value,
                "restart_count": c.restart_count,
                "uptime_seconds": round(c.uptime_seconds, 0),
                "metrics": [
                    {"name": m.name, "value": m.value, "unit": m.unit, "status": m.status.value}
                    for m in c.metrics[-5:]
                ],
            }
            for c in report.components
            if c.health != HealthStatus.HEALTHY or c.metrics
        ],
        "recommendations": report.recommendations[:5],
        "timestamp": report.timestamp,
    }


async def laap_ops_maintenance() -> Dict[str, Any]:
    """执行完整运维维护周期"""
    ops = _get_ops()
    return await ops.maintenance_cycle()


async def laap_ops_auto_heal() -> Dict[str, Any]:
    """自动诊断并修复故障"""
    ops = _get_ops()
    diagnoses = await ops.diagnose()
    repairs = await ops.auto_heal()

    return {
        "diagnoses": [
            {"component": d[0], "problem": d[1], "level": d[2].value}
            for d in diagnoses
        ],
        "repairs": [
            {
                "target": r.target,
                "action": r.action.value,
                "success": r.success,
                "description": r.description,
                "level": r.level.value,
            }
            for r in repairs
        ],
        "repairs_successful": sum(1 for r in repairs if r.success),
        "total_diagnoses": len(diagnoses),
        "total_repairs": len(repairs),
    }


# ════════════════════════════════════════════════════════════
# 工具注册表
# ════════════════════════════════════════════════════════════

TOOLS = {
    "laap_pipeline_run": {
        "function": laap_pipeline_run,
        "description": "执行完整 LAAP 六层认知管线 (L1→L6)",
        "is_async": True,
    },
    "laap_pipeline_status": {
        "function": laap_pipeline_status,
        "description": "查询六层管线的运行状态、各层延迟、总线统计、记忆统计",
        "is_async": True,
    },
    "laap_hallucination_check": {
        "function": laap_hallucination_check,
        "description": "执行防幻觉三层锁验证：因果溯源 + 事实记忆校验 + 逻辑闭环收敛",
        "is_async": True,
    },
    "laap_memory_retrieve": {
        "function": laap_memory_retrieve,
        "description": "检索记忆并返回权重信息",
        "is_async": True,
    },
    "laap_memory_maintenance": {
        "function": laap_memory_maintenance,
        "description": "触发记忆维护周期：衰减 + 归纳重组 + 仿生遗忘",
        "is_async": True,
    },
    "laap_gwt_snapshot": {
        "function": laap_gwt_snapshot,
        "description": "获取全局工作空间 (GWT) 当前快照：注意力焦点、活跃目标、权重",
        "is_async": True,
    },
    "laap_gwt_submit": {
        "function": laap_gwt_submit,
        "description": "提交信息块到全局工作空间，参与注意力竞争",
        "is_async": True,
    },
    "laap_ops_health_check": {
        "function": laap_ops_health_check,
        "description": "执行全系统健康检查：CPU/内存/磁盘/组件状态",
        "is_async": True,
    },
    "laap_ops_maintenance": {
        "function": laap_ops_maintenance,
        "description": "执行完整运维维护周期：健康检查 + 诊断 + 修复 + 优化 + 数据维护",
        "is_async": True,
    },
    "laap_ops_auto_heal": {
        "function": laap_ops_auto_heal,
        "description": "自动诊断故障并执行 L0 完全自治修复",
        "is_async": True,
    },
}


def get_tool(name: str):
    """获取工具函数"""
    tool = TOOLS.get(name)
    return tool["function"] if tool else None


def list_tools() -> List[Dict[str, str]]:
    """列出所有工具"""
    return [
        {"name": name, "description": info["description"]}
        for name, info in TOOLS.items()
    ]
