---
title: "DeLS-Spec: Decoupled Long-Short Contexts for Parallel Speculative Drafting"
source_url: "https://arxiv.org/abs/2607.07409"
arxiv_id: "2607.07409"
ingested: 2026-07-27
type: paper
tags: [speculative-decoding, long-context, short-context, parallel-drafting, context-decoupling]
categories: [cs.CL]
---

# DeLS-Spec: Decoupled Long-Short Contexts for Parallel Speculative Drafting

**Authors**: Hong-Kai Zheng, Piji Li

**Published**: 2026-07

## Abstract

Speculative decoding accelerates LLM inference by drafting multiple tokens and verifying them in parallel. Block-parallel drafters such as DFlash further improve drafting efficiency by predicting an entire block in one pass, but their position-wise predictions lack explicit intra-block causal conditioning — each position is predicted independently from the same context representation. DeLS-Spec introduces a decoupled long-short context architecture where the draft model uses a long-range context (the full prefix) for global coherence and a short-range context (recent draft positions) for local causal conditioning. This maintains the parallel drafting advantage while recovering the intra-block causal dependencies that independent predictions lose. On LLaMA-2-7B and Qwen-2.5-7B, DeLS-Spec achieves 2.4–2.8× speedup over vanilla AR decoding and consistently outperforms DFlash-style independent block drafters by 1.2–1.3×.

## Categories

cs.CL

## Key Contributions

1. Decoupled long-short context architecture for parallel speculative drafting
2. Long-range context (full prefix) for global coherence + short-range context (recent draft positions) for local causal conditioning
3. Recovers intra-block causal dependencies without sacrificing parallelism
4. 2.4–2.8× speedup over vanilla AR decoding, 1.2–1.3× over DFlash-style drafters

## Relevance to LAAP

The long-short context decoupling is a novel architectural insight for improving block-drafter quality. Relevant to LAAP's speculative decoding pipeline where maintaining causal consistency in parallel draft generation is a key challenge.
