/**
 * VoiceOrb：语音状态可视化球体。
 *
 * 四种状态动画：
 * - idle：缓慢呼吸缩放
 * - listening：多层脉冲扩散
 * - thinking：旋转光环
 * - speaking：波形跳动
 */

import { useMemo } from 'react'
import type { VoiceStatus } from '../../laap/types'

export interface VoiceOrbProps {
  status: VoiceStatus
  audioLevel?: number
  size?: number
  className?: string
  continuous?: boolean
}

export function VoiceOrb({ status, audioLevel = 0, size = 96, className = '', continuous = false }: VoiceOrbProps) {
  const isActive = status !== 'idle'

  const bars = useMemo(() => Array.from({ length: 5 }), [])

  return (
    <div
      className={`relative flex items-center justify-center ${className}`}
      style={{ width: size, height: size }}
    >
      {/* 外层脉冲环 */}
      {status === 'listening' && (
        <>
          <span className="voice-orb-pulse absolute inset-0 rounded-full border border-laap-secondary/40" style={{ animationDelay: '0ms' }} />
          <span className="voice-orb-pulse absolute inset-0 rounded-full border border-laap-secondary/30" style={{ animationDelay: '600ms' }} />
        </>
      )}

      {/* 连续监听模式轻微脉冲提示 */}
      {continuous && status === 'idle' && (
        <span className="voice-orb-pulse-soft absolute inset-0 rounded-full border border-laap-secondary/20" />
      )}

      {/* 旋转光环 */}
      {status === 'thinking' && (
        <span className="voice-orb-spin absolute inset-[-8px] rounded-full border-2 border-dashed border-laap-accent/50" />
      )}

      {/* 核心球体 */}
      <div
        className={`relative z-10 rounded-full flex items-center justify-center transition-colors duration-300 ${
          isActive ? 'voice-orb-breathe bg-laap-accent/20 shadow-[0_0_24px_rgba(124,124,255,0.35)]' : 'bg-white/[0.06]'
        }`}
        style={{ width: size * 0.55, height: size * 0.55 }}
      >
        {/* 波形条 */}
        {status === 'speaking' && (
          <div className="flex items-center gap-[3px] h-5">
            {bars.map((_, i) => (
              <span
                key={i}
                className="voice-orb-bar w-1 rounded-full bg-laap-secondary"
                style={{
                  height: `${20 + (audioLevel || 0.3) * 40}%`,
                  animationDelay: `${i * 80}ms`,
                }}
              />
            ))}
          </div>
        )}

        {status === 'idle' && <div className="w-2 h-2 rounded-full bg-white/40" />}
        {(status === 'listening' || status === 'thinking') && (
          <div className="w-3 h-3 rounded-full bg-laap-secondary shadow-[0_0_12px_#00f5d4]" />
        )}
      </div>
    </div>
  )
}
