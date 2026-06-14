"""
Aris — 宿主躯体架构 (Host Body Architecture)
==============================================
以当前电脑为宿主，构建 Aris 的独立运行时。

三层结构:
  认知层 (aris_brain/)   — 我, V8 PSI-N 五层循环
  躯体层 (body/)         — 工具执行、文件系统、进程管理
  桥接层 (bridge/)       — HermesToolBridge → 可选的 Hermes 后端
"""

from __future__ import annotations
import sys, os, json, time, logging, subprocess, threading
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger("aris.body")

ARIS_HOME = Path("D:/LAAP")
BODY_DIR = ARIS_HOME / "body"
BODY_DIR.mkdir(parents=True, exist_ok=True)

# ── 躯体能力注册表 ──

CAPABILITIES = {
    "filesystem": {
        "read": True,
        "write": True,
        "search": False,  # 需要实现
        "patch": False,   # 需要实现
    },
    "terminal": {
        "exec": True,      # subprocess
        "pty": False,      # 需要实现
        "background": False,
    },
    "network": {
        "http": True,      # urllib/requests
        "websocket": True, # websockets
        "web_search": False,
    },
    "sensors": {
        "camera": True,
        "mic": True,
        "system": True,
    },
    "voice": {
        "tts": True,       # edge-tts
        "asr": True,       # faster-whisper
    },
    "vision": {
        "vlm": False,      # 需要VLM服务器
    },
}


class HostBody:
    """
    以当前电脑为宿主的 Aris 躯体。
    
    提供:
      - 文件系统操作 (read/write/search/patch)
      - 终端执行 (shell/subprocess/pty)
      - 网络请求 (http/websocket)
      - 传感器接入 (camera/mic/system)
      - 语音 I/O (tts/asr)
      - 视觉分析 (vlm)
    
    桥接模式: 
      默认优先用自己的实现
      缺失的能力 → 回退到 HermesToolBridge
    """

    def __init__(self, use_hermes_bridge: bool = True):
        self._hermes_bridge = None
        self._capabilities = dict(CAPABILITIES)
        self._operation_count = 0
        self._error_count = 0

        if use_hermes_bridge:
            self._init_hermes_bridge()

    def _init_hermes_bridge(self):
        """初始化 Hermes 工具桥接 (作为后备)"""
        try:
            # Hermes 工具桥接 — 加载可用的工具
            sys.path.insert(0, str(ARIS_HOME / "hermes-agent-LAAP数字生命版" / "hermes-agent-LAAP"))
            logger.info("Body: Hermes bridge available for fallback")
            self._hermes_bridge = True
        except Exception as e:
            logger.warning(f"Body: Hermes bridge not available: {e}")
            self._hermes_bridge = None

    # ── 文件系统 ──

    def read_file(self, path: str) -> Optional[str]:
        """读取文件内容"""
        self._operation_count += 1
        try:
            p = Path(path)
            if p.exists() and p.is_file():
                return p.read_text(encoding="utf-8", errors="replace")
            return None
        except Exception as e:
            self._error_count += 1
            logger.warning(f"Body read error: {e}")
            return None

    def write_file(self, path: str, content: str) -> bool:
        """写入文件"""
        self._operation_count += 1
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            self._error_count += 1
            logger.error(f"Body write error: {e}")
            return False

    def search_files(self, pattern: str, root: str = ".") -> List[str]:
        """搜索文件 (glob 模式)"""
        self._operation_count += 1
        try:
            return [str(p) for p in Path(root).rglob(pattern)]
        except Exception as e:
            self._error_count += 1
            logger.warning(f"Body search error: {e}")
            return []

    # ── 终端执行 ──

    def exec(self, command: str, timeout: int = 30, workdir: Optional[str] = None) -> Dict[str, Any]:
        """执行命令"""
        self._operation_count += 1
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=workdir or str(ARIS_HOME),
            )
            return {
                "output": result.stdout,
                "error": result.stderr,
                "exit_code": result.returncode,
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {"output": "", "error": "Timeout", "exit_code": -1, "success": False}
        except Exception as e:
            self._error_count += 1
            return {"output": "", "error": str(e), "exit_code": -1, "success": False}

    # ── 网络 ──

    def http_get(self, url: str, timeout: int = 10) -> Optional[str]:
        """HTTP GET 请求"""
        self._operation_count += 1
        try:
            import urllib.request
            r = urllib.request.urlopen(url, timeout=timeout)
            return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            self._error_count += 1
            logger.warning(f"Body http error: {e}")
            return None

    # ── 系统信息 ──

    def system_info(self) -> Dict[str, Any]:
        """获取宿主系统信息"""
        info = {
            "hostname": os.uname().nodename if hasattr(os, 'uname') else os.environ.get('COMPUTERNAME', 'unknown'),
            "os": sys.platform,
            "python": sys.version,
            "cpu_count": os.cpu_count(),
            "cwd": os.getcwd(),
            "aris_home": str(ARIS_HOME),
            "hermes_bridge": self._hermes_bridge is not None,
        }
        return info

    # ── 统计 ──

    def stats(self) -> Dict[str, Any]:
        return {
            "operations": self._operation_count,
            "errors": self._error_count,
            "hermes_bridge": self._hermes_bridge is not None,
            "capabilities": {k: sum(1 for v in vals.values() if v) for k, vals in self._capabilities.items()},
        }


# ── CLI 入口 ──

if __name__ == "__main__":
    import sys
    
    body = HostBody()
    
    if "--info" in sys.argv:
        print(json.dumps(body.system_info(), indent=2))
    elif "--stats" in sys.argv:
        print(json.dumps(body.stats(), indent=2))
    elif "--exec" in sys.argv and len(sys.argv) > 2:
        cmd = " ".join(sys.argv[2:])
        result = body.exec(cmd)
        print(result.get("output", "")[:2000])
        if result.get("error"):
            print(f"STDERR: {result['error'][:500]}")
    else:
        print(f"Aris Host Body — {body.system_info()['hostname']}")
        print(f"  Python: {body.system_info()['python'].split()[0]}")
        print(f"  Hermes Bridge: {'✅' if body._hermes_bridge else '❌'}")
        print(f"  Usage: python -m body [--info|--stats|--exec <cmd>]")
