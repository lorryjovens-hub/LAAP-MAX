/**
 * SceneText：text 类型 surface
 */

import { GlassPanel } from '../../glass/GlassPanel'
import type { SceneSurface } from '../../../laap/types'

export interface SceneTextProps {
  surface: SceneSurface
}

export function SceneText({ surface }: SceneTextProps) {
  return (
    <GlassPanel className="p-4" intensity="sm" radius="var(--laap-radius-md)">
      <p className="text-sm text-white/80 whitespace-pre-wrap">
        {surface.content || '（空文本）'}
      </p>
    </GlassPanel>
  )
}
