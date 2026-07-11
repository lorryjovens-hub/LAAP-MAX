"""Ψ-Net 多实例本地测试床.

封装真实 ``PsiNetConnector`` 与轻量化 Mock 实现，提供统一的本地多实例启动、
互连、规则广播与接收等待 API，用于宏观层跨实例概念传播实验。

当真实连接器无法导入或启动失败时，自动回退到 Mock 实现，保证实验仍可运行。
"""

from __future__ import annotations

import hashlib
import json
import random
import socket
import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# 确保项目根目录在 sys.path 中，以便导入 harness.laap_coding.core.psi_net_connector
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

try:
    from harness.laap_coding.core.psi_net_connector import (
        EventPriority,
        MessageType,
        PsiMessage,
        PsiNetConnector,
        RateBuffer,
    )

    _REAL_CONNECTOR_AVAILABLE = True
except Exception as _import_exc:  # noqa: BLE001
    _REAL_CONNECTOR_AVAILABLE = False

    class MessageType(Enum):
        CAUSAL_RULE = "causal_rule"
        SPECIES_UPDATE = "species_update"
        COMPILATION_RESULT = "compilation_result"
        PING = "ping"
        PONG = "pong"
        HEARTBEAT = "heartbeat"

    class EventPriority(Enum):
        LOW = 0
        MEDIUM = 1
        HIGH = 2
        CRITICAL = 3

    @dataclass
    class PsiMessage:
        type: MessageType
        sender: str
        timestamp: float
        payload: Dict[str, Any]
        priority: EventPriority = EventPriority.MEDIUM
        signature: str = ""

        def to_dict(self) -> Dict[str, Any]:
            return {
                "type": self.type.value,
                "sender": self.sender,
                "timestamp": self.timestamp,
                "priority": self.priority.value,
                "signature": self.signature,
                "payload": self.payload,
            }

        @classmethod
        def from_dict(cls, data: Dict[str, Any]) -> "PsiMessage":
            return cls(
                type=MessageType(data["type"]),
                sender=data["sender"],
                timestamp=data["timestamp"],
                priority=EventPriority(data.get("priority", 1)),
                signature=data.get("signature", ""),
                payload=data["payload"],
            )

        def _compute_signature(self) -> str:
            content = (
                f"{self.type.value}:{self.sender}:{self.timestamp}:"
                f"{json.dumps(self.payload, sort_keys=True)}"
            )
            return hashlib.sha256(content.encode()).hexdigest()

        def sign(self) -> None:
            self.signature = self._compute_signature()

        def verify(self) -> bool:
            if not self.signature:
                return True
            return self.signature == self._compute_signature()

    class RateBuffer:
        def __init__(self, max_events_per_second: float = 1.0):
            self._max_events = max_events_per_second
            self._buffer: List[PsiMessage] = []
            self._last_flush = time.time()
            self._lock = threading.Lock()
            self._dedupe_cache: Dict[str, float] = {}

        def add(self, message: PsiMessage) -> None:
            with self._lock:
                dedupe_key = (
                    f"{message.type.value}:{message.sender}:"
                    f"{json.dumps(message.payload, sort_keys=True)}"
                )
                now = time.time()
                if dedupe_key in self._dedupe_cache:
                    if now - self._dedupe_cache[dedupe_key] < 5.0:
                        return
                self._dedupe_cache[dedupe_key] = now
                self._buffer.append(message)

        def flush(self) -> List[PsiMessage]:
            with self._lock:
                now = time.time()
                elapsed = now - self._last_flush
                max_to_flush = int(self._max_events * elapsed)
                if max_to_flush <= 0:
                    return []
                self._buffer.sort(key=lambda m: m.priority.value, reverse=True)
                to_flush = self._buffer[:max_to_flush]
                self._buffer = self._buffer[max_to_flush:]
                self._last_flush = now
                return to_flush

        def get_size(self) -> int:
            with self._lock:
                return len(self._buffer)


class MockPsiNetConnector:
    """内存级 Ψ-Net 连接器，接口与真实 PsiNetConnector 保持一致."""

    DEFAULT_PORT = 11551
    HEARTBEAT_INTERVAL = 30

    _registry: Dict[int, "MockPsiNetConnector"] = {}
    _registry_lock = threading.Lock()

    def __init__(self, instance_id: Optional[str] = None, port: Optional[int] = None):
        self.instance_id = instance_id or f"mock-{id(self):x}"
        self.port = port or self.DEFAULT_PORT
        self._peers: Dict[str, str] = {}
        self._message_handlers: Dict[str, List[Callable]] = {}
        self._rate_buffer = RateBuffer(max_events_per_second=1000.0)
        self._running = False
        self._received_messages: List[PsiMessage] = []
        self.rules: Dict[str, Any] = {}
        # 网络条件参数，由 PsiNetTestbed 注入
        self._network_latency_ms: float = 0.0
        self._message_dropout_prob: float = 0.0

    def start(self) -> None:
        self._running = True
        with self._registry_lock:
            self._registry[self.port] = self

    def stop(self) -> None:
        self._running = False
        with self._registry_lock:
            self._registry.pop(self.port, None)

    def connect_to_peer(self, host: str, port: int) -> bool:
        peer_addr = f"{host}:{port}"
        self._peers[peer_addr] = peer_addr
        return True

    def register_handler(self, message_type: str, handler: Callable) -> None:
        self._message_handlers.setdefault(message_type, []).append(handler)

    def _send_to_peer(
        self,
        peer_addr: str,
        message: PsiMessage,
        latency_ms: Optional[float] = None,
        dropout_prob: Optional[float] = None,
    ) -> bool:
        latency_ms = latency_ms if latency_ms is not None else self._network_latency_ms
        dropout_prob = dropout_prob if dropout_prob is not None else self._message_dropout_prob
        if random.random() < dropout_prob:
            return False
        if latency_ms > 0.0:
            time.sleep(latency_ms / 1000.0)
        _, port_str = peer_addr.split(":")
        port = int(port_str)
        with self._registry_lock:
            peer = self._registry.get(port)
        if peer is not None:
            peer._deliver_message(message)
            return True
        return False

    def _broadcast(
        self,
        message: PsiMessage,
        latency_ms: Optional[float] = None,
        dropout_prob: Optional[float] = None,
    ) -> int:
        sent = 0
        for peer_addr in list(self._peers.values()):
            if self._send_to_peer(peer_addr, message, latency_ms=latency_ms, dropout_prob=dropout_prob):
                sent += 1
        return sent

    def _deliver_message(self, message: PsiMessage) -> None:
        if not message.verify():
            return
        self._received_messages.append(message)
        self._rate_buffer.add(message)
        handlers = self._message_handlers.get(message.type.value, [])
        for handler in handlers:
            try:
                handler(message)
            except Exception:  # noqa: BLE001
                pass

    def send_causal_rule(
        self,
        rule: Dict[str, Any],
        priority: EventPriority = EventPriority.HIGH,
        latency_ms: Optional[float] = None,
        dropout_prob: Optional[float] = None,
    ) -> int:
        message = PsiMessage(
            type=MessageType.CAUSAL_RULE,
            sender=self.instance_id,
            timestamp=time.time(),
            payload=rule,
            priority=priority,
        )
        message.sign()
        return self._broadcast(message, latency_ms=latency_ms, dropout_prob=dropout_prob)

    def flush_buffer(self) -> List[PsiMessage]:
        return self._rate_buffer.flush()

    def get_stats(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "port": self.port,
            "peers": len(self._peers),
            "received_messages": len(self._received_messages),
            "buffer_size": self._rate_buffer.get_size(),
        }


class PsiNetTestbed:
    """在本地启动并连接多个 Ψ-Net 连接器实例."""

    def __init__(
        self,
        ports: List[int],
        *,
        use_mock: Optional[bool] = None,
        network_latency_ms: float = 0.0,
        message_dropout_prob: float = 0.0,
        buffer_rate: float = 1000.0,
    ):
        self.ports = ports
        self.network_latency_ms = network_latency_ms
        self.message_dropout_prob = message_dropout_prob
        self.buffer_rate = buffer_rate
        self.instances: List[Any] = []
        self._explicit_mock = use_mock
        self.use_mock = self._resolve_use_mock(use_mock)
        self.connector_class = MockPsiNetConnector if self.use_mock else PsiNetConnector
        self._fallback_reason: Optional[str] = None

    def _resolve_use_mock(self, use_mock: Optional[bool]) -> bool:
        """根据显式参数与可用性决定使用真实还是 Mock 连接器."""
        if use_mock is True:
            return True
        if not _REAL_CONNECTOR_AVAILABLE:
            self._fallback_reason = f"真实连接器导入失败: {_import_exc}"
            return True
        if use_mock is False:
            return False
        # 自动检测：若端口均未被占用则尝试真实连接器
        for port in self.ports:
            if not self._is_port_free(port):
                self._fallback_reason = f"端口 {port} 已被占用，回退到 Mock"
                return True
        return False

    @staticmethod
    def _is_port_free(port: int, host: str = "127.0.0.1") -> bool:
        """检查目标端口是否未被监听."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            return sock.connect_ex((host, port)) != 0

    @property
    def fallback_reason(self) -> Optional[str]:
        return self._fallback_reason

    def start(self) -> None:
        """按端口顺序创建并启动实例，并建立全互联拓扑."""
        for idx, port in enumerate(self.ports):
            instance = self.connector_class(instance_id=f"instance_{idx}", port=port)
            # 实验期间需要高频刷新 RateBuffer，以便每轮都能处理接收到的规则
            instance._rate_buffer = RateBuffer(max_events_per_second=self.buffer_rate)
            instance.rules = {}
            instance.start()
            self.instances.append(instance)

        # 给真实 socket server 留足绑定与监听时间
        time.sleep(0.3 if not self.use_mock else 0.05)

        # 注册默认规则处理器：收到因果规则后写入 instance.rules
        for instance in self.instances:
            instance.register_handler(MessageType.CAUSAL_RULE.value, self._make_rule_handler(instance))

        # 建立全连接拓扑：每个实例连接所有其他实例
        for instance in self.instances:
            for peer_port in self.ports:
                if peer_port != instance.port:
                    instance.connect_to_peer("127.0.0.1", peer_port)

        # 对 Mock 实例注入网络条件参数
        if self.use_mock:
            for instance in self.instances:
                instance._network_latency_ms = self.network_latency_ms
                instance._message_dropout_prob = self.message_dropout_prob

    def _make_rule_handler(self, instance: Any) -> Callable:
        def handler(message: PsiMessage) -> None:
            rule = message.payload
            rule_id = rule.get("rule_id")
            if rule_id:
                instance.rules[rule_id] = rule

        return handler

    def stop(self) -> None:
        """停止所有实例并清理状态."""
        for instance in self.instances:
            instance.stop()
        self.instances.clear()

    def broadcast_rule(
        self,
        sender_idx: int,
        rule: Dict[str, Any],
        priority: EventPriority = EventPriority.HIGH,
    ) -> int:
        """从指定实例广播因果规则，返回成功送达的同伴数量."""
        instance = self.instances[sender_idx]
        if self.use_mock:
            return instance.send_causal_rule(
                rule,
                priority=priority,
                latency_ms=self.network_latency_ms,
                dropout_prob=self.message_dropout_prob,
            )
        # 真实连接器暂不支持显式网络条件，由底层 socket 提供真实延迟
        result = instance.send_causal_rule(rule, priority=priority)
        return result if isinstance(result, int) else len(self.instances) - 1

    def wait_for_rule(
        self,
        receiver_idx: int,
        rule_id: str,
        timeout: float = 30.0,
        poll_interval: float = 0.01,
    ) -> tuple[bool, float]:
        """等待指定实例接收到某条规则.

        Returns:
            (success, elapsed_seconds)
        """
        instance = self.instances[receiver_idx]
        start = time.perf_counter()
        while time.perf_counter() - start < timeout:
            if rule_id in instance.rules:
                return True, time.perf_counter() - start
            # 触发 flush，确保真实连接器的缓冲消息也被处理
            instance.flush_buffer()
            time.sleep(poll_interval)
        return False, time.perf_counter() - start

    def get_rule_holders(self, rule_id: str) -> List[int]:
        """返回持有指定规则的实例索引列表."""
        return [idx for idx, inst in enumerate(self.instances) if rule_id in inst.rules]

    def get_hold_rate(self, rule_id: str) -> float:
        """返回指定规则的群体持有率."""
        if not self.instances:
            return 0.0
        return len(self.get_rule_holders(rule_id)) / len(self.instances)

    def all_instances_have_rule(self, rule_id: str) -> bool:
        return all(rule_id in inst.rules for inst in self.instances)
