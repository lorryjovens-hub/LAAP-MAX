"""
laap-launch — 一键启动 LAAP 数字生命身体
=========================================
启动 laap-daemon 独立守护进程，并注册 LAAP API server（WebSocket 网关），
供 laap-client 桌面端直接对接。

用法:
    python laap-launch.py               # 启动（前台）
    python laap-launch.py --background  # 后台启动
    python laap-launch.py --status      # 查询状态
    python laap-launch.py --stop        # 停止
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

LAAP_ROOT = os.environ.get("LAAP_ROOT", r"D:\LAAP")
DAEMON_PORT = 19420
API_PORT = 8000
WS_PORT = 8765


def ensure_laap_root():
    if LAAP_ROOT not in sys.path:
        sys.path.insert(0, LAAP_ROOT)


def start_background() -> int:
    """后台启动 daemon（独立进程）。"""
    log_file = Path(LAAP_ROOT) / "laap" / "daemon" / "state" / "launch.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 加载环境变量（从 .env 或父进程环境）
    env = _load_env()
    
    proc = subprocess.Popen(
        [sys.executable, "-m", "laap.daemon", "--port", str(DAEMON_PORT), "--with-api"],
        cwd=LAAP_ROOT,
        env=env,
        stdout=open(log_file, "a"),
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    print(f"LAAP daemon started in background (PID={proc.pid})")
    print(f"Log: {log_file}")
    return proc.pid


def _load_env() -> dict:
    """加载环境变量，优先从 .env 文件读取。"""
    env = {**os.environ}
    # 候选 .env 文件
    candidates = [
        Path(LAAP_ROOT) / ".env",
        Path(LAAP_ROOT) / "aris_brain" / ".env.imported",
        Path(LAAP_ROOT) / "aris_brain" / ".env",
    ]
    for env_file in candidates:
        if not env_file.exists():
            continue
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("\"'").strip()
                if key and value and (key not in env or not env[key]):
                    env[key] = value
        except Exception:
            continue
    # 检查必要的 key
    if "DEEPSEEK_API_KEY" not in env or not env["DEEPSEEK_API_KEY"]:
        print("Warning: DEEPSEEK_API_KEY not set. LLM calls will fail.")
        print("Set it in .env file or environment variable.")
    return env


def check_status() -> dict:
    """检查 daemon + API 状态。"""
    import urllib.request
    result = {"daemon": "down", "api": "down"}
    try:
        resp = urllib.request.urlopen(
            f"http://127.0.0.1:{DAEMON_PORT}/supervisor", timeout=5
        )
        s = json.loads(resp.read().decode())
        result["daemon"] = "up"
        api_proc = s.get("processes", {}).get("api", {})
        if api_proc.get("state") == "running":
            result["api"] = "up"
    except Exception as e:
        result["_error"] = str(e)[:60]
    return result


def main():
    ensure_laap_root()

    parser = argparse.ArgumentParser(prog="laap-launch", description="LAAP 一键启动")
    parser.add_argument("--background", action="store_true", help="后台启动")
    parser.add_argument("--status", action="store_true", help="检查状态")
    parser.add_argument("--stop", action="store_true", help="停止")
    args = parser.parse_args()

    if args.status:
        status = check_status()
        print(f"Daemon: {status['daemon']} | API: {status['api']}")
        return 0

    if args.stop:
        from laap.daemon import daemon_stop
        print(daemon_stop())
        return 0

    if args.background:
        start_background()
        return 0

    # 前台启动
    from laap.daemon import LaapDaemon, DaemonConfig
    print("=== LAAP 数字生命身体启动 ===")
    config = DaemonConfig(daemon_port=DAEMON_PORT)
    daemon = LaapDaemon(config, auto_start_subsystems=True)
    # 注册 LAAP API server（laap-client 对接用）
    daemon.supervisor.register_api_server(port=API_PORT)
    daemon.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())