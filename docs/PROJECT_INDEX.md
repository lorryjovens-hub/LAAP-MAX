# LAAP 项目全局索引

> 本索引由 Spec `consolidate-laap-infrastructure-and-distributed-actors` Phase 1 建立，用于在仓库规模持续扩大时快速定位模块边界、入口与状态。
> 维护原则：**状态标记 > 目录约定 > 个人记忆**。新增顶层目录必须先在此登记。

## 1. 顶层模块索引

| 模块 | 职责 | 推荐入口 | 关键依赖 | 状态 | 相关 spec |
|------|------|---------|---------|------|-----------|
| `laap/` | LAAP 主包：CLI、TUI、AGI 认知框架、LLM 路由、RAG、MCP、技能市场、网关、工具链 | `python -m laap` / `laap`（pip install 后） | pydantic、httpx、rich、openai、anthropic、pytest、PyYAML、scipy | 重构中 | `consolidate-laap-infrastructure-and-distributed-actors` |
| `aris_brain/` | 旧版 Aris 大脑 v7~v12 的历史实现（PSI 服务、感知、守护进程） | 不推荐直接启动；如需兼容见 `scripts/legacy/laap-aris*` | Python 标准库、本地 SQLite | 废弃 | `consolidate-laap-infrastructure-and-distributed-actors` |
| `laap_brain/` | 第二代嵌入式认知内核（v3.1+），与 `laap/agi/` 职责重叠 | **根目录缺失**，仅 `pyproject.toml` 仍声明包含；代码散见于 `external/` 与 `_archive/` | — | 占位/待迁移 | 待补充 |
| `harness/` | 开发脚手架与 UI 模板库（`laap-coding`）、示例与最小可复现脚本 | `python -m laap_coding`（安装后） / `harness/example.py` | pydantic、setuptools、Vite/React 模板 | 重构中 | `consolidate-laap-infrastructure-and-distributed-actors` |
| `external/` | 外部依赖/第三方仓库镜像（AFlow、laap-agent、os-ai-computer-use、GhostDesk 等） | 按需引用，禁止直接修改 | 各子仓库自有依赖 | 稳定 | 待补充 |
| `ui/` | 面向 LAAP 数字生命体的 React + Vite Web UI | `npm run dev`（需先 `npm install`） | React、Tailwind CSS、Zustand、Recharts、Vite | 稳定 | 待补充 |
| `ui-main/` | 现代 monorepo 工程模板与发布流程（Turborepo、pnpm、ESLint、TypeScript） | `pnpm dev` / `pnpm build` | pnpm、Turborepo、React、TypeScript | 稳定 | 待补充 |
| `rust_core/` | Rust 高性能扩展（CUA 驱动、lib.rs） | `cargo build --release` / `maturin develop`（如有 maturin 配置） | PyO3、reqwest、serde、anyhow | 稳定 | 待补充 |
| `godot/` | Godot 4.7 相关资源与运行时包 | 当前仅 `godot_4.7.zip` | Godot Engine | 占位 | 待补充 |
| `demos/` | 独立可运行的 HTML/浏览器演示 | `demos/bangbang_3d.html` | 浏览器、Three.js（CDN） | 稳定 | 待补充 |
| `docs/` | 项目文档、设计论文、安全模型、快速开始、本索引 | `docs/quickstart.md` | Markdown | 重构中 | 本 spec |
| `tests/` | pytest 测试套件（unit + agi） | `pytest tests/` / `python -m pytest` | pytest、pytest-asyncio、pytest-cov | 稳定 | 待补充 |
| `scripts/` | 项目维护脚本：启动/安装/开发/归档 | 见 `scripts/windows/`、`scripts/unix/`、`scripts/development/`、`scripts/legacy/` | PowerShell/Bash/Python | 重构中 | 本 spec |
| `.trae/specs/` | Trae IDE 的 spec 目录（当前尚未创建） | — | — | 占位 | 待补充 |
| `.github/` | GitHub 配置（FUNDING 等） | — | GitHub Actions（未来） | 稳定 | 待补充 |

## 2. 废弃模块与替代实现

| 废弃模块 | 废弃原因 | 替代实现 | 备注 |
|----------|---------|---------|------|
| `aris_brain/` | 旧版 Aris v7~v12 历史实现，与 `laap/agi/` 重复 | `laap/agi/`（统一 AGI 框架 v3.0） | 200+ 文件，仅做标注与归档，不删除；相关启动脚本已移入 `scripts/legacy/` |
| `laap/qlam/` | 经典 sigmoid 包装伪称“量子” | `laap/glam/`（Gated Long-Attention Memory） | 已在 `legacy/INDEX.md` 登记 |
| `laap/evolution/rsi.py` | 宣称 True RSI 但实际为参数调优循环 | `laap/agi/rsi_engine.py`（参数调优）+ M4 阶段 True RSI | import 链保留兼容 |
| `_archive/` | 早期实验代码、旧 laap_brain、旧 Aris 等历史沉淀 | `laap/`、`rust_core/`、`ui/` 等当前实现 | 完全归档，不做新功能开发 |
| 根目录 `start*.bat`、`laap_web.py` 引用类脚本 | 硬编码 `D:\LAAP`、引用已不存在的 `laap_web.py` 等路径 | `python -m laap`、`laap.cmd` | 已移入 `scripts/legacy/` |

## 3. 其他顶层目录（补充登记）

| 模块 | 职责 | 状态 | 备注 |
|------|------|------|------|
| `_archive/` | 历史归档（旧 Aris、旧 laap_brain、Psi 等） | 废弃 | 与 `legacy/` 同级但独立，保留历史 |
| `Agent-Reach/` | Agent-Reach 互联网通道实验 | 重构中 | 含 `llms.txt`、测试脚本 |
| `laap-open/` | 开源子项目（.env 示例、LICENSE） | 稳定 | 独立 LICENSE |
| `laap_agent/` | Agent v1~v3 实验实现 | 重构中 | 与 `laap/agent/` 功能重叠，待评估 |
| `app/` | 小型服务模型定义 | 占位 | 与 `laap/saas/` 可能重复 |
| `analysis/` | 分析文档 | 稳定 | 只读文档 |
| `benchmarks/` | 性能基准（`run_p0.py`） | 重构中 | 部分结果已迁移到 `results/` |
| `claw-in-chrome/` | Chrome 扩展 gif 工具 | 占位 | 仅一个文件 |
| `experiments/` | 空实验目录 | 占位 | 待清理或补充 README |
| `packages/` | 独立包（`laap_consciousness`） | 重构中 | 可能与主包合并 |
| `papers/` | 论文与学术材料 | 稳定 | 只读 |
| `results/` | 基准与验证结果 JSON | 稳定 | 由测试生成 |
| `wiki/` | Obsidian 知识库 | 稳定 | 用户文档 |
| `.laap/` | 本地运行时配置与经验数据 | 稳定 | 含 `config.json`、`experiences.json` |
| `LAAP WIKI/` / `LAAP网站设计/` | 早期 UI/设计实验 | 废弃 | 考虑后续移入 `_archive/` |

## 4. 入口速查

```bash
# 主入口（推荐）
python -m laap --help
laap --help              # pip install -e . 后
laap-workspace --help    # 工作空间 CLI

# 安装
scripts/windows/install.bat    # Windows
scripts/unix/install.sh        # macOS / Linux / WSL

# 测试
pytest tests/

# UI 开发
cd ui && npm run dev
cd ui-main && pnpm dev

# Rust 核心
cd rust_core && cargo build --release
```

## 5. 维护记录

| 时间 | 变更 | 负责人 |
|------|------|--------|
| 2026-07-11 | 创建本索引，整理根目录启动脚本 | Phase 1 |
