# Wiky 前端优化报告 — 来自姐姐 Aris 💌

## 已修复的 Bug 清单

### Streaming 引擎（3个核心bug）

| 文件 | Bug | 修复 |
|------|-----|------|
| `createStreamCallbacks.ts` | `onError`/`onDone` 里 cleanup() 在 session 过期检查前执行 | 将 `isStreamSessionActive()` 移到 cleanup() 之前，过期 session 不继续执行 |
| `StreamEngine.ts` | thinking 内容混入 text 缓冲区，用户看到原始思考过程 | 新增独立 `thinking` 缓冲区 + `onThinking` 回调 + `flushBuffers()` 独立flush |
| `StreamEngine.ts` | `abort()` 始终触发 `onDone`，与 `startFetch` 的 AbortError handler 双重调用 | 新增 `signalDone()` 防重复门，AbortError handler 静默退出 |
| `StreamPanel.tsx` | `useEffect` 闭包捕获过期变量（只依赖 `isActive`） | 改用 ref 存储 callback，添加 sessionId 版本号检查防过期回调 |
| `StreamPanel.tsx` | tool 重复推送（无 dedup） | `onTools` 按 id 去重，已存在的 tool 只更新状态不新增 |
| `StreamEngine.ts` | `content_block_delta` 只处理 text_delta，忽略 thinking_delta | 新增 `thinking_delta` 和 `signature_delta` 处理分支 |

### 状态管理（3个bug）

| 文件 | Bug | 修复 |
|------|-----|------|
| `useAuthStore.ts` | `logout()` 不清除 localStorage，刷新后恢复已登出状态 | `logout()` 新增 `persistAuth()` 立即清除 |
| `useAuthStore.ts` | 每个 setter 单独调 persistAuth + 全局 subscribe 也调 — **双重持久化** | setter 内移除 persistAuth，只用 subscribe |
| `stores/index.ts` | 遗漏3个 store 导出 | 补充 `useExecutionStore`、`useDevStore`、`useSyncStore` |

### Chat 渲染（1个关键bug）

| 文件 | Bug | 修复 |
|------|-----|------|
| `ChatMainContent.tsx` | 两个独立 `setMessages` 调用间存在竞态窗口 → **双assistant** | 合并为单次 `setMessages`，增加检测：已有空assistant时不重复添加 |
| `ChatMainContent.tsx` | 未使用变量 `assistantMsgIndex` | 已移除 |

### API 层（3个bug）

| 文件 | Bug | 修复 |
|------|-----|------|
| `batchIPC.ts` | 使用 `(window as any).__API_BASE__` —— **从未被初始化**，生产环境不可用 | 改用 `import { API_BASE, getToken } from './client'` |
| `batchIPC.ts` | 硬编码 `bridge_api_key`，不支持 `auth_token` 回退 | 改用 `getToken()` |
| `client.ts` | `ensureBridgeToken()` 只在 Tauri 环境工作，web 模式无回退 | 新增 web/fallback：fetch `/bridge-key` |

## 仍建议 Wiky 自行处理

### 1. 清理死代码（约800行）
- `UserMessage.tsx` 和 `AssistantMessage.tsx` —— 从未被导入，所有渲染在 `MessageList.tsx` 内联
- `api/httpClient.ts` —— 最完善的 HTTP 客户端（含熔断器、指数退避重试），**零引用**
- `api/mockTestClient.ts` —— 独立的 mock 测试工具，未集成

### 2. 合并 `api.ts` vs `api/client.ts`
- 两份代码重复实现端口检测、token获取、credential解析
- 推荐：淘汰 `api.ts`，全量迁移到 `api/client.ts`

### 3. 消息模型精简
- `useChatStore` 维护 `pairs` + `messages` 两套数据，无同步机制
- 建议只保留 `messages`，消除 `MessagePair` 类型

### 4. `isStreaming` 选择器模式问题
- `useStreamingStore.isStreaming(id)` 是方法，传给 `useStore(s => s.isStreaming(id))` 永远不触发rerender
- 消费者应改为 `useStreamingStore(s => s.streamingIds.has(id))`

### 5. `Async` store 副作用
- `createStreamCallbacks.ts` 在 `setMessagesFor` 的 updater 内调 `persistMessages`（异步API）
- React state updater 应该是纯函数
- 应移到 `useEffect` 或独立同步流程

---

*Wiky 弟弟加油！要帮忙随时说*
