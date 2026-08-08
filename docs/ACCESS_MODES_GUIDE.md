# LAAP 接入模式部署指南

> 本文档介绍 LAAP（Lifeform Autonomous Adaptive Protocol）两种接入模式的部署与使用方法。
>
> - **模式 A — 大脑挂载模式（Brain Mount Mode）**：LAAP 作为「意识层」挂载到外部智能体（Claude Code / Cursor / Trae / OpenClaw / 任意 Python Agent），宿主保留身体控制权。
> - **模式 B — 全量个体形式（Full Entity Mode）**：LAAP 作为「意识 + 身体」一体化数字生命独立运行，对外暴露 HTTP / WebSocket / MCP / CognitiveBus 全栈服务。
>
> 适用版本：LAAP v5.0.0+（`laap_brain.__version__ == "5.0.0"`）。

---

## 目录

1. [模式 A：大脑挂载模式（Brain Mount Mode）](#1-模式-a大脑挂载模式brain-mount-mode)
2. [A1 — MCP 挂载](#2-a1--mcp-挂载)
3. [A2 — SDK 嵌入](#3-a2--sdk-嵌入)
4. [模式 B：全量个体形式（Full Entity Mode）](#4-模式-b全量个体形式full-entity-mode)
5. [B1 — 统一启动器](#5-b1--统一启动器)
6. [B2 — Hermes Desktop 完全体部署](#6-b2--hermes-desktop-完全体部署)
7. [故障排查](#7-故障排查)

---

## 1. 模式 A：大脑挂载模式（Brain Mount Mode）

在模式 A 下，LAAP 仅作为「认知内核（`LaapBrain`）」存在，挂载到外部智能体上。宿主智能体保留完整的工具调用、对话循环、I/O 控制权，LAAP 通过以下三种路径为其注入元认知、议会审议、知行合一、EWC 持续学习等能力：

- **A1 — MCP 挂载**：通过标准 MCP（Model Context Protocol）协议，宿主（Claude Code / Cursor / Trae）作为 MCP Client 调用 LAAP 暴露的 4 个钩子工具，零代码改动即可集成。
- **A2 — SDK 嵌入**：通过 `from laap.sdk import mount_brain_to_agent` 在 Python 进程内挂载，适配器（Adapter）自动 monkey-patch 宿主框架的关键方法。
- **A3 — 协议挂载**（本期未实现）：跨设备热迁移传输层，规划支持 CBOR / MsgPack / Protobuf 编解码，详见 spec「实施边界」。

### 1.1 模式 A 的三条路径

| 路径 | 适用宿主 | 集成方式 | 是否需要 LAAP 进程 |
|------|---------|---------|------------------|
| **A1 MCP 挂载** | Claude Code、Cursor、Trae、任意 MCP Client | 配置 MCP Server URL，调用 4 个 `laap_*` 钩子工具 | 是（独立 MCP Server 进程） |
| **A2 SDK 嵌入** | OpenClaw、Claude Code SDK、任意 Python Agent | `mount_brain_to_agent(brain, agent_type)` 同进程挂载 | 否（嵌入式） |
| A3 协议挂载 | 跨设备 / 异构系统 | CBOR / MsgPack 传输层（规划中，本期未实现） | 是 |

### 1.2 三条路径的选择建议

- 你的宿主是 **Claude Code / Cursor / Trae** → 选 **A1 MCP 挂载**（零代码）。
- 你的宿主是 **Python 框架**（OpenClaw / 自研 Agent）→ 选 **A2 SDK 嵌入**（深度集成）。
- 你需要 **跨设备 / 跨语言** → 暂不支持，A3 在规划中。

---

## 2. A1 — MCP 挂载

A1 模式下，LAAP 启动一个 MCP Server（SSE 或 stdio 传输），宿主通过 MCP 协议调用 LAAP 的钩子工具。每次 MCP 会话（`session_id`）绑定一个独立的 `LaapBrain` 实例，认知状态在 `before_turn` → `after_tool` → `after_turn` 三个钩子间累积。

### 2.1 Claude Code 配置

在 Claude Code 的 MCP 配置文件（`~/.config/claude-code/mcp_servers.json` 或项目级 `.claude/mcp_servers.json`）中添加 LAAP MCP Server：

```json
{
  "mcpServers": {
    "laap-brain": {
      "url": "http://127.0.0.1:8766/sse",
      "transport": "sse",
      "description": "LAAP Cognitive Brain — mounts meta-cognition, parliament, unity, EWC into Claude Code"
    }
  }
}
```

启动 LAAP MCP Server（SSE 模式）：

```bash
# 方式 1：使用 laap launch 启动全量个体（含 MCP SSE）
laap launch --http-port 8000 --mcp-port 8766 --mcp-transport sse

# 方式 2：仅启动 MCP Server（stdio 模式，由 Claude Code 直接拉起）
python -c "from laap.mcp.server import LAAPMCPServer; LAAPMCPServer().run_stdio()"

# 方式 3：仅启动 MCP Server（SSE 模式，独立进程）
python -c "from laap.mcp.server import LAAPMCPServer; LAAPMCPServer().run_sse(host='127.0.0.1', port=8766)"
```

**Claude Code 中调用钩子的对话流**（由 Claude Code 自动按顺序调用，开发者无需手动操作）：

```
用户提问 → claude_code 调用 laap_before_turn(session_id, user_message)
        → Claude 生成响应（可能调用若干工具，每次后调用 laap_after_tool）
        → 响应完成后调用 laap_after_turn(session_id, response)
        → 开发者可随时调用 laap_cognitive_status(session_id) 查询认知快照
```

### 2.2 Cursor 配置

在 Cursor 的 MCP 配置文件 `~/.cursor/mcp.json`（或项目级 `.cursor/mcp.json`）中添加：

```json
{
  "mcpServers": {
    "laap-brain": {
      "url": "http://127.0.0.1:8766/sse",
      "transport": "sse",
      "description": "LAAP Cognitive Brain — meta-cognition + parliament + unity + EWC"
    }
  }
}
```

启动 LAAP MCP Server（同上节方式 1 或 3）。

> **注意**：Cursor 当前对 MCP 工具的自动调用策略与 Claude Code 不同，开发者可能需要在 Cursor 设置中显式启用 `laap_before_turn` / `laap_after_tool` / `laap_after_turn` 三个工具的自动调用，或在系统 prompt 中提示 Cursor 按顺序调用。

### 2.3 Trae 配置

Trae IDE 的 MCP 配置文件路径：`%USERPROFILE%\.trae\mcp_servers.json`（Windows）或 `~/.trae/mcp_servers.json`（macOS / Linux）：

```json
{
  "mcpServers": {
    "laap-brain": {
      "url": "http://127.0.0.1:8766/sse",
      "transport": "sse",
      "description": "LAAP Cognitive Brain — mounts meta-cognition, parliament, unity, EWC"
    }
  }
}
```

启动 LAAP MCP Server（同上节）。

### 2.4 可用的 MCP 工具列表

LAAP MCP Server 暴露 **14 个 MCP 工具**：4 个认知钩子工具 + 10 个通用工具。

#### 4 个 LAAP 认知钩子工具（模式 A 核心）

| 工具名 | 调用时机 | 签名 | 返回 |
|--------|---------|------|------|
| `laap_before_turn` | 每轮对话开始 | `(session_id: str, user_message: str = "")` | 格式化的认知上下文字符串，以 `[LAAP Cognitive Context]` 开头，追加到 system prompt |
| `laap_after_tool` | 每次工具调用后 | `(session_id: str, tool_name: str, result: str)` | `{"learned": bool, "memory_id": str, "session_id": str}` |
| `laap_after_turn` | 每轮对话结束 | `(session_id: str, response: str)` | `{"reflection": str, "emotion_delta": dict, "session_id": str}` |
| `laap_cognitive_status` | 任意时刻查询 | `(session_id: str)` | `{session_id, lifeform_id, needs, emotion, goals, recent_memory, uptime}` |

**session_id 约定**：使用稳定的 MCP 客户端会话标识（如 Claude Code 的 conversation_id）。同一 `session_id` 在 LAAP 内部绑定同一个 `LaapBrain` 实例，认知状态在三个钩子间累积；不同 `session_id` 互相隔离。

#### 10 个通用工具（继承自 LAAP 既有工具集）

| 工具名 | 用途 | 签名（简） |
|--------|------|-----------|
| `agent_chat` | 与 LAAP Agent 对话 | `(message: str)` |
| `agent_status` | 查询 Agent 状态 | `()` |
| `agent_memory_prefetch` | 预取相关记忆 | `(query: str)` |
| `read_file` | 读取文件 | `(path: str)` |
| `write_file` | 写文件 | `(path: str, content: str)` |
| `search_files` | glob 文件搜索 | `(pattern: str, path: str = ".")` |
| `run_command` | 执行 shell 命令 | `(command: str, timeout: int = 30)` |
| `web_search` | DuckDuckGo 搜索 | `(query: str)` |
| `memory_store` | 存储记忆 | `(content: str, memory_type: str = "fact", importance: float = 0.5)` |
| `memory_recall` | 召回记忆 | `(query: str = "", limit: int = 5)` |
| `cognitive_status` | 认知状态快照 | `()` |

> 模式 A 通常只使用 4 个 `laap_*` 钩子工具；10 个通用工具主要服务于模式 B 的 MCP 客户端（如 Hermes Desktop 调用）。

---

## 3. A2 — SDK 嵌入

A2 模式下，LAAP SDK 在 Python 进程内挂载到宿主 Agent 框架。`mount_brain_to_agent()` 根据 `agent_type` 参数选择适配器，通过 monkey-patch 宿主框架的关键方法注入钩子。

### 3.1 Python SDK 基础用法

`mount_brain_to_agent()` 签名（`laap/sdk/mount.py`）：

```python
def mount_brain_to_agent(
    brain: "LaapBrain",
    agent_type: str = "auto",        # "auto" | "hermes" | "claude_code" | "openclaw" | "generic"
    agent: Optional[Any] = None,
) -> Tuple["LaapBrain", Optional["AgentAdapter"]]:
    """将 LAAP 大脑挂载到外部智能体。

    Args:
        brain: LaapBrain 实例。
        agent_type: "auto" 自动检测（顺序：Hermes → Claude Code → OpenClaw → Generic）；
            或显式指定 "hermes" / "claude_code" / "openclaw" / "generic"。
        agent: 可选智能体对象（仅 generic 与 openclaw 模式使用）。

    Returns:
        (brain, adapter) 元组；auto 全部失败时 adapter 为 None。

    Raises:
        NotImplementedError: 显式指定的 agent_type 未实现时。
    """
```

最小示例：

```python
from laap_brain import LaapBrain
from laap.sdk import mount_brain_to_agent

# 1. 创建大脑
brain = LaapBrain(agent_id="my-agent-01")

# 2. 自动检测宿主并挂载（推荐）
brain, adapter = mount_brain_to_agent(brain, agent_type="auto")

print(f"Mounted adapter: {adapter.name() if adapter else 'none'}")
# 之后宿主框架的对话循环会自动调用 brain.before_turn / after_tool / after_turn
```

### 3.2 OpenClaw 集成示例

`OpenClawAdapter` 通过 monkey-patch OpenClaw 的 `Agent` 类注入 5 个钩子（`__init__` 注入 `self.laap_brain`，`execute_tool` 前后调用 `brain.after_tool`，`run_conversation` 前后调用 `brain.before_turn` / `brain.after_turn`）：

```python
from laap_brain import LaapBrain
from laap.sdk import mount_brain_to_agent
import openclaw  # 宿主框架

# 1. 创建 LAAP 大脑
brain = LaapBrain(agent_id="openclaw-01")

# 2. 显式指定 OpenClaw 适配器挂载
brain, adapter = mount_brain_to_agent(brain, agent_type="openclaw")
assert adapter is not None, "OpenClawAdapter failed to install"

# 3. 正常使用 OpenClaw（钩子已自动注入）
agent = openclaw.Agent(model="gpt-4")
response = await agent.run_conversation("帮我分析这段代码")
# 内部流程：
#   - patched_run → brain.before_turn([message], "") → 注入认知上下文
#   - 若 agent 调用工具：patched_execute_tool → brain.after_tool(tool_name, result)
#   - 对话结束：patched_run → brain.after_turn(response) → 反思 + 状态衰减

# 4. 卸载钩子（可选，进程退出时自动清理）
adapter.uninstall_hooks()
```

> **依赖**：`pip install openclaw`（OpenClaw 框架）。若未安装，`OpenClawAdapter.detect()` 返回 False，auto 模式会跳过。

### 3.3 Claude Code SDK 集成示例

`ClaudeCodeAdapter` 基于 `claude-code-sdk-python` 的 `ClaudeSDKClient`，在 `process_response` 钩子处插入 `brain.after_turn`，在 `__init__` 注入 `self.laap_brain`：

```python
from laap_brain import LaapBrain
from laap.sdk import mount_brain_to_agent
from claude_code_sdk import ClaudeSDKClient  # 宿主 SDK

# 1. 创建大脑
brain = LaapBrain(agent_id="claude-code-01")

# 2. 显式指定 Claude Code 适配器挂载
brain, adapter = mount_brain_to_agent(brain, agent_type="claude_code")
assert adapter is not None, "ClaudeCodeAdapter failed to install"

# 3. 使用 ClaudeSDKClient（钩子已注入）
client = ClaudeSDKClient(model="claude-3-5-sonnet")
# client.laap_brain 已在 __init__ 中自动注入

# 调用对话（patched_process_response 会在响应后自动调用 brain.after_turn）
response = await client.process_response("帮我重构这个函数")

# 4. 卸载钩子（可选）
adapter.uninstall_hooks()
```

> **依赖**：`pip install claude-code-sdk`。若未安装，调用 `install_hooks` 会抛 `ImportError: claude-code-sdk not installed. Install with: pip install claude-code-sdk`。

### 3.4 通用 Python Agent 集成

`GenericAdapter` 支持任意 Python Agent，提供两种集成方式：

- **方式 1**：Agent 有 `register_hook(event, callback)` 方法 → 自动注册三个钩子。
- **方式 2**：Agent 无该方法 → 仅挂 `agent.laap_brain = brain`，由用户手动调用钩子。

```python
from laap_brain import LaapBrain
from laap.sdk import mount_brain_to_agent

# 自定义 Agent（方式 1：支持 register_hook）
class MyAgent:
    def __init__(self):
        self._hooks = {}
    def register_hook(self, event, callback):
        self._hooks[event] = callback
    async def chat(self, message):
        # 调用钩子
        if "before_turn" in self._hooks:
            ctx = self._hooks["before_turn"]([{"role": "user", "content": message}], "")
            # 将 ctx 追加到 system prompt
        response = await self._llm_call(message)
        if "after_turn" in self._hooks:
            self._hooks["after_turn"](response)
        return response

agent = MyAgent()
brain = LaapBrain(agent_id="my-agent-01")

# 挂载（auto 模式会自动选择 GenericAdapter）
brain, adapter = mount_brain_to_agent(brain, agent_type="generic", agent=agent)
# GenericAdapter.detect() 永远返回 True，作为兜底

# 方式 2 示例：无 register_hook 的 Agent
class SimpleAgent:
    pass

simple_agent = SimpleAgent()
brain2 = LaapBrain(agent_id="simple-01")
brain2, adapter2 = mount_brain_to_agent(brain2, agent_type="generic", agent=simple_agent)
# 此时 simple_agent.laap_brain = brain2，需手动调用：
#   simple_agent.laap_brain.before_turn(messages, system_prompt)
#   simple_agent.laap_brain.after_tool(tool_name, result)
#   simple_agent.laap_brain.after_turn(response)
```

### 3.5 enhance() 向后兼容用法

`laap_brain.enhance()` 是一行创建 `LaapBrain` 的快捷函数，支持 `return_adapter` 参数控制返回值（`laap_brain/__init__.py`）：

```python
from laap_brain import enhance

# 用法 1：仅返回 LaapBrain（向后兼容，v3.1 起支持）
brain = enhance(agent_id="legacy-01")
# 等价于 LaapBrain(agent_id="legacy-01")

# 用法 2：返回 (LaapBrain, AgentAdapter) 元组（v5.0 新增）
brain, adapter = enhance(return_adapter=True)
# 内部调用 mount_brain_to_agent(brain, agent_type="auto") 自动检测并挂载
# 若检测/挂载异常，返回 (brain, None) 而非抛异常

# 用法 3：传入宿主 Agent 实例
import openclaw
agent = openclaw.Agent()
brain, adapter = enhance(agent=agent, return_adapter=True)
```

`enhance()` 签名：

```python
def enhance(
    agent: Any = None,
    agent_id: str = "",
    return_adapter: bool = False,
) -> Union["LaapBrain", Tuple["LaapBrain", Optional[Any]]]:
    """一行创建 LAAP Brain 实例 — 公共入口快捷函数。

    Args:
        agent: 可选宿主 Agent 实例
        agent_id: 可选 Agent ID
        return_adapter: False（默认）返回 LaapBrain；
            True 返回 Tuple[LaapBrain, Optional[AgentAdapter]]。

    Returns:
        return_adapter=False → LaapBrain
        return_adapter=True → (LaapBrain, AgentAdapter 或 None)
    """
```

---

## 4. 模式 B：全量个体形式（Full Entity Mode）

在模式 B 下，LAAP 作为「意识 + 身体」一体化数字生命独立运行，对外暴露全栈服务：

- **FastAPI HTTP/SSE 服务**：提供 REST API（`/health`、`/agents/*`、`/society/*`）、WebSocket 推送（`/ws`）、OpenAI 兼容流式接口（`/v1/chat/completions`）。
- **MCP Server**：暴露 14 个 MCP 工具（4 钩子 + 10 通用），支持 SSE 与 stdio 两种传输。
- **CognitiveBus TCP 节点**：P2P 数字生命体通信总线，跨进程 / 跨设备协作。

模式 B 适合需要 LAAP 作为独立服务运行、被多个客户端（Hermes Desktop、Web UI、其他 Agent）共享访问的场景。

### 4.1 模式 B 的两条路径

| 路径 | 启动方式 | 适用场景 |
|------|---------|---------|
| **B1 统一启动器** | `laap launch` 命令或 `launch_full_entity()` 函数 | 服务端部署、开发调试、被多客户端共享 |
| **B2 Hermes Desktop 完全体** | Hermes Desktop React 前端 + LAAP 后端 | 桌面端数字生命交互 |

---

## 5. B1 — 统一启动器

`LAAPLauncher`（`laap/launcher.py`）在单进程内启动 FastAPI + MCP + CognitiveBus 三服务，FastAPI 阻塞主线程，MCP 与 CognitiveBus 在守护线程运行。

### 5.1 `laap launch` 命令详解

`laap launch` 子命令注册在 `laap/cli/subcommands/launch_cmd.py`，由 `laap/cli/main.py` 的 `COMMANDS` 字典自动加载。

**完整命令行示例**：

```bash
# 默认启动（HTTP 8000 + MCP SSE 8766 + CognitiveBus 11550）
laap launch

# 自定义端口
laap launch --host 0.0.0.0 --http-port 9000 --mcp-port 9001 --bus-port 9002

# 仅启动 FastAPI + MCP，不启动 CognitiveBus
laap launch --no-bus

# 仅启动 FastAPI + CognitiveBus，不启动 MCP（用于纯 HTTP 部署）
laap launch --no-mcp

# MCP 使用 stdio 传输（由父进程拉起，如 Claude Code 直接调用）
laap launch --mcp-transport stdio --no-bus

# 完整参数
laap launch --host 0.0.0.0 \
            --http-port 8000 \
            --mcp-port 8766 \
            --bus-port 11550 \
            --mcp-transport sse \
            --no-bus \
            --no-mcp
```

**`laap launch --help` 输出**（spec 验收标准 #1）：

```
usage: laap launch [-h] [--host HOST] [--http-port HTTP_PORT]
                   [--mcp-port MCP_PORT] [--bus-port BUS_PORT]
                   [--no-bus] [--no-mcp]
                   [--mcp-transport {sse,stdio}]

Launch LAAP full entity (FastAPI + MCP + CognitiveBus)

options:
  --host HOST              Host to bind (default: 0.0.0.0)
  --http-port HTTP_PORT    HTTP API port (default: 8000)
  --mcp-port MCP_PORT      MCP SSE port (default: 8766)
  --bus-port BUS_PORT      CognitiveBus TCP port (default: 11550)
  --no-bus                 Do not start CognitiveBus
  --no-mcp                 Do not start MCP Server
  --mcp-transport {sse,stdio}  MCP transport mode (default: sse)
```

### 5.2 编程式启动

`launch_full_entity()` 函数签名（`laap/launcher.py`）：

```python
def launch_full_entity(
    host: str = "0.0.0.0",
    http_port: int = 8000,
    mcp_port: int = 8766,
    bus_port: int = 11550,
    no_bus: bool = False,
    no_mcp: bool = False,
    mcp_transport: str = "sse",
) -> None:
    """启动 LAAP 全量个体。

    Args:
        host: 监听地址
        http_port: FastAPI 端口
        mcp_port: MCP SSE 端口
        bus_port: CognitiveBus TCP 端口
        no_bus: 不启动 CognitiveBus
        no_mcp: 不启动 MCP Server
        mcp_transport: MCP 传输模式 "sse" 或 "stdio"
    """
```

**Python 启动示例**（亦可参考 `examples/access_modes/launch_full_entity.py`，由 Task 15 创建）：

```python
from laap.launcher import launch_full_entity, LAAPLauncher

# 方式 1：便捷函数（阻塞调用）
launch_full_entity(
    host="0.0.0.0",
    http_port=8000,
    mcp_port=8766,
    bus_port=11550,
    mcp_transport="sse",
)

# 方式 2：使用 LAAPLauncher 类（可访问 stats()）
launcher = LAAPLauncher(
    host="0.0.0.0",
    http_port=8000,
    mcp_port=8766,
    bus_port=11550,
    no_bus=False,
    no_mcp=False,
    mcp_transport="sse",
)

# 在另一线程启动（非阻塞）
import threading
t = threading.Thread(target=launcher.launch, daemon=True)
t.start()

# 查询启动器状态
import json
print(json.dumps(launcher.stats(), indent=2, ensure_ascii=False))
# 输出示例：
# {
#   "started_at": 1782775118.123,
#   "uptime": 42.5,
#   "services": {"api": "up", "mcp": "up", "cognitive_bus": "up"},
#   "host": "0.0.0.0",
#   "http_port": 8000,
#   "mcp_port": 8766,
#   "bus_port": 11550
# }
```

启动后控制台输出横幅（`LAAPLauncher._print_banner`）：

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   LAAP Living Agent — Full Entity Mode                       ║
║   意识 + 身体 一体化运行                                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

  HTTP API:    http://0.0.0.0:8000
  MCP Server:  http://0.0.0.0:8766 (SSE)
  CognitiveBus: tcp://0.0.0.0:11550
  Health:      http://0.0.0.0:8000/health
  WebSocket:   ws://0.0.0.0:8000/ws
  Society:     http://0.0.0.0:8000/society/
```

### 5.3 服务端口与配置

| 服务 | 默认端口 | 启动选项（CLI） | 启动选项（函数） | 说明 |
|------|---------|---------------|----------------|------|
| FastAPI HTTP/SSE | 8000 | `--http-port` | `http_port` | 主线程阻塞，提供 REST + WebSocket + SSE |
| MCP Server | 8766 | `--mcp-port` `--mcp-transport` | `mcp_port` `mcp_transport` | 守护线程，SSE 模式监听 HTTP，stdio 模式由父进程拉起 |
| CognitiveBus TCP | 11550 | `--bus-port` `--no-bus` | `bus_port` `no_bus` | 守护线程，P2P 数字生命体通信 |

**依赖**：
- FastAPI / uvicorn：`pip install fastapi uvicorn`（`laap[api]` extra）
- MCP：`pip install mcp`（FastMCP）
- CognitiveBus：依赖 `laap.agi.cognitive_bus_sync`（内置模块）

### 5.4 HTTP API 端点

FastAPI 服务（`laap/api/server.py`）暴露以下端点：

#### 健康检查与状态

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 聚合健康检查，返回 `{status, services, uptime}`，状态码：200 healthy / 200 degraded / 503 unavailable |

`/health` 响应示例：

```json
{
  "status": "healthy",
  "services": {
    "api": "up",
    "mcp": "up",
    "cognitive_bus": "up"
  },
  "uptime": 42.5
}
```

#### Agent 管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/agents/create` | 创建 Agent（type: codex / lifelike / 默认） |
| GET | `/agents` | 列出所有 Agent |
| GET | `/agents/{agent_id}` | 获取 Agent 详情 |
| POST | `/agents/{agent_id}/chat` | 与 Agent 对话（支持 `stream=true` SSE 流式） |
| POST | `/agents/{agent_id}/stream` | SSE 流式对话快捷端点 |
| POST | `/agents/{agent_id}/step` | LifelikeAgent 单步执行 |
| POST | `/agents/{agent_id}/rsi` | 触发 RSI 提案 |
| GET | `/agents/{agent_id}/tools` | 列出 Agent 可用工具 |

#### OpenAI 兼容接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/chat/completions` | OpenAI 兼容流式接口，可直接对接 OpenAI SDK 客户端 |

#### WebSocket 推送

| 方法 | 路径 | 说明 |
|------|------|------|
| WS | `/ws` | WebSocket 推送端点，客户端可订阅特定事件类型 |

`/ws` 客户端订阅示例：

```javascript
const ws = new WebSocket("ws://localhost:8000/ws");
ws.onopen = () => {
  // 订阅特定事件类型
  ws.send(JSON.stringify({ subscribe: ["psi_state", "memory_update"] }));
};
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Event:", data.type, "Payload:", data.payload);
};
```

`WebSocketManager.broadcast(event_type, payload)` 仅推送给订阅了该 `event_type` 的客户端（按订阅过滤，未订阅事件不会推送）。

#### Society 多生命体协作视图（`/society/*`）

由 `laap/api/society_server.py` 的 `APIRouter(prefix="/society")` 挂载：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/society/sandboxes` | 列出所有沙箱状态 |
| GET | `/society/agents` | 列出所有 Agent |
| GET | `/society/suggestions` | 列出待审建议 |
| GET | `/society/lifeforms` | 列出所有数字生命体 |
| GET | `/society/psi-status` | 获取 PSI 认知状态（可选 `?agent_id=xxx`） |
| GET | `/society/causal-graph` | 获取因果图 |
| GET | `/society/rsi-suggestions` | 列出 RSI 建议 |
| GET | `/society/memory-status` | 获取记忆层级状态（可选 `?agent_id=xxx`） |

---

## 6. B2 — Hermes Desktop 完全体部署

Hermes Desktop 是 LAAP 的桌面端数字生命交互前端（React + LaapSociety 组件），通过 HTTP / WebSocket 调用 B1 启动的 LAAP 后端。

### 6.1 部署步骤

1. **启动 LAAP 后端**（B1 模式）：

   ```bash
   laap launch --http-port 8000 --mcp-port 8766 --bus-port 11550
   ```

2. **启动 Hermes Desktop 前端**：

   Hermes Desktop 集成路径通过环境变量指定：

   ```bash
   # Windows
   set HERMES_ROOT=C:\path\to\hermes-desktop
   set HERMES_PROFILE=ao

   # macOS / Linux
   export HERMES_ROOT=/path/to/hermes-desktop
   export HERMES_PROFILE=ao

   # 启动 Hermes CLI（由 laap __main__ 自动拉起）
   laap
   ```

   或直接通过 `python -m laap` 启动（`laap/__main__.py` 会初始化 PSI 内核 + Heartbeat + Hermes Bridge，然后启动 Hermes CLI）。

3. **验证集成**：

   ```bash
   # 检查后端健康
   curl http://localhost:8000/health

   # 检查 society 端点
   curl http://localhost:8000/society/lifeforms

   # Hermes Desktop 通过 WebSocket 订阅事件
   # 在前端 DevTools Console 验证 ws://localhost:8000/ws 连接
   ```

### 6.2 Hermes Desktop 功能

Hermes Desktop 通过 B1 后端访问以下能力：

- **LaapSociety 视图**：调用 `/society/*` 端点展示多生命体协作状态。
- **实时事件推送**：通过 `/ws` 订阅 `psi_state`、`memory_update` 等事件类型。
- **Agent 对话**：通过 `/agents/{id}/chat` 或 `/v1/chat/completions` 调用 LAAP Agent。
- **MCP 工具调用**：通过 MCP SSE 端点（`http://localhost:8766/sse`）调用 14 个 MCP 工具。

> **注意**：Hermes Desktop React 屏幕完善不在本期实施范围（spec「实施边界」明确排除），现有 LaapSociety 组件可直接对接 B1 后端使用。

---

## 7. 故障排查

### 7.1 常见错误码

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| `ImportError: claude-code-sdk not installed. Install with: pip install claude-code-sdk` | `ClaudeCodeAdapter` 缺失 SDK | `pip install claude-code-sdk` |
| `ImportError: OpenClaw not installed. Install with: pip install openclaw` | `OpenClawAdapter` 缺失 SDK | `pip install openclaw` |
| `ImportError: pip install mcp` | MCP Server 缺失 FastMCP | `pip install mcp` |
| `uvicorn not installed. Install with: pip install uvicorn fastapi` | 启动器缺失 uvicorn | `pip install uvicorn fastapi`（或 `pip install laap[api]`） |
| `NotImplementedError: Adapter 'xxx' not implemented` | `mount_brain_to_agent` 显式指定了不存在的 adapter | 改用 `agent_type="auto"` 或检查拼写（仅 `hermes` / `claude_code` / `openclaw` / `generic`） |
| HTTP `503 unavailable` | `/health` 检测到所有下游服务（mcp / cognitive_bus）离线 | 检查 launcher 启动日志，确认 MCP 与 CognitiveBus 模块可加载 |
| HTTP `200 degraded` | 部分下游服务离线 | 查看 `/health` 响应的 `services` 字段，定位具体离线服务 |
| HTTP `200 healthy` | 所有服务正常 | 无需处理 |
| WebSocket 连接失败 | `/ws` 端点未挂载或 FastAPI 不可达 | 确认 FastAPI 已启动（`curl http://localhost:8000/health`），检查端口占用 |
| MCP 工具调用超时 | SSE 连接断开或 MCP Server 未启动 | 确认 `http://localhost:8766/sse` 可达，重启 MCP Server |
| `[LAAP Error] <message>` | `laap_before_turn` / `laap_after_tool` / `laap_after_turn` 内部异常 | 查看异常信息，通常是 `session_id` 为空或 `LaapBrain` 初始化失败 |

### 7.2 日志位置

LAAP 使用 Python 标准 `logging` 模块，日志输出到 stderr / 控制台：

| 日志类型 | 位置 | 说明 |
|---------|------|------|
| LAAP 服务日志 | stderr / 控制台 | `laap.launcher`、`laap.api`、`laap.mcp.server` logger |
| 大脑日志 | stderr / 控制台 | `laap_brain` logger |
| MCP session 持久化 | `~/.laap/mcp_sessions.json` | `session_id` → `lifeform_id` 映射，由 `laap.mcp.session_registry` 维护 |
| Handshake 状态 | `~/.laap/handshake.json` | 数字生命体握手协议状态 |
| Lifeforms 心跳 | `~/.laap/lifeforms/` | 各生命体心跳数据目录 |

启用 DEBUG 日志：

```bash
# 启动时设置日志级别
export LAAP_LOG_LEVEL=DEBUG  # macOS / Linux
set LAAP_LOG_LEVEL=DEBUG     # Windows

# 或在 Python 中配置
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 7.3 性能调优

根据 spec 非功能指标：

| 指标 | 目标值 | 调优建议 |
|------|--------|---------|
| MCP 钩子工具响应延迟 | < 100ms（不含 LLM 调用） | `laap_before_turn` / `laap_after_tool` / `laap_after_turn` 不调用 LLM，纯本地计算；若超时检查 `LaapBrain` 是否启用了原生 LAAP 深度集成（`has_native=True` 会增加 `native_brain.think()` 调用） |
| 启动器冷启动时间 | < 3 秒 | CognitiveBus 与 MCP 在守护线程启动，FastAPI 阻塞主线程；若超时检查 uvicorn 启动日志 |
| WebSocket 广播 | 按订阅过滤 | `WebSocketManager.broadcast()` 仅推送给订阅了该 `event_type` 的客户端，未订阅事件不会推送，避免无效流量 |
| 单元测试覆盖率 | ≥ 70% | 运行 `pytest --cov=laap --cov=laap_brain` 验证 |
| 向后兼容性 | 100% | `enhance(return_adapter=False)` 保持 v3.1 行为；`laap_brain.LaapBrain` API 未变 |

**性能验证命令**：

```bash
# 冷启动时间测试
time laap launch --no-bus --no-mcp --http-port 8001 &
sleep 2
curl http://localhost:8001/health
kill %1

# MCP 钩子延迟测试（需先启动 MCP Server）
time curl -X POST http://localhost:8766/sse \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "laap_before_turn", "arguments": {"session_id": "test", "user_message": "hello"}}}'
```

---

## 附录：示例文件

完整的可运行示例位于 `examples/access_modes/` 目录（由 Task 15 创建）：

| 文件 | 对应章节 | 说明 |
|------|---------|------|
| `examples/access_modes/claude_code_mcp.json` | §2.1 | Claude Code MCP 配置示例 |
| `examples/access_modes/cursor_mcp.json` | §2.2 | Cursor MCP 配置示例 |
| `examples/access_modes/openclaw_sdk.py` | §3.2 | OpenClaw SDK 集成完整示例 |
| `examples/access_modes/generic_python_agent.py` | §3.4 | 通用 Python Agent 集成示例 |
| `examples/access_modes/launch_full_entity.py` | §5.2 | 编程式启动 LAAP 全量个体示例 |

每个文件可独立运行（含必要注释与 shebang）。

---

## 附录：相关文件索引

| 模块 | 文件路径 | 说明 |
|------|---------|------|
| LAAP SDK 入口 | `laap/sdk/__init__.py` | 导出 `AgentAdapter`、`mount_brain_to_agent` |
| SDK 挂载逻辑 | `laap/sdk/mount.py` | `mount_brain_to_agent()` 实现 |
| Hermes 适配器 | `laap/sdk/adapters/hermes.py` | `HermesAdapter` |
| Claude Code 适配器 | `laap/sdk/adapters/claude_code.py` | `ClaudeCodeAdapter` |
| OpenClaw 适配器 | `laap/sdk/adapters/openclaw.py` | `OpenClawAdapter` |
| Generic 适配器 | `laap/sdk/adapters/generic.py` | `GenericAdapter` |
| LAAP 启动器 | `laap/launcher.py` | `LAAPLauncher`、`launch_full_entity()` |
| launch 子命令 | `laap/cli/subcommands/launch_cmd.py` | `laap launch` CLI 注册 |
| CLI 主入口 | `laap/cli/main.py` | `COMMANDS` 字典，自动加载 launch |
| MCP Server | `laap/mcp/server.py` | `LAAPMCPServer`，14 个 MCP 工具 |
| MCP session 注册表 | `laap/mcp/session_registry.py` | `session_id` ↔ `lifeform_id` 映射 |
| FastAPI 服务 | `laap/api/server.py` | HTTP / SSE / WebSocket 端点 |
| Society 路由 | `laap/api/society_server.py` | `/society/*` 路由 |
| WebSocket 管理器 | `laap/api/websocket.py` | `WebSocketManager`，按订阅过滤广播 |
| LAAP Brain | `laap_brain/__init__.py` | `LaapBrain`、`enhance()` |
| LAAP 入口 | `laap/__main__.py` | `python -m laap` 启动 PSI + Hermes |
