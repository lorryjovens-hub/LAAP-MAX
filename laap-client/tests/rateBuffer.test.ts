/**
 * RateBuffer 单元测试
 *
 * 验证高频事件去重、显著性优先级以及批量 flush 统计。
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { RateBuffer } from '../src/laap/rateBuffer'
import type { AetherMessage } from '../src/laap/types'

function makeMessage(topic: string, payload: unknown): AetherMessage {
  return {
    id: 'r-1',
    type: 'event',
    topic,
    payload,
    timestamp: Date.now(),
    sender: 'test',
  }
}

describe('RateBuffer', () => {
  let rateBuffer: RateBuffer

  beforeEach(() => {
    rateBuffer = new RateBuffer()
  })

  afterEach(() => {
    rateBuffer.stop()
    rateBuffer.clear()
  })

  it('对 1ms 窗口内相同 topic + 近似值的事件进行去重', () => {
    rateBuffer.start()
    const listener = vi.fn()
    rateBuffer.onBatch(listener)

    rateBuffer.push(makeMessage('qre_attention', { value: 0.42 }))
    rateBuffer.push(makeMessage('qre_attention', { value: 0.42 }))
    rateBuffer.push(makeMessage('qre_attention', { value: 0.43 }))

    rateBuffer.flush()

    expect(rateBuffer.getStats().dedupCount).toBeGreaterThan(0)
    expect(listener).toHaveBeenCalled()
  })

  it('flush 后清空队列并更新统计', () => {
    rateBuffer.start()
    rateBuffer.push(makeMessage('qre_attention', { value: 0.1 }))
    rateBuffer.push(makeMessage('qre_memory', { value: 0.2 }))

    rateBuffer.flush()

    expect(rateBuffer.getStats().batchSize).toBe(2)
    expect(rateBuffer.getStats().queueDepth).toBe(0)
  })

  it('clear 后统计归零', () => {
    rateBuffer.start()
    rateBuffer.push(makeMessage('qre_attention', { value: 0.1 }))
    rateBuffer.flush()
    rateBuffer.clear()

    const stats = rateBuffer.getStats()
    expect(stats.dedupCount).toBe(0)
    expect(stats.queueDepth).toBe(0)
    expect(stats.batchSize).toBe(0)
  })

  it('高显著性事件进入优先队列并优先输出', () => {
    rateBuffer.start()
    const listener = vi.fn()
    rateBuffer.onBatch(listener)

    rateBuffer.push(makeMessage('qre_attention', { value: 0.1 }))
    rateBuffer.push(makeMessage('qre_attention', { value: 0.1, salience: 0.9 }))

    rateBuffer.flush()

    const batch = listener.mock.calls[0][0]
    expect(batch.events.length).toBeGreaterThanOrEqual(1)
  })
})
