---
title: "Unlocking Parallelism in Autoregressive Language Models via Speculative Decoding with Progressive Tree Drafting"
source_url: "https://arxiv.org/abs/2607.10661"
arxiv_id: "2607.10661"
ingested: 2026-07-27
type: paper
tags: [speculative-decoding, tree-drafting, parallel-decoding, progressive-drafting]
categories: [cs.CL]
---

# Unlocking Parallelism in Autoregressive Language Models via Speculative Decoding with Progressive Tree Drafting

**Authors**: Zipeng Gao, Zhi Zheng, Qingrong Xia et al.

**Published**: 2026-07

## Abstract

Speculative decoding has significantly accelerated Large Language Model (LLM) inference by alleviating memory-bound bottlenecks. However, traditional speculative decoding typically relies on auxiliary draft modules, incurring significant training and communication overhead. Although recent methods leverage the target model itself as a drafter through early exiting, they struggle to maintain high acceptance rates when generating long draft sequences. We propose Progressive Tree Drafting (PTD), which constructs a dynamic tree of draft candidates using the target model's own early layers, progressively expanding the tree based on confidence scores at each layer. Draft tokens are verified in parallel using tree attention. Without any auxiliary parameters or external draft models, PTD achieves up to 2.3× speedup on LLaMA-2-7B and 2.1× on LLaMA-2-13B across MT-Bench and GSM8K, outperforming Medusa by 1.3× and Eagle by 1.2×.

## Categories

cs.CL

## Key Contributions

1. Self-speculative decoding using target model's own early layers as drafter (no auxiliary parameters)
2. Progressive tree construction based on layer-wise confidence scores
3. Parallel verification using tree attention
4. Up to 2.3× speedup outperforming Medusa (1.3×) and Eagle (1.2×)

## Relevance to LAAP

Self-speculative approach without external draft models is highly relevant. The progressive tree construction based on confidence scores aligns with LAAP's confidence-based verification mechanisms. The 2.3× speedup with zero additional parameters is compelling for LAAP's inference stack.
