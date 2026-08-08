---
title: "AdaFlash: Adaptive Speculative Decoding via On-Policy Distilled Diffusion Drafters"
source_url: "https://arxiv.org/abs/2607.19223"
arxiv_id: "2607.19223"
ingested: 2026-07-27
type: paper
tags: [speculative-decoding, diffusion-llm, draft-model, adaptive, distillation]
categories: [cs.LG]
---

# AdaFlash: Adaptive Speculative Decoding via On-Policy Distilled Diffusion Drafters

**Authors**: Yu-Yang Qian, Hao-Cong Wu, Chen Chen et al.

**Published**: 2026-07

## Abstract

Speculative decoding, in which a lightweight draft model first generates a draft sequence that is then verified in parallel by the target model, has become a prevalent paradigm for accelerating large language model inference. Recent work such as DFlash further boosts drafting efficiency by leveraging block-diffusion language models (dLLMs) as drafters, which produce multiple tokens per forward pass. However, static drafters trained on the target model's offline data distribution may produce draft tokens that the target model systematically rejects. AdaFlash applies on-policy distillation: the diffusion drafter is continuously refined using the target model's own verification outcomes as a reward signal, adapting its draft distribution to match what the target will accept. On MT-Bench and HumanEval, AdaFlash achieves up to 2.4× speedup over vanilla AR decoding and up to 1.5× over fixed diffusion drafters.

## Categories

cs.LG

## Key Contributions

1. On-policy distillation for diffusion drafters — adapts draft distribution using target's verification outcomes
2. Continuous refinement of drafter based on acceptance reward signal
3. Up to 2.4× speedup over vanilla AR decoding
4. Up to 1.5× over static/fixed diffusion drafters

## Relevance to LAAP

The on-policy distillation approach is directly relevant to LAAP's self-improving inference pipeline. Adaptive draft models that learn from verification outcomes align with LAAP's meta-learning cognitive cycle.
