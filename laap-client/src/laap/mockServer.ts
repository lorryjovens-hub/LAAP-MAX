/**
 * LAAP Mock WebSocket 后端
 *
 * 用于开发测试，模拟 CognitiveBus 后端行为：
 * - 周期性发送 v12_kernel、need_*、emotion_*、harness_execution_result、scene.patch 事件
 * - 高频发送 PSI 事件供 RateBuffer 测试
 * - 接收用户消息后流式返回 chunk / thought_chunk / tool_call / tool_result
 *
 * 该模块设计为在 Node.js 环境运行（Electron 主进程或独立脚本），
 * 不会在渲染进程中直接加载。
 */

import type { AetherMessage, Agent, PSIPhase } from './types'

/**
 * 本地测试开关：设为 true 时，voice.tts 事件会携带一段 base64 编码的简短蜂鸣音。
 * 生产后端请勿启用，避免污染事件负载。
 */
const MOCK_TTS_INCLUDE_AUDIO = true

/**
 * 生成 1 秒 440Hz 正弦波 WAV 并返回 base64（用于本地 TTS 播放测试）。
 */
function generateBeepWavBase64(): string {
  const sampleRate = 8000
  const duration = 1
  const frequency = 440
  const numSamples = sampleRate * duration
  const buffer = new ArrayBuffer(44 + numSamples * 2)
  const view = new DataView(buffer)

  const writeString = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i += 1) {
      view.setUint8(offset + i, str.charCodeAt(i))
    }
  }

  writeString(0, 'RIFF')
  view.setUint32(4, 36 + numSamples * 2, true)
  writeString(8, 'WAVE')
  writeString(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true) // PCM
  view.setUint16(22, 1, true) // mono
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * 2, true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeString(36, 'data')
  view.setUint32(40, numSamples * 2, true)

  for (let i = 0; i < numSamples; i += 1) {
    const t = i / sampleRate
    const sample = Math.sin(2 * Math.PI * frequency * t) * 0.5
    const value = Math.max(-1, Math.min(1, sample))
    view.setInt16(44 + i * 2, value * 0x7fff, true)
  }

  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i += 1) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary)
}

/**
 * Mock 服务器配置
 */
export interface MockServerOptions {
  port?: number
  host?: string
  /** 高频 PSI 事件发送间隔（毫秒） */
  psiEventIntervalMs?: number
  /** 低频生命周期事件发送间隔（毫秒） */
  lifecycleIntervalMs?: number
}

/**
 * 生成唯一消息 ID
 */
function generateId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
}

/**
 * 创建 AetherMessage 的辅助函数
 */
function createMessage(
  topic: string,
  type: string,
  payload: unknown,
  sender = 'mock-backend',
): AetherMessage {
  return {
    id: generateId(),
    type,
    topic,
    payload,
    timestamp: Date.now(),
    sender,
  }
}

/**
 * PSI 阶段循环
 */
const PSI_PHASES: PSIPhase[] = ['perception', 'selection', 'integration', 'learning']

/**
 * Colony 模拟数据
 */
const colonyAgents: Agent[] = [
  { id: 'agent-1', name: 'Aris', status: 'online', role: '协调者', resource: 78 },
  { id: 'agent-2', name: 'Codex', status: 'busy', role: '代码专家', resource: 62 },
  { id: 'agent-3', name: 'Guardian', status: 'offline', role: '安全审查', resource: 0 },
  { id: 'agent-4', name: 'Nexus', status: 'online', role: '记忆检索', resource: 55 },
]

const colonyEdges = [
  { id: 'e1', from: 'agent-1', to: 'agent-2', label: '任务分派', intensity: 0.8 },
  { id: 'e2', from: 'agent-2', to: 'agent-3', label: '代码审查', intensity: 0.5 },
  { id: 'e3', from: 'agent-3', to: 'agent-1', label: '报告风险', intensity: 0.3 },
  { id: 'e4', from: 'agent-4', to: 'agent-1', label: '上下文同步', intensity: 0.6 },
]

const colonyMessageTemplates = [
  { from: 'agent-1', to: 'agent-2', summary: '请优化推理链' },
  { from: 'agent-2', to: 'agent-3', summary: '请求安全审计' },
  { from: 'agent-3', to: 'agent-1', summary: '发现潜在风险' },
  { from: 'agent-4', to: 'agent-1', summary: '已召回相关记忆' },
]

/**
 * 生成随机 Colony 消息
 */
function generateColonyMessage(tick: number): { id: string; from: string; to: string; summary: string; timestamp: number } {
  const template = colonyMessageTemplates[tick % colonyMessageTemplates.length]
  return {
    id: generateId(),
    ...template,
    summary: `${template.summary} #${tick}`,
    timestamp: Date.now(),
  }
}

/**
 * 根据 tick 构造多样化的 scene patch
 */
function buildScenePatch(tick: number): Record<string, unknown> {
  const index = (tick % 8) + 1
  switch (index) {
    case 1:
      return {
        kind: 'metric',
        label: 'CPU 占用',
        value: Math.round(20 + Math.random() * 60),
        unit: '%',
      }
    case 2:
      return {
        kind: 'text',
        content: `动态场景内容 #${tick}，由 mock server 生成。`,
      }
    case 3:
      return {
        kind: 'choice',
        content: '请选择下一步操作',
        options: ['继续对话', '执行工具', '查看场景'],
        selected: '继续对话',
      }
    case 4:
      return {
        kind: 'progress',
        label: '任务进度',
        value: Math.round(Math.random() * 100),
        max: 100,
      }
    case 5:
      return {
        kind: 'weather',
        location: '上海',
        temperature: Math.round(18 + Math.random() * 12),
        condition: tick % 2 === 0 ? '晴' : '多云',
      }
    case 6:
      return {
        kind: 'image',
        src: '/logo.svg',
        alt: 'LAAP Logo',
      }
    case 7:
      return {
        kind: 'media',
        src: '/logo.svg',
        caption: '示例媒体面片',
      }
    case 8:
      return {
        kind: 'layout',
        title: '主布局',
        children: ['surface-1', 'surface-2', 'surface-3'],
      }
    default:
      return { kind: 'text', content: `默认内容 #${tick}` }
  }
}

/**
 * 启动 Mock WebSocket 服务器。
 * 返回 close 函数，用于关闭服务器。
 */
export async function startLaapMockServer(
  options: MockServerOptions = {},
): Promise<() => void> {
  const { WebSocketServer } = await import('ws')
  const port = options.port ?? 8765
  const host = options.host ?? '127.0.0.1'
  const psiEventIntervalMs = options.psiEventIntervalMs ?? 1
  const lifecycleIntervalMs = options.lifecycleIntervalMs ?? 2500

  const wss = new WebSocketServer({ host, port })
  console.log(`[MockServer] WebSocket 监听 ws://${host}:${port}`)

  // 为每个连接的客户端维护独立的状态与定时器
  wss.on('connection', (ws) => {
    console.log('[MockServer] 客户端已连接')

    let psiPhaseIndex = 0
    let psiProgress = 0.0
    let lifecycleTick = 0

    // 高频 PSI 事件：模拟 1000-2000 Hz 的输入流
    const psiTimer = setInterval(() => {
      if (ws.readyState !== 1) return
      psiProgress += 0.05
      if (psiProgress >= 1) {
        psiProgress = 0
        psiPhaseIndex = (psiPhaseIndex + 1) % PSI_PHASES.length
      }

      const phase = PSI_PHASES[psiPhaseIndex]
      const msg = createMessage('v12_kernel', 'v12_kernel', {
        phase,
        progress: Math.min(1, psiProgress),
        frequencyHz: 1000 + Math.floor(Math.random() * 1000),
      })
      ws.send(JSON.stringify(msg))
    }, psiEventIntervalMs)

    // 低频生命周期事件：需求、情感、执行结果、场景 patch
    const lifecycleTimer = setInterval(() => {
      if (ws.readyState !== 1) return
      lifecycleTick += 1

      // need_* 事件
      const needs = ['need_curiosity', 'need_trust', 'need_competence']
      const needTopic = needs[lifecycleTick % needs.length]
      ws.send(
        JSON.stringify(
          createMessage(needTopic, 'need_update', {
            value: 0.3 + Math.random() * 0.6,
            delta: (Math.random() - 0.5) * 0.1,
          }),
        ),
      )

      // emotion_* 5D 情感
      const emotions = ['emotion_pleasure', 'emotion_arousal', 'emotion_dominance', 'emotion_sociality', 'emotion_stress']
      emotions.forEach((emotion) => {
        ws.send(
          JSON.stringify(
            createMessage(emotion, 'emotion_update', {
              value: Math.random(),
            }),
          ),
        )
      })

      // harness_execution_result
      if (lifecycleTick % 3 === 0) {
        ws.send(
          JSON.stringify(
            createMessage('harness_execution_result', 'harness_execution_result', {
              success: Math.random() > 0.2,
              durationMs: 120 + Math.floor(Math.random() * 400),
              output: `mock-execution-${lifecycleTick}`,
            }),
          ),
        )
      }

      // scene.patch：周期性更新多种类型的 surface
      const surfaceId = `surface-${(lifecycleTick % 8) + 1}`
      const patch = buildScenePatch(lifecycleTick)
      ws.send(
        JSON.stringify(
          createMessage('scene.patch', 'scene_patch', {
            surfaceId,
            patch,
          }),
        ),
      )

      // colony.agent：周期性更新 Colony 状态与消息流
      colonyAgents.forEach((agent) => {
        if (Math.random() > 0.7) {
          const statuses: Agent['status'][] = ['online', 'busy', 'offline']
          agent.status = statuses[Math.floor(Math.random() * statuses.length)]
        }
        agent.resource = Math.min(100, Math.max(0, (agent.resource ?? 50) + Math.round((Math.random() - 0.5) * 10)))
      })
      ws.send(
        JSON.stringify(
          createMessage('colony.agent', 'colony_update', {
            agents: colonyAgents.map((a) => ({ ...a })),
            edges: colonyEdges.map((e) => ({ ...e })),
            messages: [generateColonyMessage(lifecycleTick)],
          }),
        ),
      )
    }, lifecycleIntervalMs)

    // 处理客户端消息
    ws.on('message', (rawData) => {
      const data = Buffer.isBuffer(rawData) ? rawData.toString('utf-8') : String(rawData)
      let message: AetherMessage
      try {
        message = JSON.parse(data) as AetherMessage
      } catch {
        console.warn('[MockServer] 收到非 JSON 消息:', data.slice(0, 200))
        return
      }

      console.log('[MockServer] 收到消息:', message.topic)

      if (message.topic === 'ping') {
        ws.send(JSON.stringify(createMessage('pong', 'pong', { timestamp: message.timestamp })))
        return
      }

      if (message.topic === 'tool.retry') {
        const payload = message.payload as { toolCall?: { id?: string; name?: string; arguments?: Record<string, unknown> } } | undefined
        const toolCall = payload?.toolCall
        if (toolCall) {
          ws.send(
            JSON.stringify(
              createMessage('tool_call', 'tool_call', {
                toolCall: {
                  id: toolCall.id ?? generateId(),
                  name: toolCall.name ?? 'mock_search',
                  arguments: toolCall.arguments ?? {},
                  status: 'running',
                },
              }),
            ),
          )
          setTimeout(() => {
            ws.send(
              JSON.stringify(
                createMessage('tool_result', 'tool_result', {
                  toolCall: {
                    id: toolCall.id ?? generateId(),
                    name: toolCall.name ?? 'mock_search',
                    arguments: toolCall.arguments ?? {},
                    status: 'success',
                    result: { found: true, summary: '重新执行后的模拟结果' },
                  },
                }),
              ),
            )
          }, 300)
        }
        return
      }

      if (message.topic === 'user.input') {
        const text = (message.payload as { text?: string }).text ?? ''
        streamReply(ws, text)
      }

      if (message.topic === 'voice.input') {
        handleVoiceInput(ws, message)
      }
    })

    ws.on('close', () => {
      console.log('[MockServer] 客户端已断开')
      clearInterval(psiTimer)
      clearInterval(lifecycleTimer)
    })
  })

  return () => {
    wss.clients.forEach((client) => {
      client.terminate()
    })
    wss.close()
    console.log('[MockServer] 已关闭')
  }
}

/**
 * 模拟语音输入处理：返回识别文本与 TTS 事件
 */
function handleVoiceInput(ws: import('ws').WebSocket, message: AetherMessage): void {
  const audio = (message.payload as { audio?: string }).audio ?? ''
  const length = Math.min(audio.length, 120)
  const mockText = `收到语音输入（长度 ${length}），这是模拟识别结果。`

  setTimeout(() => {
    if (ws.readyState !== 1) return
    ws.send(
      JSON.stringify(
        createMessage('voice.recognized', 'voice_recognized', {
          text: mockText,
          confidence: 0.85,
        }),
      ),
    )

    setTimeout(() => {
      if (ws.readyState !== 1) return
      const ttsPayload: Record<string, unknown> = {
        speaking: true,
        text: '好的，已收到您的语音指令。',
      }
      if (MOCK_TTS_INCLUDE_AUDIO) {
        ttsPayload.audioBase64 = generateBeepWavBase64()
        ttsPayload.mimeType = 'audio/wav'
      }
      ws.send(JSON.stringify(createMessage('voice.tts', 'voice_tts', ttsPayload)))
    }, 400)
  }, 300)
}

/**
 * 模拟流式回复：延迟 500ms 后依次发送 chunk、thought_chunk、
 * tool_call、tool_result，最后发送 harness_execution_result。
 */
function streamReply(ws: import('ws').WebSocket, userText: string): void {
  const replyId = generateId()

  setTimeout(() => {
    if (ws.readyState !== 1) return

    ws.send(
      JSON.stringify(
        createMessage('chunk', 'stream_chunk', {
          replyId,
          text: `收到消息：${userText}\n`,
        }),
      ),
    )

    setTimeout(() => {
      ws.send(
        JSON.stringify(
          createMessage('thought_chunk', 'thought_chunk', {
            replyId,
            text: '正在分析用户意图...',
            type: 'reasoning',
            confidence: 0.92,
          }),
        ),
      )

      setTimeout(() => {
        const toolId = generateId()
        ws.send(
          JSON.stringify(
            createMessage('tool_call', 'tool_call', {
              replyId,
              toolCall: {
                id: toolId,
                name: 'mock_search',
                arguments: { query: userText.slice(0, 20) },
                status: 'running',
              },
            }),
          ),
        )

        setTimeout(() => {
          ws.send(
            JSON.stringify(
              createMessage('tool_result', 'tool_result', {
                replyId,
                toolCall: {
                  id: toolId,
                  name: 'mock_search',
                  arguments: { query: userText.slice(0, 20) },
                  status: 'success',
                  result: { found: true, summary: '模拟检索结果' },
                },
              }),
            ),
          )

          setTimeout(() => {
            ws.send(
              JSON.stringify(
                createMessage(
                  'harness_execution_result',
                  'harness_execution_result',
                  {
                    replyId,
                    success: true,
                    durationMs: 560,
                    output: '流式回复完成',
                  },
                ),
              ),
            )
          }, 120)
        }, 200)
      }, 180)
    }, 160)
  }, 500)
}
