"""KDA / AttnRes / LatentMoE harness 工程化测试套件。"""

import numpy as np
import pytest

from triphase import (
    AttentionResidual,
    HybridMemoryScheduler,
    KimiDeltaAttention,
    LatentMoE,
    LookupMode,
    MetacogAction,
    MetacogVerdict,
    PhaseState,
    QuantileBalancedRouter,
    StageResidualMemory,
)


def verdict(action):
    return MetacogVerdict(action, 0.0, PhaseState(0.5, 0.0),
                          PhaseState(0.5, 0.0), "test")


# --------------------------------------------------------------- KDA

class TestKDA:
    def test_single_write_then_read(self):
        """β≈1 写入后，用同键读出应近似写入值。"""
        kda = KimiDeltaAttention(x_dim=8, d_k=16, d_v=8,
                                 rng=np.random.default_rng(0))
        x = np.random.default_rng(1).standard_normal(8)
        kda.b_beta = 10.0   # 强制 β≈1
        kda.b_alpha[:] = 10.0  # α≈1（全记住）
        (k, v, q), (_, beta) = kda.gates(x)
        kda.step(x)
        out = kda.S.T @ k
        assert np.allclose(out, v, atol=0.1)  # S = k vᵀ → Sᵀk = v（k 归一）

    def test_same_key_overwrites_not_accumulates(self):
        """delta 规则：同键重写是覆写，不是叠加。"""
        kda = KimiDeltaAttention(x_dim=8, d_k=16, d_v=8,
                                 rng=np.random.default_rng(2))
        kda.b_beta = 10.0
        kda.b_alpha[:] = 10.0
        rng = np.random.default_rng(3)
        x = rng.standard_normal(8)
        kda.step(x)
        v1 = kda.S.T @ kda.gates(x)[0][0]
        # 修改 W_v 制造新值，再用同键写入
        kda.W_v = rng.standard_normal((8, 8)) / np.sqrt(8)
        kda.step(x)
        (k, v2_expected, _), _ = kda.gates(x)
        v2 = kda.S.T @ k
        assert np.allclose(v2, v2_expected, atol=0.15)  # 新值覆写旧值
        assert not np.allclose(v2, v1 + v2_expected, atol=0.5)

    def test_forget_gate_erases(self):
        """α→0 时旧记忆被清除。"""
        kda = KimiDeltaAttention(x_dim=8, d_k=16, d_v=8,
                                 rng=np.random.default_rng(4))
        rng = np.random.default_rng(5)
        kda.b_beta = 10.0
        kda.b_alpha[:] = 10.0
        kda.step(rng.standard_normal(8))
        norm_before = np.linalg.norm(kda.S)
        kda.b_alpha[:] = -10.0   # α≈0
        kda.b_beta = -10.0       # 不写入
        kda.step(rng.standard_normal(8))
        assert np.linalg.norm(kda.S) < 0.1 * norm_before

    def test_state_size_independent_of_history(self):
        """定态：内存占用与历史长度无关（KV cache 的本质区别）。"""
        kda = KimiDeltaAttention(x_dim=8, d_k=16, d_v=8,
                                 rng=np.random.default_rng(6))
        rng = np.random.default_rng(7)
        before = kda.nbytes
        for _ in range(1000):
            kda.step(rng.standard_normal(8))
        assert kda.nbytes == before
        assert kda.steps == 1000

    def test_snapshot_restore(self):
        kda = KimiDeltaAttention(x_dim=8, d_k=16, d_v=8,
                                 rng=np.random.default_rng(8))
        rng = np.random.default_rng(9)
        for _ in range(10):
            kda.step(rng.standard_normal(8))
        snap = kda.snapshot()
        kda.step(rng.standard_normal(8))
        kda.restore(snap)
        assert np.allclose(kda.S, snap)


class TestHybridScheduler:
    def test_periodic_exact_lookup(self):
        kda = KimiDeltaAttention(8, 16, 8, rng=np.random.default_rng(10))
        calls = []
        sched = HybridMemoryScheduler(kda, lambda x: calls.append("exact"), ratio=3)
        rng = np.random.default_rng(11)
        modes = [sched.access(rng.standard_normal(8)).mode for _ in range(8)]
        assert modes.count(LookupMode.EXACT) == 2   # 第 4、8 步
        assert sched.stats["exact_periodic"] == 2

    def test_metacognition_overrides_schedule(self):
        """元认知触发优先于周期表：不确定时立即精确回查。"""
        kda = KimiDeltaAttention(8, 16, 8, rng=np.random.default_rng(12))
        sched = HybridMemoryScheduler(kda, lambda x: "exact", ratio=3)
        rng = np.random.default_rng(13)
        a = sched.access(rng.standard_normal(8),
                         verdict=verdict(MetacogAction.SEEK_INFO))
        assert a.mode is LookupMode.EXACT
        assert sched.stats["exact_triggered"] == 1

    def test_compression_estimate(self):
        kda = KimiDeltaAttention(8, 16, 8, rng=np.random.default_rng(14))
        sched = HybridMemoryScheduler(kda, lambda x: None)
        est = sched.compression_estimate(per_token_kv_bytes=256,
                                         history_len=100_000)
        assert est["ratio"] > 100  # 长历史下压缩比显著


# --------------------------------------------------------------- AttnRes

class TestAttnRes:
    def test_retrieves_most_relevant(self):
        ar = AttentionResidual(dim=4, temperature=0.5)
        h = [np.array([1.0, 0, 0, 0]), np.array([0, 1.0, 0, 0]),
             np.array([0, 0, 1.0, 0])]
        out, w = ar.compose(np.array([0.9, 0.1, 0, 0]), h)
        assert np.argmax(w) == 0          # 检索到最相关层
        assert w.sum() == pytest.approx(1.0)

    def test_uniform_when_temperature_high(self):
        ar = AttentionResidual(dim=4, temperature=1e6)
        h = [np.array([1.0, 0, 0, 0]), np.array([0, 1.0, 0, 0])]
        _, w = ar.compose(np.array([1.0, 0, 0, 0]), h)
        assert w[0] == pytest.approx(0.5, abs=0.01)  # 高温 ≈ 均匀累加（残差特例）

    def test_stage_memory_budget(self):
        srm = StageResidualMemory(dim=4, temperature=0.5)
        srm.push("感知", np.array([1.0, 0, 0, 0]), "obs", token_cost=100)
        srm.push("检索", np.array([0, 1.0, 0, 0]), "docs", token_cost=500)
        srm.push("推理", np.array([0.9, 0.1, 0, 0]), "cot", token_cost=300)
        ctx = srm.compose(np.array([1.0, 0, 0, 0]), token_budget=350)
        names = [s.stage for s, _ in ctx.selected]
        assert "感知" in names            # 最相关阶段必选
        assert ctx.tokens_used <= 350
        assert ctx.tokens_if_concat == 900

    def test_token_savings_vs_concat(self):
        srm = StageResidualMemory(dim=8)
        rng = np.random.default_rng(20)
        for i in range(10):
            srm.push(f"stage{i}", rng.standard_normal(8), f"p{i}",
                     token_cost=200)
        ctx = srm.compose(rng.standard_normal(8), token_budget=400)
        assert ctx.tokens_used < ctx.tokens_if_concat  # 结构性省 token


# --------------------------------------------------------------- LatentMoE

class TestRouter:
    def test_top_k_selection(self):
        r = QuantileBalancedRouter(n_experts=16, top_k=3,
                                   rng=np.random.default_rng(30))
        routed = r.route(np.random.default_rng(31).standard_normal(8))
        assert len(routed) == 3
        assert sum(w for _, w in routed) == pytest.approx(1.0)

    def test_quantile_balancing_reduces_skew(self):
        """制造一个"明星专家"：路由分数长期偏高。
        分位数均衡应显著压低其被路由频率（对比无均衡基线）。"""
        rng = np.random.default_rng(40)
        x_dim, n = 8, 8

        class BiasedRouter(QuantileBalancedRouter):
            def scores(self, x):
                s = super().scores(x)
                s[0] = 0.99   # 明星专家
                return s

        balanced = BiasedRouter(n_experts=n, top_k=2, rng=np.random.default_rng(41))
        # 无均衡基线：直接按原始分
        raw_loads = np.zeros(n)
        for _ in range(200):
            s = balanced.scores(rng.standard_normal(x_dim))
            for i in np.argsort(-s)[:2]:
                raw_loads[i] += 1
            balanced.route(rng.standard_normal(x_dim))

        star_raw = raw_loads[0] / raw_loads.sum()
        star_balanced = balanced.loads[0] / balanced.loads.sum()
        assert star_balanced < star_raw          # 均衡后明星专家被抑制
        assert balanced.load_cv < (raw_loads.std() / raw_loads.mean())

    def test_all_experts_get_traffic(self):
        r = QuantileBalancedRouter(n_experts=8, top_k=2,
                                   rng=np.random.default_rng(50))
        rng = np.random.default_rng(51)
        for _ in range(500):
            r.route(rng.standard_normal(8))
        assert (r.loads > 0).all()               # 无专家饿死


class TestLatentMoE:
    def test_routes_and_executes(self):
        calls = []
        moe = LatentMoE(
            experts={"legal": lambda x: calls.append("legal") or "L",
                     "finance": lambda x: calls.append("finance") or "F",
                     "bio": lambda x: calls.append("bio") or "B"},
            top_k=2, rng=np.random.default_rng(60))
        out = moe(np.random.default_rng(61).standard_normal(8))
        assert len(out) == 2
        assert len(calls) == 2                    # 只执行被选中的专家

    def test_combine_hook(self):
        moe = LatentMoE(
            experts={"a": lambda x: 1.0, "b": lambda x: 2.0, "c": lambda x: 3.0},
            top_k=2, rng=np.random.default_rng(70),
            combine=lambda routed: sum(r.weight * r.output for r in routed))
        out = moe(np.random.default_rng(71).standard_normal(8))
        assert isinstance(out, float)

    def test_balance_report(self):
        moe = LatentMoE(
            experts={f"e{i}": (lambda x: x) for i in range(6)},
            top_k=2, rng=np.random.default_rng(80))
        rng = np.random.default_rng(81)
        for _ in range(100):
            moe(rng.standard_normal(8))
        report = moe.balance_report()
        assert "load_cv" in report and "expert_names" in report
