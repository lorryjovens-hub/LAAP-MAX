---
title: "AdaptiveSD: A Stability-Aware, Runtime-Adaptive Speculative Decoding Framework with Multi-Policy Orchestration for CPU-Constrained LLM Inference"
arxiv_id: "2607.03876"
published: "2026-07"
authors: "Sadra Saremi"
tags:
  - speculative-decoding
  - llm-inference
  - adaptive-speculation
  - cpu-inference
  - multi-policy
abstract: "With the rise of small quantized GGUF-based language models, speculative decoding has become a practical approach for accelerating LLM inference on CPU-constrained devices. However, existing methods often assume static draft-target configurations and overlook the runtime dynamics of draft model stability. AdaptiveSD introduces a stability-aware, runtime-adaptive speculative decoding framework that dynamically orchestrates multiple draft policies based on real-time acceptance rate monitoring. The system selects between draft models, adjusts speculation lengths, and switches verification strategies to maximize throughput under varying workload conditions. Experimental results on CPU-based deployments show significant latency reductions compared to static speculative decoding baselines."
---

# AdaptiveSD: A Stability-Aware, Runtime-Adaptive Speculative Decoding Framework

**arXiv ID:** 2607.03876  
**Published:** 2026-07  
**Authors:** Sadra Saremi  
**URL:** https://arxiv.org/abs/2607.03876

## Abstract

With the rise of small quantized GGUF-based language models, speculative decoding has become a practical approach for accelerating LLM inference on CPU-constrained devices. However, existing methods often assume static draft-target configurations and overlook the runtime dynamics of draft model stability. AdaptiveSD introduces a stability-aware, runtime-adaptive speculative decoding framework that dynamically orchestrates multiple draft policies based on real-time acceptance rate monitoring. The system selects between draft models, adjusts speculation lengths, and switches verification strategies to maximize throughput under varying workload conditions. Experimental results on CPU-based deployments show significant latency reductions compared to static speculative decoding baselines.
