"""Dream-RSI 历史编译 + 控制器测试。"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, r"D:\LAAP")

from laap.dream import (
    compile_traces, compile_jsonl, compile_prediction_ledger, ingest_all,
    DiscoveryTree, DreamRSIConfig, DreamRSIController,
)


def test_compile_traces_grouping():
    traces = [
        {"id": "a", "session_id": "s1", "score": 1.0, "sketch": "a"},
        {"id": "b", "session_id": "s1", "parent_id": "a", "score": 2.0, "sketch": "b"},
        {"id": "c", "session_id": "s2", "score": 5.0, "sketch": "c"},
    ]
    trees = compile_traces(traces)
    assert len(trees) == 2
    sizes = sorted(len(t.nodes) for t in trees)
    assert sizes == [2, 3], sizes  # 一个树 2 节点(含根=1+1)，一个 3 节点(=1+2)
    print("[OK] compile_traces grouping + parent linking")


def test_compile_jsonl(tmp: Path):
    p = tmp / "traces.jsonl"
    with p.open("w", encoding="utf-8") as f:
        for rec in [
            {"id": "1", "session_id": "x", "score": 0.5},
            {"id": "2", "session_id": "x", "parent_id": "1", "score": 1.5},
        ]:
            f.write(json.dumps(rec) + "\n")
    trees = compile_jsonl(p)
    assert len(trees) == 1
    assert trees[0].max_score() == 1.5
    print("[OK] compile_jsonl")


def test_compile_prediction_ledger(tmp: Path):
    lp = tmp / "predictions.jsonl"
    recs = [
        {"record_id": "p1", "target_component": "tool_code", "status": "verified",
         "baseline_value": 10.0, "actual_value": 12.0, "direction": "up",
         "metric": "acc", "claim": "improve acc"},
        {"record_id": "p2", "target_component": "tool_code", "status": "falsified",
         "baseline_value": 12.0, "actual_value": 11.0, "direction": "up",
         "metric": "acc", "claim": "another try"},
    ]
    with lp.open("w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    res, trees = compile_prediction_ledger(lp)
    assert res.records == 2
    assert len(trees) == 1  # 同 target_component → 一棵树
    t = trees[0]
    # 第一个改进 VERIFIED 且改善 +2 → 分 2.0；第二个 FALSIFIED → 分 0
    assert t.max_score() == 2.0, t.max_score()
    assert t.size() == 3  # root + 2 尝试
    print("[OK] compile_prediction_ledger (verified/falsified scoring)")


def test_ingest_all(tmp: Path):
    lp = tmp / "pred.jsonl"
    with lp.open("w", encoding="utf-8") as f:
        f.write(json.dumps({"record_id": "z1", "target_component": "skill",
                            "status": "verified", "baseline_value": 1.0,
                            "actual_value": 3.0, "direction": "up"}) + "\n")
    out = ingest_all(ledger_path=str(lp),
                     evolution_path=str(tmp / "nonexistent.jsonl"))
    assert out["report"]["total_trees"] == 1
    assert out["report"]["total_nodes"] == 2
    print("[OK] ingest_all")


def test_controller_cycle(tmp: Path):
    # 造一份轨迹文件
    tp = tmp / "traces.jsonl"
    with tp.open("w", encoding="utf-8") as f:
        for i in range(12):
            f.write(json.dumps({
                "id": f"t{i}", "session_id": "sess",
                "score": float(i) * 0.5, "sketch": f"step{i}",
            }) + "\n")

    state = tmp / "state.json"
    cfg = DreamRSIConfig(workers=3, online_max_rounds=4,
                         candidates_per_dream=5, seed=9,
                         state_path=str(state))
    ctl = DreamRSIController(config=cfg)
    rep = ctl.run_cycle(trace_paths=[str(tp)])
    d = rep.to_dict()
    assert d["ingested_trees"] >= 1
    assert d["pool_after"] >= 1
    assert d["dream"] is not None
    assert d["monotonic_ok"] is True
    assert state.exists()
    print(f"[OK] controller cycle: {d['summary']}")
    # 再次跑（应加载上次状态）
    rep2 = ctl.run_cycle(trace_paths=[str(tp)])
    assert rep2.pool_after >= rep.pool_after
    print("[OK] controller cycle (reloaded state)")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        tests = [
            test_compile_traces_grouping,
            lambda: test_compile_jsonl(tmp),
            lambda: test_compile_prediction_ledger(tmp),
            lambda: test_ingest_all(tmp),
            lambda: test_controller_cycle(tmp),
        ]
        failed = 0
        for fn in tests:
            try:
                fn()
            except AssertionError as e:
                failed += 1
                print(f"[FAIL] {getattr(fn, '__name__', fn)}: {e}")
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"[ERROR] {getattr(fn, '__name__', fn)}: {type(e).__name__}: {e}")
        print(f"\n{'='*50}\n{len(tests) - failed}/{len(tests)} passed")
        sys.exit(1 if failed else 0)
