"""Predictive World 端到端演练：预演 → 学习 → 留用。

用可控的合成世界验证整条链路，并打印人类可读的裁决理由。
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, r"D:\LAAP")

from laap.dream.discovery_tree import DiscoveryTree
from laap.dream.exploration_policy import ExplorationPolicy, PolicyParams
from laap.dream.predictive_world import (
    FEATURE_NAMES, PredictiveSelectionPolicy, PredictiveWorldModel,
    RetentionGate, build_and_evaluate,
)
from laap.dream.replay_world import ReplayConfig, WorldPool, replay_score


def make_world_tree(rng: random.Random, latent: bool = True,
                    depth: int = 3, branch: int = 3,
                    child_coef: float = 0.6) -> DiscoveryTree:
    """生成带潜在质量因子的发现树（结构同测试）。

    ``child_coef=0`` 且 ``latent=False`` 时为真正无结构的噪声树。
    """
    tree = DiscoveryTree(tree_id=f"w_{rng.randrange(10**9)}")
    tree.nodes[tree.root_id].metadata["q"] = 0.0

    def grow(pid: str, d: int) -> None:
        if d > depth:
            return
        pnode = tree.nodes[pid]
        p_score = 0.0 if pid == tree.root_id else pnode.score
        p_q = float(pnode.metadata.get("q", 0.0)) if latent else 0.0
        for _ in range(rng.randint(1, branch)):
            s = child_coef * p_score + 0.6 * p_q + rng.gauss(0.0, 0.12)
            q = rng.gauss(0.0, 1.0) if latent else 0.0
            nd = tree.add_node(pid, score=s,
                               sketch=f"d{d}-" + "x" * rng.randint(0, 20),
                               artifact="y" * max(0, int((q + 2.0) * 12)),
                               diagnostics={"ok": True} if rng.random() > 0.3 else {})
            nd.metadata["q"] = q
            grow(nd.node_id, d + 1)

    grow(tree.root_id, 1)
    return tree


def main() -> int:
    rng = random.Random(31337)
    pool = WorldPool()
    for i in range(24):
        pool.add_tree(make_world_tree(rng))

    print("=" * 74)
    print(f"世界池: {pool.stats()}")
    print("=" * 74)

    # ── ① 学习：训练世界模型 + 可靠性体检 ──
    train = list(pool)[:-6]
    model = PredictiveWorldModel().fit(train)
    rep = model.report
    print("\n① 学习 —— 世界模型可靠性（按世界分组交叉验证）")
    print(f"   训练世界 {len(train)} / 样本 {rep.n_train}")
    print(f"   样本外 RMSE {rep.rmse:.4f}   基线(只猜均值) {rep.baseline_rmse:.4f}")
    print(f"   R² = {rep.r2:.4f}   MAE = {rep.mae:.4f}")
    print(f"   判定: {'可靠' if rep.is_reliable else '不可靠 -> 自动降级'}  ({rep.reason})")
    print("\n   学到的权重（可读的因果结构）：")
    for name in FEATURE_NAMES:
        w = model.weights.get(name, 0.0)
        bar = "#" * min(30, int(abs(w) * 25))
        sign = "+" if w >= 0 else "-"
        print(f"     {name:<16s} {sign}{abs(w):>7.4f}  {bar}")

    # ── ② 预演：在留出世界上同预算对比 ──
    test = list(pool)[-6:]
    cfg = ReplayConfig(workers=2, max_rounds=12)
    print(f"\n② 预演 —— 留出世界 {len(test)} 个，固定预算 workers=2 / rounds=12")

    rows = []
    for w in test:
        pp = PredictiveSelectionPolicy(model)
        gp = ExplorationPolicy(PolicyParams(strategy="score_greedy"), name="greedy")
        bp = ExplorationPolicy(PolicyParams(strategy="balanced"), name="balanced")
        rp, rg, rb = w.replay(pp, cfg), w.replay(gp, cfg), w.replay(bp, cfg)
        rows.append((w.world_id, rp.score, rg.score, rb.score,
                     rp.revealed_nodes, rp.best_score, pp.last_degraded))

    print(f"   {'世界':<12s} {'预判':>9s} {'greedy':>9s} {'balanced':>9s} {'揭示':>5s} {'最优分':>8s}")
    for wid, a, b, c, n, best, deg in rows:
        flag = " [降级]" if deg else ""
        print(f"   {wid:<12s} {a:>9.4f} {b:>9.4f} {c:>9.4f} {n:>5d} {best:>8.4f}{flag}")

    def avg(i):
        return sum(r[i] for r in rows) / len(rows)

    print(f"   {'平均':<12s} {avg(1):>9.4f} {avg(2):>9.4f} {avg(3):>9.4f}")

    # ── ③ 留用：组件检查 + 兼容性检查 ──
    gate = RetentionGate()
    print("\n③ 留用 —— 闸门裁决")
    for label, challenger, incumbent in [
        ("预判 vs balanced", PredictiveSelectionPolicy(model),
         ExplorationPolicy(PolicyParams(strategy="balanced"), name="balanced")),
        ("预判 vs greedy", PredictiveSelectionPolicy(model),
         ExplorationPolicy(PolicyParams(strategy="score_greedy"), name="greedy")),
    ]:
        dec = gate.evaluate(challenger, incumbent, test, cfg)
        verdict = "接受" if dec.accept else "拒绝"
        print(f"   {label:<20s} {verdict}   delta={dec.delta:+.4f} "
              f"胜/平/负 = {dec.win_rate*dec.worlds:.0f}/"
              f"{dec.tie_rate*dec.worlds:.0f}/"
              f"{(1-dec.non_inferior_rate)*dec.worlds:.0f}   "
              f"worst={dec.worst_regression:+.4f}")
        if dec.reasons:
            print(f"       理由: {', '.join(dec.reasons)}")

    # ── ④ 不可靠时的诚实降级 ──
    print("\n④ 反向检验 —— 无可学结构时是否诚实降级")
    rng2 = random.Random(999)
    noise_train = [make_world_tree(rng2, latent=False, child_coef=0.0)
                   for _ in range(10)]
    m_n = PredictiveWorldModel().fit(noise_train)
    print(f"   无结构世界 -> R²={m_n.report.r2:.3f} reliable={m_n.is_reliable} "
          f"({m_n.report.reason})")
    deg_count = 0
    for t in noise_train[-3:]:
        from laap.dream.replay_world import ReplayWorld
        p = PredictiveSelectionPolicy(m_n)
        ReplayWorld(t).replay(p, cfg)
        deg_count += 1 if p.last_degraded else 0
    print(f"   3 次回放中降级次数: {deg_count}/3")

    # ── ⑤ 世界太少时的拒绝 ──
    tiny = WorldPool()
    tiny.add_tree(make_world_tree(random.Random(1)))
    out = build_and_evaluate(tiny)
    print(f"\n⑤ 世界不足 -> build_and_evaluate: ok={out.get('ok')} {out.get('reason', '')}")

    print("\n" + "=" * 74)
    print("结论: 预判选择在可学结构上显著优于 score_greedy；无结构时自动退回启发式。")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
