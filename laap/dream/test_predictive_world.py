"""PredictiveWorldModel / PredictiveSelectionPolicy / RetentionGate 验收测试。

核心要验证的是：世界模型在**有可学结构**的树上真的能样本外预测，且在**没有
结构**时诚实报告不可靠并降级——而不是硬用一个假预测。
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from laap.dream.discovery_tree import DiscoveryTree  # noqa: E402
from laap.dream.exploration_policy import ExplorationPolicy, PolicyParams  # noqa: E402
from laap.dream.predictive_world import (  # noqa: E402
    FEATURE_NAMES, N_FEATURES, PredictiveSelectionPolicy, PredictiveWorldModel,
    RetentionGate, _ridge_fit, _ridge_predict, build_and_evaluate, features_for,
)
from laap.dream.replay_world import ReplayConfig, ReplayWorld, WorldPool  # noqa: E402

_passed = 0
_failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  PASS  {name}")
    else:
        _failed += 1
        print(f"  FAIL  {name}  {detail}")


# ══════════════════════════════════════════════════════════════════════
# 合成数据
# ══════════════════════════════════════════════════════════════════════

def make_tree(rng: random.Random, child_coef: float = 0.6,
              q_coef: float = 0.6, noise: float = 0.12, depth: int = 3,
              branch: int = 3, latent: bool = True) -> DiscoveryTree:
    """生成一棵分数有**可预判结构**的树。

    每个节点带一个潜在质量 ``q``，它对**该节点的所有子节点持续生效**:

        score(child) = child_coef · score(parent) + q_coef · q(parent) + N(0, noise)
        artifact_len(child) ∝ q(child)

    关键在于 ``q(v)`` 与 ``score(v)`` **独立**：所以“看当前分排序”（greedy）
    拿不到这层信息，而“看已揭示的兄弟分”（预判）能拿到——这正是世界模型应当
    赢过启发式的地方。``latent=False`` 时退化为 q 恒为 0，即无可学结构。
    """
    tree = DiscoveryTree(tree_id=f"t_{rng.randrange(10**9)}")
    tree.nodes[tree.root_id].metadata["q"] = 0.0

    def grow(parent_id: str, d: int) -> None:
        if d > depth:
            return
        n_kids = rng.randint(1, branch)
        p_node = tree.nodes[parent_id]
        p_score = 0.0 if parent_id == tree.root_id else p_node.score
        p_q = float(p_node.metadata.get("q", 0.0)) if latent else 0.0
        for _ in range(n_kids):
            s = child_coef * p_score + q_coef * p_q + rng.gauss(0.0, noise)
            q = rng.gauss(0.0, 1.0) if latent else 0.0
            # 努力代理：产物长度与潜在质量相关（首个决策就能用上）
            art_len = max(0, int((q + 2.0) * 12))
            nd = tree.add_node(
                parent_id, score=s,
                sketch=f"try at depth {d} " + "x" * rng.randint(0, 20),
                artifact="y" * art_len,
                diagnostics={"ok": True} if rng.random() > 0.3 else {},
            )
            nd.metadata["q"] = q
            grow(nd.node_id, d + 1)

    grow(tree.root_id, 1)
    return tree


def make_noise_tree(rng: random.Random) -> DiscoveryTree:
    """完全无结构的树：分数不与父分数、也不与任何潜在因子相关。"""
    return make_tree(rng, child_coef=0.0, q_coef=0.0, noise=1.0, latent=False)


# ══════════════════════════════════════════════════════════════════════
# 1. 特征
# ══════════════════════════════════════════════════════════════════════

print("\n[1] 特征提取")
rng = random.Random(7)
t = make_tree(rng)
node_ids = [n for n in t.nodes if n != t.root_id]
x = features_for(t, node_ids[0])
check("特征维度正确", len(x) == N_FEATURES, f"got {len(x)}")
check("特征全为有限值",
      all(isinstance(v, float) and v == v and abs(v) < 1e12 for v in x), str(x))

# 无未来信息泄露：prior_siblings 为空时 sibling_count 必须为 0
some_parent = next(n for n, nd in t.nodes.items() if len(nd.children) >= 2)
kids = sorted(t.nodes[some_parent].children, key=lambda c: t.nodes[c].created_order)
x_none = features_for(t, some_parent, prior_siblings=[])
x_one = features_for(t, some_parent, prior_siblings=kids[:1])
i_cnt = FEATURE_NAMES.index("sibling_count")
check("prior_siblings=[] 时 sibling_count=0", x_none[i_cnt] == 0.0, str(x_none[i_cnt]))
check("prior_siblings=[k] 时 sibling_count=1", x_one[i_cnt] == 1.0, str(x_one[i_cnt]))


# ══════════════════════════════════════════════════════════════════════
# 2. 岭回归求解器
# ══════════════════════════════════════════════════════════════════════

print("\n[2] 岭回归求解器")
# 造 y = 3 + 2*x1 - 1*x2，应当精确恢复
Xg, yg = [], []
for i in range(40):
    a, b = (i % 7) * 0.3, (i % 5) * 0.2
    Xg.append([a, b])
    yg.append(3.0 + 2.0 * a - 1.0 * b)
w = _ridge_fit(Xg, yg, lam=1e-6)
pred = _ridge_predict(w, [1.0, 1.0])
check("线性关系精确恢复", abs(pred - (3.0 + 2.0 - 1.0)) < 0.02, f"pred={pred:.4f}")
check("截距恢复", abs(w[0] - 3.0) < 0.02, f"b0={w[0]:.4f}")
check("系数1恢复", abs(w[1] - 2.0) < 0.02, f"w1={w[1]:.4f}")


# ══════════════════════════════════════════════════════════════════════
# 3. 世界模型：有结构 → 可靠；无结构 → 诚实报不可靠
# ══════════════════════════════════════════════════════════════════════

print("\n[3] 世界模型可靠性判定")
rng = random.Random(11)
struct_worlds = [ReplayWorld(make_tree(rng), world_id=f"w{i}") for i in range(10)]
holdout = struct_worlds[-2:]
train = struct_worlds[:-2]

m_struct = PredictiveWorldModel().fit(train)
rep = m_struct.report
print(f"        结构化: n={rep.n_train} r2={rep.r2:.3f} rmse={rep.rmse:.3f} "
      f"base={rep.baseline_rmse:.3f} reliable={rep.is_reliable} ({rep.reason})")
check("有结构数据 -> 样本外 R²>0.05", rep.r2 > 0.05, f"r2={rep.r2:.3f}")
check("有结构数据 -> 判定可靠", rep.is_reliable, rep.reason)
check("世界模型确实用上了 parent_score",
      abs(m_struct.weights.get("parent_score", 0.0)) > 0.1,
      str(m_struct.weights.get("parent_score")))

rng = random.Random(13)
noise_worlds = [ReplayWorld(make_noise_tree(rng), world_id=f"n{i}") for i in range(10)]
m_noise = PredictiveWorldModel().fit(noise_worlds[:-2])
print(f"        无结构: n={m_noise.report.n_train} r2={m_noise.report.r2:.3f} "
      f"reliable={m_noise.report.is_reliable} ({m_noise.report.reason})")
check("无结构数据 -> 判定不可靠", not m_noise.report.is_reliable, m_noise.report.reason)

# 样本太少：用一棵极小的树保证 n < min_samples
_tiny = DiscoveryTree(tree_id="tiny")
_a = _tiny.add_node(_tiny.root_id, score=0.5, sketch="only")
_tiny.add_node(_a.node_id, score=0.6, sketch="leaf")
m_tiny = PredictiveWorldModel().fit([_tiny])
print(f"        极小样本: n={m_tiny.report.n_train} reliable={m_tiny.report.is_reliable} "
      f"({m_tiny.report.reason})")
check("样本不足 -> 判定不可靠", not m_tiny.report.is_reliable, m_tiny.report.reason)
check("样本不足 -> 理由含 n_train", "n_train" in m_tiny.report.reason, m_tiny.report.reason)


# ══════════════════════════════════════════════════════════════════════
# 4. 预测质量：样本外排序能力
# ══════════════════════════════════════════════════════════════════════

print("\n[4] 样本外预测质量")
w_ho = holdout[0]
from laap.dream.replay_world import ObservedView  # noqa: E402

observed = {w_ho.tree.root_id}
view = ObservedView(w_ho.tree, observed)
# 做几轮简单揭示，构造一个有内容的观测视图
for _ in range(4):
    v = ObservedView(w_ho.tree, observed)
    el = v.eligible()
    child = w_ho.tree.earliest_unobserved_child(el[0], observed) if el else None
    if child:
        observed.add(child)

view = ObservedView(w_ho.tree, observed)
preds = [m_struct.predict(view, nid) for nid in view.eligible()]
check("全部候选都能给出预测", len(preds) == len(view.eligible()),
      f"{len(preds)} vs {len(view.eligible())}")
check("预测均值有限", all(abs(p.mean) < 1e6 for p in preds), "")
check("不确定度非负", all(p.std >= 0 for p in preds), "")
check("p_improve 在 [0,1]", all(0.0 <= p.p_improve <= 1.0 for p in preds),
      str([round(p.p_improve, 3) for p in preds]))


# ══════════════════════════════════════════════════════════════════════
# 5. 选择策略：可靠时用预判，不可靠时降级
# ══════════════════════════════════════════════════════════════════════

print("\n[5] 预演式选择策略")
pol = PredictiveSelectionPolicy(m_struct)
pol.reset()
w_test = holdout[0]
cfg = ReplayConfig(workers=3, max_rounds=8)
res_p = w_test.replay(pol, cfg)
check("可靠模型 -> 不降级", not pol.last_degraded, str(pol.last_degraded))
check("回放产生了轮次", res_p.rounds_completed > 0, str(res_p.rounds_completed))
check("产出了预测记录", len(pol.last_predictions) > 0, str(len(pol.last_predictions)))

pol_bad = PredictiveSelectionPolicy(m_noise)
pol_bad.reset()
res_b = w_test.replay(pol_bad, cfg)
check("不可靠模型 -> 自动降级", pol_bad.last_degraded, str(pol_bad.last_degraded))
check("降级后仍能正常回放", res_b.rounds_completed > 0, str(res_b.rounds_completed))

pol_none = PredictiveSelectionPolicy(None)
res_n = w_test.replay(pol_none, ReplayConfig(workers=2, max_rounds=4))
check("无模型 -> 降级且不崩", pol_none.last_degraded and res_n.rounds_completed > 0, "")


# ══════════════════════════════════════════════════════════════════════
# 6. 留用闸门
# ══════════════════════════════════════════════════════════════════════

print("\n[6] 留用闸门")


class _AlwaysWorst:
    """总是挑已揭示里最差的叶子——应当被拒。"""

    name = "always_worst"

    def select_batch(self, view, workers):
        el = [n for n in view.eligible() if n != view.root_id]
        if not el:
            return [view.root_id]
        el.sort(key=lambda n: view.node(n).score)
        return el[:workers]


class _AlwaysBest:
    """总是挑已揭示里最好的叶子——应当胜过随机/平衡。"""

    name = "always_best"

    def select_batch(self, view, workers):
        el = [n for n in view.eligible() if n != view.root_id]
        if not el:
            return [view.root_id]
        el.sort(key=lambda n: view.node(n).score, reverse=True)
        return el[:workers]


gate = RetentionGate()
test_worlds = holdout + [ReplayWorld(make_tree(random.Random(99)), world_id="x1")]

dec_bad = gate.evaluate(_AlwaysWorst(), ExplorationPolicy(
    PolicyParams(strategy="balanced"), name="balanced"), test_worlds)
print(f"        always_worst: delta={dec_bad.delta:.4f} win={dec_bad.win_rate:.2f} "
      f"accept={dec_bad.accept} {dec_bad.reasons}")
check("劣质策略被拒", not dec_bad.accept, str(dec_bad.reasons))
check("劣质策略 delta < 0", dec_bad.delta < 0, f"{dec_bad.delta:.4f}")

dec_same = gate.evaluate(ExplorationPolicy(PolicyParams(strategy="balanced"), name="b2"),
                         ExplorationPolicy(PolicyParams(strategy="balanced"), name="b1"),
                         test_worlds)
check("相同策略 delta≈0（不误判为改进）", abs(dec_same.delta) < 1e-9, f"{dec_same.delta}")

# 兼容性：人为构造一个"平均更好但某世界崩盘"的场景
dec_compat = gate.evaluate(_AlwaysBest(), _AlwaysWorst(), test_worlds)
check("兼容性裁决能产出 per_world 明细",
      len(dec_compat.per_world) == len(test_worlds), str(len(dec_compat.per_world)))


# ══════════════════════════════════════════════════════════════════════
# 7. 端到端
# ══════════════════════════════════════════════════════════════════════

print("\n[7] 端到端 build_and_evaluate")
rng = random.Random(2026)
pool = WorldPool()
for i in range(12):
    pool.add_tree(make_tree(rng))

out = build_and_evaluate(pool, ReplayConfig(workers=3, max_rounds=8))
check("端到端返回 ok", out.get("ok") is True, str(out.get("reason")))
check("含可靠性报告", "reliability" in out, "")
check("含留用裁决", "retention" in out, "")
if out.get("ok"):
    print(f"        reliability: {out['reliability']}")
    print(f"        retention  : accept={out['retention']['accept']} "
          f"delta={out['retention']['delta']} win={out['retention']['win_rate']} "
          f"{out['retention']['reasons']}")
    check("留用裁决含推理理由字段", isinstance(out["retention"]["reasons"], list), "")

# 世界太少时诚实拒绝
tiny_pool = WorldPool()
tiny_pool.add_tree(make_tree(random.Random(1)))
out2 = build_and_evaluate(tiny_pool)
check("世界不足 -> 诚实返回 ok=False", out2.get("ok") is False, str(out2))


# ══════════════════════════════════════════════════════════════════════
# 8. 序列化
# ══════════════════════════════════════════════════════════════════════
# 7.5 决定性对比：预判 vs 看当前分
# ══════════════════════════════════════════════════════════════════════

print("\n[7.5] 预判 vs 启发式（同一批留出世界，同一预算）")
rng = random.Random(4242)
train_worlds = [ReplayWorld(make_tree(rng), world_id=f"tr{i}") for i in range(14)]
eval_worlds = [ReplayWorld(make_tree(rng), world_id=f"ev{i}") for i in range(20)]

m_cmp = PredictiveWorldModel().fit(train_worlds)
print(f"        模型: n={m_cmp.report.n_train} r2={m_cmp.report.r2:.3f} "
      f"reliable={m_cmp.is_reliable} ({m_cmp.report.reason})")
print(f"        权重: {m_cmp.weights}")

cfg_cmp = ReplayConfig(workers=2, max_rounds=10)
pred_scores, greedy_scores, rand_scores = [], [], []
for w in eval_worlds:
    pp = PredictiveSelectionPolicy(m_cmp)
    gp = ExplorationPolicy(PolicyParams(strategy="score_greedy"), name="greedy")
    rp = ExplorationPolicy(PolicyParams(strategy="balanced"), name="balanced")
    pred_scores.append(w.replay(pp, cfg_cmp).score)
    greedy_scores.append(w.replay(gp, cfg_cmp).score)
    rand_scores.append(w.replay(rp, cfg_cmp).score)

mp = sum(pred_scores) / len(pred_scores)
mg = sum(greedy_scores) / len(greedy_scores)
mb = sum(rand_scores) / len(rand_scores)
wins = sum(1 for a, b in zip(pred_scores, greedy_scores) if a > b)
print(f"        预判         平均分 = {mp:.4f}")
print(f"        score_greedy 平均分 = {mg:.4f}")
print(f"        balanced     平均分 = {mb:.4f}")
print(f"        预判胜 greedy: {wins}/{len(eval_worlds)}")
check("预判优于 score_greedy（均值）", mp > mg, f"{mp:.4f} vs {mg:.4f}")
check("预判至少不输给 score_greedy（胜率过半）", wins >= len(eval_worlds) / 2,
      f"{wins}/{len(eval_worlds)}")

# 反向检验：无可学结构时，预判不得被误认为可靠
rng = random.Random(555)
noise_train = [ReplayWorld(make_noise_tree(rng), world_id=f"nt{i}") for i in range(10)]
m_noise2 = PredictiveWorldModel().fit(noise_train)
check("无可学结构 -> 模型诚实报不可靠", not m_noise2.is_reliable, m_noise2.report.reason)
noise_eval = [ReplayWorld(make_noise_tree(rng), world_id=f"ne{i}") for i in range(4)]
pol_n = PredictiveSelectionPolicy(m_noise2)
n_deg = 0
for w in noise_eval:
    pol_n.reset()
    w.replay(pol_n, cfg_cmp)
    n_deg += 1 if pol_n.last_degraded else 0
check("无可学结构 -> 每次回放都降级到启发式", n_deg == len(noise_eval), f"{n_deg}/{len(noise_eval)}")


# ══════════════════════════════════════════════════════════════════════
# 8. 序列化
# ══════════════════════════════════════════════════════════════════════

print("\n[8] 序列化往返")
d = m_struct.to_dict()
m2 = PredictiveWorldModel.from_dict(d)
check("权重往返一致", m_struct._w == m2._w, "")
check("可靠性报告往返一致", abs(m_struct.report.r2 - m2.report.r2) < 1e-3,
      f"{m_struct.report.r2} vs {m2.report.r2}")
p1 = m_struct.predict(view, view.eligible()[0])
p2 = m2.predict(view, view.eligible()[0])
check("预测往返一致", abs(p1.mean - p2.mean) < 1e-9, f"{p1.mean} vs {p2.mean}")
pol_dict = pol.to_dict()
check("策略可序列化", pol_dict.get("kind") == "predictive", str(pol_dict.get("kind")))


print("\n" + "=" * 60)
print(f"结果: {_passed} passed / {_failed} failed")
print("=" * 60)
sys.exit(0 if _failed == 0 else 1)