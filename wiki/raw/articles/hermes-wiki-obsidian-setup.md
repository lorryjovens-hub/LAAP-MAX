---
source_url: feishu://chat/oc_b98356f2e2b3a29a7b077885e5d38469
ingested: 2026-06-29
---

# Hermes + LLM Wiki + Obsidian 知识库搭建记录

2026-06-29 在 Lorry 的 LAAP 项目中搭建。

## 架构
- **Hermes (Aris)** — 自动灌入、定时扫描、内容管理
- **LLM Wiki** — Karpathy 模式的 Markdown 知识库（三层架构）
- **Obsidian** — 可视化浏览 + Graph View

## 管线
1. 用户发送论文/文章 → Aris 自动保存 raw source
2. Aris 创建概念页/实体页 + 交叉引用
3. 更新 index.md + log.md
4. Obsidian 中即时可见

## 定时任务
- arXiv 论文扫描: 每 7 天（job_id=3ba7ed014ed0）
- 关键词: speculative decoding, AGI, quantum reasoning

## 当前规模
- 16 个文件, 63KB
- 7 概念页 + 3 实体页 + 3 元页面 + 2 原始材料
