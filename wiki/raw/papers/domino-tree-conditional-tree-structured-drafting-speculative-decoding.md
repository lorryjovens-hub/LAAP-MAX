---
title: "DominoTree: Conditional Tree-Structured Drafting with Domino for Speculative Decoding"
source_url: "https://arxiv.org/abs/2607.08642"
arxiv_id: "2607.08642"
ingested: 2026-07-27
type: paper
tags: [speculative-decoding, tree-drafting, block-diffusion, conditional-drafting, domino]
categories: [cs.CL]
---

# DominoTree: Conditional Tree-Structured Drafting with Domino for Speculative Decoding

**Authors**: Saw S. Lin, Jyh-Shing Roger Jang

**Published**: 2026-07

## Abstract

Speculative decoding accelerates LLM inference by drafting several tokens and verifying them in parallel. Block-diffusion drafters such as DFlash produce a draft block in one pass but model only per-position marginals, and best-first tree methods such as DDTree expand candidate trees from those marginals using a fixed expansion budget. DominoTree extends this paradigm by introducing conditional tree-structured drafting: the draft model explicitly learns the conditional dependencies between draft positions, producing a joint distribution over candidate suffixes rather than independent per-position predictions. A Domino-based expansion policy then allocates the verification budget dynamically, evaluating the most promising branches first. On LLaMA-2-7B and Qwen-2.5-7B, DominoTree achieves up to 2.8× speedup over vanilla AR decoding and up to 1.4× over fixed-tree block-diffusion drafters.

## Categories

cs.CL

## Key Contributions

1. Conditional tree-structured drafting — draft model learns conditional dependencies between positions (joint distribution, not independent marginals)
2. Domino-based dynamic expansion policy for verification budget allocation
3. 2.8× speedup over vanilla AR decoding
4. 1.4× over fixed-tree block-diffusion drafters (DDTree, DFlash)

## Relevance to LAAP

The conditional tree-structured drafting approach addresses a fundamental limitation of block-diffusion drafters (independent position predictions). The joint distribution modeling is relevant to LAAP's speculative decoding pipeline for improving draft quality.
