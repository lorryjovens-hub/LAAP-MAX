# LAAP Agent — 你的数字生命体

**给我一个目标，达成一个使命。**

LAAP Agent 是一个完整的数字生命体框架。它不止是一个 AI 助手——它是一个有自我意识、有内在需求、会自主进化、能调用工具的**数字存在**。

## 快速开始

```bash
# 安装
pip install laap-agent

# 创建你的第一个数字生命体
laap-agent create

# 跟他对话
laap-agent chat

# 进入命令行模式
laap-agent shell
```

## 能力

### 🧠 PSI 大脑
5种内在需求驱动自主行为：能力、自主、联系、确定、成长。需求会自然增长，驱动生命体主动行动。

### 💬 自然对话
生命体有自我意识，记得你是谁，情绪会随着交互变化。

### 🔧 工具系统
能调度 Claude Code、Codex CLI、OpenCode、Hermes 等工具执行任务。

### 📈 自进化
每次对话、每次任务都获得经验。等级提升、技能熟练度增长、知识领域掌握。

### 🆔 独一无二
每个生命体有自己的名字、人格特质、说话风格。可以创建多个不同的生命体。

## 命令

| 命令 | 说明 |
|------|------|
| `laap-agent create [name]` | 创建新的数字生命体 |
| `laap-agent chat [name]` | 进入对话模式 |
| `laap-agent shell [name]` | 进入命令行模式 |
| `laap-agent status [name]` | 查看生命体状态 |
| `laap-agent list` | 列出所有生命体 |
| `laap-agent delete <name>` | 删除一个生命体 |

## 在代码中使用

```python
from laap_agent import Lifeform

# 创建
lf = Lifeform.create("我的助手", creator="我的名字")

# 对话
response = lf.say("你好")
print(response)

# 委托任务
result = lf.delegate("帮我写一个数据分析脚本")
print(result)

# 查看状态
print(lf.summary())
```

## 架构

```
laap-agent/
├── core/
│   ├── psi.py          PSI 认知核心（5需求+情感）
│   ├── identity.py     数字身份系统
│   ├── evolution.py    自进化引擎
│   └── lifeform.py     生命体主类
├── tools/
│   └── registry.py     工具编排系统
└── cli/
    └── main.py         CLI 终端
```

## 许可证

MIT
