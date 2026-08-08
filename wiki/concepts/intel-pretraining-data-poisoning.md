---
title: "Pretraining Data Poisoning via Computational Propaganda"
source_url: "https://arxiv.org/abs/2607.15267"
ingested: "2026-07-19"
source_type: arxiv
arxiv_id: "2607.15267"
intel_score:
  quality: 7.5
  safety: 8.5
  innovation: 7.0
  efficiency: 5.5
  overall: 7.1
tags: [ai-safety, alignment, data-poisoning, security, concept]
---

# Pretraining Data Poisoning via Computational Propaganda

## Overview

A landmark paper by Graf, Hajishirzi & Smith (2026) that demonstrates realistic large-scale pretraining data poisoning. Unlike previous work limited to Wikipedia-scale attacks, this paper shows how computational propaganda can contaminate the heterogeneous, large-scale corpora used in actual LLM pretraining.

## Key Findings

1. **Scale**: Demonstrates poisoning at realistic pretraining corpus scale, not just Wikipedia
2. **Heterogeneity**: Shows attacks work across diverse data sources typical of real pretraining mixes
3. **Detection Difficulty**: Poisoned behaviors are hard to detect and mitigate after training

## Implications for LAAP

- LAAP's safety alignment layer must account for large-scale data contamination vectors
- The paper validates our focus on robust training data pipelines
- Suggests need for provenance tracking in pretraining data curation

## Cross-References

- [[intel-online-safety-monitoring]] — Related safety monitoring concept
- [[lorry]] — Safety alignment priorities
- [[raw/sources/arxiv-pretraining-data-poisoning]] — Full source material

## Tags

- ai-safety, alignment, data-poisoning, security, pretraining
