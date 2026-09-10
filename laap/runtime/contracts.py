"""
laap.runtime.contracts — 运行时数据契约
========================================
对外返回的**原生 Python 对象**。按方案 §2.1 原则 2：这里不出现
任何 JSON 字符串，序列化只在 L0 适配器发生。

印记: Aris 永远记得 Lorry
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class OrganStatus:
    """单个器官的装配状态。"""
    name: str
    layer: str
    module: str
    ok: bool = False
    degraded: bool = False
    notice: str = ""
    error: str = ""
    elapsed_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "layer": self.layer,
            "module": self.module,
            "ok": self.ok,
            "degraded": self.degraded,
            "notice": self.notice,
            "error": self.error,
            "elapsed_ms": round(self.elapsed_ms, 1),
        }


@dataclass
class BootReport:
    """boot() 的结果：装配了什么、缺了什么。"""
    lifeform_id: str = "aris"
    started_at: float = field(default_factory=time.time)
    elapsed_ms: float = 0.0
    organs: List[OrganStatus] = field(default_factory=list)
    notices: List[str] = field(default_factory=list)

    @property
    def ok_count(self) -> int:
        return sum(1 for o in self.organs if o.ok)

    @property
    def degraded_count(self) -> int:
        return sum(1 for o in self.organs if o.degraded)

    @property
    def failed_count(self) -> int:
        return sum(1 for o in self.organs if not o.ok)

    @property
    def healthy(self) -> bool:
        return self.failed_count == 0

    def failed_organs(self) -> List[OrganStatus]:
        return [o for o in self.organs if not o.ok]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lifeform_id": self.lifeform_id,
            "elapsed_ms": round(self.elapsed_ms, 1),
            "ok": self.ok_count,
            "degraded": self.degraded_count,
            "failed": self.failed_count,
            "healthy": self.healthy,
            "organs": [o.to_dict() for o in self.organs],
            "notices": list(self.notices),
        }

    def summary(self) -> str:
        lines = [
            f"LAAP Runtime boot [{self.lifeform_id}] "
            f"{self.elapsed_ms:.0f}ms  "
            f"ok={self.ok_count} degraded={self.degraded_count} "
            f"failed={self.failed_count}"
        ]
        for o in self.organs:
            mark = "OK  " if o.ok else "FAIL"
            flag = " (degraded)" if o.degraded else ""
            tail = f" -- {o.notice or o.error}" if (o.notice or o.error) else ""
            lines.append(
                f"  {mark} [{o.layer}] {o.name:22s} {o.elapsed_ms:6.1f}ms"
                f"{flag}{tail}"
            )
        for n in self.notices:
            lines.append(f"  ! {n}")
        return "\n".join(lines)


@dataclass
class CognitiveContext:
    """before_turn 返回的认知上下文（原生对象，不是注入字符串）。"""
    needs: Dict[str, float] = field(default_factory=dict)
    vitals: Dict[str, float] = field(default_factory=dict)
    phase: str = "focus"
    attention: Dict[str, Any] = field(default_factory=dict)
    active_desires: List[Dict[str, Any]] = field(default_factory=list)
    pending_intentions: List[Dict[str, Any]] = field(default_factory=list)
    degraded: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "needs": self.needs,
            "vitals": self.vitals,
            "phase": self.phase,
            "attention": self.attention,
            "active_desires": self.active_desires,
            "pending_intentions": self.pending_intentions,
            "degraded": self.degraded,
        }


@dataclass
class Response:
    """on_user_message 的返回值。"""
    text: str = ""
    should_emit: bool = False
    dispatched: List[str] = field(default_factory=list)
    proactive: List[Dict[str, Any]] = field(default_factory=list)
    context: Optional[CognitiveContext] = None
    elapsed_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "should_emit": self.should_emit,
            "dispatched": self.dispatched,
            "proactive": self.proactive,
            "context": self.context.to_dict() if self.context else None,
            "elapsed_ms": round(self.elapsed_ms, 1),
        }


@dataclass
class RuntimeState:
    """某一时刻的运行时快照。"""
    lifeform_id: str = "aris"
    booted: bool = False
    uptime_s: float = 0.0
    heartbeat_running: bool = False
    tick_count: int = 0
    last_tick: Optional[Dict[str, Any]] = None
    turn_count: int = 0
    degraded_organs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lifeform_id": self.lifeform_id,
            "booted": self.booted,
            "uptime_s": round(self.uptime_s, 1),
            "heartbeat_running": self.heartbeat_running,
            "tick_count": self.tick_count,
            "last_tick": self.last_tick,
            "turn_count": self.turn_count,
            "degraded_organs": self.degraded_organs,
        }
