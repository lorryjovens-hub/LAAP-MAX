"""Dream-RSI 单元测试。

覆盖：
1. DiscoveryTree 结构（父子关系、可探索集、最早未观测子节点语义）；
2. ReplayWorld 回放语义与回放打分公式；
3. ExplorationPolicy 批次选择与变异；
4. DreamRSIEngine 完整三段闭环；
5. 单调不退化保证（V_selected ≥ V_base）；
6. 反直觉性质：回放不泄露未揭示信息（某分支只有一条延续时无法凭空扩展）。
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, r"D:\LAAP")

from laap.dream import (
    DiscoveryTree, ObservedView, ReplayConfig, ReplayWorld, WorldPool,
    replay_score, ExplorationPolicy, PolicyParams,
    default_parallel_refining_policy,
    DreamRSIConfig, DreamRSIEngine,
)


# ── 1. 发现树 ───────────────────────────────────────────────────────────

def test_discovery_tree_basic():
    t = DiscoveryTree()
    assert t.size() == 1
    assert t.eligible() == [t.root_id]

    a = t.add_node(t.root_id, score=1.0, sketch="A")
    b = t.add_node(t.root_id, score=2.0, sketch="B")
    a1 = t.add_node(a.node_id, score=5.0, sketch="A1")

    assert t.size() == 4
    assert t.max_score() == 5.0
    assert set(t.leaves()) == {b.node_id, a1.node_id}
    assert set(t.eligible()) == {t.root_id, b.node_id, a1.node_id}
    assert a1.depth == 2
    assert t.best_node().node_id == a1.node_id
    print("[OK] discovery_tree basic")


def test_tree_earliest_unobserved_child():
    t = DiscoveryTree()
    c1 = t.add_node(t.root_id, 1.0)
    c2 = t.add_node(t.root_id, 2.0)
    observed = {t.root_id}
    # 根节点：最早创建的未观测子节点
    assert t.earliest_unobserved_child(t.root_id, observed) == c1.node_id
    observed.add(c1.node_id)
    assert t.earliest_unobserved_child(t.root_id, observed) == c2.node_id
    observed.add(c2.node_id)
    assert t.earliest_unobserved_child(t.root_id, observed) is None
    # 非根：唯一子节点
    gc = t.add_node(c1.node_id, 3.0)
    assert t.earliest_unobserved_child(c1.node_id, {t.root_id}) == gc.node_id
    print("[OK] tree earliest_unobserved_child")


def test_tree_serialization():
    t = DiscoveryTree()
    t.add_node(t.root_id, 1.0, sketch="x", diagnostics={"k": "v"})
    d = t.to_dict()
    t2 = DiscoveryTree.from_dict(d)
    assert t2.size() == t.size()
    assert t2.max_score() == t.max_score()
    print("[OK] tree serialization")


# ── 2. 回放与打分 ───────────────────────────────────────────────────────

def test_replay_score_formula():
    # V = quality - b1*N + b2*N/max(1,k)
    v = replay_score(best_score=10.0, revealed_nodes=20, rounds=4,
                     beta_cost=0.1, beta_parallel=0.5)
    expected = 10.0 - 0.1 * 20 + 0.5 * (20 / 4)
    assert abs(v - expected) < 1e-9, f"{v} != {expected}"
    # rounds=0 时 max(1,k)=1
    v0 = replay_score(10.0, 10, 0, 0.1, 0.5)
    assert abs(v0 - (10.0 - 1.0 + 0.5 * 10)) < 1e-9
    # -inf 质量按 0 处理
    vinf = replay_score(float("-inf"), 0, 0, 0.1, 0.5)
    assert vinf == 0.0
    print("[OK] replay_score formula")


def _build_reference_tree() -> DiscoveryTree:
    """构造一棵参照树：根 → 3 条分支，其中一条较深。"""
    t = DiscoveryTree()
    b1 = t.add_node(t.root_id, score=1.0, sketch="branch1")
    b2 = t.add_node(t.root_id, score=2.0, sketch="branch2")
    b3 = t.add_node(t.root_id, score=3.0, sketch="branch3")
    # branch2 继续精化到高分
    c = t.add_node(b2.node_id, score=6.0, sketch="b2-refine-1")
    d = t.add_node(c.node_id, score=9.0, sketch="b2-refine-2")
    # branch3 精化一次
    t.add_node(b3.node_id, score=4.0, sketch="b3-refine-1")
    return t


def test_replay_deterministic_and_bounded():
    t = _build_reference_tree()
    world = ReplayWorld(t)
    pol = default_parallel_refining_policy()

    # 回放不得凭空造节点
    r = world.replay(pol, ReplayConfig(workers=4, max_rounds=64))
    assert r.revealed_nodes <= t.non_root_count(), \
        f"replay revealed {r.revealed_nodes} > recorded {t.non_root_count()}"
    assert r.best_score <= t.max_score() + 1e-9
    # 同一策略同一世界，重复回放结果一致（确定性）
    r2 = world.replay(pol, ReplayConfig(workers=4, max_rounds=64))
    assert abs(r.score - r2.score) < 1e-9
    assert r.revealed_nodes == r2.revealed_nodes
    print(f"[OK] replay deterministic/bounded (revealed={r.revealed_nodes}, "
          f"best={r.best_score}, V={r.score:.4f})")


def test_replay_cannot_invent():
    """反直觉性质：单链历史无法被任何策略"分叉"。"""
    t = DiscoveryTree()
    a = t.add_node(t.root_id, 1.0)
    b = t.add_node(a.node_id, 2.0)
    c = t.add_node(b.node_id, 3.0)
    world = ReplayWorld(t)
    pol = default_parallel_refining_policy()
    r = world.replay(pol, ReplayConfig(workers=8, max_rounds=64))
    # 无论并行度多高，都只能沿单链揭示 3 个节点
    assert r.revealed_nodes == 3, f"expected 3, got {r.revealed_nodes}"
    print("[OK] replay cannot invent unseen branches")


def test_replay_finds_best_branch():
    """均衡策略应能深入高分支，触达最高分节点。"""
    t = _build_reference_tree()
    world = ReplayWorld(t)
    pol = default_parallel_refining_policy()  # explore_ratio > 0
    r = world.replay(pol, ReplayConfig(workers=4, max_rounds=64))
    assert r.best_score >= 6.0, f"expected to reach deep branch, best={r.best_score}"
    print(f"[OK] replay reaches deep branch (best={r.best_score})")


def test_pure_exploit_stalls():
    """纯 exploit 策略遇到死端分支会搁浅（不崩溃，由 K2 限幅）。

    这正是回放打分要惩罚的劣质探索行为，也说明"历史当模拟器"能真实
    区分好坏策略。
    """
    t = _build_reference_tree()
    world = ReplayWorld(t)
    pol = ExplorationPolicy(
        params=PolicyParams(parallel_width=1, explore_ratio=0.0,
                            score_weight=1.0, depth_penalty=0.0, novelty_bonus=0.0),
        name="pure_exploit",
    )
    r = world.replay(pol, ReplayConfig(workers=2, max_rounds=12))
    # 卡在第一条（分数最低）分支，无法抵达深分支
    assert r.best_score <= 2.0, f"unexpectedly reached {r.best_score}"
    # 不索死：轮数被 K2 限幅
    assert r.rounds_completed <= 12
    print(f"[OK] pure exploit stalls (best={r.best_score}, rounds={r.rounds_completed})")


# ── 3. 策略 ─────────────────────────────────────────────────────────────

def test_policy_select_batch():
    t = _build_reference_tree()
    view = ObservedView(t, set(t.nodes.keys()))
    pol = default_parallel_refining_policy()
    pol.reset()
    batch = pol.select_batch(view, workers=4)
    assert 1 <= len(batch) <= 4
    assert all(nid in view.eligible() for nid in batch)
    print(f"[OK] policy select_batch -> {len(batch)} nodes")


def test_policy_mutation():
    rng = random.Random(42)
    base = default_parallel_refining_policy()
    child = base.mutate(rng)
    assert child.generation == base.generation + 1
    assert child.parent_name == base.name
    assert child.name != base.name
    # 参数仍在合法区间
    p = child.params
    assert 1 <= p.parallel_width <= 64
    assert 0.0 <= p.explore_ratio <= 1.0
    print("[OK] policy mutation")


# ── 4. 完整闭环 ─────────────────────────────────────────────────────────

def _make_synthetic_explore_fn(seed: int = 7):
    """合成的"发现智能体"：分数随深度增长但有噪声，偶有失败分支。"""
    rng = random.Random(seed)

    def explore_fn(parent, tree):
        base = 0.0 if parent.score == float("-inf") else parent.score
        gain = rng.uniform(0.5, 2.5)
        # 深分支趋向更高分；10% 概率出现失败支
        if rng.random() < 0.1:
            return {"score": base * 0.5, "sketch": "failed branch",
                    "diagnostics": {"failed": True}}
        return {
            "score": base + gain,
            "sketch": f"refine depth {parent.depth + 1}",
            "snapshot": {"depth": parent.depth + 1},
            "diagnostics": {"pass": True},
        }

    return explore_fn


def test_full_loop_and_monotonic():
    cfg = DreamRSIConfig(workers=4, online_max_rounds=8,
                         candidates_per_dream=6, seed=11,
                         state_path=str(Path("./_dream_test_state.json").resolve()))
    engine = DreamRSIEngine(config=cfg)
    explore_fn = _make_synthetic_explore_fn(seed=11)

    results = engine.run(explore_fn, iterations=3)
    assert len(results) == 3
    for r in results:
        assert r.report is not None
        # 单调不退化保证
        assert r.report.monotonic_ok, f"iteration {r.iteration}: monotonic violated"
        assert r.report.selected_score >= r.report.base_score - 1e-9
    # 世界池随迭代增长
    assert results[-1].pool_size >= results[0].pool_size
    print(f"[OK] full loop: {len(results)} iterations, "
          f"pool={results[-1].pool_size}, "
          f"improvements={[round(r.report.improvement, 4) for r in results]}")


def test_state_persistence():
    tmp = Path("./_dream_test_state.json").resolve()
    if tmp.exists():
        tmp.unlink()
    cfg = DreamRSIConfig(workers=2, online_max_rounds=4,
                         candidates_per_dream=3, seed=3,
                         state_path=str(tmp))
    engine = DreamRSIEngine(config=cfg)
    engine.run(_make_synthetic_explore_fn(seed=3), iterations=1)
    saved = engine.save_state()
    assert Path(saved).exists()

    engine2 = DreamRSIEngine(config=cfg)
    ok = engine2.load_state()
    assert ok
    assert engine2.iteration == engine.iteration
    assert len(engine2.pool) == len(engine.pool)
    assert engine2.policy.name == engine.policy.name
    tmp.unlink(missing_ok=True)
    print("[OK] state persistence")


if __name__ == "__main__":
    tests = [
        test_discovery_tree_basic,
        test_tree_earliest_unobserved_child,
        test_tree_serialization,
        test_replay_score_formula,
        test_replay_deterministic_and_bounded,
        test_replay_cannot_invent,
        test_replay_finds_best_branch,
        test_pure_exploit_stalls,
        test_policy_select_batch,
        test_policy_mutation,
        test_full_loop_and_monotonic,
        test_state_persistence,
    ]
    failed = 0
    for fn in tests:
        try:
            fn()
        except AssertionError as e:
            failed += 1
            print(f"[FAIL] {fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"[ERROR] {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{'='*50}\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
