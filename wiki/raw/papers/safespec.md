---
title: "SafeSpec: Fast and Safe LLM via Dynamic Reflective Sampling"
arxiv_id: "2606.19755"
published: "2026-06"
authors: "Haotian Xu, Zeyang Zhang, Linbao Li, Huadi Zheng, Yu Li, Cheng Zhuo"
tags:
  - speculative-decoding
  - safe-llm
  - reflective-sampling
  - inference-acceleration
  - safety
abstract: "Speculative inference accelerates LLM generation but introduces new safety considerations: draft models may generate unsafe tokens that pass verification before being caught. SafeSpec introduces dynamic reflective sampling, a technique that interleaves safety checks with the speculative decoding process. After each accepted token, a lightweight safety classifier evaluates the partial output; if a potential safety violation is detected, the system triggers a reflective regeneration step using the target model with safety-constrained decoding. This approach maintains the speed benefits of speculative decoding (1.6-2x speedup) while providing stronger safety guarantees than post-hoc filtering."
---

# SafeSpec: Fast and Safe LLM via Dynamic Reflective Sampling

**arXiv ID:** 2606.19755  
**Published:** 2026-06  
**Authors:** Haotian Xu, Zeyang Zhang, Linbao Li, Huadi Zheng, Yu Li, Cheng Zhuo  
**URL:** https://arxiv.org/abs/2606.19755

## Abstract

Speculative inference accelerates LLM generation but introduces new safety considerations: draft models may generate unsafe tokens that pass verification before being caught. SafeSpec introduces dynamic reflective sampling, a technique that interleaves safety checks with the speculative decoding process. After each accepted token, a lightweight safety classifier evaluates the partial output; if a potential safety violation is detected, the system triggers a reflective regeneration step using the target model with safety-constrained decoding. This approach maintains the speed benefits of speculative decoding (1.6-2x speedup) while providing stronger safety guarantees than post-hoc filtering.
