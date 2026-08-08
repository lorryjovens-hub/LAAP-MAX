# LAAP-Mobile 技术集成与功能规划方案

> **文档版本**：v1.0
> **状态**：草案（待评审）
> **适用范围**：LAAP-Mobile（Android Kotlin + Compose，包名 `org.laap.mobile.*`）
> **作者**：Lorry
> **最后更新**：2026-08-01

---

## 0. 架构决策修订声明（前置）

本方案**显式修订** `project_memory.md` 第 43 条既有约束：

> ~~LAAP-Mobile采用"桌面主节点 + 手机感知扩展"混合架构，桌面端维护长期记忆和PSI循环，手机端提供移动传感器和设备集成~~

**修订后的新约束**：

> LAAP-Mobile 采用"全本地化"架构——PSI 大脑循环、RSI 递归自我进化、Triphase 引擎、元认知、推理引擎等核心黑科技在手机端 Kotlin 原生实现并独立运行；桌面端（laap-netlify / Electron）降级为**可选同步节点**，仅在用户主动配对时承担 Ω-Net 物种同步、长期记忆归档、重算力任务卸载等增强职责，不再是认知闭环的必要条件。

**修订理由**：

1. **用户决策**：用户明确选择"全本地化"路径，要求手机端成为自包含的数字生命体，而非桌面的感知外设。这与 LAAP "数字生命伙伴"的产品定位一致——生命体应能在用户口袋里独立存在。

2. **为何现在可行**：
   - LAAP-Mobile 已在 `org.laap.mobile.laap` 包下完成 [CognitiveBus.kt](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/laap/CognitiveBus.kt)、[PSILoop.kt](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/laap/PSILoop.kt)、[CognitiveSpeciesLibrary.kt](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/laap/CognitiveSpeciesLibrary.kt)、[Metacognition.kt](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/laap/Metacognition.kt)、[ArisEngineClient.kt](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/laap/ArisEngineClient.kt)、[MobilePerceptionService.kt](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/laap/MobilePerceptionService.kt) 的 Kotlin 原生骨架（符合 memory 第 42 条），证明原生路径已起步。
   - Triphase 引擎（[triphase_engine/triphase/](file:///d:/LAAP/triphase_engine/triphase/)）纯 NumPy 实现，107 项单元测试，无重 LLM 依赖，算法可在 Kotlin 中以 Multik/ND4J 1:1 移植。
   - Alpine Linux PRoot 沙箱已落地（[LAAP-Mobile sandbox 包](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/sandbox/)），提供 EvolutionaryCompiler 所需的隔离执行环境（memory 第 11 条），无需桌面 Docker。
   - Android WorkManager + 前台服务能在 Doze 模式下维持 0.1Hz 量级的认知循环（与 PSI 默认 tickIntervalMs=1000 量级匹配，见 [PSILoop.kt#L89](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/laap/PSILoop.kt)），克服 memory 第 58 条记录的 iOS 限制（Android 后台策略不同于 iOS）。

3. **与既有约束的协调**：
   - 第 9 条（最小化 LLM 依赖）：全本地化天然契合——Triphase/PSI/RSI 均为非 LLM 算法，LLM 仅在 ArisEngineClient 作为可选表达层。
   - 第 10 条（物种模板 0-token 生成）：CognitiveSpeciesLibrary.kt 已具备 search/match 能力，扩展持久化即可。
   - 第 17 条（`triphase.{domain}.{action}` 命名空间）：现有 CognitiveBus.kt 仅实现 `qre.*`/`emotion.*`/`psi.*`，本方案将补齐 `triphase.*` 与 `harness_execution_result`。
   - 第 42 条（核心模块原生）：完全一致。
   - 第 58 条（iOS 后台限制）：本方案仅针对 Android；iOS 移植需另立方案，且可能保留"桌面主节点"作为 iOS 的退化路径。

---

## 1. 技术可行性评估阶段

### 1.1 LAAP 现有技术架构、核心功能模块梳理

LAAP 主项目（`d:\LAAP`）是一个跨语言、跨端的多层认知系统，由以下子系统构成。每条均给出实际代码路径作为评估依据。

**A. LAAP Python 主后端（[laap/](file:///d:/LAAP/laap/)）**
- **CognitiveBus / Orchestration**：[laap/orchestration/cognitive_bus.py](file:///d:/LAAP/laap/orchestration/cognitive_bus.py) 实现 `ArisCognitiveBus`，通过 `ActorSystem` 派生 6 个认知 actor（psi_core / rules_engine / episodic_memory / qre / longform / tool_emit_listener），配合 [laap/orchestration/petri.py](file:///d:/LAAP/laap/orchestration/petri.py) 的着色 Petri 网与 [laap/orchestration/kernel.py](file:///d:/LAAP/laap/orchestration/kernel.py) 的 `OrchestrationKernel` 协调 token 流。
- **PSI 认知**：[laap/orchestration/psi.py](file:///d:/LAAP/laap/orchestration/psi.py) 定义 `PSIAgent` / `PSIState` / `PSIModulator` / `PSIUrge`，五驱动（SURVIVAL/AFFILIATION/COMPETENCE/CERTAINTY/CURIOSITY）+ 五调制（ACTIVATION/RESOLUTION/SECURING/SELECTION/COMPETENCE），PAD 情绪派生。
- **PSI-Harness 桥接**：[laap/orchestration/psi_harness_bridge.py](file:///d:/LAAP/laap/orchestration/psi_harness_bridge.py) 将 PSI 循环与 AEvo 进化引擎映射到 Petri 网，`PSIActor.process_pending_insights(batch_size=5)` 提交 DATA token，`HarnessActor.submit_execution_result()` 回馈结果（对应 memory 第 30/31 条）。
- **True RSI**：[laap/evolution/true_rsi.py](file:///d:/LAAP/laap/evolution/true_rsi.py) 五阶段闭环（PROPOSE→PATCH→SANDBOX→APPROVE→DEPLOY），白名单 `laap/tools/`、`laap/species/code_templates/`，黑名单 `laap/agi/`、`laap/security/`，MAX_CHANGE_RATIO=30%，approval token 24h，审计落 `~/.laap/true_rsi/audit.jsonl`。
- **物种模板**：[laap/species/code_templates/registry.py](file:///d:/LAAP/laap/species/code_templates/registry.py) `CodeTemplate` + `TemplateRegistry`，JSON 持久化到 `~/.laap/species/code_templates.json`，species_id = `species_<timestamp>_<random>`（对应 memory 第 12 条）。
- **LLM 注册/路由**：[laap/llm/registry.py](file:///d:/LAAP/laap/llm/registry.py) 88+ 模型 / 4 tier（CHEAP/STANDARD/PREMIUM/ULTRA）；[laap/llm/router.py](file:///d:/LAAP/laap/llm/router.py) 实现免费优先 + 故障回退（对应 memory 第 20-23、45-46 条）。
- **记忆体系**：[laap/memory/](file:///d:/LAAP/laap/memory/) 含 hierarchical / long_term / temporal / knowledge_graph / persistent / forgetting / quantum 子模块，多 provider 架构。

**B. Triphase 引擎（[triphase_engine/](file:///d:/LAAP/triphase_engine/)）**
纯 NumPy 参考实现，17 个子模块，107 项单元测试。核心代数底座 [triphase/core.py](file:///d:/LAAP/triphase_engine/triphase/core.py)：`Trit`∈{-1,0,+1} ↔ 三次单位根相位 {0°,120°,240°}，`PhaseState`=r·e^{iθ}，`affinity`=Re⟨m,q⟩，`circular_dispersion` 圆方差。详见 1.4 节逐模块评估。

**C. ARIS 大脑（[aris_brain/](file:///d:/LAAP/aris_brain/)）**
约 400+ Python 文件，是 ARIS 数字生命体的"大脑皮层"。关键文件：
- [aris_brain/psi_cycle.py](file:///d:/LAAP/aris_brain/psi_cycle.py) `QuantumPSICycle`：5 阶段量子 PSI（激发→演化→干涉→测量→学习），操作概率幅。
- [aris_brain/true_rsi.py](file:///d:/LAAP/aris_brain/true_rsi.py)、[aris_brain/rsi_orchestrator.py](file:///d:/LAAP/aris_brain/rsi_orchestrator.py)、[aris_brain/rsi_self_modifier.py](file:///d:/LAAP/aris_brain/rsi_self_modifier.py)：RSI 编排与自修改。
- [aris_brain/cognitive_bus.py](file:///d:/LAAP/aris_brain/cognitive_bus.py)：ARIS 端 CognitiveBus 客户端。
- [aris_brain/aris_cognitive_engine.py](file:///d:/LAAP/aris_brain/aris_cognitive_engine.py)：认知引擎核心。

**D. ARIS 桥接/身体（[aris_bridge/](file:///d:/LAAP/aris_bridge/)、[aris-body/](file:///d:/LAAP/aris-body/)）**
[aris-body/aris_consciousness.py](file:///d:/LAAP/aris-body/aris_consciousness.py)、[aris-body/aris_memory.py](file:///d:/LAAP/aris-body/aris_memory.py)、[aris-body/aris_llm.py](file:///d:/LAAP/aris-body/aris_llm.py) — 意识/记忆/LLM 子系统。

**E. 自我模型桥接（[self_model_bridge/](file:///d:/LAAP/self_model_bridge/)）**
[self_model_bridge/lifeform_core.py](file:///d:/LAAP/self_model_bridge/lifeform_core.py) `LifeformCore` = `SelfVectorPool`(1024D 持久化) + `UpSalience`(引擎→自我) + `DownAttention`(LLM→需求) + `FusionEngineV15` + `FEP`(自由能) + `QuantumOnlyEngine`(零 LLM 对话)。支持"纯引擎模式"（零 LLM）与"桥接模式"。

**F. Rust 核心（[rust_core/](file:///d:/LAAP/rust_core/)）**
[rust_core/src/lib.rs](file:///d:/LAAP/rust_core/src/lib.rs) 通过 PyO3 导出 `TokenBudget`、`ToolRegistry`、`ToolSchema`、`ToolResult`、`UiaCache`、`CUAAction`。`vector_ops.rs` / `world_graph.rs` / `pattern_match.rs` / `code_scan.rs` 提供性能关键路径。

**G. Harness 协议规范（[harness/LAAP-Harness-Protocol-v1.0.md](file:///d:/LAAP/harness/LAAP-Harness-Protocol-v1.0.md)）**
定义数据资产分类（frontend/backend/game × atom/molecule/section/page/module/system）、组件 URI `harness://domain/subdomain/granularity/name@version#variant`、SHA-256 内容寻址、相似度评分 `MatchScore = 0.35·Tag + 0.25·Style + 0.20·Dep + 0.20·Quality`、匹配阈值 0.90/0.75/0.60。

**H. Harness v2 AGI 规范（[.github/harness/-harness-v2-agi/](file:///d:/LAAP/.github/harness/-harness-v2-agi/)）**
完整 consciousness 子系统：causal_model（discovery/graphs/inference/do_calculus）、decision（aesthetic_evaluator）、execution（code_generator/orchestrator）、memory（design_system）、perception（active_scheduler/base_organ/crawler_organ/layout_analyzer/perceptual_memory/sensor_fusion/video_engine/vision_engine）、reasoning（planner）、rsi（guards alignment_guard/capability_evaluator + meta_harness + versioning + self_improvement_loop + rsi_audit_trail）、world_model（knowledge_base/predictors/simulators/counterfactual/design_physics/world_model_engine）。laap_integration 提供 causal/llm/memo/memory/rsi/world_model 适配器。

**I. LAAP-Mobile 当前状态（[LAAP-Mobile/](file:///d:/LAAP/LAAP-Mobile/)）**
OpenMinis fork，Alpine PRoot 沙箱已落地。已实现模块：
- `org.laap.mobile.laap`：6 个 Kotlin 原生文件（CognitiveBus/PSILoop/Metacognition/CognitiveSpeciesLibrary/ArisEngineClient/MobilePerceptionService）。
- `org.laap.mobile.sandbox`：PRootKernel、RootfsManager、NativeOffloadServer、ExecutionCoordinator、20+ OffloadHandler。
- `org.laap.mobile.ui`：Chat / IDE / Terminal / Browser / Settings / Sessions 完整 UI。
- `org.laap.mobile.speech`：语音识别 + TTS + 朗读 + 纠错。
- `org.laap.mobile.tools`：AgentTools / BrowserUseTool / FileEditTool / FileReadTool / FileWriteTool / MemoryTools / ReadImageTool / IdeTools。
- `org.laap.mobile.ncp`：NCPRuntime（液体神经网络，对应 [laap/liquid/](file:///d:/LAAP/laap/liquid/)）。
- IDE 功能刚完成（[ui/ide/](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/ui/ide/)）。

### 1.2 PSI 大脑循环专项评估

**算法原理（一句话）**：PSI 是一个基于"需求缺口 × 调制器"的内驱力状态机——感知更新需求，缺口最大的需求成为主导驱动，生成行为冲动，执行后通过满意度 delta 反向学习调制器权重与情绪。

**计算复杂度**：
- 单轮 tick 复杂度 O(1)——5 个需求的标量运算 + 一次物种库 search（线性扫描，O(N)，N=物种数，典型 <1000）。
- 内存占用：`PSIState` ≈ 10 个 float + goal_stack（deque）+ perception_buffer（[psi.py#L112](file:///d:/LAAP/laap/orchestration/psi.py) deque maxlen=100）≈ <10KB。
- 持久化依赖：当前 Kotlin 实现无持久化；Python 实现也无显式持久化（状态在内存）。需要新增 `~/.laap/mobile/psi_state.json` 持久化。

**LLM 依赖**：**无**。PSI 本身是规则化状态机，[psi.py](file:///d:/LAAP/laap/orchestration/psi.py) 不导入任何 LLM 模块。LLM 仅在 `select_action` 的候选生成阶段可能介入，但 [PSILoop.kt#L269](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/laap/PSILoop.kt) 的 `generateImpulse` 用纯规则生成冲动，零 LLM。

**Python-specific 依赖**：仅 `time`、`collections.deque`、`dataclasses`、`enum`——Kotlin 全有等价物（`System.currentTimeMillis`、`ArrayDeque`、`data class`、`enum class`）。无 numpy/torch。

**模块边界**：
- 输入：`CognitiveBus.perceive(type, description, confidence)` → `qre.perception.*` 事件。
- 输出：`psi.impulse` 事件（need/action/target/intensity/reason）；`process_pending_insights(batch_size=5)` 提交 Harness。
- 反馈：`harness_execution_result` 事件 → `learn_from_outcome`。

**手机端可行性障碍**：
- 算力：无障碍。单轮 tick <1ms CPU。
- 内存：无障碍。<10KB。
- 后台：**主要障碍**。Android Doze 限制后台 CPU。策略：前台服务（通知栏常驻"数字生命运行中"）+ WorkManager 周期任务（15 分钟最小间隔，用于状态保活）；前台服务内以 0.1-1Hz 运行 tick。电量预算：单次 tick 1ms × 1Hz ≈ 0.1% 电量/小时，可接受。
- 已有差距：现有 [PSILoop.kt](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/laap/PSILoop.kt) 用 `CoroutineScope(Dispatchers.Default)`，无前台服务绑定，app 杀进程即停。需接入 `ForegroundService`。

### 1.3 RSI 递归自我进化技术调研

**核心实现逻辑**：[true_rsi.py](file:///d:/LAAP/laap/evolution/true_rsi.py) 五阶段闭环——
1. **PROPOSE**：`CodeAnalyzer` 在白名单目录扫描优化目标（复杂度/重复模式）。
2. **PATCH**：`PatchGenerator` 生成 AST diff，`SafetyGuard` 校验（黑名单目录、change_ratio≤30%、危险 import）。
3. **SANDBOX**：`ZoneExecutor` 在 Docker 沙箱（512MB / 1 core / 无网络）跑 pytest。
4. **APPROVE**：生成 `approval_token`（24h 过期），等人类放行。
5. **DEPLOY**：`GitIntegrator` 建分支 + commit；失败 `git revert` + 快照回滚。审计落 `~/.laap/true_rsi/audit.jsonl`。

`CognitiveFitnessChecker` 在 sandbox 之外加一层认知适应度评分（惩罚 risky import、网络/eval 暴露、大改动）。`ImpactAssessor` 评估变更影响面。

**数据依赖**：
- 源码树（白名单目录可读）。
- pytest 测试套件（SANDBOX 验证基准）。
- Git（DEPLOY 阶段）。
- 审计日志路径。

**LLM 依赖**：`PatchGenerator` 在主项目可选用 LLM 生成 patch，但有规则 fallback。**手机端可完全去 LLM**——仅用规则/模板生成 patch，对应 memory 第 10 条"优先模板匹配"。

**Python-specific 依赖**：
- `ast` 模块（Python AST）→ Kotlin 无等价物，但手机端 RSI 的目标是 **Kotlin/Java 源码**，需用 Kotlin compiler-embeddable 或 PSI（IntelliJ Platform）做 AST。MVP 阶段可降级为正则 + 缩进感知的轻量 patch。
- `subprocess`（跑 pytest）→ Kotlin `ProcessBuilder`。
- `docker`（ZoneExecutor）→ **Alpine PRoot 沙箱**（[LAAP-Mobile/sandbox/](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/sandbox/)），已有 `ExecutionCoordinator`、`PRootKernel`，可直接复用。这是全本地化的关键利好。
- `git` → JGit（Java 库，纯 Kotlin 可用）。
- `pytest` → JUnit 5 / Kotlin 测试。

**与移动端兼容性**：
- 算力：PROPOSE（扫描）+ SANDBOX（测试）较重，必须在充电 + WiFi 时段跑（WorkManager 约束）。
- 内存：PRoot 沙箱 + 测试进程，预算 200-300MB。中端机可行。
- 电量：单次 RSI 闭环可能 30-60 秒 CPU + IO。限制每周 1-2 次（用户触发或充电时触发）。
- 安全：手机端 RSI **只能修改 LAAP-Mobile 自身代码**（白名单 `org/laap/mobile/`），不可越权。approval_token 必须人工放行（通知弹窗）。

**Triphase RSI 引擎（[triphase_engine/triphase/rsi.py](file:///d:/LAAP/triphase_engine/triphase/rsi.py)）的差异**：Triphase RSI 是"复平面受控轨道"——版本化基因组 + 谱系，三值适应度裁决（灰带不晋升），不变量核（酉子空间），快照原子回滚，违例冻结，元递归（元参数域隔离 + 深度硬上限），只增不改审计账。这是比 True RSI 更严格的范式，建议作为手机端 RSI 的**安全核**，True RSI 作为**工程执行层**。

### 1.4 其他黑科技成熟度、可移植性、移动端融合度评估

| 黑科技 | 源码位置 | 算法原理 | 复杂度/内存 | LLM 依赖 | Python 库 | Kotlin 等价 | 成熟度 | 可移植性 | 移动端融合度 |
|---|---|---|---|---|---|---|---|---|---|
| **Triphase core** | [core.py](file:///d:/LAAP/triphase_engine/triphase/core.py) | 三值↔复相位，亲和度 Re⟨m,q⟩，圆方差 | O(N) / <1KB | 无 | numpy | Multik / ND4J / 手写复数 | 高（107 测试） | 极高 | 极高 |
| **CRM 复谐振记忆** | [memory.py](file:///d:/LAAP/triphase_engine/triphase/memory.py) | 三值巩固 + 谐振检索 + 负相位抗体 + 去相干遗忘 | O(N·D) / N·D·16B | 无 | numpy | Multik | 高 | 高 | 高（D=64 适配） |
| **假设生态** | [hypothesis.py](file:///d:/LAAP/triphase_engine/triphase/hypothesis.py) | Kuramoto 发散/竞争双模 + 证伪负锚点 | O(H²) / H·100B | 无 | numpy | Multik | 中 | 高 | 中（H 限 ≤50） |
| **元认知对偶层** | [metacognition.py](file:///d:/LAAP/triphase_engine/triphase/metacognition.py) | 对象振子 × 过程遥测振子干涉，正交=幻觉信号 | O(1) / <1KB | 无 | numpy | 手写 | 高 | 极高 | 极高 |
| **SPIR 反思** | [reflection.py](file:///d:/LAAP/triphase_engine/triphase/reflection.py) | 分层相位反演 + 收敛判据 + 深度熔断 + 病灶归因 | O(D) / <1KB | 无 | numpy | 手写 | 中 | 高 | 高 |
| **三值代码图** | [codegraph.py](file:///d:/LAAP/triphase_engine/triphase/codegraph.py) | 验证态守恒（未验证依赖禁止完成）+ 改动爆炸半径 | O(V+E) / 图规模 | 无 | numpy | 自建图 | 中 | 中（需 Kotlin AST） | 中 |
| **因果张量** | [causal.py](file:///d:/LAAP/triphase_engine/triphase/causal.py) | 复 CP-ALS + do-算子 + 反事实闭式解 | O(N³) / 高 | 无 | numpy | Multik（参考实现） | 中 | 中（中小规模） | 低（生产级需 GPU） |
| **PGTP 省 token** | [pipeline.py](file:///d:/LAAP/triphase_engine/triphase/pipeline.py) | 三值路由（绕过/短路/全量）+ 负相位警告注入 | O(1) / <1KB | 无 | numpy | 手写 | 高 | 极高 | 极高 |
| **KDA 定态记忆** | [kda.py](file:///d:/LAAP/triphase_engine/triphase/kda.py) | 逐通道遗忘门 + delta 规则（同键覆写）+ O(1) 定态 | O(1) / D·16B | 无 | numpy | Multik | 高 | 极高 | 极高（1000 步 15.6× 压缩） |
| **AttnRes 阶段检索** | [attnres.py](file:///d:/LAAP/triphase_engine/triphase/attnres.py) | 深度轴注意力残差，按需检索替代全量堆叠 | O(L·D) / L·D | 无 | numpy | Multik | 中 | 高 | 高（省 81% token） |
| **LatentMoE 路由** | [latentmoe.py](file:///d:/LAAP/triphase_engine/triphase/latentmoe.py) | 稀疏激活 + Quantile Balancing（无超参） | O(E·D) / E·D | 无 | numpy | Multik | 中 | 高 | 中 |
| **PCG 反幻觉基座** | [grounding.py](file:///d:/LAAP/triphase_engine/triphase/grounding.py) | 证明携带生成：声明三值裁决 + 领域硬不变量 + 弃权一等输出 | O(C·V) / C·V | 无 | numpy | Multik + 规则 | 高 | 高 | 高（4 领域核） |
| **自愈引擎** | [selfheal.py](file:///d:/LAAP/triphase_engine/triphase/selfheal.py) | 基线×观测双振子干涉 + 抗体快路径 + 修复-复测硬闭环 | O(1) / <1KB | 无 | numpy | 手写 | 中 | 高 | 高 |
| **Triphase RSI** | [rsi.py](file:///d:/LAAP/triphase_engine/triphase/rsi.py) | 版本化基因组 + 三值裁决 + 不变量核 + 审计账 | O(G) / G·1KB | 无 | numpy | Multik | 中 | 高 | 高（作为安全核） |
| **True RSI** | [true_rsi.py](file:///d:/LAAP/laap/evolution/true_rsi.py) | 5 阶段闭环 + Docker 沙箱 + approval token | 重 IO | 可选（patch 生成） | ast/subprocess/docker/git | Kotlin AST + PRoot + JGit | 高 | 中（需 AST 替代） | 中（充电时触发） |
| **量子 PSI 循环** | [aris_brain/psi_cycle.py](file:///d:/LAAP/aris_brain/psi_cycle.py) | 概率幅 5 阶段：激发→演化→干涉→测量→学习 | O(D²) / D²·16B | 无 | numpy | Multik | 低（实验性） | 中 | 中（D=64 可行） |
| **数字生命体** | [lifeform_core.py](file:///d:/LAAP/self_model_bridge/lifeform_core.py) | SelfVectorPool(1024D) + Up/Down 通道 + FEP + 零LLM对话 | O(D²) / 1024D·8KB | 可选 | numpy | Multik | 中 | 中 | 中（1024D 偏重） |
| **Aether Orchestration** | [laap/orchestration/](file:///d:/LAAP/laap/orchestration/) | ActorSystem + Petri 网 + OrchestrationKernel | O(A) / A·1KB | 无 | asyncio | Coroutines | 高 | 高 | 高 |
| **Harness Protocol v1.0** | [LAAP-Harness-Protocol-v1.0.md](file:///d:/LAAP/harness/LAAP-Harness-Protocol-v1.0.md) | 数据资产 + URI + 相似度评分 + 匹配阈值 | O(N) / N·1KB | 无 | - | 纯 Kotlin | 高 | 极高 | 极高 |
| **Rust 核心** | [rust_core/](file:///d:/LAAP/rust_core/) | TokenBudget / ToolRegistry / UiaCache / vector_ops | O(1) / <1KB | 无 | PyO3 | JNI / 纯 Kotlin 重写 | 高 | 高 | 高（可 JNI 复用） |

**结论**：Triphase 引擎的 17 个子模块中，14 个为纯 NumPy + O(1) 或 O(N·D) 复杂度，D=64 时单次运算 <1ms，全部可在手机端原生运行。True RSI 受 AST 依赖制约，需 Kotlin AST 替代方案。量子 PSI 与数字生命体的 1024D 向量池为中风险，需降维到 256-512D。

---

## 2. 技术集成方案设计

### 2.1 PSI 大脑循环移动端源码级集成方案

**算法优化**：
- 现有 [PSILoop.kt](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/laap/PSILoop.kt) 已实现 4 阶段（Perceive/Select/Act/Learn），但 `generateImpulse` 是纯规则查表，缺乏**学习闭环**——`applyImpulseToNeeds` 只做 +0.03·intensity 的固定 delta，不依赖实际执行结果。需接入 `harness_execution_result` 事件，让 `learn_from_outcome` 根据真实 success/fitness 反向调整 `memory_associations`（对应 [psi.py#L166](file:///d:/LAAP/laap/orchestration/psi.py) `learn_from_outcome`）。
- 引入 **RateBuffer**（对应 memory 第 4 条）：PSI 1000-2000Hz 与 Harness 0.1-1Hz 频率失配，需事件去重 + 优先级过滤 + 批量聚合。Kotlin 实现用 `Channel<CognitiveEvent>` + `Flow.conflate()` + `sample(1000ms)`。
- **元认知动态调频**：现有 [Metacognition.kt](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/laap/Metacognition.kt) 的 `adaptLoop` 已存在，需校准阈值——低满意度时降到 0.1Hz（省电），高好奇心时升到 2Hz（密集探索），但硬上限 4Hz。

**内存管理**：
- `PSIState` 单例，<10KB，无压力。
- `perception_buffer`：从 Python 的 `deque(maxlen=100)` 改为 `ArrayDeque<CognitiveEvent>(100)`，每条约 200B，总量 <20KB。
- `memory_associations`：`HashMap<String, Float>`，按 LRU 限制 500 条，<20KB。
- 总预算：<100KB，远低于手机端 200-500MB 预算。

**性能调优**：
- tick 协程绑定 `Dispatchers.Default`，单次 tick <1ms，不阻塞 UI。
- 物种库 search 从 O(N) 线性扫描改为 `HashMap<String, List<Species>>` 倒排索引（按 tag/name token），N=1000 时从 ~500μs 降到 ~50μs。
- 持久化：每 60s 或 app 退后台时异步写 `~/.laap/mobile/psi_state.json`（DataStore Preferences），不阻塞 tick。

**前台服务保活**：
- 新建 `PsiForegroundService : Service()`，通知栏常驻"数字生命运行中（PSI cycle=N）"。
- `onStartCommand` 返回 `START_STICKY`，系统杀后自动重启。
- `WorkManager` 周期任务（15min）作为二级保活——前台服务被杀后 WorkManager 唤醒重建。
- 约束：`setRequiresBatteryNotLow(true)` + `setRequiresCharging(false)`，PSI 本身轻量不需充电约束。

### 2.2 RSI 递归自我进化移动端实现架构

**数据存储**：
- 物种库持久化：`~/.laap/mobile/species/code_templates.json`（对齐 [registry.py#L59](file:///d:/LAAP/laap/species/code_templates/registry.py) `DEFAULT_PATH`），用 Room 表 + 全文索引（FTS4）替代 JSON 全量扫描。
- RSI 审计：`~/.laap/mobile/true_rsi/audit.jsonl`（对齐 [true_rsi.py#L82](file:///d:/LAAP/laap/evolution/true_rsi.py) `DEFAULT_AUDIT_PATH`），append-only，Room 表 `rsi_audit`。
- 基因组快照：`~/.laap/mobile/triphase_rsi/snapshots/<genome_id>.json`，用于原子回滚。
- Git 仓库：`/data/data/org.laap.mobile/files/rsi_workspace`，JGit 管理，分支命名 `rsi/<proposal_id>`。

**进化触发**：
- **手动触发**：用户在设置页"自我进化"按钮点击 → 弹窗确认范围 → 走完整 5 阶段。
- **充电+WiFi 自动触发**：WorkManager `OneTimeWorkRequest` 约束 `setRequiresCharging(true) + setRequiresUnmeteredNetwork(true) + setRequiresDeviceIdle(true)`，每周最多 1 次。
- **元认知触发**：PSI 连续 N 轮 competence < 0.3 时，元认知发布 `triphase.rsi.proposal` 事件，进入待审批队列（不自动执行）。

**安全控制（对齐 Triphase RSI 不变量核）**：
- **白名单目录**：`org/laap/mobile/tools/`、`org/laap/mobile/sandbox/`、`org/laap/mobile/laap/`（可进化自身认知模块，但有不变量核保护）。
- **黑名单目录**：`org/laap/mobile/security/`、`org/laap/mobile/sandbox/offload/`（设备控制层，禁止自改）、`org/laap/mobile/laap/TriphaseInvariantCore.kt`（不变量核本身）。
- **MAX_CHANGE_RATIO**：30%（对齐主项目）。
- **approval_token**：24h 过期，通知栏弹窗 `RSIApprovalActivity`，用户生物认证（指纹/面容）后放行。
- **沙箱执行**：复用 [PRootKernel](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/sandbox/PRootKernel.kt) + Alpine rootfs，在 PRoot 内跑 `./gradlew test`（单元测试）+ `./gradlew connectedCheck`（仪器测试，可选）。无网络（PRoot 网络隔离）。512MB 内存上限（PRoot cgroup）。
- **不变量核（酉子空间）**：`TriphaseInvariantCore.kt` 定义安全约束矩阵 U，每次变异前后 `projectToUnitary(genome)` 校验，违例即冻结 + 负相位抗体沉淀。
- **回滚**：JGit `git revert` + 快照恢复，失败时 `git reset --hard <snapshot>`。
- **审计**：`RsiAuditDao.insert()`，只增不改，记录 proposal_id / mutation / sandbox_result / approver / deploy_status / rollback_reason。

### 2.3 其他黑科技集成路径

**模块划分**（建议在 `org.laap.mobile.laap.triphase` 子包下新建）：

```
org.laap.mobile.laap/
├── CognitiveBus.kt              # 已有，扩展 triphase.* 与 harness_execution_result
├── PSILoop.kt                   # 已有，扩展 learn_from_outcome
├── Metacognition.kt             # 已有
├── CognitiveSpeciesLibrary.kt   # 已有，扩展 Room 持久化
├── ArisEngineClient.kt          # 已有
├── MobilePerceptionService.kt   # 已有
├── triphase/
│   ├── Trit.kt                  # 三值枚举 {-1,0,+1}
│   ├── PhaseState.kt            # 复相位态 r·e^{iθ}
│   ├── Affinity.kt              # 复谐振亲和度 Re⟨m,q⟩
│   ├── ComplexResonantMemory.kt # CRM 记忆（D=64）
│   ├── HypothesisEcosystem.kt   # 假设生态（Kuramoto）
│   ├── MetacognitiveMonitor.kt  # 元认知对偶层
│   ├── SpirReflection.kt        # SPIR 反思回路
│   ├── TriphaseCodeGraph.kt     # 三值代码图
│   ├── CausalTensorEngine.kt    # 因果张量（中小规模）
│   ├── TokenPipeline.kt         # PGTP 省 token 管线
│   ├── KdaWorkingMemory.kt      # KDA 定态工作记忆
│   ├── AttnResRetrieval.kt      # AttnRes 阶段检索
│   ├── LatentMoeRouter.kt       # LatentMoE 路由
│   ├── GroundingPcg.kt          # PCG 反幻觉基座
│   ├── SelfHealEngine.kt        # 自愈引擎
│   ├── TriphaseRsiEngine.kt     # Triphase RSI（安全核）
│   └── TriphaseInvariantCore.kt # 不变量核（酉子空间）
├── rsi/
│   ├── TrueRsiEngine.kt         # True RSI 5 阶段
│   ├── CodeAnalyzer.kt          # 白名单扫描
│   ├── PatchGenerator.kt        # AST diff（Kotlin PSI）
│   ├── SafetyGuard.kt           # 黑名单 + change_ratio
│   ├── SandboxTester.kt         # PRoot 沙箱测试
│   ├── ApprovalGate.kt          # approval_token 管理
│   ├── GitIntegrator.kt         # JGit 集成
│   └── RsiAuditDao.kt           # Room 审计表
├── lifeform/
│   ├── SelfVectorPool.kt        # 自我向量池（D=512 降维）
│   ├── UpSalience.kt            # 引擎→自我
│   ├── DownAttention.kt         # 自我→需求
│   └── LifeformCore.kt          # 数字生命体核心
├── harness/
│   ├── HarnessProtocol.kt       # URI 解析 + SHA-256 寻址
│   ├── AssetRegistry.kt         # 资产元数据
│   ├── MatchEngine.kt           # 相似度评分（0.35/0.25/0.20/0.20）
│   └── ComponentAssembler.kt    # 组件组装
└── sync/
    ├── OmegaNetSync.kt          # Ψ-Net 物种同步（桌面端可选）
    ├── MemorySync.kt            # 长期记忆归档同步
    └── SyncContract.kt          # 同步契约定义
```

**接口设计（签名级示例）**：

```kotlin
// Triphase 核心代数（对齐 triphase/core.py）
data class PhaseState(val magnitude: Double, val phase: Double) {
    fun interference(other: PhaseState): Double =
        magnitude * other.magnitude * cos(phase - other.phase)
    fun rotated(delta: Double) = PhaseState(magnitude, phase + delta)
    fun inverted() = rotated(PI)  // SPIR 反思算子
}

enum class Trit(val value: Int) { NEG(-1), NEUTRAL(0), POS(1) }

// CRM 记忆（对齐 triphase/memory.py）
interface ComplexResonantMemory {
    suspend fun store(state: PhaseState, key: String, payload: ByteArray, evidence: Float)
    suspend fun retrieve(query: PhaseState, topK: Int): List<MemoryHit>
    suspend fun consolidate()  // 三值巩固循环
}

// CognitiveBus 事件契约（扩展已有）
object CognitiveBusTopics {
    const val PERCEPTION_MOBILE = "qre.perception.mobile"
    const val PERCEPTION_USER = "qre.perception.user"
    const val PSI_IMPULSE = "psi.impulse"
    const val HARNESS_EXECUTION_RESULT = "harness_execution_result"  // 新增
    const val V12_KERNEL = "v12_kernel"                              // 新增
    const val NEED_DEFICIT = "need.deficit"                          // 新增
    const val EMOTION_VALENCE = "emotion.valence"
    // Triphase 命名空间（对齐 laap/triphase_bridge/topics.py）
    const val TRIPHASE_MEMORY_STORE = "triphase.memory.store"
    const val TRIPHASE_GROUNDING_VERIFY = "triphase.grounding.verify"
    const val TRIPHASE_RSI_PROPOSAL = "triphase.rsi.proposal"
    const val TRIPHASE_SELHEAL_ANOMALY = "triphase.selfheal.anomaly"
    // ... 完整 17 topic
}

// True RSI 5 阶段（对齐 laap/evolution/true_rsi.py）
interface TrueRsiEngine {
    suspend fun propose(directory: String): RsiProposal?
    suspend fun patch(proposal: RsiProposal): PatchResult
    suspend fun sandbox(proposal: RsiProposal): SandboxResult
    suspend fun requestApproval(proposal: RsiProposal): ApprovalToken
    suspend fun applyApproved(proposal: RsiProposal, token: ApprovalToken): DeployResult
    suspend fun rollback(proposal: RsiProposal): RollbackResult
}
```

**与主应用交互**：
- CognitiveBus 作为唯一事件中枢，所有模块通过 `publish/subscribe` 解耦。
- PSI 循环是主驱动，每轮 tick 触发 Triphase 元认知评估、KDA 记忆检索、PGTP 路由。
- ArisEngineClient 作为可选 LLM 表达层，仅在 PGTP 路由为"全量"时调用。
- MobilePerceptionService 产出 `qre.perception.mobile` 事件喂给 PSI。
- ChatViewModel 订阅 `psi.impulse` 与 `triphase.grounding.report` 更新 UI。

### 2.4 各黑科技协同机制

**协同链路（端到端）**：

```
MobilePerceptionService ──qre.perception.mobile──► CognitiveBus
                                                        │
                                                        ▼
                                                    PSILoop.tick()
                                                    ├── Perceive: 读取 NeedState
                                                    ├── Select: 主导驱动 + 生成 Impulse
                                                    │   └── Triphase TokenPipeline.route()
                                                    │       ├── NEG → 跳过（负相位抗体）
                                                    │       ├── NEUTRAL → 短路（KDA 定态记忆）
                                                    │       └── POS → 全量（ArisEngineClient LLM）
                                                    ├── Act: 发布 psi.impulse
                                                    │   └── CognitiveSpeciesLibrary.search()
                                                    │       └── 匹配 → 执行（0-token）
                                                    │       └── 未匹配 → Harness MatchEngine
                                                    │           └── 组装 → 执行
                                                    │   └── 执行结果 → harness_execution_result
                                                    ├── Learn: learn_from_outcome
                                                    │   ├── Triphase MetacognitiveMonitor.assess()
                                                    │   │   └── 正交态 → SPIR 反思 → 病灶归因
                                                    │   ├── Triphase SelfHealEngine（异常时）
                                                    │   ├── Triphase GroundingPcg.verify()
                                                    │   │   └── REFUTED → REJECT + 负相位抗体
                                                    │   │   └── UNVERIFIED → ABSTAIN
                                                    │   │   └── PASS → 证书随文出厂
                                                    │   └── 更新 NeedState + memory_associations
                                                    └── Metacognition.adaptLoop()
                                                        └── 调整 tickIntervalMs / driveWeights
```

**功能互补**：
- **PSI 提供驱动力**（为什么做），**Triphase 提供判断力**（该不该做、做对没有），**Harness 提供执行力**（怎么做），**RSI 提供进化力**（怎么做得更好）。
- **KDA + AttnRes** 解决手机端内存压力——1000 步上下文从 ~2MB 压到 ~130KB（15.6× 压缩 + 81% token 节省）。
- **PCG** 保证手机端离线场景的反幻觉——无 LLM 时用领域硬不变量 + 抗体快路径。
- **SelfHeal** 监控 PSI/Triphase 自身健康，基线×观测振子干涉检测异常。

**系统稳定性**：
- Triphase 不变量核作为**硬约束层**——PSI/RSI 的任何变异不得违反酉子空间，违例冻结。
- RateBuffer 隔离 PSI 高频与 Harness 低频——防止 PSI 风暴淹没执行层。
- 元认知熔断——连续 3 轮正交态（幻觉信号）触发 SPIR 深度反思 + 降频到 0.1Hz。
- 前台服务 + WorkManager 双保活——单点故障后自动恢复。
- 所有变异操作 approval gate——人工门是最后一道防线。

---

## 3. 超级APP工程架构规划

### 3.1 可扩展移动端应用架构

**分层架构（自底向上）**：

```
┌─────────────────────────────────────────────────────────┐
│  UI 层 (Compose)                                         │
│  ChatScreen / IdeScreen / TerminalScreen / SettingsScreen│
│  LaapCognitiveDebugPanel / LifeformDashboard             │
├─────────────────────────────────────────────────────────┤
│  ViewModel 层                                            │
│  ChatViewModel / IdeHomeViewModel / PsiMetricsViewModel  │
├─────────────────────────────────────────────────────────┤
│  应用服务层                                              │
│  PsiForegroundService / RsiWorkManager / SyncService     │
├─────────────────────────────────────────────────────────┤
│  认知内核层 (org.laap.mobile.laap)                       │
│  CognitiveBus / PSILoop / Metacognition                  │
│  triphase/* / rsi/* / lifeform/* / harness/* / sync/*    │
├─────────────────────────────────────────────────────────┤
│  能力层                                                  │
│  CognitiveSpeciesLibrary / ArisEngineClient(LLM)         │
│  MobilePerceptionService / ExecutionCoordinator          │
├─────────────────────────────────────────────────────────┤
│  沙箱层 (org.laap.mobile.sandbox)                        │
│  PRootKernel / RootfsManager / NativeOffloadServer       │
│  20+ OffloadHandler                                      │
├─────────────────────────────────────────────────────────┤
│  数据层 (Room + DataStore)                               │
│  AppDatabase / species / rsi_audit / memory / sync       │
├─────────────────────────────────────────────────────────┤
│  系统层                                                  │
│  Android Runtime / Coroutines / WorkManager / FGS        │
└─────────────────────────────────────────────────────────┘
```

**模块化**：采用 Gradle 多模块（未来），MVP 阶段保持单 module + 包隔离。版本升级时按子包独立演进——`triphase/` 子包版本号对齐 [triphase_engine/pyproject.toml](file:///d:/LAAP/triphase_engine/pyproject.toml)。

**插件化扩展点**：
- `OffloadHandler` 已是插件式（20+ handler），新增认知能力可作为新 handler 注册。
- `CognitiveSpeciesLibrary` 支持运行时 register（物种热加载）。
- `TriphaseGrounding` 的领域核是插件式——`verify_claim / invariants / trust_of` 三接口，可注册新领域（如本地日历/通讯录/健康数据领域核）。

### 3.2 数字生命伙伴核心功能模块划分

**A. 交互接口子系统**：
- 对话：复用 [ChatViewModel.kt](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/ui/chat/ChatViewModel.kt)，订阅 PSI 状态渲染"情绪脸"+ 注意力焦点。
- 语音：[speech/](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/speech/) 已有 ASR/TTS/纠错，接 PSI 情绪调制语调。
- 视觉：[ReadImageTool.kt](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/tools/ReadImageTool.kt) + 未来 CameraX 接入，产出 `qre.perception.visual`。
- 数字生命仪表盘：扩展 [LaapCognitiveDebugPanel.kt](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/ui/chat/LaapCognitiveDebugPanel.kt) 为 `LifeformDashboard`——展示 PSI 循环状态、好奇心指数、信任感指标、胜任感评估（对应 memory 第 15 条）、Triphase 元认知遥测、自我向量相位图。

**B. 数据处理子系统**：
- 感知融合：[MobilePerceptionService.kt](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/laap/MobilePerceptionService.kt) 聚合传感器/位置/通知/剪贴板/电量/网络，输出标准化 `Perception` 事件。
- 记忆分层：短时（KDA 定态，O(1)）→ 工作（CRM 复谐振，D=64）→ 长期（Room + FTS，对齐 [laap/memory/hierarchical.py](file:///d:/LAAP/laap/memory/hierarchical.py)）→ 归档（可选同步到桌面）。
- 反幻觉：所有 LLM 输出过 `GroundingPcg.verify()`，REFUTED 拒绝、UNVERIFIED 弃权、PASS 带证书。

**C. 学习进化子系统**：
- 在线学习：PSI `learn_from_outcome` 每轮更新需求/调制器/记忆关联。
- 巩固学习：夜间（充电+空闲）WorkManager 跑 `ComplexResonantMemory.consolidate()` + `MemoryForgettingEngine`（对齐 [laap/memory/forgetting/](file:///d:/LAAP/laap/memory/forgetting/)）。
- RSI 进化：每周 1 次（充电+WiFi），True RSI + Triphase RSI 双层保护。
- 物种库增长：每次成功执行 `CognitiveSpeciesLibrary.register()` 新模板，对齐 memory 第 37 条。

### 3.3 应用性能优化方案

**内存预算（总 200-500MB）**：
- PSI + CognitiveBus：<1MB
- Triphase 引擎（D=64）：CRM 1MB + KDA 1MB + 元认知 <100KB ≈ 2MB
- SelfVectorPool（D=512 降维）：2MB
- 物种库（Room 缓存 1000 条）：5MB
- PRoot 沙箱（运行时）：100-150MB
- Compose UI + 资源：80-120MB
- LLM 推理（可选，ONNX Runtime Mobile）：50-100MB（按需加载）
- 总计：<300MB，中端机（6GB+）舒适。

**CPU 调度**：
- PSI tick：`Dispatchers.Default`，1ms/轮，不争抢 UI 线程。
- Triphase 重算（因果张量、假设生态）：`Dispatchers.Default` 但限并发 2。
- RSI SANDBOX：`Dispatchers.IO`，PRoot 子进程独立。
- LLM 推理：`Dispatchers.Default` + `limitedParallelism(1)`，单线程防过载。

**冷启动优化**：
- CognitiveBus / PSILoop 懒初始化——app 启动只拉 UI，PSI 在前台服务启动时才 init。
- Triphase 子模块按需加载——`GroundingPcg` 仅在 LLM 输出时加载，`CausalTensorEngine` 仅在因果查询时加载。
- 物种库 Room 数据库懒开——首次 ChatViewModel 才触发。

**电池优化**：
- PSI 默认 1Hz，可配 0.1/0.5/1/2Hz（用户在设置页调）。
- Doze 模式下 WorkManager 周期任务降到 15min 一次，仅做状态保活 + 记忆巩固。
- LLM 推理仅在 app 前台或用户明确触发时进行。
- RSI 仅充电+WiFi 时触发。

### 3.4 应用安全架构

**用户数据安全**：
- 所有本地数据 Room 加密（SQLCipher）——记忆/物种/审计/自我向量。
- DataStore Preferences 存敏感配置（LLM API key），用 Android Keystore 加密。
- LLM API key 不出本地——ArisEngineClient 直连 provider，不经过中间服务器（除非用户启用桌面中继）。
- 同步到桌面端时端到端加密（X25519 密钥协商，对应 [laap/security/crypto/keys.py](file:///d:/LAAP/laap/security/crypto/keys.py)）。

**黑科技可控性**：
- **RSI approval gate**：所有代码自改必须用户生物认证放行（指纹/面容）。
- **不变量核**：`TriphaseInvariantCore.kt` 编译为独立模块，RSI 不可修改。
- **审计账**：`rsi_audit` 表只增不改，用户可在设置页查看完整进化历史。
- **回滚能力**：任何 RSI 变更可一键 revert（JGit）。
- **能力边界**：OffloadHandler 列表用户可勾选启用/禁用——位置/通讯录/通知等敏感能力默认关闭。
- **沙箱隔离**：RSI 测试在 PRoot 内，无网络、无主存储访问，仅限 `rsi_workspace`。

---

## 4. 开发实施计划

### 4.1 分阶段开发计划

按里程碑组织（不估日期，对齐 memory "Avoid giving time estimates"）：

**Milestone M1：MVP（最小可用全本地化）**
- 目标：PSI 循环独立运行，无桌面依赖，基础认知闭环。
- 交付物：
  - [PSILoop.kt](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/laap/PSILoop.kt) 接入 `learn_from_outcome` + `harness_execution_result` 事件。
  - `PsiForegroundService` 前台服务保活。
  - CognitiveBus 扩展 `triphase.*` 命名空间（17 topic）。
  - CognitiveSpeciesLibrary Room 持久化（替代内存 Map）。
  - PSI 状态持久化到 DataStore。
  - `LifeformDashboard` UI（PSI 循环状态 + 5 指标）。
- 风险点：前台服务在国产 ROM（MIUI/EMUI/ColorOS）被杀——需文档化厂商白名单设置指引。
- 回退方案：前台服务失效时降级为 WorkManager 15min 周期任务，PSI 降频到 0.01Hz。

**Milestone M2：Alpha（核心黑科技跑通）**
- 目标：Triphase 引擎核心 7 模块（core/memory/metacognition/reflection/grounding/kda/pipeline）Kotlin 移植完成，接入 PSI。
- 交付物：
  - `triphase/` 子包 7 个核心 Kotlin 文件 + 单元测试（对齐 107 项原测试）。
  - `GroundingPcg` 接入 ChatViewModel——所有 LLM 输出过 PCG 验证。
  - `KdaWorkingMemory` 替换 ChatViewModel 的上下文管理（15.6× 压缩）。
  - `TokenPipeline` 路由 ArisEngineClient 调用（NEG 跳过/NEUTRAL 短路/POS 全量）。
  - `MetacognitiveMonitor` 接入 PSI Learn 阶段——正交态触发反思。
- 风险点：Multik/ND4J 在 Android 的兼容性——需验证 ARM64 ABI。
- 回退方案：Multik 不可用时手写 `Complex` 运算（D=64 性能足够）。

**Milestone M3：Beta（协同 + 优化）**
- 目标：Triphase 全 17 模块 + True RSI + 数字生命体 + 桌面同步。
- 交付物：
  - `triphase/` 全 17 模块 + 剩余 10 模块（hypothesis/codegraph/causal/attnres/latentmoe/selfheal/rsi/worldmodel/harness）。
  - `rsi/` 子包——True RSI 5 阶段 + PRoot 沙箱测试 + JGit + approval gate。
  - `lifeform/` 子包——SelfVectorPool(D=512) + Up/Down 通道。
  - `sync/` 子包——Ω-Net 物种同步 + 记忆归档到桌面（可选）。
  - `HarnessProtocol` + `MatchEngine` 接入 CognitiveSpeciesLibrary。
  - 性能调优——内存 <300MB，PSI tick <2ms，冷启动 <3s。
- 风险点：RSI 在 PRoot 内跑 gradle 测试的稳定性——Alpine + JDK 可能缺依赖。
- 回退方案：RSI SANDBOX 降级为仅静态分析（Kotlin PSI）+ 编译检查，不跑全测试。

**Milestone M4：GA（生产就绪）**
- 目标：全功能全本地化数字生命伙伴，GPL v3 开源。
- 交付物：
  - 完整文档（用户手册 + 开发者指南 + 安全白皮书）。
  - 全平台测试（主流 Android 厂商 ROM 兼容矩阵）。
  - F-Droid 上架（GPL v3 合规）。
  - 桌面端同步节点参考实现（laap-netlify 侧）。

### 4.2 技术验证方案

**核心黑科技原型验证清单**：

| 验证项 | 验证方法 | 通过标准 | 优先级 |
|---|---|---|---|
| PSI 前台服务保活 | 杀 app 后台 1 小时 | PSI cycle 持续递增 | M1 |
| CognitiveBus 事件契约 | 单元测试 publish/subscribe | 17 triphase topic 全通 | M1 |
| 物种库持久化 | 杀 app 重启后 search | 物种不丢失 | M1 |
| Triphase core 代数 | 107 项测试 Kotlin 移植 | 100% 通过 | M2 |
| CRM 记忆 D=64 | 存 1000 条 + retrieve topK | 召回率 ≥ Python 版 95% | M2 |
| PCG 反幻觉 | 100 条 LLM 输出验证 | REFUTED/UNVERIFIED/PASS 分类正确 | M2 |
| KDA 15.6× 压缩 | 1000 步对话上下文 | 内存 ≤ Python 版 | M2 |
| True RSI 闭环 | 1 次 propose→deploy | 审计账完整，可回滚 | M3 |
| PRoot 沙箱跑 gradle | 在 Alpine 内 `./gradlew test` | 测试通过 | M3 |
| 桌面端物种同步 | 手机→桌面→手机 | 物种 ID 一致 | M3 |
| 300MB 内存上限 | Monitored 开启 1 小时 | RSS < 350MB | M3 |
| 0.1Hz Doze 保活 | Doze 模式 8 小时 | 至少 1 次 tick | M4 |

### 4.3 开发资源配置

**人员分工建议**（按角色，不按人头）：
- 认知内核工程师：负责 `triphase/` + `PSILoop` 移植，需熟练 Kotlin Coroutines + 复数运算。
- Android 平台工程师：负责前台服务 + WorkManager + Room + OffloadHandler，需 Android 后台机制经验。
- RSI 安全工程师：负责 `rsi/` + 不变量核 + 审计，需安全沙箱 + Git 内部经验。
- UI 工程师：负责 `LifeformDashboard` + ChatViewModel 集成，需 Compose 经验。
- 测试工程师：负责跨 ROM 兼容矩阵 + 性能基准。

**技术栈选择**：
- 语言：Kotlin 17（对齐项目设定）。
- UI：Jetpack Compose（已有）。
- 异步：Kotlin Coroutines + Flow（已有）。
- 数值计算：Kotlin Multik（首选，纯 Kotlin 多平台）+ ND4J（备选，JVM）。
- 数据库：Room + SQLCipher + FTS4。
- 持久化：DataStore Preferences。
- 后台：WorkManager + Foreground Service。
- Git：JGit 6.x。
- AST：Kotlin Compiler Embeddable（M3 起，MVP 用正则）。
- LLM 推理（可选）：ONNX Runtime Mobile + llama.cpp Android（通过 JNI）。
- 沙箱：复用已有 PRootKernel + Alpine rootfs。

**开发环境**：
- Android Studio（最新稳定版）。
- JDK 17。
- Android SDK 35（targetSdk）。
- NDK（如需 JNI 接 llama.cpp）。
- 测试机：至少 1 台中端（6GB RAM，Android 13+）+ 1 台低端（4GB RAM，Android 8.0，验证 minSdk=26）。

### 4.4 代码规范与质量控制标准

- **语言**：代码注释与文档用英文（对齐 codebase 现状），用户面 UI 文案与文档用中文。
- **格式**：ktlint + detekt（规则对齐 [laap/.ruff_cache](file:///d:/LAAP/.ruff_cache) 的 Python ruff 严格度）。
- **命名**：Kotlin PascalCase（类）/ camelCase（函数属性）/ SCREAMING_SNAKE_CASE（常量）。包名全小写 `org.laap.mobile.*`。
- **日志**：标准化标签 `[OK]/[ERROR]/[WARN]/[INFO]/[TOKEN]/[SERVER]/[COMPONENTS]/[BLOCKS]/[COMPLETE]`（对齐 memory 第 35 条），禁用 emoji。
- **测试覆盖率**：核心模块（triphase/ rsi/ PSILoop）≥ 80% 行覆盖；UI 模块 ≥ 50%。
- **CognitiveBus 事件命名**：严格对齐 memory 第 17 条 `triphase.{domain}.{action}` 与第 3 条 `qre_*/v12_kernel/need_*/emotion_*/harness_execution_result`。
- **GPL v3 合规**：所有源文件头部加 `This file is part of LAAP Mobile, licensed under GPL v3.`（对齐已有 [CognitiveBus.kt#L7](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/laap/CognitiveBus.kt)）。
- **审计追溯**：所有研究论文主张必须能追溯到 [harness/](file:///d:/LAAP/harness/) 或 [.github/harness/](file:///d:/LAAP/.github/harness/) 的具体文件路径（对齐 memory 第 7 条）。

---

## 5. 测试与优化策略

### 5.1 黑科技专项测试方案

**功能测试**：
- Triphase 17 模块逐个移植测试——对齐 [triphase_engine/tests/](file:///d:/LAAP/triphase_engine/tests/) 的 107 项用例，Kotlin 版必须 100% 通过。
- PSI 闭环测试——模拟 1000 轮 tick，验证需求/情绪/调制器收敛性。
- True RSI 5 阶段端到端——从 propose 到 deploy 完整跑通，验证审计账 + 回滚。
- PCG 反幻觉——构造 100 条已知幻觉（生物医学/金融/法律/政务），验证 REFUTED 拦截率 ≥ 95%。

**性能测试**：
- PSI tick 延迟：P50 < 1ms，P99 < 5ms。
- CRM retrieve topK=10：P50 < 10ms（D=64，N=1000）。
- KDA 1000 步上下文内存：< 200KB。
- 冷启动到 PSI 首 tick：< 3s（中端机）。
- RSI 单次闭环（不含 SANDBOX）：< 30s；含 SANDBOX：< 5min。

**兼容性测试**：
- Android 版本：minSdk 26（8.0）到 targetSdk 35（15）每版本至少 1 台。
- 厂商 ROM：原生 Pixel / MIUI / EMUI / ColorOS / OneUI / vivo OriginOS——重点测前台服务保活。
- ABI：arm64-v8a（主）/ armeabi-v7a（低端机降级，D=32）。
- 内存档位：4GB / 6GB / 8GB / 12GB——验证 300MB 预算。

### 5.2 用户体验测试计划

**数字生命伙伴实用性**：
- 7 日日记研究——用户每日与 LAAP-Mobile 交互，记录 PSI 情绪/注意力是否"鲜活"。
- 对话连贯性——KDA 定态记忆下，1000 轮对话后是否仍记得前文关键信息。
- 反幻觉感知——用户主动构造"陷阱问题"，PCG 是否 ABSTAIN 而非编造。
- RSI 透明度——用户能否在 `LifeformDashboard` 理解"它在自己改了什么"。

**交互友好性**：
- 前台服务通知——是否打扰？可否静默？
- RSI approval 弹窗——是否干扰主流程？是否可延后？
- `LifeformDashboard` 信息密度——5 指标 + 元认知遥测 + 自我向量相位图是否过载？

### 5.3 持续优化机制

**基于用户反馈**：
- 内测渠道（Telegram/飞书）收集 PSI 行为异常案例。
- RSI 审计账众包——用户可选匿名上传 RSI 进化历史，用于不变量核规则迭代。
- 物种库共享——用户可选上传优质物种到 Ψ-Net（桌面端中继），其他用户可下载。

**基于使用数据**：
- 本地匿名遥测（用户可选开启）——PSI tick 频率分布、PCG 拦截率、RSI 闭环成功率、内存峰值。
- 元认知遥测直通优化——`MetacognitiveMonitor.assess()` 的 `align_cos` / `min_meta_strength` 阈值在真实 trace 上校准（对齐 [triphase/README.md#L133](file:///d:/LAAP/triphase_engine/README.md) 已知边界）。

**迭代流程**：
- 双周迭代——M1/M2 阶段每两周一次内部 demo。
- 物种库版本化——每次 release 带 `species_baseline_vN.json`，用户可回退。
- Triphase 引擎版本对齐——`triphase/` 子包版本号严格对齐 [triphase_engine/pyproject.toml](file:///d:/LAAP/triphase_engine/pyproject.toml)。

### 5.4 监控与日志系统

**黑科技运行状态**：
- `LaapCognitiveDebugPanel`（已有）扩展为实时仪表盘——PSI cycle/need/emotion、Triphase metacog verdict、KDA memory size、RSI audit tail。
- 本地日志：`~/.laap/mobile/logs/psi.jsonl` / `triphase.jsonl` / `rsi.jsonl`，按日轮转（对齐 [aris_brain/log_rotation.py](file:///d:/LAAP/aris_brain/log_rotation.py)）。
- logcat 标签：`LAAP-PSI` / `LAAP-TRIPHASE` / `LAAP-RSI` / `LAAP-BUS`，可 `adb logcat -s LAAP-PSI:V` 过滤。

**性能指标**：
- `SystemResourceMonitor`（已有，[ChatScreen.kt](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/ui/chat/ChatScreen.kt) 引用）扩展——记录每轮 tick 的 CPU/内存/电量。
- ANR 检测——PSI tick 必须在主线程外，超 5ms 触发警告。
- 内存泄漏——LeakCanary 集成，PSI/Triphase 单例必须无 Activity Context 引用。

---

## 6. 项目风险管理

### 6.1 潜在风险识别

**性能瓶颈**：
- 风险 R1：CRM 记忆在 D=64 + N>10000 时 retrieve 慢（O(N·D) 矩阵乘）。
- 风险 R2：因果张量 `complex_cp_als` 在大规模数据下不可行（[README.md#L130](file:///d:/LAAP/triphase_engine/README.md) 已知边界）。
- 风险 R3：PRoot 沙箱跑 gradle 测试启动慢（Alpine + JDK 冷启动 30s+）。
- 风险 R4：1024D SelfVectorPool 在低端机内存压力大。

**兼容性**：
- 风险 R5：国产 ROM（MIUI/EMUI）杀前台服务——PSI 保活失败。
- 风险 R6：Multik/ND4J 在某些 ABI 缺原生库。
- 风险 R7：minSdk 26 设备 SQLCipher 性能差。
- 风险 R8：Kotlin Compiler Embeddable 在手机端内存占用过大（>200MB）。

**资源消耗**：
- 风险 R9：RSI 闭环耗电过高，用户投诉。
- 风险 R10：PRoot rootfs 占用存储过大（Alpine ~80MB + JDK ~200MB）。
- 风险 R11：物种库无限增长导致 Room 膨胀。

**安全/伦理**：
- 风险 R12：RSI 自改代码引入漏洞——不变量核被绕过。
- 风险 R13：PCG 领域核误判导致误拒绝/误通过。
- 风险 R14：LLM 输出泄露用户隐私到第三方 provider。

### 6.2 风险应对预案

| 风险 | 应对预案 | 备选技术方案 |
|---|---|---|
| R1 CRM 慢 | 限制 N≤5000，超限触发巩固+归档 | 用 HNSW 近似检索替代暴力扫 |
| R2 因果张量 | 手机端仅跑中小规模，大规模卸载桌面 | TT 分解替代 CP-ALS |
| R3 PRoot 慢 | RSI SANDBOX 降级为静态分析 | 仅编译检查不跑测试 |
| R4 1024D 重 | 降维到 D=256 | PCA 投影 |
| R5 ROM 杀服务 | 文档化白名单设置 + 引导用户自启 | WorkManager 兜底 + 推送唤醒 |
| R6 Multik ABI | 手写 Complex 运算 | 纯 Kotlin 复数类 |
| R7 SQLCipher 慢 | 非敏感数据用明文 Room | SQLCipher 仅加密记忆/审计表 |
| R8 Kotlin PSI 重 | MVP 用正则，M3 用 PSI | 服务器端 AST（桌面卸载） |
| R9 RSI 耗电 | 严格充电+WiFi 约束 | 用户配额（每周 1 次硬上限） |
| R10 rootfs 大 | 按需下载 JDK 组件 | 用原生 Android Runtime 跑测试 |
| R11 物种膨胀 | LRU 淘汰 + 质量分低于阈值归档 | 用户配额（10000 物种上限） |
| R12 RSI 漏洞 | 不变量核编译独立模块 + approval gate | RSI 永久禁用开关 |
| R13 PCG 误判 | 阈值可调 + 用户反馈回路 | 弃权优先于拒绝（宁弃权不误拒） |
| R14 隐私泄露 | ArisEngineClient 本地优先 + 用户可禁云端 | 本地 ONNX 小模型替代 |

### 6.3 技术难点攻关机制

**核心难点 1：Kotlin AST 替代 Python ast**
- 攻关路径：MVP 正则 + 缩进感知 → M3 Kotlin Compiler Embeddable（PSI）→ M4 服务器端 AST 卸载。
- 验证标准：能正确解析 Kotlin 文件、生成 unified diff、计算 change_ratio。

**核心难点 2：Triphase 复数运算性能**
- 攻关路径：Multik → 手写 Complex + SIMD → JNI 调 rust_core。
- 验证标准：CRM retrieve topK=10 在 N=1000 时 P99 < 20ms。

**核心难点 3：前台服务跨 ROM 保活**
- 攻关路径：标准 Foreground Service → 厂商自启白名单引导 → WorkManager + AlarmManager 组合 → 推送唤醒（桌面端中继）。
- 验证标准：8 小时后台 PSI cycle 递增 ≥ 100。

**核心难点 4：PRoot 内跑 Kotlin 测试**
- 攻关路径：Alpine + OpenJDK → 仅跑 `./gradlew testDebugUnitTest` → 失败时降级为 host 端编译检查。
- 验证标准：1 次 RSI 闭环能在 PRoot 内完成 propose→sandbox→deploy。

**攻关流程**：每个难点指定 owner，双周 review，失败时启动备选方案。所有攻关决策记录在 `docs/decision-records/` ADR 文件。

---

## 7. 交付标准与验收 criteria

### 7.1 各黑科技验收标准

**PSI 大脑循环**：
- 功能完整性：5 驱动 + 5 调制 + PAD 情绪 + 4 阶段闭环（Perceive/Select/Act/Learn）全部实现。
- 性能指标：tick P99 < 5ms；1000 轮连续运行无状态泄漏。
- 稳定性：8 小时前台服务保活成功率 ≥ 95%（Pixel 设备）；Doze 模式下 WorkManager 唤醒成功率 ≥ 90%。
- 持久化：杀 app 重启后 PSI 状态恢复，cycleCount 连续。

**RSI 递归自我进化**：
- 功能完整性：5 阶段（PROPOSE/PATCH/SANDBOX/APPROVE/DEPLOY）+ 回滚 + 审计。
- 性能指标：单次闭环（不含 SANDBOX）< 30s；SANDBOX < 5min。
- 安全性：不变量核违例 100% 冻结；黑名单目录 100% 拒绝；approval_token 24h 过期 100% 执行。
- 审计：`rsi_audit` 表只增不改，可追溯完整进化谱系。

**Triphase 引擎**：
- 功能完整性：17 模块全部 Kotlin 移植 + 单元测试。
- 性能指标：core 代数 P99 < 1ms；CRM retrieve topK=10 P99 < 20ms（N=1000, D=64）。
- 兼容性：107 项原测试 100% 通过。
- 反幻觉：PCG 在 100 条已知幻觉上 REFUTED 拦截率 ≥ 95%，零误拒。

**CognitiveBus**：
- 功能完整性：`qre_*`/`v12_kernel`/`need_*`/`emotion_*`/`harness_execution_result` + 17 `triphase.*` topic 全部实现。
- 性能指标：publish/subscribe P99 < 1ms。
- 稳定性：10000 事件无丢失（RateBuffer 验证）。

### 7.2 数字生命伙伴核心指标

- **响应速度**：用户消息到首字符 < 500ms（KDA 短路）；到完整回应 < 2s（PGTP 全量）；PSI tick 不阻塞 UI。
- **学习能力**：1000 轮对话后关键信息召回率 ≥ 90%；RSI 每周至少 1 次有效进化（用户触发或自动）；物种库每周增长 ≥ 5 个新模板。
- **交互自然度**：PSI 情绪与对话语境匹配率（用户主观评分）≥ 80%；PCG ABSTAIN 比例 5-15%（不过度弃权）；元认知反思触发后回应质量提升（用户评分）≥ 15%。
- **续航**：PSI 1Hz 运行 24 小时电量消耗 ≤ 5%；RSI 单次闭环 ≤ 10% 电量。
- **内存**：稳态 RSS < 300MB（中端机）；峰值 < 400MB（RSI SANDBOX 时）。

### 7.3 项目交付物清单

**源代码**：
- `org.laap.mobile.laap` 完整子包（CognitiveBus/PSILoop/Metacognition/CognitiveSpeciesLibrary/ArisEngineClient/MobilePerceptionService 扩展版）。
- `org.laap.mobile.laap.triphase` 17 模块 Kotlin 实现 + 测试。
- `org.laap.mobile.laap.rsi` True RSI 5 阶段 + 不变量核 + 审计。
- `org.laap.mobile.laap.lifeform` 数字生命体核心。
- `org.laap.mobile.laap.harness` Harness Protocol + MatchEngine。
- `org.laap.mobile.laap.sync` 桌面同步契约。
- `PsiForegroundService` + `RsiWorkManager` + `SyncService`。

**技术文档**：
- 本文档（集成规划方案）。
- `docs/architecture/laap-mobile-architecture.md`——详细架构图与数据流。
- `docs/triphase/kotlin-port-guide.md`——Triphase Kotlin 移植指南。
- `docs/rsi/safety-model.md`——RSI 安全模型白皮书。
- `docs/decision-records/`——ADR 决策记录。
- `docs/android-rom-compat.md`——厂商 ROM 兼容矩阵。

**测试报告**：
- 107 项 Triphase 单元测试报告（Kotlin 版）。
- 跨 ROM 兼容测试报告（10+ 设备）。
- 性能基准报告（PSI tick / CRM retrieve / KDA 压缩 / RSI 闭环）。
- PCG 反幻觉评测报告（4 领域核 × 100 案例）。
- 7 日用户日记研究报告。

**用户手册**：
- `docs/user-guide/getting-started.md`——首次使用指南。
- `docs/user-guide/lifeform-dashboard.md`——数字生命仪表盘解读。
- `docs/user-guide/rsi-approval.md`——RSI 审批流程与安全须知。
- `docs/user-guide/rom-whitelist.md`——各厂商自启白名单设置。
- `docs/user-guide/desktop-sync.md`——可选桌面端同步配置。

---

## 附录 A：术语表

| 术语 | 定义 |
|---|---|
| PSI | PsiTheory 风格的认知状态机，基于需求缺口 × 调制器驱动行为 |
| RSI | Recursive Self-Improvement，递归自我改进 |
| True RSI | 代码级 RSI 闭环（PROPOSE/PATCH/SANDBOX/APPROVE/DEPLOY） |
| Triphase | 三值 {-1,0,+1} ↔ 复相位 AGI 框架 |
| CRM | Complex Resonant Memory，复谐振记忆 |
| KDA | Kimi Delta Attention，定态工作记忆 |
| AttnRes | Attention Residual，阶段检索 |
| LatentMoE | Stable Latent Mixture of Experts |
| PCG | Proof-Carrying Generation，证明携带生成（反幻觉） |
| SPIR | 分层相位反思路径 |
| PGTP | Phase-Guided Token Pipeline，省 token 管线 |
| CognitiveBus | 认知事件总线，publish/subscribe 模型 |
| Harness | 白盒工程框架，模板匹配 + 组件组装 |
| Ψ-Net / Omega-Net | 跨实例物种同步网络 |
| ArisEngineClient | LLM 表达层客户端（可选） |
| PRoot | User-space chroot，Alpine Linux 沙箱 |
| 不变量核 | 酉子空间，安全约束不进入 RSI 搜索空间 |
| approval_token | RSI 人工审批令牌，24h 过期 |

## 附录 B：关键源码引用清单

- LAAP 主项目根：[d:\LAAP](file:///d:/LAAP/)
- LAAP Python 后端：[laap/](file:///d:/LAAP/laap/)
- Triphase 引擎：[triphase_engine/](file:///d:/LAAP/triphase_engine/)
- ARIS 大脑：[aris_brain/](file:///d:/LAAP/aris_brain/)
- 自我模型桥接：[self_model_bridge/](file:///d:/LAAP/self_model_bridge/)
- Rust 核心：[rust_core/](file:///d:/LAAP/rust_core/)
- Harness 协议：[harness/LAAP-Harness-Protocol-v1.0.md](file:///d:/LAAP/harness/LAAP-Harness-Protocol-v1.0.md)
- Harness v2 AGI：[.github/harness/-harness-v2-agi/](file:///d:/LAAP/.github/harness/-harness-v2-agi/)
- LAAP-Mobile：[LAAP-Mobile/](file:///d:/LAAP/LAAP-Mobile/)
- 已有 Kotlin 认知模块：[LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/laap/](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/laap/)
- PRoot 沙箱：[LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/sandbox/](file:///d:/LAAP/LAAP-Mobile/src/android/app/src/main/java/org/laap/mobile/sandbox/)
- 项目记忆：[project_memory.md](file:///c:/Users/user/.trae-cn/memory/projects/-d-LAAP/project_memory.md)

---

**文档结束**
