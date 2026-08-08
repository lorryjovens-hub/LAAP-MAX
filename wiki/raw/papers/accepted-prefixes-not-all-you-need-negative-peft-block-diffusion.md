---
title: "Accepted Prefixes Are Not All You Need: A Negative Result on PEFT-Based Block-Diffusion Drafting"
source_url: "https://arxiv.org/abs/2607.12422"
arxiv_id: "2607.12422"
ingested: 2026-07-27
type: paper
tags: [speculative-decoding, negative-result, block-diffusion, peft, draft-model]
categories: [cs.AI]
---

# Accepted Prefixes Are Not All You Need: A Negative Result on PEFT-Based Block-Diffusion Drafting

**Authors**: Abdurrahman Javat, Allan Kazakov

**Published**: 2026-07

## Abstract

Speculative decoding accelerates autoregressive language model inference by using a cheap drafter to propose multiple future tokens and a target model to verify them. A common design goal is therefore to improve draft quality while reducing auxiliary parameters and systems overhead. We study a negative result: whether a lightweight PEFT adapter (LoRA) on the target model itself can serve as a block-diffusion drafter. Intuitively, the target model's own representations should contain the information needed to predict future tokens, making an external draft model unnecessary. However, we find that PEFT-based block-diffusion drafters consistently underperform independent draft models across multiple model families (LLaMA-3, Qwen-2.5, DeepSeek-V3). The key failure mode is representation collapse: the PEFT adapter's limited expressiveness cannot capture the multi-modal future token distribution, leading to low acceptance rates. We provide analysis of why this happens and suggest that future work should focus on hybrid approaches rather than pure PEFT drafting.

## Categories

cs.AI

## Key Contributions

1. Rigorous negative result showing PEFT-based block-diffusion drafters underperform independent draft models
2. Identifies "representation collapse" as the key failure mode
3. Experiments across LLaMA-3, Qwen-2.5, DeepSeek-V3 model families
4. Suggests hybrid approaches over pure PEFT drafting

## Relevance to LAAP

Important negative result that saves engineering effort — LAAP should not pursue pure PEFT-based drafting. The representation collapse analysis provides insight into the fundamental limitations of lightweight adapters for multi-token prediction.
