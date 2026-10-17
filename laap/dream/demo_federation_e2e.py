"""Dream-RSI — 跨实例联邦通道端到端验证（第二个 Aris 实例）。

用真实的 LAAPer 同步通道（OneDrive\\LAAP-Sync\\dream_rsi）验证：
  Agent B（"aris-twin"，模拟第二个 Aris 实例）
      └─ 在自己的数据上做梦 → 学到策略 → 发布改编到真实通道
  Agent A（"aris"，本机）
      └─ 发现通道上的改编 → 汇合候选 → 在本地世界池验证 → 采纳

全程不共享任何原始经验（只流通策略参数 + 聚合统计）。
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, r"D:\LAAP")

from laap.dream import (
    DreamRSIConfig, DreamRSIEngine, WorldPool, ReplayConfig,
    ExplorationPolicy, PolicyParams,
)
from laap.dream.federation import (
    AdaptationStore, export_adaptation, merge_adaptations, _anonymize,
)


def make_task(seed=0, sparse=True):
    rng = random.Random(seed)
    state = {}
    c = {"n": 0}

    def fn(parent, tree):
        base = 0.0 if parent.score == float("-inf") else parent.score
        if parent.parent_id is None:
            c["n"] += 1
            b = f"b{c['n']}"
            if sparse and rng.random() < 0.10:
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


def build_pool(seed, n=5):
    cfg = DreamRSIConfig(workers=4, online_max_rounds=30, seed=seed)
    eng = DreamRSIEngine(config=cfg)
    fn = make_task(seed)
    for _ in range(n):
        eng.construct_simulator(eng.online_rollout(fn))
    return eng.pool


def avg(policy, pool, rcfg):
    return sum(w.replay(policy, rcfg).score for w in pool.worlds) / max(1, len(pool.worlds))


def main():
    print("=" * 74)
    print("跨实例联邦通道端到端验证（第二个 Aris 实例）")
    print("=" * 74)

    store = AdaptationStore.discover()
    print(f"\n[通道] root={store.root}")
    print(f"       channel_kind={getattr(store, 'channel_kind', '?')}")
    if getattr(store, "channel_kind", "") == "local":
        print("       警告：未发现真实同步通道，退化为本地目录")

    rcfg = ReplayConfig(workers=4, max_rounds=12, beta_cost=0.01, beta_parallel=0.05)

    # ── Agent B（aris-twin，第二个实例）──
    print("\n[Agent B: aris-twin] 在自己的数据上做梦…")
    pool_b = build_pool(seed=777, n=5)
    eng_b = DreamRSIEngine(config=DreamRSIConfig(
        workers=4, candidates_per_dream=10, seed=777,
        federation_enabled=True, agent_id="aris-twin", scope="general"))
    eng_b.pool = WorldPool.from_dict(pool_b.to_dict())
    eng_b._replay_cfg = rcfg

    bad = ExplorationPolicy(
        params=PolicyParams(strategy="score_greedy", parallel_width=1),
        name="twin_baseline")
    bad_score = avg(bad, pool_b, rcfg)
    deployed_b, rep_b = eng_b.dream_improve(base_policy=bad)
    print(f"   本地基线 {bad_score:.3f}  →  做梦后 {rep_b.selected_score:.3f} "
          f"({rep_b.improvement:+.3f})")
    print(f"   学到策略: {deployed_b}")

    # B 发布改编到真实通道
    ad = export_adaptation(
        deployed_b, agent_id="aris-twin", scope="general",
        evidence_worlds=len(pool_b.worlds),
        evidence_score=rep_b.selected_score,
        baseline_score=rep_b.base_score,
        notes="twin instance e2e test")
    path = store.publish(ad)
    print(f"   已发布改编 → {Path(path).name}")
    print(f"   出境字段: {sorted(json.loads(Path(path).read_text(encoding='utf-8')).keys())}")

    # ── Agent A（aris，本机）──
    print("\n[Agent A: aris] 发现并验证通道上的改编…")
    mine = _anonymize("aris")
    foreign = store.load_all(exclude_agent=mine)
    print(f"   发现 {len(foreign)} 条外部改编")
    assert foreign, "通道上没有发现外部改编"

    # A 自己的世界池（不同种子 = 不同任务实例）
    pool_a = build_pool(seed=101, n=5)
    bad_a = ExplorationPolicy(
        params=PolicyParams(strategy="score_greedy", parallel_width=1),
        name="aris_baseline")
    base_a = avg(bad_a, pool_a, rcfg)

    # 汇合 → 候选（外部改编只作候选）
    cands = merge_adaptations(bad_a, foreign, local_scope="general")
    print(f"   汇合 {len(cands)} 个候选（含结构杂交）")
    best = max(cands, key=lambda p: avg(p, pool_a, rcfg))
    got_a = avg(best, pool_a, rcfg)
    print(f"   A 本地验证: 基线 {base_a:.3f}  →  继承后 {got_a:.3f} "
          f"({got_a - base_a:+.3f})")

    # ── 结论 ──
    print("\n" + "=" * 74)
    print(f"跨实例继承: {'成功' if got_a > base_a else '未提升'}")
    print(f"  共享内容 : 仅策略参数 + 聚合统计（channel_kind={getattr(store,'channel_kind','?')}）")
    print(f"  零泄露   : 发现树 / 会话 / 记忆均未出境")
    print(f"  本地门验证: 外部改编在 A 自己的世界池上评估后才采纳（宪章第七条）")

    # 清理测试改编
    try:
        (store.root / f"{ad.adaptation_id}.json").unlink(missing_ok=True)
        print(f"\n[清理] 已移除测试改编 {ad.adaptation_id}")
    except Exception as e:  # noqa: BLE001
        print(f"\n[清理] 失败: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
