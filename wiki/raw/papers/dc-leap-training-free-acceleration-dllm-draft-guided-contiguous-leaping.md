---
title: "DC-Leap: Training-Free Acceleration of dLLMs via Draft-Guided Contiguous Leaping Decoding"
source_url: "https://arxiv.org/abs/2607.20467"
arxiv_id: "2607.20467"
ingested: 2026-07-27
type: paper
tags: [diffusion-llm, inference-acceleration, training-free, draft-guided, contiguous-leaping]
categories: [cs.AI]
---

# DC-Leap: Training-Free Acceleration of dLLMs via Draft-Guided Contiguous Leaping Decoding

**Authors**: Yanhua Jiao, Tianyi Wu, Xiaoxi Sun et al.

**Published**: 2026-07

## Abstract

While parallel decoding is central to the efficiency of Diffusion Large Language Models (dLLMs), current strategies are often hindered by overly conservative confidence thresholds. These thresholds, necessitated by the Joint Probability Dependence Error (JPDE), result in redundant denoising iterations that waste compute. We propose DC-Leap, a training-free acceleration method that introduces a lightweight external draft model to guide the dLLM's decoding. The draft model proposes contiguous token leaps, and the dLLM only needs to verify the leap endpoints rather than every intermediate denoising step. A key theoretical contribution is proving that draft-guided leaping eliminates JPDE when the draft model's acceptance rate exceeds a problem-dependent threshold, enabling aggressive leaps without quality loss. Experiments show DC-Leap achieves 1.6–2.2× speedup across various dLLM architectures (MDLM, SSD-LM, D3PM) with zero training cost.

## Categories

cs.AI

## Key Contributions

1. First training-free acceleration for dLLMs using draft-guided contiguous leaping
2. Theoretical proof that draft-guided leaping eliminates JPDE above an acceptance rate threshold
3. 1.6–2.2× speedup with zero training cost
4. Works across MDLM, SSD-LM, D3PM architectures

## Relevance to LAAP

Training-free acceleration is highly relevant. The theoretical connection between draft acceptance rate and the elimination of JPDE provides a principled basis for confidence-threshold tuning. Relevant if LAAP uses diffusion-based models.
