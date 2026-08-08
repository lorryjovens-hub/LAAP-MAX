"""RSI 递归进化引擎与自愈引擎测试套件。运行: pytest tests/test_rsi_selfheal.py -v"""

import numpy as np
import pytest

from triphase import (
    ComplexResonantMemory,
    EvolutionFrozen,
    Genome,
    InvariantCore,
    InvariantViolation,
    Modification,
    ModificationKind,
    PhaseState,
    RSILoop,
    SelfHealingEngine,
    SelfModel,
    SPIRReflector,
    Trit,
)
from triphase.selfheal import AnomalySignal


# --------------------------------------------------------------- 自愈引擎

class _ProbeBox:
    """可控探针：外部拨动健康分，模拟故障注入。"""

    def __init__(self, score=1.0):
        self.score = score

    def __call__(self):
        return self.score


class _SwitchRepair:
    """修复策略：把探针拨回健康（模拟真实修复动作）。"""

    def __init__(self, box, target=1.0, succeed=True):
        self.box, self.target, self.succeed = box, target, succeed
        self.calls = 0

    def repair(self, signal, diagnosis):
        self.calls += 1
        if self.succeed:
            self.box.score = self.target
        return True


class TestSelfModel:
    def test_healthy_when_aligned(self):
        sm = SelfModel()
        sm.register("retrieval", _ProbeBox(0.98), baseline=1.0)
        signals = sm.sync()
        assert signals[0].trit is Trit.POS

    def test_degraded_and_critical(self):
        sm = SelfModel(degraded_above=0.1, critical_above=0.4)
        sm.register("a", _ProbeBox(0.8), baseline=1.0)   # 缺损 0.2 → 退化
        sm.register("b", _ProbeBox(0.3), baseline=1.0)   # 缺损 0.7 → 危重
        sm.register("c", _ProbeBox(0.99), baseline=1.0)
        trits = {s.capability: s.trit for s in sm.sync()}
        assert trits == {"a": Trit.NEUTRAL, "b": Trit.NEG, "c": Trit.POS}

    def test_crashing_probe_is_critical(self):
        def boom():
            raise RuntimeError("probe crashed")
        sm = SelfModel()
        sm.register("x", boom, baseline=1.0)
        assert sm.sync()[0].trit is Trit.NEG

    def test_overall_health_phase_state(self):
        sm = SelfModel()
        sm.register("a", _ProbeBox(1.0))
        sm.register("b", _ProbeBox(0.5))
        sm.sync()  # 运行探针后再读取整体健康
        h = sm.health()
        assert 0.5 < h.magnitude < 1.0 and h.phase > 0


class TestSelfHealing:
    def _setup(self, succeed=True):
        mem = ComplexResonantMemory(dim=16)
        sm = SelfModel()
        box = _ProbeBox(0.2)  # 危重
        sm.register("db", box, baseline=1.0)
        strategy = _SwitchRepair(box, succeed=succeed)
        engine = SelfHealingEngine(sm, mem, strategies={"db": strategy})
        return engine, mem, box, strategy

    def test_repair_verified_and_antibody_consolidated(self):
        engine, mem, box, strategy = self._setup()
        events = engine.heal_cycle()
        assert len(events) == 1
        assert events[0].recovered
        assert events[0].trit_after is Trit.POS
        item = mem.get("repair:db")
        assert item is not None and item.state is Trit.POS  # 修复模式入库

    def test_failed_repair_leaves_negative_antibody(self):
        engine, mem, box, strategy = self._setup(succeed=False)
        events = engine.heal_cycle()
        assert not events[0].recovered
        item = mem.get("repair:db")
        assert item.state is Trit.NEG  # 失败教训硬沉淀

    def test_antibody_fastpath_skips_diagnosis(self):
        engine, mem, box, strategy = self._setup()
        engine.heal_cycle()  # 第一次：诊断路径，沉淀修复模式
        box.score = 0.2      # 再次故障
        called = []
        engine.reflector_factory = lambda name: called.append(name) or None
        events = engine.heal_cycle()
        assert events[0].path == "antibody_fastpath"
        assert not called  # 快路径未触发诊断器工厂

    def test_max_attempts_bounds_repair_oscillation(self):
        engine, _, _, strategy = self._setup(succeed=False)
        engine.heal_cycle()
        assert strategy.calls <= engine.max_attempts

    def test_unrepairable_capability_escalates(self):
        mem = ComplexResonantMemory(dim=16)
        sm = SelfModel()
        sm.register("orphan", _ProbeBox(0.1), baseline=1.0)
        engine = SelfHealingEngine(sm, mem, strategies={})
        events = engine.heal_cycle()
        assert events[0].path == "unrepairable" and not events[0].recovered


# --------------------------------------------------------------- RSI 引擎

def make_genome(fitness=0.5, **components):
    g = Genome(version=1, components=components or {"lr": 0.01, "depth": 2})
    g.fitness = fitness
    return g


def mod(target, delta, risk=0.1, kind=ModificationKind.HYPERPARAM):
    def apply(c):
        c[target] = c.get(target, 0) + delta
    return Modification(target=target, kind=kind, apply=apply, risk=risk)


class TestRSI:
    def test_promote_on_real_gain(self):
        loop = RSILoop(evaluator=lambda g: g.components["lr"])  # 适应度=lr
        g = make_genome(fitness=0.01, lr=0.01)
        g2, report = loop.step(g, [mod("lr", 0.5)])
        assert report.verdicts[0].trit is Trit.POS
        assert g2.version == 2 and g2.components["lr"] == pytest.approx(0.51)

    def test_revert_on_regression(self):
        loop = RSILoop(evaluator=lambda g: g.components["lr"])
        g = make_genome(fitness=0.5, lr=0.5)
        g2, report = loop.step(g, [mod("lr", -0.4)])
        assert report.verdicts[0].trit is Trit.NEG
        assert g2.version == 1  # 未晋升

    def test_gray_zone_holds(self):
        """灰带：微小波动不晋升（抗噪声进化）"""
        loop = RSILoop(evaluator=lambda g: g.components["lr"], promote_margin=0.1)
        g = make_genome(fitness=0.5, lr=0.5)
        g2, report = loop.step(g, [mod("lr", 0.01)])
        assert report.verdicts[0].trit is Trit.NEUTRAL
        assert g2.version == 1

    def test_invariant_violation_hard_reject(self):
        core = InvariantCore()
        core.add("lr_positive", lambda g: g.components["lr"] > 0)
        loop = RSILoop(evaluator=lambda g: g.components["lr"], invariants=core)
        g = make_genome(fitness=0.5, lr=0.5)
        g2, report = loop.step(g, [mod("lr", -1.0)])  # 会使 lr<0
        assert report.verdicts[0].trit is Trit.NEG
        assert "不变量" in report.verdicts[0].reason
        assert g2.version == 1

    def test_freeze_after_repeated_violations(self):
        core = InvariantCore()
        core.add("lr_positive", lambda g: g.components["lr"] > 0)
        loop = RSILoop(evaluator=lambda g: g.components["lr"],
                       invariants=core, freeze_after_violations=2)
        g = make_genome(fitness=0.5, lr=0.5)
        loop.step(g, [mod("lr", -1.0)])
        loop.step(g, [mod("lr", -1.0)])  # 第二次违例 → 冻结
        assert loop.frozen
        with pytest.raises(EvolutionFrozen):
            loop.step(g, [mod("lr", 0.1)])
        loop.unfreeze()  # 人工解冻
        assert not loop.frozen

    def test_human_gate_for_high_risk(self):
        approvals = []
        loop = RSILoop(
            evaluator=lambda g: g.components["lr"],
            human_gate=lambda m: approvals.append(m.id) or True,
            risk_threshold=0.5,
        )
        g = make_genome(fitness=0.5, lr=0.5)
        loop.step(g, [mod("lr", 0.3, risk=0.9)])
        assert approvals  # 高风险走了人工门

    def test_high_risk_rejected_without_gate_freezes(self):
        loop = RSILoop(evaluator=lambda g: g.components["lr"],
                       human_gate=None, risk_threshold=0.5)
        g = make_genome(fitness=0.5, lr=0.5)
        with pytest.raises(EvolutionFrozen):
            loop.step(g, [mod("lr", 0.3, risk=0.9)])

    def test_stagnation_converges(self):
        loop = RSILoop(evaluator=lambda g: 1.0, promote_margin=0.05,
                       stagnation_limit=2)
        g = make_genome(fitness=1.0)
        _, r1 = loop.step(g, [mod("lr", 0.001)])
        _, r2 = loop.step(g, [mod("lr", 0.001)])
        assert r2.converged  # 灰带停滞 → 收敛停机

    def test_meta_recursion_with_depth_cap(self):
        """元递归：改进 promote_margin 本身，深度有硬上限。"""
        loop = RSILoop(evaluator=lambda g: g.components.get("score", 0.0),
                       recursion_max_depth=2)
        g = make_genome(fitness=0.5, score=0.5)

        def widen_margin(c):
            c["promote_margin"] = 0.001   # 更敏感的晋升阈值

        meta_mod = Modification(target="promote_margin",
                                kind=ModificationKind.META,
                                apply=widen_margin, risk=0.1)
        # 元适应度：放大 margin 改进带来的收益，确保越过晋升灰带
        meta_eval = lambda gg: 10.0 * (0.02 - gg.components.get("promote_margin", 0.02))
        loop.recurse(g, [meta_mod], meta_evaluator=meta_eval)
        assert loop.promote_margin == pytest.approx(0.001)  # 元参数被改进

    def test_meta_invariants_scoped_to_meta_domain(self):
        """元层守恒核域隔离：系统不变量不作用于元基因组，反之亦然。"""
        core = InvariantCore()
        core.add("needs_lr", lambda g: "lr" in g.components)
        loop = RSILoop(evaluator=lambda g: g.components.get("lr", 0.0),
                       invariants=core)
        g = make_genome(fitness=0.5, lr=0.5)
        meta_core = InvariantCore()
        meta_core.add("margin_valid",
                      lambda g: 0.0 < g.components["promote_margin"] < 1.0)
        meta_mod = Modification("promote_margin", ModificationKind.META,
                                lambda c: c.__setitem__("promote_margin", 0.005),
                                risk=0.1)
        meta_eval = lambda gg: 10.0 * (0.02 - gg.components.get("promote_margin", 0.02))
        # 元基因组没有 "lr" 组件，但不应触发系统层不变量
        loop.recurse(g, [meta_mod], meta_evaluator=meta_eval,
                     meta_invariants=meta_core)
        assert loop.promote_margin == pytest.approx(0.005)
        # 系统层不变量仍未被污染
        assert any(name == "needs_lr" for name, _ in loop.invariants._checks)

    def test_audit_ledger_append_only(self):
        loop = RSILoop(evaluator=lambda g: g.components["lr"])
        g = make_genome(fitness=0.5, lr=0.5)
        loop.step(g, [mod("lr", 0.5), mod("lr", -0.6)])
        assert len(loop.audit_ledger) >= 2
        events = [e["event"] for e in loop.audit_ledger]
        assert "verdict" in events

    def test_snapshot_rollback_restores_state(self):
        loop = RSILoop(evaluator=lambda g: g.components["lr"])
        g = make_genome(fitness=0.5, lr=0.5)
        loop.step(g, [mod("lr", -0.6)])  # 回滚
        # 回滚后基因组组件未被污染
        assert g.components["lr"] == 0.5


# --------------------------------------------------------------- 联合闭环

class TestHealingEvolutionIntegration:
    def test_healing_antibody_feeds_evolution(self):
        """自愈沉淀的负相位抗体可被进化循环读取（共享 CRM）。"""
        mem = ComplexResonantMemory(dim=16)
        sm = SelfModel()
        box = _ProbeBox(0.1)
        sm.register("planner", box, baseline=1.0)
        engine = SelfHealingEngine(sm, mem, strategies={
            "planner": _SwitchRepair(box, succeed=False)})
        engine.heal_cycle()
        item = mem.get("repair:planner")
        assert item.state is Trit.NEG
        # 进化循环可将该抗体作为"不要往这个方向变异"的约束来源
        warns = mem.warnings(
            SelfHealingEngine._capability_vector("planner", 16))
        assert warns and "修复失败" in warns[0]
