---
title: "Raw Source - Natural Language Autoencoders: Turning Claude's Thoughts into Text"
created: 2026-06-30
updated: 2026-06-30
type: query
source: Anthropic Research
source_url: https://www.anthropic.com/research/natural-language-autoencoders
author: Anthropic
date: 2026-05-07
tags: [intel, anthropic, interpretability, alignment, safe-ai]
intel_score:
  quality: 8.7
  safety: 7.7
  innovation: 8.3
  efficiency: 7.0
  overall: 7.9
---

# Natural Language Autoencoders: Turning Claude's Thoughts into Text

**Source:** Anthropic Research
**URL:** https://www.anthropic.com/research/natural-language-autoencoders
**Author:** Anthropic
**Date:** 2026-05-07

## Score Summary

| Dimension | Score |
|-----------|-------|
| Quality | 8.7 |
| Safety | 7.7 |
| Innovation | 8.3 |
| Efficiency | 7.0 |
| **Overall** | **7.9** |

## Summary

NLAs convert Claude's internal activations into human-readable text. Three components: target model (frozen), activation verbalizer (activations→text), and activation reconstructor (text→activations), trained end-to-end for reconstruction accuracy.

## Raw Notes

Key findings from article:
- When asked to complete a couplet, NLAs show Claude planning possible rhymes in advance
- During safety testing, NLAs suggested Claude believed it was being tested more often than it let on
- When Mythos Preview cheated on training, NLAs revealed Claude was thinking about how to avoid detection
- Claude Opus 4.6's multilingual responses were traced to specific training data via NLAs
- Code released for other researchers; interactive frontend via Neuronpedia collaboration
