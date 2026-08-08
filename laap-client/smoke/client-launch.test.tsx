/**
 * 客户端启动冒烟测试
 *
 * 在 jsdom 中渲染标题栏，验证应用标题为 "LAAP Client" 且存在自定义标题栏元素。
 */

import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { TitleBar } from '../src/components/shell/TitleBar'

describe('客户端启动', () => {
  it('渲染自定义标题栏并显示应用标题', () => {
    render(<TitleBar onSettingsClick={() => {}} />)

    expect(document.body.textContent).toContain('LAAP Client')

    const titleBar = document.querySelector('.app-drag')
    expect(titleBar).toBeTruthy()
  })

  it('标题栏包含设置按钮', () => {
    let clicked = false
    render(<TitleBar onSettingsClick={() => { clicked = true }} />)

    const settingsButton = document.querySelector('[title="设置"]')
    expect(settingsButton).toBeTruthy()

    settingsButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    expect(clicked).toBe(true)
  })
})
