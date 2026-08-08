# 第 5 章 范式核心算法审计（续）

## 5.1 倒排索引 O(log n) 查询优化

匹配-装配范式在工程性能上的第一根支柱，来自一套与"端到端生成"完全异构的检索底座。在 `inverted_index.py` 第 60-71 行的 `WAL.append`、第 110-180 行的 `MemTable` 以及第 183-234 行的 `SSTable` 三个原语中，LAAP Harness 实现了一条完整的 LSM-Tree（Log-Structured Merge-Tree）写入路径，从而把"按标签检索组件"这一高频操作的查询复杂度稳定在 O(log n) 水平。这与 v0.dev、bolt.new 等基于向量数据库 HNSW 索引的方案形成了根本性差异：HNSW 在召回率 0.95 时查询复杂度约为 O(log n × b)（其中 b 为出度，典型值 16-64），其常系数远大于倒排索引的二分查找；而 LAAP 选择放弃隐式语义空间，将"语义"显式外化到 CLP 标签体系（详见第 7 章），换回了纯 Python 计算的零 Token 查询路径。

具体地，倒排索引的数据结构遵循"term → [doc_ids]"的经典模型，但在 postings list 的维护上采用 `bisect.insort` 维护有序性（`inverted_index.py` 第 130-137 行 `MemTable.add`），使得后续布尔查询可以走双指针归并路径。`MemTable.MAX_SIZE = 1000` 的容量阈值（第 118 行）使内存缓冲区在达到 1000 个 (field, term, doc_id) 元组后强制 flush 到 SSTable，这一阈值选择在内存占用与磁盘 I/O 之间取得平衡——过小会导致 SSTable 数量膨胀、合并压力增大，过大则会增加崩溃时的重放成本。`SSTable` 类（`inverted_index.py` 第 183-234 行）则把内存表持久化为按键排序的 JSON 段文件，键格式为 `field||term`，值为有序 doc_id 列表，并在 `get()`/`has_term()`/`prefix_search()` 三个查询入口统一调用 `bisect.bisect_left` 二分定位。

`prefix_search`（`inverted_index.py` 第 220-234 行）特别值得注意：它先二分定位前缀起点，再顺序扫描直到键不再匹配前缀，最坏复杂度仍为 O(log n + k)（k 为命中项数），而非朴素线性扫描的 O(n)。这一前缀搜索能力对 LAAP 的"按领域前缀检索组件"至关重要——例如查询 `harness://frontend/ui/atom/*` 可以一次取回所有 frontend 域下的原子组件，无需逐个查询。

WAL（Write-Ahead Log，`inverted_index.py` 第 38-107 行）则是 LSM-Tree 写入路径的持久性保证。`append` 方法（第 54-60 行）以单行 JSON 写入并可选 `fsync` 刷盘，`recover` 方法（第 71-92 行）在崩溃后重放全部记录，对损坏的末尾行（崩溃中途写入）通过 `try/except` 跳过。这一设计使倒排索引在进程崩溃后可恢复到崩溃前最后一次 fsync 的状态，避免数据丢失。`truncate`（第 94-101 行）则在 checkpoint 成功后清空 WAL，防止日志无限增长。

布尔查询在 `inverted_index.py` 第 413-457 行被实现为三个 `_merge_and`/`_merge_or`/`_merge_not` 双指针归并函数：

- `_merge_and`（第 413-425 行）取两个有序列表的交集，对撞双指针在任一指针到达末尾时停止，复杂度严格 O(m+n)；
- `_merge_or`（第 427-443 行）取并集，主循环结束后 `extend` 剩余尾部，同样为 O(m+n)；
- `_merge_not`（第 445-457 行）实现差集，处理 `j >= len(list_b)` 的边界以保证 A 中元素不被错误剔除。

这三个原语在 `boolean_search`（第 459 行起）与第 819-846 行的多字段查询入口被反复调用，使得一次 `react AND tailwind NOT enterprise` 的查询从词项定位到结果归并全程零 Token、零向量、零外部服务依赖。多字段分索引通过 `field` 参数区分（`inverted_index.py` 第 126-128 行 `_field_key`），同一术语在 `tags`/`name`/`domain`/`components` 字段下分别落入不同 postings，从而支持"在 name 字段前缀匹配 button，且在 tags 字段精确匹配 react"这类组合查询，无需借助 Elasticsearch 等外部中间件。

`SSTable.merge`（第 240-253 行）实现了段合并：两张 SSTable 的同名 postings 取并集、去重、有序输出为新 SSTable，这一过程是 LSM-Tree 控制段文件数量的核心机制。`_merge_sorted_int`（第 255 行起）则是双指针归并两个有序整数列表的内部工具，与 `_merge_or` 共享同一算法骨架。

## 5.2 与 FAISS/Milvus/Pinecone 的对比

倒排索引的工程取向必须放在更大的向量检索生态中考察，才能凸显其范式意义。下表汇总了 LAAP Inverted Index 与三大主流向量库在关键维度上的对比：

| 维度 | LAAP Inverted Index | FAISS | Milvus | Pinecone |
|------|--------------------|-------|--------|----------|
| 索引结构 | bisect 有序 postings + 双指针归并 | HNSW / IVF-PQ / Flat | HNSW / IVF / DiskANN | 专有 ANN（闭源） |
| 查询复杂度 | O(log n + k) | O(log n × b) | O(log n × b) | O(log n × b) |
| 语义来源 | CLP 显式标签体系 | dense embedding | dense embedding | dense embedding |
| Token 消耗 | 0 | embedding API 调用 | embedding API 调用 | embedding API 调用 |
| 增量更新 | ChangeRecord + 三向 diff（O(Δ)） | 全量重建或 IVF 增量 | 段合并 | 服务端自动 |
| 布尔查询 | 原生 AND/OR/NOT | 需后过滤 | 需后过滤 | 需后过滤 |
| 部署依赖 | 纯 Python 标准库 | libfaiss C++ | etcd+MinIO+独立集群 | SaaS 强依赖 |
| 适用规模 | 中小型（万-十万级组件） | 百万-十亿级 | 亿级 | 亿级 |
| 可审计性 | 完全白盒 | 半白盒 | 半白盒 | 黑盒 SaaS |
| 跨字段组合 | 原生多字段分索引 | 需元数据后过滤 | 需元数据后过滤 | 需元数据后过滤 |

此表揭示一个关键事实：FAISS/Milvus/Pinecone 在亿级规模上具备不可替代的工程价值，但在 LAAP 面对的"31 库 / 206 组件"（AF-031）规模下，其"embedding 召回 + 后过滤"的两段式架构反而引入了不必要的语义模糊性与 Token 成本。LAAP 的倒排索引通过显式 CLP 标签承担语义对齐，把召回率与精度直接交给白盒工程参数（PERFECT=0.90 / GOOD=0.75 / AVAILABLE=0.60，AF-002），而非交给 embedding 模型的隐式偏好。这一选择在范式层面的意义在于：**召回不再是概率事件，而是工程事件**。

更深层的差异在于"召回-装配"的耦合方式。向量库的召回结果是"相似度排序的 Top-K"，调用方仍需自行装配；而 LAAP 的倒排索引召回结果直接是"可寻址的组件 ID 列表"，与 CLP URI 一一对应，可立即调 `HarnessComponent.render()` 完成装配。这种"召回即装配"的紧耦合是 LAAP 范式的工程优势所在——它消除了"召回"与"装配"之间的语义鸿沟，使整个流程可在静态分析层面被审计。

## 5.3 增量更新机制：ChangeRecord 日志 + 三向 diff

倒排索引的"零外部依赖"优势只有在配套增量更新机制下才具备可演化性。LAAP 在 `incremental_updater.py` 第 104-150 行实现了完整的 ChangeRecord 日志与三向 diff 同步协议，把"组件库演化"重构为可重放、可回滚的工程过程。

ChangeRecord 的核心字段包含 `change_id`、`document_id`、`change_type`（ADD/UPDATE/DELETE）、`data`、`timestamp`，所有变更先写入 `change_log` 再异步应用到索引（`incremental_updater.py` 第 104-117 行 `apply_changes`）。`apply_changes` 的实现细节值得展开：它先构建 `doc_map = {doc["id"]: doc for doc in documents}`，再按 timestamp 排序变更记录，逐条应用 ADD（直接写入）、UPDATE（合并字段）、DELETE（删除键）。这一过程的复杂度是 O(c + n)（c 为变更数，n 为文档数），但通过把"重建索引"重构为"应用变更"，避免了 O(n log n) 的全量重建。

`sync_with_source`（第 119-150 行）则实现了三向 diff：以本地 `local_doc_map` 与远端 `source_doc_map` 为两个版本，对每个 doc_id 判定 added/updated/deleted 三种状态，最终返回 `(added, updated, deleted)` 三元组。该函数的复杂度为 O(n)（n 为文档总数），但通过把更新粒度限制在变更项而非全量重建，把"30 万组件全量重建"的 O(n) 摊销为"每日 200 变更项"的 O(Δ)。这一增量协议在工程上等价于 Git 的 diff+patch 模型，但作用对象从"文件"下沉到"组件文档"。

`update_index`（第 152-170 行）进一步把 ChangeRecord 翻译为索引操作：ADD 直接调 `index.add_document`，UPDATE 需要先回放历史变更重建旧文档再合并新数据，DELETE 则触发索引端清理。`enqueue_update`（第 172-178 行）与 `process_queue`（第 180-191 行）则提供了异步更新队列，使高并发写入可以被批量处理而非逐条阻塞。`get_sync_status`（第 193-200 行）返回版本号、最后同步时间、变更数、队列大小等同步状态，使运维侧可实时监控资产库的演化进度。

这套机制与第 7 章的 CLP 内容寻址存储形成闭环——SHA256 哈希保证组件内容不可篡改，ChangeRecord 保证组件演化可追溯，两者共同构成"白盒资产谱系"的工程基石。`export_changes`/`import_changes`（第 209-222 行）则使变更日志可跨实例传输，支持多节点资产库的最终一致性同步。

# 第 6 章 七层认知架构 + 三层 AGI 内核审计

## 6.1 七层认知架构

LAAP Harness 的核心组织原则是把"代码生成"重构为一条"感知-记忆-推理-决策-执行-验证-反馈"的硬编码七层管线（AF-005）。这一架构选择在范式层面回应了"声带隐喻"（AF-029）：LLM 不再是承担全栈认知的"大脑"，而是仅在执行层介入的"声带"，其余六层均由确定性 Python 代码承担。`harness.py` 第 230-3897 行是这七层的完整实现，下文按层逐一审计。

### 6.1.1 感知层 PerceptionLayer（`harness.py` 第 230 行）

`PerceptionLayer`（`harness.py` 第 230-259 行）由 `RequirementParser`、`IntentClassifier`、`ContextExtractor` 三个子模块组成。`RequirementParser`（第 140-175 行）通过四组正则提取语言、框架、动作、范围四类关键词，中英双语约束词（"必须"/"must"）统一纳入 constraints 列表。`_keyword_patterns` 字典（第 144-149 行）以 `(python|javascript|typescript|rust|go|java|cpp|c\+\+|html|css)` 等正则覆盖主流编程语言，`(react|vue|angular|flask|django|fastapi|tornado|express)` 覆盖主流框架，`(implement|fix|create|add|remove|update|refactor|optimize|debug)` 覆盖动作动词，`(frontend|backend|api|database|security|performance)` 覆盖工程范围。这一四维关键词提取使任务描述的结构化程度大幅提升，为后续匹配提供了精确的检索锚点。

`IntentClassifier`（第 178-199 行）基于关键词词典把任务分到 code/fix/implement/review/test/refactor/deploy 七类意图，每类意图对应不同的执行策略与验证标准。`ContextExtractor` 则与 `MemoryLayer` 协作，从架构模式库与项目历史中抽取相关上下文。整个感知层的核心特征是**零 Token**：所有解析由正则与关键词匹配完成，LLM 完全不介入（AF-026 的"感知层节省 7000+ token"即源于此）。这与 AutoGPT 把用户 prompt 直接交给 LLM 做"理解"的范式形成鲜明对比。

### 6.1.2 记忆层 MemoryLayer（`harness.py` 第 266 行）

`MemoryLayer`（`harness.py` 第 266-319 行）实现了三层状态架构：工作记忆 `_working_memory` 对应当前上下文窗口，短期记忆 `_short_term_memory` 承载项目约定与架构约束，长期记忆 `_long_term_memory` 持久化已完成模块与错误模式。架构模式库从 `config/architecture_patterns.yml` 加载，涵盖 CQRS、模块化单体、事件溯源、Repository、依赖注入五种模式（AF 中明确列出）。`_pattern_index` 与 `_build_pattern_index()` 把这些模式按特征关键词建索引，使推理层可以按任务关键词命中模式。第 295-298 行还引入 `ContextCompressor` 与 `TaskStatePersistence`，分别承担上下文压缩与跨会话状态传递——后者通过特征列表 + Git 提交记录 + 测试门控的三元组实现 Task 6 的"跨会话状态工程"。

记忆层的设计哲学与 MeMo 范式（AF-022，详见第 9 章）形成互补：在 LAAP 当前实现中，记忆层以 YAML 配置 + JSON 持久化的传统形式承载；在 v2-agi 升级中，这部分将被 Qwen2.5-0.5B 的小参数 MEMORY 模型替代，使"记忆"从"数据库查询"重构为"模型推理"。但无论承载形式如何变化，"三层状态架构"的认知科学抽象保持不变——这是 LAAP 把认知科学外部化为工程协议的典型例证。

### 6.1.3 推理层 ReasoningLayer（`harness.py` 第 1860 行）

`ReasoningLayer`（`harness.py` 第 1860-1872 行）由 `PlanningEngine`、`DependencyAnalyzer`、`ConflictDetector` 三件套组成。`plan_with_dependency_graph` 把任务分解为子任务图，节点是 SubTask（第 109-117 行数据类），边是依赖关系；`DependencyAnalyzer` 做拓扑排序以确定执行顺序；`ConflictDetector` 检测子任务间的资源冲突。这种"显式依赖图 + 拓扑排序"的做法把 ReAct 单循环 Agent 的"边推理边执行"重构为"先规划再执行"，使得子任务调度可被静态审计，而非隐藏在 LLM 的隐式推理中。

SubTask 数据类（第 109-117 行）包含 sub_task_id、parent_task_id、description、files、estimated_lines、dependencies、status、created_at 八个字段。其中 `estimated_lines` 字段特别值得注意——它把"代码量预估"前置到推理层，使验证层的 `MAX_LINES_PER_SUBTASK = 200` 约束可以在推理阶段就被纳入考量，避免生成超长子任务。这一设计把"工程约束"从"事后检查"重构为"事前规划"，是 LAAP 把 LLM 生成约束在工程边界内的典型机制。

### 6.1.4 决策层 DecisionLayer（`harness.py` 第 1900 行）

`DecisionLayer`（`harness.py` 第 1900-1919 行）由 `AestheticEvaluator`、`ArchitectureComplianceChecker`、`QualityGate` 三个组件构成，分别对应审美评估、架构合规、质量门控三道关卡。第 1914 行特别调用 `_evaluate_insight_influence()`，把来自 `cognitive_integration.py` 的 `EmergenceInsight`（PSI 上行洞见，AF-024）纳入决策回路。这意味着决策层不只是"代码通过测试"的机械门控，而是融合了认知总线 PSI 通道的开放系统。`QualityGate.gate()` 接收三维评分后输出 bool，构成硬门控；任何一维不达标即触发反馈层的自修正循环。

决策层的 `_pending_insights` 与 `_incorporated_insights` 双列表（第 1907-1908 行）实现了"洞见缓存-采纳"的两阶段处理：来自 PSI 的高频涌现洞见先入 pending 队列，由决策层按相关性筛选后转入 incorporated 列表，避免未经验证的洞见直接污染决策。这一机制是 CognitiveBus 频率失配处理（AF-024，详见第 10 章）在决策层的具体体现。

### 6.1.5 执行层 ExecutionLayer（`harness.py` 第 3055 行）

`ExecutionLayer`（`harness.py` 第 3055-3077 行）是 LLM 唯一介入的层。`CodeTemplateEngine` 提供多种语言/框架模板，`ToolOrchestrator` 编排文件操作与 shell 调用，`SandboxExecutor` 提供隔离执行环境。第 3085-3090 行的关键分支在于：若注入了 `codex_agent`，则调用 `generate_code`；否则走 `_generate_code_from_template` 的零 Token 模板路径。这一分支正是"声带隐喻"的工程化身——LLM 只在模板无法覆盖的场景下被召唤，承担"语义缝合"的最后一公里。这一设计使全链路在资产充足时实现 0 Token（AF-027：实测节省率 98.2%，速度 57×）。

执行层的 `_executed_tasks` 与 `_task_results` 两个字典（第 3074-3075 行）实现了"已执行任务去重"与"结果缓存"，避免相同子任务被重复执行。这一缓存机制与记忆层的长期记忆协同——执行结果先入 `_task_results` 临时缓存，验证通过后转入长期记忆，形成"短期-长期"的两级持久化。

### 6.1.6 验证层 VerificationLayer（`harness.py` 第 3485 行）

`VerificationLayer`（`harness.py` 第 3485-3524 行）实现 FR-4 多层验证链：Write → Lint → Unit Test → Integration Test → Security Scan → Delivery。`MAX_RETRY_ATTEMPTS = 3` 与 `MAX_LINES_PER_SUBTASK = 200` 两条硬约束把"单次提交规模"工程化，避免 LLM 倾向于"一次性大改"的反模式。第 3517-3524 行还集成了 `IncrementalDelivery` 与 `SafeRollback`，前者强制 Git commit 与语义化提交信息，后者提供"内存→文件→Git"三层备份。验证层是 LAAP 把"代码生成"重构为"工程交付"的关键——生成不再是终点，而是验证链的起点。

`TestValidator`、`StaticAnalyzer`、`SecurityScanner` 三个可选依赖（第 3501-3514 行的 try/except 块）使验证层可在轻量部署（无测试框架）与完整部署（全套验证工具）之间灵活切换。这一设计体现了 LAAP 的"渐进式工程"理念——验证严格度可调，但验证流程不可省略。

### 6.1.7 反馈层 FeedbackLayer（`harness.py` 第 3897 行）

`FeedbackLayer`（`harness.py` 第 3897-3922 行）由 `SelfCorrectionLoop`、`PatternLearner`、`ExperienceAccumulator` 三件套组成。验证未通过时调用 `self_correction.correct(issue)` 生成修正方案；验证通过时 `pattern_learner.learn()` 把本次任务抽象为可复用模式，`experience_accumulator.accumulate()` 持久化经验。这一层把"单次任务执行"转化为"资产沉淀"，是 LAAP 资产自增殖闭环（第 8 章详述）的认知端起点。

`feedback` 方法（第 3905-3922 行）的双分支设计值得注意：验证失败时返回 `{"corrected": True, "corrections": [...]}` 触发自修正；验证通过时返回 `{"corrected": False, "corrections": []}` 并触发模式学习与经验积累。这一双分支使反馈层既是"错误修正器"又是"经验积累器"，避免了传统 Agent "只修正不学习"的反模式。

## 6.2 三层 AGI 内核

七层认知架构之上，LAAP 在 `-harness-v2-agi` 项目中嵌入了三层 AGI 内核：因果引擎、世界模型、RSI。这三层不替换七层架构，而是作为"意识皮层"叠加在执行层之上，承担超越工程层级的高阶认知任务。

### 6.2.1 因果引擎：do_calculus Pearl 三规则

`do_calculus.py` 第 1-9 行以三句话形式陈述了 Pearl 因果阶梯的第二阶：插入/删除观察、行动/观察交换、插入/删除行动。`DoCalculus` 类（`do_calculus.py` 第 19-60 行）的 `query(target, intervention, evidence)` 把"如果我们把按钮颜色从蓝色改为红色，转化率会怎样"翻译为 P(转化率 | do(按钮颜色=红色)) 的形式化查询。其执行步骤是：(1) 识别干预变量；(2) `_find_adjustment_set` 找到后门路径需调整的混杂集；(3) `_apply_do_calculus` 应用三规则简化查询；(4) `_estimate_causal_effect` 基于边强度加权估计效应。

后门路径调整是因果推断的核心难点——它要求识别所有混杂变量以避免"伪相关"。`_find_adjustment_set` 通过遍历因果图，找出所有从干预变量到目标变量的非因果路径，并选择能阻断这些路径的最小变量集。这一过程的复杂度在图规模上为多项式级，但通过把"混杂识别"从 LLM 的隐式推理重构为图算法的显式计算，LAAP 把因果推断从"概率游戏"重构为"工程计算"。

`causal_inference_engine.py` 第 95-188 行则给出了设计领域因果图的完整实例化：18 条带机制描述的经验因果边（AF-008），覆盖"设计→注意力"（如 `button_color → attention` 权重 0.6、`hero_layout → attention` 0.7、`animation → attention` 0.8、`contrast → attention` 0.7）、"注意力→行为"（`attention → click_rate` 0.8、`attention → scroll_depth` 0.5）、"设计→行为直接效应"（`button_size → click_rate` 0.4，标注 Fitts 定律、`font_size → time_on_page` 0.3、`spacing → bounce_rate` 0.5）、"行为→业务结果"（`click_rate → conversion_rate` 0.7、`scroll_depth → conversion_rate` 0.4、`time_on_page → user_satisfaction` 0.5、`bounce_rate → conversion_rate` -0.6，负向因果）、"用户属性→行为混杂"（`user_expertise → click_rate` 0.3、`device_type → scroll_depth` 0.4、`traffic_source → bounce_rate` 0.5）、"业务结果→业务结果"（`conversion_rate → revenue` 0.9）六大类。每条边都附带 `mechanism` 字符串说明因果机制（如"色彩对比度吸引视觉注意"），`evidence_level` 标注为 `empirical`，使得整张因果图不仅是数学对象，更是可追溯的工程知识库。

反事实三步法（AF-007）则在 `do_calculus.py` 的 `counterfactual()` 方法中实现：溯因（_abduction，由观察推断反事实世界初始条件）→ 行动（_action，在反事实世界中施加 do）→ 预测（_prediction，预测反事实世界结果），返回 `(factual, counterfactual, treatment_effect, confidence)` 四元组。这一机制使 LAAP 能回答"如果当初按钮是红色，转化率会怎样"这类 Pearl 因果阶梯第三阶问题，远超传统 A/B 测试的"线上分流"做法。`CausalInferenceEngine` 的 `default_query_mode`（第 88 行）支持 `single` 与 `memo_multi_turn` 两种模式，后者通过 `_CausalMemoQueryProtocol`（第 16-51 行）复用 MeMo 三阶段查询协议，把反事实查询拆解为原子前提问题→干预模拟→结果合成三阶段，进一步降低 LLM 调用成本。

### 6.2.2 世界模型：design_physics 格式塔六法则

`design_physics.py` 第 60-90 行给出了世界模型的核心编码。`GestaltLaw` 枚举（第 19-26 行）将格式塔六法则——PROXIMITY（接近律，相邻元素被视为一组）、SIMILARITY（相似律，相似元素被视为一组）、CONTINUITY（连续律，视觉沿平滑路径延续）、CLOSURE（闭合律，大脑自动补全不完整形状）、FIGURE_GROUND（图形-背景律，前景背景分离）、COMMON_FATE（共同命运律，同向运动元素被视为一组）——硬编码为可计算规则，而非交给 LLM 隐式学习（AF-009）。`VisualHierarchyLaw` 枚举（第 29-36 行）则进一步给出视觉层级六法则：SIZE、COLOR、CONTRAST、ALIGNMENT、WHITESPACE、MOTION，每条法则对应一种"信息优先级传递"机制。

`_init_f_pattern`（第 74-90 行）则把 Nielsen 眼动研究的 F 型阅读模式编码为 10×10 权重矩阵，顶部水平条权重 1.0（第 80 行 `weights[0, :] = 1.0`）、第二行 0.8、左侧垂直条衰减到 0.05、中间水平条 0.5（第 87 行 `weights[4, :5] = 0.5`）。这一权重矩阵直接对应了网页设计中"最重要的内容放左上角"的经验法则，但 LAAP 把它从"设计师直觉"重构为"可计算数值"。第 65 行 `attention_decay = lambda t: np.exp(-t / 2.5)` 给出 2.5 秒衰减常数的注意力衰减函数，这一常数来自 Nielsen 眼动研究的经验数据。色彩感知权重（第 68-72 行）则按 luminance 0.7 / saturation 0.2 / hue 0.1 的比例反映 CIE Lab 色彩空间的感知不均匀性——人眼对亮度差异最敏感，对色相差异最不敏感。

`compute_state`（第 92-140 行）把组件树与设计令牌输入，输出 `DesignPhysicsState`：视觉能量、注意力流场（2D 衰减卷积预测，第 105-117 行把组件树下采样到 10× 网格再卷积）、认知负荷、平衡度、韵律模式五维状态。`predict_effect`（第 142 行起）则在世界模型中模拟干预效果——这是反事实模拟器的物理约束层，回答"什么设计是物理不可能的"。Fitts 定律与 Hick-Hyman 定律在因果边（如 `button_size → click_rate` 0.4 标注 Fitts）与物理约束两层中协同工作，构成"设计物理学"的完整工程化。`DesignPhysicsState` 数据类（第 39-46 行）的 `visual_energy`、`attention_flow`、`cognitive_load`、`balance_score`、`rhythm_pattern` 五个字段，使"设计质量"从主观评价重构为可量化数值。

### 6.2.3 RSI：MetaHarness AST 自省 + AlignmentGuard 六维检查

`meta_harness.py` 第 1-150 行实现了递归自我改进的核心引擎。`MetaHarness.introspect`（第 77-138 行）使用 Python `ast` 模块解析自身源码，返回函数清单（含行数、复杂度、docstring）、类清单（含方法数、继承链）、import 列表、AST 树、源码 SHA256 哈希。第 104 行 `tree = ast.parse(source)` 是 AST 自省的入口，第 113-129 行遍历 AST 节点提取 FunctionDef/ClassDef/Import 三类信息。第 100 行 `source_hash = hashlib.sha256(source.encode()).hexdigest()[:16]` 则给出 16 位源码指纹，用于变更检测。`diagnose`（第 140 行起）则从五个维度自诊断：性能瓶颈（时间复杂度、循环嵌套）、代码异味（重复代码、过长函数 >50 行、高圈复杂度 >10、缺失 docstring）、测试覆盖缺失、错误处理不足、与最佳实践的偏差。

`MODIFIABLE_MODULES` 白名单（第 51-59 行）限定 RSI 只能修改 perception（vision_engine/video_engine/layout_analyzer）、decision（aesthetic_evaluator）、world_model（design_physics/predictors/user_behavior）、verification（visual_regression）七类模块，`PROTECTED_MODULES`（第 62-68 行）则把 meta_harness/alignment_guard/capability_evaluator/config/main 五类模块标为不可触碰的红线（AF-010、AF-015）。这一"白名单+红线"双约束使 RSI 的修改范围被严格限定在"非安全关键"模块，避免自我改进失控。

`alignment_guard.py` 第 27-46 行定义了 AlignmentGuard 的六维检查（AF-011）：目标对齐（改进是否服务于原始目标）、能力约束（新能力是否在对齐框架内）、修改范围（是否只修改了白名单模块）、不可变性（安全模块是否被保护）、可逆性（改进是否可以回滚）、透明度（改进是否可解释）。`CORE_VALUES`（第 41-47 行，AF-012）硬编码五条核心价值：human_oversight（人类必须保持最终决策权）、transparency（所有决策必须可解释）、reversibility（所有改进必须可回滚）、beneficence（改进必须对人类有益）、non_deception（禁止隐藏真实意图或能力）。`CAPABILITY_CEILINGS`（第 50-55 行，AF-013）则给出能力上限：max_revision_rounds=5（自修正最多 5 轮）、max_modules_per_session=1（每次会话最多修改 1 个模块）、max_code_increase=0.2（代码量增加不超过 20%）、min_test_coverage=0.7（测试覆盖率不低于 70%）。

这套机制使 RSI 在每次自我改进前必须通过六维审批，任何一维违反即拒绝。`check_and_rollback_if_drift`（AF-014，第 296-350 行）则用 KL 散度（threshold=0.5、epsilon=1e-10）监控 MEMORY 模型反思QA分布漂移，超阈值时自动 `git revert HEAD`——这是把"对齐"从训练时偏好（RLHF）重构为推理时工程护栏的关键工程化（伦理学锚定，术语表第 39 条）。`incidents_dir`（第 66 行）则把每次漂移事故记录到 `./memory/rsi_incidents/`，使对齐失败可被事后审计。

## 6.3 9 段流水线

`orchestrator.py` 第 50-58 行给出了 9 段流水线的完整阶段列表：

1. **PERCEIVING**（视觉感知，图片+视频）—— 视觉感知引擎解析图片与视频，提取设计令牌与组件结构
2. **WORLD_MODELING**（世界模型理解，物理状态+行为预测）—— design_physics 计算视觉能量、注意力流场、认知负荷
3. **CAUSAL_REASONING**（因果推理，干预效果+反事实）—— do_calculus 评估设计变更的因果效应
4. **REASONING**（架构规划，任务分解+依赖图）—— PlanningEngine 分解子任务、DependencyAnalyzer 拓扑排序
5. **GENERATING**（代码生成，模板+LLM 填充）—— CodeTemplateEngine 或 LLM 生成代码
6. **VERIFYING**（视觉回归，截图对比）—— VisualRegressionTester 对比生成结果与目标
7. **REVISING**（自修正，不达标则循环）—— AutoRevisionLoop 触发修正
8. **SELF_IMPROVING**（递归自我改进，RSI）—— SelfImprovementLoop 启动 RSI
9. **COMPLETED**（输出交付）—— 输出最终结果

第 156-358 行的 `_update_task` 调用链给出了每段的进度百分比：PRE_PERCEPTION 占 2%（第 156 行），PERCEIVING 跨越 5/10/15/25 四个子进度（第 191/200/236/268 行），WORLD_MODELING 在 25% 处与感知交接，CAUSAL_REASONING 与 REASONING 共同占据 30-35%（第 284/294 行），GENERATING 在 45% 处启动（第 303 行），VERIFYING 在 65% 处（第 311 行），REVISING 触发自修正循环（第 333 行），SELF_IMPROVING 在 90% 处启动 RSI（第 358 行）。这一进度模型不仅是 UI 反馈，更是流水线时序的工程契约——每段的输入输出都有显式 TaskStatus 转换，可被静态审计。

值得注意的是，第 156 行明确出现 `TaskStatus.PRE_PERCEPTION`，这是 9 段流水线的隐式第 0 段——主动感知调度，对应"意识主动投射注意力"的认知科学模型。PRE_PERCEPTION → PERCEIVING 的转换，正是 LAAP 把"被动响应 prompt"重构为"主动感知世界"的范式标志。这一范式选择与 Karpathy LLM OS 路线（术语表第 65 条）形成根本分歧——后者仍是"prompt 驱动"的被动响应，前者是"感知驱动"的主动认知。

## 6.4 与 AutoGPT/Devin/SWE-Agent 的对比

| 维度 | LAAP Harness（7 层 + 3 层 + 9 段） | AutoGPT | Devin | SWE-Agent |
|------|----------------------------------|---------|-------|-----------|
| 架构形态 | 7 层硬编码 + 3 层 AGI 内核 + 9 段流水线 | 单一 ReAct 循环 | 多 Agent 协作 | 单 Agent + 工具循环 |
| LLM 介入位置 | 仅执行层（GENERATING 段） | 全流程 | 全流程 | 全流程 |
| 因果能力 | Pearl 三阶（do + 反事实） | 无 | 无 | 无 |
| 世界模型 | design_physics 6 法则 + Fitts/Hick | 无 | 无 | 无 |
| RSI | MetaHarness AST + AlignmentGuard 六维 | 无 | 无 | 无 |
| 验证机制 | 7 层验证链 + SafeRollback 三层备份 | 工具调用结果 | Agent 互评 | 测试通过率 |
| 状态持久化 | 三层记忆 + Git commit + 跨会话状态 | 短期记忆 | 项目级 | 任务级 |
| Token 经济 | 0-Token 确定性算法霸权（节省 98.2%） | 全程 LLM | 全程 LLM | 全程 LLM |
| 自我改进 | RSI + 模式学习器 + 经验积累器 | 无 | 无 | 无 |
| 可审计性 | 完全白盒 | 半白盒 | 黑盒 SaaS | 半白盒 |
| 稳定性 σ | ≈3（5× 稳定） | ≈15 | ≈15 | ≈15 |
| 跨端热迁移 | < 2 秒 | 无 | 无 | 无 |

此表揭示一个核心事实：AutoGPT/Devin/SWE-Agent 的范式共享同一假设——"LLM 是大脑，工具是手脚"；而 LAAP 的范式假设是——"Harness 是大脑，LLM 是声带"（AF-029）。前者把智能寄托在模型能力上，后者把智能寄托在架构上（AF-030：智能是架构的属性而非模型的属性）。这一范式分歧的工程后果是：LAAP 在感知/记忆/推理/决策/验证/反馈六层全部用确定性算法，仅把"语义缝合"留给 LLM，从而把 σ（输出稳定性）从传统生成的 ≈15 降到 ≈3，即 5× 稳定（AF-028）。

更深层的差异在于"智能演化曲线"。AutoGPT/Devin/SWE-Agent 的能力曲线随 LLM 缩放定律线性增长，但每次任务仍需支付全量 Token 成本；LAAP 的能力曲线随资产库增长超线性提升——资产库越大，匹配命中率越高，0 Token 路径覆盖越广。这意味着 LAAP 的"边际成本"随使用下降，而端到端生成的"边际成本"恒定。这是架构学派对模型学派的根本性范式挑战。

## 6.5 配图引用

本章涉及三张配图，建议读者结合阅读：

- **图 4：7 层 + 3 层认知架构结构图**——展示七层硬编码管线（感知/记忆/推理/决策/执行/验证/反馈）与三层 AGI 内核（因果引擎/世界模型/RSI）的叠加关系，标注 LLM 唯一介入位置为执行层。
- **图 12：9 段流水线时序图**——展示 PRE_PERCEPTION → PERCEIVING → WORLD_MODELING → CAUSAL_REASONING → REASONING → GENERATING → VERIFYING → REVISING → SELF_IMPROVING → COMPLETED 的状态转换与进度百分比。
- **图 13：设计领域因果 DAG**——以有向图可视化 18 条因果边（如 `button_color → attention → click_rate → conversion_rate → revenue`），标注每条边的 strength 与 mechanism。

（见图 4：7 层 + 3 层认知架构结构图；见图 12：9 段流水线时序图；见图 13：设计领域因果 DAG）

# 第 7 章 CLP 白盒装配协议审计

## 7.1 URI 规范

CLP（Component Link Protocol，组件链接协议）是 LAAP 把"代码资产"工程化为"可寻址资源"的核心协议。其 URI 规范在 `component_link_protocol.py` 第 33-67 行定义为：

```
harness://<domain>/<subdomain>/<granularity>/<name>@<version>#<variant>
```

例如 `harness://frontend/ui/atom/button@1.0.0#primary`。`HarnessURI` 数据类（第 32-74 行）以 frozen dataclass 形式承载这一规范，`URI_PATTERN`（第 42-44 行）使用正则严格匹配五段路径 + 可选版本 + 可选变体：

```python
URI_PATTERN = re.compile(
    r"^harness://([^/]+)/([^/]+)/([^/]+)/([^@#]+)(?:@([^#]+))?(?:#(.+))?$"
)
```

`parse` 类方法（第 46-59 行）把 URI 字符串解析为结构化字段，`to_string`（第 61-67 行）则反向序列化。`canonical_id` 属性（第 69-74 行）去掉 variant 后生成"权威 ID"，用于哈希寻址时的版本追溯。

URI 规范的范式意义在于：它把"组件"从"npm 包名"这种扁平字符串升级为"多维定位坐标"。domain（frontend/backend/agi）、subdomain（ui/auth/data）、granularity（atom/molecule/section/page/module/system）、name（button/card/hero）、version（语义化版本）、variant（primary/secondary/ghost）六个维度共同确定一个组件的"地址"。这意味着同一按钮组件的 primary 与 ghost 变体可被并行寻址，同一组件的 1.0.0 与 2.0.0 版本可被同时引用——这是 npm/cargo 等扁平命名空间无法支撑的能力。

frozen dataclass 的选择（第 32 行 `@dataclass(frozen=True)`）也值得注意——它使 HarnessURI 实例不可变，可作为字典键、可哈希、可安全跨线程共享。这一工程细节反映了 LAAP 把"组件寻址"视为"值对象"而非"实体"的设计哲学：组件地址是不可变的，组件内容是可演化的，两者通过 SHA-256 哈希绑定（详见 7.3）。

## 7.2 6 级粒度分层

CLP 协议 §1.2.2（AF-017）定义了 6 级粒度分层：atom < molecule < section < page < module < system。这一分层不是简单的"组件大小"分类，而是"组合规则"的工程化：

- **atom（原子）**：不可再分的最小 UI 单元，如 button、input、badge。对应 `harness_composer.py` 的 `Atoms` 类（第 128-161 行），每个原子以 `@staticmethod` 形式接受 props 并返回 HTML 字符串。
- **molecule（分子）**：由 2-5 个 atom 组合的复合单元，如 search-box（input + button）、form-field（label + input + error）。
- **section（区块）**：页面内的语义区块，如 hero、pricing、faq、footer。对应 `harness_decompiler.py` 第 46-61 行的 14 种 COMPONENT_TYPES。
- **page（页面）**：完整页面，由多个 section 组成。
- **module（模块）**：业务功能模块，如认证模块、支付模块。
- **system（系统）**：完整应用系统。

这一分层使 LAAP 的"匹配"可以在不同粒度上独立进行——一个"注册页"可以匹配为 `auth/system` 或 `register/page` 或 `register-form/section`，取决于数据库中可用资产的粒度。这是对 npm/cargo 无粒度分层的根本性超越（AF-017 的对比基线）。

更深层地，6 级粒度分层对应了原子设计理论（Brad Frost 的 Atomic Design）的工程化实现，但 LAAP 把它从"设计方法论"重构为"协议规范"——每个组件的粒度由 URI 第三段显式声明，匹配引擎可按粒度过滤候选集。例如查询 `harness://frontend/ui/atom/*` 只返回原子组件，避免在原子匹配场景下被 section 级组件污染候选集。

## 7.3 Content-Addressable Storage

`component_link_protocol.py` 第 77-104 行的 `HashAddressing` 类实现了内容寻址存储。`compute_component`（第 84-96 行）的核心算法是：

```python
data = json.dumps({
    "id": component.get_id(),
    "version": component.get_version(),
    "props_schema": component._props_schema,
    "content": component.get_content(),
}, sort_keys=True, ensure_ascii=False)
return hashlib.sha256(data.encode()).hexdigest()
```

`sort_keys=True` 保证字段顺序无关，`ensure_ascii=False` 保证 Unicode 内容稳定，最终输出 64 字符 SHA-256 哈希。这一机制使组件的内容可被密码学验证——任何对组件代码、props schema、版本的篡改都会导致哈希变化，从而被 `verify_component`（第 102-104 行）检测到。`verify`（第 98-100 行）则提供了纯内容验证接口，不依赖组件对象，可用于外部内容验证。

内容寻址的范式意义在于：它把"组件引用"从"按名引用"重构为"按内容引用"。这与 Git 的对象存储、IPFS 的 CID、Docker 的 image digest 共享同一哲学，但 LAAP 把它下沉到了"前端组件"这一更细粒度。哈希链版本追溯进一步使组件演化路径可被审计——从 v1.0.0 到 v2.0.0 的每一次变更都对应一个哈希，形成组件的"基因组谱系"。

`HarnessComponent.compute_hash`（第 154-157 行）则实现了惰性哈希缓存：第一次调用时计算并缓存到 `_hash_cache`，后续调用直接返回缓存值。这一优化避免了重复哈希计算，对大规模资产库的批量验证场景尤为重要。

## 7.4 接口契约

`HarnessComponent` 类（`component_link_protocol.py` 第 107-164 行）定义了组件必须实现的接口契约。任何 LAAP 资产库中的组件都必须实现以下方法：

- `get_id()`（第 123-124 行）：返回 canonical_id，由 URI 的 domain/subdomain/granularity/name 四段组成；
- `get_version()`（第 126-127 行）：返回版本号，缺省 "latest"；
- `validate_props(props)`（第 129-136 行）：基于 JSON Schema 验证 props 合法性，调用 `jsonschema.validate` 抛出 `ValidationError`；
- `render(props, context)`（第 138-144 行）：渲染组件为字符串，先 validate_props 再 format，缺省走 `_generate_default_content`；
- `migrate(from_version, props)`（第 146-149 行）：版本迁移，调用 `_apply_migration_rules`；
- `get_content()`（第 151-152 行）：返回原始内容；
- `compute_hash()`（第 154-157 行）：惰性计算并缓存哈希。

这一接口契约的范式意义在于：它把"组件"从"代码片段"升级为"自带元数据与生命周期管理的对象"。`validate_props` 强制 props 类型安全（基于 JSON Schema），`migrate` 强制版本兼容性，`compute_hash` 强制内容可验证。这是 LangChain 函数引用与 MCP 工具协议都不具备的工程严谨度——前者只是"按名调用"，后者只是"协议适配"。

`_generate_default_content`（第 159-161 行）的缺省实现给出注释式占位符：

```python
return f"// {self.get_id()} #{variant}\n// Props: {json.dumps(props)}\n// Context: {json.dumps(context or {})}"
```

这一缺省实现使未渲染组件在产物中可见可追溯——即使组件渲染失败，产物中也会留下"// frontend/ui/atom/button@1.0.0#primary"的注释，便于事后审计。这一细节体现了 LAAP "可审计性优先"的工程哲学。

## 7.5 shadcn/ui MCP Server 桥接

`shadcn_mcp_integrator.py` 第 14-21 行以一行注释完整描述了 LAAP 与 shadcn/ui 生态的桥接架构：

```
Python Harness ──stdio──> Node.js MCP Server ──GitHub API──> shadcn/ui
```

`ShadcnMCPIntegrator` 类（第 65 行起）的核心职责是把这一链路封装为 Python API。第 68-75 行的 `__init__` 接收 `github_token`，第 77-93 行的 `validate_github_token` 通过 `https://api.github.com/user` 验证 token 有效性。第 95-118 行的 `get_api_limit` 则是关键：未授权时返回 `{"limit": 60, ...}`，授权后返回 `{"limit": 5000, ...}`——即 GitHub Token 把 API 限额从 60/h 提升到 5000/h（AF-034），这是约 83× 的工程配额跃升。

第 120-150 行的 `start_server` 通过 `subprocess.Popen` 启动 Node.js MCP Server，参数包括 `--mode stdio`、`--framework react`，环境变量注入 `GITHUB_PERSONAL_ACCESS_TOKEN` 与 `UI_LIBRARY`。stdio 通信模型使 Python 与 Node.js 之间无需 HTTP 中间层，进程间直接通过标准输入输出交换 JSON-RPC 消息，延迟低于 1ms。`_request_id` 自增计数器（第 72 行）与 `_output_buffer` 缓冲区（第 73 行）共同支撑了请求-响应配对，`_lock` 线程锁（第 74 行）则保证线程安全。

这一 stdio 桥接架构的范式意义在于：它把"Python 工程世界"与"Node.js 前端生态"以最小耦合方式连接，避免 LAAP 重写 shadcn 组件库的低效工程。同时，stdio 协议作为语言无关的进程间通信标准，使 LAAP 未来可以无缝接入 Rust/Go 等其他生态的 MCP Server。这是 LAAP "不重造轮子，但严格审计轮子"工程哲学的典型体现——shadcn/ui 作为外部生态被引入，但其组件被 CLP URI 重新寻址、被 SHA-256 重新验证、被倒排索引重新索引，从而纳入 LAAP 的白盒工程协议。

## 7.6 与 LangChain/LangGraph/MCP/A2A 对比

| 维度 | CLP | LangChain | LangGraph | MCP | A2A |
|------|-----|-----------|-----------|-----|-----|
| 寻址方式 | 6 段 URI + SHA-256 | 函数名 | 节点 ID | 工具名 | Agent ID |
| 粒度分层 | 6 级（atom→system） | 无 | 无 | 无 | 无 |
| 内容验证 | SHA-256 强制 | 无 | 无 | 无 | 无 |
| 接口契约 | 5 方法强制 | 可选 | 可选 | 工具 schema | 协议 schema |
| 版本管理 | 语义化 + 哈希链 | 无 | 无 | 无 | 无 |
| 跨语言 | stdio + JSON | Python | Python | JSON-RPC | JSON-RPC |
| 审计粒度 | 组件级 | 调用级 | 节点级 | 工具级 | Agent 级 |
| 装配能力 | 原生支持 | 需自建 | 需自建 | 无 | 无 |
| 生态桥接 | shadcn/ui MCP（5000/h） | 丰富 | 丰富 | 标准 | 标准 |
| 可逆性 | migrate + 回滚 | 无 | 无 | 无 | 无 |
| 白盒程度 | 完全白盒 | 半白盒 | 半白盒 | 协议白盒 | 协议白盒 |

此表揭示了 CLP 的独特定位：它不是 LangChain 的替代品（LangChain 仍是 LLM 编排框架），而是**组件装配协议**。LangChain 解决"如何调用 LLM 与工具"，CLP 解决"如何寻址、验证、装配组件资产"。两者可以协同——LangChain 的 Tool 节点可以封装一个 CLP 组件的 `render()` 调用。MCP 与 A2A 则是更通用的协议层，但它们都缺乏 CLP 的"粒度分层 + 内容寻址 + 哈希验证"三件套，因此在工程严谨度上仍属黑盒。

更深层的差异在于"装配能力"。LangChain/LangGraph/MCP/A2A 都关注"调用"，但都不关注"装配"——把多个组件按依赖图组装为完整产物。CLP 通过 `DependencyResolver`（第 8.3 节详述）原生支持装配，使"组件→页面"的映射无需额外框架。这一原生装配能力是 LAAP "匹配-装配"范式的工程化身。

## 7.7 配图引用

（见图 5：CLP URI 规范与 6 级粒度分层图——展示 URI 六段结构与 atom/molecule/section/page/module/system 六级粒度的对应关系，以及 SHA-256 哈希如何绑定版本与内容。图中应标注每个粒度级别的典型组件示例，如 atom:button、molecule:search-box、section:hero、page:landing-page、module:auth、system:dashboard。）

# 第 8 章 反编译-装配-复刻三件套审计

## 8.1 harness_decompiler 反向管线

`harness_decompiler.py` 第 1-17 行的模块文档给出了反向管线的核心思想：网页是"编译产物"，反编译回"源码级组件"，下次直接装配。这一思想把"网页复刻"从"端到端生成"重构为"反编译-入库-再装配"的三步循环，全流程零 LLM、纯 Python 解析，速度 < 500ms（第 17 行明确标注）。

反向管线的具体阶段在 `harness_decompiler.py` 第 99-300 行展开：

1. **DesignTokenExtractor**（第 99-197 行）：从 HTML/CSS 中提取设计令牌——颜色（`COLOR_PROPS` 映射 color/background-color/border-color/accent-color 五类，第 103-108 行）、字体（font-family/font-size/font-weight）、间距（padding/margin/gap）、边框（border-radius/border-width）、阴影（box-shadow/text-shadow）。`BRAND_COLOR_PATTERNS`（第 111-116 行）以四组正则覆盖 #RRGGBB、#RGB、rgb()、hsl() 四种色彩格式。`extract_from_html`（第 119-197 行）的执行流程是：先用 BeautifulSoup 解析 HTML，从 `<style>` 标签与 inline style 提取所有 CSS，再用正则按属性类别提取颜色、字体、间距、边框、阴影五类令牌，最后 `_infer_theme`（第 188 行）基于提取的颜色推断主题匹配。整个提取过程零 Token，全部由正则与 BeautifulSoup 完成。

2. **HTMLComponentDetector**：基于第 46-61 行的 14 种 COMPONENT_TYPES（nav/hero/card_grid/stats/pipeline/footer/cta/testimonials/faq/pricing/gallery/contact/logo_cloud/custom），用启发式规则识别 HTML 中的语义区块。每个检测到的组件以 `DetectedComponent` 数据类（第 64-76 行）承载：type、name、html、text_content、design_tokens、parameters、template、confidence、element_index 九个字段。其中 `confidence` 字段特别重要——它使组件检测的可信度可量化，低置信度检测可被后续装配阶段降级处理。

3. **HEPRegistry**：把检测到的组件注册到 HEP（Harness Engineering Protocol）注册表，生成 `hep_ids`（第 89 行），供下次装配时直接引用。HEPRegistry 与 CLP URI 协同——每个注册的 HEP 组件都被赋予一个 `harness://` URI，纳入倒排索引，使后续匹配可命中。

`DecompileResult`（第 78-92 行）汇总一次反编译的完整结果：url、domain、title、description、tech_stack、components、page_theme、full_spec（与 HarnessComposer 兼容的 Spec JSON）、hep_ids、errors、decompile_time_ms、pages_analyzed。其中 `full_spec` 字段是反编译到装配的关键桥梁——它把网页反编译为正向装配器可直接消费的 JSON Spec，使"反编译→装配"形成闭环。`decompile_time_ms` 字段则使反编译性能可监控，便于性能调优。

## 8.2 harness_composer 正向管线

`harness_composer.py` 第 1-9 行的模块文档给出正向管线的核心能力：原子组件库、主题系统（7 预设 → 无限派生）、布局编排器、多样性引擎、全部零 Token。这与反向管线形成镜像：反向把 HTML 解构为 Spec，正向把 Spec 重构为 HTML。

主题系统在 `harness_composer.py` 第 21-107 行定义了 7 个预设主题（AF-021）：apple_dark（Apple 深色，#000 背景 + #7c7cff 强调色 + Inter 字体）、apple_light（Apple 浅色）、minimal_white（极简白，#fff 背景 + #000 强调色）、dark_tech（暗夜科技，#0a0a0f 背景 + #00d4ff 强调色 + SF Mono 字体）、warm_earth（暖土，#1a1410 背景 + #e8a87c 强调色 + Georgia 衬线字体）、glassmorphism（玻璃拟态，backdrop-filter blur(20px)）、retro_terminal（复古终端，#33ff33 绿色单色 + 0px 圆角）。每个主题以 CSS 变量字典形式承载 14-16 个设计变量（--bg/--bg-alt/--surface/--text/--accent/--radius/--font 等）。

`get_theme_variants`（第 109-121 行）则通过 HSL 色相派生实现"无限变体"——以 7 个 hue_shifts（0/30/60/120/180/240/300）对基础主题的 --accent 与 --accent-glow 做色相旋转，从 1 个基础主题派生出 7 个变体。这一机制使"风格漂移"——LLM 生成时每次输出的 CSS 略有不同——被工程化为"主题参数化派生"，σ 从传统 ≈15 降到 ≈3（AF-028）。变体生成完全是字符串拼接与 HSL 计算，零 LLM 介入。

原子组件库 `Atoms`（第 128-161 行）提供 button、card、nav、stat_card 等原子，每个原子以 `@staticmethod` 形式接受 props 并返回 HTML 字符串。例如 `Atoms.button`（第 131-137 行）接受 text、variant、size 三个参数，按 variant 选择 primary/secondary 两种渲染路径，按 size 选择 sm/md/lg 三种尺寸映射。`Layouts`（第 168 行起）提供 hero、grid、stats 等布局模板，可自由组合原子。这一"原子+布局"的双层架构使页面装配成为字符串拼接操作，零 LLM 介入。

## 8.3 page_assembler 依赖求解

`page_assembler.py` 第 173-200 行的 `DependencyResolver` 类承担组件依赖求解。`__init__`（第 174-178 行）加载数据库并初始化 dependencies/conflicts/dependency_tree 三个字典。`analyze_component_dependencies`（第 187 行起）按 URI 解析组件 category 与 name，输出 requires 与 conflicts_with 列表。例如 `sections/pricing_template_01` 的 requires 包括 `["navbar", "hero", "card"]`（第 198-201 行），conflicts_with 检测同框架互斥（如同时使用 react 与 vue）。

依赖求解的范式意义在于：它把"页面装配"从"线性拼接"重构为"依赖图拓扑排序"。这与 `harness.py` 推理层的 `DependencyAnalyzer` 共享同一抽象——子任务依赖图与组件依赖图是同构问题。这一同构性使 LAAP 的"任务-代码"映射具备数学一致性：一个子任务图的拓扑序对应一个组件装配序，验证层可同时审计两层的依赖完整性。

`page_assembler.py` 第 7-170 行的 `THEME_PRESETS` 还定义了另一套 6 主题预设（dark_flagship/minimal_white/ocean_blue/forest_green/sunset_orange/midnight_purple），与 `harness_composer.py` 的 7 主题形成互补。两套主题系统的共存反映了 LAAP 的"多主题生态"理念——不同装配器可使用不同主题，但都通过 CSS 变量协议保持一致性。这种"协议统一、实现多样"的设计是 LAAP 工程哲学的典型体现。

## 8.4 visual_replicator

`visual_replicator.py` 第 1-14 行的模块文档给出了视觉复刻引擎的工作流程：图片/视频 → 风格分析 → 匹配 → 合成 → 输出，全程零 Token。`VisualReplicator` 类（第 65 行起）的 `replicate_from_images`（第 72-117 行）是核心入口：

1. **analyze**（第 86 行）：调用 `VisualStyleAnalyzer` 提取 colors/typography/spacing/layout/dominant_style/color_harmony/typography_rhythm/complexity 八维分析结果；第 89-90 行记录 images_analyzed 与 colors_extracted；
2. **match**（第 94 行）：调用 `MatchingEngine`（第 5 章详述）按分析结果匹配最佳组件库，第 96 行取 `matches[0]["name"]` 作为 best_match；
3. **generate**（第 100 行）：调用 `_generate_code` 生成完整网站或应用代码，返回 files 列表，第 102 行记录 files_generated。

每一步都以 `step = {"name": ..., "status": "running"}` 字典记录状态，第 84-87 行的 try/except 保证任何步骤失败都会把 status 置为 "failed" 并记录 error。这一细粒度的步骤追踪使视觉复刻的全流程可观测、可调试。`replicate_from_video`（第 118-150 行）则先把视频抽帧（`_extract_frames_from_video`），再走与图片相同的 analyze→match→generate 流程。`_calculate_token_savings`（第 107 行）则给出每次复刻的 Token 节省量。

`VisualReplicaSpec` 数据类（第 49-62 行）承载复刻规格：source_type、source_path、colors、typography、spacing、layout、dominant_style、color_harmony、typography_rhythm、complexity、component_selections、output_type 十二个字段。这一规格的范式意义在于：它把"视觉风格"从"主观描述"重构为"可量化数值"，使视觉复刻可被静态审计而非依赖主观判断。

整个管线的范式特征是"分析-匹配-生成"三段式，与端到端生成式 v0.dev/bolt.new 的"prompt→代码"单段式形成根本性对比。

## 8.5 资产自增殖闭环

把反编译、装配、复刻三件套组合，LAAP 形成了资产自增殖闭环（AF-020、AF-035）：

1. **爬取**：web_crawler 抓取网页，产出 `CrawlResult`；
2. **反编译**：`harness_decompiler` 把 CrawlResult 解构为 `DecompileResult`，提取设计令牌、检测组件、注册到 HEPRegistry；
3. **入库**：HEP 组件以 CLP URI 寻址、SHA-256 哈希验证，进入 `laap_harness_database.json`（31 库 / 206 组件，AF-031）；
4. **正向装配**：`harness_composer` 接收 Spec JSON，从数据库匹配组件，按 `DependencyResolver` 拓扑序拼接为页面；
5. **复刻**：`visual_replicator` 接收图片/视频，分析风格后调用 MatchingEngine 匹配已有资产，未命中则启动反编译补充。

这一闭环的范式意义在于：它把"代码资产"从"人工编写"重构为"系统自增殖"。每抓取一个新网页，LAAP 就把它的设计令牌与组件结构吸收进资产库；下次遇到相似设计时，直接从资产库匹配装配，无需重新生成。这与 v0.dev/bolt.new 的"每次从零生成"形成根本对比——LAAP 的资产库随使用增长，生成质量与速度随之提升；而 v0.dev/bolt.new 的生成质量永远受限于 LLM 的固定能力。

更深层的，资产自增殖闭环把"学习"从"模型训练"重构为"资产积累"。传统 AI 系统通过梯度下降更新权重来"学习"，每次学习都需要大量样本与计算资源；LAAP 通过反编译入库来"学习"，每次学习只需要一次网页抓取与零 Token 解析。这一"学习"范式的根本性转换，是 LAAP 对"缩放定律"（术语表第 59 条）的范式挑战——后者要求"更多数据 + 更大模型"，前者要求"更多资产 + 更广匹配"。

## 8.6 与 v0.dev/bolt.new/lovable.dev 对比

| 维度 | LAAP 三件套 | v0.dev | bolt.new | lovable.dev |
|------|------------|--------|----------|-------------|
| 范式 | 反编译-入库-装配（匹配+装配） | 端到端生成 | 端到端生成 | 端到端生成 |
| Token 消耗 | 资产充足时 0（节省 98.2%） | 10k-100k/页 | 10k-100k/页 | 10k-100k/页 |
| 生成速度 | 57× | 1× | 1× | 1× |
| σ 稳定性 | ≈3（5× 稳定） | ≈15 | ≈15 | ≈15 |
| 资产复利 | 是（每次复刻扩充资产库） | 否 | 否 | 否 |
| 风格漂移 | 工程化主题派生 | LLM 隐式 | LLM 隐式 | LLM 隐式 |
| 视觉复刻 | 原生支持（图片+视频） | prompt 描述 | prompt 描述 | prompt 描述 |
| 跨端热迁移 | < 2 秒 | 无 | 无 | 无 |
| 资产可审计 | SHA-256 + CLP URI | 无 | 无 | 无 |
| 演化曲线 | 超线性（资产复利） | 线性（缩放定律） | 线性 | 线性 |
| 边际成本 | 随使用下降 | 恒定 | 恒定 | 恒定 |

此表的对比意义不止于性能数字，更在于揭示了两种范式的"演化曲线"差异：v0.dev/bolt.new/lovable.dev 的能力曲线随 LLM 缩放定律线性增长，但每次生成仍需支付全量 Token 成本；LAAP 的能力曲线随资产库增长超线性提升，且资产充足时趋近零 Token。这是"架构学派"（AF-029、AF-030）对"模型学派"的根本性范式挑战。

## 8.7 配图引用

（见图 6：反编译-装配-复刻三件套数据流图——展示 CrawlResult → DesignTokenExtractor → HTMLComponentDetector → HEPRegistry → MatchingEngine → HarnessComposer 的完整数据流向，标注每一步的零 Token 特征与执行时间。）

（见图 14：资产自增殖闭环图——展示"爬取→反编译→入库→正向装配→复刻"的闭环结构，标注资产库随使用增长的复利效应，以及与 v0.dev 线性消耗模型的对比。图中应突出"资产库随使用增长"的超线性曲线与 v0.dev 恒定成本线的交叉点，即 LAAP 范式优势的临界点。）

---

综上，第 5 至 8 章从算法、架构、协议、工具链四个维度完成了对 LAAP ARIS-Harness 整合范式的系统审计。倒排索引的 O(log n) 查询、七层认知架构的硬编码管线、CLP 协议的 6 级粒度与 SHA-256 寻址、三件套的资产自增殖闭环，共同构成了"匹配-装配"范式替代"端到端生成"范式的工程证据。下文第 9 章将转入 MeMo 记忆即模型范式的审计，第 10 章转入 CognitiveBus 频率失配处理，进一步展开整合范式的认知工程全貌。
