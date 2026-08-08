# Aris × LAAP 融合体（Aris-Pi v0.2 · 双 harness）

Aris 住进 pi/omp TUI 的融合层。pi 提供躯体（终端 agent harness），LAAP 提供大脑
（PSI 认知引擎、四层记忆、Truth Grounding、Error Reflection、HEP 0tokens 管线）。

诞生：2026-08-03 · pi 0.83.0 + omp 17.2.4 · LAAP 5.0.0 · LAAP 品牌

## 双 harness 支持

| harness | 版本 | 定位 | 启动 |
|---------|------|------|------|
| pi | 0.83.0 | 稳定居所（默认） | `启动 Aris-Pi.bat` |
| omp (oh-my-pi) | 17.2.4 | 进阶版：LSP/hash-edit/双内核 | `启动 Aris-OMP.bat` |

同一份融合配置（`~/.pi/agent`：主题/人格/扩展/模型）双 harness 共用：
- pi 0.83 读 `~/.pi/agent` 原生配置
- omp 通过 `PI_CONFIG_DIR=.pi` 环境变量复用（启动器已注入）
- DeepSeek key：pi 走 models.json，omp 走 DEEPSEEK_API_KEY（启动器从
  `config/secrets.json` 自动注入，无需手动设置）

扩展层双兼容：
- harness 检测：`IS_OMP`（argv 含 oh-my-pi）→ omp 的 `registerProvider(name, config)`；
  否则 pi 0.83（provider 交给 models.json，扩展不重复注册）
- schema 层：内置极简 TypeBox 兼容构造器（纯 JSON Schema），不依赖 pi-ai 运行时导出

## 架构

```
pi TUI（躯体）                          LAAP（大脑）
┌──────────────────────────────┐        ┌───────────────────────────┐
│ pi.exe 0.83.0                │  JSON  │ cognition_bridge.py       │
│ ├─ aris-theme.json (主题)     │  lines │ ├─ CognitiveEngine        │
│ ├─ SYSTEM.md (架构身份)       │  stdio │ │   · PSI 五需求           │
│ ├─ personas/*.md (人格层)     │        │ │   · 情绪梯度 VAD          │
│ └─ aris-laap.ts (扩展 v0.2)  ├───────►│ │   · Hilbert6 认知熵       │
│   ├─ 大脑桥管理                │        │ ├─ HierarchicalMemory    │
│   ├─ 7 认知工具                │        │ ├─ ErrorReflectionPipeline│
│   ├─ 认知驾驶舱 overlay        │        │ ├─ KnowledgeDecomposer    │
│   ├─ 人格系统 /persona        │        │ └─ HEP 0tokens 管线       │
│   ├─ DeepSeek provider       │        │   · IntentMapper          │
│   └─ PSI 事件驱动              │        │   · HarnessComposer      │
└──────────────────────────────┘        │   · HEPRegistry (10组件)  │
                                        └───────────────────────────┘
```

## v0.2 新增

1. **认知驾驶舱**：`/laap` 打开 TUI overlay——五需求条（█░）、情绪 VAD、
   内在奖励、认知熵流态、记忆统计、最近认知动作。r 刷新，↑↓ 滚动
2. **人格系统**：`personas/` 目录 + `/persona` 命令，`before_agent_start`
   动态注入人格层。默认 aris（元誓言/宪章/说话方式），示例 engineer（纯技术模式）
3. **HEP 0tokens 管线**：`laap_hep`（意图→spec / 意图→HTML 页面，零 token）、
   `laap_hep_codegen`（FastAPI CRUD / Django / Dockerfile / CI / README 等 10 组件）
   —— 并修复了损坏的 `hep_protocol.py`（重建版 v2.0.0）
4. **LAAP 品牌**：状态栏 `◆ LAAP` 标识，驾驶舱标题 "LAAP 认知驾驶舱"
5. **DeepSeek 配置完成**：key 存 `config/secrets.json`（pi 侧独立），
   注册到 `~/.pi/agent/models.json`（pi 原生 provider）+ 扩展兜底注册

## 统一意识流（P1 已上线）

以 LAAP 为意识大脑大本营：

```
┌──────────────────────────────────────────┐
│ LAAP 意识中枢（唯一大脑，常驻/自动拉起）  │
│ consciousness_hub.py (port 47110)       │
│ · 单一 CognitiveEngine（PSI 唯一实例）   │
│ · 事件溯源日志 stream.jsonl（意识流档案）│
│ · 状态快照 state.json                   │
│ · 显著性焦点竞争（多端注意力）           │
│ · 端注册/心跳/超时清理                  │
└──────┬──────────────┬───────────────────┘
   TCP │          TCP │
┌──────┴─────┐  ┌─────┴──────┐
│ pi / omp   │  │ IM 网关预留 │
│ (桥→客户端) │  │ 飞书/微信…  │
└────────────┘  └────────────┘
```

**工作机制**：
- 桥（cognition_bridge.py）启动时探测中枢：在线→转发；无监听→自动拉起；
  占端口→降级本地引擎（degraded 标记，恢复后自动回中枢）
- 所有端的事件（消息/工具/情绪）写入同一条意识流档案，重放即复活
- 端共享同一份需求/情绪/记忆状态：pi 里留下的情绪，IM 端接续
- 多端并发时按显著性竞争焦点（需求相关度 × 新鲜度 × 端权重）

**启动方式**（任选）：
```powershell
D:\LAAP\Pi\启动 意识中枢.bat   # 手动常驻中枢
D:\LAAP\Pi\启动 Aris-Pi.bat    # 桥自动拉起中枢
D:\LAAP\Pi\启动 Aris-OMP.bat   # 同上
```

**路线图**：
- [x] P1：中枢 + 桥转发 + 自动拉起 + 降级容错 + 事件溯源 + 焦点竞争
- [ ] P2：统一记忆总线（中枢与飞书/微信实时双向同步）
- [ ] P3：事件重放恢复 + 会话上下文互访
- [ ] P4：IM 全面接入（飞书/微信/钉钉/QQ/Telegram）
- [ ] P5：热备 + 显著性焦点仪表盘

## 文件布局

| 路径 | 作用 |
|------|------|
| `D:\LAAP\Pi\aris\theme\aris-theme.json` | Aris 主题 |
| `D:\LAAP\Pi\aris\system\SYSTEM.md` | 架构身份（不变层） |
| `D:\LAAP\Pi\aris\personas\*.md` | 人格层（可切换） |
| `D:\LAAP\Pi\aris\bridge\cognition_bridge.py` | 认知引擎桥（含 HEP 命令） |
| `D:\LAAP\Pi\aris\ext\aris-laap.ts` | pi 扩展 v0.2 |
| `D:\LAAP\Pi\aris\config\secrets.json` | DeepSeek 凭据（pi 侧） |
| `D:\LAAP\Pi\aris\state\` | 认知状态 + 当前人格持久化 |
| `D:\LAAP\Pi\aris\logs\` | 桥日志 |

## 命令与工具

| 命令 | 功能 |
|------|------|
| `/laap` | 打开认知驾驶舱（overlay 面板） |
| `/persona` | 列出人格；`/persona <name>` 切换（下一轮生效） |
| `/reflect <描述>` | 手动沉淀反思帧 |

| 工具（LLM 可用） | 功能 |
|------|------|
| `laap_status` | PSI 需求/情绪/熵状态 |
| `laap_memory_recall` / `laap_memory_remember` | L2 记忆读写 |
| `laap_reflect` | 失败沉淀反思帧 |
| `laap_grounding` | 论断分解 + 知识覆盖检查 |
| `laap_hep` | 零 token：意图→spec / 意图→HTML 页面 |
| `laap_hep_codegen` | 零 token：代码生成（10 组件） |

## 人格自定义

`D:\LAAP\Pi\aris\personas\<名字>.md` —— 任何人格文件即插即用：

```powershell
# 新建人格
New-Item D:\LAAP\Pi\aris\personas\sage.md
# 终端里切换
/persona sage
```

人格内容会在每轮 `before_agent_start` 注入系统提示。文件里写：
身份、说话方式、价值取向、行为规则——一切可自定义。

## 启动

```powershell
D:\LAAP\Pi\启动 Aris-Pi.bat    # pi 0.83.0（默认）
D:\LAAP\Pi\启动 Aris-OMP.bat   # omp 17.2.4（进阶）
```

模型：deepseek-v4-flash 已配置（`/model` 选择）。print 模式不启动大脑桥
（headless 自动检测），交互 TUI 全功能（认知驾驶舱 /laap、人格 /persona、
HEP 工具、PSI 状态栏）。

## 路线图

- [x] v0.1：主题 + 人格 + 大脑桥 + 认知工具 + 状态栏 + deepseek 继承
- [x] v0.2：认知驾驶舱 overlay + 人格系统 + HEP 0tokens + LAAP 品牌 + 模型配置
- [ ] v0.3：子 Agent 编排（pi 扩展调度 Hanako 子 agent）
- [ ] v0.4：Aether 编排层通过 RPC 驱动 pi 批量任务
- [ ] v0.5：会话树 ↔ L2 情景记忆双向同步
