import { create } from 'zustand'
import { CognitiveBusClient } from '../laap/bus'
import { CognitiveEngine } from '../laap/engine'
import { sceneStore, type Surface } from '../laap/scene'
import { focusStack } from '../laap/memory'
import { RateBuffer } from '../laap/rateBuffer'
import { toolPolicy, estimateToolRisk } from '../laap/tool-policy'
import { useSettingsStore, type ProviderCredential } from './settingsStore'
import type {
  ConnectionStatus,
  PSIPhase,
  VitalSigns,
  Agent,
  ColonyState,
  ColonyMessage,
  SceneState,
  SceneSurface,
  ToolCall,
  Thought,
  VoiceState,
  TerminalSession,
  ShellOutput,
  RateBufferStats,
  ChatMessage,
  ChatSession,
  TtsAudioSource,
} from '../laap/types'
function resolveBackendUrl(): string {
  return (import.meta.env.VITE_BACKEND_URL as string)?.trim() || 'ws://127.0.0.1:8763'
}

function generateId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
}

function parsePSIPhase(value: unknown): PSIPhase {
  const phases: PSIPhase[] = ['perception', 'selection', 'integration', 'learning']
  return typeof value === 'string' && phases.includes(value as PSIPhase) ? value as PSIPhase : 'perception'
}

const defaultVitalSigns: VitalSigns = { curiosity: 0.5, trust: 0.5, competence: 0.5, pleasure: 0.5, arousal: 0.5, dominance: 0.5, sociality: 0.5, stress: 0.2 }
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

export interface ToolConfirmation {
  id: string
  toolCall: ToolCall
  reason: string
  ruleId?: string
  createdAt: number
}

export interface LaapState {
  connectionStatus: ConnectionStatus; messages: ChatMessage[]
  psiCycle: { phase: PSIPhase; progress: number }; vitalSigns: VitalSigns
  rateBuffer: RateBufferStats; colony: ColonyState; scene: SceneState
  currentToolCall: ToolCall | null; thoughts: Thought[]; isStreaming: boolean; error: string | null
  voice: VoiceState
  terminalSessions: TerminalSession[]
  // Cognitive Engine integration
  engine: CognitiveEngine
  focusFrames: ReturnType<typeof focusStack.getFrames>
  surfaces: Surface[]
  contextDiagnostics: { sectionsInput: number; sectionsDropped: number; durationMs: number } | null
  // Tool confirmations
  pendingToolConfirmations: ToolConfirmation[]
  // Sessions
  sessions: ChatSession[]
  activeSessionId: string | null
  sessionMessages: Record<string, ChatMessage[]>
  // Actions
  sendUserMessage: (text: string) => void; connect: () => void; disconnect: () => void; reconnect: (url: string) => void
  newSession: () => void; selectSession: (id: string) => void; deleteSession: (id: string) => void
  updateVitalSigns: (partial: Partial<VitalSigns>) => void; retryToolCall: (id: string) => void
  confirmToolCall: (id: string) => void; rejectToolCall: (id: string) => void
  clearError: () => void; setVoiceStatus: (status: VoiceState['status']) => void
  setVoiceAudioLevel: (level: number) => void; setVoiceContinuousListening: (enabled: boolean) => void
  sendVoiceInput: (base64Audio: string, mimeType: string) => void; clearVoiceTtsAudio: () => void
  setVoiceTtsAudio: (source: TtsAudioSource) => void
  runShellCommand: (id: string, command: string, cwd?: string) => void
  abortShellCommand: (id: string) => void
  clearTerminal: () => void
  // Engine actions
  createDemoScene: () => void
  sendSceneIntent: (surfaceId: string, name: string, data: unknown) => void
}

let cognitiveBusInstance: CognitiveBusClient | null = null

export function getCognitiveBus(): CognitiveBusClient {
  if (!cognitiveBusInstance) cognitiveBusInstance = new CognitiveBusClient({ url: resolveBackendUrl() })
  return cognitiveBusInstance
}

function getLLMConfigFromSettings(): { provider: string; apiKey: string; model: string } {
  try {
    const st = useSettingsStore.getState()
    const { provider, model, creds = {} } = st.llm
    const keyField = provider + 'Key'
    const apiKey = (creds as Record<string, string>)[keyField] || ''
    return { provider: provider || 'deepseek', apiKey, model: model || 'deepseek-chat' }
  } catch {
    return { provider: 'deepseek', apiKey: '', model: 'deepseek-v4-pro' }
  }
}

function providerCredentialToPayload(cfg: ProviderCredential): Record<string, unknown> {
  return {
    provider: cfg.provider,
    model: cfg.model,
    baseUrl: cfg.baseUrl,
    creds: cfg.creds,
  }
}

function getVoiceConfigFromSettings(): { asr: Record<string, unknown>; tts: Record<string, unknown> } {
  try {
    const st = useSettingsStore.getState()
    return {
      asr: providerCredentialToPayload(st.asr),
      tts: providerCredentialToPayload(st.tts),
    }
  } catch {
    return { asr: {}, tts: {} }
  }
}

export const useLaapStore = create<LaapState>((set, get) => {
  let streamingMessageId: string | null = null
  const bus = getCognitiveBus()
  const engine = new CognitiveEngine(bus, { agentName: 'Aris' })

  // Sync scene store to surfaces state
  sceneStore.onScene((scene) => {
    set({ surfaces: scene.surfaces })
  })

  // Sync focus stack to focusFrames state
  focusStack.onEvent(() => {
    set({ focusFrames: focusStack.getFrames() })
  })

  engine.start()
  cognitiveBusInstance = bus
  const rateBuffer = new RateBuffer()

  if (typeof window !== 'undefined' && window.shell?.onData) {
    window.shell.onData((data: ShellOutput & { id: string }) => {
      set((state) => {
        const index = state.terminalSessions.findIndex((s) => s.id === data.id)
        if (index === -1) return {}
        const sessions = [...state.terminalSessions]
        const session = sessions[index]
        const stdout = data.stdout !== undefined ? session.stdout + data.stdout : session.stdout
        const stderr = data.stderr !== undefined ? session.stderr + data.stderr : session.stderr
        const exitCode = data.exitCode !== undefined ? data.exitCode : session.exitCode
        let status = session.status
        if (data.exitCode !== undefined) {
          status = data.exitCode === 0 ? 'success' : 'error'
        }
        sessions[index] = { ...session, stdout, stderr, exitCode, status, updatedAt: Date.now() }
        return { terminalSessions: sessions }
      })
    })
  }

  bus.onStatusChange((status, error) => set({ connectionStatus: status, error: error ?? null }))

  bus.subscribe('v12_kernel', (message) => {
    rateBuffer.push(message)
    const p = message.payload as { phase?: unknown; progress?: number } | undefined
    set({ psiCycle: { phase: parsePSIPhase(p?.phase), progress: p?.progress ?? 0 } })
  })

  ;['need_curiosity','need_trust','need_competence'].forEach((topic) => {
    const key = topic.replace('need_', '') as keyof VitalSigns
    bus.subscribe(topic, (message) => {
      rateBuffer.push(message)
      const v = (message.payload as { value?: number } | undefined)?.value
      if (typeof v === 'number') set((s) => ({ vitalSigns: { ...s.vitalSigns, [key]: Math.min(1, Math.max(0, v)) } }))
    })
  })

  ;['emotion_pleasure','emotion_arousal','emotion_dominance','emotion_sociality','emotion_stress'].forEach((topic) => {
    const key = topic.replace('emotion_', '') as keyof VitalSigns
    bus.subscribe(topic, (message) => {
      rateBuffer.push(message)
      const v = (message.payload as { value?: number } | undefined)?.value
      if (typeof v === 'number') set((s) => ({ vitalSigns: { ...s.vitalSigns, [key]: Math.min(1, Math.max(0, v)) } }))
    })
  })

  bus.subscribe('harness_execution_result', (message) => {
    rateBuffer.push(message)
    const p = message.payload as { success?: boolean; durationMs?: number; replyId?: string } | undefined
    if (streamingMessageId && p?.replyId) {
      set((state) => ({
        isStreaming: false,
        messages: state.messages.map((msg) =>
          msg.id === streamingMessageId ? { ...msg, content: `${msg.content}\n\n[执行${p.success ? '成功' : '失败'}，${p.durationMs ?? 0}ms]` } : msg
        ),
      }))
      streamingMessageId = null
    }
  })

  bus.subscribe('qre_*', (message) => {
    rateBuffer.push(message)
    const text = (message.payload as { insight?: string } | undefined)?.insight || ''
    if (!text) return
    set((state) => ({ thoughts: [...state.thoughts, { id: generateId(), content: text, type: 'reasoning', timestamp: message.timestamp }] }))
  })

  bus.subscribe('scene', (message) => {
    rateBuffer.push(message)
    const surfaces = (message.payload as { surfaces?: Record<string, SceneSurface> } | undefined)?.surfaces
    if (!surfaces) return
    set({ scene: { surfaces } })
  })

  bus.subscribe('scene.patch', (message) => {
    rateBuffer.push(message)
    const p = message.payload as { surfaceId?: string; patch?: Partial<SceneSurface> } | undefined
    if (!p?.surfaceId) return
    set((state) => {
      const existing = state.scene.surfaces[p.surfaceId!]
      return { scene: { surfaces: { ...state.scene.surfaces, [p.surfaceId!]: { ...(existing ?? { id: p.surfaceId!, kind: 'text' as const, content: '', updatedAt: message.timestamp }), ...p.patch, id: p.surfaceId!, updatedAt: message.timestamp } } } }
    })
  })

  bus.subscribe('chunk', (message) => {
    const text = (message.payload as { text?: string; replyId?: string } | undefined)?.text || ''
    set((state) => {
      if (streamingMessageId) {
        return { messages: state.messages.map((msg) => msg.id === streamingMessageId ? { ...msg, content: msg.content + text } : msg) }
      }
      const id = generateId()
      streamingMessageId = id
      return { isStreaming: true, messages: [...state.messages, { id, role: 'assistant', content: text, timestamp: message.timestamp }] }
    })
  })

  bus.subscribe('thought_chunk', (message) => {
    const p = message.payload as { text?: string; type?: string; confidence?: number } | undefined
    const text = p?.text || ''
    if (!text) return
    set((state) => ({
      thoughts: [...state.thoughts, { id: generateId(), content: text, type: (['reasoning','reflection','bias'] as const).includes(p?.type as any) ? p!.type as 'reasoning'|'reflection'|'bias' : 'reasoning', confidence: p?.confidence, timestamp: message.timestamp }]
    }))
  })

  bus.subscribe('tool_call', (message) => {
    const toolCall = (message.payload as { toolCall?: ToolCall } | undefined)?.toolCall
    if (!toolCall) return

    // 评估工具调用策略
    const riskScore = estimateToolRisk(toolCall.name, toolCall.arguments)
    const decision = toolPolicy.evaluate({
      toolName: toolCall.name,
      args: toolCall.arguments,
      caller: 'agent',
      riskScore,
    })

    if (decision.action === 'confirm') {
      set((state) => ({
        currentToolCall: { ...toolCall, status: 'pending' },
        pendingToolConfirmations: [
          ...state.pendingToolConfirmations,
          {
            id: toolCall.id,
            toolCall,
            reason: decision.reason,
            ruleId: decision.ruleId,
            createdAt: Date.now(),
          },
        ],
      }))
      return
    }

    if (decision.action === 'deny') {
      set((state) => ({
        currentToolCall: { ...toolCall, status: 'error', result: { error: decision.reason } },
        messages: streamingMessageId
          ? state.messages.map((msg) => msg.id === streamingMessageId ? { ...msg, toolCall: { ...toolCall, status: 'error', result: { error: decision.reason } } } : msg)
          : state.messages,
      }))
      return
    }

    set({ currentToolCall: toolCall })
    if (!streamingMessageId) return
    set((state) => ({ messages: state.messages.map((msg) => msg.id === streamingMessageId ? { ...msg, toolCall } : msg) }))
  })

  bus.subscribe('tool_result', (message) => {
    const toolCall = (message.payload as { toolCall?: ToolCall } | undefined)?.toolCall
    if (!toolCall) return
    set({ currentToolCall: toolCall })
  })

  rateBuffer.onBatch(() => set({ rateBuffer: rateBuffer.getStats() }))
  rateBuffer.start()

  bus.subscribe('colony.agent', (message) => {
    rateBuffer.push(message)
    const p = message.payload as { agents?: Agent[]; edges?: ColonyState['edges']; messages?: ColonyMessage[] } | undefined
    set((state) => ({ colony: recount(p?.agents ?? state.colony.agents, p?.edges ?? state.colony.edges, p?.messages ?? state.colony.messages) }))
  })

  bus.subscribe('voice.recognized', (message) => {
    rateBuffer.push(message)
    const text = (message.payload as { text?: string } | undefined)?.text
    if (text) set((state) => ({ voice: { ...state.voice, status: 'thinking' as const, lastRecognizedText: text } }))
  })

  bus.subscribe('voice.tts', (message) => {
    rateBuffer.push(message)
    const p = message.payload as { speaking?: boolean; text?: string; audioBase64?: string; audioUrl?: string; mimeType?: string } | undefined
    const source: TtsAudioSource = { audioBase64: p?.audioBase64, audioUrl: p?.audioUrl, mimeType: p?.mimeType }
    if (source.audioBase64 || source.audioUrl) {
      set((state) => ({ voice: { ...state.voice, ttsAudio: source } }))
      return
    }
    // 文本型 TTS 请求：仅有 text 无音频数据，标记为待合成文本，由前端 Microsoft TTS 或其他客户端 TTS 接管
    if (p?.text) {
      set((state) => ({ voice: { ...state.voice, lastRecognizedText: p.text ?? null, ttsAudio: null } }))
    }
  })

  bus.subscribe('audio.stream', (message) => {
    const p = message.payload as { audioBase64?: string; audioUrl?: string; mimeType?: string } | undefined
    const source: TtsAudioSource = { audioBase64: p?.audioBase64, audioUrl: p?.audioUrl, mimeType: p?.mimeType }
    if (!source.audioBase64 && !source.audioUrl) return
    set((state) => ({ voice: { ...state.voice, ttsAudio: source } }))
  })

  function recount(agents: Agent[], edges: ColonyState['edges'] = defaultColonyEdges, messages: ColonyMessage[] = []): ColonyState {
    return { agents, onlineCount: agents.filter((a) => a.status === 'online').length, busyCount: agents.filter((a) => a.status === 'busy').length, offlineCount: agents.filter((a) => a.status === 'offline').length, edges, messages: messages.slice(-5) }
  }

  return {
    connectionStatus: 'closed', messages: [], psiCycle: { phase: 'perception' as PSIPhase, progress: 0 },
    vitalSigns: { ...defaultVitalSigns }, rateBuffer: rateBuffer.getStats(),
    colony: recount(defaultAgents), scene: { surfaces: {} }, currentToolCall: null, thoughts: [],
    isStreaming: false, error: null,
    voice: { status: 'idle' as const, isSpeaking: false, audioLevel: 0, continuousListening: false, lastRecognizedText: null, ttsAudio: null },
    terminalSessions: [],
    sessions: [],
    activeSessionId: null,
    sessionMessages: {},
    pendingToolConfirmations: [],
    // Engine state
    engine,
    focusFrames: focusStack.getFrames(),
    surfaces: sceneStore.getScene().surfaces,
    contextDiagnostics: null,

    sendUserMessage: async (text: string) => {
      const id = generateId()
      const userMessage: ChatMessage = { id, role: 'user', content: text, timestamp: Date.now() }
      set((state) => ({ messages: [...state.messages, userMessage] }))
      // 更新会话消息计数
      set((state) => ({
        sessions: state.sessions.map((s) =>
          s.id === state.activeSessionId ? { ...s, messageCount: state.messages.length + 1, updatedAt: Date.now() } : s
        ),
      }))

      // 引擎模式：意识引擎（daemon 0-token优先） vs 直连后端
      const st = useSettingsStore.getState()
      if (st.engineMode === 'consciousness') {
        // 走 daemon 意识 Actor（0-token 优先：缓存→记忆→规则→LLM）
        const cUrl = st.consciousnessUrl || 'http://127.0.0.1:19420'
        const replyId = generateId()
        try {
          const resp = await fetch(`${cUrl}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, session_id: 'client' }),
          })
          const data = await resp.json()
          const reply = data.reply || (data.error ? `[意识引擎] ${data.error}` : '(无响应)')
          const assistantMsg: ChatMessage = {
            id: replyId, role: 'assistant', content: reply, timestamp: Date.now(),
          }
          set((s) => ({ messages: [...s.messages, assistantMsg] }))
        } catch (e) {
          const errMsg = `[意识引擎] 连接失败: ${e instanceof Error ? e.message : e}`
          set((s) => ({ messages: [...s.messages, { id: replyId, role: 'assistant', content: errMsg, timestamp: Date.now() }] }))
        }
        return
      }

      // 直连后端模式
      const llmConfig = getLLMConfigFromSettings()
      bus.sendAetherMessage({
        id, type: 'user_message', topic: 'user.input',
        payload: { text, llmConfig }, timestamp: Date.now(), sender: 'user',
      })
    },
    connect: () => bus.connect(),
    disconnect: () => bus.disconnect(),
    reconnect: (url: string) => {
      bus.setUrl(url)
      bus.connect()
    },
    newSession: () => {
      const id = generateId()
      const now = Date.now()
      const session: ChatSession = { id, title: `新会话 ${new Date().toLocaleTimeString()}`, updatedAt: now, messageCount: 0 }
      set((state) => ({
        sessions: [...state.sessions, session],
        activeSessionId: id,
        // 保存当前会话消息
        sessionMessages: { ...state.sessionMessages, [state.activeSessionId || '']: state.messages },
        messages: [],
      }))
    },
    selectSession: (id: string) => {
      const state = get()
      // 保存当前会话消息
      const updated = state.sessions.map((s) =>
        s.id === state.activeSessionId ? { ...s, messageCount: state.messages.length, updatedAt: Date.now() } : s
      )
      // 恢复目标会话消息
      const targetMessages = state.sessionMessages[id] || []
      set({
        sessions: updated,
        activeSessionId: id,
        sessionMessages: state.activeSessionId ? { ...state.sessionMessages, [state.activeSessionId]: state.messages } : state.sessionMessages,
        messages: targetMessages,
      })
    },
    deleteSession: (id: string) => {
      set((state) => ({
        sessions: state.sessions.filter((s) => s.id !== id),
        activeSessionId: state.activeSessionId === id ? null : state.activeSessionId,
        messages: state.activeSessionId === id ? [] : state.messages,
        sessionMessages: Object.fromEntries(
          Object.entries(state.sessionMessages).filter(([k]) => k !== id)
        ),
      }))
    },
    updateVitalSigns: (partial) => set((state) => ({ vitalSigns: { ...state.vitalSigns, ...partial } })),
    retryToolCall: (id) => {
      const state = get()
      const toolCall = state.currentToolCall ?? state.messages.find((msg) => msg.toolCall?.id === id)?.toolCall
      if (!toolCall) return
      bus.sendAetherMessage({ id: generateId(), type: 'tool_retry', topic: 'tool.retry', payload: { toolCall }, timestamp: Date.now(), sender: 'user' })
      set({ currentToolCall: toolCall, messages: state.messages.map((msg) => msg.toolCall?.id === id ? { ...msg, toolCall } : msg) })
    },
    confirmToolCall: (id) => {
      const state = get()
      const confirmation = state.pendingToolConfirmations.find((c) => c.id === id)
      if (!confirmation) return
      const toolCall = { ...confirmation.toolCall, status: 'running' as const }
      bus.sendAetherMessage({ id: generateId(), type: 'tool_confirm', topic: 'tool.confirm', payload: { toolCall }, timestamp: Date.now(), sender: 'user' })
      set({
        currentToolCall: toolCall,
        pendingToolConfirmations: state.pendingToolConfirmations.filter((c) => c.id !== id),
        messages: streamingMessageId
          ? state.messages.map((msg) => msg.id === streamingMessageId ? { ...msg, toolCall } : msg)
          : state.messages,
      })
    },
    rejectToolCall: (id) => {
      const state = get()
      const confirmation = state.pendingToolConfirmations.find((c) => c.id === id)
      if (!confirmation) return
      const toolCall = { ...confirmation.toolCall, status: 'error' as const, result: { error: '用户已拒绝执行该工具调用' } }
      bus.sendAetherMessage({ id: generateId(), type: 'tool_reject', topic: 'tool.reject', payload: { toolCall, reason: confirmation.reason }, timestamp: Date.now(), sender: 'user' })
      set({
        currentToolCall: toolCall,
        pendingToolConfirmations: state.pendingToolConfirmations.filter((c) => c.id !== id),
        messages: streamingMessageId
          ? state.messages.map((msg) => msg.id === streamingMessageId ? { ...msg, toolCall } : msg)
          : state.messages,
      })
    },
    clearError: () => set({ error: null }),
    setVoiceStatus: (status) => set((state) => ({ voice: { ...state.voice, status, isSpeaking: status === 'speaking' } })),
    setVoiceAudioLevel: (level) => set((state) => ({ voice: { ...state.voice, audioLevel: Math.min(1, Math.max(0, level)) } })),
    setVoiceContinuousListening: (enabled) => set((state) => ({ voice: { ...state.voice, continuousListening: enabled } })),
    sendVoiceInput: (base64Audio, mimeType) => {
      const voiceCfg = getVoiceConfigFromSettings()
      const llmCfg = getLLMConfigFromSettings()
      bus.sendAetherMessage({
        id: generateId(), type: 'voice_input', topic: 'voice.input',
        payload: {
          audio: base64Audio,
          mimeType,
          asr: voiceCfg.asr,
          tts: voiceCfg.tts,
          llm: llmCfg,
        },
        timestamp: Date.now(), sender: 'user',
      })
    },
    clearVoiceTtsAudio: () => set((state) => ({ voice: { ...state.voice, ttsAudio: null } })),
    setVoiceTtsAudio: (source: TtsAudioSource) => set((state) => ({ voice: { ...state.voice, ttsAudio: source } })),
    runShellCommand: (id: string, command: string, cwd?: string) => {
      const session: TerminalSession = {
        id, command, cwd,
        stdout: '', stderr: '', exitCode: null,
        status: 'running', createdAt: Date.now(), updatedAt: Date.now(),
      }
      set((state) => ({ terminalSessions: [...state.terminalSessions, session] }))
      window.shell?.execute(id, command, cwd)
    },
    abortShellCommand: (id: string) => {
      window.shell?.abort(id)
      set((state) => {
        const index = state.terminalSessions.findIndex((s) => s.id === id && s.status === 'running')
        if (index === -1) return {}
        const sessions = [...state.terminalSessions]
        const session = sessions[index]
        sessions[index] = {
          ...session,
          status: 'error',
          stderr: session.stderr ? `${session.stderr}\n[已中止]` : '[已中止]',
          exitCode: null,
          updatedAt: Date.now(),
        }
        return { terminalSessions: sessions }
      })
    },
    clearTerminal: () => set({ terminalSessions: [] }),
    // Engine actions
    createDemoScene: () => engine.createDemoSurfaces(),
    sendSceneIntent: (surfaceId, name, data) => engine.sendIntent(surfaceId, name, data),
  }
})
