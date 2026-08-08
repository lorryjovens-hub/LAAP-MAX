---
title: Diffusion LLM Speculation
type: concept
tags: [speculative-decoding, diffusion-llm, block-decoding, inference-acceleration]
related: [blockwise-parallel-decoding, self-speculative-decoding, markov]
source: survey
---

# Diffusion LLM Speculation

Diffusion LLM speculation uses **diffusion-based language models** as the draft model (or jointly as drafter+verifier) in speculative decoding. This is a rapidly emerging paradigm as diffusion LMs mature.

## Why Diffusion LMs as Drafters

Diffusion language models generate text through iterative refinement rather than left-to-right:
- **Parallel generation**: Can produce entire blocks simultaneously
- **Flexible ordering**: Not constrained to causal left-to-right order
- **Global coherence**: Naturally captures bidirectional context

## Key Papers

### Pure Diffusion Drafting
- **SimSD** (2606.02544): Simple Speculative Decoding in Diffusion Language Models — investigates minimal viable diffusion drafting
- **D^2SD** (2606.04446): Accelerating Speculative Decoding with Dual Diffusion Draft Models
- **Accelerating Speculative Diffusions via Block Verification** (2606.13426): Formal analysis of block verification for diffusion drafters

### Hybrid (Diffusion + AR)
- **Teaching Diffusion to Speculate Left-to-Right** (2606.11552): Adapting diffusion models for AR-compatible speculation
- **SDAR** (2510.06303): Synergistic Diffusion-AutoRegression Paradigm

### Cost-Aware Diffusion Drafting
- **Cost-Aware Diffusion Draft Trees** (2606.01813): Building draft trees with diffusion cost models
- **BlockPilot** (2606.31315): Instance-Adaptive Policy Learning

## Relevance to LAAP
- LAAP's V12.5 Markov generator produces sequences with controllable quality-speed tradeoffs — analogous to diffusion drafters
- Combining Markov (draft) with LLM (verify) mirrors the diffusion-AR hybrid pattern
- Global coherence of diffusion LMs aligns with LAAP's quantum subconscious long-range structure

## Related Concepts
- [[blockwise-parallel-decoding]]
- [[hybrid-verified-decoding]]
- [[markov]]
