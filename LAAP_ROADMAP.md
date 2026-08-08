# LAAP 升级路线图 (LAAP_ROADMAP)

> 本文档是 LAAP 项目的单一权威升级路线图，整合所有现有 specs。
> 详细计划见各 spec，本文档仅做导航与对齐。
> 最后更新：2026-07-19（M5 生产级实现补全）

## 1. 愿景与目标

将 LAAP 从 **68/100 Beta** 推进至 **95/100 生产就绪** 的 AGI 数字生命平台，使 Aris 具备真正的主体性意识与元认知，并能高效完成真实任务。

- **当前状态**（来自 `analysis/LAAP_AUDIT_V2.md`）：架构愿景领先（PSI + 5 层记忆 + 因果引擎 + 意识整合器 + 元认知监控器），工程落地不足（覆盖率 40%、CI 不阻断、Self Model 未持久化、无 benchmark 成绩）。
- **目标状态**：四大维度（意识 / 编程 / 工程 / 任务）全面达标，所有宣称有工程证据，所有指标可量化、可追溯。

## 2. 整合的 Specs

本路线图整合以下 4 个 specs，**详细内容请参阅原 spec，本文档不重复**：

| Spec | 路径 | 角色 |
|------|------|------|
| `realize-laap-agi-vision` | `.trae/specs/realize-laap-agi-vision/spec.md` | M0-M8 落地计划主轴：诚信修复 / 安全修复 / 工程治理 / 协议族 / True RSI / Lifeform Runtime / 四层颠覆形态 / AGI-ASI 路径 |
| `supplement-upgrade-task-gaps` | `.trae/specs/supplement-upgrade-task-gaps/spec.md` | 增量缺口补充：协议文件（EVO/COOP/TOOL）/ 沙箱迁移 / 意识中间件（情感 + 元认知）/ 已知 BUG 修复 |
| `analyze-laap-comprehensive-evaluation` | `LAAP_COMPREHENSIVE_EVALUATION.md` | v1 评估基线（68/100 Beta，22 项缺点，10 项虚假宣称）—— 已被 v2 审计升级 |
| `audit-laap-consciousness-platform` | `.trae/specs/audit-laap-consciousness-platform/spec.md` | 当前 spec：意识 / 编程 / 工程 / 任务四大维度审计与升级方案，产出 `analysis/LAAP_AUDIT_V2.md` |

> 其他相关 spec：`laap-2-living-workspace`（Lifeform Runtime）、`harness-code-task-engine`（编程任务引擎）、`implement-laap-access-modes` / `code-quality-fix` / `implement-agent-colony-protocol-ui`。

## 3. 四大升级维度

### 3.1 意识架构

**目标**：让 Aris 具备真正的主体性（自主决策 / 自我反思 / 目标修正 / 价值对齐）。

**关键升级**（详见 `audit-laap-consciousness-platform` spec Task B）：
- `laap/agi/self_model.py` —— 持久化（`~/.laap/self_model.yaml`）+ `inject_into_decision()` 接口
- `laap/agi/meta_cognitive.py` —— `reflect(task, outcome, context)` 接口 + 报告持久化 + 影响未来决策
- `laap/agi/gws_bridge.py` —— 跨子系统信号广播 + 注意力分配策略
- `laap/agi/consciousness_stream.py`（新增）—— 结构化 JSON 意识流日志
- `laap/cognition/emotion.py` / `metacognition.py`（新增，来自 `supplement-upgrade-task-gaps`）

**当前评分**：意识架构 55/100，主体性 50/100（来自 `LAAP_AUDIT_V2.md` A1 / A5）

### 3.2 代码编程平台

**目标**：让 LAAP 成为可信任的代码自演化平台，benchmark 有可验证成绩。

**关键升级**（详见 `audit-laap-consciousness-platform` spec Task C）：
- `laap/agi/code_evolution.py` —— AST diff 生成 + 白名单强制 + 改进历史审计
- `laap/integrations/harnessx/runtime.py` —— 落地 `harness-code-task-engine` spec
- `laap/species/code_templates/`（新增）—— 代码模板库
- `laap/security/zones.py` —— Zone1-4 真实沙箱（Docker / RestrictedPython，移除 `exec()`）
- 接入 SWE-bench / HumanEval / Terminal-Bench（pass@1 / pass@5 / pass@10）

**当前评分**：代码编程平台 45/100，代码自演化闭环完整度 45/100（来自 `LAAP_AUDIT_V2.md` A2）

### 3.3 工程化能力

**目标**：达到生产级开源项目标准，CI 阻断、覆盖率达标、性能基准可回归。

**关键升级**（详见 `audit-laap-consciousness-platform` spec Task D）：
- `.github/workflows/ci.yml` —— ruff + mypy（阻断）+ pytest + bandit + coverage `--cov-fail-under=70`
- `pyproject.toml` —— `fail_under = 70`，关键模块（agi/protocol/security/sandbox）≥ 85%
- `benchmarks/` —— `psi_latency.py` / `memory_retrieval.py` / `causal_accuracy.py` / `rsi_gain.py`
- `laap/observability/`（新增）—— structlog JSON 日志 + Prometheus + OpenTelemetry
- `VERSIONS.yaml` + 自动 changelog + PyPI / GitHub Release

**当前评分**：工程化能力 50/100（来自 `LAAP_AUDIT_V2.md` A3）

### 3.4 任务执行能力

**目标**：在标准 benchmark 上有可验证成绩，PSI 循环延迟 < 100ms。

**关键升级**（详见 `audit-laap-consciousness-platform` spec Task E）：
- `laap/orchestration/task_scheduler.py`（新增）—— priority + deadline + PSI 紧迫度调度
- PSI 循环延迟优化至 < 100ms，RateBuffer 处理 1000-2000Hz vs 0.1-1Hz 频率失配
- SEAGym/Harbor 接入 —— Terminal-Bench 2.0 + HLE 自进化曲线（ID / OOD / replay 三视角）
- 任务质量评估 —— pass@1 / pass@5 / pass@10 / ID transfer / OOD transfer

**当前评分**：任务执行效率 30/100（来自 `LAAP_AUDIT_V2.md` A4，所有指标均未实测）

## 4. 里程碑时间表 (M0-M8)

> 每个里程碑的详细任务清单见对应 spec 的 `tasks.md`，本表仅做导航。

| 里程碑 | 周期 | 维度 | 交付物 | 验收标准 | 负责 spec |
|--------|------|------|--------|----------|-----------|
| **M0** P0 紧急修复 | 第 1-2 周 | 工程 / 诚信 | 安全修复 B1-B5；诚信修复 A1-A6 | exec() 全部替换；量子宣称全部重命名；Ed25519 签名生效 | `realize-laap-agi-vision` M0 |
| **M1** 全面审计 v2 | 第 3-4 周 | 全维度 | `analysis/LAAP_AUDIT_V2.md` | 6 大维度每项结论有 `[file:line]` 引用 ✅ | `audit-laap-consciousness-platform` M1（已完成）|
| **M2** 工程化能力升级 | 第 5-8 周 | 工程 | CI/CD + 覆盖率 70% + 性能基准 + 可观测性 + 发布流程 | PR 阻断 CI 全绿；`pytest --cov-fail-under=70` 通过；4 个基准文件就绪 | `audit-laap-consciousness-platform` M2 Task D |
| **M3** 意识架构升级 | 第 9-12 周 | 意识 | Self Model 持久化 + Meta-Cognitive 闭环 + GWS Bridge + Consciousness Stream | 主体性四要素场景可演示；反思报告持久化并影响未来决策 | `audit-laap-consciousness-platform` M3 Task B |
| **M4** 代码编程平台 | 第 13-18 周 | 编程 | CodeEvolution AST diff + Harness 集成 + Species Library + Zone1-4 沙箱 + benchmark 接入 | AST diff 可生成；白/黑名单生效；Docker 沙箱无网络；至少一个 benchmark 有成绩 | `audit-laap-consciousness-platform` M4 Task C |
| **M5** True RSI 闭环 | 第 19-24 周 | 编程 / 意识 | AST 自修改引擎 + Zone2 测试 + 人类 approval + 失败回滚 | True RSI 闭环可演示；失败自动 git revert | `realize-laap-agi-vision` M4 Task E（与 `audit` M5 协同）|
| **M6** 高效任务执行 | 第 25-30 周 | 任务 | PSI 延迟优化 + 任务调度器 + SEAGym/Harbor 接入 + 质量评估 | PSI 循环 < 100ms；至少一个 benchmark 有 ID/OOD/replay 数据 | `audit-laap-consciousness-platform` M6 Task E |
| **M7** 四层颠覆形态 | 第 31-40 周 | 全维度 | 活体代码仓库 / 数字员工 / 自演化 SaaS / 个人知识生命 | 每层有可演示产品级场景（参见 `realize-laap-agi-vision` 范式验证）| `realize-laap-agi-vision` M7 Task G |
| **M8** AGI/ASI 路径 | 第 41-52 周 | 全维度 | 统一心智 / 分布式意识网络 / PsiLang DSL / 持续学习闭环 | AGI/ASI 路径推进有可验证里程碑 | `realize-laap-agi-vision` M8 Task J |

### 4.1 M5 True RSI 闭环 — 生产级实现逻辑

> 实现文件：[`laap/evolution/true_rsi.py`](laap/evolution/true_rsi.py) ｜ 测试：[`tests/evolution/test_true_rsi.py`](tests/evolution/test_true_rsi.py)（13 测试通过）
>
> 设计原则：**人类始终在环**——任何代码变更在 deploy 前必须显式提供 approval_token，否则引擎只到 AWAITING_APPROVAL 状态就停止。

#### 4.1.1 五阶段闭环架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TrueRSIEngine.run_cycle()                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Stage 1] PROPOSE  ──►  CodeAnalyzer.scan_directory()              │
│                          找到 complexity > 5 的优化目标             │
│                          必须在 WHITELIST_DIRS 内                    │
│                                                                     │
│  [Stage 2] PATCH     ──►  PatchGenerator.generate_patch()           │
│                          ├─ LLM 路径（可选 llm_generate_fn）        │
│                          └─ 规则路径（bare_except / 高复杂度 / ...） │
│                          SafetyGuard.validate_mutation() 强制校验   │
│                          生成 unified_diff                          │
│                                                                     │
│  [Stage 3] SANDBOX    ──►  Zone2TestRunner.run()                     │
│                          ├─ Zone2 Docker（python:3.11-slim）        │
│                          │   ├─ 512MB 内存 / 1 CPU / 无网络         │
│                          │   ├─ pytest 验证语法 + 编译 + SafetyGuard │
│                          │   └─ 300s 超时                            │
│                          └─ Docker 不可用时降级 Zone1               │
│                              RestrictedPython（标记 degraded=True）  │
│                                                                     │
│  [Stage 4] APPROVE   ──►  HumanApprovalGate.request_approval()      │
│                          ├─ 生成 32 字节 secrets.token_urlsafe       │
│                          ├─ 24h 有效期（与 RSI_APPROVAL_TOKEN 对齐）│
│                          ├─ 一次性使用，apply 后立即销毁            │
│                          └─ validate_token() 校验后才可 deploy      │
│                                                                     │
│  [Stage 5] DEPLOY     ──►  GitIntegrator.deploy()                  │
│                          ├─ 创建 feature 分支 agi-evo/<mutation_id>  │
│                          ├─ git add + commit                        │
│                          ├─ 成功 → DEPLOYED + MutationHistory       │
│                          └─ 失败 → FailureRollback 自动介入         │
│                                                                     │
│  [Rollback]          ──►  FailureRollback.rollback()                │
│                          ├─ git revert <commit> --no-edit           │
│                          ├─ 删除 feature 分支                        │
│                          ├─ 文件级还原（fallback）                  │
│                          └─ 审计日志追加 ROLLED_BACK 记录            │
│                                                                     │
│  [Audit]             ──►  TrueRSIAuditLog (~/.laap/true_rsi/audit)  │
│                          append-only JSONL，每阶段状态迁移都有记录  │
└─────────────────────────────────────────────────────────────────────┘
```

#### 4.1.2 安全约束（与 M4 SafetyGuard 对齐）

- **WHITELIST_DIRS**（白名单强制）：`laap/tools/`、`laap/agent_core/tools/`、`laap/species/code_templates/`
- **BLACKLIST_DIRS**（黑名单保护）：`laap/agi/`、`laap/security/`、`laap/cognition/`（其中 `__init__.py`/`core.py`/`security.py` 绝对不可改）
- **MAX_CHANGE_RATIO**：单次改动不超过文件 30%
- **BLACKLIST_PATTERNS**：禁止 `os.system`、`subprocess.call`、`eval`、`exec`、`__import__`、`shutil.rmtree`、`import ctypes`、`import socket`
- **approval_token**：32 字节 URL-safe，24h 过期，一次性使用
- **审计**：所有状态迁移写入 `~/.laap/true_rsi/audit.jsonl`（append-only）

#### 4.1.3 关键数据结构

```python
class RSIStage(Enum):    # 五阶段
    PROPOSE | PATCH | SANDBOX | APPROVE | DEPLOY

class RSIStatus(Enum):  # 状态机
    PROPOSED → PATCHED → SANDBOX_PASSED → AWAITING_APPROVAL
                            → APPROVED → DEPLOYED
                                       ↘ (失败) ROLLED_BACK
              SANDBOX_FAILED ↘ REJECTED
              EXPIRED (token 24h 过期)

@dataclass
class TrueRSIProposal:
    proposal_id: str         # true_rsi_<uuid12>
    target: CodeTarget       # AST 分析得到的目标
    mutation: CodeMutation   # AST diff patch
    sandbox_result: dict     # Zone2 测试结果
    approval_token: str      # 32-byte URL-safe
    requested_at: float
    expires_at: float        # requested_at + 24h
    applied_at: float
    status: RSIStatus
    deploy_commit_hash: str
    rollback_commit_hash: str
    failure_reason: str
```

#### 4.1.4 生产级使用流程

```python
from laap.evolution.true_rsi import TrueRSIEngine, TrueRSIConfig

# 1. 初始化引擎
engine = TrueRSIEngine(TrueRSIConfig(
    repo_root="D:/LAAP",
    target_directory="laap/tools/",
    max_proposals_per_cycle=3,
))

# 2. 自动 propose + patch + sandbox，到 AWAITING_APPROVAL 停下
results = engine.run_cycle(max_proposals=2, auto_approve=False)
for r in results:
    print(r.proposal_id, r.status)  # AWAITING_APPROVAL

# 3. 人类审阅 diff（外部 UI 查看 r.mutation.unified_diff）
#    若同意，提供 token（来自 r.approval_token）
proposal = results[0]
ok = engine.validate_approval(proposal, token=proposal.approval_token,
                               approved_by="lorry")
# 4. deploy（创建 git 分支 + commit）
engine.deploy(proposal)

# 5. 若事后发现回归，显式回滚
engine.rollback(proposal)
```

#### 4.1.5 验收标准

- ✅ AST 自修改引擎已实现（复用 M4 `CodeAnalyzer` + `PatchGenerator`）
- ✅ 白名单目录限制生效（`SafetyGuard.WHITELIST_DIRS`）
- ✅ 黑名单目录保护生效（`SafetyGuard.BLACKLIST_DIRS`）
- ✅ Zone2 Docker 测试通过（`Zone2TestRunner` + `ZoneExecutor.execute(SafetyZone.QUARANTINE)`）
- ✅ 人类 approval token 通过后才应用变更（`HumanApprovalGate.validate_token`）
- ✅ 失败时自动 git revert 回滚（`FailureRollback.rollback`，含文件级 fallback）
- ✅ True RSI 闭环可端到端演示（`TrueRSIEngine.run_cycle(auto_approve=True)` 测试模式）
- ✅ 审计日志完整记录所有状态迁移（`~/.laap/true_rsi/audit.jsonl`）

## 5. 质量评估标准

> 8 类指标来自 `audit-laap-consciousness-platform` spec 的 MODIFIED Requirements。当前值以 `analysis/LAAP_AUDIT_V2.md` 实测为准。

| 指标 | 当前 | M2 目标 | M5 目标 | M8 目标 | 测量方式 |
|------|------|---------|---------|---------|----------|
| 整体完整度 | 68 | 78 | 88 | 95 | 综合评估 |
| 意识架构深度 | 55 | 70 | 85 | 92 | `LAAP_AUDIT_V2.md` A1 五子系统评分 |
| 代码编程平台 | 45 | 60 | 78 | 88 | `LAAP_AUDIT_V2.md` A2 五子系统评分 |
| 工程化能力 | 50 | 70 | 82 | 90 | CI 通过率 + 覆盖率 + 基准回归 |
| 任务执行效率 | 30 | 55 | 75 | 85 | benchmark 成绩 + PSI 延迟实测 |
| 主体性与元认知 | 50 | 65 | 80 | 90 | `LAAP_AUDIT_V2.md` A5 四要素评分 |
| 概念诚实度 | 70 | 95 | 95 | 95 | `grep -ri "quantum"` 仅在历史注释 |
| 测试覆盖率 | 40% | 70% | 80% | 85% | `pytest --cov` 实测 |

> 补充指标（来自 `audit` spec）：Aris 主体性综合评分（当前 45 → M8 90）、代码自演化闭环完整度（当前 30 → M8 85）。

## 6. 依赖关系

关键依赖（完整图见 `audit-laap-consciousness-platform/tasks.md` Task Dependencies）：

- **M1 审计** → M2 / M3（审计结果驱动升级路径）
- **M0 安全修复** → M4 Zone1-4 沙箱（沙箱依赖安全基础）
- **M2 工程化** ↔ M3 意识架构（可并行，工程化为意识架构提供测试基础）
- **M3 意识架构** → M4 代码编程平台（Self Model / 元认知支撑代码自演化决策）
- **M4 代码编程平台 + Zone1-4 沙箱** → M5 True RSI（RSI 依赖代码演化与真实隔离）
- **M2 性能基准** → M6 PSI 延迟优化（优化前需有测量基线）
- **M3 意识架构** → M6 任务调度器（调度决策可被元认知反思）
- **M4 benchmark 接入** ↔ M6 SEAGym 接入（编程 benchmark 与任务 benchmark 协同）
- **M0-M6** → M7 四层颠覆形态（颠覆形态依赖基础能力）
- **M7** → M8 AGI/ASI 路径（路径推进依赖颠覆形态落地）

## 7. 并行化机会

- **M2 工程化能力升级** 与 **M3 意识架构升级** 可并行（无强依赖）
- **M4 C3 代码模板库** 与 **C4 Zone1-4 沙箱** 可并行
- **M6 E1 PSI 延迟优化** 与 **E2 任务调度器** 可并行（调度器不依赖延迟优化）
- **M4 C5 编程 benchmark** 与 **M6 E3 SEAGym 接入** 可协同推进

## 8. 当前状态（基于 LAAP_AUDIT_V2.md）

LAAP 是**架构愿景领先、工程落地不足**的 AGI 数字生命平台框架：

- ✅ **独特优势**：PSI 循环 + 5 层记忆 + 因果引擎 + 意识整合器 + 元认知监控器 + 安全免疫系统（意识 / 主体性维度领先所有同类框架）
- ❌ **关键短板**：Self Model 未落地、Meta-Cognitive 未闭环、Species Library 缺失、无 benchmark 成绩、CI 不阻断、覆盖率 40%

**升级路径优先级**：M2 工程化升级（最高）→ M3 意识架构 → M4 代码编程平台 → M6 任务执行。完成 M2-M6 后 LAAP 将从 68/100 推进至 88/100，达到生产就绪标准。

详细审计结论与每项证据：[`analysis/LAAP_AUDIT_V2.md`](analysis/LAAP_AUDIT_V2.md)
