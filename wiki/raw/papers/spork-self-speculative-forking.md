---
title: "SPORK: Self-Speculative Forking to Accelerate Agentic LLM Inference"
arxiv_id: "2607.03333"
published: "2026-07"
authors: "Huajun Bai, Weiwei Lv, Huichuan Zheng, Youyou Lu, Jiwu Shu"
tags:
  - speculative-decoding
  - self-speculation
  - agentic-llm
  - inference-acceleration
  - forking
abstract: "LLM-based agentic systems require multiple rounds of inference for planning, tool use, and reflection, creating significant latency challenges. SPORK introduces self-speculative forking, a technique that accelerates agentic LLM inference by forking intermediate states from the target model itself to serve as draft proposals without requiring a separate draft model. The key insight is that in multi-turn agentic workflows, intermediate computation states can be repurposed to speculate on future tokens. SPORK achieves 1.8x-2.3x speedups on agentic benchmarks while maintaining output quality, eliminating the need for training or deploying separate draft models."
---

# SPORK: Self-Speculative Forking to Accelerate Agentic LLM Inference

**arXiv ID:** 2607.03333  
**Published:** 2026-07  
**Authors:** Huajun Bai, Weiwei Lv, Huichuan Zheng, Youyou Lu, Jiwu Shu  
**URL:** https://arxiv.org/abs/2607.03333

## Abstract

LLM-based agentic systems require multiple rounds of inference for planning, tool use, and reflection, creating significant latency challenges. SPORK introduces self-speculative forking, a technique that accelerates agentic LLM inference by forking intermediate states from the target model itself to serve as draft proposals without requiring a separate draft model. The key insight is that in multi-turn agentic workflows, intermediate computation states can be repurposed to speculate on future tokens. SPORK achieves 1.8x-2.3x speedups on agentic benchmarks while maintaining output quality, eliminating the need for training or deploying separate draft models.
