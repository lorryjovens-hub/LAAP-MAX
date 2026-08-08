"""RSI 递归进化 + 自愈引擎 端到端演示。

场景：一个 agent 系统（用组件参数模拟）经历——
故障注入 → 自愈闭环 → 抗体沉淀 → 二次故障走快路径；
随后进入进化循环：候选修改 → 守恒核校验 → 三值裁决 → 晋升/回滚/冻结。
"""

import logging

from triphase import (
    ComplexResonantMemory,
    Genome,
    InvariantCore,
    Modification,
    ModificationKind,
    RSILoop,
    SelfHealingEngine,
    SelfModel,
    Trit,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def main() -> None:
    print("=" * 60)
    print("RSI 递归进化 + 自愈引擎 联合演示")
    print("=" * 60)

    # ================= 第一幕：自愈 =================
    print("\n── 第一幕：故障注入与自愈 ──")
    mem = ComplexResonantMemory(dim=16)
    sm = SelfModel()

    class ServiceBox:
        """模拟一个有内部状态的服务组件。"""
        def __init__(self):
            self.cache_valid = True
            self.connections = 10

        def probe_cache(self):
            return 1.0 if self.cache_valid else 0.2

        def probe_pool(self):
            return min(1.0, self.connections / 10.0)

    box = ServiceBox()
    sm.register("cache", box.probe_cache, baseline=1.0)
    sm.register("conn_pool", box.probe_pool, baseline=1.0)

    class CacheRepair:
        def repair(self, signal, diagnosis):
            print(f"    执行修复: 重建缓存（诊断={'有' if diagnosis else '无'}）")
            box.cache_valid = True
            return True

    engine = SelfHealingEngine(sm, mem, strategies={"cache": CacheRepair()})

    print("  [t=0] 健康基线:", {s.capability: s.trit.name for s in sm.sync()})
    box.cache_valid = False  # 故障注入
    print("  [t=1] 注入缓存故障")
    events = engine.heal_cycle()
    for e in events:
        print(f"  [t=1] {e.capability}: {e.trit_before.name} → {e.trit_after.name} "
              f"路径={e.path} 恢复={e.recovered}")

    box.cache_valid = False  # 同样的故障再次发生
    print("  [t=2] 同样故障再次发生")
    events = engine.heal_cycle()
    print(f"  [t=2] 路径={events[0].path}（抗体快路径，免诊断）恢复={events[0].recovered}")

    # ================= 第二幕：RSI 进化 =================
    print("\n── 第二幕：递归自我改进 ──")
    core = InvariantCore()
    core.add("temperature_bounded", lambda g: 0.0 <= g.components["temperature"] <= 1.0)
    core.add("has_system_prompt", lambda g: len(g.components["system_prompt"]) > 10)

    # 适应度：模拟"温度接近 0.3 且 prompt 含'三思'加分"的任务环境
    def evaluator(g: Genome) -> float:
        c = g.components
        score = 1.0 - abs(c["temperature"] - 0.3)
        if "三思" in c["system_prompt"]:
            score += 0.2
        return score

    loop = RSILoop(evaluator=core and evaluator, invariants=core,
                   promote_margin=0.02, human_gate=lambda m: True)
    genome = Genome(version=1, components={
        "temperature": 0.9,
        "system_prompt": "你是一个乐于助人的助手。",
    })
    genome.fitness = evaluator(genome)
    print(f"  初始基因组 v{genome.version} fitness={genome.fitness:.3f}")

    def set_temp(t):
        def apply(c):
            c["temperature"] = t
        return apply

    def append_prompt(s):
        def apply(c):
            c["system_prompt"] += s
        return apply

    candidates = [
        Modification("temperature", ModificationKind.HYPERPARAM,
                     set_temp(0.35), risk=0.2, rationale="接近最优温度"),
        Modification("system_prompt", ModificationKind.PROMPT,
                     append_prompt(" 输出前三思。"), risk=0.3, rationale="加入反思提示"),
        Modification("temperature", ModificationKind.HYPERPARAM,
                     set_temp(1.5), risk=0.2, rationale="（坏修改：温度越界）"),
        Modification("temperature", ModificationKind.HYPERPARAM,
                     set_temp(0.31), risk=0.2, rationale="微调"),
    ]
    genome, report = loop.step(genome, candidates)
    for v in report.verdicts:
        print(f"  修改[{v.modification.rationale}] → {v.trit.name}: {v.reason}")
    print(f"  最终基因组 v{genome.version} fitness={genome.fitness:.3f}")
    print(f"  违例计数={loop.violations} 冻结={loop.frozen} "
          f"审计条目={len(loop.audit_ledger)}")

    # ================= 第三幕：元递归 =================
    print("\n── 第三幕：元层进化（改进进化引擎自身参数）──")
    meta_mod = Modification(
        "promote_margin", ModificationKind.META,
        lambda c: c.__setitem__("promote_margin", 0.005),
        risk=0.1, rationale="更灵敏的晋升阈值")
    meta_eval = lambda gg: 10.0 * (0.02 - gg.components.get("promote_margin", 0.02))
    meta_core = InvariantCore()  # 元层守恒核：只管元参数域
    meta_core.add("margin_valid", lambda g: 0.0 < g.components["promote_margin"] < 1.0)
    loop.recurse(genome, [meta_mod], meta_evaluator=meta_eval,
                 meta_invariants=meta_core)
    print(f"  元层晋升后 promote_margin: {loop.promote_margin}")

    print("\n── 总账 ──")
    print(f"  记忆抗体库: {mem.stats()['by_state']}")
    print(f"  进化审计: {len(loop.audit_ledger)} 条（只增不改）")
    print(f"  系统健康: {sm.health().trit.name}")


if __name__ == "__main__":
    main()
