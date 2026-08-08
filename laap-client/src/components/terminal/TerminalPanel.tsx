import { useEffect, useRef, useState } from 'react'
import { Copy, RotateCcw, Square, Terminal, Trash2 } from 'lucide-react'
import { GlassPanel } from '../glass/GlassPanel'
import { useLaapStore } from '../../store/laapStore'
import type { TerminalSession } from '../../laap/types'

function generateId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
}

function statusBadge(status: TerminalSession['status']) {
  switch (status) {
    case 'running':
      return (
        <span className="flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
          running
        </span>
      )
    case 'success':
      return (
        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/20">
          success
        </span>
      )
    case 'error':
      return (
        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-rose-500/15 text-rose-300 border border-rose-500/20">
          error
        </span>
      )
  }
}

function copyText(text: string): void {
  if (navigator.clipboard?.writeText) {
    void navigator.clipboard.writeText(text)
  }
}

interface SessionItemProps {
  session: TerminalSession
  onRetry: (session: TerminalSession) => void
  onAbort: (id: string) => void
}

function SessionItem({ session, onRetry, onAbort }: SessionItemProps) {
  const output = [session.stdout, session.stderr].filter(Boolean).join('\n')
  return (
    <div className="rounded-md bg-black/20 border border-white/[0.06] overflow-hidden">
      <div className="px-3 py-2 flex items-center justify-between gap-2 border-b border-white/[0.06]">
        <div className="min-w-0 flex items-center gap-2">
          <Terminal className="w-3.5 h-3.5 text-white/40 shrink-0" />
          <code className="text-xs text-white/80 truncate font-mono">{session.command}</code>
          {session.cwd && (
            <span className="text-[10px] text-white/40 truncate max-w-[120px]">{session.cwd}</span>
          )}
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {statusBadge(session.status)}
          {session.status === 'running' ? (
            <button
              type="button"
              onClick={() => onAbort(session.id)}
              title="中止"
              className="p-1 rounded hover:bg-white/10 text-rose-300 transition-colors"
            >
              <Square className="w-3 h-3" />
            </button>
          ) : (
            <button
              type="button"
              onClick={() => onRetry(session)}
              title="重试"
              className="p-1 rounded hover:bg-white/10 text-white/60 hover:text-white/90 transition-colors"
            >
              <RotateCcw className="w-3 h-3" />
            </button>
          )}
          <button
            type="button"
            onClick={() => copyText(session.command)}
            title="复制命令"
            className="p-1 rounded hover:bg-white/10 text-white/60 hover:text-white/90 transition-colors"
          >
            <Copy className="w-3 h-3" />
          </button>
          <button
            type="button"
            onClick={() => copyText(output)}
            title="复制输出"
            className="p-1 rounded hover:bg-white/10 text-white/60 hover:text-white/90 transition-colors"
          >
            <Copy className="w-3 h-3" />
          </button>
        </div>
      </div>

      {session.exitCode !== null && session.exitCode !== undefined && (
        <div className="px-3 py-1 text-[10px] font-mono text-white/40 border-b border-white/[0.06]">
          exit code: {session.exitCode}
        </div>
      )}

      {(session.stdout || session.stderr) && (
        <div className="px-3 py-2 max-h-32 overflow-y-auto text-[11px] font-mono whitespace-pre-wrap break-all">
          {session.stdout && <div className="text-white/70">{session.stdout}</div>}
          {session.stderr && <div className="text-rose-300/80 mt-1">{session.stderr}</div>}
        </div>
      )}
    </div>
  )
}

export function TerminalPanel() {
  const { terminalSessions, runShellCommand, abortShellCommand, clearTerminal } = useLaapStore()
  const [expanded, setExpanded] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const prevLengthRef = useRef(terminalSessions.length)

  useEffect(() => {
    if (terminalSessions.length > prevLengthRef.current) {
      setExpanded(true)
    }
    prevLengthRef.current = terminalSessions.length
  }, [terminalSessions.length])

  useEffect(() => {
    if (expanded && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [terminalSessions, expanded])

  const handleRetry = (session: TerminalSession) => {
    runShellCommand(generateId(), session.command, session.cwd)
  }

  return (
    <GlassPanel className="flex flex-col shrink-0" intensity="sm" radius="var(--laap-radius-md)">
      <div className="px-3 py-2 flex items-center justify-between border-b border-white/[0.08]">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-white/60" />
          <span className="text-xs font-medium text-white/80">终端</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-white/[0.08] text-white/50 font-mono">
            {terminalSessions.length}
          </span>
        </div>
        <div className="flex items-center gap-1">
          {terminalSessions.length > 0 && (
            <button
              type="button"
              onClick={clearTerminal}
              title="清空历史"
              className="p-1 rounded hover:bg-white/10 text-white/50 hover:text-rose-300 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="text-[10px] px-2 py-1 rounded hover:bg-white/10 text-white/50 hover:text-white/80 transition-colors"
          >
            {expanded ? '收起' : '展开'}
          </button>
        </div>
      </div>

      {expanded && (
        <div
          ref={scrollRef}
          className="flex-1 min-h-0 h-48 overflow-y-auto p-3 space-y-2"
        >
          {terminalSessions.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-white/30 text-xs">
              <p>暂无命令记录</p>
              <p className="text-[10px] mt-1">从场景面片或代码中触发 shell 执行</p>
            </div>
          ) : (
            terminalSessions.map((session) => (
              <SessionItem
                key={session.id}
                session={session}
                onRetry={handleRetry}
                onAbort={abortShellCommand}
              />
            ))
          )}
        </div>
      )}
    </GlassPanel>
  )
}
