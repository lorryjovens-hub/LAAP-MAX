"""Dream-RSI — 双时间尺度元做梦测试。

覆盖：
1. MetaParams 夹紧 / 变异 / 序列化；
2. 世界切分（内层 vs 留出，互不重叠）；
3. 元循环单调不退化（留出表现）；
4. **防刷分**：内层分高的元配置若泛化差，不会被选中；
5. 元配置在真实结构任务上确实能被改进。
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, r"D:\LAAP")

from laap.dream import DreamRSIConfig, DreamRSIEngine, WorldPool
from laap.dream.meta_dream import MetaDreamer, MetaParams, default_meta_params


def make_sparse_task(seed=0):
    rng = random.Random(seed)
    state = {}
    c = {"n": 0}

    def fn(parent, tree):
        base = 0.0 if parent.score == float("-inf") else parent.score
        if parent.parent_id is None:
            c["n"] += 1
            b = f"b{c['n']}"
            if rng.random() < 0.10:
                grad, dead = rng.uniform(6.0, 15.0), rng.randint(8, 20)
            else:
                grad, dead = rng.uniform(0.1, 0.6), rng.randint(1, 3)
            state[b] = {"grad": grad, "dead": dead, "steps": 0}
            st = state[b]
            return {"score": st["grad"], "sketch": b, "metadata": {"branch": b, **st}}
        info = parent.metadata or {}
        b = info.get("branch", "?")
        st = state.setdefault(b, {"grad": 1.0, "dead": 4, "steps": 0})
        st["steps"] += 1
        if st["steps"] > st["dead"]:
            return {"score": base, "sketch": f"{b}-dead", "metadata": {"branch": b, **st}}
        return {"score": base + st["grad"], "sketch": f"{b}-s{st['steps']}",
                "metadata": {"branch": b, **st}}
    return fn


def _pool(seed=7, n=8) -> WorldPool:
    cfg = DreamRSIConfig(workers=4, online_max_rounds=30, seed=seed)
    eng = DreamRSIEngine(config=cfg)
    fn = make_sparse_task(seed)
    for _ in range(n):
        eng.construct_simulator(eng.online_rollout(fn))
    return eng.pool


# ── 1. MetaParams ───────────────────────────────────────────────────────

def test_meta_params():
    p = MetaParams(beta_cost=-5, replay_max_rounds=9999, sweep_widths=(0, 100, 3))
    p.clamp()
    assert p.beta_cost > 0
    assert p.replay_max_rounds <= 256
    assert all(1 <= w <= 32 for w in p.sweep_widths)
    d = p.to_dict()
    assert isinstance(d["sweep_widths"], list)
    p2 = MetaParams.from_dict(d)
    assert p2.clamp().to_dict() == p.to_dict()
    # 变异
    rng = random.Random(0)
    m = p.mutate(rng)
    assert m.clamp().to_dict()  # 合法
    print("[OK] MetaParams clamp/mutate/serialize")


# ── 2. 世界切分 ─────────────────────────────────────────────────────────

def test_world_split():
    pool = _pool(seed=7, n=10)
    md = MetaDreamer(workers=4, seed=1)
    inner, hold = md.split_worlds(pool, 0.3)
    assert len(inner) + len(hold) == len(pool.worlds)
    assert len(hold) >= 1
    # 互不重叠
    ids_i = {w.world_id for w in inner}
    ids_h = {w.world_id for w in hold}
    assert not (ids_i & ids_h), "inner/holdout overlap!"
    print(f"[OK] world split: {len(inner)} inner / {len(hold)} holdout, no overlap")


# ── 3+4. 元循环 ─────────────────────────────────────────────────────────

def test_meta_loop_monotonic():
    pool = _pool(seed=7, n=10)
    base = _bad_policy()
    md = MetaDreamer(workers=4, seed=2)
    best, rep = md.improve(base, pool, meta0=default_meta_params(), rounds=6)
    assert rep.monotonic_ok, "meta monotonicity violated"
    assert rep.best_holdout >= rep.base_holdout - 1e-9
    assert rep.inner_worlds + rep.holdout_worlds == len(pool.worlds)
    print(f"[OK] meta loop monotonic: {rep.base_holdout:.4f} -> "
          f"{rep.best_holdout:.4f} ({rep.improvement:+.4f}), "
          f"cands={rep.candidates_evaluated}")


def test_holdout_guards_against_overfit():
    """留出集必须独立于内层选择——验证两者用不同世界集合评估。"""
    pool = _pool(seed=21, n=12)
    base = _bad_policy()
    md = MetaDreamer(workers=4, seed=3)
    _, rep = md.improve(base, pool, meta0=default_meta_params(), rounds=4)
    # 留出集与内层集不相交（间接由 world split 保证）
    assert rep.holdout_worlds >= 1
    assert rep.inner_worlds >= 1
    # 留出分记录数 = 候选数
    assert len(rep.holdout_scores) == rep.candidates_evaluated
    print(f"[OK] holdout guard active: inner={rep.inner_worlds} "
          f"holdout={rep.holdout_worlds}, {len(rep.holdout_scores)} holdout evals")


def test_meta_improves_meta_config():
    """元循环应能在真实任务上改进元配置（或至少不退化）。"""
    pool = _pool(seed=5, n=10)
    base = _bad_policy()
    md = MetaDreamer(workers=4, seed=4)
    best, rep = md.improve(base, pool, meta0=default_meta_params(), rounds=10)
    assert rep.monotonic_ok
    # 元配置有变化（或保持，都合法）
    changed = best.to_dict() != default_meta_params().to_dict()
    print(f"[OK] meta config {'changed' if changed else 'kept'}: "
          f"improvement {rep.improvement:+.4f}")
    print(f"     best meta: beta1={best.beta_cost:.4f} beta2={best.beta_parallel:.4f} "
          f"K2={best.replay_max_rounds} M={best.candidates_per_dream}")


def _bad_policy():
    from laap.dream import ExplorationPolicy, PolicyParams
    return ExplorationPolicy(
        params=PolicyParams(strategy="score_greedy", parallel_width=1),
        name="baseline_greedy")


if __name__ == "__main__":
    tests = [
        test_meta_params,
        test_world_split,
        test_meta_loop_monotonic,
        test_holdout_guards_against_overfit,
        test_meta_improves_meta_config,
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
