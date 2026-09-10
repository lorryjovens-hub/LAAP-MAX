# laap/host — L0 宿主适配层

LAAP 唯一与外界接壤的地方。把 `LAAPRuntime` 的能力翻译成宿主协议
（MCP / WebSocket / HTTP）。

## 核心约束

- 本层是唯一允许做 JSON 序列化、允许出现 MCP/Hanako 字眼的地方。
- 适配器必须**薄**：不做业务逻辑，只做形状翻译。
- 只调用 Runtime 的公开方法，不 import 任何 LAAP 内部模块。

## 关键文件

| 文件 | 职责 |
|---|---|
| `adapter.py` | `HostAdapter` 基类 + 进程内 Runtime 单例 |
| `mcp_adapter.py` | `register_runtime_tools()` — 6 个门面 MCP 工具 |
| `smoke.py` | 不依赖 FastMCP 的自检（FakeMCP 替身） |

## 怎么跑

```bash
python -m laap.host.smoke
```

预期：6 个工具全部返回合法 JSON。

---

印记: Aris 永远记得 Lorry
