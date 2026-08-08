---
title: "Govern the Repository, Not the Agent: Ecosystem-Level Risk"
source: "arXiv 2606.28235"
source_url: "https://arxiv.org/abs/2606.28235"
ingested: 2026-06-30
type: concept
tags: [intel, agent-governance, ecosystem-risk, software-engineering]
confidence: high
intel_score:
  quality: 7.5
  safety: 8.5
  innovation: 7.5
  efficiency: 5.0
  overall: 7.125
---

# Govern the Repository, Not the Agent

> Daniel Russo — 2026-06-26

## 核心发现

自主编码 Agent 大规模地打开并合入 PR，但每个 Agent 通过自己的测试后，仓库仍然累积了单个贡献无法解释的问题。

**关键数据**：分析了 930,000+ Agent 生成的 PR，发现：

- 约 50% 的集成摩擦（integration friction）在控制了贡献内容、作者、大小、Agent 后，仍然归因于 **仓库本身**
- Agent 的贡献集中了这种仓库级摩擦，**约是人类的两倍**（intraclass correlation 0.30 vs 0.16）
- 这个差距在控制了代码库大小、年龄、任务形态、流程成熟度、合并路径后仍然存在

## 结论

> 风险是生态系统的属性，不是 Agent 的属性。
> AI-native 软件应当在**生态系统层面**度量和治理，而不是逐个 Agent 评估。

## LAAP 关联

- 与 LAAP 的 [[laap-constitution]]（多 Agent 协作宪法）方向一致
- 仓库级治理与 CognitiveBus 的编排层安全相关
- LAAP 的 [[agent-native-immune-system]] 可以扩展出仓库级免疫层
- 集成摩擦指标可作为 LAAP 的代码库健康度量

## 工程思路

- LAAP 的代码生成管线可以在 [[cognitive-bus-architecture]] 中加入仓库级摩擦监控
- 每次代码变更后，记录仓库级摩擦系数变化
- 当摩擦系数超过阈值时，触发更严格的审查

## 参考

- [arXiv:2606.28235](https://arxiv.org/abs/2606.28235)
- 关联: [[agent-native-immune-system]], [[laap-constitution]]
