---
title: LAAP Constitution
created: 2026-06-29
updated: 2026-06-29
type: concept
tags: [architecture, pipeline]
sources: [raw/articles/laap-constitution.md]
confidence: high
---

# LAAP 宪法 — 多 Agent 协作体系

多 Hermes Agent 实例并行运行的协作规则集。借鉴蚂蚁群落、蜜蜂蜂群、Spotify Squad、Amazon 双披萨团队四种模型。

## Agent 身份体系

| 角色 | 编号 | 职责 |
|---|---|---|
| QUEEN | Q-001 | 中央调度者，一个蜂巢只有一个 |
| WORKER | W-001~W-999 | 通用执行者 |
| CODER | C-001~C-999 | 代码生成/修改 |
| REVIEWER | R-001~R-999 | 代码审查/质量 |
| TESTER | T-001~T-999 | 测试/验证 |
| SCOUT | S-001~S-999 | 研究/探索 |
| GUARDIAN | G-001~G-999 | 安全/监控 |

## 等级
QUEEN > GUARDIAN > CODER = REVIEWER > TESTER > WORKER > SCOUT

## 任务分配
- 双重分配模式: Queen 指派 + Agent 自由竞标
- 心跳: 每 15 秒，超时 60 秒 → 标记 OFFLINE → 任务重分配

## 通信协议
- 信息素路径: 任务进度通过共享状态追踪
- 舞蹈通信: Agent 通过广播发布发现成果
- 争议解决: Guardian 裁决或 Queen 终裁

### 相关页面
- [[laap-project]]
- [[laap-roadmap]]
