/**
 * Overlay 渲染进程入口。
 *
 * 桌面悬浮通知窗口，显示简短 thought 或通知内容。
 * 接收主进程的 overlay:show 事件，3 秒后由主进程控制淡出。
 */

import { useEffect, useState } from 'react'
import { GlassPanel } from './components/glass/GlassPanel'

interface OverlayPayload {
  title: string
  content: string
}

function OverlayApp() {
  const [payload, setPayload] = useState<OverlayPayload | null>(null)

  useEffect(() => {
    const desktop = (window as unknown as { desktop?: {
      onOverlayShow: (callback: (p: OverlayPayload) => void) => void
    } }).desktop
    desktop?.onOverlayShow((p) => setPayload(p))
  }, [])

  if (!payload) return null

  return (
    <div className="w-screen h-screen flex items-start justify-end p-4 overflow-hidden bg-transparent">
      <GlassPanel
        className="w-[320px] p-4 border border-white/[0.12]"
        intensity="lg"
        radius="var(--laap-radius-md)"
      >
        <div className="flex items-center gap-2 mb-1">
          <span className="w-2 h-2 rounded-full bg-laap-accent" />
          <span className="text-xs font-medium text-white/80">{payload.title}</span>
        </div>
        <div className="text-sm text-white/70 leading-relaxed line-clamp-3">{payload.content}</div>
      </GlassPanel>
    </div>
  )
}

export default OverlayApp
