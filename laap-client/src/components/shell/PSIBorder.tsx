/**
 * PSIBorder — PSI 呼吸边框
 *
 * 窗口边缘的渐变呼吸光效，颜色随 PSI 阶段变化：
 *   perception  → 蓝色 (观察)
 *   selection   → 金色 (选择)
 *   integration → 紫色 (整合)
 *   learning    → 绿色 (学习)
 *
 * 透明度随 stress 升高而增强（压力越大，光芒越强）。
 */

export interface PSIBorderProps {
  phase?: string
  stress?: number
  className?: string
}

const PHASE_COLORS: Record<string, [string, string]> = {
  perception:  ['rgba(96, 165, 250, 0.5)', 'rgba(59, 130, 246, 0.3)'],
  selection:   ['rgba(251, 191, 36, 0.5)',  'rgba(245, 158, 11, 0.3)'],
  integration: ['rgba(167, 139, 250, 0.5)', 'rgba(124, 58, 237, 0.3)'],
  learning:    ['rgba(52, 211, 153, 0.5)',  'rgba(16, 185, 129, 0.3)'],
}

export function PSIBorder({ phase = 'perception', stress = 0.2, className = '' }: PSIBorderProps) {
  const colors = PHASE_COLORS[phase] ?? PHASE_COLORS.perception
  const baseOpacity = 0.15 + stress * 0.4
  const animationDuration = 3 + (1 - stress) * 3  // stress 高时呼吸更快

  return (
    <div
      className={`psi-border-glow ${className}`}
      style={{
        '--psi-color-1': colors[0],
        '--psi-color-2': colors[1],
        '--psi-glow-opacity': Math.min(baseOpacity, 0.6),
        '--psi-breath-duration': `${animationDuration}s`,
      } as React.CSSProperties}
    />
  )
}

export default PSIBorder
