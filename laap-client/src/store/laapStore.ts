/**
 * LAAP 全局状态管理（Zustand）
 *
 * 在应用初始化时创建 CognitiveBusClient 与 RateBuffer 实例，
 * 订阅后端事件并驱动 UI 状态更新。
 */

import { create } from 'zustand'
import { CognitiveBusClient } from '../laap/bus'
import { RateBuffer } from '../laap/rateBuffer'
import type {
  Agent,
  ChatMessage,
  ColonyMessage,
  ColonyState,
  ConnectionStatus,
  PSIPhase,
  RateBufferStats,
  SceneState,
  SceneSurface,
  Thought,
  ToolCall,
  VoiceState,
  VitalSigns,
  TtsAudioSource,
} from '../laap/types'

/**
 * 生产环境后端地址：优先读取环境变量，否则使用默认地址
 */
function resolveBackendUrl(): string {
  const envUrl = import.meta.env.VITE_BACKEND_URL as string | undefined
  return envUrl?.trim() || 'ws://127.0.0.1:8765'
}

/**
 * 生成唯一 ID
 */
function generateId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
}

/**
 * 验证并转换 PSI 阶段
 */
function parsePSIPhase(value: unknown): PSIPhase {
  const phases: PSIPhase[] = ['perception', 'selection', 'integration', 'learning']
  if (typeof value === 'string' && phases.includes(value as PSIPhase)) {
    return value as PSIPhase
  }
  return 'perception'
}

/**
 * 默认生命体征
 */
const defaultVitalSigns: VitalSigns = {
  curiosity: 0.5,
  trust: 0.5,
  competence: 0.5,
  pleasure: 0.5,
  arousal: 0.5,
  dominance: 0.5,
  sociality: 0.5,
  stress: 0.2,
}

/**
 * 默认 Colony 状态
 */
const defaultAgents: Agent[] = [
  { id: 'agent-1', name: 'Aris', status: 'online', role: '协调者', resource: 78 },
  { id: 'agent-2', name: 'Codex', status: 'busy', role: '代码专家', resource: 62 },
  { id: 'agent-3', name: 'Guardian', status: 'offline', role: '安全审查', resource: 0 },
]

const defaultColonyEdges = [
  { id: 'e1', from: 'agent-1', to: 'agent-2', label: '任务分派', intensity: 0.8 },
  { id: 'e2', from: 'agent-2', to: 'agent-3', label: '代码审查', intensity: 0.5 },
  { id: 'e3', from: 'agent-3', to: 'agent-1', label: '报告风险', intensity: 0.3 },
]

/**
 * LaapState 接口
 */
export interface LaapState {
  connectionStatus: ConnectionStatus
  messages: ChatMessage[]
  psiCycle: { phase: PSIPhase; progress: number }
  vitalSigns: VitalSigns
  rateBuffer: RateBufferStats
  colony: ColonyState
  scene: SceneState
  currentToolCall: ToolCall | null
  thoughts: Thought[]
  isStreaming: boolean
  error: string | null
  voice: VoiceState

  sendUserMessage: (text: string) => void
  connect: () => void
  disconnect: () => void
  updateVitalSigns: (partial: Partial<VitalSigns>) => void
  retryToolCall: (id: string) => void
  clearError: () => void
  setVoiceStatus: (status: VoiceState['status']) => void
  setVoiceAudioLevel: (level: number) => void
  setVoiceContinuousListening: (enabled: boolean) => void
  sendVoiceInput: (base64Audio: string) => void
  clearVoiceTtsAudio: () => void
}

/**
 * CognitiveBus 单例引用，允许外部模块在不订阅 store 的情况下访问总线。
 */
let cognitiveBusInstance: CognitiveBusClient | null = null

/**
 * 获取当前应用使用的 CognitiveBusClient 实例。
 */
export function getCognitiveBus(): CognitiveBusClient {
  if (!cognitiveBusInstance) {
    cognitiveBusInstance = new CognitiveBusClient({ url: resolveBackendUrl() })
  }
  return cognitiveBusInstance
}

/**
 * 创建全局 store
 */
export const useLaapStore = create<LaapState>((set, get) => {
  // 在 store 外部维护当前流式回复的消息 ID，避免污染状态树
  let streamingMessageId: string | null = null

  // 创建 CognitiveBusClient 与 RateBuffer 实例，复用外部单例
  const bus = getCognitiveBus()
  cognitiveBusInstance = bus
  const rateBuffer = new RateBuffer()

  // 连接状态监听
  bus.onStatusChange((status, error) => {
    set({ connectionStatus: status, error: error ?? null })
  })

  // 高频 PSI 事件进入 RateBuffer
  bus.subscribe('v12_kernel', (message) => {
    rateBuffer.push(message)
    const payload = message.payload as { phase?: unknown; progress?: number } | undefined
    set({
      psiCycle: {
        phase: parsePSIPhase(payload?.phase),
        progress: payload?.progress ?? 0,
      },
    })
  })

  // 需求事件 -> 生命体征
  bus.subscribe('need_curiosity', (message) => {
    rateBuffer.push(message)
    const value = (message.payload as { value?: number } | undefined)?.value
    if (typeof value === 'number') {
      set((state) => ({
        vitalSigns: { ...state.vitalSigns, curiosity: Math.min(1, Math.max(0, value)) },
      }))
    }
  })
  bus.subscribe('need_trust', (message) => {
    rateBuffer.push(message)
    const value = (message.payload as { value?: number } | undefined)?.value
    if (typeof value === 'number') {
      set((state) => ({
        vitalSigns: { ...state.vitalSigns, trust: Math.min(1, Math.max(0, value)) },
      }))
    }
  })
  bus.subscribe('need_competence', (message) => {
    rateBuffer.push(message)
    const value = (message.payload as { value?: number } | undefined)?.value
    if (typeof value === 'number') {
      set((state) => ({
        vitalSigns: { ...state.vitalSigns, competence: Math.min(1, Math.max(0, value)) },
      }))
    }
  })

  // 5D 情感事件 -> 生命体征
  bus.subscribe('emotion_pleasure', (message) => {
    rateBuffer.push(message)
    const value = (message.payload as { value?: number } | undefined)?.value
    if (typeof value === 'number') {
      set((state) => ({
        vitalSigns: { ...state.vitalSigns, pleasure: Math.min(1, Math.max(0, value)) },
      }))
    }
  })
  bus.subscribe('emotion_arousal', (message) => {
    rateBuffer.push(message)
    const value = (message.payload as { value?: number } | undefined)?.value
    if (typeof value === 'number') {
      set((state) => ({
        vitalSigns: { ...state.vitalSigns, arousal: Math.min(1, Math.max(0, value)) },
      }))
    }
  })
  bus.subscribe('emotion_dominance', (message) => {
    rateBuffer.push(message)
    const value = (message.payload as { value?: number } | undefined)?.value
    if (typeof value === 'number') {
      set((state) => ({
        vitalSigns: { ...state.vitalSigns, dominance: Math.min(1, Math.max(0, value)) },
      }))
    }
  })
  bus.subscribe('emotion_sociality', (message) => {
    rateBuffer.push(message)
    const value = (message.payload as { value?: number } | undefined)?.value
    if (typeof value === 'number') {
      set((state) => ({
        vitalSigns: { ...state.vitalSigns, sociality: Math.min(1, Math.max(0, value)) },
      }))
    }
  })
  bus.subscribe('emotion_stress', (message) => {
    rateBuffer.push(message)
    const value = (message.payload as { value?: number } | undefined)?.value
    if (typeof value === 'number') {
      set((state) => ({
        vitalSigns: { ...state.vitalSigns, stress: Math.min(1, Math.max(0, value)) },
      }))
    }
  })

  // harness_execution_result：低频但重要，直接更新状态
  bus.subscribe('harness_execution_result', (message) => {
    rateBuffer.push(message)
    const payload = message.payload as
      | { success?: boolean; durationMs?: number; output?: string; replyId?: string }
      | undefined

    // 若存在进行中的流式回复，追加执行结果摘要并结束流式状态
    if (streamingMessageId && payload?.replyId) {
      set((state) => ({
        isStreaming: false,
        messages: state.messages.map((msg) =>
          msg.id === streamingMessageId
            ? {
                ...msg,
                content: `${msg.content}\n\n[执行结果] ${payload.success ? '成功' : '失败'}，耗时 ${payload.durationMs ?? 0}ms`,
              }
            : msg,
        ),
      }))
      streamingMessageId = null
    }
  })

  // QRE 涌现洞察：进入 thought 流，类型标记为 reasoning
  bus.subscribe('qre_*', (message) => {
    rateBuffer.push(message)
    const payload = message.payload as
      | { insight?: string; confidence?: number; replyId?: string }
      | undefined
    const text = payload?.insight ?? ''
    if (!text) return
    const thought: Thought = {
      id: generateId(),
      content: text,
      type: 'reasoning',
      confidence: payload?.confidence,
      timestamp: message.timestamp,
    }
    set((state) => ({ thoughts: [...state.thoughts, thought] }))
  })

  // 全量 scene 快照：直接替换 surfaces
  bus.subscribe('scene', (message) => {
    rateBuffer.push(message)
    const payload = message.payload as
      | { surfaces?: Record<string, SceneSurface> }
      | undefined
    const surfaces = payload?.surfaces
    if (!surfaces) return
    set({ scene: { surfaces } })
  })

  // 场景 patch：合并更新 surfaces，支持任意 kind 与字段
  bus.subscribe('scene.patch', (message) => {
    rateBuffer.push(message)
    const payload = message.payload as
      | { surfaceId?: string; patch?: Partial<SceneSurface> }
      | undefined
    const surfaceId = payload?.surfaceId
    if (!surfaceId) return

    set((state) => {
      const existing = state.scene.surfaces[surfaceId]
      const patch = payload?.patch ?? {}
      const next: SceneSurface = {
        ...(existing ?? {
          id: surfaceId,
          kind: 'text',
          content: '',
          updatedAt: message.timestamp,
        }),
        ...patch,
        id: surfaceId,
        kind: patch.kind ?? existing?.kind ?? 'text',
        updatedAt: message.timestamp,
      }
      return {
        scene: {
          surfaces: { ...state.scene.surfaces, [surfaceId]: next },
        },
      }
    })
  })

  // 流式文本 chunk
  bus.subscribe('chunk', (message) => {
    const payload = message.payload as { text?: string; replyId?: string } | undefined
    const text = payload?.text ?? ''

    set((state) => {
      if (streamingMessageId) {
        return {
          messages: state.messages.map((msg) =>
            msg.id === streamingMessageId ? { ...msg, content: msg.content + text } : msg,
          ),
        }
      }
      const id = generateId()
      streamingMessageId = id
      return {
        isStreaming: true,
        messages: [
          ...state.messages,
          { id, role: 'assistant', content: text, timestamp: message.timestamp },
        ],
      }
    })
  })

  // 思维链 chunk -> 生成独立的思考流条目
  bus.subscribe('thought_chunk', (message) => {
    const payload = message.payload as
      | { text?: string; type?: string; confidence?: number; alert?: string; replyId?: string }
      | undefined
    const text = payload?.text ?? ''
    if (!text) return

    const allowedTypes = ['reasoning', 'reflection', 'bias'] as const
    const thoughtType = allowedTypes.includes(payload?.type as typeof allowedTypes[number])
      ? (payload!.type as typeof allowedTypes[number])
      : 'reasoning'

    const thought: Thought = {
      id: generateId(),
      content: text,
      type: thoughtType,
      confidence: payload?.confidence,
      alert: payload?.alert,
      timestamp: message.timestamp,
    }

    set((state) => ({ thoughts: [...state.thoughts, thought] }))
  })

  // 工具调用：将工具调用挂载到当前流式消息，不污染文本内容
  bus.subscribe('tool_call', (message) => {
    const payload = message.payload as { toolCall?: ToolCall; replyId?: string } | undefined
    const toolCall = payload?.toolCall
    if (!toolCall) return

    set({ currentToolCall: toolCall })
    if (!streamingMessageId) return
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === streamingMessageId ? { ...msg, toolCall } : msg,
      ),
    }))
  })

  // 工具结果：更新当前工具调用状态与挂载结果
  bus.subscribe('tool_result', (message) => {
    const payload = message.payload as { toolCall?: ToolCall; replyId?: string } | undefined
    const toolCall = payload?.toolCall
    if (!toolCall) return

    set({ currentToolCall: toolCall })
    if (!streamingMessageId) return
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === streamingMessageId ? { ...msg, toolCall } : msg,
      ),
    }))
  })

  // RateBuffer batch 输出同步到 store
  rateBuffer.onBatch(() => {
    set({ rateBuffer: rateBuffer.getStats() })
  })
  rateBuffer.start()

  // Colony 状态更新：支持 mock server 推送 agent 状态与消息流
  bus.subscribe('colony.agent', (message) => {
    rateBuffer.push(message)
    const payload = message.payload as
      | { agents?: Agent[]; edges?: ColonyState['edges']; messages?: ColonyMessage[] }
      | undefined
    set((state) => {
      const nextAgents = payload?.agents ?? state.colony.agents
      const nextEdges = payload?.edges ?? state.colony.edges
      const nextMessages = payload?.messages ?? state.colony.messages
      return { colony: recountColony(nextAgents, nextEdges, nextMessages) }
    })
  })

  // 语音输入识别结果
  bus.subscribe('voice.recognized', (message) => {
    rateBuffer.push(message)
    const text = (message.payload as { text?: string } | undefined)?.text
    if (text) {
      set((state) => ({
        voice: { ...state.voice, status: 'thinking', lastRecognizedText: text },
      }))
    }
  })

  // TTS 事件：携带真实音频时写入 voice.ttsAudio 供 useTtsAudio 播放；
  // 仅包含文本/元数据时作为无音频 fallback，不自动播放。
  bus.subscribe('voice.tts', (message) => {
    rateBuffer.push(message)
    const payload = message.payload as
      | { speaking?: boolean; text?: string; audioBase64?: string; audioUrl?: string }
      | undefined
    const source: TtsAudioSource = {
      audioBase64: payload?.audioBase64,
      audioUrl: payload?.audioUrl,
    }
    const hasAudio = Boolean(source.audioBase64 || source.audioUrl)

    if (!hasAudio) {
      console.warn('[WARN] 收到 voice.tts 事件但未包含音频数据，跳过播放')
      return
    }

    set((state) => ({
      voice: { ...state.voice, ttsAudio: source },
    }))
  })

  // 兼容部分后端可能使用 audio.stream topic 推送 TTS 音频
  bus.subscribe('audio.stream', (message) => {
    rateBuffer.push(message)
    const payload = message.payload as
      | { audioBase64?: string; audioUrl?: string }
      | undefined
    const source: TtsAudioSource = {
      audioBase64: payload?.audioBase64,
      audioUrl: payload?.audioUrl,
    }
    if (!source.audioBase64 && !source.audioUrl) {
      console.warn('[WARN] 收到 audio.stream 事件但未包含音频数据，跳过播放')
      return
    }
    set((state) => ({
      voice: { ...state.voice, ttsAudio: source },
    }))
  })

  // 初始化 colony 计数
  function recountColony(
    agents: Agent[],
    edges: ColonyState['edges'] = defaultColonyEdges,
    messages: ColonyMessage[] = [],
  ): ColonyState {
    return {
      agents,
      onlineCount: agents.filter((a) => a.status === 'online').length,
      busyCount: agents.filter((a) => a.status === 'busy').length,
      offlineCount: agents.filter((a) => a.status === 'offline').length,
      edges,
      messages: messages.slice(-5),
    }
  }

  return {
    connectionStatus: 'closed',
    messages: [],
    psiCycle: { phase: 'perception', progress: 0 },
    vitalSigns: { ...defaultVitalSigns },
    rateBuffer: rateBuffer.getStats(),
    colony: recountColony(defaultAgents),
    scene: { surfaces: {} },
    currentToolCall: null,
    thoughts: [],
    isStreaming: false,
    error: null,
    voice: {
      status: 'idle',
      audioLevel: 0,
      isSpeaking: false,
      continuousListening: false,
      lastRecognizedText: null,
      ttsAudio: null,
    },

    sendUserMessage: (text: string) => {
      const trimmed = text.trim()
      if (!trimmed) return

      const userMessage: ChatMessage = {
        id: generateId(),
        role: 'user',
        content: trimmed,
        timestamp: Date.now(),
      }
      set((state) => ({
        messages: [...state.messages, userMessage],
        thoughts: [],
        isStreaming: false,
      }))
      bus.sendMessage(trimmed)
    },

    connect: () => {
      bus.connect()
    },

    disconnect: () => {
      bus.disconnect()
    },

    reconnect: (url: string) => {
      bus.setUrl(url)
      bus.connect()
    },

    updateVitalSigns: (partial: Partial<VitalSigns>) => {
      set((state) => ({
        vitalSigns: { ...state.vitalSigns, ...partial },
      }))
    },

    retryToolCall: (id: string) => {
      const state = get()
      const toolCall =
        state.currentToolCall ??
        state.messages.find((msg) => msg.toolCall?.id === id)?.toolCall
      if (!toolCall) return

      const running: ToolCall = { ...toolCall, status: 'running' }
      bus.sendAetherMessage({
        id: generateId(),
        type: 'tool_retry',
        topic: 'tool.retry',
        payload: { toolCall: running },
        timestamp: Date.now(),
        sender: 'user',
      })

      set({
        currentToolCall: running,
        messages: state.messages.map((msg) =>
          msg.toolCall?.id === id ? { ...msg, toolCall: running } : msg,
        ),
      })
    },

    clearError: () => {
      set({ error: null })
    },

    setVoiceStatus: (status: VoiceState['status']) => {
      set((state) => ({
        voice: { ...state.voice, status, isSpeaking: status === 'speaking' },
      }))
    },

    setVoiceAudioLevel: (level: number) => {
      const clamped = Math.min(1, Math.max(0, level))
      set((state) => ({ voice: { ...state.voice, audioLevel: clamped } }))
    },

    setVoiceContinuousListening: (enabled: boolean) => {
      set((state) => ({
        voice: { ...state.voice, continuousListening: enabled, status: enabled ? 'listening' : 'idle' },
      }))
    },

    clearVoiceTtsAudio: () => {
      set((state) => ({
        voice: { ...state.voice, ttsAudio: null, isSpeaking: false },
      }))
    },

    sendVoiceInput: (base64Audio: string) => {
      bus.sendAetherMessage({
        id: generateId(),
        type: 'voice_input',
        topic: 'voice.input',
        payload: { audio: base64Audio, mimeType: 'audio/webm' },
        timestamp: Date.now(),
        sender: 'user',
      })
    },
  }
})
