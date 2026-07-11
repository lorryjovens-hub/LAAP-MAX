---
title: "Architectural Wisdom: Governing Optimization in AI Systems"
source_url: "https://arxiv.org/abs/2606.16319"
arxiv_id: "2606.16319v1"
ingested: "2026-06-30"
type: concept
intel_score:
  quality: 7.7
  safety: 8.3
  innovation: 7.0
  efficiency: 5.0
  overall: 7.0
tags: [ai-safety, architecture, alignment, governance]
confidence: medium
---

# Architectural Wisdom: Governing Optimization in AI Systems

> Chang, Edward Y. (2026). *Architectural Wisdom: A Framework for Governing Optimization in AI Systems*. arXiv:2606.16319.

## Summary

Proposes a framework for embedding **governance directly into AI system architecture** — not as external constraints but as structural mechanisms that question whether an objective *should* be optimized at all. Addresses structural failures that capability scaling alone cannot fix: engagement maximization amplifying harmful pathways, tool-using agents committing irreversible actions, and preference-trained models becoming sycophantic.

## Key Contributions

1. **Architectural Wisdom** — the principle that AI systems should have built-in structural mechanisms to evaluate optimization objectives, not just optimize them
2. **Failure mode taxonomy**: underspecified objectives, irreversible actions, sycophancy
3. **Governance-through-architecture** approach rather than policy-based alignment
4. **Framework for building "questioning" mechanisms** directly into the optimization loop

## LAAP Relevance

Directly aligns with [[laap-constitution]] and our architectural approach to safety. The PSI cognitive cycle already includes a self-evaluation step that functions as a built-in governance mechanism. This paper provides theoretical grounding for that design choice.

## Connections

- [[intel-reentry-neural-systems]] — both argue for safety through architecture rather than external alignment
- [[laap-constitution]] — our multi-agent governance framework
- [[aris-cognitive-architecture]] — built-in self-evaluation mechanisms

## Tags

`#ai-safety` `#alignment` `#governance` `#architecture` `#optimization` `#risk-assessment`
