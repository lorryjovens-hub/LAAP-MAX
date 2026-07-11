---
title: "You Don't Need to Run Every Eval: Rank-2 Structure in LM Benchmarks"
source_url: "https://arxiv.org/abs/2606.24020"
arxiv_id: "2606.24020v1"
ingested: "2026-06-30"
type: concept
intel_score:
  quality: 7.7
  safety: 6.0
  innovation: 6.7
  efficiency: 7.7
  overall: 7.0
tags: [evaluation, efficiency, benchmarking, llm, rank-analysis]
confidence: medium
---

# You Don't Need to Run Every Eval

> Zeng, Yuchen & Papailiopoulos, Dimitris (2026). *You Don't Need to Run Every Eval*. arXiv:2606.24020.

## Summary

Compiles a public score matrix of **84 frontier models** on **133 benchmarks** (2,604 cells, 23.3% filled) and discovers it is approximately **rank-2**: a model's scores across nearly all benchmarks can be predicted from just two numbers. This means the massive benchmark evaluation infrastructure is dramatically overdetermined.

## Key Contributions

1. **Rank-2 discovery** — LM evaluation scores are approximately 2-dimensional; most benchmarks measure the same 2 latent factors
2. **Practical implication** — you can predict ~90% of benchmark performance from 2 strategically chosen evals
3. **Public dataset** — 84 models × 133 benchmarks matrix released for further analysis
4. **Efficiency argument** — saves compute, reduces benchmark overfitting potential

## LAAP Relevance

Directly relevant to how we evaluate our system. Suggests we can dramatically reduce evaluation overhead by identifying the 2-3 evals that capture most of the signal. Also relevant to [[rsi-self-evolution]] — if we can evaluate faster, we can iterate faster.

## Connections

- [[rsi-self-evolution]] — faster evaluation enables faster RSI cycles
- [[zero-llm-pipeline]] — evaluation efficiency for non-LLM pipelines

## Tags

`#evaluation` `#benchmarking` `#efficiency` `#rank-analysis` `#llm` `#meta-learning`
