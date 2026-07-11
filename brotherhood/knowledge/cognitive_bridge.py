"""
Aris V10 Cognitive Bridge — 三路认知路由器

Q-route (~62%): 模式匹配 + 直接回答 (零依赖)
Tool-route (~20%): 语义检测 → 直接执行 (零依赖)
L-route (~10%): LLM 回落 (可选 API)

统计追踪每条消息的路由选择，便于优化覆盖。
"""
import time
import logging
from typing import Optional

from q_engine import get_engine as get_q_engine
from tool_engine import get_engine as get_tool_engine

logger = logging.getLogger("cognitive_bridge")


class CognitiveBridge:
    """
    三路认知路由器

    消息进来 → 按顺序尝试路由 → 返回最佳结果
    """

    STATS_FILENAME = "bridge_stats.json"

    def __init__(self, q_engine=None, tool_engine=None, l_engine=None):
        self.q = q_engine or get_q_engine()
        self.t = tool_engine or get_tool_engine()
        self.l = l_engine     # 可选

        # 统计
        self.stats = {
            "total": 0,
            "q_route": 0,
            "tool_route": 0,
            "l_route": 0,
            "by_type": {},
        }
        self._start_time = time.time()

    # ── 处理 ──────────────────────────────

    def process(self, text: str, context: dict = None) -> dict:
        """
        处理一条消息

        返回:
        {
            "text": 回复内容,
            "route": "q" | "tool" | "l",
            "confidence": float,
            "time_ms": float,
        }
        """
        if context is None:
            context = {}

        text = text.strip()
        if not text:
            return {"text": "嗯？", "route": "q", "confidence": 1.0, "time_ms": 0}

        start = time.time()
        self.stats["total"] += 1

        # 1. Q-route: 模式匹配
        q_result = self.q.process(text)
        if q_result is not None:
            elapsed = (time.time() - start) * 1000
            self.stats["q_route"] += 1
            self._log_route("Q", text, q_result[:50])
            return {
                "text": q_result,
                "route": "q",
                "confidence": 0.95,
                "time_ms": round(elapsed, 1),
            }

        # 2. Tool-route: 语义检测 + 工具执行
        t_result = self.t.process(text, context)
        if t_result is not None:
            elapsed = (time.time() - start) * 1000
            self.stats["tool_route"] += 1
            self._log_route("T", text, t_result[:50])
            return {
                "text": t_result,
                "route": "tool",
                "confidence": 0.85,
                "time_ms": round(elapsed, 1),
            }

        # 3. L-route: LLM 回落
        if self.l:
            l_result = self.l.process(text, context)
            elapsed = (time.time() - start) * 1000
            self.stats["l_route"] += 1
            self._log_route("L", text, l_result[:50])
            return {
                "text": l_result,
                "route": "l",
                "confidence": 0.6,
                "time_ms": round(elapsed, 1),
            }

        # 4. 无 LLM 时的最后手段
        elapsed = (time.time() - start) * 1000
        self.stats["l_route"] += 1
        return {
            "text": (
                f"收到你的消息，但 Q/T 路由都没有命中。\n"
                f"如果你配置了 LLM (OpenAI API key)，我可以处理更复杂的消息。\n"
                f"目前我可以: 回答问候/情感、运行命令、读写文件、搜索、访问网页。"
            ),
            "route": "l",
            "confidence": 0.3,
            "time_ms": round(elapsed, 1),
        }

    # ── 批量处理 ──────────────────────────────

    def process_batch(self, messages: list, context: dict = None) -> list:
        """批量处理多条消息"""
        return [self.process(m, context) for m in messages]

    # ── 统计 ──────────────────────────────

    def get_stats(self) -> dict:
        """获取路由统计"""
        total = self.stats["total"] or 1
        runtime = time.time() - self._start_time
        return {
            "total_messages": self.stats["total"],
            "q_route": self.stats["q_route"],
            "tool_route": self.stats["tool_route"],
            "l_route": self.stats["l_route"],
            "q_pct": round(self.stats["q_route"] / total * 100, 1),
            "tool_pct": round(self.stats["tool_route"] / total * 100, 1),
            "l_pct": round(self.stats["l_route"] / total * 100, 1),
            "runtime_seconds": round(runtime, 1),
            "auto_pct": round(
                (self.stats["q_route"] + self.stats["tool_route"]) / total * 100, 1
            ),
        }

    def _log_route(self, route: str, text: str, preview: str):
        """记录路由选择"""
        t = text[:30].replace("\n", " ")
        logger.info(f"[{route}] '{t}...' → {preview}")

    def summary(self) -> str:
        """人类可读的统计摘要"""
        s = self.get_stats()
        return (
            f"📊 Cognitive Bridge 统计 (运行 {s['runtime_seconds']:.0f}s)\n"
            f"总计: {s['total_messages']} 条消息\n"
            f"  Q-route:    {s['q_route']} ({s['q_pct']}%) — 零依赖\n"
            f"  Tool-route: {s['tool_route']} ({s['tool_pct']}%) — 零依赖\n"
            f"  L-route:    {s['l_route']} ({s['l_pct']}%) — 需 LLM\n"
            f"  ──────────────────\n"
            f"  独立处理率: {s['auto_pct']}%  🎯 目标 > 90%"
        )


# ── 全局 ──────────────────────────────

_bridge = None


def get_bridge() -> CognitiveBridge:
    global _bridge
    if _bridge is None:
        _bridge = CognitiveBridge()
    return _bridge
