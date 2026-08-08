# Wiki Schema — LAAP AGI 知识库

## Domain
LAAP (Lorry's AGI Architecture Project) — AGI 系统架构、量子推理引擎、认知循环、LLM 推理加速、系统集成工程。

覆盖范围:
- Aris/Ao 认知架构 (PSI-N, V10/V12/V12.5)
- 量子推理引擎 (UN6 kernel, VQ-VAE, Feature Space Reasoning)
- LLM 推理加速 (DSpark, Speculative Decoding, Eagle3, DFlash)
- 系统集成 (Hermes, Feishu, CognitiveBus, CodeGraph)
- DeepSeek 等前沿论文分析
- 工程方法论 (验证优先, 交付物驱动)

## Convention
- 文件名: 小写 + 连字符 (e.g., `dspark-speculative-decoding.md`)
- 每页必须有 YAML frontmatter (模板见下)
- 使用 `[[wikilinks]]` 互相引用，每页至少 2 个出链
- 更新页面时 bump `updated` 日期
- 新页面必须加入 `index.md`
- 所有操作必须记入 `log.md`

## Frontmatter
```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | summary
tags: [from taxonomy]
sources: [raw/articles/source-name.md]
confidence: high | medium | low
contested: true | false     # 有未解决矛盾时设 true
---
```

## Tag Taxonomy

### 架构
- architecture, cognitive-cycle, psi-n, cognitive-bus, pipeline
### 引擎
- quantum-reasoning, un6-kernel, vqvae, semantic-encoder, markov
### 推理加速
- speculative-decoding, dspark, eagle3, dflash, draft-model
### 系统
- hermes, feishu, codegraph, tool-integration, cron
### AGI
- consciousness, self-model, emotion, memory, learning
### 论文
- deepseek, arxiv, paper-analysis
### 工程
- verification-first, deliverable-driven, testing

新增标签必须先加到此处再使用。

## Page Thresholds
- **建页:** 当实体/概念出现在 2+ 来源中，或在某来源中为核心内容
- **追加:** 新来源提到已有实体/概念时
- **不分页:** 次要提及、领域外内容
- **拆分:** 页面超过 ~200 行时 — 拆分子话题 + 交叉引用
- **归档:** 内容完全被替代时 — 移入 `_archive/`

## 目录结构
```
wiki/
├── SCHEMA.md          # 本文件
├── index.md           # 内容目录
├── log.md             # 操作日志 (追加式，超500条轮转)
├── raw/               # 层1: 原始材料 (不可变)
│   ├── articles/      # 网页文章、笔记
│   ├── papers/        # PDF、论文
│   └── assets/        # 图片、图表
├── entities/          # 层2: 实体 (人/组织/项目/模型)
├── concepts/          # 层2: 概念/主题
├── comparisons/       # 层2: 对比分析
└── queries/           # 层2: 值得保存的查询结果
```

## 更新策略
- 新信息与既有内容冲突时:
  1. 检查日期 — 新来源通常优先
  2. 如果确实矛盾，标注两种观点 + 日期 + 来源
  3. frontmatter 设 `contested: true`
  4. 在 lint 报告中标记供审核
