---
title: "TIGER: Text-Conditioned Visual Gated Routing with Acceptance Alignment for Multimodal Speculative Decoding"
source_url: "https://arxiv.org/abs/2607.11131"
arxiv_id: "2607.11131"
ingested: 2026-07-27
type: paper
tags: [speculative-decoding, multimodal, vlm, visual-routing, acceptance-alignment]
categories: [cs.CL]
---

# TIGER: Text-Conditioned Visual Gated Routing with Acceptance Alignment for Multimodal Speculative Decoding

**Authors**: Quynh Vo, Cong-Duy Nguyen, Ponhvoan Srey et al.

**Published**: 2026-07

## Abstract

Speculative decoding accelerates autoregressive generation by letting a lightweight drafter propose multiple tokens that are verified by a larger target model. Although effective for text-only LLMs, speculative decoding yields limited gains in VLMs because drafters often diverge on vision-critical content — when generating tokens that describe visual features, the text-only drafter's embeddings lack visual grounding, causing frequent rejections. We propose TIGER, which introduces a lightweight text-conditioned visual gating network that selectively routes vision features into the drafter's hidden states when generating visually relevant tokens. An acceptance alignment objective additionally trains the gating network to maximize the expected acceptance rate. On LLaVA-1.6 and InstructBLIP benchmarks, TIGER achieves 1.8–2.6× speedup over vanilla AR decoding and 1.4× over text-only SD baselines for VLM inference.

## Categories

cs.CL

## Key Contributions

1. First SD system addressing the VLM-specific divergence problem with text-conditioned visual gating
2. Lightweight gating network selectively routes vision features to drafter only when generating visually relevant tokens
3. Acceptance alignment objective maximizing expected acceptance rate
4. 1.8–2.6× speedup over vanilla AR decoding for VLM inference

## Relevance to LAAP

Relevant if LAAP's vision pipeline uses autoregressive VLMs. The selective visual gating approach could be adapted for LAAP's multimodal cognitive cycle.
