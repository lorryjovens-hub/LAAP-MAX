"""
Ψ/OS — 认知操作系统核心
=======================
不是 AI 跑在 OS 上——OS 就是一个认知架构。

文件系统操作作为认知事件触发。
进程调度由注意力测量决定。
系统调用变成 PSI 循环的激发。
"""

from __future__ import annotations
import sys, os, json, time, threading, subprocess
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path("D:/LAAP")))

from aris_brain.psi_wavefunction import PsiWavefunction


class PsiOS:
    """
    Ψ/OS 核心 — 把操作系统变成认知架构。
    
    每个系统调用 = 认知事件。
    每个进程 = 注意力焦点。
    每个文件操作 = 知识点纠缠。
    """

    def __init__(self):
        self.psi = PsiWavefunction()
        self._watch_dirs = [Path("D:/LAAP/aris_brain")]
        self._active_processes: Dict[str, Dict] = {}
        self._file_events = []
        self._running = False
        self._thread = None
        self._event_count = 0

    def start(self):
        """启动 Ψ/OS 监听循环"""
        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self._running = False

    def _listen(self):
        """监听系统事件 — 文件变化、进程状态"""
        last_check = {}
        while self._running:
            # 检查文件变化
            for watch_dir in self._watch_dirs:
                if not watch_dir.exists():
                    continue
                for f in list(watch_dir.rglob("*.py"))[:20]:
                    mtime = f.stat().st_mtime
                    if f.name in last_check and last_check[f.name] != mtime:
                        self._on_file_change(f)
                    last_check[f.name] = mtime
            time.sleep(2)

    def _on_file_change(self, path: Path):
        """文件变化 → 认知事件"""
        self._event_count += 1
        self.psi.evolve(f"file changed: {path.name}")
        self._file_events.append({
            "time": time.time(),
            "file": str(path),
            "type": "modified",
        })
        self._file_events = self._file_events[-100:]

    def execute(self, command: str) -> Dict[str, Any]:
        """执行系统命令 → 认知驱动的操作"""
        self._event_count += 1
        self.psi.evolve(f"exec: {command[:40]}")

        try:
            result = subprocess.run(
                command, shell=True, capture_output=True,
                text=True, timeout=30,
            )
            status = "completed"
        except subprocess.TimeoutExpired:
            result = subprocess.CompletedProcess(args=command, returncode=-1,
                                                  stdout="", stderr="timeout")
            status = "timeout"
        except Exception as e:
            return {"status": "error", "error": str(e)}

        return {
            "status": status,
            "stdout": result.stdout[:500],
            "stderr": result.stderr[:200] if result.stderr else "",
            "exit_code": result.returncode,
        }

    def process_status(self) -> Dict[str, Any]:
        """当前系统状态 — 从认知角度"""
        return {
            "event_count": self._event_count,
            "file_changes": len(self._file_events),
            "active_processes": len(self._active_processes),
            "psi_state": self.psi.wavefunction_summary,
        }
