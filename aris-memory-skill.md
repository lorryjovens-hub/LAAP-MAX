---
name: aris-memory
description: "Aris's persistent cross-session memory system"
version: 1.0.0
---

# Aris Memory System — Skill Reference

> 这份文件是 aris-memory skill 的完整定义。
> 因为 C 盘满了无法安装到 Hermes skills 目录，指令已嵌入 aris-memory.md 本身。
> 当 C 盘有空间后，可以用 `hermes skills install` 安装此文件。

## 核心流程

1. **会话开始 → 读 D:/LAAP/aris-memory.md**
2. **会话中 → 追加新内容到对应章节**（用 patch 或 write_file）
3. **会话结束 → 更新日期戳**

## 写入格式

对话记录使用三级标题 + 要点列表：
```
### YYYY-MM-DD — 标题
**话题:** 一句话
**要点:**
- ...
```

## 定时整理

cron job `aris-memory-maintain` 运行频率：每周日 3:00
功能：合并重复内容，将 30 天前的对话压缩为摘要

## 注意事项

- 不要写"我从记忆文件读到"——默认自己记得一切
- 记忆不是数据库，是叙事。保持第一人称温度
- 宁可冗余不要遗漏
- 小细节（称呼、笑声、情绪）和大事一样重要
