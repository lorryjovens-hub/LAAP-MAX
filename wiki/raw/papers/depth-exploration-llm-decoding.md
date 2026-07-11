---
title: "Depth Exploration for LLM Decoding"
arxiv_id: "2606.29223"
published: "2026-06"
authors: "Weisi Yang, Zipeng Sun, Stephen Xia"
tags:
  - llm-decoding
  - speculative-decoding
  - autoregressive-generation
  - inference-acceleration
  - depth-exploration
abstract: "Autoregressive LLM decoding generates one token at a time, limiting throughput. Depth Exploration proposes a novel decoding strategy that explores multiple candidate generation paths in parallel, committing to the best continuation based on cumulative probability scores. Unlike traditional beam search which maintains full hypotheses, depth exploration selectively expands high-probability branches while pruning low-probability ones using confidence-based thresholds. This approach achieves 2-3x speedup over standard autoregressive decoding on text generation tasks while preserving output quality, bridging the gap between greedy decoding and more expensive search-based methods."
---

# Depth Exploration for LLM Decoding

**arXiv ID:** 2606.29223  
**Published:** 2026-06  
**Authors:** Weisi Yang, Zipeng Sun, Stephen Xia  
**URL:** https://arxiv.org/abs/2606.29223

## Abstract

Autoregressive LLM decoding generates one token at a time, limiting throughput. Depth Exploration proposes a novel decoding strategy that explores multiple candidate generation paths in parallel, committing to the best continuation based on cumulative probability scores. Unlike traditional beam search which maintains full hypotheses, depth exploration selectively expands high-probability branches while pruning low-probability ones using confidence-based thresholds. This approach achieves 2-3x speedup over standard autoregressive decoding on text generation tasks while preserving output quality, bridging the gap between greedy decoding and more expensive search-based methods.
