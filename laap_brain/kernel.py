"""LAAPKernel — PSI 驱动主循环

PSI 认知循环: perceive → select → integrate → act → learn

架构:
  Hermes = 传输层（工具/LLM）
  LAAP   = 认知层（PSI Kernel）

LLM ↔ V5 转换:
  - Mode "llm": 标准 LLM 推理（Hermes 原生）
  - Mode "v5":  PSI 增强认知（LAAP Kernel）
  - Mode "auto": 自动选择（复杂任务用 v5，简单用 llm）
"""
from __future__ import annotations
import time, logging, threading, json
from typing import Any, Callable, Dict, List, Optional, Tuple

from laap_brain.psi_driver import PSIDriver, PSIState
from laap_brain.core import AGIAgent
from laap_brain.multi_agent import AgentRegistry, EventBus, SafeRollback
from laap_brain.evolution_engine import GitHubFusion, LearningLoop, MemoryOptimizer
from laap_brain.heartbeat_daemon import Heartbeat

logger = logging.getLogger("laap_brain.kernel")

__all__ = ["LAAPKernel", "LLMv5Converter"]


# ════════════════════════════════════════════════════════════
# LLM ↔ V5 转换器
# ════════════════════════════════════════════════════════════

class LLMv5Converter:
    """
    LLM ↔ V5 认知模式转换器

    支持三种模式:
      - "llm":  标准 LLM，走 Hermes 原生工具+LLM
      - "v5":   PSI 增强，经 LAAP Kernel 认知处理后再调用 LLM
      - "auto": 自动根据任务复杂度选择

    自动选择规则:
      - 包含代码/多步/分析性任务 → v5
      - 简单问答/闲聊 → llm
    """

    AUTO_V5_KEYWORDS = [
        "debug", "analyze", "implement", "refactor", "design",
        "compare", "evaluate", "optimize", "research", "investigate",
        "架构", "设计", "实现", "调试", "优化", "分析",
    ]

    def __init__(self, default_mode: str = "auto"):
        self.default_mode = default_mode
        self._mode_history: List[Tuple[str, str, str]] = []  # (input, mode, reason)

    def classify(self, text: str, mode_override: str = None) -> Tuple[str, str]:
        """
        分类输入并返回模式

        Args:
            text: 用户输入
            mode_override: 手动指定模式

        Returns:
            (mode, reason) 例如 ("v5", "包含代码关键词")
        """
        if mode_override and mode_override in ("llm", "v5"):
            reason = f"手动指定: {mode_override}"
            self._mode_history.append((text[:50], mode_override, reason))
            return (mode_override, reason)

        if self.default_mode == "llm":
            return ("llm", "默认 LLM 模式")
        if self.default_mode == "v5":
            return ("v5", "默认 V5 模式")

        # auto 模式：分析任务复杂度
        force_v5 = any(k in text.lower() for k in self.AUTO_V5_KEYWORDS)
        is_long = len(text) > 200
        has_code = any(c in text for c in ("def ", "class ", "import ", "{", "}", "->"))

        if force_v5 or is_long or has_code:
            reasons = []
            if force_v5: reasons.append("含分析关键词")
            if is_long: reasons.append("输入较长")
            if has_code: reasons.append("含代码")
            mode, reason = ("v5", "+".join(reasons))
        else:
            mode, reason = ("llm", "简单任务")

        self._mode_history.append((text[:50], mode, reason))
        return (mode, reason)

    def get_stats(self) -> dict:
        if not self._mode_history:
            return {"total": 0}
        modes = {}
        for _, m, _ in self._mode_history:
            modes[m] = modes.get(m, 0) + 1
        return {"total": len(self._mode_history), "modes": modes}


# ════════════════════════════════════════════════════════════
# LAAPKernel — PSI 主循环
# ════════════════════════════════════════════════════════════

class LAAPKernel:
    """
    LAAPKernel — PSI 驱动认知内核

    管理完整的 PSI 认知循环，集成所有 v5 子模块。
    Hermes 作为传输层，本 Kernel 作为认知层。

    用法:
        kernel = LAAPKernel(model="deepseek-v4-flash")
        kernel.initialize()
        kernel.run()
    """

    def __init__(self, model: str = "deepseek-v4-flash", psi_mode: str = "auto"):
        self.model = model
        self.psi_mode = psi_mode
        self.version = "5.0.0"

        # 子模块
        self.psi = PSIDriver()
        self.agent = AGIAgent(name="Ao", enable_all=True)
        self.event_bus = EventBus()
        self.registry = AgentRegistry(event_bus=self.event_bus)
        self.rollback = SafeRollback()
        self.heartbeat = Heartbeat()
        self.evolution_github = GitHubFusion()
        self.learning_loop = LearningLoop()
        self.memory_optimizer = MemoryOptimizer()
        self.converter = LLMv5Converter(default_mode=psi_mode)

        self._initialized = False
        self._running = False
        self._psi_failures = 0
        self._total_cycles = 0
        self._start_time = 0.0

        # LLM 回调（由 Hermes 注册）
        self._llm_chat_fn: Callable = None

    def initialize(self):
        """初始化所有子模块"""
        if self._initialized:
            return

        logger.info(f"LAAPKernel v{self.version} initializing...")

        # 注册心跳 tick 回调
        def on_heartbeat(vitals):
            pass  # 可扩展：更新 UI 等

        self.heartbeat = Heartbeat(on_tick=on_heartbeat)

        # 注册 PSI 回调
        self.psi.set_hooks(
            perceive=self._psi_perceive,
            select=self._psi_select,
            integrate=self._psi_integrate,
            act=self._psi_act,
            learn=self._psi_learn,
        )

        # 注册默认代理
        self.registry.register(
            "laap-kernel", instance=self,
            name="LAAP Kernel", role="leader",
            capabilities=["psi", "cognition", "evolution", "memory"],
        )

        self._initialized = True
        self._start_time = time.time()
        logger.info(f"LAAPKernel v{self.version} initialized ✓")

    def run(self):
        """启动 Kernel（阻塞）"""
        if not self._initialized:
            self.initialize()

        self._running = True
        self.heartbeat.start()
        logger.info("LAAPKernel running (heartbeat 60bpm)")

        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        """安全关闭"""
        self._running = False
        self.heartbeat.stop()
        logger.info("LAAPKernel shut down")

    # ═══ LLM 回调注册 ═══

    def set_llm_chat_fn(self, fn: Callable):
        """注册 LLM 聊天函数（由 Hermes 提供）"""
        self._llm_chat_fn = fn

    # ═══ 核心交互接口 ═══

    def run_interaction(self, text: str, mode_override: str = None,
                        domain: str = "general") -> Dict:
        """
        运行一次完整的交互

        Args:
            text: 用户输入
            mode_override: "llm" | "v5" | None (使用 auto 判断)
            domain: 领域标签

        Returns:
            {"response": "...", "mode": "...", "psi": {...}}
        """
        if not self._initialized:
            self.initialize()

        # 1. 模式选择
        mode, reason = self.converter.classify(text, mode_override)
        self._total_cycles += 1

        if mode == "llm":
            # 直接走 LLM（跳过 PSI 认知循环）
            return self._run_llm(text, domain)

        # 2. PSI 增强路径
        psi_result = self.psi.run(text, domain=domain)

        if psi_result.get("fallback"):
            self._psi_failures += 1
            # 3 次失败后降级到 LLM
            if self._psi_failures >= 3:
                logger.warning("PSI 连续失败3次，降级到 LLM 模式")
                return self._run_llm(text, domain)

        # 3. 更新 AGI Agent
        score = psi_result.get("phases", {}).get("learn", {}).get("success", False)
        self.agent.process_interaction(
            text, domain=domain,
            action_outcome={"action": "psi_cycle", "score": 0.7 if score else 0.3, "success": score},
        )

        # 4. 学习
        self.learning_loop.observe(text, domain, score)
        self.heartbeat.apply_event("success" if score else "challenge")

        # 5. 构建响应
        response = psi_result.get("response", "")
        if not response and self._llm_chat_fn:
            # 如果 PSI 未生成响应，回退到 LLM
            response = self._llm_chat_fn(text)

        return {
            "response": response,
            "mode": mode,
            "mode_reason": reason,
            "psi": psi_result,
            "agent_state": self.agent.get_state(),
            "iteration": self._total_cycles,
        }

    def _run_llm(self, text: str, domain: str = "general") -> Dict:
        """纯 LLM 模式"""
        response = ""
        if self._llm_chat_fn:
            response = self._llm_chat_fn(text)

        self.agent.process_interaction(text, domain=domain)
        self.learning_loop.observe(text, domain, bool(response))
        self.heartbeat.apply_event("idle")

        return {
            "response": response,
            "mode": "llm",
            "mode_reason": "直接 LLM",
            "agent_state": self.agent.get_state(),
            "iteration": self._total_cycles,
        }

    # ═══ PSI 阶段回调 ═══

    def _psi_perceive(self, input_data, context):
        text = str(input_data)
        return {
            "type": "text",
            "length": len(text),
            "load": min(1.0, len(text) / 2000),
            "has_question": "?" in text or "？" in text,
            "has_code": any(c in text for c in ("def ", "class ", "import ", "{")),
            "language": "zh" if any("\u4e00" <= c <= "\u9fff" for c in text) else "en",
        }

    def _psi_select(self, perceived, context):
        text = str(perceived.get("summary", "")) or ""
        focus = "general"
        if perceived.get("has_code", False):
            focus = "code"
        elif perceived.get("has_question", False):
            focus = "qa"
        confidence = 0.6 + 0.3 * (1.0 - perceived.get("load", 0))
        return {"focus": focus, "confidence": min(1.0, confidence)}

    def _psi_integrate(self, perceived, selected, context):
        return {"focus": selected.get("focus", "general"), "reasoning": "direct"}

    def _psi_act(self, integrated, context):
        # 如果有 LLM 回调，调用它
        response = ""
        if self._llm_chat_fn:
            response = self._llm_chat_fn(integrated.get("focus", "general"))
        return {"action": "llm_query", "response": response}

    def _psi_learn(self, action_result, context):
        success = bool(action_result.get("response"))
        return {"success": success, "learned": success}

    # ═══ 状态接口 ═══

    def get_status(self) -> dict:
        """完整状态报告"""
        return {
            "version": self.version,
            "model": self.model,
            "psi_mode": self.psi_mode,
            "running": self._running,
            "initialized": self._initialized,
            "cycles": self._total_cycles,
            "psi_failures": self._psi_failures,
            "uptime": time.time() - self._start_time if self._start_time else 0,
            "heartbeat": self.heartbeat.stats(),
            "psi": self.psi.stats(),
            "agent": self.agent.get_state(),
            "converter": self.converter.get_stats(),
            "learning": self.learning_loop.stats(),
            "evolution": self.evolution_github.stats(),
            "memory": self.memory_optimizer.stats(),
            "registry": self.registry.stats(),
        }

    def get_summary(self) -> str:
        """人类可读摘要"""
        s = self.get_status()
        lines = [
            f"LAAP Kernel v{s['version']}",
            f"  Model: {s['model']} | Mode: {s['psi_mode']}",
            f"  Cycles: {s['cycles']} | PSI Failures: {s['psi_failures']} | Uptime: {s['uptime']:.0f}s",
            f"  Heartbeat: {'running' if s['heartbeat']['running'] else 'stopped'} | Ticks: {s['heartbeat']['tick_count']}",
            f"  Vitals: {s['heartbeat']['vitals']}",
            f"  PSI: {s['psi']}",
            f"  Agent: {s['agent']['self_knowledge']['name']} | Efficacy: {s['agent']['self_knowledge']['efficacy']}",
            f"  Learning: {s['learning']['total_observed']} obs, {s['learning']['skills_generated']} skills",
            f"  Memory: {s['memory']['memories']} items, {s['memory']['fisher_params']} fisher params",
        ]
        return "\n".join(lines)

    def info(self) -> str:
        """快速状态行"""
        s = self.get_status()
        v = s['heartbeat']['vitals']
        return (f"Kernel v{s['version']} | {s['cycles']} cycles | "
                f"⚡{v['energy']:.0%} 🎯{v['focus']:.0%} 💚{v['mood']:.0%} | "
                f"PSI: {s['psi']['healthy']}")
