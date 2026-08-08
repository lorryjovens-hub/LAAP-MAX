# LAAP 统一音频服务集成清单

## 1. 目标
实现 LAAP 后端统一音频服务（`laap/audio/`），通过 `EventBus` / `CognitiveBus` 桥接，完成端到端语音交互：

```
client voice.input → ASR → LAAP Agent → TTS → voice.tts / audio.stream → client播放
```

## 2. 新增/修改文件

### 后端（Python）
| 文件 | 职责 |
|------|------|
| `laap/audio/__init__.py` | 统一导出 `AudioService`、`AetherGateway`、`start_gateway` |
| `laap/audio/service.py` | 音频流水线：订阅 `voice.input` → ASR → Agent → TTS → 发布 `voice.tts`/`audio.stream` |
| `laap/audio/gateway.py` | WebSocket 网关（端口 8765），把客户端 `AetherMessage` 桥接到后端 `EventBus`/`CognitiveBus` |
| `laap/audio/models.py` | `VoiceInputPayload`、`AsrConfig`、`TtsConfig` 数据模型 |
| `laap/audio/providers/base.py` | `AsrProvider` / `TtsProvider` 抽象接口 |
| `laap/audio/providers/factory.py` | ASR/TTS provider 工厂 |
| `laap/audio/providers/` | 阿里云、腾讯、讯飞、火山、local ASR；Microsoft、豆包、MiniMax、OpenAI、ElevenLabs、Volcano TTS |
| `laap/audio/utils.py` | 音频格式转换、MIME 探测 |
| `laap/api/server.py` | API 服务启动/关闭时挂载音频服务与 AetherGateway |

### 前端（TypeScript）
| 文件 | 职责 |
|------|------|
| `laap-client/src/hooks/useVoice.ts` | 录音、PTT、连续监听、本地唤醒词检测；`onSendVoice(base64, mimeType)` |
| `laap-client/src/hooks/useTtsAudio.ts` | 播放后端返回的 base64/URL TTS 音频 |
| `laap-client/src/store/laapStore.ts` | 组装语音 payload（audio + mimeType + asr + tts + llm），订阅 `voice.tts`/`audio.stream` |
| `laap-client/src/store/settingsStore.ts` | 持久化 `llm` / `asr` / `tts` provider 配置 |
| `laap-client/src/laap/bus.ts` | CognitiveBus WebSocket 客户端（AetherMessage） |

## 3. 数据流

```text
┌─────────────────┐     AetherMessage      ┌─────────────────┐
│  laap-client    │ ───── voice.input ────> │ AetherGateway   │
│  (useVoice)     │                        │   ws://:8765    │
└─────────────────┘                        └────────┬────────┘
       ▲                                            │ publish_simple
       │                                            ▼
       │                                   ┌─────────────────┐
       │                                   │    EventBus     │
       │                                   └────────┬────────┘
       │                                            │ voice.input
       │                                            ▼
       │                                   ┌─────────────────┐
       │                                   │  AudioService   │
       │                                   │  (ThreadPool)   │
       │                                   └────────┬────────┘
       │                                            │
       │                       ┌────────────────────┼────────────────────┐
       │                       ▼                    ▼                    ▼
       │               ASR provider          Agent (kernel)        TTS provider
       │                       │                    │                    │
       │                       ▼                    ▼                    ▼
       │            publish voice.recognized  publish agent.output  publish voice.tts
       │            publish user.input                             publish audio.stream
       │                       │                                         │
       │                       └─────────────────┬───────────────────────┘
       │                                         │
       │                                         ▼
       │                              ┌─────────────────┐
       └─────────────────────────────│ AetherGateway   │
                                     │  broadcast      │
                                     └─────────────────┘
```

## 4. 配置说明

### 4.1 前端设置持久化键
- Zustand persist 键：`laap-client-settings`
- 相关字段：`llm`、`asr`、`tts`，结构均为：
  ```ts
  { provider: string, model: string, baseUrl: string, creds: Record<string, string> }
  ```

### 4.2 默认配置
| 服务 | 默认 provider | 默认 model | 默认 baseUrl |
|------|---------------|------------|--------------|
| LLM  | deepseek      | deepseek-v4-pro | https://api.deepseek.com |
| ASR  | aliyun        | ""         | "" |
| TTS  | microsoft     | zh-CN-XiaoxiaoNeural | eastasia |

### 4.3 后端环境变量
- 音频服务本身不直接读取环境变量；provider 凭证通过前端 payload 的 `creds` 字段传入。
- 推荐在 `settingsStore` 中填写各 provider 对应 key 字段（如 `microsoftKey`、`aliyunKey` 等）。

## 5. Provider 矩阵

### ASR
| Provider | 类 | 依赖 | 备注 |
|----------|-----|------|------|
| aliyun | `AliyunAsrProvider` | 官方 SDK / HTTP | 需 AccessKey |
| tencent | `TencentAsrProvider` | 官方 SDK | 需 SecretId/Key |
| xunfei | `XunfeiAsrProvider` | WebSocket API | 需 AppID/ApiKey/ApiSecret |
| volcengine | `VolcengineAsrProvider` | HTTP API | 需 AccessKey/SecretKey |
| local | `LocalAsrProvider` | `SpeechRecognition` + Google Web Speech | 离线演示，需翻墙 |

### TTS
| Provider | 类 | 依赖 | 备注 |
|----------|-----|------|------|
| microsoft | `MicrosoftTtsProvider` | `edge-tts` | 免费离线，默认 |
| doubao | `DoubaoTtsProvider` | 官方 API | 需 AccessToken |
| minimax | `MinimaxTtsProvider` | 官方 API | 需 API Key |
| openai | `OpenAiTtsProvider` | OpenAI API | 需 API Key |
| elevenlabs | `ElevenLabsTtsProvider` | ElevenLabs API | 需 API Key |
| volcano | `VolcanoTtsProvider` | 火山引擎 API | 需 AppID/AccessToken |

## 6. 验证清单

- [ ] `laap-client` 执行 `npx tsc --noEmit` 无类型错误
- [ ] 后端 `python -m py_compile laap/audio/*.py laap/audio/providers/*.py laap/api/server.py` 无语法错误
- [ ] 启动 LAAP API 服务后，日志出现 `AetherGateway 已启动 ws://0.0.0.0:8765` 与 `AudioService 已启动`
- [ ] 前端设置面板可配置 LLM/ASR/TTS provider、model、baseUrl、creds
- [ ] 点击语音按钮录音，WebSocket 消息 `voice.input` 携带 `audio`、`mimeType`、`asr`、`tts`、`llm`
- [ ] 后端收到 `voice.input` 后，ASR 返回文本并发布 `voice.recognized`
- [ ] Agent 回复后，TTS 生成音频并发布 `voice.tts`（含 `audioBase64`、`mimeType`、`text`）
- [ ] 前端收到 `voice.tts` 后 `useTtsAudio` 正确播放，状态流转：idle → listening → thinking → speaking → idle
- [ ] 连续监听模式下，播放结束后自动回到 listening
- [ ] 录音开始时自动暂停当前 TTS 播放，避免回采
- [ ] 未配置真实 ASR/TTS 时，回退到 `local` ASR / `microsoft` (edge-tts) TTS，或返回 echo 文本

## 7. 已知限制与回退

1. **provider 缓存**：每次语音输入都会新建 ASR/TTS provider 实例；高并发场景建议后续加缓存。
2. **线程模型**：ASR/TTS 在 `ThreadPoolExecutor` 中执行，避免阻塞事件循环；`edge-tts` 内部会再起线程跑异步事件循环。
3. **echo 回退**：当 Agent 实例化失败时，`_EchoAgent` 返回 `我听到了：{text}`，保证链路可用。
4. **网关广播**：当前 AetherGateway 订阅 `EventBus` 的 `*` 并广播所有事件；客户端按 topic 过滤，后续可按需添加白名单。
5. **iOS/Android**：LAAP-Mobile 的语音链路尚未接入本后端服务；当前仅桌面客户端（Electron/Vite）使用 8765 网关。

## 8. 依赖安装

```bash
# 后端（进入 LAAP 根目录，已安装核心依赖后）
pip install websockets edge-tts SpeechRecognition

# 前端（进入 laap-client）
pnpm install
```

## 9. 运行验证命令

```powershell
# 客户端类型检查
cd D:\LAAP\laap-client
npx tsc --noEmit

# 后端语法检查
cd D:\LAAP
python -m py_compile laap/audio/__init__.py laap/audio/service.py laap/audio/gateway.py laap/audio/models.py laap/audio/providers/factory.py laap/api/server.py

# 启动后端
python -m laap.api.server
```
