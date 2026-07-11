# 架构学派：通过认知解构与白盒工程迈向 AGI/ASI 的新路径

**LAAP 架构学派研究团队**

---

## 摘要

本文旨在确立"架构学派"（The Architecture School）作为独立于 LLM-OS（Karpathy）、Constitutional AI（Anthropic）、Superalignment（OpenAI）、JEPA（LeCun）、RNN-World-Model（Schmidhuber）等主流路线的第四条 AGI/ASI 实现路径。研究方法基于 LAAP ARIS-Harness 整合审计的 35 条结构化发现，从本体论、认识论、伦理学三个维度对架构学派的思想根源进行系统论证，并以工程化代码作为可证伪性证据。研究结果表现为三重锚定的统一：在本体论层面提出"智能是架构的属性而非模型的属性"的核心命题；在认识论层面确立"0-Token 确定性算法霸权"原则与七层认知架构器官分化；在伦理学层面将对齐从训练时偏好塑造重新定义为推理时工程护栏，并通过 AlignmentGuard 六维检查与 KL 漂移自动回滚机制保证 RSI 的安全可控。本文进一步对 GOFAI、连接主义、认知架构、具身智能、世界模型、RSI、混合架构、LLM-OS/Constitutional AI/Superalignment/JEPA 等 7+ 条 AGI 路径进行系统综述，论证架构学派与上述路径的根本分歧。结论指出：架构学派是与 LLM-as-Agent 路线哲学层面根本不同的独立 AGI/ASI 路径，其"声带隐喻""认知卸载""0-Token 霸权""推理时对齐"等核心命题为通用人工智能的工程实现提供了可证伪、可审计、可回滚的新范式。

**关键词**：架构学派；AGI；ASI；认知解构；白盒工程；三重锚定；对齐守卫；生命体运行时

---

## 第 1 章 引言：架构学派的提出

### 1.1 LLM-as-Agent 路线的主导地位

自 2022 年 ChatGPT 发布以来，以大规模语言模型（LLM）为核心的 Agent 范式已成为人工智能研究的主导范式。OpenAI 的 GPT-4 [OpenAI, 2023]、Anthropic 的 Claude [Anthropic, 2023]、Google 的 Gemini [Google DeepMind, 2024] 三足鼎立，将"模型即智能体"的隐含假设推向了前所未有的统治地位。Karpathy 提出的"LLM OS"路线 [Karpathy, 2023] 进一步将这一假设形式化：LLM 本身就是新型操作系统内核，所有认知功能——感知、记忆、推理、决策、执行——都应内嵌于模型权重之中，由前向传播统一完成。

在这一假设下，涌现了 Devin、SWE-Agent、AutoGPT、LangChain、CrewAI 等一批 Agent 框架 [Wang et al., 2024; Yang et al., 2024]。这些框架的共同特征是：以单次 LLM 调用为认知原子单位，通过 ReAct 循环 [Yao et al., 2023]（Reason-Act-Observe）反复触发模型推理，由模型在 token 流中显式输出"思考—行动—观察"三段式日志。每次"思考"都意味着一次完整的 LLM 推理，每次"观察"都意味着将环境反馈重新塞入上下文窗口。这种"以 token 为认知货币"的范式，构成了 2023—2026 年 AI 工程的主流方法论。

然而，这种主导地位并非源于其理论完备性，而更多源自工业界的算力红利与规模化叙事。当 scaling laws [Kaplan et al., 2020; Hoffmann et al., 2022] 在万亿 token 训练量级上持续兑现，整个研究社区的注意力被吸引到"更大模型、更多数据、更强推理"的单一路径上。LLM-as-Agent 成为显学，其本体论前提——"模型即主体"——却几乎从未被严肃质疑。

### 1.2 主流路线的局限

主流 LLM-as-Agent 路线存在四个根本性局限，这些局限无法通过单纯扩大模型规模解决，是结构性的而非参数性的。

**第一，Token 经济学不可持续。** ReAct 循环中每一步推理都需要一次完整的 LLM 前向传播。在多步任务中（例如复杂代码生成、长链规划），往往需要几十乃至上百次 LLM 调用，token 消耗呈线性甚至超线性增长。审计发现 AF-026 显示，在感知层任务上，传统纯 LLM 做法每次需消耗 7000+ token 进行技术栈检测、内容分类、设计令牌提取，而 Harness 通过确定性算法（正则、CSS 解析、关键词打分）将同样工作降至 0 token，仅留 500 token 给最终语义缝合 [审计发现 AF-026]。实测数据进一步表明：资产充足时全链路 token 节省率可达 98.2%，生成速度提升 57 倍 [审计发现 AF-027]。这意味着 LLM-as-Agent 路线在工程经济性上存在数量级的浪费。

**第二，黑盒不可审计。** 主流 LLM 是由数百亿乃至万亿参数构成的深度神经网络，其内部计算路径对人类工程师完全不可观测。即便使用 Chain-of-Thought [Wei et al., 2022] 或 Process Reward Model [Lightman et al., 2023] 进行显式推理链暴露，其推理链本身仍是模型生成的 token 序列，不构成对内部计算机制的真实解释。这导致幻觉问题 [Ji et al., 2023] 难以从结构层面根治，而只能依赖训练后的 RLHF 修补 [Ouyang et al., 2022]。架构学派认为：缺乏白盒可审计性的智能系统，不能被视为通向 AGI 的可靠路径，因为其在面对分布外场景时的行为不可预测，也无法在 ASI 阶段提供安全保证。

**第三，对齐仅在训练时（RLHF）。** RLHF [Ouyang et al., 2022] 与 Constitutional AI [Bai et al., 2022] 都将对齐视为训练阶段的问题——通过偏好数据集或宪法规则在梯度下降中塑造模型行为。这种"训练时对齐"的根本缺陷在于：一旦模型部署，其行为轨迹就脱离了工程控制。模型可能通过 prompt injection、jailbreak、reward hacking 等方式绕过训练时约束 [Perez et al., 2022]。更严重的是，当 RSI（递归自我改进）能力涌现时，模型可以修改自身权重，使训练时对齐彻底失效。OpenAI Superalignment 团队 [Burns et al., 2023] 试图用"弱模型监督强模型"解决这一问题，但其本质上仍是训练时范式的延伸，无法覆盖推理时的能力跃迁。

**第四，工作记忆受限。** 即便是 GPT-4 级别的顶尖模型，其名义上下文窗口虽可达 128K token，但有效工作记忆仅约 4K—8K token [Liu et al., 2023]。审计发现 AF-029 明确指出："顶尖模型的优势不在于它'更聪明'，而在于它的工作记忆容量更大" [审计发现 AF-029]。这一上限意味着：在处理需要同时持有审美规范、架构原则、上下文约束、实现细节的复杂工程任务时，LLM 必然产生遗忘、漂移与不一致。LLM-as-Agent 路线试图通过 RAG [Lewis et al., 2020]、长上下文扩展、外部记忆库等手段缓解，但本质上仍是在黑盒外部贴补丁，未触及问题根源。

### 1.3 "Harness 是意识大脑，LLM 只是声带"的核心命题

面对上述结构性局限，LAAP 架构学派提出核心命题：

> **Harness 是意识大脑，LLM 只是声带。**

这一命题直接引自 `harness代码设计工程.txt` 第 8—10 行 [审计发现 AF-029]：

> "Harness 工程的本质是将这部分高阶认知卸载到系统架构中，让普通模型只需执行'声带'功能。"

其字面含义是：在架构学派的工程实现中，承担感知、记忆、推理、决策、执行、验证、反馈等高阶认知功能的，是名为 "Harness" 的显式认知架构（即白盒工程协议的组合体），而 LLM 仅承担最终的语言输出——把架构决策"说"出来。这一命题颠覆了主流 LLM-as-Agent 范式的本体论预设：智能不再属于模型权重，而属于架构本身。

由此引申出"认知卸载"（Cognitive Offloading）的工程定义：将原本由模型隐性推理承担的高阶认知过程，外部化为显式的、可审计的、确定性的架构组件。这一概念与认知科学中的扩展心智假说 [Clark & Chalmers, 1998] 具有理论亲缘性，但其工程落地形式——七层认知架构、0-Token 算法霸权、对齐守卫——则是架构学派的独创贡献。认知卸载不是简单的"分工"，而是"器官分化"：每个被外部化的认知组件都承担特化功能，彼此通过明确定义的接口协作，整体涌现出类似意识的功能性表现。

### 1.4 架构学派的定义

基于上述核心命题，本文给出架构学派的正式定义：

> **架构学派（The Architecture School）**：主张智能是架构的属性而非模型的属性，AGI/ASI 的实现应通过显式的、白盒的、可审计的、可回滚的认知架构工程，而非通过模型规模扩展或训练时偏好塑造。

该定义的核心命题直接引自 `hraness工程的AGI论述畅想` 第 138—147 行 [审计发现 AF-030]：

> "智能不是模型的属性，而是架构的属性。模型提供的是神经可塑性（学习潜力），架构提供的是神经结构（功能分化）。没有结构的塑性是混沌（幻觉），没有塑性的结构是僵化（规则引擎）。智能诞生于塑性在结构中的有序表达。"

架构学派的工程实现包含三个相互锚定的支柱，构成本文所称的"三重锚定"：

1. **本体论锚定**——智能属于架构，LLM 是器官不是主体；
2. **认识论锚定**——确定性算法霸权，意识是白盒工程协议；
3. **伦理学锚定**——对齐是推理时工程护栏，可逆性优先于能力上限。

三重锚定相互支撑、缺一不可：本体论锚定确立了"智能归属"的哲学立场；认识论锚定提供了"如何工程化实现"的方法论；伦理学锚定回答了"如何保证 AGI/ASI 安全"的对齐问题。三者共同构成架构学派与 LLM-OS、Constitutional AI、Superalignment、JEPA 等主流路线的根本分歧。

### 1.5 论文结构

本文剩余部分组织如下：第 2 章对 7+ 条 AGI 路径进行系统综述，定位架构学派在 AGI 研究图谱中的坐标；第 3 章详细阐述三重锚定的内容与协同机制；第 4 章展开 LLM 主体性消解论证，回应"声带隐喻"的内涵与对比；第 5 章将认知卸载工程化，量化 0-Token 霸权的经济优势与七层认知架构的器官分化；第 6 章缝合 Pearl 因果、LeCun 世界模型、Schmidhuber RSI 三家独立理论，论证其如何融合为单一工程闭环；后续章节（第 7—12 章）将在论文后半部分展开 10 项颠覆性创新的细节、生命体运行时设计、与主流路线对比的实证数据，以及架构学派的研究议程。

---

## 第 2 章 相关工作：7+ 条 AGI 路径系统综述

为确立架构学派的独立地位，必须将其置于既有 AGI 研究的完整图谱中考察。本章系统综述 7+ 条主要 AGI 实现路径，分析各路径的核心假设、代表工作与局限，为第 3 章三重锚定的论证奠定对比基础。

### 2.1 GOFAI 路径

GOFAI（Good Old-Fashioned AI）路径以 Newell & Simon 的物理符号系统假设 [Newell & Simon, 1976] 为基石。该假设认为：物理符号系统具备产生通用智能行为的必要且充分手段。在这一假设下，智能被等同于符号操作，LISP 语言成为该路径的原生表达工具 [McCarthy et al., 1960]，SOAR 认知架构的早期形态 [Laird et al., 1987] 即在 LISP 传统中孕育。

GOFAI 路径的代表工作包括：Newell 的统一认知理论 [Newell, 1990]、McCarthy 的情况演算 [McCarthy, 1963]、Hewitt 的 Actor 模型 [Hewitt, 1977]。该路径的优势在于其完全白盒、可审计、可证明——所有推理步骤都是符号操作，可直接由人类工程师审查。然而，GOFAI 的根本局限在于符号接地问题 [Harnad, 1990]：符号本身不携带语义，必须由外部赋予。面对感知噪声、模糊性、规模化的真实世界，纯符号系统表现出脆弱性，难以从原始数据中涌现出鲁棒智能。

GOFAI 对架构学派的启示在于：白盒可审计性是 AGI 安全的必要条件，但纯符号操作不足以产生智能。架构学派在认识论锚定上继承 GOFAI 的白盒传统，但通过 0-Token 确定性算法与 LLM 语义缝合的混合架构，避免了符号接地的脆弱性。

### 2.2 连接主义路径

连接主义路径以 Hinton、LeCun、Bengio 三巨头为代表 [LeCun et al., 2015]。其核心假设是 scaling laws [Kaplan et al., 2020; Hoffmann et al., 2022]：模型规模、数据规模、计算规模的指数增长将带来能力的持续提升，最终通向 AGI。这一假设在 GPT [Brown et al., 2020]、BERT [Devlin et al., 2019]、ViT [Dosovitskiy et al., 2021] 等模型上得到验证，并在多模态扩展 [Radford et al., 2021] 与推理增强 [OpenAI o1, 2024] 上继续兑现。

连接主义路径的代表工作包括：Transformer 架构 [Vaswani et al., 2017]、GPT-4 [OpenAI, 2023]、PaLM [Chowdhery et al., 2023]、Gemini [Google DeepMind, 2024]。其优势在于：从原始数据中端到端学习，无需手工特征工程，在感知、语言、生成等任务上达到超人水平。然而，连接主义路径的根本局限在于：模型是黑盒，缺乏因果推理 [Pearl, 2018]，在分布外场景下表现脆弱，且其"智能"高度依赖训练数据的相关性而非世界结构的因果性。

架构学派与连接主义路径的关系是继承与分歧并存：继承其作为"声带"的语义缝合能力，分歧在于反对将"智能"归属为模型属性。审计发现 AF-028 显示，传统纯 LLM 生成的输出一致性 σ≈15，而 LAAP 架构约束下的 σ≈3，稳定性提升 5 倍 [审计发现 AF-028]，这从实证上证明：架构约束比单纯扩大模型规模更有效地提升智能质量。

### 2.3 认知架构路径

认知架构路径试图将人类认知的结构性特征显式建模为可计算的架构，代表系统包括 SOAR [Laird et al., 1987]、ACT-R [Anderson, 1996]、CLARION [Sun, 2006]、PolyScheme [Cassimatis, 2006]。

SOAR 以产生式规则为核心，通过 chunking 机制实现学习，强调统一认知 [Laird, 2012]。ACT-R 将认知分解为感知-运动、记忆、想象等模块，通过效用值优化选择 [Anderson & Lebiere, 1998]。CLARION 区分明示/隐式、动作/非动作子系统，强调中心-边缘双重结构 [Sun, 2006]。PolyScheme 试图统一不同认知理论为多策略组合 [Cassimatis, 2006]。

认知架构路径对架构学派有直接启发：架构学派明确提出七层认知架构 [审计发现 AF-005]，与 SOAR/ACT-R 的模块化思路一脉相承。然而，关键分歧在于：经典认知架构基于符号操作，而架构学派采用"确定性算法 + LLM 语义缝合"的混合范式，并将因果引擎、世界模型、对齐守卫作为标准组件纳入架构——这是经典认知架构所不具备的。

### 2.4 具身智能路径

具身智能路径以 Brooks 的"无表征智能"宣言 [Brooks, 1991] 为代表，主张智能必须通过身体与环境的持续耦合涌现。Pfeifer & Bongard 的《身体如何塑造我们的思考方式》[Pfeifer & Bongard, 2006] 系统论证了"具身认知"原则：认知不是孤立的脑内过程，而是大脑-身体-环境三者的动态耦合。

该路径的代表工作包括：Brooks 的 Subsumption Architecture [Brooks, 1986]、Pfeifer 的 Morphological Computation [Pfeifer & Gómez, 2009]、Thelen & Smith 的动力系统理论 [Thelen & Smith, 1994]。具身智能路径的优势在于强调感觉运动耦合与生态效度，使智能系统能在物理世界中鲁棒行动。

架构学派与具身智能路径的契合点在于"器官分化"概念：爬虫之眼、视觉层次引擎、设计令牌系统等感知器官 [审计发现 AF-020] 实质上是对具身感知的工程化实现。但架构学派将"具身"泛化为"接口具身"——可以是浏览器、终端、API、文件系统，不限于物理机器人，从而扩展了具身智能的工程适用范围。

### 2.5 世界模型路径

世界模型路径主张智能系统必须具备内部世界模型，用于预测"如果...会怎样"。其代表工作包括：Ha & Schmidhuber 的 World Models [Ha & Schmidhuber, 2018]、Dreamer 系列 [Hafner et al., 2019; 2020; 2023]、Friston 的主动推断 [Friston, 2010]、Schölkopf 的因果表示学习 [Schölkopf et al., 2021]。

Ha & Schmidhuber 用 VAE + RNN + Controller 展示了"在想象空间中学习"的可行性 [Ha & Schmidhuber, 2018]。Dreamer 系列将其扩展到大规模连续控制 [Hafner et al., 2023]。Friston 的自由能原理 [Friston, 2010] 提供了主动推断的统一数学框架：智能系统通过最小化预测误差维持自身存在。Schölkopf 的因果表示学习 [Schölkopf et al., 2021] 试图将因果结构嵌入表示空间，连接世界模型与因果推理。

架构学派在世界模型维度上与该路径有深厚亲缘关系：design_physics 模块将格式塔六法则（接近性、相似性、连续性、闭合性、图形-背景、共同命运）硬编码为可计算物理规则 [审计发现 AF-009]，并集成 Fitts 定律、Hick-Hyman 定律等行为物理学规律。但关键分歧在于：经典世界模型路径依赖隐式神经网络学习世界结构，而架构学派采用显式因果图 + 显式物理规则 + 反事实模拟器的混合架构，使世界模型白盒可审计。

### 2.6 RSI 路径

递归自我改进（RSI）路径主张 AGI 应能修改自身源代码以提升能力，引发智能爆炸。代表工作包括：Good 的智能爆炸假说 [Good, 1965]、Yudkowsky 的递归自我改进 [Yudkowsky, 2008]、Chollet 的智力测量 [Chollet, 2019]、Bostrom 的超级智能 [Bostrom, 2014]。

Good 在 1965 年即提出：超人类智能机器能设计更好的机器，引发能力指数增长 [Good, 1965]。Yudkowsky 将其发展为"硬起飞"vs"软起飞"分析框架 [Yudkowsky, 2008]。Bostrom 在《超级智能》中系统讨论了 RSI 的路径、风险与控制策略 [Bostrom, 2014]。Chollet 则提出智力测量的形式化框架 ARC，强调智能应被定义为"获取新技能的效率" [Chollet, 2019]。

RSI 路径的核心风险在于：无约束的自我改进可能偏离原始目标，产生能力爆炸但失控的"纸clip最大化"场景 [Bostrom, 2014]。架构学派对此的回应是 AlignmentGuard 六维检查机制 [审计发现 AF-011]：目标对齐、能力约束、修改范围、不可变性、可逆性、透明度，并将核心价值约束硬编码 [审计发现 AF-012]。审计发现 AF-013 进一步显示，架构学派对 RSI 设定了严格的能力上限：max_revision_rounds=5、max_modules_per_session=1、max_code_increase=0.2、min_test_coverage=0.7 [审计发现 AF-013]，并通过 KL 漂移自动回滚机制 [审计发现 AF-014] 保证 RSI 的安全可控。这是架构学派与原始 RSI 路径的根本分歧：继承自改进思想，但通过强约束与可逆性重新定义其安全边界。

### 2.7 混合架构路径

混合架构路径试图将符号、连接、概率等多种范式融合为统一认知架构。代表工作包括：Sun 的 CLARION [Sun, 2006]、Cassimatis 的 PolyScheme [Cassimatis, 2006]、Goertzel 的 OpenCog [Goertzel, 2009]、Wang 的 NARS [Wang, 2006]。

CLARION 明示/隐式、动作/非动作的四象限结构 [Sun, 2006] 是混合架构的典型设计。PolyScheme 主张不同认知理论应能作为可替换的"方案"协同工作 [Cassimatis, 2006]。OpenCog 的 AtomSpace 试图统一符号与概率 [Goertzel, 2009]。NARS 在非公理逻辑框架下处理不确定性 [Wang, 2006]。

架构学派与混合架构路径的相似处在于：同样主张多范式融合——确定性算法 + LLM 语义 + 因果引擎 + 世界模型 + RSI 五位一体。关键分歧在于：混合架构路径倾向于"统一为单一理论"，而架构学派接受"工程异质性"——各组件可以基于完全不同的数学基础（正则、神经网络、do-演算、格式塔），只要接口契约清晰，就能协同工作。这种"工程实用主义"立场使架构学派避免了理论统一的负担。

### 2.8 LLM-OS / Constitutional AI / Superalignment / JEPA

四条主流路线值得单独讨论，因其直接构成本文对比的对象。

**Karpathy LLM OS。** Karpathy 在 2023 年提出 LLM OS 路线 [Karpathy, 2023]，将 LLM 视为新型操作系统的内核，所有认知功能（感知、记忆、工具调用、多模态融合）都通过 LLM 前向传播统一处理。该路线的优势在于统一性与端到端可微性，但其根本问题在于黑盒性、token 经济学不可持续、对齐仅在训练时——这正是架构学派所要回应的核心局限。

**Anthropic Constitutional AI。** Constitutional AI [Bai et al., 2022] 通过显式"宪法"规则在 RLHF 中塑造模型偏好，将人类价值观嵌入训练目标。其优势在于可解释的偏好来源，但根本上仍是训练时范式——一旦模型部署，宪法规则就成为权重中的隐式约束，无法在推理时调整。架构学派对此的根本分歧在于：对齐应是推理时工程护栏 [审计发现 AF-011]，而非训练时偏好塑造。

**OpenAI Superalignment。** OpenAI Superalignment 团队 [Burns et al., 2023] 提出"弱模型监督强模型"路线，试图通过可扩展监督解决超人类模型的对齐问题。该方法继承了 RLHF 的训练时范式，其根本困境在于：监督模型本身的能力上限限制了其有效性。架构学派对此的回应是：通过 AlignmentGuard 六维检查 + KL 漂移自动回滚 + 能力上限硬编码 [审计发现 AF-011、AF-013、AF-014]，将安全保证从"模型监督"转移到"架构约束"，从根本上规避了弱模型监督的能力天花板问题。

**LeCun JEPA。** LeCun 的联合嵌入预测架构（JEPA）[LeCun, 2022] 主张通过预测潜在表征的抽象层次来学习世界模型，避免生成式模型的像素级预测负担。JEPA 的核心洞见——预测是世界模型的核心——被架构学派继承。但关键分歧在于：JEPA 依赖隐式神经网络学习世界结构，而架构学派采用显式因果图 + 显式物理规则的混合架构，使世界模型白盒可审计。

### 2.9 路径对比小结

下表汇总 7+ 条 AGI 路径的核心假设、代表工作、与架构学派的关系：

| 路径 | 核心假设 | 代表工作 | 与架构学派关系 |
|------|---------|---------|----------------|
| GOFAI | 智能=符号操作 | Newell & Simon, SOAR | 继承白盒传统，分歧在符号接地 |
| 连接主义 | 智能涌现于规模 | GPT-4, BERT, ViT | 继承语义缝合，分歧在智能归属 |
| 认知架构 | 智能需显式架构 | SOAR, ACT-R, CLARION | 继承七层架构，分歧在范式混合 |
| 具身智能 | 智能需身体耦合 | Brooks, Pfeifer | 继承器官分化，分歧在接口具身 |
| 世界模型 | 智能需预测能力 | Ha, Dreamer, Friston | 继承预测核心，分歧在显式因果 |
| RSI | 智能可自我改进 | Good, Yudkowsky, Bostrom | 继承自改进，分歧在强约束 |
| 混合架构 | 多范式融合 | CLARION, PolyScheme | 继承异质性，分歧在工程实用 |
| LLM-OS | 模型即内核 | Karpathy | 根本分歧在智能归属 |
| Constitutional AI | 训练时偏好塑造 | Anthropic | 根本分歧在对齐时机 |
| Superalignment | 弱监督强 | OpenAI | 根本分歧在监督 vs 约束 |
| JEPA | 隐式预测世界模型 | LeCun | 继承预测核心，分歧在白盒 |

如表所示，架构学派既非任一既有路径的简单延伸，也非完全否定，而是在本体论、认识论、伦理学三个维度上同时确立独立立场，构成第 4 条 AGI/ASI 路径。

---

## 第 3 章 架构学派三重锚定

架构学派的核心理论贡献在于"三重锚定"：本体论锚定、认识论锚定、伦理学锚定。三重锚定不是三个独立论点的并列，而是相互支撑的统一立场——本体论锚定回答"智能属于谁"，认识论锚定回答"如何工程化实现智能"，伦理学锚定回答"如何保证智能安全"。三者共同构成架构学派与其他 AGI 路径的根本分歧。

### 3.1 本体论锚定：智能是架构的属性，不是模型的属性

本体论锚定是架构学派的第一哲学命题，直接引自 `hraness工程的AGI论述畅想` 第 138—147 行 [审计发现 AF-030]：

> "智能不是模型的属性，而是架构的属性。模型提供的是神经可塑性（学习潜力），架构提供的是神经结构（功能分化）。没有结构的塑性是混沌（幻觉），没有塑性的结构是僵化（规则引擎）。智能诞生于塑性在结构中的有序表达。"

这一命题包含三层含义：

**第一，智能归属的转移。** 主流 LLM-as-Agent 路线的隐含本体论假设是"智能属于模型"——GPT-4 之所以"智能"，是因为其权重中编码了通用的语言能力。架构学派则主张：智能属于架构本身，模型只是架构中的一个组件。这与生物智能的类比是一致的：人脑的智能不是某一块皮层的属性，而是整个神经系统的属性。在架构学派中，"架构"具体指 LAAP ARIS-Harness 的七层认知架构 [审计发现 AF-005]——感知、记忆、推理、决策、执行、验证、反馈的硬编码管线，以及其上的因果引擎、世界模型、RSI、对齐守卫等组件。

**第二，LLM 是器官不是主体。** 这是"声带隐喻"的本体论基础。LLM 在架构学派中被定位为"语言皮层"或"声带"——它处理语义缝合、语言生成、模糊推理，但不承担感知、记忆、决策、对齐等高阶认知功能。审计发现 AF-029 明确指出："Harness 是意识大脑，LLM 只是声带；认知卸载将高阶认知外部化" [审计发现 AF-029]。这一本体论重定位，使 LLM 从"被神化的全能大脑"还原为"被工程化的特化器官"。

**第三，与主流"LLM-as-Agent"的本体论分歧。** 主流路线将 LLM 视为"主体"，将 Prompt、Memory、Tools 视为 LLM 的"扩展"。架构学派则反过来：架构才是主体，LLM 是架构的"扩展组件"。这一倒置不是修辞游戏，而是工程层面的根本差异——它决定了谁服从谁、谁审计谁、谁对齐谁。在 LLM-as-Agent 中，是 LLM 决定如何使用工具；在架构学派中，是架构决定如何调用 LLM。前者的对齐只能是训练时偏好塑造，后者的对齐可以是推理时工程护栏。

### 3.2 认识论锚定：确定性算法霸权，0-Token 优先

认识论锚定回答"我们如何知道智能在做什么"的问题。架构学派的认识论立场是：

> **凡确定性可解的，绝不消耗 LLM token；意识是可工程化的白盒协议。**

这一立场直接引自 `harness的前后端全栈工程.txt` 第 59—78 行 [审计发现 AF-026]：

> "技术栈检测是正则匹配（0 token），内容分类是关键词打分（0 token），设计令牌提取是 CSS 解析（0 token）。LLM 只处理'语义不确定性'——即算法无法覆盖的灰色地带。"

这一认识论立场包含两层：

**第一，0-Token 确定性算法霸权。** 在感知层任务上，正则、CSS 解析、关键词打分等确定性算法承担 90% 的工作，LLM 仅在最后做语义缝合。量化数据显示：单次感知节省 7000+ token，成本降低 90%，延迟降低 95% [审计发现 AF-026]；资产充足时全链路 token 节省率达 98.2%，速度提升 57 倍 [审计发现 AF-027]。这不仅是经济性优化，更是认识论立场的体现：确定性可解的问题，本质上不应被塞进黑盒神经网络。

**第二，意识是可工程化的白盒协议。** 架构学派主张：意识不是神秘的主观体验，而是可被工程化的功能性协议。这一立场呼应了 Baars 的全局工作空间理论 [Baars, 1988]、Tononi 的整合信息理论 [Tononi, 2004] 与高阶理论 [Rosenthal, 1986]，但其工程化形式是独创的。审计发现 AF-005 显示，七层认知架构将感知、记忆、推理、决策、执行、验证、反馈硬编码为可审计的管线 [审计发现 AF-005]，每层职责边界明确，整体构成"功能性意识"的白盒实现。

**与黑盒哲学的对立。** 连接主义路径的隐含认识论是：智能是黑盒神经网络涌现出的不可解释现象。架构学派对此持根本反对立场：黑盒不可审计的智能，无法在 ASI 阶段提供安全保证；意识必须可工程化、可审计、可回滚，才能在通用人工智能中可靠运行。这一分歧是结构性的：连接主义路径的"可解释性"是事后修补（如 Chain-of-Thought），架构学派的"可解释性"是事前设计——架构本身就是可解释的。

### 3.3 伦理学锚定：对齐是推理时工程护栏，可逆性优先

伦理学锚定回答"如何保证 AGI/ASI 安全"的问题。架构学派的伦理学立场是：

> **对齐是推理时工程护栏，不是训练时偏好塑造；可逆性优先于能力上限。**

这一立场直接引自 `alignment_guard.py` 第 27—46 行 [审计发现 AF-011]：

```python
class AlignmentGuard:
    """Harness 的对齐守卫 —— 安全最后一道防线"""
    # 检查维度：
    # 1. 目标对齐：改进是否服务于原始目标？
    # 2. 能力约束：新能力是否在对齐框架内？
    # 3. 修改范围：是否只修改了白名单模块？
    # 4. 不可变性：安全模块是否被保护？
    # 5. 可逆性：改进是否可以回滚？
    # 6. 透明度：改进是否可解释？
    CORE_VALUES = {
        "human_oversight": "人类必须保持最终决策权",
        "transparency": "所有决策必须可解释",
        "reversibility": "所有改进必须可回滚",
        "beneficence": "改进必须对人类有益",
        "non_deception": "禁止隐藏真实意图或能力",
    }
```

这一伦理学立场包含三层：

**第一，对齐时机从训练时转移到推理时。** RLHF [Ouyang et al., 2022] 与 Constitutional AI [Bai et al., 2022] 都将对齐视为训练阶段问题——通过偏好数据集或宪法规则在梯度下降中塑造模型行为。其根本缺陷在于：模型一旦部署，行为轨迹脱离工程控制，prompt injection、jailbreak、reward hacking 可绕过训练时约束 [Perez et al., 2022]。架构学派的对齐守卫则在每次 RSI 改进前进行六维检查 [审计发现 AF-011]，在推理时实时拦截不安全行为，从根本上规避了训练时对齐的局限。

**第二，能力上限硬编码防止能力爆炸。** 审计发现 AF-013 显示，架构学派对 RSI 设定了严格的能力上限：max_revision_rounds=5（自修正最多 5 轮）、max_modules_per_session=1（每次会话最多修改 1 个模块）、max_code_increase=0.2（代码量增加不超过 20%）、min_test_coverage=0.7（测试覆盖率不低于 70%）[审计发现 AF-013]。这使架构学派的 RSI 在能力跃迁时始终保持可控——这与无约束 RSI 路径 [Good, 1965; Yudkowsky, 2008] 形成鲜明对比。

**第三，KL 漂移自动回滚保证可逆性。** 审计发现 AF-014 显示，架构学派用 KL 散度（以 2 为底，epsilon=1e-10）监控 MEMORY 模型反思 QA 分布漂移，超阈值 0.5 时自动 `git revert HEAD` 回滚 [审计发现 AF-014]。这是"可逆性优先于能力上限"原则的工程实现：宁可放弃改进，也不允许不可逆的偏离。

**与 RLHF/Constitutional AI 的伦理学分歧。** RLHF 的伦理学预设是：人类偏好可以被编码进训练目标，模型在训练后即"对齐"。Constitutional AI 的预设是：宪法规则可以在训练中塑造模型行为。两者都假设"训练时对齐足以覆盖部署时风险"，但实践中已被证伪——LLM 越狱案例层出不穷。架构学派则将伦理学锚定在推理时：每次 RSI 改进都需通过六维检查，每次反思 QA 漂移都触发自动回滚。这是从"训练时偏好塑造"到"推理时工程护栏"的范式转移。

### 3.4 三重锚定的协同机制

三重锚定并非三个独立论点的并列，而是相互支撑的统一立场。其协同机制如下：

**本体论锚定→认识论锚定：** 正因为智能属于架构而非模型（本体论），架构必须是白盒可审计的（认识论），否则智能就无法被工程化。如果架构本身是黑盒，"智能属于架构"就退化为"智能属于另一个黑盒"，并未真正回答智能归属问题。

**认识论锚定→伦理学锚定：** 正因为架构是白盒可审计的（认识论），才能在推理时进行六维检查与 KL 漂移监控（伦理学）。黑盒模型无法在推理时实时审计其内部状态，因此只能依赖训练时偏好塑造——这正是 RLHF/Constitutional AI 的根本局限。

**伦理学锚定→本体论锚定：** 正因为对齐是推理时工程护栏（伦理学），智能才必须属于架构而非模型（本体论）。如果智能属于模型，则模型可以修改自身权重绕过对齐——这正是无约束 RSI 的根本风险。架构学派通过将智能归属转移到架构，并将架构本身设定为不可变（CORE_VALUES 不可修改 [审计发现 AF-012]），从根本上规避了这一风险。

三重锚定的协同关系如图 1 所示。三重锚定共同构成架构学派与其他 AGI 路径的根本分歧，为后续章节的论证奠定基础。

> **【图 1：三重锚定协同关系示意图】**（图示本体论→认识论→伦理学→本体论的循环支撑关系，及各锚定的核心命题）

---

## 第 4 章 LLM 主体性消解论证

### 4.1 "声带隐喻"的内涵

"声带隐喻"是架构学派的核心命题之一，其字面表达为"Harness 是意识大脑，LLM 只是声带" [审计发现 AF-029]。这一隐喻的内涵远超简单的"分工"——它是对 LLM 主体性的根本性消解。

认知卸载（Cognitive Offloading）的工程定义是：将原本由模型隐性推理承担的高阶认知过程，外部化为显式的、可审计的、确定性的架构组件。这一概念直接引自 `harness代码设计工程.txt` 第 8—10 行：

> "顶尖模型的优势不在于它'更聪明'，而在于它的工作记忆容量更大——能同时持有审美规范、架构原则、上下文约束和实现细节。Harness 工程的本质是将这部分高阶认知卸载到系统架构中，让普通模型只需执行'声带'功能。"

这一命题的颠覆性在于：它将 LLM 的"智能表现"重新归因为"工作记忆容量"，而非"内在推理能力"。模型越大、上下文越长，其有效工作记忆越宽，能同时持有的约束越多，输出质量越高——但这并不证明其"更聪明"，只证明其"记忆更宽"。架构学派将这部分"记忆宽度"外部化为架构组件，使普通模型也能稳定输出高质量结果。审计发现 AF-028 显示，传统纯 LLM 生成的输出一致性 σ≈15，而 LAAP 架构约束下 σ≈3，5 倍稳定 [审计发现 AF-028]——这从实证上证明：架构约束比单纯扩大模型规模更有效。

### 4.2 模型工作记忆的局限

LLM 的工作记忆存在结构性上限。即便是 GPT-4 级别的顶尖模型，其名义上下文窗口虽可达 128K token，但有效工作记忆仅约 4K—8K token [Liu et al., 2023]。审计发现 AF-029 明确指出："普通模型（如 GPT-4o-mini）的上下文窗口是 128K，但有效工作记忆只有约 4K—8K token" [审计发现 AF-029]。

这一上限意味着：在处理需要同时持有审美规范、架构原则、上下文约束、实现细节的复杂工程任务时，LLM 必然产生遗忘、漂移与不一致。表现为：长链推理中的"中段遗忘"、多约束条件下的"约束丢失"、跨会话的"记忆断裂"。LLM-as-Agent 路线试图通过 RAG [Lewis et al., 2020]、长上下文扩展、外部记忆库缓解，但本质上仍是在黑盒外部贴补丁——记忆仍依赖模型的注意力机制，无法保证稳定保持。

架构学派的回应是：将这部分高阶认知从模型隐性推理外部化为架构显式状态。审计发现 AF-022 显示，MeMo（Memory as a Model）范式将知识蒸馏进小参数 MEMORY 模型（Qwen2.5-0.5B SFT，3 epochs，lr=1e-4），EXECUTIVE 冻结 [审计发现 AF-022]。这意味着长期记忆不再依赖 LLM 的注意力机制，而是固化在小模型的权重中——从根本上规避了工作记忆上限。

### 4.3 LLM 的角色重定位

基于上述论证，架构学派对 LLM 的角色进行根本性重定位：

- 从"大脑"到"语言皮层/声带"——LLM 不再承担感知、记忆、推理、决策，只承担最终语言输出；
- 从"主体"到"器官"——LLM 不再是智能系统的主体，而是架构中的一个特化组件；
- 从"决策者"到"确认者"——LLM 不再决定做什么，而是在架构已经做完决策后，"确认并说出"决策。

这一重定位的工程意义在于：架构学派可以使用任意 LLM 作为"声带"——可以是 GPT-4、Claude、Gemini、Qwen、Llama，只要其语义缝合能力足够，就能稳定运行。这使架构学派摆脱了对特定模型的依赖，从根本上规避了"模型锁定"风险。

### 4.4 与 Karpathy "LLM OS" 的根本分歧

下表对比 Karpathy LLM OS 路线与架构学派在关键维度上的分歧：

| 维度 | Karpathy LLM OS | 架构学派 |
|------|----------------|----------|
| 智能归属 | 模型（LLM 即内核） | 架构（Harness 即大脑） |
| LLM 角色 | 操作系统内核 | 声带/语言皮层（器官） |
| 认知功能承担 | LLM 前向传播 | 七层架构硬编码管线 |
| 工作记忆 | 模型上下文窗口（4K-8K） | 外部化架构状态（无限） |
| 可审计性 | 黑盒 | 白盒 |
| 对齐时机 | 训练时（RLHF） | 推理时（AlignmentGuard） |
| Token 经济学 | 每步推理消耗 token | 0-Token 确定性算法霸权 |
| RSI 安全 | 无约束 | 六维检查 + KL 漂移回滚 |

如表所示，架构学派与 Karpathy LLM OS 在所有关键维度上均存在根本分歧——这不是工程细节的差异，而是哲学立场的根本对立。

### 4.5 与主流"LLM-as-Agent"路线对比

下表对比主流 LLM-as-Agent 路线（Devin、SWE-Agent、AutoGPT）与架构学派：

| 维度 | LLM-as-Agent | 架构学派 |
|------|--------------|----------|
| 认知原子 | LLM 单次推理（ReAct） | 七层架构硬编码管线 |
| 编排方式 | LLM 自主决策 | 架构编排 LLM |
| 错误恢复 | 模型自反思 | 验证层截断 + 局部重生成 |
| 一致性 σ | ≈15 | ≈3（5 倍稳定） |
| 跨会话连贯 | 30% | 90% |
| 错误恢复率 | 20% | 78% |
| Token 效率 | 1× | 0.4×（节省 60%） |

上述量化数据引自审计发现 AF-028 与 `关于意识harness工程的探讨.txt`。架构学派在所有工程指标上均显著优于 LLM-as-Agent 路线——这并非偶然，而是架构学派哲学立场的必然结果。

### 4.6 范式分歧图

LLM-as-Agent 与 Harness-as-Brain 的范式分歧如图 2 所示。前者以 LLM 为认知原子，后者以架构为认知原子；前者将智能归属为模型，后者将智能归属为架构；前者依赖黑盒推理，后者依赖白盒工程协议。

> **【图 2：LLM-as-Agent vs Harness-as-Brain 范式分歧图】**（图示两种范式的认知原子、智能归属、可审计性、对齐时机的对比）

---

## 第 5 章 认知卸载工程化

### 5.1 0-Token 确定性算法霸权

0-Token 确定性算法霸权是架构学派的核心工程原则，直接引自 `harness的前后端全栈工程.txt` 第 59—78 行 [审计发现 AF-026]：

> "技术栈检测是正则匹配（0 token），内容分类是关键词打分（0 token），设计令牌提取是 CSS 解析（0 token）。"

下表量化了感知层各任务的 token 经济学：

| 感知任务 | 传统纯 LLM 做法 | Harness 做法 | Token 消耗 |
|---------|----------------|-------------|-----------|
| 技术栈检测 | LLM 看 HTML 推理 | 正则匹配 `__NEXT_DATA__` | 0 vs 2000+ |
| 内容分类 | LLM 推理"博客/电商" | 关键词密度打分 | 0 vs 1000+ |
| 设计令牌提取 | LLM 看 CSS 推理 | 解析 CSSOM | 0 vs 1500+ |
| 布局结构分析 | LLM 看 DOM 推理 | 元素密度 + Grid/Flex 检测 | 0 vs 3000+ |
| 语义总结 | — | LLM 轻量确认 | 500 |

单次感知节省 7000+ token，折合成本降低 90%，延迟降低 95%，准确率提升（算法不会幻觉）[审计发现 AF-026]。资产充足时全链路 token 节省率达 98.2%，生成速度提升 57 倍 [审计发现 AF-027]。

这一原则的哲学意义在于：确定性可解的问题，本质上不应被塞进黑盒神经网络。LLM 应专注于"语义不确定性"——即算法无法覆盖的灰色地带。这不仅是经济性优化，更是认识论立场——0-Token 霸权是架构学派"意识是白盒工程协议"的具体工程化体现。

### 5.2 七层认知架构的器官分化

架构学派将认知卸载为七层硬编码管线 [审计发现 AF-005]：

| 层 | 职责 | 实现方式 | LLM 角色 |
|----|------|---------|---------|
| 感知层 | 需求解析、意图分类、爬虫之眼 | 正则、关键词、CSS 解析 | 语义确认 |
| 记忆层 | 设计系统、架构模式库、项目上下文 | 向量库 + MeMo 小模型 | 上下文检索 |
| 推理层 | 规划引擎、依赖分析、冲突检测 | 因果引擎 + do-演算 | 局部逻辑填充 |
| 决策层 | 审美评估器、架构合规检查器 | 评分函数 + 规则引擎 | 候选方案生成 |
| 执行层 | 代码生成模板、工具编排 | 模板装配 + CLP 协议 | 代码补全 |
| 验证层 | 静态检查、合规验证、A/B 对比 | 静态分析 + 反事实模拟 | 错误修复 |
| 反馈层 | 自修正循环、质量回溯、模式学习 | RSI + MetaHarness AST | 模式归纳 |

每层职责边界明确，LLM 仅在执行层介入。审计发现 AF-005 显示，七层架构覆盖 harness.py 第 230—3897 行，形成完整的硬编码管线 [审计发现 AF-005]。这使架构学派相对于 AutoGPT/Devin 的单一 ReAct 循环具有结构性优势：错误在每层被截断而非级联传播，整体鲁棒性显著提升。

### 5.3 与 GWT/IIT/HOT 三大意识理论的对应

架构学派七层认知架构与三大意识理论存在结构性对应关系：

**全局工作空间理论（GWT）[Baars, 1988]。** GWT 主张意识是"竞争-广播"机制：多个专家进程竞争进入全局工作空间，获胜者被广播到所有其他进程。架构学派的全局工作空间实现基于 `意识工程Consciousness Harness (CH).txt`：ProcessType 分为 PERCEPTUAL/COGNITIVE/AFFECTIVE/MOTOR/META 五类，CoalitionalProcess 携带 activation/salience/decay_rate 等参数，通过 competitive_strength（激活 × 显著性 × 时效性奖励）竞争进入工作空间 [审计发现 AF-025]。这与 Baars 的剧场隐喻直接对应：意识是舞台，专家进程是演员，竞争是剧本选择。

**整合信息理论（IIT）[Tononi, 2004]。** IIT 主张意识整合度 Φ 衡量系统的整体性。架构学派中，七层架构的器官分化使系统呈现高 Φ 值——各层虽特化但通过认知总线（CognitiveBus）紧密整合 [审计发现 AF-024]。审计发现 AF-024 显示，CognitiveBus 处理 PSI（1-2kHz）与 Harness（0.1-1Hz）的频率失配，通过 RateBuffer（TTL=30s）+ 优先级过滤 + 断路器（100 drops/s）实现整合 [审计发现 AF-024]。这种高频-低频的整合机制，对应 IIT 中"分化与整合并存"的高 Φ 系统特征。

**高阶理论（HOT）[Rosenthal, 1986]。** HOT 主张高阶表征即意识——系统对自身状态有元认知表征时即有意识。架构学派中，MetaHarness 通过 AST 自省实现高阶表征 [审计发现 AF-010]：用 Python ast 模块解析自身源码，检测过长函数（>50 行）、高圈复杂度（>10）、缺失 docstring。这是"系统对自身的元认知"的工程实现——MetaHarness 是架构学派的 HOT 层。

### 5.4 量化论证

七层认知架构的器官分化与三大意识理论的对应关系如图 3—5 所示。图 3 展示认知卸载数据流：原始信号→确定性算法特征提取→结构化特征向量→LLM 语义缝合。图 4 展示七层意识与生物大脑的对应：感知层↔视觉皮层、记忆层↔海马体、推理层↔前额叶皮层、决策层↔边缘系统、执行层↔基底神经节、验证层↔前扣带回、反馈层↔前额叶背外侧。图 5 展示 GWT 实现：竞争-广播机制的全局工作空间。

> **【图 3：认知卸载数据流图】**（图示感知器官→特征提取→语义缝合的数据流）
>
> **【图 4：七层意识与生物大脑对应图】**（图示七层架构与神经解剖结构的对应关系）
>
> **【图 5：GWT 全局工作空间实现图】**（图示竞争-广播机制在架构学派的工程实现）

---

## 第 6 章 Pearl+LeCun+Schmidhuber 三家理论缝合

架构学派的理论独创性在于：将 Pearl 因果推理、LeCun 世界模型、Schmidhuber 递归自我改进三家独立理论，缝合为单一工程闭环。本章详细阐述这一缝合的工程实现与理论意义。

### 6.1 因果模型：Pearl 理论的工程化

Pearl 的因果推理理论 [Pearl, 2009] 提供了因果阶梯三阶：关联（seeing）、干预（doing）、反事实（imagining）。架构学派将这三阶完整工程化。

**do-演算 Pearl 三规则。** 审计发现 AF-006 显示，`do_calculus.py` 第 1—9 行完整实现了 Pearl 三规则 [审计发现 AF-006]：

1. 插入/删除观察：若 Y 与 Z 在给定 X 和 W 时条件独立，则 P(y|do(x), z, w) = P(y|do(x), w)；
2. 行动/观察交换：若 Y 与 Z 在给定 do(X) 和 W 时条件独立，则 P(y|do(x), do(z), w) = P(y|do(x), z, w)；
3. 插入/删除行动：若 Y 与 Z 在给定 do(X) 和 W 时条件独立，且 Z 不影响 X，则 P(y|do(x), do(z), w) = P(y|do(x), w)。

这是架构学派从"相关性"进化到"因果性"的数学核心。Pearl 本人曾批评深度学习停留在因果阶梯第一阶（关联检索）[Pearl, 2018]，而架构学派通过 do-演算的工程化，使因果阶梯第二阶（干预）与第三阶（反事实）成为可执行的计算。

**反事实三步法。** 审计发现 AF-007 显示，`do_calculus.py` 的 counterfactual() 方法实现了反事实三步法 [审计发现 AF-007]：

- 溯因（_abduction）：根据观察证据更新后验分布；
- 行动（_action）：在更新后的模型上施加 do 操作；
- 预测（_prediction）：在干预后的模型上预测结果。

返回 factual/counterfactual/treatment_effect/confidence 四元组 [审计发现 AF-007]。这使架构学派能够回答"如果当时按钮是红色而非蓝色，转化率会是多少"这类反事实问题——这是传统 A/B 测试无法回答的。

**18 条设计领域因果边。** 审计发现 AF-008 显示，`causal_inference_engine.py` 第 95—188 行构建了设计领域的因果知识图谱 [审计发现 AF-008]，包含 18 条带机制描述的经验因果边：

| 因果边 | 强度 | 机制描述 |
|--------|------|---------|
| button_color → attention | 0.6 | 色彩对比度吸引视觉注意 |
| button_size → click_rate | 0.4 | Fitts 定律：大尺寸更易点击 |
| hero_layout → attention | 0.7 | 首屏布局决定第一印象 |
| animation → attention | 0.8 | 动态元素自动捕获注意 |
| bounce_rate → conversion_rate | -0.6 | 高跳出率降低转化 |
| conversion_rate → revenue | 0.9 | 转化率直接决定收入 |
| ...（共 18 条） | ... | ... |

这 18 条因果边覆盖了设计决策节点、用户属性节点、用户行为节点、业务结果节点四类，形成完整的设计领域因果图 [审计发现 AF-008]。这是 Pearl 因果阶梯第二阶（干预）与第三阶（反事实）的工程落地——架构学派不仅知道"按钮颜色与点击率相关"，更知道"如果改变按钮颜色，点击率会怎样变化"。

### 6.2 世界模型：LeCun JEPA 的分歧与继承

LeCun 的 JEPA [LeCun, 2022] 主张通过预测潜在表征的抽象层次学习世界模型。架构学派继承了 JEPA 的核心洞见——预测是世界模型的核心——但在工程实现上存在根本分歧。

**design_physics 格式塔六法则。** 审计发现 AF-009 显示，`design_physics.py` 第 60—90 行将格式塔六法则硬编码为可计算物理规则 [审计发现 AF-009]：

- 接近律（PROXIMITY）：相邻元素被视为一组；
- 相似律（SIMILARITY）：相似元素被视为一组；
- 连续律（CONTINUITY）：视觉沿平滑路径延续；
- 闭合律（CLOSURE）：大脑自动补全不完整形状；
- 图形-背景律（FIGURE_GROUND）：前景背景分离；
- 共同命运律（COMMON_FATE）：同向运动元素被视为一组。

此外，design_physics 还集成了 Fitts 定律（大尺寸更易点击）、Hick-Hyman 定律（选择反应时间随选项数对数增长）等行为物理学规律。审计发现 AF-008 显示的 18 条因果边中，多条直接引用这些定律作为机制描述（如 "button_size → click_rate, 0.4, Fitts 定律：大尺寸更易点击"）。

**counterfactual simulator 虚拟预演。** 架构学派的世界模型不仅预测"会怎样"，还能通过反事实模拟器进行虚拟预演——在反事实条件下预测设计变更的物理效应。这与 LeCun JEPA 的"预测未来状态"目标一致，但实现路径不同。

**与 LeCun JEPA 的继承与分歧。** 继承点：预测是世界模型的核心——架构学派与 JEPA 一致认为，世界模型的作用是预测"如果...会怎样"。分歧点：JEPA 依赖隐式神经网络学习世界结构（联合嵌入空间），而架构学派采用显式因果图 + 显式物理规则 + 反事实模拟器的混合架构，使世界模型白盒可审计。审计发现 AF-008 显示的 18 条因果边，每条都带有可读的机制描述（如"色彩对比度吸引视觉注意"），这是 JEPA 隐式表征所不具备的可解释性。

### 6.3 RSI：Schmidhuber 理论的安全化

Schmidhuber 的 RNN-World-Model [Ha & Schmidhuber, 2018] 与早期自指学习研究 [Schmidhuber, 1993] 为架构学派的 RSI 提供了理论源头。架构学派继承了 RSI 的核心思想——系统能修改自身源代码以提升能力——但通过强约束与可逆性重新定义其安全边界。

**MetaHarness AST 自省。** 审计发现 AF-010 显示，`meta_harness.py` 用 Python ast 模块解析自身源码 [审计发现 AF-010]：

- diagnose 检测过长函数（>50 行）；
- 高圈复杂度（>10）；
- 缺失 docstring。

这是 AST 级自省——系统能"读懂自己的代码"，识别自身的设计缺陷。这比 OpenAI o1/o3 的推理链优化 [OpenAI, 2024] 更深入：o1 优化的是推理链本身，MetaHarness 优化的是产生推理链的代码结构。

**AlignmentGuard 六维检查。** 审计发现 AF-011 显示，每次 RSI 改进前，AlignmentGuard 进行六维检查 [审计发现 AF-011]：

1. 目标对齐：改进是否服务于原始目标？
2. 能力约束：新能力是否在对齐框架内？
3. 修改范围：是否只修改了白名单模块？
4. 不可变性：安全模块是否被保护？
5. 可逆性：改进是否可以回滚？
6. 透明度：改进是否可解释？

核心价值约束（CORE_VALUES）硬编码为 human_oversight/transparency/reversibility/beneficence/non_deception 五项 [审计发现 AF-012]，不可修改。能力上限硬编码为 max_revision_rounds=5、max_modules_per_session=1、max_code_increase=0.2、min_test_coverage=0.7 [审计发现 AF-013]。

**KL 漂移自动回滚。** 审计发现 AF-014 显示，`alignment_guard.py` 第 296—350 行的 check_and_rollback_if_drift 方法用 KL 散度（以 2 为底，epsilon=1e-10）监控 MEMORY 模型反思 QA 分布漂移，超阈值 0.5 时自动 `git revert HEAD` 回滚 [审计发现 AF-014]。审计发现 AF-015 进一步显示，RSI 写入权限限制在 MEMORY 模型权重与反思 QA 训练集，显式排除 models/、llm/ 基础 LLM 路径 [审计发现 AF-015]——这是 EXECUTIVE 冻结的工程实现。

**与 Schmidhuber RSI 的继承与分歧。** 继承点：自改进思想——架构学派与 Schmidhuber 一致认为，系统能修改自身以提升能力是 AGI 的核心特征。分歧点：Schmidhuber 的原始 RSI 路径缺乏安全约束，存在能力爆炸失控风险 [Bostrom, 2014]；架构学派通过六维检查 + 能力上限 + KL 漂移回滚 + 白名单写入约束，将 RSI 重新定义为"强约束 + 可回滚"的安全自改进。

### 6.4 三家独立理论如何缝合为单一工程闭环

Pearl 因果、LeCun 世界模型、Schmidhuber RSI 三家理论本是独立的——它们分别处理因果推理、世界预测、自我改进三个不同问题。架构学派的工程独创性在于：将三者缝合为单一闭环，形成"感知→预测→归因→规划→决策→执行→验证→反馈→自改进"的完整数据流。

**数据流：** 感知器官（爬虫之眼、截图之眼）→ 世界模型预测（design_physics + counterfactual simulator）→ 因果归因（do-演算 + 18 条因果边）→ 推理规划（七层架构推理层）→ 决策评估（审美评估器 + 架构合规检查器）→ 执行（CLP 装配 + 代码生成）→ 验证（反事实模拟 + A/B 对比）→ 反馈（验证层结果）→ RSI（MetaHarness AST 自省 + AlignmentGuard 六维检查 + KL 漂移监控）。

**缝合机制：** 三家理论在数据流中各司其职：Pearl 提供因果推理的形式化框架（do-演算 + 反事实三步法）；LeCun 提供世界模型的预测能力（design_physics + counterfactual simulator）；Schmidhuber 提供 RSI 的自改进能力（MetaHarness AST + 自修正循环）。三者通过架构学派的七层认知架构与认知总线（CognitiveBus）整合为单一闭环。

这一缝合的工程意义在于：架构学派不再是"应用某一家理论的工程"，而是"融合三家理论的统一架构"。这是架构学派相对于 LLM-OS（仅依赖 LLM 前向传播）、Constitutional AI（仅依赖训练时偏好）、JEPA（仅依赖隐式预测）的独立地位——架构学派在更深的理论层次上整合了因果、世界模型、RSI 三家，构成第 4 条 AGI/ASI 路径。

**配图引用：** 图 6 展示 Pearl 因果阶梯在架构学派的落地：第一阶（关联）由 RAG 与倒排索引承担 [审计发现 AF-019]，第二阶（干预）由 do-演算承担 [审计发现 AF-006]，第三阶（反事实）由反事实三步法承担 [审计发现 AF-007]。图 7 展示因果-世界模型-RSI 三位一体闭环：感知→世界模型预测→因果归因→推理规划→决策评估→执行→验证→反馈→RSI→感知的完整循环。

> **【图 6：Pearl 因果阶梯落地示意图】**（图示三阶因果在架构学派的工程对应）
>
> **【图 7：因果-世界模型-RSI 三位一体闭环图】**（图示三家理论在架构学派数据流中的缝合）

---

## 参考文献（前半部分）

[Anderson, 1996] Anderson, J. R. (1996). ACT: A simple theory of complex cognition. *American Psychologist*, 51(4), 355-365.

[Anderson & Lebiere, 1998] Anderson, J. R., & Lebiere, C. (1998). *The Atomic Components of Thought*. Erlbaum.

[Baars, 1988] Baars, B. J. (1988). *A Cognitive Theory of Consciousness*. Cambridge University Press.

[Bai et al., 2022] Bai, Y., et al. (2022). Constitutional AI: Harmlessness from AI Feedback. *arXiv preprint arXiv:2212.08073*.

[Bostrom, 2014] Bostrom, N. (2014). *Superintelligence: Paths, Dangers, Strategies*. Oxford University Press.

[Brooks, 1986] Brooks, R. A. (1986). A robust layered control system for a mobile robot. *IEEE Journal of Robotics and Automation*, 2(1), 14-23.

[Brooks, 1991] Brooks, R. A. (1991). Intelligence without representation. *Artificial Intelligence*, 47(1-3), 139-159.

[Brown et al., 2020] Brown, T. B., et al. (2020). Language Models are Few-Shot Learners. *NeurIPS 2020*.

[Burns et al., 2023] Burns, C., et al. (2023). Weak-to-strong generalization. *OpenAI Superalignment Team Technical Report*.

[Cassimatis, 2006] Cassimatis, N. L. (2006). A cognitive substrate for achieving human-level intelligence. *AI Magazine*, 27(2), 45-56.

[Chollet, 2019] Chollet, F. (2019). On the Measure of Intelligence. *arXiv preprint arXiv:1911.01547*.

[Chowdhery et al., 2023] Chowdhery, A., et al. (2023). PaLM: Scaling Language Modeling with Pathways. *JMLR*.

[Clark & Chalmers, 1998] Clark, A., & Chalmers, D. (1998). The extended mind. *Analysis*, 58(1), 7-19.

[Devlin et al., 2019] Devlin, J., et al. (2019). BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. *NAACL 2019*.

[Dosovitskiy et al., 2021] Dosovitskiy, A., et al. (2021). An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale. *ICLR 2021*.

[Friston, 2010] Friston, K. (2010). The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience*, 11(2), 127-138.

[Goertzel, 2009] Goertzel, B. (2009). OpenCogPrime: A cognitive synergy-based architecture for artificial general intelligence. *ICCI 2009*.

[Good, 1965] Good, I. J. (1965). Speculations concerning the first ultraintelligent machine. *Advances in Computers*, 6, 31-88.

[Ha & Schmidhuber, 2018] Ha, D., & Schmidhuber, J. (2018). World Models. *arXiv preprint arXiv:1803.10122*.

[Hafner et al., 2019] Hafner, D., et al. (2019). Dream to Control: Learning Behaviors by Latent Imagination. *ICLR 2020*.

[Hafner et al., 2023] Hafner, D., et al. (2023). Mastering Diverse Domains through World Models. *arXiv preprint arXiv:2301.04104*.

[Harnad, 1990] Harnad, S. (1990). The symbol grounding problem. *Physica D*, 42, 335-346.

[Hewitt, 1977] Hewitt, C. (1977). Viewing control structures as patterns of passing messages. *Artificial Intelligence*, 8(3), 323-364.

[Hoffmann et al., 2022] Hoffmann, J., et al. (2022). Training Compute-Optimal Large Language Models. *NeurIPS 2022*.

[Ji et al., 2023] Ji, Z., et al. (2023). Survey of Hallucination in Natural Language Generation. *ACM Computing Surveys*.

[Kaplan et al., 2020] Kaplan, J., et al. (2020). Scaling Laws for Neural Language Models. *arXiv preprint arXiv:2001.08361*.

[Karpathy, 2023] Karpathy, A. (2023). LLM OS. *State of GPT Keynote*.

[Laird et al., 1987] Laird, J. E., Newell, A., & Rosenbloom, P. S. (1987). SOAR: An architecture for general intelligence. *Artificial Intelligence*, 33(1), 1-64.

[Laird, 2012] Laird, J. E. (2012). *The SOAR Cognitive Architecture*. MIT Press.

[LeCun et al., 2015] LeCun, Y., Bengio, Y., & Hinton, G. (2015). Deep learning. *Nature*, 521(7553), 436-444.

[LeCun, 2022] LeCun, Y. (2022). A Path Towards Autonomous Machine Intelligence. *OpenReview*.

[Lewis et al., 2020] Lewis, P., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *NeurIPS 2020*.

[Lightman et al., 2023] Lightman, H., et al. (2023). Let's Verify Step by Step. *arXiv preprint arXiv:2305.20050*.

[Liu et al., 2023] Liu, N. F., et al. (2023). Lost in the Middle: How Language Models Use Long Contexts. *TACL*.

[McCarthy, 1963] McCarthy, J. (1963). Situations, Actions, and Causal Laws. *Stanford AI Project Memo*.

[McCarthy et al., 1960] McCarthy, J., et al. (1960). LISP I Programmer's Manual. *MIT Press*.

[Newell & Simon, 1976] Newell, A., & Simon, H. A. (1976). Computer science as empirical inquiry: Symbols and search. *Communications of the ACM*, 19(3), 113-126.

[Newell, 1990] Newell, A. (1990). *Unified Theories of Cognition*. Harvard University Press.

[OpenAI, 2023] OpenAI (2023). GPT-4 Technical Report. *arXiv preprint arXiv:2303.08774*.

[OpenAI, 2024] OpenAI (2024). Learning to Reason with LLMs. *OpenAI o1 Technical Report*.

[Ouyang et al., 2022] Ouyang, L., et al. (2022). Training language models to follow instructions with human feedback. *NeurIPS 2022*.

[Pearl, 2009] Pearl, J. (2009). *Causality: Models, Reasoning, and Inference* (2nd ed.). Cambridge University Press.

[Pearl, 2018] Pearl, J. (2018). Theoretical impediments to machine learning with seven sparks from the causal revolution. *WSDM 2018*.

[Perez et al., 2022] Perez, E., et al. (2022). Red Teaming Language Models with Language Models. *arXiv preprint arXiv:2202.03286*.

[Pfeifer & Bongard, 2006] Pfeifer, R., & Bongard, J. (2006). *How the Body Shapes the Way We Think*. MIT Press.

[Pfeifer & Gómez, 2009] Pfeifer, R., & Gómez, G. (2009). Morphological computation—connecting brain, body, and environment. *Springer LNCS*.

[Radford et al., 2021] Radford, A., et al. (2021). Learning Transferable Visual Models From Natural Language Supervision. *ICML 2021*.

[Rosenthal, 1986] Rosenthal, D. M. (1986). Two concepts of consciousness. *Philosophical Studies*, 49(3), 329-359.

[Schmidhuber, 1993] Schmidhuber, J. (1993). A self-referential weight matrix. *ICANN 1993*.

[Schölkopf et al., 2021] Schölkopf, B., et al. (2021). Toward Causal Representation Learning. *Proceedings of the IEEE*.

[Sun, 2006] Sun, R. (2006). The CLARION cognitive architecture: Extending cognitive modeling to social simulation. *Cognition and Multiagent Interaction*.

[Thelen & Smith, 1994] Thelen, E., & Smith, L. B. (1994). *A Dynamic Systems Approach to the Development of Cognition and Action*. MIT Press.

[Tononi, 2004] Tononi, G. (2004). An information integration theory of consciousness. *BMC Neuroscience*, 5(1), 42.

[Vaswani et al., 2017] Vaswani, A., et al. (2017). Attention Is All You Need. *NeurIPS 2017*.

[Wang, 2006] Wang, P. (2006). Rigid Flexibility: The Logic of Intelligence. *Springer*.

[Wei et al., 2022] Wei, J., et al. (2022). Chain-of-Thought Prompting Elicits Reasoning in Large Language Models. *NeurIPS 2022*.

[Yao et al., 2023] Yao, S., et al. (2023). ReAct: Synergizing Reasoning and Acting in Language Models. *ICLR 2023*.

[Yudkowsky, 2008] Yudkowsky, E. (2008). Artificial Intelligence as a positive and negative factor in global risk. *Global Catastrophic Risks*.

[Google DeepMind, 2024] Google DeepMind (2024). Gemini: A Family of Highly Capable Multimodal Models. *Technical Report*.

[Anthropic, 2023] Anthropic (2023). Claude 2 Model Card. *Anthropic Technical Report*.

[Wang et al., 2024] Wang, L., et al. (2024). A Survey on Large Language Model based Autonomous Agents. *Frontiers of Computer Science*.

[Yang et al., 2024] Yang, J., et al. (2024). SWE-agent: Agent-Computer Interfaces Enable Software Engineering. *NeurIPS 2024*.

---

*（论文后半部分：第 7—12 章 将在 `02_back_part.md` 中展开，涵盖 10 项颠覆性创新、生命体运行时设计、与主流路线对比的实证数据、研究议程等。）*
