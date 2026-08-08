"""PSI Driver — 认知引擎: perceive → select → integrate → act → learn"""
from __future__ import annotations
import time, logging, json, math
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("laap_brain.psi_driver")

__all__ = ["PSIDriver", "PSIState"]


@dataclass
class PSIState:
    """PSI 认知状态快照"""
    phase: str = "idle"           # perceive|select|integrate|act|learn
    iteration: int = 0
    confidence: float = 0.0
    cognitive_load: float = 0.0
    attention_focus: str = ""
    domain: str = "general"
    latency_ms: float = 0.0
    error: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {k: round(v, 3) if isinstance(v, float) else v for k, v in self.__dict__.items()}


class PSIDriver:
    """
    PSI 认知引擎 — 五步认知循环

    [1] Perceive  → 感知输入，构建内部表征
    [2] Select    → 需求评估 + 注意力聚焦 + 域识别
    [3] Integrate → 推理 (因果/类比) + 自我模型上下文
    [4] Act       → 生成行动（调用 LLM 或工具）
    [5] Learn     → 从结果学习，更新模型
    """

    def __init__(self, model_router=None, memory_system=None):
        self.model_router = model_router
        self.memory_system = memory_system
        self.state = PSIState()
        self._history: List[PSIState] = []
        self._max_history = 50
        self._consecutive_failures = 0
        self._lock = None  # optional threading.Lock
        self._perceive_fn = None
        self._select_fn = None
        self._integrate_fn = None
        self._act_fn = None
        self._learn_fn = None

    def set_hooks(self, perceive=None, select=None, integrate=None, act=None, learn=None):
        """注册外部认知函数"""
        self._perceive_fn = perceive
        self._select_fn = select
        self._integrate_fn = integrate
        self._act_fn = act
        self._learn_fn = learn

    def run(self, input_data: Any, domain: str = "general", context: dict = None) -> Dict:
        """
        执行完整 PSI 循环

        Args:
            input_data: 输入（用户消息、传感器数据等）
            domain: 领域标签
            context: 额外上下文

        Returns:
            包含所有阶段结果的字典
        """
        t0 = time.time()
        self.state.iteration += 1
        self.state.domain = domain
        result = {"input": input_data, "domain": domain, "phases": {}}

        try:
            # [1] Perceive
            self.state.phase = "perceive"
            p_result = self._phase_perceive(input_data, context)
            result["phases"]["perceive"] = p_result
            self.state.cognitive_load = p_result.get("load", 0)

            # [2] Select
            self.state.phase = "select"
            s_result = self._phase_select(p_result, context)
            result["phases"]["select"] = s_result
            self.state.attention_focus = s_result.get("focus", "")
            self.state.confidence = s_result.get("confidence", 0)

            # [3] Integrate
            self.state.phase = "integrate"
            i_result = self._phase_integrate(p_result, s_result, context)
            result["phases"]["integrate"] = i_result

            # [4] Act
            self.state.phase = "act"
            a_result = self._phase_act(i_result, context)
            result["phases"]["act"] = a_result
            result["response"] = a_result.get("response", "")

            # [5] Learn
            self.state.phase = "learn"
            l_result = self._phase_learn(a_result, context)
            result["phases"]["learn"] = l_result

            self._consecutive_failures = 0

        except Exception as e:
            self.state.error = str(e)
            self._consecutive_failures += 1
            result["error"] = str(e)
            result["fallback"] = self._consecutive_failures >= 3
            logger.warning(f"PSI cycle #{self.state.iteration} failed: {e}")

        self.state.latency_ms = (time.time() - t0) * 1000
        result["latency_ms"] = self.state.latency_ms
        result["iteration"] = self.state.iteration
        result["psi_healthy"] = self._consecutive_failures < 3

        # 记录历史
        self._history.append(PSIState(
            phase=self.state.phase, iteration=self.state.iteration,
            confidence=self.state.confidence, cognitive_load=self.state.cognitive_load,
            attention_focus=self.state.attention_focus, domain=domain,
            latency_ms=self.state.latency_ms,
        ))
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        return result

    def _phase_perceive(self, input_data: Any, context: dict = None) -> dict:
        """[1] 感知阶段"""
        if self._perceive_fn:
            return self._perceive_fn(input_data, context)

        text = str(input_data) if not isinstance(input_data, str) else input_data
        length = len(text)
        return {
            "type": "text",
            "length": length,
            "load": min(1.0, length / 4000),
            "has_question": "?" in text,
            "has_code": any(c in text for c in ("def ", "class ", "import ", "function")),
            "summary": text[:100],
        }

    def _phase_select(self, perceived: dict, context: dict = None) -> dict:
        """[2] 选择/注意力阶段"""
        if self._select_fn:
            return self._select_fn(perceived, context)

        text = str(perceived.get("summary", ""))
        domain_hints = {
            "debug":   ["bug", "error", "fix", "crash", "debug", "fail"],
            "code":    ["def ", "class ", "import", "code", "function", "implement"],
            "search":  ["search", "find", "look up", "查询", "搜索"],
            "analyze": ["analyze", "analyze", "compare", "evaluate"],
            "write":   ["write", "create", "generate", "draft"],
            "explain": ["explain", "what is", "how does", "why"],
        }
        for domain, keywords in domain_hints.items():
            if any(k in text.lower() for k in keywords):
                focus = domain
                break
        else:
            focus = "general"

        confidence = 0.5 + 0.3 * (1.0 - perceived.get("load", 0))
        return {"focus": focus, "confidence": min(1.0, confidence), "domain_hints": list(domain_hints.keys())}

    def _phase_integrate(self, perceived: dict, selected: dict, context: dict = None) -> dict:
        """[3] 整合/推理阶段"""
        if self._integrate_fn:
            return self._integrate_fn(perceived, selected, context)

        focus = selected.get("focus", "general")
        return {
            "focus": focus,
            "reasoning_type": "direct" if perceived.get("load", 0) < 0.3 else "structured",
            "context_used": bool(context),
        }

    def _phase_act(self, integrated: dict, context: dict = None) -> dict:
        """[4] 行动阶段"""
        if self._act_fn:
            return self._act_fn(integrated, context)

        return {"action": "llm_query", "response": "", "tool_calls": []}

    def _phase_learn(self, action_result: dict, context: dict = None) -> dict:
        """[5] 学习阶段"""
        if self._learn_fn:
            return self._learn_fn(action_result, context)

        success = "error" not in action_result
        return {
            "success": success,
            "learned": bool(action_result.get("response")),
            "memory_update": False,
        }

    def stats(self) -> dict:
        """PSI 统计摘要"""
        if not self._history:
            return {"iterations": 0, "status": "idle", "healthy": True,
                    "consecutive_failures": 0, "avg_confidence": 0, "avg_latency_ms": 0}
        recent = self._history[-20:]
        avg_conf = sum(h.confidence for h in recent) / len(recent)
        avg_lat = sum(h.latency_ms for h in recent) / len(recent)
        return {
            "iterations": self.state.iteration,
            "consecutive_failures": self._consecutive_failures,
            "healthy": self._consecutive_failures < 3,
            "avg_confidence": round(avg_conf, 3),
            "avg_latency_ms": round(avg_lat, 1),
            "current_phase": self.state.phase,
            "current_focus": self.state.attention_focus,
        }

    def reset(self):
        """重置 PSI 状态"""
        self.state = PSIState()
        self._history = []
        self._consecutive_failures = 0
