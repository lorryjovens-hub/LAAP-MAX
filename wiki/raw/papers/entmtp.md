---
title: "EntMTP: Accelerating LLM Inference with Entropy Guided Multi Token Prediction"
arxiv_id: "2606.27550"
published: "2026-06"
authors: "Carrie Chen"
tags:
  - multi-token-prediction
  - entropy-guided
  - self-speculative-decoding
  - inference-acceleration
  - adaptive-speculation
abstract: "Multi-token prediction has been shown to increase data density during training, improve downstream text-generation quality, and serves as the de facto approach for self-speculative decoding. Existing foundation and open source models that use MTP heads commit to a static tree-based attention topology throughout the entire generation sequence, meaning the speculation depth stays constant regardless of context. EntMTP proposes Entropy-guided Multi-Token Prediction, a training-free scheduler that toggles between tree-based attention topologies conditioned on a running estimate of local generation entropy. By matching speculation depth to context predictability, EntMTP maximizes expected accepted-token throughput. When evaluated across Humaneval, ShareGPT, GSM8k, and LitBench benchmarks, EntMTP consistently achieves a 1.15x speedup against Hydra and peak speedup of 1.36x against Medusa baselines."
---

# EntMTP: Accelerating LLM Inference with Entropy Guided Multi Token Prediction

**arXiv ID:** 2606.27550  
**Published:** 2026-06  
**Authors:** Carrie Chen  
**URL:** https://arxiv.org/abs/2606.27550

## Abstract

Multi-token prediction has been shown to increase data density during training, improve downstream text-generation quality, and serves as the de facto approach for self-speculative decoding. Existing foundation and open source models that use MTP heads commit to a static tree-based attention topology throughout the entire generation sequence, meaning the speculation depth stays constant regardless of context. EntMTP proposes Entropy-guided Multi-Token Prediction, a training-free scheduler that toggles between tree-based attention topologies conditioned on a running estimate of local generation entropy. By matching speculation depth to context predictability, EntMTP maximizes expected accepted-token throughput. When evaluated across Humaneval, ShareGPT, GSM8k, and LitBench benchmarks, EntMTP consistently achieves a 1.15x speedup against Hydra and peak speedup of 1.36x against Medusa baselines.
