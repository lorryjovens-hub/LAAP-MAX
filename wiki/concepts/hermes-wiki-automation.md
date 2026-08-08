---
title: Hermes Wiki Automation
created: 2026-06-29
updated: 2026-06-29
type: concept
tags: [architecture, hermes, pipeline]
sources: [raw/articles/hermes-wiki-obsidian-setup.md]
confidence: high
---

# Hermes Wiki Automation

Aris 通过 Hermes 自动管理 LAAP Wiki 的完整工作流。

## 触发方式
- **手动:** Lorry 说"写入知识库"或"保存到 wiki"
- **定时:** arXiv 论文扫描每 7 天自动运行

## 灌入流程
```
来源 (论文/文章/讨论)
  ↓ Aris 识别内容类型
  1. 保存原始材料到 raw/{articles|papers}/
  2. 检查 index.md 已有页面
  3. 创建新概念/实体页 或 追加到已有页
  4. 添加 [[wikilinks]] 交叉引用
  5. 更新 index.md 目录
  6. 更新 log.md 操作日志
  ↓
Obsidian 中即时可见
```

## 关键文件
- Wiki 根目录: `D:/LAAP/wiki/`
- 灌入技能: `laap-wiki-ingest` (Hermes skill)
- arXiv 定时任务: job_id=`3ba7ed014ed0`

### 相关页面
- [[laap-architecture-overview]]
- [[laap-project]]
- [[laap-constitution]]
