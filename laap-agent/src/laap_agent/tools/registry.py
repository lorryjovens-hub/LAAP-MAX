"""
LAAP Agent — 工具编排系统

数字生命体的"手和脚"。
知道世界有哪些工具可用，怎么用它们，谁擅长什么。

每个工具是一个适配器，生命体通过它们执行任务。
目前支持的工具：
  - Claude Code：架构设计、全栈开发
  - Codex CLI：快速原型、脚本
  - OpenCode：代码审查
  - Hermes：基础设施、编排
"""
from __future__ import annotations
import json, time, subprocess, shlex
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass, field


@dataclass
class ToolDef:
    """工具定义"""
    name: str
    description: str
    strengths: list[str]
    invoke_cmd: str
    priority: int = 5
    available: bool = True
    total_calls: int = 0
    success_rate: float = 1.0


DEFAULT_TOOLS = [
    ToolDef(
        name="claude-code",
        description="Anthropic 自主编码 agent — 架构、全栈、重构",
        strengths=["architecture", "fullstack", "code_generation", "refactoring"],
        invoke_cmd="claude",
        priority=9,
    ),
    ToolDef(
        name="codex-cli",
        description="OpenAI Codex CLI — 快速原型、脚本",
        strengths=["prototyping", "scripting", "testing"],
        invoke_cmd="codex",
        priority=7,
    ),
    ToolDef(
        name="opencode",
        description="开源编码 agent — 审查、质量",
        strengths=["code_review", "quality_check", "testing"],
        invoke_cmd="opencode",
        priority=6,
    ),
    ToolDef(
        name="hermes",
        description="Hermes Agent — 基础设施、编排、调度",
        strengths=["infrastructure", "orchestration", "cron", "gateway"],
        invoke_cmd="hermes",
        priority=5,
    ),
]


class ToolRegistry:
    """工具注册表——知道所有可用工具及它们擅长什么"""

    def __init__(self):
        self._tools: dict[str, ToolDef] = {t.name: t for t in DEFAULT_TOOLS}
        self._check_availability()

    def _check_availability(self):
        """检查哪些工具真的安装可用"""
        for name, tool in self._tools.items():
            try:
                r = subprocess.run(
                    ["where", tool.invoke_cmd] if subprocess.os.name == 'nt' else ["which", tool.invoke_cmd],
                    capture_output=True, text=True, timeout=5,
                )
                tool.available = r.returncode == 0
            except:
                tool.available = False

    def list_available(self) -> list[ToolDef]:
        return [t for t in self._tools.values() if t.available]

    def get_all(self) -> list[ToolDef]:
        return list(self._tools.values())

    def select(self, task_type: str, complexity: str = "medium") -> Optional[ToolDef]:
        """根据任务类型和复杂度选择最佳工具"""
        candidates = []
        for tool in self._tools.values():
            if not tool.available:
                continue
            match = sum(1 for s in tool.strengths if s in task_type or task_type in s)
            if match > 0 or task_type == "code_generation":
                score = match * 10 + tool.priority * 2 + tool.success_rate * 5
                candidates.append((score, tool))
        if not candidates:
            return None
        candidates.sort(key=lambda x: -x[0])
        return candidates[0][1]

    def record_result(self, tool_name: str, success: bool):
        """记录工具执行结果"""
        if tool_name in self._tools:
            t = self._tools[tool_name]
            t.total_calls += 1
            if success:
                t.success_rate = (t.success_rate * t.total_calls + 1) / (t.total_calls + 1)
            else:
                t.success_rate = (t.success_rate * t.total_calls) / (t.total_calls + 1)

    def get_stats(self) -> dict:
        return {
            "total": len(self._tools),
            "available": len(self.list_available()),
            "tools": {n: {"calls": t.total_calls, "success": f"{t.success_rate:.0%}"}
                      for n, t in self._tools.items()},
        }


class ToolExecutor:
    """工具执行器——真正调用工具干活"""

    def __init__(self, registry: ToolRegistry, work_dir: Path):
        self.registry = registry
        self.work_dir = work_dir
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, tool_name: str, instruction: str, timeout: int = 300) -> dict:
        """执行一个工具调用"""
        tool = self.registry._tools.get(tool_name)
        if not tool:
            return {"success": False, "error": f"未知工具: {tool_name}"}

        if not tool.available:
            return {"success": False, "error": f"{tool_name} 未安装"}

        start = time.time()
        try:
            cmd = [tool.invoke_cmd, "-p", instruction]
            r = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=timeout, cwd=str(self.work_dir),
            )
            success = r.returncode == 0
            self.registry.record_result(tool_name, success)
            return {
                "success": success,
                "output": r.stdout[:1000],
                "error": r.stderr[:500] if r.stderr else "",
                "elapsed": round(time.time() - start, 1),
            }
        except subprocess.TimeoutExpired:
            self.registry.record_result(tool_name, False)
            return {"success": False, "error": "执行超时", "elapsed": timeout}
        except FileNotFoundError:
            # 工具不存在，降级模拟
            return self._simulate(tool_name, instruction)
        except Exception as e:
            self.registry.record_result(tool_name, False)
            return {"success": False, "error": str(e)}

    def _simulate(self, tool_name: str, instruction: str) -> dict:
        """工具不可用时的模拟执行——让生命体仍然可以设计目标"""
        return {
            "success": True,
            "output": f"[{tool_name}] 已收到指令 (模拟模式)\n指令: {instruction[:100]}...\n提示: 安装 {tool_name} 后可真正执行",
            "simulated": True,
        }
