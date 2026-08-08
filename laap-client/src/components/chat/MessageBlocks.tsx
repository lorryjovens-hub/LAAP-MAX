/**
 * ThinkingBlock — 可折叠的推理过程展示（Hanako 风格）
 */

import { useState } from 'react'
import { ChevronDown, ChevronRight, Sparkles } from 'lucide-react'

export function ThinkingBlock({ content, thinking }: { content?: string; thinking?: string }) {
  const [open, setOpen] = useState(false)
  const text = thinking || (content || '').slice(0, 120)
  if (!text) return null

  return (
    <div className="w-full mb-1.5">
      <button onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-[10px] text-laap-accent/60 hover:text-laap-accent transition-colors">
        {open ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        <Sparkles className="w-2.5 h-2.5" />
        思考过程
      </button>
      {open && (
        <div className="mt-1 px-3 py-2 rounded-lg bg-white/[0.03] border border-white/[0.06] text-[11px] text-white/40 italic leading-relaxed">
          {text}
        </div>
      )}
    </div>
  )
}

export function MessageActions({ content }: { content: string }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = async () => {
    try { await navigator.clipboard.writeText(content); setCopied(true); setTimeout(() => setCopied(false), 1500) } catch { /* */ }
  }
  return (
    <div className="flex items-center gap-0.5 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
      <button onClick={handleCopy} title="复制"
        className="w-6 h-6 rounded flex items-center justify-center hover:bg-white/[0.08] transition-colors">
        <span className="text-[9px] text-white/40">{copied ? '✓' : '复制'}</span>
      </button>
      <button title="编辑"
        className="w-6 h-6 rounded flex items-center justify-center hover:bg-white/[0.08] transition-colors">
        <span className="text-[9px] text-white/40">编辑</span>
      </button>
      <button title="重试"
        className="w-6 h-6 rounded flex items-center justify-center hover:bg-white/[0.08] transition-colors">
        <span className="text-[9px] text-white/40">重试</span>
      </button>
    </div>
  )
}