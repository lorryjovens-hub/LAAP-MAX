---
title: "VIA-SD: Verification via Intra-Model Routing for Speculative Decoding"
arxiv_id: "2606.12243"
published: "2026-06"
authors: "Yuchen Xian, Yang He, Yunqiu Xu, Yi Yang"
tags:
  - speculative-decoding
  - intra-model-routing
  - verification
  - inference-acceleration
  - draft-routing
abstract: "Speculative decoding (SD) addresses the high inference cost of large language models by using small draft models to generate candidate tokens. However, standard verification requires the full target model to process all candidate tokens, creating a computational bottleneck. VIA-SD introduces verification via intra-model routing, where only a subset of the target model's layers are activated during verification based on the difficulty of the draft predictions. A lightweight router predicts which layers are needed for reliable verification — easy-to-verify tokens use fewer layers, while hard cases use the full model. This reduces verification cost by 30-45% while maintaining identical output distribution to full verification."
---

# VIA-SD: Verification via Intra-Model Routing for Speculative Decoding

**arXiv ID:** 2606.12243  
**Published:** 2026-06  
**Authors:** Yuchen Xian, Yang He, Yunqiu Xu, Yi Yang  
**URL:** https://arxiv.org/abs/2606.12243

## Abstract

Speculative decoding (SD) addresses the high inference cost of large language models by using small draft models to generate candidate tokens. However, standard verification requires the full target model to process all candidate tokens, creating a computational bottleneck. VIA-SD introduces verification via intra-model routing, where only a subset of the target model's layers are activated during verification based on the difficulty of the draft predictions. A lightweight router predicts which layers are needed for reliable verification — easy-to-verify tokens use fewer layers, while hard cases use the full model. This reduces verification cost by 30-45% while maintaining identical output distribution to full verification.
