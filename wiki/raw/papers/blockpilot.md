---
title: "BlockPilot: Instance-Adaptive Policy Learning for Diffusion-based Speculative Decoding"
arxiv_id: "2606.31315"
published: "2026-06"
authors: "Hao Zhang, Yiming Hu, Yong Wang, Mingqiao Mo, Xin Xiao, Xiangxiang Chu"
tags:
  - speculative-decoding
  - diffusion-lm
  - policy-learning
  - adaptive
  - block-drafting
abstract: "Speculative decoding with diffusion-based draft models can accelerate autoregressive generation by producing blocks of tokens in parallel. However, the optimal drafting policy varies across instances depending on text predictability and computational constraints. BlockPilot introduces instance-adaptive policy learning for diffusion-based speculative decoding. A lightweight policy network observes the current context and adaptively determines the block size, diffusion steps, and verification strategy for each generation step. This instance-level adaptation significantly improves upon fixed-policy baselines, achieving 2.8-3.8x speedup on standard benchmarks. The policy network is trained via reinforcement learning to directly optimize end-to-end generation throughput."
---

# BlockPilot: Instance-Adaptive Policy Learning for Diffusion-based Speculative Decoding

**arXiv ID:** 2606.31315  
**Published:** 2026-06  
**Authors:** Hao Zhang, Yiming Hu, Yong Wang, Mingqiao Mo, Xin Xiao, Xiangxiang Chu  
**URL:** https://arxiv.org/abs/2606.31315

## Abstract

Speculative decoding with diffusion-based draft models can accelerate autoregressive generation by producing blocks of tokens in parallel. However, the optimal drafting policy varies across instances depending on text predictability and computational constraints. BlockPilot introduces instance-adaptive policy learning for diffusion-based speculative decoding. A lightweight policy network observes the current context and adaptively determines the block size, diffusion steps, and verification strategy for each generation step. This instance-level adaptation significantly improves upon fixed-policy baselines, achieving 2.8-3.8x speedup on standard benchmarks. The policy network is trained via reinforcement learning to directly optimize end-to-end generation throughput.
