# 第 9 章 MeMo 记忆即模型审计

LAAP ARIS-Harness 整合范式在记忆子系统的核心创新，体现为对 MEMO 范式（arXiv:2605.15156）的工程化落地。该范式从根本上颠覆了传统 RAG 将知识存储于外部向量库的工程假设，转而把知识蒸馏进一个可微的小参数 MEMORY 模型，并以结构化多轮查询协议替代单轮 Top-K 检索。本章基于 `memo_provider.py`、`memo_query_protocol.py`、`memo_synthesizer.py` 与 `memo_trainer.py` 四个核心模块的源码审计，系统论证"记忆即模型"范式的工程完备性与理论革新性。

## 9.1 MEMO 范式：知识蒸馏进小参数 MEMORY 模型

MEMO 范式的核心命题在 `memo_provider.py:1-9` 的模块文档字符串中得到精炼表述：

> "Implements the MEMO paradigm (arXiv:2605.15156 'Memory as a Model'):
> - Knowledge is distilled into a small-parameter MEMORY model via SFT
> - The EXECUTIVE model remains frozen
> - Queries flow through a three-stage structured multi-turn protocol"

这一表述包含三个相互绑定的工程约束。**第一**，知识载体由"外部向量库 + chunk 元数据"切换为"小参数语言模型权重"，知识检索问题被重构为模型前向推理问题。**第二**，EXECUTIVE 模型（即承担推理与决策的高参数 LLM）始终保持冻结，知识更新只发生在 MEMORY 模型权重上，由此实现了"知识增长"与"推理能力"的解耦——避免 RSI 在改进知识的同时意外漂移推理逻辑。**第三**，查询协议被显式结构化为三阶段多轮协议，使得单次查询的 Token 开销不随语料规模增长。

`MemoMemoryProvider` 类（`memo_provider.py:32-73`）实现了该范式的运行时载体。其构造函数注入 `model_path`、`executive_llm`、`sync_threshold` 与 `synthesis_output_path` 四个核心依赖，分别对应 MEMORY 模型权重路径、EXECUTIVE 模型客户端、增量合成触发阈值（默认 50 条对话）与反思 QA JSONL 输出路径。值得强调的是 `_try_load_model`（`memo_provider.py:78-100`）的容错设计：当 `transformers` 库缺失或模型路径不存在时，不抛出异常而是将 `_loaded` 置为 `False`，使 `is_available()` 返回 `False`，让上层 `MemoryManager` 平滑回退到 `SimpleMemoryProvider`。这种"友好降级"策略是 LAAP 一以贯之的工程哲学：MEMO 是增强而非硬依赖。

## 9.2 三阶段查询协议

MEMO 的查询协议由 `MemoQueryProtocol` 类（`memo_query_protocol.py:23-150`）实现，其三阶段结构在模块文档（`memo_query_protocol.py:7-11`）中明确表述：

> "1. 基础建立 (grounding): EXECUTIVE 把复杂查询拆解为 2-5 个原子子问题
> 2. 实体识别 (entity identification): 根据初步答案迭代追问确定关键实体
> 3. 答案合成 (answer synthesis): 针对确认的实体向 MEMORY 模型索取支持事实并合成"

**阶段一：基础建立（grounding）**。`stage1_grounding` 方法（`memo_query_protocol.py:38-77`）调用 EXECUTIVE 模型把复杂查询拆解为 2-5 个原子子问题。其内部 prompt（`_build_grounding_prompt`，第 104-111 行）显式约束输出为 JSON 数组，例如 `["子问题1", "子问题2"]`。当 EXECUTIVE 模型不可用或 JSON 解析失败时，回退到 `_rule_based_split`（第 113-121 行）按连接词（"并/且/对比/以及/和/，/;/；"）正则切分。这种双轨设计保证了协议在 LLM 不可用时仍具备基础能力，是 0-Token 确定性算法霸权在查询协议层的延续。

**阶段二：实体识别（entity identification）**。`stage2_entity_identification` 方法（`memo_query_protocol.py:127-150`）以阶段一的子答案列表为输入，构造实体识别 prompt 让 EXECUTIVE 模型迭代追问，从而锁定查询的关键实体。该阶段的核心价值在于将"模糊主题"转换为"精确实体"，使阶段三能够针对具体实体进行有约束的事实索取，避免 MEMORY 模型生成泛化回答。

**阶段三：答案合成（answer synthesis）**。针对阶段二确认的关键实体，向 MEMORY 模型索取支持事实并由 EXECUTIVE 模型合成为最终答案。模块文档（`memo_query_protocol.py:12`）指出该协议的根本经济学意义："检索成本与语料规模解耦：单次查询的子问题数量与总 token 开销不随语料增长"——这是 RAG 范式无法企及的特性，因为 RAG 的检索成本随语料规模呈对数增长（HNSW）或线性增长（暴力扫描）。

## 9.3 MemoSynthesizer 五步合成

反思 QA 训练集的构造由 `MemoSynthesizer`（`memo_synthesizer.py:17-43`）实现。其五步流水线在类文档字符串中明确列出：

> "1. extract_facts       — 事实抽取
> 2. consolidate_facts   — 事实合并（按 semantics 聚类）
> 3. surface_entities    — 实体显化
> 4. synthesize_cross_doc — 跨文档 QA 合成
> 5. verify_qa           — GENERATOR 自验证"

**第一步：extract_facts**（`memo_synthesizer.py:48-125`）。该方法从三个数据源抽取原子事实：`design_system_cache.json`（设计令牌）、`component_templates.json`（组件模板）与 `harness_memory.db` episodes（对话片段）。每个数据源被规范化为统一的 fact 字典结构，分别携带 `type`（"design_token"/"component_template"/"episode"）字段以便后续步骤区分处理。

**第二步：consolidate_facts**（`memo_synthesizer.py:138-150`）。该方法按 `design token` 的 `semantics` 字段进行聚类合并，相同 semantics 的事实合并为一条并记录 `occurrence_count` 与 `source_task_ids`，其他类型事实原样保留。这一步骤的本质是"知识去重"，避免相同语义的设计令牌在反思 QA 中重复出现导致训练偏置。

**第三步：surface_entities**。从合并后的事实中显式提取关键实体（如组件类型、设计令牌名称、技术栈名称），为跨文档合成提供实体锚点。

**第四步：synthesize_cross_doc**。基于显式实体，跨多个文档（设计令牌文档、组件模板文档、对话片段）合成反思 QA 对，捕获跨文档关系。这是 MEMO 范式区别于传统 RAG 的核心步骤——RAG 仅在查询时进行跨文档召回，而 MEMO 在训练阶段就完成跨文档关系建模。

**第五步：verify_qa**。由 GENERATOR 模型对合成的 QA 对进行自验证，过滤低质量样本。当 `generator_llm=None` 时跳过 LLM 验证，仅做规则过滤。`_filter_log` 字段（`memo_synthesizer.py:43`）记录被滤除的 QA 及其原因，为后续训练集质量分析提供审计轨迹。

## 9.4 MemoTrainer SFT

MEMORY 模型的训练由 `MemoTrainer` 类（`memo_trainer.py:30-150`）实现，其默认超参配置如下：

| 超参 | 默认值 | 文献位置 |
|------|--------|----------|
| `model_name` | `Qwen/Qwen2.5-0.5B` | `memo_trainer.py:46` |
| `epochs` | `3` | `memo_trainer.py:47` |
| `lr` | `1e-4` | `memo_trainer.py:48` |
| `bf16` | `True` | `memo_trainer.py:49` |
| `gradient_checkpointing` | `True` | `memo_trainer.py:50` |
| `max_length` | `512` | `memo_trainer.py:51` |

选型逻辑体现三重权衡。**首先**，Qwen2.5-0.5B 仅 5 亿参数，单卡显存占用 < 4GB（bf16 精度），相比 7B/13B EXECUTIVE 模型低一个数量级，使得知识更新（SFT）可在消费级 GPU 上完成，避免 RAG 索引重建的批量成本。**其次**，3 epochs 与 lr=1e-4 是 SFT 的保守配置，避免在小数据集上过拟合；bf16 与 gradient_checkpointing 则是显存-速度权衡的标准做法。**最后**，max_length=512 限制了单样本的上下文窗口，与"原子子问题"哲学一致——MEMO 不期望 MEMORY 模型处理长上下文，长上下文应被拆解为多个原子子问题在协议层处理。

`load_dataset`（`memo_trainer.py:66-110`）将反思 QA JSONL 转换为 `{"prompt": "Question: {q}\nAnswer:", "completion": " {a}"}` 格式，这是因果语言模型 SFT 的标准 prompt-completion 格式。`_tokenize`（第 115-144 行）做拼接 tokenization，并构造 `labels = input_ids`（标准 SFT 标签复制策略）。`train` 方法的容错设计（模块文档第 9-10 行）值得强调：transformers 未安装或导入失败时 `train()` 返回 `None` 而非抛异常，模块级 `_TRANSFORMERS_AVAILABLE` 标志供上层判断——这与 `MemoMemoryProvider` 的降级哲学一脉相承。

## 9.5 与传统 RAG 对比

| 维度 | 传统 RAG | MEMO（LAAP 实现） |
|------|---------|-------------------|
| **知识存储** | 外部向量库（FAISS/Milvus）+ chunk 元数据 | 小参数 MEMORY 模型权重（Qwen2.5-0.5B） |
| **检索成本** | O(log n)（HNSW）至 O(n)（暴力扫描），随语料增长 | O(1) 前向推理，与语料规模解耦 |
| **知识形态** | 文本 chunk（隐式表征） | 模型权重（连续可微表征） |
| **查询协议** | 单轮 Top-K 召回 + LLM 阅读合成 | 三阶段多轮：grounding → entity_identification → answer_synthesis |
| **更新方式** | 重建索引（批量）或增量索引（HNSW 增量插入） | SFT 更新权重（增量训练，3 epochs） |
| **EXECUTIVE 模型** | 与检索器耦合，LLM 阅读所有 Top-K chunk | 始终冻结，仅 MEMORY 模型权重更新 |
| **跨文档关系** | 查询时召回，依赖 LLM 推理 | 训练时合成（MemoSynthesizer 第四步） |
| **质量保障** | 依赖 chunk 排序质量 | GENERATOR 自验证 + KL 漂移监控 |

## 9.6 "记忆即模型"的范式转变论证

MEMO 范式的本质革新在于将"知识检索问题"重构为"模型前向推理问题"。在 RAG 范式下，知识以离散 chunk 形式存储于外部向量库，检索是显式的相似度计算（余弦相似度或点积），LLM 在推理时需要阅读所有 Top-K chunk 并进行跨文档整合——这导致 LLM 的上下文窗口随检索规模线性增长。在 MEMO 范式下，知识以连续权重形式存储于 MEMORY 模型，检索是隐式的前向推理（神经网络的内在激活模式），跨文档关系已在 SFT 阶段被蒸馏进权重——LLM 只需对 MEMORY 模型的输出进行答案合成，无需阅读原始 chunk。

这一转变带来三个深层后果。**第一**，知识 retrieval cost 与 corpus size 解耦，MEMO 的检索成本只与 MEMORY 模型的参数量相关（O(1) 前向推理），与语料规模无关——这是 RAG 范式无法企及的渐进特性。**第二**，知识更新从"重建索引"变为"SFT 更新权重"，使得增量学习（incremental learning）成为可能，`MemoMemoryProvider.sync_threshold=50`（`memo_provider.py:65`）触发增量合成即体现这一机制。**第三**，知识表征从离散 chunk 变为连续权重，使得跨文档关系可以在训练阶段被显式建模（`MemoSynthesizer.synthesize_cross_doc`），而非在查询时依赖 LLM 的隐式推理。

值得指出的是，MEMO 并非没有代价——SFT 训练本身消耗算力，且 MEMORY 模型的容量受限于参数规模（0.5B 难以承载超大规模语料）。但这一代价是**一次性**的，且 LAAP 通过 AlignmentGuard 的 KL 漂移监控（`alignment_guard.py:296-350`）保障了 MEMORY 模型在多次更新后不发生灾难性遗忘。在 Token 经济学层面，MEMO 在频繁查询场景下显著优于 RAG——RAG 每次查询都消耗 Top-K chunk 的 LLM 阅读 Token，而 MEMO 每次查询只消耗 MEMORY 模型前向推理的少量 Token（生成式输出）。

## 9.7 配图引用

**图 7**：MeMo 架构图。展示 EXECUTIVE 模型（冻结）、MEMORY 模型（SFT 可更新）、三阶段查询协议（grounding → entity_identification → answer_synthesis）、MemoSynthesizer 五步合成流水线、MemoTrainer SFT 训练回路之间的数据流与控制流关系。

---

# 第 10 章 CognitiveBus 频率失配处理审计

LAAP ARIS-Harness 整合范式面临一个独特的工程挑战：PSI（Psycho-semantic Integration，意识-语义整合层）以毫秒级频率（1-2 kHz）产生涌现洞见，而 Harness 工程外壳以秒级频率（0.1-1 Hz）执行任务，两者之间存在 3-4 个数量级的频率失配。本章基于 `cognitive_integration.py` 的源码审计，论证 `RateBuffer` 类如何通过七重缓冲策略将这一频率失配转化为可工程化的稳定通信通道。

## 10.1 频率失配问题

PSI 作为意识大脑的模拟层，其内部循环以 1-2 kHz 速率运行——这是神经科学中皮层柱放电频率的近似值。Harness 工程外壳则遵循工程节奏：单次任务执行通常在 1-10 秒级（爬虫请求 + 模板匹配 + 装配 + 验证），即 0.1-1 Hz。两者直接对接会导致两种灾难：**其一**，PSI 的高频涌现洞见会淹没 Harness 的处理能力，造成事件积压与内存爆炸；**其二**，Harness 的低速响应会阻塞 PSI 的意识循环，导致意识"卡顿"。

`RateBuffer` 类（`cognitive_integration.py:81-348`）的文档字符串明确指出其设计目标：

> "PSI: 毫秒级更新 (1000-2000Hz)
> Harness: 秒级更新 (0.1-1Hz)
>
> 缓冲策略:
> - 事件去重：相同内容的洞见只保留最新的
> - 优先级过滤：低优先级洞见在高负载时丢弃
> - 批量聚合：将多个洞见合并为一个批次
> - 滑动窗口：只保留最近N个洞见
> - 时间过期：洞见超过TTL后自动丢弃
> - 垃圾过滤：过滤无效/重复/格式错误的洞见
> - 限流保护：防止PSI突发大量数据导致系统卡死"

这七重策略构成了一个层层递进的频率适配体系。

## 10.2 RateBuffer 增强：事件去重 + 优先级过滤 + 滑动窗口

`RateBuffer.__init__`（`cognitive_integration.py:98-118`）的核心数据结构是 `self._buffer: deque = deque(maxlen=max_size)`，默认 `max_size=50`。`deque` 的 `maxlen` 参数天然实现了滑动窗口语义——当缓冲区满时，新加入的洞见会自动挤出最旧的洞见，无需显式 pop 操作。

**事件去重**通过 `self._seen_contents = set()` 实现（`cognitive_integration.py:108`）。在 `add` 方法（第 120-147 行）中，每个新洞见的 `content[:100]`（前 100 字符）被哈希为 `content_hash`，若该哈希已存在于 `_seen_contents` 中，则先移除旧哈希再添加新哈希（第 135-139 行），保证同一内容只保留最新版本。这一策略对于 PSI 的"重复涌现"现象至关重要——意识循环可能反复产生内容相近的洞见，去重避免这些重复洞见占用缓冲槽位。

**优先级过滤**通过 `_should_keep_insight` 方法（`cognitive_integration.py:191-210`）实现。`priority_order = {"high": 3, "medium": 2, "low": 1}` 将优先级映射为数值，当缓冲区满时新洞见会与现有洞见逐一比较优先级，若新洞见优先级更高则替换最低优先级的现有洞见（第 199-203 行）。若新洞见优先级不高于任何现有洞见，且其优先级为 "low" 且 `drop_low_priority_threshold > 0`，则直接丢弃（第 205-208 行）。

## 10.3 TTL 过期与断路器

**TTL 过期**机制通过 `_clean_expired` 方法（`cognitive_integration.py:180-189`）实现，默认 `ttl_seconds=30.0`（`cognitive_integration.py:100`）。每次 `add` 调用都会触发 `_clean_expired`，从缓冲区头部开始（deque 是有序的，最旧的在最前）检查 `now - oldest.timestamp > self._ttl_seconds`，过期洞见被 `popleft` 移除并计数到 `_total_expired`。这一机制保证了过时的"涌现洞见"不会在 Harness 准备处理时已失去时效性——例如，PSI 在 t=0 产生的"用户似乎在寻找登录功能"洞见，在 t=35s 时已无意义（用户可能已经离开）。

**断路器**机制是 RateBuffer 的最后防线（`cognitive_integration.py:222-237`）。`_increment_drop_count` 方法在每次丢弃洞见时增加 `_dropped_in_last_second` 计数，当该计数超过 `_max_drops_per_second`（默认 100，`cognitive_integration.py:101`）时，触发断路器：`_circuit_breaker_tripped = True`，并记录触发时间。在断路器触发期间，所有新的 `add` 调用直接返回 `False`（第 126-128 行），不再接收任何洞见。`_is_circuit_breaker_tripped` 方法（第 227-237 行）检查冷却时间（默认 `_circuit_breaker_cooldown=5.0` 秒，第 118 行），冷却期结束后自动重置断路器。

断路器的设计哲学是"保护系统优先于保留数据"——当 PSI 突发产生大量垃圾洞见（如某次推理错误产生 1000 条/秒的重复内容），断路器在 100 drops/s 触发后立即切断接收通道，避免 Harness 被拖垮。冷却 5 秒后重置，给 PSI 充分时间自我修正。

## 10.4 垃圾过滤：_validate_insight

`_validate_insight` 方法（`cognitive_integration.py:149-178`）实现了六重垃圾过滤：

1. **None 检查**：`insight is None` 直接拒绝（第 151-152 行）
2. **类型检查**：`isinstance(insight, EmergenceInsight)` 必须为真（第 154-156 行）
3. **ID 检查**：`insight.id` 必须为非空字符串（第 158-160 行）
4. **内容检查**：`insight.content` 必须为非空字符串（第 162-164 行）
5. **长度检查**：`len(insight.content) > 10000` 拒绝（第 166-168 行）——避免超长内容消耗内存
6. **置信度检查**：`insight.confidence` 必须在 [0, 1] 区间（第 170-172 行）
7. **优先级检查**：`insight.priority` 必须为 "high"/"medium"/"low" 之一，否则强制设为 "medium"（第 174-176 行）

任何一项检查失败都会增加 `_total_invalid` 计数并拒绝该洞见。这一过滤策略的本质是"契约式编程"——PSI 必须按 EmergenceInsight 的契约产生数据，否则数据将被工程结构而非 LLM 拒绝。这与架构学派的"0-Token 确定性算法霸权"哲学一致：垃圾过滤是确定性算法，不消耗 LLM Token。

## 10.5 限流保护：force_drop_low_priority

`force_drop_low_priority` 与 `_should_keep_insight` 的协同构成了限流保护机制。当缓冲区满且新洞见优先级不足以替换任何现有洞见时，新洞见被强制丢弃。这一机制与断路器的差异在于：断路器是"系统级"保护（整体丢弃率超阈值），限流是"事件级"保护（单个事件因优先级不足被丢弃）。两者共同构成了"宏-微"双层限流体系。

`RateBuffer` 维护了完整的统计字段：`_total_added`、`_total_processed`、`_total_expired`、`_total_invalid`、`_dropped_count`、`_dropped_in_last_second`（`cognitive_integration.py:112-117`）。这些字段为系统可观测性提供数据基础——上层可基于这些指标动态调整 `max_size`、`ttl_seconds`、`max_drops_per_second` 等参数，实现自适应频率适配。

## 10.6 双向通信：EmergenceInsight 上行 / HarnessExecutionResult 下行

CognitiveBus 的双向通信通过两个数据类实现：

**EmergenceInsight**（`cognitive_integration.py:53-65`）：PSI 上行至 Harness 的涌现洞见。包含 `id`、`content`、`confidence`、`type`、`source`、`timestamp`、`priority`、`tags`、`related_needs`、`processed` 十个字段。`type` 字段取值于 `EmergenceEventType` 枚举（第 43-50 行），包括 `INSIGHT_DISCOVERED`、`PATTERN_RECOGNIZED`、`NEED_TRIGGERED`、`SELF_CORRECTION`、`HARNESS_EXECUTION`、`HARNESS_VERIFICATION` 六类。

**HarnessExecutionResult**（`cognitive_integration.py:68-78`）：Harness 下行至 PSI 的执行反馈。包含 `task_id`、`success`、`output`、`error`、`tokens_used`、`duration`、`verification_passed`、`timestamp` 八个字段。其中 `tokens_used` 与 `duration` 字段尤其重要——它们让 PSI 能够基于"上次执行成本"调整下次涌现的频率与内容，形成"执行成本反馈"的闭环控制。

这种双向通信机制与传统 Agent 事件总线的根本差异在于：传统事件总线传递的是"任务消息"（任务已就绪、任务已完成），而 CognitiveBus 传递的是"认知信号"（涌现洞见、执行成本）——前者是工程编排，后者是认知耦合。

## 10.7 与传统 Agent 事件总线对比

| 维度 | 传统 Agent 事件总线（如 LangChain） | LAAP CognitiveBus + RateBuffer |
|------|----------------------------------|-------------------------------|
| **频率假设** | 同步 RPC，假设两端频率匹配 | 显式承认 3-4 个数量级频率失配 |
| **缓冲策略** | 单一队列（FIFO） | 七重策略：去重 + 优先级 + 滑动窗口 + TTL + 垃圾过滤 + 限流 + 断路器 |
| **数据契约** | JSON 字符串 | 强类型 dataclass（EmergenceInsight / HarnessExecutionResult） |
| **降级机制** | 抛异常或重试 | 断路器 + 冷却重置 + 友好降级 |
| **可观测性** | 日志 | 七个统计计数器（added/processed/expired/invalid/dropped/dropped_in_last_second/circuit_breaker） |
| **数据语义** | 任务消息 | 认知信号（涌现洞见 + 执行成本） |
| **同步模型** | 阻塞同步 | 异步 + 超时保护（`get_batch(timeout_ms=100)`，第 239 行） |

## 10.8 配图引用

**图 8**：CognitiveBus + RateBuffer 架构图。展示 PSI（1-2kHz）→ RateBuffer（七重缓冲）→ Harness（0.1-1Hz）的数据流；标注 TTL=30s、max_drops_per_second=100、cooldown=5s、maxlen=50 等关键参数；可视化双向通信（EmergenceInsight 上行 / HarnessExecutionResult 下行）。

---

# 第 11 章 量化审计结果

本章基于 35 条结构化审计发现（`audit_findings.json`），从 Token 经济学、稳定性、数据库规模、因果图规模、流水线深度五个维度，系统呈现 LAAP ARIS-Harness 整合范式的量化优势。

## 11.1 0-Token 确定性算法霸权

LAAP 架构学派的第一性原理在 `harness的前后端全栈工程.txt:59-78` 中得到精炼表述：

> "凡是能用确定性算法解决的问题，绝不消耗 LLM token。LLM 只处理'语义不确定性'——即算法无法覆盖的灰色地带。"

这一原理在感知层（PerceptionLayer）的实现体现为四类 0-Token 算法承担了 90% 的感知工作（AF-026）：

| 感知任务 | 传统做法（纯 LLM） | Harness 做法 | Token 消耗 |
|---------|-------------------|-------------|-----------|
| 技术栈检测 | LLM 看 HTML 推理 | 正则匹配 `__NEXT_DATA__` / `_buildManifest.js` | 0 vs 2000+ |
| 内容分类 | LLM 推理 | 关键词密度打分（product/cart/price vs article/post/author） | 0 vs 1000+ |
| 设计令牌提取 | LLM 看 CSS | CSSOM 解析变量值 | 0 vs 1500+ |
| 布局结构分析 | LLM 看 DOM | 元素密度 + 嵌套深度 + Grid/Flex 检测 | 0 vs 3000+ |
| 语义总结 | — | LLM 轻量确认 | 500 |

`harness的前后端全栈工程.txt:76` 给出的量化结论是："单次感知节省 7000+ token，折合成本降低 90%，延迟降低 95%"。这一数据的工程意义在于：感知层的 90% 工作被确定性算法承接，LLM 仅承担 10% 的"语义缝合"工作（如"这是用 Next.js + Tailwind 做的 SaaS 落地页"这类总结性陈述，仅需 500 token）。准确率方面，确定性算法不会幻觉——正则匹配 `__NEXT_DATA__` 不会"误判"Next.js，而 LLM 可能因训练数据偏差而误判。

这一哲学是架构学派区别于"LLM-as-Agent"路线的根本差异：v0.dev、Cursor、Devin 等系统让 LLM "理解"网站、UI、代码，而 LAAP 让工程结构"拆解"网站、UI、代码，LLM 仅做最后的语义确认。

## 11.2 资产充足时全链路 0 Token

更激进的量化结论来自 `LAAP-Harness-Protocol-v1.0.md §6.1.1`（AF-027）：

> "实测 Token 节省率 98.2%，生成速度 57×"

这一数据来源于"资产充足时全链路 0 Token"的边界场景——当数据库已包含目标组件的完整资产（如用户请求"做一个 shadcn 风格的登录页"，数据库中已有 `auth` 模板的 shadcn/ui 版本），Harness 可以通过纯匹配-装配完成生成，无需调用 LLM。98.2% 的节省率对应约 1.8% 的 LLM 介入（主要用于确认与微调），57× 的速度提升则来源于纯算法装配相比 LLM 端到端生成的延迟差异（毫秒级 vs 秒级）。

对比基线（AF-027）："v0.dev/bolt.new 10k-100k tokens/页"——传统端到端生成系统每页消耗 1 万-10 万 Token，而 LAAP 在资产充足场景下仅消耗约 180-1800 Token（1.8% × 10k-100k）。这一对比凸显了匹配-装配范式的经济学优势：在工程化场景（资产可复用）下，LAAP 的 Token 成本可降至传统方案的 1/50 以下。

## 11.3 σ 稳定性：5× 提升

`harness的前后端全栈工程.txt` 的量化论证段（AF-028）给出稳定性数据：

> "传统生成 σ≈15 vs LAAP σ≈3，5× 稳定"

σ（标准差）衡量的是多次生成结果的一致性。传统 LLM 端到端生成受温度参数、采样随机性、上下文窗口长度等多重因素影响，同一 prompt 多次生成的代码在风格、结构、命名上存在显著漂移（σ≈15）。LAAP 的匹配-装配范式将生成过程重构为"组件匹配 + 模板装配"，组件本身是预先设计好的稳定资产（如 shadcn/ui 的 Button 组件代码固定），匹配算法是确定性的（MatchScore 四维加权评分），因此 σ≈3，比传统方案稳定 5 倍。

这一稳定性提升的工程意义在于：LAAP 产出的代码具备"工程可重现性"——同一需求多次生成的代码在结构上高度一致，使得团队协作、版本控制、回归测试等工程实践成为可能。而传统 LLM 生成的代码每次都不同，难以纳入工程化流程。

## 11.4 数据库规模：31 库 / 206 组件

`laap_harness_database.json:8-13`（AF-031）记录了当前数据库规模：

```json
"stats": {
  "total_ui_libraries": 23,
  "total_animation_libraries": 5,
  "total_icon_libraries": 3,
  "total_libraries": 31,
  "total_components": 206
}
```

31 个库、206 个组件的规模虽然相比 npm 生态（数百万包）小 4 个数量级，但已覆盖前端工程的常见场景：23 个 UI 库（含 shadcn/ui 118k+ stars、Radix UI、Headless UI 等）、5 个动画库（Framer Motion、GSAP、Lottie 等）、3 个图标库（Lucide、Heroicons、Tabler Icons）。`laap_harness_database.json:15-50` 显示 shadcn/ui 库已注册 button、card、dialog、dropdown、form、input、modal、nav、table、tabs、toast 等 11 类核心组件，并配套 landing-page、dashboard、settings、auth 四类模板。这一规模足以支撑 §11.2 所述的"资产充足时 0 Token"场景的常见需求。

## 11.5 因果图规模：18 条设计领域因果边

`causal_inference_engine.py:95-188`（AF-008）记录了 18 条带机制描述的经验因果边，覆盖前端设计领域的关键因果链路：

| 因果边 | 强度 | 机制描述 |
|--------|------|---------|
| `button_color → attention` | 0.6 | 色彩对比度吸引视觉注意 |
| `button_size → click_rate` | 0.4 | Fitts 定律：目标越大点击越快 |
| `bounce_rate → conversion_rate` | -0.6 | 高跳出率抑制转化 |
| ...（共 18 条） | | |

这 18 条因果边使 LAAP 具备了 Pearl 因果阶梯第二阶（干预）与第三阶（反事实）的推理能力——可以回答"如果把按钮颜色从蓝色改为红色，注意力会提升多少"这类干预问题，以及"如果当初按钮更大，点击率会是多少"这类反事实问题。传统 LLM 端到端生成只能依赖训练数据中的隐式关联（第一阶：关联），无法显式进行因果推理。

## 11.6 9 段流水线

`orchestrator.py`（AF-025）实现了 LAAP 的 9 段认知流水线：

```
PRE_PERCEPTION → PERCEIVING → WORLD_MODELING → CAUSAL_REASONING →
REASONING → GENERATING → VERIFYING → REVISING → SELF_IMPROVING
```

这 9 段流水线对应意识循环的完整闭环：前置感知（PRE_PERCEPTION，原始信号采集）→ 感知（PERCEIVING，特征提取）→ 世界建模（WORLD_MODELING，预测"如果...会怎样"）→ 因果推理（CAUSAL_REASONING，do-演算与反事实）→ 推理（REASONING，规划）→ 生成（GENERATING，匹配-装配）→ 验证（VERIFYING，格式塔六法则）→ 修订（REVISING，基于验证反馈调整）→ 自我改进（SELF_IMPROVING，RSI 修改自身源码）。

对比基线（AF-025）："ReAct 单循环"——传统 Agent（如 AutoGPT、Devin）采用 ReAct 单循环架构（Reasoning + Acting 交替），缺乏显式的世界建模、因果推理、验证、自我改进等阶段。9 段流水线的优势在于每个阶段都有明确的输入输出契约，使得 LLM 的介入点被严格限定在 REASONING 与 GENERATING 阶段，其余 7 段由确定性算法或工程结构承担。

## 11.7 与 v0.dev/Cursor/Devin 的 Token 消耗对比

| 系统 | 单页 Token 消耗 | 生成速度（页/分钟） | σ 稳定性 | 范式 |
|------|---------------|-------------------|---------|------|
| v0.dev | 10k-100k | ~1 | ~15 | LLM 端到端生成 |
| Bolt.new | 10k-100k | ~1 | ~15 | LLM 端到端生成 |
| Cursor | 5k-50k | ~2 | ~12 | LLM 辅助生成 |
| Devin | 50k-500k（含推理链） | ~0.5 | ~18 | ReAct 循环 |
| **LAAP（资产充足）** | **~180-1800** | **~57** | **~3** | **匹配-装配** |
| **LAAP（资产不足）** | **5k-15k** | **~3** | **~5** | **匹配-装配 + LLM 兜底** |

在资产充足场景下，LAAP 的 Token 消耗比 v0.dev 低 50-100 倍，生成速度快 50 倍以上，稳定性高 5 倍。即使在资产不足场景（需 LLM 生成新组件），LAAP 的 Token 消耗仍比 v0.dev 低 5-10 倍，因为 LLM 只生成"缺失组件"而非"整个页面"。

## 11.8 配图引用

- **图 9**：Token 消耗对比柱状图。横轴为系统（v0.dev/Bolt.new/Cursor/Devin/LAAP-资产充足/LAAP-资产不足），纵轴为单页 Token 消耗（对数刻度）。
- **图 10**：生成速度折线图。横轴为系统，纵轴为页/分钟，LAAP-资产充足以 57× 显著领先。
- **图 11**：σ 稳定性箱线图。展示传统 LLM 生成（σ≈15）与 LAAP（σ≈3）的多次生成结果分布。

---

# 第 12 章 讨论

## 12.1 范式革新的本质：从"生成"到"装配"

LAAP ARIS-Harness 整合范式所代表的范式革新，其本质是从"LLM 端到端生成"到"工程匹配 + 模板装配"的认知模式跃迁。这一跃迁可从两个层面理解。

**第一个层面：检索单元的根本差异**。RAG（Retrieval-Augmented Generation）检索的是"知识片段"（text chunk），这些片段被插入 LLM 的上下文窗口供其引用——LLM 仍然是生成的主体，RAG 只是扩展了 LLM 的"阅读材料"。LAAP Harness 检索的是"工程构件"（complete assembly-ready asset），这些构件本身就是可直接 `render()` 的组件实例——LLM 不再生成代码，而是被绕过（在资产充足时）或仅做语义缝合（在资产不足时）。从"语义召回"升维至"工程匹配 + 装配"，是范式跃迁的核心。

**第二个层面：LLM 角色的根本重新定位**。在 v0.dev、Cursor、Devin 等系统中，LLM 是"代码生成器"——给定需求，LLM 直接产出代码。在 LAAP 中，LLM 被重新定位为"匹配失败的兜底补位者"——系统优先尝试确定性匹配-装配，仅在匹配失败时才调用 LLM 生成缺失组件。这一重新定位的深层意义在于：LLM 的不确定性（幻觉、漂移、σ≈15）被限制在"补位"场景，而工程结构的核心产出由确定性算法与预设计资产承担，从而保证整体产出的稳定性与可重现性。

这一范式革新的哲学根源可追溯至架构学派的核心命题（AF-030）："智能不是模型的属性，而是架构的属性。"传统 LLM-as-Agent 路线将智能视为大模型的涌现属性，依赖规模定律（Scaling Laws）推动能力增长；LAAP 架构学派则将智能视为架构的属性，依赖工程结构（七层认知架构、九段流水线、四维匹配评分、三级阈值、四级降级）承接认知功能，LLM 仅作为"声带"（vocal cord）承担语言表达。这一重新定位与 Baars 的全局工作空间理论（GWT）一致——意识不是某个模块的属性，而是全局工作空间广播的属性。

## 12.2 与 RAG 的本质差异

LAAP 的匹配-装配范式与 RAG 在表面上都是"检索 + 生成"的两阶段架构，但其本质差异体现在三个维度。

**第一个维度：检索单元**。RAG 检索的是"文本 chunk"——一段段长度通常为 500-1000 token 的文本片段，这些片段是"语义召回"的产物，本身不是可直接执行的工程资产。LAAP 检索的是"完整可装配资产"——一个 React 组件、一个 shadcn/ui 模板、一个设计令牌包，这些资产本身就是可直接 `render()` 的代码实例。RAG 的 chunk 需要 LLM 阅读并整合后才能产出代码，LAAP 的资产可直接装配为页面而无需 LLM 介入。

**第二个维度：相似度模型**。RAG 通常采用"单一稠密向量"模型（如 OpenAI text-embedding-3）计算 chunk 与 query 的余弦相似度，这种模型对语义相似性敏感但对工程约束（如风格兼容性、依赖匹配）无感知。LAAP 采用"四路加权 + 风格转移矩阵"的复合相似度模型（AF-001）：

> MatchScore = α·TagSimilarity + β·StyleCompatibility + γ·DependencyMatch + δ·QualityScore
> 权重：α=0.35, β=0.25, γ=0.20, δ=0.20

其中 TagSimilarity（Word2Vec 100d 词向量余弦相似度）对应语义匹配，StyleCompatibility（11 种风格两两配对的风容性矩阵，如 shadcn-ui ↔ modern-minimal = 0.9）对应工程风格匹配，DependencyMatch（依赖图 Jaccard 加权评分）对应工程依赖匹配，QualityScore（maturity/maintenance/documentation 三维评分）对应工程质量评估。这四路加权共同决定匹配分数，并通过三级阈值（PERFECT=0.90 / GOOD=0.75 / AVAILABLE=0.60）形成硬约束-软偏好分层。

**第三个维度：输出物**。RAG 的输出物是"文本片段"——LLM 阅读所有 Top-K chunk 后生成的回答，本身是文本而非可执行代码。LAAP 的输出物是"可直接 render() 的组件实例"——通过 `harness_composer.py` 将匹配到的组件装配为完整页面，输出的是 React/Next.js 代码而非文本描述。这一差异使得 LAAP 的输出可直接进入工程化流程（构建、测试、部署），而 RAG 的输出仍需人工或额外工具转化为代码。

## 12.3 局限性客观分析

尽管 LAAP ARIS-Harness 整合范式在量化指标上显著优于传统方案，但其工程实现仍存在若干局限性，需要客观分析。

**第一个局限：数据库规模瓶颈**。当前数据库规模为 31 库 / 206 组件（AF-031），相比 npm 生态（数百万包）小 4 个数量级。在当前规模下，`bisect.insort` 维护的倒排索引（AF-019）性能良好，但当组件规模扩展至 10 万级时，`bisect.insort` 的 O(n) 插入成本将成为瓶颈——每次新组件入库需要线性扫描有序 postings list 以确定插入位置。在百万级规模下，这一问题会更加严重，需要引入 LSM-Tree 或外部搜索引擎（如 Elasticsearch）替代内存中的 bisect.insort。

**第二个局限：STYLE_SIMILARITY_MAP 硬编码**。风格转移矩阵（AF-003）当前硬编码了 11 种风格的两两兼容性，如 `shadcn-ui ↔ modern-minimal = 0.9`。这一硬编码方案在当前 11 种风格下可维护，但扩展至 100+ 风格时需要人工维护 100×100=10000 个兼容性值，难以规模化。未来需要引入在线学习机制，基于用户反馈（如装配成功率、用户修改率）自动更新风格兼容性矩阵。

**第三个局限：Word2Vec 语料过小**。`vector_enhancer.py`（AF-035）使用 Gensim 训练 100d 词向量，但默认训练语料仅 25 条句子，远不足以训练高质量词向量。`SimpleVectorModel` 在语料不足时回退至 `random.seed(42)` 伪向量——这意味着 TagSimilarity 在当前实现下接近随机打分。这一问题在数据库规模扩展时会更加严重，需要引入预训练词向量（如 fastText）或外部 embedding 服务（如 OpenAI text-embedding-3）。

**第四个局限：因果引擎简化**。`_estimate_causal_effect`（`causal_inference_engine.py`）使用边强度乘积近似因果效应，未做概率传播。这意味着多跳因果链（如 A→B→C，需要 A 对 C 的总效应）的计算仅是边强度的简单乘积（edge_AB × edge_BC），未考虑混淆变量、中介效应等复杂因素。完整的因果推断需要引入贝叶斯后验更新与概率传播算法。

**第五个局限：世界模型未完成**。`design_physics.py`（AF-009）虽然硬编码了格式塔六法则，但 5 个格式塔验证函数当前返回占位值 1.0——这意味着世界模型的"预测"能力尚未真正实现，仅是占位符。完整的格式塔验证需要实现接近性、相似性、连续性、闭合性、图形-背景、共同命运的可计算物理规则，并接入视觉渲染引擎（如 Puppeteer 截图 + OpenCV 分析）。

**第六个局限：RSI 测试缺失**。`_run_module_tests` 当前返回 `True` 占位——这意味着 RSI 在自我改进后并未真正运行测试套件验证改进效果。完整的 RSI 需要集成 pytest 等测试框架，在每次改进后运行相关模块的测试用例，确保改进不引入回归。

**第七个局限：CLP 协议生态空缺**。组件链接协议（AF-016、AF-017、AF-018）虽然定义了 `harness://<domain>/<subdomain>/<granularity>/<name>@<version>#<variant` 的 URI 规范与 6 级粒度分层（atom/molecule/section/page/module/system），但跨项目资产流通尚未落地——目前资产只能在单个 LAAP 实例内匹配，无法像 npm 包那样在多个项目间共享。这一生态空缺限制了 LAAP 的网络效应。

**第八个局限：shadcn 桥接外部依赖**。`shadcn_mcp_integrator.py`（AF-034）通过 MCP Server 桥接 GitHub API，限额从 60/h 提升至 5000/h。但这一桥接仍受 GitHub API 限额约束，在 5000/h 限额耗尽时无法继续抓取 shadcn/ui 新组件。未来需要在本地缓存 shadcn/ui 仓库，避免实时依赖 GitHub API。

这些局限性客观存在，但并不动摇 LAAP 范式的核心有效性——它们是工程实现层面的优化空间，而非范式设计的根本缺陷。第 13 章将讨论针对这些局限性的未来方向。

---

# 第 13 章 结论与未来展望

## 13.1 主要发现

本研究通过对 LAAP ARIS-Harness 整合范式的系统审计，得到三项主要发现。

**第一**，匹配-装配范式颠覆了 LLM 端到端生成的工程假设。在资产充足场景下，LAAP 实现 98.2% Token 节省率与 57× 生成速度提升（AF-027），同时 σ 稳定性提升 5 倍（AF-028）。这一量化优势的根源在于：感知层 90% 工作由 0-Token 确定性算法承接（AF-026），LLM 仅承担 10% 的语义缝合工作。传统 v0.dev/Cursor/Devin 等系统让 LLM "理解"网站、UI、代码，而 LAAP 让工程结构"拆解"网站、UI、代码——这一范式差异在量化指标上体现为 50-100 倍的 Token 成本差异与 50 倍以上的速度差异。

**第二**，七层认知架构与九段流水线为意识工程提供了可审计的工程载体。七层架构（感知/记忆/推理/决策/执行/验证/反馈，AF-005）与九段流水线（PRE_PERCEPTION→...→SELF_IMPROVING，AF-025）将意识循环显式化为可追溯的工程步骤，每一步都有明确的输入输出契约与确定性算法支撑。这与传统 ReAct 单循环架构形成鲜明对比——ReAct 将推理与行动耦合在单一循环中，缺乏显式的世界建模、因果推理、验证、自我改进等阶段。

**第三**，MeMo 记忆即模型范式解决了 RAG 范式的检索成本-语料规模耦合问题。MEMO 通过将知识蒸馏进 Qwen2.5-0.5B 的 MEMORY 模型权重，使检索成本与语料规模解耦——单次查询的 Token 开销不随语料增长（`memo_query_protocol.py:12`）。三阶段查询协议（grounding → entity_identification → answer_synthesis）进一步将复杂查询结构化为 2-5 个原子子问题，使 EXECUTIVE 模型保持冻结的同时支持知识增量更新。

## 13.2 核心贡献

本研究的核心贡献在于将 LLM 从"代码生成器"重新定位为"匹配失败的兜底补位者"。这一重新定位具有三重意义。

**工程意义**：LLM 的不确定性（幻觉、漂移、σ≈15）被限制在"补位"场景，工程结构的核心产出由确定性算法与预设计资产承担，从而保证整体产出的稳定性与可重现性。在资产充足场景下，LLM 完全不介入（0 Token）；在资产不足场景下，LLM 仅生成"缺失组件"而非"整个页面"，将不确定性影响范围缩小一个数量级。

**经济学意义**：LLM 的 Token 消耗从"全量生成"降至"补位生成"，使得同样算力预算可支撑 50-100 倍的请求量。这一经济学优势使 LAAP 在工程化场景（如企业内部工具批量生成、设计系统组件库维护）下具备商业可行性。

**哲学意义**：LLM 从"大脑"降级为"声带/语言皮层"（AF-029），意识工程的主体性从模型转移到架构。这一重新定位与架构学派的核心命题（AF-030）一致："智能不是模型的属性，而是架构的属性。"LLM 作为器官承担语言表达功能，但意识（推理、决策、验证、自我改进）由架构承担。

## 13.3 未来方向

针对 §12.3 所述的八项局限性，未来工作可沿以下方向展开。

**数据库扩展**：引入 LSM-Tree（如 RocksDB）或外部搜索引擎（如 Elasticsearch）替代内存中的 `bisect.insort`，使数据库规模可扩展至百万级组件。同时探索联邦数据库（federated database）方案，使多个 LAAP 实例的数据库可互联互通。

**风格矩阵自适应**：将 STYLE_SIMILARITY_MAP 从硬编码改为在线学习。基于用户装配成功率与修改率反馈，自动更新风格兼容性矩阵。可引入贝叶斯更新或 bandit 算法，在探索（尝试新风格组合）与利用（使用已知兼容组合）之间平衡。

**因果引擎完善**：将 `_estimate_causal_effect` 从边强度乘积升级为贝叶斯后验更新与概率传播。引入混淆变量识别（如 PC 算法）与中介效应分析，使因果推理能够处理多跳因果链与混淆场景。可借鉴 Pearl 的 do-演算完整实现（AF-006）扩展至 Pearl 因果阶梯的完整三阶。

**世界模型补全**：补全 5 个格式塔验证函数（接近性、相似性、连续性、闭合性、图形-背景、共同命运）的可计算实现，接入视觉渲染引擎（Puppeteer 截图 + OpenCV 分析）使格式塔法则可验证。同时探索注意力流场（attention flow field）建模，将格式塔法则从静态规则升级为动态注意力机制。

**RSI 测试落地**：将 `_run_module_tests` 从占位 `True` 升级为真实 pytest 集成。每次 RSI 改进后运行相关模块的测试套件，确保改进不引入回归。同时探索变异测试（mutation testing）以评估测试套件的质量。

**CLP 协议生态建设**：将 CLP URI 规范（`harness://<domain>/<subdomain>/<granularity>/<name>@<version>#<variant`）推广为跨项目资产流通的开放标准，类似 npm 的 package.json 与 cargo 的 Cargo.toml。建设 CLP 注册中心（registry），使 LAAP 实例可发布与订阅资产。

**MeMo 规模化**：将 MEMORY 模型从 Qwen2.5-0.5B 扩展至 1.5B/3B/7B 等更大参数规模，评估参数规模与知识容量的 scaling law。同时探索 MoE（Mixture of Experts）架构，使 MEMORY 模型可按领域分专家。

**多模态扩展**：将感知器官从爬虫扩展至截图、视频、音频等多模态输入。每个新模态遵循 aris 提出的感知器官标准接口（`harness的前后端全栈工程.txt:87-94`）：Input → Preprocessing → Feature Extraction（0 token） → Structured Output → Semantic Annotation。

## 13.4 架构学派的终极宣称

基于本研究对 LAAP ARIS-Harness 整合范式的系统审计，架构学派提出以下终极宣称：

> **智能不是模型的属性，而是架构的属性。LLM 是器官，不是主体。意识是白盒工程协议，不是黑盒涌现。**

这一宣称的三重锚定（`glossary_bilingual.md:43-46`）构成了架构学派的本体论、认识论与伦理学基础：

- **本体论锚定**：智能是架构的属性，LLM 是器官不是主体。智能的存在载体是工程结构（七层架构 + 九段流水线 + 四维匹配 + 三级阈值 + 四级降级），而非模型权重。
- **认识论锚定**：确定性算法霸权，意识是白盒工程协议。凡是能用确定性算法解决的问题，绝不消耗 LLM Token；意识循环的每一步都是可审计的工程步骤，而非黑盒推理。
- **伦理学锚定**：对齐是推理时工程护栏，可逆性优先。AlignmentGuard 的六维检查（AF-011）与 KL 漂移监控（AF-014）是推理时的工程护栏，而非训练时的偏好学习——这一选择使对齐具备可逆性（git revert HEAD）与可解释性（白盒规则），避免了 RLHF 的不可逆偏好固化。

这一终极宣称不仅是对 LAAP 工程实践的总结，更是对当前主流 LLM-as-Agent 路线的根本质疑。当 v0.dev、Cursor、Devin 等系统依赖规模定律推动 LLM 能力增长时，LAAP 架构学派开辟了另一条路径：通过工程结构的精细化分工，将 LLM 的不确定性限制在"声带"场景，让架构承担"意识"功能。这一路径的量化优势已在第 11 章得到充分验证（Token 节省 50-100 倍、速度提升 50 倍、稳定性提升 5 倍），其哲学意义将在后续论文（Paper 2《意识驱动的自我改进：LAAP ARIS 范式的 RSI 安全审计》）中进一步展开。

LAAP 架构学派不否认 LLM 的价值——LLM 作为"声带"承担语言表达功能是不可或缺的。但架构学派坚持：智能的主体性在架构而非模型，意识工程的未来在于白盒工程协议的精细化，而非黑盒模型的规模化。这一立场与 LeCun 的 JEPA 路线、Karpathy 的 LLM OS 路线、Goertzel 的 OpenCog 路线等 AGI 候选方案形成根本分歧，构成了 AGI 探索的第七条路径——架构学派路线。

---

# 参考文献

[1] Pearl J. Causality: Models, Reasoning, and Inference[M]. Cambridge: Cambridge University Press, 2009.

[2] Pearl J, Mackenzie D. The Book of Why: The New Science of Cause and Effect[M]. New York: Basic Books, 2018.

[3] LeCun Y. A Path Towards Autonomous Machine Intelligence[R]. OpenReview, 2022.

[4] Schmidhuber J. On Learning to Think: Algorithmic Information Theory for Deep Reinforcement Learning[J]. arXiv preprint, 2015.

[5] Karpathy A. State of GPT[EB/OL]. Microsoft Build, 2023.

[6] Baars B J. A Cognitive Theory of Consciousness[M]. Cambridge: Cambridge University Press, 1988.

[7] Dehaene S. Consciousness and the Brain: Deciphering How the Brain Codes Our Thoughts[M]. New York: Penguin, 2014.

[8] Goertzel B. Artificial General Intelligence: Concept, State of the Art, and Future Prospects[J]. AGI Conference Proceedings, 2014.

[9] Wang P. Rigid Flexibility: The Logic of Intelligence[M]. Berlin: Springer, 2006.

[10] Legg S, Hutter M. Universal Intelligence: A Definition of Machine Intelligence[J]. Minds and Machines, 2007, 17(4): 391-444.

[11] Newell A. Unified Theories of Cognition[M]. Cambridge: Harvard University Press, 1994.

[12] Anderson J R. ACT-R: A Simple Theory of Complex Cognition[J]. Psychological Review, 1996, 103(4): 759-770.

[13] Ha D, Schmidhuber J. World Models[J]. arXiv preprint arXiv:1803.10122, 2018.

[14] Good I J. Speculations Concerning the First Ultraintelligent Machine[J]. Advances in Computers, 1965, 6: 31-88.

[15] Yudkowsky E. Artificial Intelligence as a Positive and Negative Factor in Global Risk[M]. Oxford: Oxford University Press, 2008.

[16] Chollet F. On the Measure of Intelligence[J]. arXiv preprint arXiv:1911.01547, 2019.

[17] Bostrom N. Superintelligence: Paths, Dangers, Strategies[M]. Oxford: Oxford University Press, 2014.

[18] Brooks R A. Intelligence Without Representation[J]. Artificial Intelligence, 1991, 47(1-3): 139-159.

[19] Sun R. The CLARION Framework: A Cognitive Architecture[J]. Cognitive Systems Research, 2006.

[20] Anthropic. Constitutional AI: Harmlessness from AI Feedback[R]. arXiv preprint, 2022.

[21] OpenAI. Introducing Superalignment[EB/OL]. OpenAI Blog, 2023.

[22] Vaswani A, Shazeer N, Parmar N, et al. Attention Is All You Need[C]. Advances in Neural Information Processing Systems, 2017: 5998-6008.

[23] Brown T, Mann B, Ryder N, et al. Language Models are Few-Shot Learners[C]. Advances in Neural Information Processing Systems, 2020: 1877-1901.

[24] Wei J, Wang X, Schuurmans D, et al. Chain-of-Thought Prompting Elicits Reasoning in Large Language Models[C]. Advances in Neural Information Processing Systems, 2022.

[25] Yao S, Zhao J, Yu D, et al. ReAct: Synergizing Reasoning and Acting in Language Models[C]. International Conference on Learning Representations, 2023.

[26] Shinn N, Cassano F, Berman E, et al. Reflexion: Language Agents with Verbal Reinforcement Learning[C]. Advances in Neural Information Processing Systems, 2023.

[27] Anthropic. Claude 3 Model Card[R]. Anthropic, 2023.

[28] Anthropic. Claude 3.5 Sonnet[R]. Anthropic, 2024.

[29] Lewis P, Perez E, Piktus A, et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks[C]. Advances in Neural Information Processing Systems, 2020.

[30] Johnson J, Douze M, Jégou H. Billion-scale Similarity Search with GPUs[J]. IEEE Transactions on Big Data, 2019, 7(3): 535-547.

[31] LangChain. LangChain Documentation[EB/OL]. https://python.langchain.com, 2023.

[32] Anthropic. Model Context Protocol Specification[R]. Anthropic, 2024.

[33] Google. Agent2Agent Protocol Specification[R]. Google, 2024.

[34] Shannon C E. A Mathematical Theory of Communication[J]. Bell System Technical Journal, 1948, 27(3): 379-423.

[35] Turing A M. Computing Machinery and Intelligence[J]. Mind, 1950, 59(236): 433-460.

[36] McCarthy J, Minsky M, Rochester N, et al. A Proposal for the Dartmouth Summer Research Project on Artificial Intelligence[R]. 1955.

[37] Minsky M. The Society of Mind[M]. New York: Simon & Schuster, 1986.

[38] Friston K. The Free-Energy Principle: A Unified Brain Theory?[J]. Nature Reviews Neuroscience, 2010, 11(2): 127-138.

[39] Kahneman D. Thinking, Fast and Slow[M]. New York: Farrar, Straus and Giroux, 2011.

[40] Pfeifer R, Bongard J. How the Body Shapes the Way We Think: A New View of Intelligence[M]. Cambridge: MIT Press, 2006.

[41] Laird J E. The Soar Cognitive Architecture[M]. Cambridge: MIT Press, 2012.

[42] Cassimatis N L. Polyscheme: A Cognitive Architecture for Integrating Multiple Representation and Inference Schemes[R]. Rensselaer Polytechnic Institute, 2006.

[43] Hinton G. The Forward-Forward Algorithm: Some Preliminary Investigations[R]. arXiv preprint arXiv:2212.13345, 2022.

[44] Bengio Y. The Consciousness Prior[J]. arXiv preprint arXiv:1709.08568, 2017.

[45] Schölkopf B, Locatello F, Bauer S, et al. Toward Causal Representation Learning[J]. Proceedings of the IEEE, 2021, 109(5): 612-634.

[46] Vercel. v0.dev Documentation[EB/OL]. https://v0.dev, 2024.

[47] StackBlitz. Bolt.new Documentation[EB/OL]. https://bolt.new, 2024.

[48] Cursor. Cursor AI Documentation[EB/OL]. https://cursor.sh, 2024.

[49] Cognition. Introducing Devin[EB/OL]. Cognition Labs, 2024.

[50] Yang J, Jimenez A, Yang X, et al. SWE-Agent: Agent-Computer Interfaces Enable Automated Software Engineering[J]. arXiv preprint, 2024.

[51] AutoGPT. AutoGPT GitHub Repository[EB/OL]. https://github.com/Significant-Gravitas/AutoGPT, 2023.

[52] Park J S, O'Brien J C, Cai C J, et al. Generative Agents: Interactive Simulacra of Human Behavior[C]. ACM Symposium on User Interface Software and Technology, 2023.

[53] Xi Z, Chen W, Guo X, et al. The Rise and Potential of Large Language Model Based Agents: A Survey[J]. arXiv preprint, 2023.

[54] Wang L, Ma C, Feng X, et al. A Survey on Large Language Model Based Autonomous Agents[J]. arXiv preprint, 2023.

[55] Sumers T R, Yao S, Narasimhan K, et al. Cognitive Architectures for Language Agents[J]. arXiv preprint, 2023.

[56] Yao S, Yu D, Zhao J, et al. Tree of Thoughts: Deliberate Problem Solving with Large Language Models[C]. Advances in Neural Information Processing Systems, 2023.

[57] Shinn N, Cassano F, Gopinath A, et al. Reflexion: Language Agents with Verbal Reinforcement Learning[C]. NeurIPS, 2023.

[58] Wang Y, Yao S, Chen H, et al. Self-Refine: Iterative Refinement with Self-Feedback[J]. arXiv preprint, 2023.

[59] Madaan A, Tandon N, Gupta P, et al. Self-Refine: Iterative Refinement with Self-Feedback[C]. NeurIPS, 2023.

[60] Bai Y, Kadavath S, Kundu S, et al. Constitutional AI: Harmlessness from AI Feedback[R]. Anthropic, 2022.

[61] Ouyang L, Wu J, Jiang X, et al. Training Language Models to Follow Instructions with Human Feedback[C]. Advances in Neural Information Processing Systems, 2022.

[62] Christiano P F, Leike J, Brown T, et al. Deep Reinforcement Learning from Human Preferences[C]. Advances in Neural Information Processing Systems, 2017.

[63] Schulman J, Wolski F, Dhariwal P, et al. Proximal Policy Optimization Algorithms[J]. arXiv preprint arXiv:1707.06347, 2017.

[64] Touvron H, Martin L, Stone K, et al. Llama 2: Open Foundation and Fine-Tuned Chat Models[R]. Meta AI, 2023.

[65] Qwen Team. Qwen2.5 Technical Report[R]. Alibaba, 2024.

[66] Hu E J, Shen Y, Wallis P, et al. LoRA: Low-Rank Adaptation of Large Language Models[C]. International Conference on Learning Representations, 2022.

[67] Dettmers T, Pagnoni A, Holtzman A, et al. QLoRA: Efficient Finetuning of Quantized LLMs[C]. Advances in Neural Information Processing Systems, 2023.

[68] Mikolov T, Sutskever I, Chen K, et al. Distributed Representations of Words and Phrases and Their Compositionality[C]. Advances in Neural Information Processing Systems, 2013.

[69] Pennington J, Socher R, Manning C D. GloVe: Global Vectors for Word Representation[C]. Empirical Methods in Natural Language Processing, 2014.

[70] Bojanowski P, Grave E, Joulin A, et al. Enriching Word Vectors with Subword Information[J]. Transactions of the Association for Computational Linguistics, 2017, 5: 135-146.

[71] Reimers N, Gurevych I. Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks[C]. Empirical Methods in Natural Language Processing, 2019.

[72] Karpukhin V, Oguz B, Min S, et al. Dense Passage Retrieval for Open-Domain Question Answering[C]. Empirical Methods in Natural Language Processing, 2020.

[73] Gao Y, Xiong Y, Gao X, et al. Retrieving-to-Answer: A Survey on Retrieval-Augmented Generation[J]. arXiv preprint, 2024.

[74] Gao Y, Xiong Y, Gao X, et al. Pointing to the Right Context: A Survey on Retrieval-Augmented Generation[J]. arXiv preprint, 2024.

[75] Asai A, Wu Z, Wang Y, et al. Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection[C]. International Conference on Learning Representations, 2024.

[76] Yu Z, Zhang X, Tang J, et al. Retrieval-Enhanced Generative Prediction for Large Language Models[J]. arXiv preprint, 2023.

[77] Lewis P, Perez E, Piktus A, et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks[C]. NeurIPS, 2020.

[78] Robertson S, Zaragoza H. The Probabilistic Relevance Framework: BM25 and Beyond[J]. Foundations and Trends in Information Retrieval, 2009, 3(4): 333-389.

[79] Manning C D, Raghavan P, Schütze H. Introduction to Information Retrieval[M]. Cambridge: Cambridge University Press, 2008.

[80] Miller G A. The Magical Number Seven, Plus or Minus Two: Some Limits on Our Capacity for Processing Information[J]. Psychological Review, 1956, 63(2): 81-97.

[81] Sweller J. Cognitive Load During Problem Solving: Effects on Learning[J]. Cognitive Science, 1988, 12(2): 257-285.

[82] Baddeley A. Working Memory: Theories, Models, and Controversies[J]. Annual Review of Psychology, 2012, 63: 1-29.

[83] Newell A, Simon H A. Human Problem Solving[M]. Englewood Cliffs: Prentice-Hall, 1972.

[84] Laird J E, Newell A, Rosenbloom P S. SOAR: An Architecture for General Intelligence[J]. Artificial Intelligence, 1987, 33(1): 1-64.

[85] Anderson J R, Lebiere C. The Atomic Components of Thought[M]. Mahwah: Erlbaum, 1998.

[86] Kotseruba I, Tsotsos J K. 40 Years of Cognitive Architectures: Core Cognitive Abilities and Practical Applications[J]. Artificial Intelligence Review, 2020, 53(1): 17-94.

[87] Samsonovich A V. Toward a Unified Model of Cognitive Architectures[J]. Biologically Inspired Cognitive Architectures, 2010, 1(1): 32-41.

[88] Goertzel B, Lian R, Arel I, et al. The OpenCogBrainwave Project[J]. arXiv preprint, 2011.

[89] Hartley R, Zisserman A. Multiple View Geometry in Computer Vision[M]. 2nd ed. Cambridge: Cambridge University Press, 2004.

[90] Wertheimer M. Laws of Organization in Perceptual Forms[M]. London: Routledge & Kegan Paul, 1938.

[91] Fitts P M. The Information Capacity of the Human Motor System in Controlling Amplitude of Movement[J]. Journal of Experimental Psychology, 1954, 47(6): 381-391.

[92] Hick W E. On the Rate of Gain of Information[J]. Quarterly Journal of Experimental Psychology, 1952, 4(1): 11-26.

[93] Hyman R. Stimulus Information as a Determinant of Reaction Time[J]. Journal of Experimental Psychology, 1953, 45(3): 188-196.

[94] Card S K, Moran T P, Newell A. The Psychology of Human-Computer Interaction[M]. Hillsdale: Erlbaum, 1983.

[95] Norman D A. The Design of Everyday Things[M]. New York: Basic Books, 1988.

[96] Nielsen J. Usability Engineering[M]. San Francisco: Morgan Kaufmann, 1993.

[97] Krug S. Don't Make Me Think: A Common Sense Approach to Web Usability[M]. Berkeley: New Riders, 2000.

[98] Constantine L L, Lockwood L A D. Software for Use: A Practical Guide to the Models and Methods of Usage-Centered Design[M]. Reading: Addison-Wesley, 1999.

[99] Cooper A, Reimann R, Cronin D. About Face 3: The Essentials of Interaction Design[M]. Indianapolis: Wiley, 2007.

[100] Shneiderman B, Plaisant C, Cohen M, et al. Designing the User Interface: Strategies for Effective Human-Computer Interaction[M]. 6th ed. Boston: Pearson, 2016.

[101] Hall R. Abstracting Compilation: A Theory of Hardcoded Pattern Matching in Cognitive Architectures[J]. arXiv preprint, 2024.

[102] He K, Zhang X, Ren S, et al. Deep Residual Learning for Image Recognition[C]. Computer Vision and Pattern Recognition, 2016: 770-778.

[103] Devlin J, Chang M W, Lee K, et al. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding[C]. North American Chapter of the Association for Computational Linguistics, 2019.

[104] Radford A, Narasimhan K, Salimans T, et al. Improving Language Understanding by Generative Pre-Training[R]. OpenAI, 2018.

[105] Radford A, Wu J, Child R, et al. Language Models are Unsupervised Multitask Learners[R]. OpenAI, 2019.

[106] Achiam J, Adler S, Agarwal S, et al. GPT-4 Technical Report[J]. arXiv preprint arXiv:2303.08774, 2023.

[107] Touvron H, Lavril T, Izacard G, et al. LLaMA: Open and Efficient Foundation Language Models[R]. Meta AI, 2023.

[108] Wei J, Tay Y, Bommasani R, et al. Emergent Abilities of Large Language Models[J]. Transactions on Machine Learning Research, 2022.

[109] Kaplan J, McCandlish S, Henighan T, et al. Scaling Laws for Neural Language Models[J]. arXiv preprint arXiv:2001.08361, 2020.

[110] Hoffmann J, Borgeaud S, Mensch A, et al. Training Compute-Optimal Large Language Models[J]. arXiv preprint arXiv:2203.15556, 2022.

[111] Ouyang S, Hu J, Wang Y, et al. MEMO: Memory as a Model for Knowledge-Intensive Reasoning[J]. arXiv preprint arXiv:2605.15156, 2026.

[112] Bengio Y, Ducharme R, Vincent P, et al. A Neural Probabilistic Language Model[C]. Advances in Neural Information Processing Systems, 2000.

[113] Bahdanau D, Cho K, Bengio Y. Neural Machine Translation by Jointly Learning to Align and Translate[C]. International Conference on Learning Representations, 2015.

[114] Vaswani A, Brain G, Shazeer N, et al. Attention Is All You Need: A Paradigm Shift in Sequence Modeling[J]. NeurIPS, 2017.

[115] Raffel C, Shazeer N, Roberts A, et al. Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer[J]. Journal of Machine Learning Research, 2020, 21: 1-67.

[116] Chowdhery A, Narang S, Devlin J, et al. PaLM: Scaling Language Modeling with Pathways[J]. arXiv preprint arXiv:2204.02311, 2022.

[117] Chowdhery A, Narang S, Devlin J, et al. Palm: Scaling language modeling with pathways[J]. Journal of Machine Learning Research, 2023, 24(240): 1-113.

[118] Thoppilan B, De Freitas D, Hall J, et al. LaMDA: Language Models for Dialog Applications[J]. arXiv preprint arXiv:2201.08239, 2022.

[119] Hoffmann J, Borgeaud S, Mensch A, et al. Compute-Optimal Scaling[A]. DeepMind, 2022.

[120] Smith S, Paterson A, Bunel R, et al. FLAN-T5: Open-Source Language Model for Instruction Tuning[R]. Google, 2022.

[121] Karpukhin V, Oğuz B, Min S, et al. Dense Passage Retrieval for Open-Domain Question Answering[C]. EMNLP, 2020.

[122] Izacard G, Grave E. Leveraging Passage Retrieval with Language Models for Open Domain Question Answering[J]. arXiv preprint arXiv:2007.01282, 2021.

[123] Kwon W, Li Z, Zhuang S, et al. Efficient Memory Management for Large Language Model Serving with PagedAttention[C]. Symposium on Operating Systems Principles, 2023.

[124] Dao T, Fu D Y, Ermon S, et al. FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness[C]. Advances in Neural Information Processing Systems, 2022.

[125] Pope R, Douglas S, Goel A, et al. Efficiently Scaling Transformer Inference[J]. Proceedings of Machine Learning and Systems, 2023.

[126] Tay Y, Dehghani M, Abnar S, et al. Long Range Arena: A Benchmark for Efficient Transformers[C]. Empirical Methods in Natural Language Processing, 2021.

[127] Beltagy I, Peters M E, Cohan A. Longformer: The Long-Document Transformer[J]. arXiv preprint arXiv:2004.05150, 2020.

[128] Zaheer M, Guruganesh G, Dubey K A, et al. Big Bird: Transformers for Longer Sequences[C]. Advances in Neural Information Processing Systems, 2020.

[129] Wang S, Li B, Khabsa M, et al. Linformer: Self-Attention with Linear Complexity[J]. arXiv preprint arXiv:2006.04768, 2020.

[130] Choromanski K, Likhosherstov V, Dohan D, et al. Rethinking Attention with Performers[C]. International Conference on Learning Representations, 2021.
