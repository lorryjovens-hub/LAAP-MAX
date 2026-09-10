"""
LAAP 去中心化认知节点网络 + 数字孪生 v1.0
===========================================
白皮书第 14.4 节（基础设施生态）和第 16.2.3 节（数字孪生体）对应。

认知节点网络:
  - P2P 节点发现 (UDP 广播 + 手动配置)
  - 任务路由 (复杂度评估 → 节点选择)
  - 经验共享 (认知经验广播 + 接收)
  - 节点信誉 (基于任务完成质量)
  - 心跳维护 (节点存活检测)

数字孪生体:
  - 云端认知镜像 (状态同步)
  - 仿真预演 (在云端预演任务)
  - 硬件迁移 (认知状态导出/导入)
  - 远程监控 (状态查询)

用法:
  # 节点
  node = CognitiveNode(node_id="edge-001")
  await node.start()
  await node.broadcast_experience({"task": "pickup", "result": "success"})

  # 数字孪生
  twin = DigitalTwin(node_id="robot-001")
  twin.sync_state({"position": [1,2,3], "battery": 0.8})
  forecast = twin.predict("battery", horizon=10)
"""

import asyncio
import json
import logging
import socket
import struct
import time
import uuid
import hashlib
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from collections import defaultdict

logger = logging.getLogger("laap.node_network")


# ════════════════════════════════════════════════════════════
# 常量
# ════════════════════════════════════════════════════════════

DISCOVERY_PORT = 11521
HEARTBEAT_INTERVAL = 30       # 心跳间隔 (秒)
NODE_TIMEOUT = 90             # 节点超时 (秒)
MAX_PEERS = 50                # 最大对等节点数
EXPERIENCE_BROADCAST_PORT = 11522

class NodeType(str, Enum):
    FULL_COGNITIVE  = "full_cognitive"    # 全认知节点
    LIGHT_COGNITIVE = "light_cognitive"   # 轻量认知节点
    SPECIALIZED     = "specialized"       # 专用节点 (推理/记忆/感知)
    VERIFIER        = "verifier"          # 验证节点
    EDGE            = "edge"              # 边缘节点

class NodeStatus(str, Enum):
    ONLINE     = "online"
    OFFLINE    = "offline"
    BUSY       = "busy"
    DEGRADED   = "degraded"
    MAINTENANCE = "maintenance"

class TaskType(str, Enum):
    INFERENCE      = "inference"
    MEMORY_RETRIEVAL = "memory_retrieval"
    CAUSAL_REASONING = "causal_reasoning"
    HALLUCINATION_CHECK = "hallucination_check"
    MULTIMODAL     = "multimodal"
    EVOLUTION      = "evolution"
    CUSTOM         = "custom"

class TwinSyncMode(str, Enum):
    REALTIME   = "realtime"      # 实时同步
    BATCH      = "batch"         # 批量同步
    ON_DEMAND  = "on_demand"     # 按需同步


# ════════════════════════════════════════════════════════════
# 认知节点数据结构
# ════════════════════════════════════════════════════════════

@dataclass
class NodeInfo:
    """节点信息"""
    node_id: str
    node_type: NodeType = NodeType.LIGHT_COGNITIVE
    address: str = "127.0.0.1"
    port: int = DISCOVERY_PORT
    status: NodeStatus = NodeStatus.ONLINE
    capabilities: List[str] = field(default_factory=list)
    load: float = 0.0               # 当前负载 0-1
    reputation: float = 0.5         # 信誉 0-1
    last_heartbeat: float = field(default_factory=time.time)
    first_seen: float = field(default_factory=time.time)
    completed_tasks: int = 0
    failed_tasks: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_alive(self) -> bool:
        return (time.time() - self.last_heartbeat) < NODE_TIMEOUT

    def success_rate(self) -> float:
        total = self.completed_tasks + self.failed_tasks
        return self.completed_tasks / total if total > 0 else 0.0


@dataclass
class CognitiveTask:
    """认知任务"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    task_type: TaskType = TaskType.INFERENCE
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: float = 0.5
    complexity: float = 0.5
    timeout_seconds: float = 30
    assigned_node: str = ""
    result: Optional[Dict] = None
    status: str = "pending"       # pending | assigned | completed | failed
    created_at: float = field(default_factory=time.time)

@dataclass
class SharedExperience:
    """共享经验"""
    experience_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    source_node: str = ""
    task_type: TaskType = TaskType.INFERENCE
    description: str = ""
    outcome: str = "success"      # success | failure | partial
    learning: str = ""            # 学到的经验
    confidence: float = 0.5
    tags: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


# ════════════════════════════════════════════════════════════
# 认知节点
# ════════════════════════════════════════════════════════════

class CognitiveNode:
    """
    去中心化认知节点 — P2P 网络中的单个节点。

    白皮书 14.4.1 的工程实现。
    """

    def __init__(
        self,
        node_id: str,
        node_type: NodeType = NodeType.LIGHT_COGNITIVE,
        address: str = "127.0.0.1",
        port: int = DISCOVERY_PORT,
    ):
        self.info = NodeInfo(
            node_id=node_id,
            node_type=node_type,
            address=address,
            port=port,
            capabilities=self._infer_capabilities(node_type),
        )
        self._peers: Dict[str, NodeInfo] = {}
        self._tasks: Dict[str, CognitiveTask] = {}
        self._experiences: List[SharedExperience] = []
        self._running = False
        self._discovery_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._on_experience_received: List[Callable] = []
        self._task_handlers: Dict[TaskType, Callable] = {}
        logger.info(f"认知节点初始化: {node_id} ({node_type.value})")

    def _infer_capabilities(self, node_type: NodeType) -> List[str]:
        caps = {
            NodeType.FULL_COGNITIVE: [
                "inference", "memory", "causal", "hallucination_check",
                "multimodal", "evolution", "verification",
            ],
            NodeType.LIGHT_COGNITIVE: [
                "inference", "memory", "hallucination_check",
            ],
            NodeType.SPECIALIZED: ["inference", "causal"],
            NodeType.VERIFIER: ["verification"],
            NodeType.EDGE: ["inference", "memory"],
        }
        return caps.get(node_type, ["inference"])

    # ── 生命周期 ────────────────────────────────────────

    async def start(self):
        """启动节点 (开始发现 + 心跳)"""
        self._running = True
        self._discovery_task = asyncio.create_task(self._discovery_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"节点 {self.info.node_id} 已启动")

    async def stop(self):
        """停止节点"""
        self._running = False
        if self._discovery_task:
            self._discovery_task.cancel()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        self.info.status = NodeStatus.OFFLINE
        logger.info(f"节点 {self.info.node_id} 已停止")

    # ── P2P 发现 ────────────────────────────────────────

    async def _discovery_loop(self):
        """节点发现循环"""
        while self._running:
            await self._broadcast_presence()
            await self._sweep_stale_peers()
            await asyncio.sleep(HEARTBEAT_INTERVAL)

    async def _broadcast_presence(self):
        """广播自身存在 (UDP)"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(1)

            msg = json.dumps({
                "type": "discovery",
                "node_id": self.info.node_id,
                "node_type": self.info.node_type.value,
                "address": self.info.address,
                "port": self.info.port,
                "capabilities": self.info.capabilities,
                "reputation": self.info.reputation,
                "load": self.info.load,
                "timestamp": time.time(),
            }).encode()

            sock.sendto(msg, ("255.255.255.255", DISCOVERY_PORT))
            sock.close()
        except Exception:
            pass  # 静默失败（网络不可用时）

    def add_peer_manual(self, address: str, port: int, node_id: str = "") -> None:
        """手动添加对等节点"""
        nid = node_id or f"peer_{address}:{port}"
        self._peers[nid] = NodeInfo(
            node_id=nid,
            address=address,
            port=port,
            status=NodeStatus.ONLINE,
            capabilities=["inference", "memory"],
            last_heartbeat=time.time(),
        )

    async def _sweep_stale_peers(self):
        """清理过期节点"""
        stale = [nid for nid, peer in self._peers.items() if not peer.is_alive()]
        for nid in stale:
            self._peers[nid].status = NodeStatus.OFFLINE
            del self._peers[nid]
        if stale:
            logger.debug(f"清理 {len(stale)} 个过期节点")

    # ── 心跳 ────────────────────────────────────────────

    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._running:
            self.info.last_heartbeat = time.time()
            await asyncio.sleep(HEARTBEAT_INTERVAL)

    # ── 任务路由 ─────────────────────────────────────────

    async def submit_task(self, task: CognitiveTask) -> str:
        """提交任务到网络"""
        self._tasks[task.task_id] = task

        # 选择最佳节点
        best_node = self._select_node(task)
        if best_node:
            task.assigned_node = best_node.node_id
            task.status = "assigned"
            logger.info(f"任务 {task.task_id} 分配给 {best_node.node_id}")
        else:
            task.status = "failed"
            logger.warning(f"任务 {task.task_id} 无可用的节点")

        return task.task_id

    def _select_node(self, task: CognitiveTask) -> Optional[NodeInfo]:
        """选择最佳节点处理任务"""
        candidates = [
            peer for peer in self._peers.values()
            if peer.is_alive()
            and peer.status == NodeStatus.ONLINE
            and any(c in peer.capabilities for c in self._task_capability(task.task_type))
        ]

        if not candidates:
            return None

        # 评分：信誉 * 0.5 + (1-负载) * 0.3 + 成功率 * 0.2
        scored = []
        for node in candidates:
            score = (
                node.reputation * 0.5 +
                (1.0 - node.load) * 0.3 +
                node.success_rate() * 0.2
            )
            scored.append((node, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0] if scored else None

    def _task_capability(self, task_type: TaskType) -> List[str]:
        return {
            TaskType.INFERENCE: ["inference"],
            TaskType.MEMORY_RETRIEVAL: ["memory"],
            TaskType.CAUSAL_REASONING: ["causal"],
            TaskType.HALLUCINATION_CHECK: ["hallucination_check"],
            TaskType.MULTIMODAL: ["multimodal"],
            TaskType.EVOLUTION: ["evolution"],
        }.get(task_type, ["inference"])

    # ── 经验共享 ─────────────────────────────────────────

    async def broadcast_experience(self, experience: SharedExperience) -> None:
        """广播经验到网络"""
        experience.source_node = self.info.node_id
        self._experiences.append(experience)

        # 通过 UDP 广播
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(1)

            msg = json.dumps({
                "type": "experience",
                **asdict(experience),
            }).encode()

            sock.sendto(msg, ("255.255.255.255", EXPERIENCE_BROADCAST_PORT))
            sock.close()
        except Exception:
            pass

        logger.info(f"经验广播: {experience.description[:80]}")

    def receive_experience(self, experience: SharedExperience) -> None:
        """接收来自其他节点的经验"""
        self._experiences.append(experience)
        logger.info(f"收到经验: {experience.source_node} → {experience.description[:60]}")

        # 触发回调
        for cb in self._on_experience_received:
            try:
                cb(experience)
            except Exception:
                pass

    def on_experience(self, callback: Callable):
        """注册经验接收回调"""
        self._on_experience_received.append(callback)

    # ── 查询 ────────────────────────────────────────────

    def get_peers(self) -> List[NodeInfo]:
        return [p for p in self._peers.values() if p.is_alive()]

    def get_peer_count(self) -> int:
        return len(self.get_peers())

    def get_experiences(self, limit: int = 50) -> List[SharedExperience]:
        return self._experiences[-limit:]

    def get_tasks(self) -> List[CognitiveTask]:
        return list(self._tasks.values())

    def get_status(self) -> Dict[str, Any]:
        return {
            "node": asdict(self.info),
            "peers": self.get_peer_count(),
            "tasks": len(self._tasks),
            "experiences": len(self._experiences),
            "running": self._running,
        }


# ════════════════════════════════════════════════════════════
# 数字孪生体
# ════════════════════════════════════════════════════════════

@dataclass
class TwinState:
    """数字孪生状态快照"""
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    entity_id: str = ""
    timestamp: float = field(default_factory=time.time)
    # 认知状态
    memory_snapshot: Dict[str, Any] = field(default_factory=dict)
    motivation_state: Dict[str, float] = field(default_factory=dict)
    attention_focus: str = ""
    cognitive_load: float = 0.0
    # 物理状态 (机器人)
    position: List[float] = field(default_factory=list)  # [x, y, z]
    orientation: List[float] = field(default_factory=list)  # [roll, pitch, yaw]
    joint_states: Dict[str, float] = field(default_factory=dict)
    battery_level: float = 1.0
    # 环境状态
    environment_map: Dict[str, Any] = field(default_factory=dict)
    nearby_objects: List[Dict] = field(default_factory=list)
    # 任务状态
    active_tasks: List[Dict] = field(default_factory=list)
    task_history: List[Dict] = field(default_factory=list)


class DigitalTwin:
    """
    数字孪生体 — 物理/虚拟智能体的云端镜像。

    白皮书 16.2.3 的工程实现。
    """

    def __init__(self, entity_id: str, sync_mode: TwinSyncMode = TwinSyncMode.BATCH):
        self.entity_id = entity_id
        self.sync_mode = sync_mode
        self._snapshots: List[TwinState] = []
        self._current_state = TwinState(entity_id=entity_id)
        self._prediction_log: List[Dict] = []
        self._simulation_results: List[Dict] = []
        self._max_snapshots = 1000
        logger.info(f"数字孪生体初始化: {entity_id}")

    # ── 状态同步 ────────────────────────────────────────

    def sync_state(self, state_update: Dict[str, Any]) -> TwinState:
        """
        同步状态 — 物理实体推送状态更新到孪生体。

        Args:
            state_update: 状态更新字典，可包含 position, battery, joint_states 等

        Returns:
            更新后的 TwinState
        """
        self._current_state.timestamp = time.time()

        for key, value in state_update.items():
            if hasattr(self._current_state, key):
                setattr(self._current_state, key, value)

        # 创建快照
        current_dict = asdict(self._current_state)
        snapshot = TwinState(
            entity_id=self.entity_id,
            **{k: v for k, v in current_dict.items()
               if k in TwinState.__dataclass_fields__ and k not in ("entity_id", "snapshot_id", "timestamp")},
        )
        self._snapshots.append(snapshot)
        if len(self._snapshots) > self._max_snapshots:
            self._snapshots = self._snapshots[-self._max_snapshots:]

        return snapshot

    def get_current_state(self) -> TwinState:
        """获取当前状态"""
        return self._current_state

    def get_snapshot_history(self, limit: int = 50) -> List[TwinState]:
        """获取历史快照"""
        return self._snapshots[-limit:]

    # ── 仿真预演 ────────────────────────────────────────

    async def simulate(
        self,
        action: str,
        parameters: Dict[str, Any],
        horizon: int = 10,
    ) -> Dict[str, Any]:
        """
        在数字孪生体中预演一个动作。

        Args:
            action: 动作名称
            parameters: 动作参数
            horizon: 预测步长

        Returns:
            仿真结果 {predicted_outcome, confidence, risk, alternative_actions}
        """
        # 简化的仿真引擎
        current = self._current_state

        result = {
            "action": action,
            "parameters": parameters,
            "horizon": horizon,
            "predicted_outcome": "success",
            "confidence": 0.7,
            "risk": 0.0,
            "alternative_actions": [],
            "estimated_energy_cost": 0.0,
            "estimated_time_ms": 0.0,
        }

        # 电池检查
        if current.battery_level < 0.1:
            result["predicted_outcome"] = "failure"
            result["risk"] = 0.9
            result["alternative_actions"] = ["recharge", "low_power_mode"]
        elif current.battery_level < 0.3:
            result["risk"] = 0.3
            result["estimated_energy_cost"] = 0.15

        # 碰撞检查 (简化)
        if action in ("move", "navigate", "grasp"):
            nearby = current.nearby_objects
            if nearby:
                result["risk"] = min(0.5, len(nearby) * 0.1)
                result["alternative_actions"] = ["replan_path", "wait"]

        self._simulation_results.append(result)
        return result

    # ── 预测 ────────────────────────────────────────────

    def predict(self, entity_property: str, horizon: int = 10) -> Dict[str, Any]:
        """
        预测实体属性在未来 horizon 步的状态。

        Args:
            entity_property: 属性名 (如 "battery", "position")
            horizon: 预测步长

        Returns:
            预测结果
        """
        if len(self._snapshots) < 2:
            return {"predicted": None, "confidence": 0.0}

        recent = self._snapshots[-10:]
        prediction = {
            "property": entity_property,
            "horizon": horizon,
            "predicted": None,
            "confidence": 0.5,
            "trend": "stable",
        }

        # 简单趋势外推
        if entity_property == "battery_level":
            values = [s.battery_level for s in recent]
            if len(values) >= 2:
                delta = (values[-1] - values[0]) / len(values)
                predicted = max(0.0, values[-1] + delta * horizon)
                prediction["predicted"] = round(predicted, 3)
                prediction["trend"] = "falling" if delta < 0 else "rising"
                prediction["confidence"] = 0.6

        elif entity_property == "cognitive_load":
            values = [s.cognitive_load for s in recent]
            if len(values) >= 2:
                delta = (values[-1] - values[0]) / len(values)
                predicted = max(0.0, min(1.0, values[-1] + delta * horizon))
                prediction["predicted"] = round(predicted, 3)
                prediction["trend"] = "rising" if delta > 0 else "falling"
                prediction["confidence"] = 0.5

        self._prediction_log.append(prediction)
        return prediction

    # ── 硬件迁移 ────────────────────────────────────────

    def export_state(self) -> Dict[str, Any]:
        """导出完整状态 (用于硬件迁移)"""
        return {
            "entity_id": self.entity_id,
            "current_state": asdict(self._current_state),
            "snapshot_count": len(self._snapshots),
            "exported_at": time.time(),
        }

    def import_state(self, state_data: Dict[str, Any]) -> None:
        """导入状态 (从旧硬件迁移)"""
        if "current_state" in state_data:
            self.entity_id = state_data.get("entity_id", self.entity_id)
            self._current_state = TwinState(
                **{k: v for k, v in state_data["current_state"].items()
                   if k in TwinState.__dataclass_fields__},
            )
            logger.info(f"数字孪生状态迁移: {self.entity_id}")

    # ── 查询 ────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "snapshots": len(self._snapshots),
            "simulations": len(self._simulation_results),
            "predictions": len(self._prediction_log),
            "battery": self._current_state.battery_level,
            "cognitive_load": self._current_state.cognitive_load,
            "active_tasks": len(self._current_state.active_tasks),
            "last_sync": self._current_state.timestamp,
        }


# ════════════════════════════════════════════════════════════
# 全局工厂
# ════════════════════════════════════════════════════════════

_nodes: Dict[str, CognitiveNode] = {}
_twins: Dict[str, DigitalTwin] = {}


def get_or_create_node(
    node_id: str,
    node_type: NodeType = NodeType.LIGHT_COGNITIVE,
) -> CognitiveNode:
    if node_id not in _nodes:
        _nodes[node_id] = CognitiveNode(node_id=node_id, node_type=node_type)
    return _nodes[node_id]


def get_or_create_twin(
    entity_id: str,
    sync_mode: TwinSyncMode = TwinSyncMode.BATCH,
) -> DigitalTwin:
    if entity_id not in _twins:
        _twins[entity_id] = DigitalTwin(entity_id=entity_id, sync_mode=sync_mode)
    return _twins[entity_id]
