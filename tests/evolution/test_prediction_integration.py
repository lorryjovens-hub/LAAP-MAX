"""TrueRSIEngine × PredictionLedger 接入集成测试。

验证四段式流程接入点：
1. 不带账本时行为完全不变（向后兼容）
2. 带账本时 PATCH 成功后自动登记可证伪预测
3. verify_prediction 由外部评估器写入判定
4. 自定义 prediction_fn 可覆盖默认零回归预测
5. 完整闭环（auto_approve）端到端登记
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from laap.evolution.prediction_ledger import PredictionLedger, PredictionStatus
from laap.evolution.true_rsi import TrueRSIConfig, TrueRSIEngine

from tests.evolution.test_true_rsi import temp_repo  # reuse fixture


def _engine_with_ledger(tmp_path: Path, repo_root: str, **cfg_kwargs):
    ledger_path = tmp_path / "predictions.jsonl"
    ledger = PredictionLedger(str(ledger_path))
    cfg = TrueRSIConfig(
        repo_root=repo_root,
        target_directory="laap/tools/",
        ledger=ledger,
        **cfg_kwargs,
    )
    engine = TrueRSIEngine(cfg)
    return engine, ledger, ledger_path


# ─── 1. 向后兼容：不带账本 ───────────────────────────────────────────────

def test_engine_without_ledger_preserves_behavior(temp_repo):
    """未配置账本时 register_prediction 返回空串，主流程不受影响。"""
    engine = TrueRSIEngine(TrueRSIConfig(
        repo_root=str(temp_repo),
        target_directory="laap/tools/",
    ))
    proposal = engine.propose()
    assert proposal is not None
    assert engine.patch(proposal)
    # 账本未启用 → 不登记、不抛错
    assert engine.register_prediction(proposal) == ""
    assert proposal.prediction_record_id == ""
    ok, reason = engine.verify_prediction(proposal, actual_value=0.0)
    assert ok is False and "no prediction" in reason


# ─── 2. 带账本：PATCH 后自动登记 ─────────────────────────────────────────

def test_engine_registers_prediction_on_patch(temp_repo, tmp_path):
    """PATCH 成功后应自动登记默认零回归预测。"""
    engine, ledger, ledger_path = _engine_with_ledger(
        tmp_path, str(temp_repo))
    proposal = engine.propose()
    assert proposal is not None
    assert engine.patch(proposal)

    assert proposal.prediction_record_id, "PATCH 后应登记预测"
    record = ledger.get(proposal.prediction_record_id)
    assert record is not None
    assert record.source == "true_rsi"
    assert record.proposal_id == proposal.proposal_id
    assert record.metric == "held_out_regression_count"
    assert record.direction == "down" and record.threshold == 0.0
    assert record.eval_set == "held_out"
    assert record.status == PredictionStatus.PREDICTED.value
    assert "零回归" in record.claim
    # 账本文件已落盘
    assert ledger_path.exists()
    assert ledger_path.stat().st_size > 0


# ─── 3. 外部评估器写入判定 ───────────────────────────────────────────────

def test_engine_verify_prediction_verdicts(temp_repo, tmp_path):
    """verify_prediction 应支持达标与证伪两种判定。"""
    engine, ledger, _ = _engine_with_ledger(tmp_path, str(temp_repo))
    proposal = engine.propose()
    assert proposal is not None
    assert engine.patch(proposal)

    # 达标：零回归
    ok, status = engine.verify_prediction(
        proposal, actual_value=0.0,
        evidence_path="D:/LAAP/benchmarks/regression_run_001.json",
        verified_by="eval_script", note="held-out 回归 0 失败",
    )
    assert ok is True and status == PredictionStatus.VERIFIED.value

    # 幂等：重复判定被拒绝
    ok2, status2 = engine.verify_prediction(proposal, actual_value=0.0)
    assert ok2 is False and "already" in status2


def test_engine_verify_prediction_falsified(temp_repo, tmp_path):
    """回归数 > 0 时应判定为 FALSIFIED。"""
    engine, ledger, _ = _engine_with_ledger(tmp_path, str(temp_repo))
    proposal = engine.propose()
    assert proposal is not None
    assert engine.patch(proposal)

    ok, status = engine.verify_prediction(
        proposal, actual_value=3.0,
        evidence_path="D:/LAAP/benchmarks/regression_run_002.json",
        verified_by="eval_script", note="held-out 回归 3 失败",
    )
    assert ok is False and status == PredictionStatus.FALSIFIED.value


# ─── 4. 自定义预测函数 ───────────────────────────────────────────────────

def test_engine_custom_prediction_fn(temp_repo, tmp_path):
    """自定义 prediction_fn 应覆盖默认零回归预测。"""
    def my_predictor(proposal):
        return {
            "claim": "patch 应降低延迟",
            "metric": "latency_ms",
            "direction": "down",
            "threshold": 100.0,
            "eval_set": "live",
            "baseline_value": 250.0,
        }

    engine, ledger, _ = _engine_with_ledger(
        tmp_path, str(temp_repo), prediction_fn=my_predictor)
    proposal = engine.propose()
    assert proposal is not None
    assert engine.patch(proposal)

    record = ledger.get(proposal.prediction_record_id)
    assert record is not None
    assert record.metric == "latency_ms"
    assert record.eval_set == "live" and record.baseline_value == 250.0


# ─── 5. 完整闭环端到端 ───────────────────────────────────────────────────

def test_run_cycle_registers_predictions_end_to_end(temp_repo, tmp_path):
    """run_cycle(auto_approve=True) 跑完后，账本应有记录且统计可用。"""
    engine, ledger, _ = _engine_with_ledger(tmp_path, str(temp_repo))
    results = engine.run_cycle(max_proposals=2, auto_approve=True)
    assert len(results) >= 1

    registered = [
        p for p in results
        if p.prediction_record_id and ledger.get(p.prediction_record_id) is not None
    ]
    # 至少 PATCH 成功的提案登记了预测（sandbox 降级失败的不算）
    assert any(r.prediction_record_id for r in results if r.mutation is not None)

    stats = ledger.stats()
    assert stats["total"] == len(registered)
    assert "hit_rate" in stats and "verification_rate" in stats
