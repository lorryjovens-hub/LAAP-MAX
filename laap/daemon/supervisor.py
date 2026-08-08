"""
laap.daemon.supervisor — 监管树
================================
实现 LAAP 子系统的进程监管树：
- 根 supervisor 在 daemon 内部运行
- 每个子系统（认知引擎、记忆服务、API 网关等）是一个 ManagedProcess
- 崩溃时自动重启，不可恢复时升级到根 supervisor
- 提供统一的状态查询接口

用法:
    sv = Supervisor()
    sv.register("cognitive", ["python", "-m", "laap.cognition"], port=9000)
    sv.start_all()
    sv.status()
    sv.stop_all()
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
from typing import Dict, List, Optional

from .process import ManagedProcess, ProcessState

log = logging.getLogger("laap.daemon.supervisor")


class Supervisor:
    """LAAP 子系统监管树。"""

    def __init__(self, daemon_port: int = 19420):
        self.daemon_port = daemon_port
        self._processes: Dict[str, ManagedProcess] = {}
        self._lock = threading.Lock()
        self._escalation_count = 0

    # ── 注册子系统 ──────────────────────────────────

    def register_cognitive_engine(self, port: int = 9001) -> ManagedProcess:
        """注册认知引擎进程。"""
        return self._register(
            "cognitive",
            ["python", "-m", "laap.cognition", "--port", str(port)],
            health_check_url=f"http://127.0.0.1:{port}/health",
            cwd=r"D:\LAAP",
        )

    def register_memory_service(self, port: int = 9002) -> ManagedProcess:
        """注册记忆服务进程。"""
        return self._register(
            "memory",
            ["python", "-m", "laap.memory.service", "--port", str(port)],
            health_check_url=f"http://127.0.0.1:{port}/health",
            cwd=r"D:\LAAP",
        )

    def register_api_gateway(self, port: int = 9003) -> ManagedProcess:
        """注册 API 网关进程。"""
        return self._register(
            "api",
            ["python", "-m", "laap.api.server", "--port", str(port)],
            health_check_url=f"http://127.0.0.1:{port}/health",
            cwd=r"D:\LAAP",
        )

    def register_api_server(self, api_port: int = 8000, ws_port: int = 8765) -> ManagedProcess:
        """注册 LAAP API 服务器（FastAPI + AetherGateway WebSocket 网关）。

        Args:
            api_port: API HTTP 端口（health check 用）
            ws_port: AetherGateway WebSocket 端口（laap-client 对接用）
        """
        return self._register(
            "api",
            [sys.executable, "-c", (
                "import sys; sys.path.insert(0, r'D:\\LAAP'); "
                f"import os; os.environ['AETHER_GATEWAY_PORT']='{ws_port}'; "
                "from laap.api.server import serve; serve(port=" + str(api_port) + ")"
            )],
            health_check_url=f"http://127.0.0.1:{api_port}/health",
            cwd=r"D:\LAAP",
        )

    def register_custom(
        self,
        name: str,
        command: list[str],
        health_check_url: str = "",
        cwd: str = "",
        max_retries: int = 3,
    ) -> ManagedProcess:
        """注册自定义子系统。"""
        return self._register(
            name, command,
            health_check_url=health_check_url,
            cwd=cwd or os.getcwd(),
            max_retries=max_retries,
        )

    def _register(
        self,
        name: str,
        command: list[str],
        *,
        health_check_url: str = "",
        cwd: str = "",
        max_retries: int = 3,
    ) -> ManagedProcess:
        proc = ManagedProcess(
            name=name,
            command=command,
            cwd=cwd or os.getcwd(),
            health_check_url=health_check_url,
            max_retries=max_retries,
        )
        proc.on_crash(self._on_process_crash)
        proc.on_recovery(self._on_process_recovery)

        with self._lock:
            self._processes[name] = proc
        log.info("Supervisor registered: %s (max_retries=%d)", name, max_retries)
        return proc

    # ── 生命周期 ────────────────────────────────────

    def start_all(self):
        """启动所有注册的子系统。"""
        for name, proc in self._processes.items():
            log.info("Supervisor starting: %s", name)
            proc.start()

    def stop_all(self, timeout: float = 10.0):
        """优雅停止所有子系统。"""
        log.info("Supervisor stopping all subsystems...")
        for name, proc in self._processes.items():
            proc.stop(timeout=timeout)
        log.info("Supervisor all subsystems stopped")

    def restart_all(self):
        """重启所有子系统。"""
        self.stop_all()
        time.sleep(2)
        self.start_all()

    # ── 回调 ────────────────────────────────────────

    def _on_process_crash(self, proc: ManagedProcess):
        """子进程崩溃回调。"""
        log.warning("Supervisor: %s crashed", proc.name)
        # 若超过最大重试，记录一次升级
        if proc._retry_count >= proc.max_retries:
            with self._lock:
                self._escalation_count += 1
            log.error("Supervisor: %s escalated after %d retries", proc.name, proc._retry_count)

    def _on_process_recovery(self, proc: ManagedProcess):
        """子进程恢复回调。"""
        log.info("Supervisor: %s recovered (attempt %d)", proc.name, proc._retry_count)

    # ── 状态 ────────────────────────────────────────

    def status(self) -> dict:
        """获取所有子系统状态。"""
        with self._lock:
            processes = {name: p.get_status() for name, p in self._processes.items()}
            running = sum(1 for p in self._processes.values() if p.state == ProcessState.RUNNING)
            crashed = sum(1 for p in self._processes.values() if p.state == ProcessState.CRASHED)
            return {
                "total": len(self._processes),
                "running": running,
                "crashed": crashed,
                "escalation_count": self._escalation_count,
                "processes": processes,
            }

    def get_process(self, name: str) -> Optional[ManagedProcess]:
        return self._processes.get(name)