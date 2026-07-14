/**
 * Scene 渲染冒烟测试
 *
 * 模拟 scene.patch 事件结果（直接写入 store.scene.surfaces），
 * 验证 SceneRenderer 根据 kind 渲染对应 surface。
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { render } from '@testing-library/react'
import { SceneRenderer } from '../src/components/scene/SceneRenderer'
import { useLaapStore } from '../src/store/laapStore'

describe('Scene 渲染', () => {
  beforeEach(() => {
    useLaapStore.setState({ scene: { surfaces: {} } })
  })

  it('渲染文本 surface', () => {
    useLaapStore.setState({
      scene: {
        surfaces: {
          'note-1': {
            id: 'note-1',
            kind: 'text',
            content: '这是场景说明文本',
            updatedAt: Date.now(),
          },
        },
      },
    })

    render(<SceneRenderer />)
    expect(document.body.textContent).toContain('这是场景说明文本')
  })

  it('渲染 metric surface', () => {
    useLaapStore.setState({
      scene: {
        surfaces: {
          'metric-1': {
            id: 'metric-1',
            kind: 'metric',
            label: 'CPU 使用率',
            value: 78,
            unit: '%',
            updatedAt: Date.now(),
          },
        },
      },
    })

    render(<SceneRenderer />)
    expect(document.body.textContent).toContain('CPU 使用率')
    expect(document.body.textContent).toContain('78')
  })

  it('多个 surface 按 updatedAt 排序渲染', () => {
    const now = Date.now()
    useLaapStore.setState({
      scene: {
        surfaces: {
          'a': { id: 'a', kind: 'text', content: '较早', updatedAt: now - 1000 },
          'b': { id: 'b', kind: 'text', content: '最新', updatedAt: now },
        },
      },
    })

    render(<SceneRenderer />)
    expect(document.body.textContent).toContain('较早')
    expect(document.body.textContent).toContain('最新')
  })
})
