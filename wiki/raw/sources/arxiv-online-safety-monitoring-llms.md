---
source_url: "https://arxiv.org/abs/2607.02510"
ingested: 2026-07-05
type: paper
intel_score:
  quality: 6.7
  safety: 8.0
  innovation: 6.7
  efficiency: 5.0
  overall: 6.6
tags: [safety, alignment, llm, monitoring, anomaly-detection]
---

# Online Safety Monitoring for LLMs

**Authors:** Mona Schirmer, Metod Jazbec, Alexander Timans, Christian Naesseth, Maja Waldron, Eric Nalisnick

**Published:** 2026-07-02 | **Category:** cs.AI, cs.CL, cs.LG

## Abstract

Despite alignment training, LLMs remain prone to generating unsafe outputs at deployment time. Monitoring outputs online and raising an alarm when safety can no longer be assumed is therefore critical. This paper studies a simple real-time monitor that turns a verifier signal from an external model into an alarm — a statistical process control approach for LLM safety.

## Relevance to LAAP

Directly maps to [[aris-cognitive-loop]]'s safety guardrails. The real-time monitoring approach (converting verifier signals into statistical alarms) is architecturally similar to our PSI safety subsystem. Could be integrated as an additional safety layer in the [[psi-quantum-integration]] cognitive core.

## Key Insights

1. Real-time LLM output monitoring using external verifier signals
2. Statistical process control for anomaly detection in LLM outputs
3. Applicable to our agent safety architecture

## Links

- Paper: https://arxiv.org/abs/2607.02510
- PDF: https://arxiv.org/pdf/2607.02510
