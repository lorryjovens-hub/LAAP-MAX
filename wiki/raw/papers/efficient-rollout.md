---
title: "EfficientRollout: System-Aware Self-Speculative Decoding for RL Rollouts"
arxiv_id: "2606.18967"
published: "2026-06"
authors: "Minseo Kim, Minjae Lee, Seunghyuk Oh, Kevin Galim, Donghoon Kim, Coleman Hooper, Harman Singh, Amir Gholami, Hyung Il Koo, Wonjun Kang"
tags:
  - speculative-decoding
  - self-speculation
  - reinforcement-learning
  - rl-rollouts
  - inference-acceleration
abstract: "Reinforcement learning (RL) has become a representative post-training paradigm for LLMs, but the rollout stage remains the key bottleneck. EfficientRollout introduces a system-aware self-speculative decoding framework tailored for RL training pipelines. The key insight is that during RL rollouts, the same LLM is used to generate multiple trajectories from the same checkpoint — the model state can be forked at intermediate layers to create lightweight draft heads that speculate on future tokens without requiring a separate draft model. EfficientRollout achieves 2-3x acceleration in RL rollout generation while maintaining the diversity and quality required for effective RL training, significantly reducing the end-to-end RL training time."
---

# EfficientRollout: System-Aware Self-Speculative Decoding for RL Rollouts

**arXiv ID:** 2606.18967  
**Published:** 2026-06  
**Authors:** Minseo Kim, Minjae Lee, Seunghyuk Oh, et al.  
**URL:** https://arxiv.org/abs/2606.18967

## Abstract

Reinforcement learning (RL) has become a representative post-training paradigm for LLMs, but the rollout stage remains the key bottleneck. EfficientRollout introduces a system-aware self-speculative decoding framework tailored for RL training pipelines. The key insight is that during RL rollouts, the same LLM is used to generate multiple trajectories from the same checkpoint — the model state can be forked at intermediate layers to create lightweight draft heads that speculate on future tokens without requiring a separate draft model. EfficientRollout achieves 2-3x acceleration in RL rollout generation while maintaining the diversity and quality required for effective RL training, significantly reducing the end-to-end RL training time.
