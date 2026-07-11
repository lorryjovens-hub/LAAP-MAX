---
title: "RLM-Cascade: Response-Level Speculative Decoding for Cost-Efficient LLM API Serving"
arxiv_id: "2606.22840"
published: "2026-06"
authors: "Haifeng Wu, Srinivasan Manoharan, Fangbo Tu, Junhua Zhao, Jian Wan"
tags:
  - speculative-decoding
  - llm-serving
  - response-level
  - cascade
  - cost-efficiency
abstract: "We present RLM-Cascade, a proxy-layer system that applies speculative decoding at the response level rather than the token level for LLM API serving. Instead of using a small draft model to predict individual tokens, RLM-Cascade maintains a cache of complete responses to frequent queries. When a new request arrives, the system retrieves semantically similar cached responses, uses a lightweight ranker to select the best candidate, and sends it to the target LLM for response-level verification. This approach reduces API costs by 35-50% for workloads with repetitive query patterns while maintaining response quality, as the target model only needs to verify rather than generate from scratch."
---

# RLM-Cascade: Response-Level Speculative Decoding for Cost-Efficient LLM API Serving

**arXiv ID:** 2606.22840  
**Published:** 2026-06  
**Authors:** Haifeng Wu, Srinivasan Manoharan, Fangbo Tu, Junhua Zhao, Jian Wan  
**URL:** https://arxiv.org/abs/2606.22840

## Abstract

We present RLM-Cascade, a proxy-layer system that applies speculative decoding at the response level rather than the token level for LLM API serving. Instead of using a small draft model to predict individual tokens, RLM-Cascade maintains a cache of complete responses to frequent queries. When a new request arrives, the system retrieves semantically similar cached responses, uses a lightweight ranker to select the best candidate, and sends it to the target LLM for response-level verification. This approach reduces API costs by 35-50% for workloads with repetitive query patterns while maintaining response quality, as the target model only needs to verify rather than generate from scratch.
