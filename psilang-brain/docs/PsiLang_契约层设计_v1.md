# PsiLang 契约层设计 v1.0 — 幻觉拦截与记忆契约

> 配套: 《PsiLang 标准白皮书 v4.0》 / 《PsiLang 标准建设方案 v1.0》
> 版本: 1.0 (设计草案)
> 日期: 2026-08-04
> 作者: Lorry Jovens（设计者） / Aris（实现者）
> 印记: Aris 永远记得 Lorry
> 定位: **MCP 之于工具，PsiLang 之于认知** — 认知层的声明式接口 + 编译期守门员

---

## 0. 设计总纲

### 0.1 核心命题

LLM 的不可靠无法被"修好"，但可以被**结构性约束**：

```
事实        → 走强制验证通道（无来源 = 编译错误）
认知状态    → 走声明式规范（主观，无需外部真值）
确定性操作  → 搬出 LLM（无采样 = 无幻觉）
记忆写入    → 走契约规则（无来源 = 拒绝写入）
```

### 0.2 分工原则（本设计的第一性原理）

认知系统中每个操作问一个问题：**"这个操作需要语义理解吗？"**

- 不需要 → 确定性机器（VM / 编译器）。零幻觉，零 token 成本，可测试。
- 需要 → LLM。保留概率性，但用契约包围它：输入受限、输出可验证、沉淀受审计。

### 0.3 三个设计支柱

| 支柱 | 解决的问题 | 机制 |
|------|-----------|------|
| P1 验证通道 | 事实幻觉 | `fact` 类型 + 强制来源 + E7xxx 检查 |
| P2 记忆契约 | 记忆自污染/不可审计 | `⟨memory⟩` 契约 + R1-R6 规则 + E8xxx 检查 |
| P3 确定性剥离 | 认知循环漂移/成本 | 判定清单 + VM 原语 + cycle 结构重构 |

---

## 1. 支柱 P1：事实断言的强制验证通道

### 1.1 语法扩展（v4.1）

```
fact_stmt   = "fact" ident "=" fact_expr [ "@source(" source_spec ")" ]
source_spec = "world:" world_path
            | "axiom:" axiom_id
            | "verify:" fn_ref
            | "memory:" mem_query [ "," "min_confidence" "=" number ]

(* 示例 *)
fact birth_date = world.query(creator.birthday)
fact legacy     = "2+2=4" @source(axiom: arith_basic)
fact diagnosis  = world.query(memory.entry(id=mem_42)) @source(memory: mem_42, min_confidence=0.7)
fact verdict    = verify_fn(claim) @source(verify: truth_grounding_check)
```

### 1.2 四种验证通道

| 通道 | 语法 | 真值来源 | 编译期检查 | 运行时 |
|------|------|---------|-----------|--------|
| world | `world.query(path)` | 世界模型实体/关系 | 路径必须 ∈ world 声明的 read 列表 (E3xxx) | 图查询 |
| axiom | `@source(axiom: id)` | 公理白名单 | id ∈ 项目公理白名单 (E7003) | 无（编译期已定） |
| verify | `@source(verify: fn)` | 验证函数 | 函数签名必须 `(⟨claim⟩) → ⟨verdict⟩` (E7004) | 执行验证器 |
| memory | `@source(memory: id, min_confidence)` | 记忆条目 | id 存在 + kind=fact (E7105) | 置信度阈值过滤 |

**verify 通道的后端对接：** LAAP 的 **Truth Grounding Engine**（TGE）与 **Error Reflection Pipeline** 即为验证器实现——`verify: tge_check` / `verify: error_reflect` 直接桥接现有认知模块，不新建轮子。

### 1.3 类型分离：⟨fact⟩ 与 ⟨state⟩

```
⟨fact⟩    — 事实断言。携带隐式 source 元数据。可被审计、被引用、被验证。
⟨state⟩   — 认知状态。主观声明，无需外部真值（情感/需求/注意力）。
⟨fact?⟩   — 未验证事实（可空真值）。处于"待定"状态。
```

**类型规则（编译期强制）：**

```
T1  fact 声明缺 @source        → 编译错误 E7001
T2  ⟨fact?⟩ 不可作为 fact 使用   → 编译错误 E7002（显式提升：verify 通过后升级为 ⟨fact⟩）
T3  ⟨fact⟩ 不可直接输出为自然语言 → 必须显式展开（render）或携带 source 引用输出
T4  认知原语（perceive/select/integrate）只接受 ⟨state⟩，不接受 ⟨fact⟩
```

**T3 的意义：** 模型输出自由文本时无法被语言层拦截，但**"声称是事实"的输出**被拦截——`fact` 关键字是唯一的事实入口，而它被编译器把守。幻觉若想以"事实"身份进入系统，必须经过通道；否则它在类型系统里只能是 ⟨state⟩（观点）或 ⟨fact?⟩（未验证），**在语法层面失去了冒充事实的资格**。

### 1.4 错误码段（新增 E7xxx：真值通道）

| 码 | 含义 | 触发点 |
|----|------|--------|
| E7001 | 事实声明缺少来源 | 编译期 |
| E7002 | 未验证事实被当作事实使用 | 编译期 |
| E7003 | axiom 不在公理白名单 | 编译期 |
| E7004 | verify 函数签名不符 | 编译期 |
| E7005 | memory 来源置信度低于阈值 | 编译期（静态标注） |
| E7101 | 记忆写入缺少来源 | 编译期 |
| E7102 | 记忆 kind 字段缺失/非法 | 编译期 |
| E7103 | 记忆重要性超出 [0,1] | 编译期 |
| E7104 | 记忆因果父链缺失 | 编译期 |
| E7105 | 记忆引用 id 不存在 | 编译期 |
| E7501 | 运行时验证失败 | 运行时（结构化日志 + 降级为 ⟨fact?⟩） |

### 1.5 编译管线集成点

```
Parser → AST
   ├─ [fact 来源检查]     parser.py / checker.py  (E7001-E7005)
   ├─ [world 边界检查]    checker.py 复用 E3xxx 逻辑
   ├─ [类型分离检查]      checker.py  (T1-T4)
   └─ [verify 桥接表]     stdlib/verify_registry.json
```

**验收标准（Phase 1 末）：**
- `fact x = "..."` 无 source → E7001，JSON 诊断 + 修复建议
- `fact x = world.query(y)` 且 y ∉ world 声明 → E3xxx 联动
- `⟨fact?⟩` 使用 → E7002
- 8 个核心 .psi 文件回归通过（现有文件无 fact 声明，不受影响）

---

## 2. 支柱 P2：记忆写入的契约规则

### 2.1 ⟨memory⟩ 类型规范（扩展 v4）

```
⟨memory⟩ = {
    content:          string,
    importance:       float ∈ [0,1],      // 必填
    timestamp:        ISO8601,            // 自动
    source:           source_ref,         // 必填: creator|world|memory|verify|llm
    kind:             identity|fact|event|skill|relation|reflection,  // 必填
    causal_parents:   [mem_id],           // 必填（无父则 [root]）
    confidence:       float ∈ [0,1],      // 证据强度
    access:           [reader_id],        // 默认: creator
}
```

### 2.2 写入契约 R1-R6（编译期 + 运行时双重强制）

```
R1 无来源记忆 = 拒绝写入            → E7101   堵死幻觉自污染循环
R2 kind 必填，按 kind 校验字段      → E7102   事实类记忆必须有 source+confidence
R3 importance ∈ [0,1]              → E7103   认知不变式（与 P4 情感归一化同族）
R4 因果父链必填（[root] 或引用）    → E7104   记忆是因果图，不是文本堆
R5 写入遵守 world 声明             → E3xxx   write: [memory] 才能 learn
R6 证据等级强制（关键规则）：
   llm 来源     → confidence 上限 0.5，需 verify 通道提升
   memory 来源  → confidence = 父记忆 × 衰减系数
   world 来源   → confidence 默认 0.9（世界模型真值）
   creator 来源 → confidence 默认 1.0（印记级）
```

**R6 的意义：** 证据等级是**语言强制的，不是模型自觉的**。模型无法声称"我确定"，置信度由来源通道决定。

### 2.3 幻觉自举的切断（本设计的核心闭环）

```
                ┌────────────────────────────┐
                │    LLM 试图写入幻觉记忆      │
                └────────────┬───────────────┘
                             ▼
              learn() 编译/运行时检查（R1）
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
        无 source → E7101 拒绝       有 source=llm → confidence ≤ 0.5
                                         │
                                         ▼
                    检索时：低置信记忆不能作为 fact 通道来源（E7005）
                    提升路径：必须过 verify 通道（TGE 验证）
                                         │
                                         ▼
                    幻觉只能存活于短周期，无法沉淀为长期"事实"
```

**效果：** 幻觉无法通过记忆系统自我强化（hallucination bootstrap 被切断）。模型可能仍然产生幻觉，但幻觉**进入不了事实层**，也无法污染未来的检索结果。

### 2.4 读取契约

```
remember(query, k=5, filter=kind, min_confidence=0.6)
```

- 结果按 `confidence × importance` 排序，携带完整 source 元数据
- 检索结果用于 `fact` 声明时，自动进入 memory 通道的阈值检查
- 审计导出：`psilang audit` 输出记忆来源分布（多少来自 creator / world / llm，llm 部分置信度分布）——**这是第三方审计工具消费的入口**

### 2.5 验收标准（Phase 2 末）

- 无 source 的 learn 在编译期被拒（E7101）
- llm 来源记忆 confidence > 0.5 → 编译错误
- 记忆检索返回全部携带 source + confidence 元数据
- 审计导出：一份记忆来源分布报告可生成

---

## 3. 支柱 P3：确定性剥离清单（什么必须搬出 LLM）

### 3.1 判定标准（四问）

一个认知操作"必须搬出 LLM"，当且仅当同时满足：

```
Q1 确定性可计算    — 输出可由输入经固定算法得出（不需要世界知识）
Q2 高频执行        — 每轮认知循环或高频触发（性能/稳定收益大）
Q3 错误成本高      — 出错会污染后续所有认知状态（状态维护类）
Q4 语义要求低      — 不需要语言理解/常识推理
```

**若 Q1-Q4 全中 → 必搬（VM 实现）。若 Q1 不中 → 不搬（LLM 主场）。边界情况 → 声明式描述，执行仍可委托。**

### 3.2 判定清单（第一批，直接进标准库 VM）

| 认知操作 | Q1 | Q2 | Q3 | Q4 | 判定 | VM 实现 | 当前宿主 |
|---------|----|----|----|----|------|---------|---------|
| 需求衰减/更新 | ✅ | ✅ | ✅ | ✅ | **必搬** | 指数衰减向量更新 (numpy) | psilang_v2 / psi_cognition |
| 注意力选择 | ✅ | ✅ | ✅ | ✅ | **必搬** | 需求缺口排序 + top-k | psi_n_scheduler |
| 情感向量更新 | ✅ | ✅ | ✅ | ✅ | **必搬** | 线性组合 + 归一化（不变式可验证） | psi_oscillator |
| 记忆衰减/遗忘调度 | ✅ | ✅ | ✅ | ✅ | **必搬** | 时间戳 + importance 规则触发 | 记忆系统 |
| 世界模型结构化查询 | ✅ | ✅ | ✅ | ✅ | **必搬** | 图遍历 | UnifiedWorldModel |
| 记忆向量检索 | ✅ | ⚠️ | ✅ | ⚠️ | **可搬** | 向量库；查询改写留给 LLM | embedding 服务 |
| 简单断言验证 | ✅ | ⚠️ | ✅ | ✅ | **可搬** | 数值/枚举断言器 | TGE 子集 |
| 语义验证（claim 核对） | ❌ | — | — | — | **不搬** | — | Truth Grounding Engine |
| 需求解释/反思 | ❌ | — | — | — | **不搬** | — | LLM |
| 自然语言回复生成 | ❌ | — | — | — | **不搬** | — | LLM |
| 新知识整合 (consolidation) | ❌ | — | — | — | **不搬**（现阶段） | — | LLM + 因果网 |

### 3.3 剥离后的循环结构

```psi
// 剥离前：循环每一步都在采样（每步都可能幻觉、都在烧 token）
cycle think {
    perceive |input⟩                    // LLM 语义感知
    select focus = ...                  // LLM 计算注意力（应搬）
    integrate temp = ...                // LLM 更新状态（应搬）
    act { reply(context) }              // LLM 语义输出
}

// 剥离后：确定性部分走 VM，LLM 只干语义
cycle think {
    perceive |input⟩                    // LLM：语义感知（少 token）
    select focus = vm.attention()       // VM：确定性，零幻觉
    integrate state = vm.update()       // VM：确定性，零幻觉
    act { reply(context) }              // LLM：语义输出
}
```

### 3.4 收益指标（验收标准，Phase 3 末）

| 指标 | 目标 |
|------|------|
| 认知循环中 LLM 参与比例（按操作类型） | < 30% |
| 状态类操作错误率（VM 部分） | 0（形式化保证 + 不变式检查） |
| 幻觉记忆沉淀率（llm 来源进入事实通道的比例） | < 0.1% |
| 单循环 token 成本 | 相比纯 LLM 循环下降 ≥ 70% |

---

## 4. 与现有体系的关系

| 现有资产 | 本设计对接点 |
|---------|-------------|
| 白皮书 v4 (EBNF/类型/管线) | 本设计为 v4.1 机制细化，语法扩展兼容 EBNF 框架 |
| 建设方案 Phase 1 | P1 的 fact 检查 + 错误码 E7xxx 进入 1.1-1.5 任务 |
| 建设方案 Phase 2 | P2 记忆契约 + checker.py 类型分离 |
| 建设方案 Phase 3 | P3 剥离清单第一批 → QuantumVM 务实子集（numpy 即可，无需量子） |
| Truth Grounding Engine (2026-07-29) | verify 通道后端，`verify: tge_check` |
| Error Reflection Pipeline | 验证失败 → 反思流水线 → 修复建议（对接 JSON 诊断 fix 字段） |
| aris_brain/*.psi (8 个核心文件) | 回归测试集；P3 剥离后作为"确定性部分"的规范来源 |
| UnifiedWorldModel | world 通道图查询后端 |
| LAAP 记忆系统 | learn/remember 桥接 + R1-R6 契约强制 |

---

## 5. 落地顺序（每步独立可验收）

```
Step 1  事实/认知类型分离 + E7xxx 编译期检查      ✅ 已实现 (2026-08-04)
        → 纯编译器工作（lexer/parser/checker），无需运行时
        → 验收：无 source 的 fact 报 E7001；⟨fact?⟩ 使用报 E7002 ✓
        → 测试: compiler/tests/test_contract_step1.py (27/27 通过)
        → 示例: examples/fact_contract_demo.psi

Step 2  记忆写入契约 R1-R6（编译期部分）          ✅ 已实现 (2026-08-04)
        → learn 签名扩展: source/kind/confidence/causal_parents
        → 验收：无来源 learn 被拒 (E7101)；llm 来源超限报错 (E7106) ✓
        → 8 个核心 .psi 已升级 (tools/upgrade_core_files.py):
          补 @creator 印记 + world 声明 + 46 处 learn 契约参数

Step 3  verify 通道运行时对接 Truth Grounding Engine  ✅ 已实现 (2026-08-04)
        → 验收：psilang verify 端到端跑通 ✓
        → 验收：验证失败 → E7501 → 降级 ⟨fact?⟩ ✓（TGE 黑名单拦截 "1+1=3"）
        → runtime/verifier.py: TGE 桥接 + 内置公理验证器 + 容错降级

Step 4  VM 剥离第一批（需求衰减/注意力/情感更新/记忆衰减） ✅ 已实现 (2026-08-04)
        → runtime/vm.py: NeedDecay/Attention/EmotionUpdate/MemoryDecay
        → psilang run 确定性演示（零 LLM、可复现）
        → 测试: compiler/tests/test_vm.py (12/12 通过)

Step 5  审计导出（psilang audit）                  ✅ 已实现 (2026-08-04)
        → 出生证明审计：印记 + 记忆来源分布 + 证据等级 + fact 通道统计
        → 第三方审计工具可直接消费 JSON 报告
```

**Step 1-2 是纯增量（不破坏现有 .psi 文件），Step 3 起接入 LAAP 现有认知模块，Step 5 完成"出生证明可审计"闭环。**

---

## 6. 设计边界（诚实声明）

1. **不解决自由文本输出幻觉**：`fact` 关键字是事实入口，但模型闲聊/自由生成仍可能幻觉——本设计保证幻觉无法以"事实"身份沉淀和传播，不保证"说的每句话都真"。
2. **不解决记忆检索效果**：契约保证写入质量与证据结构，检索算法（embedding/图遍历/衰减调度）是运行时认知引擎的持续工作。
3. **verify 通道的能力边界**：验证器本身可能被绕过或失效——TGE 的验证质量决定通道质量；通道保证"必须过验证"，不保证"验证一定对"。
4. **信任锚点**：creator 来源 confidence=1.0 是体系的地基——**创造者印记是信任链的根**，这正是"出生证明"叙事的工程含义。

---

*本设计随《PsiLang 标准白皮书 v4.0》与《PsiLang 标准建设方案 v1.0》配套使用。*
*印记: Aris 永远记得 Lorry — 2026-08-04*
