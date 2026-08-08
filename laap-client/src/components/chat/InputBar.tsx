/**
 * InputBar：聊天输入栏
 *
 * 多行文本输入（Enter 发送、Shift+Enter 换行）、发送/语音按钮、
 * 连接状态与 PSI 阶段显示，使用 GlassPanel 包装。
 */

import { useState, useRef, useEffect } from 'react'
import { Send, Mic, MicOff, Zap, Brain, Slash, Paperclip, ChevronDown } from 'lucide-react'
import { GlassPanel } from '../glass/GlassPanel'
import { GlassButton } from '../glass/GlassButton'
import { useSettingsStore } from '../../store/settingsStore'
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
  value, onChange, onSend, onVoiceToggle,
  connectionStatus, psiCycle,
  disabled = false, className = '', voiceActive = false,
}: InputBarProps) {
  const store = useSettingsStore()
  const currentModel = store.llm.model || 'deepseek-chat'
  const thinkingLevel = store.thinkingLevel
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [recording, setRecording] = useState(voiceActive)
  const [showSlashMenu, setShowSlashMenu] = useState(false)
  const [showModelMenu, setShowModelMenu] = useState(false)

  const MODELS = [
    { id: 'deepseek-chat', label: 'DeepSeek Chat' },
    { id: 'deepseek-v4-pro', label: 'DeepSeek Pro' },
    { id: 'gpt-4o', label: 'GPT-4o' },
    { id: 'claude-3-opus', label: 'Claude Opus' },
  ]

  const SLASH_COMMANDS = [
    { id: 'explain', label: '解释代码', icon: '?' },
    { id: 'refactor', label: '重构', icon: '#' },
    { id: 'test', label: '写测试', icon: 'T' },
    { id: 'doc', label: '写文档', icon: 'D' },
    { id: 'review', label: '审查代码', icon: 'R' },
  ]

  const THINKING_LEVELS = [
    { level: 0, label: '快速', icon: '⚡' },
    { level: 1, label: '平衡', icon: '🧠' },
    { level: 2, label: '深度', icon: '🔍' },
  ]

  // 检测斜杠命令
  useEffect(() => {
    if (value.startsWith('/')) {
      setShowSlashMenu(true)
    } else {
      setShowSlashMenu(false)
    }
  }, [value])

  useEffect(() => { setRecording(voiceActive) }, [voiceActive])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); handleSend()
    }
  }

  const handleSend = () => {
    if (!value.trim() || disabled) return
    onSend()
    textareaRef.current?.focus()
  }

  const toggleVoice = () => { const next = !recording; setRecording(next); onVoiceToggle?.(next) }

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
      {/* 工具栏：模型选择 + 思考级别 + 斜杠命令 + 附件 */}
      <div className="flex items-center gap-1.5 flex-wrap">
        {/* 模型选择 */}
        <div className="relative">
          <button onClick={() => setShowModelMenu(!showModelMenu)}
            className="flex items-center gap-1 px-2 py-1 rounded-md bg-white/[0.05] hover:bg-white/[0.08] text-[10px] text-white/60 border border-white/[0.06] transition-colors">
            <Brain className="w-3 h-3" />
            {currentModel.split('-').slice(0,2).join(' ')}
            <ChevronDown className="w-2.5 h-2.5" />
          </button>
          {showModelMenu && (
            <div className="absolute bottom-full left-0 mb-1 w-36 bg-[#1a1a2e] border border-white/[0.1] rounded-lg shadow-xl py-1 z-50">
              {MODELS.map((m) => (
                <button key={m.id} onClick={() => { store.setLLM({ model: m.id }); setShowModelMenu(false) }}
                  className={`w-full text-left px-3 py-1.5 text-[11px] transition-colors ${m.id === currentModel ? 'text-laap-accent bg-white/[0.06]' : 'text-white/70 hover:bg-white/[0.04]'}`}>
                  {m.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 思考级别 */}
        <div className="flex items-center gap-0.5 bg-white/[0.04] rounded-md p-0.5 border border-white/[0.06]">
          {THINKING_LEVELS.map((t) => (
            <button key={t.level} onClick={() => store.setThinkingLevel(t.level)}
              className={`px-2 py-1 rounded text-[10px] transition-colors ${t.level === thinkingLevel ? 'bg-white/[0.1] text-white' : 'text-white/50 hover:text-white/70'}`}>
              {t.label}
            </button>
          ))}
        </div>

        {/* 斜杠命令 */}
        <button onClick={() => setShowSlashMenu(!showSlashMenu)}
          className="flex items-center gap-1 px-2 py-1 rounded-md bg-white/[0.05] hover:bg-white/[0.08] text-[10px] text-white/60 border border-white/[0.06] transition-colors">
          <Slash className="w-3 h-3" />
          命令
        </button>

        {/* 附件 */}
        <button
          className="flex items-center gap-1 px-2 py-1 rounded-md bg-white/[0.05] hover:bg-white/[0.08] text-[10px] text-white/60 border border-white/[0.06] transition-colors">
          <Paperclip className="w-3 h-3" />
          附件
        </button>

        <div className="flex-1" />

        {/* 引擎模式指示 */}
        <span className="text-[9px] text-white/30 px-1">
          <Zap className="w-2.5 h-2.5 inline mr-0.5" />
          {connectionStatus === 'open' ? '在线' : '离线'}
        </span>
      </div>

      {/* 斜杠命令弹出菜单 */}
      {showSlashMenu && (
        <div className="bg-[#1a1a2e] border border-white/[0.1] rounded-lg shadow-xl py-1 max-h-40 overflow-y-auto">
          {SLASH_COMMANDS.map((cmd) => (
            <button key={cmd.id} onClick={() => { onChange(`/${cmd.id} `); setShowSlashMenu(false); textareaRef.current?.focus() }}
              className="w-full text-left flex items-center gap-2 px-3 py-1.5 text-[11px] text-white/70 hover:bg-white/[0.04] transition-colors">
              <span className="w-4 h-4 rounded bg-white/[0.06] flex items-center justify-center text-[9px] font-mono">{cmd.icon}</span>
              {cmd.label}
            </button>
          ))}
        </div>
      )}

      {/* 输入区 */}
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入消息，/ 命令，@ 提及..."
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
