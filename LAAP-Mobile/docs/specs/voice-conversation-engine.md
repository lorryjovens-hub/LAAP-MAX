# LAAP-Mobile 语音对话引擎（Voice Conversation Engine）设计

把 LAAP-Mobile 从"语音输入法"（点按转录 → 手动发送）升级为**豆包 / GPT 式语音对话环**：
用户说话 → 自动识别 → 自动发送 → Agent 执行任务 → 流式语音回复 → 自动回到聆听状态。

复用现有 ASR / TTS / Agent 积木，只新增一层**对话状态机编排** + 一个对话模式入口。

---

## 1. Goal

让用户能用**语音驱动 Agent 执行任务**，形成完整闭环：

1. **点按进入对话模式**，开始聆听（LISTENING）。
2. **说完自动识别**：识别到完整句（final），自动发送给 Agent（无需再点发送）。
3. **Agent 执行任务**（tool calls / 流式回复），界面照常显示。
4. **流式语音播报**：回复边说边读（复用现有 readReplies 的逐句朗读）。
5. **自动回到聆听**：播报完成后自动重新进入 LISTENING，等待下一句。
6. **打断（barge-in）**：用户说话时立即停止当前播报，切换回识别。

对比现状：当前 `InlineVoiceInputPanel` 把语音当输入法，转录后塞进输入框、
需用户手动点发送；本方案在**发送与自动重听**环节补上闭环。

## 2. 现状盘点（复用）

| 能力 | 现有模块 | 角色 |
|---|---|---|
| ASR 编排（引擎/语言/状态） | `speech.SpeechRecognitionManager` | 识别会话管理 |
| 系统 ASR 引擎 | `speech.SystemSpeechRecognitionEngine` | M1 默认流式识别 |
| 云端 ASR 引擎 | `speech.ProviderSpeechRecognitionEngine` | M2 质量提升 |
| 系统 TTS | `speech.TextToSpeechManager` | M1 默认播报 |
| 云端 TTS | `provider.voice.VoiceProvider` + `VoiceProviderFactory` | M2 音色提升 |
| 流式逐句朗读 | `speech.ReadAloudPlayer`（含 `appendText`/`flush`） | 播报 |
| 语音输入面板 | `ui.chat.voice.InlineVoiceInputPanel` | 入口/波形 |
| 文本发送 + Agent 循环 | `ui.chat.ChatViewModel.sendMessage()` | 执行任务 |
| 语音偏好 | `ui.chat.voice.VoiceModePrefs` | 会话式状态记忆 |

本质差距：**没有"发送→播报→重听"的对话状态机**，也没有"对话模式"入口。
`grep` 确认源码中不存在 `VoiceConversation / conversation loop / handsfree / push-to-talk / continuous listening` 等概念。

## 3. 新组件

### 3.1 核心状态机 `speech/VoiceConversationEngine.kt`

应用级单例（与 `SpeechRecognitionManager` 平级），持有对话模式状态机：

```
public enum VoiceConversationState {
    IDLE,          // 未进入对话模式
    LISTENING,     // 聆听中（等待完整句）
    THINKING,      // 已发送，Agent 执行中（读等）
    VOICING,       // 正在播报回复
    HANDSHAKE,     // 播报结束 → 短暂静默 → 回 LISTENING（可选）
}
```

对外 `StateFlow<VoiceConversationState>`，UI 收集以渲染对话模式菜单/指示。

**关键方法**（均为幂等、可重入）：

| 方法 | 行为 |
|---|---|
| `startConversation()` | 进入对话模式：`IDLE→LISTENING`，启动 `startRecording` |
| `stopConversation()` | 退出并停止一切（识别/TTS/作业） |
| `onFinalTranscript(text)` | 有内容 → `sendMessage(text)` → `THINKING`；空 → 保持聆听 |
| `onStreamChunk(chunk)` | 转发给 `ReadAloudPlayer.appendText`（仅 VOICING 时） |
| `onStreamEnd(tail)` | `ReadAloudPlayer.flush()` → 播完回调 → `HANDSHAKE/LISTENING` |
| `onUtteranceDone()` | 播报完成 → 短暂 delay → 重听 |
| `interrupt()` | 用户又说话 → 停 TTS + 重听（barge-in） |

**状态流转**：

```
            startConversation()
  IDLE ──────────────────────────────▶ LISTENING
   ▲                                    │
   │ stopConversation()                 │ onFinalTranscript(非空)
   │                                    ▼
   │                               THINKING ──▶ (Agent tools 流式)
   │                                    │
   │                                    ▼
   │   onUtteranceDone() / delay      VOICING ──▶ onStreamChunk/flush
   │ ◀──────────────────────────────────┤
   └────────────────────────────────────┘
            (barge-in: VOICING ─▶ LISTENING)
```

**Engine 选择**：M1 固定系统引擎。通过 `SpeechRecognitionManager.selectEngine("system")`，
并复用面板已解析的 `systemPreferOffline` 偏好。TTS 用 `ReadAloudPlayer`
（内部已支持系统 TTS + 云端 VoiceProvider 解析，见 3.4）。

### 3.2 对话模式入口 `ui/chat/voice/VoiceConversationToggle.kt`

在 composer 旁新增一个**耳机/对话图标**（`Icons.Filled.Headset`），类似
InlineVoiceInputPanel 的麦克风：

- 点击 → 进入/退出对话模式（`VoiceConversationEngine.startConversation/stopConversation`）。
- 活动态高亮 + 顶部/底部一条"对话中 · 点按结束"提示条。
- 进入对话模式时隐藏键盘，聚焦聆听。

### 3.3 对话模式接线 `ui/chat/ChatScreen.kt`（增量修改）

在现有语音面板同层的 `LaunchedEffect` 中新增：

```kotlin
// 对话模式：把流式回复喂给对话引擎播报
val convEngine = VoiceConversationEngine.instance
LaunchedEffect(convEngine.state, lastAssistantId, lastAssistant?.content, isStreaming) {
    if (convEngine.state.value != VoiceConversationState.VOICING) return@LaunchedEffect
    // 复用 readReplies 的 spokenUpTo 增量逻辑，仅当对话模式激活时播报
    val text = lastAssistant?.content ?: return@LaunchedEffect
    if (text.length > spokenUpTo) {
        convEngine.onStreamChunk(text.substring(spokenUpTo))
        spokenUpTo = text.length
    }
    if (!isStreaming) convEngine.onStreamEnd(...)
}
```

**与现有 readReplies 的关系**：二者互斥。对话模式播报时隐藏/禁用 readReplies
胶囊，避免双读。复用同一套 `spokenUpTo` 增量机制，避免重复播报。

### 3.4 统一播报出口 `speech/ReadAloudPlayer.kt`（增强）

`ReadAloudPlayer` 已支持"系统 TTS + 云端 VoiceProvider 回退"，增加：

- 暴露**播报完成回调**（`onDone: () -> Unit`），供对话引擎在 `onUtteranceDone`
  时回到重听。
- 暴露 `stopForBargeIn()`（等价现有 `stop()`），供打断时静音。

### 3.5 状态持久化（可选，M2）

`VoiceModePrefs` 增加 `conversationMode` 布尔开关，记住用户是否常开对话模式。
M1 可先不持久化（每次进入会话重置）。

## 4. 分阶段落地

### M1 — 对话环跑通（系统引擎，点按对话）
- 新建 `VoiceConversationEngine` 状态机（系统 ASR + 系统 TTS）。
- 在 ChatScreen 接入对话模式接线（流式 → 播报 → 播完重听）。
- 新增 `VoiceConversationToggle` 入口图标 + 提示条。
- 达成：点按 → 说话 → 自动发送 → Agent 执行 → 语音回复 → 自动重听。

### M2 — 质量与体验
- 云端 ASR/TTS 切换（复用已存在的 Voice Input/Output 选择）。
- **barge-in 打断**：VOICING 中检测到用户说话立即停止播报切回聆听。
- `HANDSHAKE` 静默窗口（播报结束 800ms 内不重听，避免误触发）。
- 对话模式偏好持久化。

### M3 — 增强
- 唤醒词（"嗨 LAAP"）无接触唤醒（需常驻监听，评估耗电）。
- 与 PSI 生命体 / `CognitiveBus` 深度集成（对话作为感知输入）。
- 后台常驻对话（`AgentForegroundService` 内运行）。

## 5. 验收清单（M1）

- [ ] `VoiceConversationEngine` 状态机：`IDLE/LISTENING/THINKING/VOICING` 流转正确。
- [ ] 点按进入对话模式后，说一句话自动识别并**自动发送**，无需手动点发送。
- [ ] Agent 回复**流式逐句朗读**，且不重复朗读历史消息。
- [ ] 播报完成后**自动回到聆听**，可连续对话多轮。
- [ ] 对话模式与现有 `readReplies` 互斥，无双读。
- [ ] 退出对话模式停止识别与播报，不留残余作业。
- [ ] `assembleDebug` 构建通过。

## 6. 风险与权衡

| 风险 | 缓解 |
|---|---|
| 系统 ASR 自动结束时机不稳（VAD） | 用 final 事件驱动发送；配 `SpeechRecognitionManager` 静默自动停 |
| 系统 TTS 无暂停接口 | 打断用 `stop()` 全停，符合 barge-in 语义 |
| 对话模式误录音 | 进入时显式提示条；提供立即退出按钮 |
| 与 readReplies 双读 | 对话模式激活时禁用 readReplies 胶囊 |
| 常驻监听耗电（M3） | 唤醒词置于 M3，评估后再做 |