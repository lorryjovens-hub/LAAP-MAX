import { useEffect, useState } from 'react'
import { Maximize2, Minimize2, Menu, Minus, Settings, X, Fullscreen, Minimize } from 'lucide-react'
import { GlassPanel } from '../glass/GlassPanel'

export interface TitleBarProps {
  /** 标题栏目标元素引用，供 LiquidGlass 观察尺寸 */
  targetRef?: React.RefObject<HTMLElement | null>
  /** 侧边栏是否已折叠 */
  sidebarCollapsed?: boolean
  /** 切换侧边栏回调 */
  onSidebarToggle?: () => void
  /** 打开设置面板回调 */
  onSettingsClick?: () => void
}

interface WindowState {
  isMaximized: boolean
  isFullScreen: boolean
  isMinimized: boolean
}

/**
 * 自定义标题栏。
 *
 * 左侧显示 LAAP logo 与应用标题，右侧提供最小化、最大化/还原、关闭按钮。
 * 标题栏整体支持拖拽移动窗口（app-drag），按钮区域排除拖拽（no-drag）。
 */
export function TitleBar({ targetRef, sidebarCollapsed, onSidebarToggle, onSettingsClick }: TitleBarProps) {
  const [state, setState] = useState<WindowState>({
    isMaximized: false,
    isFullScreen: false,
    isMinimized: false,
  })

  useEffect(() => {
    window.desktop?.getWindowState().then(setState)
    window.desktop?.onWindowState(setState)
  }, [])

  const handleMinimize = () => window.desktop?.minimize()
  const handleMaximize = () => window.desktop?.maximize()
  const handleFullscreen = () => window.desktop?.toggleFullscreen()
  const handleClose = () => window.desktop?.close()

  return (
    <GlassPanel
      ref={targetRef as React.RefObject<HTMLDivElement>}
      className="app-drag h-12 shrink-0 flex items-center justify-between px-4 rounded-t-laap-lg"
      radius="var(--laap-radius-lg) var(--laap-radius-lg) 0 0"
      intensity="md"
      liquidGlass
    >
      {/* 左侧：sidebar 切换 + logo + 标题 */}
      <div className="flex items-center gap-3">
        {onSidebarToggle && (
          <button
            type="button"
            onClick={onSidebarToggle}
            className="no-drag p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
            title={sidebarCollapsed ? '展开侧边栏' : '折叠侧边栏'}
          >
            <Menu className="w-4 h-4" />
          </button>
        )}
        <svg
          className="w-6 h-6"
          viewBox="0 0 256 256"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <linearGradient
              id="titlebar-logo-gradient"
              x1="32"
              y1="32"
              x2="224"
              y2="224"
              gradientUnits="userSpaceOnUse"
            >
              <stop offset="0%" stopColor="#7c7cff" />
              <stop offset="100%" stopColor="#00F5D4" />
            </linearGradient>
          </defs>
          <path
            d="M80 208 V96 C80 72 96 56 128 56 C160 56 176 72 176 96 V208"
            stroke="url(#titlebar-logo-gradient)"
            strokeWidth="22"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />
          <path
            d="M104 132 H152"
            stroke="url(#titlebar-logo-gradient)"
            strokeWidth="22"
            strokeLinecap="round"
          />
          <path
            d="M128 132 L128 208"
            stroke="url(#titlebar-logo-gradient)"
            strokeWidth="22"
            strokeLinecap="round"
          />
          <circle cx="128" cy="132" r="13" fill="#050608" />
        </svg>
        <span className="text-sm font-medium text-white/90 tracking-wide">
          LAAP Client
        </span>
      </div>

      {/* 右侧：设置 + 窗口控制按钮 */}
      <div className="no-drag flex items-center gap-1">
        {onSettingsClick && (
          <button
            onClick={onSettingsClick}
            className="p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
            title="设置"
            type="button"
          >
            <Settings className="w-4 h-4" />
          </button>
        )}
        <button
          onClick={handleMinimize}
          className="p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
          title="最小化"
          type="button"
        >
          <Minus className="w-4 h-4" />
        </button>
        <button
          onClick={handleMaximize}
          className="p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
          title={state.isMaximized ? '还原' : '最大化'}
          type="button"
        >
          {state.isMaximized ? (
            <Minimize2 className="w-4 h-4" />
          ) : (
            <Maximize2 className="w-4 h-4" />
          )}
        </button>
        <button
          onClick={handleFullscreen}
          className="p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
          title={state.isFullScreen ? '退出全屏' : '全屏'}
          type="button"
        >
          {state.isFullScreen ? (
            <Minimize className="w-4 h-4" />
          ) : (
            <Fullscreen className="w-4 h-4" />
          )}
        </button>
        <button
          onClick={handleClose}
          className="p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-red-500/80 transition-colors"
          title="关闭"
          type="button"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </GlassPanel>
  )
}
