"""LAAP — 分层证据访问（AGI 路线 #3）。

对应 AHE 经验可观测性支柱：原始轨迹 → per-task 根因报告 → 聚合概览。

设计
----
两层结构：
1. PerTaskReport：一次任务或轮次的根因分析报告（含失败记录关联）；
2. EvidenceAggregator：收集多份 PerTaskReport，生成聚合概览（趋势、热点、高频组件）。

与 StructuredFailureRecord 的关系：
- PerTaskReport 引用 0-N 条 StructuredFailureRecord；
- EvidenceAggregator 汇总所有报告中的失败模式。
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger("laap.cognition.evidence_view")

DEFAULT_EVIDENCE_DIR = "~/.laap/evidence/"


@dataclass
class PerTaskReport:
    """一次任务或轮次的根因分析报告。"""

    report_id: str = field(default_factory=lambda: f"rpt_{uuid.uuid4().hex[:8]}")
    task_goal: str = ""  # 任务目标
    success: bool = False
    duration_ms: float = 0.0
    failure_records: List[Dict[str, Any]] = field(default_factory=list)  # 关联的失败记录
    root_cause_summary: str = ""  # 一句话根因总结
    suggested_components: List[str] = field(default_factory=list)  # 建议改进的组件
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceOverview:
    """聚合概览（多份报告汇总）。"""

    total_reports: int = 0
    success_count: int = 0
    success_rate: float = 0.0
    total_failures: int = 0
    component_hotspots: Dict[str, int] = field(default_factory=dict)  # 组件故障频次
    top_failure_patterns: List[str] = field(default_factory=list)
    avg_duration_ms: float = 0.0
    generated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EvidenceAggregator:
    """分层证据收集器。"""

    def __init__(self, storage_dir: str = DEFAULT_EVIDENCE_DIR) -> None:
        self._dir = os.path.expanduser(storage_dir)
        os.makedirs(self._dir, exist_ok=True)
        self._reports: List[PerTaskReport] = []

    # ── 写入 ────────────────────────────────────────────────────────────

    def add_report(self, report: PerTaskReport) -> str:
        """添加一份报告（内存 + JSONL 持久化）。"""
        self._reports.append(report)
        self._write(report)
        logger.info(
            f"[Evidence] {report.report_id}: "
            f"{'SUCCESS' if report.success else 'FAIL'} "
            f"{report.task_goal[:60]}"
        )
        return report.report_id

    def create_report(
        self,
        task_goal: str,
        success: bool,
        failure_records: Optional[List[Dict[str, Any]]] = None,
        root_cause_summary: str = "",
        suggested_components: Optional[List[str]] = None,
        duration_ms: float = 0.0,
    ) -> PerTaskReport:
        """创建并添加一份报告（快捷方法）。"""
        report = PerTaskReport(
            task_goal=task_goal,
            success=success,
            failure_records=failure_records or [],
            root_cause_summary=root_cause_summary,
            suggested_components=suggested_components or [],
            duration_ms=duration_ms,
        )
        self.add_report(report)
        return report

    # ── 查询 ────────────────────────────────────────────────────────────

    def overview(self) -> EvidenceOverview:
        """生成聚合概览。"""
        n = len(self._reports)
        if n == 0:
            return EvidenceOverview()

        succ = sum(1 for r in self._reports if r.success)
        all_failures = [r for r in self._reports if not r.success]
        total_fail = sum(len(r.failure_records) for r in self._reports)
        durations = [r.duration_ms for r in self._reports if r.duration_ms > 0]

        # 组件热点
        hotspots: Dict[str, int] = {}
        for r in self._reports:
            for comp in r.suggested_components:
                hotspots[comp] = hotspots.get(comp, 0) + 1
            for fr in r.failure_records:
                comp = fr.get("suggested_component", fr.get("layers", {}).get("abstract", ""))
                if comp:
                    hotspots[comp] = hotspots.get(comp, 0) + 1

        # 高频失败模式
        patterns: Dict[str, int] = {}
        for r in self._reports:
            for fr in r.failure_records:
                surface = fr.get("layers", {}).get("surface", "")
                if surface:
                    patterns[surface] = patterns.get(surface, 0) + 1
        top_patterns = sorted(patterns, key=patterns.get, reverse=True)[:5]

        return EvidenceOverview(
            total_reports=n,
            success_count=succ,
            success_rate=round(succ / n, 3),
            total_failures=total_fail,
            component_hotspots=dict(sorted(hotspots.items(), key=lambda x: -x[1])[:10]),
            top_failure_patterns=top_patterns,
            avg_duration_ms=round(sum(durations) / len(durations), 1) if durations else 0.0,
        )

    def recent_reports(self, n: int = 10) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._reports[-n:]]

    def stats(self) -> Dict[str, Any]:
        return self.overview().to_dict()

    # ── 内部 ────────────────────────────────────────────────────────────

    def _write(self, report: PerTaskReport) -> None:
        path = os.path.join(self._dir, "evidence.jsonl")
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(report.to_dict(), ensure_ascii=False, default=str) + "\n"
                )
        except OSError as e:
            logger.warning(f"[Evidence] write failed: {e}")

    def load(self) -> int:
        """从持久化文件恢复报告。"""
        path = os.path.join(self._dir, "evidence.jsonl")
        if not os.path.exists(path):
            return 0
        count = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    self._reports.append(PerTaskReport(**data))
                    count += 1
                except (json.JSONDecodeError, TypeError):
                    continue
        return count