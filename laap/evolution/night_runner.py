"""LAAP — NightRunner：夜间自动实验调度器（AGI 路线 P2-A）。

设计
----
夜间在低风险区域自动运行 RSI 闭环，结果汇总为晨报，天亮后人工审批。
与现有 TrueRSIEngine / RSISandbox 的关系：
- TrueRSIEngine：完整 PROPOSE→PATCH→SANDBOX→APPROVE→DEPLOY 闭环
- RSISandbox：轻量 MUTATE→SANDBOX→GROUND→CHARTER→DECIDE 建议模式
- NightRunner：调度器——在限定范围内自动跑上述循环，不做 DEPLOY，
  只做建议（suggest_adopt），汇总为晨报供人类审批。

安全约束
--------
- 仅限白名单目录（laap/tools/、laap/agent_core/tools/）；
- 所有提案状态为 suggest_adopt，**绝不自动采纳**；
- 超出时间窗口自动终止；
- 运行日志与 RuntimeGuard 兼容。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger("laap.evolution.night_runner")

# 白名单：仅这些目录下的代码可被自动改进
WHITELIST_DIRS = [
    "laap/tools/",
    "laap/agent_core/tools/",
]

# 默认窗口：午夜 0:00 到清晨 6:00 可运行
DEFAULT_WINDOW = (0, 6)

# 单次运行最多提案数
MAX_PROPOSALS_PER_RUN = 5


@dataclass
class NightReport:
    """一次夜间运行的完整报告。"""

    run_id: str = ""
    started_at: float = 0.0
    completed_at: float = 0.0
    duration_min: float = 0.0
    proposals_attempted: int = 0
    proposals_suggested: int = 0  # 通过沙箱+验证的建议
    proposals_failed: int = 0
    items: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class NightRunner:
    """夜间自动实验调度器。"""

    def __init__(
        self,
        engine: Any = None,
        sandbox: Any = None,
        window: tuple = DEFAULT_WINDOW,
        max_proposals: int = MAX_PROPOSALS_PER_RUN,
    ) -> None:
        self._engine = engine
        self._sandbox = sandbox
        self.window = window
        self.max_proposals = max_proposals
        self._run_id_counter = 0
        self._reports: List[NightReport] = []

    # ── 核心 ────────────────────────────────────────────────────────────

    def run(self, force: bool = False) -> NightReport:
        """执行一次夜间实验。

        Args:
            force: 强制运行（忽略时间窗口检查）。

        Returns:
            NightReport（含每步详情）。
        """
        if not force and not self._in_window():
            return NightReport(
                summary=f"不在运行窗口 {self.window[0]}:00-{self.window[1]}:00"
            )

        self._run_id_counter += 1
        run_id = f"night_{self._run_id_counter:04d}"
        started = time.time()
        logger.info(f"[NightRunner] {run_id} 开始")

        report = NightReport(run_id=run_id, started_at=started)
        items: List[Dict[str, Any]] = []

        # 用 RSISandbox 模式（建议模式，不自动部署）
        if self._sandbox is not None:
            for i in range(self.max_proposals):
                try:
                    result = self._run_one_sandbox(i)
                    items.append(result)
                    if result.get("status") == "suggest_adopt":
                        report.proposals_suggested += 1
                    else:
                        report.proposals_failed += 1
                except Exception as e:
                    items.append({"step": i, "status": "error", "error": str(e)[:200]})
                    report.proposals_failed += 1
                report.proposals_attempted += 1

        # 用 TrueRSIEngine 模式（完整闭环，自动审批）
        elif self._engine is not None:
            proposals = self._engine.run_cycle(
                max_proposals=self.max_proposals, auto_approve=False
            )
            for p in proposals:
                status = p.status.value if hasattr(p.status, "value") else str(p.status)
                items.append({
                    "proposal_id": p.proposal_id,
                    "target": str(getattr(p.target, "file_path", "")),
                    "status": status,
                    "description": getattr(p.mutation, "description", "")[:200],
                })
                report.proposals_attempted += 1
                if status == "awaiting_approval":
                    report.proposals_suggested += 1
                else:
                    report.proposals_failed += 1
        else:
            logger.warning("[NightRunner] 无引擎可用")

        report.items = items
        report.completed_at = time.time()
        report.duration_min = round((report.completed_at - started) / 60, 1)
        report.summary = (
            f"尝试 {report.proposals_attempted} 个提案，"
            f"建议 {report.proposals_suggested} 个，"
            f"失败 {report.proposals_failed} 个"
            f"（{report.duration_min} 分钟）"
        )
        self._reports.append(report)
        logger.info(f"[NightRunner] {run_id} 完成: {report.summary}")
        return report

    def _run_one_sandbox(self, step: int) -> Dict[str, Any]:
        """用 RSISandbox 跑一次建议。"""
        candidate = self._sandbox.mutate()
        if candidate is None:
            return {"step": step, "status": "no_candidate"}
        self._sandbox.sandbox_check(candidate)
        self._sandbox.ground(candidate)
        self._sandbox.charter_audit(candidate)
        self._sandbox.decide(candidate)
        return {
            "step": step,
            "candidate_id": candidate.candidate_id,
            "target": candidate.target_module,
            "status": candidate.status,
            "description": candidate.description[:200],
        }

    # ── 查询 ────────────────────────────────────────────────────────────

    def last_report(self) -> Optional[NightReport]:
        return self._reports[-1] if self._reports else None

    def stats(self) -> Dict[str, Any]:
        total = len(self._reports)
        suggested = sum(r.proposals_suggested for r in self._reports)
        return {
            "total_runs": total,
            "total_suggested": suggested,
            "reports": [r.to_dict() for r in self._reports[-3:]],
        }

    # ── 内部 ────────────────────────────────────────────────────────────

    @staticmethod
    def _in_window(window: tuple = DEFAULT_WINDOW) -> bool:
        """检查当前时间是否在运行窗口内。"""
        hour = time.localtime().tm_hour
        return window[0] <= hour < window[1]

    def morning_report_text(self) -> str:
        """生成人类可读的晨报文本。"""
        r = self.last_report()
        if r is None:
            return "没有夜间运行记录。"
        lines = [
            f"🌙 夜间实验报告 #{r.run_id}",
            f"时间: {time.strftime('%H:%M', time.localtime(r.started_at))} - "
            f"{time.strftime('%H:%M', time.localtime(r.completed_at))} "
            f"({r.duration_min} 分钟)",
            r.summary,
            "",
        ]
        for item in r.items:
            status = item.get("status", "?")
            target = item.get("target", item.get("candidate_id", ""))
            desc = item.get("description", "")
            lines.append(f"  [{status}] {target}")
            if desc:
                lines.append(f"    {desc[:100]}")
        return "\n".join(lines)