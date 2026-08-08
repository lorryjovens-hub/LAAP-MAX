/**
 * LiquidGlass 单元测试
 *
 * 验证动态水波纹 displacement map 随时间变化、
 * animated=false 时不启动动画循环、以及组件卸载时清理资源。
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, act } from '@testing-library/react'
import { useRef } from 'react'
import { LiquidGlass, generateLaapGlassDisplacementMap } from '../src/components/glass/LiquidGlass'

const rafCallbacks: Array<FrameRequestCallback> = []
const revokedUrls: string[] = []

class MockResizeObserver {
  observe = vi.fn()
  disconnect = vi.fn()
  unobserve = vi.fn()
}

function TestWrapper({ animated = true }: { animated?: boolean }) {
  const ref = useRef<HTMLDivElement>(null)
  return (
    <>
      <div ref={ref} data-testid="target" style={{ width: 400, height: 92, borderRadius: 24 }}>
        target
      </div>
      <LiquidGlass targetRef={ref} animated={animated} />
    </>
  )
}

beforeEach(() => {
  rafCallbacks.length = 0
  revokedUrls.length = 0

  globalThis.requestAnimationFrame = vi.fn((cb: FrameRequestCallback) => {
    rafCallbacks.push(cb)
    return rafCallbacks.length
  })
  globalThis.cancelAnimationFrame = vi.fn((id: number) => {
    rafCallbacks.splice(id - 1, 1)
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
})

afterEach(() => {
  rafCallbacks.length = 0
  revokedUrls.length = 0
})

describe('generateLaapGlassDisplacementMap', () => {
  it('同一尺寸下，不同 time 生成不同 SVG', () => {
    const svg1 = generateLaapGlassDisplacementMap(400, 92, 24, 0)
    const svg2 = generateLaapGlassDisplacementMap(400, 92, 24, 1000)
    expect(svg1).not.toBe(svg2)
    expect(svg1).toContain('linearGradient')
    expect(svg2).toContain('linearGradient')
  })

  it('time=0 时返回静态 displacement map', () => {
    const svg = generateLaapGlassDisplacementMap(400, 92, 24, 0)
    expect(svg).toContain('x1="100.00%"')
    expect(svg).toContain('y2="100.00%"')
  })
})

describe('LiquidGlass', () => {
  it('渲染 SVG 滤镜定义', () => {
    const { container } = render(<TestWrapper />)
    const filter = container.querySelector('filter')
    expect(filter).not.toBeNull()
    expect(filter?.getAttribute('id')).toBe('laap-liquid-glass-filter')
  })

  it('animated=true 时启动 requestAnimationFrame 循环', () => {
    render(<TestWrapper animated />)
    expect(requestAnimationFrame).toHaveBeenCalled()
    expect(rafCallbacks.length).toBeGreaterThan(0)
  })

  it('animated=false 时不启动 requestAnimationFrame 循环', () => {
    render(<TestWrapper animated={false} />)
    expect(requestAnimationFrame).not.toHaveBeenCalled()
    expect(rafCallbacks.length).toBe(0)
  })

  it('动画帧更新 feImage 的 href', () => {
    const { container } = render(<TestWrapper animated />)
    const feImage = container.querySelector('feImage')
    const initialHref = feImage?.getAttribute('href') ?? ''

    act(() => {
      rafCallbacks.forEach((cb) => cb(performance.now() + 40))
    })

    const nextHref = feImage?.getAttribute('href') ?? ''
    expect(nextHref).not.toBe(initialHref)
    expect(nextHref).toContain('blob:mock-url-')
  })

  it('卸载时撤销 blob URL', () => {
    const { unmount } = render(<TestWrapper animated />)
    unmount()
    expect(revokedUrls.length).toBeGreaterThan(0)
  })
})
