/**
 * SceneImage：image 类型 surface
 */

import { GlassPanel } from '../../glass/GlassPanel'
import type { SceneSurface } from '../../../laap/types'

export interface SceneImageProps {
  surface: SceneSurface
}

export function SceneImage({ surface }: SceneImageProps) {
  return (
    <GlassPanel className="p-3 flex flex-col gap-2" intensity="sm" radius="var(--laap-radius-md)">
      {surface.src ? (
        <img
          src={surface.src}
          alt={surface.alt || surface.title || '图片'}
          className="w-full rounded-lg object-cover"
        />
      ) : (
        <div className="w-full aspect-video rounded-lg bg-black/20 flex items-center justify-center text-xs text-white/40">
          无图片源
        </div>
      )}
      {surface.alt && <span className="text-[10px] text-white/50">{surface.alt}</span>}
    </GlassPanel>
  )
}
