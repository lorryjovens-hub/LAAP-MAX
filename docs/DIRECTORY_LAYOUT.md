# LAAP 目录布局治理

> 本文件定义 `laap/`、`legacy/`、`scripts/`、`docs/`、`demos/`、`tests/` 的用途与准入规则。所有新增文件应优先落入对应目录；如需新增顶层目录，必须先在 `docs/PROJECT_INDEX.md` 登记。

## 1. `laap/` — 主包

**用途**：LAAP 数字生命体核心 Python 包。包含 CLI/TUI、AGI 认知框架、LLM 路由、RAG、MCP、技能市场、网关、工具链、安全区等。

**准入规则**：
- ✅ 必须是被 `pyproject.toml` 包含的 Python 包代码。
- ✅ 每个子包需有明确的单一职责（SRP），禁止出现“大杂烩”模块。
- ✅ 新增子系统应先在 `docs/PROJECT_INDEX.md` 登记。
- ❌ 禁止放置启动脚本、一次性实验脚本、平台特定脚本。
- ❌ 禁止放置已废弃的 Aris/qlam 代码；如需兼容请通过 `legacy/` 或 `laap/agi/` 迁移。

**当前主要子目录**：

| 子目录 | 用途 |
|--------|------|
| `laap/api/` | REST / WebSocket / SSE 服务端入口 |
| `laap/cli/` | 命令行与交互式 REPL/TUI |
| `laap/agi/` | 统一 AGI 认知框架 |
| `laap/llm/` | LLM 工厂、提供者、路由 |
| `laap/rag/` | RAG 检索增强生成 |
| `laap/mcp/` | Model Context Protocol 客户端/服务器 |
| `laap/skills/` | 技能市场、加载器、Curator |
| `laap/tools/` | 工具注册表与内置工具 |
| `laap/ui/` | TUI/3D 形象/声音主题 |
| `laap/gateway/` | 飞书等外部网关 |
| `laap/security/` | 安全区与访问控制 |

## 2. `legacy/` — 归档登记

**用途**：集中登记全仓库已废弃但仍保留的模块、包、脚本、文档。`legacy/` 本身不一定存放代码，但所有归档项必须在此索引中可见。

**准入规则**：
- ✅ 接收已废弃且不再新开发的代码登记。
- ✅ 原位保留的废弃模块（如 `aris_brain/`、`laap/qlam/`）在此登记。
- ✅ 从根目录移入 `scripts/legacy/` 的启动脚本在此登记。
- ❌ 禁止将活跃代码直接移入 `legacy/`（除非整个子包已确认无活跃引用）。
- ❌ 禁止删除已登记项，仅做移动/归档。

**相关文件**：
- `legacy/INDEX.md`：归档总表，含原因、替代实现、时间、状态。
- `scripts/legacy/README.md`：已不推荐使用的启动脚本清单。

## 3. `scripts/` — 项目脚本

**用途**：所有与 LAAP 项目维护、启动、安装、开发相关的脚本。

### 3.1 `scripts/windows/`

**用途**：Windows 平台专用脚本（`.bat`、`.cmd`、`.ps1`）。

**准入规则**：
- ✅ 当前可用的 Windows 启动/安装/工具脚本。
- ✅ 脚本应使用相对路径或 `%CD%`/`$PSScriptRoot`，避免硬编码 `D:\LAAP`。
- ❌ 禁止放入已废弃、硬编码路径、引用不存在文件的旧脚本（那些进 `scripts/legacy/`）。

**当前内容示例**：
- `install.bat`：Windows 安装器
- `laap.cmd`：Windows CMD 主入口包装
- `setup_path.bat`：环境变量设置

### 3.2 `scripts/unix/`

**用途**：macOS / Linux / WSL 平台专用脚本（`.sh`）。

**准入规则**：
- ✅ 当前可用的 Unix 安装/发布/工具脚本。
- ✅ 脚本应使用 `$(cd "$(dirname "$0")" && pwd)` 等相对路径写法。
- ❌ 禁止放入硬编码 `/opt/aris` 等环境特定路径的旧脚本（那些进 `scripts/legacy/`）。

**当前内容示例**：
- `install.sh`：Unix 安装器
- `publish.sh`：发布脚本

### 3.3 `scripts/development/`

**用途**：跨平台开发/工具脚本（主要为 Python），不依赖特定操作系统。

**准入规则**：
- ✅ 跨平台 CI、清理、数据生成、分析、安装辅助脚本。
- ✅ 应能在 Windows 与 Unix 上无修改运行（优先使用 Python 标准库）。
- ❌ 禁止放入一次性调试脚本、个人实验脚本（那些进 `scripts/legacy/` 或留在本地）。

**当前内容示例**：
- `ci_test_runner.py`
- `clean_cache.py`
- `install.py`

### 3.4 `scripts/legacy/`

**用途**：已不推荐使用的旧启动脚本归档。

**准入规则**：
- ✅ 功能重复、平台相关、硬编码路径、引用已不存在文件、依赖外部 Hermes 特定版本的脚本。
- ✅ 必须附带 `scripts/legacy/README.md` 说明废弃原因与替代命令。
- ❌ 禁止新增脚本到此目录。

## 4. `docs/` — 文档

**用途**：项目级文档、设计论文、安全模型、快速开始、索引。

**准入规则**：
- ✅ 面向贡献者/用户的说明文档（`.md`）。
- ✅ 架构决策、安全模型、API 说明、升级计划。
- ❌ 禁止放置个人笔记、未整理草稿（可先放入 `docs/drafts/` 并在整理后转正）。
- ❌ 禁止放置代码生成物（如图表可由 `docs/figures.py` 生成，但输出应进 `results/` 或 `.laap/`）。

**建议子目录**：
- `docs/legacy/`：已归档的旧规划/设计文档。
- `docs/drafts/`：待整理的草稿（不设则默认不放）。

## 5. `demos/` — 演示

**用途**：独立可运行的演示页面或最小可复现示例。

**准入规则**：
- ✅ 可直接用浏览器或 `python` 运行的演示。
- ✅ 代码应尽量自包含，避免依赖主包内部未公开 API。
- ❌ 禁止放置生产代码、测试代码、开发脚本。

## 6. `tests/` — 测试

**用途**：pytest 测试套件。

**准入规则**：
- ✅ 单元测试、集成测试、AGI 能力测试。
- ✅ 测试名与 `laap/` 模块结构对齐。
- ❌ 禁止将测试脚本放在根目录或 `laap/` 包内（特殊 harness 除外）。
- ❌ 禁止提交大型二进制或敏感凭证。

## 7. 根目录保留清单

根目录应保持最小化。以下类型可保留：

| 类型 | 示例 | 说明 |
|------|------|------|
| 项目元数据 | `pyproject.toml`、`README.md`、`LICENSE` | 必须 |
| 版本/配置 | `VERSION.json`、`VERSIONS.yaml`、`.env.example` | 允许 |
| 最小入口包装 | `laap.cmd`（可选） | 若保留，必须代理到 `python -m laap` |
| CI/容器 | `Dockerfile`、`docker-compose.yml`、`.github/` | 允许 |

**不应出现在根目录**：
- 大量 `.bat` / `.ps1` / `.sh` 启动脚本 → 移入 `scripts/`
- 个人调试脚本 `test_*.py` / `debug_*.py` → 移入 `tests/` 或 `scripts/development/`
- 历史归档代码 → 移入 `_archive/` 或 `legacy/`

## 8. 决策流程

新增文件时按以下顺序判断：

1. 是核心 Python 包代码？ → `laap/`
2. 是测试代码？ → `tests/`
3. 是文档？ → `docs/`
4. 是演示？ → `demos/`
5. 是脚本？按平台/用途进入 `scripts/windows/`、`scripts/unix/`、`scripts/development/`
6. 是废弃脚本？ → `scripts/legacy/` 并在 `legacy/INDEX.md` 登记
7. 都不属于？先在 `docs/PROJECT_INDEX.md` 登记，再决定位置。

## 9. 维护记录

| 时间 | 变更 | 负责人 |
|------|------|--------|
| 2026-07-11 | 创建本布局治理文档，整理 `scripts/` 子目录 | Phase 1 |
