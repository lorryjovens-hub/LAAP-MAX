/**
 * EmotionIndicator — 情绪状态指示器
 *
 * 显示在底部栏右侧，展示当前主导情绪 + 需求强度。
 * 颜色脉冲动画 + emoji 表情，让界面有「活着」的感觉。
 */

export interface EmotionIndicatorProps {
  /** 当前主导情绪 */
  dominant?: string
  /** 各项生命体征 (0-1) */
  vitalSigns?: Record<string, number>
  /** 是否正在思考/说话 */
  isActive?: boolean
}

const EMOTION_CONFIG: Record<string, { emoji: string; color: string; label: string }> = {
  curiosity:  { emoji: '🔍', color: '#60a5fa', label: '好奇' },
  trust:      { emoji: '🤝', color: '#34d399', label: '信任' },
  competence: { emoji: '⚡', color: '#a78bfa', label: '胜任' },
  pleasure:   { emoji: '😊', color: '#f472b6', label: '愉悦' },
  arousal:    { emoji: '🔥', color: '#fb923c', label: '兴奋' },
  dominance:  { emoji: '💪', color: '#818cf8', label: '主导' },
  sociality:  { emoji: '💬', color: '#2dd4bf', label: '社交' },
  stress:     { emoji: '🌊', color: '#f87171', label: '压力' },
}

function getDominant(vitals: Record<string, number> = {}): string {
  let maxV = 0, maxK = 'curiosity'
  for (const [k, v] of Object.entries(vitals)) {
    if (v > maxV) { maxV = v; maxK = k }
  }
  return maxK
}

export function EmotionIndicator({ dominant, vitalSigns = {}, isActive }: EmotionIndicatorProps) {
  const top = dominant || getDominant(vitalSigns)
  const config = EMOTION_CONFIG[top] ?? EMOTION_CONFIG.curiosity

  // Building a mini mood bar
  const moodKeys = ['curiosity', 'pleasure', 'trust', 'stress'] as const
  const bars = moodKeys.map((k) => ({
    key: k,
    value: vitalSigns[k] ?? 0.5,
    color: EMOTION_CONFIG[k]?.color ?? '#666',
  }))

  return (
    <div className="flex items-center gap-2" title={`主导情绪: ${config.label}`}>
      {/* Emotion dot */}
      <span
        className="mood-indicator"
        style={{
          backgroundColor: `${config.color}15`,
          borderColor: `${config.color}30`,
          borderWidth: 1,
          borderStyle: 'solid',
        }}
      >
        <span
          className="mood-indicator-dot"
          style={{
            backgroundColor: config.color,
            animationDuration: isActive ? '1.2s' : '2.5s',
          }}
        />
        <span style={{ color: config.color }}>{config.emoji}</span>
        <span style={{ color: `${config.color}cc` }}>{config.label}</span>
      </span>

      {/* Mini bars */}
      <div className="flex items-center gap-1">
        {bars.map(({ key, value, color }) => (
          <div key={key} className="flex flex-col items-center gap-0.5" title={`${key}: ${(value * 100).toFixed(0)}%`}>
            <div
              className="w-1 rounded-full transition-all duration-700"
              style={{
                height: `${Math.max(3, value * 16)}px`,
                backgroundColor: color,
                opacity: 0.3 + value * 0.5,
              }}
            />
          </div>
        ))}
      </div>
    </div>
  )
}

export default EmotionIndicator
