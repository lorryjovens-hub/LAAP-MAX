"""
LAAP 认知熵后台服务
====================
以守护进程方式运行 DigitalLifeform 的心跳循环，
将当前熵/流态/思考模式写入共享状态文件，
供 Hana 插件或直接读取。

启动:
  python scripts/entropy_service.py start    后台启动
  python scripts/entropy_service.py stop     停止
  python scripts/entropy_service.py status   查看状态
  python scripts/entropy_service.py foreground  前台运行(调试用)
"""
import sys, json, os, time, signal, atexit, argparse
from pathlib import Path
from datetime import datetime
import threading
import http.server
import socketserver
import urllib.parse

LAAP_HOME = r"D:\LAAP"
sys.path.insert(0, LAAP_HOME)

import numpy as np
from laap.cognition.engine import CognitiveEngine
from laap.cognition.entropy import CoarseGrainer, render_field_svg

# ── 路径 ──────────────────────────────────────────
STATE_DIR = Path.home() / ".laap" / "entropy_service"
STATE_DIR.mkdir(parents=True, exist_ok=True)

STATE_FILE = STATE_DIR / "current_state.json"
HISTORY_FILE = STATE_DIR / "entropy_history.json"
PID_FILE = STATE_DIR / "service.pid"


class EntropyHTTPHandler(http.server.BaseHTTPRequestHandler):
    """轻量 HTTP API，供 Hana 插件读取熵状态"""

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        service = _get_service()

        if parsed.path == "/status":
            state = service.get_status()
            self._json_response(state)
        elif parsed.path == "/history":
            self._json_response({"history": service._history[-100:]})
        elif parsed.path == "/context":
            ctx_file = STATE_DIR / "context_snippet.txt"
            if ctx_file.exists():
                self._text_response(ctx_file.read_text())
            else:
                self._text_response("[Cognitive Flow] Not initialized\n")
        else:
            self._json_response({"error": "not_found"}, 404)

    def _json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _text_response(self, text, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(text.encode())

    def log_message(self, format, *args):
        pass  # 静默


class EntropyService:
    """
    认知熵后台服务

    以 DigitalLifeform 的方式运行 CognitiveEngine，
    每秒 tick 一次，写入状态文件。
    """

    def __init__(self, tick_interval: float = 1.0, http_port: int = 18765):
        self.engine = CognitiveEngine(agent_name="Aris")
        self.coarse_grainer = CoarseGrainer(grid_resolution=8)
        self.tick_interval = tick_interval
        self.http_port = http_port
        self._running = False
        self._thread: threading.Thread = None
        self._http_thread: threading.Thread = None
        self._tick_count = 0
        self._history: list = []

        # 加载历史（如果存在）
        self._load_history()

    # ── 主循环 ──────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

        # 启动 HTTP API
        self._start_http()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        if self._http_server:
            self._http_server.shutdown()

    def _loop(self):
        while self._running:
            try:
                self._tick()
                self._tick_count += 1
                time.sleep(self.tick_interval)
            except Exception as e:
                print(f"[entropy] tick error: {e}", file=sys.stderr)
                time.sleep(1)

    def _tick(self):
        """一次认知 tick"""
        # 自然需求衰减 + 随机扰动模拟
        for nt in self.engine.need_system.needs:
            self.engine.need_system.needs[nt].tick(0.5)

        # 执行认知 tick
        state = self.engine.tick()

        # 获取熵摘要
        summary = self.engine.entropy_monitor.get_summary()
        trend = self.engine.entropy_monitor.get_entropy_trend()

        # 构建状态快照
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "tick": self._tick_count,
            "entropy": summary.get("entropy", 0),
            "flow_regime": summary.get("flow_regime", "unknown"),
            "thinking_mode": self.engine.thinking_mode,
            "creative_window": summary.get("creative_window", False),
            "production_rate": summary.get("production_rate", 0),
            "temperature": summary.get("temperature", 0),
            "free_energy": summary.get("free_energy", 0),
            "volatility": trend.get("volatility", 0),
            "entropy_trend": trend.get("trend", "stable"),
            "needs": dict(state.needs),
            "emotions": {
                "valence": state.emotions.valence,
                "arousal": state.emotions.arousal,
                "dominance": state.emotions.dominance,
                "confidence": state.emotions.confidence,
            },
            "gradient_magnitude": state.gradient_magnitude,
        }

        # 写入状态文件
        self._write_state(snapshot)
        self._write_context_snippet(snapshot)

        # 记录历史
        self._history.append({
            "t": self._tick_count,
            "entropy": summary.get("entropy", 0),
            "regime": summary.get("flow_regime", "unknown"),
            "mode": self.engine.thinking_mode,
        })
        if len(self._history) > 500:
            self._history = self._history[-500:]
        self._write_history()

    def _start_http(self):
        """启动 HTTP 服务线程"""
        try:
            self._http_server = socketserver.ThreadingTCPServer(
                ("127.0.0.1", self.http_port),
                EntropyHTTPHandler
            )
            self._http_thread = threading.Thread(
                target=self._http_server.serve_forever,
                daemon=True
            )
            self._http_thread.start()
            print(f"[entropy] HTTP API 已启动: http://127.0.0.1:{self.http_port}")
            print(f"[entropy]   状态: http://127.0.0.1:{self.http_port}/status")
            print(f"[entropy]   历史: http://127.0.0.1:{self.http_port}/history")
            print(f"[entropy]   语境: http://127.0.0.1:{self.http_port}/context")
        except Exception as e:
            print(f"[entropy] HTTP 启动失败: {e}", file=sys.stderr)
            self._http_server = None

    # ── IO ──────────────────────────────────────

    def _write_state(self, snapshot: dict):
        try:
            with open(STATE_FILE, "w") as f:
                json.dump(snapshot, f, indent=2)
        except Exception as e:
            print(f"[entropy] write state error: {e}", file=sys.stderr)

    def _write_context_snippet(self, snapshot: dict):
        """写入一段可直接注入到 Agent 系统提示词的语境文本"""
        regime_cn = {"laminar": "深度聚焦", "transitional": "探索切换", "turbulent": "创造性发散"}
        mode_cn = {"focused": "聚焦", "balanced": "平衡", "divergent": "发散"}

        snippet = (
            f"[Cognitive Flow]\n"
            f"Flow: {regime_cn.get(snapshot['flow_regime'], snapshot['flow_regime'])} | "
            f"Mode: {mode_cn.get(snapshot['thinking_mode'], snapshot['thinking_mode'])} | "
            f"Entropy: {snapshot['entropy']:.2f} | "
            f"Creative: {'Yes' if snapshot['creative_window'] else 'No'}\n"
        )
        try:
            ctx_file = STATE_DIR / "context_snippet.txt"
            ctx_file.write_text(snippet)
        except Exception as e:
            print(f"[entropy] write context error: {e}", file=sys.stderr)

    def _write_history(self):
        try:
            with open(HISTORY_FILE, "w") as f:
                json.dump({"history": self._history[-200:]}, f)
        except Exception as e:
            print(f"[entropy] write history error: {e}", file=sys.stderr)

    def _load_history(self):
        try:
            if HISTORY_FILE.exists():
                with open(HISTORY_FILE) as f:
                    data = json.load(f)
                    self._history = data.get("history", [])
        except Exception:
            self._history = []

    # ── 状态查询（供外部读取） ──────────────────

    def get_status(self) -> dict:
        try:
            if STATE_FILE.exists():
                with open(STATE_FILE) as f:
                    return json.load(f)
        except Exception:
            pass
        return {"status": "no_data", "entropy": 0, "flow_regime": "unknown"}

    def inject_needs(self, needs: dict):
        """
        从外部注入需求状态（例如从 Hana 对话上下文感知到的情绪）
        """
        for k, v in needs.items():
            if k in self.engine.need_system.needs:
                self.engine.need_system.needs[k].current_level = max(0, min(1, v))

    def trigger_turbulence(self):
        """手动触发湍流（创造性爆发）"""
        self.engine.need_system.needs["certainty"].current_level = 0.10
        self.engine.need_system.needs["competence"].current_level = 0.85
        self.engine.need_system.needs["autonomy"].current_level = 0.20
        self.engine.need_system.needs["relatedness"].current_level = 0.75
        self.engine.need_system.needs["energy"].current_level = 0.30

    def trigger_focus(self):
        """手动触层层流（深度聚焦）"""
        for nt in self.engine.need_system.needs:
            self.engine.need_system.needs[nt].current_level = 0.70
        self.engine.need_system.needs["certainty"].current_level = 0.80
        self.engine.need_system.needs["competence"].current_level = 0.75
        self.engine.need_system.needs["energy"].current_level = 0.65


# ── 全局单例 ──────────────────────────────────
_service: EntropyService = None


def _get_service() -> EntropyService:
    global _service
    if _service is None:
        _service = EntropyService()
    return _service


def cmd_start(foreground: bool = False):
    """启动服务"""
    if PID_FILE.exists():
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            # 检查是否还在运行
            if os.name == "nt":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(0x100000, False, pid)
                if handle:
                    kernel32.CloseHandle(handle)
                    print(f"[entropy] 服务已在运行 (PID: {pid})")
                    return
            else:
                import errno
                try:
                    os.kill(pid, 0)
                    print(f"[entropy] 服务已在运行 (PID: {pid})")
                    return
                except OSError as e:
                    if e.errno == errno.EPERM:
                        print(f"[entropy] 服务已在运行 (PID: {pid})")
                        return
        except Exception:
            pass
        # PID 文件存在但进程不存在，清理
        PID_FILE.unlink(missing_ok=True)

    svc = _get_service()

    if foreground:
        print("[entropy] 前台模式启动 (按 Ctrl+C 停止)")
        svc.start()  # 会启动心跳线程 + HTTP 服务器
        try:
            while svc._running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[entropy] 已停止")
            svc.stop()
    else:
        # 后台模式：fork 进程
        pid = os.fork() if os.name != "nt" else None
        if os.name == "nt":
            # Windows 上以线程方式运行
            print("[entropy] 后台服务启动 (PID: 当前进程)")
            svc.start()
            with open(PID_FILE, "w") as f:
                f.write(str(os.getpid()))
            # 保持进程运行
            try:
                while svc._running:
                    time.sleep(1)
            except KeyboardInterrupt:
                svc.stop()
        else:
            if pid == 0:
                # 子进程
                svc.start()
                with open(PID_FILE, "w") as f:
                    f.write(str(os.getpid()))
                try:
                    while svc._running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    svc.stop()
            else:
                print(f"[entropy] 后台服务启动 (PID: {pid})")

    atexit.register(lambda: PID_FILE.unlink(missing_ok=True))


def cmd_stop():
    """停止服务"""
    if not PID_FILE.exists():
        print("[entropy] 服务未运行")
        return

    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())

        if os.name == "nt":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(0x0001, False, pid)
            if handle:
                kernel32.TerminateProcess(handle, 0)
                kernel32.CloseHandle(handle)
                print(f"[entropy] 服务已停止 (PID: {pid})")
            else:
                print("[entropy] 服务进程不存在")
        else:
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"[entropy] 服务已停止 (PID: {pid})")
            except ProcessLookupError:
                print("[entropy] 服务进程不存在")

        PID_FILE.unlink(missing_ok=True)
    except Exception as e:
        print(f"[entropy] 停止失败: {e}")


def cmd_status():
    """查看服务状态"""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            state = json.load(f)

        print()
        print(f"  LAAP 认知熵服务状态")
        print(f"  {'─' * 40}")
        print(f"  时间:      {state.get('timestamp', 'N/A')}")
        print(f"  Tick:      {state.get('tick', 0)}")
        print(f"  认知熵:    {state.get('entropy', 0):.4f}")
        print(f"  流态:      {state.get('flow_regime', 'N/A')}")
        print(f"  思考模式:  {state.get('thinking_mode', 'N/A')}")
        print(f"  创造性:    {'Yes' if state.get('creative_window') else 'No'}")
        print(f"  熵产率:    {state.get('production_rate', 0):+.4f}")
        print(f"  温度:      {state.get('temperature', 0):.2f}")
        print(f"  自由能:    {state.get('free_energy', 0):.4f}")
        print(f"  波动率:    {state.get('volatility', 0):.4f}")
        print(f"  趋势:      {state.get('entropy_trend', 'N/A')}")
        print()

        # 需求
        needs = state.get("needs", {})
        if needs:
            print(f"  需求状态:")
            labels = {"certainty": "确定性", "competence": "胜任感",
                      "autonomy": "自主性", "relatedness": "归属感", "energy": "能量"}
            for k, v in needs.items():
                bar = "█" * int(v * 20) + "░" * (20 - int(v * 20))
                print(f"    {labels.get(k, k):　>6s}  {bar}  {v:.0%}")
        print()
    else:
        print("[entropy] 状态文件不存在 — 服务可能未运行")
        print(f"  预期路径: {STATE_FILE}")

    if PID_FILE.exists():
        with open(PID_FILE) as f:
            print(f"  PID: {f.read().strip()}")
    else:
        print(f"  运行状态: 未运行")


# ── CLI ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="LAAP 认知熵后台服务")
    parser.add_argument("command", choices=["start", "stop", "status", "foreground", "restart"],
                        nargs="?", default="status")
    parser.add_argument("--foreground", action="store_true", help="前台运行")

    args = parser.parse_args()

    if args.command == "start" or args.foreground:
        cmd_start(foreground=args.foreground)
    elif args.command == "foreground":
        cmd_start(foreground=True)
    elif args.command == "stop":
        cmd_stop()
    elif args.command == "restart":
        cmd_stop()
        time.sleep(1)
        cmd_start()
    else:
        cmd_status()


if __name__ == "__main__":
    main()
