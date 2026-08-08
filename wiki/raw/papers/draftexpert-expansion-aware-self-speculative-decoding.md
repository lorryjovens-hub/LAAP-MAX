---
title: "DraftExpert: Expansion-Aware Self-Speculative Decoding for End-Device MoE Inference"
source_url: "https://arxiv.org/abs/2607.24434"
arxiv_id: "2607.24434"
ingested: 2026-07-27
type: paper
tags: [speculative-decoding, moe, inference-acceleration, self-speculative, edge-device]
categories: [cs.LG]
---

# DraftExpert: Expansion-Aware Self-Speculative Decoding for End-Device MoE Inference

**Authors**: Dengke Han et al.

**Published**: 2026-07

## Abstract

Large Mixture-of-Experts (MoE) language models are attractive for end-device deployment because only a small subset of experts is active per token, but their routed expert weights often exceed accelerator memory. We target latency-critical single-user settings where routed experts are staged on demand from host memory. Observing that consecutive tokens often activate overlapping expert sets, we propose DraftExpert, a self-speculative decoding framework that uses the already-loaded shared + dense experts as the draft model and speculatively generates multiple tokens before routing to full routed experts. An expansion-aware acceptance mechanism adaptively adjusts draft length based on expert activation patterns, and a tree-structured drafting strategy is employed to increase throughput. On MT-Bench, DraftExpert achieves up to 2.1× speedup over vanilla MoE decoding on an NVIDIA Jetson Orin NX 16GB.

## Categories

cs.LG

## Key Contributions

1. Self-speculative decoding for MoE models using already-loaded shared/dense experts as draft model (no additional parameters)
2. Expansion-aware acceptance mechanism that adapts draft length based on expert activation patterns
3. Tree-structured drafting for increased throughput
4. Targets end-device MoE inference (NVIDIA Jetson Orin NX)
5. Up to 2.1× speedup on MT-Bench

## Relevance to LAAP

MoE inference optimization is directly relevant to LAAP's Unified Engine, which uses mixture-of-experts routing. The self-speculative approach without additional draft model parameters is particularly interesting for resource-constrained deployment scenarios.
