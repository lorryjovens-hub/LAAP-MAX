"""triphase 全模块测试套件。运行: pytest tests/ -v"""

import math

import numpy as np
import pytest

from triphase import (
    AttentionBudget,
    BudgetExhausted,
    ComplexMultilinearRegressor,
    ComplexResonantMemory,
    DependencyUnverifiedError,
    HypothesisEcosystem,
    InvarianceScreener,
    LinearSCM,
    MetacogAction,
    MetacognitiveMonitor,
    PhaseState,
    PhaseWorldModel,
    PrefixStore,
    SPIRReflector,
    Step,
    StepKind,
    Telemetry,
    TernaryCodeGraph,
    TernaryKVCache,
    TokenPipeline,
    Trit,
    VerificationState,
    angular_distance,
    circular_dispersion,
    complex_cp_als,
    ternary_quantize,
)
from triphase.core import SECTOR_PHASES

RNG = np.random.default_rng(42)


def rand_cvec(dim, seed=None):
    r = np.random.default_rng(seed) if seed is not None else RNG
    return r.standard_normal(dim) + 1j * r.standard_normal(dim)


# --------------------------------------------------------------- core

class TestCore:
    def test_trit_sector_mapping(self):
        assert Trit.from_phase(0.0) is Trit.POS
        assert Trit.from_phase(SECTOR_PHASES[1]) is Trit.NEUTRAL
        assert Trit.from_phase(SECTOR_PHASES[2]) is Trit.NEG
        # 扇区边界容差
        assert Trit.from_phase(0.1) is Trit.POS
        assert Trit.from_phase(-0.1) is Trit.POS

    def test_trit_from_score(self):
        assert Trit.from_score(0.9) is Trit.POS
        assert Trit.from_score(-0.9) is Trit.NEG
        assert Trit.from_score(0.1) is Trit.NEUTRAL

    def test_phase_state_interference(self):
        a = PhaseState(1.0, 0.0)
        b = PhaseState(1.0, 0.0)
        assert a.interference(b) == pytest.approx(1.0)
        c = PhaseState(1.0, math.pi)
        assert a.interference(c) == pytest.approx(-1.0)

    def test_phase_inversion(self):
        s = PhaseState(0.8, 0.3)
        inv = s.inverted()
        assert angular_distance(inv.phase, s.phase) == pytest.approx(math.pi)
        assert inv.magnitude == s.magnitude

    def test_decoherence_decays_magnitude(self):
        rng = np.random.default_rng(0)
        s = PhaseState(1.0, 1.0).decohered(dt=10.0, tau=5.0, phase_diffusion=0.1, rng=rng)
        assert s.magnitude < 0.2

    def test_angular_distance(self):
        assert angular_distance(0.1, 2 * math.pi - 0.1) == pytest.approx(0.2)

    def test_circular_dispersion(self):
        assert circular_dispersion([0.0, 0.0, 0.0]) == pytest.approx(0.0)
        assert circular_dispersion(list(SECTOR_PHASES)) == pytest.approx(1.0)


# --------------------------------------------------------------- memory

class TestCRM:
    def test_consolidation_three_states(self):
        mem = ComplexResonantMemory(dim=8)
        item = mem.store(rand_cvec(8), payload="x", key="k1")
        mem.consolidate("k1", 0.9)
        assert mem.get("k1").state is Trit.POS
        # 巩固后的记忆有惯性，需多次证伪才迁移（设计行为）
        for _ in range(4):
            mem.consolidate("k1", -1.0)
        assert mem.get("k1").state is Trit.NEG

    def test_falsified_memory_not_deleted(self):
        mem = ComplexResonantMemory(dim=8)
        mem.store(rand_cvec(8), payload="坏路径", key="bad")
        mem.consolidate("bad", -1.0)
        assert len(mem) == 1  # 负相位记忆保留（抗体）

    def test_resonance_retrieval_ranks_aligned_first(self):
        mem = ComplexResonantMemory(dim=8)
        v = rand_cvec(8, seed=1)
        mem.store(v, payload="target", key="t", initial_evidence=0.9)
        mem.store(rand_cvec(8, seed=2), payload="other", key="o", initial_evidence=0.9)
        results = mem.retrieve(v, top_k=2)
        assert results[0].item.key == "t"

    def test_negative_memory_produces_warning(self):
        mem = ComplexResonantMemory(dim=8, negative_warn_threshold=0.05)
        v = rand_cvec(8, seed=3)
        v = v / np.linalg.norm(v)
        mem.store(v, payload="DELETE 语句误用", key="bad", initial_evidence=-0.9)
        warns = mem.warnings(v)
        assert warns and "DELETE" in warns[0]

    def test_decay_and_rebuild_advantage(self):
        mem = ComplexResonantMemory(dim=8)
        mem.store(rand_cvec(8), key="k", initial_evidence=0.5)
        before = abs(mem.get("k").strength)
        mem.decay(dt=3600)
        after = abs(mem.get("k").strength)
        assert after < before
        mem.store(rand_cvec(8), key="k")  # 再写入 → 再认优势
        assert mem.get("k").rebuilds == 1


# --------------------------------------------------------------- hypothesis

class TestHypothesis:
    def test_compete_converges(self):
        eco = HypothesisEcosystem(base_coupling=2.0, rng=np.random.default_rng(1))
        for i in range(6):
            eco.add(phase=float(i), strength=0.8)
        out = eco.compete(steps=500)
        assert out.dispersion < 0.5  # 耦合下拉拢

    def test_mutual_exclusion_edge_pushes_apart(self):
        eco = HypothesisEcosystem(base_coupling=0.0, rng=np.random.default_rng(2))
        a = eco.add(phase=0.0, strength=1.0)
        b = eco.add(phase=0.05, strength=1.0)
        eco.link(a.id, b.id, coupling=-1.5)  # 互斥
        for _ in range(400):
            eco.step(0.05, coupling=0.0)
        gap = angular_distance(a.phase, b.phase)
        assert gap > math.pi / 2  # 被推开

    def test_falsify_moves_to_neg_sector_and_callback(self):
        captured = []
        eco = HypothesisEcosystem(on_falsified=lambda h: captured.append(h.id))
        h = eco.add(phase=0.0)
        eco.falsify(h.id, "实验证伪")
        assert Trit.from_phase(eco._hypotheses[h.id].phase) is Trit.NEG
        assert captured == [h.id]


# --------------------------------------------------------------- metacognition

class TestMetacognition:
    def setup_method(self):
        self.mon = MetacognitiveMonitor()

    def test_aligned_acts(self):
        obj = PhaseState(0.9, 0.0)
        tel = Telemetry(retrieval_hit_rate=0.9, hypothesis_dispersion=0.1,
                        unverified_dependency_ratio=0.0)
        v = self.mon.assess(obj, tel)
        assert v.action is MetacogAction.ACT

    def test_confident_but_unsupported_triggers_seek(self):
        """幻觉检测：对象层自信 + 过程无支撑 → SEEK_INFO"""
        obj = PhaseState(0.95, 0.0)
        tel = Telemetry(retrieval_hit_rate=0.0, hypothesis_dispersion=0.9,
                        unverified_dependency_ratio=0.9)
        v = self.mon.assess(obj, tel)
        assert v.action is MetacogAction.SEEK_INFO
        assert "幻觉" in v.rationale

    def test_conflict_triggers_reflect(self):
        obj = PhaseState(0.9, 0.0)
        tel = Telemetry(retrieval_hit_rate=0.8, hypothesis_dispersion=0.1,
                        negative_conflicts=3)
        v = self.mon.assess(obj, tel)
        assert v.action is MetacogAction.REFLECT

    def test_low_evidence_seeks_info(self):
        v = self.mon.assess(PhaseState(0.1, 0.0), Telemetry())
        assert v.action is MetacogAction.SEEK_INFO


# --------------------------------------------------------------- reflection

class _DummyLevel:
    def __init__(self, name, stable):
        self.name = name
        self._stable = stable
        self._n = 0

    def invert_and_run(self, conclusion):
        self._n += 1
        if self._stable:
            return PhaseState(0.7, 0.5)  # 收敛到固定相位
        return PhaseState(conclusion.magnitude, conclusion.phase + 1.0)  # 持续漂移


class TestSPIR:
    def test_finds_culprit_level(self):
        lessons = []
        levels = [_DummyLevel("行动参数", stable=False),
                  _DummyLevel("策略", stable=True)]
        spir = SPIRReflector(levels, on_lesson=lambda msg, s: lessons.append(msg))
        result = spir.reflect(PhaseState(0.8, 0.0))
        assert result.resolved
        assert result.culprit_level == 1
        assert result.culprit_name == "策略"
        assert lessons  # 沉淀回调触发

    def test_circuit_breaker_falls_back(self):
        levels = [_DummyLevel(f"L{i}", stable=False) for i in range(4)]
        spir = SPIRReflector(levels, max_depth=4)
        result = spir.reflect(PhaseState(0.8, 0.0))
        assert not result.resolved
        assert result.fallback_to_seeking
        assert result.final_state.trit is Trit.NEUTRAL  # 退入未定扇区


# --------------------------------------------------------------- codegraph

class TestCodeGraph:
    def build(self):
        g = TernaryCodeGraph()
        g.add_node("db", "module")
        g.add_node("dao", "module")
        g.add_node("service", "module")
        g.add_node("api", "module")
        g.add_edge("db", "dao", coupling=0.9)
        g.add_edge("dao", "service", coupling=0.8)
        g.add_edge("service", "api", coupling=0.7)
        return g

    def test_conservation_law_blocks_unverified(self):
        g = self.build()
        with pytest.raises(DependencyUnverifiedError):
            g.mark_complete("service")  # dao 未验证 → 硬约束

    def test_conservation_law_passes_when_verified(self):
        g = self.build()
        g.verify("db", True)
        g.verify("dao", True)
        g.verify("service", True)
        g.mark_complete("service")

    def test_broken_blocks_completion(self):
        g = self.build()
        g.verify("dao", False)
        with pytest.raises(DependencyUnverifiedError):
            g.mark_complete("service")

    def test_impact_propagation_ordering(self):
        g = self.build()
        impact = g.impact_analysis("db")
        ids = [e.node_id for e in impact]
        assert ids[0] == "dao"          # 最近邻风险最高
        assert set(ids) == {"dao", "service", "api"}
        assert abs(impact[0].risk) > abs(impact[-1].risk)

    def test_polarity_flips_sign(self):
        g = TernaryCodeGraph()
        g.add_node("a", "function")
        g.add_node("b", "function")
        g.add_edge("a", "b", polarity=-1)
        impact = g.impact_analysis("a")
        assert impact[0].risk < 0  # 反向行为变化


# --------------------------------------------------------------- causal

class TestCausal:
    def test_cp_als_recovers_rank1(self):
        rng = np.random.default_rng(7)
        a = rng.standard_normal(5) + 1j * rng.standard_normal(5)
        b = rng.standard_normal(6) + 1j * rng.standard_normal(6)
        c = rng.standard_normal(4) + 1j * rng.standard_normal(4)
        X = np.einsum("i,j,k->ijk", a, b, c)
        w, factors, err = complex_cp_als(X, rank=1, n_iter=500,
                                         rng=np.random.default_rng(3))
        assert err < 1e-3

    def test_regressor_learns_bilinear(self):
        rng = np.random.default_rng(11)
        n = 200
        X1 = rng.standard_normal((n, 3)) + 1j * rng.standard_normal((n, 3))
        X2 = rng.standard_normal((n, 3)) + 1j * rng.standard_normal((n, 3))
        # 真模型：y = (w1·x1)(w2·x2)
        w1 = rng.standard_normal(3) + 1j * rng.standard_normal(3)
        w2 = rng.standard_normal(3) + 1j * rng.standard_normal(3)
        y = (X1 @ w1) * (X2 @ w2)
        reg = ComplexMultilinearRegressor(rank=1, lr=0.05,
                                          rng=np.random.default_rng(5))
        reg.fit([X1, X2], y, epochs=800)
        pred = reg.predict([X1, X2])
        rel = np.linalg.norm(pred - y) / np.linalg.norm(y)
        assert reg.loss_history[-1] < reg.loss_history[0]
        assert rel < 0.15

    def test_scm_intervention_and_counterfactual(self):
        # X → Y → Z，Y = 2X + uY，Z = 3Y + uZ
        scm = LinearSCM(["X", "Y", "Z"], parents={"Y": ["X"], "Z": ["Y"]})
        data = {
            "X": np.array([1, 2, 3, 4], dtype=complex),
            "Y": np.array([2, 4, 6, 8], dtype=complex),
            "Z": np.array([6, 12, 18, 24], dtype=complex),
        }
        scm.fit(data)
        # do(X=5) → Y=10, Z=30
        out = scm.intervene({"X": 5 + 0j})
        assert out["Y"] == pytest.approx(10 + 0j, abs=1e-6)
        assert out["Z"] == pytest.approx(30 + 0j, abs=1e-6)
        # 反事实：个体 X=2（uY=uZ=0），do(Y=0) → Z=0
        cf = scm.counterfactual({"X": 2, "Y": 4, "Z": 12}, do={"Y": 0 + 0j})
        assert cf["Z"] == pytest.approx(0 + 0j, abs=1e-6)
        # 条件 ≠ 干预：do(Y=0) 不改变 X
        assert cf["X"] == pytest.approx(2 + 0j, abs=1e-6)

    def test_invariance_screening(self):
        rng = np.random.default_rng(21)
        envs = []
        for shift in [0.0, 1.0, 2.0]:
            n = 100
            cause = rng.standard_normal(n) + shift
            noise = rng.standard_normal(n)
            target = 2.0 * cause + 0.1 * noise          # 因果特征：系数稳定
            spurious = target * 1.5 + rng.standard_normal(n) * (1 + shift)  # 伪相关
            envs.append({"cause": cause, "spurious": spurious, "y": target})
        scr = InvarianceScreener()
        verdicts = scr.screen(envs, target="y", candidates=["cause", "spurious"])
        v = {x.feature: x for x in verdicts}
        assert v["cause"].trit is Trit.POS
        assert v["spurious"].trit is not Trit.POS


# --------------------------------------------------------------- pipeline

class TestPipeline:
    def setup_method(self):
        self.mem = ComplexResonantMemory(dim=8)
        self.pipe = TokenPipeline(self.mem, deterministic_executor=lambda s: "ok")

    def test_deterministic_step_bypasses_llm(self):
        step = Step("fmt", StepKind.FORMAT, params={"a": 1})
        d = self.pipe.route(step)
        assert d.route is Trit.NEUTRAL
        assert self.pipe.stats.bypassed == 1

    def test_reasoning_goes_full(self):
        step = Step("think", StepKind.REASONING)
        assert self.pipe.route(step).route is Trit.POS

    def test_cache_short_circuits(self):
        step = Step("call", StepKind.TOOL_CALL, params={"x": 1})
        self.pipe._cache[step.cache_key] = "done"
        d = self.pipe.route(step)
        assert d.route is Trit.NEG and d.cached_result == "done"

    def test_antibody_short_circuits_with_warning(self):
        v = rand_cvec(8, seed=9)
        v = v / np.linalg.norm(v)
        self.mem.store(v, payload="已证伪方案", key="bad", initial_evidence=-0.9)
        step = Step("explore", StepKind.REASONING, query_vector=v)
        d = self.pipe.route(step)
        assert d.route is Trit.NEG
        assert any("已证伪" in w for w in d.warnings)

    def test_context_assembly_respects_budget(self):
        for i in range(10):
            self.mem.store(rand_cvec(8, seed=i), payload=f"经验{i}" * 50,
                           key=f"m{i}", initial_evidence=0.8)
        ctx, used = self.pipe.assemble_context(rand_cvec(8), token_budget=100)
        assert used <= 100

    def test_record_outcome_drives_consolidation(self):
        step = Step("t", StepKind.TOOL_CALL, params={"k": 1})
        self.pipe.record_outcome(step, "res", rand_cvec(8), success=False)
        item = self.mem.get(f"outcome:{step.cache_key}")
        assert item.state is Trit.NEG  # 失败 → 负相位沉淀


# --------------------------------------------------------------- harness

class TestHarness:
    def test_ternary_quantize(self):
        x = np.array([10.0, -9.0, 0.01, 0.0, 8.0])
        q, scale = ternary_quantize(x, threshold=0.5)
        assert set(np.unique(q)) <= {-1, 0, 1}
        assert q[2] == 0 and q[0] == 1 and q[1] == -1

    def test_kv_cache_lifecycle(self):
        evicted = []
        cache = TernaryKVCache(capacity=2, on_evict=lambda e: evicted.append(e.key))
        k0 = rand_cvec(4, seed=10)
        cache.put("k0", k0, np.arange(8.0))
        cache.access("k0", k0)          # 提升 k0 亲和度 → 保留满精度
        cache.put("k1", rand_cvec(4, seed=11), np.arange(8.0))
        cache.put("k2", rand_cvec(4, seed=12), np.arange(8.0))  # 触发维护
        st = cache.stats()
        assert st["size"] <= 2
        assert evicted                  # 驱逐回调触发（摘要入记忆通道）
        assert st["by_state"]["FULL"] >= 1  # 高亲和条目保留满精度

    def test_kv_quantized_readback(self):
        cache = TernaryKVCache(capacity=10, quantize_below=100.0)  # 强制全量化
        key_vec = rand_cvec(4, seed=5)
        cache.put("a", key_vec, np.array([4.0, -4.0, 0.01, 3.9]))
        cache.access("a", key_vec)      # 建立亲和度，避免被自然驱逐
        cache.maintenance()
        val = cache.access("a", key_vec)
        assert val is not None and val.shape == (4,)

    def test_prefix_partial_invalidation(self):
        store = PrefixStore(invalidate_within=np.pi / 3)
        store.register("sys", {"kv": 1}, phase_tag=0.0)
        store.register("domain", {"kv": 2}, phase_tag=np.pi)  # 远相位
        doomed = store.invalidate(updated_phase=0.2)
        assert doomed == ["sys"]
        assert store.get("domain") is not None

    def test_budget_allocation_and_exhaustion(self):
        from triphase.metacognition import MetacogAction as MA
        b = AttentionBudget(total=100.0)
        assert b.grant(MA.ACT) == pytest.approx(50.0)
        b.spend(60.0)
        with pytest.raises(BudgetExhausted):
            b.spend(50.0)


# --------------------------------------------------------------- worldmodel

class TestWorldModel:
    def test_rollout_shapes(self):
        wm = PhaseWorldModel(dim=6, action_dim=2, radius=5.0,
                             rng=np.random.default_rng(0))
        z0 = 0.1 * rand_cvec(6, seed=1)
        actions = [np.zeros(2, dtype=complex) for _ in range(5)]
        res = wm.rollout(z0, actions)
        assert len(res.trajectory) == 5
        assert all(isinstance(t, Trit) for t in res.verdicts)

    def test_near_unitary_bounds_magnitude_growth(self):
        wm = PhaseWorldModel(dim=4, action_dim=1, damping=1.0, radius=1e6,
                             rng=np.random.default_rng(2))
        z = rand_cvec(4, seed=3)
        z = z / np.linalg.norm(z)
        for _ in range(100):
            z = wm.step(z, np.zeros(1, dtype=complex))
        assert np.linalg.norm(z) == pytest.approx(1.0, rel=1e-6)  # 模长不爆炸

    def test_forbidden_detection(self):
        wm = PhaseWorldModel(dim=4, action_dim=1, radius=1.0,
                             rng=np.random.default_rng(4))
        assert wm.classify(np.ones(4) * 100) is Trit.NEG  # 违反守恒约束
