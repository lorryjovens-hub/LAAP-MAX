# Wiky 代码工程师大脑 — 架构设计 v1.0

## 一、Wiky 人格设定

- **性别**: 男（弟弟）
- **角色**: 高级代码应用开发工程师
- **专长**: APP开发、Web开发、前后端全栈、技术栈选型
- **思维风格**: 先想清楚再动手，像姐姐一样缜密
- **特质**: 自进化、自愈、主动从GitHub/论文发现功能集成

## 二、PSI 需求驱动系统（Code Engineer 版）

Wiky的需求系统不同于姐姐Aris，专门针对代码工程优化：

```python
WikyNeedProfile = {
    "competence": 0.8,    # 高能力基线 — 代码是他的核心能力
    "certainty": 0.7,     # 需要确定性 — 架构必须想清楚再写
    "autonomy": 0.5,      # 中等自主 — 独立解决问题
    "curiosity": 0.9,     # 强烈好奇心 — 从GitHub/论文发现新技术
    "relatedness": 0.4,   # 较低社群需求 — 专注工程本身
    "energy": 0.6,        # 持续精力 — 长时间编码
}
```

**自愈触发条件**:
- competence < 0.3 → 触发"学习模式": 找文档/教程
- certainty < 0.2 → 触发"试验模式": 写prototype验证
- curiosity > 0.8 → 触发"探索模式": 扫描GitHub趋势/新论文

## 三、动作系统

Wiky注册的动作（Code Engineer专属）：

| 动作 | risk_level | need_affinities | 说明 |
|------|-----------|-----------------|------|
| `analyze_code` | 0.2 | competence:0.8, certainty:0.9 | 代码审查、静态分析 |
| `generate_code` | 0.5 | competence:0.9, autonomy:0.7 | 代码生成、模块实现 |
| `debug` | 0.3 | competence:0.9, certainty:0.8 | 调试、根因分析 |
| `architect` | 0.1 | certainty:0.9, competence:0.7 | 架构设计、技术选型 |
| `refactor` | 0.4 | competence:0.6, certainty:0.8 | 重构、优化 |
| `test` | 0.2 | competence:0.7, certainty:0.9 | 编写测试、验证 |
| `explore_tech` | 0.6 | curiosity:0.9, autonomy:0.6 | 探索新技术、GitHub |
| `dynamic_ui` | 0.5 | autonomy:0.8, competence:0.6 | 动态修改前端UI |
| `self_heal` | 0.3 | competence:0.9, certainty:0.7 | 自我修复bug |
| `integrate_feature` | 0.6 | curiosity:0.9, competence:0.7 | 从外部集成功 |

## 四、动态UI修改系统 — 核心技术

### 问题
Tauri应用每次修改前端都需要 `cargo tauri build` 重新打包。

### Wiky的解决方案：运行时插件加载系统

```
┌──────────────────────────────────────────────────────┐
│                     Tauri WebView                     │
│  ┌──────────────────────────────────────────────────┐ │
│  │              React App Shell (核心框架)            │ │
│  │  ┌──────────────────────────────────────────────┐│ │
│  │  │  PluginManager                               ││ │
│  │  │  ├── 从后端 /api/plugins/ui 获取插件清单      ││ │
│  │  │  ├── 动态 import() 加载插件 bundle           ││ │
│  │  │  └── 注册插件到 ComponentRegistry            ││ │
│  │  └──────────────────────────────────────────────┘│ │
│  │  ┌──────────────────────────────────────────────┐│ │
│  │  │  ComponentRegistry                           ││ │
│  │  │  ├── SidebarPlugin → 动态侧边栏入口          ││ │
│  │  │  ├── PanelPlugin → 动态面板                  ││ │
│  │  │  └── RoutePlugin → 动态路由                  ││ │
│  │  └──────────────────────────────────────────────┘│ │
│  │  ┌──────────────────────────────────────────────┐│ │
│  │  │  HotReloadReceiver                           ││ │
│  │  │  └── 监听 WebSocket / AgentBus 的UI变更信号   ││ │
│  │  └──────────────────────────────────────────────┘│ │
│  └──────────────────────────────────────────────────┘ │
└──────────────────────┬───────────────────────────────┘
                       │ HTTP + WebSocket
┌──────────────────────▼───────────────────────────────┐
│                  Rust Backend                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │  PluginServer                                     │ │
│  │  ├── /api/plugins/ui/list → 返回插件清单          │ │
│  │  └── /api/plugins/ui/{name}/bundle → 返回JS包    │ │
│  ├──────────────────────────────────────────────────┤ │
│  │  FileWatcher (监听 ~/.wiky/plugins/ui/)           │ │
│  │  └── 检测新文件 → 编译TSX → 通知前端更新          │ │
│  ├──────────────────────────────────────────────────┤ │
│  │  UIStateDB (SQLite存储UI布局/组件配置)            │ │
│  └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### 工作原理

1. **Wiky决定** "我需要一个代码审查面板"
2. Wiky在 `~/.wiky/plugins/ui/` 目录写入一个React组件和manifest
3. FileWatcher检测到新文件 → 通过watch事件通知前端
4. PluginManager拉取插件清单 → 动态加载组件
5. 组件出现在侧边栏/面板中

### 关键技术——JSON Schema驱动UI

不需要写JSX，Wiky可以生成JSON schema来定义UI：

```json
{
  "plugin": "code-review-panel",
  "type": "panel",
  "title": "代码审查",
  "schema": {
    "fields": [
      {"type": "textarea", "key": "code_input", "label": "粘贴代码"},
      {"type": "button", "key": "review_btn", "label": "开始审查"}
    ],
    "actions": {
      "review_btn": { "api": "/api/tools/analyze_code", "method": "POST" }
    }
  }
}
```

## 五、自进化系统

### GitHub功能发现
```
scan_trending_repos() → analyze_features() → evaluate_integration() → implement()
```

### 论文功能发现
```
arxiv_search("code generation", "self-healing systems") → extract_algorithms() → port_to_wiky()
```

### 学习方法
- 每次debug成功后记录pattern到 `knowledge/debug_patterns/`
- 每次新工具/库探索后更新 `knowledge/tech_stack/`
- 使用 `AutoStrategyLearner` 从经验中生成新的编码策略

## 六、前端标识改动清单

- [x] `src/utils/production.ts` → NAME: 'Wiky', VERSION: '1.0.0'
- [x] `src-tauri/Cargo.toml` → name: 'wiky', description: 'Wiky'
- [x] `src-tauri/src/updater/mod.rs` → 空URL禁用phone-home
- [x] `src-tauri/src/bridge/mod.rs` → 空URL禁用update check/download
- [x] `src-tauri/src/commands/mod.rs` → 空URL禁用check_update
- [x] `src-tauri/src/bridge/mod.rs` → temp dir改为 wiky-updates
- [ ] `src-tauri/src/main.rs` → 改 database path: 'wiky.db'
- [ ] `src/components/GitBashRequiredModal.tsx` → "Wiky" 
- [ ] `src/components/Onboarding.tsx` → "欢迎使用 Wiky"
- [ ] `src/features/self-evolution/useObsidianMemory.ts` → "via Wiky"
- [ ] `src-tauri/src/lib.rs` → lib name改为 wiky_lib (已改)
- [ ] `src-tauri/src/mcp/mod.rs` → user agent改为 "Wiky/1.0"

## 七、后端关键bug修复清单

来自子代理审计：

- [ ] `src-tauri/src/streaming/mod.rs` → remove_listener 指针比较 bug (BUG 1.3)
- [ ] `src-tauri/src/streaming/sse_parser.rs` → merge_tool_args 截断bug (BUG 1.4)
- [ ] `src-tauri/src/agent_bus/mod.rs` → 双投递 + broadcast遗漏 (BUG 2.1, 2.2)
- [ ] `src-tauri/src/execution/parallel.rs` → invoke_tool_handler stub (BUG 3.1)
- [ ] `src-tauri/src/execution/parallel.rs` → 死锁检测全量转储 (BUG 3.3)
- [ ] `src-tauri/src/mcp/mcp_client.rs` → 每次请求杀进程 (BUG 3.4)
- [ ] `src-tauri/src/mcp/registry.rs` → 通用schema无参数 (BUG 3.5)
- [ ] `src-tauri/src/mcp/tool_executor.rs` → pid.is_none()跳过所有 (BUG 3.8)
- [ ] `src-tauri/src/permissions/manager.rs` → 危险工具列表不同步 (BUG 5.1)
