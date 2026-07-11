---
title: "WhiFlash: Accelerating Speculative Decoding with Token-Level Cross-Paradigm Routing"
arxiv_id: "2606.07710"
published: "2026-06"
authors: "Young D. Kwon, Miles Williams, Rui Li, Alexandros Kouris, Stylianos I. Venieris"
tags:
  - speculative-decoding
  - cross-paradigm
  - token-level-routing
  - inference-acceleration
  - draft-selection
abstract: "The autoregressive nature of large language models limits their inference throughput. Speculative decoding mitigates this by using a draft model, but existing approaches commit to a single draft paradigm (e.g., a fixed small model or n-gram cache). WhiFlash introduces token-level cross-paradigm routing, which dynamically selects among multiple draft strategies — small model, n-gram cache, retrieval-augmented prediction, and learned draft heads — on a per-token basis. A lightweight routing network predicts which draft paradigm is most likely to be accepted for each position, enabling the system to adapt to local text predictability. WhiFlash achieves 2.5-3.5x speedup over autoregressive decoding, outperforming single-paradigm speculative decoding methods by 20-40%."
---

# WhiFlash: Accelerating Speculative Decoding with Token-Level Cross-Paradigm Routing

**arXiv ID:** 2606.07710  
**Published:** 2026-06  
**Authors:** Young D. Kwon, Miles Williams, Rui Li, Alexandros Kouris, Stylianos I. Venieris  
**URL:** https://arxiv.org/abs/2606.07710

## Abstract

The autoregressive nature of large language models limits their inference throughput. Speculative decoding mitigates this by using a draft model, but existing approaches commit to a single draft paradigm (e.g., a fixed small model or n-gram cache). WhiFlash introduces token-level cross-paradigm routing, which dynamically selects among multiple draft strategies — small model, n-gram cache, retrieval-augmented prediction, and learned draft heads — on a per-token basis. A lightweight routing network predicts which draft paradigm is most likely to be accepted for each position, enabling the system to adapt to local text predictability. WhiFlash achieves 2.5-3.5x speedup over autoregressive decoding, outperforming single-paradigm speculative decoding methods by 20-40%.
