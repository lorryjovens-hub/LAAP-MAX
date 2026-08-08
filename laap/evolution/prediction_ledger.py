"""PredictionLedger —— 决策可观测性账本（AHE 支柱 3 落地）。

背景
----
对照 AHE（Agentic Harness Engineering）三大可观测性支柱评估 LAAP 管线后，
决策可观测性是最弱的一环：现有 TrueRSIEngine / RSISandbox 记录了"改了什么"
（audit.jsonl 状态迁移），但没有记录"预期改善什么、怎么验证、是否达标"。

本模块补齐四段式流程的数据层：

    PROPOSE → PREDICT → VERIFY → RECORD

- PROPOSE: 既有 RSI 提案（TrueRSIProposal / RSICandidate），或人工登记的改进；
- PREDICT: 每次改进必须携带可证伪预测（claim + metric + direction + threshold）；
- VERIFY: 独立评估（held-in / held-out / 生产观测）产生实际值；
- RECORD: 判定 VERIFIED / FALSIFIED，append-only 落盘。

设计约束
--------
- 纯数据层：不依赖 Docker / LLM / 第三方库，零运行风险；
- 不侵入现有引擎：与 true_rsi.py 平行，通过 register() 接入；
- append-only JSONL：与 TrueRSIAuditLog 同风格，记录不可篡改（保留即证据）；
- 评估器外置：本账本只记录结果，不参与评估本身——验证方必须是循环之外的
  独立脚本/评测集（防 reward hacking，对应翁荔挑战 5）。
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Iterator, Optional

DEFAULT_LEDGER_PATH = "~/.laap/true_rsi/predictions.jsonl"

#: 与 AHE 对齐的可编辑组件清单（用于 target_component 规范化）
COMPONENTS = (
    "system_prompt",       # 系统提示
    "tool_description",    # 工具描述
    "tool_implementation", # 工具实现
    "middleware",          # 中间件
    "skill",               # 技能
    "subagent_config",     # 子 agent 配置
    "long_term_memory",    # 长期记忆
    "laap_module",         # laap/ 源码模块（TrueRSI 目标）
    "manual",              # 人工登记的外部改进（未落入上述类）
)


class PredictionStatus(str, Enum):
    """预测生命周期状态。"""

    PREDICTED = "predicted"    # 已登记，尚未验证
    VERIFIED = "verified"      # 实际值达标，预测成立
    FALSIFIED = "falsified"    # 实际值未达标，预测被证伪
    SKIPPED = "skipped"        # 因故跳过验证（须记录原因）
    EXPIRED = "expired"        # 超时未验证，自动失效


@dataclass
class PredictionRecord:
    """一条可证伪预测的完整记录。

    所有字段可被 ``asdict()`` 序列化，与 TrueRSIAuditLog 记录风格一致。
    """

    record_id: str = field(
        default_factory=lambda: f"pred_{uuid.uuid4().hex[:12]}"
    )
    #: 来源引擎："true_rsi" / "rsi_sandbox" / "manual"
    source: str = "manual"
    #: 关联提案 id（TrueRSIProposal.proposal_id 或 RSICandidate.candidate_id）
    proposal_id: str = ""
    #: 目标组件（优先取 COMPONENTS 枚举值，laap 模块可填路径）
    target_component: str = ""
    #: 预测陈述（人可读，一句"做了 X，预期 Y"）
    claim: str = ""
    #: 可证伪指标名（如 "held_out_error_rate" / "latency_ms" / "recall@30d"）
    metric: str = ""
    #: 期望方向："up" = 越大越好， "down" = 越小越好
    direction: str = "up"
    #: 达标阈值（方向敏感）
    threshold: float = 0.0
    #: 验证集类型："held_in" / "held_out" / "live"
    eval_set: str = "held_out"
    #: 基线值（改进前的指标值，用于计算变化量）
    baseline_value: Optional[float] = None
    #: 验证时限（秒）。超过则视为 EXPIRED，避免预测无限挂起
    ttl_sec: int = 7 * 24 * 3600  # 默认 7 天
    status: str = PredictionStatus.PREDICTED.value
    created_at: float = field(default_factory=time.time)
    verified_at: float = 0.0
    #: 验证后的实际值
    actual_value: Optional[float] = None
    #: 判定理由（人可读，说明为什么达标/未达标）
    verdict_reason: str = ""
    #: 证据路径（评测脚本 / 日志 / 报告文件，必须可被审计方访问）
    evidence_path: str = ""
    #: 验证者（"eval_script" / "human" / 具体评估器名——必须外置于改进循环）
    verified_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    # -- 判定辅助 ---------------------------------------------------------

    def is_satisfied(self, actual: float) -> bool:
        """方向敏感达标判定。"""
        if self.direction == "up":
            return actual >= self.threshold
        return actual <= self.threshold

    def delta(self) -> Optional[float]:
        """相对基线的变化量（无基线时返回 None）。"""
        if self.baseline_value is None or self.actual_value is None:
            return None
        return self.actual_value - self.baseline_value


class PredictionLedger:
    """预测账本：append-only JSONL 存储 + 统计。

    用法::

        from laap.evolution.prediction_ledger import PredictionLedger

        ledger = PredictionLedger()
        rid = ledger.register(
            source="true_rsi",
            proposal_id="true_rsi_abc123",
            target_component="laap_module",
            claim="重构记忆压缩后，跨会话召回率应提升",
            metric="recall@30d", direction="up", threshold=0.80,
            baseline_value=0.62, eval_set="held_out",
        )
        ledger.record_verdict(
            rid, actual_value=0.84,
            evidence_path="D:/LAAP/benchmarks/recall_baseline.json",
            verified_by="eval_script",
            note="30 天窗口实测",
        )
        print(ledger.stats())
    """

    def __init__(self, path: str = DEFAULT_LEDGER_PATH) -> None:
        self.path = os.path.expanduser(path)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    # -- 写入 -------------------------------------------------------------

    def register(
        self,
        claim: str,
        metric: str,
        direction: str = "up",
        threshold: float = 0.0,
        source: str = "manual",
        proposal_id: str = "",
        target_component: str = "",
        eval_set: str = "held_out",
        baseline_value: Optional[float] = None,
        ttl_sec: int = 7 * 24 * 3600,
    ) -> str:
        """登记一条可证伪预测，返回 record_id。"""
        record = PredictionRecord(
            source=source,
            proposal_id=proposal_id,
            target_component=target_component,
            claim=claim,
            metric=metric,
            direction=direction,
            threshold=threshold,
            eval_set=eval_set,
            baseline_value=baseline_value,
            ttl_sec=ttl_sec,
        )
        self._append(record)
        return record.record_id

    def record_verdict(
        self,
        record_id: str,
        actual_value: float,
        evidence_path: str = "",
        verified_by: str = "eval_script",
        note: str = "",
    ) -> tuple[bool, str]:
        """写入验证结果并判定。

        Returns:
            (is_verified, status)
        """
        record = self.get(record_id)
        if record is None:
            return False, "record not found"
        if record.status in (
            PredictionStatus.VERIFIED.value,
            PredictionStatus.FALSIFIED.value,
        ):
            return False, f"already {record.status}"

        record.actual_value = actual_value
        record.verified_at = time.time()
        record.evidence_path = evidence_path
        record.verified_by = verified_by
        satisfied = record.is_satisfied(actual_value)
        record.status = (
            PredictionStatus.VERIFIED.value
            if satisfied
            else PredictionStatus.FALSIFIED.value
        )
        record.verdict_reason = note or (
            f"actual={actual_value} {'>=' if record.direction == 'up' else '<='} "
            f"threshold={record.threshold} -> "
            f"{'verified' if satisfied else 'falsified'}"
        )
        self._append(record)
        return satisfied, record.status

    def mark_skipped(self, record_id: str, reason: str = "") -> bool:
        """跳过验证（如改进中途回滚），必须留原因。"""
        record = self.get(record_id)
        if record is None or record.status != PredictionStatus.PREDICTED.value:
            return False
        record.status = PredictionStatus.SKIPPED.value
        record.verdict_reason = reason or "skipped"
        record.verified_at = time.time()
        self._append(record)
        return True

    def expire_stale(self, now: Optional[float] = None) -> int:
        """将超时未验证的预测标记为 EXPIRED，返回处理条数。"""
        now = now or time.time()
        n = 0
        for record in self._load_all():
            if (
                record.status == PredictionStatus.PREDICTED.value
                and now - record.created_at > record.ttl_sec
            ):
                record.status = PredictionStatus.EXPIRED.value
                record.verdict_reason = "ttl exceeded"
                self._append(record)
                n += 1
        return n

    # -- 读取 -------------------------------------------------------------

    def get(self, record_id: str) -> Optional[PredictionRecord]:
        """按 id 读取（含历史版本，返回最新一条）。"""
        found = None
        for record in self._load_all():
            if record.record_id == record_id:
                found = record
        return found

    def iter_records(self) -> Iterator[PredictionRecord]:
        """按写入顺序迭代全部记录（含历史版本）。"""
        yield from self._load_all()

    def stats(self) -> dict[str, Any]:
        """成绩单指标（基于最新版本去重统计）。"""
        latest: dict[str, PredictionRecord] = {}
        for record in self._load_all():
            latest[record.record_id] = record

        total = len(latest)
        counts = {s.value: 0 for s in PredictionStatus}
        verified, falsified = 0, 0
        deltas: list[float] = []
        for rec in latest.values():
            counts[rec.status] = counts.get(rec.status, 0) + 1
            d = rec.delta()
            if d is not None:
                deltas.append(d)

        resolved = counts[PredictionStatus.VERIFIED.value] + counts[
            PredictionStatus.FALSIFIED.value
        ]
        return {
            "total": total,
            "by_status": counts,
            #: 改进采纳率（= 验证通过率）——成绩单指标之一
            "hit_rate": (
                counts[PredictionStatus.VERIFIED.value] / resolved
                if resolved
                else 0.0
            ),
            #: 验证覆盖率（已决 / 总数）
            "verification_rate": (resolved / total if total else 0.0),
            "avg_delta": (sum(deltas) / len(deltas) if deltas else None),
            "path": self.path,
        }

    # -- 内部 -------------------------------------------------------------

    def _append(self, record: PredictionRecord) -> None:
        entry = {
            "timestamp": time.time(),
            "record_id": record.record_id,
            "event": "register" if record.status == PredictionStatus.PREDICTED.value
            else f"verdict:{record.status}",
            "payload": record.to_dict(),
        }
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        except OSError as e:
            # 账本写入失败必须显式告警，不可静默
            import logging

            logging.getLogger("laap.evolution.prediction_ledger").error(
                f"[PredictionLedger] write failed: {e}"
            )

    def _load_all(self) -> list[PredictionRecord]:
        if not os.path.exists(self.path):
            return []
        records: list[PredictionRecord] = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    records.append(PredictionRecord(**entry["payload"]))
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue  # 跳过损坏行，保持账本可读
        return records


# ─── CLI 入口 ─────────────────────────────────────────────────────────────

def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="PredictionLedger 决策可观测性账本")
    parser.add_argument("--path", default=DEFAULT_LEDGER_PATH, help="账本 JSONL 路径")
    parser.add_argument(
        "--register",
        nargs="*",
        metavar="KEY=VALUE",
        help="登记预测，如 --register claim='...' metric=recall@30d direction=up "
        "threshold=0.8 baseline_value=0.62 eval_set=held_out",
    )
    parser.add_argument("--verdict", nargs="+", metavar="KEY=VALUE",
                        help="写入验证结果，如 --verdict record_id=pred_x "
                        "actual_value=0.84 evidence_path=D:/x.json verified_by=eval_script")
    parser.add_argument("--stats", action="store_true", help="输出成绩单统计")
    parser.add_argument("--expire", action="store_true", help="失效超时预测")
    args = parser.parse_args()

    ledger = PredictionLedger(args.path)

    if args.register:
        kv: dict[str, Any] = {}
        for item in args.register:
            k, _, v = item.partition("=")
            kv[k.strip()] = v.strip()
        # 数值字段转换
        for num_key in ("threshold", "baseline_value", "ttl_sec"):
            if num_key in kv:
                try:
                    kv[num_key] = float(kv[num_key])
                except ValueError:
                    pass
        if "ttl_sec" in kv:
            kv["ttl_sec"] = int(kv["ttl_sec"])
        rid = ledger.register(**kv)
        print(f"registered: {rid}")

    if args.verdict:
        kv = {}
        for item in args.verdict:
            k, _, v = item.partition("=")
            kv[k.strip()] = v.strip()
        ok, status = ledger.record_verdict(
            record_id=kv.get("record_id", ""),
            actual_value=float(kv.get("actual_value", 0.0)),
            evidence_path=kv.get("evidence_path", ""),
            verified_by=kv.get("verified_by", "eval_script"),
            note=kv.get("note", ""),
        )
        print(f"verdict: {status} (verified={ok})")

    if args.expire:
        print(f"expired: {ledger.expire_stale()}")

    if args.stats:
        print(json.dumps(ledger.stats(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _main()
