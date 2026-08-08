/**
 * LLM Provider 客户端封装
 *
 * 使用原生 fetch + ReadableStream 实现 OpenAI 兼容的流式 chat completions。
 * 支持 deepseek / openai / anthropic / llamacpp 四家 provider，
 * 其中 Anthropic 使用 /v1/messages endpoint 并做请求/响应格式适配。
 *
 * 该模块可在 Node.js 环境（Electron 主进程 / mock server）以及支持 fetch 的浏览器运行。
 */

import type { ChatMessage, ChatRole } from './types'

export type LlmProvider = 'deepseek' | 'openai' | 'anthropic' | 'llamacpp'

export interface LlmConfig {
  provider: LlmProvider
  /** API key，真实请求时必填 */
  apiKey: string
  /** 服务端点，例如 https://api.deepseek.com 或 http://localhost:8080/v1 */
  baseUrl?: string
  /** 模型 ID */
  model?: string
  /** 采样温度，默认 0.7 */
  temperature?: number
  /** 最大生成 token 数 */
  maxTokens?: number
  /** 是否使用真实 API（mockServer 决策用） */
  useRealApi?: boolean
}

export interface StreamChatCallbacks {
  /** 普通文本/内容块回调 */
  onChunk: (text: string) => void
  /** 错误回调 */
  onError: (err: Error) => void
  /** 思考/推理内容回调；未提供时合入 onChunk */
  onThoughtChunk?: (text: string) => void
}

const DEFAULT_BASE_URLS: Record<LlmProvider, string> = {
  deepseek: 'https://api.deepseek.com',
  openai: 'https://api.openai.com/v1',
  anthropic: 'https://api.anthropic.com',
  llamacpp: 'http://127.0.0.1:8080/v1',
}

const DEFAULT_MODELS: Record<LlmProvider, string> = {
  deepseek: 'deepseek-v4-pro',
  openai: 'gpt-5.5',
  anthropic: 'claude-sonnet-4-20250514',
  llamacpp: 'local-model',
}

function getModel(config: LlmConfig): string {
  return config.model?.trim() || DEFAULT_MODELS[config.provider]
}

function getBaseUrl(config: LlmConfig): string {
  return (config.baseUrl?.trim() || DEFAULT_BASE_URLS[config.provider]).replace(/\/+$/, '')
}

function getChatUrl(config: LlmConfig): string {
  const base = getBaseUrl(config)
  if (config.provider === 'anthropic') {
    return `${base}/v1/messages`
  }
  if (base.endsWith('/v1')) {
    return `${base}/chat/completions`
  }
  return `${base}/v1/chat/completions`
}

/**
 * 将内部 ChatMessage 转换为 OpenAI 兼容的消息格式。
 * Anthropic 会在后续步骤中进一步过滤 system 角色。
 */
function toOpenAiMessages(messages: ChatMessage[]): Array<{ role: ChatRole; content: string; name?: string }> {
  return messages.map((m) => ({
    role: m.role,
    content: m.content,
  }))
}

function isAnthropic(config: LlmConfig): boolean {
  return config.provider === 'anthropic'
}

/**
 * 构建 Anthropic /v1/messages 请求体。
 * Anthropic 不允许 messages 中出现 system 角色，需将 system 提取到顶层。
 */
function buildAnthropicBody(config: LlmConfig, messages: ChatMessage[]): Record<string, unknown> {
  const systemParts: string[] = []
  const chatMessages = messages
    .filter((m) => m.role !== 'tool')
    .map((m) => {
      if (m.role === 'system') {
        systemParts.push(m.content)
        return null
      }
      return { role: m.role === 'assistant' ? 'assistant' : 'user', content: m.content }
    })
    .filter(Boolean) as Array<{ role: 'user' | 'assistant'; content: string }>

  const body: Record<string, unknown> = {
    model: getModel(config),
    messages: chatMessages,
    stream: true,
    temperature: config.temperature ?? 0.7,
  }
  if (config.maxTokens !== undefined && config.maxTokens > 0) {
    body.max_tokens = config.maxTokens
  }
  if (systemParts.length > 0) {
    body.system = systemParts.join('\n\n')
  }
  return body
}

/**
 * 构建 OpenAI 兼容 /v1/chat/completions 请求体。
 */
function buildOpenAiBody(config: LlmConfig, messages: ChatMessage[]): Record<string, unknown> {
  const body: Record<string, unknown> = {
    model: getModel(config),
    messages: toOpenAiMessages(messages),
    stream: true,
    temperature: config.temperature ?? 0.7,
  }
  if (config.maxTokens !== undefined && config.maxTokens > 0) {
    body.max_tokens = config.maxTokens
  }
  // OpenAI 部分账号支持 stream_options.include_usage；llama.cpp 可能不支持，为避免兼容性问题仅对非本地 provider 启用
  if (config.provider !== 'llamacpp') {
    body.stream_options = { include_usage: false }
  }
  return body
}

function buildRequestBody(config: LlmConfig, messages: ChatMessage[]): Record<string, unknown> {
  return isAnthropic(config) ? buildAnthropicBody(config, messages) : buildOpenAiBody(config, messages)
}

function buildHeaders(config: LlmConfig): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (isAnthropic(config)) {
    headers['x-api-key'] = config.apiKey
    headers['anthropic-version'] = '2023-06-01'
  } else {
    headers.Authorization = `Bearer ${config.apiKey}`
  }
  return headers
}

/**
 * 测试 LLM 连接可用性。
 * 对 OpenAI 兼容接口调用 /v1/models，对 Anthropic 同样调用 /v1/models。
 * 返回 endpoint 是否可达、key 是否有效，以及可选的模型列表。
 */
export async function testConnection(
  config: LlmConfig,
): Promise<{ ok: boolean; error?: string; models?: string[] }> {
  if (!config.apiKey.trim()) {
    return { ok: false, error: 'LLM API key 为空' }
  }

  const base = getBaseUrl(config)
  const url = `${base}${base.endsWith('/v1') ? '' : '/v1'}/models`
  const headers = buildHeaders(config)
  delete headers['Content-Type']

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 10000)

  let response: Response
  try {
    response = await fetch(url, {
      method: 'GET',
      headers,
      signal: controller.signal,
    })
  } catch (err) {
    clearTimeout(timer)
    if (err instanceof Error && err.name === 'AbortError') {
      return { ok: false, error: '连接测试超时' }
    }
    return { ok: false, error: err instanceof Error ? err.message : `请求失败: ${String(err)}` }
  }
  clearTimeout(timer)

  if (!response.ok) {
    const text = await response.text().catch(() => '')
    const message = parseApiError(config.provider, text) || `HTTP ${response.status}`
    return { ok: false, error: message }
  }

  try {
    const data = (await response.json()) as { data?: Array<{ id: string }>; models?: Array<{ id: string }> }
    const list = (data.data || data.models || []).map((m) => m.id).filter(Boolean)
    return { ok: true, models: list }
  } catch {
    return { ok: true }
  }
}

/**
 * 从 OpenAI 兼容 SSE 数据对象中提取普通内容与思考内容。
 */
function extractOpenAiDelta(obj: unknown): { content?: string; thinking?: string } {
  const result: { content?: string; thinking?: string } = {}
  if (!obj || typeof obj !== 'object') return result
  const cast = obj as Record<string, unknown>

  const choices = cast.choices
  if (Array.isArray(choices) && choices.length > 0) {
    const first = choices[0] as Record<string, unknown>
    const delta = first?.delta as Record<string, unknown> | undefined
    if (delta) {
      if (typeof delta.content === 'string') {
        result.content = delta.content
      }
      if (typeof delta.reasoning_content === 'string') {
        result.thinking = delta.reasoning_content
      }
    }
  }
  return result
}

/**
 * 从 Anthropic /v1/messages SSE 数据对象中提取普通内容与思考内容。
 */
function extractAnthropicDelta(obj: unknown): { content?: string; thinking?: string } {
  const result: { content?: string; thinking?: string } = {}
  if (!obj || typeof obj !== 'object') return result
  const cast = obj as Record<string, unknown>

  const delta = cast.delta as Record<string, unknown> | undefined
  if (!delta) return result

  if (typeof delta.text === 'string') {
    result.content = delta.text
  }
  if (typeof delta.thinking === 'string') {
    result.thinking = delta.thinking
  }
  return result
}

function extractDelta(provider: LlmProvider, obj: unknown): { content?: string; thinking?: string } {
  return provider === 'anthropic' ? extractAnthropicDelta(obj) : extractOpenAiDelta(obj)
}

/**
 * 解析 API 返回的错误信息，优先读取 JSON 中的 error.message。
 */
function parseApiError(_provider: LlmProvider, body: string): string {
  try {
    const parsed = JSON.parse(body) as Record<string, unknown>
    const err = parsed.error as Record<string, unknown> | string | undefined
    if (typeof err === 'string') return err
    if (err && typeof err === 'object') {
      const msg = err.message
      if (typeof msg === 'string') return msg
      return JSON.stringify(err)
    }
    if (typeof parsed.message === 'string') return parsed.message
  } catch {
    // body 不是 JSON，直接返回原始文本
  }
  return body
}

/**
 * 流式调用 LLM。
 *
 * @param config LLM 配置
 * @param messages 对话历史
 * @param onChunk 普通文本回调
 * @param onError 错误回调
 * @param onThoughtChunk 思考内容回调（可选）
 */
export async function streamChat(
  config: LlmConfig,
  messages: ChatMessage[],
  onChunk: (text: string) => void,
  onError: (err: Error) => void,
  onThoughtChunk?: (text: string) => void,
): Promise<void> {
  if (!config.apiKey) {
    onError(new Error('LLM API key 为空'))
    return
  }

  const url = getChatUrl(config)
  const headers = buildHeaders(config)
  const body = buildRequestBody(config, messages)

  let response: Response
  try {
    response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    })
  } catch (err) {
    onError(err instanceof Error ? err : new Error(`请求 LLM 失败: ${String(err)}`))
    return
  }

  if (!response.ok) {
    const text = await response.text().catch(() => '')
    const message = parseApiError(config.provider, text) || `HTTP ${response.status}`
    onError(new Error(`LLM 请求失败: ${message}`))
    return
  }

  const reader = response.body?.getReader()
  if (!reader) {
    onError(new Error('LLM 响应没有 readable body'))
    return
  }

  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed.startsWith('data:')) continue

        const data = trimmed.slice(trimmed.indexOf(':') + 1).trim()
        if (data === '[DONE]') continue
        if (!data) continue

        let parsed: unknown
        try {
          parsed = JSON.parse(data)
        } catch {
          continue
        }

        const delta = extractDelta(config.provider, parsed)
        if (delta.content) {
          onChunk(delta.content)
        }
        if (delta.thinking) {
          if (onThoughtChunk) {
            onThoughtChunk(delta.thinking)
          } else {
            onChunk(delta.thinking)
          }
        }
      }
    }
  } catch (err) {
    onError(err instanceof Error ? err : new Error(`解析 LLM 流失败: ${String(err)}`))
  } finally {
    reader.releaseLock()
  }
}
