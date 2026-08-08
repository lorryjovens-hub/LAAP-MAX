/**
 * LeftSidebar：左侧可折叠边栏
 *
 * 展开宽度 340px，折叠后宽度 64px 并显示图标。
 * 内部垂直布局：顶部 VideoPlayer、下方 VitalSignsPanel。
 */

import { Film, Activity } from 'lucide-react'
import { GlassPanel } from '../glass/GlassPanel'
import { VideoPlayer } from '../media/VideoPlayer'
import { VitalSignsPanel } from '../panels/VitalSignsPanel'
import type { PSICycle, VitalSigns } from '../../laap/types'

export interface LeftSidebarProps {
  collapsed: boolean
  psiCycle: PSICycle
  vitalSigns: VitalSigns
  /** 自定义视频路径，留空使用默认视频 */
  videoSrc?: string
}

/**
 * 折叠态图标列表
 */
function CollapsedSidebar() {
  return (
    <div className="flex flex-col items-center gap-5 py-4">
      <div
        className="w-9 h-9 rounded-xl bg-white/[0.05] border border-white/[0.08] flex items-center justify-center"
        title="媒体播放器"
      >
        <Film className="w-4 h-4 text-white/60" />
      </div>
      <div
        className="w-9 h-9 rounded-xl bg-white/[0.05] border border-white/[0.08] flex items-center justify-center"
        title="生命体征"
      >
        <Activity className="w-4 h-4 text-laap-accent" />
      </div>
    </div>
  )
}

export function LeftSidebar({
  collapsed,
  psiCycle,
  vitalSigns,
  videoSrc,
}: LeftSidebarProps) {
  return (
    <div
      className={`shrink-0 h-full overflow-hidden transition-all duration-300 ease-out ${
        collapsed ? 'w-16' : 'w-[340px]'
      }`}
    >
      <GlassPanel
        className="h-full w-full"
        intensity="sm"
        radius="var(--laap-radius-md)"
        liquidGlass
      >
        {collapsed ? (
          <CollapsedSidebar />
        ) : (
          <div className="h-full flex flex-col gap-4 p-4 overflow-y-auto">
            <VideoPlayer src={videoSrc} />
            <VitalSignsPanel vitalSigns={vitalSigns} psiCycle={psiCycle} />
          </div>
        )}
      </GlassPanel>
    </div>
  )
}
