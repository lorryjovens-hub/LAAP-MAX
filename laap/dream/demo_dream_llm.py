"""Dream-RSI 演示：从劣质策略出发，做梦发现优质策略。

任务：稀疏高价值搜索——90% 分支平平（grad 0.1-0.6，浅），10% 分支高价值
（grad 6-15，深）。必须广泛探测才能找到高价值分支，再深挖才能兑现。

对照：固定劣质基线 vs 模板变异 vs 真实 LLM 改写。
"""

from __future__ import annotations

import random
import sys

sys.path.insert(0, r"D:\LAAP")
from laap.dream import (
    DreamRSIConfig, DreamRSIEngine, ExplorationPolicy, PolicyParams,
    ReplayConfig, WorldPool, default_parallel_refining_policy,
)


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


def build_pool(seed=7, n_worlds=4):
    cfg = DreamRSIConfig(workers=4, online_max_rounds=40, seed=seed)
    eng = DreamRSIEngine(config=cfg)
    fn = make_sparse_task(seed)
    for _ in range(n_worlds):
        eng.construct_simulator(eng.online_rollout(fn))
    return eng.pool, fn


def avg(policy, pool, rcfg):
    return sum(w.replay(policy, rcfg).score for w in pool.worlds) / max(1, len(pool.worlds))


def main():
    print("=" * 74)
    print("Dream-RSI 演示：从劣质策略出发，做梦发现优质策略")
    print("=" * 74)

    pool, fn = build_pool(seed=7, n_worlds=4)
    rcfg = ReplayConfig(workers=4, max_rounds=12, beta_cost=0.01, beta_parallel=0.05)
    print(f"世界池: {pool.stats()}  (回放 K2={rcfg.max_rounds})")

    # 劣质基线：纯贪分（不开新分支，永远卡在第一条浅分支）
    bad = ExplorationPolicy(
        params=PolicyParams(strategy="score_greedy", parallel_width=1,
                            min_score_to_continue=None),
        name="baseline_greedy")
    bad_score = avg(bad, pool, rcfg)
    print(f"\n[劣质基线] {bad.name}: {bad_score:.4f}")
    print(f"  {bad}")

    # ── B. 模板变异 ──
    print("\n[模板变异] M=10 候选（无 LLM）…")
    eng_mut = DreamRSIEngine(config=DreamRSIConfig(
        workers=4, candidates_per_dream=10, seed=3))
    eng_mut.pool = WorldPool.from_dict(pool.to_dict())
    eng_mut._replay_cfg = rcfg
    deploy_mut, rep_mut = eng_mut.dream_improve(base_policy=bad)
    print(f"  选定 {deploy_mut.name}: {rep_mut.selected_score:.4f} "
          f"(Δ={rep_mut.improvement:+.4f})")
    print(f"  {deploy_mut}")

    # ── C. 真实 LLM ──
    print("\n[真实 LLM] DeepSeek 改写策略…")
    eng_llm = DreamRSIEngine(config=DreamRSIConfig(
        workers=4, candidates_per_dream=10, seed=3,
        use_real_llm=True, llm_model="deepseek-flash"))
    eng_llm.pool = WorldPool.from_dict(pool.to_dict())
    eng_llm._replay_cfg = rcfg
    print(f"  LLM 开发桥: {'已接入' if eng_llm.dev_agent._llm_dev else '未接入'}")
    deploy_llm, rep_llm = eng_llm.dream_improve(base_policy=bad)
    print(f"  选定 {deploy_llm.name} ({deploy_llm.origin}): "
          f"{rep_llm.selected_score:.4f} (Δ={rep_llm.improvement:+.4f})")
    print(f"  {deploy_llm}")
    print(f"  候选分排名:")
    for name, sc in sorted(rep_llm.scores.items(), key=lambda x: -x[1])[:6]:
        print(f"    {name:24s} {sc:.4f}")

    print("=" * 74)
    print(f"劣质基线      : {bad_score:.4f}")
    print(f"模板变异      : {rep_mut.selected_score:.4f} "
          f"(提升 {rep_mut.selected_score / max(1e-9, bad_score):.2f}×)")
    print(f"真实 LLM      : {rep_llm.selected_score:.4f} "
          f"(提升 {rep_llm.selected_score / max(1e-9, bad_score):.2f}×)")
    print(f"单调不退化    : {rep_mut.monotonic_ok and rep_llm.monotonic_ok}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
