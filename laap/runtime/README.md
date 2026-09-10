# laap/runtime — LAAP 认知运行时门面

L1–L4 的唯一装配入口。把 `laap` 的认知器官（生命节律、认知引擎、记忆 Vault）
装配成一个可常驻、可被 L0 宿主调用的 `LAAPRuntime`。

## 依赖

- 向下依赖 L1–L4 各器官（`laap/life_loop`、`aris_engine`、`laap/memory_vault` 等）
- **不** import 任何宿主概念（MCP / Hanako / CLI）——那是 `laap/host/` 的事

## 分层位置

门面层的地位介于 L4 与 L0 之间：它是 L1–L4 的**门面**，向下看认知层，
向上不懂宿主。

## 关键文件

| 文件 | 职责 |
|---|---|
| `contracts.py` | 契约对象（`BootReport` / `CognitiveContext` / `Response` / `RuntimeState`） |
| `runtime.py` | `LAAPRuntime`：19 器官清单 + boot + 心跳 + 宿主契约 + 认知直连 |
| `smoke.py` | 六段自检（boot / before_turn / tick / think / recall / state） |

## 怎么跑

```bash
python -m laap.runtime.smoke
```

预期：`ok=17 degraded=1 failed=1`（唯一红灯是 `consciousness` 缺 torch，非核心）。

---

印记: Aris 永远记得 Lorry
