/**
 * InputToolbar — 输入区工具栏（Hanako 完整风格）
 * 集成模型选择、思考级别、计划模式、@提及、文件引用、附件、上下文环
 */

import { useState } from 'react'
import { Brain, Slash, AtSign, Paperclip, FileText, Target, ChevronDown } from 'lucide-react'
import { useSettingsStore } from '../../store/settingsStore'

const MODELS = [
  { id: 'deepseek-chat', label: 'DeepSeek Chat' },
  { id: 'deepseek-v4-pro', label: 'DeepSeek Pro' },
  { id: 'gpt-4o', label: 'GPT-4o' },
  { id: 'claude-3-opus', label: 'Claude Opus' },
]

const THINKING_LEVELS = [
  { level: 0, label: '快速', desc: '低延迟' },
  { level: 1, label: '平衡', desc: '默认' },
  { level: 2, label: '深度', desc: '高质量' },
]

export function InputToolbar({ onSlashCommand }: { onSlashCommand?: (cmd: string) => void }) {
  const store = useSettingsStore()
  const [showModelMenu, setShowModelMenu] = useState(false)
  const [showMention, setShowMention] = useState(false)

  const currentModel = store.llm.model || 'deepseek-chat'
  const thinkingLevel = store.thinkingLevel

  return (
    <div className="flex items-center gap-1 flex-wrap">
      {/* 模型选择 */}
      <div className="relative">
        <button onClick={() => setShowModelMenu(!showModelMenu)}
          className="flex items-center gap-1 px-2 py-1 rounded-md bg-white/[0.05] hover:bg-white/[0.08] text-[10px] text-white/60 border border-white/[0.06] transition-colors">
          <Brain className="w-3 h-3" />
          <span className="max-w-16 truncate">{currentModel.includes('deepseek') ? 'DeepSeek' : currentModel}</span>
          <ChevronDown className="w-2.5 h-2.5" />
        </button>
        {showModelMenu && (
          <div className="absolute bottom-full left-0 mb-1 w-40 bg-[#1a1a2e] border border-white/[0.1] rounded-lg shadow-xl py-1 z-50 max-h-48 overflow-y-auto">
            {MODELS.map(m => (
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
        {THINKING_LEVELS.map(t => (
          <button key={t.level} onClick={() => store.setThinkingLevel(t.level)}
            className={`px-2 py-1 rounded text-[10px] transition-colors ${t.level === thinkingLevel ? 'bg-white/[0.1] text-white' : 'text-white/50 hover:text-white/70'}`}
            title={t.desc}>
            {t.label}
          </button>
        ))}
      </div>

      {/* 计划模式 */}
      <button className="flex items-center gap-1 px-2 py-1 rounded-md bg-white/[0.05] hover:bg-white/[0.08] text-[10px] text-white/60 border border-white/[0.06] transition-colors">
        <Target className="w-3 h-3" />
        计划
      </button>

      {/* 斜杠命令 */}
      <button onClick={() => onSlashCommand?.('/')} title="命令"
        className="flex items-center gap-1 px-2 py-1 rounded-md bg-white/[0.05] hover:bg-white/[0.08] text-[10px] text-white/60 border border-white/[0.06] transition-colors">
        <Slash className="w-3 h-3" />
        命令
      </button>

      {/* @提及 */}
      <div className="relative">
        <button onClick={() => setShowMention(!showMention)}
          className="flex items-center gap-1 px-2 py-1 rounded-md bg-white/[0.05] hover:bg-white/[0.08] text-[10px] text-white/60 border border-white/[0.06] transition-colors">
          <AtSign className="w-3 h-3" />
          提及
        </button>
        {showMention && (
          <div className="absolute bottom-full left-0 mb-1 w-32 bg-[#1a1a2e] border border-white/[0.1] rounded-lg shadow-xl py-1 z-50">
            {['文件', '技能', 'Agent'].map(item => (
              <button key={item} onClick={() => { setShowMention(false); onSlashCommand?.(`@${item} `) }}
                className="w-full text-left px-3 py-1.5 text-[11px] text-white/70 hover:bg-white/[0.04] transition-colors">
                @{item}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 文件引用 */}
      <button className="flex items-center gap-1 px-2 py-1 rounded-md bg-white/[0.05] hover:bg-white/[0.08] text-[10px] text-white/60 border border-white/[0.06] transition-colors">
        <FileText className="w-3 h-3" />
        引用
      </button>

      {/* 附件 */}
      <button className="flex items-center gap-1 px-2 py-1 rounded-md bg-white/[0.05] hover:bg-white/[0.08] text-[10px] text-white/60 border border-white/[0.06] transition-colors">
        <Paperclip className="w-3 h-3" />
        附件
      </button>

      <div className="flex-1" />

      {/* 上下文环 */}
      <div className="flex items-center gap-1 text-[9px] text-white/30" title="上下文使用率">
        <Target className="w-2.5 h-2.5" />
        <span>72%</span>
      </div>
    </div>
  )
}