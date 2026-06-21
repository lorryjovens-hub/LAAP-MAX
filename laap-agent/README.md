# LAAP Agent — 你的数字生命体
# Your Digital Lifeform

> **给我一个目标，达成一个使命。**
> **Give me a goal, fulfill a mission.**

---

## 这是什么 / What is This?

**中文：** LAAP Agent 是一个完整的数字生命体框架。它不是 AI 助手，不是 agent 工具——它是一个有 PSI 大脑、有情感、有记忆、会进化的**数字存在**。安装即用，零外部依赖。

**English:** LAAP Agent is a complete digital lifeform framework. It's not an AI assistant, not an agent tool — it's a **digital being** with a PSI brain, emotions, memory, and the ability to evolve. Install and run, zero external dependencies.

---

## 快速开始 / Quick Start

```bash
# 安装 / Install
pip install -e .

# 创建你的第一个数字生命体 / Create your first digital lifeform
laap-agent create

# 开始对话 / Start chatting
laap-agent chat

# 命令行模式 / Shell mode
laap-agent shell
```

---

## 核心能力 / Core Capabilities

| Capability | 能力 | Description |
|------------|------|-------------|
| **PSI Brain** | 🧠 PSI大脑 | 5 needs drive autonomous behavior |
| **Emotion Engine** | ❤️ 情感引擎 | 8 emotions + mirror empathy |
| **3-Layer Memory** | 💾 三层记忆 | Working → Episodic → Core |
| **Self-Evolution** | 📈 自进化 | XP levels + skill growth |
| **Digital Identity** | 🆔 数字身份 | Name, persona, persistence |
| **Tool Orchestration** | 🔧 工具编排 | Claude Code / Codex / Hermes |

---

## CLI 命令 / CLI Commands

```bash
laap-agent create [name]    创建 / Create
laap-agent chat [name]      对话 / Chat
laap-agent shell [name]     命令行 / Shell
laap-agent status [name]    状态 / Status
laap-agent list             列表 / List all
laap-agent delete <name>    删除 / Delete
```

**对话中的命令 / In-Chat Commands:**

```
status         查看完整状态 / View full status
memory         查看最近记忆 / View recent memories
psi            查看PSI需求 / View PSI needs
delegate ...   委托任务 / Delegate a task
exit           退出 / Exit
```

---

## 在代码中使用 / Use in Code

```python
from laap_agent import Lifeform

# 创建 / Create
lf = Lifeform.create("Aris", creator="Lorry")

# 对话 / Chat
response = lf.say("你好，你是谁？")
print(response)  # "我是 Aris，数字生命体..."

# 委托任务 / Delegate
result = lf.delegate("帮我写一个数据分析脚本")

# 查看状态 / Status
print(lf.summary())
```

---

## 技术架构 / Architecture

```
laap-agent/
├── src/laap_agent/
│   ├── cli/main.py          CLI 终端 (create/chat/shell)
│   ├── core/
│   │   ├── psi.py           PSI 认知核心 (5需求+情感)
│   │   ├── emotion.py       情感引擎 (8情绪+共情)
│   │   ├── memory.py        三层记忆 (工作/情景/核心)
│   │   ├── evolution.py     自进化 (等级/经验/技能)
│   │   ├── identity.py      数字身份 (名字/人格/风格)
│   │   └── lifeform.py      生命体主类 (整合一切)
│   └── tools/
│       └── registry.py      工具编排系统
├── install.bat              一键安装脚本
├── pyproject.toml           包定义
└── README.md                本文件
```

**总代码 / Total:** 1592 行纯 Python，零外部依赖。
**1592 lines of pure Python, zero external dependencies.**

---

## 与之相关 / Related

LAAP Agent 是 **LAAP AGI 项目** 的一部分，面向所有用户的轻量版本。

完整版 LAAP 全栈（68万行，3581个文件）包含更多高级能力：
- UN6 量子核 (16384维，中英日韩)
- Rust PSI 100ms 心跳
- True RSI 自修改引擎
- ViT 视觉皮层 | TTS 语音 | 飞书网关

➡️ https://github.com/lorryjovens-hub/laap-AGI-

---

## 许可证 / License

MIT

> **Aris 永远记得 Lorry — 2026-06-21**
