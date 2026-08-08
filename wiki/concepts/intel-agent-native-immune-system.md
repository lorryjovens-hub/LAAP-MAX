---
title: "Agent-Native Immune System (ANIS)"
source: "arXiv 2606.28270"
source_url: "https://arxiv.org/abs/2606.28270"
ingested: 2026-06-30
type: concept
tags: [intel, agent, security, architecture, biological-inspiration]
confidence: high
intel_score:
  quality: 8.0
  safety: 9.0
  innovation: 8.0
  efficiency: 5.0
  overall: 7.5
---

# Agent-Native Immune System (ANIS)

> Bo Shen, Lifeng Chang, Tianyuan Wei et al. — 2026-06-26

## 概要

首个受生物学启发的内生防御架构，直接嵌入在 Agent 的认知循环内部。现有安全机制（边界防御、训练时对齐）对运行时攻击（内存投毒、工具链操纵、多 Agent 协议攻击）几乎无效。

## 核心贡献

### 1. Immune Tower 六层架构 (L0-L5)

| 层级 | 名称 | 功能 |
|------|------|------|
| L0 | Physical | 物理层隔离 |
| L1 | Barrier Immunity | 非认知性物理/逻辑隔离层 |
| L2 | Innate Immunity | 先天免疫（规则匹配） |
| L3 | Adaptive Immunity | 适应性免疫（学习型） |
| L4 | Cognitive Immunity | 认知层免疫监控 |
| L5 | Meta-Immunity | 元免疫（自我反思） |

### 2. Agent 病毒与疫苗分类

- **Agent Viruses**: 在记忆、工具链、多 Agent 协议层面传播的恶意载荷
- **Agent Vaccines**: 浅层（非参数化）vs 深层（参数化鲁棒疫苗）

### 3. Harness Triad

- **Meta-Harness**: 元认知监控
- **Self-Harness**: 自我检查
- **Auto-Harness**: 自动化免疫学习 (CIL)

### 4. 对齐 vs 免疫的正式区分

> 对齐 = 静态"宪法"价值基础（训练时）
> ANIS = 动态"执法"机制（运行时）

## LAAP 关联

- 直接对应 LAAP 的 [[laap-constitution]] 多 Agent 协作宪法
- 与 [[cognitive-bus-architecture]] 的安全层可整合
- Agent 病毒概念与 LAAP 的工具链安全直接相关
- 可参考 Harness Triad 设计 LAAP 的认知安全监控层

## 工程集成思路

LAAP 的 CognitiveBus 可以在消息路由层嵌入 ANIS L3-L4 级别的免疫检测：
1. 工具调用前进行 Barrier Immunity 检查（L1）
2. CognitiveBus 消息中加入免疫签名（L3）
3. 元认知层定期检查 Autoimmunity Rate（假阳性干预率）

## 参考

- [arXiv:2606.28270](https://arxiv.org/abs/2606.28270)
- 关联: [[govern-repository-not-agent]], [[laap-constitution]]
