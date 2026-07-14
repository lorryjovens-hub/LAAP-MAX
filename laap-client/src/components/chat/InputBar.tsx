/**
 * InputBar：聊天输入栏
 *
 * 多行文本输入（Enter 发送、Shift+Enter 换行）、发送/语音按钮、
 * 连接状态与 PSI 阶段显示，使用 GlassPanel 包装。
 */

import { useState, useRef, useEffect } from 'react'
import { Send, Mic, MicOff } from 'lucide-react'
import { GlassPanel } from '../glass/GlassPanel'
import { GlassButton } from '../glass/GlassButton'
import type { ConnectionStatus, PSICycle } from '../../laap/types'

export interface InputBarProps {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  onVoiceToggle?: (active: boolean) => void
  connectionStatus: ConnectionStatus
  psiCycle: PSICycle
  disabled?: boolean
  className?: string
  voiceActive?: boolean
}

function getConnectionDot(status: ConnectionStatus): string {
  switch (status) {
    case 'open':
      return 'bg-laap-secondary shadow-[0_0_6px_#00f5d4]'
    case 'connecting':
      return 'bg-laap-status-info animate-pulse'
    case 'error':
      return 'bg-laap-status-error'
    default:
      return 'bg-white/30'
  }
}

function getConnectionLabel(status: ConnectionStatus): string {
  switch (status) {
    case 'open':
      return '已连接'
    case 'connecting':
      return '连接中'
    case 'error':
      return '连接异常'
    case 'closed':
      return '已关闭'
    default:
      return '未知'
  }
}

export function InputBar({
  value,
  onChange,
  onSend,
  onVoiceToggle,
  connectionStatus,
  psiCycle,
  disabled = false,
  className = '',
  voiceActive = false,
}: InputBarProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [recording, setRecording] = useState(voiceActive)

  // 当外部 voice 状态变化时同步内部按钮状态
  useEffect(() => {
    setRecording(voiceActive)
  }, [voiceActive])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSend = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend()
    textareaRef.current?.focus()
  }

  const toggleVoice = () => {
    const next = !recording
    setRecording(next)
    onVoiceToggle?.(next)
  }

  // 根据内容自动调整高度
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 140)}px`
  }, [value])

  return (
    <GlassPanel
      className={`flex flex-col gap-2 px-4 py-3 ${className}`}
      intensity="md"
      radius="var(--laap-radius-md)"
      liquidGlass
    >
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入消息，按 Enter 发送，Shift+Enter 换行..."
          disabled={disabled}
          rows={1}
          className="flex-1 min-h-[44px] max-h-[140px] bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-white/90 placeholder:text-white/30 focus:outline-none focus:border-laap-accent/50 disabled:opacity-40 resize-none"
        />
        <GlassButton
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          className="px-4 py-2.5 shrink-0"
        >
          <Send className="w-4 h-4" />
        </GlassButton>
        <button
          type="button"
          onClick={toggleVoice}
          className={`shrink-0 w-10 h-10 rounded-xl flex items-center justify-center border transition-colors ${
            recording
              ? 'bg-laap-status-error/20 border-laap-status-error/40 text-laap-status-error'
              : 'bg-white/[0.05] border-white/[0.08] text-white/70 hover:bg-white/[0.08]'
          }`}
          title={recording ? '停止连续监听' : '开始连续监听'}
        >
          {recording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
        </button>
      </div>

      <div className="flex items-center justify-between text-[10px] text-white/40">
        <div className="flex items-center gap-2">
          <span className={`w-1.5 h-1.5 rounded-full ${getConnectionDot(connectionStatus)}`} />
          <span>{getConnectionLabel(connectionStatus)}</span>
        </div>
        <div className="font-mono">
          PSI {psiCycle.phase} {Math.round(psiCycle.progress * 100)}%
        </div>
      </div>
    </GlassPanel>
  )
}
