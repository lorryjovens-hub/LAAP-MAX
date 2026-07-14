/**
 * RateBuffer：高频 PSI 事件可视化适配器
 *
 * 接收高频 AetherMessage 流（模拟 1000-2000 Hz），执行：
 * - 1ms 窗口内基于 topic + 近似值的重复事件去重
 * - 显著性阈值过滤，高显著性事件优先通过
 * - 每 100ms 或累积 50 条事件时输出一个 batch
 * - 实时统计 dedupCount、queueDepth、batchSize、aggregationWindowMs
 */

import { useEffect, useState } from 'react'
import type { AetherMessage, RateBufferBatch, RateBufferStats } from './types'

/**
 * RateBuffer 配置选项
 */
export interface RateBufferOptions {
  /** 去重时间窗口（毫秒） */
  dedupWindowMs?: number
  /** 显著性阈值，超过该值的事件优先通过 */
  salienceThreshold?: number
  /** 批量聚合最大事件数 */
  maxBatchSize?: number
  /** 批量聚合时间窗口（毫秒） */
  aggregationIntervalMs?: number
}

/**
 * 从 payload 中提取数值，用于近似去重
 */
function getPayloadSignature(payload: unknown): string {
  if (payload === null || payload === undefined) return 'none'
  if (typeof payload === 'number') return Math.round(payload * 100).toString()
  if (typeof payload === 'object' && payload !== null) {
    const obj = payload as Record<string, unknown>
    if (typeof obj.value === 'number') {
      return Math.round(obj.value * 100).toString()
    }
    if (typeof obj.progress === 'number') {
      return Math.round(obj.progress * 100).toString()
    }
    if (typeof obj.frequencyHz === 'number') {
      return Math.round(obj.frequencyHz / 100).toString()
    }
    return JSON.stringify(payload).slice(0, 80)
  }
  return String(payload).slice(0, 40)
}

/**
 * 从 payload 中提取显著性值
 */
function getSalience(payload: unknown): number {
  if (payload !== null && typeof payload === 'object') {
    const obj = payload as Record<string, unknown>
    if (typeof obj.salience === 'number') return obj.salience
    if (typeof obj.delta === 'number') return Math.abs(obj.delta) * 10
    if (typeof obj.value === 'number') return obj.value
  }
  return 0.5
}

/**
 * RateBuffer 类
 */
export class RateBuffer {
  private options: Required<RateBufferOptions>
  private queue: AetherMessage[] = []
  private priorityQueue: AetherMessage[] = []
  private dedupMap = new Map<string, number>()
  private stats: RateBufferStats
  private listeners = new Set<(batch: RateBufferBatch) => void>()
  private flushTimer: ReturnType<typeof setInterval> | null = null
  private lastFlushTime = Date.now()

  constructor(options: RateBufferOptions = {}) {
    this.options = {
      dedupWindowMs: options.dedupWindowMs ?? 1,
      salienceThreshold: options.salienceThreshold ?? 0.75,
      maxBatchSize: options.maxBatchSize ?? 50,
      aggregationIntervalMs: options.aggregationIntervalMs ?? 100,
    }
    this.stats = {
      dedupCount: 0,
      queueDepth: 0,
      batchSize: 0,
      aggregationWindowMs: 0,
    }
  }

  /**
   * 启动聚合定时器
   */
  start(): void {
    if (this.flushTimer) return
    this.flushTimer = setInterval(() => {
      this.flush()
    }, this.options.aggregationIntervalMs)
  }

  /**
   * 停止聚合定时器
   */
  stop(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer)
      this.flushTimer = null
    }
  }

  /**
   * 推送单条事件
   */
  push(message: AetherMessage): void {
    const now = Date.now()
    const key = `${message.topic}:${getPayloadSignature(message.payload)}`

    // 去重：1ms 窗口内相同 topic + 近似值的事件合并
    const lastSeen = this.dedupMap.get(key)
    if (lastSeen !== undefined && now - lastSeen <= this.options.dedupWindowMs) {
      this.stats.dedupCount += 1
      this.updateStats()
      return
    }
    this.dedupMap.set(key, now)
    this.cleanupDedupMap(now)

    const salience = getSalience(message.payload)

    // 高显著性事件优先进入优先队列
    if (salience >= this.options.salienceThreshold) {
      this.priorityQueue.push(message)
    } else {
      this.queue.push(message)
    }

    this.updateStats()

    // 达到批量阈值时立即 flush
    if (this.queue.length + this.priorityQueue.length >= this.options.maxBatchSize) {
      this.flush()
    }
  }

  /**
   * 订阅 batch 输出
   */
  onBatch(callback: (batch: RateBufferBatch) => void): () => void {
    this.listeners.add(callback)
    return () => {
      this.listeners.delete(callback)
    }
  }

  /**
   * 获取当前统计快照
   */
  getStats(): RateBufferStats {
    return { ...this.stats }
  }

  /**
   * 清空队列与统计
   */
  clear(): void {
    this.queue = []
    this.priorityQueue = []
    this.dedupMap.clear()
    this.stats = {
      dedupCount: 0,
      queueDepth: 0,
      batchSize: 0,
      aggregationWindowMs: 0,
    }
  }

  /**
   * 聚合输出一个 batch
   */
  private flush(): void {
    const now = Date.now()
    const events = [...this.priorityQueue, ...this.queue]
    this.priorityQueue = []
    this.queue = []

    if (events.length === 0) {
      this.stats.batchSize = 0
      this.stats.aggregationWindowMs = now - this.lastFlushTime
      this.updateStats()
      return
    }

    this.stats.batchSize = events.length
    this.stats.aggregationWindowMs = now - this.lastFlushTime
    this.lastFlushTime = now
    this.updateStats()

    const batch: RateBufferBatch = {
      timestamp: now,
      events,
      stats: { ...this.stats },
    }

    this.listeners.forEach((listener) => {
      try {
        listener(batch)
      } catch (err) {
        console.error('[RateBuffer] batch 监听器执行失败:', err)
      }
    })
  }

  /**
   * 更新队列深度等统计
   */
  private updateStats(): void {
    this.stats.queueDepth = this.queue.length + this.priorityQueue.length
  }

  /**
   * 清理过期去重记录，避免内存无限增长
   */
  private cleanupDedupMap(now: number): void {
    const windowMs = this.options.dedupWindowMs * 5
    for (const [key, timestamp] of this.dedupMap) {
      if (now - timestamp > windowMs) {
        this.dedupMap.delete(key)
      }
    }
  }
}

/**
 * 默认 RateBuffer 单例
 */
export const defaultRateBuffer = new RateBuffer()

/**
 * React Hook：订阅 RateBuffer 统计变化
 */
export function useRateBuffer(rateBuffer: RateBuffer = defaultRateBuffer): RateBufferStats {
  const [stats, setStats] = useState<RateBufferStats>(() => rateBuffer.getStats())

  useEffect(() => {
    rateBuffer.start()
    const unsubscribe = rateBuffer.onBatch(() => {
      setStats(rateBuffer.getStats())
    })
    return () => {
      unsubscribe()
    }
  }, [rateBuffer])

  return stats
}
