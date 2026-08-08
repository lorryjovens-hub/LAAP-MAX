/**
 * LLM 端到端链路测试
 *
 * mock fetch 与 ws 模块，验证：
 * config.llm 保存 → mockServer 接收 → user.input 触发真实 LLM 调用 →
 * chunk / thought_chunk 事件回传的完整链路。
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { WebSocket as MockWebSocket } from 'ws'
import { startLaapMockServer } from '../src/laap/mockServer'
import { CognitiveBusClient } from '../src/laap/bus'
import type { AetherMessage } from '../src/laap/types'

vi.mock('ws', () => {
  const registry = new Map<string, any>()

  class MockServerSocket {
    readyState = 1
    messageListeners = new Set<(data: any) => void>()
    closeListeners = new Set<() => void>()
    clientSocket: any = null

    send(data: string | Uint8Array) {
      const str = typeof data === 'string' ? data : Buffer.from(data).toString('utf-8')
      this.clientSocket?.onmessage?.({ data: str })
    }

    close() {
      if (this.readyState === 3) return
      this.readyState = 3
      this.closeListeners.forEach((cb) => cb())
    }

    terminate() {
      this.close()
    }

    on(event: string, cb: any) {
      if (event === 'message') this.messageListeners.add(cb)
      if (event === 'close') this.closeListeners.add(cb)
    }
  }

  class MockWSS {
    options: { host: string; port: number }
    clients = new Set<any>()
    connectionListeners = new Set<(socket: any) => void>()

    constructor(options: any) {
      this.options = { host: options.host ?? '127.0.0.1', port: options.port ?? 8765 }
      registry.set(`ws://${this.options.host}:${this.options.port}`, this)
    }

    on(event: string, cb: any) {
      if (event === 'connection') this.connectionListeners.add(cb)
    }

    close() {
      registry.delete(`ws://${this.options.host}:${this.options.port}`)
      this.clients.forEach((c: any) => c.close())
    }
  }

  class MockWebSocketImpl {
    static CONNECTING = 0
    static OPEN = 1
    static CLOSING = 2
    static CLOSED = 3

    url: string
    readyState = MockWebSocketImpl.CONNECTING
    onopen?: () => void
    onclose?: () => void
    onerror?: () => void
    onmessage?: (event: { data: string }) => void
    serverSocket: any

    constructor(url: string) {
      this.url = url
      const server = registry.get(url)
      if (!server) {
        queueMicrotask(() => this.onerror?.())
        return
      }
      const ss = new MockServerSocket()
      ss.clientSocket = this
      this.serverSocket = ss
      server.clients.add(ss)
      queueMicrotask(() => {
        this.readyState = MockWebSocketImpl.OPEN
        this.onopen?.()
        server.connectionListeners.forEach((cb: any) => cb(ss))
      })
    }

    send(data: string) {
      this.serverSocket?.messageListeners.forEach((cb: any) => cb(data))
    }

    close() {
      if (this.readyState === MockWebSocketImpl.CLOSED) return
      this.readyState = MockWebSocketImpl.CLOSED
      this.serverSocket?.close()
      this.onclose?.()
    }
  }

  return {
    WebSocketServer: MockWSS,
    WebSocket: MockWebSocketImpl,
  }
})

const SERVER_URL = 'ws://127.0.0.1:18765'

function sseEvent(obj: unknown): string {
  return `data: ${JSON.stringify(obj)}\n\n`
}

function createSSEReader(events: string[]) {
  let index = 0
  return {
    read: async () => {
      if (index >= events.length) {
        return { done: true, value: undefined }
      }
      const encoder = new TextEncoder()
      return { done: false, value: encoder.encode(events[index++]) }
    },
    releaseLock: () => {},
  }
}

function mockFetchResponse(events: string[]) {
  return {
    ok: true,
    status: 200,
    body: {
      getReader: () => createSSEReader(events),
    },
  }
}

describe('LLM end-to-end 链路', () => {
  let closeServer: (() => void) | null = null
  let client: CognitiveBusClient
  const fetchMock = vi.fn()

  beforeEach(() => {
    globalThis.WebSocket = MockWebSocket as unknown as typeof WebSocket
    globalThis.fetch = fetchMock
    fetchMock.mockReset()
  })

  afterEach(() => {
    client?.disconnect()
    closeServer?.()
    closeServer = null
    vi.restoreAllMocks()
  })

  it('config.llm → user.input → fetch → chunk / thought_chunk 回传', async () => {
    const events = [
      sseEvent({ choices: [{ delta: { content: 'Hi' } }] }),
      sseEvent({ choices: [{ delta: { reasoning_content: 'thinking' } }] }),
      sseEvent({ choices: [{ delta: { content: ' there' } }] }),
      'data: [DONE]\n\n',
    ]
    fetchMock.mockResolvedValue(mockFetchResponse(events))

    closeServer = await startLaapMockServer({
      port: 18765,
      host: '127.0.0.1',
      psiEventIntervalMs: 100000,
      lifecycleIntervalMs: 100000,
    })

    client = new CognitiveBusClient({ url: SERVER_URL })

    const chunks: string[] = []
    const thoughts: string[] = []
    const results: AetherMessage[] = []

    client.subscribe('chunk', (message) => {
      chunks.push((message.payload as { text?: string }).text ?? '')
    })
    client.subscribe('thought_chunk', (message) => {
      thoughts.push((message.payload as { text?: string }).text ?? '')
    })
    client.subscribe('harness_execution_result', (message) => {
      results.push(message)
    })

    client.connect()

    await vi.waitFor(() => {
      expect(client.getConnectionStatus()).toBe('open')
    })

    client.sendAetherMessage({
      id: 'cfg-1',
      type: 'config_update',
      topic: 'config.llm',
      payload: {
        provider: 'deepseek',
        apiKey: 'sk-e2e',
        model: 'deepseek-v4-pro',
        baseUrl: 'https://api.deepseek.com',
        useRealApi: true,
      },
      timestamp: Date.now(),
      sender: 'user',
    })

    client.sendAetherMessage({
      id: 'input-1',
      type: 'user_message',
      topic: 'user.input',
      payload: { text: 'hello' },
      timestamp: Date.now(),
      sender: 'user',
    })

    await vi.waitFor(() => {
      expect(fetchMock).toHaveBeenCalledOnce()
    })

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('https://api.deepseek.com/v1/chat/completions')
    const body = JSON.parse(init?.body as string)
    expect(body).toMatchObject({
      model: 'deepseek-v4-pro',
      stream: true,
      messages: [{ role: 'user', content: 'hello' }],
    })

    await vi.waitFor(() => {
      expect(chunks).toEqual(['Hi', ' there'])
      expect(thoughts).toEqual(['thinking'])
    })

    await vi.waitFor(() => {
      expect(results.length).toBeGreaterThanOrEqual(1)
    })

    expect((results[0].payload as { success?: boolean }).success).toBe(true)
  })
})
