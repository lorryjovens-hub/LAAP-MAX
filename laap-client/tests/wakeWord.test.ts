/**
 * 唤醒词检测辅助函数单元测试
 *
 * 验证灵敏度到能量阈值的映射以及 RMS 计算。
 */

import { describe, it, expect } from 'vitest'
import { sensitivityToThreshold, computeRms } from '../src/hooks/useVoice'

describe('sensitivityToThreshold', () => {
  it('默认灵敏度 0.5 返回中间阈值', () => {
    expect(sensitivityToThreshold(0.5)).toBeCloseTo(0.08, 5)
  })

  it('最低灵敏度返回最高阈值', () => {
    expect(sensitivityToThreshold(0)).toBe(0.15)
  })

  it('最高灵敏度返回最低阈值', () => {
    expect(sensitivityToThreshold(1)).toBeCloseTo(0.01, 10)
  })

  it('超出范围的灵敏度被截断到 [0, 1]', () => {
    expect(sensitivityToThreshold(-1)).toBeCloseTo(0.15, 10)
    expect(sensitivityToThreshold(2)).toBeCloseTo(0.01, 10)
  })
})

describe('computeRms', () => {
  it('静音（全为 128）的 RMS 接近 0', () => {
    const data = new Uint8Array(64).fill(128)
    expect(computeRms(data)).toBeCloseTo(0, 5)
  })

  it('正弦波时域数据的 RMS 大于 0', () => {
    const data = new Uint8Array(64)
    for (let i = 0; i < data.length; i += 1) {
      data[i] = 128 + Math.round(64 * Math.sin((i / data.length) * Math.PI * 2))
    }
    expect(computeRms(data)).toBeGreaterThan(0.1)
  })

  it('恒定最大振幅的 RMS 接近 1', () => {
    const data = new Uint8Array(64).fill(0)
    expect(computeRms(data)).toBeCloseTo(1, 5)
  })
})
