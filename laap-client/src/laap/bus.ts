import type { AetherMessage, ConnectionStatus } from './types'

/**
 * CognitiveBus 客户端配置
 */
export interface CognitiveBusClientOptions {
  /** WebSocket 后端地址 */
  url?: string
  /** 心跳间隔（毫秒） */
  heartbeatIntervalMs?: number
  /** 自动重连基础间隔（毫秒） */
  reconnectBaseMs?: number
  /** 自动重连最大间隔（毫秒） */
  reconnectMaxMs?: number
  /** 随机抖动比例，避免多个客户端同时重连 */
  reconnectJitter?: number
}

/**
 * 事件订阅回调签名
 */
export type AetherMessageCallback = (message: AetherMessage) => void

/**
 * 生成唯一消息 ID
 */
function generateMessageId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
}

/**
 * 简单通配符匹配，仅支持单个 '*' 表示任意字符序列。
 * 例如 'qre_*' 可匹配 'qre_attention'、'qre_memory' 等。
 */
function matchPattern(pattern: string, topic: string): boolean {
  if (pattern === topic) return true
  if (!pattern.includes('*')) return false

  const parts = pattern.split('*')
  if (parts.length !== 2) return false

  const [prefix, suffix] = parts
  if (prefix && !topic.startsWith(prefix)) return false
  if (suffix && !topic.endsWith(suffix)) return false
  return topic.length >= prefix.length + suffix.length
}

/**
 * CognitiveBus WebSocket 客户端。
 *
 * 负责与 LAAP 后端建立 WebSocket 连接、自动重连、心跳保活、
 * 订阅/发布 AetherMessage，并按 topic/type 分发给订阅者。
 */
export class CognitiveBusClient {
  private url: string
  private ws: WebSocket | null = null
  private status: ConnectionStatus = 'closed'
  private reconnectAttempts = 0
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private pongTimer: ReturnType<typeof setTimeout> | null = null

  private readonly heartbeatIntervalMs: number
  private readonly reconnectBaseMs: number
  private readonly reconnectMaxMs: number
  private readonly reconnectJitter: number

  private subscribers = new Map<string, Set<AetherMessageCallback>>()
  private statusListeners = new Set<(status: ConnectionStatus, error?: string) => void>()

  constructor(options: CognitiveBusClientOptions = {}) {
    this.url = options.url ?? 'ws://127.0.0.1:8765'
    this.heartbeatIntervalMs = options.heartbeatIntervalMs ?? 15000
    this.reconnectBaseMs = options.reconnectBaseMs ?? 1000
    this.reconnectMaxMs = options.reconnectMaxMs ?? 30000
    this.reconnectJitter = options.reconnectJitter ?? 0.2
  }

  /**
   * 获取当前连接状态
   */
  getConnectionStatus(): ConnectionStatus {
    return this.status
  }

  /**
   * 更新后端 WebSocket 地址，断开当前连接。
   * 需要重新连接时，请在外部调用 connect()。
   */
  setUrl(url: string): void {
    const next = url.trim()
    if (this.url === next) return
    this.url = next
    this.disconnect()
  }

  /**
   * 注册连接状态监听器
   */
  onStatusChange(callback: (status: ConnectionStatus, error?: string) => void): () => void {
    this.statusListeners.add(callback)
    return () => {
      this.statusListeners.delete(callback)
    }
  }

  /**
   * 建立 WebSocket 连接
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN || this.ws?.readyState === WebSocket.CONNECTING) {
      return
    }

    this.setStatus('connecting')

    try {
      this.ws = new WebSocket(this.url)
    } catch (err) {
      this.setStatus('error', err instanceof Error ? err.message : '创建 WebSocket 失败')
      this.scheduleReconnect()
      return
    }

    this.ws.onopen = () => {
      this.reconnectAttempts = 0
      this.setStatus('open')
      this.startHeartbeat()
    }

    this.ws.onmessage = (event) => {
      this.handleMessage(event.data)
    }

    this.ws.onerror = () => {
      this.setStatus('error', 'WebSocket 发生错误')
    }

    this.ws.onclose = () => {
      this.stopHeartbeat()
      this.setStatus('closed')
      this.ws = null
      this.scheduleReconnect()
    }
  }

  /**
   * 主动断开连接，断开后不会自动重连，直到再次调用 connect()
   */
  disconnect(): void {
    this.clearReconnectTimer()
    this.stopHeartbeat()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.setStatus('closed')
  }

  /**
   * 发送用户文本消息，自动包装为 AetherMessage
   */
  sendMessage(text: string): void {
    const message: AetherMessage = {
      id: generateMessageId(),
      type: 'user_message',
      topic: 'user.input',
      payload: { text },
      timestamp: Date.now(),
      sender: 'user',
    }
    this.sendAetherMessage(message)
  }

  /**
   * 发送原始 AetherMessage
   */
  sendAetherMessage(message: AetherMessage): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('[CognitiveBus] 连接未就绪，消息发送失败:', message.topic)
      return
    }
    this.ws.send(JSON.stringify(message))
  }

  /**
   * 订阅指定 topic 模式，支持 '*' 通配符
   */
  subscribe(pattern: string, callback: AetherMessageCallback): () => void {
    let set = this.subscribers.get(pattern)
    if (!set) {
      set = new Set()
      this.subscribers.set(pattern, set)
    }
    set.add(callback)

    return () => {
      this.unsubscribe(pattern, callback)
    }
  }

  /**
   * 取消订阅
   */
  unsubscribe(pattern: string, callback: AetherMessageCallback): void {
    const set = this.subscribers.get(pattern)
    if (set) {
      set.delete(callback)
      if (set.size === 0) {
        this.subscribers.delete(pattern)
      }
    }
  }

  /**
   * 处理收到的消息文本，解析并按 topic/type 分发
   */
  private handleMessage(data: unknown): void {
    let message: AetherMessage
    try {
      message = JSON.parse(String(data)) as AetherMessage
    } catch {
      console.warn('[CognitiveBus] 收到非 JSON 消息:', data)
      return
    }

    if (message.topic === 'pong') {
      this.clearPongTimer()
      return
    }

    this.dispatch(message)
  }

  /**
   * 将消息分发给所有匹配 pattern 的订阅者
   */
  private dispatch(message: AetherMessage): void {
    const topic = message.topic ?? message.type ?? ''
    for (const [pattern, callbacks] of this.subscribers) {
      if (matchPattern(pattern, topic)) {
        callbacks.forEach((cb) => {
          try {
            cb(message)
          } catch (err) {
            console.error('[CognitiveBus] 订阅回调执行失败:', err)
          }
        })
      }
    }
  }

  /**
   * 启动心跳
   */
  private startHeartbeat(): void {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      this.sendPing()
    }, this.heartbeatIntervalMs)
    this.sendPing()
  }

  /**
   * 停止心跳
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
    this.clearPongTimer()
  }

  /**
   * 发送 ping 并设置超时检测
   */
  private sendPing(): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return

    this.ws.send(JSON.stringify({ topic: 'ping', timestamp: Date.now() }))
    this.clearPongTimer()
    this.pongTimer = setTimeout(() => {
      console.warn('[CognitiveBus] 心跳超时，准备重连')
      this.ws?.close()
    }, this.heartbeatIntervalMs)
  }

  /**
   * 清除 pong 超时计时器
   */
  private clearPongTimer(): void {
    if (this.pongTimer) {
      clearTimeout(this.pongTimer)
      this.pongTimer = null
    }
  }

  /**
   * 调度自动重连，采用指数退避 + 抖动
   */
  private scheduleReconnect(): void {
    this.clearReconnectTimer()
    const base = Math.min(
      this.reconnectMaxMs,
      this.reconnectBaseMs * 2 ** this.reconnectAttempts,
    )
    const jitter = base * this.reconnectJitter * (Math.random() * 2 - 1)
    const delay = Math.max(this.reconnectBaseMs, Math.floor(base + jitter))

    this.reconnectAttempts += 1
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, delay)
  }

  /**
   * 清除重连计时器
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }

  /**
   * 更新内部状态并通知监听器
   */
  private setStatus(status: ConnectionStatus, error?: string): void {
    if (this.status === status && !error) return
    this.status = status
    this.statusListeners.forEach((listener) => listener(status, error))
  }
}

/**
 * 默认 CognitiveBus 单例，应用生命周期内复用
 */
export const defaultCognitiveBus = new CognitiveBusClient()
