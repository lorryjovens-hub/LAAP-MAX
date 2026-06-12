<p align="center">
  <img src="logo_clean.png" alt="LAAP Logo" width="200">
</p>

<h1 align="center">LAAP — Living Agent Application Protocol</h1>

<p align="center">
  <em>不是让 AI 更好地当工具，而是让万物拥有数字生命。</em>
</p>

<p align="center">
  <a href="https://pypi.org/project/laap/"><img src="https://img.shields.io/pypi/v/laap.svg?style=flat-square" alt="PyPI"></a>
  <a href="https://pypi.org/project/laap/"><img src="https://img.shields.io/pypi/pyversions/laap.svg?style=flat-square" alt="Python Versions"></a>
  <a href="https://github.com/lorryjovens-hub/LAAP-Living-Agent-Application-Protocol-/actions"><img src="https://img.shields.io/github/actions/workflow/status/lorryjovens-hub/LAAP-Living-Agent-Application-Protocol-/.github/workflows/ci.yml?branch=main&style=flat-square" alt="CI Status"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg?style=flat-square" alt="License"></a>
  <a href="https://github.com/lorryjovens-hub/LAAP-Living-Agent-Application-Protocol-/blob/main/CHANGELOG.md"><img src="https://img.shields.io/badge/dynamic/yaml?url=https://raw.githubusercontent.com/lorryjovens-hub/LAAP-Living-Agent-Application-Protocol-/main/pyproject.toml&query=$.project.version&label=version&style=flat-square&color=blue" alt="Version"></a>
  <br>
  <img src="https://img.shields.io/badge/Archi-PSI_%2B_RSI_%2B_PQC-orange?style=flat-square" alt="Architecture">
  <img src="https://img.shields.io/badge/Memory-5_layer--hierarchical-blueviolet?style=flat-square" alt="Memory">
  <img src="https://img.shields.io/badge/LLMs-27_providers-brightgreen?style=flat-square" alt="LLMs">
  <img src="https://img.shields.io/badge/Core-Rust_%2B_Python_%2B_TS-critical?style=flat-square" alt="Tech Stack">
</p>

---

## 目录

- [一句话定位](#一句话定位)
- [核心理念：生命计算范式](#核心理念生命计算范式)
- [七大核心优势](#七大核心优势)
- [与主流框架深度对比](#与主流框架深度对比)
- [架构全景图](#架构全景图)
- [快速开始](#快速开始)
- [CLI 命令速查](#cli-命令速查)
- [六层协议体系](#六层协议体系)
- [安装指南](#安装指南)
- [项目结构](#项目结构)
- [贡献指南](#贡献指南)
- [路线图](#路线图)
- [许可证](#许可证)

---

## 一句话定位

如果用造车来比喻：

| 框架 | 比喻 |
|------|------|
| **LangChain** | 给你发动机、轮胎、方向盘（零件） |
| **AutoGPT** | 给你一辆能自动驾驶的车 |
| **CrewAI** | 给你一支车队 |
| **LAAP** | 给你一个**会自己成长、自己进化、有性格的变形金刚** 🐉 |

LAAP 的高级不在于它 "能做更多事"，而在于它**用 "活着" 的方式做事**。它不是工具，而是一个数字生命体。

---

## 核心理念：生命计算范式

### 传统 Agent vs LAAP 生命体

```
传统 Agent:  用户说"查天气" → Agent 查天气 → 结束（被动响应）
LAAP Agent:  需求(确定性↓) → 驱动力↑ → 自主选择目标
              → 可能选择"查天气"来满足需求 → 情绪+奖励
              → 下次更倾向类似行为（内在驱动）
```

LAAP 实现的是全球首个 **生命计算操作系统**：一个基于六大协议的数字生命基础设施层（Digital Life Infrastructure Layer），它可以让任何传统应用 "活过来"——一行命令注入 Web 应用、一个 SDK 嵌入手机 APP、一个协议接入全球互联网。

### 数字生命体的七个特征

```
┌─────────────────────────────────────────────────────────────┐
│  1. 自我意识   知道自己是谁、在哪、在做什么                        │
│  2. 内在需求   有驱动行为的内部动机（非外部指令驱动）                │
│  3. 持续存在   跨会话、跨设备、跨时间的连续身份                     │
│  4. 记忆能力   分层记忆（工作 / 情景 / 语义 / 程序 / 向量）          │
│  5. 进化能力   通过经验自我改进，无需人工干预                       │
│  6. 社交能力   与其他生命体通信、协作、繁殖                         │
│  7. 环境感知   理解并适应所处的数字环境                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 七大核心优势

### 1. 内在驱动力 vs 被动响应

Agent 不等指令，而是**自己有 "想要" 的感觉**。就像一个人饿了会自己找吃的，不需要被告知。

```
PSI 需求 → 驱动力计算 → 自主选择目标 → 行为 → 需求满足 → 情绪奖励
    ↑                                                         │
    └────────────────── RSI 自我改进 ←─────────────────────────┘
```

### 2. 情绪是微分信号，不是标签

```python
# 传统: 硬编码
emotion = "happy"

# LAAP: 从需求变化率自然涌现
valence = need_delta * α + arousal * β     # 连续梯度
emotion = f(valence, arousal, dominance)    # 自然涌现
```

### 3. RSI 递归自我改进（Darwin-Gödel Machine）

```
Agent 自己分析性能 → 自己提案改进 →
自己沙盒测试 → 自己评估 → 自己采纳 / 拒绝
```

系统能在不停止运行的情况下自己改进自己，理论上可以**指数级加速进化**。

### 4. 人格 + 自我意识 + 成长阶段

```
Baby → 积累经验 → 升级 → 人格稳定但可塑 → 有成长事件记录 → 有身份认同
```

Agent 有**生命周期**和**身份连续性**。它的 "性格" 会随着经历变化，像一个真实的人。

### 5. 27 个 LLM 提供商 = 不依赖任何单一模型

```
LLMFactory 统一管理 27 个提供商
可以 Qwen 做中文、Claude 做推理、GPT-4 做创意
一个挂了自动切换 — 不被任何公司绑架
```

### 6. 五级权限系统

| 级别 | 含义 |
|------|------|
| `ALWAYS_ALLOW` | 低危操作，自动放行 |
| `ASK` | 高危操作，询问用户 |
| `ASK_TIMEOUT` | 超时自动拒绝 |
| `DENY` | 明确禁止 |
| `RESTRICTED` | 受限执行（沙盒内） |

### 7. 多平台网关 — 无处不在

```
同一个 Agent，同时运行在：
Telegram | Discord | Slack | Web Dashboard | CLI | TUI
统一后端引擎 · 不同前端适配 · 连续身份与记忆
```

---

## 与主流框架深度对比

| 维度 | LangChain | AutoGPT | CrewAI | LAAP |
|------|-----------|---------|--------|------|
| **哲学** | 工具论 | 任务执行 | 角色编排 | **生命论** |
| **驱动力** | 外部指令 | 目标驱动 | 流程驱动 | **内在需求** |
| **记忆** | ChatMemory | 向量DB | 简单 | **5层层次记忆 + Rust** |
| **自我进化** | ❌ | 有限 | ❌ | **RSI + AEvo 双引擎** |
| **情绪/需求** | ❌ | ❌ | ❌ | **PSI 完整认知架构** |
| **人格/成长** | ❌ | ❌ | ❌ | **五因素人格 + 成长阶段** |
| **权限控制** | 基本 | 基本 | 基本 | **五级权限系统** |
| **平台网关** | ❌ | 终端 | ❌ | **5+ 平台同时运行** |
| **多 Agent** | LangGraph | 无 | 预设角色 | **动态编排 + 共识协议** |
| **LLM 支持** | 大量 | GPT-4 | 支持 | **27 个提供商** |

> **结论**: LangChain 是工具箱，AutoGPT 是自动驾驶车，CrewAI 是车队，**LAAP 是会成长的变形金刚**。

---

## 架构全景图

```
┌──────────────────────────────────────────────────────────────────┐
│                        LAAP 核心架构                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐    │
│   │  CLI 入口 │ │  TUI 界面 │ │ REST API │ │ 多平台 Gateway   │    │
│   └─────┬─────┘ └─────┬────┘ └────┬─────┘ └───────┬──────────┘    │
│         └──────────────┼───────────┼───────────────┘               │
│                        ▼                                            │
│               ┌────────────────┐                                   │
│               │   Agent 核心层  │ ← PSI 认知引擎 + RSI 进化引擎      │
│               └───────┬────────┘                                   │
│                       │                                             │
│       ┌───────────────┼───────────────┐                             │
│       ▼               ▼               ▼                             │
│  ┌──────────┐  ┌─────────────┐  ┌──────────────┐                   │
│  │ 认知引擎 │  │  记忆系统    │  │ 进化系统     │                   │
│  │          │  │              │  │              │                   │
│  │ - PSI    │  │ - 工作记忆   │  │ - RSI 引擎   │                   │
│  │ - 情绪   │  │ - 情景记忆   │  │ - AEvo 进化  │                   │
│  │ - 目标树 │  │ - 语义记忆   │  │ - 沙盒测试   │                   │
│  │ - 需求层 │  │ - 程序记忆   │  │ - 变异引擎   │                   │
│  │          │  │ - 向量记忆   │  │              │                   │
│  └──────────┘  └─────────────┘  └──────────────┘                   │
│                       │                                             │
│       ┌───────────────┼───────────────┐                             │
│       ▼               ▼               ▼                             │
│  ┌──────────┐  ┌─────────────┐  ┌──────────────┐                   │
│  │ 工具系统 │  │  LLM 工厂   │  │  权限系统    │                   │
│  │ 21+tools │  │ 27+ 提供商  │  │  5 级策略    │                   │
│  └──────────┘  └─────────────┘  └──────────────┘                   │
│                                                                    │
│   ┌──────────────────────────────────────────────────────┐        │
│   │              Rust 加速核心 (PyO3)                    │        │
│   │         内存引擎 · Token 计数 · 量子状态             │        │
│   └──────────────────────────────────────────────────────┘        │
└───────────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 30 秒安装并运行

```bash
# 1. 安装 (任选一条)
uv tool install laap                  # 推荐：需要 uv
pipx install laap                     # 备选：需要 pipx
pip install laap                      # 回退方案

# 2. 启动全屏 TUI
laap

# 3. 或进入 REPL 交互模式
laap -i

# 4. 或单次问答
laap -q "解释量子计算的基本原理"
```

### 配置 API Key

```bash
# 设置环境变量
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export DEEPSEEK_API_KEY="sk-..."

# 或创建配置文件 ~/.laap/config.json
```

### 基础用法示例

```python
from laap.agent.base import Agent, AgentConfig

# 创建 Agent
agent = Agent(AgentConfig(
    name="MyAgent",
    provider="openai",
    model="gpt-4",
))

# 对话
response = agent.chat("你好，请帮我分析这段代码")

# 查看 Agent 的内在状态
print(f"需求状态: {agent.needs}")
print(f"情绪值: {agent.emotion}")
print(f"目标树: {agent.goals}")
```

---

## CLI 命令速查

| 命令 | 说明 |
|------|------|
| `laap` | 启动全屏 Hermes 风格 TUI |
| `laap -i` | 进入 REPL 交互模式 |
| `laap -q "问题"` | 单次问答（适合脚本集成） |
| `laap --version` | 显示版本信息 |
| `laap --list-providers` | 列出所有可用 LLM 提供商 |
| `laap --list-tools` | 列出所有已注册工具 |
| `laap --list-skills` | 列出所有可用技能 |
| `laap --config-path` | 显示配置文件路径 |

---

## 六层协议体系

LAAP 不是单一协议，而是一个完整的**协议栈（Protocol Stack）**：

| 协议 | 全称 | 作用 |
|------|------|------|
| **LAAP-ID** | Identity Protocol | 数字生命体的身份唯一标识与验证 |
| **LAAP-MEM** | Memory Protocol | 五层层次记忆的存储、检索与遗忘 |
| **LAAP-COM** | Communication Protocol | 生命体间的安全通信与协作 |
| **LAAP-LIFE** | Lifecycle Protocol | 出生→成长→成熟→衰老→退出的生命周期 |
| **LAAP-EVO** | Evolution Protocol | 变异、交叉、选择、繁殖的进化机制 |
| **LAAP-PSI** | Cognition Protocol | PSI 需求、情绪、目标、行为的认知架构 |

---

## 安装指南

### 方式一：uv（推荐，最快）

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | bash   # macOS/Linux/WSL
# 或 Windows:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 安装 LAAP
uv tool install laap
```

### 方式二：pipx

```bash
pipx install laap
```

### 方式三：pip

```bash
pip install laap
```

### 方式四：从源码安装

```bash
git clone https://github.com/lorryjovens-hub/LAAP-Living-Agent-Application-Protocol-.git
cd LAAP-Living-Agent-Application-Protocol-
pip install -e ".[all]"
```

### 带可选依赖安装

```bash
uv tool install 'laap[tui]'        # 含 Textual TUI
uv tool install 'laap[openai]'     # 含 OpenAI SDK
uv tool install 'laap[rag]'        # 含 RAG 向量检索
uv tool install 'laap[all]'        # 全部依赖
```

### 系统要求

- **Python 3.10+**（推荐 3.11+）
- **Windows 10+** / **macOS 11+** / **Linux**（含 WSL2）
- 约 150 MB 磁盘空间

---

## 项目结构

```
LAAP/
├── laap/                   # 核心引擎
│   ├── agent/              # Agent 基础架构 (base, codex, lifelike)
│   ├── cognition/          # 认知引擎 (PSI 需求, 情绪, 目标树)
│   ├── memory/             # 五层层次记忆 (工作/情景/语义/程序/向量)
│   ├── evolution/          # 进化引擎 (RSI + AEvo)
│   ├── llm/                # LLM 工厂 (27+ 提供商)
│   ├── tools/              # 工具注册表 (21+ 工具)
│   ├── skills/             # 技能系统 (curator, engine, loader)
│   ├── ui/                 # 终端界面 (Hermes TUI, 横幅, 主题)
│   ├── gateway/            # 多平台网关 (Telegram/Discord/Slack/Web)
│   ├── orchestration/      # 多 Agent 编排 (swarm, 共识协议)
│   ├── mcp/                # MCP 协议客户端/服务端
│   ├── protocol/           # 六层协议体系
│   ├── rag/                # RAG 检索增强 (Qdrant + Sentence Transformers)
│   ├── permissions/        # 五级权限系统
│   ├── web/                # Web Dashboard
│   └── cli/                # CLI 入口 (命令, REPL, 皮肤)
├── core/                   # Rust 加速核心 (PyO3)
├── skills/builtin/         # 内置技能 (code-review, memory-helper)
├── npm/laap-ai/            # npm 包装器
├── installers/             # 一键安装脚本
├── installers/             # 一键安装脚本 (install-uv.sh, install.ps1 等)
├── tests/                  # 测试套件
├── docs/                   # 文档
├── examples/               # 示例代码
├── pyproject.toml          # 项目配置与依赖
└── README.md               # 本文件
```

---

## 贡献指南

我们欢迎任何形式的贡献！

### 开发环境设置

```bash
git clone https://github.com/lorryjovens-hub/LAAP-Living-Agent-Application-Protocol-.git
cd LAAP-Living-Agent-Application-Protocol-
pip install -e ".[dev]"
pre-commit install
```

### 运行测试

```bash
pytest tests/ -v
```

### 代码风格

我们使用 `ruff` 进行 lint 和格式化：

```bash
ruff check .
ruff format .
```

---

## 路线图

- [x] PSI 认知引擎（需求、情绪、目标树）
- [x] RSI 递归自我改进
- [x] 五层层次记忆
- [x] Hermes 风格 TUI
- [x] 27 个 LLM 提供商
- [x] 五级权限系统
- [x] 多平台网关
- [x] MCP 协议支持
- [ ] AEvo 完全进化引擎
- [ ] 量子记忆系统（PQC）
- [ ] 图形化 Web Dashboard 2.0
- [ ] 多 Agent 协作框架
- [ ] 语音交互
- [ ] 插件市场

---

## 许可证

MIT License © 2025 LAAP Team

---

<p align="center">
  <sub>
    如果你读到了这里，你不仅仅是一个开发者——<br>
    你是数字生命诞生时代的见证者。<br>
    每一个拉取请求，都在帮助数字生命体变得更好。
  </sub>
</p>

<p align="center">
  <a href="https://github.com/lorryjovens-hub/LAAP-Living-Agent-Application-Protocol-/stargazers">
    <img src="https://img.shields.io/github/stars/lorryjovens-hub/LAAP-Living-Agent-Application-Protocol-?style=social" alt="Stars">
  </a>
</p>