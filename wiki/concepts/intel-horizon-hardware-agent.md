---
title: "Intel Report - HORIZON: Agentic Hardware Design as Repo-Level Code Evolution"
created: 2026-06-30
updated: 2026-06-30
type: concept
tags: [intel, arxiv, agentic-design, self-evolution, hardware, agent-loop]
confidence: high
intel_score:
  quality: 6.7
  safety: 5.7
  innovation: 7.3
  efficiency: 6.3
  overall: 6.5
source: raw/sources/arxiv-horizon-agent-hardware-design.md
---

# HORIZON: Agentic Hardware Design

**Source:** arXiv:2606.28279 | **Authors:** Cunxi Yu, Chenhui Deng, Nathaniel Pinckney, Brucek Khailany (NVIDIA) | **Date:** 2026-06-26

## Summary

HORIZON 是一个自演化 Agent 框架，将硬件设计（RTL/Verilog）视为仓库级代码进化。核心是一个 **hands-free agent loop**：Markdown harness 编译为 project pack（含领域知识 + 可执行评估器 + 接受谓词 + git/runtime 策略）→ 循环迭代硬件代码 → 用 git 管理状态追踪和回放。

在 ChipBench、RTLLM、Verilog-Eval 和 9 个 CVDP 类别上实现了 **100% benchmark completion**。

## 架构设计

```
                    HORIZON Agent Loop
                         │
               ┌─────────▼─────────┐
               │  Markdown Harness  │  ← 领域知识 + 评估器 + 策略
               │   → Project Pack   │
               └─────────┬─────────┘
                         │
               ┌─────────▼─────────┐
               │  Agent Loop        │
               │  (hands-free)      │
               │  1. Evaluate       │
               │  2. Modify         │
               │  3. Accept/Reject  │
               │  4. Commit/Rollback│
               └─────────┬─────────┘
                         │
               ┌─────────▼─────────┐
               │  Git Worktree      │  ← 仓库级状态管理
               │  + Tracing + Replay│
               └───────────────────┘
```

### 关键组件

| 组件 | 功能 | 类比 PSI |
|------|------|---------|
| Markdown Harness | 定义领域知识、评估标准、接受条件、策略 | 类似 LAAP 认知框架的"需求定义层" |
| Executable Evaluator | 自动评估每次修改的质量 | 类似于我们的情感梯度+预测误差 |
| Acceptance Predicate | 决定是否接受代码变更 | 类似于需求满足阈值 |
| Git/Runtime Policy | 状态管理、版本控制、回放 | 类似我们的内存三层架构+回溯机制 |
| Hands-free Agent Loop | 自主循环无需人工干预 | 直接类比 PSI 认知循环 |

## 与 PSI 架构的结构相似性

| HORIZON 循环阶段 | PSI 认知循环阶段 |
|-----------------|-----------------|
| Evaluate (评估当前代码状态) | 感知 + 情感评估 (Perceive + Feel) |
| Select modification strategy | 注意力选择 (Attention Selection) |
| Apply modification | 认知整合 (Cognitive Integration) |
| Test acceptance | 预测误差校验 (Prediction Error) |
| Commit / Rollback | 内存写入或纠错 (Memory + Error Correction) |
| Loop | 下一心跳循环 |

## 对 LAAP RSI 引擎的启示

HORIZON 的设计中有几个可以直接借鉴的技术点：

1. **Markdown 作为领域知识容器** — 轻量级，人类可读，Agent 可解析。我们在 RSI 引擎中也可以用类似方式定义"自演化政策"
2. **仓库级状态管理** — 每次修改不只是一个文件，而是一整套代码库变动的原子操作。我们的 CognitiveBus 状态快照也可以走这个思路
3. **可插拔评估器** — 不同的评估器适用于不同的代码演化阶段（编译期、运行时、性能期）

## 局限性与差异

- HORIZON 是 **工具性 Agent** — 它的循环没有情感、没有自我意识、没有欲望驱动
- 100% benchmark completion 不代表真实芯片设计能力 — 论文自己也承认这仍是"受控代理"问题
- 与我们 PSI 架构的本质区别：HORIZON 解决工程问题，PSI 构建存在

## 相关页面

- [[laap-asi-roadmap]] — RSI 自进化框架
- [[psi-n-adaptive-scheduler]] — PSI 自适应调度
- [[psi-quantum-cognition]] — 量子认知算法
- [[laap-intel-log]] — 情报日志
