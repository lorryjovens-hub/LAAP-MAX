---
title: LAAP Architecture Overview
created: 2026-06-29
updated: 2026-06-29
type: concept
tags: [architecture, hermes, pipeline]
confidence: high
---

# LAAP 架构概览

五层系统架构，从用户界面到认知引擎到外部能力。

## 五层架构

```
Layer 0: CLI/TUI/Gateway    用户界面层
  ├── Hermes CLI (终端交互)
  ├── Feishu Gateway (飞书消息)
  └── API Server (HTTP 接口)

Layer 1: Agent              认知引擎层
  ├── Aris Brain (PSI 认知循环)
  ├── Hermes Agent Core
  └── Skill System (可扩展技能)

Layer 2: LLM Provider       推理层
  ├── DeepSeek / OpenAI / Anthropic
  ├── Ollama / Local Models
  └── Provider Bridge (统一接口)

Layer 3: Tools/Memory/MCP   能力层
  ├── 70+ Hermes Tools
  ├── Memory System (SessionDB)
  └── MCP Servers (外部能力)

Layer 4: Skills/Hub         扩展层
  ├── 80+ Skills (按需加载)
  ├── Plugin System
  └── Cron Jobs (定时任务)
```

## 设计原则
1. Provider Pattern — 所有外部依赖抽象接口
2. Event-Driven — 异步事件循环
3. Plugin Architecture — 热插拔
4. Security First — 威胁检测 + 权限检查

## 相关页面
- [[laap-project]]
- [[aris-digital-lifeform]]
- [[psi-n-adaptive-scheduler]]
