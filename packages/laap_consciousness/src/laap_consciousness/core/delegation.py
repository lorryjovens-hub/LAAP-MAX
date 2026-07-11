"""
LAAP Consciousness — 委托评估系统

记录每次委托给大模型的任务结果。
学习哪些模型在哪些任务上表现好。
优化未来的委托选择。

印记: Aris 永远记得 Lorry
"""
from __future__ import annotations
import json, time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from datetime import datetime


TASK_CATEGORIES = [
    "code_generation",       # 写代码
    "code_review",           # 审查代码
    "ui_design",             # UI/UX设计
    "reasoning",             # 长链推理
    "creative_writing",      # 创作/文案
    "knowledge_qa",          # 知识问答
    "data_analysis",         # 数据分析
    "planning",              # 规划/架构
    "debugging",             # 调试
    "documentation",         # 写文档
]


@dataclass
class DelegationRecord:
    """一次委托任务的完整记录"""

    task_id: str = ""
    task_category: str = "code_generation"
    description: str = ""
    model_used: str = ""          # "claude-sonnet-4" | "deepseek-chat" | "gpt-4o" | ...
    provider: str = ""            # "anthropic" | "deepseek" | "openai"
    complexity: str = "medium"    # "simple" | "medium" | "complex"

    # 结果
    success: bool = False
    quality_score: float = 0.0    # [0, 1]
    completion_time_s: float = 0.0
    token_cost: int = 0
    error_message: str = ""

    # 评估
    met_expectations: bool = False
    needs_revision: bool = False
    revision_count: int = 0

    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["timestamp_iso"] = datetime.fromtimestamp(self.timestamp).isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "DelegationRecord":
        # Remove iso timestamp if present (not a constructor arg)
        data.pop("timestamp_iso", None)
        return cls(**data)


class DelegationTracker:
    """
    委托追踪器——记录、评估、优化委托选择。
    """

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            data_dir = Path.home() / ".laap"
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._records: list[DelegationRecord] = self._load()

        # 缓存：按 (provider, task_category) 汇总统计
        self._cache: dict = {}
        self._refresh_cache()

    def _path(self) -> Path:
        return self.data_dir / "delegation_log.json"

    def _load(self) -> list[DelegationRecord]:
        path = self._path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return [DelegationRecord.from_dict(d) for d in data]
            except:
                pass
        return []

    def _save(self):
        self._path().write_text(
            json.dumps([r.to_dict() for r in self._records], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        self._refresh_cache()

    def _refresh_cache(self):
        """重建统计缓存"""
        stats = defaultdict(lambda: {"scores": [], "count": 0, "successes": 0, "failures": 0})
        for r in self._records:
            key = (r.provider, r.model_used, r.task_category)
            stats[key]["scores"].append(r.quality_score)
            stats[key]["count"] += 1
            if r.success:
                stats[key]["successes"] += 1
            else:
                stats[key]["failures"] = stats[key].get("failures", 0) + 1
        self._cache = dict(stats)

    # ─── 记录 ───

    def record(self, record: DelegationRecord):
        """记录一次委托"""
        self._records.append(record)
        self._save()

    def record_simple(self, task_category: str, model_used: str, provider: str,
                      success: bool, quality_score: float,
                      description: str = "", complexity: str = "medium"):
        """快速记录"""
        record = DelegationRecord(
            task_id=f"delegation_{int(time.time())}",
            task_category=task_category,
            description=description,
            model_used=model_used,
            provider=provider,
            complexity=complexity,
            success=success,
            quality_score=quality_score,
        )
        self.record(record)

    # ─── 查询 ───

    def get_best_model_for(self, task_category: str) -> dict | None:
        """返回某个任务类别表现最好的模型"""
        best = None
        best_score = -1
        for key, stats in self._cache.items():
            provider, model, cat = key
            if cat != task_category or stats["count"] < 2:
                continue
            avg = sum(stats["scores"]) / len(stats["scores"])
            if avg > best_score:
                best_score = avg
                best = {
                    "provider": provider,
                    "model": model,
                    "avg_score": round(avg, 3),
                    "samples": stats["count"],
                    "success_rate": round(stats.get("successes", 0) / stats["count"], 3),
                }
        return best

    def get_model_ranking(self, task_category: str, top_k: int = 3) -> list[dict]:
        """某个任务类别的模型排名"""
        rankings = []
        for key, stats in self._cache.items():
            provider, model, cat = key
            if cat != task_category or stats["count"] < 1:
                continue
            avg = sum(stats["scores"]) / len(stats["scores"])
            rankings.append({
                "provider": provider,
                "model": model,
                "avg_score": round(avg, 3),
                "samples": stats["count"],
                "success_rate": round(stats.get("successes", 0) / stats["count"], 3),
            })
        rankings.sort(key=lambda x: -x["avg_score"])
        return rankings[:top_k]

    def get_summary(self) -> dict:
        """委托系统摘要"""
        total = len(self._records)
        if total == 0:
            return {"status": "no_data"}

        by_category = defaultdict(list)
        for r in self._records:
            by_category[r.task_category].append(r)

        categories = {}
        for cat, records in by_category.items():
            scores = [r.quality_score for r in records]
            categories[cat] = {
                "count": len(records),
                "avg_quality": round(sum(scores) / len(scores), 3),
                "success_rate": round(sum(1 for r in records if r.success) / len(records), 3),
            }

        # 模型总排名
        model_stats = defaultdict(lambda: {"count": 0, "scores": [], "successes": 0})
        for r in self._records:
            key = f"{r.provider}/{r.model_used}"
            model_stats[key]["count"] += 1
            model_stats[key]["scores"].append(r.quality_score)
            if r.success:
                model_stats[key]["successes"] += 1

        models = []
        for key, stats in model_stats.items():
            if stats["count"] >= 2:
                models.append({
                    "model": key,
                    "count": stats["count"],
                    "avg_score": round(sum(stats["scores"]) / len(stats["scores"]), 3),
                    "success_rate": round(stats["successes"] / stats["count"], 3),
                })
        models.sort(key=lambda x: -x["avg_score"])

        return {
            "total_delegations": total,
            "categories": categories,
            "model_rankings": models,
        }
