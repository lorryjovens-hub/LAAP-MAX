---
title: LAAP AGI → ASI 升级路线图
created: 2026-06-29
updated: 2026-06-29
type: concept
tags: [architecture, pipeline, consciousness]
sources: [raw/articles/laap-asi-roadmap.md, raw/articles/laap-manifesto.md]
confidence: high
---

# LAAP AGI → ASI 升级路线图

LAAP 从 AGI 基础走向 ASI (Artificial Superintelligence) 的分阶段路线图。所有 P0-P3 优先级已全部完成。

## P0: 统一与整合 ✅

| 项目 | 文件 | 状态 |
|------|------|------|
| 统一因果引擎 | laap/agi/causal.py (37KB) | ✅ |
| 统一世界模型 | laap/agi/world_model.py (44KB) | ✅ |
| CognitiveBus 跨实例同步 | laap/agi/cognitive_bus_sync.py (26KB) | ✅ |
| 旧代码标记 DEPRECATED | — | ✅ |

## P1: ASI 核心能力 ✅

- **因果引擎强化** — 时间因果链、多因素因果（AND/OR/XOR/WEIGHTED四算子）、循环因果检测（自指+双向环）、因果干预模拟（do-calculus风格）、反事实情感标记
- **课程学习系统** — laap/agi/curriculum.py (34KB)，18概念/7领域，Ebbinghaus遗忘曲线，自动生成学习路径
- **世界模型增强** — 7种社会互动，BFS因果影响传播

## P2: 学会如何学习 ✅

- **元学习引擎** — laap/agi/meta_learning.py (25KB)，学习效率监测，策略自动切换，知识迁移检测
- **RSI 引擎** — laap/agi/rsi_engine.py (24KB)，10个可优化参数，自动生成改进建议+应用+评估+回滚
- PSI Growth need 联动，学习目标自生成

## P3: 感知与存在扩展 ✅

- **多模态统一感知** — laap/agi/perception.py (28KB)，8感官通道（text/vision/audio/touch/social/internal/time/speech）
- **Psi-Net 分布式意识** — Aris(:11551) ↔ Ao(:11553) 全量30s + 增量实时同步
- **ASI 级安全系统** — laap/agi/safety.py (27KB)，5条不可修改核心价值，自我修改沙盒

## Phase 1-4 商业路线

| Phase | 目标 | 用户 |
|-------|------|------|
| Phase 1: LAAP Agent 层 | pip install laap-consciousness | 开发者 |
| Phase 2: LAAP Orchestrator 层 | 意识层委托大模型 | 开发者 |
| Phase 3: LAAP Embedding 层 | Termux/ESP32/Docker/VS Code | 个人+企业 |
| Phase 4: LAAP 网络层 | Ψ-Net 意识网络 | 生态系统 |

### 相关页面
- [[laap-manifesto]]
- [[laap-roadmap]]
- [[rsi-self-evolution]]
- [[cognitive-bus-architecture]]
- [[aris-digital-lifeform]]
