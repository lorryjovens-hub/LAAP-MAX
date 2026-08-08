import { forwardRef } from 'react'
import { GlassPanel } from '../glass/GlassPanel'

export interface WindowFrameProps {
  children?: React.ReactNode
  titleBar?: React.ReactNode
  bottomBar?: React.ReactNode
  className?: string
}

/**
 * 无边框窗口外壳。
 *
 * 提供整体圆角、阴影与溢出隐藏，内部划分为顶部标题栏、中间内容区、
 * 底部可选控制栏。整个容器使用玻璃面板作为视觉基底。
 */
export const WindowFrame = forwardRef<HTMLDivElement, WindowFrameProps>(
  function WindowFrame({ children, titleBar, bottomBar, className = '' }, ref) {
    return (
      <GlassPanel
        ref={ref}
        className={`h-full w-full flex flex-col overflow-hidden rounded-laap-lg shadow-2xl ${className}`}
        radius="var(--laap-radius-lg)"
        intensity="sm"
      >
        {titleBar}

        <main className="flex-1 min-h-0 overflow-hidden relative">
          {children}
        </main>

        {bottomBar && (
          <footer className="relative shrink-0 flex items-center justify-between px-4 h-12 border-t border-white/[0.06]">
            <GlassPanel
              className="absolute inset-0 -z-10 h-full w-full rounded-none"
              intensity="sm"
              liquidGlass
            />
            {bottomBar}
          </footer>
        )}
      </GlassPanel>
    )
  },
)
