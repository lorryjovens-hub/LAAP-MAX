"""Dream-RSI — 反事实世界生成测试。

覆盖：
1. 合成节点带 synthetic 标记 + 置信折扣（分数 = 估计 × 置信度）；
2. 只在叶子上生长，不修改已记录节点；
3. 溯源信息完整（estimated_score / confidence / reasoning）；
4. LLM 返回非法时优雅降级；
5. 真实 LLM（可选）能生成结构合理的反事实。
"""

from __future__ import annotations

import json
import sys

sys.path.insert(0, r"D:\LAAP")

from laap.dream import DiscoveryTree
from laap.dream.counterfactual import (
    CounterfactualGenerator, CounterfactualConfig, expand_pool_counterfactuals,
)


def _tree() -> DiscoveryTree:
    t = DiscoveryTree()
    a = t.add_node(t.root_id, score=1.0, sketch="try approach A")
    b = t.add_node(a.node_id, score=2.0, sketch="refine A")
    c = t.add_node(t.root_id, score=0.5, sketch="try approach B")
    t.add_node(c.node_id, score=0.6, sketch="refine B (dead end)")
    return t


def _mock_llm(alts=None):
    def fn(prompt):
        items = alts if alts is not None else [
            {"sketch": "alternative: try approach C", "estimated_score": 5.0,
             "reasoning": "promising unexplored direction"},
            {"sketch": "alternative: combine A and B", "estimated_score": 3.0,
             "reasoning": "hybrid"},
        ]
        return json.dumps(items)
    return fn


# ── 1. 折扣 + 标记 ──────────────────────────────────────────────────────

def test_discount_and_marking():
    t = _tree()
    before_real = t.non_root_count()
    gen = CounterfactualGenerator(_mock_llm(), CounterfactualConfig(
        enabled=True, confidence=0.5, max_nodes_per_tree=4,
        max_alternatives_per_leaf=2, max_leaves=4))
    rep = gen.expand(t)
    assert rep.synthetic_nodes > 0, "no synthetic nodes generated"
    # 找到合成节点
    synth = [n for n in t.nodes.values()
             if (n.diagnostics or {}).get("synthetic")]
    assert synth, "no nodes marked synthetic"
    for n in synth:
        est = n.diagnostics["estimated_score"]
        assert abs(n.score - est * 0.5) < 1e-9, f"discount wrong: {n.score} vs {est}"
        assert n.diagnostics["confidence"] == 0.5
        assert "reasoning" in n.diagnostics  # 溯源
    print(f"[OK] discount+marking: {len(synth)} synthetic nodes, "
          f"score = estimate x 0.5")


# ── 2. 不修改真实节点 ───────────────────────────────────────────────────

def test_no_mutation_of_real_nodes():
    t = _tree()
    real_before = {nid: (n.score, n.sketch) for nid, n in t.nodes.items()}
    gen = CounterfactualGenerator(_mock_llm(), CounterfactualConfig(enabled=True))
    gen.expand(t)
    for nid, (score, sketch) in real_before.items():
        n = t.nodes[nid]
        assert n.score == score and n.sketch == sketch, f"real node {nid} mutated!"
        assert not (n.diagnostics or {}).get("synthetic")
    print("[OK] real nodes untouched; synthetic only appended at leaves")


# ── 3. 只在叶子上生长 ───────────────────────────────────────────────────

def test_grows_only_at_leaves():
    t = _tree()
    leaves_before = set(t.leaves())
    gen = CounterfactualGenerator(_mock_llm(), CounterfactualConfig(enabled=True))
    gen.expand(t)
    for n in t.nodes.values():
        if (n.diagnostics or {}).get("synthetic"):
            assert n.parent_id in leaves_before, \
                f"synthetic node attached to non-leaf {n.parent_id}"
    print("[OK] synthetic growth confined to original leaves")


# ── 4. 优雅降级 ─────────────────────────────────────────────────────────

def test_graceful_on_bad_llm():
    t = _tree()
    gen = CounterfactualGenerator(lambda p: "I cannot help.", CounterfactualConfig(enabled=True))
    rep = gen.expand(t)
    assert rep.synthetic_nodes == 0
    assert t.non_root_count() == 4  # 未改变
    # 抛异常的 LLM
    def boom(p):
        raise RuntimeError("llm down")
    rep2 = CounterfactualGenerator(boom, CounterfactualConfig(enabled=True)).expand(t)
    assert rep2.synthetic_nodes == 0
    assert rep2.errors
    print("[OK] graceful degradation on bad/raising LLM")


# ── 5. 关闭时不动 ───────────────────────────────────────────────────────

def test_disabled_by_default():
    t = _tree()
    gen = CounterfactualGenerator(_mock_llm(), CounterfactualConfig())  # enabled=False
    rep = gen.expand(t)
    assert rep.synthetic_nodes == 0
    assert t.non_root_count() == 4
    print("[OK] disabled by default (no synthetic nodes)")


# ── 6. 真实 LLM（可选）──────────────────────────────────────────────────

def test_real_llm_optional():
    try:
        from laap.dream.llm_bridge import make_llm_fn, llm_available
        if not llm_available():
            print("[SKIP] no LLM key")
            return
        fn = make_llm_fn(model="deepseek-flash")
        if fn is None:
            print("[SKIP] no llm fn")
            return
        t = _tree()
        gen = CounterfactualGenerator(fn, CounterfactualConfig(
            enabled=True, confidence=0.5, max_nodes_per_tree=3, max_leaves=2))
        rep = gen.expand(t)
        print(f"[OK] real LLM counterfactuals: {rep.synthetic_nodes} nodes "
              f"({rep.leaves_expanded} leaves expanded)")
    except Exception as e:  # noqa: BLE001
        print(f"[SKIP] real LLM path unavailable: {e}")


if __name__ == "__main__":
    tests = [
        test_discount_and_marking,
        test_no_mutation_of_real_nodes,
        test_grows_only_at_leaves,
        test_graceful_on_bad_llm,
        test_disabled_by_default,
        test_real_llm_optional,
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
