"""Dream-RSI 对照实验：隔离"做梦"阶段，验证策略在同一世界池上的单调爬升。

实验设计（对应论文 §3 的 offline phase）：
  Phase A  单次在线探索 → 冻结世界池；
  Phase B  在固定世界池上连续做梦 N 轮，观察回放分是否单调不退化并逐步收敛；
  Phase C  重新实现在线探索 → 世界池扩大。

对照组：Recursive Fixed Exploration（策略固定，从不做梦）——对应论文的主基线。
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, r"D:\LAAP")

from laap.dream import (
    DreamRSIConfig, DreamRSIEngine, ReplayConfig,
    default_parallel_refining_policy,
)


def make_task(seed: int = 0):
    """有结构的发现任务：分支有隐藏质量梯度与死胡同深度。"""
    rng = random.Random(seed)
    state: dict[str, dict] = {}
    counter = {"n": 0}

    def explore_fn(parent, tree):
        base = 0.0 if parent.score == float("-inf") else parent.score
        if parent.parent_id is None:
            counter["n"] += 1
            bname = f"b{counter['n']}"
            state[bname] = {"grad": rng.uniform(0.5, 4.0),
                            "dead": rng.choice([2, 3, 5, 8]), "steps": 0}
            st = state[bname]
            return {"score": st["grad"], "sketch": bname,
                    "metadata": {"branch": bname, **st}}
        info = parent.metadata or {}
        bname = info.get("branch", "?")
        st = state.setdefault(bname, {"grad": 1.0, "dead": 4, "steps": 0})
        st["steps"] += 1
        if st["steps"] > st["dead"]:
            return {"score": base, "sketch": f"{bname}-dead", "metadata": {"branch": bname, **st}}
        return {"score": base + st["grad"], "sketch": f"{bname}-s{st['steps']}",
                "metadata": {"branch": bname, **st}}

    return explore_fn


def phase_b_frozen_dreaming(engine: DreamRSIEngine, rounds: int):
    """在冻结的世界池上连续做梦，返回分数轨迹。"""
    trace = []
    for _ in range(rounds):
        deployed, rep = engine.dream_improve(base_policy=engine.policy)
        engine.policy = deployed
        # 记录"当前策略在冻结池上的平均回放分"
        scores = [w.replay(engine.policy, engine._replay_cfg).score
                  for w in engine.pool.worlds]
        avg = sum(scores) / max(1, len(scores))
        trace.append((rep.base_score, rep.selected_score, avg, rep.improvement))
    return trace


def main():
    print("=" * 72)
    print("Dream-RSI 对照实验：冻结世界池上的策略单调爬升")
    print("=" * 72)

    # ── Phase A：单次在线探索构建世界池 ──
    cfg = DreamRSIConfig(workers=4, online_max_rounds=12,
                         candidates_per_dream=10, beta_cost=0.02, beta_parallel=0.05,
                         seed=21, state_path=str(Path("./_dream_ab_state.json").resolve()))
    engine = DreamRSIEngine(config=cfg)
    explore_fn = make_task(seed=21)

    print("\n[Phase A] 在线探索 × 5 轮，构建世界池…")
    for _ in range(5):
        tree = engine.online_rollout(explore_fn)
        engine.construct_simulator(tree)
    print(f"  世界池: {engine.pool.stats()}")

    # ── Phase B：冻结池上做梦 ──
    print("\n[Phase B] 在冻结世界池上连续做梦 12 轮…")
    print(f"  {'轮':>3} {'基线分':>9} {'选定分':>9} {'当前均分':>9} {'改进':>8} {'单调':>5}")
    print("  " + "-" * 50)
    trace = phase_b_frozen_dreaming(engine, 12)
    for i, (b, s, avg, imp) in enumerate(trace, 1):
        mono = "OK" if s >= b - 1e-9 else "VIOLATED"
        print(f"  {i:>3} {b:>9.3f} {s:>9.3f} {avg:>9.3f} {imp:>+8.3f} {mono:>5}")

    baseline_first = trace[0][0]
    final = trace[-1][2]
    print(f"\n  冻结池上：起始平均回放分 {baseline_first:.4f} → 最终 {final:.4f} "
          f"（净提升 {final - baseline_first:+.4f}）")
    print(f"  全程单调不退化: {all(s >= b - 1e-9 for b, s, _, _ in trace)}")

    # ── Phase C：重新在线探索，池扩张 ──
    print("\n[Phase C] 重新在线探索 × 3 轮…")
    for _ in range(3):
        tree = engine.online_rollout(explore_fn)
        engine.construct_simulator(tree)
    print(f"  世界池: {engine.pool.stats()}")

    print("\n" + "=" * 72)
    print(f"最终部署策略: {engine.policy}")
    print(f"最终策略源码审计:\n{engine.policy.to_source()}")
    engine.save_state()
    print(f"状态已保存: {cfg.state_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
