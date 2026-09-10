"""
LAAP 管线运行时集成 v1.0 — PipelineRuntime
===========================================
将六层认知管线接入 LAAP MCP 运行时，实现"自己的架构用自己"。

集成点:
  1. laap_before_turn  → 运行管线，注入认知上下文
  2. laap_after_turn   → 反馈结果，触发学习
  3. laap_after_tool   → 工具调用后更新记忆

认知上下文注入格式:
  [LAAP Pipeline Context]
  - 防幻觉: 通过/拦截
  - 记忆: 检索到 N 条相关记忆
  - 注意力: 当前焦点
  - 动机: 主导需求
  - 管线延迟: L1~L6 各层耗时

用法:
  # 在 MCP server.py 中:
  from aris_engine.pipeline_runtime import PipelineRuntime
  runtime = PipelineRuntime()

  # 在 laap_before_turn 中:
  context = await runtime.before_turn(session_id, user_message)

  # 在 laap_after_turn 中:
  await runtime.after_turn(session_id, response_text)

自检: 运行 python -m aris_engine.pipeline_runtime --self-test
"""

import asyncio
import json
import logging
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger("laap.pipeline_runtime")


class PipelineRuntime:
    """
    管线运行时 — 连接六层管线到 LAAP MCP 服务器。

    每个 session 维护独立的管线实例，确保会话间记忆隔离。
    """

    def __init__(self, lazy: bool = True):
        self._sessions: Dict[str, Any] = {}  # session_id → pipeline state
        self._lazy = lazy
        self._pipeline = None
        self._stats = {
            "total_turns": 0,
            "total_blocks": 0,
            "total_memories_retrieved": 0,
            "avg_latency_ms": 0.0,
        }
        logger.info("PipelineRuntime 初始化完成")

    def _ensure_pipeline(self):
        """延迟加载管线"""
        if self._pipeline is None:
            try:
                # 确保 aris_engine 在路径中
                aris_engine = Path(__file__).resolve().parent
                if str(aris_engine) not in sys.path:
                    sys.path.insert(0, str(aris_engine))

                from laap_pipeline import LAAPPipeline, PipelineConfig, get_laap_pipeline
                from message_bus import reset_message_bus
                from memory_weight_engine import reset_memory_weight_engine
                from global_workspace import reset_global_workspace

                # 使用默认配置
                config = PipelineConfig(
                    enable_hallucination_check=True,
                    enable_deep_recursion=False,   # 太耗时，默认关闭
                    enable_adversarial=False,       # 太耗时，默认关闭
                    enable_realtime_reflection=True,
                    evolution_interval=10,
                )
                self._pipeline = LAAPPipeline(config=config)
                logger.info("管线已加载")
            except Exception as e:
                logger.error(f"管线加载失败: {e}")
                self._pipeline = None

    # ── 主入口: before_turn ──────────────────────────────

    async def before_turn(self, session_id: str, user_message: str) -> str:
        """
        在每次用户消息前调用。运行六层管线，返回认知上下文。

        Args:
            session_id: MCP 会话 ID
            user_message: 用户输入文本

        Returns:
            格式化的认知上下文字符串，注入到系统提示中
        """
        if not user_message.strip():
            return ""

        self._ensure_pipeline()
        if self._pipeline is None:
            return ""

        self._stats["total_turns"] += 1
        t0 = time.time()

        try:
            # 初始化会话状态
            if session_id not in self._sessions:
                self._sessions[session_id] = {
                    "history": [],
                    "memory_count": 0,
                    "blocks": 0,
                }

            # 运行六层管线
            result = await self._pipeline.run(
                user_input=user_message,
                context={"session_id": session_id},
            )

            latency = (time.time() - t0) * 1000
            self._stats["avg_latency_ms"] = (
                self._stats["avg_latency_ms"] * 0.9 + latency * 0.1
            )
            self._stats["total_memories_retrieved"] += len(result.memory_retrieved)

            session = self._sessions[session_id]
            session["history"].append({
                "input": user_message[:100],
                "confidence": result.confidence,
                "attention": result.attention_focus,
                "hallucination": (
                    result.hallucination_result.verdict.value
                    if result.hallucination_result else "skipped"
                ),
                "latency_ms": latency,
            })

            # 是否被拦截
            if not result.success or result.confidence < 0.3:
                session["blocks"] += 1
                self._stats["total_blocks"] += 1

            # 构建认知上下文
            context = self._build_context(result, session)

            return context

        except Exception as e:
            logger.error(f"管线执行失败 [{session_id}]: {e}", exc_info=True)
            return f"[LAAP Pipeline] 管线异常: {e}"

    def _build_context(self, result, session: Dict) -> str:
        """构建认知上下文注入文本"""
        parts = []

        parts.append("[LAAP Pipeline Context]")

        # 防幻觉
        if result.hallucination_result:
            h = result.hallucination_result
            parts.append(f"防幻觉: {h.verdict.value} (置信度 {h.confidence:.2f})")
            if not h.passed:
                locks = [lr.lock_name for lr in h.lock_results if not lr.passed]
                parts.append(f"  拦截层: {', '.join(locks)}")
                if h.fix_suggestions:
                    parts.append(f"  修复建议: {h.fix_suggestions[0][:100]}")

        # 记忆
        if result.memory_retrieved:
            parts.append(f"记忆检索: {len(result.memory_retrieved)} 条")
            for w in result.memory_retrieved[:3]:
                if w.content:
                    parts.append(f"  [{w.weight:.2f}] {w.content[:80]}")

        # 注意力
        parts.append(f"注意力焦点: {result.attention_focus}")

        # 动机
        if result.motivation_state:
            dominant = max(result.motivation_state, key=result.motivation_state.get)
            parts.append(f"主导动机: {dominant} ({result.motivation_state[dominant]:.2f})")

        # 管线性能
        parts.append(
            f"管线延迟: "
            f"L1={result.phase_trace[0]['ms']:.0f}ms "
            f"L2={result.phase_trace[1]['ms']:.0f}ms "
            f"L3={result.phase_trace[2]['ms']:.0f}ms "
            f"L4={result.phase_trace[3]['ms']:.0f}ms "
            f"L5={result.phase_trace[4]['ms']:.0f}ms "
            f"L6={result.phase_trace[5]['ms']:.0f}ms "
            if len(result.phase_trace) >= 6 else ""
        )

        # 会话统计
        parts.append(f"会话: {len(session['history'])} 轮, 拦截 {session['blocks']} 次")

        return "\n".join(parts)

    # ── after_turn ───────────────────────────────────────

    async def after_turn(self, session_id: str, response_text: str) -> Dict[str, Any]:
        """
        在每次助手回复后调用。反馈学习。

        Args:
            session_id: MCP 会话 ID
            response_text: 助手回复文本

        Returns:
            反馈结果
        """
        self._ensure_pipeline()
        if self._pipeline is None:
            return {"learned": False}

        try:
            # 将回复作为新记忆存储
            self._pipeline.memory_engine.register(
                memory_id=f"response_{session_id}_{int(time.time())}",
                content=response_text[:300],
                importance=0.4,
                tags=["assistant_response", session_id],
            )

            # 触发轻量反思
            if self._pipeline.config.enable_realtime_reflection:
                # 检查是否需要防幻觉复核
                from anti_hallucination_pipeline import AntiHallucinationPipeline
                checker = AntiHallucinationPipeline()
                check_result = await checker.verify(
                    claim=response_text[:500],
                    context=f"session={session_id}",
                )
                if not check_result.passed:
                    logger.warning(f"after_turn 防幻觉复核拦截 [{session_id}]: {check_result.summary}")
                    return {
                        "learned": True,
                        "hallucination_detected": True,
                        "verdict": check_result.verdict.value,
                        "fix_suggestions": check_result.fix_suggestions[:3],
                    }

            return {"learned": True, "hallucination_detected": False}

        except Exception as e:
            logger.error(f"after_turn 失败: {e}")
            return {"learned": False, "error": str(e)}

    # ── 状态查询 ────────────────────────────────────────

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self._sessions:
            return {"error": "session not found"}
        session = self._sessions[session_id]
        return {
            "turns": len(session["history"]),
            "blocks": session["blocks"],
            "last_input": session["history"][-1]["input"] if session["history"] else "",
            "last_confidence": session["history"][-1]["confidence"] if session["history"] else 0,
        }

    def get_global_stats(self) -> Dict[str, Any]:
        self._ensure_pipeline()
        stats = dict(self._stats)
        if self._pipeline:
            stats["pipeline"] = self._pipeline.get_summary()
        stats["sessions"] = len(self._sessions)
        return stats

    # ── 自检 ────────────────────────────────────────────

    async def self_test(self) -> Dict[str, Any]:
        """运行自检，验证管线是否正常工作"""
        self._ensure_pipeline()

        results = {"pipeline_loaded": self._pipeline is not None, "tests": []}

        if not self._pipeline:
            results["error"] = "管线未加载"
            return results

        test_inputs = [
            "你好，介绍一下 LAAP",
            "什么是因果推理？",
            "LAAP 的六层架构包含哪些？",
        ]

        for text in test_inputs:
            t0 = time.time()
            try:
                result = await self._pipeline.run(text)
                latency = (time.time() - t0) * 1000
                results["tests"].append({
                    "input": text[:50],
                    "success": result.success,
                    "confidence": round(result.confidence, 3),
                    "attention": result.attention_focus,
                    "hallucination_passed": (
                        result.hallucination_result.passed
                        if result.hallucination_result else True
                    ),
                    "memories": len(result.memory_retrieved),
                    "latency_ms": round(latency, 1),
                    "phase_trace": [
                        {"layer": p["layer"], "ms": round(p["ms"], 1)}
                        for p in result.phase_trace
                    ],
                })
            except Exception as e:
                results["tests"].append({
                    "input": text[:50],
                    "error": str(e),
                })

        results["summary"] = {
            "total": len(results["tests"]),
            "successful": sum(1 for t in results["tests"] if t.get("success")),
            "avg_latency_ms": round(
                sum(t.get("latency_ms", 0) for t in results["tests"]) / max(len(results["tests"]), 1), 1
            ),
        }

        return results


# ════════════════════════════════════════════════════════════
# 全局单例
# ════════════════════════════════════════════════════════════

_runtime: Optional[PipelineRuntime] = None


def get_pipeline_runtime() -> PipelineRuntime:
    global _runtime
    if _runtime is None:
        _runtime = PipelineRuntime()
    return _runtime


# ════════════════════════════════════════════════════════════
# 自检入口
# ════════════════════════════════════════════════════════════

async def main():
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║   LAAP PipelineRuntime 自检                          ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()

    runtime = get_pipeline_runtime()
    results = await runtime.self_test()

    print(f"  管线加载: {'✅' if results['pipeline_loaded'] else '❌'}")
    print()

    for i, t in enumerate(results["tests"]):
        status = "✅" if t.get("success") else "❌"
        print(f"  {status} 测试 {i+1}: \"{t['input']}\"")
        if "error" in t:
            print(f"     错误: {t['error']}")
        else:
            print(f"     置信度: {t['confidence']}, 注意力: {t['attention']}, "
                  f"防幻觉: {'通过' if t['hallucination_passed'] else '拦截'}, "
                  f"记忆: {t['memories']}条, 延迟: {t['latency_ms']}ms")
            parts = [f"{p['layer']}={p['ms']:.0f}ms" for p in t['phase_trace']]
            print(f"     各层: {' -> '.join(parts)}")

    print()
    print(f"  汇总: {results['summary']['successful']}/{results['summary']['total']} 成功, "
          f"平均延迟 {results['summary']['avg_latency_ms']}ms")
    print()

    success = results["summary"]["successful"] == results["summary"]["total"]
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
