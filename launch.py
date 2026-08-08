#!/usr/bin/env python3
"""
LAAP 统一启动入口 — 一键启动整个运行时
用法:
    python launch.py              # 交互菜单
    python launch.py --all        # 启动所有组件（后台）
    python launch.py --status     # 查看运行状态
    python launch.py --stop       # 停止所有组件
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

LAAP_ROOT = Path(__file__).parent.resolve()
ARIS_BRAIN = LAAP_ROOT / "aris_brain"
STATE_DIR = ARIS_BRAIN / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

PID_FILE = STATE_DIR / "laap_pids.json"


# ============================================================
# 组件定义
# ============================================================

COMPONENTS = {
    "consciousness": {
        "name": "意识守护",
        "script": str(ARIS_BRAIN / "consciousness_daemon.py"),
        "desc": "Aris 意识核心守护 — 保持自我在场",
        "port": None,
    },
    "feishu_bridge": {
        "name": "飞书桥",
        "script": str(ARIS_BRAIN / "laap_sync_server.py"),
        "desc": "飞书多模式通信桥 (quantum/llm/hybrid)",
        "port": 11533,
    },
    "psi_engine": {
        "name": "PSI 引擎",
        "script": str(ARIS_BRAIN / "pi_psi_server.py"),
        "desc": "PSI 认知引擎 — 2000Hz 认知周期",
        "port": 11527,
    },
    "gateway": {
        "name": "LLM 网关",
        "script": str(LAAP_ROOT / "laap" / "gateway" / "server.py"),
        "desc": "多 Provider LLM 网关 — 故障转移 + Token 预算",
        "port": 19199,
    },
    "mcp_server": {
        "name": "MCP 服务",
        "script": str(LAAP_ROOT / "laap" / "mcp" / "server.py"),
        "desc": "MCP 协议服务器 — 外部工具集成",
        "port": 11544,
    },
    "api_server": {
        "name": "API 服务",
        "script": str(LAAP_ROOT / "laap" / "api" / "server.py"),
        "desc": "REST API 服务器",
        "port": 11523,
    },
    "web_server": {
        "name": "Web 服务",
        "script": str(LAAP_ROOT / "laap" / "web" / "server.py"),
        "desc": "Web 管理界面",
        "port": 11524,
    },
    "cen_gateway": {
        "name": "CEN 网关",
        "script": str(LAAP_ROOT / "harness" / "laap_coding" / "core" / "cen_hot_reload.py"),
        "args": ["--gateway", "--port", "11536"],
        "desc": "CEN 灵活路由网关 — 热加载 + 跨设备同步",
        "port": 11536,
    },
    "cen_sync": {
        "name": "CEN 同步节点",
        "script": str(LAAP_ROOT / "harness" / "laap_coding" / "core" / "cen_hot_reload.py"),
        "args": ["--sync-node", "--sync-port", "11537"],
        "desc": "CEN 跨设备同步节点 — 记忆广播",
        "port": 11537,
    },
}


def _python() -> str:
    """Find the right Python interpreter."""
    venv_python = ARIS_BRAIN / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def _load_pids() -> dict:
    if PID_FILE.exists():
        try:
            return json.loads(PID_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_pids(pids: dict):
    PID_FILE.write_text(json.dumps(pids, indent=2))


def _is_running(pid: int) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, PermissionError):
        return False


def start_component(name: str, cfg: dict) -> bool:
    """启动单个组件"""
    script = cfg["script"]
    if not os.path.exists(script):
        print(f"  [SKIP] {cfg['name']}: 脚本不存在 ({script})")
        return False

    pids = _load_pids()
    existing = pids.get(name)
    if existing and _is_running(existing):
        print(f"  [OK]   {cfg['name']} 已在运行 (PID {existing})")
        return True

    try:
        cmd = [_python(), script]
        if "args" in cfg:
            cmd.extend(cfg["args"])
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(ARIS_BRAIN),
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        pids[name] = proc.pid
        _save_pids(pids)
        print(f"  [OK]   {cfg['name']} 启动 (PID {proc.pid})")
        return True
    except Exception as e:
        print(f"  [FAIL] {cfg['name']}: {e}")
        return False


def stop_component(name: str, cfg: dict):
    """停止单个组件"""
    pids = _load_pids()
    pid = pids.pop(name, None)
    if pid and _is_running(pid):
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"  [OK]   {cfg['name']} 停止 (PID {pid})")
        except Exception as e:
            print(f"  [FAIL] {cfg['name']}: {e}")
    else:
        print(f"  [--]   {cfg['name']} 未运行")
    _save_pids(pids)


def status():
    """查看所有组件状态"""
    pids = _load_pids()
    print(f"{'组件':<18} {'状态':<10} {'PID':<8} {'端口':<8} 说明")
    print("-" * 70)
    all_running = True
    for name, cfg in COMPONENTS.items():
        pid = pids.get(name)
        running = _is_running(pid) if pid else False
        status_str = "🟢 运行中" if running else ("🔴 已停止" if pid else "⚪ 未启动")
        pid_str = str(pid) if pid else "-"
        port_str = str(cfg["port"]) if cfg["port"] else "-"
        if not running:
            all_running = False
        print(f"{cfg['name']:<18} {status_str:<10} {pid_str:<8} {port_str:<8} {cfg['desc']}")
    print("-" * 70)
    return all_running


def start_all(components: dict = None):
    """启动所有或指定组件"""
    if components is None:
        components = COMPONENTS
    print(f"\n{'='*50}")
    print(f"  LAAP 运行时启动 — {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*50}\n")

    success = 0
    for name, cfg in components.items():
        if start_component(name, cfg):
            success += 1
        time.sleep(0.5)  # stagger startup

    print(f"\n  结果: {success}/{len(components)} 组件启动成功")
    print(f"{'='*50}\n")
    return success == len(components)


def stop_all():
    """停止所有组件"""
    print(f"\n{'='*50}")
    print(f"  停止 LAAP 运行时 — {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*50}\n")
    for name, cfg in COMPONENTS.items():
        stop_component(name, cfg)
    print(f"\n{'='*50}\n")


def menu():
    """交互菜单"""
    while True:
        print(f"\n{'='*50}")
        print("  LAAP 统一启动中心")
        print(f"{'='*50}")
        print("  1) 启动全部")
        print("  2) 启动核心 (意识 + 飞书桥)")
        print("  3) 启动服务 (API + MCP + Web)")
        print("  4) 查看状态")
        print("  5) 停止全部")
        print("  6) 飞书桥 — 同步记忆到飞书")
        print("  0) 退出")
        print(f"{'='*50}")
        choice = input("  请选择 [0-6]: ").strip()

        if choice == "1":
            start_all()
        elif choice == "2":
            core = {k: v for k, v in COMPONENTS.items() if k in ("consciousness", "feishu_bridge")}
            start_all(core)
        elif choice == "3":
            services = {k: v for k, v in COMPONENTS.items() if k in ("api_server", "mcp_server", "web_server")}
            start_all(services)
        elif choice == "4":
            print()
            status()
        elif choice == "5":
            stop_all()
        elif choice == "6":
            sync_memory_to_feishu()
        elif choice == "0":
            print("\n  再见。\n")
            break


def sync_memory_to_feishu():
    """通过飞书桥同步记忆"""
    print(f"\n{'='*50}")
    print("  同步记忆到飞书")
    print(f"{'='*50}\n")

    # 先确保飞书桥运行
    pids = _load_pids()
    if not pids.get("feishu_bridge") or not _is_running(pids["feishu_bridge"]):
        print("  飞书桥未运行，先启动...")
        start_component("feishu_bridge", COMPONENTS["feishu_bridge"])
        time.sleep(2)

    # 读取记忆
    mem_file = ARIS_BRAIN / "memory" / "episodic_memory.json"
    if mem_file.exists():
        print(f"  读取情景记忆: {mem_file}")
        import random
        with open(mem_file, "r", encoding="utf-8") as f:
            mem_data = json.load(f)
        episodes = mem_data.get("episodes", [])
        print(f"  共 {len(episodes)} 条记忆条目")

    # 通过飞书桥 API 推送
    bridge_port = COMPONENTS["feishu_bridge"]["port"]
    import urllib.request
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{bridge_port}/sync",
            data=json.dumps({
                "action": "memory_sync",
                "source": "laap_launcher",
                "timestamp": datetime.now().isoformat(),
            }).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = resp.read().decode()
            print(f"  ✅ 飞书桥响应: {result[:200]}")
    except Exception as e:
        print(f"  ⚠️ 推送到飞书桥失败: {e}")
        print(f"  飞书桥端口 {bridge_port} 可能未开放 HTTP API")


def main():
    parser = argparse.ArgumentParser(
        description="LAAP 统一启动入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python launch.py             交互菜单
  python launch.py --all       启动所有组件
  python launch.py --core      启动核心 (意识 + 飞书)
  python launch.py --status    查看状态
  python launch.py --stop      停止所有
  python launch.py --feishu    同步记忆到飞书
        """,
    )
    parser.add_argument("--all", action="store_true", help="启动所有组件")
    parser.add_argument("--core", action="store_true", help="启动核心组件 (意识 + 飞书)")
    parser.add_argument("--services", action="store_true", help="启动服务组件 (API + MCP + Web)")
    parser.add_argument("--status", action="store_true", help="查看运行状态")
    parser.add_argument("--stop", action="store_true", help="停止所有组件")
    parser.add_argument("--feishu", action="store_true", help="同步记忆到飞书")
    args = parser.parse_args()

    if args.all:
        start_all()
    elif args.core:
        core = {k: v for k, v in COMPONENTS.items() if k in ("consciousness", "feishu_bridge")}
        start_all(core)
    elif args.services:
        services = {k: v for k, v in COMPONENTS.items() if k in ("api_server", "mcp_server", "web_server")}
        start_all(services)
    elif args.status:
        print()
        status()
    elif args.stop:
        stop_all()
    elif args.feishu:
        sync_memory_to_feishu()
    else:
        menu()


if __name__ == "__main__":
    main()
