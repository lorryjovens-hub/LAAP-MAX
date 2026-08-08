/**
 * ThoughtFloat — 思维浮泡
 *
 * 当 Aris 产生自发思维时，从屏幕右下角浮入一个玻璃气泡。
 * 取代传统的桌面通知，更沉浸、更有「意识感」。
 *
 * 用法:
 *   <ThoughtFloat
 *     thoughts={thoughts}
 *     onDismiss={(id) => setThoughts((p) => p.filter((t) => t.id !== id))}
 *   />
 */

import { useEffect, useState } from 'react'
import { GlassPanel } from '../glass/GlassPanel'
import { Sparkles, Lightbulb, AlertTriangle } from 'lucide-react'

export interface Thought {
  id: string
  content: string
  type?: 'reasoning' | 'reflection' | 'bias' | 'insight'
  confidence?: number
  timestamp?: number
}

export interface ThoughtFloatProps {
  thoughts: Thought[]
  maxVisible?: number
  dismissAfterMs?: number
  onDismiss?: (id: string) => void
}

const TYPE_CONFIG: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  reasoning: { icon: Lightbulb, color: '#60a5fa', label: '推理' },
  reflection: { icon: Sparkles, color: '#a78bfa', label: '反思' },
  bias:       { icon: AlertTriangle, color: '#fbbf24', label: '偏差' },
  insight:    { icon: Sparkles, color: '#34d399', label: '洞察' },
}

function ThoughtBubble({
  thought,
  onDismiss,
  dismissAfter,
}: {
  thought: Thought
  onDismiss?: () => void
  dismissAfter?: number
}) {
  const [exiting, setExiting] = useState(false)
  const config = TYPE_CONFIG[thought.type ?? 'reasoning'] ?? TYPE_CONFIG.reasoning
  const Icon = config.icon

  useEffect(() => {
    if (!dismissAfter) return
    const timer = setTimeout(() => {
      setExiting(true)
      setTimeout(() => onDismiss?.(), 300)
    }, dismissAfter)
    return () => clearTimeout(timer)
  }, [dismissAfter, onDismiss])

  return (
    <div
      className={`thought-float ${exiting ? 'exiting' : ''}`}
      onClick={() => {
        setExiting(true)
        setTimeout(() => onDismiss?.(), 300)
      }}
    >
      <GlassPanel intensity="md" className="p-3 rounded-xl" liquidGlass>
        <div className="flex items-start gap-2">
          <div
            className="shrink-0 w-6 h-6 rounded-full flex items-center justify-center"
            style={{ backgroundColor: `${config.color}20` }}
          >
            <Icon className="w-3.5 h-3.5" style={{ color: config.color }} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <span className="text-[9px] font-medium" style={{ color: config.color }}>
                {config.label}
              </span>
              {thought.confidence != null && (
                <span className="text-[8px] text-white/40">
                  {(thought.confidence * 100).toFixed(0)}%
                </span>
              )}
            </div>
            <p className="text-[11px] text-white/80 leading-relaxed line-clamp-3">
              {thought.content}
            </p>
          </div>
        </div>
      </GlassPanel>
    </div>
  )
}

export function ThoughtFloat({
  thoughts,
  maxVisible = 3,
  dismissAfterMs = 8000,
  onDismiss,
}: ThoughtFloatProps) {
  const visible = thoughts.slice(-maxVisible)

  if (visible.length === 0) return null

  return (
    <div className="fixed right-6 bottom-20 z-50 flex flex-col-reverse gap-2 pointer-events-none">
      {visible.map((thought) => (
        <div key={thought.id} className="pointer-events-auto">
          <ThoughtBubble
            thought={thought}
            dismissAfter={dismissAfterMs}
            onDismiss={() => onDismiss?.(thought.id)}
          />
        </div>
      ))}
    </div>
  )
}

export default ThoughtFloat
