/**
 * useTtsAudio Hook 单元测试
 *
 * 验证 TTS 音频播放状态转换、录音冲突处理以及 AnalyserNode 暴露。
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { useTtsAudio } from '../src/hooks/useTtsAudio'

class MockAnalyserNode {
  fftSize = 256
  frequencyBinCount = 128
  connect = vi.fn()
  disconnect = vi.fn()
  getByteFrequencyData = vi.fn()
  getByteTimeDomainData = vi.fn()
}

class MockAudioContext {
  state = 'running'
  destination = {}
  resume = vi.fn(async () => undefined)
  close = vi.fn(async () => undefined)
  createMediaElementSource = vi.fn(() => {
    const node = {
      connect: vi.fn(),
      disconnect: vi.fn(),
      mediaElement: {},
    }
    return node
  })
  createAnalyser = vi.fn(() => new MockAnalyserNode())
}

const createdAudios: MockAudio[] = []

class MockAudio {
  src = ''
  volume = 1
  crossOrigin = ''
  paused = true
  private listeners: Record<string, Array<(e?: Event | string) => void>> = {}

  constructor(src?: string) {
    if (src) this.src = src
    createdAudios.push(this)
  }

  play = vi.fn(async () => {
    this.paused = false
    this.emit('playing')
  })

  pause = vi.fn(() => {
    this.paused = true
  })

  load = vi.fn(() => {
    // no-op
  })

  addEventListener(event: string, cb: (e?: Event | string) => void): void {
    if (!this.listeners[event]) this.listeners[event] = []
    this.listeners[event].push(cb)
  }

  removeEventListener(event: string, cb: (e?: Event | string) => void): void {
    if (!this.listeners[event]) return
    this.listeners[event] = this.listeners[event].filter((c) => c !== cb)
  }

  emit(event: string, data?: Event | string): void {
    this.listeners[event]?.forEach((cb) => cb(data))
  }
}

beforeEach(() => {
  createdAudios.length = 0
  globalThis.AudioContext = MockAudioContext as unknown as typeof AudioContext
  globalThis.Audio = MockAudio as unknown as typeof Audio
})

afterEach(() => {
  createdAudios.length = 0
})

describe('useTtsAudio', () => {
  it('source 为 null 时不创建音频元素', () => {
    renderHook(() =>
      useTtsAudio({
        source: null,
        onStatusChange: vi.fn(),
        onEnded: vi.fn(),
      }),
    )
    expect(createdAudios.length).toBe(0)
  })

  function lastAudio(): MockAudio {
    expect(createdAudios.length).toBeGreaterThanOrEqual(1)
    return createdAudios[createdAudios.length - 1]
  }

  it('source 包含 audioUrl 时使用该 URL 创建音频', async () => {
    renderHook(() =>
      useTtsAudio({
        source: { audioUrl: 'http://example.com/tts.mp3' },
        onStatusChange: vi.fn(),
        onEnded: vi.fn(),
      }),
    )
    await waitFor(() => expect(createdAudios.length).toBeGreaterThanOrEqual(1))
    expect(lastAudio().src).toBe('http://example.com/tts.mp3')
  })

  it('source 包含 audioBase64 时构造 data URL', async () => {
    renderHook(() =>
      useTtsAudio({
        source: { audioBase64: 'AAAA', mimeType: 'audio/wav' },
        onStatusChange: vi.fn(),
        onEnded: vi.fn(),
      }),
    )
    await waitFor(() => expect(createdAudios.length).toBeGreaterThanOrEqual(1))
    expect(lastAudio().src).toBe('data:audio/wav;base64,AAAA')
  })

  it('enabled 为 false 时不播放', async () => {
    renderHook(() =>
      useTtsAudio({
        source: { audioBase64: 'AAAA' },
        enabled: false,
        onStatusChange: vi.fn(),
        onEnded: vi.fn(),
      }),
    )
    await new Promise((resolve) => setTimeout(resolve, 50))
    expect(createdAudios.length).toBe(0)
  })

  it('播放开始时通知 speaking，结束时通知 idle 并触发 onEnded', async () => {
    const onStatusChange = vi.fn()
    const onEnded = vi.fn()

    renderHook(() =>
      useTtsAudio({
        source: { audioBase64: 'AAAA' },
        onStatusChange,
        onEnded,
      }),
    )

    await waitFor(() => expect(createdAudios.length).toBeGreaterThanOrEqual(1))
    const audio = lastAudio()
    act(() => {
      audio.emit('playing')
    })
    expect(onStatusChange).toHaveBeenCalledWith('speaking')

    act(() => {
      audio.emit('ended')
    })
    await waitFor(() => expect(onStatusChange).toHaveBeenCalledWith('idle'))
    expect(onEnded).toHaveBeenCalled()
  })

  it('播放出错时恢复 idle 并触发 onEnded', async () => {
    const onStatusChange = vi.fn()
    const onEnded = vi.fn()

    renderHook(() =>
      useTtsAudio({
        source: { audioBase64: 'AAAA' },
        onStatusChange,
        onEnded,
      }),
    )

    await waitFor(() => expect(createdAudios.length).toBeGreaterThanOrEqual(1))
    const audio = lastAudio()
    act(() => {
      audio.emit('error')
    })
    await waitFor(() => expect(onStatusChange).toHaveBeenCalledWith('idle'))
    expect(onEnded).toHaveBeenCalled()
  })

  it('isRecording 变为 true 时停止播放并触发 onEnded', async () => {
    const onStatusChange = vi.fn()
    const onEnded = vi.fn()
    const source = { audioBase64: 'AAAA' }

    const { rerender } = renderHook(
      ({ isRecording }) =>
        useTtsAudio({
          source,
          isRecording,
          onStatusChange,
          onEnded,
        }),
      { initialProps: { isRecording: false } },
    )

    await waitFor(() => expect(createdAudios.length).toBeGreaterThanOrEqual(1))
    const audio = lastAudio()
    act(() => {
      audio.emit('playing')
    })
    expect(onStatusChange).toHaveBeenCalledWith('speaking')

    rerender({ isRecording: true })

    await waitFor(() => expect(audio.pause).toHaveBeenCalled())
    await waitFor(() => expect(onEnded).toHaveBeenCalled())
    expect(onStatusChange).toHaveBeenCalledWith('idle')
  })

  it('连续监听模式下结束后恢复 listening', async () => {
    const onStatusChange = vi.fn()
    const onEnded = vi.fn()

    renderHook(() =>
      useTtsAudio({
        source: { audioBase64: 'AAAA' },
        continuousListening: true,
        onStatusChange,
        onEnded,
      }),
    )

    await waitFor(() => expect(createdAudios.length).toBeGreaterThanOrEqual(1))
    const audio = lastAudio()
    act(() => {
      audio.emit('ended')
    })
    await waitFor(() => expect(onStatusChange).toHaveBeenCalledWith('listening'))
    expect(onEnded).toHaveBeenCalled()
  })
})
