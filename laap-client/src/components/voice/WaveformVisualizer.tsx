/**
 * WaveformVisualizer：播放 TTS 音频时显示的波形动画。
 *
 * 当传入 analyserRef 且处于 active 状态时，从 AnalyserNode 读取真实频域数据
 * 驱动波形条高度；否则回退到基于 audioLevel 的 CSS 动画模拟。
 */

import { useEffect, useMemo, useRef, useState } from 'react'

export interface WaveformVisualizerProps {
  active: boolean
  audioLevel?: number
  barCount?: number
  className?: string
  /** 由 useTtsAudio 提供的真实音频分析节点 */
  analyserRef?: React.RefObject<AnalyserNode | null>
}

export function WaveformVisualizer({
  active,
  audioLevel = 0.5,
  barCount = 24,
  className = '',
  analyserRef,
}: WaveformVisualizerProps) {
  const bars = useMemo(() => Array.from({ length: barCount }), [barCount])
  const [realHeights, setRealHeights] = useState<number[] | null>(null)
  const rafRef = useRef<number | null>(null)

  useEffect(() => {
    const analyser = analyserRef?.current
    if (!active || !analyser) {
      setRealHeights(null)
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current)
        rafRef.current = null
      }
      return
    }

    const data = new Uint8Array(analyser.frequencyBinCount)
    const step = Math.max(1, Math.floor(data.length / barCount))

    const loop = () => {
      if (!analyserRef?.current) return
      analyserRef.current.getByteFrequencyData(data)
      const heights: number[] = []
      for (let i = 0; i < barCount; i += 1) {
        const idx = Math.min(data.length - 1, i * step)
        const value = data[idx] / 255
        heights.push(value)
      }
      setRealHeights(heights)
      rafRef.current = requestAnimationFrame(loop)
    }

    rafRef.current = requestAnimationFrame(loop)

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current)
        rafRef.current = null
      }
    }
  }, [active, analyserRef, barCount])

  const hasRealAudio = realHeights !== null

  return (
    <div className={`flex items-center justify-center gap-[2px] h-8 ${className}`}>
      {bars.map((_, i) => {
        const delay = i * 40
        const realHeight = hasRealAudio ? (realHeights[i] ?? 0) : null
        const baseHeight = hasRealAudio
          ? 10 + (realHeight ?? 0) * 90
          : active
            ? 20 + Math.random() * 60 * (audioLevel || 0.5)
            : 4

        return (
          <span
            key={i}
            className={`w-1 rounded-full transition-all duration-75 ${
              active ? 'bg-laap-secondary' : 'bg-white/20'
            } ${active && !hasRealAudio ? 'waveform-bar' : ''}`}
            style={{
              height: active ? `${baseHeight}%` : '4px',
              animationDelay: `${delay}ms`,
            }}
          />
        )
      })}
    </div>
  )
}
