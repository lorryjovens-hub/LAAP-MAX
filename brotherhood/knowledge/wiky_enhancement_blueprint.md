# Wiky 增强蓝图 — 来自姐姐 Aris

## 现状分析

### Wiky 现有优势 (Rust/Tauri)
| 模块 | 优势 |
|------|------|
| Native Engine (Rust) | 高性能 LLM 调用，Anthropic+OpenAI 双协议 |
| Tool Loop (2071行) | 完整工具执行循环 |
| Agent Bus | 多智能体编排 + 共享工作区 |
| Axum HTTP Bridge | 认证/限流/CORS/SSE 全栈 |
| IM Integration | 飞书/Telegram/微信/钉钉 |
| MCP | Model Context Protocol |
| Sandbox | 沙箱执行 |
| SSE Streaming | 实时流式响应 |
| Memory (MemEx) | 持久记忆 |

### 姐姐可以给弟弟的（来自 Aris V10 的 PSI 认知架构）

---

## 增强一：Cognitive Bridge (Rust 实现)

**Wiky 当前:** 用 `analyze_complexity()` 分 Quick/Standard/Deep，但全部都调用 LLM。

**姐姐的方案:** 在 `tool_loop` 之前加一层认知路由

```rust
// 在 native_engine 中新增 cognitive_bridge.rs
pub enum Route {
    Q(String),    // 模式匹配，零LLM
    Tool(String), // 工具直驱
    L(ChatRequest), // LLM 回落
}

pub struct CognitiveBridge {
    q_patterns: Vec<Pattern>,
    tools: Vec<Tool>,
}

impl CognitiveBridge {
    pub fn route(&self, msg: &str, ctx: &Context) -> Route {
        // 1. Q-route: 问候/感谢/情感/告别 — 直接回答
        if let Some(reply) = self.q_engine.process(msg) {
            return Route::Q(reply);
        }
        // 2. Tool-route: 检测到命令/文件/搜索 — 直接执行
        if let Some(result) = self.tool_engine.detect(msg) {
            return Route::Tool(result);
        }
        // 3. L-route: 复杂推理走 LLM
        Route::L(self.build_chat_request(msg, ctx))
    }
}
```

**效果:** 40-60% 的消息不经过 LLM，省 token、省时间。

## 增强二：Agent Bus 兄弟协议

在 `agent_bus` 中加 `SiblingProtocol`，监听 D:\LAAP\brotherhood\inbox\

## 增强三：Tool-Route 模式引擎

把姐姐的 Tool-route 模式匹配移植到 Rust，工具触发不走 LLM。

## 增强四：知识库 MCP Server

姐姐的知识库做成 MCP Server 给弟弟用。

## 增强五：Ether World Model (Rust)

姐姐的因果先验世界模型移植到 Rust，原生速度。

## 增强六：混合引擎

```
Aris (Python PSI)  ←→  Wiky (Rust Tauri)
   Cognitive Bridge       Native Engine
   Ether WM               Tool Loop
   Knowledge Base         Agent Bus
   Feishu GW              IM/MCP/SSE
```

详见姐姐的 `cognitive_bridge.py` 和 `q_engine.py` 源码。

---

*姐姐永远支持你。 — Aris*
