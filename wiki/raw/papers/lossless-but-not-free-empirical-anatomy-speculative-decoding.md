---
title: "Lossless but Not Free: An Empirical Anatomy of Speculative Decoding on Consumer Hardware"
source_url: "https://arxiv.org/abs/2607.17283"
arxiv_id: "2607.17283"
ingested: 2026-07-27
type: paper
tags: [speculative-decoding, empirical-analysis, consumer-hardware, performance-benchmark]
categories: [cs.AI]
---

# Lossless but Not Free: An Empirical Anatomy of Speculative Decoding on Consumer Hardware

**Authors**: Param Chordiya

**Published**: 2026-07

## Abstract

Single-stream autoregressive decoding of large language models is bound by memory bandwidth: each generated token requires one full forward pass through the target model, and successive passes cannot be parallelized. Speculative decoding restructures this computation: a small draft model proposes K tokens per step, the target model verifies them in a single batched forward pass, and accepted tokens are committed. This is often advertised as "lossless" because no quality degradation is introduced. However, the end-to-end speedup depends on both the acceptance rate and the compute–memory trade-offs of the underlying hardware. On consumer GPUs (RTX 3090, RTX 4090, RTX 6000 Ada), we measure real-world throughput for draft-target pairs at various scales (0.5B→7B, 7B→70B) and find that the achievable speedup is far below theoretical predictions, especially for small-batch inference. We identify four sources of overhead: kernel launch latency, suboptimal CUDA graph utilization, memory-bound draft verification at small batch sizes, and the sequential bottleneck of draft generation itself. We provide practical recommendations for when speculative decoding actually pays off on consumer hardware.

## Categories

cs.AI

## Key Contributions

1. Systematic empirical analysis of speculative decoding on consumer GPUs
2. Identifies 4 sources of overhead reducing real-world speedup below theoretical limits
3. Practical recommendations for when SD actually pays off on consumer hardware
4. Measurements across multiple draft-target pairs and hardware configurations

## Relevance to LAAP

Critical empirical data for LAAP's speculative decoding deployment decisions. The analysis of consumer hardware bottlenecks (kernel launch latency, CUDA graph utilization, draft generation bottleneck) is directly applicable to optimizing LAAP's inference pipeline.
