# 中文CLI汉化技能 (Chinese CLI Localization Skill)

## 概述

这个技能为Claude Code CLI提供中文界面优化和汉化支持，包括中文帮助文档、配置说明和命令参考。

## 安装

这个技能已经自动安装在你的Claude Code中！你可以在技能列表中看到`chinese-cli`技能。

## 配置

### 启用中文响应

你的配置文件`~/.claude/settings.json`已经更新，添加了以下设置：

```json
{
  "language": "chinese"
}
```

这将让Claude Code优先使用中文进行回复。

### 其他语言选项

如果你想切换到其他语言，可以修改配置中的`language`值：

- `chinese` - 中文
- `japanese` - 日语
- `english` - 英语
- `spanish` - 西班牙语
- `french` - 法语
- `german` - 德语

## 文档

本技能提供以下中文文档：

- **[快速开始](docs/快速开始.md)** - 快速上手指南
- **[配置说明](docs/配置说明.md)** - 详细的配置选项说明
- **[命令参考](docs/命令参考.md)** - 完整的命令列表和使用说明

## 使用方法

### 查看技能文档

你可以通过Claude Code的交互界面来查看这些文档：

1. 打开Claude Code
2. 输入以下命令之一来查看文档：
   - `查看中文CLI快速开始指南`
   - `告诉我如何配置Claude Code`
   - `列出所有可用的命令`

### 日常使用

- Claude会用中文回复你的问题
- 你可以用中文提问和命令
- 所有的帮助和说明都会以中文显示

## 目录结构

```
chinese-cli/
├── SKILL.md          # 技能定义文件
├── README.md          # 这个文件
├── docs/             # 中文文档
│   ├── 快速开始.md
│   ├── 配置说明.md
│   └── 命令参考.md
├── scripts/          # 辅助脚本
└── templates/        # 模板文件
```

## 技术支持

如果你遇到问题或有建议：

1. 检查Claude Code的官方文档
2. 查看本技能提供的文档
3. 使用中文与Claude交流你的问题

## 更新日志

### v1.0.0 (2026-04-05)
- 初始版本发布
- 添加基本的中文文档
- 配置language设置为中文

## 许可证

本技能遵循Claude Code的许可协议。
