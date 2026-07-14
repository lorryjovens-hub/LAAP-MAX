/**
 * LAAP 核心类型定义
 * 包含 AetherMessage、生命体征、PSI 周期、Agent、场景面片、工具调用等。
 */

/** Aether 消息主题前缀与类型常量 */
export const QRE_PREFIX = 'qre_'
export const V12_KERNEL = 'v12_kernel'
export const NEED_PREFIX = 'need_'
export const EMOTION_PREFIX = 'emotion_'
export const HARNESS_EXECUTION_RESULT = 'harness_execution_result'
export const SCENE = 'scene'
export const SCENE_PATCH = 'scene.patch'

/** PSI 处理阶段 */
export type PSIPhase = 'perception' | 'selection' | 'integration' | 'learning'

/** Aether 消息结构，CognitiveBus 中传递的基本单元 */
export interface AetherMessage {
  id: string
  type: string
  topic: string
  payload: unknown
  timestamp: number
  sender: string
  vectorClock?: Record<string, number>
}

/** PSI 周期状态 */
export interface PSICycle {
  phase: PSIPhase
  progress: number
}

/** 生命体征：需求与 5D 情感维度 */
export interface VitalSigns {
  curiosity: number
  trust: number
  competence: number
  pleasure: number
  arousal: number
  dominance: number
  sociality: number
  stress: number
}

/** Agent 在线状态 */
export type AgentStatus = 'online' | 'busy' | 'offline'

/** Agent 实体 */
export interface Agent {
  id: string
  name: string
  status: AgentStatus
  role?: string
  avatar?: string
  /** 资源水平，0-100 */
  resource?: number
}

/** Colony 协作关系边 */
export interface ColonyEdge {
  id: string
  from: string
  to: string
  label?: string
  intensity?: number
}

/** Colony 最近消息摘要 */
export interface ColonyMessage {
  id: string
  from: string
  to: string
  summary: string
  timestamp: number
}

/** 语音交互状态 */
export type VoiceStatus = 'idle' | 'listening' | 'thinking' | 'speaking'

/** 思维流条目 */
export interface Thought {
  id: string
  content: string
  type: 'reasoning' | 'reflection' | 'bias'
  confidence?: number
  alert?: string
  timestamp: number
}

/** 场景面片（surface） */
export interface SceneSurface {
  id: string
  kind: string
  content?: string
  value?: number
  max?: number
  unit?: string
  src?: string
  alt?: string
  caption?: string
  options?: string[]
  selected?: string
  label?: string
  title?: string
  location?: string
  temperature?: number
  condition?: string
  children?: string[]
  metadata?: Record<string, unknown>
  updatedAt: number
}

/** 工具调用状态 */
export type ToolCallStatus = 'pending' | 'running' | 'success' | 'error'

/** 工具调用描述 */
export interface ToolCall {
  id: string
  name: string
  arguments: Record<string, unknown>
  status: ToolCallStatus
  result?: unknown
}

/** 聊天消息角色 */
export type ChatRole = 'user' | 'assistant' | 'system' | 'tool'

/** 聊天消息 */
export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  toolCall?: ToolCall
  timestamp: number
}

/** RateBuffer 输出统计 */
export interface RateBufferStats {
  dedupCount: number
  queueDepth: number
  batchSize: number
  aggregationWindowMs: number
}

/** RateBuffer 聚合事件 */
export interface RateBufferBatch {
  timestamp: number
  events: AetherMessage[]
  stats: RateBufferStats
}

/** CognitiveBus 连接状态 */
export type ConnectionStatus = 'connecting' | 'open' | 'closed' | 'error'

/** Colony 聚合状态 */
export interface ColonyState {
  agents: Agent[]
  onlineCount: number
  busyCount: number
  offlineCount: number
  edges: ColonyEdge[]
  messages: ColonyMessage[]
}

/** TTS 音频来源 */
export interface TtsAudioSource {
  /** Base64 编码的音频数据（如 MP3/WAV） */
  audioBase64?: string
  /** 可播放音频 URL */
  audioUrl?: string
  /** Base64 音频 MIME 类型，默认 audio/wav */
  mimeType?: string
}

/** 语音交互状态切片 */
export interface VoiceState {
  status: VoiceStatus
  /** 当前麦克风音频电平，0-1 */
  audioLevel: number
  /** 是否正在播放 TTS */
  isSpeaking: boolean
  /** 是否启用连续监听 */
  continuousListening: boolean
  /** 最近一次识别文本 */
  lastRecognizedText: string | null
  /** 当前待播放的 TTS 音频（由 voice.tts 事件携带） */
  ttsAudio: TtsAudioSource | null
}

/** 场景状态 */
export interface SceneState {
  surfaces: Record<string, SceneSurface>
}
