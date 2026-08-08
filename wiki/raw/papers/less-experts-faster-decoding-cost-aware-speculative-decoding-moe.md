---
title: "Less Experts, Faster Decoding: Cost-Aware Speculative Decoding for Mixture-of-Experts"
source_url: "https://arxiv.org/abs/2607.12696"
arxiv_id: "2607.12696"
ingested: 2026-07-27
type: paper
tags: [speculative-decoding, mixture-of-experts, inference-acceleration, cost-aware]
categories: [cs.CL]
---

# Less Experts, Faster Decoding: Cost-Aware Speculative Decoding for Mixture-of-Experts

**Authors**: Jincheng Xie, Runheng Liu, Heyan Huang et al.

**Published**: 2026-07

## Abstract

Sparse Mixture-of-Experts (MoE) models have become an important approach for scaling Large Language Models (LLMs), but their inference efficiency depends strongly on expert activation patterns. Speculative decoding (SD) accelerates autoregressive generation by verifying multiple draft tokens in parallel, yet existing SD methods treat all target model forward passes as equal cost. For MoE, this is inaccurate: the cost of a forward pass depends on how many experts the draft tokens collectively activate. We propose Cost-Aware Speculative Decoding (CASD), which models the per-step cost of verification as a function of the expert activation footprint. Our draft model is trained to minimize the expected cost per accepted token rather than maximize acceptance rate, resulting in draft tokens that are not only likely to be accepted but also cheap to verify. Experiments on Mixtral 8×7B and DeepSeekMoE-16B show CASD achieves 1.9–2.5× speedup over vanilla decoding and 1.3× over acceptance-rate-only SD baselines.

## Categories

cs.CL

## Key Contributions

1. First cost-aware SD formulation for MoE models — models verification cost as function of expert activation footprint
2. Draft model trained to minimize expected cost per accepted token, not maximize acceptance rate
3. 1.9–2.5× speedup over vanilla decoding on Mixtral 8×7B and DeepSeekMoE-16B
4. 1.3× improvement over acceptance-rate-only SD baselines

## Relevance to LAAP

Directly relevant to LAAP's Unified Engine v2 which uses MoE routing. The cost-aware approach aligns with LAAP's desire-driven optimization where resource cost is part of the optimization objective, not just throughput.
