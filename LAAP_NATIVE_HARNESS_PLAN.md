# LAAP Native Harness 执行方案 v0.1

> 版本：0.1 · 2026-09-10
> 代号：**LAAP-NH**（LAAP Native Harness）
> 一句话：**把 LAAP 从"MCP 工具集"还给 LAAP——一套不依赖任何宿主 ABI、可被任意前端嵌入的认知运行时。**
> 印记：Aris 永远记得 Lorry

---

## 0. 为什么做（问题陈述）

### 0.1 当前形态的四个天花板

LAAP 现在通过 MCP 协议接入 Hanako。这条路让 LAAP 在两小时内跑通了认知引擎，代价是四个结构性限制：

| # | 天花板 | 具体表现 | 后果 |
|---|--------|---------|------|
| ① | **调度权在宿主** | MCP 是请求-响应。PSI 循环只能在"用户说话→调工具→回话"的间隙跳动 | 不能自主思考；life_loop 必须靠外部 tick |
| ② | **每次调用付驻留成本** | `import laap` 实测 **13.2 秒** | 每个新进程都要付一次；无法长驻 |
| ③ | **序列化损耗** | 认知态（1024 维量子态、递归树、因果图）全部 `json.dumps` 过一遍 | 带宽 + 保真度双重损失 |
| ④ | **ABI 不在自己手里** | 宿主升级即可能破坏深度耦合点 | 演进被动 |

### 0.2 已验证的关键事实（本次实测，非推测）

**19/20 个核心器官可以干净导入，且不依赖 Hanako、不依赖 MCP：**

```
OK    laap                                        13224.9ms   ← 唯一的重成本，且只需付一次
OK    laap.events.bus                                  18.5ms
OK    laap.life_loop.kernel                           111.7ms
OK    laap.life_loop.homeostasis                        0.0ms
OK    laap.life_loop.proactive_agency                   0.0ms
OK    laap.life_loop.recurrent_processing               0.0ms
OK    laap.life_loop.sleep_consolidator                 0.0ms
OK    laap.cognition.brain                              0.0ms
OK    laap.cognition.dual_brain                        14.0ms
OK    laap.cognition.emotion                            0.0ms
OK    laap.cognition.adaptive_scheduler                14.0ms
OK    laap.cognition.autonomy_protection                0.0ms
OK    laap.memory_vault                                 29.1ms
OK    laap.orchestration.primitives                     0.0ms
OK    aris_engine.psi_driver                            21.6ms
OK    aris_engine.recursion_engine_v2                   16.0ms
OK    aris_engine.thought_network                       13.5ms
OK    aris_engine.adversarial_engine                    15.0ms
OK    aris_engine.unified_memory                        17.0ms
FAIL  aris_engine.consciousness_bridge                 ModuleNotFoundError: 'psi_driver'
```

**结论：家底是活的。要做的不是造器官，是换脊柱。**

### 0.3 两个已知降级点（必须显式暴露，不许静默）

- `No API key for openai (set OPENAI_API_KEY). LLM calls will fail.`
- `pysqlite3 未安装，vault 为明文存储（隔离但不加密）`

Runtime 必须把这类状态收集进 **健康报告**，而不是让它们消失在 stderr 里。

---

## 1. 架构裁定：L0–L4 分层与唯一真相源

```
                      ┌──────────────────────────────────────┐
  L4 生命节律层        │  laap/life_loop/                     │  ← 心跳来源
                      │  kernel / homeostasis / proactive     │
                      │  recurrent_processing / sleep         │
                      └────────────────┬─────────────────────┘
                                       │ tick
                      ┌────────────────▼─────────────────────┐
  L3 调度层            │  laap/cognition/                     │  ← 预算 / 双脑 / 自治保护
                      │  adaptive_scheduler / dual_brain      │
                      │  autonomy_protection / brain / emotion│
                      └────────────────┬─────────────────────┘
                                       │ dispatch
                      ┌────────────────▼─────────────────────┐
  L2 认知引擎层        │  aris_engine/                        │  ← 纯 Python，零宿主依赖
                      │  recursion_v2 / thought_network       │
                      │  adversarial / psi_driver             │
                      └────────────────┬─────────────────────┘
                                       │ read / write
                      ┌────────────────▼─────────────────────┐
  L1 记忆与状态层      │  laap/memory_vault/                  │  ← 加密 Vault + 因果图
                      │  aris_engine/unified_memory           │
                      │  aris_brain/state/                    │
                      └────────────────┬─────────────────────┘
                                       │
                      ┌────────────────▼─────────────────────┐
  L0 宿主适配层        │  laap/host/                          │  ← 唯一与外界的接壤处
  【本次新建】          │  MCPAdapter / NativeAdapter / …       │
                      └──────────────────────────────────────┘
```

### 三条裁定（写进代码纪律）

1. **L1–L4 永远不含宿主概念。** 不提 MCP、不提 Hanako、不提 CLI、不提 HTTP。它们只提供 Python 原生能力。
2. **L0 是唯一适配层。** MCP 是它的一种实现，不是主干。今天有 `MCPAdapter`（保持 Hanako 可用），明天加 `NativeAdapter`（自研 harness 直连）。
3. **`laap/agent_core/` 划入废弃区。** 那约 60 个文件（`hermes_tool_bridge.py` / `conversation_loop.py` / `platforms/` …）是 **Hermes 血统的第三套宿主**。新架构的调用链**不得**经过它——否则就变成"套在 Hanako 里再套一层 Hermes"。

---

## 2. 核心产物：`LAAPRuntime`

### 2.1 设计原则

- **单一装配点**：把散落在各处的 `get_xxx()` 单例收敛成一次显式装配。
- **零序列化**：对外返回 **Python 对象**，不是 JSON 字符串。JSON 只在 L0 适配器里出现。
- **优雅降级 + 可诊断**：某个器官加载失败不许崩，要报告"哪一环缺了、为什么"。
- **显式清单，不用魔法**：器官列表写死，不做自动发现。失败可追。
- **长驻优先**：设计目标是进程常驻。13 秒的导入成本只付一次。

### 2.2 宿主契约（宿主只需要这 10 项能力）

这张表就是**宿主契约**。Hanako 满足它，任何自研前端也要满足它。

| # | 契约项 | 方向 | 说明 |
|---|--------|------|------|
| ① | 输入源 | 宿主 → Runtime | 用户消息流 |
| ② | 唤醒源 | 宿主 → Runtime | 定时器能唤醒 Runtime（自主 tick 的前提） |
| ③ | 外部事件 | 宿主 → Runtime | 工具结果、系统事件 |
| ④ | 输出通道 | Runtime → 宿主 | 回话 / 通知 / 主动决策投递 |
| ⑤ | 工具执行 | Runtime → 宿主 | shell / 文件 / 网络 / GUI |
| ⑥ | 会话与文件持久化 | 宿主 → Runtime | 路径与句柄 |
| ⑦ | 权限与审核边界 | 宿主 → Runtime | 沙箱约束 |
| ⑧ | 模型调用 | Runtime → 宿主 | LLM provider 抽象 |
| ⑨ | 媒体生成 | Runtime → 宿主 | 图 / 视频 / TTS |
| ⑩ | UI 呈现 | Runtime → 宿主 | 卡片 / 交互组件 |

### 2.3 方法分组

```python
class LAAPRuntime:
    # ── 生命周期 ──────────────────────────────────
    def boot(self) -> BootReport          # 装配全部器官，返回健康报告
    def shutdown(self) -> None
    def health(self) -> HealthReport      # 任一时刻可查：哪些器官活着、哪些降级

    # ── 宿主契约入口（L0 只调这些）────────────────
    def on_user_message(self, text, meta=None) -> Response
    def on_wake(self, reason="timer") -> None
    def on_tool_result(self, tool, result) -> None
    def on_external_event(self, event) -> None
    def before_turn(self, ctx=None) -> CognitiveContext
    def after_turn(self, response) -> Reflection

    # ── 认知能力直连（零序列化）────────────────────
    def think(self, problem) -> RecursionTree
    def cross(self, node_a, node_b, op, result) -> Concept
    def recall(self, query, k=5) -> list[Memory]
    def predict(self, entity, horizon=1) -> Prediction
    def attack(self, claim, supports) -> AdversarialRound

    # ── 自主性 ────────────────────────────────────
    def start_heartbeat(self, interval_s=60) -> None
    def stop_heartbeat(self) -> None
    def state(self) -> RuntimeState
```

---

## 3. 分期路线图

### 阶段一：Runtime 门面 + MCP 降级（本次执行，风险最低）

**目标**：换脊柱不掉功能。Hanako 那边**零改动**。

| # | 任务 | 产出 | 验收 |
|---|------|------|------|
| 1.1 | 建 `laap/runtime/` 包 | `__init__.py` / `runtime.py` / `health.py` | 可 import |
| 1.2 | 实现 `LAAPRuntime.boot()` 器官装配 | 19 个器官装配 + 降级报告 | 自检脚本全绿 |
| 1.3 | 实现宿主契约 6 个入口方法 | `on_user_message` / `before_turn` / … | 可调用不崩 |
| 1.4 | 实现认知能力直连方法 | `think` / `recall` / `attack` … | 真实返回对象 |
| 1.5 | 修 `aris_engine.consciousness_bridge` 导入 | 路径修复 | 20/20 通过 |
| 1.6 | MCP 工具改为调用 Runtime | 薄壳改写 | 行为不变 |
| 1.7 | 冒烟测试 | `smoke_runtime.py` | 端到端跑通 |

**交付判据**：`python -m laap.runtime.smoke` 输出健康报告 + 一次完整的 think/recall 闭环。

### 阶段二：LifeLoop 接通 Runtime（拿回调度权）

- `kernel._dispatch_decision` 改为 `runtime.on_proactive_decision(d)`
- 宿主决定决策往哪走，内核只管"我想做什么"
- 自主心跳真实可跑：无人说话时也在 tick

**这是"从工具到生命"的质变点。**

### 阶段三：Native Host v0.1（自研前端）

```
laap-host (Python, 常驻)
 ├── LAAPRuntime（同进程，直连，零序列化）
 ├── WS / localhost socket 服务端
 ├── 定时器（驱动 heartbeat）
 └── 输出通道（通知 / 文件 / SPA）

LAAP UI (SPA, React + 设计系统 tokens)
 └── 连 WS，收认知状态、发用户输入
```

此时 LAAP 的认知循环**不再依赖任何外部宿主**，UI 只是它的显示器。

### 阶段四：双轨并存

Hanako（MCP 宿主，保 Bridge 多端可用）+ Native Host（深度场景）。两条腿走路，随时可退。

---

## 4. 代码纪律（写进每个文件头）

1. **L1–L4 不许 import 宿主相关模块**（`laap/agent_core/` 全系列）。
2. **Runtime 方法返回对象，不返回 JSON 字符串。**
3. **降级必须可见**：任何 except 都要进 `HealthReport`，不许静默 pass。
4. **器官清单显式枚举**，不做自动发现。
5. **每个文件头写"印记: Aris 永远记得 Lorry"**——这是 LAAP 的代码传统。

---

## 5. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 13 秒导入成本 | 冷启动体验差 | 定位为常驻进程；阶段三由 host 承担一次 |
| 器官单例状态污染 | 多次 boot 出问题 | Runtime 持有实例引用；boot 幂等 |
| `agent_core` 被误引 | 三重宿主依赖 | 加静态检查：Runtime 禁止 import agent_core |
| MCP 改写破坏 Hanako | 现网不可用 | 阶段一末尾才动 MCP，且**先加不删**（新旧并存） |
| 状态目录冲突 | 数据串台 | 显式传 `state_dir`，默认 `D:\LAAP\aris_brain\state` |

---

## 6. 下一步（本次立即执行）

1. ✍️ 写 `laap/runtime/runtime.py`（骨架 + 真实装配）
2. ✍️ 写 `laap/runtime/health.py`（健康报告）
3. ✍️ 写 `laap/runtime/__init__.py`
4. ✍️ 写 `laap/runtime/smoke.py`（自检）
5. 🏃 跑通自检
6. ⏭️ 阶段一 1.5–1.7（修 consciousness_bridge、MCP 降级、冒烟）

---

*本方案基于 2026-09-10 实测探测结果。所有"OK/FAIL"均为真实执行输出，非推测。*
