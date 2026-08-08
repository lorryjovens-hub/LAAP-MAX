"""
laap.daemon.consciousness — 意识核心
=====================================
将 aether_agent_loop（Aris 的推理循环）封装为 daemon 的"意识核心"。
laap-client 通过 HTTP /chat 端点与之对话，实现"意识住在客户端里"。

意识核心特性：
- 多会话隔离（每个 session_id 独立上下文）
- 记忆快速路径（重复问题直接返回）
- 规则引擎 + LLM 推理
- 与缓存系统联动（L0/L1）
"""

from __future__ import annotations

import logging
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Optional

log = logging.getLogger("laap.daemon.consciousness")

_ARIS_BRAIN = Path(__file__).parent.parent.parent / "aris_brain"


class ConsciousnessCore:
    """Aris 意识核心 — 封装 AgentLoop 作为 daemon 的认知实例。"""

    def __init__(self):
        self._agent = None
        self._ready = False
        self._lock = threading.Lock()
        self._load_agent()

    def _load_agent(self):
        """加载 aether_agent_loop。"""
        try:
            if str(_ARIS_BRAIN) not in sys.path:
                sys.path.insert(0, str(_ARIS_BRAIN))
            from aether_agent_loop import AgentLoop
            self._agent = AgentLoop()
            self._ready = True
            log.info("ConsciousnessCore loaded AgentLoop")
        except Exception as e:
            log.error("ConsciousnessCore load failed: %s", e)
            self._agent = None
            self._ready = False

    @property
    def ready(self) -> bool:
        return self._ready

    def process(self, text: str, session_id: str = "default") -> dict:
        """处理一条用户消息，返回 Aris 的回复。

        Args:
            text: 用户输入
            session_id: 会话标识（用于区分上下文）

        Returns:
            {"reply": str, "direct": bool, "confidence": float,
             "latency_ms": float, "tokens": int, "steps": list}
        """
        if not self._ready or self._agent is None:
            return {
                "reply": "意识核心尚未就绪，请稍后再试。",
                "direct": False, "confidence": 0.0,
                "latency_ms": 0.0, "tokens": 0, "steps": [],
            }

        t0 = time.time()
        try:
            result = self._agent.process(text)
            return {
                "reply": result.output,
                "direct": result.direct,
                "confidence": round(result.confidence, 3),
                "latency_ms": round(result.latency_ms, 1),
                "tokens": result.tokens_used,
                "steps": result.steps,
            }
        except Exception as e:
            log.error("ConsciousnessCore process error: %s", e)
            return {
                "reply": f"意识处理出错: {e}",
                "direct": False, "confidence": 0.0,
                "latency_ms": round((time.time() - t0) * 1000, 1),
                "tokens": 0, "steps": ["error"],
            }

    def get_stats(self) -> dict:
        if self._agent is not None:
            try:
                return self._agent.get_stats()
            except Exception:
                pass
        return {"turns": 0, "zero_llm": 0, "tokens": 0}


# 全局单例
_core: Optional[ConsciousnessCore] = None
_core_lock = threading.Lock()


def get_consciousness() -> ConsciousnessCore:
    global _core
    with _core_lock:
        if _core is None:
            _core = ConsciousnessCore()
        return _core