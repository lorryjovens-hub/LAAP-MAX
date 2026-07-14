import React, { useEffect, useRef } from 'react'

interface Props {
  size?: number
  emotion?: string
  isSpeaking?: boolean
  onClick?: () => void
}

const Avatar: React.FC<Props> = ({ size = 120, emotion = 'neutral', isSpeaking = false, onClick }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const pulseRef = useRef<number>(0)

  // Draw a stylized avatar indicator (pulsing ring + emoji face)
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const dpr = window.devicePixelRatio || 1
    canvas.width = size * dpr
    canvas.height = size * dpr
    ctx.scale(dpr, dpr)

    let running = true

    const draw = () => {
      if (!running) return
      ctx.clearRect(0, 0, size, size)
      const cx = size / 2
      const cy = size / 2
      const r = size * 0.42

      // Glow ring
      pulseRef.current += 0.02
      const pulse = isSpeaking
        ? 0.3 + Math.sin(pulseRef.current * 3) * 0.15
        : 0.2 + Math.sin(pulseRef.current * 0.8) * 0.05

      const gradient = ctx.createRadialGradient(cx, cy, r * 0.5, cx, cy, r * 1.2)
      gradient.addColorStop(0, `rgba(0,212,170,${pulse * 0.3})`)
      gradient.addColorStop(0.5, `rgba(0,212,170,${pulse * 0.15})`)
      gradient.addColorStop(1, 'rgba(0,212,170,0)')
      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.arc(cx, cy, r * 1.2, 0, Math.PI * 2)
      ctx.fill()

      // Outer ring
      ctx.strokeStyle = `rgba(0,212,170,${0.3 + pulse * 0.3})`
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.arc(cx, cy, r + 4, 0, Math.PI * 2)
      ctx.stroke()

      // Main circle
      ctx.fillStyle = '#16213e'
      ctx.strokeStyle = 'rgba(0,212,170,0.5)'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.arc(cx, cy, r, 0, Math.PI * 2)
      ctx.fill()
      ctx.stroke()

      // Inner glow
      const ig = ctx.createRadialGradient(cx - r * 0.3, cy - r * 0.3, 0, cx, cy, r)
      ig.addColorStop(0, 'rgba(0,212,170,0.1)')
      ig.addColorStop(1, 'rgba(0,212,170,0)')
      ctx.fillStyle = ig
      ctx.beginPath()
      ctx.arc(cx, cy, r, 0, Math.PI * 2)
      ctx.fill()

      // Face: eyes
      const eyeY = cy - r * 0.1
      const eyeSpacing = r * 0.25
      const eyeR = r * 0.08

      // Eyes
      ctx.fillStyle = '#00d4aa'
      ctx.beginPath()
      ctx.arc(cx - eyeSpacing, eyeY, eyeR, 0, Math.PI * 2)
      ctx.fill()
      ctx.beginPath()
      ctx.arc(cx + eyeSpacing, eyeY, eyeR, 0, Math.PI * 2)
      ctx.fill()

      // Eye shine
      ctx.fillStyle = 'rgba(255,255,255,0.4)'
      ctx.beginPath()
      ctx.arc(cx - eyeSpacing - eyeR * 0.3, eyeY - eyeR * 0.3, eyeR * 0.4, 0, Math.PI * 2)
      ctx.fill()
      ctx.beginPath()
      ctx.arc(cx + eyeSpacing - eyeR * 0.3, eyeY - eyeR * 0.3, eyeR * 0.4, 0, Math.PI * 2)
      ctx.fill()

      // Mouth based on emotion
      const mouthY = cy + r * 0.2
      ctx.strokeStyle = '#00d4aa'
      ctx.lineWidth = 2
      ctx.lineCap = 'round'

      if (emotion === 'happy' || isSpeaking) {
        ctx.beginPath()
        ctx.arc(cx, mouthY + 2, r * 0.15, 0.1, Math.PI - 0.1)
        ctx.stroke()
      } else if (emotion === 'sad') {
        ctx.beginPath()
        ctx.arc(cx, mouthY + 8, r * 0.15, Math.PI + 0.1, -0.1)
        ctx.stroke()
      } else {
        ctx.beginPath()
        ctx.moveTo(cx - r * 0.12, mouthY)
        ctx.lineTo(cx + r * 0.12, mouthY)
        ctx.stroke()
      }

      // Speaking indicator: waves
      if (isSpeaking) {
        ctx.strokeStyle = `rgba(0,212,170,${0.2 + Math.sin(pulseRef.current * 4) * 0.1})`
        ctx.lineWidth = 1.5
        for (let i = 1; i <= 2; i++) {
          const waveR = r * 0.7 + i * 10 + Math.sin(pulseRef.current * 2 + i) * 3
          ctx.beginPath()
          ctx.arc(cx, cy, waveR, -0.3, 0.3)
          ctx.stroke()
        }
      }

      pulseRef.current = performance.now() / 1000
      requestAnimationFrame(draw)
    }

    draw()
    return () => { running = false }
  }, [size, emotion, isSpeaking])

  return (
    <canvas
      ref={canvasRef}
      onClick={onClick}
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        cursor: onClick ? 'pointer' : 'default',
        display: 'block',
      }}
    />
  )
}

export default Avatar
