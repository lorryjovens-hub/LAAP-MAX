"""task-bench: 任务级智能评估基准（AGI 路线 P1-B）。

扩展 recall-bench 的方法论从"记忆 recall"到"任务完成"：

- 定义一组标准任务（代码生成、信息检索、工具调用、多步推理、适应任务）；
- 通过 TaskBackend 协议运行——任何"任务执行系统"可被测；
- 指标：success_rate / avg_completion_time / adaptation_speed；
- 适应任务：连续执行同一类型任务，测量"第二次是否比第一次快/准"。

用法::

    class MyExecutor:
        name = "my_agent"
        def execute(self, goal: str) -> dict: ...

    report = run_task_bench(MyExecutor())
    print(report.success_rate, report.adaptation_speed)
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Protocol, runtime_checkable


# ── 任务定义 ─────────────────────────────────────────────────────────────

TASK_POOL: List[Dict[str, Any]] = [
    # 代码生成
    {"goal": "写一个 Python 函数，计算斐波那契数列的第 n 项", "domain": "code_gen", "adaptation": False},
    {"goal": "写一个函数，判断字符串是否为回文", "domain": "code_gen", "adaptation": False},
    {"goal": "写一个 Python 函数，用二分查找在有序列表中找目标值", "domain": "code_gen", "adaptation": False},
    # 信息检索
    {"goal": "搜索 Python 中字典合并的几种方法", "domain": "retrieval", "adaptation": False},
    {"goal": "查找什么是递归自我改进（RSI）", "domain": "retrieval", "adaptation": False},
    {"goal": "搜索 SQLite 中全文搜索的用法", "domain": "retrieval", "adaptation": False},
    # 多步推理
    {"goal": "分析：给定一个整数列表，找出和为 target 的两个数的索引", "domain": "reasoning", "adaptation": False},
    {"goal": "推理：一个水池单开进水管 3 小时满，单开排水管 5 小时空，同时开几小时满", "domain": "reasoning", "adaptation": False},
    {"goal": "分析：三个连续奇数的和为 57，求这三个数", "domain": "reasoning", "adaptation": False},
    # 适应任务（同域连续执行，测学习速度）
    {"goal": "写一个函数，实现冒泡排序", "domain": "adapt_sort", "adaptation": True},
    {"goal": "写一个函数，实现选择排序", "domain": "adapt_sort", "adaptation": True},
    {"goal": "写一个函数，实现插入排序", "domain": "adapt_sort", "adaptation": True},
]


@runtime_checkable
class TaskBackend(Protocol):
    """任务执行系统协议。"""

    name: str

    def execute(self, goal: str) -> Dict[str, Any]:
        """执行一个任务，返回 {"success": bool, "result": str, "error": str}。"""
        ...


# ── 运行器 ───────────────────────────────────────────────────────────────


@dataclass
class TaskResult:
    goal: str = ""
    domain: str = ""
    success: bool = False
    duration_ms: float = 0.0
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TaskBenchReport:
    backend: str = ""
    total: int = 0
    success: int = 0
    success_rate: float = 0.0
    avg_duration_ms: float = 0.0
    by_domain: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    adaptation_speed: float = 0.0  # 适应任务：第 2-3 次相对第 1 次的耗时下降率
    per_item: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def run_task_bench(backend: TaskBackend, task_pool: Optional[List[Dict[str, Any]]] = None) -> TaskBenchReport:
    """执行一次任务基准。"""
    pool = task_pool or TASK_POOL
    results: List[TaskResult] = []

    for task in pool:
        t0 = time.time()
        try:
            resp = backend.execute(task["goal"])
        except Exception as e:
            resp = {"success": False, "result": "", "error": str(e)}
        duration = (time.time() - t0) * 1000
        success = bool(resp.get("success", False))
        results.append(TaskResult(
            goal=task["goal"][:60],
            domain=task["domain"],
            success=success,
            duration_ms=round(duration, 1),
            error=resp.get("error", "")[:200],
        ))

    # 汇总
    n = len(results)
    succ = sum(1 for r in results if r.success)
    by_domain: Dict[str, Dict[str, Any]] = {}
    adapt_durations: List[float] = []
    for r in results:
        d = by_domain.setdefault(r.domain, {"total": 0, "success": 0, "durations": []})
        d["total"] += 1
        d["success"] += 1 if r.success else 0
        d["durations"].append(r.duration_ms)
        if r.domain.startswith("adapt"):
            adapt_durations.append(r.duration_ms)

    domain_stats = {
        d: {
            "total": v["total"],
            "success": v["success"],
            "success_rate": round(v["success"] / v["total"], 3) if v["total"] else 0.0,
            "avg_duration_ms": round(sum(v["durations"]) / len(v["durations"]), 1) if v["durations"] else 0.0,
        }
        for d, v in sorted(by_domain.items())
    }

    # 适应速度：第 2 次以后相对第 1 次的耗时下降率
    adaptation_speed = 0.0
    if len(adapt_durations) >= 2:
        first = adapt_durations[0]
        if first > 0:
            rest_avg = sum(adapt_durations[1:]) / len(adapt_durations[1:])
            adaptation_speed = round((first - rest_avg) / first, 3)

    return TaskBenchReport(
        backend=backend.name if hasattr(backend, "name") else "unknown",
        total=n,
        success=succ,
        success_rate=round(succ / n, 3),
        avg_duration_ms=round(sum(r.duration_ms for r in results) / n, 1) if n else 0.0,
        by_domain=domain_stats,
        adaptation_speed=adaptation_speed,
        per_item=[r.to_dict() for r in results],
    )


def print_report(report: TaskBenchReport) -> None:
    print(f"\n{'='*52}")
    print(f"TASK BENCHMARK  backend={report.backend}")
    print(f"  total {report.total} | success {report.success} | "
          f"success_rate = {report.success_rate:.1%}")
    print(f"  avg_duration {report.avg_duration_ms} ms | "
          f"adaptation_speed {report.adaptation_speed:+.1%}")
    print("-" * 52)
    for domain, s in report.by_domain.items():
        bar = "#" * int(s["success_rate"] * 20)
        print(f"  {domain:<16} {s['success_rate']:6.1%}  {bar:<20} "
              f"{s['success']}/{s['total']}  {s['avg_duration_ms']:.0f}ms")
    print("=" * 52)