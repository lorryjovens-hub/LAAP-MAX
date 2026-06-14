"""
Aris V7 — 认知总线 (CognitiveBus)
====================================
协处理器注册、事件路由、多声带调度。

所有模块通过 CognitiveBus 通信:
  感知模块 → 发布事件 → 总线路由 → 认知模块订阅
  认知模块 → 发布结果 → 总线路由 → 声带输出
"""

from __future__ import annotations
import time, json, logging, threading
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("aris.bus")


class EventType(Enum):
    PERCEPTION_INCOMING = "perception_incoming"
    PREDICTION_ERROR = "prediction_error"
    CONSCIOUS_FRAME = "conscious_frame"
    ATTENTION_SHIFT = "attention_shift"
    EMOTION_CHANGED = "emotion_changed"
    NEED_CHANGED = "need_changed"
    VOICE_REQUEST = "voice_request"
    VOICE_RESPONSE = "voice_response"
    ARCHITECTURE_EVENT = "architecture_event"


@dataclass
class BusEvent:
    type: EventType
    source: str
    data: Dict[str, Any]
    timestamp: float = 0.0
    priority: int = 0  # 0=normal, 1=high, 2=critical

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class CognitiveBus:
    """
    V7 认知总线 — 模块间事件路由。
    
    任何模块都可以:
      - publish(event) — 发布事件
      - subscribe(type, callback) — 订阅事件
      - register_coprocessor(name, handler) — 注册协处理器
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._coprocessors: Dict[str, Callable] = {}
        self._event_log: List[BusEvent] = []
        self._max_log = 1000
        self._start_time = time.time()

    # ── 发布/订阅 ──

    def publish(self, event: BusEvent):
        """发布一个事件到总线上"""
        with self._lock:
            self._event_log.append(event)
            if len(self._event_log) > self._max_log:
                self._event_log = self._event_log[-self._max_log:]

        # 通知订阅者
        subscribers = list(self._subscribers.get(event.type, []))
        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.warning(f"Bus subscriber error: {e}")

    def subscribe(self, event_type: EventType, callback: Callable):
        """订阅特定类型的事件"""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable):
        with self._lock:
            if event_type in self._subscribers:
                self._subscribers[event_type] = [
                    cb for cb in self._subscribers[event_type] if cb != callback
                ]

    # ── 协处理器注册 ──

    def register_coprocessor(self, name: str, handler: Callable):
        """
        注册一个协处理器（例如: 声带LLM、本地推理、外部工具）。
        handler 接收 (event) → 返回结果
        """
        self._coprocessors[name] = handler
        logger.info(f"Bus: coprocessor '{name}' registered")

    def unregister_coprocessor(self, name: str):
        self._coprocessors.pop(name, None)

    def call_coprocessor(self, name: str, event: BusEvent) -> Optional[Any]:
        """调用指定的协处理器"""
        handler = self._coprocessors.get(name)
        if handler:
            return handler(event)
        return None

    # ── 便利方法 ──

    def publish_perception(self, source: str, data: Dict):
        """快捷: 发布感知事件"""
        self.publish(BusEvent(EventType.PERCEPTION_INCOMING, source, data))

    def publish_prediction_error(self, source: str, error_magnitude: float, detail: str = ""):
        """快捷: 发布预测误差 — 驱动注意力转向"""
        self.publish(BusEvent(
            EventType.PREDICTION_ERROR, source,
            {"error": error_magnitude, "detail": detail},
            priority=1 if error_magnitude > 0.5 else 0,
        ))

    def publish_voice_request(self, source: str, text: str, task_type: str = "daily"):
        """快捷: 请求声带输出"""
        self.publish(BusEvent(
            EventType.VOICE_REQUEST, source,
            {"text": text, "task_type": task_type},
        ))

    # ── 统计 ──

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            event_counts = {}
            for event in self._event_log:
                event_counts[event.type.value] = event_counts.get(event.type.value, 0) + 1
            return {
                "uptime": round(time.time() - self._start_time),
                "total_events": len(self._event_log),
                "event_breakdown": event_counts,
                "subscribers": {k.value: len(v) for k, v in self._subscribers.items()},
                "coprocessors": list(self._coprocessors.keys()),
            }
