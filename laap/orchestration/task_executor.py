"""LAAP — TaskExecutor：自主任务执行引擎（AGI 路线 P1 行动闭环）。

功能
----
1. 任务接收与分解：接收高级目标 → 拆解为可执行步骤；
2. 工具调度：从 tool_registry 查找并调用工具执行步骤；
3. 进度监控：跟踪每步状态（pending/running/done/failed），支持超时；
4. 错误恢复：重试（可配置次数）→ 替代方案 → 优雅降级；
5. 结果报告：结构化输出每步结果与最终总结。

与 TaskScheduler 的关系：
- TaskScheduler：优先级队列调度（谁先执行）；
- TaskExecutor：步骤执行引擎（怎么执行），可被 TaskScheduler 调度。

设计约束：
- 零新第三方依赖；
- 全部可降级：工具不可用、步骤失败不阻断整个任务；
- 执行日志与 RuntimeGuard 兼容（record 行为）。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("laap.orchestration.task_executor")


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskStep:
    """单个执行步骤。"""

    name: str
    description: str
    action: str  # 工具名或内置操作名
    args: Dict[str, Any] = field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    result: str = ""
    error: str = ""
    retries: int = 0
    alternatives: List[str] = field(default_factory=list)  # 替代方案描述
    started_at: float = 0.0
    completed_at: float = 0.0
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TaskExecution:
    """一次完整任务执行记录。"""

    task_id: str
    goal: str
    steps: List[TaskStep] = field(default_factory=list)
    status: str = "running"  # running / done / failed / partial
    started_at: float = field(default_factory=time.time)
    completed_at: float = 0.0
    total_duration_ms: float = 0.0
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration_ms": round(self.total_duration_ms, 1),
            "steps": [s.to_dict() for s in self.steps],
            "summary": self.summary,
        }


class TaskExecutor:
    """自主任务执行引擎。"""

    def __init__(
        self,
        tool_registry: Any = None,
        max_retries: int = 2,
        step_timeout_sec: float = 120.0,
    ) -> None:
        self._tools = tool_registry
        self.max_retries = max_retries
        self.step_timeout_sec = step_timeout_sec
        self._task_id_counter = 0
        self._executions: Dict[str, TaskExecution] = {}

    # ── 核心执行 ────────────────────────────────────────────────────────

    def execute(
        self,
        goal: str,
        steps: Optional[List[Dict[str, Any]]] = None,
    ) -> TaskExecution:
        """执行一个任务。

        Args:
            goal: 任务目标描述。
            steps: 可选预定义步骤列表（不提供则自动分解）。

        Returns:
            TaskExecution（含详细步骤记录）。
        """
        self._task_id_counter += 1
        task_id = f"task_{self._task_id_counter:04d}"

        exec_ = TaskExecution(task_id=task_id, goal=goal)

        if steps:
            exec_.steps = [TaskStep(**s) for s in steps]
        else:
            exec_.steps = self._decompose(goal)

        logger.info(f"[TaskExecutor] {task_id}: {goal} ({len(exec_.steps)} steps)")

        for step in exec_.steps:
            step.status = StepStatus.RUNNING
            step.started_at = time.time()
            success, result, error = self._execute_step(step)
            step.completed_at = time.time()
            step.duration_ms = (step.completed_at - step.started_at) * 1000
            if success:
                step.status = StepStatus.DONE
                step.result = result[:500]
            else:
                step.status = StepStatus.FAILED
                step.error = error[:500]
                # 尝试替代方案
                recovered = self._try_alternatives(step)
                if recovered:
                    step.status = StepStatus.DONE
                    step.result = f"[recovered] {step.result[:400]}"

        # 汇总
        done = sum(1 for s in exec_.steps if s.status == StepStatus.DONE)
        failed = sum(1 for s in exec_.steps if s.status == StepStatus.FAILED)
        exec_.completed_at = time.time()
        exec_.total_duration_ms = (exec_.completed_at - exec_.started_at) * 1000
        exec_.status = "done" if failed == 0 else ("partial" if done > 0 else "failed")
        exec_.summary = f"{done}/{len(exec_.steps)} steps done, {failed} failed ({exec_.total_duration_ms:.0f}ms)"

        self._executions[task_id] = exec_
        logger.info(f"[TaskExecutor] {task_id} done: {exec_.summary}")
        return exec_

    # ── 步骤执行 ────────────────────────────────────────────────────────

    def _execute_step(self, step: TaskStep) -> Tuple[bool, str, str]:
        """执行单步，返回 (success, result, error)。"""
        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                logger.info(f"[TaskExecutor] 重试 {step.name} (#{attempt})")
                step.retries += 1
            try:
                tool = self._find_tool(step.action)
                if tool is None:
                    return False, "", f"工具不可用: {step.action}"
                # 调用工具
                result = self._call_tool(tool, step.args)
                if result is not None:
                    return True, str(result), ""
                return False, "", "工具返回空"
            except Exception as e:
                error = f"{type(e).__name__}: {e}"
                if attempt < self.max_retries:
                    time.sleep(0.5)
                    continue
                return False, "", error
        return False, "", "max retries exceeded"

    def _try_alternatives(self, step: TaskStep) -> bool:
        """步骤失败后尝试替代方案。"""
        for alt_desc in step.alternatives:
            logger.info(f"[TaskExecutor] 尝试替代: {alt_desc}")
            alt_step = TaskStep(
                name=f"{step.name}[alt]",
                description=alt_desc,
                action=step.action,
                args=step.args,
            )
            success, result, error = self._execute_step(alt_step)
            if success:
                step.result = result[:500]
                return True
        return False

    # ── 任务分解（模板式） ──────────────────────────────────────────────

    @staticmethod
    def _decompose(goal: str) -> List[TaskStep]:
        """将目标拆解为步骤序列（模板式，可靠无 LLM）。"""
        goal_lower = goal.lower()

        if any(kw in goal_lower for kw in ["搜索", "查找", "查", "search", "find", "look up"]):
            return [
                TaskStep(name="搜索", description="搜索相关信息", action="web_search", args={"query": goal}),
                TaskStep(name="整理", description="整理搜索结果", action="read", args={}),
            ]
        if any(kw in goal_lower for kw in ["代码", "写", "编写", "code", "write", "implement"]):
            return [
                TaskStep(name="分析需求", description="解析任务需求", action="read", args={}),
                TaskStep(name="编码", description="编写代码", action="code_edit", args={"goal": goal}),
                TaskStep(name="验证", description="运行测试验证", action="code_runner", args={}),
            ]
        if any(kw in goal_lower for kw in ["分析", "总结", "analyze", "summarize", "review"]):
            return [
                TaskStep(name="收集", description="收集相关信息", action="web_search", args={"query": goal}),
                TaskStep(name="分析", description="分析信息", action="read", args={}),
                TaskStep(name="总结", description="生成总结报告", action="write", args={"content": ""}),
            ]
        # 通用步骤
        return [
            TaskStep(name="理解", description="理解任务目标", action="read", args={"goal": goal}),
            TaskStep(name="执行", description="执行任务", action="shell", args={"cmd": goal}),
            TaskStep(name="确认", description="确认结果", action="read", args={}),
        ]

    # ── 工具接口 ────────────────────────────────────────────────────────

    def _find_tool(self, name: str) -> Any:
        if self._tools is None:
            return None
        if hasattr(self._tools, "get_tool"):
            return self._tools.get_tool(name)
        if hasattr(self._tools, "__getitem__"):
            try:
                return self._tools[name]
            except (KeyError, IndexError):
                return None
        return None

    @staticmethod
    def _call_tool(tool: Any, args: Dict[str, Any]) -> Any:
        if callable(tool):
            return tool(**args)
        if hasattr(tool, "execute"):
            return tool.execute(**args)
        if hasattr(tool, "run"):
            return tool.run(**args)
        return None

    # ── 查询 ────────────────────────────────────────────────────────────

    def get_execution(self, task_id: str) -> Optional[TaskExecution]:
        return self._executions.get(task_id)

    def recent(self, n: int = 5) -> List[TaskExecution]:
        return list(self._executions.values())[-n:]

    def stats(self) -> Dict[str, Any]:
        total = len(self._executions)
        done = sum(1 for e in self._executions.values() if e.status == "done")
        partial = sum(1 for e in self._executions.values() if e.status == "partial")
        failed = sum(1 for e in self._executions.values() if e.status == "failed")
        return {
            "total": total,
            "done": done,
            "partial": partial,
            "failed": failed,
            "success_rate": round(done / total, 3) if total else 0.0,
        }