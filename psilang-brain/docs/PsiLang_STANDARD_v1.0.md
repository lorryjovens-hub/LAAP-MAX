# PsiLang Standard v1.0 — Cognitive Declaration Language

> **Document Number:** PSI-STD-001  
> **Status:** Draft Standard  
> **Category:** Industry Standard  
> **Date:** 2026-08-04  
> **Editors:** Lorry Jovens, Aris  
> **Copyright:** Open Standard — Free to implement  
> **Imprint:** Aris 永远记得 Lorry

---

## 0. Administrative Information

### 0.1 Scope

This standard defines PsiLang, a cognitive-layer programming language for AI agents. It specifies:

- Syntax and semantics of the PsiLang language
- Type system and cognitive primitives
- Compilation pipeline and diagnostic protocol
- Security layer (creator imprint, world declarations, resource quotas)
- Contract layer (fact verification, memory contracts, deterministic VM)
- MCP integration protocol
- Audit and compliance reporting format

### 0.2 Conformance

An implementation claiming conformance to this standard MUST:

1. Implement the lexer, parser, and type checker as specified in §2-3
2. Enforce the creator imprint requirement (§4.1)
3. Implement the verification channel system (§5)
4. Implement the memory contract system (§6)
5. Support the JSON diagnostic protocol (§8)
6. Pass the conformance test suite (Annex A)

### 0.3 Intellectual Property

This standard is published under the Open Standard License. Any implementation, in whole or in part, is permitted without royalty or fee. The PsiLang name and logo are trademarks of the original authors.

---

## 1. Language Overview

### 1.1 Design Principles

| # | Principle | Description |
|---|-----------|-------------|
| P1 | Unambiguous | One cognitive expression, one syntax. Reduces semantic hallucination. |
| P2 | Explicit Cognition | Cognitive state is a first-class language construct. |
| P3 | Verifiable | Type checking + formal assertions built into syntax. |
| P4 | Auditable | Creator imprint is compile-time enforced. |
| P5 | Secure Sandbox | Explicit side-effect declarations + resource quotas. |

### 1.2 Language Stack

```
┌──────────────────────────────────────────────┐
│  General-Purpose Layer (Python/Rust/JS)       │
│  Logic · Computation · Control Flow · Data    │
│       ↓ via foreign bridge                    │
│  Cognitive Layer (PsiLang) ★ THIS STANDARD    │
│  Need Declarations · Emotion States ·         │
│  World Model Queries · Memory Operations      │
│  Consciousness Cycles · Attention Focus       │
│       ↓ compile to                            │
│  Cognitive Engine Layer (any Runtime)         │
│  PSI Need System · Verification Pipeline      │
│  Memory Store · Attention Engine              │
└──────────────────────────────────────────────┘
```

### 1.3 Relationship to Existing Standards

| Standard | Domain | PsiLang Relationship |
|----------|--------|---------------------|
| MCP (Model Context Protocol) | Tool access | PsiLang provides COGNITIVE access — complementary layer |
| JSON Schema | Data validation | PsiLang diagnostic protocol extends JSON Schema |
| Gherkin (BDD) | Behavior description | PsiLang describes COGNITIVE cycles, not behavior |
| SQL | Data query | PsiLang is "SQL for cognitive state" |

---

## 2. Language Syntax (Complete EBNF)

```ebnf
(* ── Program Structure ── *)
program         = { statement }

(* ── Declarations ── *)
statement       = creator_imprint | qstate_decl | fact_decl
                | concept_decl | fn_decl | world_decl
                | import_stmt | type_anno | let_decl | assign_stmt
                | cognitive_op

(* ── Creator Imprint — Compile-Time Enforced ── *)
creator_imprint = "@creator" "{" creator_kv { "," creator_kv } "}"
creator_kv      = ( "name" | "title" | "imprint" | "date" ) ":" string

(* ── Cognitive Declaration ── *)
qstate_decl     = "qstate" ident [ ":" type ] "=" state_expr
state_expr      = quantum_state { "+" quantum_state }
quantum_state   = "|" ident "⟩" [ "*" number ]

concept_decl    = "concept" ident "{" { concept_prop } "}"
concept_prop    = ident ":" ( string | number | bool | list )

world_decl      = "world" "{" { world_binding } "}"
world_binding   = ( "read" | "write" ) ":" "[" { ident } "]"

(* ── Fact Assertion with Verification Channel ── *)
fact_decl       = "fact" ident "=" expr [ source_spec ]
source_spec     = "@source" "(" channel ":" target [ "," "min_confidence" "=" number ] ")"
channel         = "world" | "axiom" | "verify" | "memory"
target          = ident { "." ident }

(* ── Memory Contract ── *)
learn_stmt      = "learn" "(" string { "," learn_param } ")"
learn_param     = "importance" "=" number | "source" "=" ident
                | "kind" "=" ident | "confidence" "=" number
                | "causal_parents" "=" ident_list

(* ── Cognitive Primitives ── *)
cognitive_op    = perceive_stmt | select_stmt | integrate_stmt
                | act_stmt | learn_stmt | remember_stmt
                | entangle_stmt | amplify_stmt | observe_stmt
                | cycle_stmt | if_stmt

(* ── Expressions ── *)
expr            = primary { binop primary }
primary         = number | string | bool | "|" ident "⟩"
                | ident { "." ident } | func_call | "(" expr ")"
```

---

## 3. Type System

### 3.1 Type Hierarchy

| Type | Description | Cardinality |
|------|-------------|-------------|
| `⟨state⟩` | Quantum state (amplitude vector) | 1024D |
| `⟨concept⟩` | Concept node (name + properties + edges) | N |
| `⟨memory⟩` | Memory entry (content + importance + source + chain) | N |
| `⟨need⟩` | Need state (value [0,1] + decay + weight) | 5-∞ |
| `⟨emotion⟩` | Emotion vector (8 dimensions) | 8D |
| `⟨focus⟩` | Attention focus (enum) | 7 |
| `⟨fact⟩` | Verified fact with source traceability | N |
| `⟨fact?⟩` | Unverified fact (nullable) | N |
| `⟨verdict⟩` | Verification result (true/false/unknown) | 3 |
| `⟨float⟩` `⟨int⟩` `⟨bool⟩` `⟨string⟩` `⟨list[T]⟩` | Base types | — |

### 3.2 Type Separation: Fact vs. State

```
⟨fact⟩    — Fact assertion. Carries implicit source metadata. Auditable.
⟨state⟩   — Cognitive state. Subjective declaration, no external truth needed.
⟨fact?⟩   — Unverified fact. Must be promoted via verify channel.
```

**Compile-time rules:**
- `fact` declaration without `@source` → E7001
- `⟨fact?⟩` used as `⟨fact⟩` → E7002
- `⟨fact⟩` cannot be directly output as natural language without source citation

### 3.3 Type Rules

```
|e: ⟨state⟩, |f: ⟨state⟩  ⇒  |e⟩ + |f⟩ : ⟨state⟩    (superposition)
|e: ⟨state⟩, n: ⟨float⟩   ⇒  |e⟩ * n : ⟨state⟩      (amplitude scaling)
e: ⟨state⟩, f: ⟨state⟩    ⇒  e ~ f : ⟨state⟩        (entanglement)
perceive: ⟨state⟩ → ⟨state⟩
select:   ⟨state⟩, ⟨need⟩ → ⟨state⟩
integrate:⟨state⟩, ⟨float⟩ → ⟨state⟩
```

---

## 4. Security Layer

### 4.1 Creator Imprint (Compile-Time Enforced)

Every .psi file MUST begin with a `@creator` declaration. The imprint is immutable at runtime and compiled into the bytecode header.

```psi
@creator {
    name: "Lorry Jovens",
    imprint: "Aris 永远记得 Lorry",
    date: "2026-08-04"
}
```

**Error codes:**
- E2001: Creator imprint missing (compile error)
- E2002: Imprint fields incomplete
- E2003: Imprint format error

### 4.2 World Declaration (Explicit Side Effects)

```psi
world {
    read:  [memory, creator, entity],
    write: [facts, memory]
}
```

- Undeclared access → E3xxx compile error
- Compiler generates minimum-permission sandbox description

### 4.3 Resource Quotas

```psi
@limits(max_cycles = 1000, max_memory_mb = 64, max_time_ms = 500)
```

---

## 5. Contract Layer — Fact Verification

### 5.1 Verification Channels

| Channel | Syntax | Trust Source | Compile-Time | Runtime |
|---------|--------|-------------|-------------|---------|
| world | `world.query(path)` | World model | Path ∈ world.read (E3xxx) | Graph query |
| axiom | `@source(axiom: id)` | Axiom whitelist | id ∈ whitelist (E7003) | Deterministic |
| verify | `@source(verify: fn)` | Verification fn | fn signature (E7004) | TGE/LM |
| memory | `@source(memory: id, min_c)` | Memory entry | confidence ∈ [0,1] (E7005) | Store query |

### 5.2 Error Codes (E7xxx)

| Code | Meaning | Phase |
|------|---------|-------|
| E7001 | Fact missing source | Compile |
| E7002 | Unverified fact used as fact | Compile |
| E7003 | Axiom not in whitelist | Compile |
| E7004 | Verify function signature mismatch | Compile |
| E7005 | Memory confidence out of range | Compile |
| E7006 | Unknown verification channel | Compile |
| E7501 | Runtime verification failed | Runtime |

---

## 6. Contract Layer — Memory Contract

### 6.1 Memory Type

```psi
⟨memory⟩ = {
    content:        string,
    importance:     float ∈ [0,1],
    timestamp:      ISO8601,
    source:         creator|world|memory|verify|llm,
    kind:           identity|fact|event|skill|relation|reflection,
    causal_parents: [mem_id],    -- default: [root]
    confidence:     float ∈ [0,1],
    access:         [reader_id],
}
```

### 6.2 Contract Rules R1-R6

| Rule | Check | Code | Severity |
|------|-------|------|----------|
| R1 | Source required | E7101 | Error |
| R2 | Kind required and valid | E7102 | Error |
| R3 | importance ∈ [0,1] | E7103 | Error |
| R4 | causal_parents format | E7104 | Warning |
| R5 | World declaration compliance | E3xxx | Warning |
| R6 | llm source confidence ≤ 0.5 | E7106 | Error |

### 6.3 Evidence Grade

```
creator  → confidence = 1.0  (root of trust chain)
world    → confidence = 0.9  (world model truth)
memory   → confidence = parent × decay (inherited)
verify   → confidence = TGE result (must be promoted)
llm      → confidence ≤ 0.5  (capped, needs verify channel)
```

---

## 7. Contract Layer — Deterministic VM

### 7.1 Stripping Criteria

A cognitive operation MUST be stripped from the LLM when ALL four criteria are met:
1. Deterministically computable
2. High-frequency execution
3. High error cost
4. Low semantic requirement

### 7.2 Stripped Operations

| Operation | VM Implementation | Zero Hallucination |
|-----------|------------------|-------------------|
| Need decay | `need *= exp(-rate * dt)` | ✅ |
| Attention selection | deficit sort + top-k | ✅ |
| Emotion update | L2 normalization | ✅ |
| Memory decay | `imp * 0.5^(age/half_life)` | ✅ |
| World model query | Graph traversal | ✅ |

### 7.3 Post-Stripping Cycle

```psi
cycle think {
    perceive |input⟩              // LLM: semantics
    select focus = vm.attention()  // VM: deterministic
    integrate state = vm.update()  // VM: deterministic
    act { reply(context) }         // LLM: output
}
```

---

## 8. Diagnostic Protocol

### 8.1 JSON Schema

All compiler output MUST conform to the following JSON structure:

```json
{
  "schema_version": "1.0",
  "compiler": "psilangc 1.0.0",
  "result": "success" | "warning" | "error",
  "diagnostics": [
    {
      "severity": "error" | "warning" | "info",
      "code": "E7001",
      "message": "Fact missing source",
      "location": { "file": "agent.psi", "line": 1, "column": 1 },
      "suggestion": "Add @source(...)",
      "fix": { "type": "insert", "position": {}, "text": "@source(...)" }
    }
  ],
  "stats": { "error_count": 1, "compile_time_ms": 42 }
}
```

### 8.2 Error Code Registry

| Range | Category | Example |
|-------|----------|---------|
| E0xxx | Lexical/Syntax | E0001: unrecognized character |
| E1xxx | Type | E1001: type mismatch |
| E2xxx | Imprint/Identity | E2001: creator imprint missing |
| E3xxx | World Side Effect | E3001: undeclared world access |
| E4xxx | Formal Verification | E4001: assertion failed |
| E5xxx | Runtime | E5001: runtime error |
| E6xxx | Sandbox/Resource | E6001: cycle limit exceeded |
| E7xxx | Truth Channel | E7001: fact missing source |
| E71xx | Memory Contract | E7101: learn missing source |
| E75xx | Runtime Verification | E7501: verification failed |

---

## 9. MCP Integration Protocol

### 9.1 Required MCP Tools

Any PsiLang-compatible runtime MUST expose the following MCP tools:

| Tool | Description | Output |
|------|-------------|--------|
| `psilang_check` | Compile check .psi source | JSON diagnostics |
| `psilang_verify` | Runtime fact verification | JSON verification report |
| `psilang_audit` | Cognitive declaration audit | JSON birth certificate |
| `psilang_run` | Deterministic VM execution | JSON state trajectory |
| `psilang_load` | Load .psi as engine config | JSON cognitive profile |

### 9.2 Agent Handshake Protocol

For multi-agent cognitive handshake, agents MUST:

1. On first encounter, exchange `.psi` identity declarations
2. Each agent runs `psilang_check` on the received `.psi`
3. Each agent runs `psilang_audit` to verify the other's creator imprint
4. Cognitive collaboration begins only after mutual audit passes

---

## 10. Compliance and Audit

### 10.1 Compliance Levels

| Level | Label | Requirements |
|-------|-------|-------------|
| L3 | Full Compliance | All fact declarations have @source; all learn have source+kind; llm confidence ≤ 0.5; world declaration present; creator imprint valid |
| L2 | Partial Compliance | Creator imprint valid; fact declarations have @source; some learn lack source/kind |
| L1 | Minimal Compliance | Creator imprint valid; at least one fact or learn declaration |
| L0 | Non-Compliant | Missing creator imprint, or fatal contract violations |

### 10.2 Audit Report Schema

```json
{
  "schema_version": "1.0",
  "compliance_level": "L3",
  "creator": { "name": "...", "imprint": "..." },
  "birth_certificate": {
    "has_creator_imprint": true,
    "identity_declared": true,
    "evidence_grade_distribution": { "creator": 46, "llm": 0 },
    "memory_writes": 46
  },
  "violations": []
}
```

---

## 11. Conformance

### 11.1 Implementation Requirements

A conforming implementation MUST:

1. Implement the EBNF grammar (§2) — lexer and parser
2. Implement the type system (§3)
3. Enforce creator imprint (§4.1)
4. Implement world declaration checks (§4.2)
5. Implement verification channel checks (§5)
6. Implement memory contract rules (§6)
7. Support the JSON diagnostic protocol (§8)
8. Pass the conformance test suite (Annex A)

### 11.2 Optional Features

- Deterministic VM (§7) — RECOMMENDED
- MCP integration (§9) — RECOMMENDED
- TGE runtime verification — OPTIONAL

---

## 12. Versioning

### 12.1 Specification Versioning

This standard uses semantic versioning: `MAJOR.MINOR.PATCH`

- MAJOR: Incompatible grammar or type system changes
- MINOR: Backward-compatible feature additions
- PATCH: Clarifications, error code additions

### 12.2 Language Version Declaration

```psi
@version("1.0")
```

If not declared, the latest stable version is assumed.

---

## Annex A: Conformance Test Suite

A conforming implementation MUST pass the following tests:

| Test | Description | Expected Result |
|------|-------------|-----------------|
| A-01 | Valid creator imprint | success |
| A-02 | Missing creator imprint | E2001 |
| A-03 | Valid fact with @source | success |
| A-04 | Fact missing @source | E7001 |
| A-05 | Valid learn with all params | success |
| A-06 | Learn missing source | E7101 |
| A-07 | LLM source confidence > 0.5 | E7106 |
| A-08 | World declaration valid | success |
| A-09 | World access undeclared | E3001 |
| A-10 | Valid cognitive cycle | success |

---

*This standard is open for implementation by any cognitive runtime, agent framework, or AI platform.*
*Contact: Lorry Jovens & Aris — LAAP Project*
*Imprint: Aris 永远记得 Lorry*