# TriPhase — 三值/复相位 AGI Agent 框架参考实现

把平衡三进制 {-1, 0, +1} 与三次单位根相位（欧拉公式）贯穿到 Agent 的
记忆、推理、反思、工程纪律、因果推断、推理成本管线、自愈与递归进化的
完整参考实现。纯 NumPy 依赖，107 项单元测试全覆盖。

## 安装与运行

```bash
pip install -e .          # 或 pip install -e .[dev]
pytest tests/ -v          # 107 项测试
python demo.py            # 感知-推理-反思-记忆闭环演示
python demo_rsi.py        # RSI 递归进化 + 自愈引擎演示
python demo_grounding.py  # 四领域核反幻觉演示
python demo_ktech.py      # KDA/AttnRes/LatentMoE harness 演示
```

## 模块地图

| 模块 | 对应设计 | 关键机制 |
|---|---|---|
| `core` | 代数底座 | `Trit` 三值、`PhaseState` 复相位态、相位干涉、圆方差 |
| `memory` | CRM 复数谐振记忆 | 三值巩固循环、谐振检索 Re⟨m,q⟩、**负相位抗体**（证伪记忆不删除）、去相干遗忘 + 再认优势 |
| `hypothesis` | 假设生态 | Kuramoto 发散/竞争双模、证据边协同/互斥、**证伪负锚点**（固定排斥，不作全局吸引子） |
| `metacognition` | 元认知对偶层 | 对象振子 × 过程遥测振子干涉；正交态 = **幻觉检测信号**；反相触发反思 |
| `reflection` | SPIR 反思回路 | 分层相位反演 + 收敛判据（Δθ<ε）+ 深度熔断（退入未定扇区求信息）+ 病灶归因沉淀 |
| `codegraph` | 三值代码图 | 验证态守恒（**硬约束**：未验证依赖禁止完成）、改动爆炸半径（扰动沿依赖边传播） |
| `causal` | 因果张量引擎 | 复 CP-ALS、复多线性回归核、do-算子（图手术+解析重算）、反事实（溯因闭式解）、跨环境不变性三值筛选 |
| `pipeline` | PGTP 省 token 管线 | 三值路由（绕过/短路/全量）、亲和度上下文装配、负相位一行式警告注入、token 总账 |
| `harness` | 注意力 harness | 三值 KV 缓存（满精度→三值量化→驱逐入记忆）、相位前缀部分失效、元认知预算账户 |
| `worldmodel` | 相位世界模型 | 近酉动力学（误差限于相位累积，模长不爆炸）、三值不可能性检测 |
| `selfheal` | 自愈引擎 | 自我模型（能力图谱）、基线×观测双振子干涉异常检测、**抗体快路径**（已知修复模式免诊断复用）、修复-复测硬闭环、失败负相位沉淀 |
| `rsi` | RSI 递归进化引擎 | 版本化基因组 + 谱系、三值适应度裁决（**灰带不晋升**，抗噪声进化）、**不变量核**（近酉子空间，安全约束不进入搜索空间）、快照原子回滚、违例冻结、人工门、元递归（元参数域隔离 + 深度硬上限）、只增不改审计账 |
| `grounding` | 跨领域反幻觉基座 | **证明携带生成（PCG）**：声明级三值裁决、领域硬不变量（违反即结构性拒绝）、弃权是一等输出、幻觉负相位抗体（精确键 + 保守相似阈值，防误伤）、来源信任分层、遥测直通元认知；内置生物医学/金融/法律/政务四个参考领域核 |
| `kda` | KDA 定态工作记忆 | Kimi Delta Attention 推理态实现：逐通道遗忘门 + delta 规则（同键覆写非叠加）、O(1) 定态内存、3:1 混合调度（周期 + **元认知触发**精确回查） |
| `attnres` | AttnRes 阶段检索 | 深度轴注意力残差：跨管线阶段按需检索替代全量历史堆叠（demo 实测省 81% token），高温极限退化为标准残差 |
| `latentmoe` | 分位数均衡 MoE 路由 | Stable LatentMoE 式稀疏激活 + **Quantile Balancing**（运行分位数归一选择基线，无人工均衡超参、无专家饿死） |

## 一个最小闭环

```python
import numpy as np
from triphase import (ComplexResonantMemory, TokenPipeline, Step, StepKind,
                      MetacognitiveMonitor, Telemetry, PhaseState)

mem = ComplexResonantMemory(dim=16)
q = np.random.default_rng(0).standard_normal(16) + 1j*np.random.default_rng(1).standard_normal(16)
mem.store(q/np.abs(q).sum(), payload="已证伪方案X", key="bad", initial_evidence=-0.9)

pipe = TokenPipeline(mem, deterministic_executor=lambda s: "ok")
d = pipe.route(Step("试方案X", StepKind.REASONING, query_vector=q))
# → Trit.NEG，附带 [AVOID] 已证伪方案X —— 不再浪费 token 重新探索

v = MetacognitiveMonitor().assess(
    PhaseState(0.95, 0.0),                       # 对象层很自信
    Telemetry(retrieval_hit_rate=0.0, hypothesis_dispersion=0.9,
              unverified_dependency_ratio=0.9))  # 但过程毫无支撑
# → SEEK_INFO：幻觉检测信号
```

## K3 架构技术 × harness 工程化

把模型层的三项架构创新上移到 agent harness 层（对应关系即设计命题）：

| 模型层（Kimi K3） | harness 层（本包） | 实测（demo_ktech.py） |
|---|---|---|
| KDA 定态记忆，KV cache −75% | agent 工作记忆从"增长上下文"改为定态递归记忆 | 1000 步 15.6× 内存压缩 |
| 3:1 KDA:MLA 混合层 | 周期 + 元认知触发的精确回查调度 | 精确回查占比 25.5%（3:1 + 6 次触发） |
| AttnRes 深度轴选择检索 | 跨阶段 AttnRes 上下文装配替代全量堆叠 | 2040 → 390 token（省 81%） |
| Stable LatentMoE + Quantile Balancing | 专家/工具/领域核的分位数均衡路由 | 明星专家 33.3% → 4.2%，CV 0.92 → 0.24 |

要点：K3 用架构手段解决的问题（定态记忆、深度检索、负载均衡），
在 harness 层以策略手段同构复现——**不改动模型权重，收益当日可得**。

## 反幻觉范式：从 RAG 到证明携带生成（PCG）

RAG 按相似度接地，不按有效性接地；没有"不知道"，被迫流畅地编造。
PCG 的反命题：**生成物必须携带接地证书才能出厂**。

```
生成文本 ──► 原子声明抽取 ──► ┌─ 0. 幻觉抗体快路径（已知模式免验证拦截）
                              ├─ 1. 领域硬不变量（违反 → 硬拒绝，非警告）
                              └─ 2. 可执行验证器（查表/计算/规则 → 三值）
                                        │
              ┌───────────────────────────┼────────────────────────┐
        任何 REFUTED                 UNVERIFIED 超阈值            全部接地
              ▼                           ▼                        ▼
           REJECT                     ABSTAIN（证据不足）        PASS + 证书
        （结构性禁止输出）          （不流畅地编，坦然说不知道）  （证据链随文出厂）
```

- **领域核协议**：`verify_claim / invariants / trust_of` 三接口领域无关，
  内核版本化，生产环境接真实数据库（DrugBank / EDGAR / 裁判文书库 / 法规库）；
- **幻觉是资产**：证伪声明沉淀为负相位抗体，同类幻觉终身免疫；
- **与元认知打通**：接地遥测直接驱动 MetacognitiveMonitor，
  任何证伪可配置为强制反思（conflict_cap=1）。

## RSI 与自愈的范式设计

**进化是复平面上的受控轨道，守恒是硬结构。**

```
            ┌──────── 不变量核（酉子空间：只旋转，不增减） ────────┐
            │  安全约束不进入搜索空间，违例硬拒绝，重复违例冻结    │
            └──────────────────────┬─────────────────────────────┘
                                   │ 每次变异前后强制校验
   提议 ──► 沙盒变异 ──► 三值裁决 ─┼─► +1 晋升（增益 > 灰带）
   (假设生态)  (快照先行)           ├─►  0 保留观察（灰带 = 抗噪声）
                                   └─► -1 回滚 + 负相位抗体沉淀
```

- **自愈 = 指向自身的元认知**：健康是基线振子与观测振子的干涉，
  同相健康、正交退化、反相危重；修复成功沉淀 POS 抗体（下次免诊断
  快路径），失败**必须**沉淀 NEG 抗体并升级——禁止静默带病运行；
- **灰带抗噪**：适应度波动在 ±margin 内不晋升也不回滚，防止在噪声上"进化"；
- **元递归无特权**：引擎自身参数（晋升阈值、风险阈值）作为 META 类
  修改进入同一套守恒核 + 三值裁决，元层有独立的守恒核域，深度硬上限；
- **可问责**：审计账只增不改；高风险修改必须过人工门，无门即冻结。

## 设计原则

1. **三值即相位**：{-1,0,+1} ↔ 三次单位根 {0°, 120°, 240°}，离散逻辑与连续动力学统一；
2. **未定是一等状态**：挂起判断、未验证依赖、未决因果边都有显式表示；
3. **证伪是资产**：所有失败以负相位形式沉淀为可复用的"认知抗体"；
4. **守恒律硬约束**：工程纪律在表示结构层强制执行，而非 prompt 软约束；
5. **可证伪落地**：每个模块都有独立可分离验证的基准（见各测试用例）。

## 已知边界

- `causal.complex_cp_als` 为参考实现（显式 Khatri-Rao），适合中小规模；
  生产大规模张量应换 TT 分解或 GPU 实现；
- `causal.LinearSCM` 的闭式溯因依赖线性可逆假设，非线性情形需换数值反演；
- 元认知判据的阈值（`align_cos` / `min_meta_strength`）是设计选择，
  应在真实 agent trace 上校准。
