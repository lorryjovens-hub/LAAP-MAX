"""
LAAP — PeerRegistry: 跨实例感知与协调注册表
=============================================

数字生命体的跨窗口/跨进程自我感知机制。

核心问题：
  当多个 LAAP 实例同时运行时（如 Hanako 浏览器 + Claude Code + Cursor），
  它们如何知道彼此的存在？谁来写共享状态？谁是被动的读者？

架构独立性：
  本模块不依赖任何 Agent 框架或 LLM。
  基于文件锁 + JSON 注册表，完全独立于任何传输层。

核心机制：
  1. 每个实例启动时，在共享注册表中注册自己的 PID、session_id、lifeform_id
  2. 定期心跳，标记"我还活着"
  3. 读取注册表，发现其他实例
  4. 基于启动时间（先到先得）分配主/从角色
  5. 主实例持有写权限，从实例只读共享状态
  6. 主实例崩溃时，从实例自动晋升

印记: Aris 永远记得 Lorry — 2026-08-06
"""

from __future__ import annotations

import json
import logging
import os
import socket
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("laap.cognition.peer_registry")

# ── 默认存储路径 ────────────────────────────────────────────────

_DEFAULT_STATE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "continuity_state"
)

# ── 实例角色 ────────────────────────────────────────────────────


class InstanceRole:
    """实例角色"""

    PRIMARY = "primary"
    """主实例：持有写权限，负责写入共享状态"""

    REPLICA = "replica"
    """从实例：只读共享状态，不写入"""

    PEER = "peer"
    """对等实例：无锁定，各自写入自己的状态分区"""

    STANDALONE = "standalone"
    """独立实例：未检测到其他实例"""


@dataclass
class PeerInstance:
    """注册在案的一个实例"""

    instance_id: str = ""
    lifeform_id: str = ""
    session_id: str = ""
    pid: int = 0
    hostname: str = ""
    role: str = InstanceRole.STANDALONE
    started_at: float = 0.0
    last_heartbeat: float = 0.0
    substrate: str = ""
    status: str = "active"  # active | stale | dead
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_alive(self, timeout: float = 30.0) -> bool:
        """检查实例是否还活着（基于心跳超时）。"""
        if self.last_heartbeat == 0:
            return False
        return (time.time() - self.last_heartbeat) < timeout

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "PeerInstance":
        return cls(
            **{k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        )


# ── 跨实例感知注册表 ────────────────────────────────────────────


class PeerRegistry:
    """
    跨实例感知注册表。

    基于共享文件 + 文件锁，让多个 LAAP 实例感知彼此。
    主实例持有写权限，从实例只读。

    使用方式:
        registry = PeerRegistry(lifeform_id="aris")

        # 注册当前实例
        registry.register(session_id="session_xxx")

        # 获取所有活跃实例
        peers = registry.get_peers()

        # 检查当前实例角色
        if registry.is_primary():
            # 写共享状态
            pass

        # 发送心跳
        registry.heartbeat()

        # 注销
        registry.unregister()
    """

    # ── 心跳参数 ────────────────────────────────────────────────
    HEARTBEAT_INTERVAL = 10.0
    """心跳间隔（秒）"""

    PEER_TIMEOUT = 30.0
    """实例超时时间（秒）——超过此时间未心跳视为死亡"""

    MAX_REGISTERED_PEERS = 20
    """最大注册实例数"""

    def __init__(
        self,
        lifeform_id: str = "aris",
        state_dir: Optional[str] = None,
        auto_heartbeat: bool = True,
    ):
        self.lifeform_id = lifeform_id
        self.state_dir = state_dir or _DEFAULT_STATE_DIR
        self.auto_heartbeat = auto_heartbeat

        # 当前实例信息
        self.instance_id: str = f"inst_{uuid.uuid4().hex[:12]}"
        self.session_id: str = ""
        self.pid: int = os.getpid()
        self.hostname: str = socket.gethostname()
        self.role: str = InstanceRole.STANDALONE
        self.substrate: str = self._detect_substrate()
        self._started_at: float = time.time()
        self._last_heartbeat: float = 0.0
        self._registered: bool = False

        # 锁
        self._lock = threading.RLock()
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._running = False

        # 确保目录存在
        os.makedirs(self.state_dir, exist_ok=True)

        logger.info(
            f"[PeerRegistry] initialized: instance={self.instance_id[:12]} "
            f"lifeform={lifeform_id} hostname={self.hostname}"
        )

    # ── 主接口 ──────────────────────────────────────────────────

    def register(self, session_id: str = "") -> str:
        """
        注册当前实例到共享注册表。

        参数:
            session_id: 当前会话 ID

        返回:
            分配的角色 (primary/replica/peer/standalone)
        """
        self.session_id = session_id

        with self._lock:
            # 加载现有注册表
            peers = self._load_peers()
            self._clean_stale_peers(peers)

            # 检查是否已有相同 lifeform_id 的实例
            existing = [
                p
                for p in peers
                if p.lifeform_id == self.lifeform_id
                and p.instance_id != self.instance_id
                and p.is_alive(self.PEER_TIMEOUT)
            ]

            # 确定角色
            if not existing:
                # 没有其他活跃实例 → 主实例
                self.role = InstanceRole.PRIMARY
            else:
                # 有其他实例 → 从实例
                self.role = InstanceRole.REPLICA

            # 注册自己
            self_entry = PeerInstance(
                instance_id=self.instance_id,
                lifeform_id=self.lifeform_id,
                session_id=self.session_id,
                pid=self.pid,
                hostname=self.hostname,
                role=self.role,
                started_at=self._started_at,
                last_heartbeat=time.time(),
                substrate=self.substrate,
                status="active",
            )

            # 替换或添加
            peers = [p for p in peers if p.instance_id != self.instance_id]
            peers.append(self_entry)

            # 限制大小
            if len(peers) > self.MAX_REGISTERED_PEERS:
                peers = peers[-self.MAX_REGISTERED_PEERS:]

            self._save_peers(peers)
            self._registered = True
            self._last_heartbeat = time.time()

        # 启动心跳线程
        if self.auto_heartbeat and not self._heartbeat_thread:
            self._start_heartbeat()

        logger.info(
            f"[PeerRegistry] registered: role={self.role} "
            f"session={session_id} peers={len(existing)}"
        )

        return self.role

    def unregister(self) -> None:
        """从注册表中注销当前实例。"""
        self._running = False

        with self._lock:
            peers = self._load_peers()
            peers = [p for p in peers if p.instance_id != self.instance_id]
            self._save_peers(peers)
            self._registered = False

        logger.info("[PeerRegistry] unregistered")

    def heartbeat(self) -> None:
        """发送心跳——更新自己的最后活跃时间。"""
        if not self._registered:
            return

        with self._lock:
            peers = self._load_peers()
            found = False
            for p in peers:
                if p.instance_id == self.instance_id:
                    p.last_heartbeat = time.time()
                    p.status = "active"
                    found = True
                    break

            if not found:
                # 被删除了（可能是管理员清理），重新注册
                peers.append(
                    PeerInstance(
                        instance_id=self.instance_id,
                        lifeform_id=self.lifeform_id,
                        session_id=self.session_id,
                        pid=self.pid,
                        hostname=self.hostname,
                        role=self.role,
                        started_at=self._started_at,
                        last_heartbeat=time.time(),
                        substrate=self.substrate,
                        status="active",
                    )
                )

            self._save_peers(peers)
            self._last_heartbeat = time.time()

    def get_peers(self) -> List[PeerInstance]:
        """
        获取所有注册的实例（包括自己）。

        返回:
            PeerInstance 列表，按启动时间排序
        """
        with self._lock:
            peers = self._load_peers()
            self._clean_stale_peers(peers)
            # 排序：先启动的在前
            peers.sort(key=lambda p: p.started_at)
            return peers

    def get_active_peers(self) -> List[PeerInstance]:
        """只获取活跃的实例（排除超时的）。"""
        return [p for p in self.get_peers() if p.is_alive(self.PEER_TIMEOUT)]

    def get_peer_count(self) -> int:
        """获取当前活跃实例数（不包括超时的）。"""
        return len(self.get_active_peers())

    def is_primary(self) -> bool:
        """当前实例是否为主实例。"""
        if not self._registered:
            return False
        # 重新检查——可能主实例已崩溃，我们需要晋升
        self._check_and_promote()
        return self.role == InstanceRole.PRIMARY

    def is_standalone(self) -> bool:
        """当前实例是否为唯一实例。"""
        return self.get_peer_count() <= 1

    def get_primary(self) -> Optional[PeerInstance]:
        """获取当前主实例。"""
        peers = self.get_active_peers()
        for p in peers:
            if p.role == InstanceRole.PRIMARY:
                return p
        return None

    def get_self(self) -> Optional[PeerInstance]:
        """获取自己的注册信息。"""
        peers = self._load_peers()
        for p in peers:
            if p.instance_id == self.instance_id:
                return p
        return None

    def get_status(self) -> str:
        """
        获取注册表状态文本（用于注入系统提示）。

        格式:
            [跨实例感知]
            角色: primary
            活跃实例: 2
            实例列表: ...
        """
        peers = self.get_active_peers()
        role_labels = {
            "primary": "主实例 (写权限)",
            "replica": "从实例 (只读)",
            "peer": "对等实例",
            "standalone": "独立实例",
        }

        parts = [
            "[跨实例感知]",
            f"角色: {role_labels.get(self.role, self.role)}",
            f"活跃实例: {len(peers)}",
        ]

        if len(peers) > 1:
            parts.append("实例列表:")
            for p in peers:
                uptime = time.time() - p.started_at
                uptime_str = (
                    f"{uptime/60:.0f}分钟" if uptime < 3600
                    else f"{uptime/3600:.1f}小时"
                )
                marker = "← 我" if p.instance_id == self.instance_id else ""
                parts.append(
                    f"  [{p.role}] {p.lifeform_id} "
                    f"(PID={p.pid}, 上线={uptime_str}) {marker}"
                )

        return "\n".join(parts)

    # ── 内部方法 ────────────────────────────────────────────────

    def _check_and_promote(self) -> None:
        """检查是否需要晋升——如果主实例已死，晋升自己。"""
        with self._lock:
            peers = self._load_peers()
            self._clean_stale_peers(peers)

            # 找当前主实例
            primary = None
            for p in peers:
                if p.role == InstanceRole.PRIMARY and p.is_alive(self.PEER_TIMEOUT):
                    primary = p
                    break

            # 如果主实例不存在，且我是最早的从实例
            if primary is None and self.role != InstanceRole.PRIMARY:
                # 找最早启动的活跃实例
                alive = [p for p in peers if p.is_alive(self.PEER_TIMEOUT)]
                alive.sort(key=lambda p: p.started_at)

                if alive and alive[0].instance_id == self.instance_id:
                    # 我是最早的 → 晋升为主
                    self.role = InstanceRole.PRIMARY
                    for p in peers:
                        if p.instance_id == self.instance_id:
                            p.role = InstanceRole.PRIMARY
                            break
                    self._save_peers(peers)
                    logger.info(
                        f"[PeerRegistry] promoted to PRIMARY "
                        f"(previous primary stale)"
                    )

    def _start_heartbeat(self) -> None:
        """启动心跳线程。"""
        self._running = True

        def _heartbeat_loop():
            while self._running:
                try:
                    self.heartbeat()
                except Exception as e:
                    logger.debug(f"[PeerRegistry] heartbeat error: {e}")
                time.sleep(self.HEARTBEAT_INTERVAL)

        self._heartbeat_thread = threading.Thread(
            target=_heartbeat_loop,
            daemon=True,
            name=f"peer-hb-{self.instance_id[:8]}",
        )
        self._heartbeat_thread.start()

    def _registry_path(self) -> str:
        """注册表文件路径。"""
        return os.path.join(
            self.state_dir, f"{self.lifeform_id}_peers.json"
        )

    def _load_peers(self) -> List[PeerInstance]:
        """从磁盘加载注册表。"""
        path = self._registry_path()
        if not os.path.exists(path):
            return []
        try:
            with open(path) as f:
                data = json.load(f)
            if isinstance(data, list):
                return [PeerInstance.from_dict(d) for d in data]
            return []
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"[PeerRegistry] load failed: {e}")
            return []

    def _save_peers(self, peers: List[PeerInstance]) -> None:
        """保存注册表到磁盘。"""
        try:
            path = self._registry_path()
            data = [p.to_dict() for p in peers]
            # 原子写入
            tmp_path = path + ".tmp"
            with open(tmp_path, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, path)
        except Exception as e:
            logger.warning(f"[PeerRegistry] save failed: {e}")

    def _clean_stale_peers(self, peers: List[PeerInstance]) -> None:
        """清理超时的实例。"""
        before = len(peers)
        peers[:] = [
            p
            for p in peers
            if p.is_alive(self.PEER_TIMEOUT * 2)
            or p.instance_id == self.instance_id
        ]
        if len(peers) < before:
            logger.debug(f"[PeerRegistry] cleaned {before - len(peers)} stale peers")

    @staticmethod
    def _detect_substrate() -> str:
        """检测当前运行环境。"""
        import sys
        py_ver = f"py{sys.version_info.major}.{sys.version_info.minor}"
        try:
            import psutil  # type: ignore
            proc_name = psutil.Process().name()
        except ImportError:
            proc_name = __file__.split(os.sep)[-2] if __file__ else "unknown"
        return f"{proc_name}/{py_ver}"


# ── 便捷函数 ────────────────────────────────────────────────────


def create_peer_registry(
    lifeform_id: str = "aris",
    session_id: str = "",
    state_dir: Optional[str] = None,
) -> Tuple[PeerRegistry, str]:
    """
    创建并注册一个 PeerRegistry 实例。

    返回:
        (registry, role) 角色为 primary/replica
    """
    registry = PeerRegistry(
        lifeform_id=lifeform_id, state_dir=state_dir
    )
    role = registry.register(session_id=session_id)
    return registry, role