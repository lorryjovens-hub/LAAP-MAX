---
title: "T²MLR: Transformer with Temporal Middle-Layer Recurrence"
source_url: "https://arxiv.org/abs/2607.15178"
ingested: "2026-07-19"
source_type: arxiv
arxiv_id: "2607.15178"
intel_score:
  quality: 7.0
  safety: 5.0
  innovation: 7.5
  efficiency: 6.0
  overall: 6.4
tags: [arxiv, transformer-alternative, cognitive-architecture, recurrence]
---

# T²MLR: Transformer with Temporal Middle-Layer Recurrence

**Authors**: Ziyang Cai, Xingyu Zhu, Yihe Dong
**Published**: 2026-07-16
**Categories**: cs.CL, cs.AI

## Abstract

Transformer reasoning is limited by autoregressive decoding, which repeatedly compresses rich hidden computation through token space and makes it difficult for intermediate reasoning states to persist across time. We introduce Transformers with Temporal Middle-Layer Recurrence (T²MLR), a transformer variant that adds recurrence at the middle layers, enabling persistent reasoning states across time steps.

## LAAP Relevance

This paper directly addresses a core limitation of autoregressive transformers — the inability to maintain persistent intermediate reasoning states. This is highly relevant to LAAP's cognitive architecture research and the PSI cognitive loop, where persistent state carrying across cognitive cycles is a key requirement.

## Key Insights

1. Middle-layer recurrence allows reasoning states to persist across decoding steps
2. Avoids the bottleneck of compressing all hidden computation through token space
3. Potential to improve multi-step reasoning in LLMs

## Tags

- transformer-alternative, cognitive-architecture, recurrence, persistent-state
