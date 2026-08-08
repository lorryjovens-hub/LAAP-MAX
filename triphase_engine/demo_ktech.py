"""KDA / AttnRes / LatentMoE 在 harness 工程中的运用演示。

模拟一个长时程 agent：1000 步执行，对比三种记忆/路由策略——
1. KDA 定态记忆 vs 全量上下文（内存对比）；
2. AttnRes 阶段检索 vs 全量历史堆叠（token 对比）；
3. 分位数均衡路由 vs 无均衡路由（专家负载对比）。
"""

import logging

import numpy as np

from triphase import (
    HybridMemoryScheduler,
    KimiDeltaAttention,
    LatentMoE,
    MetacogAction,
    MetacogVerdict,
    PhaseState,
    StageResidualMemory,
)

logging.basicConfig(level=logging.WARNING)

rng = np.random.default_rng(42)
LINE = "─" * 60


def main() -> None:
    print("=" * 60)
    print("Kimi K3 黑科技 × harness 工程化演示")
    print("=" * 60)

    # ---------- 1. KDA 定态记忆 ----------
    print(f"\n{LINE}\n【KDA】1000 步长时程 agent 的工作记忆\n{LINE}")
    kda = KimiDeltaAttention(x_dim=32, d_k=64, d_v=32,
                             rng=np.random.default_rng(1))
    sched = HybridMemoryScheduler(kda, exact_lookup=lambda x: "<精确回查>",
                                  ratio=3)
    uncertain = MetacogVerdict(MetacogAction.SEEK_INFO, 0.0,
                               PhaseState(0.5, 0), PhaseState(0.5, 0), "t")
    for i in range(1000):
        # 每 173 步注入一次"不确定"事件，验证元认知触发
        v = uncertain if i % 173 == 0 else None
        sched.access(rng.standard_normal(32), verdict=v)

    est = sched.compression_estimate(per_token_kv_bytes=256, history_len=1000)
    print(f"  全量 KV cache : {est['kv_cache_bytes']/1024:>8.1f} KB（随历史线性增长）")
    print(f"  KDA 定态记忆  : {est['kda_state_bytes']/1024:>8.1f} KB（恒定）")
    print(f"  压缩比        : {est['ratio']:>8.1f}×")
    print(f"  访问分布      : {sched.stats}")
    print(f"  精确回查占比  : {sched.exact_ratio:.1%}（周期 3:1 + 元认知触发）")

    # ---------- 2. AttnRes 阶段检索 ----------
    print(f"\n{LINE}\n【AttnRes】8 阶段管线的上下文装配\n{LINE}")
    srm = StageResidualMemory(dim=32, temperature=0.5)
    stages = ["感知", "检索", "假设", "推理", "验证", "反思", "沉淀", "规划"]
    query = rng.standard_normal(32)
    for i, name in enumerate(stages):
        # 让"推理"与查询最相关
        v = query + 0.05 * rng.standard_normal(32) if name == "推理" \
            else rng.standard_normal(32)
        srm.push(name, v, f"<{name}产出>", token_cost=150 + i * 30)
    ctx = srm.compose(query, token_budget=400)
    print(f"  全量堆叠成本  : {ctx.tokens_if_concat} token")
    print(f"  AttnRes 检索  : {ctx.tokens_used} token"
          f"（省 {1 - ctx.tokens_used/ctx.tokens_if_concat:.0%}）")
    print(f"  入选阶段      : "
          + ", ".join(f"{s.stage}(w={w:.2f})" for s, w in ctx.selected))

    # ---------- 3. LatentMoE 分位数均衡路由 ----------
    print(f"\n{LINE}\n【LatentMoE】12 个领域专家，每次激活 3 个\n{LINE}")
    expert_names = ["生物医学", "金融", "法律", "政务", "代码", "数学",
                    "检索", "写作", "翻译", "数据分析", "规划", "审计"]

    def make_star_biased_moe(balanced: bool) -> LatentMoE:
        moe = LatentMoE(experts={n: (lambda x: x) for n in expert_names},
                        top_k=3, rng=np.random.default_rng(2))
        if not balanced:
            moe.router.route = _raw_route(moe.router)  # 无均衡对照
        return moe

    def _raw_route(router):
        def route(x):
            s = router.scores(x)
            s[0] = 0.99  # "生物医学"是明星专家
            top = np.argsort(-s)[: router.top_k]
            w = s[top] / s[top].sum()
            for i in top:
                router.loads[i] += 1
            return [(int(i), float(wj)) for i, wj in zip(top, w)]
        return route

    moe_raw = make_star_biased_moe(balanced=False)
    moe_bal = LatentMoE(experts={n: (lambda x: x) for n in expert_names},
                        top_k=3, rng=np.random.default_rng(2))
    # 均衡组也给"生物医学"明星分
    orig_scores = moe_bal.router.scores
    moe_bal.router.scores = lambda x: np.where(
        np.arange(12) == 0, 0.99, orig_scores(x))

    for _ in range(300):
        x = rng.standard_normal(32)
        moe_raw(x)
        moe_bal(x)

    raw_loads = moe_raw.router.loads / moe_raw.router.loads.sum()
    bal_loads = moe_bal.router.loads / moe_bal.router.loads.sum()
    print(f"  {'专家':<6}{'无均衡':>10}{'分位数均衡':>12}")
    for i, n in enumerate(expert_names[:6]):
        print(f"  {n:<8}{raw_loads[i]:>9.1%}{bal_loads[i]:>11.1%}")
    print(f"  负载变异系数 CV: {moe_raw.router.load_cv:.2f}（无均衡）"
          f" → {moe_bal.router.load_cv:.2f}（分位数均衡）")
    print(f"  激活专家数    : {(moe_raw.router.loads > 0).sum()} → "
          f"{(moe_bal.router.loads > 0).sum()} / 12（无专家饿死）")


if __name__ == "__main__":
    main()
