import { forwardRef, useEffect, useState } from 'react'
import { supportsLaapLiquidGlass } from './LiquidGlass'

export interface GlassButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * 是否启用液态玻璃 SVG 滤镜。
   */
  liquidGlass?: boolean
}

/**
 * 胶囊形玻璃按钮。
 *
 * hover / active 状态提供缩放与发光反馈；
 * 支持液态玻璃滤镜，不支持时回退到 backdrop-filter。
 */
export const GlassButton = forwardRef<HTMLButtonElement, GlassButtonProps>(
  function GlassButton({ children, className = '', liquidGlass = false, style, ...rest }, ref) {
    const [svgOk, setSvgOk] = useState(false)

    useEffect(() => {
      if (liquidGlass) {
        setSvgOk(supportsLaapLiquidGlass())
      }
    }, [liquidGlass])

    const glassStyle: React.CSSProperties = {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '8px 20px',
      borderRadius: 'var(--laap-radius-pill)',
      border: '1px solid rgba(255, 255, 255, 0.10)',
      background: 'rgba(0, 0, 0, 0.12)',
      color: 'var(--laap-text-primary)',
      fontFamily: 'var(--laap-font-sans)',
      fontSize: '14px',
      fontWeight: 500,
      cursor: 'pointer',
      transition:
        'transform 0.18s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.18s ease, background 0.18s ease',
      boxShadow:
        'inset 0 1px 0 rgba(255, 255, 255, 0.18), 0 4px 14px rgba(0, 0, 0, 0.18)',
      backdropFilter: liquidGlass && svgOk ? 'url(#laap-liquid-glass-filter) saturate(1)' : 'blur(12px) saturate(1.8) brightness(1.16)',
      WebkitBackdropFilter:
        liquidGlass && svgOk ? 'url(#laap-liquid-glass-filter) saturate(1)' : 'blur(12px) saturate(1.8) brightness(1.16)',
      ...style,
    }

    return (
      <button
        ref={ref}
        className={`glass-button ${className}`}
        style={glassStyle}
        {...rest}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'scale(1.04)'
          e.currentTarget.style.boxShadow =
            'inset 0 1px 0 rgba(255, 255, 255, 0.28), 0 0 18px rgba(124, 124, 255, 0.35), 0 6px 20px rgba(0, 0, 0, 0.22)'
          rest.onMouseEnter?.(e)
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'scale(1)'
          e.currentTarget.style.boxShadow =
            'inset 0 1px 0 rgba(255, 255, 255, 0.18), 0 4px 14px rgba(0, 0, 0, 0.18)'
          rest.onMouseLeave?.(e)
        }}
        onMouseDown={(e) => {
          e.currentTarget.style.transform = 'scale(0.97)'
          rest.onMouseDown?.(e)
        }}
        onMouseUp={(e) => {
          e.currentTarget.style.transform = 'scale(1.04)'
          rest.onMouseUp?.(e)
        }}
      >
        {children}
      </button>
    )
  },
)
