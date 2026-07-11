# LAAP 归档代码登记表

> **核心原则**：归档不删除。所有废弃代码 MUST 保留原位（或移至 `legacy/` 子目录），在文件头添加 `DEPRECATED` 标注，并在此登记。
>
> **删除例外**：仅当文件为完全空白的占位 `__init__.py` 或重复定义的纯代码冗余（如重复方法）时，才允许直接删除。

## 登记表

| 原路径 | 类型 | 废弃原因 | 替代实现 | 废弃时间 | 状态 | 备注 |
|--------|------|---------|---------|---------|------|------|
| `laap/evolution/rsi.py` | 模块 | 宣称 True RSI 但实际为参数调优循环 | `laap/agi/rsi_engine.py`（参数调优）+ M4 阶段 True RSI | 2026-06-30 | DEPRECATED，原位保留 | import 链保留：`from laap.evolution.rsi import RSIEngine` 仍可用 |
| `laap/qlam/` | 包 | 经典 sigmoid 包装伪称"量子" | `laap/glam/`（Gated Long-Attention Memory） | 2026-06-30 | DEPRECATED，原位保留 | 历史命名 qlam = Quantum Long-Attention Memory，实际为 sigmoid |
| `laap/orchestration/psi_harness.py` | 模块 | PSI-Harness 双实现合并 | `laap/orchestration/psi_harness_bridge.py` | 2026-07-11 | DEPRECATED，原位保留 | 公共 API 委托至 bridge：`PSIActor`、`HarnessActor`、`build_psi_harness_net`、`PSIHarnessOrchestrator` |
| `laap/orchestration/protocol.py` | 模块 | AgentMessage/MessageType 语义合并至 primitives | `laap/orchestration/primitives.py` | 2026-07-11 | DEPRECATED，原位保留 | `AgentMessage`/`MessageType`/`MessageRouter` 均为 Aether 原语别名 |
| `laap/agent/base.py` | 模块 | Agent 对外入口统一至 agent_core/agent.py | `laap/agent_core/agent.Agent(mode="agi")` | 2026-07-11 | DEPRECATED，原位保留 | `AGIBrain` 与 `Agent` 别名保留，继续作为 `Agent(mode="agi")` 的底层实现 |
| `laap/agent/lifelike.py` | 模块 | Agent 对外入口统一至 agent_core/agent.py | `laap/agent_core/agent.Agent(mode="agi")` | 2026-07-11 | DEPRECATED，原位保留 | 功能将逐步迁移到 agent_core/ |
| `laap/agent/codex.py` | 模块 | Agent 对外入口统一至 agent_core/agent.py | `laap/agent_core/agent.Agent(mode="agi")` | 2026-07-11 | DEPRECATED，原位保留 | 功能将逐步迁移到 agent_core/ |
| `aris_brain/` | 包 | 旧版"Aris 大脑"v7~v12 历史实现 | `laap/agi/`（统一 AGI 框架 v3.0） | M1 阶段 | 待归档 | 200+ 文件，仅添加 DEPRECATED 标注 |
| `aris_v10/` | 包 | 独立认知运行时（零依赖版） | `laap/agi/` | M1 阶段 | 待归档 | 9 文件 |
| `aris/` | 包 | 早期实验性实现 | `laap/agi/` | M1 阶段 | 待归档 | 如存在 |
| `laap_brain/core.py` | 模块 | 已标 DEPRECATED 但 kernel.py 仍 active | `laap_brain/kernel.py` | 早期 | 已标 DEPRECATED | 14 文件嵌入式内核 v3.1 |
| `laap/agent_core/plugins/`（部分） | 子包 | 9 个占位插件（仅 `__init__.py`） | M1 阶段补实质实现或归档 | M1 阶段 | 待评估 | 无价值者移至 `legacy/plugins/` |
| `LAAP_UPGRADE_PLAN.md` 等 4 份 | 文档 | 4 份并行升级方案造成混乱 | 合并为 `LAAP_ROADMAP.md` | M0-A6 | 待归档 | 旧文档移至 `docs/legacy/` |

## 归档策略

### 1. 模块/包级归档（保留原位）

适用场景：模块被其他代码 import，删除会破坏 import 链。

操作步骤：
1. 在文件头添加 `DEPRECATED` 标注块（见下方模板）
2. 保留所有原有代码与导出
3. 在 `legacy/INDEX.md` 登记
4. 如有 `__init__.py` 导出，加 `warnings.warn(..., DeprecationWarning)`

### 2. 子包级归档（移至 legacy/）

适用场景：整个子包已无任何活跃引用，可安全移动。

操作步骤：
1. `git mv <path> legacy/<path>`
2. 在新位置添加 `DEPRECATED.md`
3. 在 `legacy/INDEX.md` 登记
4. 全仓库 grep 确认无残留 import

### 3. 文档级归档（移至 docs/legacy/）

适用场景：旧版本规划/设计文档被新文档取代。

操作步骤：
1. `git mv <doc> docs/legacy/<doc>`
2. 在 `docs/legacy/README.md` 列出所有归档文档
3. 在 `legacy/INDEX.md` 登记

## DEPRECATED 标注模板

### Python 文件头标注

```python
"""
[原模块名与功能描述]

DEPRECATED — 本模块已废弃
=========================
废弃原因：[原因]
替代实现：[新路径/新方案]
废弃时间：[YYYY-MM-DD]
登记位置：legacy/INDEX.md

代码保留目的：[说明为何不删除，如 import 兼容、历史追溯、回滚备份]
"""
```

### 包级 DEPRECATED.md

```markdown
# [包名] — DEPRECATED

**废弃原因**：[原因]
**替代实现**：[新路径]
**废弃时间**：[YYYY-MM-DD]
**登记位置**：[legacy/INDEX.md](../legacy/INDEX.md)

## 保留目的

[说明为何不删除]

## 历史价值

[简述此包在 LAAP 演化中的历史意义]
```

## 4. Phase 1 新增归档项（启动脚本）

> 2026-07-11 由 Spec `consolidate-laap-infrastructure-and-distributed-actors` Phase 1 从根目录移入 `scripts/legacy/`。
> 完整清单与替代命令见 `scripts/legacy/README.md`。

| 原路径 | 类型 | 废弃原因 | 替代实现 | 废弃时间 | 状态 | 备注 |
|--------|------|---------|---------|---------|------|------|
| `laap.bat` | 脚本 | 硬编码 `D:\LAAP\laap\cli\main.py` | `python -m laap` / `scripts/windows/laap.cmd` | 2026-07-11 | ARCHIVED | 已移入 `scripts/legacy/` |
| `laap.ps1` | 脚本 | 硬编码 `D:\LAAP\laap\cli\laap_main.py` | `python -m laap` | 2026-07-11 | ARCHIVED | 已移入 `scripts/legacy/` |
| `start*.bat` / `start_*.bat` / `start-*.bat` / `start_*.cmd` | 脚本 | 引用已不存在的 `laap_web.py` 或硬编码外部路径 | `python -m laap.web.server` / `serve_web.py` | 2026-07-11 | ARCHIVED | 已批量移入 `scripts/legacy/` |
| `laap-aris.*` / `hermes-aris.ps1` / `aris_*.bat` | 脚本 | Aris 历史入口，硬编码路径与端口 | `python -m laap`（已脱离 Aris） | 2026-07-11 | ARCHIVED | 已移入 `scripts/legacy/` |
| `LAAP_Launcher.bat` / `LAAP_Ultimate.bat` | 脚本 | 旧版控制面板/终极启动器，硬编码路径 | `python -m laap` | 2026-07-11 | ARCHIVED | 已移入 `scripts/legacy/` |
| `launch_ao.py` | 脚本 | 硬编码 `D:\LAAP` 与 `D:\hermes-agent-main`，依赖不存在模块 | `python -m laap` | 2026-07-11 | ARCHIVED | 已移入 `scripts/legacy/` |
| `launch_desktop.py` | 脚本 | 引用不存在的 `laap_desktop_server.py` 与 `laap_desktop/` | 不推荐 | 2026-07-11 | ARCHIVED | 已移入 `scripts/legacy/` |
| `_start_aris.sh` | 脚本 | 硬编码 `/opt/aris` 与飞书凭证，环境特定 | 不推荐直接运行 | 2026-07-11 | ARCHIVED | 已移入 `scripts/legacy/` |
| `start-gen*.bat` / `start-gen*.ps1` | 脚本 | 依赖外部 Hermes 特定路径，历史世代入口 | `python -m laap` | 2026-07-11 | ARCHIVED | 已移入 `scripts/legacy/` |

## 验证清单

- [x] `legacy/INDEX.md` 每条登记对应实际存在的文件/目录
- [ ] 所有 DEPRECATED 文件头标注完整（原因/替代/时间/登记位置）
- [ ] 所有 DEPRECATED 模块仍可被 import（如保留导出）
- [ ] 所有 DEPRECATED 包有 `DEPRECATED.md`
- [ ] `pytest tests/` 全过（确认归档未破坏功能）
