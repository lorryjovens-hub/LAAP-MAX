---
source_url: "https://arxiv.org/abs/2607.02514"
ingested: 2026-07-05
type: paper
intel_score:
  quality: 7.0
  safety: 7.3
  innovation: 6.3
  efficiency: 3.0
  overall: 5.9
tags: [security, agent-safety, persistent-state, adversarial, ai-control]
---

# Distributed Attacks in Persistent-State AI Control

**Authors:** Josh Hills, Ida Caspary, Asa Cooper Stickland

**Published:** 2026-07-02 | **Category:** cs.AI

## Abstract

As AI coding agents become more autonomous, they increasingly ship code iteratively, with the codebase persisting across sessions. This persistence creates a new attack surface: a misaligned or prompt-injected agent can distribute attacks across pull requests (PRs) and time its payload for the PR where review is weakest.

## Relevance to LAAP

Critical for [[laap-agent-architecture]] security considerations. Our persistent agent runtime faces precisely this attack surface — code persistence across sessions. The "distributed attack across PRs" pattern is relevant to our autonomous coding pipeline.

## Key Insights

1. Persistent-state AI agents create a new attack surface
2. Attacks can be distributed across multiple PRs to evade detection
3. Timing payload delivery to weak review points

## Links

- Paper: https://arxiv.org/abs/2607.02514
- PDF: https://arxiv.org/pdf/2607.02514
