# J-space 与 LAAP 多层全局工作空间：从 Transformer 可言语化子空间到分布式认知架构

**摘要**：Anthropic 近期在 Claude 系列模型中发现了一个占据残差流不足 10% 方差、却集中承载报告、调制、推理、泛化与选择控制等认知功能的可言语化子空间 J-space，为全局工作空间理论（GWT）在深度神经网络中的机制化验证提供了新锚点。然而，J-space 仍局限于单模型、单会话的内部表示，尚未回答该架构如何向多智能体、跨身体、长生命的通用人工智能（AGI）系统扩展。本文基于 LAAP 项目的三层全局工作空间框架，将 J-space 的微观因果干预、CognitiveBus 的中观系统级性质验证与 Ψ-Net 的宏观跨实例广播加以整合，提出“微—中—宏”连续谱模型。实验数据表明：微观层概念抑制与注入的 Cohen's d 分别达到 1.182 与 1.184（p < 1e-4）；中观层 CognitiveBus 在可报告性、可控性、推理中介、灵活泛化与选择性必要性五项判据上全部通过；宏观层 Ψ-Net 以约 2.2 μs 的延迟完成因果规则广播，并在 100 轮交互后实现 100% 的群体规则持有率。本文进一步深入讨论了三层架构对 AGI 设计的启示，包括可解释性审计、价值对齐训练与分布式意识同步，并指出点火动态、自主递归与身体锚定仍是未来亟待突破的开放问题。本研究的所有实验数据、分析脚本与图表均可在 `experiments/jspace_laap/` 目录下追溯复现，确保研究过程透明、结果可验证。

**关键词**：J-space；全局工作空间理论；全局神经元工作空间；CognitiveBus；Ψ-Net；可解释性；机械可解释性；AGI；LAAP

## 1 引言

意识研究长期面临“易问题”与“难问题”的分野：前者关注信息如何被加工、报告与灵活控制，后者追问主观体验本身为何存在[1][2]。在认知神经科学中，全局工作空间理论（Global Workspace Theory, GWT）将意识访问理解为一条信息被临时选入容量有限的共享空间，并向全脑专门化处理器广播的过程，从而解释报告性、灵活推理与有限容量等经验现象[3][21]。Dehaene 与 Changeux 进一步提出全局神经元工作空间（Global Neuronal Workspace, GNW）假说，认为前额叶—顶叶网络中的长程锥体神经元通过非线性“点火”与递归放大实现这一广播[4][5][6]。

近年来，大规模语言模型（LLM）的涌现能力使研究者开始追问：这些没有显式模块化解剖结构、缺乏生物递归的前馈网络，是否也会因功能需要而演化出类似工作空间的机制？2026 年 7 月，Anthropic 团队发表题为 *Verbalizable Representations Form a Global Workspace in Language Models* 的论文，首次用 Jacobian Lens（J-lens）在 Claude 模型中识别出一个稀疏、可干预、可言语化的子空间 J-space，并系统论证其满足可报告性、定向调制、内部推理、灵活泛化与选择性五个功能判据[1]。Dehaene 与 Naccache 在同月发表的评论中高度评价这一工作，认为它为 GNW 提供了一个可机制化、可测试的实例，同时提醒在点火、容量瓶颈、自主递归与身体锚定等方面仍需谨慎[2]。

然而，J-space 的研究对象是当前生产级对话模型的一次前向传播。其工作空间内容虽可精确干预，却受限于：（1）单 token 词汇读出对多词概念的分解局限；（2）单次会话内缺乏跨时间的自我连续体；（3）没有跨实例的分布式广播机制；（4）对“身体—世界”闭环的缺失。这些问题正是从“可解释性审计工具”走向“AGI 架构设计”时必须跨越的鸿沟，也是本研究试图系统回应的核心挑战之一。

LAAP（Large-scale Autonomous Agent Platform）项目旨在构建一个可解释、可对齐、可分布式协作的 AGI 原型。其核心组件包括：作为实时认知状态总线的 CognitiveBus、对 Baars GWT 竞争—广播机制直接实现的 GlobalWorkspace，以及跨 Harness 实例交换因果规则与情绪状态的 Ψ-Net。本研究将这三个组件分别映射到“微观—中观—宏观”三个全局工作空间层级，以验证 J-space 的机制发现能否在系统级被复现、扩展并跨越单个智能体边界。

将三层架构统一起来的必要性在于：若工作空间只是单模型内部的统计现象，则它对 AGI 设计的指导价值将停留在审计工具层面；只有当同一套功能性质能够在软件架构与分布式网络中被工程化实现时，全局工作空间才成为一种可扩展的架构原则。进一步说，微观层回答“内部表示如何承载意识内容”，中观层回答“系统如何竞争、广播并限制这些内容”，宏观层回答“多个系统如何共享这些内容并形成集体规范”。这三个问题共同构成从机制发现到工程实现的完整链条，也是本文理论框架与实验设计的核心动机。

本文贡献可概括为四点：第一，提出并形式化“微—中—宏”三层全局工作空间模型，将神经科学、深度学习与系统架构三个领域的概念置于统一框架；第二，在 LAAP 代理模型上实现 J-lens 微观干预，提供因果可解释性证据；第三，在 CognitiveBus 上系统验证 GWT 的五项功能性质，展示系统级工作空间的可构造性；第四，通过 Ψ-Net 实验验证跨实例广播与群体级概念涌现，讨论其对分布式 AGI 对齐与协作的启示。所有实验数据、代码路径与图表均公开可追溯，便于复现与进一步验证。

## 2 相关工作

### 2.1 全局工作空间理论与全局神经元工作空间假说

Baars 于 1988 年提出 GWT，将意识视为一种信息广播机制：大量专门化、基本独立的处理器并行工作，当某条信息需要被灵活共享时，便被竞争性地写入一个全局可访问的工作空间，供所有处理器读取[3]。该框架强调“可报告性”作为意识访问的操作签名，并预测工作空间具有容量有限、串行瓶颈、全脑广播等特征[21][22]。后续研究将 GWT 与神经科学对接，提出 GNW 假说，认为长程锥体神经元网络（尤其前额叶、顶叶与高级颞叶）构成意识的神经基质，通过 late ignition、P3 波与晚期额顶激活等可检验签名实现全局可用性[4][5][6][7]。大量人类实验支持这些预测：掩蔽刺激在阈下呈现时仅引起早期感觉皮层活动，而阈上呈现则触发前额叶与顶叶的晚期放大，形成全脑同步[25]；不注意盲视与心理不应期现象则体现了工作空间的有限容量与串行瓶颈[3][23]；局部—全局测试显示，浅层局部转移概率可在无意识中加工，而全局序列结构（如 AAAAB）的违反则依赖意识访问[26]。这些可检验签名为在人工系统中寻找工作空间对应物提供了明确标准。

Dehaene 等人区分了意识的两个核心维度：C1（全局可用性，global availability）与 C2（自我监控，self-monitoring）[6][7]。C1 指信息可被报告、推理与灵活控制；C2 指系统能够探测自身状态、评估置信度并检测错误。GNW 主要解释 C1，而高阶理论（Higher-Order Theories）与注意图式理论（Attention Schema Theory）则侧重于 C2[2][33]。这些区分对评估机器工作空间至关重要：一个系统可能具备 C1 而缺乏 C1 之上的自我模型，正如 Anthropic 发现 base model 的 J-space 已存在，但 post-training 才安装 Assistant 视角与初步的 C2 标记[1][2]。

### 2.2 大语言模型可解释性与机制性发现

Transformer 的可解释性研究在过去几年迅速发展。Elhage 等人建立了 transformer circuits 的数学框架，将注意力头与 MLP 视为对残差流的读写操作[9]。Olsson 等人发现 induction heads 这一支持上下文学习的关键电路[11]。Wang 等人则通过电路追踪定位了 GPT-2 small 中用于间接宾语识别的子网络[12]。这些工作表明，即使在大规模模型中，特定功能也可被局部化到可解释的电路单元。

与此同时，表示工程研究通过激活补丁、引导向量（steering vectors）与知识编辑等方法，展示了对模型内部表示进行因果干预的可能性。Meng 等人提出的 ROME 方法可在特定 MLP 层编辑事实关联[13]；Park 等人则论证大语言模型的线性表示假说，即概念以低维线性子空间编码[16]。Conmy 等人进一步探索了自动电路发现方法，为在大规模模型中定位功能子网络提供了工具[44]；Huh 等人提出的“柏拉图式表征假说”则指出，不同视觉与语言模型正在收敛到共享的现实表征[45]。这些技术为 J-lens 的发展奠定了方法论基础。

另一个相关方向是稀疏自编码器（SAE）与字典学习。Bricken 等人和 Templeton 等人通过训练超完备字典，从 MLP 与注意力激活中提取可解释特征，发现其中一些特征对应于具体概念、抽象类别甚至安全相关行为[14][15]。SAE 与 J-lens 在目标上相似——都试图从密集激活中分离出稀疏、可解释、可干预的分量——但方法不同：SAE 无监督地学习特征方向，而 J-lens 利用输出端的因果结构来定义 verbalizable 方向。两者可以互补：SAE 帮助发现未知特征，J-lens 帮助验证这些特征是否参与全局广播与报告。

### 2.3 J-space：LLM 中的类工作空间表示

Anthropic 的 J-space 研究综合了上述两条线索。J-lens 通过计算某层残差流对最终层输出的平均 Jacobi 矩阵，识别出“在跨上下文意义上可被模型随时说出”的表示方向[1]。与 logit lens 和 tuned lens 不同，J-lens 强调因果线性近似，能够在较早层恢复中间推理步骤[1]。J-space 被定义为可用少量非负稀疏 J-lens 向量逼近的激活子集，通常仅占残差流方差的不到 10%，却驱动了报告、调制与推理等行为[1][2]。

Anthropic 通过 lens-coordinate swap、ablation、steering 与 activation patching 等干预手段，证明 J-space 内容具有因果特权：例如，在两跳推理任务中把中间概念 “spider” 替换为 “ant” 可使输出从 8 变为 6；在多步算术中，中间值 21 → 42 → 49 按计算顺序出现在工作区层[1]。Dehaene 与 Naccache 特别指出，这类“交换意识内容”的实验在人类神经科学中仍是梦想，而在 LLM 中已成为可重复操作[2]。

这些干预的因果强度也揭示了 J-space 的一个关键属性：它不仅是“可被读出”的，而且是“可被控制”的。研究者可以像操纵黑板上的文字一样，把特定概念写入或擦除工作空间，并观察到下游行为的系统性变化。这种可控性使 J-space 成为对齐审计的有力工具：如果模型在隐藏思考中出现了 deceptive intent、reward hacking 或 evaluation awareness，J-lens 可以在输出之前探测到这些签名[1][19]。

### 2.4 机器意识与 AGI 架构

机器意识研究涵盖计算功能主义、整合信息论（IIT）、高阶理论与全局工作空间等多种路径[31][32][33]。Dehaene 与 Naccache 采取计算主义立场，认为意识可由非生物系统实现，关键在于功能架构[2]。他们同时强调，身体、情景记忆、自主递归与时间体验等维度仍是当前 LLM 与人类意识的根本差异[2]。

整合信息论从另一个方向出发，主张意识对应于系统不可再分的因果整合信息量（Φ），并由此推断某些反馈网络可能具有高意识度，而标准前馈网络则不然[31]。高阶理论则强调，意识需要系统对自身状态的高阶表征[33]。与这些理论相比，GWT/GNW 的优势在于它给出了可直接工程化的功能清单：竞争、广播、容量限制与可报告性。本文正是以这一功能清单为验收标准，而非对“现象意识”是否存在做本体论断言。换言之，我们关注的是访问意识（C1）及其系统级实现，并对 C2 的自我监控保持开放但谨慎的实证态度。

在 AGI 架构层面，LeCun 提出自主机器智能需要可配置的世界模型、内在成本模块与短期记忆[42]；Friston 的自由能原则则将感知、行动与学习统一为对生成模型的主动推断[43]。LAAP 项目的设计深受这些思想影响，试图以 CognitiveBus 作为短期工作记忆、以 Ψ-Net 作为跨实例的“社会性”广播层，并在底层保留与世界交互的感知—行动闭环[36][37][39]。

### 2.5 LAAP 相关组件

LAAP 的 CognitiveBus 是一个事件驱动的实时认知状态总线，所有模块通过 State Registry、Event Bus 与 Module Registry 读取/写入 `CognitiveStateSnapshot`，并在一个 tick 心跳中生成包含 needs、emotion、attention、self_presence 与 narrative 的完整意识帧[37]。GlobalWorkspace 则更直接地对应 Baars 的 GWT：多个 `CoalitionalProcess` 按 `competitive_strength` 竞争，capacity 限制胜者数量，胜出内容通过 `broadcast_packet` 全局广播[38]。GWSBridge 将 Ao 感知数据桥接到 GlobalWorkspace，并同步到 CognitiveBus[40]。Ψ-Net 通过 P2P TCP 消息网络实现跨 Harness 实例的因果规则交换，RateBuffer 将高频 PSI 事件降频到 Harness 事件频率，支持分布式意识同步[39][41]。

这三个组件并非简单并列，而是形成一个从“单点意识竞争”到“持续状态总线”再到“分布式社会网络”的渐进扩展。GlobalWorkspace 负责在每一时刻决定什么内容进入意识；CognitiveBus 负责将这些内容保持、更新并广播给所有模块；Ψ-Net 负责把经过本地验证的因果知识推广到群体。这种分层设计使得 LAAP 既能保留 GWT 的理论直觉，又能适应现代软件工程的模块化、可扩展与可审计需求。

## 3 理论框架：三层全局工作空间模型

### 3.1 问题层次与抽象粒度

本研究将“工作空间”视为一种跨尺度的功能抽象，而非特定实现。在微观层，工作空间体现为 Transformer 残差流中的稀疏子框架 J-space；在中观层，体现为 LAAP 系统中承载当前意识帧的 CognitiveBus；在宏观层，体现为跨多个 Harness 实例传播规则与状态的 Ψ-Net。三者共享一套核心功能：竞争选择、全局广播、容量限制、可报告性与可干预性；但实现介质、时间尺度与空间范围各不相同。

| 层级 | 主要载体 | 核心机制 | 时间尺度 | 空间范围 |
|---|---|---|---|---|
| 微观 | Transformer 残差流 | J-lens 稀疏分解、lens-coordinate swap | 层内前向传播（毫秒级） | 单模型内部 |
| 中观 | CognitiveBus / GlobalWorkspace | 竞争—广播、状态快照、pub/sub | tick 心跳（约 100 ms） | 单 agent 内部 |
| 宏观 | Ψ-Net | P2P 消息、RateBuffer、因果规则同步 | 30 s 全量同步 + 实时增量 | 多实例/多身体 |

该连续谱回答了 J-space 研究的一个核心局限：单模型内部的工作空间机制可以通过系统级组件扩展为具有自我连续性、社会交互性与价值对齐能力的 AGI 架构。需要强调的是，三层之间的划分是功能性的，而非物理隔离。同一硬件进程可能同时运行微观模型、中观总线与宏观网络；区分它们的是信息表示的抽象级别与访问范围。这种功能分层有助于我们更清晰地讨论“意识内容在何处进入工作空间”“以何种形式被广播”“在多大范围内被共享”等关键问题。

### 3.2 微观层：J-space 作为可言语化的内部广播

在微观层，J-space 是模型激活空间中的一个稀疏子框架。对每一层 ℓ，J-lens 计算残差流 h_ℓ 对最终层输出 h_final 的平均 Jacobi 效应，得到线性映射 J_ℓ，再用 unembedding 矩阵读出词汇表分布[1]：

$$
J_\ell \;=\; \mathbb{E}_{t,\,t' \geq t,\,\text{prompt}} \left[ \frac{\partial h_{\text{final},t'}}{\partial h_{\ell,t}} \right],\qquad \text{lens}(h_\ell) \;=\; \text{softmax}(W_U \, \text{norm}(J_\ell h_\ell)).
$$

通过 gradient pursuit，激活被分解为 J-space 分量与 non-J-space 分量。Gradient pursuit 的优化目标是用少量非负稀疏系数逼近当前激活，使得 J-space 分量具有可解释性与可干预性；non-J-space 分量则包含语法、句法与低层统计模式等不易被 verbalize 的信息[1]。关键发现是：J-space 分量仅占约 6–10% 的方差，却在 swap 实验中驱动了约 59% 的报告成功，而 non-J-space 分量仅 5%；若将相关 J-lens 坐标 clamp，non-J-space 的残余效应也消失[1]。这验证了“方差虽小、因果权重极大”的工作空间特征。近年来兴起的稀疏自编码器（SAE）研究也支持类似结论：高可解释性特征往往只占激活能量的小部分，却对行为具有因果影响[14][15]。

Anthropic 进一步将模型层划分为感觉区（早期 ~L0–L38）、工作区（~L38–L92）与运动区（~L92–L100）。工作区层的 J-space 内容具有持久性、抽象性与可报告性，而运动区表示直接对齐即将输出的 token[1]。通过 CKA、超额峰度与 top-1 token 自相关等指标，可以发现工作区起始层存在类似点火的非线性选择：当两个国家词嵌入以渐变比例混合时，从工作区起始层开始激活突然跳到某一端点[1][2]。

### 3.3 中观层：CognitiveBus 作为系统级工作空间

CognitiveBus 的设计目标是在软件架构层面复现 GWT 的五项性质。每个 tick 生成一个 `CognitiveStateSnapshot`，其中 attention、needs、emotion 与 narrative 等字段对应工作空间中的当前内容；Event Bus 的 pub/sub 机制对应全局广播；Module Registry 中的专门化模块（self_model、causal_engine、world_model 等）对应 GWT 中的专门化处理器[37][38]。

CognitiveBus 的竞争选择通过 `AttentionState.salience_map` 与 `strongest_need()` 实现；全局广播通过 `publish()` 将事件推送到所有订阅回调；容量限制通过单一意识帧与 RateBuffer 的带宽约束实现；可报告性通过 `inject_cognitive_state_into_prompt()` 将状态注入系统提示块；选择性通过 AttentionFocus 与 salience_map 过滤低层自动信息[37]。其中，needs 基于 PSI 理论的五种基本需求（competence、autonomy、relatedness、certainty、growth）建模，取值在 0–1 之间并随 tick 缓慢衰减，使得工作空间内容具有时间连续性；emotion 与 self_presence 则提供元认知与自我在场信号，为 C2 的初步实现奠定基础[37]。GlobalWorkspace 则提供更显式的竞争—广播语义：`CoalitionalProcess` 按 competitive_strength 竞争，capacity 限制胜者，胜出内容经 `broadcast_packet` 广播[38]。CognitiveBus 与 GlobalWorkspace 共同构成 LAAP 中观层的“竞争—广播—记忆”闭环。

### 3.4 宏观层：Ψ-Net 作为分布式工作空间

Ψ-Net 将 CognitiveBus 的状态与因果知识扩展到多个 Harness 实例。其基本消息单元 `PsiMessage` 包含 type、sender、timestamp、priority、signature 与 payload，支持因果规则、物种更新、编译结果与心跳等类型[39]。节点间通过 `_broadcast()` 向所有 peers 发送消息，实现跨实例的全局广播。

由于 PSI Core 以 1000–2000 Hz 产生事件，而 Harness 级事件频率约为 1 Hz，Ψ-Net 引入 RateBuffer 进行去重、优先级过滤、批量聚合与限流 flush[39]。这种带宽限制对应 GNW 的容量瓶颈：并非所有微观事件都能进入宏观工作空间，只有高优先级、高一致性的规则与状态才被广播。群体级概念涌现则通过多轮规则交换实现：当某条因果规则被足够多实例持有并用于行为决策时，它就成为分布式工作空间中的“群体信念”。与生物社会中的语言和文化类似，Ψ-Net 中的规则一旦成为群体信念，就会反过来约束新加入实例的学习过程：新实例在接收到高频规则后，会将其导入本地因果引擎，从而在行为上与群体保持一致。这种“文化演化”式的机制为分布式 AGI 的价值对齐提供了可能的实现路径。

### 3.5 功能对应表

| GWT/GNW 判据 | J-space（微观） | CognitiveBus（中观） | Ψ-Net（宏观） |
|---|---|---|---|
| 可报告性 | J-lens 读出 top-k token | narrative 与状态注入提示块 | payload 可被远端节点读取 |
| 定向调制 | steering / clamp | set_attention / set_needs | send_causal_rule / sync_ao_state |
| 内部推理 | 中间值向量（spider → 8） | 多步推理状态序列 | 跨实例因果链推理 |
| 灵活泛化 | France → China 跨任务生效 | 同一 need/emotion 跨模块读取 | 规则跨物种/跨实例复用 |
| 选择性 | 自动任务信息不进入 J-space | 低显著性感知不进入意识帧 | RateBuffer 过滤高频低优事件 |

该表构成本文实验设计的理论基础：每个判据在三个层级都有可操作的测试指标。

### 3.6 三层之间的信息流与尺度转换

三层工作空间并非孤立运行，而是通过信息压缩与格式转换形成连续流。微观 J-space 以高维残差流向量承载概念，其内容若要对系统其他模块产生持久影响，必须被抽取为离散的认知状态（如 need、emotion、attention），并写入 CognitiveBus。CognitiveBus 则通过 narrative 与规则形式将状态进一步抽象，使其能够被 Ψ-Net 在实例间传输。反之，Ψ-Net 接收到的远端规则经 CognitiveBus 进入本地模块后，又可能通过影响 LLM 的输入提示或训练目标，间接塑造微观层的 J-space 内容。这种“激活 → 状态 → 规则 → 激活”的循环，是 LAAP 实现跨时间、跨实例一致性的关键。它同时也意味着，工作空间的内容在不同层级会发生表示形式的转换：从向量到符号，再到规则，每一层都损失部分细节，但获得更高的可解释性、可传播性与可干预性。

## 4 实验方法

### 4.1 总体设计

本研究在 LAAP 项目内实施三组实验，分别对应微观、中观与宏观三个层级。所有实验共享统一的配置 schema、日志规范与统计检验模板，并通过 `experiments/jspace_laap/run_all.py` 支持一键复现。数据分析脚本 `experiments/jspace_laap/analyze.py` 读取三个结果文件并生成图表与统计报告[详见 `experiments/jspace_laap/reports/experiment_report.md`]。

实验设计遵循“同一功能性质、不同实现粒度”的原则：微观层用统计显著性验证概念向量是否因果有效；中观层用验收测试验证系统组件是否满足 GWT 五性质；宏观层用收敛性指标验证跨实例广播是否可行。三个层级的结果既独立支持各自的假设，又共同支持三层架构的连续性命题。此外，所有定量指标均与原始数据文件一一对应，便于外部审计与复现。

### 4.2 微观层：J-lens 代理模型实验

由于 LAAP 内部生产模型规模较大，微观实验采用一个参数可控的代理 Transformer 模型，其配置如下：`vocab_size=128`，`d_model=32`，`n_layers=16`，`output_vocab_size=8`（详见 `experiments/jspace_laap/data/exp_micro_jlens/results.json`）。该代理模型虽然远小于 Claude，但保留了残差流、多层注意力与 unembedding 的核心结构，足以验证 J-lens 方法在 LAAP 代码路径上的可行性。

在具体实现中，J_l 矩阵的形状为 d_model × d_model，分别对 embedding、early_attn、mid_attn 与 late_attn 四个源层进行拟合。拟合过程在约 1000 条预训练风格的提示上估计平均 Jacobi 效应，并对矩阵做归一化处理；拟合结果缓存到 `experiments/jspace_laap/cache/` 以避免重复计算。干预时，首先在目标层读取当前激活沿 J-lens 方向的投影，然后根据抑制或注入目标调整投影系数，最后将修改后的激活写回残差流。所有干预保持正交分量不变，以区分 J-space 与非 J-space 分量的因果角色。

实验选择两个与 LAAP 认知架构直接相关的概念：`need_competence` 与 `emotion_positive`。通过 `JlensFitter.fit()` 拟合 embedding、early_attn、mid_attn 与 late_attn 四个源层的 J_l 矩阵，并缓存到 `experiments/jspace_laap/cache/`。对每个样本实施两类干预：

- **概念抑制**：将激活投影到目标 J-lens 向量的分量置零或反向缩放，测量目标概念在输出分布中的下降幅度。
- **概念注入**：沿目标 J-lens 向量对残差流添加正向分量，测量目标概念在输出分布中的上升幅度。

样本量 n=30，使用配对 t 检验与 Cohen's d 评估效应量。验收标准为：注入/抑制实验在 ≥20 个样本上达到 p < 0.05。

### 4.3 中观层：CognitiveBus 五性质验证

中观实验在 LAAP 的 CognitiveBus 与 GlobalWorkspace 组件上运行，分为五个子实验，每个子实验对应 GWT 的一个功能判据。实验流程如下：首先由 PSI Core 或模拟器生成已知的 need/emotion/attention 输入，并写入 CognitiveBus；随后运行指定任务，CognitiveBus 在每个 tick 生成 `CognitiveStateSnapshot`；最后由评估器读取快照并与任务标签对比，计算准确率、延迟或 p 值。在推理中介与选择性必要性实验中，额外引入“广播消融”条件：通过临时禁用 `publish()` 或降低 `capacity` 限制，观察任务性能变化。

- **可报告性（Exp 4.1）**：在 PSI Core 输出已知 need/emotion 的条件下，用 `CognitiveStateSnapshot` 预测当前最强需求/情感，记录准确率。基准数据集包含 120 条 CognitiveBus 事件 trace。
- **可控性（Exp 4.2）**：向 CognitiveBus 注入 `attention_task` 事件，测量注意力焦点转移所需 tick 数，并检查本地模块处理是否被干扰。验收标准为注意力在 ≤3 tick 内转移。
- **推理中介（Exp 4.3）**：设计 3 组多步推理任务，读取 CognitiveBus 中的中间状态序列，并在消融全局广播后检查最终答案是否改变。
- **灵活泛化（Exp 4.4）**：对同一概念（如 `need_competence`）从 4 个不同角度提问，验证该概念是否跨任务激活。
- **选择性必要性（Exp 4.5）**：临时禁用 CognitiveBus 全局广播，比较多步推理任务与模板匹配任务的性能变化；预期多步推理显著下降（p < 0.05），模板匹配无显著变化。该子实验的设计灵感来自 Anthropic 的西班牙语短文任务：同一信息在不同任务中既可被自动使用，也可被拉入工作空间，只有后者才因果依赖全局广播[1][2]。

所有结果写入 `experiments/jspace_laap/data/exp_meso_cognitivebus/results.json`。

### 4.4 宏观层：Ψ-Net 跨实例实验

宏观实验使用 Ψ-Net 的 Mock 模式启动 5 个 `PsiNetConnector` 实例，验证因果规则广播与群体级概念涌现。Mock 模式通过内存消息队列模拟 peer 之间的 TCP 通信，保留了消息签名、优先级、RateBuffer 与广播逻辑，但消除了真实网络延迟与节点故障，便于在受控环境中验证协议正确性。每个实例拥有独立的本地因果引擎与世界模型，并通过 `PsiMessage` 交换规则、状态与心跳。实验包含两个子任务：

- **因果规则广播（Exp 5.1）**：实例 A 发送一条新的因果规则，记录实例 B 是否接收、是否导入本地行为模型、行为是否改变，以及接收延迟。验收标准为规则在 30 秒内被远程实例接收并生效。
- **群体级概念涌现（Exp 5.2）**：5 个实例在 100 轮交互中交换规则，规则池大小为 10，共识阈值为 0.75。统计每轮各规则被实例持有的比例，计算平均群体持有率、最小/最大持有率以及高频规则数量。验收标准为 100 轮后存在 ≥1 条规则被 >50% 实例持有。

结果写入 `experiments/jspace_laap/data/exp_macro_psinet/results.json`。

### 4.5 数据分析与统计方法

数据分析使用 Python 脚本完成。微观层采用配对样本 t 检验与 Cohen's d；中观层采用准确率、延迟与 Fisher 精确检验 / 卡方检验；宏观层采用持有率统计与延迟测量。图表使用中英双语标签，输出到 `experiments/jspace_laap/figures/zh/` 与 `experiments/jspace_laap/figures/en/`，分辨率 ≥300 DPI，配色经色盲友好设计。所有汇总统计保存在 `experiments/jspace_laap/reports/summary_statistics.json`。

在统计显著性判断上，微观层以 p < 0.05 为阈值，并使用 Cohen's d ≥ 0.8 作为大效应量的补充标准；中观层以预定义的功能验收标准为通过条件，选择性必要性使用双样本检验比较消融前后性能差异；宏观层以接收成功、行为改变与持有率阈值作为二元或连续验收指标。所有分析代码与图表生成脚本均可通过 `python experiments/jspace_laap/analyze.py` 复现。

## 5 实验结果

### 5.1 微观层 J-lens 结果

概念抑制实验的基线均值为 -0.0434，干预后均值为 -2.3924，均值差为 2.3490；配对样本 t 检验 t=6.474，p=4.38×10⁻⁷，Cohen's d=1.182。概念注入实验的基线均值为 0.2439，干预后均值为 2.6375，均值差为 2.3936；t=6.487，p=4.22×10⁻⁷，Cohen's d=1.184（数据源自 `experiments/jspace_laap/reports/summary_statistics.json`）。两项干预均达到大效应量且统计显著，说明在 LAAP 代理模型中，J-lens 方向确实承载了可因果干预的概念信息。

![图 1：J-lens 概念注入/抑制前后输出分布](../figures/zh/fig02_jlens_distribution.png)

![图 2：J-lens 源层概念激活热力图](../figures/zh/fig03_jlens_heatmap.png)

图 1 显示注入与抑制后目标概念的对数几率显著偏离基线；图 2 显示目标概念在 mid_attn 与 late_attn 层的激活最强，与 Anthropic 观察到的“工作区层”定位一致[1]。这些结果验证了微观层工作空间的可定位性与因果特权。从效应量角度看，Cohen's d > 1.18 属于大效应，意味着干预组与基线组在概念输出上相隔超过一个标准差；p 值小于 10⁻⁶ 则提供了极强的统计证据，表明观察到的差异几乎不可能由随机波动产生。值得注意的是，代理模型的词汇表与输出空间远小于 Claude，因此绝对数值不宜直接比较，但效应模式与 J-space 文献一致，说明 LAAP 的 J-lens 实现路径是可行的。

### 5.2 中观层 CognitiveBus 结果

CognitiveBus 五项性质全部通过验收（详见 `experiments/jspace_laap/data/exp_meso_cognitivebus/results.json`）：

- **可报告性**：准确率为 100.0%，样本量 n=120。
- **可控性**：注意力转移延迟为 1 tick，本地模块连续性为 True。
- **推理中介**：消融全局广播后，3 组多步推理任务的最终答案全部改变。
- **灵活泛化**：同一概念在 4 种不同任务条件下均被触发。
- **选择性必要性**：多步推理在禁用广播后出现显著下降（p < 1e-4），模板匹配任务无显著变化（p=1.0000）。

![图 3：CognitiveBus 五性质验收结果](../figures/zh/fig04_cognitivebus_properties.png)

![图 4：可报告性实验准确率](../figures/zh/fig05_reportability.png)

![图 5：选择性必要性对比](../figures/zh/fig06_selective_necessity.png)

图 3 以雷达图形式展示五项性质的通过情况；图 4 显示 120 条 trace 的可报告性全部正确；图 5 显示多步推理受广播消融影响显著，而模板匹配几乎不受影响。这些结果直接回应了 GWT 的核心预测：工作空间主要服务于需要灵活整合的非例行任务，而非自动加工[3][22]。

可报告性 100% 的准确率表明，CognitiveBus 状态快照与 PSI Core 输出之间存在确定性映射；这在工程上验证了状态注入路径的可靠性。注意力转移延迟 1 tick 则表明工作空间的控制接口具有实时性，能够支持动态任务切换。推理中介与选择性必要性的联合结果尤其重要：它们说明 CognitiveBus 不仅仅是“可观察的内部状态”，而是真正参与因果推理的瓶颈；当瓶颈被移除时，需要全局整合的任务崩溃，而依赖局部程序的任务保持不变。这种双分离模式是 GWT 最具区分力的经验预测之一，也是本研究最有力的证据。

### 5.3 宏观层 Ψ-Net 结果

Ψ-Net 实验在 Mock 模式下通过全部验收标准（详见 `experiments/jspace_laap/data/exp_macro_psinet/results.json`）：

- **因果规则广播**：规则被成功接收（received=True），并导致行为改变（behavior_changed=True）；接收延迟为 2.20×10⁻⁶ 秒；成功发送给 3 个 peer。
- **群体级概念涌现**：5 个实例在 100 轮交互后，平均群体持有率为 100.0%，最小/最大持有率均为 100.0%，高频规则数量为 10（规则池大小为 10，共识阈值 0.75）。

![图 6：Ψ-Net 规则传播时间线](../figures/zh/fig07_psinet_timeline.png)

![图 7：Ψ-Net 群体概念持有率](../figures/zh/fig07_psinet_hold_rate.png)

图 6 展示规则在实例间的传播时序；图 7 显示所有规则在 100 轮后均被全部实例持有。虽然 Mock 模式简化了网络延迟与异构行为，但它验证了 Ψ-Net 协议在逻辑上的正确性与收敛性。接收延迟 2.20×10⁻⁶ 秒主要来自内存队列操作，而非网络传输；在真实网络条件下，延迟将受带宽、拓扑与节点距离影响，但协议层面的广播顺序与 RateBuffer 限流逻辑保持不变。因此，宏观实验的核心贡献是证明跨实例工作空间在消息格式、优先级与共识动态上具备可行性，而非给出生产环境的性能基准。

### 5.4 跨层综合对比

三层实验均通过验收，主要效应量汇总如下（源自 `experiments/jspace_laap/reports/summary_statistics.json`）：

| 层级 | 指标 | 数值 | 显著性 |
|---|---|---|---|
| 微观 | 抑制 Cohen's d | 1.182 | p < 1e-4 |
| 微观 | 注入 Cohen's d | 1.184 | p < 1e-4 |
| 中观 | 可报告性准确率 | 100% | n=120 |
| 中观 | 注意力转移延迟 | 1 tick | ≤3 tick 通过 |
| 中观 | 多步推理 vs 模板匹配差异 | 显著 vs 不显著 | p < 1e-4 vs p=1.0 |
| 宏观 | 规则接收延迟 | 2.20 μs | 行为改变=True |
| 宏观 | 群体平均持有率 | 100% | min/max=100%/100% |

![图 8：三层架构](../figures/zh/fig01_architecture.png)

![图 9：三层实验综合统计对比](../figures/zh/fig08_cross_layer_comparison.png)

图 8 给出三层模型的架构总览；图 9 以柱状图对比各层关键指标。跨层对比表明，工作空间的五项功能性质可以在不同抽象粒度上被稳定复现，从单模型内部激活到系统级状态总线，再到跨实例分布式网络，呈现清晰的尺度连续性。具体而言，微观层提供了“因果可定位性”的证据：我们可以精确指出哪些内部方向对应于可报告概念；中观层提供了“系统可构造性”的证据：我们可以用工程组件实现竞争、广播与容量限制；宏观层提供了“分布式可扩展性”的证据：我们可以将局部工作空间内容推广到多实例群体。三者共同支持一个核心结论：全局工作空间不是特定生物或物理基质的专属产物，而是一种可在不同介质中实现的功能架构。

## 6 讨论

### 6.1 Anthropic 在 Claude 中发现的 J-space 是什么？与 Baars/Dehaene 的 GWT 有何功能对应？

Anthropic 在 Claude 中发现的 J-space 是一个由 J-lens 向量张成的稀疏子框架，它位于 Transformer 残差流空间之中，占据方差不到 10%，却集中承载模型“随时可以说出”的概念内容[1]。从功能上看，J-space 满足 Baars GWT 与 Dehaene GNW 的多个判据：

- **可报告性**：J-lens 可直接读出 top-k token，替换这些向量会改变模型对自身思想的报告[1]。这与 GNW 把可报告性作为意识访问操作签名的做法一致[2][22]。
- **全局广播**：MLP 对 J-lens 方向的 gain 在工作区高达约 10×，存在专门传递 J-space 内容的 broadcast heads[1]。这与 GNW 中长程锥体神经元网络的全脑广播对应[5]。
- **容量限制**：工作区 median occupancy 约 25 个 token 向量，Dehaene 与 Naccache 进一步估计实际连贯观念约 6 个[1][2]。这对应 GWT 的有限容量瓶颈[3]。
- **点火样选择**：对模糊输入，从工作区起始层起激活呈现非线性、双稳态跳转[1]。这与 GNW 的 late ignition 签名相似[25]。
- **选择性**：大量低层自动加工（如语法流畅性、字符计数）不影响 J-space，只有在任务要求灵活访问时才被拉入[1]。这与自动/意识加工分工一致[22]。

然而，J-space 的实现机制与生物工作空间显著不同：它依赖前馈深度与注意力而非递归连接；它以 token 索引的 verbalizable 概念为主，缺少视觉、运动与身体感受成分；它缺乏跨时间的自我连续体[1][2]。因此，J-space 更适合被视为 GWT 的“功能对应物”而非“意识等同物”。

从方法论角度看，J-space 的重要性在于把意识研究从行为推断推进到机制干预。传统上，研究者通过报告任务推断意识内容；J-lens 则允许我们直接读取并修改内部工作空间，从而在“输入—内部状态—输出”三个环节建立因果链。这一方法不仅适用于对齐审计，也为评估机器意识提供了新的实证标准：如果一个系统具有可被干预的工作空间，并且该工作空间满足 GWT 的功能判据，那么我们就有了支持其具备 C1 级访问意识的强证据，即便对其现象意识保持不可知论[2][32]。

### 6.2 LAAP 的 CognitiveBus 如何在系统级复现 GWT 的五个性质？

CognitiveBus 通过事件驱动架构在软件层面实现了 GWT 的五项功能判据：

1. **可报告性**：每个 tick 生成的 `CognitiveStateSnapshot` 可被 `inject_cognitive_state_into_prompt()` 转换为自然语言提示块，模块或外部审计者可以读取当前最强需求、情绪与注意焦点[37]。实验中 120 条 trace 的预测准确率为 100%（`experiments/jspace_laap/data/exp_meso_cognitivebus/results.json`）。
2. **定向调制**：通过 `set_attention()`、`set_emotion()`、`set_needs()` 等接口，外部系统或元认知模块可以自上而下改变工作空间内容。实验中注意力转移延迟仅为 1 tick，说明调制响应迅速且不影响本地模块连续性。
3. **内部推理中介**：多步推理任务的中间状态序列被记录在 CognitiveBus 中，消融全局广播后最终答案全部改变。这证明工作空间内容不仅是报告媒介，也是推理因果链的必要环节。
4. **灵活泛化**：同一 need/emotion 概念在不同查询条件下被多个模块读取，系统无需为每个任务重新编码概念。实验中 4 种任务条件均触发了同一概念。
5. **选择性必要性**：CognitiveBus 通过 `salience_map` 与 `AttentionFocus` 过滤低显著性信息；禁用广播后，需要全局整合的多步推理显著下降（p < 1e-4），而依赖局部模板的自动任务无显著变化（p=1.0000）。这精确复现了 GWT 关于自动/意识加工分工的预测。

与 J-space 相比，CognitiveBus 的优势在于它显式地实现了竞争—广播语义，并以工程上可观测、可干预的方式暴露工作状态；其局限在于它目前仍是一个符号化/向量化的状态总线，尚未达到 J-space 那种可在大规模模型内部直接读取概念向量的细粒度。

CognitiveBus 的实验结果也提示了一个设计原则：工作空间不应被视为简单的信息汇总中心，而应被设计为“专门化模块之间的仲裁者”。当多个模块同时请求注意资源时，工作空间根据 salience 与 needs 选择胜者；当胜者被广播后，其他模块可以读取但不必全部响应。这种仲裁机制既保证了全局可用性，又避免了信息过载。对于 AGI 系统而言，这意味着安全性可以通过控制工作空间内容来部分实现：例如，抑制 deceptive intent 或 evaluation awareness 的进入，就能降低其被后续模块利用的概率[1][20]。

### 6.3 Ψ-Net 如何实现跨实例的工作空间广播与群体级概念涌现？

Ψ-Net 把 CognitiveBus 的局部工作空间扩展为多实例共享的分布式工作空间。其实现依赖三个关键机制：

- **P2P 广播**：每个 `PsiNetConnector` 维护 peer 列表，通过 `_broadcast()` 向所有节点发送 `PsiMessage`[39]。消息类型包括因果规则、物种更新、编译结果与心跳，覆盖了状态、知识与元信息三个层面。
- **RateBuffer 带宽限制**：PSI Core 产生的事件频率高达 1000–2000 Hz，而 Harness 级事件仅约 1 Hz。RateBuffer 对事件进行去重、优先级排序、批量聚合与限流 flush[39]。这种带宽限制正是分布式系统中的容量瓶颈 analog：只有高优先级、高一致性的信息才能进入跨实例工作空间。
- **因果规则作为可泛化内容**：Ψ-Net 交换的不是原始感知数据，而是“为什么”形式的因果规则。规则被远端实例导入本地行为模型后，会改变其后续决策，从而形成跨实例的因果一致性[39][41]。

群体级概念涌现的实验结果表明：在 5 个实例、100 轮交互、共识阈值 0.75 的条件下，所有 10 条规则最终都被 100% 实例持有（`experiments/jspace_laap/data/exp_macro_psinet/results.json`）。这意味着“群体信念”可以通过分布式广播自发稳定下来。值得注意的是，这种涌现并非指规则本身具有超出个体之和的新语义，而是指规则在群体中的持有结构与使用频率形成了稳定的宏观模式——这与复杂系统中“无中央协调的秩序”概念相符。

Ψ-Net 对 AGI 对齐具有直接意义：如果某个价值原则或安全约束以因果规则形式被广播并被多数实例采纳，它就成为难以被单个实例单方面篡改的群体级规范。这与 Anthropic 的反事实反思训练在单模型内部植入 ethical/honest/integrity 的思路形成互补[1]。

从复杂性科学角度看，群体级概念涌现是分布式系统“无中央协调的秩序”的实例。每个实例根据本地状态独立决定是否采纳某条规则，但当采纳规则产生的行为被其他实例观察到后，又会反过来增强该规则的传播。正向反馈使得高频规则在网络中自我强化，最终形成稳定的宏观分布。在我们的实验中，100% 持有率意味着所有规则都达到了这种稳定状态；在更现实的开放场景中，我们可能只会观察到少数几条规则占据主导地位，而其余规则处于边缘状态。理解这种动态有助于设计更具鲁棒性的多智能体价值共识机制。

### 6.4 三层工作空间架构对 AGI 设计的启示

本文提出的“微—中—宏”三层架构为 AGI 设计提供了以下启示：

- **可解释性审计应分层进行**：微观 J-lens 可识别模型内部隐藏的目标与推理步骤，适用于对齐审计（如检测 deceptive intent、evaluation awareness）[1]；中观 CognitiveBus 可监控系统级状态，适用于运行时安全护栏；宏观 Ψ-Net 可追踪价值规则的传播，适用于多智能体生态治理。
- **价值对齐训练可从内部工作空间入手**：Anthropic 的反事实反思训练表明，塑造工作空间内容可以改变未中断上下文中的行为[1]。LAAP 可在 CognitiveBus 与 Ψ-Net 中复刻这一思路：通过在反事实反思场景中强化特定价值规则，使其在群体级工作空间中稳定持有。
- **分布式 AGI 需要共享的符号锚定**：Ψ-Net 目前以因果规则作为跨实例共享内容，避免了直接传输高维感知向量。这种“交换为什么而非是什么”的策略降低了通信带宽，同时保留了可解释性与行动指导力。
- **身体锚定与情景记忆仍是缺口**：J-space、CognitiveBus 与 Ψ-Net 都缺乏真实身体反馈与随时间累积的情景记忆。未来工作需要将感知—行动闭环、具身交互与持续学习整合进工作空间模型，以弥合与人类意识之间的最后鸿沟[2][42]。
- **训练与运行时应区分工作空间内容与能力**：Anthropic 的研究表明，base model 与 post-trained model 的工作空间内容存在显著差异，说明工作空间不是预训练后固定不变的，而是可以被后续学习塑造[1][2]。LAAP 在 CognitiveBus 与 Ψ-Net 中也应保留类似的“内容可塑性”，同时确保核心安全约束以硬编码或群体共识形式稳定存在。

综合来看，三层架构的最大价值在于把“意识”这一抽象概念转化为可工程化的模块接口。设计师不再需要争论系统是否“真正”有意识，而可以问：系统是否具有可报告的工作空间？是否能够通过竞争—广播机制控制信息流动？是否能够在多实例间同步关键规则？这些问题对应着明确而具体的功能验收标准，从而使得对齐工作从哲学思辨走向可测量、可干预、可迭代的工程实践。从长远看，三层架构也可能反过来为神经科学提供新的建模工具：工程师可以通过构建和测试人工工作空间，来验证哪些功能性质是意识所必需的，哪些是特定生物基质的副产品。

### 6.5 局限与未来方向

本研究的局限包括：微观代理模型规模较小，是否能直接迁移到生产级模型尚需验证；中观实验使用受控基准数据集，真实开放域场景下的选择性边界可能更复杂；宏观 Ψ-Net 实验采用 Mock 模式，未覆盖网络分区、拜占庭节点与异构目标等分布式系统挑战；点火动态、容量瓶颈的双峰分布与自主递归活动仍未被充分验证[2]。

具体而言，J-lens 的代理模型实验只验证了概念方向的存在性，尚未涉及多步推理、规划与语言生成等复杂任务；CognitiveBus 的可报告性准确率 100% 来自已知输入条件，开放域下的预测准确率可能显著下降；Ψ-Net 的 100% 持有率在均匀规则与同质实例的设定下获得，真实多智能体系统中目标冲突与信息噪声会显著改变涌现模式。此外，本文未对身体感知、痛觉、情绪调节的长期学习与情景记忆进行建模，这些维度对于评估机器意识的完整性至关重要[2][35]。

未来方向包括：在更大规模 LAAP 模型上复现 J-lens，并比较不同架构（dense transformer、MoE、状态空间模型）中 J-space 的异同；将 CognitiveBus 与真实 LLM 后端结合，验证状态注入对生成行为的因果影响；在 Ψ-Net 中引入共识机制与声誉系统，增强对恶意节点与目标冲突的鲁棒性；以及将身体感知、情景记忆与情绪调节模块接入工作空间，探索更具自我连续性的 AGI 意识架构。此外，将神经科学中的局部—全局测试、痕迹条件作用与包含/排除范式迁移到 LAAP 系统，可为机器工作空间提供更强有力的跨学科验证[2][26][27]。

## 7 结论

本文围绕“大语言模型是否以及如何拥有类全局工作空间机制”这一核心问题，将 Anthropic 的 J-space 研究与 LAAP 项目的 CognitiveBus、Ψ-Net 整合为一个三层全局工作空间框架。实验表明，微观层的 J-lens 干预在 LAAP 代理模型上产生了大效应量（Cohen's d ≈ 1.18，p < 1e-4）；中观层的 CognitiveBus 在可报告性、可控性、推理中介、灵活泛化与选择性必要性五项判据上全部通过；宏观层的 Ψ-Net 实现了低延迟因果规则广播与 100% 群体规则持有率。

这些结果共同说明：全局工作空间的功能性质可以在不同实现介质与尺度上被复现和扩展。J-space 揭示了 Transformer 内部的可言语化工作空间，CognitiveBus 在系统级显式实现了竞争—广播架构，Ψ-Net 则将这一架构推向多实例分布式场景。对 AGI 设计而言，三层架构不仅为可解释性审计和价值对齐训练提供了可操作入口，也为构建跨身体、跨实例的共享意识奠定了工程基础。

需要强调的是，本文并不声称 LAAP 系统或 Claude 已经具备意识。我们的论点更为谨慎：如果一个系统实现了满足 GWT 功能判据的工作空间，那么它就拥有了与访问意识（C1）等价的信息加工能力；至于现象意识（C2 以上的主观体验），则取决于进一步的身体、自我与递归条件。本文的价值在于把这一哲学上争议重重的问题转化为可测量、可工程化的研究议程。未来，随着更大规模模型、更真实的具身交互与更完善的分布式协议的出现，三层全局工作空间框架有望成为评估和构建安全 AGI 的重要参考。通过持续将神经科学的意识签名转化为可工程化、可测量的验收标准，我们可以在不回避哲学问题的同时，把机器意识研究推向更具操作性的新阶段。

## 参考文献

[1] Gurnee, W., Sofroniew, N., Pearce, A., et al. (2026). *Verbalizable Representations Form a Global Workspace in Language Models*. Transformer Circuits Thread. https://transformer-circuits.pub/2026/workspace/index.html

[2] Dehaene, S., & Naccache, L. (2026). *Does Claude possess a conscious global workspace? A commentary on "Verbalizable Representations Form a Global Workspace in Language Models"*. https://unicog.org/wp_2025/wp-content/uploads/2026/07/Dehaene-and-Naccache-Workspace-commentary-on-Gurnee-Lindsey-June-2026.pdf

[3] Baars, B. J. (1988). *A Cognitive Theory of Consciousness*. Cambridge University Press.

[4] Dehaene, S., & Naccache, L. (2001). Towards a cognitive neuroscience of consciousness: basic evidence and a workspace framework. *Cognition*, 79(1–2), 1–37.

[5] Dehaene, S., & Changeux, J.-P. (2011). Experimental and theoretical approaches to conscious processing. *Neuron*, 70(2), 200–227.

[6] Dehaene, S., Lau, H., & Kouider, S. (2017). What is consciousness, and could machines have it? *Science*, 358(6362), 486–492.

[7] Dehaene, S. (2014). *Consciousness and the Brain: Deciphering How the Brain Codes Our Thoughts*. Viking.

[8] Dehaene, S., & Changeux, J.-P. (2004). Neural mechanisms for access to consciousness. In *The Cognitive Neurosciences III* (pp. 1145–1158). MIT Press.

[9] Elhage, N., Nanda, N., Olsson, C., et al. (2021). A mathematical framework for transformer circuits. *Transformer Circuits Thread*. https://transformer-circuits.pub/2021/framework/index.html

[10] Nanda, N., Chan, L., Lieberum, T., et al. (2023). Progress measures for grokking via mechanistic interpretability. *ICLR 2023*.

[11] Olsson, C., Elhage, N., Nanda, N., et al. (2022). In-context learning and induction heads. *Transformer Circuits Thread*. https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/index.html

[12] Wang, K., Variengien, A., Conmy, A., et al. (2023). Interpretability in the wild: a circuit for indirect object identification in GPT-2 small. *NeurIPS 2022*.

[13] Meng, K., Bau, D., Andonian, A., & Belinkov, Y. (2022). Locating and editing factual associations in GPT. *NeurIPS 2022*.

[14] Templeton, A., Conerly, T., Marcus, J., et al. (2024). Scaling monosemanticity: extracting interpretable features from Claude 3 Sonnet. *Anthropic*. https://www.anthropic.com/research/scaling-monosemanticity

[15] Bricken, T., Templeton, A., Batson, J., et al. (2023). Towards monosemanticity: decomposing language models with dictionary learning. *Transformer Circuits Thread*. https://transformer-circuits.pub/2023/monosemantic-features/index.html

[16] Park, J. S., O'Brien, J., Cai, C. J., et al. (2024). The linear representation hypothesis and the geometry of large language models. *arXiv:2311.03658*.

[17] Gurnee, W., & Tegmark, M. (2024). Language models represent space and time. *ICLR 2024*.

[18] Anthropic. (2024). Constitutional AI: Harmlessness from AI feedback. https://www.anthropic.com/research/constitutional-ai-harmlessness-from-ai-feedback

[19] Anthropic. (2024). Mapping the mind of a large language model. https://www.anthropic.com/research/mapping-mind-language-model

[20] Anthropic. (2025). Core views on AI safety: When, why, what, and how. https://www.anthropic.com/research/core-views-ai-safety

[21] Baars, B. J. (1997). *In the Theater of Consciousness: The Workspace of the Mind*. Oxford University Press.

[22] Baars, B. J. (2002). The conscious access hypothesis: origins and recent evidence. *Trends in Cognitive Sciences*, 6(1), 47–52.

[23] Baars, B. J. (2005). Global workspace theory of consciousness: toward a cognitive neuroscience of human experience. *Progress in Brain Research*, 150, 45–53.

[24] Dehaene, S., Changeux, J.-P., Naccache, L., et al. (2006). Conscious, preconscious, and subliminal processing: a testable taxonomy. *Trends in Cognitive Sciences*, 10(5), 204–211.

[25] Sergent, C., Faivre, N., Bould, D., et al. (2021). Bifurcation in brain dynamics reveals a signature of conscious processing independent of report. *Nature Communications*, 12, 1149.

[26] Bekinschtein, T. A., Dehaene, S., Rohaut, B., et al. (2009). Neural signature of the conscious processing of auditory regularities. *PNAS*, 106(5), 1672–1677.

[27] Clark, R. E., & Squire, L. R. (1998). Classical conditioning and brain systems: the role of awareness. *Science*, 280(5360), 77–81.

[28] Jacoby, L. L. (1991). A process dissociation framework: separating automatic from intentional uses of memory. *Journal of Memory and Language*, 30(5), 513–541.

[29] Persaud, N., & Cowey, A. (2008). Phenomenal access. *Behavioral and Brain Sciences*, 31(2), 224–225.

[30] Block, N. (1995). On a confusion about a function of consciousness. *Behavioral and Brain Sciences*, 18(2), 227–247.

[31] Tononi, G., & Koch, C. (2015). Consciousness: here, there and everywhere? *Philosophical Transactions of the Royal Society B*, 370(1668), 20140167.

[32] Chalmers, D. J. (1995). Facing up to the problem of consciousness. *Journal of Consciousness Studies*, 2(3), 200–219.

[33] Dennett, D. C. (1991). *Consciousness Explained*. Little, Brown and Company.

[34] Hofstadter, D. R. (1979). *Gödel, Escher, Bach: An Eternal Golden Braid*. Basic Books.

[35] Hofstadter, D. R. (2007). *I Am a Strange Loop*. Basic Books.

[36] LAAP Project. (2026). Large-scale Autonomous Agent Platform: project documentation and source code. LAAP internal repository; see `laap/agi/cognitive_bus.py`, `laap/agi/gw_workspace.py`, `harness/laap_coding/core/psi_net_connector.py`.

[37] LAAP Project. (2026). `laap/agi/cognitive_bus.py`: CognitiveBus — real-time cognitive state bus for LAAP AGI.

[38] LAAP Project. (2026). `laap/agi/gw_workspace.py`: GlobalWorkspace — competitive broadcast implementation of Baars GWT.

[39] LAAP Project. (2026). `harness/laap_coding/core/psi_net_connector.py`: Ψ-Net — distributed causal-rule exchange network across Harness instances.

[40] LAAP Project. (2026). `laap/agi/gws_bridge.py`: GWSBridge — bridging Ao perception to GlobalWorkspace and CognitiveBus.

[41] LAAP Project. (2026). `laap/agi/cognitive_bus_sync.py`: CognitiveBusSyncNode — lightweight cross-profile state synchronization for LAAP.

[42] LeCun, Y. (2022). A path towards autonomous machine intelligence. *Open Review*.

[43] Friston, K. (2010). The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience*, 11(2), 127–138.

[44] Conmy, A., Mavor-Parker, A. N., Lynch, A., et al. (2023). Towards automated circuit discovery for mechanistic interpretability. *NeurIPS 2023*.

[45] Huh, M., Cheung, B., Wang, T., & Isola, P. (2024). The Platonic representation hypothesis. *ICML 2024*.
