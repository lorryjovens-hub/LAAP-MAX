/**
 * ThoughtStream：思考流可折叠面板
 *
 * 展示 reasoning_content、confidence、metacognitive alerts，
 * 每个 thought 项显示时间戳与类型标签。
 */

import { useState } from 'react'
import { ChevronDown, ChevronUp, BrainCircuit, AlertTriangle } from 'lucide-react'
import { GlassPanel } from '../glass/GlassPanel'
import type { Thought } from '../../laap/types'

export interface ThoughtStreamProps {
  thoughts: Thought[]
  className?: string
}

const TYPE_LABELS: Record<Thought['type'], string> = {
  reasoning: '推理',
  reflection: '反思',
  bias: '偏差检测',
}

const TYPE_STYLES: Record<Thought['type'], string> = {
  reasoning: 'bg-laap-accent/15 text-laap-accent-light border-laap-accent/20',
  reflection: 'bg-laap-secondary/15 text-laap-secondary border-laap-secondary/20',
  bias: 'bg-orange-500/15 text-orange-300 border-orange-500/20',
}

function formatTime(timestamp: number): string {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export function ThoughtStream({ thoughts, className = '' }: ThoughtStreamProps) {
  const [expanded, setExpanded] = useState(true)

  return (
    <GlassPanel
      className={`flex flex-col overflow-hidden ${className}`}
      intensity="sm"
      radius="var(--laap-radius-md)"
    >
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 border-b border-white/[0.08] hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-center gap-2">
          <BrainCircuit className="w-4 h-4 text-laap-accent-light" />
          <span className="text-sm font-medium text-white/90">思考流</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-white/[0.08] text-white/50">
            {thoughts.length}
          </span>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-white/50" />
        ) : (
          <ChevronDown className="w-4 h-4 text-white/50" />
        )}
      </button>

      {expanded && (
        <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-2">
          {thoughts.length === 0 && (
            <div className="h-24 flex flex-col items-center justify-center text-white/30 text-xs gap-2">
              <BrainCircuit className="w-6 h-6 opacity-50" />
              <p>暂无思考记录</p>
            </div>
          )}
          {thoughts.map((thought) => (
            <div
              key={thought.id}
              className="rounded-xl bg-white/[0.03] border border-white/[0.06] p-3"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full border ${TYPE_STYLES[thought.type]}`}
                >
                  {TYPE_LABELS[thought.type]}
                </span>
                <span className="text-[10px] font-mono text-white/40">
                  {formatTime(thought.timestamp)}
                </span>
              </div>
              <p className="text-xs text-white/80 leading-relaxed">{thought.content}</p>
              {typeof thought.confidence === 'number' && (
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-[10px] text-white/40">置信度</span>
                  <div className="flex-1 h-1.5 rounded-full bg-white/[0.08] overflow-hidden">
                    <div
                      className="h-full rounded-full bg-laap-accent transition-all duration-500"
                      style={{ width: `${Math.round(thought.confidence * 100)}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-mono text-white/60">
                    {Math.round(thought.confidence * 100)}%
                  </span>
                </div>
              )}
              {thought.alert && (
                <div className="mt-2 flex items-start gap-1.5 text-[10px] text-orange-300/90 bg-orange-500/10 rounded-lg px-2 py-1.5">
                  <AlertTriangle className="w-3 h-3 shrink-0 mt-0.5" />
                  <span>{thought.alert}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </GlassPanel>
  )
}
