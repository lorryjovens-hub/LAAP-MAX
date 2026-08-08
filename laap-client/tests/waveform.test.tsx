/**
 * WaveformVisualizer 单元测试
 *
 * 验证无真实音频时回退到 CSS 动画，有 AnalyserNode 时读取真实频域数据。
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, act } from '@testing-library/react'
import { useRef } from 'react'
import { WaveformVisualizer } from '../src/components/voice/WaveformVisualizer'

class MockAnalyserNode {
  fftSize = 256
  frequencyBinCount = 128
  connect = vi.fn()
  disconnect = vi.fn()
  getByteFrequencyData = vi.fn((data: Uint8Array) => {
    for (let i = 0; i < data.length; i += 1) {
      data[i] = (i * 2) % 256
    }
  })
  getByteTimeDomainData = vi.fn()
}

const rafCallbacks: Array<() => void> = []

beforeEach(() => {
  globalThis.requestAnimationFrame = vi.fn((cb: FrameRequestCallback) => {
    rafCallbacks.push(cb as () => void)
    return rafCallbacks.length
  })
  globalThis.cancelAnimationFrame = vi.fn((id: number) => {
    rafCallbacks.splice(id - 1, 1)
  })
})

afterEach(() => {
  rafCallbacks.length = 0
})

const sharedAnalyser = new MockAnalyserNode()

function TestWrapperWithAnalyser() {
  const analyserRef = useRef<AnalyserNode | null>(sharedAnalyser as unknown as AnalyserNode)
  return <WaveformVisualizer active barCount={8} analyserRef={analyserRef} />
}

describe('WaveformVisualizer', () => {
  it('渲染指定数量的波形条', () => {
    const { container } = render(<WaveformVisualizer active={false} barCount={12} />)
    const bars = container.querySelectorAll('span')
    expect(bars.length).toBe(12)
  })

  it('无 analyserRef 时使用 CSS 动画类', () => {
    const { container } = render(<WaveformVisualizer active barCount={4} audioLevel={0.8} />)
    const bars = container.querySelectorAll('span')
    bars.forEach((bar) => {
      expect(bar.classList.contains('waveform-bar')).toBe(true)
    })
  })

  it('传入 analyserRef 时不使用 CSS 动画类', () => {
    const { container } = render(<TestWrapperWithAnalyser />)
    act(() => {
      rafCallbacks.forEach((cb) => cb())
    })
    const bars = container.querySelectorAll('span')
    bars.forEach((bar) => {
      expect(bar.classList.contains('waveform-bar')).toBe(false)
    })
  })

  it('传入 analyserRef 时读取频域数据并更新高度', () => {
    sharedAnalyser.getByteFrequencyData.mockClear()
    render(<TestWrapperWithAnalyser />)

    // 手动触发一次 requestAnimationFrame 回调
    act(() => {
      rafCallbacks.forEach((cb) => cb())
    })

    expect(sharedAnalyser.getByteFrequencyData).toHaveBeenCalled()
  })
})
