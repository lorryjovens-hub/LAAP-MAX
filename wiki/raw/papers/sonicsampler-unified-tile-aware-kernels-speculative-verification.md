---
title: "SonicSampler: Unified Tile-Aware Kernels for LLM Sampling and Speculative Verification"
source_url: "https://arxiv.org/abs/2607.20475"
arxiv_id: "2607.20475"
ingested: 2026-07-27
type: paper
tags: [speculative-decoding, gpu-kernel, sampling, verification, inference-optimization]
categories: [cs.AI]
---

# SonicSampler: Unified Tile-Aware Kernels for LLM Sampling and Speculative Verification

**Authors**: Pragaash Ponnusamy, Shivam Sahni, Jue Wang et al.

**Published**: 2026-07

## Abstract

Sampling in LLM inference comprises a combinatorial set of logit processing, token selection, and verification operations for speculative decoding. However, existing implementations either accelerate only subsets of this pipeline, rely on multiple kernel launches, or assume homogeneous sampling behavior across sequences. We introduce SonicSampler, a set of unified, tile-aware kernels that fuse logit processing, top-p/top-k filtering, sampling (multinomial, argmax), and speculative verification (rejection sampling, tree attention) into a single GPU kernel. SonicSampler supports variable sampling parameters per sequence, dynamic tree structures, and heterogeneous batch configurations. On NVIDIA H100 GPUs, SonicSampler achieves up to 4.2× end-to-end speedup over the vLLM + FlashInfer sampling pipeline and up to 3.5× over TRT-LLM for speculative decoding workloads.

## Categories

cs.AI

## Key Contributions

1. Unified tile-aware GPU kernels fusing logit processing, sampling, and verification
2. Variable sampling parameters per sequence in a single kernel
3. Supports dynamic tree structures and heterogeneous batch configurations
4. Up to 4.2× speedup over vLLM/FlashInfer pipeline

## Relevance to LAAP

GPU kernel-level optimization is directly applicable to LAAP's inference pipeline. The fused sampling + verification kernel approach could be integrated into the Unified Engine's speculative decoding infrastructure.
