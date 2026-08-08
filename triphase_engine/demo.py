"""triphase 端到端演示：一个完整的"感知-推理-反思-记忆"闭环。

场景：agent 面对一个新任务，走完整管线——
路由 → 上下文装配 → 假设竞争 → 元认知裁决 → （必要时）反思 → 记忆沉淀。
"""

import logging

import numpy as np

from triphase import (
    ComplexResonantMemory,
    HypothesisEcosystem,
    MetacognitiveMonitor,
    PhaseState,
    SPIRReflector,
    Step,
    StepKind,
    Telemetry,
    TokenPipeline,
    Trit,
)
from triphase.metacognition import MetacogAction

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
rng = np.random.default_rng(7)
DIM = 16


def rand_vec():
    v = rng.standard_normal(DIM) + 1j * rng.standard_normal(DIM)
    return v / np.linalg.norm(v)


def main() -> None:
    print("=" * 60)
    print("TriPhase Agent 端到端闭环演示")
    print("=" * 60)

    # ---------- 基础设施 ----------
    memory = ComplexResonantMemory(dim=DIM)
    pipeline = TokenPipeline(memory, deterministic_executor=lambda s: "tool-result")
    monitor = MetacognitiveMonitor()

    # 预置经验：两条有效经验 + 一条已证伪路径（负相位抗体）
    v_good = rand_vec()
    memory.store(v_good, payload="方案A：先建索引再批量写入", key="expA",
                 initial_evidence=0.9)
    v_bad = rand_vec()
    memory.store(v_bad, payload="方案B：直接全表扫描 UPDATE（已证伪，锁表）",
                 key="expB", initial_evidence=-0.95)

    # ---------- Phase 0: 路由 ----------
    print("\n[Phase 0] 三值路由")
    steps = [
        Step("格式化输出", StepKind.FORMAT, params={"fmt": "json"}),
        Step("设计迁移方案", StepKind.REASONING, query_vector=v_good + 0.05 * rand_vec()),
        Step("尝试危险路径", StepKind.REASONING, query_vector=v_bad + 0.03 * rand_vec()),
    ]
    for s in steps:
        d = pipeline.route(s)
        print(f"  {s.name:<12} → {d.route.name:<8} {d.reason}"
              + (f" | 抗体警告: {d.warnings[0]}" if d.warnings else ""))

    # ---------- Phase 1: 上下文装配 ----------
    print("\n[Phase 1] 相位亲和度上下文装配（预算 80 token）")
    ctx, used = pipeline.assemble_context(v_good, token_budget=80)
    print(f"  注入 {used} token:\n    " + ctx.replace("\n", "\n    "))

    # ---------- 假设生态：发散 → 竞争 ----------
    print("\n[假设生态] 发散-竞争")
    eco = HypothesisEcosystem(
        base_coupling=2.0,
        on_falsified=lambda h: memory.store(
            rand_vec(), payload=f"证伪归因: {h.falsified_reason}",
            key=f"falsified:{h.id}", initial_evidence=-0.9),
        rng=np.random.default_rng(3),
    )
    h1 = eco.add(phase=0.2, strength=0.8, payload="增量迁移")
    h2 = eco.add(phase=0.1, strength=0.6, payload="影子表迁移")
    h3 = eco.add(phase=3.5, strength=0.7, payload="停机全量迁移")
    eco.link(h1.id, h2.id, coupling=0.8)    # 协同
    eco.link(h1.id, h3.id, coupling=-1.2)   # 互斥
    eco.diverge(steps=30)
    print(f"  发散后分散度: {eco.dispersion():.3f}")
    eco.falsify(h3.id, "业务不允许停机窗口")
    out = eco.compete(steps=400)
    print(f"  竞争后分散度: {out.dispersion:.3f} | 主导 {len(out.dominant)} "
          f"悬置 {len(out.pending)} 证伪 {len(out.falsified)}")

    # ---------- 元认知裁决 ----------
    print("\n[元认知] 双振子干涉裁决")
    conclusion = PhaseState(magnitude=0.85, phase=0.15)  # 对象层：倾向方案A
    telemetry = Telemetry(
        retrieval_hit_rate=0.9,
        hypothesis_dispersion=out.dispersion,
        unverified_dependency_ratio=0.1,
        negative_conflicts=0,
    )
    verdict = monitor.assess(conclusion, telemetry)
    print(f"  裁决: {verdict.action.value} | 干涉值 {verdict.interference:+.3f}")
    print(f"  依据: {verdict.rationale}")

    # ---------- SPIR 反思（构造一个需要反思的场景） ----------
    print("\n[SPIR] 反思回路（元层反相触发）")
    bad_verdict = monitor.assess(
        conclusion,
        Telemetry(retrieval_hit_rate=0.8, hypothesis_dispersion=0.1,
                  negative_conflicts=3),
    )
    print(f"  冲突裁决: {bad_verdict.action.value}")

    if bad_verdict.action is MetacogAction.REFLECT:
        class Level:
            def __init__(self, name, stable):
                self.name, self._stable = name, stable

            def invert_and_run(self, c):
                if self._stable:
                    return PhaseState(0.7, 2.2)   # 修正后收敛到新相位
                return PhaseState(c.magnitude, c.phase + 1.1)

        spir = SPIRReflector(
            [Level("行动参数", False), Level("策略", True)],
            on_lesson=lambda msg, s: memory.store(
                rand_vec(), payload=msg, key="lesson:1", initial_evidence=0.7),
        )
        result = spir.reflect(conclusion)
        print(f"  病灶层: {result.culprit_name} | 收敛: {result.resolved}")
        print(f"  反思沉淀入记忆: {memory.get('lesson:1') is not None}")

    # ---------- 状态沉淀 + 管线总账 ----------
    print("\n[总账]")
    pipeline.record_outcome(steps[1], "采用增量迁移方案", v_good, success=True)
    st = pipeline.stats
    print(f"  步骤 {st.steps_total} | LLM 调用 {st.llm_calls} "
          f"| 绕过 {st.bypassed} | 短路 {st.short_circuited}")
    print(f"  估算节省 token: {st.estimated_tokens_saved}")
    print(f"  记忆库: {memory.stats()}")


if __name__ == "__main__":
    main()
