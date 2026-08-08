"""Multi-Agent — 多智能体系统: AgentRegistry + EventBus + SafeRollback"""
from __future__ import annotations
import time, logging, threading, uuid, json
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger("laap_brain.multi_agent")

__all__ = ["AgentRegistry", "EventBus", "SafeRollback", "AgentRole", "AgentInfo"]


class AgentRole(Enum):
    LEADER = "leader"
    WORKER = "worker"
    OBSERVER = "observer"
    CRITIC = "critic"
    COORDINATOR = "coordinator"


@dataclass
class AgentInfo:
    id: str = ""
    name: str = ""
    role: AgentRole = AgentRole.WORKER
    status: str = "idle"           # idle|busy|error|offline
    capabilities: List[str] = field(default_factory=list)
    registered_at: float = 0.0
    metadata: dict = field(default_factory=dict)


@dataclass
class Event:
    type: str = ""
    data: Any = None
    source: str = ""
    timestamp: float = 0.0
    id: str = ""


# ════════════════════════════════════════════════════════════
# EventBus — 事件总线
# ════════════════════════════════════════════════════════════

class EventBus:
    """轻量级事件总线，支持发布/订阅"""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._history: List[Event] = []
        self._max_history = 100
        self._lock = threading.Lock()

    def on(self, event_type: str, handler: Callable):
        """订阅事件"""
        with self._lock:
            self._handlers[event_type].append(handler)

    def off(self, event_type: str, handler: Callable = None):
        """取消订阅"""
        with self._lock:
            if handler:
                self._handlers[event_type] = [h for h in self._handlers[event_type] if h != handler]
            else:
                self._handlers[event_type] = []

    def emit(self, event_type: str, data: Any = None, source: str = ""):
        """发布事件"""
        event = Event(
            type=event_type, data=data, source=source,
            timestamp=time.time(), id=uuid.uuid4().hex[:8],
        )
        with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]
            handlers = list(self._handlers.get(event_type, []))
            wildcard = list(self._handlers.get("*", []))

        for h in handlers + wildcard:
            try:
                h(event)
            except Exception as e:
                logger.warning(f"Event handler error ({event_type}): {e}")

    def history(self, event_type: str = None, limit: int = 20) -> List[Event]:
        """查看事件历史"""
        with self._lock:
            events = self._history
            if event_type:
                events = [e for e in events if e.type == event_type]
            return events[-limit:]

    def clear(self):
        with self._lock:
            self._handlers.clear()
            self._history.clear()


from collections import defaultdict


# ════════════════════════════════════════════════════════════
# AgentRegistry — 代理注册表
# ════════════════════════════════════════════════════════════

class AgentRegistry:
    """代理注册表 — 管理多智能体生命周期"""

    def __init__(self, event_bus: EventBus = None):
        self._agents: Dict[str, AgentInfo] = {}
        self._instances: Dict[str, Any] = {}
        self.bus = event_bus or EventBus()
        self._lock = threading.Lock()

    def register(self, agent_id: str, instance: Any = None,
                 name: str = "", role=None,
                 capabilities: List[str] = None) -> AgentInfo:
        """注册一个代理"""
        if role is None:
            role = AgentRole.WORKER
        elif isinstance(role, str):
            try:
                role = AgentRole(role)
            except ValueError:
                role = AgentRole.WORKER
        info = AgentInfo(
            id=agent_id, name=name or agent_id,
            role=role, status="idle",
            capabilities=capabilities or [],
            registered_at=time.time(),
        )
        with self._lock:
            self._agents[agent_id] = info
            if instance:
                self._instances[agent_id] = instance
        self.bus.emit("agent:registered", {"id": agent_id, "name": info.name})
        logger.info(f"Agent registered: {info.name} ({role.value})")
        return info

    def unregister(self, agent_id: str):
        """注销代理"""
        with self._lock:
            self._agents.pop(agent_id, None)
            self._instances.pop(agent_id, None)
        self.bus.emit("agent:unregistered", {"id": agent_id})

    def get(self, agent_id: str) -> Optional[AgentInfo]:
        return self._agents.get(agent_id)

    def get_instance(self, agent_id: str) -> Any:
        return self._instances.get(agent_id)

    def list(self, role: AgentRole = None, status: str = None) -> List[AgentInfo]:
        with self._lock:
            agents = list(self._agents.values())
        if role:
            agents = [a for a in agents if a.role == role]
        if status:
            agents = [a for a in agents if a.status == status]
        return agents

    def set_status(self, agent_id: str, status: str):
        with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].status = status
                self.bus.emit("agent:status_change", {"id": agent_id, "status": status})

    def broadcast(self, event_type: str, data: Any = None):
        """向所有注册代理广播事件"""
        self.bus.emit(event_type, data)
        with self._lock:
            for aid in list(self._agents.keys()):
                inst = self._instances.get(aid)
                if inst and hasattr(inst, "handle_event"):
                    try:
                        inst.handle_event(event_type, data)
                    except Exception as e:
                        logger.warning(f"Agent {aid} handle_event error: {e}")

    def stats(self) -> dict:
        with self._lock:
            total = len(self._agents)
            by_role = {}
            by_status = {}
            for a in self._agents.values():
                by_role[a.role.value] = by_role.get(a.role.value, 0) + 1
                by_status[a.status] = by_status.get(a.status, 0) + 1
            return {"total": total, "by_role": by_role, "by_status": by_status}


# ════════════════════════════════════════════════════════════
# SafeRollback — 安全回滚
# ════════════════════════════════════════════════════════════

class SafeRollback:
    """安全回滚机制 — 快照 → 变异 → 回滚"""

    def __init__(self):
        self._snapshots: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def snapshot(self, name: str, data: Any = None) -> str:
        """创建快照"""
        key = f"{name}_{uuid.uuid4().hex[:6]}"
        with self._lock:
            self._snapshots[key] = data
        logger.debug(f"Snapshot created: {key}")
        return key

    def rollback(self, key: str) -> Optional[Any]:
        """回滚到快照"""
        with self._lock:
            data = self._snapshots.pop(key, None)
        if data is None:
            logger.warning(f"Rollback key not found: {key}")
        return data

    def list_snapshots(self) -> List[str]:
        with self._lock:
            return list(self._snapshots.keys())

    def clear(self):
        with self._lock:
            self._snapshots.clear()
