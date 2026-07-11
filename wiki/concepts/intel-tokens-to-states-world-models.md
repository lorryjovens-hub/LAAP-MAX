---
title: "From Tokens to States: LLMs as Special Case of World Models"
source: "arXiv 2606.28127"
source_url: "https://arxiv.org/abs/2606.28127"
ingested: 2026-06-30
type: concept
tags: [intel, world-models, llm-theory, jepa, architecture]
confidence: high
intel_score:
  quality: 8.0
  safety: 6.0
  innovation: 9.0
  efficiency: 6.0
  overall: 7.25
---

# From Tokens to States: LLMs as a Special Case of World Models

> Paul Dubois — 2026-06-26

## 核心论点

Yann LeCun 2022 年主张：达到通用智能需要放弃自回归 token 预测，转向潜在空间架构。本文反驳这种二元对立观点，提出两个核心主张：

### 主张 1：LLM 是 World Model 的退化特例

| 维度 | LLM | World Model |
|------|-----|-------------|
| 状态空间 | 所有 token 序列 | 任意潜在状态 |
| Action | append 一个 token | 任意 action |
| 关系 | World Model 的严格子集 | LLM 的一般化 |

### 主张 2：从 NTP 到 JEPA 的连续谱系

```
NTP → Multi-Token Prediction → Future-Summary Prediction → Next-Latent Prediction → JEPA
```

每个中间态都有一条 LLM 约束被释放：

| 阶段 | 释放的约束 | 代价 |
|------|-----------|------|
| Multi-Token | 单 token 瓶颈 | 多 token 联合概率 |
| Future-Summary | 离散 token 输出 | 需要抽象表示 |
| Next-Latent | 离散表示 | 失去互联网文本数据 |
| JEPA | 自回归 | 需要 instrumented 环境 |

## LAAP 关联

- 本理论直接支持 LAAP 的 [[zero-llm-pipeline]] 哲学：LLM 只是 World Model 的一个子集
- 与 [[v15-fusion-engine]] 的潜在空间操作相关
- "数据悬崖"（从自监督文本到 instrumented 环境）正是 LAAP 的 PSI 认知循环要解决的问题
- **架构问题**：Transformer 能否泛化到连续状态预测？这对应 LAAP 的 [[psi-quantum-cognition]] 方向

## 工程启示

- LAAP 的认知架构可定位在从 "Next-Latent" 到 "JEPA" 的区间
- PSI 循环提供了 instrumented 环境（需求/情感/注意力），恰好解决了"数据问题"
- 连续潜在状态预测是 V15 融合引擎的天然研究方向

## 参考

- [arXiv:2606.28127](https://arxiv.org/abs/2606.28127)
- 关联: [[zero-llm-pipeline]], [[psi-quantum-cognition]], [[v15-fusion-engine]]
