/**
 * CognitiveBusClient 单元测试
 *
 * 验证 WebSocket 连接状态通知、topic 订阅/发布以及 AetherMessage 发送逻辑。
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { CognitiveBusClient } from '../src/laap/bus'
import type { AetherMessage } from '../src/laap/types'

class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  url: string
  readyState = MockWebSocket.CONNECTING
  sent: string[] = []

  onopen?: () => void
  onclose?: () => void
  onerror?: () => void
  onmessage?: (event: { data: string }) => void

  constructor(url: string) {
    this.url = url
    activeSockets.push(this)
  }

  send(data: string): void {
    this.sent.push(data)
  }

  close(): void {
    if (this.readyState === MockWebSocket.CLOSED) return
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.()
  }

  simulateOpen(): void {
    this.readyState = MockWebSocket.OPEN
    this.onopen?.()
  }

  simulateMessage(data: string): void {
    this.onmessage?.({ data })
  }
}

let activeSockets: MockWebSocket[] = []

beforeEach(() => {
  activeSockets = []
  globalThis.WebSocket = MockWebSocket as unknown as typeof WebSocket
})

afterEach(() => {
  activeSockets.forEach((socket) => socket.close())
})

function makeMessage(topic: string, payload: unknown): AetherMessage {
  return {
    id: 'msg-1',
    type: 'event',
    topic,
    payload,
    timestamp: Date.now(),
    sender: 'test',
  }
}

describe('CognitiveBusClient', () => {
  it('连接成功后通知状态监听器', () => {
    const client = new CognitiveBusClient()
    const listener = vi.fn()
    client.onStatusChange(listener)

    client.connect()
    expect(activeSockets).toHaveLength(1)

    activeSockets[0].simulateOpen()
    expect(listener).toHaveBeenCalledWith('open', undefined)
  })

  it('按 topic 分发消息给订阅者', () => {
    const client = new CognitiveBusClient()
    const handler = vi.fn()
    client.subscribe('need_curiosity', handler)
    client.connect()
    activeSockets[0].simulateOpen()

    const message = makeMessage('need_curiosity', { value: 0.88 })
    activeSockets[0].simulateMessage(JSON.stringify(message))

    expect(handler).toHaveBeenCalledTimes(1)
    expect(handler).toHaveBeenCalledWith(expect.objectContaining({ topic: 'need_curiosity' }))
  })

  it('未订阅的 topic 不会触发回调', () => {
    const client = new CognitiveBusClient()
    const handler = vi.fn()
    client.subscribe('need_trust', handler)
    client.connect()
    activeSockets[0].simulateOpen()

    activeSockets[0].simulateMessage(JSON.stringify(makeMessage('need_curiosity', { value: 0.5 })))
    expect(handler).not.toHaveBeenCalled()
  })

  it('支持通配符订阅', () => {
    const client = new CognitiveBusClient()
    const handler = vi.fn()
    client.subscribe('emotion_*', handler)
    client.connect()
    activeSockets[0].simulateOpen()

    activeSockets[0].simulateMessage(JSON.stringify(makeMessage('emotion_pleasure', { value: 0.6 })))
    activeSockets[0].simulateMessage(JSON.stringify(makeMessage('emotion_arousal', { value: 0.7 })))

    expect(handler).toHaveBeenCalledTimes(2)
  })

  it('连接已打开时发送 AetherMessage', () => {
    const client = new CognitiveBusClient()
    client.connect()
    activeSockets[0].simulateOpen()

    client.sendMessage('你好')
    // 连接打开后会立即发送一次心跳 ping，因此消息数至少为 1
    expect(activeSockets[0].sent.length).toBeGreaterThanOrEqual(1)

    const userMessage = activeSockets[0].sent
      .map((data) => JSON.parse(data))
      .find((msg) => msg.type === 'user_message')
    expect(userMessage).toMatchObject({
      type: 'user_message',
      topic: 'user.input',
      payload: { text: '你好' },
      sender: 'user',
    })
  })

  it('setUrl 并手动 connect 后使用新地址重新连接', () => {
    const client = new CognitiveBusClient({ url: 'ws://old' })
    client.connect()
    activeSockets[0].simulateOpen()

    client.setUrl('ws://new')
    client.connect()
    expect(activeSockets).toHaveLength(2)
    expect(activeSockets[1].url).toBe('ws://new')
  })
})
