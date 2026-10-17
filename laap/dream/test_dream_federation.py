"""Dream-RSI — 跨 Agent 策略联邦测试。

覆盖：
1. export_adaptation：匿名化 + 置信度计算；
2. merge_adaptations：作用域过滤 / 证据门控 / 结构杂交；
3. AdaptationStore：发布 / 加载 / 统计；
4. **端到端**：Agent A 本地做梦学到好策略 → 发布 → Agent B 直接继承
   （无须重新探索），且不共享任何原始经验。
"""

from __future__ import annotations

import json
import random
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, r"D:\LAAP")

from laap.dream import (
    ExplorationPolicy, PolicyParams, DreamRSIConfig, DreamRSIEngine, WorldPool,
    ReplayConfig, default_parallel_refining_policy,
)
from laap.dream.federation import (
    PolicyAdaptation, export_adaptation, merge_adaptations, AdaptationStore,
    _anonymize,
)


def _bad_policy() -> ExplorationPolicy:
    return ExplorationPolicy(
        params=PolicyParams(strategy="score_greedy", parallel_width=1),
        name="baseline_greedy")


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


def _build_pool(seed: int, n: int = 4) -> WorldPool:
    cfg = DreamRSIConfig(workers=4, online_max_rounds=40, seed=seed)
    eng = DreamRSIEngine(config=cfg)
    fn = make_sparse_task(seed)
    for _ in range(n):
        eng.construct_simulator(eng.online_rollout(fn))
    return eng.pool


# ── 1. 导出 ─────────────────────────────────────────────────────────────

def test_export_no_raw_experience():
    pol = default_parallel_refining_policy()
    a = export_adaptation(pol, agent_id="aris", scope="code",
                          evidence_worlds=5, evidence_score=10.0,
                          baseline_score=8.0)
    d = a.to_dict()
    # 出境字段只含策略参数与聚合统计
    allowed = {"adaptation_id", "origin_agent", "scope", "policy_name",
               "policy_params", "evidence_worlds", "evidence_score",
               "baseline_score", "improvement", "confidence", "created_at", "notes"}
    assert set(d.keys()) == allowed, set(d.keys()) ^ allowed
    # 匿名化：不含原始 agent id
    assert a.origin_agent != "aris"
    assert a.origin_agent == _anonymize("aris")
    assert a.improvement == 2.0
    assert a.confidence > 0
    print(f"[OK] export has no raw experience; agent anonymized -> {a.origin_agent}")


def test_confidence_scaling():
    pol = default_parallel_refining_policy()
    lo = export_adaptation(pol, evidence_worlds=1, evidence_score=10, baseline_score=9)
    hi = export_adaptation(pol, evidence_worlds=20, evidence_score=10, baseline_score=9)
    assert hi.confidence > lo.confidence, (lo.confidence, hi.confidence)
    # 无提升 → 置信度 0
    none = export_adaptation(pol, evidence_worlds=20, evidence_score=9, baseline_score=9)
    assert none.confidence == 0.0
    print(f"[OK] confidence scales with evidence ({lo.confidence} < {hi.confidence}; no-gain=0)")


# ── 2. 汇合 ─────────────────────────────────────────────────────────────

def test_merge_scope_filter():
    local = default_parallel_refining_policy()
    adapts = [
        PolicyAdaptation(scope="code", policy_params={"strategy": "breadth_first"},
                         improvement=5.0, confidence=0.8, origin_agent="a1"),
        PolicyAdaptation(scope="chat", policy_params={"strategy": "depth_first"},
                         improvement=9.0, confidence=0.9, origin_agent="a2"),
    ]
    out = merge_adaptations(local, adapts, local_scope="code")
    # 只接受 code / general
    names = {c.params.strategy for c in out}
    assert "breadth_first" in names
    assert "depth_first" not in names, "chat adaptation leaked into code scope"
    print("[OK] merge respects scope typing")


def test_merge_evidence_gate():
    local = default_parallel_refining_policy()
    adapts = [
        PolicyAdaptation(scope="general", policy_params={"strategy": "novelty_seeking"},
                         improvement=1.0, confidence=0.1, origin_agent="a1"),
    ]
    assert merge_adaptations(local, adapts, min_confidence=0.5) == []
    assert len(merge_adaptations(local, adapts, min_confidence=0.0)) >= 1
    print("[OK] merge respects evidence gate")


def test_merge_hybrids():
    local = ExplorationPolicy(
        params=PolicyParams(strategy="balanced", parallel_width=7),
        name="local")
    adapts = [PolicyAdaptation(scope="general",
                               policy_params={"strategy": "breadth_first",
                                              "parallel_width": 2},
                               improvement=3.0, confidence=0.9, origin_agent="a1")]
    out = merge_adaptations(local, adapts, include_hybrids=True)
    hybrids = [c for c in out if "hybrid" in c.name]
    assert hybrids, "no hybrid candidate generated"
    h = hybrids[0]
    # 结构取外部，数值保留本地
    assert h.params.strategy == "breadth_first"
    assert h.params.parallel_width == 7
    print("[OK] merge generates structure hybrids (ext strategy + local numerics)")


# ── 3. 存储 ─────────────────────────────────────────────────────────────

def test_store(tmp: Path):
    store = AdaptationStore(tmp / "fed")
    a1 = export_adaptation(default_parallel_refining_policy(), agent_id="aris",
                           scope="code", evidence_worlds=5, evidence_score=10, baseline_score=8)
    p = store.publish(a1)
    assert Path(p).exists()
    loaded = store.load_all()
    assert len(loaded) == 1
    assert loaded[0].origin_agent == a1.origin_agent
    # 排除自己的
    assert store.load_all(exclude_agent=_anonymize("aris")) == []
    assert store.stats()["count"] == 1
    print("[OK] adaptation store publish/load")


def test_channel_discovery(tmp: Path):
    """LAAPer 联邦通道自动发现：显式 > LAAP 同步根 > 本地。"""
    import os as _os
    # 1) 显式环境变量
    _os.environ["LAAP_DREAM_SYNC"] = str(tmp / "chan")
    try:
        st = AdaptationStore.discover()
        assert st.channel_kind == "community", st.channel_kind
        assert "chan" in str(st.root)
    finally:
        del _os.environ["LAAP_DREAM_SYNC"]
    # 2) LAAP_SYNC_ROOT
    _os.environ["LAAP_SYNC_ROOT"] = str(tmp / "lanroot")
    try:
        st = AdaptationStore.discover()
        assert st.channel_kind == "lan", st.channel_kind
        assert str(st.root).endswith("dream_rsi") or "dream_rsi" in str(st.root)
    finally:
        del _os.environ["LAAP_SYNC_ROOT"]
    # 3) 本地回退
    st = AdaptationStore.discover(tmp / "localonly")
    assert st.channel_kind in ("local", "lan")
    print("[OK] channel discovery: explicit/community -> LAN -> local fallback")


# ── 4. 端到端：Agent A 学 → Agent B 继承 ───────────────────────────────

def test_cross_agent_inheritance(tmp: Path):
    store_dir = str(tmp / "fed")
    rcfg = ReplayConfig(workers=4, max_rounds=12, beta_cost=0.01, beta_parallel=0.05)

    # Agent A：拥有自己的世界池，从烂基线出发做梦，学到好策略
    pool_a = _build_pool(seed=7)
    eng_a = DreamRSIEngine(config=DreamRSIConfig(
        workers=4, candidates_per_dream=10, seed=3,
        federation_enabled=True, federation_dir=store_dir,
        agent_id="agent_A", scope="general"))
    eng_a.pool = WorldPool.from_dict(pool_a.to_dict())
    eng_a._replay_cfg = rcfg
    _, rep_a = eng_a.dream_improve(base_policy=_bad_policy())
    # A 学到的最优候选名（从扫描命名中反推策略结构）
    best_a_name = max(rep_a.scores, key=lambda k: rep_a.scores[k])
    from laap.dream.exploration_policy import STRATEGIES
    best_strategy = next((s for s in STRATEGIES if f"sweep_{s}_" in best_a_name),
                         "balanced")
    best_policy = ExplorationPolicy(
        params=PolicyParams(strategy=best_strategy, parallel_width=2),
        name=best_a_name)
    store = AdaptationStore(store_dir)
    ad = export_adaptation(best_policy, agent_id="agent_A", scope="general",
                           evidence_worlds=len(pool_a.worlds),
                           evidence_score=rep_a.selected_score,
                           baseline_score=rep_a.base_score)
    store.publish(ad)

    # Agent B：不同任务种子、不同世界池，烂基线；联邦开启
    pool_b = _build_pool(seed=99)
    eng_b = DreamRSIEngine(config=DreamRSIConfig(
        workers=4, candidates_per_dream=10, seed=5,
        federation_enabled=True, federation_dir=store_dir,
        agent_id="agent_B", scope="general"))
    eng_b.pool = WorldPool.from_dict(pool_b.to_dict())
    eng_b._replay_cfg = rcfg

    # B 汇合外部改编为候选
    from laap.dream.federation import merge_adaptations
    foreign = store.load_all(exclude_agent=_anonymize("agent_B"))
    cands = merge_adaptations(_bad_policy(), foreign, local_scope="general")
    assert cands, "Agent B got no federated candidates"

    # B 在**自己的**世界池上评估候选（外部改编不能直接生效）
    def avg(p):
        return sum(w.replay(p, rcfg).score for w in eng_b.pool.worlds) / len(eng_b.pool.worlds)

    bad = avg(_bad_policy())
    best_foreign = max(cands, key=avg)
    got = avg(best_foreign)
    assert got > bad, f"federated inheritance failed: {bad:.3f} -> {got:.3f}"
    print(f"[OK] cross-agent inheritance: B {bad:.3f} -> {got:.3f} "
          f"(+{got - bad:.3f}) via adaptation from {foreign[0].origin_agent}")
    # 确认没有原始经验泄露
    raw = json.loads(Path(store.publish(ad)).read_text(encoding="utf-8"))
    assert "tree" not in json.dumps(raw).lower()
    assert "session" not in json.dumps(raw).lower()


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        tests = [
            test_export_no_raw_experience,
            test_confidence_scaling,
            test_merge_scope_filter,
            test_merge_evidence_gate,
            test_merge_hybrids,
            lambda: test_store(tmp),
            lambda: test_channel_discovery(tmp),
            lambda: test_cross_agent_inheritance(tmp),
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
