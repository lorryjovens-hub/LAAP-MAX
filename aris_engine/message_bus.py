"""
LAAP 统一消息总线 v1.0 — MessageBus
====================================
六层架构间的异步通信基础设施。

设计原则:
  - Actor 模型: 每层是一个逻辑 Actor，通过消息总线通信
  - 类型安全: 每种消息类型有明确的 Schema
  - 可观测: 所有消息可追踪、可回放
  - 解耦: 层间不直接调用，全部通过总线

消息类型:
  PerceptionEvent   — L1→L2 感知输入
  FilteredEvent     — L2→L3 过滤后的安全输入
  CognitiveResult   — L3→L4 推理结果（含因果链）
  MemoryQuery       — L4 内部 记忆检索请求
  MemoryUpdate      — L4 内部 记忆更新请求
  DecisionIntent    — L5 决策意图
  EvolutionSignal   — L6 自进化信号
  SystemEvent       — 系统级事件（心跳、错误、重启）

用法:
  bus = MessageBus()
  bus.subscribe("perception", perception_handler)
  bus.publish(PerceptionEvent(source="text", payload={...}))
"""

import asyncio
import json
import time
import uuid
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Awaitable, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict

logger = logging.getLogger("laap.message_bus")

# ════════════════════════════════════════════════════════════
# 消息类型定义
# ════════════════════════════════════════════════════════════

class MessageType(str, Enum):
    """六层架构消息类型"""
    PERCEPTION_EVENT   = "perception_event"     # L1→L2
    FILTERED_EVENT     = "filtered_event"       # L2→L3
    COGNITIVE_RESULT   = "cognitive_result"     # L3→L4 + L5
    MEMORY_QUERY       = "memory_query"         # 内部
    MEMORY_UPDATE      = "memory_update"        # 内部
    DECISION_INTENT    = "decision_intent"      # L5→外部
    EVOLUTION_SIGNAL   = "evolution_signal"     # L6→各层
    SYSTEM_EVENT       = "system_event"         # 系统级
    ERROR_EVENT        = "error_event"          # 错误

class LayerID(str, Enum):
    PERCEPTION   = "L1_perception"
    FILTER       = "L2_filter"
    COGNITION    = "L3_cognition"
    MEMORY       = "L4_memory"
    DECISION     = "L5_decision"
    EVOLUTION    = "L6_evolution"
    SYSTEM       = "system"

class EventSource(str, Enum):
    TEXT      = "text"
    IMAGE     = "image"
    AUDIO     = "audio"
    SENSOR    = "sensor"
    WEB4_A2A  = "web4_a2a"
    WEB4_DID  = "web4_did"
    WEB4_CHAIN = "web4_chain"
    SYSTEM    = "system"

class PriorityLevel(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"

class AuthLevel(str, Enum):
    L0_FULL_AUTO = "L0"   # 完全自治
    L1_NOTIFY    = "L1"   # 通知后执行
    L2_CONFIRM   = "L2"   # 需确认
    L3_HUMAN     = "L3"   # 人工介入

# ════════════════════════════════════════════════════════════
# 消息数据结构
# ════════════════════════════════════════════════════════════

@dataclass
class Message:
    """统一消息基类"""
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    msg_type: MessageType = MessageType.SYSTEM_EVENT
    source_layer: LayerID = LayerID.SYSTEM
    target_layer: LayerID = LayerID.SYSTEM
    timestamp: float = field(default_factory=time.time)
    priority: PriorityLevel = PriorityLevel.MEDIUM
    correlation_id: str = ""       # 关联同一认知周期的消息
    trace_id: str = ""             # 追踪整个请求链
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["msg_type"] = self.msg_type.value
        d["source_layer"] = self.source_layer.value
        d["target_layer"] = self.target_layer.value
        d["priority"] = self.priority.value
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)

    @classmethod
    def from_dict(cls, d: Dict) -> "Message":
        d = d.copy()
        d["msg_type"] = MessageType(d["msg_type"])
        d["source_layer"] = LayerID(d["source_layer"])
        d["target_layer"] = LayerID(d["target_layer"])
        d["priority"] = PriorityLevel(d["priority"])
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class PerceptionEvent(Message):
    """L1 感知事件 → 进入 L2 预处理"""
    msg_type: MessageType = MessageType.PERCEPTION_EVENT
    source_layer: LayerID = LayerID.PERCEPTION
    target_layer: LayerID = LayerID.FILTER
    source: EventSource = EventSource.TEXT
    auth_level: AuthLevel = AuthLevel.L0_FULL_AUTO
    sender_did: str = ""            # Web4 场景: 发送者 DID
    raw_text: str = ""              # 原始文本输入
    raw_data: Dict[str, Any] = field(default_factory=dict)  # 非文本原始数据


@dataclass
class FilteredEvent(Message):
    """L2 过滤后的安全输入 → 进入 L3 认知推理"""
    msg_type: MessageType = MessageType.FILTERED_EVENT
    source_layer: LayerID = LayerID.FILTER
    target_layer: LayerID = LayerID.COGNITION
    original_event_id: str = ""     # 关联原始感知事件
    safe_text: str = ""             # 清洗后的文本
    safe_data: Dict[str, Any] = field(default_factory=dict)
    trust_score: float = 0.5        # 信息可信度 0-1
    noise_level: float = 0.0        # 噪声等级 0-1
    security_flags: List[str] = field(default_factory=list)  # 安全标记
    injection_detected: bool = False  # 是否检测到注入攻击
    injection_details: str = ""     # 注入详情


@dataclass
class CognitiveResult(Message):
    """L3 认知推理结果 → 进入 L4 记忆 + L5 决策"""
    msg_type: MessageType = MessageType.COGNITIVE_RESULT
    source_layer: LayerID = LayerID.COGNITION
    target_layer: LayerID = LayerID.MEMORY  # 同时发往 L4 和 L5
    # 推理输出
    reasoning_text: str = ""        # 推理结论
    causal_path: List[str] = field(default_factory=list)  # 因果路径节点 ID
    confidence: float = 0.5         # 置信度 0-1
    # 防幻觉三层锁结果
    hallucination_checks: Dict[str, Any] = field(default_factory=dict)
    # 注意力状态
    attention_focus: str = ""       # 当前注意力焦点
    attention_scores: Dict[str, float] = field(default_factory=dict)
    # 动机状态
    dominant_motivation: str = ""   # 主导动机
    motivation_scores: Dict[str, float] = field(default_factory=dict)
    # GWT 工作空间快照
    workspace_snapshot: List[Dict] = field(default_factory=list)


@dataclass
class MemoryQuery(Message):
    """记忆检索请求"""
    msg_type: MessageType = MessageType.MEMORY_QUERY
    source_layer: LayerID = LayerID.COGNITION
    target_layer: LayerID = LayerID.MEMORY
    query_text: str = ""
    query_vector: Optional[List[float]] = None
    top_k: int = 10
    filter_tags: List[str] = field(default_factory=list)
    min_weight: float = 0.0


@dataclass
class MemoryUpdate(Message):
    """记忆更新请求"""
    msg_type: MessageType = MessageType.MEMORY_UPDATE
    source_layer: LayerID = LayerID.COGNITION
    target_layer: LayerID = LayerID.MEMORY
    content: str = ""
    memory_type: str = "episodic"   # episodic | semantic | procedural
    importance: float = 0.5
    emotion_tag: str = ""
    causal_parents: List[str] = field(default_factory=list)


@dataclass
class DecisionIntent(Message):
    """L5 决策意图 → 输出"""
    msg_type: MessageType = MessageType.DECISION_INTENT
    source_layer: LayerID = LayerID.DECISION
    target_layer: LayerID = LayerID.SYSTEM
    # 意图
    intent_type: str = "chat_reply"  # chat_reply | skill_call | a2a_message | robot_action
    output_text: str = ""
    output_skill: Dict[str, Any] = field(default_factory=dict)
    output_a2a: Dict[str, Any] = field(default_factory=dict)
    # 安全
    permission_check: bool = True
    did_boundary_compliant: bool = True
    risk_level: AuthLevel = AuthLevel.L0_FULL_AUTO
    # 可追溯
    reasoning_trace: str = ""
    cognitive_result_id: str = ""


@dataclass
class EvolutionSignal(Message):
    """L6 自进化信号"""
    msg_type: MessageType = MessageType.EVOLUTION_SIGNAL
    source_layer: LayerID = LayerID.EVOLUTION
    target_layer: LayerID = LayerID.SYSTEM
    signal_type: str = "reflect"    # reflect | optimize | repair | alert
    target_module: str = ""         # 需要调整的模块
    description: str = ""
    params_before: Dict[str, Any] = field(default_factory=dict)
    params_after: Dict[str, Any] = field(default_factory=dict)
    fitness_delta: float = 0.0


@dataclass
class SystemEvent(Message):
    """系统级事件"""
    msg_type: MessageType = MessageType.SYSTEM_EVENT
    source_layer: LayerID = LayerID.SYSTEM
    event_type: str = "heartbeat"   # heartbeat | error | restart | config_change
    details: Dict[str, Any] = field(default_factory=dict)


# ════════════════════════════════════════════════════════════
# 消息总线核心
# ════════════════════════════════════════════════════════════

Handler = Callable[[Message], Awaitable[None]]


class MessageBus:
    """
    统一消息总线 — Actor 模型的核心通信层。

    特性:
      - 基于 topic 的发布/订阅
      - 支持通配符订阅 (layer.* 匹配所有该层的消息)
      - 消息历史追踪（可回放）
      - 异步处理
    """

    def __init__(self, trace_history: int = 1000):
        self._subscribers: Dict[str, List[Handler]] = defaultdict(list)
        self._history: List[Message] = []
        self._max_history = trace_history
        self._correlation_counters: Dict[str, int] = defaultdict(int)
        self._active = True
        self._stats = {
            "published": 0,
            "delivered": 0,
            "errors": 0,
            "start_time": time.time(),
        }
        logger.info("MessageBus 初始化完成")

    # ── 订阅管理 ────────────────────────────────────────

    def subscribe(self, topic: str, handler: Handler) -> None:
        """订阅消息主题。topic 可以是 'perception_event' 或 'L3_cognition' 等"""
        self._subscribers[topic].append(handler)
        logger.debug(f"订阅: {topic} → {handler.__name__ if hasattr(handler, '__name__') else 'anon'}")

    def unsubscribe(self, topic: str, handler: Handler) -> None:
        if topic in self._subscribers:
            self._subscribers[topic] = [h for h in self._subscribers[topic] if h is not handler]

    # ── 消息发布 ────────────────────────────────────────

    async def publish(self, msg: Message) -> str:
        """发布一条消息，返回 msg_id"""
        if not self._active:
            logger.warning("消息总线已停止，消息被丢弃")
            return msg.msg_id

        # 设置追踪 ID
        if not msg.trace_id:
            msg.trace_id = str(uuid.uuid4())[:12]
        if not msg.correlation_id:
            self._correlation_counters[msg.trace_id] += 1
            msg.correlation_id = f"{msg.trace_id}-{self._correlation_counters[msg.trace_id]}"

        # 记录历史
        self._history.append(msg)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        self._stats["published"] += 1

        # 分发到订阅者
        topics = self._resolve_topics(msg)
        for topic in topics:
            for handler in self._subscribers.get(topic, []):
                try:
                    await handler(msg)
                    self._stats["delivered"] += 1
                except Exception as e:
                    self._stats["errors"] += 1
                    logger.error(f"消息处理失败 [{topic}]: {e}", exc_info=True)

        return msg.msg_id

    def publish_sync(self, msg: Message) -> str:
        """同步发布（用于非异步上下文）"""
        return asyncio.get_event_loop().run_until_complete(self.publish(msg))

    # ── 辅助方法 ────────────────────────────────────────

    def _resolve_topics(self, msg: Message) -> List[str]:
        """解析消息应该发送到哪些 topic"""
        topics = [
            msg.msg_type.value,           # e.g. "perception_event"
            msg.source_layer.value,       # e.g. "L1_perception"
            msg.target_layer.value,       # e.g. "L2_filter"
            "*",                          # 全局监听
        ]
        return topics

    def new_correlation(self) -> str:
        """生成新的关联 ID，开始一个认知周期"""
        cid = str(uuid.uuid4())[:12]
        self._correlation_counters[cid] = 0
        return cid

    # ── 查询 ────────────────────────────────────────────

    def get_history(self, limit: int = 50, msg_type: Optional[str] = None) -> List[Message]:
        """获取消息历史"""
        msgs = self._history[-limit:]
        if msg_type:
            msgs = [m for m in msgs if m.msg_type.value == msg_type]
        return msgs

    def get_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "uptime": time.time() - self._stats["start_time"],
            "history_size": len(self._history),
            "active_subscribers": sum(len(v) for v in self._subscribers.values()),
            "topics": list(self._subscribers.keys()),
        }

    def stop(self) -> None:
        self._active = False
        logger.info("MessageBus 已停止")


# ════════════════════════════════════════════════════════════
# 全局单例
# ════════════════════════════════════════════════════════════

_bus: Optional[MessageBus] = None


def get_message_bus() -> MessageBus:
    global _bus
    if _bus is None:
        _bus = MessageBus()
    return _bus


def reset_message_bus() -> None:
    global _bus
    if _bus:
        _bus.stop()
    _bus = None
