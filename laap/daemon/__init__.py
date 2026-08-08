"""
LAAP Daemon — 数字生命独立守护进程
==================================
让 LAAP 认知引擎脱离宿主（Hanako）寄生，以独立后台进程运行。

职责：
- 进程生命周期管理（spawn / monitor / restart / shutdown）
- 缓存持久化（L0 精确 + L1 语义，进程重启后自动恢复）
- 健康检查（HTTP 探活 + 心跳）
- 优雅降级（崩溃自动重启，数据不丢失）

用法:
    python -m laap.daemon                     # 启动守护进程
    python -m laap.daemon --status            # 查询状态
    python -m laap.daemon --stop              # 停止
    python -m laap.daemon --config config.json
"""

from __future__ import annotations

from .config import DaemonConfig
from .runner import LaapDaemon, daemon_status, daemon_stop
from .process import ManagedProcess, ProcessState, HealthCheckMethod
from .supervisor import Supervisor

__all__ = [
    "DaemonConfig", "LaapDaemon", "daemon_status", "daemon_stop", "__version__",
    "ManagedProcess", "ProcessState", "HealthCheckMethod", "Supervisor",
]

__version__ = "0.1.0"