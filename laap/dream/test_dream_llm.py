"""Dream-RSI — LLM 策略开发桥 + 策略结构 + 真实数据源编译 测试。

覆盖：
1. summarize_replays 反馈提炼；
2. LLMPolicyDeveloper 解析 LLM 提议（含 markdown 栅栏容错 / 非法 JSON 降级）；
3. 六种策略结构都能产生合法批次；
4. 带 LLM 开发桥的完整闭环（用 mock LLM）；
5. compile_evolution_log 编译真实格式的经验日志；
6. 从真实 evolution.jsonl（若存在）编译。
"""

from __future__ import annotations

import json
import random
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, r"D:\LAAP")

from laap.dream import (
    ExplorationPolicy, PolicyParams, PolicyDevelopmentAgent, LLMPolicyDeveloper,
    STRATEGIES, summarize_replays, DiscoveryTree, ReplayWorld, ReplayConfig,
    default_parallel_refining_policy, DreamRSIConfig, DreamRSIEngine,
    compile_evolution_log,
)


# ── 1. 反馈提炼 ─────────────────────────────────────────────────────────

def _build_tree():
    t = DiscoveryTree()
    b1 = t.add_node(t.root_id, 1.0)
    b2 = t.add_node(t.root_id, 2.0)
    t.add_node(b2.node_id, 6.0)
    return t


def test_summarize_replays():
    t = _build_tree()
    world = ReplayWorld(t)
    pol = default_parallel_refining_policy()
    r = world.replay(pol, ReplayConfig(workers=2, max_rounds=8))
    fb = summarize_replays([r])
    for k in ("worlds", "avg_quality", "avg_cost", "avg_parallel",
              "avg_wasted_rounds", "avg_score", "cost_ratio"):
        assert k in fb, f"missing {k}"
    assert fb["worlds"] == 1
    print(f"[OK] summarize_replays -> {json.dumps(fb, ensure_ascii=False)}")


# ── 2. LLM 策略开发 ─────────────────────────────────────────────────────

def test_llm_policy_developer_parses():
    def mock_llm(prompt: str) -> str:
        # 模拟 LLM 返回带 markdown 栅栏的 JSON
        return "```json\n" + json.dumps([
            {"strategy": "breadth_first", "params": {"explore_ratio": 0.5},
             "reason": "stuck; explore more"},
            {"strategy": "depth_first", "params": {"depth_bonus": 0.3},
             "reason": "deep branches pay off"},
        ]) + "\n```"

    dev = LLMPolicyDeveloper(mock_llm)
    base = default_parallel_refining_policy()
    props = dev.propose(base, {"avg_quality": 5.0, "avg_cost": 1.0})
    assert len(props) == 2
    assert props[0].params.strategy == "breadth_first"
    assert abs(props[0].params.explore_ratio - 0.5) < 1e-9
    assert props[1].params.strategy == "depth_first"
    assert props[0].origin == "llm"
    print("[OK] LLMPolicyDeveloper parses fenced JSON")


def test_llm_policy_developer_graceful_failure():
    def bad_llm(prompt: str) -> str:
        return "I cannot help with that."  # 无 JSON

    dev = LLMPolicyDeveloper(bad_llm)
    props = dev.propose(default_parallel_refining_policy(), {})
    assert props == [], props
    print("[OK] LLMPolicyDeveloper graceful failure (no JSON)")


def test_llm_policy_developer_clamps():
    def evil_llm(prompt: str) -> str:
        return json.dumps([{
            "strategy": "not_a_real_strategy",
            "params": {"parallel_width": 9999, "explore_ratio": -5},
        }])

    dev = LLMPolicyDeveloper(evil_llm)
    props = dev.propose(default_parallel_refining_policy(), {})
    assert len(props) == 1
    # 非法策略名回退到 balanced，参数被夹到合法区间
    assert props[0].params.strategy == "balanced"
    assert props[0].params.parallel_width <= 64
    assert props[0].params.explore_ratio >= 0.0
    print("[OK] LLMPolicyDeveloper clamps out-of-range proposals")


# ── 3. 策略结构 ─────────────────────────────────────────────────────────

def test_all_strategies_produce_batches():
    t = _build_tree()
    from laap.dream import ObservedView
    view = ObservedView(t, set(t.nodes.keys()))
    for s in STRATEGIES:
        pol = ExplorationPolicy(params=PolicyParams(strategy=s), name=f"p_{s}")
        pol.reset()
        batch = pol.select_batch(view, workers=3)
        assert isinstance(batch, list)
        assert len(batch) <= 3
        assert all(nid in view.eligible() for nid in batch), (s, batch)
    print(f"[OK] all {len(STRATEGIES)} strategies produce valid batches")


# ── 4. 带 LLM 的完整闭环 ────────────────────────────────────────────────

def test_engine_with_llm_dev():
    calls = {"n": 0}

    def mock_llm(prompt: str) -> str:
        calls["n"] += 1
        # 轮流提议不同结构
        s = STRATEGIES[calls["n"] % len(STRATEGIES)]
        return json.dumps([{"strategy": s, "params": {"explore_ratio": 0.35},
                            "reason": "explore"}])

    # 造一点世界
    rng = random.Random(1)
    def explore_fn(parent, tree):
        base = 0.0 if parent.score == float("-inf") else parent.score
        return {"score": base + rng.uniform(0.5, 2.0), "sketch": "x"}

    cfg = DreamRSIConfig(workers=3, online_max_rounds=5, candidates_per_dream=6,
                         seed=4, use_llm_policy_dev=True,
                         state_path=str(Path(tempfile.gettempdir()) / "drs_test.json"))
    engine = DreamRSIEngine(config=cfg, llm_fn=mock_llm)
    res = engine.step(explore_fn)
    assert res.report is not None
    assert res.report.monotonic_ok
    assert calls["n"] > 0, "LLM dev was not called"
    print(f"[OK] engine with LLM dev (llm calls={calls['n']}, "
          f"candidates={res.report.candidates_evaluated}, "
          f"Δ={res.report.improvement:+.4f})")


# ── 5. evolution.jsonl 编译 ─────────────────────────────────────────────

def test_compile_evolution_log(tmp: Path):
    p = tmp / "evolution.jsonl"
    recs = [
        {"task": "接入 vision_core", "capabilities": ["视觉评分"],
         "methods": ["第一性原理"], "tools": ["vision_core.py"],
         "lessons": ["现成工具没用好就自己重写"], "project": "harness/game",
         "confidence": 1.0, "timestamp": 100.0},
        {"task": "改进渲染", "tools": ["render.py"],
         "lessons": ["光照要充足"], "project": "harness/game",
         "confidence": 0.8, "timestamp": 200.0},
        {"task": "另一个项目", "project": "other", "confidence": 0.5,
         "timestamp": 150.0},
    ]
    with p.open("w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    res, trees = compile_evolution_log(p)
    assert res.records == 3
    assert len(trees) == 2  # 两个 project
    game_tree = [t for t in trees if t.root.metadata.get("project") == "harness/game"][0]
    assert game_tree.size() == 3  # root + 2 记录
    assert game_tree.max_score() == 1.0
    print("[OK] compile_evolution_log")


def test_compile_real_evolution_if_present():
    from pathlib import Path as P
    real = P.home() / ".laap" / "evolution.jsonl"
    if not real.exists():
        print("[SKIP] real evolution.jsonl not present")
        return
    res, trees = compile_evolution_log(real)
    assert res.records > 0
    assert len(trees) >= 1
    print(f"[OK] real evolution.jsonl: {res.records} records -> "
          f"{len(trees)} trees, {sum(t.size() for t in trees)} nodes")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as td:
        tmp = P = Path(td)
        tests = [
            test_summarize_replays,
            test_llm_policy_developer_parses,
            test_llm_policy_developer_graceful_failure,
            test_llm_policy_developer_clamps,
            test_all_strategies_produce_batches,
            test_engine_with_llm_dev,
            lambda: test_compile_evolution_log(tmp),
            test_compile_real_evolution_if_present,
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
