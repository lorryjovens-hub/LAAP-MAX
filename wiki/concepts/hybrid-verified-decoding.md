---
title: Hybrid Verified Decoding
type: concept
tags: [speculative-decoding, verification, inference-acceleration, confidence-scheduling]
related: [self-speculative-decoding, blockwise-parallel-decoding, psi-n]
source: survey
---

# Hybrid Verified Decoding

Hybrid Verified Decoding refers to methods that **learn to dynamically allocate verification budget** across speculative tokens or positions, rather than using a fixed acceptance criterion (like standard rejection sampling in speculative decoding).

## Key Ideas

### Adaptive Acceptance Threshold
Instead of accepting/rejecting each draft token with a fixed threshold, learn or adapt the threshold:
- **Hybrid Verified Decoding** (2606.01019): Learning to Allocate Verification in Speculative Decoding
- **Performance-Driven Policy Optimization** (2605.14978): Adaptive Windowing

### Sparse Verification
Only verify a subset of tokens, using confidence scores to decide which:
- **Dustin** (2606.24957): Draft-Augmented Sparse Verification for Long-Context Generation
- **SSV** (2605.19893): Sparse Speculative Verification

### Intra-Model Routing
Route verification internally based on hidden state quality:
- **VIA-SD** (2606.12243): Verification via Intra-Model Routing

### Multi-Policy Orchestration
Use multiple verification strategies and select the best:
- **AdaptiveSD** (2607.03876): Runtime-Adaptive Multi-Policy Orchestration

## Connection to LAAP's PSI Architecture
- LAAP's PSI cognitive loop already uses dynamic scheduling — verification budget allocation is a natural extension
- The "confidence-scheduled" aspect maps to PSI's uncertainty-aware emotional modulation
- Sparse verification aligns with LAAP's token optimization strategy (only verify what matters)

## Related Concepts
- [[self-speculative-decoding]]
- [[blockwise-parallel-decoding]]
