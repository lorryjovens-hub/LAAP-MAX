# -*- coding: utf-8 -*-
"""PredictionLedger 端到端冒烟测试（临时路径，不污染生产账本）。"""
import json
import os
import sys
import tempfile
import time

sys.path.insert(0, r"D:\LAAP")
from laap.evolution.prediction_ledger import PredictionLedger  # noqa: E402

path = os.path.join(tempfile.mkdtemp(), "pred.jsonl")
ledger = PredictionLedger(path)

# 1. 登记一条预测（模拟 TrueRSI 提案接入）
rid = ledger.register(
    source="true_rsi",
    proposal_id="true_rsi_demo",
    target_component="laap_module",
    claim="重构记忆压缩后跨会话召回率应提升",
    metric="recall@30d", direction="up", threshold=0.80,
    baseline_value=0.62, eval_set="held_out",
)
print("registered:", rid)

# 2. 写入验证结果（达标）
ok, status = ledger.record_verdict(
    rid, actual_value=0.84,
    evidence_path=r"D:/LAAP/benchmarks/recall_baseline.json",
    verified_by="eval_script",
)
print("verdict1:", status, "verified=", ok)
assert ok is True

# 3. 第二条预测被证伪
rid2 = ledger.register(
    source="rsi_sandbox", proposal_id="rsi_demo2",
    target_component="skill", claim="新 skill 应降低工具误用率",
    metric="tool_misuse_rate", direction="down", threshold=0.05, baseline_value=0.12,
)
ok2, status2 = ledger.record_verdict(rid2, actual_value=0.09, note="实测 9%")
print("verdict2:", status2, "verified=", ok2)
assert ok2 is False

# 4. 第三条挂起 + 跳过
rid3 = ledger.register(source="manual", claim="人工改进示例", metric="x",
                       direction="up", threshold=1.0)
ledger.mark_skipped(rid3, reason="改进中途回滚")

# 5. 过期处理
rid4 = ledger.register(source="manual", claim="过期示例", metric="x",
                       direction="up", threshold=1.0, ttl_sec=1)
time.sleep(1.1)
n = ledger.expire_stale()
print("expired:", n)
assert n == 1

# 6. 成绩单统计
stats = ledger.stats()
print("stats:", json.dumps(stats, ensure_ascii=False))
assert stats["hit_rate"] == 0.5, stats["hit_rate"]  # 1 verified / 2 resolved
assert stats["verification_rate"] == 0.5, stats["verification_rate"]
assert abs(stats["avg_delta"] - 0.095) < 1e-9, stats["avg_delta"]

# 7. 幂等：重复验证同一记录应被拒绝
ok3, status3 = ledger.record_verdict(rid, actual_value=0.9)
print("idempotent:", ok3, status3)
assert ok3 is False

print("ALL ASSERTIONS PASSED")
