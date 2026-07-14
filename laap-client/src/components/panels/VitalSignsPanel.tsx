/**
 * VitalSignsPanel：数字生命体征面板
 *
 * 展示 PSI 循环阶段、需求仪表盘（好奇心/信任/胜任）、5D 情感条形图，
 * 所有数值均从 store 实时读取并带有平滑过渡动画。
 * 每个指标区块均使用 GlassPanel 单独包装。
 */

import { GlassPanel } from '../glass/GlassPanel'
import type { PSICycle, VitalSigns } from '../../laap/types'

export interface VitalSignsPanelProps {
  vitalSigns: VitalSigns
  psiCycle: PSICycle
  className?: string
}

const PSI_PHASES: { key: PSICycle['phase']; label: string }[] = [
  { key: 'perception', label: '感知' },
  { key: 'selection', label: '选择' },
  { key: 'integration', label: '整合' },
  { key: 'learning', label: '学习' },
]

/**
 * 指标卡片包装器
 */
function MetricCard({
  children,
  className = '',
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <GlassPanel
      className={`p-3 ${className}`}
      intensity="sm"
      radius="var(--laap-radius-sm)"
    >
      {children}
    </GlassPanel>
  )
}

/**
 * 径向仪表盘
 */
function RadialGauge({
  label,
  value,
  color,
}: {
  label: string
  value: number
  color: string
}) {
  const radius = 28
  const circumference = 2 * Math.PI * radius
  const clamped = Math.min(1, Math.max(0, value))
  const offset = circumference * (1 - clamped)
  const percent = Math.round(clamped * 100)

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-16 h-16">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 64 64">
          <circle
            cx="32"
            cy="32"
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth="6"
          />
          <circle
            cx="32"
            cy="32"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="transition-all duration-700 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center text-xs font-mono text-white/90">
          {percent}%
        </div>
      </div>
      <span className="text-[10px] text-white/60 text-center leading-tight">{label}</span>
    </div>
  )
}

/**
 * 5D 情感五轴条形图
 */
function EmotionAxes({ vitalSigns }: { vitalSigns: VitalSigns }) {
  const axes = [
    { key: 'pleasure', label: '愉悦 Pleasure', color: '#ff6b6b' },
    { key: 'arousal', label: '唤醒 Arousal', color: '#a07cff' },
    { key: 'dominance', label: '支配 Dominance', color: '#00c2ff' },
    { key: 'sociality', label: '社交 Sociality', color: '#7cff7c' },
    { key: 'stress', label: '压力 Stress', color: '#ff9f43' },
  ] as const

  return (
    <div className="space-y-2">
      {axes.map((axis) => {
        const value = vitalSigns[axis.key] ?? 0
        const percent = Math.round(Math.min(1, Math.max(0, value)) * 100)
        return (
          <div key={axis.key} className="flex items-center gap-2">
            <span className="w-24 text-[10px] text-white/60 truncate">{axis.label}</span>
            <div className="flex-1 h-2 rounded-full bg-white/[0.08] overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500 ease-out"
                style={{
                  width: `${percent}%`,
                  background: axis.color,
                  boxShadow: `0 0 6px ${axis.color}`,
                }}
              />
            </div>
            <span className="w-7 text-[10px] font-mono text-white/80 text-right">{percent}</span>
          </div>
        )
      })}
    </div>
  )
}

export function VitalSignsPanel({
  vitalSigns,
  psiCycle,
  className = '',
}: VitalSignsPanelProps) {
  const activeIndex = PSI_PHASES.findIndex((p) => p.key === psiCycle.phase)

  return (
    <GlassPanel
      className={`flex flex-col gap-4 p-5 ${className}`}
      intensity="md"
      radius="var(--laap-radius-md)"
    >
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold bg-gradient-to-r from-laap-accent to-laap-secondary bg-clip-text text-transparent">
          生命体征
        </h3>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/[0.08] text-white/50 font-mono">
          VITAL
        </span>
      </div>

      {/* PSI 阶段指示器 */}
      <MetricCard>
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between text-[10px] text-white/50">
            <span>PSI 循环</span>
            <span className="font-mono text-white/70">
              {Math.round(psiCycle.progress * 100)}%
            </span>
          </div>
          <div className="relative flex items-center justify-between">
            {PSI_PHASES.map((phase, index) => {
              const isActive = index === activeIndex
              const isCompleted = index < activeIndex
              return (
                <div key={phase.key} className="flex flex-col items-center gap-1.5 z-10">
                  <div
                    className={`w-3 h-3 rounded-full border-2 transition-all duration-300 ${
                      isActive
                        ? 'bg-laap-accent border-laap-accent shadow-[0_0_8px_#7c7cff] scale-110'
                        : isCompleted
                          ? 'bg-laap-secondary/50 border-laap-secondary'
                          : 'bg-transparent border-white/20'
                    }`}
                  />
                  <span
                    className={`text-[9px] transition-colors duration-300 ${
                      isActive ? 'text-white/90' : 'text-white/40'
                    }`}
                  >
                    {phase.label}
                  </span>
                </div>
              )
            })}
            <div className="absolute left-0 right-0 top-[5px] h-px bg-white/[0.08] -z-0" />
          </div>
          <div className="h-1 w-full rounded-full bg-white/[0.08] overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-laap-accent to-laap-secondary transition-all duration-300"
              style={{ width: `${Math.round(psiCycle.progress * 100)}%` }}
            />
          </div>
          <div className="text-center text-[10px] text-white/60">
            当前阶段：
            <span className="text-white/90 ml-1">
              {PSI_PHASES[activeIndex]?.label ?? '感知'}
            </span>
          </div>
        </div>
      </MetricCard>

      {/* 需求仪表盘 */}
      <MetricCard>
        <div className="grid grid-cols-3 gap-2">
          <RadialGauge label="好奇心" value={vitalSigns.curiosity} color="#7c7cff" />
          <RadialGauge label="信任感" value={vitalSigns.trust} color="#00f5d4" />
          <RadialGauge label="胜任感" value={vitalSigns.competence} color="#ffd166" />
        </div>
      </MetricCard>

      {/* 5D 情感 */}
      <MetricCard>
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] text-white/60">5D 情感状态</span>
        </div>
        <EmotionAxes vitalSigns={vitalSigns} />
      </MetricCard>

      {/* 人格轮廓敏感度 */}
      <MetricCard>
        <div className="text-[10px] text-white/40 mb-1">情感动力学人格轮廓敏感度</div>
        <div className="text-xs font-mono text-white/70">[2.5, 2.0, 1.5, 2.0, 2.2]</div>
      </MetricCard>
    </GlassPanel>
  )
}
