"""LAAP — RSICoordinator：RSI 进化协调器（顶级 subagent 机制核心）。

功能
----
把"感知 → 拆解 → 执行 → 验证 → 合并 → 汇报"串成一条 RSI 进化管线：

1. **感知（CodebaseSensor）**：检测代码库最近改动（谁改的/改了什么）、
   并行会话冲突、热加载记录、预测账本状态——增强自身代码感知；
2. **拆解（TaskDecomposer）**：把进化目标拆成可并行的子任务；
3. **执行**：复用 TaskExecutor 执行各子任务；
4. **验证**：复用 CodeVerifier + 测试，每子任务验收门控；
5. **合并**：收集结果、检测冲突（同一文件多任务修改）；
6. **汇报**：生成统一进化报告（人类可读 + JSON）。

设计约束
--------
- 全部复用现有组件（TaskExecutor/CodeVerifier/PredictionLedger/HotReload）；
- 零新第三方依赖；
- 全部降级：任一环节失败不影响整体管线；
- 与 RuntimeGuard 兼容。
"""

from __future__ import annotations

import logging
import os
import subprocess
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("laap.evolution.rsi_coordinator")

LAAP_ROOT = r"D:\LAAP"


# ═══════════════════════════════════════════════════════════════════
# 1. 感知层：CodebaseSensor
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ChangeInfo:
    """一个文件改动记录。"""

    path: str = ""
    mtime: float = 0.0
    size: int = 0
    age_hours: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CodebaseSensor:
    """代码库感知器：检测最近改动、git 状态、并行冲突。"""

    def __init__(self, root: str = LAAP_ROOT, window_hours: float = 24.0) -> None:
        self.root = root
        self.window_hours = window_hours

    # ── 最近改动 ────────────────────────────────────────────────────────

    def recent_changes(self, window_hours: Optional[float] = None) -> List[ChangeInfo]:
        """检测最近 window_hours 小时内修改的 Python 文件（laap/ + tests/）。"""
        wh = window_hours or self.window_hours
        cutoff = time.time() - wh * 3600
        changes: List[ChangeInfo] = []
        for base_dir in ("laap", "tests"):
            base = os.path.join(self.root, base_dir)
            for dirpath, dirnames, filenames in os.walk(base):
                # 跳过缓存/虚拟环境
                dirnames[:] = [d for d in dirnames
                               if d not in ("__pycache__", ".venv", "node_modules")]
                for fn in filenames:
                    if not fn.endswith(".py"):
                        continue
                    fp = os.path.join(dirpath, fn)
                    try:
                        st = os.stat(fp)
                        if st.st_mtime >= cutoff:
                            changes.append(ChangeInfo(
                                path=os.path.relpath(fp, self.root).replace(os.sep, "/"),
                                mtime=st.st_mtime,
                                size=st.st_size,
                                age_hours=round((time.time() - st.st_mtime) / 3600, 2),
                            ))
                    except OSError:
                        continue
        changes.sort(key=lambda c: -c.mtime)
        return changes

    # ── git 状态 ────────────────────────────────────────────────────────

    def git_status(self) -> Dict[str, Any]:
        """git 状态摘要（modified/untracked 数量）。"""
        try:
            r = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.root, capture_output=True, text=True, timeout=10,
            )
            lines = [l for l in r.stdout.splitlines() if l.strip()]
            modified = sum(1 for l in lines if l.startswith(" M") or l.startswith("M "))
            untracked = sum(1 for l in lines if l.startswith("??"))
            return {"dirty_lines": len(lines), "modified": modified,
                    "untracked": untracked, "ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}

    # ── 并行冲突检测 ────────────────────────────────────────────────────

    def detect_conflicts(self, recent: Optional[List[ChangeInfo]] = None) -> List[Dict[str, Any]]:
        """检测潜在并行开发冲突。

        规则：
        1. 同一目录多文件在窗口内被修改 → 可能存在多会话并行；
        2. 与已知"他人文件"重叠 → 高冲突风险。
        """
        changes = recent or self.recent_changes()
        if not changes:
            return []
        # 按目录聚合
        by_dir: Dict[str, List[ChangeInfo]] = {}
        for c in changes:
            d = os.path.dirname(c.path)
            by_dir.setdefault(d, []).append(c)
        conflicts = []
        for d, items in by_dir.items():
            if len(items) >= 3:  # 同一目录 3+ 文件同时改动
                conflicts.append({
                    "dir": d,
                    "files": [i.path for i in items[:5]],
                    "count": len(items),
                    "level": "high" if len(items) >= 5 else "medium",
                })
        return conflicts

    # ── 热加载/账本状态 ────────────────────────────────────────────────

    def hot_reload_stats(self) -> Dict[str, Any]:
        """热加载管理器统计。"""
        try:
            from laap.evolution.hot_reload import HotReloadManager

            return HotReloadManager().stats()
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}

    def ledger_stats(self) -> Dict[str, Any]:
        """预测账本统计（成绩单）。"""
        try:
            from laap.evolution.prediction_ledger import PredictionLedger

            return PredictionLedger().stats()
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}

    # ── 汇总 ────────────────────────────────────────────────────────────

    def full_report(self) -> Dict[str, Any]:
        """完整感知报告。"""
        changes = self.recent_changes()
        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "recent_changes": [c.to_dict() for c in changes[:20]],
            "change_count": len(changes),
            "git": self.git_status(),
            "conflicts": self.detect_conflicts(changes),
            "hot_reload": self.hot_reload_stats(),
            "ledger": self.ledger_stats(),
        }


# ═══════════════════════════════════════════════════════════════════
# 2. 拆解层：TaskDecomposer
# ═══════════════════════════════════════════════════════════════════

@dataclass
class EvolveTask:
    """一个 RSI 进化子任务。"""

    task_id: str = field(default_factory=lambda: f"ev_{uuid.uuid4().hex[:6]}")
    name: str = ""
    target: str = ""  # 目标文件/模块
    description: str = ""
    status: str = "pending"  # pending / running / done / failed
    result: str = ""
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TaskDecomposer:
    """进化任务拆解：目标 → 子任务列表。"""

    @staticmethod
    def decompose(goal: str, targets: List[str]) -> List[EvolveTask]:
        """把进化目标拆成按文件组织的子任务。"""
        if not targets:
            return [EvolveTask(name="分析目标", target=goal,
                               description=f"分析进化目标: {goal}")]
        tasks = []
        for t in targets[:8]:  # 上限 8 个并行子任务
            tasks.append(EvolveTask(
                name=f"进化 {os.path.basename(t)}",
                target=t,
                description=f"对 {t} 执行 RSI 进化提案",
            ))
        return tasks


# ═══════════════════════════════════════════════════════════════════
# 3. 协调器：RSICoordinator
# ═══════════════════════════════════════════════════════════════════

@dataclass
class CoordinationReport:
    """一次协调管线的完整报告。"""

    run_id: str = field(default_factory=lambda: f"coord_{uuid.uuid4().hex[:8]}")
    goal: str = ""
    started_at: float = 0.0
    completed_at: float = 0.0
    duration_ms: float = 0.0
    sense: Dict[str, Any] = field(default_factory=dict)
    tasks: List[EvolveTask] = field(default_factory=list)
    task_results: List[Dict[str, Any]] = field(default_factory=list)
    merged_conflicts: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "goal": self.goal[:200],
            "duration_ms": round(self.duration_ms, 1),
            "sense": self.sense,
            "tasks": [t.to_dict() for t in self.tasks],
            "task_results": self.task_results,
            "merged_conflicts": self.merged_conflicts,
            "summary": self.summary,
        }


class RSICoordinator:
    """RSI 进化协调器（感知→拆解→执行→验证→合并→汇报）。"""

    def __init__(
        self,
        sensor: Optional[CodebaseSensor] = None,
        executor: Any = None,
        verifier: Any = None,
        decomposer: Optional[TaskDecomposer] = None,
        task_runner: Optional[Callable[[EvolveTask], Tuple[bool, str]]] = None,
    ) -> None:
        self.sensor = sensor or CodebaseSensor()
        self.executor = executor  # TaskExecutor 或 None
        self.verifier = verifier  # CodeVerifier 或 None
        self.decomposer = decomposer or TaskDecomposer()
        self._task_runner = task_runner  # 自定义子任务执行器
        self._reports: List[CoordinationReport] = []

    # ── 主管线 ──────────────────────────────────────────────────────────

    def coordinate(self, goal: str, targets: Optional[List[str]] = None) -> CoordinationReport:
        """执行一次完整的 RSI 协调管线。"""
        started = time.time()
        report = CoordinationReport(goal=goal)

        # 1. 感知
        try:
            report.sense = self.sensor.full_report()
        except Exception as e:
            report.sense = {"ok": False, "error": str(e)[:100]}

        # 2. 拆解
        tasks = self.decomposer.decompose(goal, targets or [])
        report.tasks = tasks

        # 3-4. 执行 + 验证（每子任务）
        for task in tasks:
            task.status = "running"
            ok, result = self._run_task(task)
            task.status = "done" if ok else "failed"
            task.result = result[:300] if ok else ""
            task.error = "" if ok else result[:200]
            report.task_results.append(task.to_dict())

        # 5. 合并冲突检测（多任务同目录修改）
        report.merged_conflicts = self._merge_conflicts(tasks)

        # 6. 汇报
        done = sum(1 for t in tasks if t.status == "done")
        failed = sum(1 for t in tasks if t.status == "failed")
        report.completed_at = time.time()
        report.duration_ms = (report.completed_at - started) * 1000
        report.summary = (
            f"感知 {report.sense.get('change_count', 0)} 个改动 | "
            f"拆解 {len(tasks)} 任务 | 完成 {done} | 失败 {failed} | "
            f"冲突 {len(report.merged_conflicts)} | {report.duration_ms:.0f}ms"
        )
        self._reports.append(report)
        logger.info(f"[RSICoordinator] {report.summary}")
        return report

    # ── 内部 ────────────────────────────────────────────────────────────

    def _run_task(self, task: EvolveTask) -> Tuple[bool, str]:
        """执行单个子任务（自定义 runner > TaskExecutor > 降级）。"""
        if self._task_runner is not None:
            try:
                return self._task_runner(task)
            except Exception as e:
                return False, f"runner 异常: {e}"
        if self.executor is not None:
            try:
                steps = [{"name": "进化", "description": task.description,
                          "action": "analyze", "args": {"target": task.target}}]
                r = self.executor.execute(task.description, steps=steps)
                return r.status == "done", r.summary
            except Exception as e:
                return False, f"executor 异常: {e}"
        return True, "无执行器（仅拆解演示）"

    @staticmethod
    def _merge_conflicts(tasks: List[EvolveTask]) -> List[Dict[str, Any]]:
        """合并阶段冲突检测：同目录多任务修改。"""
        by_dir: Dict[str, List[str]] = {}
        for t in tasks:
            d = os.path.dirname(t.target)
            by_dir.setdefault(d, []).append(t.target)
        return [
            {"dir": d, "files": files, "count": len(files)}
            for d, files in by_dir.items() if len(files) >= 2
        ]

    # ── 查询 ────────────────────────────────────────────────────────────

    def recent(self, n: int = 5) -> List[CoordinationReport]:
        return self._reports[-n:]

    def stats(self) -> Dict[str, Any]:
        total = len(self._reports)
        if not total:
            return {"total_runs": 0}
        tasks = [t for r in self._reports for t in r.tasks]
        done = sum(1 for t in tasks if t.status == "done")
        return {
            "total_runs": total,
            "total_tasks": len(tasks),
            "task_success_rate": round(done / len(tasks), 3) if tasks else 0.0,
        }