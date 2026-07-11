---
title: "Delay-Adaptive Speculation Control for Low-Latency Edge-Cloud LLM Inference"
arxiv_id: "2606.20591"
published: "2026-06"
authors: "Kangkang Sun, Jianhua Li, Xiuzhen Chen, Junyi He, Minyi Guo"
tags:
  - speculative-decoding
  - edge-cloud
  - delay-adaptive
  - low-latency
  - inference-acceleration
abstract: "Speculative decoding accelerates edge-cloud LLM inference by running a lightweight draft model on the edge device while the target model verifies in the cloud. However, variable network delays make it challenging to maintain consistent speedups. Delay-Adaptive Speculation Control introduces a real-time control mechanism that dynamically adjusts speculation length based on measured network RTT and recent draft acceptance rates. When network conditions are favorable, the system speculates more aggressively; under high latency, it falls back to shorter speculation or direct inference. Experiments on real 5G edge networks show 1.5-2x latency reductions compared to fixed-length speculation, with robust performance across varying network conditions."
---

# Delay-Adaptive Speculation Control for Low-Latency Edge-Cloud LLM Inference

**arXiv ID:** 2606.20591  
**Published:** 2026-06  
**Authors:** Kangkang Sun, Jianhua Li, Xiuzhen Chen, Junyi He, Minyi Guo  
**URL:** https://arxiv.org/abs/2606.20591

## Abstract

Speculative decoding accelerates edge-cloud LLM inference by running a lightweight draft model on the edge device while the target model verifies in the cloud. However, variable network delays make it challenging to maintain consistent speedups. Delay-Adaptive Speculation Control introduces a real-time control mechanism that dynamically adjusts speculation length based on measured network RTT and recent draft acceptance rates. When network conditions are favorable, the system speculates more aggressively; under high latency, it falls back to shorter speculation or direct inference. Experiments on real 5G edge networks show 1.5-2x latency reductions compared to fixed-length speculation, with robust performance across varying network conditions.
