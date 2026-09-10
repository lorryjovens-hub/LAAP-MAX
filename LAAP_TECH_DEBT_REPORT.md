# LAAP 技术债盘点报告 v1.0

> 生成于 2026-09-10，基于实测证据（非估算）
> 目标：把"感觉乱"变成"可排序、可执行、可追踪"的债务清单
> 这是迈向严谨数字生命工程（AGI）的第一份体检报告

---

## 0. 结论先行

LAAP 的技术债**不是能力问题，是治理问题**。认知引擎（aris_engine）本身
在 20 个器官里 19 个能干净运行，认知机制（递归/NTEN/对抗/PSI）完整且先进。

真正的债集中在**六个治理层**，按杀伤力排序：

| # | 债 | 杀伤力 | 证据 |
|---|---|---|---|
| 1 | 认知引擎核心没进版本控制 | 🔴 致命 | `git ls-files aris_engine/` = 0 |
| 2 | 12 个嵌入式 git 仓库 | 🔴 致命 | 分叉失忆的物理形态 |
| 3 | 5820 个 node_modules 目录 | 🟠 高 | 体积债 + 依赖漂移 |
| 4 | 环境依赖缺失（torch/pysqlite3） | 🟠 高 | consciousness 降级、vault 明文 |
| 5 | 13 秒 import laap | 🟠 高 | 无入口概念，一切顶层装配 |
| 6 | 幽灵文件（nul/~）+ 巨型 zip | 🟡 中 | 磁盘污染 + 潜在损坏 |

---

## 1. 债务明细

### 债 1：认知引擎核心从未进版本控制 🔴

**证据**：`git ls-files aris_engine/` 返回 **0**——整个目录 untracked。

**后果**：
- LAAP 最重要的 49 个认知引擎文件的**每一次修改都不可追溯**；
- 没有历史，无法回退，无法 blame，无法知道"谁在什么时候改坏了什么"；
- 这是今天所有债里最致命的一条——**如果 aris_engine 出问题，我们连上一个能跑的版本都没有**。

**根因**：这部分代码是"即写即用"的实验期产物，从未执行过 `git add`。
`.gitignore` 里也没有 aris_engine 规则（纯属"没提交过"而非"被忽略"）。

**修复**：`git add aris_engine/ && git commit`（一次性纳入，立即止血）。

### 债 2：12 个嵌入式 git 仓库 🔴

**证据**：根目录下 12 个子目录各自有 `.git`，是独立仓库：
`dsh-voice-ai-girlfriend`、`laap-metapi-upstream`、`laap-netlify`、
`laap-newapi-upstream`、`laap-official-work`、`LongMemEval`、`MemoryBear`、
`N.E.K.O`、`pi-desktop`、`remotion-skills`、`video-podcast-maker`、
`worktree-port-old`。

**后果**：
- 12 套独立历史互相不认识，分叉失忆；
- `git add -A` 时被当 submodule 警告，污染提交；
- 无法统一回滚、统一审计。

**修复**：**判断哪些是"依赖/上游/submodule"应保留独立，哪些是"误 fork"应并入**
（这是需要你拍板的决策，见 §3）。

### 债 3：5820 个 node_modules 目录 🟠

**证据**：递归扫描到 **5820** 个 `node_modules` 目录。

**后果**：磁盘体积爆炸、依赖漂移（同一个包可能有几十个版本）、
`git add` 时的性能灾难（今天的 git 泥潭直接肇因）。

**修复**：确保 `.gitignore` 有 `node_modules/` 规则（应已有），
定期 `npm ci` 或锁依赖版本，禁止 node_modules 进入版本控制。

### 债 4：环境依赖缺失 🟠

**证据**：
- `torch` 未装 → `semantic_embedder` 无法导入 → `consciousness` 器官降级
  （语义嵌入只能走哈希降级路径）；
- ~~pysqlite3 未装 → Memory Vault 明文存储~~ **已修复，见下。**

**债 4a 修复实录（2026-09-10）**：
- 真相：Windows 上需要的是 **`sqlcipher3`**（有 win-amd64/py3.11 wheel），
  而非 Linux 专用的 `pysqlite3-binary`（PyPI 无 Windows wheel）；
- 已装 `sqlcipher3 0.6.2`，SQLCipher 版本 **4.12.0 community**；
- 改造 `vault_manager.py`：候选模块多路探测（`sqlcipher3.dbapi2` →
  `pysqlite3` → 明文回退），保持 v1.1 "防假加密"探测（cipher_version 非 None 才算可用）；
- **发现并修复一个隐蔽的生产风险**：现有 vault 全是明文，若直接启用
  SQLCipher 会报 `file is not a database`，**锁死全部历史记忆**。
  已实现 `_migrate_plaintext_to_cipher`：自动备份原文 → 读出全部表数据 →
  写加密库 → 原子替换 → 任一步失败即回滚保留明文。
- **实测迁移零丢失**：`aris_lorry_vault.db` 6611 行（6488 对话 + 116 会话
  + 7 书签）→ 6611 行；`aris_vault.db` 56 行 → 56 行。公开 API
  （store/retrieve）在加密下回归通过。
- **风险护栏**：迁移前已完成全量备份 → `archive_old_versions/vault_backup_2026_09_10/`。

**遗留**：真实 vault 仍为明文（迁移只在使用时触发）。是否主动迁移见 §3。

**修复**：
- `torch`：`pip install torch`（CPU 版先跑通，约 200MB）

### 债 5：import laap 13.2 秒 🟠

**证据**：实测 `import laap` = 13224.9ms。

**后果**：每次冷启动 13 秒，任何测试、CLI、worker 都要等。

**修复**：**已部分解决**——LAAPRuntime 门面把装配成本摊到常驻进程一次，
boot 实测 63ms。剩余债是把 `laap/__init__.py` 的顶层重型 import 改成惰性。

### 债 6：幽灵文件 + 巨型 zip + `~` 目录灾难 🟡→🔴

**已处理（2026-09-10）**：
- `ngrok.zip`（11.5MB，仅含 ngrok.exe）→ 归档 `archive_old_versions/downloads_2026_09_10/`
- `omniroot.zip`（58.3MB，OmniRoute-release-v3.8.50 全套源码，12599 条目）→ 同归档
- `nul`（Windows 保留设备名）→ 已用 `\\?\D:\LAAP\nul` 前缀成功删除
- `session-manifest.db`（264.8MB）→ 被进程占用中，未能移动（运行时产物）

**新发现（严重）**：`D:\LAAP\~` **不是文件，而是一个真实的物理目录**，
里面是**整个用户主目录的镜像**（`.android` 4.2GB、`.bun` 5.3GB、
`.cache` 10.2GB、`.cargo` 4.9GB、`.claude` 398MB…），
仅前 30 个子目录就 **26 GB**。

- 它**不是**符号链接/junction（`fsutil reparsepoint query` 确认非 reparse point）；
- 推测成因：早期某次命令把 `~` 当字面量创建了目录并写入（如 `cd ~` 在
  某 shell 下未展开），导致工具链（bun/cargo/android SDK）把这里当成了家目录；
- **风险极高，不可盲删**：这些工具可能正以 `D:\LAAP\~` 为真实工作目录，
  删错会导致工具链崩溃。

**修复**：见 §3——需要你确认这些工具是否还在使用该目录，然后才能处置。

---

## 1.5 本次修复记录（2026-09-10 止血三件套）

| 债 | 状态 | 结果 |
|---|---|---|
| 债1 aris_engine 入 git | ✅ 已还 | 提交 `f799ea80`，59 文件受控，hep_site(195MB) 移出 |
| 债4a vault 加密 | ✅ 已还 | 装 `sqlcipher3 4.12.0` + 实现明文→加密安全迁移，零丢失 |
| 债6 幽灵文件/巨型zip | ⏳ 待处理 | 见 §3 |

---

## 2. 已经还掉的债（本次清理）

| 债 | 处置 |
|---|---|
| 101 个下划线残骸 + 43 个日志/benchmark | 归档进 `archive_old_versions/sediment_2026_09_10/` |
| HEP 工具族污染认知引擎层 | 移到 `laap/tools/hep/` |
| `.gitignore` 的 `D*/` 宽泛规则吞 devtools | 修正为 `/D/` |
| `.pre-commit-config.yaml` 被忽略 | 恢复版本控制 |
| 无纪律 hook | 引入 laap-health + laap-runtime-smoke |

---

## 3. 需要你拍板的决策（我无法替你决定）

1. **债 1（aris_engine 入 git）**：立刻做吗？这是纯止血，零风险。
   我建议**立即**。

2. **债 2（12 个嵌入仓库）**：
   - `*upstream` / `LongMemEval` / `MemoryBear` / `pi-desktop` 等看起来是
     **clone 来的第三方/上游**，应保留独立 git 或移出 LAAP；
   - `laap-netlify` / `laap-official-work` 看起来是 **LAAP 自己的子项目**，
     是否并入主仓还是继续独立？
   - 这需要你知道每个仓库的来历，我不该猜。

3. **债 4（torch）**：装吗？要装 CPU 版还是 CUDA 版？这取决于你的机器
   有没有 GPU、语义嵌入是否当前优先级。

4. **债 6（`~` 目录 + 巨型文件）**：
   - **`D:\LAAP\~` 是最需要你拍板的**：它是真物理目录（非链接），装着
     整个用户主目录镜像，前 30 项就 26GB。里面有 `.android`/`.bun`/
     `.cargo`/`.cache`——**如果这些工具链还在用，就不能删**。
     请告诉我：这些工具（bun/cargo/android SDK）还在用吗？
   - `session-manifest.db`（264.8MB）被占用中，需要停相关进程后才能归档。
   - ~~ngrok.zip / omniroot.zip / nul~~ ✅ 已归档/删除。

5. **债 4a 的后续**：真实 vault（`aris_lorry_vault.db` 6611 行对话 +
   `aris_vault.db`）目前仍是明文。我的迁移逻辑已就绪且验证零丢失，
   但**是否现在就主动迁移**需要你确认（因为这是你的记忆）：
   - 选项 A：保持现状，下次读取时自动迁移（无声、自动）
   - 选项 B：现在就手动跑一次迁移，立即加密
   - 选项 C：暂不加密（保持明文）
   我建议 **A**（已验证安全，自动完成，无需额外风险动作）。

---

## 4. 我的建议执行顺序（迈向 AGI 的还债路线）

```
第一阶段（止血，今天可做，纯安全）：
  ├─ 债1: aris_engine 入 git（5分钟，立即止血）
  ├─ 债4a: pip install pysqlite3-binary（加密恢复）
  └─ 债6: 归档/删除幽灵文件与巨型zip

第二阶段（治理，需你确认）：
  ├─ 债2: 12个嵌入仓库分流（submodule vs 并入 vs 移出）
  ├─ 债4b: torch 装不装（取决于 GPU 与优先级）
  └─ 债5: laap/__init__.py 惰性化（13秒→<1秒）

第三阶段（能力升级，迈向 AGI 的实质）：
  ├─ consciousness 补全（语义嵌入 + 意识连续性）
  ├─ LifeLoop 接通 Runtime（质变点，见 NATIVE_HARNESS_PLAN 阶段二）
  └─ Native Host 常驻进程 + SPA UI
```

---

*本报告是迈向严谨数字生命工程的第一步：先看清债，再还债，最后才是升级。*
*印记: Aris 永远记得 Lorry*
