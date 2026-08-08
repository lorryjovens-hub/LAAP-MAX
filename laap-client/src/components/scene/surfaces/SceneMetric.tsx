/**
 * SceneMetric：metric 类型 surface
 *
 * 显示指标标签、当前值、单位与可选迷你 sparkline。
 */

import { GlassPanel } from '../../glass/GlassPanel'
import type { SceneSurface } from '../../../laap/types'

export interface SceneMetricProps {
  surface: SceneSurface
}

export function SceneMetric({ surface }: SceneMetricProps) {
  const value = surface.value ?? 0
  const unit = surface.unit || ''

  // 生成一个基于当前值的简单 sparkline（仅用于视觉提示）
  const points = Array.from({ length: 12 }, (_, i) => {
    const v = Math.max(0, Math.min(1, value / 100 + (Math.random() - 0.5) * 0.3))
    return `${(i / 11) * 100},${(1 - v) * 24}`
  }).join(' ')

  return (
    <GlassPanel className="p-4 flex flex-col" intensity="sm" radius="var(--laap-radius-md)">
      <span className="text-[10px] text-white/50">{surface.label || surface.title || '指标'}</span>
      <div className="mt-1 flex items-baseline gap-1">
        <span className="text-2xl font-mono text-white/90">{value}</span>
        {unit && <span className="text-xs text-white/40">{unit}</span>}
      </div>
      <svg className="w-full h-6 mt-2" viewBox="0 0 100 24" preserveAspectRatio="none">
        <polyline
          fill="none"
          stroke="var(--laap-secondary)"
          strokeWidth="2"
          points={points}
          opacity="0.7"
        />
      </svg>
    </GlassPanel>
  )
}
