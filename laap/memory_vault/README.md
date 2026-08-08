# LAAP Memory Vault

数字生命记忆库 — 每个 Agent 独立加密的跨会话记忆保险库。

## 架构概览

本模块包含两套互补的记忆系统：

| 组件 | 类 | 用途 | 文件 |
|------|------|------|------|
| 旧版共享 vault | `MemoryVault` | Aris & Lorry 共享聊天记忆（`aris_lorry_vault.db`） | `vault_manager.py` |
| 新版 per-agent vault | `VaultManager` | 每个 agent 独立加密 vault（`{agent}_vault.db`） | `vault_manager.py` |

P1-memory-vault 引入 `VaultManager`，使任意新 agent 创建时自动生成独立加密 vault，接入 MCP 工具 `memory_store` / `memory_retrieve` / `memory_consolidate`。

## 自动初始化机制

### 触发时机

1. **Hanako agent 创建路径**：`hanako/core/agent-manager.ts` 的 `createAgent()` 方法在成功创建 agent 后，best-effort 调用 sidecar `POST /vault/init`（非阻塞，失败仅记录警告）
2. **首次 store 调用自动初始化**：若 agent 的 vault 尚未初始化，`VaultManager.store()` 会自动调用 `init_for_agent()`
3. **Aris 每轮对话**：`hanako/aris-bridge/aris-plugin/index.js` 的 `session:after.message` hook 把每轮对话摘要写入 aris 的 episodic vault

### 幂等性

`init_for_agent(agent_name)` 严格幂等：
- vault 文件已存在时仅 `CREATE TABLE IF NOT EXISTS`，不覆盖数据
- `vault_meta` 表用 `INSERT OR REPLACE` 更新元信息
- 重复调用安全，不会破坏已有记忆

### 跨 agent 隔离

每个 agent 拥有独立的 `{agent_name}_vault.db` 文件。`VaultManager.retrieve(agent_name, query)` 只查询指定 agent 的 vault，物理隔离保证 Aris 的 vault 不会被 Butter 查询到。

## 密钥派生

vault 密钥从 `laap/security/crypto/keys.py` 的 `KeyManager` 派生：

```
key_id = f"vault-{slug}"           # slug 是规范化的 agent_name
key_hex = KeyManager.generate(key_id).private_key   # 64 字符 SHA256 hex
```

### SQLCipher 支持

- 优先使用 `pysqlite3`（含 SQLCipher），通过 `PRAGMA key = "x'{key_hex}'"` 加密
- 若 `pysqlite3` 不可用（标准库 `sqlite3` 无 SQLCipher 支持），降级为非加密但文件隔离的 vault
- `vault_meta.sqlcipher_enabled` 字段记录当前 vault 是否启用加密
- 升级路径：安装 `pip install pysqlite3-binary` 后重启即可启用加密，旧 vault 需重新初始化

## MCP 工具用法

`laap/mcp/server.py` 注册三个 MCP 工具（基于 FastMCP）：

### memory_store

```python
# 写入 episodic 记忆
result = await memory_store(
    scope="episodic",          # episodic / semantic / procedural / working / meta
    content="用户提到项目 X 架构",
    metadata={"source": "chat"},  # 可选
    agent_name="aris",         # 默认 aris
)
# 返回: {"stored": true, "memory_id": "mem_xxxx", "scope": "episodic", "id": 1}
```

### memory_retrieve

```python
# 检索记忆
results = await memory_retrieve(
    query="项目 X",
    scope="episodic",     # 可选，限定层级
    limit=10,             # 默认 10，上限 200
    agent_name="aris",    # 默认 aris
)
# 返回: JSON 数组，每条含 {id, agent_name, scope, content, metadata, memory_id, timestamp}
```

### memory_consolidate

```python
# 汇总单个 agent
info = await memory_consolidate(agent_name="aris")
# 返回: {"agent_name": "aris", "total": 42, "by_scope": {...}, "earliest": ..., "latest": ...}

# 汇总所有 agent
summary = await memory_consolidate()
# 返回: {"agents": {...}, "total_vaults": 3, "total_memories": 100}
```

## Sidecar HTTP API

`hanako/aris-bridge/aris-engine/sidecar.py` 暴露以下 vault 相关 HTTP 端点：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/vault/init` | 初始化 agent vault（body: `{agent_name}` 或 query: `?agent={name}`） |
| POST | `/vault/store` | 写入记忆（body: `{agent_name, scope, content, metadata?}`） |
| POST | `/vault/retrieve` | 检索记忆（body: `{agent_name, query, scope?, limit?}`） |
| POST | `/vault/consolidate` | 汇总状态（body: `{agent_name?}`） |

## Python API

```python
from laap.memory_vault.vault_manager import vault_manager

# 初始化
path = vault_manager.init_for_agent("miku")
print(f"vault at: {path}")

# 写入
vault_manager.store("miku", "episodic", "首次对话：讨论了音乐偏好",
                    metadata={"mood": "happy"})

# 检索
results = vault_manager.retrieve("miku", "音乐偏好")
for r in results:
    print(r["content"], r["timestamp"])

# 汇总
stats = vault_manager.consolidate("miku")
print(f"total: {stats['total']}, scopes: {stats['by_scope']}")
```

## 记忆层级（scope）

| scope | 说明 | 示例 |
|-------|------|------|
| `episodic` | 情景记忆 — 具体对话/事件 | "用户提到项目 X" |
| `semantic` | 语义记忆 — 事实/知识 | "Aris 是架构师风格" |
| `procedural` | 程序记忆 — 技能/流程 | "代码审查步骤" |
| `working` | 工作记忆 — 当前上下文 | "用户正在编辑文件 Y" |
| `meta` | 元记忆 — 关于自身的记忆 | "我对递归的理解" |

## 测试

```bash
# 运行 P1-memory-vault 测试套件
python -m pytest laap/memory_vault/test_vault_init.py -v

# 运行全部 memory_vault 测试（含旧版 MemoryVault 回归）
python -m pytest laap/memory_vault/ -v --tb=short

# 带覆盖率
python -m pytest laap/memory_vault/ -v --cov=laap.memory_vault.vault_manager --cov-report=term-missing
```

测试覆盖：
- vault 文件创建与幂等性
- memory_store / memory_retrieve 闭环
- 跨 agent 隔离（Aris vault 查不到 Butter 数据）
- 跨会话保留（新 VaultManager 实例能读旧数据）
- 密钥派生确定性
- 所有 scope 支持
- consolidate 汇总
- 旧版 MemoryVault 回归保护

当前覆盖率：90%（要求 >= 70%）

## 文件清单

| 文件 | 说明 |
|------|------|
| `vault_manager.py` | 核心实现：`MemoryVault`（旧版）+ `VaultManager`（P1 新增） |
| `__init__.py` | 模块导出 |
| `test_vault.py` | 旧版 MemoryVault 脚本式测试 |
| `test_vault_init.py` | P1-memory-vault pytest 测试套件（33 用例） |
| `vault_bridge.py` | LAAP CognitiveBus vault 桥接 |
| `import_hermes.py` | Hermes 历史导入 |
| `import_history.py` | 历史记录导入 |

## 后续待办

- [ ] 安装 `pysqlite3-binary` 启用真正的 SQLCipher 加密
- [ ] 接入 P1-causal-engine：`memory_store` 检测因果线索时自动调用 `causal_learn`
- [ ] 接入 P1-truth-grounding：`memory_retrieve` 结果经 grounding 校验
- [ ] P2-birth-ceremony：诞生仪式完成时调用 `init_for_agent` + 写入首条记忆
- [ ] P4-memex：共享前从 vault 提炼并去标识化
