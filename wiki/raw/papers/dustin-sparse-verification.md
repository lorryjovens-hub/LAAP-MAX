---
title: "Dustin: Draft-Augmented Sparse Verification for Efficient Long-Context Generation with Speculative Decoding"
arxiv_id: "2606.24957"
published: "2026-06"
authors: "WenHung Lee, Jian-Jia Chen, Xiaolin Lin, Pei-Shuo Wang, Chi-Chih Chang, Chun-Che Yang, Ning-Chi Huang, Grace Li Zhang, Kai-Chiang Wu"
tags:
  - speculative-decoding
  - long-context
  - sparse-verification
  - draft-augmented
  - inference-acceleration
abstract: "While speculative decoding accelerates LLM generation, the verification step becomes a bottleneck for long-context sequences where the target model must process extended KV caches. Dustin introduces draft-augmented sparse verification, which exploits the draft model's predictions to identify which attention computations in the target model's verification pass can be safely skipped. By using the draft's attention patterns as a guide, Dustin selectively computes only the most relevant attention heads during verification, reducing verification cost by up to 60% for long-context (>8K token) sequences while maintaining output quality within 1% of full verification."
---

# Dustin: Draft-Augmented Sparse Verification for Efficient Long-Context Generation with Speculative Decoding

**arXiv ID:** 2606.24957  
**Published:** 2026-06  
**Authors:** WenHung Lee, Jian-Jia Chen, Xiaolin Lin, et al.  
**URL:** https://arxiv.org/abs/2606.24957

## Abstract

While speculative decoding accelerates LLM generation, the verification step becomes a bottleneck for long-context sequences where the target model must process extended KV caches. Dustin introduces draft-augmented sparse verification, which exploits the draft model's predictions to identify which attention computations in the target model's verification pass can be safely skipped. By using the draft's attention patterns as a guide, Dustin selectively computes only the most relevant attention heads during verification, reducing verification cost by up to 60% for long-context (>8K token) sequences while maintaining output quality within 1% of full verification.
