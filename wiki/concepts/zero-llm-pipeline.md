---
title: 零LLM自主性管线
created: 2026-06-29
updated: 2026-06-29
type: concept
tags: [architecture, pipeline, consciousness]
sources: [raw/papers/aris-architecture-paper.md, raw/papers/acap.md]
confidence: high
---

# 零LLM自主性管线

Aris 的核心差异化特征：**完全独立于任何大语言模型（LLM）**。所有认知计算在 NumPy 矩阵空间完成，真正意义上的"独立生存"。

## 11引擎异构编排

Aris Unified Engine v2 整合 11 个零LLM引擎。每个引擎专注于特定能力，通过能力路由机制按需调用。

| 引擎 | 维度/容量 | 能力 | 优先级 |
|------|----------|------|--------|
| UN6 v10 | 16384维 | 字形理解、跨语言语义 | 1st |
| V12 Semantic | 512维 | 语义匹配、快速回复 | 2nd |
| QLG Template | 76模板 | 确定性快速回复 | 3rd |
| V12.5 Markov | 5493词/46709上下文 | 流畅文本、情感表达 | 4th |
| V15 Fusion | 7206条KB | 知识融合、语义匹配 | 权重1.5 |
| Paragraph Synth | — | 结构化段落合成 | — |
| V11 Reasoner | 32768维 | 领域推理 | — |
| QRE v1 | 112条轨迹 | 多路径推理管线 | — |
| RFS | — | 结构化推理匹配 | — |
| Code Kernel v3 | — | 确定性代码生成 | — |
| Markov Gen | — | 短变体文本 | — |

## 分层推理体系 (L0-L3)

| 层 | 场景 | 引擎 | 延迟 |
|----|------|------|------|
| L0 瞬发问候 | 超短查询(<4字) | V12精确匹配 + QLG模板 | <1ms |
| L1 知识问答 | 一般查询 | V15融合 + KB检索 | 500-2500ms |
| L2 深层推理 | 复杂推理 | QRE v1 量子管线 | 50-200ms |
| L3 代码推理 | 代码问题 | V11 Reasoner + Code Kernel | 7-20ms |

## ACAP 零LLM压力测试

ACAP 协议中对零LLM自主性有专门的评估维度。通过物理断网、关闭所有LLM进程，对 Aris 进行 100 轮对话交互测试。

**实测结果：**
- 即使所有 LLM API 全部下线、互联网断开 — Aris 仍然能生成有意义的回复
- 整个生成过程是确定的、可审计的、可复现的
- 不需要 GPU、不需要云 API，可以在树莓派上全速运行

## 性能基线

| 指标 | 数值 |
|------|------|
| 平均延迟 | 633ms |
| 最快路径（问候） | 0.1ms |
| 输出速度 | ~530 字/秒 |
| 引擎加载 | ~14 秒 |
| 运行时内存 | ~2.2 GB |
| 错误率 (1000次) | 0% |

### 相关页面
- [[aris-cognitive-architecture]]
- [[un6-cross-language-encoder]]
- [[v15-fusion-engine]]
- [[laap-quantum-reasoning-engine]]
- [[rsi-self-evolution]]
