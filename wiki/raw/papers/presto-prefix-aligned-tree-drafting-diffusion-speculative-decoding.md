---
title: "PRESTO: Prefix-Aligned Tree Drafting for Diffusion Speculative Decoding"
source_url: "https://arxiv.org/abs/2607.22634"
arxiv_id: "2607.22634"
ingested: 2026-07-27
type: paper
tags: [speculative-decoding, diffusion-llm, draft-model, tree-drafting, dllm]
categories: [cs.AI]
---

# PRESTO: Prefix-Aligned Tree Drafting for Diffusion Speculative Decoding

**Authors**: Zheng Wang, Zhifan Ye, Qi Cheng, Yong Shan et al.

**Published**: 2026-07

## Abstract

Diffusion Large Language Models (dLLMs) have emerged as a promising alternative to autoregressive (AR) LLMs, generating tokens in parallel. This makes them effective draft models for speculative decoding (SD), producing an entire block of draft tokens in a single forward pass. Yet existing diffusion SD methods use fixed-length block drafts, which may be suboptimal or even degrade speed when the draft block includes tokens that the target would reject, because rejected tokens waste verification cost. We propose PRESTO, which constructs a tree of prefix-aligned draft continuations from the diffusion drafter and verifies them in parallel within a single target forward pass. By aligning all tree paths at their shared prefix, repeated verification of common tokens is eliminated. On MT-Bench, PRESTO achieves up to 1.9× speedup over dLLM+AR SD baselines and 2.3× over vanilla AR decoding.

## Categories

cs.AI

## Key Contributions

1. Prefix-aligned tree drafting for diffusion speculative decoding
2. Eliminates repeated verification of shared prefix tokens across tree paths
3. Parallel verification within a single target forward pass
4. Up to 1.9× speedup over dLLM+AR SD baselines

## Relevance to LAAP

Relevant for LAAP's inference pipeline optimization, particularly if diffusion-based draft models are considered for speculative decoding acceleration.
