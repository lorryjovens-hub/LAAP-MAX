---
source_url: "https://arxiv.org/abs/2607.02501"
ingested: 2026-07-05
type: paper
intel_score:
  quality: 7.5
  safety: 4.0
  innovation: 7.5
  efficiency: 8.0
  overall: 6.8
tags: [embodied-ai, inference, runtime, edge-devices, vla]
---

# Embodied.cpp: A Portable Inference Runtime of Embodied AI Models on Heterogeneous Robots

**Authors:** Ling Xu, Chuyu Han, Borui Li, Hao Wu, Shiqi Jiang, Ting Cao, Chuanyou Li, Sheng Zhong, Shuai Wang

**Published:** 2026-07-02 | **Category:** cs.RO, cs.CV, cs.OS

## Abstract

Embodied AI models now span vision-language-action (VLA) models and world-action models (WAMs), but practical deployment remains fragmented across model-specific Python stacks, backend assumptions, and robot-side glue code, especially on heterogeneous edge devices.

## Relevance to LAAP

Strong relevance to [[aria-embedded-deployment]] and our embedded AI strategy. The portable C++ runtime approach mirrors our goals for lightweight inference deployment. Could inform [[cosyvoice-windows-deployment]] and other edge inference pipelines.

## Key Insights

1. Unified C++ inference runtime for VLA and WAM models
2. Portable across heterogeneous edge devices and robots
3. Addresses fragmentation in embodied AI deployment

## Links

- Paper: https://arxiv.org/abs/2607.02501
- PDF: https://arxiv.org/pdf/2607.02501
