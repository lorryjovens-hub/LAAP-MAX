/**
 * Sparkline — 内联 SVG 迷你折线图（无依赖）
 *
 * 用法:
 *   <Sparkline data={[0.3, 0.5, 0.7, 0.4, 0.8]} width={120} height={32} color="#laap-accent" />
 */

export interface SparklineProps {
  data: number[]
  width?: number
  height?: number
  color?: string
  strokeWidth?: number
  className?: string
  showDot?: boolean
}

export function Sparkline({
  data,
  width = 120,
  height = 32,
  color = '#5b93ff',
  strokeWidth = 1.5,
  className = '',
  showDot = false,
}: SparklineProps) {
  if (!data || data.length < 2) {
    return <svg className={className} width={width} height={height} />
  }

  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1
  const pad = 2

  const xScale = (i: number) => pad + (i / (data.length - 1)) * (width - pad * 2)
  const yScale = (v: number) => height - pad - ((v - min) / range) * (height - pad * 2)

  const points = data.map((v, i) => `${xScale(i).toFixed(1)},${yScale(v).toFixed(1)}`)
  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p}`).join(' ')

  // Gradient fill under the line
  const gradientId = `sparkline-fill-${color.replace('#', '')}`

  return (
    <svg className={className} width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.2" />
          <stop offset="100%" stopColor={color} stopOpacity="0.02" />
        </linearGradient>
      </defs>
      {/* Area fill */}
      <path
        d={`${pathD} L${xScale(data.length - 1)},${height - pad} L${xScale(0)},${height - pad} Z`}
        fill={`url(#${gradientId})`}
      />
      {/* Line */}
      <path d={pathD} fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
      {/* End dot */}
      {showDot && (
        <circle
          cx={xScale(data.length - 1)}
          cy={yScale(data[data.length - 1])}
          r={2.5}
          fill={color}
          stroke="rgba(0,0,0,0.3)"
          strokeWidth={1}
        />
      )}
    </svg>
  )
}

/**
 * MiniBarChart — 迷你柱状图
 *
 * 用法:
 *   <MiniBarChart data={[10, 20, 15, 30]} width={120} height={32} color="#laap-accent" />
 */

export interface MiniBarChartProps {
  data: number[]
  width?: number
  height?: number
  color?: string
  className?: string
  maxValue?: number
}

export function MiniBarChart({
  data,
  width = 120,
  height = 32,
  color = '#5b93ff',
  className = '',
  maxValue,
}: MiniBarChartProps) {
  if (!data || data.length === 0) {
    return <svg className={className} width={width} height={height} />
  }

  const max = maxValue != null ? maxValue : (Math.max(...data) || 1)
  const pad = 1
  const barWidth = Math.max(2, (width - pad * 2) / data.length - 1)

  return (
    <svg className={className} width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {data.map((v, i) => {
        const barH = (v / max) * (height - pad * 2)
        const x = pad + i * (barWidth + 1)
        const y = height - pad - barH
        return (
          <rect
            key={i}
            x={x}
            y={y}
            width={barWidth}
            height={Math.max(barH, 1)}
            rx={1}
            fill={color}
            opacity={0.7 + (v / max) * 0.3}
          />
        )
      })}
    </svg>
  )
}

/**
 * TrendIndicator — 趋势箭头指示器
 */
export interface TrendIndicatorProps {
  value: number  // 正数=上升，负数=下降
  className?: string
}

export function TrendIndicator({ value, className = '' }: TrendIndicatorProps) {
  const isUp = value > 0
  const isDown = value < 0
  const abs = Math.abs(value)

  return (
    <span className={`inline-flex items-center gap-0.5 text-[10px] font-mono ${
      isUp ? 'text-emerald-400' : isDown ? 'text-red-400' : 'text-white/50'
    } ${className}`}>
      {isUp ? '↑' : isDown ? '↓' : '→'}
      {abs.toFixed(1)}
    </span>
  )
}
