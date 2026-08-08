---
title: "SpecLA: Efficient Speculative Decoding for Linear-Attention Models"
source_url: "https://arxiv.org/abs/2607.16673"
arxiv_id: "2607.16673"
ingested: 2026-07-27
type: paper
tags: [speculative-decoding, linear-attention, state-space-models, inference-acceleration]
categories: [cs.CL]
---

# SpecLA: Efficient Speculative Decoding for Linear-Attention Models

**Authors**: Zhibin Wang, Xuying Han, Zhaohua Yang et al.

**Published**: 2026-07

## Abstract

Linear-attention models replace the growing KV cache with recurrent states, but autoregressive decoding still reads, updates, and writes these states one token at a time. Speculative decoding can reduce this cost by verifying several draft tokens in one target pass, yet existing speculative systems are designed for softmax attention and do not account for the unique properties of linear-attention state reuse. We propose SpecLA, which introduces a state-reuse verification kernel that processes multiple draft tokens in parallel while correctly maintaining the recurrent state. A key insight is that linear-attention states can be efficiently combined across the draft sequence, enabling verification without sequential state recomputation. Experiments on Mamba-2 and Based architectures show SpecLA achieves 1.6–2.3× speedup over standard AR decoding while preserving the theoretical losslessness guarantee.

## Categories

cs.CL

## Key Contributions

1. First speculative decoding system specifically designed for linear-attention models
2. State-reuse verification kernel enabling parallel verification without recurrent state recomputation
3. Experimental validation on Mamba-2 and Based architectures
4. 1.6–2.3× speedup over standard AR decoding

## Relevance to LAAP

Linear attention is a key component of LAAP's cognitive cycle for efficient long-context processing. SpecLA's state-reuse approach could be integrated into LAAP's inference engine for linear-attention based subsystems.
