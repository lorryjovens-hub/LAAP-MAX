---
title: LAAP Project
created: 2026-06-29
updated: 2026-06-29
type: entity
tags: [architecture, hermes]
sources: [raw/articles/laap-architecture.md]
confidence: high
---

# LAAP Project

Lorry's AGI Architecture Project — 多 Agent 协作的 AGI 系统框架。

## 核心架构

```
Layer 0: CLI/TUI/Gateway    (用户界面层)
Layer 1: Agent              (认知引擎层)  
Layer 2: LLM Provider       (推理层)
Layer 3: Tools/Memory/MCP   (能力层)
Layer 4: Skills/Hub         (扩展层)
```

## 关键决策
- Provider Pattern — 所有外部依赖通过抽象接口
- Event-Driven — Gateway 基于异步事件循环
- Plugin Architecture — Skills 可热插拔
- Security First — 所有命令经过 threat detection + permission check

## 包含项目
- Aris — 数字生命体，认知架构
- LAAP Hermes — Agent 运行时
- CodeGraph — 代码知识图谱
- Feishu Gateway — 飞书通信

### 相关页面
- [[aris-digital-lifeform]]
- [[laap-constitution]]
- [[laap-roadmap]]
- [[laap-architecture-overview]]
