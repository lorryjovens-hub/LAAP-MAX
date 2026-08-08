---
title: "Trees from Marginals: Autoregressive Drafting with Factorized Priors"
source_url: "https://arxiv.org/abs/2607.06763"
arxiv_id: "2607.06763"
ingested: 2026-07-27
type: paper
tags: [speculative-decoding, factorized-priors, tree-drafting, autoregressive-drafting, marginals]
categories: [cs.LG]
---

# Trees from Marginals: Autoregressive Drafting with Factorized Priors

**Authors**: Yuma Oda, Ryan Mathieu, Roman Knyazhitskiy et al.

**Published**: 2026-07

## Abstract

Speculative decoding greatly increases the interactivity of autoregressive language models by trading off computation for extra tokens generated in a single forward pass. Factorized draft models are especially efficient because they predict future-token marginals in parallel, but their independence assumption means they cannot construct the joint draft distribution needed for tree-based verification. Trees from Marginals (TfM) bridges this gap: it takes any factorized (independent) drafter and, without retraining, builds a conditional tree of draft candidates using the marginal predictions as a factorized prior. The tree structure is constructed via a lightweight autoregressive refinement process that adds conditional dependencies post-hoc. TfM achieves 2.1–2.5× speedup on LLaMA-2 and Qwen-2.5 using standard factorized drafters (which alone achieve only 1.4–1.6×), demonstrating that the gap between independent and joint draft models can be substantially closed with a post-hoc tree construction method.

## Categories

cs.LG

## Key Contributions

1. Post-hoc tree construction from any factorized (independent) drafter without retraining
2. Lightweight autoregressive refinement adds conditional dependencies to independent marginals
3. 2.1–2.5× speedup vs 1.4–1.6× for factorized-only drafters
4. Bridges the gap between independent and joint draft models

## Relevance to LAAP

The post-hoc approach is significant because it means LAAP can use efficient factorized drafters while still getting tree-structured verification benefits. No retraining required — a practical advantage for deployment.
