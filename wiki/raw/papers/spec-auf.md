---
title: "Spec-AUF: Accept-Until-Fail Training under Train-Inference Misalignment for Masked Block Drafters"
arxiv_id: "2607.01893"
published: "2026-07"
authors: "Tianjian Yang, Meng Li"
tags:
  - speculative-decoding
  - block-drafting
  - masked-drafters
  - training
  - inference-acceleration
abstract: "Speculative decoding with masked block drafters offers a promising path to accelerate LLM inference by generating multiple tokens per draft step. However, these drafters suffer from train-inference misalignment: during training they learn to predict full blocks, but during inference only the prefix up to the first rejection is used. Spec-AUF (Accept-Until-Fail) introduces a training objective that explicitly accounts for this misalignment by conditioning the draft model on the accept-until-fail behavior of the verification step. This alignment-aware training improves draft acceptance rates by 15-25% across multiple model scales, translating to significant end-to-end speedups."
---

# Spec-AUF: Accept-Until-Fail Training under Train-Inference Misalignment for Masked Block Drafters

**arXiv ID:** 2607.01893  
**Published:** 2026-07  
**Authors:** Tianjian Yang, Meng Li  
**URL:** https://arxiv.org/abs/2607.01893

## Abstract

Speculative decoding with masked block drafters offers a promising path to accelerate LLM inference by generating multiple tokens per draft step. However, these drafters suffer from train-inference misalignment: during training they learn to predict full blocks, but during inference only the prefix up to the first rejection is used. Spec-AUF (Accept-Until-Fail) introduces a training objective that explicitly accounts for this misalignment by conditioning the draft model on the accept-until-fail behavior of the verification step. This alignment-aware training improves draft acceptance rates by 15-25% across multiple model scales, translating to significant end-to-end speedups.
