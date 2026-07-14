import { useEffect, useRef } from 'react'

export interface LiquidGlassProps {
  /**
   * 要观察尺寸变化的目标元素。
   * LiquidGlass 会根据目标宽高生成对应 displacement map 并写入 feImage。
   */
  targetRef?: React.RefObject<HTMLElement | null>
  /**
   * SVG 滤镜 ID，默认 laap-liquid-glass-filter。
   */
  filterId?: string
}

/**
 * 生成液态玻璃 displacement map 的 data URI SVG。
 *
 * 原理：
 * - 黑色底保证无位移区域。
 * - 水平红色渐变提供 R 通道位移。
 * - 垂直蓝色渐变（mix-blend-mode:difference）提供 B 通道位移。
 * - 内部灰色模糊矩形在边缘形成柔和的过渡。
 */
export function generateLaapGlassDisplacementMap(
  width: number,
  height: number,
  radius: number,
): string {
  const w = Math.max(240, Math.round(width || 400))
  const h = Math.max(48, Math.round(height || 92))
  const r = Math.max(12, Math.round(radius || 50))
  const borderWidth = 0.07
  const edge = Math.min(w, h) * (borderWidth * 0.5)
  const innerW = Math.max(1, w - edge * 2)
  const innerH = Math.max(1, h - edge * 2)

  const svg =
    `<svg viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg">` +
    '<defs>' +
    '<linearGradient id="glass-red" x1="100%" y1="0%" x2="0%" y2="0%"><stop offset="0%" stop-color="#0000"/><stop offset="100%" stop-color="red"/></linearGradient>' +
    '<linearGradient id="glass-blue" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#0000"/><stop offset="100%" stop-color="blue"/></linearGradient>' +
    '</defs>' +
    `<rect x="0" y="0" width="${w}" height="${h}" fill="black"/>` +
    `<rect x="0" y="0" width="${w}" height="${h}" rx="${r}" fill="url(#glass-red)"/>` +
    `<rect x="0" y="0" width="${w}" height="${h}" rx="${r}" fill="url(#glass-blue)" style="mix-blend-mode:difference"/>` +
    `<rect x="${edge.toFixed(2)}" y="${edge.toFixed(2)}" width="${innerW.toFixed(2)}" height="${innerH.toFixed(2)}" rx="${r}" fill="hsl(0 0% 50% / 1)" style="filter:blur(11px)"/>` +
    '</svg>'

  return `data:image/svg+xml,${encodeURIComponent(svg)}`
}

/**
 * 检测当前浏览器是否支持使用 SVG filter 作为 backdrop-filter。
 * Safari 与 Firefox 对此支持不佳，回退到普通 backdrop-filter。
 */
export function supportsLaapLiquidGlass(): boolean {
  try {
    const ua = navigator.userAgent || ''
    if ((/Safari/.test(ua) && !/Chrome/.test(ua)) || /Firefox/.test(ua)) {
      return false
    }
    const div = document.createElement('div')
    div.style.backdropFilter = 'url(#laap-liquid-glass-filter)'
    return div.style.backdropFilter !== ''
  } catch {
    return false
  }
}

/**
 * 液态玻璃 SVG 滤镜组件。
 *
 * 通过 feImage + 三个 feDisplacementMap（R/G/B 通道不同 scale）+ feOffset
 * 制造横向色差，再用 feBlend mode="screen" 合并，最后轻微高斯模糊。
 */
export function LiquidGlass({ targetRef, filterId = 'laap-liquid-glass-filter' }: LiquidGlassProps) {
  const feImageRef = useRef<SVGFEImageElement>(null)
  const lastKeyRef = useRef<string>('')

  useEffect(() => {
    const target = targetRef?.current
    const img = feImageRef.current
    if (!target || !img) return

    const update = () => {
      const rect = target.getBoundingClientRect()
      if (rect.width < 2 || rect.height < 2) return

      const computed = window.getComputedStyle(target)
      const radius = parseFloat(computed.borderRadius) || 24
      const key = `${Math.round(rect.width)}x${Math.round(rect.height)}:${Math.round(radius)}`
      if (key === lastKeyRef.current) return

      lastKeyRef.current = key
      const href = generateLaapGlassDisplacementMap(rect.width, rect.height, radius)
      img.setAttribute('href', href)
      try {
        img.setAttributeNS('http://www.w3.org/1999/xlink', 'href', href)
      } catch {
        // 部分浏览器不支持 xlink 命名空间，忽略即可
      }
    }

    // 初始化一次
    update()

    const observer = new ResizeObserver(update)
    observer.observe(target)

    return () => observer.disconnect()
  }, [targetRef])

  return (
    <svg
      className="fixed w-0 h-0 overflow-hidden pointer-events-none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      focusable="false"
    >
      <defs>
        <filter
          id={filterId}
          colorInterpolationFilters="sRGB"
          x="-12%"
          y="-28%"
          width="124%"
          height="156%"
        >
          <feImage
            ref={feImageRef}
            x="0"
            y="0"
            width="100%"
            height="100%"
            preserveAspectRatio="none"
            result="map"
          />
          <feDisplacementMap
            in="SourceGraphic"
            in2="map"
            scale="180"
            xChannelSelector="R"
            yChannelSelector="B"
            result="dispRed"
          />
          <feOffset in="dispRed" dx="-90" dy="0" result="dispRedShifted" />
          <feMerge result="dispRedAligned">
            <feMergeNode in="SourceGraphic" />
            <feMergeNode in="dispRedShifted" />
          </feMerge>
          <feColorMatrix
            in="dispRedAligned"
            type="matrix"
            values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0"
            result="red"
          />
          <feDisplacementMap
            in="SourceGraphic"
            in2="map"
            scale="170"
            xChannelSelector="R"
            yChannelSelector="B"
            result="dispGreen"
          />
          <feOffset in="dispGreen" dx="-90" dy="0" result="dispGreenShifted" />
          <feMerge result="dispGreenAligned">
            <feMergeNode in="SourceGraphic" />
            <feMergeNode in="dispGreenShifted" />
          </feMerge>
          <feColorMatrix
            in="dispGreenAligned"
            type="matrix"
            values="0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0"
            result="green"
          />
          <feDisplacementMap
            in="SourceGraphic"
            in2="map"
            scale="160"
            xChannelSelector="R"
            yChannelSelector="B"
            result="dispBlue"
          />
          <feOffset in="dispBlue" dx="-90" dy="0" result="dispBlueShifted" />
          <feMerge result="dispBlueAligned">
            <feMergeNode in="SourceGraphic" />
            <feMergeNode in="dispBlueShifted" />
          </feMerge>
          <feColorMatrix
            in="dispBlueAligned"
            type="matrix"
            values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0"
            result="blue"
          />
          <feBlend in="red" in2="green" mode="screen" result="rg" />
          <feBlend in="rg" in2="blue" mode="screen" result="output" />
          <feGaussianBlur in="output" stdDeviation="0.5" />
        </filter>
      </defs>
    </svg>
  )
}
