/**
 * SceneLayout：layout 类型 surface
 *
 * 子 surface 容器，展示标题与子节点引用。
 */

import { GlassPanel } from '../../glass/GlassPanel'
import type { SceneSurface } from '../../../laap/types'

export interface SceneLayoutProps {
  surface: SceneSurface
  allSurfaces: Record<string, SceneSurface>
}

export function SceneLayout({ surface, allSurfaces }: SceneLayoutProps) {
  return (
    <GlassPanel className="p-4 flex flex-col gap-3" intensity="sm" radius="var(--laap-radius-md)">
      <span className="text-sm font-medium text-white/90">
        {surface.title || '布局'}
      </span>
      {surface.children && surface.children.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {surface.children.map((childId) => (
            <span
              key={childId}
              className="text-[10px] px-2 py-1 rounded-full bg-white/[0.06] text-white/50 border border-white/[0.08]"
            >
              {allSurfaces[childId]?.title || allSurfaces[childId]?.label || childId}
            </span>
          ))}
        </div>
      )}
    </GlassPanel>
  )
}
