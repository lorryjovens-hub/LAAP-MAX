/**
 * SceneTerminal：terminal 类型 surface
 *
 * 展示一个可点击执行的命令卡片，点击后通过 laapStore 触发本地安全 shell。
 */

import { Play, Terminal } from 'lucide-react'
import { GlassPanel } from '../../glass/GlassPanel'
import { useLaapStore } from '../../../store/laapStore'
import type { SceneSurface } from '../../../laap/types'

export interface SceneTerminalProps {
  surface: SceneSurface
}

export function SceneTerminal({ surface }: SceneTerminalProps) {
  const runShellCommand = useLaapStore((state) => state.runShellCommand)

  const handleExecute = () => {
    const command = surface.command?.trim()
    if (!command) return
    const id = `${surface.id}-${Date.now().toString(36)}`
    runShellCommand(id, command, surface.cwd)
  }

  return (
    <GlassPanel className="p-3 flex flex-col gap-2" intensity="sm" radius="var(--laap-radius-md)">
      <div className="flex items-center gap-2">
        <Terminal className="w-4 h-4 text-amber-300/70" />
        <span className="text-[10px] uppercase tracking-wider text-white/40">Terminal</span>
      </div>
      <code className="text-xs font-mono text-white/80 truncate">{surface.command || '（无命令）'}</code>
      {surface.cwd && (
        <span className="text-[10px] text-white/40 truncate">cwd: {surface.cwd}</span>
      )}
      <button
        type="button"
        onClick={handleExecute}
        disabled={!surface.command?.trim()}
        className="mt-1 flex items-center justify-center gap-1.5 text-[11px] px-3 py-1.5 rounded-md bg-amber-500/15 text-amber-200 border border-amber-500/20 hover:bg-amber-500/25 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        <Play className="w-3 h-3" />
        执行
      </button>
    </GlassPanel>
  )
}
