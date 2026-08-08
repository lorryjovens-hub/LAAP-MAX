---
title: DSpark Speculative Decoding
created: 2026-06-29
updated: 2026-06-29
type: concept
tags: [speculative-decoding, dspark, deepseek, draft-model]
sources: [raw/papers/dspark-2026-deepseek.md]
confidence: high
---

# DSpark Speculative Decoding

DeepSeek 2026 年提出的投机解码框架，已部署在 V4-Flash/V4-Pro 生产环境。

## 核心架构

### 半自回归生成
- 并行 backbone (DFlash 改进版) — 一次前向生成整个 block
- 轻量串行 head — Markov 一阶转移矩阵或 RNN 循环状态
- 效果: 保留了并行的速度 (Pos-1 高接受率)，修正了串行的语义连贯性 (消除 multi-modal collision)

### 置信度调度验证 (Algorithm 1)
- Confidence head 估算每位置存活概率
- 全局排序候选 token → 贪心加入 → 期望吞吐最大化
- 低负载全验证，高负载只验证高置信度 token

### 训练目标
- L_ce (交叉熵) + L_tv (总变差距离) + L_conf (置信度 BCE)
- 权重: α_ce=0.1, α_tv=0.9, α_conf=1.0
- 重点优化分布匹配而非精确预测

## 对我们的影响

### 已落地的工程优化
1. **psi_n_scheduler.py** — 自适应调度器: SystemLoadTracker + LayerConfidence + AdaptiveTickController + STS 校准
2. **quantum_reasoning_engine.py** — SequentialCoherenceModule: 跳跃检测 + 平滑修正 + 融合分数选优

### 相关页面
- [[psi-n-adaptive-scheduler]]
- [[semantic-entanglement-theory]]
- [[laap-quantum-reasoning-engine]]
