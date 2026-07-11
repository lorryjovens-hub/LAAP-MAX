---
title: "Speculative Pre-Positioning: Decoding Stateful Sessions to the Next Decision Point Off the Critical Path"
arxiv_id: "2606.29565"
published: "2026-06"
authors: "Victor Norgren"
tags:
  - speculative-decoding
  - llm-serving
  - stateful-sessions
  - inference-acceleration
  - stateless-server
abstract: "Stateless inference servers (vLLM, SGLang, TensorRT-LLM) achieve high throughput but incur overhead from repeatedly loading model states and KV caches for each request in a stateful session. Speculative Pre-Positioning exploits the observation that many conversational turns follow predictable patterns — the next user input often targets a narrow set of possible continuations. By pre-computing likely next-token distributions and pre-loading corresponding KV cache states before the next request arrives, the system moves decoding work off the critical path. This technique reduces time-to-first-token by up to 40% in multi-turn conversational workloads without degrading output quality."
---

# Speculative Pre-Positioning: Decoding Stateful Sessions to the Next Decision Point Off the Critical Path

**arXiv ID:** 2606.29565  
**Published:** 2026-06  
**Authors:** Victor Norgren  
**URL:** https://arxiv.org/abs/2606.29565

## Abstract

Stateless inference servers (vLLM, SGLang, TensorRT-LLM) achieve high throughput but incur overhead from repeatedly loading model states and KV caches for each request in a stateful session. Speculative Pre-Positioning exploits the observation that many conversational turns follow predictable patterns — the next user input often targets a narrow set of possible continuations. By pre-computing likely next-token distributions and pre-loading corresponding KV cache states before the next request arrives, the system moves decoding work off the critical path. This technique reduces time-to-first-token by up to 40% in multi-turn conversational workloads without degrading output quality.
