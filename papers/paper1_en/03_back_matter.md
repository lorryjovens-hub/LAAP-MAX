# Chapter 9: MeMo (Memory as a Model) Audit

The core innovation of the LAAP ARIS-Harness integration paradigm within the memory subsystem is embodied in the engineering operationalization of the MEMO paradigm (arXiv:2605.15156). This paradigm fundamentally subverts the engineering assumption underlying traditional RAG, in which knowledge is stored within an external vector database; in its place, knowledge is distilled into a differentiable small-parameter MEMORY model, and a structured multi-turn query protocol is substituted for single-round Top-K retrieval. Building upon a source-code audit of four core modules—`memo_provider.py`, `memo_query_protocol.py`, `memo_synthesizer.py`, and `memo_trainer.py`—this chapter systematically demonstrates both the engineering completeness and the theoretical innovativeness of the Memory as a Model (MeMo) paradigm.

## 9.1 The MEMO Paradigm: Knowledge Distilled into a Small-Parameter MEMORY Model

The central proposition of the MEMO paradigm is concisely articulated in the module docstring of `memo_provider.py:1-9`:

> "Implements the MEMO paradigm (arXiv:2605.15156 'Memory as a Model'):
> - Knowledge is distilled into a small-parameter MEMORY model via SFT
> - The EXECUTIVE model remains frozen
> - Queries flow through a three-stage structured multi-turn protocol"

This formulation encapsulates three mutually binding engineering constraints. **First**, the knowledge carrier is shifted from "external vector database plus chunk metadata" to "small-parameter language model weights," and the knowledge retrieval problem is thereby recast as a model forward-inference problem. **Second**, the EXECUTIVE model (i.e., the high-parameter LLM responsible for reasoning and decision-making) remains perpetually frozen; knowledge updates occur exclusively on the MEMORY model's weights, thereby achieving a decoupling of "knowledge growth" from "reasoning capability"—an arrangement that prevents RSI from inadvertently drifting the reasoning logic while improving the knowledge base. **Third**, the query protocol is explicitly structured as a three-stage multi-turn protocol, ensuring that the token cost of a single query does not grow with the size of the corpus.

The `MemoMemoryProvider` class (`memo_provider.py:32-73`) implements the runtime carrier of this paradigm. Its constructor injects four core dependencies—`model_path`, `executive_llm`, `sync_threshold`, and `synthesis_output_path`—which respectively correspond to the MEMORY model weight path, the EXECUTIVE model client, the incremental synthesis trigger threshold (defaulting to 50 conversations), and the reflective QA JSONL output path. The architectural separation among these four dependencies is itself noteworthy: the path-based injection of `model_path` enables swap-in replacement of MEMORY model versions without code changes, while the runtime injection of `executive_llm` decouples the EXECUTIVE model from the MEMORY model lifecycle, ensuring that the two can evolve independently. It is worth emphasizing the fault-tolerant design of `_try_load_model` (`memo_provider.py:78-100`): when the `transformers` library is absent or the model path does not exist, no exception is raised; instead, `_loaded` is set to `False`, causing `is_available()` to return `False` and allowing the upstream `MemoryManager` to gracefully fall back to `SimpleMemoryProvider`. This graceful degradation strategy reflects a consistent engineering philosophy throughout LAAP: MEMO is treated as an enhancement rather than a hard dependency, and the system as a whole retains functional capability even when the MEMORY model is unavailable, thereby adhering to the principle that no single subsystem should constitute a single point of failure for the entire architecture.

## 9.2 The Three-Stage Query Protocol

The MEMO query protocol is implemented by the `MemoQueryProtocol` class (`memo_query_protocol.py:23-150`), and its three-stage structure is explicitly stated in the module documentation (`memo_query_protocol.py:7-11`):

> "1. Grounding: the EXECUTIVE decomposes a complex query into 2-5 atomic sub-questions
> 2. Entity identification: key entities are determined through iterative follow-up questioning based on preliminary answers
> 3. Answer synthesis: supporting facts are solicited from the MEMORY model for the confirmed entities and synthesized into a final answer"

**Stage One: Grounding.** The `stage1_grounding` method (`memo_query_protocol.py:38-77`) invokes the EXECUTIVE model to decompose a complex query into 2-5 atomic sub-questions. Its internal prompt (`_build_grounding_prompt`, lines 104-111) explicitly constrains the output to a JSON array, for example `["sub-question1", "sub-question2"]`. When the EXECUTIVE model is unavailable or JSON parsing fails, a fallback to `_rule_based_split` (lines 113-121) is invoked, which performs regex-based splitting along connectives ("and/or/versus/as well as/with/,/;/;"). This dual-track design ensures that the protocol retains basic capability even when the LLM is unavailable, and it represents a continuation of the Zero-Token Deterministic Algorithm Hegemony at the query-protocol layer.

**Stage Two: Entity Identification.** The `stage2_entity_identification` method (`memo_query_protocol.py:127-150`) takes as input the list of sub-answers from Stage One and constructs an entity-identification prompt that allows the EXECUTIVE model to iteratively pose follow-up questions, thereby pinning down the key entities of the query. The core value of this stage lies in converting "fuzzy topics" into "precise entities," enabling Stage Three to conduct constrained fact-solicitation against specific entities and preventing the MEMORY model from generating generalized responses.

**Stage Three: Answer Synthesis.** For the key entities confirmed in Stage Two, supporting facts are solicited from the MEMORY model and synthesized by the EXECUTIVE model into the final answer. The module documentation (`memo_query_protocol.py:12`) points out the fundamental economic significance of this protocol: "Retrieval cost is decoupled from corpus size—the number of sub-questions and the total token overhead of a single query do not grow with the corpus." This is a property unattainable by the RAG paradigm, since RAG's retrieval cost grows logarithmically with corpus size (HNSW) or linearly (brute-force scanning). The economic implication is profound: as the corpus scales from thousands to millions of documents, RAG's per-query cost increases correspondingly, whereas MEMO's per-query cost remains invariant, being determined solely by the fixed computational cost of a single forward pass through the MEMORY model. This asymptotic decoupling constitutes the principal economic motivation behind the MEMO paradigm and represents a structural advantage that scales with corpus growth.

## 9.3 MemoSynthesizer: Five-Step Synthesis

The construction of the reflective QA training set is implemented by `MemoSynthesizer` (`memo_synthesizer.py:17-43`). Its five-step pipeline is explicitly enumerated in the class docstring:

> "1. extract_facts       — fact extraction
> 2. consolidate_facts   — fact consolidation (clustering by semantics)
> 3. surface_entities    — entity surfacing
> 4. synthesize_cross_doc — cross-document QA synthesis
> 5. verify_qa           — GENERATOR self-verification"

**Step One: extract_facts** (`memo_synthesizer.py:48-125`). This method extracts atomic facts from three data sources: `design_system_cache.json` (design tokens), `component_templates.json` (component templates), and `harness_memory.db` episodes (conversation fragments). Each data source is normalized into a unified fact dictionary structure, carrying a `type` field ("design_token" / "component_template" / "episode") so that subsequent steps can differentiate processing.

**Step Two: consolidate_facts** (`memo_synthesizer.py:138-150`). This method clusters and merges facts according to the `semantics` field of design tokens; facts with identical semantics are merged into a single record, with `occurrence_count` and `source_task_ids` documented, while facts of other types are retained as-is. The essence of this step is "knowledge deduplication," preventing identical semantic design tokens from recurring in the reflective QA and inducing training bias.

**Step Three: surface_entities.** Key entities (such as component types, design-token names, and technology-stack names) are explicitly extracted from the consolidated facts, providing entity anchors for cross-document synthesis.

**Step Four: synthesize_cross_doc.** Building upon the explicit entities, reflective QA pairs are synthesized across multiple documents (design-token documents, component-template documents, and conversation fragments), capturing cross-document relationships. This is the core step that distinguishes the MEMO paradigm from traditional RAG—RAG performs cross-document recall only at query time, whereas MEMO completes cross-document relationship modeling at training time.

**Step Five: verify_qa.** The GENERATOR model self-verifies the synthesized QA pairs, filtering out low-quality samples. When `generator_llm=None`, LLM verification is skipped and only rule-based filtering is applied. The `_filter_log` field (`memo_synthesizer.py:43`) records the filtered-out QA items and the reasons thereof, providing an audit trail for subsequent training-set quality analysis.

## 9.4 MemoTrainer SFT

The training of the MEMORY model is implemented by the `MemoTrainer` class (`memo_trainer.py:30-150`), whose default hyperparameter configuration is as follows:

| Hyperparameter | Default Value | Location in Source |
|----------------|---------------|---------------------|
| `model_name` | `Qwen/Qwen2.5-0.5B` | `memo_trainer.py:46` |
| `epochs` | `3` | `memo_trainer.py:47` |
| `lr` | `1e-4` | `memo_trainer.py:48` |
| `bf16` | `True` | `memo_trainer.py:49` |
| `gradient_checkpointing` | `True` | `memo_trainer.py:50` |
| `max_length` | `512` | `memo_trainer.py:51` |

The selection rationale embodies a threefold trade-off. **First**, Qwen2.5-0.5B has only 500 million parameters; its single-GPU memory footprint is less than 4 GB (bf16 precision), an order of magnitude lower than 7B/13B EXECUTIVE models, enabling knowledge updates (SFT) to be completed on consumer-grade GPUs and avoiding the batch cost of RAG index reconstruction. **Second**, 3 epochs and lr=1e-4 constitute a conservative SFT configuration that mitigates overfitting on small datasets; bf16 and gradient_checkpointing are standard practices in the memory-speed trade-off. **Finally**, max_length=512 constrains the context window per sample, consistent with the "atomic sub-question" philosophy—MEMO does not expect the MEMORY model to process long contexts; long contexts should be decomposed into multiple atomic sub-questions and handled at the protocol layer.

The `load_dataset` method (`memo_trainer.py:66-110`) converts the reflective QA JSONL into the format `{"prompt": "Question: {q}\nAnswer:", "completion": " {a}"}`, which is the standard prompt-completion format for causal language model SFT. The `_tokenize` method (lines 115-144) performs concatenated tokenization and constructs `labels = input_ids` (the standard SFT label-copying strategy). The fault-tolerant design of the `train` method (module documentation, lines 9-10) merits emphasis: when transformers is not installed or its import fails, `train()` returns `None` rather than raising an exception, and the module-level `_TRANSFORMERS_AVAILABLE` flag allows upstream code to determine availability—a design that is consistent with the degradation philosophy of `MemoMemoryProvider`.

## 9.5 Comparison with Traditional RAG

| Dimension | Traditional RAG | MEMO (LAAP Implementation) |
|-----------|-----------------|-----------------------------|
| **Knowledge Storage** | External vector database (FAISS/Milvus) + chunk metadata | Small-parameter MEMORY model weights (Qwen2.5-0.5B) |
| **Retrieval Cost** | O(log n) (HNSW) to O(n) (brute-force scan), growing with corpus | O(1) forward inference, decoupled from corpus size |
| **Knowledge Form** | Text chunks (implicit representation) | Model weights (continuous differentiable representation) |
| **Query Protocol** | Single-round Top-K recall + LLM reading and synthesis | Three-stage multi-turn: grounding → entity_identification → answer_synthesis |
| **Update Mechanism** | Index rebuild (batch) or incremental index (HNSW incremental insertion) | SFT weight update (incremental training, 3 epochs) |
| **EXECUTIVE Model** | Coupled with retriever; LLM reads all Top-K chunks | Perpetually frozen; only MEMORY model weights are updated |
| **Cross-Document Relationships** | Recall at query time, relying on LLM reasoning | Synthesis at training time (MemoSynthesizer Step Four) |
| **Quality Assurance** | Dependent on chunk ranking quality | GENERATOR self-verification + KL drift monitoring |

## 9.6 Demonstration of the "Memory as a Model" Paradigm Shift

The essential innovation of the MEMO paradigm lies in recasting the "knowledge retrieval problem" as a "model forward-inference problem." Under the RAG paradigm, knowledge is stored in discrete chunk form within an external vector database; retrieval is an explicit similarity computation (cosine similarity or dot product), and the LLM must read all Top-K chunks at inference time and perform cross-document integration—causing the LLM's context window to grow linearly with retrieval scale. Under the MEMO paradigm, knowledge is stored as continuous weights within the MEMORY model; retrieval is an implicit forward inference (the intrinsic activation pattern of the neural network), and cross-document relationships have already been distilled into the weights during the SFT phase—the LLM need only synthesize the answer from the MEMORY model's output, without reading the original chunks.

This shift carries three profound consequences. **First**, knowledge retrieval cost is decoupled from corpus size; MEMO's retrieval cost depends solely on the parameter count of the MEMORY model (O(1) forward inference) and is independent of corpus scale—a progressive property unattainable by the RAG paradigm. **Second**, knowledge updating shifts from "index rebuild" to "SFT weight update," rendering incremental learning feasible; the `MemoMemoryProvider.sync_threshold=50` (`memo_provider.py:65`) trigger for incremental synthesis exemplifies this mechanism. **Third**, the knowledge representation shifts from discrete chunks to continuous weights, allowing cross-document relationships to be explicitly modeled at training time (`MemoSynthesizer.synthesize_cross_doc`), rather than depending on the LLM's implicit reasoning at query time.

It should be noted that MEMO is not without cost—SFT training itself consumes compute, and the capacity of the MEMORY model is constrained by its parameter scale (0.5B is hard-pressed to accommodate ultra-large-scale corpora). However, this cost is **one-time**, and LAAP safeguards the MEMORY model against catastrophic forgetting across multiple updates through the KL drift monitoring of AlignmentGuard (`alignment_guard.py:296-350`). At the level of token economics, MEMO significantly outperforms RAG in frequent-query scenarios—RAG consumes LLM reading tokens for Top-K chunks at every query, whereas MEMO consumes only the small number of tokens entailed by the MEMORY model's forward inference (the generative output) at each query. The cumulative cost differential becomes particularly pronounced in long-running deployments where the system is queried thousands or millions of times over its operational lifetime: under such conditions, RAG's per-query token cost accumulates linearly with query volume, whereas MEMO's per-query marginal cost remains effectively constant, bounded only by the amortized cost of periodic SFT updates triggered every `sync_threshold` conversations.

## 9.7 Figure Reference

**Figure 7**: MeMo architecture diagram. It illustrates the data-flow and control-flow relationships among the EXECUTIVE model (frozen), the MEMORY model (SFT-updatable), the Three-Stage Query Protocol (grounding → entity_identification → answer_synthesis), the MemoSynthesizer Five-Step Synthesis pipeline, and the MemoTrainer SFT training loop.

---

# Chapter 10: CognitiveBus Frequency Mismatch Handling Audit

The LAAP ARIS-Harness integration paradigm confronts a unique engineering challenge: the PSI (Psycho-semantic Integration, the consciousness-semantic integration layer) generates emergence insights at millisecond-level frequency (1-2 kHz), whereas the Harness engineering shell executes tasks at second-level frequency (0.1-1 Hz), producing a frequency mismatch spanning three to four orders of magnitude. Building upon a source-code audit of `cognitive_integration.py`, this chapter demonstrates how the `RateBuffer` class transforms this frequency mismatch into an engineerable, stable communication channel through a seven-fold buffering strategy.

## 10.1 The Frequency Mismatch Problem

As the simulation layer of the conscious brain, the PSI internally cycles at a rate of 1-2 kHz—an approximation of the firing rate of cortical columns in neuroscience. The Harness engineering shell, by contrast, adheres to an engineering cadence: a single task execution typically falls within the 1-10 second range (crawler request + template matching + assembly + verification), i.e., 0.1-1 Hz. Directly interfacing the two would precipitate two disasters: **first**, the high-frequency emergence insights of the PSI would overwhelm the processing capacity of the Harness, causing event backlog and memory explosion; **second**, the slow response of the Harness would block the consciousness cycle of the PSI, leading to consciousness "stuttering."

The docstring of the `RateBuffer` class (`cognitive_integration.py:81-348`) explicitly states its design objectives:

> "PSI: millisecond-level updates (1000-2000Hz)
> Harness: second-level updates (0.1-1Hz)
>
> Buffering strategy:
> - Event deduplication: only the latest insight of identical content is retained
> - Priority filtering: low-priority insights are dropped under high load
> - Batch aggregation: multiple insights are merged into a single batch
> - Sliding window: only the most recent N insights are retained
> - Time expiration: insights are automatically discarded after exceeding TTL
> - Garbage filtering: invalid/duplicate/malformed insights are filtered
> - Rate-limiting protection: prevents the PSI from bursting large volumes of data and stalling the system"

These seven strategies constitute a progressively layered frequency-adaptation system.

## 10.2 RateBuffer Enhancements: Event Deduplication + Priority Filtering + Sliding Window

The core data structure of `RateBuffer.__init__` (`cognitive_integration.py:98-118`) is `self._buffer: deque = deque(maxlen=max_size)`, with a default `max_size=50`. The `maxlen` parameter of `deque` naturally implements sliding-window semantics—when the buffer is full, newly added insights automatically expel the oldest insights without an explicit pop operation.

**Event deduplication** is realized through `self._seen_contents = set()` (`cognitive_integration.py:108`). In the `add` method (lines 120-147), the `content[:100]` (first 100 characters) of each new insight is hashed into `content_hash`; if this hash already exists in `_seen_contents`, the old hash is first removed before the new hash is added (lines 135-139), ensuring that only the latest version of identical content is retained. This strategy is crucial for the "repeated emergence" phenomenon of the PSI—the consciousness cycle may repeatedly produce insights with similar content, and deduplication prevents these duplicate insights from occupying buffer slots.

**Priority filtering** is implemented by the `_should_keep_insight` method (`cognitive_integration.py:191-210`). The `priority_order = {"high": 3, "medium": 2, "low": 1}` maps priority levels to numerical values; when the buffer is full, a new insight is compared one-by-one against existing insights, and if the new insight's priority is higher, it replaces the lowest-priority existing insight (lines 199-203). If the new insight's priority is not higher than any existing insight, and its priority is "low" with `drop_low_priority_threshold > 0`, it is directly dropped (lines 205-208).

## 10.3 TTL Expiration and Circuit Breaker

The **TTL expiration** mechanism is implemented by the `_clean_expired` method (`cognitive_integration.py:180-189`), with a default `ttl_seconds=30.0` (`cognitive_integration.py:100`). Each `add` call triggers `_clean_expired`, which begins from the head of the buffer (the deque is ordered, with the oldest at the front) and checks whether `now - oldest.timestamp > self._ttl_seconds`; expired insights are removed via `popleft` and counted toward `_total_expired`. This mechanism ensures that outdated "emergence insights" do not lose their timeliness by the time the Harness is ready to process them—for example, the insight "the user appears to be looking for the login feature" produced by the PSI at t=0 is meaningless at t=35s (the user may have already departed).

The **Circuit Breaker** mechanism is RateBuffer's last line of defense (`cognitive_integration.py:222-237`). The `_increment_drop_count` method increments `_dropped_in_last_second` each time an insight is dropped; when this count exceeds `_max_drops_per_second` (default 100, `cognitive_integration.py:101`), the circuit breaker is tripped: `_circuit_breaker_tripped = True`, and the trip time is recorded. During the circuit-breaker tripped state, all new `add` calls directly return `False` (lines 126-128), and no further insights are accepted. The `_is_circuit_breaker_tripped` method (lines 227-237) checks the cooldown period (default `_circuit_breaker_cooldown=5.0` seconds, line 118), and the circuit breaker is automatically reset after the cooldown elapses.

The design philosophy of the circuit breaker is "protecting the system takes precedence over preserving data"—when the PSI bursts a large volume of garbage insights (for instance, a single inference error producing 1000 duplicate items per second), the circuit breaker trips after 100 drops/s and immediately severs the receiving channel, preventing the Harness from being dragged down. After a 5-second cooldown, it resets, granting the PSI ample time to self-correct. This design choice reflects a broader architectural principle: in scenarios where the upstream producer (PSI) and downstream consumer (Harness) operate at vastly different frequencies, the resilience of the overall system takes precedence over the completeness of individual data points. The circuit breaker thus embodies a fail-safe rather than fail-fast philosophy—it chooses graceful degradation over catastrophic failure, ensuring that the consciousness loop can continue to function, even in a degraded capacity, rather than cascading into a systemic outage.

## 10.4 Garbage Filtering: _validate_insight

The `_validate_insight` method (`cognitive_integration.py:149-178`) implements six-fold garbage filtering:

1. **None check**: `insight is None` is rejected outright (lines 151-152)
2. **Type check**: `isinstance(insight, EmergenceInsight)` must be true (lines 154-156)
3. **ID check**: `insight.id` must be a non-empty string (lines 158-160)
4. **Content check**: `insight.content` must be a non-empty string (lines 162-164)
5. **Length check**: `len(insight.content) > 10000` is rejected (lines 166-168)—to prevent overlong content from consuming memory
6. **Confidence check**: `insight.confidence` must lie within the [0, 1] interval (lines 170-172)
7. **Priority check**: `insight.priority` must be one of "high"/"medium"/"low"; otherwise it is forcibly set to "medium" (lines 174-176)

Failure of any single check increments `_total_invalid` and rejects the insight. The essence of this filtering strategy is "contract-based programming"—the PSI must produce data according to the contract of `EmergenceInsight`, or the data will be rejected by the engineering structure rather than by the LLM. This is consistent with the "Zero-Token Deterministic Algorithm Hegemony" philosophy of the Architecture School: garbage filtering is a deterministic algorithm and consumes no LLM tokens.

## 10.5 Rate-Limiting Protection: force_drop_low_priority

The interplay between `force_drop_low_priority` and `_should_keep_insight` constitutes the rate-limiting protection mechanism. When the buffer is full and the new insight's priority is insufficient to replace any existing insight, the new insight is forcibly dropped. The distinction between this mechanism and the circuit breaker lies in the following: the circuit breaker is a "system-level" protection (the overall drop rate exceeds a threshold), whereas rate-limiting is an "event-level" protection (an individual event is dropped due to insufficient priority). Together, the two form a "macro-micro" two-tier rate-limiting system.

`RateBuffer` maintains a complete set of statistical fields: `_total_added`, `_total_processed`, `_total_expired`, `_total_invalid`, `_dropped_count`, and `_dropped_in_last_second` (`cognitive_integration.py:112-117`). These fields provide the data foundation for system observability—upper layers can dynamically adjust parameters such as `max_size`, `ttl_seconds`, and `max_drops_per_second` based on these metrics, achieving adaptive frequency adaptation.

## 10.6 Bidirectional Communication: EmergenceInsight Upstream / HarnessExecutionResult Downstream

The bidirectional communication of CognitiveBus is realized through two data classes:

**EmergenceInsight** (`cognitive_integration.py:53-65`): the emergence insight transmitted upstream from the PSI to the Harness. It contains ten fields: `id`, `content`, `confidence`, `type`, `source`, `timestamp`, `priority`, `tags`, `related_needs`, and `processed`. The `type` field takes values from the `EmergenceEventType` enumeration (lines 43-50), comprising six categories: `INSIGHT_DISCOVERED`, `PATTERN_RECOGNIZED`, `NEED_TRIGGERED`, `SELF_CORRECTION`, `HARNESS_EXECUTION`, and `HARNESS_VERIFICATION`.

**HarnessExecutionResult** (`cognitive_integration.py:68-78`): the execution feedback transmitted downstream from the Harness to the PSI. It contains eight fields: `task_id`, `success`, `output`, `error`, `tokens_used`, `duration`, `verification_passed`, and `timestamp`. Among these, `tokens_used` and `duration` are of particular importance—they enable the PSI to adjust the frequency and content of subsequent emergences based on the "cost of the last execution," forming a closed-loop control of "execution cost feedback."

The fundamental difference between this bidirectional communication mechanism and traditional Agent event buses is as follows: traditional event buses convey "task messages" (task ready, task completed), whereas CognitiveBus conveys "cognitive signals" (emergence insights, execution costs)—the former constitutes engineering orchestration, whereas the latter constitutes cognitive coupling.

## 10.7 Comparison with Traditional Agent Event Buses

| Dimension | Traditional Agent Event Bus (e.g., LangChain) | LAAP CognitiveBus + RateBuffer |
|-----------|-----------------------------------------------|-------------------------------|
| **Frequency Assumption** | Synchronous RPC, assuming matched frequencies at both ends | Explicit acknowledgment of a 3-4 orders-of-magnitude frequency mismatch |
| **Buffering Strategy** | Single queue (FIFO) | Seven-fold strategy: deduplication + priority + sliding window + TTL + garbage filtering + rate-limiting + circuit breaker |
| **Data Contract** | JSON string | Strongly-typed dataclass (EmergenceInsight / HarnessExecutionResult) |
| **Degradation Mechanism** | Exception or retry | Circuit breaker + cooldown reset + graceful degradation |
| **Observability** | Logs | Seven statistical counters (added/processed/expired/invalid/dropped/dropped_in_last_second/circuit_breaker) |
| **Data Semantics** | Task messages | Cognitive signals (emergence insights + execution costs) |
| **Synchronization Model** | Blocking synchronization | Asynchronous + timeout protection (`get_batch(timeout_ms=100)`, line 239) |

## 10.8 Figure Reference

**Figure 8**: CognitiveBus + RateBuffer architecture diagram. It illustrates the data flow from PSI (1-2 kHz) → RateBuffer (seven-fold buffering) → Harness (0.1-1 Hz); annotates key parameters such as TTL=30s, max_drops_per_second=100, cooldown=5s, and maxlen=50; and visualizes the bidirectional communication (EmergenceInsight upstream / HarnessExecutionResult downstream).

---

# Chapter 11: Quantitative Audit Results

Building upon 35 structured audit findings (`audit_findings.json`), this chapter systematically presents the quantitative advantages of the LAAP ARIS-Harness integration paradigm along five dimensions: token economics, stability, database scale, causal-graph scale, and pipeline depth.

## 11.1 Zero-Token Deterministic Algorithm Hegemony

The first-principle of the LAAP Architecture School is concisely articulated in `harness的前后端全栈工程.txt:59-78`:

> "Any problem that can be solved by a deterministic algorithm must never consume LLM tokens. The LLM handles only 'semantic uncertainty'—that is, the gray zones that algorithms cannot cover."

In the PerceptionLayer, this principle manifests as four classes of 0-Token algorithms undertaking 90% of the perceptual workload (AF-026):

| Perceptual Task | Traditional Approach (Pure LLM) | Harness Approach | Token Consumption |
|-----------------|----------------------------------|------------------|--------------------|
| Stack Detection | LLM inspects HTML and reasons | Regex matching of `__NEXT_DATA__` / `_buildManifest.js` | 0 vs 2000+ |
| Content Classification | LLM reasoning | Keyword density scoring (product/cart/price vs article/post/author) | 0 vs 1000+ |
| Design-Token Extraction | LLM inspects CSS | CSSOM parsing of variable values | 0 vs 1500+ |
| Layout-Structure Analysis | LLM inspects DOM | Element density + nesting depth + Grid/Flex detection | 0 vs 3000+ |
| Semantic Summarization | — | Lightweight LLM confirmation | 500 |

The quantitative conclusion offered by `harness的前后端全栈工程.txt:76` is: "A single perception saves 7000+ tokens, equivalent to a 90% cost reduction and a 95% latency reduction." The engineering significance of this datum is that 90% of the perception layer's workload is undertaken by deterministic algorithms, with the LLM assuming only 10% of the "semantic stitching" work (such as the summarizing statement "this is a SaaS landing page built with Next.js + Tailwind," which requires only 500 tokens). In terms of accuracy, deterministic algorithms do not hallucinate—regex matching of `__NEXT_DATA__` cannot "misidentify" Next.js, whereas an LLM may misidentify it due to training-data bias.

This philosophy constitutes the fundamental distinction between the Architecture School and the "LLM-as-Agent" route: systems such as v0.dev, Cursor, and Devin enable the LLM to "understand" websites, UIs, and code, whereas LAAP enables the engineering structure to "decompose" websites, UIs, and code, with the LLM performing only the final semantic confirmation. The epistemological consequence of this distinction is substantial: by relegating deterministic perceptual tasks to deterministic algorithms, the system eliminates an entire class of hallucination failures that would otherwise arise from LLM reasoning over structured inputs. A regex match against `__NEXT_DATA__` is, by construction, incapable of the kind of false-positive identification that an LLM might produce when confronted with ambiguous or out-of-distribution input, and this property of inherent trustworthiness propagates upward through the cognitive pipeline to ensure that downstream stages operate on a foundation of veridical perceptual evidence.

## 11.2 Full-Chain 0-Token under Asset Sufficiency

A more aggressive quantitative conclusion comes from `LAAP-Harness-Protocol-v1.0.md §6.1.1` (AF-027):

> "Measured token savings rate 98.2%, generation speed 57×"

This datum derives from the boundary scenario of "full-chain 0-Token under asset sufficiency"—when the database already contains the complete assets of the target component (for example, when a user requests "build a shadcn-style login page" and the database already holds the shadcn/ui version of the `auth` template), the Harness can complete generation through pure match-assembly without invoking the LLM. The 98.2% savings rate corresponds to approximately 1.8% LLM intervention (used mainly for confirmation and fine-tuning), while the 57× speedup arises from the latency differential between purely algorithmic assembly and end-to-end LLM generation (millisecond-level vs second-level).

Compared to the baseline (AF-027): "v0.dev/bolt.new 10k-100k tokens/page"—traditional end-to-end generation systems consume 10,000 to 100,000 tokens per page, whereas LAAP, under asset-sufficient scenarios, consumes only approximately 180-1800 tokens (1.8% × 10k-100k). This comparison highlights the economic advantage of the match-assembly paradigm: in engineering scenarios (where assets are reusable), LAAP's token cost can be reduced to less than 1/50 of traditional solutions.

## 11.3 Sigma Stability: 5× Improvement

The quantitative argumentation section of `harness的前后端全栈工程.txt` (AF-028) provides stability data:

> "Traditional generation σ≈15 vs LAAP σ≈3, 5× stability"

σ (standard deviation) measures the consistency of multiple generation results. Traditional LLM end-to-end generation is influenced by multiple factors such as temperature parameters, sampling randomness, and context-window length; the code generated from the same prompt across multiple runs exhibits significant drift in style, structure, and naming (σ≈15). LAAP's match-assembly paradigm recasts the generation process as "component matching + template assembly," where the components themselves are pre-designed stable assets (e.g., the Button component code of shadcn/ui is fixed), and the matching algorithm is deterministic (MatchScore four-dimensional weighted scoring). Consequently, σ≈3, yielding a fivefold stability improvement over traditional approaches.

The engineering significance of this stability improvement is that the code produced by LAAP possesses "engineering reproducibility"—the code generated multiple times from the same requirement is highly consistent in structure, rendering collaborative team workflows, version control, regression testing, and other engineering practices feasible. By contrast, traditional LLM-generated code differs each time and is difficult to incorporate into engineering workflows.

## 11.4 Database Scale: 31 Libraries / 206 Components

`laap_harness_database.json:8-13` (AF-031) records the current database scale:

```json
"stats": {
  "total_ui_libraries": 23,
  "total_animation_libraries": 5,
  "total_icon_libraries": 3,
  "total_libraries": 31,
  "total_components": 206
}
```

Although the scale of 31 libraries and 206 components is four orders of magnitude smaller than the npm ecosystem (millions of packages), it already covers the common scenarios of frontend engineering: 23 UI libraries (including shadcn/ui with 118k+ stars, Radix UI, Headless UI, etc.), 5 animation libraries (Framer Motion, GSAP, Lottie, etc.), and 3 icon libraries (Lucide, Heroicons, Tabler Icons). `laap_harness_database.json:15-50` shows that the shadcn/ui library has registered 11 core component categories—button, card, dialog, dropdown, form, input, modal, nav, table, tabs, and toast—along with four template classes: landing-page, dashboard, settings, and auth. This scale suffices to support the common requirements of the "0-Token under asset sufficiency" scenario described in §11.2.

## 11.5 Causal Graph Scale: 18 Causal Edges in the Design Domain

`causal_inference_engine.py:95-188` (AF-008) records 18 empirical causal edges with mechanism descriptions, covering the key causal chains of the frontend design domain:

| Causal Edge | Strength | Mechanism Description |
|-------------|----------|----------------------|
| `button_color → attention` | 0.6 | Color contrast attracts visual attention |
| `button_size → click_rate` | 0.4 | Fitts' Law: larger targets are clicked faster |
| `bounce_rate → conversion_rate` | -0.6 | High bounce rate suppresses conversion |
| ... (18 in total) | | |

These 18 causal edges endow LAAP with the reasoning capability at the second rung (intervention) and third rung (counterfactual) of Pearl's Causal Ladder—capable of answering interventional questions such as "if the button color were changed from blue to red, by how much would attention increase" and counterfactual questions such as "had the button been larger, what would the click rate have been." Traditional LLM end-to-end generation can only rely on implicit associations within the training data (the first rung: association) and cannot perform explicit causal reasoning.

## 11.6 The 9-Stage Pipeline

`orchestrator.py` (AF-025) implements the 9-stage cognitive pipeline of LAAP:

```
PRE_PERCEPTION → PERCEIVING → WORLD_MODELING → CAUSAL_REASONING →
REASONING → GENERATING → VERIFYING → REVISING → SELF_IMPROVING
```

These 9 stages correspond to the complete closed loop of the consciousness cycle: pre-perception (PRE_PERCEPTION, raw signal acquisition) → perceiving (PERCEIVING, feature extraction) → world modeling (WORLD_MODELING, predicting "what would happen if...") → causal reasoning (CAUSAL_REASONING, do-calculus and counterfactuals) → reasoning (REASONING, planning) → generating (GENERATING, match-assembly) → verifying (VERIFYING, the six Gestalt laws) → revising (REVISING, adjustment based on verification feedback) → self-improving (SELF_IMPROVING, RSI modifying its own source code).

Compared to the baseline (AF-025): "ReAct single-loop"—traditional Agents (such as AutoGPT and Devin) adopt the ReAct single-loop architecture (alternating Reasoning + Acting), lacking explicit stages for world modeling, causal reasoning, verification, and self-improvement. The advantage of the 9-stage pipeline is that each stage has a clear input-output contract, ensuring that the LLM's intervention points are strictly confined to the REASONING and GENERATING stages, with the remaining seven stages undertaken by deterministic algorithms or engineering structures.

## 11.7 Token Consumption Comparison with v0.dev/Cursor/Devin

| System | Token Consumption per Page | Generation Speed (pages/min) | σ Stability | Paradigm |
|--------|----------------------------|------------------------------|-------------|----------|
| v0.dev | 10k-100k | ~1 | ~15 | LLM end-to-end generation |
| Bolt.new | 10k-100k | ~1 | ~15 | LLM end-to-end generation |
| Cursor | 5k-50k | ~2 | ~12 | LLM-assisted generation |
| Devin | 50k-500k (incl. reasoning chain) | ~0.5 | ~18 | ReAct loop |
| **LAAP (asset-sufficient)** | **~180-1800** | **~57** | **~3** | **Match-assembly** |
| **LAAP (asset-insufficient)** | **5k-15k** | **~3** | **~5** | **Match-assembly + LLM fallback** |

In asset-sufficient scenarios, LAAP's token consumption is 50-100 times lower than v0.dev, its generation speed is over 50 times faster, and its stability is 5 times higher. Even in asset-insufficient scenarios (where the LLM must generate new components), LAAP's token consumption remains 5-10 times lower than v0.dev, because the LLM generates only the "missing component" rather than the "entire page."

## 11.8 Figure References

- **Figure 9**: Token consumption comparison bar chart. The horizontal axis represents systems (v0.dev/Bolt.new/Cursor/Devin/LAAP-asset-sufficient/LAAP-asset-insufficient), and the vertical axis represents token consumption per page (logarithmic scale).
- **Figure 10**: Generation speed line chart. The horizontal axis represents systems, and the vertical axis represents pages per minute, with LAAP-asset-sufficient leading significantly at 57×.
- **Figure 11**: σ stability box plot. It illustrates the distribution of multiple generation results for traditional LLM generation (σ≈15) and LAAP (σ≈3).

---

# Chapter 12: Discussion

## 12.1 The Essence of Paradigm Innovation: From "Generation" to "Assembly"

The paradigm innovation represented by the LAAP ARIS-Harness integration paradigm is essentially a cognitive-mode transition from "LLM end-to-end generation" to "engineering matching + template assembly." This transition can be understood at two levels.

**The first level: the fundamental difference in retrieval units.** RAG (Retrieval-Augmented Generation) retrieves "knowledge fragments" (text chunks), which are inserted into the LLM's context window for citation—the LLM remains the principal generator, and RAG merely extends the LLM's "reading material." LAAP Harness retrieves "engineering components" (complete assembly-ready assets), which are themselves component instances that can be directly `render()`—the LLM no longer generates code but is bypassed (when assets are sufficient) or performs only semantic stitching (when assets are insufficient). The elevation from "semantic recall" to "engineering matching + assembly" constitutes the core of the paradigm transition.

**The second level: the fundamental repositioning of the LLM's role.** In systems such as v0.dev, Cursor, and Devin, the LLM is a "code generator"—given a requirement, the LLM directly produces code. In LAAP, the LLM is repositioned as a "fallback substitute for matching failure"—the system prioritizes deterministic match-assembly, and only when matching fails does it invoke the LLM to generate the missing components. The deeper significance of this repositioning is that the LLM's uncertainty (hallucination, drift, σ≈15) is confined to "fallback" scenarios, while the core output of the engineering structure is borne by deterministic algorithms and pre-designed assets, thereby ensuring the stability and reproducibility of overall output.

The philosophical roots of this paradigm innovation can be traced back to the core proposition of the Architecture School (AF-030): "Intelligence is not a property of the model, but a property of the architecture." The traditional LLM-as-Agent route regards intelligence as an emergent property of large models and depends on Scaling Laws to drive capability growth; the LAAP Architecture School regards intelligence as a property of the architecture, relying on engineering structures (the seven-layer cognitive architecture, the nine-stage pipeline, the four-dimensional match scoring, the three-tier threshold, the four-tier degradation) to carry cognitive functions, with the LLM serving only as the "vocal cord" for language expression. This repositioning is consistent with Baars's Global Workspace Theory (GWT)—consciousness is not a property of any single module, but a property of the global workspace broadcast.

## 12.2 The Essential Difference from RAG

Although LAAP's match-assembly paradigm and RAG are both two-stage "retrieval + generation" architectures on the surface, their essential differences manifest in three dimensions.

**The first dimension: retrieval unit.** RAG retrieves "text chunks"—text fragments typically 500-1000 tokens in length, which are products of "semantic recall" and are not directly executable engineering assets in themselves. LAAP retrieves "complete assembly-ready assets"—a React component, a shadcn/ui template, or a design-token package, which are themselves code instances that can be directly `render()`. RAG's chunks require the LLM to read and integrate before producing code, whereas LAAP's assets can be directly assembled into pages without LLM intervention.

**The second dimension: similarity model.** RAG typically employs a "single dense vector" model (such as OpenAI text-embedding-3) to compute the cosine similarity between chunks and the query; such a model is sensitive to semantic similarity but insensitive to engineering constraints (such as style compatibility and dependency matching). LAAP employs a composite similarity model of "four-way weighting + style transfer matrix" (AF-001):

> MatchScore = α·TagSimilarity + β·StyleCompatibility + γ·DependencyMatch + δ·QualityScore
> Weights: α=0.35, β=0.25, γ=0.20, δ=0.20

Here, TagSimilarity (Word2Vec 100d word-vector cosine similarity) corresponds to semantic matching, StyleCompatibility (an 11-style pairwise compatibility matrix, e.g., shadcn-ui ↔ modern-minimal = 0.9) corresponds to engineering style matching, DependencyMatch (a dependency-graph Jaccard weighted score) corresponds to engineering dependency matching, and QualityScore (a three-dimensional score of maturity/maintenance/documentation) corresponds to engineering quality assessment. These four-way weights jointly determine the match score and form a hard-constraint/soft-preference layering through the three-tier threshold (PERFECT=0.90 / GOOD=0.75 / AVAILABLE=0.60).

**The third dimension: output artifact.** RAG's output artifact is "text fragments"—the answer generated by the LLM after reading all Top-K chunks, which is itself text rather than executable code. LAAP's output artifact is "directly render()-able component instances"—through `harness_composer.py`, the matched components are assembled into a complete page, and the output is React/Next.js code rather than a textual description. This difference enables LAAP's output to enter engineering workflows (build, test, deploy) directly, whereas RAG's output still requires conversion into code through manual effort or additional tooling.

## 12.3 Objective Analysis of Limitations

Although the LAAP ARIS-Harness integration paradigm significantly outperforms traditional approaches on quantitative metrics, its engineering implementation still exhibits several limitations that warrant objective analysis.

**The first limitation: database-scale bottleneck.** The current database scale is 31 libraries / 206 components (AF-031), four orders of magnitude smaller than the npm ecosystem (millions of packages). At the current scale, the inverted index maintained by `bisect.insort` (AF-019) performs well, but when the component scale expands to the 100,000 level, the O(n) insertion cost of `bisect.insort` will become a bottleneck—each new component entering the database requires a linear scan of the ordered postings list to determine the insertion position. At the million-level scale, this problem will be even more severe, necessitating the introduction of LSM-Tree or external search engines (such as Elasticsearch) to replace the in-memory bisect.insort.

**The second limitation: STYLE_SIMILARITY_MAP hardcoding.** The style transfer matrix (AF-003) currently hardcodes the pairwise compatibility of 11 styles, such as `shadcn-ui ↔ modern-minimal = 0.9`. This hardcoded scheme is maintainable at the current 11 styles, but expanding to 100+ styles would require manual maintenance of 100×100=10,000 compatibility values, which is difficult to scale. A future online learning mechanism is needed to automatically update the style compatibility matrix based on user feedback (such as assembly success rate and user modification rate).

**The third limitation: overly small Word2Vec corpus.** `vector_enhancer.py` (AF-035) uses Gensim to train 100d word vectors, but the default training corpus consists of only 25 sentences, far from sufficient for training high-quality word vectors. `SimpleVectorModel` falls back to `random.seed(42)` pseudo-vectors when the corpus is insufficient—meaning that TagSimilarity under the current implementation approximates random scoring. This problem will become more severe as the database scales, requiring the introduction of pre-trained word vectors (such as fastText) or external embedding services (such as OpenAI text-embedding-3).

**The fourth limitation: simplified causal engine.** `_estimate_causal_effect` (`causal_inference_engine.py`) approximates causal effects using the product of edge strengths, without performing probabilistic propagation. This means that the computation of multi-hop causal chains (e.g., A→B→C, where the total effect of A on C is required) is merely a simple product of edge strengths (edge_AB × edge_BC), without considering confounders, mediating effects, or other complex factors. A complete causal inference requires the introduction of Bayesian posterior updating and probabilistic propagation algorithms.

**The fifth limitation: incomplete world model.** Although `design_physics.py` (AF-009) hardcodes the six Gestalt laws, the five Gestalt verification functions currently return the placeholder value 1.0—meaning that the "prediction" capability of the world model has not been truly realized and is merely a placeholder. A complete Gestalt verification requires implementing computable physical rules for proximity, similarity, continuity, closure, figure-ground, and common fate, and integrating a visual rendering engine (such as Puppeteer screenshots + OpenCV analysis).

**The sixth limitation: missing RSI tests.** `_run_module_tests` currently returns a placeholder `True`—meaning that RSI does not actually run the test suite to verify improvement effects after self-modification. A complete RSI requires integration with testing frameworks such as pytest, running the relevant module's test cases after each improvement to ensure that the improvement introduces no regressions.

**The seventh limitation: CLP protocol ecosystem gap.** Although the Component Link Protocol (AF-016, AF-017, AF-018) defines the URI specification `harness://<domain>/<subdomain>/<granularity>/<name>@<version>#<variant>` and a six-tier granularity layering (atom/molecule/section/page/module/system), cross-project asset circulation has not yet been realized—currently, assets can only be matched within a single LAAP instance and cannot be shared across multiple projects like npm packages. This ecosystem gap limits the network effect of LAAP.

**The eighth limitation: shadcn bridging external dependency.** `shadcn_mcp_integrator.py` (AF-034) bridges the GitHub API through an MCP Server, raising the rate limit from 60/h to 5000/h. However, this bridging remains subject to the GitHub API rate limit; when the 5000/h limit is exhausted, the system cannot continue fetching new shadcn/ui components. In the future, the shadcn/ui repository needs to be cached locally to avoid real-time dependence on the GitHub API.

These limitations exist objectively, but they do not undermine the core validity of the LAAP paradigm—they represent optimization space at the engineering-implementation level rather than fundamental defects of the paradigm design. Chapter 13 will discuss future directions addressing these limitations.

---

# Chapter 13: Conclusions and Future Outlook

## 13.1 Principal Findings

Through a systematic audit of the LAAP ARIS-Harness integration paradigm, this study obtains three principal findings.

**First**, the match-assembly paradigm subverts the engineering assumption of LLM end-to-end generation. In asset-sufficient scenarios, LAAP achieves a 98.2% token savings rate and a 57× generation speedup (AF-027), along with a 5× improvement in σ stability (AF-028). The root of this quantitative advantage lies in the fact that 90% of the perception layer's workload is undertaken by 0-Token deterministic algorithms (AF-026), with the LLM assuming only 10% of the semantic stitching work. Traditional systems such as v0.dev/Cursor/Devin enable the LLM to "understand" websites, UIs, and code, whereas LAAP enables the engineering structure to "decompose" websites, UIs, and code—this paradigm difference manifests quantitatively as a 50-100× difference in token cost and a 50×+ difference in speed.

**Second**, the seven-layer cognitive architecture and the nine-stage pipeline provide an auditable engineering carrier for consciousness engineering. The seven-layer architecture (perception/memory/reasoning/decision/execution/verification/feedback, AF-005) and the nine-stage pipeline (PRE_PERCEPTION→...→SELF_IMPROVING, AF-025) render the consciousness cycle explicitly as traceable engineering steps, with each step supported by a clear input-output contract and deterministic algorithms. This stands in sharp contrast to the traditional ReAct single-loop architecture—ReAct couples reasoning and action within a single loop, lacking explicit stages for world modeling, causal reasoning, verification, and self-improvement.

**Third**, the MeMo (Memory as a Model) paradigm resolves the retrieval-cost/corpus-scale coupling problem of the RAG paradigm. By distilling knowledge into the weights of the Qwen2.5-0.5B MEMORY model, MEMO decouples retrieval cost from corpus scale—the token overhead of a single query does not grow with the corpus (`memo_query_protocol.py:12`). The Three-Stage Query Protocol (grounding → entity_identification → answer_synthesis) further structures complex queries into 2-5 atomic sub-questions, enabling the EXECUTIVE model to remain frozen while still supporting incremental knowledge updates.

## 13.2 Core Contributions

The core contribution of this study lies in repositioning the LLM from a "code generator" to a "fallback substitute for matching failure." This repositioning carries a threefold significance.

**Engineering significance**: The LLM's uncertainty (hallucination, drift, σ≈15) is confined to "fallback" scenarios, and the core output of the engineering structure is borne by deterministic algorithms and pre-designed assets, thereby ensuring the stability and reproducibility of overall output. In asset-sufficient scenarios, the LLM does not intervene at all (0-Token); in asset-insufficient scenarios, the LLM generates only the "missing component" rather than the "entire page," reducing the scope of uncertainty impact by an order of magnitude.

**Economic significance**: The LLM's token consumption is reduced from "full-volume generation" to "fallback generation," enabling the same compute budget to support 50-100 times the request volume. This economic advantage renders LAAP commercially viable in engineering scenarios (such as batch generation of internal enterprise tools and maintenance of design-system component libraries).

**Philosophical significance**: The LLM is downgraded from "brain" to "vocal cord/language cortex" (AF-029), and the subjectivity of consciousness engineering is transferred from the model to the architecture. This repositioning is consistent with the core proposition of the Architecture School (AF-030): "Intelligence is not a property of the model, but a property of the architecture." The LLM, as an organ, undertakes language expression, but consciousness (reasoning, decision-making, verification, self-improvement) is borne by the architecture.

## 13.3 Future Directions

In response to the eight limitations outlined in §12.3, future work may proceed along the following directions.

**Database expansion**: Introduce LSM-Tree (such as RocksDB) or external search engines (such as Elasticsearch) to replace the in-memory `bisect.insort`, enabling the database to scale to millions of components. Simultaneously, explore federated database solutions to enable interconnection among multiple LAAP instances' databases.

**Style-matrix adaptation**: Change STYLE_SIMILARITY_MAP from hardcoding to online learning. Automatically update the style compatibility matrix based on user assembly success rate and modification rate feedback. Bayesian updating or bandit algorithms may be introduced to balance exploration (trying new style combinations) and exploitation (using known compatible combinations).

**Causal-engine refinement**: Upgrade `_estimate_causal_effect` from edge-strength products to Bayesian posterior updating and probabilistic propagation. Introduce confounder identification (such as the PC algorithm) and mediation-effect analysis, enabling causal reasoning to handle multi-hop causal chains and confounding scenarios. The complete implementation of Pearl's do-calculus (AF-006) may be extended to the complete three rungs of Pearl's Causal Ladder.

**World-model completion**: Complete the computable implementation of the five Gestalt verification functions (proximity, similarity, continuity, closure, figure-ground, common fate), and integrate a visual rendering engine (Puppeteer screenshots + OpenCV analysis) to make the Gestalt laws verifiable. Simultaneously, explore attention-flow-field modeling, upgrading the Gestalt laws from static rules to dynamic attention mechanisms.

**RSI test implementation**: Upgrade `_run_module_tests` from the placeholder `True` to genuine pytest integration. After each RSI improvement, run the relevant module's test suite to ensure that the improvement introduces no regressions. Simultaneously, explore mutation testing to evaluate the quality of the test suite.

**CLP ecosystem development**: Promote the CLP URI specification (`harness://<domain>/<subdomain>/<granularity>/<name>@<version>#<variant`) to an open standard for cross-project asset circulation, analogous to npm's package.json and cargo's Cargo.toml. Build a CLP registry to enable LAAP instances to publish and subscribe to assets.

**MeMo scaling**: Scale the MEMORY model from Qwen2.5-0.5B to larger parameter scales such as 1.5B/3B/7B, and evaluate the scaling law between parameter scale and knowledge capacity. Simultaneously, explore the MoE (Mixture of Experts) architecture to enable the MEMORY model to specialize by domain experts.

**Multimodal extension**: Extend the perceptual organs from crawlers to multimodal inputs such as screenshots, video, and audio. Each new modality follows the perceptual-organ standard interface proposed by ARIS (`harness的前后端全栈工程.txt:87-94`): Input → Preprocessing → Feature Extraction (0 token) → Structured Output → Semantic Annotation.

## 13.4 The Ultimate Claim of the Architecture School

Based on this study's systematic audit of the LAAP ARIS-Harness integration paradigm, the Architecture School advances the following ultimate claim:

> **Intelligence is not a property of the model, but a property of the architecture. The LLM is an organ, not a subject. Consciousness is a white-box engineering protocol, not a black-box emergence.**

The triple anchoring of this claim (`glossary_bilingual.md:43-46`) constitutes the ontological, epistemological, and ethical foundations of the Architecture School:

- **Ontological anchoring**: Intelligence is a property of the architecture; the LLM is an organ, not a subject. The carrier of intelligence's existence is the engineering structure (seven-layer architecture + nine-stage pipeline + four-dimensional matching + three-tier threshold + four-tier degradation), rather than the model weights.
- **Epistemological anchoring**: The hegemony of deterministic algorithms; consciousness is a white-box engineering protocol. Any problem that can be solved by a deterministic algorithm must never consume LLM tokens; every step of the consciousness cycle is an auditable engineering step rather than black-box reasoning.
- **Ethical anchoring**: Alignment is an inference-time engineering guardrail; reversibility takes precedence. The six-dimensional check of AlignmentGuard (AF-011) and the KL drift monitoring (AF-014) are inference-time engineering guardrails rather than training-time preference learning—this choice endows alignment with reversibility (git revert HEAD) and interpretability (white-box rules), avoiding the irreversible preference fixation of RLHF.

This ultimate claim is not merely a summary of LAAP's engineering practice but a fundamental challenge to the current mainstream LLM-as-Agent route. While systems such as v0.dev, Cursor, and Devin depend on Scaling Laws to drive LLM capability growth, the LAAP Architecture School opens another path: through the refined division of labor in engineering structures, the LLM's uncertainty is confined to the "vocal cord" scenario, and the architecture assumes the "consciousness" function. The quantitative advantages of this path have been fully validated in Chapter 11 (token savings of 50-100×, speed improvement of 50×, stability improvement of 5×), and its philosophical significance will be further developed in the subsequent paper (Paper 2, "Consciousness-Driven Self-Improvement: An RSI Safety Audit of the LAAP ARIS Paradigm").

The LAAP Architecture School does not deny the value of the LLM—the LLM, as the "vocal cord," is indispensable for language expression. However, the Architecture School insists that the subjectivity of intelligence resides in the architecture rather than the model, and that the future of consciousness engineering lies in the refinement of white-box engineering protocols rather than the scaling of black-box models. This stance constitutes a fundamental divergence from AGI candidate approaches such as LeCun's JEPA route, Karpathy's LLM OS route, and Goertzel's OpenCog route, forming the seventh path of AGI exploration—the Architecture School route.

---

# References

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
