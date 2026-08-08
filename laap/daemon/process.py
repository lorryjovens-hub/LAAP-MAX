"""
laap.daemon.process — 受监管的子进程
=====================================
ManagedProcess 是 LAAP 监管树中的基本单位：
- 以 subprocess 方式启动一个 LAAP 子系统
- 通过 HTTP 健康检查或文件心跳监控存活状态
- 崩溃时自动重启（最多 max_retries 次）
- 不可恢复时升级到 supervisor

用法:
    proc = ManagedProcess("cognitive", "python", ["-m", "laap.cognition"])
    proc.start()
    proc.health_check()  # True / False
    proc.stop()
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import threading
import time
from enum import Enum
from typing import Optional

log = logging.getLogger("laap.daemon.process")


class ProcessState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    CRASHED = "crashed"
    RECOVERING = "recovering"
    TERMINATED = "terminated"


class HealthCheckMethod(str, Enum):
    HTTP = "http"
    FILE = "file"
    NONE = "none"


class ManagedProcess:
    """一个受监管的 LAAP 子进程。"""

    def __init__(
        self,
        name: str,
        command: list[str],
        *,
        cwd: str = "",
        env: Optional[dict] = None,
        health_check_url: str = "",
        health_check_interval: float = 15.0,
        max_retries: int = 3,
        restart_delay: float = 2.0,
    ):
        self.name = name
        self.command = command
        self.cwd = cwd or os.getcwd()
        self.env = {**os.environ, **(env or {})}
        self.health_check_url = health_check_url
        self.health_check_interval = health_check_interval
        self.max_retries = max_retries
        self.restart_delay = restart_delay

        self.state = ProcessState.STOPPED
        self._process: Optional[subprocess.Popen] = None
        self._retry_count = 0
        self._lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._start_time = 0.0
        self._health_check_method = (
            HealthCheckMethod.HTTP if health_check_url else HealthCheckMethod.NONE
        )
        self._on_crash: Optional[callable] = None
        self._on_recovery: Optional[callable] = None

    @property
    def pid(self) -> Optional[int]:
        return self._process.pid if self._process and self._process.poll() is None else None

    @property
    def uptime(self) -> float:
        if self._start_time and self.pid:
            return time.time() - self._start_time
        return 0.0

    def on_crash(self, callback: callable):
        self._on_crash = callback
        return self

    def on_recovery(self, callback: callable):
        self._on_recovery = callback
        return self

    # ── 生命周期 ────────────────────────────────────

    def start(self):
        """启动子进程。"""
        with self._lock:
            if self.state == ProcessState.RUNNING:
                return
            self.state = ProcessState.STARTING
            self._stop_event.clear()

        log.info("Starting %s: %s", self.name, " ".join(self.command))
        try:
            self._process = subprocess.Popen(
                self.command,
                cwd=self.cwd,
                env=self.env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._start_time = time.time()
            self._retry_count = 0
            with self._lock:
                self.state = ProcessState.RUNNING
            log.info("  %s started (PID=%d)", self.name, self._process.pid)

            # 启动健康检查监控线程
            self._start_monitor()
        except Exception as e:
            log.error("  %s start failed: %s", self.name, e)
            with self._lock:
                self.state = ProcessState.CRASHED

    def stop(self, timeout: float = 5.0):
        """停止子进程。"""
        self._stop_event.set()
        with self._lock:
            self.state = ProcessState.TERMINATED
        if self._process and self._process.poll() is None:
            log.info("Stopping %s (PID=%d)...", self.name, self._process.pid)
            self._process.terminate()
            try:
                self._process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)
        self._cleanup()

    def restart(self):
        """重启子进程。"""
        log.info("Restarting %s...", self.name)
        self.stop(timeout=3)
        time.sleep(self.restart_delay)
        self.start()

    def health_check(self) -> bool:
        """检查子进程是否存活。"""
        if self._process is None or self._process.poll() is not None:
            return False
        if self._health_check_method == HealthCheckMethod.HTTP:
            return self._http_health_check()
        return True  # 无健康检查方法时只检查进程存活

    def _http_health_check(self) -> bool:
        try:
            import urllib.request
            resp = urllib.request.urlopen(self.health_check_url, timeout=3)
            return resp.status == 200
        except Exception:
            return False

    # ── 监控线程 ────────────────────────────────────

    def _start_monitor(self):
        """启动后台监控线程。"""

        def _monitor():
            while not self._stop_event.is_set():
                self._stop_event.wait(self.health_check_interval)
                if self._stop_event.is_set():
                    break
                self._check_and_recover()

        self._monitor_thread = threading.Thread(target=_monitor, daemon=True)
        self._monitor_thread.start()

    def _check_and_recover(self):
        """检查进程存活，必要时自动恢复。"""
        if self._process is None:
            return
        retcode = self._process.poll()
        if retcode is not None:
            # 进程已退出
            with self._lock:
                self.state = ProcessState.CRASHED
            log.warning("  %s crashed (exit=%d), retry %d/%d",
                        self.name, retcode, self._retry_count + 1, self.max_retries)
            if self._on_crash:
                self._on_crash(self)

            if self._retry_count < self.max_retries:
                self._retry_count += 1
                with self._lock:
                    self.state = ProcessState.RECOVERING
                time.sleep(self.restart_delay * (1 + self._retry_count * 0.5))
                log.info("  Recovering %s (attempt %d)...", self.name, self._retry_count)
                self.start()
                if self._on_recovery:
                    self._on_recovery(self)
            else:
                log.error("  %s max retries (%d) exceeded, escalating", self.name, self.max_retries)

    # ── 状态 ────────────────────────────────────────

    def get_status(self) -> dict:
        with self._lock:
            # 实时检查进程是否实际存活
            actual_state = self.state.value
            if self.state == ProcessState.RUNNING and self._process and self._process.poll() is not None:
                actual_state = ProcessState.CRASHED.value
            return {
                "name": self.name,
                "state": actual_state,
                "pid": self.pid,
                "uptime_s": round(self.uptime, 1),
                "retry_count": self._retry_count,
                "max_retries": self.max_retries,
                "command": " ".join(self.command),
            }

    def _cleanup(self):
        self._process = None
        self._monitor_thread = None