/**
 * LiquidGlass 性能与 GlassPanel 行为测试
 *
 * 验证 GlassPanel 默认启用动画、animated=false 不启动 RAF、
 * 卸载清理资源、svgOk=false 回退到 backdrop-filter，
 * 以及动画帧率约为 30fps 且不阻塞 React 渲染。
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render } from '@testing-library/react'
import { GlassPanel } from '../src/components/glass/GlassPanel'
import { supportsLaapLiquidGlass } from '../src/components/glass/LiquidGlass'

vi.mock('../src/components/glass/LiquidGlass', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../src/components/glass/LiquidGlass')>()
  return {
    ...actual,
    supportsLaapLiquidGlass: vi.fn(() => true),
  }
})

const rafCallbacks: Array<FrameRequestCallback> = []
const revokedUrls: string[] = []
let rafIdCounter = 0

class MockResizeObserver {
  observe = vi.fn()
  disconnect = vi.fn()
  unobserve = vi.fn()
}

beforeEach(() => {
  rafCallbacks.length = 0
  revokedUrls.length = 0
  rafIdCounter = 0

  globalThis.requestAnimationFrame = vi.fn((cb: FrameRequestCallback) => {
    rafCallbacks.push(cb)
    rafIdCounter += 1
    return rafIdCounter
  })
  globalThis.cancelAnimationFrame = vi.fn((id: number) => {
    const idx = rafCallbacks.findIndex((_, i) => i + 1 === id)
    if (idx >= 0) rafCallbacks.splice(idx, 1)
  })

  globalThis.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver

  Element.prototype.getBoundingClientRect = vi.fn(() => ({
    width: 400,
    height: 92,
    top: 0,
    left: 0,
    bottom: 92,
    right: 400,
    x: 0,
    y: 0,
    toJSON: () => {},
  }))

  globalThis.getComputedStyle = vi.fn(() => ({ borderRadius: '24px' } as CSSStyleDeclaration))

  let urlCounter = 0
  globalThis.URL.createObjectURL = vi.fn(() => {
    urlCounter += 1
    return `blob:mock-url-${urlCounter}`
  }) as unknown as typeof URL.createObjectURL
  globalThis.URL.revokeObjectURL = vi.fn((url: string) => {
    revokedUrls.push(url)
  }) as unknown as typeof URL.revokeObjectURL

  vi.mocked(supportsLaapLiquidGlass).mockReturnValue(true)

  if (globalThis.performance) {
    vi.spyOn(globalThis.performance, 'now').mockReturnValue(0)
  }
})

afterEach(() => {
  rafCallbacks.length = 0
  revokedUrls.length = 0
})

describe('GlassPanel 动画与 RAF 行为', () => {
  it('默认渲染 animated 状态并启动 requestAnimationFrame', () => {
    render(<GlassPanel liquidGlass>content</GlassPanel>)

    expect(supportsLaapLiquidGlass).toHaveBeenCalled()
    expect(requestAnimationFrame).toHaveBeenCalled()
    expect(rafCallbacks.length).toBeGreaterThan(0)
  })

  it('animated=false 时不启动 requestAnimationFrame', () => {
    render(<GlassPanel liquidGlass animated={false}>content</GlassPanel>)

    expect(requestAnimationFrame).not.toHaveBeenCalled()
    expect(rafCallbacks.length).toBe(0)
  })

  it('卸载后撤销 blob URL 并停止 RAF', () => {
    const { unmount } = render(<GlassPanel liquidGlass>content</GlassPanel>)

    expect(requestAnimationFrame).toHaveBeenCalled()
    const rafCountBefore = rafCallbacks.length
    expect(rafCountBefore).toBeGreaterThan(0)

    unmount()

    expect(cancelAnimationFrame).toHaveBeenCalled()
    expect(revokedUrls.length).toBeGreaterThan(0)
  })
})

describe('GlassPanel 静态 fallback', () => {
  it('svgOk=false 时使用 backdrop-filter: blur() 回退', () => {
    vi.mocked(supportsLaapLiquidGlass).mockReturnValue(false)

    const { container } = render(<GlassPanel liquidGlass animated={false}>content</GlassPanel>)
    const panel = container.querySelector('.laap-glass-panel')
    expect(panel).not.toBeNull()

    const style = (panel as HTMLElement).style
    expect(style.backdropFilter).toContain('blur')
    expect(style.backdropFilter).not.toContain('url(#')
  })
})

describe('动画性能', () => {
  it('RAF 调用频率约为 30fps 且不阻塞 React 渲染', () => {
    const { container } = render(<GlassPanel liquidGlass>content</GlassPanel>)
    const feImage = container.querySelector('feImage')
    expect(feImage).not.toBeNull()

    const hrefs: string[] = []
    const timestamps: number[] = []

    // 先记录初始 href，避免把 mount 时的静态值误判为第一次动画更新
    const initialHref = feImage?.getAttribute('href') ?? ''
    if (initialHref) hrefs.push(initialHref)

    // 模拟 160ms 的 60fps RAF 调度，LiquidGlass 内部以 30fps 为间隔过滤，
    // 因此有效 displacement map 更新应大约发生在 33ms、66ms、99ms、132ms 附近。
    let rafFramesProcessed = 0
    for (let t = 0; t <= 160; t += 16) {
      const current = rafCallbacks.slice()
      rafCallbacks.length = 0
      rafFramesProcessed += current.length
      current.forEach((cb) => cb(t))
      const href = feImage?.getAttribute('href') ?? ''
      if (href && href !== hrefs[hrefs.length - 1]) {
        hrefs.push(href)
        timestamps.push(t)
      }
    }

    // 160ms 内应产生 3~5 次实际的 displacement map 更新（30fps）
    expect(hrefs.length).toBeGreaterThanOrEqual(3)
    expect(hrefs.length).toBeLessThanOrEqual(6)

    // 处理的 RAF 帧数应明显多于实际更新次数，说明动画被节流而非每帧重绘
    expect(rafFramesProcessed).toBeGreaterThan(hrefs.length * 2)

    // 相邻两次有效更新间隔应接近 33ms（允许 26~50ms 抖动）
    for (let i = 1; i < timestamps.length; i += 1) {
      const delta = timestamps[i] - timestamps[i - 1]
      expect(delta).toBeGreaterThanOrEqual(26)
      expect(delta).toBeLessThanOrEqual(50)
    }

    // React 渲染未崩溃且容器仍挂载
    expect(container.firstChild).not.toBeNull()
  })
})
