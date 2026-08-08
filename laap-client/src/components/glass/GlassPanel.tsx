import { forwardRef, useEffect, useId, useRef, useState } from 'react'
import { LiquidGlass, supportsLaapLiquidGlass } from './LiquidGlass'

export interface GlassPanelProps {
  children?: React.ReactNode
  className?: string
  radius?: number | string
  intensity?: 'xs' | 'sm' | 'md' | 'lg'
  /**
   * 是否启用液态玻璃 SVG 滤镜（依赖 LiquidGlass 组件）。
   * 不支持时自动回退到 backdrop-filter。
   */
  liquidGlass?: boolean
  /**
   * 是否启用动态水波纹效果。
   * 默认 true；设为 false 时保持静态液态玻璃。
   */
  animated?: boolean
  style?: React.CSSProperties
}

const intensityMap = {
  xs: 'blur(var(--laap-glass-blur, 6px)) saturate(var(--laap-glass-saturate, 1.4)) brightness(var(--laap-glass-brightness, 1.08))',
  sm: 'blur(var(--laap-glass-blur, 10px)) saturate(var(--laap-glass-saturate, 1.6)) brightness(var(--laap-glass-brightness, 1.12))',
  md: 'blur(var(--laap-glass-blur, 12px)) saturate(var(--laap-glass-saturate, 1.8)) brightness(var(--laap-glass-brightness, 1.16))',
  lg: 'blur(var(--laap-glass-blur, 18px)) saturate(var(--laap-glass-saturate, 2)) brightness(var(--laap-glass-brightness, 1.2))',
}

/**
 * 玻璃面板容器。
 *
 * 基础样式提供半透明黑底 + 背景模糊 + 内发光与外阴影。
 * 当 liquidGlass=true 且浏览器支持时，内部会渲染 LiquidGlass 并应用其滤镜
 * 以获得边缘扭曲色差效果；否则使用 backdrop-filter 回退。
 */
export const GlassPanel = forwardRef<HTMLDivElement, GlassPanelProps>(
  function GlassPanel(
    { children, className = '', radius, intensity = 'md', liquidGlass = false, animated = true, style },
    ref,
  ) {
    const [svgOk, setSvgOk] = useState(false)
    const reactId = useId().replace(/:/g, '-')
    const filterId = `laap-glass-panel-${reactId}`
    const innerRef = useRef<HTMLDivElement | null>(null)

    const setRef = (el: HTMLDivElement | null) => {
      innerRef.current = el
      if (typeof ref === 'function') {
        ref(el)
      } else if (ref) {
        ;(ref as React.MutableRefObject<HTMLDivElement | null>).current = el
      }
    }

    useEffect(() => {
      if (liquidGlass) {
        setSvgOk(supportsLaapLiquidGlass())
      }
    }, [liquidGlass])

    const borderRadius = radius !== undefined ? (typeof radius === 'number' ? `${radius}px` : radius) : 'var(--laap-radius-md)'
    const backdrop = intensityMap[intensity]

    const glassStyle: React.CSSProperties = {
      background: 'rgba(0, 0, 0, 0.10)',
      borderRadius,
      boxShadow:
        'inset 0 0 2px 1px rgba(255, 255, 255, 0.35), inset 0 0 10px 4px rgba(255, 255, 255, 0.15), 0 4px 16px rgba(17, 17, 26, 0.05), 0 8px 24px rgba(17, 17, 26, 0.05), 0 16px 56px rgba(17, 17, 26, 0.05)',
      backdropFilter: liquidGlass && svgOk ? `url(#${filterId}) saturate(1)` : backdrop,
      WebkitBackdropFilter:
        liquidGlass && svgOk ? `url(#${filterId}) saturate(1)` : backdrop,
      ...style,
    }

    return (
      <>
        {liquidGlass && svgOk && (
          <LiquidGlass targetRef={innerRef} filterId={filterId} animated={animated} />
        )}
        <div
          ref={setRef}
          className={`laap-glass-panel ${liquidGlass ? 'laap-glass-panel--liquid' : ''} ${className}`.trim()}
          style={glassStyle}
        >
          {children}
        </div>
      </>
    )
  },
)
