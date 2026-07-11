---
source_url: "https://arxiv.org/abs/2607.02509"
ingested: 2026-07-05
type: paper
intel_score:
  quality: 6.7
  safety: 4.0
  innovation: 6.7
  efficiency: 6.3
  overall: 5.9
tags: [long-context, reasoning, llm, memory, context-window]
---

# ReContext: Recursive Evidence Replay as LLM Harness for Long-Context Reasoning

**Authors:** Yanjun Zhao, Ruizhong Qiu, Tianxin Wei, Yuanchen Bei, Zhining Liu, Lingjie Chen, Ismini Lourentzou

**Published:** 2026-07-02 | **Category:** cs.AI

## Abstract

Understanding and reasoning over long contexts has become a key requirement for deploying large language models (LLMs). Although recent LLMs support increasingly long context windows, they often fail to use relevant evidence already present in the input, revealing a "lost-in-the-middle" problem.

## Relevance to LAAP

Maps to [[aris-memory-system]]'s long-context handling. The recursive evidence replay approach could be adapted for our memory consolidation and retrieval pipeline.

## Key Insights

1. LLMs fail to use relevant evidence even within long context windows
2. Recursive evidence replay improves long-context reasoning
3. "Lost-in-the-middle" problem persists in modern LLMs

## Links

- Paper: https://arxiv.org/abs/2607.02509
- PDF: https://arxiv.org/pdf/2607.02509
