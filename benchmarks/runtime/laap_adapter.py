"""
Real LAAP Adapter — 把真实 LAAPKernel 包装为基准测试可用接口
================================================================

这是 P0 #1 的核心文件——把论文§6 的"参数化模拟器"替换为真实 LAAP 调用。

设计原则:
    1. 真实调用 LAAPKernel.run_interaction，不模拟任何 LAAP 行为
    2. 与 baseline LLM 接口一致（都提供 answer(task) -> dict）
    3. 收集完整 trace：PSI 阶段耗时、模式选择、agent_state 等
    4. 支持三种模式: "v5"（完整 PSI）/ "llm"（仅 LLM，对照）/ "auto"

用法:
    from benchmarks.runtime.llm_bridge import auto_bridge
    from benchmarks.runtime.laap_adapter import RealLAAPAdapter

    bridge = auto_bridge(model="gpt-4o-mini")
    adapter = RealLAAPAdapter(llm_bridge=bridge, mode="v5")
    result = adapter.answer({"prompt": "什么是量子纠缠？"})
    print(result["answer"], result["time_ms"], result["mode"])
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("benchmarks.laap_adapter")

__all__ = ["RealLAAPAdapter", "RawLLMAdapter"]


# ════════════════════════════════════════════════════════════
#  RealLAAPAdapter
# ════════════════════════════════════════════════════════════


class RealLAAPAdapter:
    """真实 LAAP 运行时适配器——包装 LAAPKernel.run_interaction。

    Args:
        llm_bridge: LLMBridge 实例（提供真实 LLM 调用）
        mode: PSI 模式
            - "v5": 强制走完整 PSI 认知循环（LAAP 增强模式）
            - "llm": 强制走纯 LLM 模式（与基线对照，验证 PSI 是否真的有效）
            - "auto": 由 LAAPKernel 自动选择
        kernel_kwargs: 传给 LAAPKernel 的额外参数
        reset_per_call: 是否每次调用前重置 kernel 状态（默认 False，性能优先）
    """

    def __init__(self, llm_bridge, mode: str = "v5",
                 kernel_kwargs: Optional[Dict[str, Any]] = None,
                 reset_per_call: bool = False):
        from laap_brain.kernel import LAAPKernel

        self.bridge = llm_bridge
        self.mode = mode
        self.reset_per_call = reset_per_call
        self.kernel_kwargs = kernel_kwargs or {}

        # 创建 LAAPKernel 实例
        self.kernel = LAAPKernel(
            model=llm_bridge.model_name,
            psi_mode=mode if mode == "auto" else "auto",
            **self.kernel_kwargs,
        )
        self.kernel.initialize()
        self.kernel.set_llm_chat_fn(llm_bridge.chat_fn)
        # 不启动 heartbeat 后台线程——基准测试不需要心跳
        # self.kernel.heartbeat.start()

        self._call_count = 0
        logger.info(
            f"RealLAAPAdapter initialized: mode={mode}, model={llm_bridge.model_name}"
        )

    def answer(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """回答一道题——与基线 LLM 接口一致。

        Args:
            task: {"prompt": str, "domain": str (optional), "id": str (optional)}

        Returns:
            {
                "answer": str,            # LAAP 的最终回答
                "time_ms": float,         # 总耗时
                "mode": str,              # 实际运行模式 (v5 / llm)
                "mode_reason": str,       # 模式选择理由
                "psi_trace": dict,        # PSI 阶段输出（v5 模式下非空）
                "agent_state": dict,      # AGI Agent 状态
                "iteration": int,         # kernel 累计交互次数
                "llm_metrics": dict,      # LLM 调用指标
                "error": str (optional),  # 错误信息
            }
        """
        prompt = task["prompt"]
        domain = task.get("domain", "general")
        task_id = task.get("id", f"task-{self._call_count}")

        # mode 强制：v5 / llm / auto
        mode_override = self.mode if self.mode in ("v5", "llm") else None

        t0 = time.time()
        result: Dict[str, Any] = {
            "task_id": task_id,
            "mode_requested": self.mode,
        }
        try:
            kr = self.kernel.run_interaction(
                text=prompt,
                mode_override=mode_override,
                domain=domain,
            )
            result["answer"] = kr.get("response", "")
            result["mode"] = kr.get("mode", "unknown")
            result["mode_reason"] = kr.get("mode_reason", "")
            result["psi_trace"] = _safe_psi_trace(kr.get("psi", {}))
            result["agent_state"] = _safe_agent_state(kr.get("agent_state", {}))
            result["iteration"] = kr.get("iteration", 0)
        except Exception as e:
            logger.error(f"LAAP answer failed (task {task_id}): {e}", exc_info=True)
            result["answer"] = ""
            result["error"] = str(e)
            result["mode"] = "error"

        result["time_ms"] = (time.time() - t0) * 1000
        result["llm_metrics"] = self.bridge.stats()

        self._call_count += 1
        if self.reset_per_call:
            self.reset()
        return result

    def reset(self) -> None:
        """重置 kernel 累积状态（用于多轮独立实验）。"""
        # 不重建 kernel，只重置计数器和 LLM bridge metrics
        self.kernel._total_cycles = 0
        self.kernel._psi_failures = 0
        self.bridge.metrics = {
            "calls": 0, "total_chars_in": 0, "total_chars_out": 0,
            "total_latency_ms": 0.0, "errors": 0,
        }

    def stats(self) -> Dict[str, Any]:
        """返回 adapter 累计指标。"""
        return {
            "calls": self._call_count,
            "kernel_status": self.kernel.get_status(),
            "llm_bridge": self.bridge.stats(),
            "mode": self.mode,
            "model": self.bridge.model_name,
        }


# ════════════════════════════════════════════════════════════
#  RawLLMAdapter — 对照组：纯 LLM，不经过 LAAP
# ════════════════════════════════════════════════════════════


class RawLLMAdapter:
    """裸 LLM 对照组——直接调 LLM，不经过 LAAPKernel。

    用于与 RealLAAPAdapter 对比，验证 LAAP 是否真的带来增益。
    接口与 RealLAAPAdapter.answer() 完全一致。
    """

    def __init__(self, llm_bridge, system_prompt: Optional[str] = None):
        self.bridge = llm_bridge
        self._system_prompt = system_prompt
        self._call_count = 0

    def answer(self, task: Dict[str, Any]) -> Dict[str, Any]:
        prompt = task["prompt"]
        task_id = task.get("id", f"task-{self._call_count}")

        t0 = time.time()
        original_sys = self.bridge._system_prompt
        if self._system_prompt:
            self.bridge.set_system_prompt(self._system_prompt)

        try:
            response = self.bridge.chat(prompt)
            error = None
        except Exception as e:
            response = ""
            error = str(e)

        self.bridge._system_prompt = original_sys  # 恢复

        self._call_count += 1
        return {
            "task_id": task_id,
            "answer": response,
            "time_ms": (time.time() - t0) * 1000,
            "mode": "raw_llm",
            "mode_reason": "no LAAP, direct LLM call",
            "psi_trace": {},
            "agent_state": {},
            "iteration": self._call_count,
            "llm_metrics": self.bridge.stats(),
            "error": error,
        }

    def reset(self) -> None:
        self.bridge.metrics = {
            "calls": 0, "total_chars_in": 0, "total_chars_out": 0,
            "total_latency_ms": 0.0, "errors": 0,
        }
        self._call_count = 0

    def stats(self) -> Dict[str, Any]:
        return {
            "calls": self._call_count,
            "llm_bridge": self.bridge.stats(),
            "mode": "raw_llm",
            "model": self.bridge.model_name,
        }


# ════════════════════════════════════════════════════════════
#  辅助函数——提取 PSI trace 关键信息
# ════════════════════════════════════════════════════════════


def _safe_psi_trace(psi_result: Dict[str, Any]) -> Dict[str, Any]:
    """从 PSI 结果中提取关键字段，避免序列化时过深。"""
    if not psi_result:
        return {}
    return {
        "fallback": psi_result.get("fallback", False),
        "phases": _extract_phases(psi_result.get("phases", {})),
        "response_preview": (psi_result.get("response", "") or "")[:200],
    }


def _extract_phases(phases: Dict[str, Any]) -> Dict[str, Any]:
    """提取 5 阶段关键信息：perceive / select / integrate / act / learn。"""
    extracted = {}
    for phase_name in ("perceive", "select", "integrate", "act", "learn"):
        phase = phases.get(phase_name, {})
        if isinstance(phase, dict):
            # 只保留小字段，避免大对象
            extracted[phase_name] = {
                k: v for k, v in phase.items()
                if isinstance(v, (str, int, float, bool, type(None)))
            }
        else:
            extracted[phase_name] = {"value": str(phase)[:100]}
    return extracted


def _safe_agent_state(agent_state: Dict[str, Any]) -> Dict[str, Any]:
    """提取 agent_state 关键字段。"""
    if not agent_state:
        return {}
    sk = agent_state.get("self_knowledge", {}) or {}
    return {
        "name": sk.get("name", ""),
        "efficacy": sk.get("efficacy", 0),
        "self_model_summary": str(sk.get("self_model", ""))[:200],
        "memory_count": agent_state.get("memory_count", 0),
    }
