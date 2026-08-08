"""laap.daemon — CLI 入口。支持 `python -m laap.daemon`。"""

from __future__ import annotations

import argparse
import os
import sys


def _ensure_laap_root():
    """确保 LAAP 根目录在 sys.path 中。"""
    laap_root = os.environ.get("LAAP_ROOT", r"D:\LAAP")
    if laap_root not in sys.path:
        sys.path.insert(0, laap_root)


def main():
    _ensure_laap_root()

    parser = argparse.ArgumentParser(prog="laap-daemon", description="LAAP 数字生命守护进程")
    parser.add_argument("--config", type=str, default="", help="配置文件路径")
    parser.add_argument("--status", action="store_true", help="查询守护进程状态")
    parser.add_argument("--stop", action="store_true", help="停止守护进程")
    parser.add_argument("--port", type=int, default=0, help="覆盖 HTTP 端口")
    parser.add_argument("--with-api", action="store_true", help="同时启动 LAAP API server (port 8000)")
    parser.add_argument("--api-port", type=int, default=8000, help="API server HTTP 端口")
    args = parser.parse_args()

    from .config import DaemonConfig
    from .runner import LaapDaemon, daemon_status, daemon_stop

    if args.status:
        print(daemon_status())
        return 0
    if args.stop:
        print(daemon_stop())
        return 0

    config = DaemonConfig.from_file(args.config) if args.config else DaemonConfig()
    if args.port:
        config.daemon_port = args.port

    daemon = LaapDaemon(config, auto_start_subsystems=args.with_api)
    if args.with_api:
        daemon.supervisor.register_api_server(api_port=args.api_port)
    daemon.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())