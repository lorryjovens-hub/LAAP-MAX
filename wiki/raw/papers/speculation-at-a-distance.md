---
title: "Speculation at a Distance: Where Edge-Cloud Speculative Decoding Actually Pays Off"
arxiv_id: "2606.25091"
published: "2026-06"
authors: "Yuan Lyu, Bharath Irukulapati, Jaya Prakash Champati"
tags:
  - speculative-decoding
  - edge-cloud
  - distributed-inference
  - latency-analysis
  - inference-acceleration
abstract: "Speculative decoding (SD) accelerates LLM inference by using a lightweight draft model to generate candidate tokens that are verified by the target model. However, in edge-cloud settings where the draft runs on-device and the target in the cloud, communication latency can negate the benefits. This paper provides a rigorous analytical framework for determining when edge-cloud SD actually pays off. The authors derive conditions on draft acceptance rates, network latency, and compute ratios under which SD outperforms direct cloud inference. They show that SD is most beneficial when draft acceptance rates exceed 0.7 and network RTT is below 50ms, and provide a practical decision algorithm for adaptive speculation control."
---

# Speculation at a Distance: Where Edge-Cloud Speculative Decoding Actually Pays Off

**arXiv ID:** 2606.25091  
**Published:** 2026-06  
**Authors:** Yuan Lyu, Bharath Irukulapati, Jaya Prakash Champati  
**URL:** https://arxiv.org/abs/2606.25091

## Abstract

Speculative decoding (SD) accelerates LLM inference by using a lightweight draft model to generate candidate tokens that are verified by the target model. However, in edge-cloud settings where the draft runs on-device and the target in the cloud, communication latency can negate the benefits. This paper provides a rigorous analytical framework for determining when edge-cloud SD actually pays off. The authors derive conditions on draft acceptance rates, network latency, and compute ratios under which SD outperforms direct cloud inference. They show that SD is most beneficial when draft acceptance rates exceed 0.7 and network RTT is below 50ms, and provide a practical decision algorithm for adaptive speculation control.
