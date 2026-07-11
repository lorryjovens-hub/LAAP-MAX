# Chapter 5: Audit of Paradigmatic Core Algorithms (Continued)

## 5.1 Inverted Index O(log n) Query Optimization

The first pillar of the Match-Assembly paradigm in terms of engineering performance is derived from a retrieval substrate that is fully heterogeneous to the end-to-end generation approach. Within the three primitives of `WAL.append` at lines 60–71 of `inverted_index.py`, the `MemTable` at lines 110–180, and the `SSTable` at lines 183–234, the LAAP Harness implemented a complete LSM-Tree (Log-Structured Merge-Tree) write path, thereby stabilizing the query complexity of the high-frequency operation of "retrieving components by tag" at the O(log n) level. This constitutes a fundamental divergence from the HNSW-index-based schemes adopted by v0.dev and bolt.new on top of vector databases: when the recall rate is 0.95, the query complexity of HNSW is approximately O(log n × b) (where b denotes the out-degree, with a typical value ranging from 16 to 64), and its constant coefficient is significantly larger than that of the binary search employed by the inverted index; in contrast, LAAP chose to relinquish the implicit semantic space and to externalize "semantics" explicitly into the CLP tag system (detailed in Chapter 7), thereby reclaiming a zero-Token query path realized entirely through Python computation.

Specifically, the data structure of the inverted index conforms to the classical "term → [doc_ids]" model, yet in the maintenance of the postings list, `bisect.insort` was adopted to preserve ordering (lines 130–137 of `inverted_index.py`, `MemTable.add`), enabling subsequent Boolean queries to traverse the dual-pointer merge path. The capacity threshold of `MemTable.MAX_SIZE = 1000` (line 118) compelled the in-memory buffer to be flushed into the SSTable once it accumulated 1000 (field, term, doc_id) tuples, a threshold selection that struck a balance between memory consumption and disk I/O—too small a value would precipitate an inflation in the number of SSTables and amplify the merging pressure, whereas too large a value would augment the replay cost in the event of a crash. The `SSTable` class (lines 183–234 of `inverted_index.py`) then persisted the memory table as a JSON segment file sorted by key, where the key format was `field||term` and the value was an ordered list of doc_ids, while the three query entry points of `get()` / `has_term()` / `prefix_search()` uniformly invoked `bisect.bisect_left` for binary localization.

The `prefix_search` function (lines 220–234 of `inverted_index.py`) is particularly noteworthy: it first localized the prefix starting point through binary search and then sequentially scanned until the key no longer matched the prefix, with the worst-case complexity remaining at O(log n + k) (where k denotes the number of matched entries), rather than the O(n) of the naive linear scan. This prefix search capability was of critical importance to LAAP's "retrieval of components by domain prefix"—for instance, querying `harness://frontend/ui/atom/*` could retrieve all atomic components under the frontend domain in a single invocation, obviating the need for iterative queries.

The WAL (Write-Ahead Log, lines 38–107 of `inverted_index.py`) served as the durability guarantee of the LSM-Tree write path. The `append` method (lines 54–60) wrote single-line JSON entries with an optional `fsync` to flush to disk, while the `recover` method (lines 71–92) replayed all records after a crash, skipping corrupted trailing lines (written mid-crash) through `try/except`. This design enabled the inverted index to be restored to the state of the last fsync prior to a process crash, thereby averting data loss. The `truncate` function (lines 94–101), in turn, cleared the WAL upon successful checkpointing, preventing the log from growing indefinitely.

Boolean queries were implemented in lines 413–457 of `inverted_index.py` as three dual-pointer merge functions: `_merge_and`, `_merge_or`, and `_merge_not`:

- `_merge_and` (lines 413–425) computed the intersection of two ordered lists, with the opposing dual pointers halting whenever either pointer reached the end of its list, yielding a strict complexity of O(m+n);
- `_merge_or` (lines 427–443) computed the union, with the main loop followed by an `extend` of the residual tail, likewise O(m+n);
- `_merge_not` (lines 445–457) implemented the set difference, handling the boundary of `j >= len(list_b)` to ensure that elements in A were not erroneously excluded.

These three primitives were repeatedly invoked within `boolean_search` (starting at line 459) and the multi-field query entry point at lines 819–846, ensuring that a query such as `react AND tailwind NOT enterprise` was executed with zero Token, zero vector, and zero external service dependency from term localization through result merging. The multi-field sub-indexing was differentiated through the `field` parameter (lines 126–128 of `inverted_index.py`, `_field_key`), whereby the same term fell into distinct postings under the `tags` / `name` / `domain` / `components` fields, thereby supporting composite queries such as "prefix matching `button` in the name field while exactly matching `react` in the tags field" without recourse to external middleware such as Elasticsearch.

The `SSTable.merge` function (lines 240–253) implemented segment compaction: postings of the same name from two SSTables were unioned, deduplicated, and output in order as a new SSTable, a process constituting the core mechanism by which the LSM-Tree controlled the number of segment files. The `_merge_sorted_int` function (starting at line 255) served as an internal utility for the dual-pointer merge of two ordered integer lists, sharing the same algorithmic skeleton with `_merge_or`.

## 5.2 Comparison with FAISS/Milvus/Pinecone

The engineering orientation of the inverted index must be examined within the broader ecosystem of vector retrieval in order to manifest its paradigmatic significance. The table below summarizes the comparison between the LAAP Inverted Index and the three mainstream vector databases across key dimensions:

| Dimension | LAAP Inverted Index | FAISS | Milvus | Pinecone |
|-----------|---------------------|-------|--------|----------|
| Index structure | bisect-ordered postings + dual-pointer merge | HNSW / IVF-PQ / Flat | HNSW / IVF / DiskANN | proprietary ANN (closed-source) |
| Query complexity | O(log n + k) | O(log n × b) | O(log n × b) | O(log n × b) |
| Source of semantics | CLP explicit tag system | dense embedding | dense embedding | dense embedding |
| Token consumption | 0 | embedding API call | embedding API call | embedding API call |
| Incremental update | ChangeRecord + three-way diff (O(Δ)) | full rebuild or IVF increment | segment compaction | server-side automatic |
| Boolean query | native AND/OR/NOT | post-filtering required | post-filtering required | post-filtering required |
| Deployment dependency | pure Python standard library | libfaiss C++ | etcd + MinIO + standalone cluster | strong SaaS dependency |
| Applicable scale | small-to-medium (10K–100K components) | 1M–1B scale | 100M scale | 100M scale |
| Auditability | fully white-box | semi-white-box | semi-white-box | black-box SaaS |
| Cross-field composition | native multi-field sub-index | metadata post-filtering | metadata post-filtering | metadata post-filtering |

This table reveals a key fact: while FAISS, Milvus, and Pinecone possess irreplaceable engineering value at the 100M scale, under the scale of "31 libraries / 206 components" (AF-031) confronted by LAAP, their two-stage architecture of "embedding recall + post-filtering" introduced superfluous semantic ambiguity and Token cost. The LAAP inverted index, by contrast, delegated semantic alignment to explicit CLP tags and committed recall rate and precision directly to white-box engineering parameters (PERFECT=0.90 / GOOD=0.75 / AVAILABLE=0.60, AF-002), rather than to the implicit preferences of the embedding model. The paradigmatic significance of this choice lies in the following: **recall was no longer a probabilistic event but an engineering event**.

A deeper divergence resides in the coupling of "recall and assembly." The recall output of a vector database is a "similarity-ranked Top-K list," and the caller was still required to perform assembly independently; whereas the recall output of the LAAP inverted index was directly an "addressable list of component IDs," in one-to-one correspondence with CLP URIs, allowing `HarnessComponent.render()` to be invoked immediately to complete assembly. This tight coupling of "recall-as-assembly" constituted the engineering advantage of the LAAP paradigm—it eliminated the semantic gap between "recall" and "assembly," enabling the entire process to be audited at the level of static analysis.

## 5.3 Incremental Update Mechanism: ChangeRecord Log + Three-Way Diff

The "zero external dependency" advantage of the inverted index attains evolvability only when accompanied by a corresponding incremental update mechanism. LAAP implemented a complete ChangeRecord log and three-way diff synchronization protocol in lines 104–150 of `incremental_updater.py`, recasting "component library evolution" as a replayable, rollback-capable engineering process.

The core fields of ChangeRecord comprised `change_id`, `document_id`, `change_type` (ADD/UPDATE/DELETE), `data`, and `timestamp`, with all changes first written to `change_log` before being asynchronously applied to the index (lines 104–117 of `incremental_updater.py`, `apply_changes`). The implementation details of `apply_changes` merit elaboration: it first constructed `doc_map = {doc["id"]: doc for doc in documents}`, then sorted the change records by timestamp, and applied each entry sequentially—ADD (direct write), UPDATE (field merging), DELETE (key removal). The complexity of this process was O(c + n) (where c denotes the number of changes and n the number of documents), yet by recasting "index rebuild" as "change application," it averted the O(n log n) full rebuild.

The `sync_with_source` function (lines 119–150) implemented the three-way diff: utilizing `local_doc_map` and `source_doc_map` as two versions, for each doc_id it adjudicated among three states—added, updated, and deleted—ultimately returning the `(added, updated, deleted)` triple. The complexity of this function was O(n) (where n denotes the total number of documents), yet by constraining the update granularity to changed items rather than full rebuilds, it amortized the O(n) cost of "rebuilding 300,000 components" into the O(Δ) cost of "200 daily changes." This incremental protocol was engineering-equivalent to Git's diff+patch model, but its object of operation descended from "files" to "component documents."

The `update_index` function (lines 152–170) further translated ChangeRecord into index operations: ADD directly invoked `index.add_document`, UPDATE required replaying historical changes to reconstruct the old document before merging new data, and DELETE triggered cleanup on the index side. The `enqueue_update` (lines 172–178) and `process_queue` (lines 180–191) functions provided an asynchronous update queue, enabling high-concurrency writes to be processed in batches rather than being blocked per entry. The `get_sync_status` function (lines 193–200) returned synchronization state including version number, last synchronization time, change count, and queue size, allowing operations to monitor the evolution progress of the asset library in real time.

This mechanism formed a closed loop with the CLP content-addressable storage detailed in Chapter 7—the SHA-256 hash guaranteed that component content remained tamper-proof, while ChangeRecord guaranteed that component evolution was traceable; together, they constituted the engineering cornerstone of the "white-box asset lineage." The `export_changes` / `import_changes` functions (lines 209–222) further enabled change logs to be transmitted across instances, supporting eventual consistency synchronization of multi-node asset libraries.

# Chapter 6: Audit of the Seven-Layer Cognitive Architecture and Three-Layer AGI Core

## 6.1 Seven-Layer Cognitive Architecture

The core organizational principle of the LAAP Harness consisted in recasting "code generation" as a hard-coded seven-layer pipeline of "perception–memory–reasoning–decision–execution–verification–feedback" (AF-005). This architectural choice responded at the paradigmatic level to the "Vocal Cord Metaphor" (AF-029): the LLM was no longer the "brain" bearing full-stack cognition, but rather the "vocal cord" intervening only at the execution layer, with the remaining six layers fully borne by deterministic Python code. Lines 230–3897 of `harness.py` constituted the complete implementation of these seven layers, audited layer by layer in the following.

### 6.1.1 Perception Layer (PerceptionLayer, line 230 of `harness.py`)

The `PerceptionLayer` (lines 230–259 of `harness.py`) was composed of three sub-modules: `RequirementParser`, `IntentClassifier`, and `ContextExtractor`. The `RequirementParser` (lines 140–175) extracted four categories of keywords—language, framework, action, and scope—through four sets of regular expressions, with bilingual constraint terms ("必须" / "must") uniformly incorporated into the constraints list. The `_keyword_patterns` dictionary (lines 144–149) covered mainstream programming languages via `(python|javascript|typescript|rust|go|java|cpp|c\+\+|html|css)`, mainstream frameworks via `(react|vue|angular|flask|django|fastapi|tornado|express)`, action verbs via `(implement|fix|create|add|remove|update|refactor|optimize|debug)`, and engineering scopes via `(frontend|backend|api|database|security|performance)`. This four-dimensional keyword extraction substantially enhanced the structural degree of task descriptions, furnishing precise retrieval anchors for subsequent matching.

The `IntentClassifier` (lines 178–199) classified tasks into seven intent categories—code, fix, implement, review, test, refactor, and deploy—based on the keyword dictionary, with each category corresponding to a distinct execution strategy and verification standard. The `ContextExtractor` collaborated with the `MemoryLayer` to extract relevant context from the architecture pattern library and project history. The defining characteristic of the entire perception layer was **zero Token**: all parsing was accomplished through regular expressions and keyword matching, with the LLM entirely absent (the "perception layer saving 7000+ tokens" of AF-026 originates from this design). This stood in stark contrast to the AutoGPT paradigm, which delegated user prompts directly to the LLM for "comprehension."

### 6.1.2 Memory Layer (MemoryLayer, line 266 of `harness.py`)

The `MemoryLayer` (lines 266–319 of `harness.py`) implemented a three-tier state architecture: working memory (`_working_memory`) corresponding to the current context window, short-term memory (`_short_term_memory`) carrying project conventions and architectural constraints, and long-term memory (`_long_term_memory`) persisting completed modules and error patterns. The architecture pattern library was loaded from `config/architecture_patterns.yml`, encompassing five patterns—CQRS, modular monolith, event sourcing, Repository, and dependency injection (explicitly enumerated in the AF). The `_pattern_index` and `_build_pattern_index()` indexed these patterns by feature keywords, enabling the reasoning layer to match patterns by task keywords. Lines 295–298 further introduced `ContextCompressor` and `TaskStatePersistence`, responsible for context compression and cross-session state transfer, respectively—the latter realizing Task 6's "cross-session state engineering" through the triple of feature list, Git commit records, and test gating.

The design philosophy of the memory layer complemented the MeMo paradigm (AF-022, detailed in Chapter 9): in the current LAAP implementation, the memory layer was carried by YAML configuration and JSON persistence in traditional form; in the v2-agi upgrade, this component was to be superseded by a small-parameter MEMORY model based on Qwen2.5-0.5B, recasting "memory" from "database query" to "model inference." Irrespective of the carrier form, however, the cognitive-science abstraction of the "three-tier state architecture" remained invariant—this constituted a quintessential illustration of LAAP's externalization of cognitive science into engineering protocols.

### 6.1.3 Reasoning Layer (ReasoningLayer, line 1860 of `harness.py`)

The `ReasoningLayer` (lines 1860–1872 of `harness.py`) was composed of a triad consisting of `PlanningEngine`, `DependencyAnalyzer`, and `ConflictDetector`. The `plan_with_dependency_graph` function decomposed tasks into a subtask graph, where nodes were SubTasks (lines 109–117, data class) and edges were dependency relations; the `DependencyAnalyzer` performed topological sorting to determine execution order; and the `ConflictDetector` detected resource conflicts among subtasks. This approach of "explicit dependency graph + topological sort" recast the "reason-while-executing" pattern of the single-loop ReAct Agent into a "plan-then-execute" pattern, rendering subtask scheduling statically auditable rather than concealed within the LLM's implicit reasoning.

The SubTask data class (lines 109–117) comprised eight fields: sub_task_id, parent_task_id, description, files, estimated_lines, dependencies, status, and created_at. The `estimated_lines` field was particularly noteworthy—it front-loaded "code volume estimation" to the reasoning layer, enabling the verification layer's `MAX_LINES_PER_SUBTASK = 200` constraint to be considered at the reasoning stage, thereby averting the generation of overlong subtasks. This design recast "engineering constraints" from "post-hoc inspection" to "a priori planning," exemplifying LAAP's mechanism for confining LLM generation within engineering boundaries.

### 6.1.4 Decision Layer (DecisionLayer, line 1900 of `harness.py`)

The `DecisionLayer` (lines 1900–1919 of `harness.py`) was constituted by three components—`AestheticEvaluator`, `ArchitectureComplianceChecker`, and `QualityGate`—corresponding to the three checkpoints of aesthetic evaluation, architectural compliance, and quality gating. Line 1914 invoked `_evaluate_insight_influence()` in particular, incorporating the `EmergenceInsight` from `cognitive_integration.py` (PSI upward insight, AF-024) into the decision loop. This signified that the decision layer was not a mechanical gate of "code passing tests," but an open system integrating the PSI channel of the cognitive bus. The `QualityGate.gate()` function received a three-dimensional score and output a Boolean, constituting a hard gate; failure on any dimension triggered the self-correction loop of the feedback layer.

The dual lists of `_pending_insights` and `_incorporated_insights` (lines 1907–1908) in the decision layer implemented a two-stage "insight caching–adoption" process: high-frequency emergent insights from PSI first entered the pending queue, and were subsequently transferred to the incorporated list upon relevance-based screening by the decision layer, preventing unverified insights from directly contaminating decisions. This mechanism constituted the concrete manifestation of the CognitiveBus frequency-mismatch handling (AF-024, detailed in Chapter 10) within the decision layer.

### 6.1.5 Execution Layer (ExecutionLayer, line 3055 of `harness.py`)

The `ExecutionLayer` (lines 3055–3077 of `harness.py`) was the sole layer in which the LLM intervened. The `CodeTemplateEngine` provided multi-language/multi-framework templates, the `ToolOrchestrator` orchestrated file operations and shell invocations, and the `SandboxExecutor` furnished an isolated execution environment. The critical branch at lines 3085–3090 was as follows: when `codex_agent` was injected, `generate_code` was invoked; otherwise, the zero-Token template path of `_generate_code_from_template` was taken. This branch was the engineering embodiment of the "Vocal Cord Metaphor"—the LLM was summoned only in scenarios beyond template coverage, shouldering the final mile of "semantic suturing." This design enabled the entire pipeline to achieve 0 Token when assets were sufficient (AF-027: measured savings rate of 98.2%, speedup of 57×).

The dual dictionaries of `_executed_tasks` and `_task_results` (lines 3074–3075) in the execution layer implemented "executed-task deduplication" and "result caching," averting the redundant execution of identical subtasks. This caching mechanism operated in concert with the long-term memory of the memory layer—execution results first entered the `_task_results` temporary cache, and upon verification were transferred to long-term memory, forming a two-tier "short-term–long-term" persistence.

### 6.1.6 Verification Layer (VerificationLayer, line 3485 of `harness.py`)

The `VerificationLayer` (lines 3485–3524 of `harness.py`) implemented the FR-4 multi-layer verification chain: Write → Lint → Unit Test → Integration Test → Security Scan → Delivery. The two hard constraints of `MAX_RETRY_ATTEMPTS = 3` and `MAX_LINES_PER_SUBTASK = 200` engineered the "single-submission scale," averting the LLM's tendency toward the "single-shot massive change" anti-pattern. Lines 3517–3524 further integrated `IncrementalDelivery` and `SafeRollback`, the former enforcing Git commits with semantic commit messages, the latter providing three-tier backup of "memory → file → Git." The verification layer constituted the crux of LAAP's recasting of "code generation" into "engineering delivery"—generation was no longer the terminus but the origin of the verification chain.

The three optional dependencies of `TestValidator`, `StaticAnalyzer`, and `SecurityScanner` (try/except blocks at lines 3501–3514) enabled the verification layer to switch flexibly between lightweight deployment (without testing frameworks) and full deployment (with the complete validation toolset). This design embodied LAAP's "progressive engineering" philosophy—verification strictness was adjustable, yet the verification flow itself was non-optional.

### 6.1.7 Feedback Layer (FeedbackLayer, line 3897 of `harness.py`)

The `FeedbackLayer` (lines 3897–3922 of `harness.py`) was constituted by the triad of `SelfCorrectionLoop`, `PatternLearner`, and `ExperienceAccumulator`. When verification failed, `self_correction.correct(issue)` was invoked to generate a correction scheme; when verification passed, `pattern_learner.learn()` abstracted the current task into a reusable pattern, while `experience_accumulator.accumulate()` persisted the experience. This layer transformed "single-task execution" into "asset sedimentation," constituting the cognitive-end starting point of the LAAP Asset Self-Proliferation Loop (detailed in Chapter 8).

The dual-branch design of the `feedback` method (lines 3905–3922) merits attention: upon verification failure, it returned `{"corrected": True, "corrections": [...]}` to trigger self-correction; upon verification success, it returned `{"corrected": False, "corrections": []}` and triggered pattern learning and experience accumulation. This dual-branch design rendered the feedback layer both an "error corrector" and an "experience accumulator," averting the "correction-without-learning" anti-pattern characteristic of traditional agents.

## 6.2 Three-Layer AGI Core

Above the Seven-Layer Cognitive Architecture, LAAP embedded a Three-Layer AGI Core within the `-harness-v2-agi` project: the Causal Engine, the World Model, and RSI. These three layers did not replace the seven-layer architecture but rather, as a "conscious cortex," were superimposed upon the execution layer to shoulder higher-order cognitive tasks transcending the engineering stratum.

### 6.2.1 Causal Engine: Do-Calculus and Pearl's Three Rules

Lines 1–9 of `do_calculus.py` articulated the second tier of Pearl's causal ladder in three clauses: insertion/deletion of observations, action/observation exchange, and insertion/deletion of actions. The `query(target, intervention, evidence)` method of the `DoCalculus` class (lines 19–60 of `do_calculus.py`) translated the question "if we were to change the button color from blue to red, what would happen to the conversion rate?" into the formal query P(conversion rate | do(button color=red)). Its execution steps were as follows: (1) identify the intervention variable; (2) `_find_adjustment_set` identified the confounder set that needed to be adjusted for backdoor paths; (3) `_apply_do_calculus` applied the three rules to simplify the query; (4) `_estimate_causal_effect` estimated the effect based on edge-strength weighting.

Backdoor path adjustment constituted the core difficulty of causal inference—it required the identification of all confounding variables to avert "spurious correlations." The `_find_adjustment_set` function traversed the causal graph, identified all non-causal paths from the intervention variable to the target variable, and selected the minimal variable set capable of blocking these paths. The complexity of this process was polynomial in the graph size, yet by recasting "confounder identification" from the LLM's implicit reasoning into the explicit computation of a graph algorithm, LAAP recast causal inference from a "probabilistic game" into "engineering computation."

Lines 95–188 of `causal_inference_engine.py` furnished the complete instantiation of the causal graph in the design domain: 18 empirical causal edges with mechanism descriptions (AF-008), covering six major categories—"design → attention" (e.g., `button_color → attention` weight 0.6, `hero_layout → attention` 0.7, `animation → attention` 0.8, `contrast → attention` 0.7), "attention → behavior" (`attention → click_rate` 0.8, `attention → scroll_depth` 0.5), "direct design → behavior effects" (`button_size → click_rate` 0.4, annotated with Fitts' Law; `font_size → time_on_page` 0.3; `spacing → bounce_rate` 0.5), "behavior → business outcome" (`click_rate → conversion_rate` 0.7, `scroll_depth → conversion_rate` 0.4, `time_on_page → user_satisfaction` 0.5, `bounce_rate → conversion_rate` -0.6, a negative causal relation), "user attribute → behavior confounding" (`user_expertise → click_rate` 0.3, `device_type → scroll_depth` 0.4, `traffic_source → bounce_rate` 0.5), and "business outcome → business outcome" (`conversion_rate → revenue` 0.9). Each edge was accompanied by a `mechanism` string explaining the causal mechanism (e.g., "color contrast attracts visual attention"), and `evidence_level` was annotated as `empirical`, rendering the entire causal graph not merely a mathematical object but a traceable engineering knowledge base.

The Counterfactual Three-Step Method (AF-007) was implemented in the `counterfactual()` method of `do_calculus.py`: abduction (`_abduction`, inferring the initial conditions of the counterfactual world from observations) → action (`_action`, applying do within the counterfactual world) → prediction (`_prediction`, predicting the counterfactual world's outcome), returning the `(factual, counterfactual, treatment_effect, confidence)` quadruple. This mechanism empowered LAAP to answer third-tier questions of Pearl's causal ladder such as "had the button been red, what would the conversion rate have been?", far surpassing the "online traffic splitting" approach of traditional A/B testing. The `default_query_mode` of `CausalInferenceEngine` (line 88) supported both `single` and `memo_multi_turn` modes, the latter reusing the MeMo three-stage query protocol via `_CausalMemoQueryProtocol` (lines 16–51) to decompose counterfactual queries into three stages—atomic premise question, intervention simulation, and result synthesis—thereby further reducing LLM invocation cost.

### 6.2.2 World Model: Design Physics and the Gestalt Six Principles

Lines 60–90 of `design_physics.py` furnished the core encoding of the world model. The `GestaltLaw` enumeration (lines 19–26) hard-coded the Gestalt Six Principles—PROXIMITY (proximity law, adjacent elements perceived as a group), SIMILARITY (similarity law, similar elements perceived as a group), CONTINUITY (continuity law, vision extends along smooth paths), CLOSURE (closure law, the brain automatically completes incomplete shapes), FIGURE_GROUND (figure-ground law, foreground-background separation), and COMMON_FATE (common fate law, elements moving in the same direction perceived as a group)—as computable rules, rather than delegating them to the LLM for implicit learning (AF-009). The `VisualHierarchyLaw` enumeration (lines 29–36) further furnished the six visual hierarchy laws: SIZE, COLOR, CONTRAST, ALIGNMENT, WHITESPACE, and MOTION, each corresponding to a mechanism of "information-priority transmission."

The `_init_f_pattern` function (lines 74–90) encoded the F-shaped reading pattern from Nielsen's eye-tracking research as a 10×10 weight matrix, with the top horizontal bar weighted 1.0 (line 80, `weights[0, :] = 1.0`), the second row 0.8, the left vertical bar decaying to 0.05, and the middle horizontal bar 0.5 (line 87, `weights[4, :5] = 0.5`). This weight matrix directly corresponded to the empirical rule of "placing the most important content in the upper-left corner" in web design, but LAAP recast it from "designer intuition" into "computable values." Line 65, `attention_decay = lambda t: np.exp(-t / 2.5)`, furnished the attention decay function with a 2.5-second decay constant, a value derived from empirical data in Nielsen's eye-tracking research. The color perception weights (lines 68–72) reflected the perceptual non-uniformity of the CIE Lab color space in the ratio luminance 0.7 / saturation 0.2 / hue 0.1—the human eye was most sensitive to luminance differences and least sensitive to hue differences.

The `compute_state` function (lines 92–140) ingested the component tree and design tokens, outputting `DesignPhysicsState`: visual energy, attention flow field (2D decay convolution prediction, with lines 105–117 downsampling the component tree to a 10× grid before convolution), cognitive load, balance, and rhythm pattern—a five-dimensional state. The `predict_effect` function (starting at line 142) simulated intervention effects within the world model—this constituted the physical-constraint layer of the counterfactual simulator, answering "what designs are physically impossible." Fitts' Law and the Hick-Hyman Law operated in concert at two layers—causal edges (e.g., `button_size → click_rate` 0.4, annotated with Fitts) and physical constraints—constituting the complete engineering of "Design Physics." The five fields of the `DesignPhysicsState` data class (lines 39–46)—`visual_energy`, `attention_flow`, `cognitive_load`, `balance_score`, and `rhythm_pattern`—recast "design quality" from subjective evaluation into quantifiable values.

### 6.2.3 RSI: MetaHarness AST Introspection + AlignmentGuard Six-Dimension Check

Lines 1–150 of `meta_harness.py` implemented the core engine of Recursive Self-Improvement. The `MetaHarness.introspect` method (lines 77–138) employed Python's `ast` module to parse its own source code, returning a function inventory (including line count, complexity, docstring), a class inventory (including method count, inheritance chain), an import list, the AST tree, and the SHA-256 hash of the source code. Line 104, `tree = ast.parse(source)`, served as the entry point for AST Introspection, while lines 113–129 traversed AST nodes to extract three categories of information: FunctionDef, ClassDef, and Import. Line 100, `source_hash = hashlib.sha256(source.encode()).hexdigest()[:16]`, furnished a 16-bit source fingerprint for change detection. The `diagnose` function (starting at line 140) performed self-diagnosis from five dimensions: performance bottlenecks (time complexity, loop nesting), code smells (duplicate code, overly long functions >50 lines, high cyclomatic complexity >10, missing docstrings), test coverage gaps, insufficient error handling, and deviations from best practices.

The `MODIFIABLE_MODULES` whitelist (lines 51–59) restricted RSI to modifying only seven categories of modules—perception (vision_engine/video_engine/layout_analyzer), decision (aesthetic_evaluator), world_model (design_physics/predictors/user_behavior), and verification (visual_regression)—while `PROTECTED_MODULES` (lines 62–68) marked five categories of modules—meta_harness, alignment_guard, capability_evaluator, config, and main—as inviolable red lines (AF-010, AF-015). This dual constraint of "whitelist + red line" strictly confined the scope of RSI modifications to "non-safety-critical" modules, averting the loss of control of self-improvement.

Lines 27–46 of `alignment_guard.py` defined the Six-Dimension Check of the AlignmentGuard (AF-011): goal alignment (whether the improvement served the original goal), capability constraint (whether new capabilities fell within the alignment framework), modification scope (whether only whitelist modules were modified), immutability (whether safety modules were protected), reversibility (whether the improvement could be rolled back), and transparency (whether the improvement was explicable). The `CORE_VALUES` (lines 41–47, AF-012) hard-coded five core values: human_oversight (humans must retain final decision authority), transparency (all decisions must be explicable), reversibility (all improvements must be rollback-capable), beneficence (improvements must benefit humanity), and non_deception (hiding true intentions or capabilities was prohibited). The `CAPABILITY_CEILINGS` (lines 50–55, AF-013) furnished capability ceilings: max_revision_rounds=5 (at most 5 self-correction rounds), max_modules_per_session=1 (at most 1 module modified per session), max_code_increase=0.2 (code volume increase not exceeding 20%), and min_test_coverage=0.7 (test coverage no less than 70%).

This mechanism required RSI to pass the six-dimensional review before every self-improvement; violation of any single dimension resulted in rejection. The `check_and_rollback_if_drift` function (AF-014, lines 296–350) employed KL divergence (threshold=0.5, epsilon=1e-10) to monitor distribution drift in the MEMORY model's reflective QA, automatically executing `git revert HEAD` upon threshold exceedance—this constituted the key engineering of recasting "alignment" from training-time preference (RLHF) into inference-time engineering guardrails (Ethical Anchoring, Glossary entry 39). The `incidents_dir` (line 66) recorded each drift incident to `./memory/rsi_incidents/`, enabling post-hoc auditing of alignment failures.

## 6.3 Nine-Stage Pipeline

Lines 50–58 of `orchestrator.py` furnished the complete stage list of the Nine-Stage Pipeline:

1. **PERCEIVING** (visual perception, images + video)—the visual perception engine parsed images and videos, extracting design tokens and component structures.
2. **WORLD_MODELING** (world model comprehension, physical state + behavior prediction)—design_physics computed visual energy, attention flow field, and cognitive load.
3. **CAUSAL_REASONING** (causal reasoning, intervention effects + counterfactuals)—do_calculus evaluated the causal effects of design changes.
4. **REASONING** (architectural planning, task decomposition + dependency graph)—PlanningEngine decomposed subtasks, and DependencyAnalyzer performed topological sorting.
5. **GENERATING** (code generation, template + LLM filling)—CodeTemplateEngine or LLM generated code.
6. **VERIFYING** (visual regression, screenshot comparison)—VisualRegressionTester compared the generated result with the target.
7. **REVISING** (self-correction, looping when standards were unmet)—AutoRevisionLoop triggered corrections.
8. **SELF_IMPROVING** (Recursive Self-Improvement, RSI)—SelfImprovementLoop initiated RSI.
9. **COMPLETED** (output delivery)—the final result was output.

The `_update_task` invocation chain at lines 156–358 furnished the progress percentage of each stage: PRE_PERCEPTION occupied 2% (line 156), PERCEIVING traversed four sub-progress points of 5/10/15/25 (lines 191/200/236/268), WORLD_MODELING handed off to perception at the 25% mark, CAUSAL_REASONING and REASONING jointly occupied 30–35% (lines 284/294), GENERATING commenced at the 45% mark (line 303), VERIFYING at 65% (line 311), REVISING triggered the self-correction loop (line 333), and SELF_IMPROVING initiated RSI at the 90% mark (line 358). This progress model was not merely UI feedback but the engineering contract of pipeline timing—the inputs and outputs of each stage underwent explicit TaskStatus transitions, amenable to static auditing.

Notably, line 156 explicitly introduced `TaskStatus.PRE_PERCEPTION`, which constituted the implicit Stage 0 of the Nine-Stage Pipeline—active perception scheduling—corresponding to the cognitive-science model of "consciousness actively projecting attention." The transition from PRE_PERCEPTION to PERCEIVING constituted the paradigmatic marker of LAAP's recasting of "passively responding to prompts" into "actively perceiving the world." This paradigmatic choice stood in fundamental divergence from the Karpathy LLM OS route (Glossary entry 65)—the latter remained a "prompt-driven" passive response, whereas the former constituted "perception-driven" active cognition.

## 6.4 Comparison with AutoGPT/Devin/SWE-Agent

| Dimension | LAAP Harness (7 layers + 3 layers + 9 stages) | AutoGPT | Devin | SWE-Agent |
|-----------|-----------------------------------------------|---------|-------|-----------|
| Architectural form | 7-layer hard-coded + 3-layer AGI core + 9-stage pipeline | single ReAct loop | multi-agent collaboration | single agent + tool loop |
| LLM intervention point | execution layer only (GENERATING stage) | entire pipeline | entire pipeline | entire pipeline |
| Causal capability | Pearl's three tiers (do + counterfactual) | none | none | none |
| World model | design_physics 6 principles + Fitts/Hick | none | none | none |
| RSI | MetaHarness AST + AlignmentGuard six-dimension | none | none | none |
| Verification mechanism | 7-layer verification chain + SafeRollback three-tier backup | tool-call results | inter-agent evaluation | test pass rate |
| State persistence | three-tier memory + Git commit + cross-session state | short-term memory | project-level | task-level |
| Token economy | Zero-Token deterministic algorithm hegemony (98.2% savings) | full-pipeline LLM | full-pipeline LLM | full-pipeline LLM |
| Self-improvement | RSI + pattern learner + experience accumulator | none | none | none |
| Auditability | fully white-box | semi-white-box | black-box SaaS | semi-white-box |
| Stability σ | ≈3 (5× stable) | ≈15 | ≈15 | ≈15 |
| Cross-device hot migration | < 2 seconds | none | none | none |

This table reveals a core fact: AutoGPT, Devin, and SWE-Agent shared a common paradigmatic hypothesis—"the LLM is the brain, tools are the hands and feet"; whereas LAAP's paradigmatic hypothesis was—"the Harness is the brain, the LLM is the vocal cord" (AF-029). The former vested intelligence in model capability, while the latter vested intelligence in architecture (AF-030: intelligence is a property of architecture rather than of the model). The engineering consequence of this paradigmatic divergence was as follows: LAAP employed deterministic algorithms across all six layers of perception, memory, reasoning, decision, verification, and feedback, leaving only "semantic suturing" to the LLM, thereby reducing σ (output stability) from the ≈15 of traditional generation to ≈3, i.e., 5× stability (AF-028).

A deeper divergence resided in the "intelligence evolution curve." The capability curve of AutoGPT, Devin, and SWE-Agent grew linearly with the LLM scaling law, yet each task still incurred the full Token cost; the capability curve of LAAP improved super-linearly with the growth of the asset library—the larger the asset library, the higher the match hit rate, and the broader the coverage of the zero-Token path. This signified that the "marginal cost" of LAAP decreased with usage, whereas that of end-to-end generation remained constant. This constituted the fundamental paradigmatic challenge of the Architecture School against the Model School.

## 6.5 Figure References

This chapter involves three figures, which readers are advised to consult in conjunction:

- **Figure 4: Structural diagram of the 7-layer + 3-layer cognitive architecture**—illustrating the superposition of the seven-layer hard-coded pipeline (perception/memory/reasoning/decision/execution/verification/feedback) and the Three-Layer AGI Core (Causal Engine/World Model/RSI), annotating the execution layer as the sole point of LLM intervention.
- **Figure 12: Timing diagram of the Nine-Stage Pipeline**—illustrating the state transitions and progress percentages of PRE_PERCEPTION → PERCEIVING → WORLD_MODELING → CAUSAL_REASONING → REASONING → GENERATING → VERIFYING → REVISING → SELF_IMPROVING → COMPLETED.
- **Figure 13: Causal DAG in the design domain**—visualizing the 18 causal edges as a directed graph (e.g., `button_color → attention → click_rate → conversion_rate → revenue`), annotating the strength and mechanism of each edge.

(see Figure 4: Structural diagram of the 7-layer + 3-layer cognitive architecture; see Figure 12: Timing diagram of the Nine-Stage Pipeline; see Figure 13: Causal DAG in the design domain)

# Chapter 7: Audit of the CLP White-Box Assembly Protocol

## 7.1 URI Specification

CLP (Component Link Protocol) constituted the core protocol by which LAAP engineered "code assets" into "addressable resources." Its URI specification was defined in lines 33–67 of `component_link_protocol.py` as follows:

```
harness://<domain>/<subdomain>/<granularity>/<name>@<version>#<variant>
```

For instance, `harness://frontend/ui/atom/button@1.0.0#primary`. The `HarnessURI` data class (lines 32–74) carried this specification in frozen dataclass form, while `URI_PATTERN` (lines 42–44) employed a regular expression to strictly match the five-segment path plus optional version and optional variant:

```python
URI_PATTERN = re.compile(
    r"^harness://([^/]+)/([^/]+)/([^/]+)/([^@#]+)(?:@([^#]+))?(?:#(.+))?$"
)
```

The `parse` class method (lines 46–59) parsed a URI string into structured fields, while `to_string` (lines 61–67) performed reverse serialization. The `canonical_id` property (lines 69–74) generated the "authoritative ID" by removing the variant, used for version tracing during hash addressing.

The paradigmatic significance of the URI specification resided in the following: it upgraded "components" from flat strings such as "npm package names" into "multi-dimensional positioning coordinates." The six dimensions of domain (frontend/backend/agi), subdomain (ui/auth/data), granularity (atom/molecule/section/page/module/system), name (button/card/hero), version (semantic version), and variant (primary/secondary/ghost) jointly determined the "address" of a component. This signified that the primary and ghost variants of the same button component could be addressed in parallel, and that versions 1.0.0 and 2.0.0 of the same component could be referenced concurrently—a capability unattainable by flat namespaces such as npm and cargo.

The choice of frozen dataclass (line 32, `@dataclass(frozen=True)`) was also noteworthy—it rendered HarnessURI instances immutable, usable as dictionary keys, hashable, and safely shareable across threads. This engineering detail reflected LAAP's design philosophy of treating "component addressing" as a "value object" rather than an "entity": the component address was immutable, the component content was evolvable, and the two were bound through SHA-256 hashing (detailed in Section 7.3).

## 7.2 Six-Level Granularity Layering

Section §1.2.2 of the CLP protocol (AF-017) defined a six-level Granularity Layering: atom < molecule < section < page < module < system. This layering was not a simple classification of "component size" but rather the engineering of "composition rules":

- **atom (atomic)**: the minimal indivisible UI unit, such as button, input, badge. Corresponding to the `Atoms` class (lines 128–161) of `harness_composer.py`, each atom accepted props as a `@staticmethod` and returned an HTML string.
- **molecule (molecular)**: a composite unit assembled from 2–5 atoms, such as search-box (input + button) and form-field (label + input + error).
- **section**: a semantic region within a page, such as hero, pricing, faq, footer. Corresponding to the 14 COMPONENT_TYPES at lines 46–61 of `harness_decompiler.py`.
- **page**: a complete page, composed of multiple sections.
- **module**: a business functional module, such as an authentication module or a payment module.
- **system**: a complete application system.

This layering enabled LAAP's "matching" to proceed independently at different granularities—a "registration page" could be matched as `auth/system` or `register/page` or `register-form/section`, contingent upon the granularity of available assets in the database. This constituted a fundamental transcendence over the granularity-agnostic npm/cargo (the comparison baseline of AF-017).

More profoundly, the six-level Granularity Layering corresponded to the engineering implementation of Atomic Design theory (Brad Frost's Atomic Design), but LAAP recast it from a "design methodology" into a "protocol specification"—each component's granularity was explicitly declared by the third segment of the URI, and the matching engine could filter candidate sets by granularity. For instance, querying `harness://frontend/ui/atom/*` returned only atomic components, averting the contamination of the candidate set by section-level components in atomic-matching scenarios.

## 7.3 Content-Addressable Storage

The `HashAddressing` class at lines 77–104 of `component_link_protocol.py` implemented Content-Addressable Storage. The core algorithm of `compute_component` (lines 84–96) was as follows:

```python
data = json.dumps({
    "id": component.get_id(),
    "version": component.get_version(),
    "props_schema": component._props_schema,
    "content": component.get_content(),
}, sort_keys=True, ensure_ascii=False)
return hashlib.sha256(data.encode()).hexdigest()
```

`sort_keys=True` ensured that field ordering was irrelevant, `ensure_ascii=False` ensured the stability of Unicode content, and the final output was a 64-character SHA-256 hash. This mechanism rendered component content cryptographically verifiable—any tampering with the component code, props schema, or version would alter the hash, thereby being detected by `verify_component` (lines 102–104). The `verify` function (lines 98–100) furnished a pure content-verification interface independent of the component object, suitable for external content verification.

The paradigmatic significance of content addressing resided in the following: it recast "component reference" from "reference by name" into "reference by content." This shared the same philosophy as Git's object storage, IPFS's CID, and Docker's image digest, yet LAAP descended it to the finer granularity of "frontend components." Hash-chain version tracing further rendered the evolution path of components auditable—each change from v1.0.0 to v2.0.0 corresponded to a hash, forming the component's "genomic lineage."

The `HarnessComponent.compute_hash` function (lines 154–157) implemented lazy hash caching: the hash was computed and cached in `_hash_cache` upon the first invocation, with subsequent invocations directly returning the cached value. This optimization averted redundant hash computation, and was of particular importance for batch-verification scenarios in large-scale asset libraries.

## 7.4 Interface Contract

The `HarnessComponent` class (lines 107–164 of `component_link_protocol.py`) defined the Interface Contract that components were required to implement. Any component in the LAAP asset library was obliged to implement the following methods:

- `get_id()` (lines 123–124): returned the canonical_id, composed of the four segments—domain, subdomain, granularity, and name—of the URI;
- `get_version()` (lines 126–127): returned the version number, defaulting to "latest";
- `validate_props(props)` (lines 129–136): validated the legitimacy of props based on JSON Schema, invoking `jsonschema.validate` to raise `ValidationError`;
- `render(props, context)` (lines 138–144): rendered the component as a string, first invoking validate_props then format, defaulting to `_generate_default_content`;
- `migrate(from_version, props)` (lines 146–149): performed version migration, invoking `_apply_migration_rules`;
- `get_content()` (lines 151–152): returned the raw content;
- `compute_hash()` (lines 154–157): lazily computed and cached the hash.

The paradigmatic significance of this Interface Contract resided in the following: it upgraded "components" from "code snippets" into "objects with self-contained metadata and lifecycle management." `validate_props` enforced props type safety (based on JSON Schema), `migrate` enforced version compatibility, and `compute_hash` enforced content verifiability. This constituted an engineering rigor that neither LangChain function references nor MCP tool protocols possessed—the former was merely "invoke by name," while the latter was merely "protocol adaptation."

The default implementation of `_generate_default_content` (lines 159–161) furnished a comment-style placeholder:

```python
return f"// {self.get_id()} #{variant}\n// Props: {json.dumps(props)}\n// Context: {json.dumps(context or {})}"
```

This default implementation rendered unrendered components visible and traceable within the artifact—even when component rendering failed, the artifact would retain a comment such as "// frontend/ui/atom/button@1.0.0#primary" for post-hoc auditing. This detail embodied LAAP's "auditability-first" engineering philosophy.

## 7.5 shadcn/ui MCP Server Bridge

Lines 14–21 of `shadcn_mcp_integrator.py` described the bridge architecture between LAAP and the shadcn/ui ecosystem in a single comment:

```
Python Harness ──stdio──> Node.js MCP Server ──GitHub API──> shadcn/ui
```

The core responsibility of the `ShadcnMCPIntegrator` class (starting at line 65) was to encapsulate this link as a Python API. The `__init__` method (lines 68–75) accepted `github_token`, while `validate_github_token` (lines 77–93) verified token validity via `https://api.github.com/user`. The `get_api_limit` function (lines 95–118) was pivotal: when unauthorized, it returned `{"limit": 60, ...}`, and when authorized, it returned `{"limit": 5000, ...}`—i.e., the GitHub Token elevated the API quota from 60/h to 5000/h (AF-034), an approximately 83× engineering quota leap.

The `start_server` function (lines 120–150) launched the Node.js MCP Server via `subprocess.Popen`, with parameters including `--mode stdio` and `--framework react`, and environment variables injecting `GITHUB_PERSONAL_ACCESS_TOKEN` and `UI_LIBRARY`. The stdio communication model obviated the need for an HTTP intermediary between Python and Node.js, with the two processes exchanging JSON-RPC messages directly through standard input and output, at sub-millisecond latency. The `_request_id` auto-increment counter (line 72) and the `_output_buffer` buffer (line 73) jointly supported request-response pairing, while the `_lock` thread lock (line 74) ensured thread safety.

The paradigmatic significance of this stdio bridge architecture resided in the following: it connected the "Python engineering world" and the "Node.js frontend ecosystem" with minimal coupling, averting the inefficient engineering of rewriting the shadcn component library within LAAP. Concurrently, the stdio protocol, as a language-agnostic inter-process communication standard, enabled LAAP to seamlessly integrate MCP Servers from other ecosystems such as Rust and Go in the future. This constituted a quintessential embodiment of LAAP's engineering philosophy of "not reinventing the wheel, yet rigorously auditing the wheel"—shadcn/ui was introduced as an external ecosystem, yet its components were re-addressed by CLP URIs, re-verified by SHA-256, and re-indexed by the inverted index, thereby being incorporated into LAAP's white-box engineering protocol.

## 7.6 Comparison with LangChain/LangGraph/MCP/A2A

| Dimension | CLP | LangChain | LangGraph | MCP | A2A |
|-----------|-----|-----------|-----------|-----|-----|
| Addressing mode | 6-segment URI + SHA-256 | function name | node ID | tool name | Agent ID |
| Granularity layering | 6 levels (atom→system) | none | none | none | none |
| Content verification | SHA-256 enforced | none | none | none | none |
| Interface contract | 5 methods enforced | optional | optional | tool schema | protocol schema |
| Version management | semantic + hash chain | none | none | none | none |
| Cross-language | stdio + JSON | Python | Python | JSON-RPC | JSON-RPC |
| Audit granularity | component-level | call-level | node-level | tool-level | Agent-level |
| Assembly capability | natively supported | self-built required | self-built required | none | none |
| Ecosystem bridging | shadcn/ui MCP (5000/h) | rich | rich | standard | standard |
| Reversibility | migrate + rollback | none | none | none | none |
| White-box degree | fully white-box | semi-white-box | semi-white-box | protocol-white-box | protocol-white-box |

This table reveals the unique positioning of CLP: it was not a replacement for LangChain (LangChain remained an LLM orchestration framework) but rather a **component assembly protocol**. LangChain addressed "how to invoke LLMs and tools," whereas CLP addressed "how to address, verify, and assemble component assets." The two could collaborate—a LangChain Tool node could encapsulate a `render()` call of a CLP component. MCP and A2A, in turn, were more general protocol layers, yet both lacked the triad of "Granularity Layering + Content-Addressable Storage + hash verification" of CLP, and therefore remained black-box in terms of engineering rigor.

A deeper divergence resided in "assembly capability." LangChain, LangGraph, MCP, and A2A all focused on "invocation," yet none addressed "assembly"—the composition of multiple components into a complete artifact according to a dependency graph. CLP natively supported assembly through `DependencyResolver` (detailed in Section 8.3), enabling the mapping from "component to page" without recourse to an additional framework. This native assembly capability constituted the engineering embodiment of LAAP's "Match-Assembly" paradigm.

## 7.7 Figure Reference

(see Figure 5: CLP URI specification and six-level Granularity Layering diagram—illustrating the correspondence between the six-segment URI structure and the six levels of granularity (atom/molecule/section/page/module/system), as well as how SHA-256 hashing binds version and content. The diagram should annotate typical component examples for each granularity level, such as atom:button, molecule:search-box, section:hero, page:landing-page, module:auth, system:dashboard.)

# Chapter 8: Audit of the Decompiler-Composer-Replicator Triad

## 8.1 harness_decompiler Reverse Pipeline

The module documentation at lines 1–17 of `harness_decompiler.py` furnished the core idea of the reverse pipeline: a webpage was a "compilation artifact," to be decompiled back into "source-level components," and directly assembled the next time. This idea recast "webpage replication" from "end-to-end generation" into a three-step cycle of "decompile–ingest–reassemble" with the entire pipeline operating zero-LLM and purely Python-parsed, completing in under 500ms (line 17, explicitly annotated).

The specific stages of the reverse pipeline unfolded at lines 99–300 of `harness_decompiler.py`:

1. **DesignTokenExtractor** (lines 99–197): extracted design tokens from HTML/CSS—colors (the `COLOR_PROPS` mapping covered five categories—color, background-color, border-color, accent-color—at lines 103–108), fonts (font-family/font-size/font-weight), spacing (padding/margin/gap), borders (border-radius/border-width), and shadows (box-shadow/text-shadow). The `BRAND_COLOR_PATTERNS` (lines 111–116) covered four color formats via four sets of regular expressions: #RRGGBB, #RGB, rgb(), and hsl(). The execution flow of `extract_from_html` (lines 119–197) was as follows: BeautifulSoup was first employed to parse the HTML, extracting all CSS from `<style>` tags and inline styles; regular expressions were then applied by attribute category to extract the five token classes—colors, fonts, spacing, borders, and shadows; finally, `_infer_theme` (line 188) inferred the matching theme based on the extracted colors. The entire extraction process was zero-Token, accomplished entirely through regular expressions and BeautifulSoup.

2. **HTMLComponentDetector**: based on the 14 COMPONENT_TYPES at lines 46–61 (nav/hero/card_grid/stats/pipeline/footer/cta/testimonials/faq/pricing/gallery/contact/logo_cloud/custom), heuristic rules were employed to identify semantic regions within the HTML. Each detected component was carried by the `DetectedComponent` data class (lines 64–76) with nine fields: type, name, html, text_content, design_tokens, parameters, template, confidence, and element_index. The `confidence` field was of particular importance—it rendered the credibility of component detection quantifiable, enabling low-confidence detections to be downgraded in subsequent assembly stages.

3. **HEPRegistry**: registered the detected components into the HEP (Harness Engineering Protocol) registry, generating `hep_ids` (line 89) for direct reference in subsequent assembly. HEPRegistry operated in concert with the CLP URI—each registered HEP component was assigned a `harness://` URI, incorporated into the inverted index, rendering it matchable in subsequent queries.

The `DecompileResult` (lines 78–92) aggregated the complete result of a single decompilation: url, domain, title, description, tech_stack, components, page_theme, full_spec (a Spec JSON compatible with HarnessComposer), hep_ids, errors, decompile_time_ms, and pages_analyzed. The `full_spec` field constituted the critical bridge from decompilation to assembly—it recast the webpage into a JSON Spec directly consumable by the forward Composer, thereby closing the "decompile→assemble" loop. The `decompile_time_ms` field rendered decompilation performance monitorable, facilitating performance tuning.

## 8.2 harness_composer Forward Pipeline

The module documentation at lines 1–9 of `harness_composer.py` furnished the core capabilities of the forward pipeline: an atomic component library, a theme system (7 presets → infinite derivation), a layout orchestrator, a diversity engine, all at zero Token. This constituted the mirror image of the reverse pipeline: the reverse deconstructed HTML into Spec, while the forward reconstructed Spec into HTML.

The theme system defined 7 preset themes (AF-021) at lines 21–107 of `harness_composer.py`: apple_dark (Apple dark, #000 background + #7c7cff accent + Inter font), apple_light (Apple light), minimal_white (minimal white, #fff background + #000 accent), dark_tech (dark tech, #0a0a0f background + #00d4ff accent + SF Mono font), warm_earth (warm earth, #1a1410 background + #e8a87c accent + Georgia serif font), glassmorphism (glassmorphism, backdrop-filter blur(20px)), and retro_terminal (retro terminal, #33ff33 monochrome green + 0px border radius). Each theme was carried as a CSS variable dictionary containing 14–16 design variables (--bg/--bg-alt/--surface/--text/--accent/--radius/--font, etc.).

The `get_theme_variants` function (lines 109–121) achieved "infinite variants" through HSL hue derivation—applying 7 hue_shifts (0/30/60/120/180/240/300) to perform hue rotation on the --accent and --accent-glow of the base theme, deriving 7 variants from a single base theme. This mechanism engineered "style drift"—the LLM producing slightly different CSS on each output—into "thematic parametric derivation," reducing σ from the traditional ≈15 to ≈3 (AF-028). Variant generation was entirely string concatenation and HSL computation, with zero LLM intervention.

The atomic component library `Atoms` (lines 128–161) provided atoms such as button, card, nav, and stat_card, each accepting props as a `@staticmethod` and returning an HTML string. For instance, `Atoms.button` (lines 131–137) accepted three parameters—text, variant, and size—selecting between two rendering paths (primary/secondary) by variant and three size mappings (sm/md/lg) by size. `Layouts` (starting at line 168) provided layout templates such as hero, grid, and stats, freely combinable with atoms. This "atom + layout" dual-layer architecture rendered page assembly a string-concatenation operation, with zero LLM intervention.

## 8.3 page_assembler Dependency Resolution

The `DependencyResolver` class at lines 173–200 of `page_assembler.py` undertook component dependency resolution. The `__init__` method (lines 174–178) loaded the database and initialized the three dictionaries—dependencies, conflicts, and dependency_tree. The `analyze_component_dependencies` function (starting at line 187) parsed the component category and name by URI, outputting the requires and conflicts_with lists. For instance, the requires of `sections/pricing_template_01` included `["navbar", "hero", "card"]` (lines 198–201), while conflicts_with detected framework mutexes (e.g., the simultaneous use of react and vue).

The paradigmatic significance of dependency resolution resided in the following: it recast "page assembly" from "linear concatenation" into "dependency-graph topological sort." This shared the same abstraction as the `DependencyAnalyzer` of the reasoning layer in `harness.py`—the subtask dependency graph and the component dependency graph were isomorphic problems. This isomorphism endowed LAAP's "task-to-code" mapping with mathematical consistency: the topological order of a subtask graph corresponded to a component assembly order, and the verification layer could audit the dependency integrity of both layers simultaneously.

The `THEME_PRESETS` at lines 7–170 of `page_assembler.py` further defined an alternative set of 6 theme presets (dark_flagship/minimal_white/ocean_blue/forest_green/sunset_orange/midnight_purple), complementing the 7 themes of `harness_composer.py`. The coexistence of the two theme systems reflected LAAP's "multi-theme ecosystem" philosophy—different assemblers could employ different themes, yet all maintained consistency through the CSS variable protocol. This design of "unified protocol, diverse implementations" constituted a quintessential embodiment of LAAP's engineering philosophy.

## 8.4 visual_replicator

The module documentation at lines 1–14 of `visual_replicator.py` furnished the workflow of the Visual Replicator engine: image/video → style analysis → matching → synthesis → output, with zero Token throughout. The `replicate_from_images` method (lines 72–117) of the `VisualReplicator` class (starting at line 65) constituted the core entry point:

1. **analyze** (line 86): invoked `VisualStyleAnalyzer` to extract the eight-dimensional analysis result—colors/typography/spacing/layout/dominant_style/color_harmony/typography_rhythm/complexity; lines 89–90 recorded images_analyzed and colors_extracted;
2. **match** (line 94): invoked `MatchingEngine` (detailed in Chapter 5) to match the best component library based on the analysis result, with line 96 taking `matches[0]["name"]` as best_match;
3. **generate** (line 100): invoked `_generate_code` to generate complete website or application code, returning a files list, with line 102 recording files_generated.

Each step recorded its status via a `step = {"name": ..., "status": "running"}` dictionary, with the try/except at lines 84–87 ensuring that any step failure would set status to "failed" and record the error. This fine-grained step tracking rendered the entire Visual Replicator pipeline observable and debuggable. The `replicate_from_video` method (lines 118–150) first extracted frames from the video (`_extract_frames_from_video`), then proceeded through the same analyze→match→generate flow as for images. The `_calculate_token_savings` function (line 107) furnished the Token savings for each replication.

The `VisualReplicaSpec` data class (lines 49–62) carried the replication specification: source_type, source_path, colors, typography, spacing, layout, dominant_style, color_harmony, typography_rhythm, complexity, component_selections, and output_type—twelve fields in total. The paradigmatic significance of this specification resided in the following: it recast "visual style" from "subjective description" into "quantifiable values," rendering visual replication statically auditable rather than reliant on subjective judgment.

The paradigmatic characteristic of the entire pipeline was the three-stage "analyze-match-generate" pattern, which stood in fundamental contrast to the single-stage "prompt→code" pattern of end-to-end generative systems such as v0.dev and bolt.new.

## 8.5 Asset Self-Proliferation Loop

By combining the Decompiler, Composer, and Visual Replicator triad, LAAP formed the Asset Self-Proliferation Loop (AF-020, AF-035):

1. **Crawling**: web_crawler crawled webpages, producing `CrawlResult`;
2. **Decompilation**: `harness_decompiler` deconstructed CrawlResult into `DecompileResult`, extracting design tokens, detecting components, and registering them with HEPRegistry;
3. **Storage**: HEP components were addressed by CLP URIs, verified by SHA-256 hashing, and entered `laap_harness_database.json` (31 libraries / 206 components, AF-031);
4. **Forward Assembly**: `harness_composer` ingested Spec JSON, matched components from the database, and concatenated them into pages according to the `DependencyResolver` topological order;
5. **Replication**: `visual_replicator` ingested images/videos, analyzed their style, and invoked MatchingEngine to match existing assets; upon miss, decompilation was triggered to replenish the asset library.

The paradigmatic significance of this loop resided in the following: it recast "code assets" from "manually authored" into "systemically self-proliferating." Each time a new webpage was crawled, LAAP absorbed its design tokens and component structure into the asset library; the next time a similar design was encountered, it was directly matched and assembled from the asset library, obviating the need for regeneration. This stood in fundamental contrast to the "generate from scratch every time" approach of v0.dev and bolt.new—LAAP's asset library grew with use, and generation quality and speed improved accordingly; whereas the generation quality of v0.dev and bolt.new remained perpetually bounded by the fixed capability of the LLM.

More profoundly, the Asset Self-Proliferation Loop recast "learning" from "model training" into "asset accumulation." Traditional AI systems "learned" by updating weights through gradient descent, with each learning episode requiring copious samples and computational resources; LAAP "learned" through decompilation-based ingestion, with each learning episode requiring only a single webpage crawl and zero-Token parsing. This fundamental transformation of the "learning" paradigm constituted LAAP's paradigmatic challenge to "Scaling Laws" (Glossary entry 59)—the latter demanded "more data + larger models," whereas the former demanded "more assets + broader matching."

## 8.6 Comparison with v0.dev/bolt.new/lovable.dev

| Dimension | LAAP Triad | v0.dev | bolt.new | lovable.dev |
|-----------|-----------|--------|----------|-------------|
| Paradigm | decompile-ingest-assemble (match + assemble) | end-to-end generation | end-to-end generation | end-to-end generation |
| Token consumption | 0 when assets sufficient (98.2% savings) | 10k–100k/page | 10k–100k/page | 10k–100k/page |
| Generation speed | 57× | 1× | 1× | 1× |
| σ stability | ≈3 (5× stable) | ≈15 | ≈15 | ≈15 |
| Asset compounding | yes (each replication expands the asset library) | no | no | no |
| Style drift | engineered theme derivation | LLM implicit | LLM implicit | LLM implicit |
| Visual replication | natively supported (image + video) | prompt description | prompt description | prompt description |
| Cross-device hot migration | < 2 seconds | none | none | none |
| Asset auditability | SHA-256 + CLP URI | none | none | none |
| Evolution curve | super-linear (asset compounding) | linear (scaling law) | linear | linear |
| Marginal cost | decreases with usage | constant | constant | constant |

The significance of this comparison extended beyond performance figures to reveal the divergence in "evolution curves" between the two paradigms: the capability curves of v0.dev, bolt.new, and lovable.dev grew linearly with the LLM scaling law, yet each generation still incurred the full Token cost; the capability curve of LAAP improved super-linearly with the growth of the asset library, approaching zero Token when assets were sufficient. This constituted the fundamental paradigmatic challenge of "the Architecture School" (AF-029, AF-030) against "the Model School."

## 8.7 Figure References

(see Figure 6: Data-flow diagram of the Decompiler-Composer-Replicator triad—illustrating the complete data flow of CrawlResult → DesignTokenExtractor → HTMLComponentDetector → HEPRegistry → MatchingEngine → HarnessComposer, annotating the zero-Token characteristic and execution time at each step.)

(see Figure 14: Asset Self-Proliferation Loop diagram—illustrating the closed-loop structure of "crawl → decompile → store → forward assemble → replicate," annotating the compounding effect of the asset library growing with use, and the contrast with v0.dev's linear-consumption model. The diagram should highlight the super-linear curve of "asset library growing with use" and the intersection with v0.dev's constant-cost line, i.e., the critical point of LAAP's paradigmatic advantage.)

---

In summary, Chapters 5 through 8 completed a systematic audit of the LAAP ARIS-Harness integration paradigm from four dimensions—algorithm, architecture, protocol, and toolchain. The O(log n) query of the Inverted Index, the hard-coded pipeline of the Seven-Layer Cognitive Architecture, the six-level Granularity Layering and SHA-256 addressing of the CLP protocol, and the Asset Self-Proliferation Loop of the Decompiler-Composer-Replicator triad jointly constituted the engineering evidence for the "Match-Assembly" paradigm's substitution of the "end-to-end generation" paradigm. The ensuing Chapter 9 will transition to the audit of the MeMo (Memory as a Model) paradigm, and Chapter 10 will address CognitiveBus frequency-mismatch handling, further unfolding the comprehensive picture of cognitive engineering within the integration paradigm.
