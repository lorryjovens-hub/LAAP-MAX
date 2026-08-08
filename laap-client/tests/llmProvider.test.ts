/**
 * LLM Provider 单元测试
 *
 * 验证 streamChat 的 SSE 解析、testConnection 的状态处理，
 * 以及 deepseek / openai / anthropic / llamacpp 四家 provider 的请求体差异。
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { streamChat, testConnection, type LlmConfig, type LlmProvider } from '../src/laap/llm'
import type { ChatMessage } from '../src/laap/types'

const PROVIDERS: LlmProvider[] = ['deepseek', 'openai', 'anthropic', 'llamacpp']

function sseEvent(obj: unknown): string {
  return `data: ${JSON.stringify(obj)}\n\n`
}

function makeReader(chunks: string[]) {
  let index = 0
  return {
    read: async () => {
      if (index >= chunks.length) return { done: true, value: undefined }
      const chunk = chunks[index++]
      const encoder = new TextEncoder()
      return { done: false, value: encoder.encode(chunk) }
    },
    releaseLock: () => {},
  }
}

function mockFetchResponse(chunks: string[], status = 200) {
  return {
    ok: status === 200,
    status,
    text: async () => 'error',
    body: {
      getReader: () => makeReader(chunks),
    },
  } as unknown as Response
}

describe('streamChat', () => {
  beforeEach(() => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() =>
      Promise.resolve(mockFetchResponse([])),
    )
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('解析 SSE 流并调用 onChunk', async () => {
    const fetchMock = vi.mocked(globalThis.fetch)
    const config: LlmConfig = { provider: 'deepseek', apiKey: 'sk-test' }
    const messages: ChatMessage[] = [{ id: '1', role: 'user', content: '你好', timestamp: 1 }]
    const chunks: string[] = [
      sseEvent({ choices: [{ delta: { content: '你好' } }] }),
      sseEvent({ choices: [{ delta: { content: '！' } }] }),
      'data: [DONE]\n\n',
    ]
    fetchMock.mockResolvedValueOnce(mockFetchResponse(chunks))

    const onChunk = vi.fn()
    const onError = vi.fn()

    await streamChat(config, messages, onChunk, onError)

    expect(onError).not.toHaveBeenCalled()
    expect(onChunk).toHaveBeenCalledTimes(2)
    expect(onChunk).toHaveBeenNthCalledWith(1, '你好')
    expect(onChunk).toHaveBeenNthCalledWith(2, '！')
  })

  it('将 reasoning_content 分发给 onThoughtChunk', async () => {
    const fetchMock = vi.mocked(globalThis.fetch)
    const config: LlmConfig = { provider: 'deepseek', apiKey: 'sk-test' }
    const messages: ChatMessage[] = [{ id: '1', role: 'user', content: '你好', timestamp: 1 }]
    const chunks: string[] = [
      sseEvent({ choices: [{ delta: { content: '你好', reasoning_content: '思考中' } }] }),
      sseEvent({ choices: [{ delta: { reasoning_content: '继续思考' } }] }),
      'data: [DONE]\n\n',
    ]
    fetchMock.mockResolvedValueOnce(mockFetchResponse(chunks))

    const onChunk = vi.fn()
    const onError = vi.fn()
    const onThoughtChunk = vi.fn()

    await streamChat(config, messages, onChunk, onError, onThoughtChunk)

    expect(onError).not.toHaveBeenCalled()
    expect(onChunk).toHaveBeenCalledWith('你好')
    expect(onThoughtChunk).toHaveBeenCalledWith('思考中')
    expect(onThoughtChunk).toHaveBeenCalledWith('继续思考')
  })

  it('未提供 onThoughtChunk 时思考内容合入 onChunk', async () => {
    const fetchMock = vi.mocked(globalThis.fetch)
    const config: LlmConfig = { provider: 'deepseek', apiKey: 'sk-test' }
    const messages: ChatMessage[] = [{ id: '1', role: 'user', content: '你好', timestamp: 1 }]
    const chunks: string[] = [
      sseEvent({ choices: [{ delta: { content: 'A', reasoning_content: 'B' } }] }),
      'data: [DONE]\n\n',
    ]
    fetchMock.mockResolvedValueOnce(mockFetchResponse(chunks))

    const onChunk = vi.fn()
    const onError = vi.fn()

    await streamChat(config, messages, onChunk, onError)

    expect(onChunk).toHaveBeenCalledWith('A')
    expect(onChunk).toHaveBeenCalledWith('B')
  })

  it('HTTP 错误通过 onError 回调', async () => {
    const fetchMock = vi.mocked(globalThis.fetch)
    const config: LlmConfig = { provider: 'deepseek', apiKey: 'sk-test' }
    const messages: ChatMessage[] = [{ id: '1', role: 'user', content: '你好', timestamp: 1 }]
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 401,
      text: async () => JSON.stringify({ error: { message: 'Invalid key' } }),
      body: null,
    } as unknown as Response)

    const onChunk = vi.fn()
    const onError = vi.fn()

    await streamChat(config, messages, onChunk, onError)

    expect(onChunk).not.toHaveBeenCalled()
    expect(onError).toHaveBeenCalledOnce()
    expect(onError.mock.calls[0][0]).toBeInstanceOf(Error)
    expect(onError.mock.calls[0][0].message).toContain('Invalid key')
  })

  it('API key 为空时直接触发 onError', async () => {
    const fetchMock = vi.mocked(globalThis.fetch)
    const config: LlmConfig = { provider: 'deepseek', apiKey: '' }
    const messages: ChatMessage[] = [{ id: '1', role: 'user', content: '你好', timestamp: 1 }]

    const onChunk = vi.fn()
    const onError = vi.fn()

    await streamChat(config, messages, onChunk, onError)

    expect(fetchMock).not.toHaveBeenCalled()
    expect(onError).toHaveBeenCalledOnce()
    expect(onError.mock.calls[0][0].message).toContain('API key 为空')
  })
})

describe('testConnection', () => {
  beforeEach(() => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: async () => ({ data: [] }),
        text: async () => '',
      } as unknown as Response),
    )
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('HTTP 200 返回 ok:true 与模型列表', async () => {
    const fetchMock = vi.mocked(globalThis.fetch)
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: [{ id: 'model-a' }, { id: 'model-b' }] }),
      text: async () => '',
    } as unknown as Response)

    const result = await testConnection({ provider: 'deepseek', apiKey: 'sk-test' })

    expect(result.ok).toBe(true)
    expect(result.models).toEqual(['model-a', 'model-b'])
  })

  it('HTTP 401 返回 ok:false 与错误信息', async () => {
    const fetchMock = vi.mocked(globalThis.fetch)
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({}),
      text: async () => JSON.stringify({ error: { message: 'Authentication failed' } }),
    } as unknown as Response)

    const result = await testConnection({ provider: 'deepseek', apiKey: 'sk-wrong' })

    expect(result.ok).toBe(false)
    expect(result.error).toContain('Authentication failed')
  })

  it('API key 为空时直接返回错误', async () => {
    const result = await testConnection({ provider: 'deepseek', apiKey: '' })
    expect(result.ok).toBe(false)
    expect(result.error).toContain('API key 为空')
  })
})

describe('provider 请求体差异', () => {
  beforeEach(() => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() =>
      Promise.resolve(mockFetchResponse(['data: [DONE]\n\n'])),
    )
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it.each(PROVIDERS)('%s 使用正确的 endpoint 与 headers', async (provider) => {
    const fetchMock = vi.mocked(globalThis.fetch)
    const config: LlmConfig = { provider, apiKey: 'sk-test' }
    const messages: ChatMessage[] = [{ id: '1', role: 'user', content: 'hi', timestamp: 1 }]

    await streamChat(config, messages, vi.fn(), vi.fn())

    expect(fetchMock).toHaveBeenCalledOnce()
    const [url, init] = fetchMock.mock.calls[0]

    if (provider === 'anthropic') {
      expect(url).toBe('https://api.anthropic.com/v1/messages')
      expect(init?.headers).toMatchObject({
        'Content-Type': 'application/json',
        'x-api-key': 'sk-test',
        'anthropic-version': '2023-06-01',
      })
    } else if (provider === 'llamacpp') {
      expect(url).toBe('http://127.0.0.1:8080/v1/chat/completions')
      expect(init?.headers).toMatchObject({
        'Content-Type': 'application/json',
        Authorization: 'Bearer sk-test',
      })
    } else if (provider === 'openai') {
      expect(url).toBe('https://api.openai.com/v1/chat/completions')
      expect(init?.headers).toMatchObject({
        'Content-Type': 'application/json',
        Authorization: 'Bearer sk-test',
      })
    } else {
      expect(url).toBe('https://api.deepseek.com/v1/chat/completions')
      expect(init?.headers).toMatchObject({
        'Content-Type': 'application/json',
        Authorization: 'Bearer sk-test',
      })
    }
  })

  it('deepseek / openai 请求体包含 stream_options.include_usage', async () => {
    const fetchMock = vi.mocked(globalThis.fetch)

    for (const provider of ['deepseek', 'openai'] as LlmProvider[]) {
      fetchMock.mockClear()
      const config: LlmConfig = { provider, apiKey: 'sk-test' }
      const messages: ChatMessage[] = [{ id: '1', role: 'user', content: 'hi', timestamp: 1 }]

      await streamChat(config, messages, vi.fn(), vi.fn())

      const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string)
      expect(body.stream_options).toEqual({ include_usage: false })
    }
  })

  it('llamacpp 请求体不包含 stream_options', async () => {
    const fetchMock = vi.mocked(globalThis.fetch)
    const config: LlmConfig = { provider: 'llamacpp', apiKey: 'sk-test' }
    const messages: ChatMessage[] = [{ id: '1', role: 'user', content: 'hi', timestamp: 1 }]

    await streamChat(config, messages, vi.fn(), vi.fn())

    const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string)
    expect(body.stream_options).toBeUndefined()
  })

  it('anthropic 将 system 提取到顶层且 messages 中无 system 角色', async () => {
    const fetchMock = vi.mocked(globalThis.fetch)
    const config: LlmConfig = { provider: 'anthropic', apiKey: 'sk-test' }
    const messages: ChatMessage[] = [
      { id: '1', role: 'system', content: '你是助手', timestamp: 1 },
      { id: '2', role: 'user', content: '你好', timestamp: 2 },
    ]

    await streamChat(config, messages, vi.fn(), vi.fn())

    const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string)
    expect(body.system).toBe('你是助手')
    expect(body.messages).toEqual([{ role: 'user', content: '你好' }])
    expect(body.stream_options).toBeUndefined()
  })

  it('anthropic 过滤 tool 角色的消息', async () => {
    const fetchMock = vi.mocked(globalThis.fetch)
    const config: LlmConfig = { provider: 'anthropic', apiKey: 'sk-test' }
    const messages: ChatMessage[] = [
      { id: '1', role: 'user', content: 'hi', timestamp: 1 },
      { id: '2', role: 'tool', content: 'tool result', timestamp: 2 },
    ]

    await streamChat(config, messages, vi.fn(), vi.fn())

    const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string)
    expect(body.messages).toEqual([{ role: 'user', content: 'hi' }])
  })

  it('不同 provider 使用默认 model', async () => {
    const fetchMock = vi.mocked(globalThis.fetch)
    const expectedModels: Record<LlmProvider, string> = {
      deepseek: 'deepseek-v4-pro',
      openai: 'gpt-5.5',
      anthropic: 'claude-sonnet-4-20250514',
      llamacpp: 'local-model',
    }

    for (const provider of PROVIDERS) {
      fetchMock.mockClear()
      const config: LlmConfig = { provider, apiKey: 'sk-test' }
      const messages: ChatMessage[] = [{ id: '1', role: 'user', content: 'hi', timestamp: 1 }]

      await streamChat(config, messages, vi.fn(), vi.fn())

      const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string)
      expect(body.model).toBe(expectedModels[provider])
    }
  })
})
