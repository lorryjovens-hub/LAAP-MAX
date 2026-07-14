/**
 * SceneChoice：choice 类型 surface
 *
 * 展示问题与选项按钮组。
 */

import { GlassPanel } from '../../glass/GlassPanel'
import type { SceneSurface } from '../../../laap/types'

export interface SceneChoiceProps {
  surface: SceneSurface
}

export function SceneChoice({ surface }: SceneChoiceProps) {
  return (
    <GlassPanel className="p-4 flex flex-col gap-3" intensity="sm" radius="var(--laap-radius-md)">
      {surface.content && (
        <p className="text-sm text-white/80">{surface.content}</p>
      )}
      <div className="flex flex-wrap gap-2">
        {surface.options?.map((option) => {
          const selected = surface.selected === option
          return (
            <button
              key={option}
              type="button"
              className={`px-3 py-1.5 rounded-lg text-xs border transition-colors ${
                selected
                  ? 'bg-laap-accent/20 border-laap-accent/40 text-white/90'
                  : 'bg-white/[0.05] border-white/[0.08] text-white/70 hover:bg-white/[0.08]'
              }`}
            >
              {option}
            </button>
          )
        })}
      </div>
    </GlassPanel>
  )
}
