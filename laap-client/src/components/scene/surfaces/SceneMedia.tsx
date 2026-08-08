/**
 * SceneMedia：media 类型 surface
 *
 * 根据扩展名自动判断渲染图片或视频。
 */

import { GlassPanel } from '../../glass/GlassPanel'
import type { SceneSurface } from '../../../laap/types'

export interface SceneMediaProps {
  surface: SceneSurface
}

function isVideoSrc(src: string): boolean {
  return /\.(mp4|webm|mov|mkv|avi|m4v)(\?.*)?$/i.test(src)
}

export function SceneMedia({ surface }: SceneMediaProps) {
  const src = surface.src

  return (
    <GlassPanel className="p-3 flex flex-col gap-2" intensity="sm" radius="var(--laap-radius-md)">
      {src ? (
        isVideoSrc(src) ? (
          <video
            src={src}
            controls
            loop
            className="w-full rounded-lg bg-black/30"
          />
        ) : (
          <img
            src={src}
            alt={surface.alt || surface.caption || '媒体'}
            className="w-full rounded-lg object-cover"
          />
        )
      ) : (
        <div className="w-full aspect-video rounded-lg bg-black/20 flex items-center justify-center text-xs text-white/40">
          无媒体源
        </div>
      )}
      {surface.caption && (
        <span className="text-[10px] text-white/50">{surface.caption}</span>
      )}
    </GlassPanel>
  )
}
