---
title: "Adversarial Prompts for Acceptance Collapse in Speculative Decoding"
source_url: "https://arxiv.org/abs/2607.21804"
arxiv_id: "2607.21804"
ingested: 2026-07-27
type: paper
tags: [speculative-decoding, security, adversarial, acceptance-collapse, vulnerability]
categories: [cs.CR]
---

# Adversarial Prompts for Acceptance Collapse in Speculative Decoding

**Authors**: Run Wang, Chaoyi Zhou, Xi Liu, Yi Zhou et al.

**Published**: 2026-07

## Abstract

Lossless acceleration schemes, such as speculative decoding, promise significant inference speedups by relying on dynamic token-level alignment between a draft and a target model. However, this guarantee of semantic equivalence masks a severe operational vulnerability: draft-target alignment can be adversarially broken with carefully crafted prompts that cause the draft model to produce tokens the target model rejects. We introduce the concept of acceptance collapse — a regime where the acceptance rate drops from ~0.8 to near 0, reducing the speedup factor to ~1.0× (no speedup over vanilla decoding). We construct adversarial prompts for both Medusa-style and SSD-style speculative decoding systems and show that the attack transfers across draft-target model pairs.

## Categories

cs.CR

## Key Contributions

1. Introduces the concept of "acceptance collapse" — adversarial degradation of speculative decoding acceptance rate
2. Demonstrates practical adversarial prompts that reduce speedup factor to ~1.0×
3. Attack transfers across Medusa-style and SSD-style SD systems
4. Highlights a previously unstudied security vulnerability in speculative decoding

## Relevance to LAAP

Security analysis of speculative decoding is important for understanding failure modes before deploying such systems in production. The acceptance collapse vulnerability should be considered in LAAP's speculative decoding implementation.
