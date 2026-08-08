/**
 * RateBufferPanel：高频事件缓冲区可视化面板
 *
 * 展示去重计数、优先级队列深度、聚合窗口时长、最近 batch 大小，
 * 使用动画条形图与数字滚动效果。
 */

import { GlassPanel } from '../glass/GlassPanel'
import type { RateBufferStats } from '../../laap/types'

export interface RateBufferPanelProps {
  stats: RateBufferStats
  className?: string
}

/**
 * 单项指标条
 */
function MetricBar({
  label,
  value,
  max,
  color,
  suffix,
}: {
  label: string
  value: number
  max: number
  color: string
  suffix?: string
}) {
  const clamped = Math.min(1, Math.max(0, value / max))
  const displayValue = Number.isFinite(value) ? Math.round(value) : 0

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between text-xs text-white/70">
        <span>{label}</span>
        <span className="font-mono text-white/90">
          {displayValue}
          {suffix ? <span className="text-white/50 ml-0.5">{suffix}</span> : null}
        </span>
      </div>
      <div className="h-2 w-full rounded-full bg-white/[0.08] overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-300 ease-out"
          style={{
            width: `${clamped * 100}%`,
            background: color,
            boxShadow: `0 0 8px ${color}`,
          }}
        />
      </div>
    </div>
  )
}

export function RateBufferPanel({ stats, className = '' }: RateBufferPanelProps) {
  return (
    <GlassPanel
      className={`flex flex-col gap-4 p-5 ${className}`}
      intensity="md"
      radius="var(--laap-radius-md)"
    >
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-white/90">RateBuffer 实时监控</h3>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/[0.08] text-white/50 font-mono">
          PSI
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4">
        <MetricBar
          label="去重计数"
          value={stats.dedupCount}
          max={5000}
          color="var(--laap-status-warn)"
        />
        <MetricBar
          label="队列深度"
          value={stats.queueDepth}
          max={60}
          color="var(--laap-accent)"
        />
        <MetricBar
          label="最近 Batch 大小"
          value={stats.batchSize}
          max={60}
          color="var(--laap-secondary)"
        />
        <MetricBar
          label="聚合窗口时长"
          value={stats.aggregationWindowMs}
          max={200}
          suffix="ms"
          color="var(--laap-status-info)"
        />
      </div>

      <div className="grid grid-cols-2 gap-3 pt-1">
        <div className="rounded-xl bg-white/[0.04] px-3 py-2 border border-white/[0.06]">
          <div className="text-[10px] text-white/40 mb-1">去重计数</div>
          <div className="text-lg font-mono text-white/90 tabular-nums">
            {stats.dedupCount}
          </div>
        </div>
        <div className="rounded-xl bg-white/[0.04] px-3 py-2 border border-white/[0.06]">
          <div className="text-[10px] text-white/40 mb-1">队列深度</div>
          <div className="text-lg font-mono text-white/90 tabular-nums">
            {stats.queueDepth}
          </div>
        </div>
        <div className="rounded-xl bg-white/[0.04] px-3 py-2 border border-white/[0.06]">
          <div className="text-[10px] text-white/40 mb-1">Batch 大小</div>
          <div className="text-lg font-mono text-white/90 tabular-nums">
            {stats.batchSize}
          </div>
        </div>
        <div className="rounded-xl bg-white/[0.04] px-3 py-2 border border-white/[0.06]">
          <div className="text-[10px] text-white/40 mb-1">窗口时长</div>
          <div className="text-lg font-mono text-white/90 tabular-nums">
            {stats.aggregationWindowMs}
            <span className="text-xs text-white/40 ml-0.5">ms</span>
          </div>
        </div>
      </div>
    </GlassPanel>
  )
}
