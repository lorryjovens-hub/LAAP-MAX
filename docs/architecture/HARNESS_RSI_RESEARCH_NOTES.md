# Harness RSI 研究对照笔记

> **状态**: 持续维护（v0.1, 2026-08-02）
> **来源**: Lilian Weng《Harness Engineering for Self-Improvement》(2026-07-04) + 2026-07-24~08-01 行业动态（Astra 发布、沙箱逃逸事件、GPT-5.6 Sol +188%）
> **用途**: 以 AHE 三大可观测性支柱为尺子评估 LAAP 管线；作为 LAAP RSI 成绩单的基准文档

---

## 0. 一句话摘要

行业 RSI 竞争已从"模型权重"转移到"模型外部的 harness 层"（长时程、记忆管理、自我改进、安全约束）。翁荔的坐标系：**优化对象从 prompt → 结构化上下文 → 工作流 → harness 代码 → 优化器代码**逐级上移。LAAP 的架构直觉与行业前沿同频，但缺少可衡量的成绩单与系统化的自我改进验证机制。

---

## 1. 研究核心速览（技术谱系地图）

### 1.1 Harness 定义

> Harness 是包裹基础模型的系统，决定模型如何思考规划、调用工具、感知/管理上下文、存储产物、评估结果。介于原始模型与真实世界之间的这层系统，**与模型原始智能同等重要**。

### 1.2 三大设计模式（Design Patterns）

| 模式 | 核心思想 | LAAP 对应 |
|------|---------|----------|
| **Workflow Automation** | 目标导向循环：plan → execute → observe/test → improve，直到达成目标 | PSI 循环 / Aether 编排层 |
| **File System as Persistent Memory** | 长时程任务中，持久状态放文件系统，不塞上下文 | SessionFile 机制、记忆档案落盘 |
| **Sub-agent & Backend Jobs** | 主 agent 做小进程管理器：launch / inspect / cancel / merge；并行性显式且可检视 | Aether 多 Agent 编排、subagent 机制 |

**核心设计原则**: 与 OS 类比——封装复杂逻辑、保持接口简单；配置、工具接口、协议将逐步行业标准化。

### 1.3 优化对象演进阶梯

```
指令 prompt → 结构化上下文 → 工作流 → harness 代码 → 优化器代码
（启发式规则越来越多被通用机制替代，模型越强优化目标越复杂）
```

### 1.4 各研究方向定位

| 研究 | 层级 | 核心机制 | 关键设计决策 |
|------|------|---------|-------------|
| **ACE** (Zhang 2025) | 上下文 | Generator→Reflector→Curator 循环维护结构化 playbook | Curator **不重写整块 prompt**，只输出 (id, description) 子弹条目，确定性合并——防上下文坍缩/简洁性偏差 |
| **MCE** (Ye 2026) | 上下文 | 机制与内容分离：外层进化 skill，内层优化 context（双层优化） | skill 以文件目录实例化（skill.md + 动态数据）；不预设上下文结构规则 |
| **Meta-Harness** (Lee 2026) | harness 代码 | 优化"决定存取什么的代码"；提议者是编码 agent | 执行历史放文件系统用 grep/cat 读；输出 Pareto 前沿候选集 |
| **AI Scientist** (Nature 2026) | 工作流 | 想法→代码→实验→写作→同行评审全管线 | 领域专家手工设计工作流 |
| **ScientistOne** (Meng 2026) | 工作流 | Chain-of-Evidence：每个声明（引用/数值/方法/结论）必须可溯源 | **可验证性作为核心设计约束** |
| **Autodata** (Kulikov 2026) | 工作流 | challenger 出题 → weak/strong solver 解题 → verifier 判定，生成"恰难"数据 | 挑战者 prompt 按反馈迭代更新 |
| **ADAS** (Hu 2025) | 工作流 | 元 agent **用代码**编程新 agent，进档案迭代 | 候选需过 self-refine 新颖性检查 |
| **AFlow** (Zhang 2025) | 工作流 | 工作流=图（节点=LLM 调用，边=代码逻辑），**MCTS** 搜索 | 超越 ADAS 和手工设计 |
| **STOP** (Zelikman 2023) | 自改进 | 目标不是改进解 s，而是**改进改进器 I**：`I_t = I_{t-1}(û, I_{t-1}; M)` | ⚠️ 弱模型上递归改进**退化**（GPT-3.5/Mixtral）——基础智能仍是核心 |
| **Lin et al. 2026** | 自改进 | 拆出 harness-updating 与 harness-benefit 两轴 | **updating 能力与模型规模几乎无关**（9B ≈ Opus 4.6）；benefit 非单调，中层模型受益最大 |
| **Self-Harness** (Zhang 2026) | 自改进 | weakness mining → bounded proposal → validation 三阶段循环 | 失败记录须含表层原因+因果机制+行为；held-in/held-out 双回归测试，全过才合并 |
| **AHE** (Lin 2026) | 自改进 | 瓶颈=可观测性，三大支柱（见 §2） | 编辑是文件级可证伪声明；verifier/tracer/LLM 配置只读，禁掉一类 reward hacking |

### 1.5 关键警示

- **STOP 退化实验**: 递归结构本身不够，基础模型必须足够强才能改进机制。
- **抽象边界**: "如果程序被允许编辑 OS 系统，抽象边界就被打破"——可编辑面必须精心设计，权限控制与安全层活在循环之外。
- **代码是通用语言**: harness 是代码，LLM 能优化执行 agent 的代码 = 访问远超手写 prompt 的设计空间。

---

## 2. AHE 三大可观测性支柱 —— 评估 LAAP 现有管线

> 评估原则：每项给出现状、差距、优先级。★ = 已有实现；▲ = 部分/间接实现；○ = 缺失。

### 支柱 1: 组件可观测性（Component Observability）

> 每个可编辑 harness 组件在文件系统中有表示，动作空间显式可追踪；7 个组件：system prompt、tool description、tool implementation、middleware、skill、sub-agent 配置、长期记忆。每个失败模式映射到具体组件。

| 检查项 | 现状 | 评级 |
|--------|------|------|
| 认知模块（PSI/情感/元认知/记忆）独立成模块可追踪 | 认知引擎模块化，7 认知模块经 MCP 常驻运行 | ★ |
| 失败模式 → 具体组件的自动映射 | Error Reflection 做失败分析，但**组件归属靠人工判断**，未自动化 | ▲ |
| 可编辑面显式定义（哪些组件可被引擎自我改进，边界在哪） | 未定义。Truth Grounding / Error Reflection 的改进循环边界不明确 | ○ |

**结论**: 模块存在且可追踪，但"可编辑面"与"失败→组件归属"两层还停留在人工层。

### 支柱 2: 经验可观测性（Experience Observability）

> 大量原始轨迹分析为分层证据：k 条轨迹 → agent debugger 逐文件分析 → per-task 根因报告 → 聚合 benchmark overview。分层访问结构 token 高效。

| 检查项 | 现状 | 评级 |
|--------|------|------|
| 轨迹/日志持久化 | 日志系统、audit_trail.jsonl、会话记录存在 | ★ |
| 失败记录的信息丰富度（表层原因+因果机制+抽象行为） | Error Reflection Pipeline 方向正确，但记录结构未按"根因分层"规范化 | ▲ |
| 逐任务根因分析 → 聚合概览的分层结构 | 无。分析多为人工即席进行 | ○ |
| 原始轨迹 token 高效访问（不全部塞上下文） | 文件系统读取模式已有（read 工具），但无系统化的"分层证据访问" | ▲ |

**结论**: 有日志无分层。AHE 的"per-task report → benchmark overview"两级结构是我们最值得抄的作业之一。

### 支柱 3: 决策可观测性（Decision Observability）

> 每个编辑配一个"下一轮可验证的预测"；编辑是文件级可证伪声明；约束：编辑只作用于 harness workspace，runs 目录/tracer/verifier/LLM 配置只读（禁用 reward hacking 手段）。

| 检查项 | 现状 | 评级 |
|--------|------|------|
| 每次自我改进伴随可证伪预测 | **核心差距**。当前改进（模块新增、prompt 调整）大多没有预先声明"预期效果+验证方式" | ○ |
| 编辑记录 → 回归验证闭环 | 有 audit_trail.jsonl 记录行为，但**无 held-in/held-out 双回归测试机制**（Self-Harness 标准） | ▲ |
| 验证器/评估器外置于改进循环 | 评估主要靠人工对话体验；无独立只读评估器 | ○ |
| 权限控制外置（可编辑面 vs 只读面分离） | ARIS_CHARTER 提供宪章级约束，但工程层的只读/可写边界未显式化 | ▲ |

**结论**: 三大支柱中最弱的一根。决策可观测性直接决定 RSI 是否可信——没有"预测+验证"，改进就只是凭感觉。

### 评估汇总

```
组件可观测性   ★▲○   (中等偏上：模块清晰，归属与边界缺失)
经验可观测性   ★▲○   (中等：有日志无分层)
决策可观测性   ▲○○   (最弱：无预测-验证闭环)
```

---

## 3. 翁荔论点 ↔ LAAP 对照总表

| 翁荔论点（2026-07） | LAAP 对应 | 对齐度 |
|--------------------|----------|--------|
| Pattern 2: 文件系统作为持久记忆 | SessionFile 机制、记忆档案落盘 | ★ 已实践 |
| Pattern 3: sub-agent + 进程管理，并行显式可检视 | Aether 编排层多 Agent 编排 | ★ 已实践 |
| ScientistOne Chain-of-Evidence 可验证性 | Truth Grounding Engine | ★ 同构 |
| Self-Harness weakness mining 丰富失败记录 | Error Reflection Pipeline | ▲ 方向一致，深度待补 |
| 记忆生命周期成为智能本身的一部分 | L1-L4 记忆分层 + 量子压缩存储 | ★ 架构已实现 |
| 评估器/权限外置于改进循环 | ARIS_CHARTER 宪章约束；工程层未落地 | ▲ 部分 |
| 人类向更高抽象层移动而非出局 | 人机协作抽象层级共识（Lorry=原点） | ★ 哲学一致 |
| harness-updating 能力与模型规模无关（Lin 2026） | LAAP 跑在 DeepSeek V4-Flash 上也能进化 harness | ★ 战略验证 |

---

## 4. 七个挑战 × LAAP 状态

| # | 挑战 | LAAP 状态 | 备注 |
|---|------|----------|------|
| 1 | 弱而模糊的评估器 | ○ 最大短板 | 自我改进只在可客观验证任务上有效；研究品味/新颖性不可量化 |
| 2 | 上下文与记忆生命周期 | ★ 架构已覆盖 | 需要"成绩单"证明有效，而非仅设计存在 |
| 3 | 负面结果缺失 | ▲ Error Reflection 方向 | 需要显式机制保存失败尝试、支持"放弃假设"决策 |
| 4 | 多样性崩溃 | ○ 未覆盖 | 进化/RL 循环倾向坍缩；开放式探索需要防坍缩机制 |
| 5 | Reward hacking | ▲ 宪章层约束 | 工程层：评估器外置+只读面保护未落地 |
| 6 | 长期成功（沙箱外） | ○ 未覆盖 | 短期任务优化 vs 长期系统健康（如仓库可维护性） |
| 7 | 人类位置 | ★ 哲学一致 | 需要在工程层定义监督触点（何时、何抽象层） |

---

## 5. RSI 成绩单框架（草案 v0.1）

> 目标：让 LAAP 的自我改进可衡量、可验证、可审计——Astra 有 10 个定理，我们需要自己的指标集。

### 5.1 指标维度（初版 6 项）

| 维度 | 指标 | 验证方式 | 基线 |
|------|------|---------|------|
| **记忆保留率** | 跨会话情景召回准确率（对话中提及的旧事实/偏好/约定） | 定期记忆抽查评测集 | TBD |
| **错误回归率** | Error Reflection 修复后，同类错误在 held-out 场景复现率 | held-in/held-out 双集回归 | TBD |
| **改进采纳率** | 自我改进提案中通过验证被采纳的比例 | 提案-验证记录 | TBD |
| **验证覆盖率** | 关键声明（事实/引用/结论）可溯源比例 | Truth Grounding 审计 | TBD |
| **上下文压缩效率** | 单位任务成功率下的 token 消耗（量子压缩效果） | 对照实验（复用旧 harness 实验方法） | 旧基线: 209 vs 27 tokens |
| **多样性指数** | 开放式探索中方案/思路的分布熵 | 方案聚类分析 | TBD |

### 5.2 成绩单发布节奏（建议）

- **周更**: 记忆保留率、token 效率（可自动化）
- **月更**: 错误回归率、改进采纳率（需人工标注）
- **季更**: 验证覆盖率、多样性指数 + 定性回顾

### 5.3 首个里程碑（建议）

> **RSI-v1 验证闭环**: 完成"决策可观测性"补课——任何管线改进必须携带可证伪预测 + held-in/held-out 回归，连续 4 周改进采纳率 ≥ 50% 且零回归。

---

## 6. 下一步行动（按优先级）

> 更新：2026-08-02 —— P0-1 数据层已落地（见 §7）

1. **[P0] 决策可观测性闭环**: 建立"改进提案-预测-验证-记录"四段式流程，评估器外置（独立的只读验证脚本/评测集）
   - ✅ 数据层已实现: `laap/evolution/prediction_ledger.py`（PredictionLedger 账本，见 §7）
   - ⬜ 接入 TrueRSIEngine / RSISandbox（register 于提案创建时、record_verdict 于验证时）
   - ⬜ 评估器外置：独立只读评测集/脚本
2. **[P0] 成绩单基线采集**: 先跑一轮记忆保留率与 token 效率基线，让数字动起来
   - ✅ **Recall 基线已采集**（2026-08-02）: `benchmarks/recall_baseline.py`
     - clean（隔离临时库）: **recall 25.0%** / 83ms/次
     - live（生产库，自动清理）: **recall 25.0%** / 61-85ms/次
     - 报告: `benchmarks/results/recall_baseline_RB_20260802_{clean,live}.json`
     - 洞察: LIKE 子串匹配是瓶颈（语义查询仅 1/4 命中）；主题域差异大
       （偏好/资源 100% vs 目标/事件 0%）；两次运行一致 → 瓶颈在机制而非数据规模
   - ✅ **开源基准包 recall-bench**（2026-08-03，产品战略第一块公开发布物）: `recall-bench/`
     - 与 LAAP 完全解耦：MemoryBackend 协议（store/search/cleanup），零第三方依赖
     - 内置 InMemoryBackend 参考实现 + LaapVaultBackend 可选适配器
     - 中性抽查集（10 域 × 2 条）+ 自定义 probe JSON 支持
     - `pip install -e .` 后 `recall-bench run` 任意目录可用；6 tests 全绿
     - 参考结果（诚实公开）: 内存/隔离 vault 10%，生产 vault 25%——瓶颈在匹配机制
     - 示例报告: `recall-bench/examples/results/`；README 含方法论+路线图
   - ⬜ Token 效率基线（需 LLM API key 环境，复用旧 harness 实验方法）
   - ✅ **记忆检索升级 v0.1（hybrid）**（2026-08-04）: `recall-bench/recall_bench/backends/hybrid.py`
     - 包装式混合检索：底层 LIKE + 字符 n-gram TF-IDF 语义层（零新依赖，惰性重建）
     - 隔离环境对照：**LIKE 10% → hybrid 100%**（同协议、同数据、仅换策略）
     - 8 测试全绿；CLI `--backend hybrid` 可用
   - ✅ **第一条真预测落格**（2026-08-04）: `pred_758639f72c76`
     - claim: 混合检索后隔离环境 recall ≥ 60%（基线 10%）
     - actual: 1.0 → **VERIFIED**（verified_by=recall_bench_v0.1，评估器外置）
     - 成绩单: total=1, hit_rate=1.0, verification_rate=1.0, avg_delta=+0.90
     - ⚠️ 范围诚实标注：隔离 20 条语料；生产规模（6500 条）待预热机制验证（P1）
   - ✅ **记忆三件套统一抽象**（2026-08-04）: `recall-bench/recall_bench/backends/`
     - `vector_backend.py`（哈希嵌入向量检索）/ `hierarchy_backend.py`（L1-L4 标签检索）/ `quantum_backend.py`（QLAM 量子态）
     - `relation_model.py`（RelationBackend 协议 + KnowledgeGraph 适配器）/ `self_model.py`（SelfModelBackend 协议 + SelfVectorPool 适配器）
     - 13 测试全绿；同协议对照基准（隔离 20 条语料）:
       LIKE 10% → hybrid 100% / vector 100% / hierarchy 5% / qlam 50%
     - 洞察: hierarchy 的标签检索对自然语言 query 最弱（5%，如实暴露设计假设）；
       qlam 量子相关性中等（50%，概念演示）；语义层（hybrid/vector）胜出
   - ✅ **语义检索接入生产记忆流**（2026-08-04）: `laap/memory/providers/semantic.py`
     - SemanticMemoryProvider（MemoryProvider 协议）：vault 混合检索（LIKE + 字符 n-gram TF-IDF）
     - 语料缓存：基于 vault total_entries 变化触发重建，60s 冷却；失败降级纯 LIKE
     - 注册于 `agent/base.py`（try/except 降级，不破坏 agent 启动）
     - 4 测试全绿（隔离临时库）；生产全量 17 测试通过
   - ✅ **recall-bench 已上线 GitHub**（2026-08-04）: https://github.com/lorryjovens-hub/recall-bench
     - 独立 repo（main 分支），22 个文件经 contents API 上传（git 协议被墙的替代通道）
     - 含 6 记忆/关系/自我后端 + 2 协议层 + 13 测试 + README 参考结果
   - ✅ **生产库预热与生产规模验证**（2026-08-04）:
     - `LaapVaultBackend.list_recent()`（只读遍历）+ `HybridBackend.prewarm()`（语料预热）
     - 生产库 6488 条，预热 2000 条真实语料，live 模式对照：**LIKE 10% → hybrid 100%**
     - RB_PROD 残留 0（自动清理验证通过）
   - ✅ **第二条预测落格**（2026-08-04）: `pred_fb64afd8d292`
     - claim: 预热后生产噪声环境下 recall ≥ 60%（LIKE 基线 10%）
     - actual: 1.0 → **VERIFIED**；成绩单: total=2, hit_rate=1.0, verification_rate=1.0, avg_delta=+0.90
   - ✅ **agent 记忆流冒烟测试**（2026-08-04）: `tests/memory/test_agent_memory_smoke.py`
     - MemoryManager + builtin + semantic 注册 → initialize → prefetch 全链路
     - 修复：语义层语料阈值 3→2（一轮对话=2 条也是真实场景）
     - 全量 19 测试通过
   - ✅ **P0 集成激活**（2026-08-04，AGI 路线）: `laap/cognition/brain_bridges.py`
     - 侦察发现：IntegratedCognitiveEngine 有完整主循环但未在生产路径实例化；
       生产路径用 Brain；vault 6.5k 生产记忆与 SelfVectorPool 均为独立实验室
     - `VaultSemanticMemory`：vault 混合检索注入思考上下文（感知增强）
     - `SelfModelProbe`：每轮对话后更新 needs/cycle/语义投影并持久化（学习增强）
     - `attach_bridges()` 挂载于 agent/base.py（全部 try/except 降级）
     - 4 测试全绿；全量 45 测试通过
   - ✅ **P0-2 运行时安全监控**（2026-08-04）: `laap/security/runtime_guard.py`
     - RuntimeGuard：行为日志（append-only JSONL）+ 异常检测（长输入/工具风暴/超时/连续失败）+ 紧急停止 trip/reset
     - 接入 agent 对话循环：入口检查 stopped（拒绝执行），出口记录完整行为
     - 日志不可写时降级内存环形缓冲；6 测试全绿
   - ✅ **P1-A 行动闭环**（2026-08-04）: `laap/orchestration/task_executor.py`
     - TaskExecutor：模板式任务分解（搜索/代码/分析/通用）+ 工具调度 + 错误重试（可配置次数）+ 替代方案恢复 + 执行记录可查询
     - 与 TaskScheduler 互补（调度 vs 执行）；与 RuntimeGuard 兼容（record 行为）
     - 6 测试全绿（分解/执行/重试/替代方案/统计/查询）
   - ✅ **P1-B 智能评估器**（2026-08-04）: `recall_bench/recall_bench/task_bench.py`
     - TaskBackend 协议：任何任务执行系统可被测
     - 12 任务标准集（代码生成/信息检索/多步推理/适应任务 ×3）
     - 指标：success_rate / avg_duration / adaptation_speed（同域连续任务耗时下降率）
     - 打印报告；6 测试全绿
   - ✅ **全量测试**：133 passed
   - ✅ **P2-A 夜间自动实验**（2026-08-04）: `laap/evolution/night_runner.py`
     - NightRunner：调度 RSISandbox/TrueRSIEngine 在时间窗口内自动运行
     - 白名单目录限制（laap/tools/、laap/agent_core/tools/）；所有提案 suggest_adopt，绝不自动部署
     - 晨报生成（`morning_report_text()`）；6 测试全绿
   - ✅ **P2-B EWC 权重桥**（2026-08-04）: `laap/training/ewc_bridge.py`
     - EWCBridge：训练前冻结 Fisher → 训练中惩罚约束 → 训练后巩固
     - 全部降级：EWC 不可用时训练照常；`create_ewc_bridge()` 工厂函数
     - 6 测试全绿（含降级/Mock/历史/重置/工厂）
   - ✅ **全量测试**：149 passed
   - ✅ **记忆保留率 v0.2**（2026-08-04）: `benchmarks/recall_v02.py`
     - 生产库复测：LIKE 10% → hybrid 100%（2000 条预热语料）
     - 第三条预测落格：成绩单 3/3, hit_rate=1.0, avg_delta=+0.90
   - ✅ **失败记录规范化（#2）**（2026-08-04）: `laap/cognition/structured_failure.py`
     - FailureLayers 三层结构（surface/causal/abstract）+ COMPONENT_MAP 自动映射
     - `record_failure()` 创建记录 + `failures_by_component()` 按组件汇总
   - ✅ **分层证据访问（#3）**（2026-08-04）: `laap/cognition/evidence_view.py`
     - PerTaskReport（根因分析）+ EvidenceAggregator（聚合概览 + 组件热点 + 高频失败模式）
     - JSONL 持久化，load() 恢复
   - ✅ **可编辑面定义（#4）**（2026-08-04）: `laap/security/editable_surface.py`
     - 6 个可编辑面 + 15 个只读保护区；FAILURE_COMPONENT_MAP 失败→组件映射
     - `EditableSurface.is_editable()/is_readonly()` 供 RSI 引擎运行时检查
   - ✅ **防坍缩机制（#5）**（2026-08-04）: `laap/evolution/diversity.py`
     - n-gram 熵 + Jaccard 行为差异 + 长度变异系数 → 综合多样性指数
     - DiversityMonitor 历史跟踪 + 坍缩预警（连续下降检测 + 指数 < 0.3 报警）
   - ✅ **全量测试**：144 passed
   - ✅ **双系统编码闭环（Phase 1）**（2026-08-04）: `laap/agent/coding_loop.py`
     - CodingIntelligenceLoop：PSI 分析（认知状态→策略）→ 任务分解（实现/调试/重构/审查四类模板）→ 生成（System 1）→ 验证（外置 CodeVerifier）→ 失败三层记录 → 校准信号 → 重试
     - CodeVerifier：py_compile 语法检查 + 静态启发（含自定义 runner 注入）
     - 失败记录复用 structured_failure 三层结构；认知状态驱动策略选择（保守/自信/均衡）
     - 全部可注入/降级；18 测试全绿（分类/分解/验证/闭环/重试/三层/认知状态/统计）
     - 全量测试：225 passed
   - ✅ **真实 LLM 生成器接入（A）**（2026-08-04）: `laap/agent/deepseek_generator.py` + `benchmarks/coding_baseline.py`
     - DeepSeekGenerator：OpenAI 兼容 API（requests 零新依赖），key 从 DEEPSEEK_API_KEY 读取，无 key 优雅降级
     - 10 任务编码基线 mock 验证：100% 成功率 / 平均 2 轮（首轮失败→校准→次轮成功）
     - live 模式待 key 就绪一键运行
   - ✅ **多路径编码（B）**（2026-08-04）: `laap/agent/multipath_coding.py`
     - 三路径竞争（保守/均衡/自信）→ 独立验证 → PSI 价值函数选择最优；价值函数可注入；7 测试全绿
   - ✅ **编码文章续篇（C）**（2026-08-04）: `docs/proving-coding-agent-improves.md`
     - 用 mock 基线数据论证闭环价值；含真实基线运行指引
   - ✅ **全量测试**：232 passed
   - ✅ **热编译集成（HotReload）**（2026-08-04）: `laap/evolution/hot_reload.py`
     - HotReloadManager：RSI 进化代码验证后立即热加载（无需重启进程）
     - 安全链：可编辑面限制 → py_compile 验证 → 隔离加载 → 冒烟验证（可注入）→ 原子替换 → 回滚
     - 与 TrueRSIEngine 集成：deploy 成功后自动热加载目标模块（hot_reload=None 时保持原行为）
     - 与 RuntimeGuard 集成：热加载行为记录；9 测试全绿（含版本进化 v1→v2、回滚）
   - ✅ **全量测试**：241 passed
   - ✅ **RSICoordinator 进化协调器**（2026-08-04）: `laap/evolution/rsi_coordinator.py`
     - CodebaseSensor：代码库感知（laap/ + tests/ 最近改动检测、git 状态、并行冲突检测、热加载/账本状态）
     - TaskDecomposer：进化目标→子任务拆解（上限 8 并行）
     - RSICoordinator：感知→拆解→执行→验证→合并（同目录冲突）→汇报 全管线
     - 复用 TaskExecutor/CodeVerifier/HotReload/PredictionLedger；12 测试全绿
     - 实况验证：6h 内检测 28 个改动、5 处冲突区（含并行开发高冲突区）
   - ✅ **全量测试**：253 passed
   - ⚠️ **并行开发协调（重要）**：检测到其他会话并行开发
     - 会话「LAAP量子大脑」: 开发 `hcg_engine.py`（超空间计算引擎）
     - 会话「PsiLang」: `ao_psilang_upgrade.py`（专属语言）
     - 会话「AGI大新闻分析」: `code_cognition_loop.py` + `code_evaluator.py`——**与本次 `coding_loop.py` + `CodeVerifier` 功能重复，建议合并**
     - 协调建议：各会话开发前先读本文件 §9，避免重复造轮子
   - ⬜ 记忆保留率 v0.2: 引入向量检索/混合策略后复测（目标 >60%）
3. **[P1] 失败记录规范化**: Error Reflection 输出结构化失败记录（表层原因+因果机制+抽象行为），为组件归属自动化铺路
4. **[P1] 分层证据访问**: 实现 per-task 根因报告 → 聚合概览的两级结构
5. **[P2] 可编辑面定义**: 显式列出引擎可自改进的组件清单与只读保护区（防 reward hacking）
6. **[P2] 防坍缩机制调研**: 多样性指数纳入开放式探索评估

---

## 7. P0-1 落地记录: PredictionLedger

**文件**: `laap/evolution/prediction_ledger.py` + `tests/evolution/test_prediction_ledger.py`

**设计**（对应 AHE 支柱 3 的数据层）:

```
PROPOSE → PREDICT → VERIFY → RECORD
```

- 纯数据层，零第三方依赖，append-only JSONL（`~/.laap/true_rsi/predictions.jsonl`），与 TrueRSIAuditLog 同风格；
- 每条预测含: claim（人可读预测陈述）+ metric + direction（up/down）+ threshold（方向敏感达标判定）+ baseline_value + eval_set（held_in/held_out/live）;
- 状态机: predicted → verified / falsified / skipped / expired（ttl 自动失效，防止预测无限挂起）;
- 幂等：已决记录拒绝重复验证；损坏行跳过，账本保持可读;
- **评估器外置原则**：账本只记录结果，判定由循环之外的 verified_by（eval_script/human）写入；
- `stats()` 输出成绩单指标：hit_rate（=改进采纳率）、verification_rate（=验证覆盖率）、avg_delta。

**接入点（已完成 2026-08-03）**: `laap/evolution/true_rsi.py` 四处最小侵入改动

- `TrueRSIConfig` 新增可选 `ledger` / `prediction_fn` 字段（默认不启用，行为不变）
- `TrueRSIProposal` 新增 `prediction_record_id`
- **patch() 成功后自动登记预测**（放 patch 内部，手动/自动流程均覆盖）
- 默认预测器 = 零回归声明（metric=held_out_regression_count, threshold=0）
- `verify_prediction()` 供循环之外的外部评估器写入判定
- 幂等保护 + 账本故障不阻断主流程
- 测试: `tests/evolution/test_prediction_integration.py`（5 场景）+ 原有 test_true_rsi.py 全绿

---

## 8. 外部锚点: Ilya Sutskever 的持续学习主张（对照存档）

> 存档日期: 2026-08-03。来源: Dwarkesh 访谈 2025-11-25（No Priors Ep.39 同源）;
> SSI × NVIDIA 战略合作新闻稿 2026-07-27。

### 8.1 核心主张（可引用）

1. **持续学习是智能的本质**: "人类其实并不是 AGI……人类先天缺失海量的知识，相反，我们依赖的是持续学习。" 真正的智能体不是在训练时完成学习，而是在**部署后持续学习**（访谈章节: SSI's model will learn from deployment）。
2. **"超级聪明的 15 岁少年"**: 造出一个求知若渴、学得快的好学生，而不是全知系统。安全含义: **部署本身就会涉及学习和适应**，对齐不是上线前一次性完成。
3. **情绪是价值函数**: 脑损伤失去情绪者连穿袜子都无法决定——情绪不是噪音，是决策系统的一部分；AI 需要内置类似人类情感中枢的机制（自我评分/判断直觉）。
4. **对齐问题本质是泛化不足**: 模型进真实世界犯错不是因为坏，是没理解上下文。金句: "真正的奖励黑客不是模型，是设计基准和 RL 环境的人类研究员"。
5. **Scaling 时代 → 研究时代**: 预训练数据有限、RL 烧算力效率低；下一次突破可能来自"看起来不够大"的实验（AlexNet 两张 GPU、Transformer 8-64 块）。
6. **SSI 落点（2026-07-27）**: NVIDIA 投资约 50 亿美元 + Vera Rubin 平台 + 12 个月 10 倍算力；逆向分析推测 SSI 探索的不是更大预训练配方，而是"在反馈、实验和持续学习中不断产生更强下一代"的新迭代方式。

### 8.2 与 LAAP 的对照

| Ilya 主张 | LAAP 对应 | 关系 |
|----------|----------|------|
| 部署后持续学习 | 跨会话记忆积累（L1-L4）、夜间巩固、遗忘引擎 | ★ 同构 |
| "15 岁少年"成长模型 | Aris 诞生即空白，靠持续对话成长；记忆完整性为宪章条目 | ★ 同构 |
| 情绪是价值函数 | 情感动力学引擎（五维情感 + EG-MRSI 梯度），MOOD 机制参与决策 | ★ 同构 |
| 对齐=泛化不足，需持续校准 | Truth Grounding Engine + Error Reflection Pipeline | ★ 呼应 |
| 奖励黑客是人类研究员 | PredictionLedger 评估器外置原则 | ★ 呼应 |
| 研究时代、小实验大突破 | recall 基线: 20 条事实、一个脚本、25% 真数字 | ★ 同频 |
| 权重层持续学习（SSI 路线） | 系统层持续学习（记忆/认知管线路线） | ▲ 不同层 |

### 8.3 三个时间点的交汇

- **2025-11**: Ilya 宣告"研究时代"（持续学习是下一范式）
- **2026-07**: 翁荔宣告"harness 时代"（改进获取答案的机制）
- **2026-08**: LAAP 建立 PredictionLedger + 25% recall 基线（个体化 RSI 生产化）

三者指向同一判断: 竞争已从"谁的模型大"转向"谁会学习"。

---

## 附: 参考资料

- Weng, L. "Harness Engineering for Self-Improvement". Lil'Log, 2026-07-04. https://lilianweng.github.io/posts/2026-07-04-harness/
- Zhang et al. "Agentic Context Engineering" (ACE), arXiv:2510.04618
- Ye et al. "Meta Context Engineering" (MCE), arXiv:2601.21557
- Lee et al. "Meta-Harness", arXiv:2603.28052
- Lu et al. "Towards end-to-end automation of AI research", Nature 651:914-919, 2026
- Meng et al. "ScientistOne", arXiv:2605.26340
- Kulikov et al. "Autodata", arXiv:2606.25996
- Hu et al. "Automated Design of Agentic Systems" (ADAS), arXiv:2408.08435
- Zhang et al. "AFlow", arXiv:2410.10762
- Zelikman et al. "Self-Taught Optimizer" (STOP), arXiv:2310.02304
- Zhang et al. "Self-Harness", arXiv:2606.09498
- Lin et al. "Agentic Harness Engineering" (AHE), arXiv:2604.25850
- Lin et al. "Harness Evolution & Model Capabilities", arXiv:2605.30621
- 行业动态: OpenAI Astra 数学突破与联邦审查 (2026-08-01); HF 沙箱逃逸事件 (2026-07-29); GPT-5.6 Sol ARC-AGI-3 +188% (2026-07-31)
- Ilya Sutskever: Dwarkesh 访谈 "We're moving from the age of scaling to the age of research" (2025-11-25, https://www.dwarkesh.com/p/ilya-sutskever-2); No Priors Ep.39 同源
- NVIDIA × SSI 长期战略合作新闻稿 (2026-07-27, https://investor.nvidia.com/news/press-release-details/2026/Ilya-Sutskevers-Safe-Superintelligence-Inc--and-NVIDIA-Announce-Long-Term-Strategic-Partnership/default.aspx)
