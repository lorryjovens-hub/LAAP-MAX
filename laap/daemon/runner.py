"""laap.daemon.runner — 守护进程主循环。"""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, Optional

from .config import DaemonConfig
from .consciousness import ConsciousnessCore, get_consciousness
from .process import ManagedProcess, ProcessState
from .supervisor import Supervisor

log = logging.getLogger("laap.daemon")

# ── 全局状态 ────────────────────────────────────────

_daemon_instance: Optional["LaapDaemon"] = None
_SHUTDOWN = threading.Event()


class LaapDaemon:
    """LAAP 独立守护进程。"""

    def __init__(self, config: Optional[DaemonConfig] = None, auto_start_subsystems: bool = False):
        self.config = config or DaemonConfig()
        self._cache_ready = False
        self._l0 = None
        self._l1 = None
        self._httpd: Optional[HTTPServer] = None
        self._save_timer: Optional[threading.Thread] = None
        self._start_time = time.time()
        self._lock = threading.Lock()
        self._auto_start_subsystems = auto_start_subsystems
        self.supervisor = Supervisor(daemon_port=self.config.daemon_port)
        self._aether_system = None
        self._consciousness_actor = None

    # ── 生命周期 ────────────────────────────────────

    def start(self):
        """启动守护进程。"""
        _SHUTDOWN.clear()  # 确保 from 上一个测试周期的残留状态
        self._setup_logging()
        log.info("LAAP Daemon v0.1.0 starting...")
        log.info("Agent: %s | Port: %d", self.config.agent_id, self.config.daemon_port)

        # 1. 先启动 HTTP 服务（轻量，不依赖模型）
        self._start_http()

        # 2. 初始化 Aether ActorSystem 并注册意识 Actor
        self._init_aether()

        # 3. 加载缓存（可能因模型加载耗时 20s+）
        self._load_cache()

        # 3. 启动自动保存定时器
        self._start_auto_save()

        # 4. 启动注册的受监管子进程（如 API server）
        if self._auto_start_subsystems:
            self.supervisor.start_all()

        # 5. 注册信号处理（仅主线程可用）
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)

        log.info("Daemon ready — http://localhost:%d/status", self.config.daemon_port)
        log.info("Cache auto-save every %ds", self.config.auto_save_interval)

        # 主循环：等待关闭信号
        _SHUTDOWN.wait()
        self._shutdown()

    def stop(self):
        """请求停止。"""
        log.info("Stop requested")
        _SHUTDOWN.set()

    @property
    def uptime(self) -> float:
        return time.time() - self._start_time

    # ── Aether 集成 ──────────────────────────────────

    def _init_aether(self):
        """初始化 Aether ActorSystem 并注册意识 Actor。

        将 ConsciousnessActor 注册进编排层，使 Aris 的意识
        成为 Aether 编排树上的一个节点，可被其他 Actor 通过消息调用。
        """
        self._aether_system = None
        self._consciousness_actor = None
        self._aether_loading = True

        try:
            import asyncio
            from laap.orchestration.actor import ActorSystem, Capability

            system = ActorSystem(
                system_id=f"laap-daemon-{self.config.agent_id}",
                node_id="local",
            )
            self._aether_system = system

            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "aris_brain"))
            from aether_consciousness_actor import spawn_consciousness_actor
            actor = spawn_consciousness_actor(system)
            self._consciousness_actor = actor

            log.info("Aether ActorSystem initialized, %s registered", actor.actor_id)
            log.info("  Capabilities: %s", [c.name for c in actor.capabilities])
        except Exception as e:
            log.warning("Aether ActorSystem init skipped: %s", e)
        finally:
            self._aether_loading = False

    # ── 缓存管理 ────────────────────────────────────

    def _load_cache(self):
        """从磁盘加载持久化缓存。"""
        try:
            # L0 缓存
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "aris_brain"))
            from aether_llm_gateway import L0Cache
            self._l0 = L0Cache(max_size=self.config.l0_max_size, ttl=self.config.l0_ttl)
            n0 = self._l0.load(self.config.l0_cache_path)
            log.info("L0 cache loaded: %d entries from %s", n0, self.config.l0_cache_path)

            # L1 语义缓存
            from aether_semantic_cache import SemanticCache
            self._l1 = SemanticCache(
                threshold=self.config.l1_threshold,
                max_size=self.config.l1_max_size,
                ttl=self.config.l1_ttl,
            )
            n1 = self._l1.load(self.config.l1_cache_path)
            log.info("L1 cache loaded: %d entries from %s", n1, self.config.l1_cache_path)

            self._cache_ready = True
        except ImportError as e:
            log.warning("Cache modules not available (aris_brain not in path): %s", e)
        except Exception as e:
            log.error("Cache load failed: %s", e)

    def _save_cache(self):
        """保存缓存到磁盘。"""
        if not self._cache_ready:
            return
        try:
            if self._l0:
                self._l0.save(self.config.l0_cache_path)
            if self._l1:
                self._l1.save(self.config.l1_cache_path)
            log.debug("Cache auto-saved")
        except Exception as e:
            log.error("Cache save failed: %s", e)

    # ── HTTP 健康检查 ────────────────────────────────

    def _start_http(self):
        """启动健康检查 HTTP 服务（后台线程）。"""

        class Handler(BaseHTTPRequestHandler):
            daemon = self

            def log_message(self, fmt, *args):
                log.debug("HTTP: "+fmt, *args)

            def _respond(self, code: int, data: dict):
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

            def do_GET(self):
                if self.path == "/status":
                    self._respond(200, self.daemon._status_data())
                elif self.path == "/health":
                    self._respond(200, {"status": "ok"})
                elif self.path == "/stats":
                    self._respond(200, self.daemon._stats_data())
                elif self.path == "/supervisor":
                    self._respond(200, self.daemon.supervisor.status())
                elif self.path == "/consciousness":
                    c = get_consciousness()
                    actor = self.daemon._consciousness_actor
                    self._respond(200, {
                        "ready": c.ready or (actor and actor._ready),
                        "stats": c.get_stats(),
                        "aether_actor": bool(actor),
                        "actor_ready": bool(actor and actor._ready),
                        "actor_capabilities": actor.CAPABILITIES if actor else [],
                    })
                elif self.path == "/aether":
                    daemon = self.daemon
                    system = daemon._aether_system
                    actor = daemon._consciousness_actor
                    if daemon._aether_loading:
                        self._respond(200, {"status": "loading", "message": "Aether 意识核心加载中（模型加载约 20s）..."})
                        return
                    if not system:
                        self._respond(200, {"status": "inactive", "reason": "Aether ActorSystem not initialized"})
                        return
                    self._respond(200, {
                        "status": "active",
                        "system_id": system.system_id,
                        "node_id": system.node_id,
                        "actors": list(system.actors.keys()),
                        "consciousness": {
                            "registered": bool(actor),
                            "actor_id": actor.actor_id if actor else None,
                            "capabilities": actor.CAPABILITIES if actor else [],
                            "ready": bool(actor and actor._ready),
                        },
                    })
                elif self.path.startswith("/supervisor/"):
                    name = self.path.split("/")[-1]
                    proc = self.daemon.supervisor.get_process(name)
                    if proc:
                        self._respond(200, proc.get_status())
                    else:
                        self._respond(404, {"error": f"unknown process: {name}"})
                else:
                    self._respond(404, {"error": "not found"})

            def do_POST(self):
                if self.path == "/stop":
                    threading.Thread(target=self.daemon.stop, daemon=True).start()
                    self._respond(200, {"status": "stopping"})
                elif self.path == "/save":
                    self.daemon._save_cache()
                    self._respond(200, {"status": "saved"})
                elif self.path == "/supervisor/start":
                    self.daemon.supervisor.start_all()
                    self._respond(200, {"status": "started"})
                elif self.path == "/supervisor/stop":
                    self.daemon.supervisor.stop_all()
                    self._respond(200, {"status": "stopped"})
                elif self.path == "/supervisor/restart":
                    threading.Thread(target=self.daemon.supervisor.restart_all, daemon=True).start()
                    self._respond(200, {"status": "restarting"})
                elif self.path == "/chat":
                    content_length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
                    data = json.loads(body)
                    text = data.get("text", "")
                    session_id = data.get("session_id", "default")
                    if not text:
                        self._respond(400, {"error": "missing 'text' field"})
                        return

                    # 优先走意识 Actor（已注册进 Aether 编排层）
                    daemon = self.daemon
                    if daemon._consciousness_actor and daemon._consciousness_actor._ready:
                        result = daemon._consciousness_actor.chat(text, session_id=session_id)
                        self._respond(200, {"source": "aether_actor", "session_id": session_id, **result})
                        return

                    # 回退到意识核心
                    consciousness = get_consciousness()
                    if not consciousness.ready:
                        self._respond(503, {"error": "consciousness not ready", "reply": "意识核心加载中，请稍后再试..."})
                        return
                    result = consciousness.process(text, session_id=session_id)
                    self._respond(200, {"source": "core", "session_id": session_id, **result})
                elif self.path.startswith("/supervisor/start/"):
                    name = self.path.split("/")[-1]
                    proc = self.daemon.supervisor.get_process(name)
                    if proc:
                        threading.Thread(target=proc.start, daemon=True).start()
                        self._respond(200, {"status": "starting", "name": name})
                    else:
                        self._respond(404, {"error": f"unknown process: {name}"})
                elif self.path.startswith("/supervisor/stop/"):
                    name = self.path.split("/")[-1]
                    proc = self.daemon.supervisor.get_process(name)
                    if proc:
                        threading.Thread(target=proc.stop, daemon=True).start()
                        self._respond(200, {"status": "stopping", "name": name})
                    else:
                        self._respond(404, {"error": f"unknown process: {name}"})
                elif self.path.startswith("/supervisor/restart/"):
                    name = self.path.split("/")[-1]
                    proc = self.daemon.supervisor.get_process(name)
                    if proc:
                        threading.Thread(target=proc.restart, daemon=True).start()
                        self._respond(200, {"status": "restarting", "name": name})
                    else:
                        self._respond(404, {"error": f"unknown process: {name}"})
                else:
                    self._respond(404, {"error": "not found"})

        self._httpd = HTTPServer(("127.0.0.1", self.config.daemon_port), Handler)
        t = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        t.start()

    # ── 自动保存 ────────────────────────────────────

    def _start_auto_save(self):
        """周期性自动保存缓存。"""

        def _loop():
            while not _SHUTDOWN.is_set():
                _SHUTDOWN.wait(self.config.auto_save_interval)
                if not _SHUTDOWN.is_set():
                    self._save_cache()

        self._save_timer = threading.Thread(target=_loop, daemon=True)
        self._save_timer.start()

    # ── 信号处理 ────────────────────────────────────

    def _signal_handler(self, signum, frame):
        log.info("Signal %d received, shutting down...", signum)
        self.stop()

    def _shutdown(self):
        """优雅关闭。"""
        log.info("Shutting down...")
        self._save_cache()
        if self._httpd:
            self._httpd.shutdown()
        log.info("Daemon stopped (uptime: %.1fs)", self.uptime)

    # ── 状态 ────────────────────────────────────────

    def _status_data(self) -> dict:
        return {
            "status": "running",
            "agent_id": self.config.agent_id,
            "uptime_s": round(self.uptime, 1),
            "cache_ready": self._cache_ready,
            "cache_loading": not self._cache_ready and self.uptime < 30,
            "supervisor": self.supervisor.status(),
            "config": self.config.to_dict(),
        }

    def _stats_data(self) -> dict:
        stats = {"daemon": self._status_data()}
        with self._lock:
            if self._l0:
                stats["l0"] = self._l0.get_stats()
            if self._l1:
                stats["l1"] = self._l1.get_stats()
        return stats

    def _setup_logging(self):
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        if self.config.log_file:
            logging.basicConfig(level=self.config.log_level, format=fmt,
                                filename=self.config.log_file, filemode="a")
        else:
            logging.basicConfig(level=self.config.log_level, format=fmt)
        # 抑制冗长的三方日志
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("http.server").setLevel(logging.WARNING)


# ── 命令行工具函数 ──────────────────────────────────

def daemon_status() -> Dict[str, Any]:
    """查询守护进程状态（通过 HTTP）。"""
    import urllib.request
    cfg = DaemonConfig()
    try:
        resp = urllib.request.urlopen(f"http://127.0.0.1:{cfg.daemon_port}/status", timeout=3)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"status": "stopped", "error": str(e)}


def daemon_stop() -> Dict[str, Any]:
    """停止守护进程（通过 HTTP）。"""
    import urllib.request
    cfg = DaemonConfig()
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{cfg.daemon_port}/stop", method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=3)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"status": "error", "error": str(e)}