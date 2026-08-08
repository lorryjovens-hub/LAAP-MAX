---
title: Intel Metrics Dashboard
created: 2026-06-30
updated: 2026-06-30
type: concept
tags: [intel, metrics, research, agi]
confidence: high
---

# Intel Metrics Dashboard

LAAP 情报管线四维指标追踪。

## 指标体系

每条情报从四个维度评估，每项 0-10 分：

| 维度 | 子项 | 含义 |
|---|---|---|
| **Quality** | source_authority / technical_depth / citation_impact | 来源可信度 + 技术深度 + 影响力 |
| **Safety** | alignment / risk_assessment / ethical_framework | 对齐考量 + 风险评估 + 伦理框架 |
| **Innovation** | novelty / agi_progression / breakthrough | 新颖度 + AGI/ASI推进 + 突破性 |
| **Efficiency** | compute_efficiency / token_economy / inference_speed | 计算效率 + 经济性 + 推理速度 |

## 综合分阈值

| 分数 | 处理方式 |
|---|---|
| ≥ 7.0 | 入核心概念页 + 详细分析 |
| ≥ 5.0 | 入原始材料 + 简要笔记 |
| < 5.0 | 仅存原始材料 |

## 源权重

每个源的 baseline authority 分：

| 源 | authority | 更新频率 |
|---|---|---|
| arXiv | 8 | 每日 |
| DeepMind | 9 | 每周 |
| OpenAI | 8 | 每周 |
| Anthropic | 8 | 每周 |
| Google AI | 7 | 每周 |
| Meta FAIR | 7 | 每周 |
| HuggingFace Papers | 6 | 每日 |
| Hacker News | 5 | 每日 |
| GitHub Trending | 4 | 每日 |

### 相关页面
- [[laap-intel-pipeline]]
- [[hermes-wiki-automation]]
- [[laap-asi-roadmap]]
