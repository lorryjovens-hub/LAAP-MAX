/**
 * SceneRenderer：Scene Protocol 渲染器
 *
 * 订阅 useLaapStore 中的 scene.surfaces，根据 surface.kind 渲染为不同组件。
 * 所有 surface 组件均位于 ./surfaces 目录并按 kind 拆分。
 */

import { useLaap } from '../../hooks/useLaap'
import { GlassPanel } from '../glass/GlassPanel'
import { CodePanel } from '../code/CodePanel'
import {
  SceneMetric,
  SceneMedia,
  SceneImage,
  SceneText,
  SceneChoice,
  SceneProgress,
  SceneLayout,
  SceneWeather,
  SceneTerminal,
} from './surfaces'
import type { SceneSurface, CodeSurface, DiffSurface } from '../../laap/types'

function SurfaceRenderer({
  surface,
  allSurfaces,
}: {
  surface: SceneSurface
  allSurfaces: Record<string, SceneSurface>
}) {
  switch (surface.kind) {
    case 'metric':
      return <SceneMetric surface={surface} />
    case 'media':
      return <SceneMedia surface={surface} />
    case 'image':
      return <SceneImage surface={surface} />
    case 'text':
      return <SceneText surface={surface} />
    case 'choice':
      return <SceneChoice surface={surface} />
    case 'progress':
      return <SceneProgress surface={surface} />
    case 'layout':
      return <SceneLayout surface={surface} allSurfaces={allSurfaces} />
    case 'weather':
      return <SceneWeather surface={surface} />
    case 'terminal':
      return <SceneTerminal surface={surface} />
    case 'code':
    case 'diff':
      return <CodePanel surface={surface as CodeSurface | DiffSurface} />
    default:
      return (
        <GlassPanel className="p-4" intensity="sm" radius="var(--laap-radius-md)">
          <span className="text-[10px] text-white/40">未知 surface 类型：{surface.kind}</span>
          <p className="text-sm text-white/60 mt-1">{surface.content}</p>
        </GlassPanel>
      )
  }
}

export interface SceneRendererProps {
  className?: string
}

export function SceneRenderer({ className = '' }: SceneRendererProps) {
  const { scene } = useLaap()
  const surfaces = Object.values(scene.surfaces).sort((a, b) => b.updatedAt - a.updatedAt)

  return (
    <GlassPanel
      className={`overflow-hidden flex flex-col ${className}`}
      intensity="sm"
      radius="var(--laap-radius-md)"
    >
      <div className="shrink-0 px-4 py-3 border-b border-white/[0.08]">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-white/90">场景渲染</h2>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/[0.08] text-white/50 font-mono">
            {surfaces.length}
          </span>
        </div>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto p-4">
        {surfaces.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-white/30 text-sm">
            <p>暂无场景面片</p>
            <p className="text-xs mt-1">等待 scene.patch 事件...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {surfaces.map((surface) => (
              <SurfaceRenderer
                key={surface.id}
                surface={surface}
                allSurfaces={scene.surfaces}
              />
            ))}
          </div>
        )}
      </div>
    </GlassPanel>
  )
}
