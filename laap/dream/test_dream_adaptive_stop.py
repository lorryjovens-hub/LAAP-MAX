"""Dream-RSI — 自适应想象预算（RISE 式 Roll/Stop）测试。

覆盖：
1. 无收益时门控提前停止（省轮次）；
2. 持续有收益时不提前停；
3. min_rounds / max_rounds 边界；
4. 与回放集成：启用后轮数减少且最优分不显著下降；
5. 关闭时退化为固定 K2；
6. 元配置可学到开关。
"""

from __future__ import annotations

import random
import sys

sys.path.insert(0, r"D:\LAAP")

from laap.dream import DiscoveryTree, ReplayWorld, ReplayConfig
from laap.dream.adaptive_stop import RollStopGate, RollStopConfig
from laap.dream.exploration_policy import default_parallel_refining_policy
from laap.dream.meta_dream import MetaParams


def _dead_end_tree() -> DiscoveryTree:
    """一条无收益长链：继续回放拿不到更高分。"""
    t = DiscoveryTree()
    prev = t.root_id
    for i in range(20):
        n = t.add_node(prev, score=1.0, sketch=f"flat-{i}")
        prev = n.node_id
    return t


def _gain_tree() -> DiscoveryTree:
    """一条持续升分的链：每一步都有收益。"""
    t = DiscoveryTree()
    prev = t.root_id
    for i in range(20):
        n = t.add_node(prev, score=float(i + 1), sketch=f"gain-{i}")
        prev = n.node_id
    return t


# ── 1/2. 门控基本行为 ───────────────────────────────────────────────────

def test_gate_stops_when_no_gain():
    gate = RollStopGate(RollStopConfig(patience=2, gain_ratio=1.0, min_rounds=1,
                                       max_rounds=30), beta_cost=0.01)
    gate.reset()
    stopped_at = None
    for r in range(30):
        if gate.should_stop():
            stopped_at = r
            break
        gate.observe(best_score=1.0, revealed_nodes=r + 1)  # 分数不涨
    assert stopped_at is not None, "gate never stopped on flat scores"
    assert stopped_at <= 6, f"stopped too late: {stopped_at}"
    print(f"[OK] gate stops early on flat scores (round {stopped_at})")


def test_gate_keeps_going_when_gaining():
    gate = RollStopGate(RollStopConfig(patience=2, gain_ratio=1.0, min_rounds=1,
                                       max_rounds=30), beta_cost=0.01)
    gate.reset()
    stopped_at = None
    for r in range(30):
        if gate.should_stop():
            stopped_at = r
            break
        gate.observe(best_score=float(r + 1) * 10.0, revealed_nodes=r + 1)  # 每轮 +10
    assert stopped_at is None, f"gate stopped despite gains at {stopped_at}"
    print("[OK] gate keeps rolling while gains continue")


def test_gate_bounds():
    # min_rounds 强制不早停
    g = RollStopGate(RollStopConfig(patience=1, min_rounds=5, max_rounds=10),
                     beta_cost=0.01)
    g.reset()
    for r in range(4):
        assert not g.should_stop(), f"stopped before min_rounds at {r}"
        g.observe(1.0, r + 1)
    # max_rounds 强制停
    g2 = RollStopGate(RollStopConfig(patience=1, min_rounds=1, max_rounds=3),
                      beta_cost=0.01)
    g2.reset()
    stopped = None
    for r in range(10):
        if g2.should_stop():
            stopped = r
            break
        g2.observe(float(r) * 100, r + 1)  # 持续大涨
    assert stopped == 3, f"expected stop at max_rounds=3, got {stopped}"
    print("[OK] gate respects min_rounds / max_rounds")


# ── 4/5. 回放集成 ───────────────────────────────────────────────────────

def test_replay_with_gate():
    t = _dead_end_tree()
    world = ReplayWorld(t)
    pol = default_parallel_refining_policy()

    # 固定 K2
    r_fixed = world.replay(pol, ReplayConfig(workers=4, max_rounds=64))
    # 自适应停止
    gate = RollStopGate(RollStopConfig(patience=2, gain_ratio=1.0, min_rounds=1,
                                       max_rounds=64), beta_cost=0.01)
    r_adaptive = world.replay(pol, ReplayConfig(workers=4, max_rounds=64, stop_gate=gate))

    assert r_adaptive.rounds_completed <= r_fixed.rounds_completed, \
        "adaptive stop used more rounds than fixed"
    # 质量不应显著下降（这是死端树，最优分相同）
    assert abs(r_adaptive.best_score - r_fixed.best_score) < 1e-9
    assert "adaptive_stop" in r_adaptive.terminated_reason, r_adaptive.terminated_reason
    print(f"[OK] replay+gate: rounds {r_fixed.rounds_completed} -> "
          f"{r_adaptive.rounds_completed} (best unchanged)")


def test_gate_disabled():
    t = _dead_end_tree()
    world = ReplayWorld(t)
    pol = default_parallel_refining_policy()
    gate = RollStopGate(RollStopConfig(enabled=False), beta_cost=0.01)
    r = world.replay(pol, ReplayConfig(workers=4, max_rounds=10, stop_gate=gate))
    assert r.terminated_reason != "adaptive_stop:max_rounds"
    assert r.rounds_completed == 10, r.rounds_completed
    print(f"[OK] gate disabled -> fixed K2 behavior ({r.rounds_completed} rounds)")


# ── 6. 元配置 ───────────────────────────────────────────────────────────

def test_meta_params_adaptive_stop():
    p = MetaParams(adaptive_stop=True, stop_patience=4, stop_gain_ratio=2.0)
    cfg = p.to_replay_config(workers=4)
    assert cfg.stop_gate is not None
    assert cfg.stop_gate.config.patience == 4
    p2 = MetaParams(adaptive_stop=False)
    assert p2.to_replay_config(4).stop_gate is None
    # 变异保持合法
    rng = random.Random(0)
    m = p.mutate(rng)
    assert m.clamp().to_dict()
    print("[OK] MetaParams adaptive_stop wired into replay config")


if __name__ == "__main__":
    tests = [
        test_gate_stops_when_no_gain,
        test_gate_keeps_going_when_gaining,
        test_gate_bounds,
        test_replay_with_gate,
        test_gate_disabled,
        test_meta_params_adaptive_stop,
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
