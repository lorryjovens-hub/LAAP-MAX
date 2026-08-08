/**
 * 生命体征面板冒烟测试
 *
 * 通过更新 store 中的 vitalSigns，验证 VitalSignsPanel 正确渲染最新指标。
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { render } from '@testing-library/react'
import { VitalSignsPanel } from '../src/components/panels/VitalSignsPanel'
import { useLaapStore } from '../src/store/laapStore'

const defaultVitalSigns = {
  curiosity: 0.5,
  trust: 0.5,
  competence: 0.5,
  pleasure: 0.5,
  arousal: 0.5,
  dominance: 0.5,
  sociality: 0.5,
  stress: 0.2,
}

describe('生命体征', () => {
  beforeEach(() => {
    useLaapStore.setState({ vitalSigns: defaultVitalSigns })
  })

  it('好奇心更新后 VitalSignsPanel 显示新数值', () => {
    useLaapStore.getState().updateVitalSigns({ curiosity: 0.83 })
    const vitalSigns = useLaapStore.getState().vitalSigns

    render(<VitalSignsPanel vitalSigns={vitalSigns} psiCycle={{ phase: 'perception', progress: 0 }} />)

    expect(document.body.textContent).toContain('83%')
  })

  it('信任感更新后 VitalSignsPanel 显示新数值', () => {
    useLaapStore.getState().updateVitalSigns({ trust: 0.62 })
    const vitalSigns = useLaapStore.getState().vitalSigns

    render(<VitalSignsPanel vitalSigns={vitalSigns} psiCycle={{ phase: 'selection', progress: 0.5 }} />)

    expect(document.body.textContent).toContain('62%')
  })
})
