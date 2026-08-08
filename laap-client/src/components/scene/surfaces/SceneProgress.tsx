/**
 * SceneProgress：progress 类型 surface
 */

import { GlassPanel } from '../../glass/GlassPanel'
import type { SceneSurface } from '../../../laap/types'

export interface SceneProgressProps {
  surface: SceneSurface
}

export function SceneProgress({ surface }: SceneProgressProps) {
  const max = surface.max ?? 100
  const value = Math.min(max, Math.max(0, surface.value ?? 0))
  const percent = max > 0 ? (value / max) * 100 : 0

  return (
    <GlassPanel className="p-4 flex flex-col gap-2" intensity="sm" radius="var(--laap-radius-md)">
      <div className="flex items-center justify-between text-xs text-white/70">
        <span>{surface.label || surface.title || '进度'}</span>
        <span className="font-mono">{Math.round(percent)}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-white/[0.08] overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-laap-accent to-laap-secondary transition-all duration-500"
          style={{ width: `${percent}%` }}
        />
      </div>
    </GlassPanel>
  )
}
