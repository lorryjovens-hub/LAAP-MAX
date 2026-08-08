---
title: "D-cut: Adaptive Verification Depth Pruning for Batched Speculative Decoding"
source_url: "https://arxiv.org/abs/2607.14647"
arxiv_id: "2607.14647"
ingested: 2026-07-27
type: paper
tags: [speculative-decoding, verification-pruning, batching, inference-acceleration]
categories: [cs.CL]
---

# D-cut: Adaptive Verification Depth Pruning for Batched Speculative Decoding

**Authors**: Tianyu Liu, Yuhao Shen, Rui Cen, Jun Wang et al.

**Published**: 2026-07

## Abstract

Speculative decoding accelerates large language model (LLM) inference without compromising output quality. Recent parallel drafting methods further improve single-request performance by decoupling draft length from drafting latency, enabling longer drafts and higher mean accepted tokens (MAT). However, in batched settings where sequences share a single verification step, the effective acceptance rate becomes the worst-case across the batch — and verification cost scales with draft length regardless of how many tokens are actually accepted. We propose D-cut, which dynamically prunes verification depth at the batch level using an adaptive threshold function. When batch contention is high, D-cut reduces the verification window such that the expected accepted tokens per batch step is maximized. Experiments on A100 GPUs show D-cut achieves up to 1.8× end-to-end speedup over fixed-length batched SD and maintains near-optimal throughput across diverse batch size and draft length regimes.

## Categories

cs.CL

## Key Contributions

1. First work to address verification depth pruning for batched speculative decoding
2. Adaptive threshold function that maximizes expected accepted tokens per batch step
3. Up to 1.8× speedup over fixed-length batched SD
4. Maintains near-optimal throughput across diverse configurations

## Relevance to LAAP

Batched inference optimization is critical for LAAP's production serving. D-cut's adaptive verification pruning addresses the batch-level acceptance contention problem that arises when serving multiple users simultaneously.
