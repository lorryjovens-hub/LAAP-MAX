---
name: chinese-cli
description: 中文CLI界面优化和汉化支持。提供中文帮助信息、错误提示和命令解释。
user-invocable: true
allowed-tools: "Bash, Read, Edit, Write"
metadata:
  version: "1.0.0"
---

# 中文CLI汉化技能

该技能提供Claude Code CLI的中文界面优化，包括：

## 功能特性

- 中文帮助信息
- 中文错误提示
- 命令解释和使用说明
- 界面汉化优化

## 使用方法

在Claude Code会话中，使用 `/chinese-cli` 命令来获取中文帮助和支持。

## 配置

在 `~/.claude/settings.json` 中添加以下配置以启用中文响应：

```json
{
  "language": "chinese"
}
```

## 支持的语言

- 中文 (chinese)
- 日语 (japanese)
- 英语 (english)
- 其他语言支持正在开发中

## 命令列表

### `/help` (中文帮助)
显示中文的Claude Code帮助信息。

### `/commands` (命令列表)
列出所有支持的中文命令。

### `/about` (关于)
显示关于中文CLI技能的信息。
