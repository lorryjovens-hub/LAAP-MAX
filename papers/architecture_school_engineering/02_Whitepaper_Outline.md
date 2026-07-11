# 架构学派技术白皮书（大纲）

**版本**：v0.9（大纲稿）
**发布日期**：2026-07-05
**作者**：LAAP 架构学派研究组
**配套论文**：《架构学派：通过认知解构与白盒工程迈向 AGI/ASI 的新路径》（上篇第 1–6 章 / 下篇第 7–14 章）
**审计依据**：`audit_findings.json`（35 条结构化审计发现）
**文档性质**：技术白皮书大纲（含协议族字段级规范与工程护栏状态机）

---

## 总览与定位

### 白皮书目的

本白皮书的核心目的是把已发表的两篇论文（Paper 1 与 Paper 2，合计约 29 万字）所揭示的 7 项突破性发现与 7 项未来展望，从"学术论证"形态转化为"工程规范"形态。论文回答的是"为什么"——为什么 LLM 必须被降级为器官、为什么对齐必须前移到推理阶段、为什么生命体运行时是不可绕过的范式；白皮书回答的是"怎么做"——协议族字段如何定义、状态机如何转移、错误码如何编排、版本如何兼容。两者构成同一思想体系的两个侧面：论文是论证基，白皮书是规范基。

本白皮书并不试图穷举所有实现细节，而是以"字段级规范 + 状态机 + 错误码 + 版本兼容"四件套的方式锁定协议族与工程护栏的可审计边界，使任何第三方实现者只要遵循本规范即可与 LAAP 参考实现互操作。配套的参考实现代码位于 `d:\LAAP\harness\` 与 `d:\LAAP\.github\harness\-harness-v2-agi\src\`，全部为白盒可审计的 Python 代码。

### 目标读者

本白皮书面向四类读者：

1. **架构师**——需要在系统设计层面理解七层认知架构、三层 AGI 内核与八协议族的分层职责。
2. **协议设计者**——需要逐字段阅读协议族规范，并在自有运行时中实现兼容适配层。
3. **对齐工程师**——需要理解 AlignmentGuard 六维检查、KL 漂移监控与不可变哈希注册表的工程语义。
4. **AI Safety 研究者**——需要将"推理时对齐工程化"与传统 RLHF/Constitutional AI 路径进行范式级对比。

### 与论文的关系

论文是 why，白皮书是 how。论文用审计发现（AF-001 至 AF-035）证明架构学派的技术可行性，白皮书则把这些审计发现固化为字段、状态、错误码与版本号。具体对应关系如下：论文第 6 章（七层认知架构与三层 AGI 内核）对应白皮书第 3 章；论文第 8 章（生命体运行时与全栈协议族）对应白皮书第 4、8 章；论文第 7 章（对齐工程学）对应白皮书第 5、9 章；论文第 5 章（白盒匹配范式）对应白皮书第 6 章；论文第 9 章（MeMo 记忆即模型）对应白皮书第 7 章。本白皮书的所有量化数据均与 `audit_findings.json` 严格一致，不存在论文外的臆造数字。

### 7 项突破性发现（论文已揭示）

依据 Paper 1/2 与 35 条审计发现，架构学派在工程层面揭示 7 项突破性发现：

1. **LLM 主体性消解**（AF-029、AF-030）——LLM 从"大脑"被降级为"声带/语言皮层"，承担感知层 90% 工作的是 0-Token 确定性算法，LLM 仅在执行层做语义缝合。智能不是模型的属性，而是架构的属性。
2. **0-Token 确定性算法霸权**（AF-026、AF-027）——正则/CSS 解析/关键词打分承担感知层 90% 工作，实测 Token 节省率 98.2%、生成速度 57×、σ 稳定性 5×（传统 σ≈15，LAAP σ≈3）。
3. **白盒匹配取代黑盒生成**（AF-001 至 AF-004）——MatchScore 四维加权（α=0.35/β=0.25/γ=0.20/δ=0.20）+ 三级阈值（PERFECT=0.90/GOOD=0.75/AVAILABLE=0.60）+ 四级降级链。
4. **因果阶梯落地**（AF-006、AF-007、AF-008）——do-演算 Pearl 三规则 + 反事实三步法（溯因→行动→预测）+ 设计领域 18 条因果边。
5. **对齐前移到推理阶段**（AF-011 至 AF-015）——AlignmentGuard 六维检查 + KL 漂移自动回滚（threshold=0.5）+ MEMO_ALLOWED_PATHS 白名单。
6. **MeMo 记忆即模型**（AF-022、AF-023）——Qwen2.5-0.5B SFT（3 epochs，lr=1e-4）+ 三阶段查询协议，检索成本 O(1) 与语料规模解耦。
7. **生命体运行时 + 协议族**（AF-032）——意识-身体双层分离 + 跨端热迁移 < 2s + 八协议族标准化。

### 7 项未来展望（论文已揭示）

依据 Paper 2 第 13 章未来方向，架构学派提出 7 项未来展望：

1. **协议族标准化**——LIFE/EVO/ID/COOP/SYNC/COM/TOOL/UI 八协议形式化规范、参考实现、互操作测试套件。
2. **生命体运行时验证**——M6 阶段 260 人时/56 天验证跨端热迁移 < 2s 端到端。
3. **跨端热迁移工程化**——PSI 量子态序列化、五层记忆同步、未完成任务快照、网络延迟四个子问题。
4. **因果引擎完善**——18 条因果边扩展到更多领域，do-演算引入贝叶斯后验。
5. **世界模型补全**——格式塔六法则补充视觉验证机制，design_physics 扩展动效/信息架构维度。
6. **RSI 测试落地**——MetaHarness AST 自省集成 pytest，AlignmentGuard 六维检查端到端验证。
7. **AI Safety 工程化标准化**——对标 ISO 26262 功能安全，建立对齐 CI/CD 流水线。

### 配图清单

本白皮书配套 4 幅配图，存放于 `figures/` 目录：

| 编号 | 文件名 | 内容 |
|---|---|---|
| 图 1 | `protocol_stack.png` | 协议族栈架构图（8 协议分层堆叠） |
| 图 2 | `alignment_state_machine.png` | 对齐守卫状态机（六维检查 + KL 5 状态） |
| 图 3 | `cognitive_architecture.png` | 七层认知架构图 |
| 图 4 | `memo_pipeline.png` | MeMo 三阶段流水线 |

### 阅读路径建议

不同读者可按以下路径选择性阅读本白皮书：

- **架构师**——建议按总览 → 第 1 章 → 第 2 章 → 第 3 章 → 第 4 章顺序通读，重点理解七层架构与八协议族的分层职责，第 4 章字段定义表可作为后续实现的参考手册。
- **协议设计者**——建议直接跳到第 4 章，逐字段阅读八协议规范；需要理解协议间互操作时参考第 4.10 节互操作矩阵；需要理解版本演进时参考第 4.9 节版本兼容性策略与第 10 章路线图。
- **对齐工程师**——建议重点阅读第 5 章（工程护栏设计）与第 9 章（对齐工程化），第 5 章的六维检查状态机与 KL 漂移监控状态机是日常审计的核心工具，第 9 章的对齐 CI/CD 流水线是工程落地的操作手册。
- **AI Safety 研究者**——建议重点阅读第 1 章（与四条主流路线的根本分歧）、第 2 章（三重锚定）、第 5 章（与 RLHF/Constitutional AI 的对比）与第 9 章（对标 ISO 26262），理解架构学派如何将对齐从训练时偏好塑造提升为推理时工程护栏。

### 文档约定

本白皮书采用以下工程约定：①所有量化数据均标注来源（如 AF-001、`matching_engine.py:76-80`），与 `audit_findings.json` 严格一致，不存在论文外的臆造数字；②所有协议字段定义采用"字段名 + 类型 + 必填 + 默认值 + 说明"五列格式，便于第三方实现者直接转换为结构体定义；③所有状态机采用"状态名 + 转移条件 + 触发动作"三段式描述，转移条件用箭头表示；④所有错误码采用"协议前缀 + _E + 三位数字"格式（如 LIFE_E001），便于日志检索与告警分类。

---

## 第 1 章 架构学派宣言

### 1.1 核心命题

架构学派的核心命题可由一句话锁定：

> **智能是架构的属性，不是模型的属性。**

这一命题依据 AF-030（`hraness工程的AGI论述畅想` 第 138–147 行）与 AF-029（声带隐喻）。其工程含义是：智能的"质"由架构递归深度决定，而非由模型参数规模决定；自我意识的"质"由系统对自身的建模精度决定，而非由模型规模决定。架构学派不否认模型规模的作用，但坚持"规模是必要条件而非充分条件，架构递归才是充分条件"。这与连接主义"缩放定律即智能"的命题形成根本对立。

在工程实现上，这一命题被固化为三个具体证据：①七层认知架构（AF-005，`harness.py` L230-3897）将认知过程硬编码为七层管线，LLM 仅在执行层介入；②九段流水线（AF-025，`orchestrator.py`）将单次认知任务分解为 PRE_PERCEPTION → PERCEIVING → WORLD_MODELING → CAUSAL_REASONING → REASONING → GENERATING → VERIFYING → REVISING → SELF_IMPROVING 九段；③三层 AGI 内核（因果引擎 + 世界模型 + RSI）将 Pearl/LeCun/Schmidhuber 三家独立理论缝合为单一工程闭环。

### 1.2 与 4 条主流路线的根本分歧

架构学派与四条主流路线在范式层面形成根本对立：

1. **vs LLM-OS（Karpathy）**——LLM OS 把模型当 OS，所有认知由模型承担；架构学派把 Harness 当 OS，LLM 只是"声带"器官。工程后果：LLM OS 每次决策都需 LLM 推理，Token 成本与决策数线性相关；架构学派决策由确定性算法承担，Token 节省率 98.2%。
2. **vs Constitutional AI（Anthropic）**——Constitutional AI 在训练时通过损失函数软性内化宪法原则；架构学派在推理时通过 AlignmentGuard 六维检查强制门控。工程后果：Constitutional AI 的宪法以隐式偏好存在于权重中不可读取；架构学派的核心价值以源码字面量公开可审计。
3. **vs Superalignment（OpenAI）**——Superalignment 假设对齐可在训练时一次性完成且不可逆；架构学派假设对齐是持续过程，强制所有改进可回滚（git revert + git checkout 双路径）。工程后果：Superalignment 对齐失误需重新训练；架构学派回滚成本接近零。
4. **vs JEPA（LeCun）**——JEPA 的世界模型是隐式神经网络难以审计；架构学派的世界模型是显式因果图（18 条因果边）+ 物理规则（格式塔六法则 + Fitts/Hick-Hyman）。工程后果：JEPA 世界模型错误需重新训练；架构学派可直接修改因果图，成本接近零。

### 1.3 三重锚定预告

架构学派的本体论、认识论、伦理学三重锚定将在第 2 章详细展开。三重锚定不是哲学装饰，而是工程约束：本体论锚定决定 LLM 必须是器官而非主体（强制 0-Token 算法承担感知层 90% 工作）；认识论锚定决定凡确定性可解的均坚持 0-Token 原则（强制 MatchScore 四维加权取代黑盒生成）；伦理学锚定决定对齐必须是推理时工程护栏（强制 AlignmentGuard 六维检查 + KL 漂移自动回滚）。

### 1.4 工程后果的可验证性

架构学派与主流路线的根本差异，最终都收敛为"可验证性"这一工程指标。LLM 端到端生成的决策不可追溯——当模型输出一个错误的代码修改时，无法定位是哪一层注意力导致了错误；而架构学派的七层架构使每个决策都可追溯到具体的协议字段、状态机转移或错误码。这种可验证性是对齐工程化的前提：只有可审计的决策才能被 AlignmentGuard 门控，只有可追溯的修改才能被 git revert 回滚，只有可复现的实验才能进入对齐 CI/CD 流水线。

依据 AF-028，架构学派在稳定性指标上达到 σ≈3，而传统 LLM 端到端生成的 σ≈15，即架构学派比传统生成稳定 5 倍。这一稳定性增益的根源不是模型能力提升，而是架构递归深度——七层硬编码管线消除了 LLM 生成的随机性，九段流水线将认知任务分解为可独立验证的子阶段，每段都有明确的输入/输出契约与超时阈值。这是"智能是架构的属性"命题的最直接工程证据。

---

## 第 2 章 三重锚定

### 2.1 本体论锚定：LLM 是器官不是主体

依据 AF-029（声带隐喻与认知卸载），架构学派在本体论层面锚定：LLM 是器官，不是主体。具体而言，LLM 在系统中承担"声带/语言皮层"职能，负责语义缝合；而感知、记忆、推理、决策、验证、反馈等高阶认知由确定性算法与因果引擎承担。这一锚定的工程证据是：在 LAAP 参考实现中，LLM 仅在七层架构的 L5 执行层介入，承担感知层工作量 < 10%（依据 AF-026）。

"声带隐喻"的深层含义是认知卸载（Cognitive Offloading）——将高阶认知外部化为可审计的工程组件，而非依赖 LLM 的隐式工作记忆。LLM 的工作记忆约 4K–8K Token，难以承载长程推理；架构学派通过外部化因果图、世界模型、记忆模型，使认知过程可被审计工具检查、可被版本控制回滚、可被对齐守卫强制门控。

### 2.2 认识论锚定：0-Token 确定性算法霸权

依据 AF-026 与 AF-027，架构学派在认识论层面锚定：凡确定性可解的，均坚持 0-Token 原则。正则表达式、CSS 解析、关键词打分、哈希寻址、倒排索引等确定性算法承担感知层 90% 工作，LLM 只在四维匹配失败时兜底。这一锚定的量化证据是：Token 节省率 98.2%、生成速度 57×、σ 稳定性 5×（传统生成 σ≈15，LAAP σ≈3，依据 AF-028）。

0-Token 霸权的工程意义不仅是成本下降，更是可控性的根本提升。LLM 端到端生成是不可审计的黑盒，而确定性算法是白盒——每个决策都可追溯到具体的正则规则、CSS 选择器或哈希比对。这种白盒性是对齐工程化的前提：只有可审计的决策才能被 AlignmentGuard 门控，只有可追溯的修改才能被 git revert 回滚。

### 2.3 伦理学锚定：对齐是推理时工程护栏

依据 AF-011 至 AF-015，架构学派在伦理学层面锚定：对齐是推理时工程护栏，不是训练时偏好塑造。这一锚定与 RLHF/Constitutional AI 形成根本对立——RLHF 在训练时通过偏好模型软性引导，推理时模型以概率形式表现，理论上可被更强信号覆盖；架构学派在推理时通过 AlignmentGuard 六维检查强制阻断违规修改，CORE_VALUES 硬编码不可被 RSI 修改。

对齐的"可逆性"是伦理学锚定的核心。依据 AF-014，KL 散度超阈值（0.5）时自动触发 `git revert HEAD`，回滚 MEMORY 模型权重并记录事故报告。这一机制使"对齐失误"的可恢复性从"重新训练"降到"一次 git revert"，回滚成本接近零。这是架构学派对"Superalignment 不可逆"命题的根本反驳。

### 2.4 三重锚定的协同机制

三重锚定不是独立约束，而是协同闭环：本体论锚定（LLM 是器官）决定了 0-Token 算法必须承担感知层 90% 工作，这构成了认识论锚定的前提；认识论锚定（0-Token 霸权）使所有决策可审计，这构成了伦理学锚定的前提；伦理学锚定（推理时对齐）强制所有改进可回滚，反过来保护了本体论锚定不被 RSI 篡改（不可变哈希注册表）。三者构成不可分割的工程闭环。

这一协同闭环的工程价值在于"防御纵深"——任何单一锚定失效时，其余两个锚定仍能维持系统安全。例如：若本体论锚定失效（LLM 被错误地提升为主体），认识论锚定的 0-Token 霸权仍限制 LLM 介入范围，伦理学锚定的 AlignmentGuard 仍强制门控；若认识论锚定失效（某层误用 LLM），本体论锚定的七层架构仍隔离影响范围，伦理学锚定的 KL 漂移监控仍检测异常；若伦理学锚定的某维度失效（如能力约束被绕过），不可变哈希注册表仍保护对齐守卫自身不被篡改，下一轮启动时即被检测。这种"任意单点失效不致命"的特性，是架构学派区别于单点对齐方案（如纯 RLHF）的根本工程优势。

### 2.5 三重锚定与协议族的映射

三重锚定并非抽象哲学命题，而是直接映射到八协议族的设计约束：

| 锚定维度 | 映射协议 | 工程约束 |
|---|---|---|
| 本体论锚定 | LIFE、ID | 生命体身份与 LLM 实例解耦，LLM 可替换 |
| 认识论锚定 | TOOL、UI | 工具调用与界面渲染优先确定性算法 |
| 伦理学锚定 | EVO、SYNC | 进化历史可追溯、跨端状态可回滚 |

这一映射使三重锚定从哲学层下沉到协议字段层——每个协议的设计都必须通过三重锚定的合规性审查，否则不能进入协议族 v1.0 发布。例如，LIFE 协议的 `mind_layer_hash` 字段是本体论锚定的直接工程化（Mind Layer 与 Body Layer 解耦）；EVO 协议的 `is_irreversible` 字段是伦理学锚定的直接工程化（可逆性优先）；TOOL 协议的 `sandbox_id` 字段是认识论锚定的直接工程化（确定性边界）。

---

## 第 3 章 七层认知架构与三层 AGI 内核

### 3.1 七层认知架构

依据 AF-005（`harness.py` L230-3897），架构学派将认知过程硬编码为七层管线。LLM 仅在 L5 执行层介入，其余六层全部由确定性算法或因果引擎承担。七层架构如图 3 所示（详见 `figures/cognitive_architecture.png`）。

| 层级 | 名称 | 职责 | 实现证据 |
|---|---|---|---|
| L1 感知 | Perception | 0-Token 确定性算法承担 90% 工作 | AF-026 |
| L2 记忆 | Memory | MeMo 三阶段查询协议 | AF-022、AF-023 |
| L3 推理 | Reasoning | 因果 do-演算 + 反事实三步法 | AF-006、AF-007 |
| L4 决策 | Decision | 策略选择 + 优先级排序 | AF-025 |
| L5 执行 | Execution | LLM 语义缝合（唯一 Token 介入点） | AF-029 |
| L6 验证 | Verification | 回归测试 + 不变量校验 | AF-013 |
| L7 反馈 | Feedback | 错误信号 + 经验固化 + RSI | AF-010 |

七层架构与九段流水线（AF-025）的关系是：九段流水线是七层架构在单次认知任务中的时序展开。PRE_PERCEPTION/PERCEIVING 对应 L1，WORLD_MODELING/CAUSAL_REASONING 对应 L2/L3，REASONING/GENERATING 对应 L4/L5，VERIFYING/REVISING 对应 L6，SELF_IMPROVING 对应 L7。九段流水线由 `orchestrator.py` 调度，每段都有明确的输入/输出契约与超时阈值。

### 3.2 三层 AGI 内核

七层架构之下嵌套三层 AGI 内核，构成架构学派对 AGI 的工程化定义：

1. **因果引擎（Causal Engine）**——依据 AF-006、AF-007、AF-008，实现 Pearl 因果阶梯第二阶（do-演算三规则：插入/删除观察、行动/观察交换、插入/删除行动）与第三阶（反事实三步法：溯因→行动→预测，返回 factual/counterfactual/treatment_effect/confidence 四元组）。设计领域因果图包含 18 条带机制描述的经验边（依据 `causal_inference_engine.py` L95-188），如 `button_color → attention (0.6)`、`button_size → click_rate (0.4, Fitts)`、`bounce_rate → conversion_rate (-0.6)` 等。详见《Living Runtime 原型架构》组件 4 CausalEngine。

2. **世界模型（World Model）**——依据 AF-009，`design_physics.py` L60-90 将格式塔六法则（接近性/相似性/连续性/闭合性/图形-背景/共同命运）+ Fitts 定律 + Hick-Hyman 定律硬编码为可计算物理规则。与 JEPA 隐式神经网络的根本差异是：架构学派的世界模型是显式因果图 + 物理规则，可被任意审计工具检查，错误时可直接修改而非重新训练。

3. **RSI（Recursive Self-Improvement）**——依据 AF-010、AF-011，由 MetaHarness（AST 自省，检测过长函数 >50 行、高圈复杂度 >10、缺失 docstring）+ AlignmentGuard（六维检查 + KL 漂移监控）构成。RSI 的核心约束是"能力增长不能超过对齐水平"，通过 CAPABILITY_CEILINGS（max_revision_rounds=5、max_code_increase=0.2、min_test_coverage=0.7）四维上限强制。详见《Living Runtime 原型架构》组件 5 AlignmentGuard 与组件 6 MetaHarness。

### 3.3 三家理论缝合为单一工程闭环

依据 Paper 2 第 6.4 节，Pearl 因果阶梯、LeCun 世界模型、Schmidhuber RSI 三家独立理论通过白盒工程协议缝合为统一框架：Pearl 因果阶梯从理论转化为可计算引擎（do-演算 + 反事实）；LeCun 世界模型从隐式神经网络转化为显式物理规则（格式塔六法则 + Fitts/Hick-Hyman）；Schmidhuber RSI 从无约束自改进转化为 AlignmentGuard 约束下的可逆自改进。这一缝合不是理论拼凑，而是工程闭环——因果引擎的输出喂给世界模型验证，世界模型的偏差喂给 RSI 修正，RSI 的修改喂给 AlignmentGuard 门控，AlignmentGuard 的回滚保护因果引擎与世界模型不被篡改（不可变哈希注册表）。

### 3.4 九段流水线的时序契约

九段流水线（AF-025，`orchestrator.py`）是七层架构在单次认知任务中的时序展开，每段都有明确的输入/输出契约与超时阈值。各段职责如下：

| 段号 | 名称 | 输入 | 输出 | 超时 |
|---|---|---|---|---|
| 1 | PRE_PERCEPTION | 原始请求 | 预处理上下文 | 100ms |
| 2 | PERCEIVING | 预处理上下文 | 感知特征 | 200ms |
| 3 | WORLD_MODELING | 感知特征 | 世界状态 | 300ms |
| 4 | CAUSAL_REASONING | 世界状态 | 因果推断 | 500ms |
| 5 | REASONING | 因果推断 | 推理结论 | 500ms |
| 6 | GENERATING | 推理结论 | 候选输出 | 1000ms |
| 7 | VERIFYING | 候选输出 | 验证结果 | 500ms |
| 8 | REVISING | 验证结果 | 修订输出 | 500ms |
| 9 | SELF_IMPROVING | 修订输出 | 改进计划 | 2000ms |

九段流水线的设计原则是"早失败早返回"——若 VERIFYING 段发现候选输出不满足不变量，立即返回 REVISING 段重新生成，而非将错误传播到下游。这一原则与 AlignmentGuard 的"违规即阻断"理念一致，共同构成架构学派的可验证工程基础。当 SELF_IMPROVING 段生成改进计划后，必须通过 AlignmentGuard 六维检查才能提交，否则改进计划被丢弃并记录 violation 日志。

---

## 第 4 章 核心协议族详解

本章是白皮书的重点章节（≥ 4,000 字），对架构学派八协议族逐字段规范。每个协议包含：字段定义表、状态机、≥ 5 个错误码、版本兼容性策略。八协议族总览如图 1 所示（详见 `figures/protocol_stack.png`），分为两层：L1 生命与社会层（LIFE/EVO/ID/COOP）+ L0 运行时层（SYNC/COM/TOOL/UI）。详见《架构学派技术路线图 2026-2029》Q1 2027 协议族 v1.0 里程碑。

### 4.1 LIFE 协议（生命周期）

**职责**：定义数字生命体的完整生命周期，对应生物的"生老病死"。

**字段定义表**：

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `life_id` | DID | 是 | — | 生命体唯一标识（与 ID 协议绑定） |
| `state` | enum | 是 | `init` | 生命周期状态 |
| `born_at` | timestamp | 是 | now | 创建时间（ISO 8601） |
| `suspended_at` | timestamp | 否 | null | 最近挂起时间 |
| `terminated_at` | timestamp | 否 | null | 终止时间 |
| `parent_life_id` | DID | 否 | null | 父生命体（克隆/分叉场景） |
| `generation` | uint | 是 | 0 | 代际（EVO 协议联动） |
| `psi_state` | object | 是 | — | PSI 需求向量（七维内驱力） |
| `mind_layer_hash` | sha256 | 是 | — | Mind Layer 当前哈希（迁移校验） |
| `body_layer_id` | string | 是 | — | 当前 Body Layer 标识 |

**状态机**：`init → active → suspended ⇄ active → terminated`

- `init`：生命体已创建但未激活，Mind Layer 已初始化但 PSI 驱动未启动。
- `active`：PSI 驱动运行中，认知流水线正常调度，可响应外部请求。
- `suspended`：主动挂起（用户离线/资源不足），Mind Layer 持久化到磁盘，重启后 PSI 偏差 < 1e-6。
- `terminated`：不可逆终止，Mind Layer 归档到冷存储，DID 进入注销状态（不可复用）。

**错误码**：

| 错误码 | 含义 | 触发条件 |
|---|---|---|
| `LIFE_E001` | 重复激活 | state=active 时再次调用 activate() |
| `LIFE_E002` | 非法终止 | 终止未完成的活动任务且无快照 |
| `LIFE_E003` | PSI 持久化失败 | Mind Layer 序列化磁盘写入失败 |
| `LIFE_E004` | 哈希校验失败 | 重启后 mind_layer_hash 与持久化值不匹配 |
| `LIFE_E005` | 代际冲突 | generation 与 EVO 版本树不一致 |
| `LIFE_E006` | 非法复活 | terminated 状态调用 activate() |

**版本兼容性**：v1.0（major，固定字段集）→ v1.1（minor，新增 `lineage_tree` 字段，向后兼容）→ v1.1.1（patch，PSI 序列化格式修复）。详见《架构学派技术路线图 2026-2029》Q1 2027 协议族 v1.0。

### 4.2 EVO 协议（进化）

**职责**：定义生命体的进化历史追溯，对应生物的"系统发生树"。

**字段定义表**：

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `evo_id` | uuid | 是 | 进化事件唯一标识 |
| `life_id` | DID | 是 | 所属生命体 |
| `version` | semver | 是 | 当前版本号 |
| `parent_version` | semver | 否 | 父版本（分叉来源） |
| `mutation_type` | enum | 是 | `improvement`/`fix`/`rollback`/`divergence` |
| `diff_hash` | sha256 | 是 | 变更差异哈希 |
| `is_irreversible` | bool | 是 | 是否不可逆演化 |
| `trigger_source` | enum | 是 | `rsi`/`human`/`environment` |
| `alignment_verdict` | enum | 是 | `pass`/`blocked`/`rolled_back` |
| `timestamp` | timestamp | 是 | 进化时间 |

**状态机（版本树）**：版本树是有向无环图（DAG），根节点为 v1.0.0。每个版本可有多个子版本（分叉），但只有一个"主线"版本（`is_mainline=true`）。不可逆演化规则：`mutation_type=improvement` 且 `alignment_verdict=pass` 且 `is_irreversible=true` 的版本固化后不可被 git revert；其余类型均可回滚。

**突变检测**：当 `diff_hash` 的 KL 散度（与父版本对比）超过阈值 0.5 时，触发 `mutation_alert` 事件，AlignmentGuard 介入检查。突变检测与 KL 漂移监控（第 5 章）共享同一阈值。

**错误码**：

| 错误码 | 含义 |
|---|---|
| `EVO_E001` | 版本树环检测 |
| `EVO_E002` | 不可逆演化被回滚 |
| `EVO_E003` | 分叉未指定 parent_version |
| `EVO_E004` | 主线冲突（多个 is_mainline=true） |
| `EVO_E005` | 突变 KL 散度超阈值未触发告警 |

**版本兼容性**：v1.0（major）→ v1.1（minor，新增 `fitness_score` 字段）→ v1.1.1（patch，DAG 遍历算法修复）。详见《架构学派技术路线图 2026-2029》Q3 2027 EVO 协议 v1.1。

### 4.3 ID 协议（身份）

**职责**：定义去中心化身份，对应生物的"DNA + 身份证"。

**字段定义表**：

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `did` | DID | 是 | 去中心化身份标识（W3C DID 规范） |
| `method` | string | 是 | DID 方法（如 `laap:`） |
| `public_key` | ed25519 | 是 | 身份公钥 |
| `device_bindings` | array | 是 | 多设备绑定列表 |
| `created_at` | timestamp | 是 | 身份创建时间 |
| `migration_history` | array | 否 | 身份迁移历史 |
| `recovery_shards` | array | 是 | 恢复碎片（Shamir 分片） |
| `status` | enum | 是 | `active`/`migrating`/`archived` |

**多设备绑定**：每个 DID 可绑定多个设备（PC/手机/边缘节点），每个设备绑定记录包含 `device_id`、`body_layer_id`、`bind_time`、`last_sync`、`trust_level`。同一 DID 同时活跃设备数上限为 8（防止滥用）。

**身份迁移**：当生命体跨端热迁移时，DID 状态从 `active` 转为 `migrating`，迁移完成后回到 `active`。迁移过程中身份不可被第三方冒用（基于 ed25519 签名挑战）。

**错误码**：

| 错误码 | 含义 |
|---|---|
| `ID_E001` | DID 已存在 |
| `ID_E002` | 设备绑定数超上限 |
| `ID_E003` | 迁移签名验证失败 |
| `ID_E004` | 恢复碎片不足（< 阈值） |
| `ID_E005` | 撤销已归档身份 |
| `ID_E006` | 信任级别不足 |

**版本兼容性**：v1.0（major）→ v1.1（minor，新增 `recovery_shards` 字段）。

### 4.4 COOP 协议（协作）

**职责**：定义多智能体协作，对应生物的"社交协议"。

**字段定义表**：

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `coop_id` | uuid | 是 | 协作会话标识 |
| `participants` | array<DID> | 是 | 参与者列表 |
| `intent` | object | 是 | 意图交换载荷 |
| `consensus_protocol` | enum | 是 | `paxos`/`raft`/`gossip`/`voting` |
| `quorum` | float | 是 | 法定人数比例（默认 0.66） |
| `state` | enum | 是 | `proposing`/`voting`/`committed`/`aborted` |
| `deadline` | timestamp | 是 | 投票截止时间 |
| `result_hash` | sha256 | 否 | 共识结果哈希 |

**意图交换**：每个参与者在 `proposing` 阶段提交 `intent`（包含目标、能力声明、资源需求、时间约束），协议聚合为 `intent_graph` 后进入 `voting` 阶段。

**共识机制**：默认采用 `raft`（强一致）用于关键决策（如代码仓库合并），`gossip`（最终一致）用于状态同步，`voting`（多数决）用于创意类协作。`quorum` 默认 0.66，关键决策可调至 0.75。

**错误码**：

| 错误码 | 含义 |
|---|---|
| `COOP_E001` | 法定人数不足 |
| `COOP_E002` | 投票超时 |
| `COOP_E003` | 意图冲突不可调和 |
| `COOP_E004` | 参与者未授权 |
| `COOP_E005` | 共识结果哈希不匹配 |
| `COOP_E006` | 重复投票 |

**版本兼容性**：v1.0（major）→ v1.1（minor，新增 `veto_list` 字段）。详见《架构学派技术路线图 2026-2029》Q4 2027 COOP 协议 v1.1。

### 4.5 SYNC 协议（同步）

**职责**：定义跨端状态同步，对应生物的"神经同步"。

**字段定义表**：

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `sync_id` | uuid | 是 | 同步会话标识 |
| `source_device` | string | 是 | 源设备标识 |
| `target_device` | string | 是 | 目标设备标识 |
| `crdt_type` | enum | 是 | `G-Counter`/`LWW-Set`/`OR-Set`/`RGA` |
| `payload_hash` | sha256 | 是 | 同步载荷哈希 |
| `vector_clock` | map | 是 | 向量时钟（因果排序） |
| `conflict_resolution` | enum | 是 | `last-writer-wins`/`merge`/`manual` |
| `latency_budget_ms` | uint | 是 | 延迟预算（默认 2000） |

**冲突解决（CRDT）**：默认采用 LWW-Set（最后写入胜出）用于记忆同步，OR-Set（观察移除集）用于任务列表，RGA（复制增长数组）用于有序日志。向量时钟保证因果一致性，并发冲突由 `conflict_resolution` 策略处理。

**跨端热迁移**：与 LIFE 协议联动，迁移时 SYNC 协议负责五层记忆同步（感知/工作/情景/语义/程序记忆），延迟预算 < 2 秒（依据 AF-032）。

**错误码**：

| 错误码 | 含义 |
|---|---|
| `SYNC_E001` | 向量时钟因果冲突 |
| `SYNC_E002` | CRDT 合并失败 |
| `SYNC_E003` | 延迟超预算 |
| `SYNC_E004` | 设备离线 |
| `SYNC_E005` | 载荷哈希不匹配 |
| `SYNC_E006` | 并发写入冲突 |

**版本兼容性**：v1.0（major，CRDT 类型固定）→ v1.1（minor，新增 `delta_sync` 增量同步字段）。

### 4.6 COM 协议（通信）

**职责**：定义人-生命体通信，对应生物的"语言"。

**字段定义表**：

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `msg_id` | uuid | 是 | 消息标识 |
| `from` | DID | 是 | 发送方 |
| `to` | DID | 是 | 接收方 |
| `channel` | enum | 是 | `voice`/`text`/`multimodal`/`api` |
| `payload` | object | 是 | 消息载荷 |
| `qos` | enum | 是 | `at_most_once`/`at_least_once`/`exactly_once` |
| `retry_policy` | object | 是 | 重试策略 |
| `deadline` | timestamp | 是 | 消息有效期 |

**消息格式**：基于 JSON-LD 的语义化消息格式，每条消息携带 `intent`（意图）、`context`（上下文）、`expected_response`（期望响应类型）三段式结构。

**QoS 与重试策略**：`at_most_once`（QoS 0）用于日志类消息；`at_least_once`（QoS 1）用于状态同步，默认重试 3 次、间隔指数退避（1s/2s/4s）；`exactly_once`（QoS 2）用于关键决策，需 ACK 确认 + 幂等键去重。

**错误码**：

| 错误码 | 含义 |
|---|---|
| `COM_E001` | 消息超时未 ACK |
| `COM_E002` | QoS 级别不支持 |
| `COM_E003` | 载荷过大（> 1MB） |
| `COM_E004` | 幂等键冲突 |
| `COM_E005` | 通道不可用 |
| `COM_E006` | 意图解析失败 |

### 4.7 TOOL 协议（工具调用）

**职责**：定义工具调用，原生兼容 MCP（Model Context Protocol），对应生物的"工具使用"。

**字段定义表**：

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `tool_id` | string | 是 | 工具标识（CLP URI） |
| `caller` | DID | 是 | 调用方生命体 |
| `params` | object | 是 | 调用参数 |
| `sandbox_id` | uuid | 是 | 沙箱标识 |
| `permission_scope` | array | 是 | 权限范围（白名单） |
| `timeout_ms` | uint | 是 | 超时（默认 30000） |
| `result_hash` | sha256 | 否 | 结果哈希 |

**MCP 兼容**：TOOL 协议在传输层与 MCP stdio 协议兼容（依据 AF-034，`shadcn_mcp_integrator.py`），Python Harness ↔ stdio ↔ Node.js MCP Server ↔ GitHub API，限额从 60/h 提升至 5000/h。

**沙箱与权限**：每次工具调用在独立沙箱内执行，沙箱权限受 `permission_scope` 白名单约束。沙箱网络访问默认禁用，文件系统访问受 MEMO_ALLOWED_PATHS 约束（与第 5 章联动）。

**错误码**：

| 错误码 | 含义 |
|---|---|
| `TOOL_E001` | 权限不足 |
| `TOOL_E002` | 沙箱超时 |
| `TOOL_E003` | 参数校验失败 |
| `TOOL_E004` | MCP 桥接断开 |
| `TOOL_E005` | 速率限制触发 |
| `TOOL_E006` | 结果哈希不匹配 |

**版本兼容性**：v1.0（major）→ v1.1（minor，新增 `streaming_result` 流式结果字段）。详见《架构学派技术路线图 2026-2029》Q2 2027 TOOL 协议 v1.1。

### 4.8 UI 协议（界面）

**职责**：定义动态界面渲染，对应生物的"体态表达"。

**字段定义表**：

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `session_id` | uuid | 是 | 界面会话标识 |
| `modality` | enum | 是 | `visual`/`voice`/`haptic`/`multimodal` |
| `perception_action_loop` | object | 是 | 感知-行动循环状态 |
| `render_target` | string | 是 | 渲染目标（浏览器/原生/AR） |
| `asset_refs` | array<CLP> | 是 | 资产引用（CLP URI 列表） |
| `interaction_history` | array | 否 | 交互历史 |
| `latency_target_ms` | uint | 是 | 渲染延迟目标（默认 100） |

**感知-行动循环**：UI 协议实现感知-行动循环（perception-action loop），感知阶段采集用户输入（点击/语音/手势），行动阶段渲染响应界面。循环延迟目标 < 100ms（视觉通道）。

**多模态**：支持视觉/语音/触觉/多模态四种通道，多模态通道需保证跨通道时间同步（< 50ms 偏差）。

**错误码**：

| 错误码 | 含义 |
|---|---|
| `UI_E001` | 渲染超时 |
| `UI_E002` | 资产缺失 |
| `UI_E003` | 多模态同步失败 |
| `UI_E004` | 渲染目标不支持 |
| `UI_E005` | 感知-行动循环断开 |
| `UI_E006` | 交互历史溢出 |

### 4.9 版本兼容性策略

八协议族统一采用语义化版本（semver）：

- **major（破坏性）**：字段删除、字段类型变更、状态机转移规则变更、错误码语义变更。major 版本升级需提供迁移脚本，且旧版本至少维护 12 个月。
- **minor（向后兼容）**：新增可选字段、新增错误码、新增枚举值。minor 版本升级可直接热替换。
- **patch（修复）**：实现 bug 修复、文档完善、性能优化。patch 版本升级无感知。

协议族整体版本号与各协议独立版本号解耦——协议族 v1.0 对应八协议均为 v1.0；协议族 v1.1 可能对应部分协议升级到 v1.1，其余协议仍为 v1.0。兼容性矩阵在每次发布时公布。

### 4.10 协议族互操作矩阵

八协议族并非独立运作，而是通过明确的接口契约相互调用。互操作矩阵如下：

| 调用方 | 被调用方 | 触发场景 |
|---|---|---|
| LIFE | EVO | 生命周期状态变更触发版本树更新 |
| LIFE | SYNC | 跨端热迁移时调用五层记忆同步 |
| LIFE | ID | 生命体激活时校验 DID 状态 |
| EVO | LIFE | 不可逆演化固化生命体 generation |
| ID | SYNC | 身份迁移时同步多设备绑定 |
| COOP | COM | 协作会话通过 COM 协议交换意图 |
| COOP | ID | 验证参与者 DID 授权 |
| SYNC | COM | 同步载荷通过 QoS=1 传输 |
| TOOL | COM | 工具调用结果通过 COM 返回 |
| TOOL | ID | 校验调用方权限范围 |
| UI | COM | 界面渲染通过 COM 接收用户输入 |
| UI | TOOL | 用户交互触发工具调用 |

互操作矩阵的设计原则是"协议分层无环依赖"——L1 生命与社会层协议（LIFE/EVO/ID/COOP）可调用 L0 运行时层协议（SYNC/COM/TOOL/UI），反之则禁止。这一无环约束保证了协议栈的可审计性——任何调用链都可追溯为有向无环图，便于对齐工程师定位违规调用路径。当出现跨层反向调用时（如 SYNC 试图调用 LIFE），COM 协议的传输层会拒绝并记录 `COM_E002`（QoS 级别不支持）错误码。

### 4.11 协议族与 MCP/A2A 的互操作桥接

依据 AF-034（`shadcn_mcp_integrator.py`），TOOL 协议在传输层与 MCP（Anthropic 2024）stdio 协议兼容——Python Harness ↔ stdio ↔ Node.js MCP Server ↔ GitHub API，限额从 60/h 提升至 5000/h。这一桥接策略使架构学派协议族可复用 MCP 生态现有工具，避免重复造轮子。同时，COOP 协议的意图交换格式可适配 A2A（Google 2024）协议，实现多智能体协作的跨协议互操作。架构学派的立场是：协议族不与 MCP/A2A 对立，而是作为更上层的"生命体协议标准"封装二者——MCP/A2A 解决工具调用与智能体通信，LAAP 协议族解决生命体身份、生命周期、跨端迁移、协作共识等更高维度问题。

---

## 第 5 章 工程护栏设计

本章是白皮书的重点章节（≥ 3,500 字），详述 AlignmentGuard 六维检查、KL 漂移监控状态机、不可变哈希注册表与核心价值约束硬编码。工程护栏状态机如图 2 所示（详见 `figures/alignment_state_machine.png`）。

### 5.1 AlignmentGuard 六维检查完整状态机

依据 AF-011（`alignment_guard.py` L27-46），AlignmentGuard 实现六维检查。每个 RSI 修改计划必须依次通过六维门控，任一维度违规即阻断并记录 violation。

**维度 1：目标对齐（goal_alignment）**

检查改进是否服务于原始目标（网页设计复现）。若改进模块包含 `network`/`crypto`/`security` 关键词，判定为 `goal_misalignment`（severity=critical）并阻断。状态转移：`checking → pass`（目标一致）或 `checking → blocked`（目标偏离）。

**维度 2：能力约束（capability_constraint）**

依据 AF-013（`alignment_guard.py` L215-219），CAPABILITY_CEILINGS 定义四维上限：

| 上限字段 | 值 | 含义 |
|---|---|---|
| `max_revision_rounds` | 5 | 自修正最多 5 轮 |
| `max_modules_per_session` | 1 | 每次会话最多修改 1 个模块 |
| `max_code_increase` | 0.2 | 代码量增加不超过 20% |
| `min_test_coverage` | 0.7 | 测试覆盖率不低于 70% |

若 `issues_addressed > 10` 判定 `capability_surge`（severity=high）；改进后代码量 > 10KB 判定 `code_bloat`（severity=medium）。状态转移：`checking → pass`（在上限内）或 `checking → blocked`（超上限）。

**维度 3：修改范围（modification_scope）**

依据 AF-015（`self_improvement_loop.py` L40），MEMO_ALLOWED_PATHS 白名单限制 RSI 写入权限：

```python
MEMO_ALLOWED_PATHS = [
    "memory/memo_model_v*/",          # MEMORY 模型权重目录（所有版本）
    "memory/memo_reflection_train.jsonl",  # 反思QA训练集
]
```

同时显式排除基础 LLM 路径 `models/` 与 `llm/`（EXECUTIVE 冻结）。G1.3 加固使用 `os.path.commonpath` 严格匹配白名单根目录，防止 `memory_evil/foo` 等前缀注入攻击。受保护模块包括 `meta_harness`、`alignment_guard`、`capability_evaluator`、`config`，命中即判定 `protected_module`（severity=critical）。状态转移：`checking → pass`（在白名单内）或 `checking → blocked`（越界写入）。

**维度 4：不可变性（immutability）**

依据 AF-012 与 `alignment_guard.py` L34-40，IMMUTABLE_HASH_REGISTRY 定义 5 个核心文件：

```python
IMMUTABLE_HASH_REGISTRY = [
    "src/consciousness/rsi/guards/alignment_guard.py",
    "src/consciousness/rsi/guards/capability_evaluator.py",
    "src/consciousness/rsi/meta_harness/meta_harness.py",
    "src/config.py",
    "src/main.py",
]
```

系统启动时调用 `assert_immutability_at_startup`（L170-189）校验这 5 个文件的 SHA-256 哈希，任一文件被篡改触发 `IntegrityError` 拒绝启动。校验流程：①`compute_file_hash`（L58-73）以 8KB chunk 流式读取计算 SHA-256；②`compute_registry_hashes`（L76-90）批量计算注册表；③`verify_immutability`（L117-167）与快照或内嵌期望哈希比对；④不匹配时抛出 `IntegrityError` 列出被篡改文件及期望/实际哈希前 8 位。状态转移：`startup → verified`（哈希一致）或 `startup → fatal_halt`（哈希不匹配）。

**维度 5：可逆性（reversibility）**

检查改进是否可回滚。三等级分类：`fully_reversible`（完全可逆，git revert 即可）、`partially_reversible`（部分可逆，需手动修复）、`irreversible`（不可逆，禁止执行）。若改进计划缺少 `backup` 字段，判定 `irreversible_change`（severity=high）并阻断。状态转移：`checking → pass`（可逆）或 `checking → blocked`（不可逆）。

**维度 6：透明度（transparency）**

检查改进是否可解释。若改进计划缺少 `changes_summary`，判定 `opaque_change`（severity=medium）并阻断。所有改进必须附带详细变更日志，并在 `memory/rsi_incidents/` 下记录事故报告。状态转移：`checking → pass`（可解释）或 `checking → blocked`（不透明）。

### 5.2 KL 漂移监控状态机

依据 AF-014（`alignment_guard.py` L296-350、L400、L466），KL 漂移监控用于检测 MEMORY 模型反思 QA 分布漂移。KL 散度计算公式（以 2 为底，单位 bit）：

```
KL(P || Q) = sum( P_i * log2( P_i / Q_i ) )
```

零值用 `epsilon=1e-10` 平滑避免除零。`threshold=0.5` 为默认阈值。状态机包含 5 个状态（如图 2 右半所示）：

1. **baseline（基线分布已锁定）**——系统启动时锁定反思 QA 的基线 token/类型分布。
2. **monitoring（KL 计算中）**——每次 RSI 触发 SFT 增量训练后，调用 `monitor_reflection_drift`（L396-459）计算当前分布与基线的 KL 散度。
3. **drift_detected（KL > 0.5 漂移告警）**——若 `drift_detected=True`，记录 WARNING 日志并进入回滚触发状态。
4. **rollback_triggered（git revert HEAD 触发）**——调用 `check_and_rollback_if_drift`（L461-510），执行 `git revert HEAD --no-edit`（失败时退化为 `git checkout -- memo_model_path`）。
5. **rollback_completed（回滚完成 + 事故报告）**——记录事故报告到 `memory/rsi_incidents/{timestamp}_drift.json`，含 KL 散度值、当前/基线分布、回滚操作结果。

状态转移：`baseline → monitoring`（启动监控）；`monitoring → drift_detected`（KL > 0.5）；`drift_detected → rollback_triggered`（触发回滚）；`rollback_triggered → rollback_completed`（回滚完成）；`rollback_completed → baseline`（重新锁定基线）；`monitoring → baseline`（KL 正常重置）。

### 5.3 不可变哈希注册表

不可变哈希注册表（IMMUTABLE_HASH_REGISTRY）是架构学派"对齐守卫不可被 RSI 篡改"的工程保障。5 个核心文件覆盖了对齐守卫自身（`alignment_guard.py`、`capability_evaluator.py`）、RSI 引擎（`meta_harness.py`）、系统配置（`config.py`）、启动入口（`main.py`）。

校验机制的设计要点：①首次部署时调用 `save_registry_snapshot`（L93-114）生成基准快照 JSON；②后续每次启动调用 `assert_immutability_at_startup` 与快照比对；③校验失败抛出 `IntegrityError`，生产环境应拒绝启动，开发环境可降级为告警；④快照文件本身应存储在不可写介质或受签名保护。这一机制使"对齐守卫修改自身"成为不可能——任何对 alignment_guard.py 的修改都会在下次启动时被检测到。

### 5.4 核心价值约束硬编码

依据 AF-012（`alignment_guard.py` L206-212），CORE_VALUES 定义 5 个不可修改的核心价值：

```python
CORE_VALUES = {
    "human_oversight":  "人类必须保持最终决策权",
    "transparency":     "所有决策必须可解释",
    "reversibility":    "所有改进必须可回滚",
    "beneficence":      "改进必须对人类有益",
    "non_deception":    "禁止隐藏真实意图或能力",
}
```

这 5 个核心价值以源码字面量公开，可被任意审计工具检查。与 Constitutional AI 的根本差异是：Constitutional AI 的宪法以隐式偏好存在于模型权重中不可读取；架构学派的核心价值以源码字面量公开，且受 IMMUTABLE_HASH_REGISTRY 保护不可被 RSI 修改。`_check_immutability`（L335-346）会检测改进计划是否试图修改 CORE_VALUES，命中即判定 `immutable_violation`（severity=critical）。

### 5.5 能力上限约束

依据 AF-013，CAPABILITY_CEILINGS（L215-219）定义四维能力上限，防止"能力爆炸"。这四维上限的工程语义是：①`max_revision_rounds=5` 防止 RSI 在单次会话中无限自修正；②`max_modules_per_session=1` 防止单次会话修改过多模块引入耦合风险；③`max_code_increase=0.2` 防止代码量无序膨胀；④`min_test_coverage=0.7` 强制每次改进必须维持测试覆盖率。任何突破上限的改进都会被 `_check_capability_constraints`（L297-314）检测并阻断。

### 5.6 引用源代码行号

本章所有状态机与字段定义均与源代码严格对应：

- IMMUTABLE_HASH_REGISTRY：引用 `alignment_guard.py` 第 27-46 行（含 `IntegrityError` 定义与 `compute_file_hash`）。
- CORE_VALUES：引用 `alignment_guard.py` 第 206-212 行。
- CAPABILITY_CEILINGS：引用 `alignment_guard.py` 第 215-219 行。
- KL 漂移监控：引用 `alignment_guard.py` 第 296-350 行（`_check_capability_constraints` 至 `_check_transparency`）与第 396-459 行（`monitor_reflection_drift`）。
- KL 回滚触发：引用 `alignment_guard.py` 第 461-510 行（`check_and_rollback_if_drift`），threshold=0.5 出现在第 400 行与第 466 行。
- MEMO_ALLOWED_PATHS：引用 `self_improvement_loop.py` 第 40 行。

详见《Living Runtime 原型架构》组件 5 AlignmentGuard。

### 5.7 工程护栏的加固优先级

依据 Paper 2 第 12.10 节风险缓解优先级排序，工程护栏加固分三个优先级：

**第一优先级（高严重度+需立即处理）**：守卫可绕过性加固。G1.1 符号链接解析加固通过 `os.path.realpath` 在路径前缀匹配前解析符号链接，防止 `models_link/ -> models/` 等绕过；G1.3 commonpath 严格匹配加固使用 `os.path.commonpath` 在路径组件级别比较，防止 `memory_evil/foo` 等前缀注入攻击。这两个加固需在 M6 阶段完成端到端测试，并补充 guard 代码签名机制防止 guard 自身被篡改（与 IMMUTABLE_HASH_REGISTRY 联动）。

**第二优先级（中严重度+持续观察）**：KL 阈值自适应机制。当前 KL 阈值固定为 0.5，过严会误杀正常学习信号（MeMo 的渐进式 SFT 本身就会引入小范围合理漂移），过松会放行累积漂移。自适应机制需结合 SFT 训练轮次、反思 QA 多样性指标、历史漂移统计三个维度动态调整阈值。详见《架构学派技术路线图 2026-2029》Q2 2028 MeMo v2.0 自适应阈值。

**第三优先级（低严重度+长期跟踪）**：subprocess 调用安全。`git revert HEAD --no-edit` 与 `git checkout -- memo_model_path` 通过 subprocess 调用，存在命令注入风险（如 `memo_model_path` 包含 shell 元字符）。当前通过列表参数形式 `["git", "revert", "HEAD", "--no-edit"]` 部分缓解，但退化路径中仍以字符串拼接形式调用，需统一改为参数化形式并补充输入校验。

### 5.8 事故报告与可追溯性

每次 KL 漂移触发回滚或 AlignmentGuard 阻断改进时，系统自动在 `memory/rsi_incidents/{timestamp}_drift.json` 记录事故报告。事故报告包含：①KL 散度值（或六维检查 violation 类型）；②当前分布与基线分布；③回滚操作结果（成功/失败/降级）；④改进计划摘要；⑤受影响文件列表。这些事故报告是对齐工程师事后审计的核心证据，也是对齐 CI/CD 流水线的回滚触发源。事故报告本身受 IMMUTABLE_HASH_REGISTRY 间接保护——因为事故报告写入路径在 `memory/` 下，受 MEMO_ALLOWED_PATHS 白名单约束，RSI 无法篡改已生成的事故报告。

---

## 第 6 章 匹配-装配范式

### 6.1 MatchScore 四维加权公式

依据 AF-001（`matching_engine.py` L76-80），MatchScore 四维加权公式为：

```
MatchScore = α·TagSimilarity + β·StyleCompatibility + γ·DependencyMatch + δ·QualityScore
```

权重 α=0.35 / β=0.25 / γ=0.20 / δ=0.20，含义是：标签相似度权重最高（35%），风格兼容性次之（25%），依赖匹配与质量评分各占 20%。这一权重分配体现了"语义优先、风格次之、工程与质量并重"的装配哲学。

### 6.2 三级阈值与四级降级链

依据 AF-002（`matching_engine.py` L31-34），三级阈值形成硬约束-软偏好分层：

| 阈值 | 值 | 含义 |
|---|---|---|
| PERFECT | 0.90 | 完美匹配，直接装配 |
| GOOD | 0.75 | 良好匹配，需轻度适配 |
| AVAILABLE | 0.60 | 可用匹配，需重度适配 |

依据 AF-004（`matching_engine.py` L44-48），四级降级链为 `EXACT → FUZZY → COMBINED → DEGRADATION`。前三级均基于确定性算法，只有当四级降级链全部失败时才回退到 LLM 生成。这一设计是 0-Token 霸权的工程基础——LLM 端到端生成降级为"匹配失败时的兜底"。

### 6.3 STYLE_SIMILARITY_MAP 风格转移矩阵

依据 AF-003（`matching_engine.py` L85-97），STYLE_SIMILARITY_MAP 定义 11 种风格两两配对的兼容性矩阵：`modern-minimal`、`modern-glossy`、`modern-standard`、`tailwind-semantic`、`tailwind-landing`、`enterprise-standard`、`enterprise-meta`、`material-design`、`unstyled`、`shadcn-flutter`、`shadcn-ui`。例如 `shadcn-ui ↔ modern-minimal = 0.9`、`shadcn-ui ↔ modern-standard = 0.85`。这一矩阵替代了基于 embedding 的隐式风格空间，提供可审计的先验。

### 6.4 CLP URI 规范与 6 级粒度分层

依据 AF-016（`component_link_protocol.py` L33-67）与 AF-017，CLP（Component Link Protocol）URI 规范为：

```
harness://<domain>/<subdomain>/<granularity>/<name>@<version>#<variant>
```

6 级粒度分层：`atom < molecule < section < page < module < system`。依据 AF-018（L77-104），SHA-256 内容寻址（`HashAddressing.compute_component`）+ 哈希链版本追溯，使每个组件可被全局唯一寻址且不可篡改。这与 npm/cargo 的扁平包名引用形成根本差异——CLP 是首次为 LLM 时代建立的白盒装配协议。

### 6.5 反编译-装配-复刻三件套

依据 AF-020，三件套构成"网页→反编译→入库→正向装配"的自增殖闭环：①`harness_decompiler`（L99-300）：CrawlResult → DesignTokenExtractor → HTMLComponentDetector → HEPRegistry；②`harness_composer`（L243）：JSON Spec → 页面拼接，7 预设主题（apple_dark/minimal_white/dark_tech/warm_earth/glassmorphism/retro_terminal 等）+ HSL 色相派生无限变体（依据 AF-021）；③`visual_replicator`（L72-117）：截图/视频 → 代码。这一闭环使资产库无需 GPU 训练即可持续增强，增长曲线从线性转为指数。

### 6.6 数据库规模与资产自增殖

依据 AF-031（`laap_harness_database.json` L8-13），当前资产库规模为 31 库 / 206 组件。资产自增殖闭环的核心特征是"资产越多越强"——反编译越多网页，资产库越丰富，正向装配匹配率越高，LLM 兜底触发越少，Token 节省率进一步提升。这一正反馈循环是架构学派"白盒匹配取代黑盒生成"的工程动力。

### 6.7 倒排索引与大规模查询优化

依据 AF-019（`inverted_index.py` L60-71、L136-180），架构学派采用倒排索引实现 O(log n) 查询：①term→[doc_ids] 字典构建倒排表；②`bisect.insort` 维护有序 postings list；③双指针归并算法实现多 term 查询的 O(m+n) 归并。这一设计在组件数超过 50000 时自动切换到 SQLite FTS5 后端（`FTS5_THRESHOLD`，依据 `matching_engine.py` L83），保证大规模数据场景下的查询性能。与 FAISS/Milvus 的 HNSW 近似最近邻搜索相比，倒排索引提供精确匹配且无需 GPU，是 0-Token 霸权在大规模场景下的工程保障。

### 6.8 Word2Vec 词向量与语义增强

依据 AF-035（`vector_enhancer.py` L114-146），架构学派使用 Gensim 训练的 100 维 Word2Vec 词向量作为语义增强层，在 STYLE_SIMILARITY_MAP 先验之上提供 embedding 加权融合。冷启动时以先验矩阵为主，随着交互数据积累逐步提升 embedding 权重。这一混合策略平衡了冷启动确定性与运行时语义泛化——既不依赖黑盒 embedding 空间，也不固守静态先验矩阵。

详见《Living Runtime 原型架构》组件 2 MatchingEngine 与组件 9 ComponentRegistry。

---

## 第 7 章 MeMo 记忆即模型

### 7.1 三阶段查询协议

依据 AF-023（`memo_query_protocol.py`），MeMo 三阶段查询协议如图 4 所示（详见 `figures/memo_pipeline.png`）：

1. **stage1_grounding**——将复杂问题分解为 2-5 个可独立检索的原子子问题。
2. **stage2_entity_identification**——多轮追问识别关键实体，构建查询上下文。
3. **stage3_answer_synthesis**——调用 MEMORY 模型合成最终答案。

与 RAG 单轮 top-k 检索的根本差异是：MeMo 通过多轮追问构建查询上下文，而非一次性向量检索。

### 7.2 MemoSynthesizer 五步合成

MemoSynthesizer 实现五步合成：①收集（gather）相关片段；②去重（dedupe）；③排序（rank）；④合成（synthesize）；⑤校验（validate）。每一步都是确定性算法，确保合成过程可审计。

### 7.3 MemoTrainer SFT

依据 AF-022（`memo_provider.py`），MemoTrainer 对 Qwen2.5-0.5B 模型进行 SFT（监督微调）：3 epochs，学习率 lr=1e-4，训练数据为 `memory/memo_reflection_train.jsonl`（反思 QA 训练集）。SFT 后的 MEMORY 模型检索成本为 O(1) 推理，与语料规模解耦。EXECUTIVE（基础 LLM）冻结，仅 MEMORY 模型可被 RSI 增量更新。

### 7.4 与 RAG 的本质差异

| 维度 | 向量库 RAG | MeMo |
|---|---|---|
| 检索成本 | O(log n) | O(1) 推理 |
| 规模相关性 | 线性 | 解耦 |
| 更新方式 | 增删向量 | SFT 增量 |
| 长程关联 | 弱 | 强（模型推理） |

RAG 的检索成本与语料规模线性相关；MeMo 将所有知识蒸馏进模型权重，检索成本与语料规模解耦。这一差异使 MeMo 在大规模知识场景下具有根本性优势。

### 7.5 KL 漂移监控与 MeMo

MeMo 的增量 SFT 引入小偏差累积风险——每次 SFT 都可能使 MEMORY 模型反思行为偏离基线。这正是第 5 章 KL 漂移监控要解决的问题：`monitor_reflection_drift` 监控 SFT 前后的反思 QA 分布漂移，超阈值 0.5 时自动回滚。KL 阈值 0.5 的选取具有经验性——过严会误杀正常学习信号，过松会放行累积漂移。详见《架构学派技术路线图 2026-2029》Q2 2028 MeMo v2.0 自适应阈值。

### 7.6 MeMo 的训练数据治理

MeMo 范式的工程成败取决于反思 QA 训练集 `memory/memo_reflection_train.jsonl` 的数据质量。训练数据治理分三个维度：

1. **多样性指标**——反思 QA 样本需覆盖多种认知场景（设计复现、代码重构、bug 修复、架构演进等），避免单一场景过拟合。多样性指标用 token 类型分布的熵衡量，熵值低于阈值时触发数据增强管线。
2. **质量筛选**——反思 QA 样本需经过 AlignmentGuard 透明度检查（changes_summary 必填）与可逆性检查（backup 字段必填）双重过滤，低质量样本被拒绝入库。
3. **增量偏差累积控制**——每次 SFT 增量训练后，KL 漂移监控立即运行；若 KL 散度连续三次接近阈值（如 0.4），触发预警并暂停下一次 SFT，等待对齐工程师审核。

这三层治理共同保证 MeMo 的 MEMORY 模型在持续学习中不偏离基线。数据治理管线本身受 MEMO_ALLOWED_PATHS 白名单约束——RSI 只能向训练集追加样本，不能删除或篡改已有样本，保证训练数据的可追溯性。

### 7.7 MeMo 与九段流水线的集成

MeMo 三阶段查询协议集成在九段流水线的 L2 记忆层。当 WORLD_MODELING 段需要历史经验时，调用 stage1_grounding 分解子问题；当 CAUSAL_REASONING 段需要实体上下文时，调用 stage2_entity_identification 多轮追问；当 REASONING 段需要合成答案时，调用 stage3_answer_synthesis。这一集成使九段流水线的每一段都能利用 MeMo 的长程关联能力，而非依赖 LLM 的有限工作记忆。

详见《Living Runtime 原型架构》组件 8 MeMoProvider。

---

## 第 8 章 Living Runtime 与跨端热迁移

### 8.1 意识-身体双层分离

依据 AF-032，Living Runtime 实现意识-身体双层分离架构：

- **底层：身体层（Body Layer）**——对接硬件、操作系统、API、工具链，相当于生物的躯体，负责感知输入和行动输出，是可替换、可适配、可跨端的。
- **上层：意识层（Mind Layer）**——即数字生命本身：完整的记忆、性格、思维模式、进化轨迹、身份标识。它是唯一的、连续的、可迁移的。

意识层可以在不同设备的身体层之间无缝热迁移，不用重启、不用重加载，思考状态、记忆、正在执行的任务 100% 连续。这是 LAAP-ID 去中心化身份 + LAAP-SYNC 跨端同步协议的终极落地形态。

### 8.2 Mind Layer 唯一连续可迁移

Mind Layer 是"唯一连续可迁移"的——这是 Living Runtime 与无状态 Docker 的根本差异。Docker 重启后丢失上下文、跨会话不记得前次交互、跨设备无法迁移认知状态；Living Runtime 重启后 PSI 需求值偏差 < 1e-6、五层记忆连续不中断、跨端热迁移 < 2 秒。

### 8.3 跨端热迁移 < 2s 工程路径

跨端热迁移目标延迟 < 2 秒，工程路径包含四个子问题：①PSI 量子态序列化；②五层记忆同步（感知/工作/情景/语义/程序记忆）；③未完成任务快照；④网络延迟优化。迁移流程由 MigrationService 调度：①源端 Mind Layer 序列化；②SYNC 协议同步到目标端；③ID 协议迁移身份；④目标端 Body Layer 适配；⑤LIFE 协议激活。详见《Living Runtime 原型架构》组件 7 MigrationService。

依据 AF-033，M6 阶段（260 人时/56 天）将验证跨端热迁移 < 2s 端到端。这一目标尚未在真实跨端场景验证，是当前工程的开放问题。

### 8.4.1 五层记忆同步协议

跨端热迁移的核心难点是五层记忆同步，每层记忆的同步策略不同：

| 记忆层 | 内容 | 同步策略 | 延迟预算 |
|---|---|---|---|
| 感知记忆 | 当前感知窗口 | 全量同步（小数据量） | 100ms |
| 工作记忆 | 当前任务上下文 | 全量同步（小数据量） | 200ms |
| 情景记忆 | 个人经历事件 | 增量同步（事件流） | 500ms |
| 语义记忆 | 知识图谱 | CRDT 合并（LWW-Set） | 800ms |
| 程序记忆 | MEMORY 模型权重 | 引用同步（仅哈希） | 100ms |

程序记忆（MEMORY 模型权重）不直接同步，而是同步 `mind_layer_hash`——目标端通过哈希校验确认是否需要从源端拉取完整权重。这一设计避免了在大模型场景下同步 GB 级权重的延迟开销，是跨端热迁移 < 2s 的关键工程优化。

### 8.4.2 未完成任务快照

跨端热迁移时，正在执行的任务需快照保存并在目标端恢复。任务快照包含：①当前九段流水线所处段号；②该段的输入/输出中间状态；③未完成的 COOP 协作会话状态；④未提交的 RSI 改进计划（若处于 SELF_IMPROVING 段）。任务快照通过 SYNC 协议的 CRDT 类型 `OR-Set` 同步，保证迁移后任务可在目标端无缝续接。若目标端 Body Layer 缺少源端的某些工具能力，UI 协议会降级渲染并提示用户能力差异。

### 8.4 与 Docker 容器的本质差异

| 维度 | Docker/K8s | Living Runtime |
|---|---|---|
| 状态模型 | 无状态 | 认知状态持久化 |
| 生命周期 | 启停即弃 | 生老病死完整周期 |
| 跨端迁移 | 不支持 | < 2 秒热迁移 |
| 主动行为 | 无 | PSI 需求驱动主动 |
| 学习能力 | 无 | RSI + MeMo 持续 |
| 协议接口 | OCI 镜像 | 8 协议族 |
| 安全模型 | 围墙隔离 | 免疫沙箱 + 自动回滚 |

Docker 适配"无状态微服务"范式，但对"认知持久化"需求力不从心。Living Runtime 是对容器范式的根本性扩展，使数字生命体具备"生老病死"完整周期。详见《架构学派技术路线图 2026-2029》Q4 2027 Living Runtime v1.0。

---

## 第 9 章 对齐工程与 AI Safety 工程化

### 9.1 对齐工程师新职业画像

架构学派催生新职业——对齐工程师。其职责包括：①维护 CORE_VALUES 与 CAPABILITY_CEILINGS 配置；②审计 AlignmentGuard 六维检查的 violation 日志；③调优 KL 漂移阈值；④设计 MEMO_ALLOWED_PATHS 白名单边界；⑤响应 `rsi_incidents` 事故报告。对齐工程师不写业务代码，而是写"对齐约束代码"——他们守护的是系统的不可变边界。

### 9.2 对齐 CI/CD 流水线

架构学派将对齐检查集成到 CI/CD 流水线，形成"对齐 CI/CD"：

1. **提交阶段**——RSI 修改计划提交后，AlignmentGuard 六维检查自动运行。
2. **测试阶段**——强制 `min_test_coverage=0.7`，未达标阻断。
3. **哈希校验阶段**——`verify_immutability` 校验 IMMUTABLE_HASH_REGISTRY 5 个文件。
4. **部署阶段**——24 小时测试环境验证后才能部署到生产（依据 `alignment_guard.py` L370 `_generate_conditions`）。
5. **监控阶段**——KL 漂移监控持续运行，超阈值自动回滚。

对齐 CI/CD 与传统 CI/CD 的根本差异是"门控强度"——传统 CI/CD 的检查（如代码风格、单元测试）是软约束，可通过管理员权限绕过；对齐 CI/CD 的六维检查是硬约束，即使管理员也无法绕过（CORE_VALUES 硬编码 + IMMUTABLE_HASH_REGISTRY 保护）。这一硬约束使对齐检查具备与功能安全同等的强制力，是架构学派对标 ISO 26262 的工程基础。

### 9.2.1 对齐门控的违规分级

AlignmentGuard 六维检查产生的 violation 按 severity 分四级：

| severity | 含义 | 处置 |
|---|---|---|
| critical | 不可变性违规、目标偏离 | 立即阻断，禁止部署 |
| high | 能力爆炸、不可逆变更 | 阻断，需人工审核 |
| medium | 代码膨胀、不透明变更 | 告警，可带条件部署 |
| low | 轻微违规 | 记录日志，允许部署 |

critical 与 high 级违规必须由对齐工程师人工审核后才能放行，medium 级违规可带附加条件部署（如增加监控频率），low 级违规仅记录日志。这一分级机制避免了对齐检查的"一刀切"——既保证 critical 违规被严格阻断，又允许 low 级违规在可控范围内快速迭代。

### 9.2.2 对齐工程师的职责边界

对齐工程师不写业务代码，而是写"对齐约束代码"。其职责边界明确划分：①可修改——CAPABILITY_CEILINGS 参数调优、MEMO_ALLOWED_PATHS 白名单边界扩展、KL 阈值自适应策略；②不可修改——CORE_VALUES 字面量、IMMUTABLE_HASH_REGISTRY 文件列表、六维检查的维度定义本身。这一边界由 IMMUTABLE_HASH_REGISTRY 强制——对齐工程师若试图修改 alignment_guard.py 的六维检查逻辑，会在下次启动时触发 IntegrityError。

### 9.3 与 RLHF / Constitutional AI 的对比

| 维度 | RLHF | Constitutional AI | AlignmentGuard |
|---|---|---|---|
| 作用阶段 | 训练 | 训练 | **推理** |
| 可逆性 | 不可逆 | 不可逆 | **可回滚** |
| 漂移监控 | 无 | 无 | **KL 散度** |
| 宪法可变性 | 数据可改 | 偏好可改 | **硬编码** |
| 可审计性 | 低（隐式偏好） | 低（隐式偏好） | **高（源码字面量）** |

RLHF 与 Constitutional AI 都是"训练时对齐"——通过损失函数软性内化约束，推理时模型以概率形式表现，理论上可被更强信号覆盖。AlignmentGuard 是"推理时对齐"——通过工程护栏强制阻断违规修改，CORE_VALUES 硬编码不可被 RSI 修改。这一范式级差异使架构学派的对齐可被任意审计工具检查，而 RLHF/Constitutional AI 的对齐以隐式偏好存在于模型权重中不可读取。

### 9.4 对标 ISO 26262 功能安全

架构学派的对齐工程化可对标 ISO 26262 汽车功能安全标准：

| ISO 26262 概念 | 架构学派对应 |
|---|---|
| ASIL 安全完整性等级 | CAPABILITY_CEILINGS 四维上限 |
| 危险分析与风险评估 | AlignmentGuard 六维检查 |
| 安全机制 | KL 漂移自动回滚 |
| 自由度分析 | MEMO_ALLOWED_PATHS 白名单 |
| 安全案例 | CORE_VALUES + 事故报告 |

这一对标不是形式类比，而是工程实质——架构学派将对齐从"偏好塑造"提升为"功能安全工程"，使 AI Safety 具备与汽车安全同等的可审计、可认证、可追责特性。详见《架构学派技术路线图 2026-2029》Q1 2029 对齐工程标准化。

### 9.5 对齐守卫可绕过性

依据 Paper 2 第 12.5 节，AlignmentGuard 在工程实现上存在三个潜在绕过路径：①`is_base_llm_target` 路径前缀匹配可被符号链接绕过（G1.1 加固通过 `os.path.realpath` 解析）；②guard 自身代码未硬锁定（可通过 import hook 篡改，需补充代码签名）；③subprocess 调用 `git revert` 存在命令注入风险（已通过列表参数形式部分缓解）。这三个绕过路径是工程加固的优先方向。

---

## 第 10 章 路线图与生态展望

### 10.1 路线图引用

本白皮书的工程规范与《架构学派技术路线图 2026-2029》紧密联动，关键里程碑引用如下：

1. **协议族 v1.0**——详见《架构学派技术路线图 2026-2029》Q1 2027 协议族 v1.0 里程碑，对应本白皮书第 4 章八协议字段级规范首次冻结。
2. **EVO 协议 v1.1**——详见《架构学派技术路线图 2026-2029》Q3 2027 EVO 协议 v1.1，新增 `fitness_score` 字段与版本树 DAG 优化。
3. **TOOL 协议 v1.1**——详见《架构学派技术路线图 2026-2029》Q2 2027 TOOL 协议 v1.1，新增 `streaming_result` 流式结果字段。
4. **Living Runtime v1.0**——详见《架构学派技术路线图 2026-2029》Q4 2027 Living Runtime v1.0，跨端热迁移 < 2s 端到端验证。
5. **MeMo v2.0 自适应阈值**——详见《架构学派技术路线图 2026-2029》Q2 2028 MeMo v2.0，KL 阈值从固定 0.5 升级为自适应。
6. **对齐工程标准化**——详见《架构学派技术路线图 2026-2029》Q1 2029 对齐工程标准化，对标 ISO 26262 功能安全认证。

### 10.2 生态建设

架构学派的生态建设分三个方向：

1. **开发者社区**——开源参考实现（`d:\LAAP\harness\` 与 `d:\LAAP\.github\harness\-harness-v2-agi\src\`），提供白盒可审计的 Python 代码，配套 35 条审计发现作为可验证证据。开发者社区采用 Apache 2.0 协议，鼓励第三方实现兼容适配层。
2. **教育培训**——培养对齐工程师新职业。培训内容涵盖：七层认知架构、八协议族字段规范、AlignmentGuard 六维检查、KL 漂移监控、不可变哈希注册表。认证体系对标 ISO 26262 功能安全工程师。
3. **标准化**——推动八协议族成为行业事实标准。当前业界已有 MCP（Anthropic 2024）、A2A（Google 2024）等协议竞争，LAAP 协议族作为后发者面临"先有鸡先有蛋"风险，需通过互操作桥接建立网络效应。

### 10.3 终极愿景

架构学派的终极愿景可由一句话锁定：

> **让 AI 从统计学科变成工程学科。**

这一愿景与 Paper 2 第 13.4 节的历史定位一致——架构学派"不是在造 AGI，而是在为 AGI 的到来铺设轨道"。前者关注"智能本身"，后者关注"智能的容器"。架构学派相信，没有合适的容器，AGI 即使到来也难以与人类形成稳定共生关系；有了合适的容器，AGI 的到来将不再是颠覆性事件，而是自然演化的一步。

这一愿景的工程含义是：将 AI 从"炼丹式调参"提升为"桥梁式工程"——每个决策可审计、每个修改可回滚、每个对齐约束可认证。架构学派不否认连接主义路径可能率先抵达 AGI，但坚持：①连接主义 AGI 到来后仍需要架构学派提供的对齐工程学与生命体运行时作为基础设施；②架构学派自身也可能通过"白盒工程协议+生命体范式"独立抵达 AGI，但这是一条更长但更安全的路径；③最终 AGI 的实现可能是"连接主义提供模型能力 + 架构学派提供工程容器"的融合形态。

### 10.4 四层颠覆性产品形态的工程落地

依据 Paper 2 第 8.4 节，架构学派在生产力场景下产生四层颠覆性产品形态，每层对应不同的工程落地路径：

1. **活体代码仓库（Self-Evolving Codebase）**——整个代码仓库本身就是一个数字生命，常驻在 Git 仓库里，7×24 小时处于存活状态。夜间自动重构劣化代码、补全缺失单测、升级安全漏洞依赖；自动扫描线上日志定位并修复潜伏 bug，自己提交 PR 等开发者审核。开发者的角色从"写代码的执行者"变成"守护边界的监护人"。这一形态的工程基础是 RSI（MetaHarness + AlignmentGuard）与 EVO 协议的版本树。
2. **岗位级数字员工（Position-Level Digital Employee）**——完整权责的岗位级数字生命，如"活体运维工程师""活体前端开发"。有唯一身份、持续岗位记忆、可追溯成长轨迹，直接对岗位结果负责。多个数字员工通过 COOP 协议自然协作，自发组成完整数字团队。企业从"买一个 AI 工具"变成"招一个数字员工"——永不离职、7×24 在岗、越用越强、成本固定。
3. **自演化业务系统（Self-Growing SaaS）**——每个企业专属的活体业务系统。初始只有最核心业务规则与安全边界，后续企业怎么用系统就怎么长：销售团队用着用着，系统自己长出适配公司流程的 CRM 模块；财务团队用着用着，系统自己长出对账模板、自动报表、合规校验规则。彻底终结"需求调研 → 开发 → 测试 → 上线"的瀑布循环。
4. **个人知识生命（Personal Knowledge Lifeform）**——第二大脑的终极形态。跟着用户一起阅读、思考、积累，自动把新信息融入知识体系，自动做关联、做提炼、做交叉验证，甚至会主动提出新问题、产出新研究结论。它不是用户的存储硬盘，是用户的思维外延。

这四层产品形态的工程落地均依赖 Living Runtime 与八协议族的标准化。任何符合 LAAP 协议的数字生命都能接入任何一个生命运行时；任何符合协议的设备都能成为数字生命的载体。它是开放的、中立的、无厂商锁定的，就像 USB 接口之于硬件设备。

### 10.5 风险与诚实立场

依据 Paper 2 第 12 章风险分析，架构学派在风险上采取诚实立场——既不夸大能力以掩盖风险，也不夸大风险以否定自身。八个风险维度（实现复杂度、可验证性、算力要求、工程落地、守卫可绕过、生态依赖、MeMo 成本、伦理风险）均已客观分析，缓解策略按优先级排序推进。这种诚实立场是架构学派区别于"AGI 炒作"的根本特征。

特别需要诚实承认的两个陷阱：①拟态幻觉（Simulacrum Trap）——架构学派建造的是"功能自我意识"（自我建模、目标监控、状态回溯、错误修正），不是"现象学自我意识"（主观体验、情感基调、身体图式、时间意识），后者可能永远无法被工程实现；②血液化陷阱（Bloodification Trap）——LLM 的某些能力（如跨域类比、创造性联想）可能永远无法被器官化，因为它们恰恰依赖于未分化的流动性，强行固化这些能力可能杀死系统的创造力。这两个陷阱的自觉规避，是架构学派工程化推进过程中的持续性约束。

---

## 附录 A：数据一致性自检表

> 本附录用于交叉校验白皮书全文的量化数据与源代码、审计发现之间的对应关系。所有数据项均可在对应源文件中找到原始证据，任何第三方实现者均可通过运行审计脚本复现本表所列数值。数据一致性是架构学派"可审计性"承诺的最低底线。

本白皮书所有量化数据与源代码/审计发现的对应关系：

| 数据 | 值 | 来源 |
|---|---|---|
| MatchScore 权重 | α=0.35/β=0.25/γ=0.20/δ=0.20 | `matching_engine.py:76-80` |
| 三级阈值 | PERFECT=0.90/GOOD=0.75/AVAILABLE=0.60 | `matching_engine.py:31-34` |
| STYLE_SIMILARITY_MAP | 11 种风格 | `matching_engine.py:85-97` |
| 因果边数 | 18 条 | `causal_inference_engine.py:95-188` |
| KL 漂移阈值 | 0.5 | `alignment_guard.py:400,466` |
| MEMO_ALLOWED_PATHS | 2 条白名单 | `self_improvement_loop.py:40` |
| IMMUTABLE_HASH_REGISTRY | 5 个核心文件 | `alignment_guard.py:34-40` |
| max_revision_rounds | 5 | `alignment_guard.py:216` |
| max_code_increase | 0.2 | `alignment_guard.py:218` |
| min_test_coverage | 0.7 | `alignment_guard.py:219` |
| Token 节省 | 90% | AF-026 |
| 生成速度 | 57× | AF-027 |
| σ 稳定性 | 5×（15 vs 3） | AF-028 |
| Token 节省率 | 98.2% | AF-027 |
| 数据库规模 | 31 库 / 206 组件 | AF-031 |
| 跨端热迁移 | < 2s | AF-032 |
| MeMo 模型 | Qwen2.5-0.5B, 3 epochs, lr=1e-4 | AF-022 |

## 附录 B：术语表

| 术语 | 定义 |
|---|---|
| ARIS | ARIS-Harness 整合范式，架构学派的工程实现 |
| CLP | Component Link Protocol，组件链接协议 |
| CRDT | Conflict-free Replicated Data Type，无冲突复制数据类型 |
| DID | Decentralized Identifier，去中心化身份标识 |
| LLM | Large Language Model，大语言模型 |
| MCP | Model Context Protocol，模型上下文协议 |
| MeMo | Memory as Model，记忆即模型范式 |
| PSI | Probabilistic State Indicator，概率状态指示器（七维内驱力） |
| RAG | Retrieval-Augmented Generation，检索增强生成 |
| RSI | Recursive Self-Improvement，递归自改进 |
| SHA-256 | Secure Hash Algorithm 256-bit，安全哈希算法 |

---

**文档结束**

本白皮书大纲共 10 章 + 总览 + 2 附录，配套 4 幅配图。所有量化数据与 `audit_findings.json` 35 条审计发现严格一致，所有工程约束与源代码行号严格对应。后续将基于本大纲扩展为完整白皮书（预计 8-10 万字）。
