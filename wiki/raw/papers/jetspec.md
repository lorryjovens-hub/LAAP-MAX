---
title: "JetSpec: Breaking the Scaling Ceiling of Speculative Decoding with Parallel Tree Drafting"
arxiv_id: "2606.18394"
published: "2026-06"
authors: "Lanxiang Hu, Zhaoxiang Feng, Yulun Wu, Haoran Yuan, Yujie Zhao, Yu-Yang Qian, Bojun Wang, Peng Zhao, Daxin Jiang, Yibo Zhu, Tajana Rosing, Hao Zhang"
tags:
  - speculative-decoding
  - parallel-drafting
  - tree-drafting
  - scaling
  - inference-acceleration
abstract: "Speculative decoding's speedup is fundamentally limited by the draft model's ability to generate tokens in parallel. JetSpec breaks this scaling ceiling by introducing parallel tree drafting, where a single draft model generates multiple candidate token sequences organized as a tree structure in one forward pass. The key innovation is a tree-aware attention mechanism that enables the draft model to produce diverse candidate branches simultaneously, which are then verified in parallel by the target model. JetSpec achieves up to 4x speedup on standard LLM benchmarks, significantly outperforming existing speculative decoding methods whose speedup plateaus at 2-3x. The approach scales favorably with model size, achieving larger speedups on larger target models."
---

# JetSpec: Breaking the Scaling Ceiling of Speculative Decoding with Parallel Tree Drafting

**arXiv ID:** 2606.18394  
**Published:** 2026-06  
**Authors:** Lanxiang Hu, Zhaoxiang Feng, Yulun Wu, et al.  
**URL:** https://arxiv.org/abs/2606.18394

## Abstract

Speculative decoding's speedup is fundamentally limited by the draft model's ability to generate tokens in parallel. JetSpec breaks this scaling ceiling by introducing parallel tree drafting, where a single draft model generates multiple candidate token sequences organized as a tree structure in one forward pass. The key innovation is a tree-aware attention mechanism that enables the draft model to produce diverse candidate branches simultaneously, which are then verified in parallel by the target model. JetSpec achieves up to 4x speedup on standard LLM benchmarks, significantly outperforming existing speculative decoding methods whose speedup plateaus at 2-3x. The approach scales favorably with model size, achieving larger speedups on larger target models.
