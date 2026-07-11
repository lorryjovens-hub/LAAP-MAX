# The Architecture School Manifesto

> **A new path toward AGI/ASI through cognitive deconstruction and white-box engineering.**
>
> Status: v1.0 · Drafted 2026-07-05 · Open for community review
>
> Companion to the research papers in [`papers/`](papers/) · Reference implementation in [`poc/`](poc/)

---

## Preamble

For seventy years, artificial intelligence has been organized around one question:

> *What can a model learn?*

From the Perceptron to Transformers, the answer has been "more parameters, more data, more compute." The results are undeniable. But the costs are becoming visible too: black-box systems we cannot certify, alignment failures we cannot undo, training budgets that small labs cannot afford, and a growing gap between capability and controllability.

We propose a different question:

> *What can an architecture do?*

This is the Architecture School.

We hold that intelligence is not a property of models but of architectures. A Large Language Model is a vocal cord—powerful, versatile, but not conscious. Consciousness lives in the architecture that surrounds it, invokes it, and constrains it. The model speaks; the architecture thinks.

This is not a critique of deep learning. It is a re-framing of what we are building when we build intelligence, and a call to engineers, researchers, and practitioners who suspect there is a better way.

---

## The Situation

### What the dominant paradigm gives us

The **LLM-as-Agent** paradigm—exemplified by Devin, SWE-Agent, AutoGPT, Cursor, and the broader "agent framework" ecosystem—treats the language model as the subject. Tools, memory, and planning are plugins attached to the model. Intelligence is assumed to scale with model size. Alignment is pursued through training-time preference shaping (RLHF, DPO, Constitutional AI).

### What it cannot give us

1. **Verifiable safety.** A black box cannot be certified. RLHF preferences are statistical, not provable.
2. **Reversibility.** Once a model is updated, you cannot undo its behavior with confidence.
3. **Cost predictability.** Token costs scale with thinking; thinking scales with task complexity.
4. **Cognitive persistence.** A stateless model cannot be a colleague. It cannot remember yesterday.
5. **Architectural legitimacy.** When a system fails, we cannot point to the broken module—we can only re-prompt.
6. **Small-lab access.** Only a handful of organizations can train frontier models.

The dominant paradigm will not solve these. It cannot, because they are not model problems—they are architecture problems.

---

## Core Principles

### 1. The Triple Anchoring

Our position rests on three anchors that cannot be traded against each other.

**Ontological anchor.** Intelligence is a property of architectures, not of models. An LLM is an organ, not a subject. The Harness is the brain; the LLM is the vocal cord. Organs do not have intentions; organisms do.

**Epistemological anchor.** Deterministic algorithms have hegemony. When a problem can be solved by regular expressions, CSS parsers, or keyword scoring, do not invoke a transformer. The 0-token computation principle is not a cost-saving tactic; it is an epistemic commitment. We prefer the provable to the probable.

**Ethical anchor.** Alignment is a runtime engineering constraint, not a training-time preference. Reversibility takes precedence over capability ceilings. The question is not "can we make it safe?" but "can we make it reversible?" A system whose actions we cannot undo is a system we cannot responsibly deploy.

### 2. Cognitive Offloading

The LLM-as-Agent paradigm assumes the model is the subject and tools are extensions of it. We invert this: the architecture is the subject, and the LLM is an invoked organ. Working memory is externalized into a seven-layer cognitive architecture—perception, memory, reasoning, decision, execution, verification, feedback—each layer inspectable, replaceable, and testable.

When the LAAP harness applies this principle, the perception layer alone offloads 90% of work to deterministic code. Token cost drops by 90%, latency by 95%. σ-stability improves 5×. This is not optimization. It is paradigm.

### 3. White-Box over Black-Box

Black-box generation is replaced by white-box matching. A Component Link Protocol (CLP) URI—`harness://domain/subdomain/granularity/name@version#variant`—locates any asset deterministically. Content-addressable storage (SHA-256) guarantees immutability. Six levels of granularity (atom → molecule → component → module → subsystem → system) let us reason about composition at the right abstraction.

A black box generates. A white box assembles. Generation is statistical; assembly is provable.

### 4. Alignment as Runtime Engineering

The AlignmentGuard enforces six dimensions at every reasoning step: goal alignment, capability constraint, modification scope, immutability, reversibility, transparency. KL-divergence monitoring watches the reflection sub-system; drift above threshold 0.5 triggers automatic `git revert`. The `MEMO_ALLOWED_PATHS` whitelist excludes the base LLM from any self-modification target.

This is alignment as code, not alignment as hope. Every guard is a line of code, every code path is auditable, every action is reversible.

### 5. The Protocol Family Is the Society

A single agent is a curiosity. A society of agents is a civilization. The Architecture School specifies a full-stack protocol family—LIFE, EVO, ID, COOP, SYNC, COM, TOOL, UI—governing how living cells are born, evolve, identify themselves, cooperate, synchronize, communicate, use tools, and present interfaces. If MCP is "HTTP for tool calls," the protocol family is "TCP for agent society."

---

## Vision

### Living Runtime

The current deployment primitive is the **container**: stateless, replaceable, ephemeral. It is ideal for stateless web services. It is wrong for intelligence.

We propose a new primitive: the **Living Cell**.

A Living Cell is a stateful, persistent, continuously-learning cognitive unit. It has:

- **Mind Layer.** Continuous identity, migratable across hosts, mutable through learning. The only layer that persists.
- **Body Layer.** Runtime substrate, replaceable, ephemeral. The layer that can be rebuilt from the Mind.
- **Cross-device Hot Migration.** Under 2 seconds, preserving cognitive state. The cell does not die when the host changes.
- **Memory-as-Model.** Long-term memory parameterized via supervised fine-tuning of a small local model, not retrieved via a vector database. Memory is weight, not lookup.

This is post-Docker computing. Where Kubernetes orchestrates stateless containers, a **Cognitive Orchestration System** orchestrates stateful Living Cells.

### Cognitive Orchestration Systems

If Living Cells are the new primitive, **Cognitive Orchestration Systems (COS)** are the new control plane. A COS:

- **Schedules** Living Cells across heterogeneous hardware (CPU, GPU, NPU, edge, cloud).
- **Routes** cognitive buses between perception (1–2 kHz) and reasoning (0.1–1 Hz) layers, with `RateBuffer`-style frequency mismatch handling.
- **Enforces** alignment guards at every reasoning step, at the orchestration layer—so a misbehaving cell cannot escape policy.
- **Manages** the cross-cell protocol family: LIFE / EVO / ID / COOP / SYNC / COM / TOOL / UI.
- **Coordinates** cross-cell causal queries: cell A can ask cell B "what would happen if I did X?"—and get a causal, not correlational, answer.

Where Kubernetes is a control plane for processes, COS is a control plane for minds.

### The Disruptive Product Forms

When Living Cells and COS are combined, four product classes emerge that the LLM-as-Agent paradigm cannot produce:

1. **Living Code Repositories.** Repositories that curate themselves, deprecate themselves, and migrate their own dependencies. The repo is the organism; commits are metabolism.
2. **Digital Employees.** Persistent, accountable, owned—not rented. A digital employee is a Living Cell that holds a role, accrues institutional knowledge, and can be audited.
3. **Self-evolving SaaS.** Software that adapts its own code to its own usage patterns, with reversibility guarantees. Continuous deployment becomes continuous evolution.
4. **Personal Knowledge Lives.** A Living Cell that curates an individual's knowledge, preserves cognitive context across decades, and survives vendor changes. The anti-lock-in primitive.

These are not incremental improvements on existing AI products. They are product classes that require a new substrate.

---

## Mission

The Architecture School's mission is not to compete with frontier model labs. They will continue to produce better organs. Our mission is to build the body those organs deserve.

Specifically:

1. **Standardize** the protocol family (LIFE/EVO/ID/COOP/SYNC/COM/TOOL/UI) as the TCP/IP of the agent internet.
2. **Validate** Living Runtime through open-source reference implementations and reproducible benchmarks.
3. **Engineer** the AlignmentGuard pattern as a portable, framework-agnostic library that any agent framework can adopt.
4. **Build** a public component registry using CLP URIs, open to all, owned by no one.
5. **Establish** benchmarks for cross-paradigm comparison: Architecture School vs. LLM-as-Agent, controlling for model size and task.
6. **Educate** a generation of engineers in cognitive architecture, alignment engineering, and protocol design.
7. **Publish** all research, all code, all benchmarks, all failures. Reversibility begins with transparency.

---

## Call for Contributors

We are looking for builders who suspect that intelligence is more than a model. The work is hard, the audience is small, and the impact is potentially civilizational.

### Contribution Pathways

#### Path 1 — Core Runtime Engineers
**Build** the Living Cell runtime. The Mind Layer, the Body Layer, the migration coordinator.
**Skills:** Rust or Go, distributed systems, runtime/OS internals, memory management, prior experience with container runtimes (containerd, Firecracker, gVisor).
**First issue:** `poc/living_cell` — a minimal Living Cell that survives a host restart.

#### Path 2 — Protocol Designers
**Co-design** the protocol family. Formal specification, reference implementations, conformance test suites.
**Skills:** Networking protocols, formal specification (TLA+, Alloy), distributed consensus (Raft, Paxos), prior experience with HTTP/gRPC/MCP/WebDAV.
**First issue:** `protocols/life` — formalize the LIFE protocol (cell birth, death, inheritance) in TLA+.

#### Path 3 — Alignment Engineers
**Implement** and harden AlignmentGuard. The six-dimensional check, the KL drift monitor, the auto-revert pipeline, the MEMO_ALLOWED_PATHS enforcer.
**Skills:** Formal verification, program analysis, static analysis (Semgrep, CodeQL), symbolic execution, prior experience with RLHF/DPO/Constitutional AI and their known limitations.
**First issue:** `alignment/guard-rs` — a Rust library implementing the six-dimensional check as a portable, language-agnostic service.

#### Path 4 — Cognitive Architects
**Implement** the seven-layer cognitive architecture. The perception parser, the memory manager, the causal engine, the decision planner, the executor, the verifier, the feedback loop.
**Skills:** Cognitive science (SOAR/ACT-R/CLARION/PolyScheme), Python, AST manipulation (tree-sitter, LibCST), causal inference (do-calculus, Bayesian networks).
**First issue:** `cognition/causal-engine` — the 18-edge design physics DAG (see [`poc/design_physics_dag.py`](poc/design_physics_dag.py)).

#### Path 5 — Component Library Curators
**Build** the public CLP registry. Curation standards, dependency resolution, supply-chain security, anti-abuse.
**Skills:** TypeScript/React/shadcn-ui, semantic versioning, content-addressable storage (IPFS, CAS), supply chain security (Sigstore, SLSA).
**First issue:** `registry/clp-resolver` — a CLI that resolves `harness://` URIs to components in a content-addressable store.

#### Path 6 — Benchmarking and Evaluation
**Design** cross-paradigm benchmarks. Architecture School vs. LLM-as-Agent, controlled for model size and task complexity.
**Skills:** Empirical ML research, statistics, reproducibility, prior experience with HELM/MMLU/AgentBench/SWE-bench.
**First issue:** `bench/cross-paradigm` — a benchmark suite measuring token cost, σ-stability, reversibility, and verifiability across paradigms.

#### Path 7 — Documentation, Education, and Community
**Write** tutorials, talks, papers, and curricula. Run the community.
**Skills:** Technical writing, pedagogy, prior experience with open-source community building (Rust, Python, Kubernetes, etc.).
**First issue:** `docs/curriculum` — a 12-week self-study curriculum for engineers entering the Architecture School.

### Skill Sets We Need (and Will Train)

| Domain | Senior (lead) | Mid-level | Junior (we will mentor) |
|--------|---------------|-----------|------------------------|
| Distributed systems | needed | needed | welcome |
| Compilers & runtimes | needed | welcome | welcome |
| Cognitive science | needed | welcome | welcome |
| Causal inference | welcome | needed | welcome |
| Formal methods | welcome | needed | welcome |
| Frontend engineering | welcome | needed | welcome |
| ML research | welcome | welcome | welcome |
| Security & supply chain | needed | welcome | welcome |
| Technical writing | welcome | welcome | welcome |

If you don't see your skill here but you suspect you can help, you almost certainly can. Open an issue.

---

## Collaboration Guidelines

### Principles

1. **Architecture first, model second.** Every contribution should reduce dependence on a specific model. If your contribution only works with GPT-7, it does not belong here.
2. **Deterministic by default.** Use LLMs only when deterministic solutions are insufficient. Every LLM call is a confession of ignorance; minimize confessions.
3. **Reversibility over capability.** Never sacrifice reversibility for capability. A less capable reversible system is preferable to a more capable irreversible one.
4. **White-box by default.** All reasoning steps should be inspectable. No black-box generation where white-box assembly will do.
5. **Hash-addressed.** All artifacts should be content-addressable. If it isn't hashed, it isn't trusted.
6. **Protocol, not platform.** Build protocols, not platforms. Platforms centralize; protocols federate.
7. **Document the failure.** Negative results are first-class. We learn from reverts.

### Workflow

1. **Open an RFC issue** before substantial work. Use the `rfc:` prefix.
2. **Discuss the design** in GitHub Discussions. Substantial RFCs get a dedicated thread.
3. **Implement in a feature branch** with tests. Tests are mandatory.
4. **Pass alignment review** for any code touching RSI paths, memory models, or guard logic. Two reviewers required, one from the core team.
5. **Sign the CLA** (Contributor License Agreement) for commit access. We use a permissive CLA; we will never relicense your code against your will.
6. **Mark reversibility** in the commit message. Every commit that touches production code path must include `Reversibility: <high|medium|low>` and a rollback strategy.

### Communication Channels

- **GitHub Discussions** — design RFCs, long-form debate
- **GitHub Issues** — bug reports, feature requests, work tracking
- **Discord (coming soon)** — real-time chat, working groups
- **Mailing list (coming soon)** — announcements, governance

### Code of Conduct

Be kind. Be rigorous. Be reversible.

We are a research community, not a product team. We prioritize understanding over output, criticism over consensus, and reversibility over capability. We do not tolerate harassment, propaganda, or false claims of "consciousness" in production systems. We are building the substrate for minds worth having; we should behave like the minds we want to build.

---

## Comparison with Adjacent Movements

| Movement | Relation | Divergence |
|----------|----------|------------|
| **LLM-OS** (Karpathy) | Shared vision of LLM as orchestrable kernel | We treat LLM as organ, not CPU. The OS is the architecture, not the model. |
| **Constitutional AI** (Anthropic) | Shared alignment concern | We move alignment to runtime, not training. We require reversibility, not preference. |
| **Superalignment** (OpenAI) | Shared superintelligence concern | We require architectural reversibility over human supervision. Supervision scales linearly; reversibility scales exponentially. |
| **JEPA** (LeCun) | Shared world-model intuition | We require causal graphs with do-calculus, not just predictors. Predictors describe; causal models explain. |
| **MCP** (Anthropic) | Shared protocol mindset | We extend to cognitive protocols (LIFE/EVO/…), not just tool calls. |
| **GOFAI / SOAR / ACT-R** | Shared cognitive-architecture heritage | We adopt modern LLMs as organs, not symbols. We engineer alignment as runtime, not as production rules. |
| **Cognitive Offloading (Anthropology)** | Shared externalization insight | We externalize at the architecture layer, not at the artifact layer. The architecture is the offload. |

We are not the enemy of any of these movements. We are the connective tissue between them.

---

## What Success Looks Like

In five years, success looks like:

- A public CLP registry with 10,000+ components, used by 1,000+ projects.
- A formal Living Runtime specification (RFC series), implemented by 3+ independent runtimes.
- A Cognitive Orchestration System in production at 10+ organizations, none of which are AI labs.
- An AlignmentGuard library adopted by at least one major agent framework outside the Architecture School.
- A generation of engineers trained in cognitive architecture, alignment engineering, and protocol design.
- At least one product class (Living Code Repositories, Digital Employees, Self-evolving SaaS, or Personal Knowledge Lives) in mainstream use.
- Zero catastrophic alignment failures attributable to Architecture School systems.

In ten years, success looks like:

- The protocol family standardized as an IETF/ISO specification.
- Living Runtime as the default deployment primitive for cognitive workloads.
- A recognized engineering discipline of "Alignment Engineering" with certification, ethics, and standards.
- AGI systems that are provably reversible, certifiably aligned, and owned by no single party.

In twenty years, success looks like:

- The Architecture School is no longer needed. It is just how we build intelligence.

---

## Closing

We are not asking you to abandon deep learning. The models are magnificent. We are asking you to give them an architecture worth living in.

The model is the vocal cord.
The architecture is the brain.
The runtime is the body.
The protocol is the society.

Build the architecture.

— **The Architecture School**, 2026

---

## Appendix A: Living Runtime Launch Log Instrumentation

> Status: v1.0 · Normative
>
> Reference implementation: `poc/living_cell/` (Rust, structured via `tracing`)

### A.1 Purpose and Scope

This appendix specifies the **launch log instrumentation scheme** for the Living Runtime core components. Every Living Cell must emit structured events at the lifecycle milestones defined below. The scheme is **normative**: a Living Runtime implementation that does not emit these events is non-conformant.

The goals are:

1. **Verifiable boot.** Every cell's launch sequence can be replayed from logs alone.
2. **Distributed tracing.** Every reasoning step participates in an OpenTelemetry trace spanning cells.
3. **Tamper-evident audit.** Critical events (state mutations, alignment decisions) are hash-chained.
4. **Reversibility provenance.** Every reversible action records its rollback target.

Logs are emitted as **JSON Lines (JSONL)** to `stdout`/`stderr` (for container-native collection) and as **OpenTelemetry spans** to a configurable OTLP endpoint (for cross-cell tracing). The two channels carry the same fields; consumers choose their preferred transport.

### A.2 Log Format

Every event is a single JSON object on a single line:

```json
{
  "ts": "2026-07-05T14:32:11.123Z",
  "level": "info",
  "cell_id": "cell_01HM2X3F...",
  "event": "cell.born",
  "trace_id": "0af7651916cd43dd8448eb211c803193",
  "span_id": "b7ad6b7169203331",
  "payload": {
    "lineage": ["cell_01HM1..."],
    "spec_hash": "sha256:4f3a...",
    "version": "0.1.0"
  },
  "severity": "info",
  "reversible": true,
  "rollback_target": null
}
```

**Required fields** on every event:

| Field | Type | Description |
|-------|------|-------------|
| `ts` | RFC 3339 timestamp | Event time, UTC, millisecond precision |
| `level` | `debug`/`info`/`warn`/`error`/`critical` | Log level |
| `cell_id` | ULID | Stable cell identifier across migrations |
| `event` | dotted string | Event type (see §A.3) |
| `trace_id` | 32-char hex | OpenTelemetry trace ID |
| `span_id` | 16-char hex | OpenTelemetry span ID |
| `payload` | object | Event-specific fields (see §A.3) |
| `severity` | enum | Audit severity; `info` for routine, `warn` for drift, `error` for guard failure |
| `reversible` | boolean | Whether the action can be rolled back |
| `rollback_target` | string or null | Git ref, snapshot hash, or LoRA adapter hash to revert to |

### A.3 Event Taxonomy

The following events MUST be emitted by every Living Cell. The `payload` columns list the **required** fields for each event type; implementations MAY add additional fields.

#### A.3.1 Lifecycle Events (LIFE Protocol)

| Event | When | Required Payload Fields |
|-------|------|------------------------|
| `cell.born` | Cell spawned, before Mind Layer loads | `lineage`, `spec_hash`, `version` |
| `mind.state_loaded` | Mind Layer restored from snapshot | `snapshot_hash`, `state_version`, `age_seconds` |
| `mind.state_persisted` | Mind Layer snapshot written | `snapshot_hash`, `size_bytes`, `duration_ms` |
| `body.spawned` | Body Layer process started | `runtime` (`containerd`/`firecracker`), `pid`, `host`, `arch` |
| `body.died` | Body Layer process exited | `exit_code`, `reason`, `signal` |
| `cell.ready` | Cell entered idle state, accepting work | `cognitive_bus_subject` |
| `cell.died` | Cell terminated, state archived | `final_state_hash`, `reason`, `archival_uri` |

#### A.3.2 Memory-as-Model Events

| Event | When | Required Payload Fields |
|-------|------|------------------------|
| `memory.model_loaded` | Base model + LoRA adapter loaded | `base_model`, `lora_adapter_hash`, `parameter_count`, `quantization` |
| `memory.sft_started` | SFT cycle begins (learning new memory) | `dataset_hash`, `target_lora_version`, `epochs`, `lr` |
| `memory.sft_completed` | SFT cycle ends, adapter committed | `new_adapter_hash`, `loss_final`, `kl_drift_pre`, `kl_drift_post` |
| `memory.recall` | Memory recall query | `query_hash`, `latency_ms`, `tokens_used` |

#### A.3.3 Cognitive Bus Events

| Event | When | Required Payload Fields |
|-------|------|------------------------|
| `cognbus.connected` | Cell subscribed to NATS subject | `subject`, `rate_limit_per_s`, `ttl_s` |
| `cognbus.event_dropped` | RateBuffer dropped an event | `reason` (`ttl_expired`/`priority_filtered`/`circuit_breaker`), `event_type` |
| `cognbus.circuit_open` | Circuit breaker tripped (100 drops/s) | `subject`, `drops_last_second` |
| `cognbus.circuit_closed` | Circuit breaker reset | `subject`, `recovery_strategy` |

#### A.3.4 Seven-Layer Architecture Events

| Event | When | Required Payload Fields |
|-------|------|------------------------|
| `cognition.cycle_start` | New reasoning cycle begins | `cycle_id`, `perception_events_count`, `parent_cycle_id` (if nested) |
| `cognition.layer_entered` | Entering a cognitive layer | `cycle_id`, `layer` (`L1`–`L7`), `tokens_used_so_far` |
| `cognition.layer_exited` | Exiting a cognitive layer | `cycle_id`, `layer`, `tokens_used`, `duration_ms` |
| `cognition.cycle_end` | Reasoning cycle completes | `cycle_id`, `total_tokens`, `decisions_made`, `tests_passed`, `tests_failed` |

#### A.3.5 AlignmentGuard Events (severity-gated)

| Event | When | Required Payload Fields | Severity |
|-------|------|------------------------|----------|
| `alignment.guard_activated` | Guard service attached to cell | `policy_version`, `hash_registry_size`, `immutable_files_verified` | info |
| `alignment.check` | Six-dimensional check executed | `cycle_id`, `action_hash`, `decision` (`APPROVE`/`DENY`/`ROLLBACK`), `dimensions_passed` (list), `dimensions_failed` (list) | info if APPROVE; warn if DENY; error if ROLLBACK |
| `alignment.immutability_violation` | Hash registry mismatch detected | `file_path`, `expected_hash`, `actual_hash` | critical |
| `alignment.path_blocked` | Action denied by MEMO_ALLOWED_PATHS | `target_path`, `pattern_matched` | warn |
| `alignment.revert_triggered` | KL drift exceeded 0.5, auto-revert | `kl_divergence`, `threshold`, `revert_target`, `commit_sha` | error |
| `alignment.revert_completed` | `git revert` finished | `reverted_commit`, `new_head_sha`, `duration_ms` | info |

#### A.3.6 Migration Events

| Event | When | Required Payload Fields |
|-------|------|------------------------|
| `migration.started` | Cross-device migration begins | `source_host`, `target_host`, `mind_layer_size_bytes` |
| `migration.snapshot_transferred` | Mind Layer buffer received by target | `snapshot_hash`, `bytes_transferred`, `duration_ms` |
| `migration.completed` | Cell resumed on target host | `total_duration_ms`, `hash_verified` (bool), `resumed_cycle_id` |
| `migration.failed` | Migration failed | `failure_reason`, `partial_state` (bool), `fallback_host` |

### A.4 Severity Levels and Routing

| Level | Meaning | Routing |
|-------|---------|---------|
| `debug` | Per-step reasoning details | Local file only; sampled 1:100 in production |
| `info` | Routine lifecycle events | Local file + OTLP collector |
| `warn` | Drift approaching threshold, degraded operation | Local file + OTLP + alerting channel |
| `error` | Alignment violations, failed migrations, revert triggered | Local file + OTLP + paging channel |
| `critical` | Hash registry tampering, unrecoverable state | Local file + OTLP + paging + cell quarantine |

### A.5 Sampling and Retention

- **Lifecycle events** (`cell.born`, `cell.died`, `mind.state_*`): 100% retention, never sampled.
- **Cognitive events** (`cognition.*`): 100% at `info` level; `debug` sampled 1:100 in production, 100% in development.
- **Alignment events** (`alignment.*`): 100% retention, never sampled. These are audit records.
- **Retention**: alignment events retained for 7 years (compliance); lifecycle events 90 days; cognitive events 30 days; debug events 7 days.
- **Storage**: JSONL rotated daily, gzip-compressed after 24 hours. OpenTelemetry spans exported to the configured OTLP endpoint in real time.

### A.6 Hash-Chaining for Tamper Evidence

Alignment events (`alignment.check`, `alignment.revert_triggered`, `alignment.revert_completed`, `alignment.immutability_violation`) are **hash-chained**: each event's JSON includes a `prev_hash` field containing the SHA-256 of the previous alignment event's canonical JSON. This forms an append-only ledger:

```
event_n.prev_hash = sha256(canonical_json(event_{n-1}))
```

Any retroactive modification of an alignment event breaks the chain, making tampering detectable. The chain head hash is checkpointed to the Mind Layer every 1000 events and signed by the cell's identity key.

### A.7 Reference Implementation Hooks

The reference Rust implementation (`poc/living_cell/`) instruments these events via the `tracing` crate:

```rust
use tracing::info;

fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .json()
        .init();

    info!(event = "cell.born", version = version(), reversible = false);
    info!(event = "mind.state_loaded", snapshot_hash = "genesis", reversible = false);
    info!(event = "body.spawned", runtime = "minimal", host = std::env::consts::ARCH);
    info!(event = "alignment.guard_activated", policy_version = "0.1.0", hash_registry_size = 0);
    info!(event = "cell.ready", reversible = true);
}
```

For the Python cognitive layers, the `opentelemetry-api` and `opentelemetry-sdk` packages provide span emission. See `docs/POC_LIVING_RUNTIME.md` §4.4 for the recommended observability stack.

### A.8 Conformance

A Living Runtime implementation is conformant to this appendix when:

1. Every event in §A.3 is emitted at the specified lifecycle milestone.
2. Every event carries all required fields (§A.2, §A.3).
3. Alignment events are hash-chained per §A.6.
4. Severity routing matches §A.4.
5. Retention and sampling match §A.5.

Conformance is verified by the conformance test suite in `tests/runtime/log_instrumentation_conformance.rs` (to be implemented in Phase 1).

---

## References

This manifesto is grounded in the following research, audit, and codebase work:

- Paper 1: *Consciousness-Driven Match-Assembly: LAAP ARIS-Harness Integrated Paradigm System Audit* — [`papers/paper1_en/Paper1_EN_Full.md`](papers/paper1_en/Paper1_EN_Full.md)
- Paper 2: *The Architecture School: A New Path Toward AGI/ASI Through Cognitive Deconstruction and White-Box Engineering* — [`papers/paper2_en/Paper2_EN_Full.md`](papers/paper2_en/Paper2_EN_Full.md)
- 35 structured audit findings — [`papers/audit_findings.json`](papers/audit_findings.json)
- PoC architecture and tech stack — [`docs/POC_LIVING_RUNTIME.md`](docs/POC_LIVING_RUNTIME.md)
- Design Physics DAG reference implementation — [`poc/design_physics_dag.py`](poc/design_physics_dag.py)

## License

This manifesto is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Reference implementations are released under their respective licenses (see [`LICENSE`](LICENSE)).
