/**
 * UI 回归测试
 *
 * 验证主要布局组件（侧边栏、聊天输入栏、底部控制台）应用玻璃面板类名，
 * 并确认核心设计 token 未发生非预期变化。
 */

import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { LeftSidebar } from '../src/components/shell/LeftSidebar'
import { InputBar } from '../src/components/chat/InputBar'
import { WindowFrame } from '../src/components/shell/WindowFrame'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const tokensCss = readFileSync(resolve(__dirname, '../src/styles/tokens.css'), 'utf-8')

const mockPsiCycle = { phase: 'perception' as const, progress: 0.25 }
const mockVitalSigns = {
  curiosity: 0.5,
  trust: 0.5,
  competence: 0.5,
  pleasure: 0.5,
  arousal: 0.5,
  dominance: 0.5,
  sociality: 0.5,
  stress: 0.2,
}

describe('UI 回归：主要布局玻璃面板类名', () => {
  it('侧边栏应用 laap-glass-panel 与 --liquid 修饰类', () => {
    const { container } = render(
      <LeftSidebar
        collapsed={false}
        psiCycle={mockPsiCycle}
        vitalSigns={mockVitalSigns}
      />,
    )

    const sidebar = container.querySelector('.laap-glass-panel')
    expect(sidebar).not.toBeNull()
    expect(sidebar?.classList.contains('laap-glass-panel--liquid')).toBe(true)
  })

  it('聊天输入栏应用 laap-glass-panel 与 --liquid 修饰类', () => {
    const { container } = render(
      <InputBar
        value=""
        onChange={() => {}}
        onSend={() => {}}
        connectionStatus="open"
        psiCycle={mockPsiCycle}
      />,
    )

    const inputBar = container.querySelector('.laap-glass-panel')
    expect(inputBar).not.toBeNull()
    expect(inputBar?.classList.contains('laap-glass-panel--liquid')).toBe(true)
  })

  it('底部控制台应用 laap-glass-panel', () => {
    const { container } = render(
      <WindowFrame
        bottomBar={<div data-testid="bottom-content">bottom bar</div>}
      />,
    )

    const panels = container.querySelectorAll('.laap-glass-panel')
    expect(panels.length).toBeGreaterThanOrEqual(2)

    // 底部控制台是 WindowFrame 内部 footer 中的 GlassPanel
    const footerPanel = container.querySelector('footer .laap-glass-panel')
    expect(footerPanel).not.toBeNull()
  })
})

describe('UI 回归：颜色 token 未发生非预期变化', () => {
  it('--laap-bg-primary 保持 #050608', () => {
    expect(tokensCss).toContain('--laap-bg-primary: #050608')
  })

  it('--laap-accent 保持 #7c7cff', () => {
    expect(tokensCss).toContain('--laap-accent: #7c7cff')
  })

  it('--laap-secondary 保持 #00f5d4', () => {
    expect(tokensCss).toContain('--laap-secondary: #00f5d4')
  })

  it('--laap-text-primary 保持 #f5f5f7', () => {
    expect(tokensCss).toContain('--laap-text-primary: #f5f5f7')
  })
})
