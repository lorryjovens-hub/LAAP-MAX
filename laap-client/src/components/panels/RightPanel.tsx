/**
 * RightPanel — 右侧面板（Hanako 风格）
 *
 * 包含：会话状态卡片、待办事项、Agent 活动、工作流状态
 */

import { useState } from 'react'
import { CheckCircle2, Circle, Bot, Brain, X, FileText, Zap } from 'lucide-react'

interface TodoItem {
  id: string
  text: string
  done: boolean
}

interface RightPanelProps {
  onClose?: () => void
  sessionStats?: { tokens: number; cost: number; messages: number }
  agentActivities?: { name: string; status: string; action: string }[]
}

export function RightPanel({ onClose, sessionStats, agentActivities }: RightPanelProps) {
  const [todos, setTodos] = useState<TodoItem[]>([])
  const [newTodo, setNewTodo] = useState('')

  const addTodo = () => {
    if (!newTodo.trim()) return
    setTodos([...todos, { id: Date.now().toString(), text: newTodo.trim(), done: false }])
    setNewTodo('')
  }

  const toggleTodo = (id: string) => {
    setTodos(todos.map(t => t.id === id ? { ...t, done: !t.done } : t))
  }

  const deleteTodo = (id: string) => {
    setTodos(todos.filter(t => t.id !== id))
  }

  return (
    <div className="w-72 shrink-0 bg-black/20 border-l border-white/[0.06] flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 h-10 border-b border-white/[0.06]">
        <span className="text-xs font-medium text-white/70">面板</span>
        {onClose && (
          <button onClick={onClose} className="w-6 h-6 rounded flex items-center justify-center hover:bg-white/[0.08] text-white/40">
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 p-3">
        {/* 会话状态 */}
        <Section title="会话状态" icon={FileText}>
          <div className="space-y-1.5">
            <div className="flex justify-between text-[11px]">
              <span className="text-white/50">消息</span>
              <span className="text-white/80 font-mono">{sessionStats?.messages || 0}</span>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-white/50">Token</span>
              <span className="text-white/80 font-mono">{sessionStats?.tokens?.toLocaleString() || 0}</span>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-white/50">成本</span>
              <span className="text-laap-accent/80 font-mono">${sessionStats?.cost?.toFixed(4) || '0.0000'}</span>
            </div>
            <div className="mt-2 pt-2 border-t border-white/[0.06] flex items-center gap-1.5 text-[10px] text-laap-accent/60">
              <Zap className="w-3 h-3" />
              0-token 优先引擎
            </div>
          </div>
        </Section>

        {/* 待办事项 */}
        <Section title="待办事项" icon={CheckCircle2}>
          <div className="space-y-1">
            {todos.map(todo => (
              <div key={todo.id} className="flex items-center gap-2 group">
                <button onClick={() => toggleTodo(todo.id)}
                  className={`shrink-0 ${todo.done ? 'text-emerald-400' : 'text-white/30 hover:text-white/50'}`}>
                  {todo.done ? <CheckCircle2 className="w-3.5 h-3.5" /> : <Circle className="w-3.5 h-3.5" />}
                </button>
                <span className={`flex-1 text-[11px] ${todo.done ? 'text-white/30 line-through' : 'text-white/70'}`}>
                  {todo.text}
                </span>
                <button onClick={() => deleteTodo(todo.id)}
                  className="shrink-0 opacity-0 group-hover:opacity-100 text-white/30 hover:text-red-400 transition-all">
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
            <div className="flex gap-1 pt-1">
              <input type="text" value={newTodo} onChange={e => setNewTodo(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') addTodo() }}
                placeholder="新增待办..."
                className="flex-1 bg-white/[0.05] border border-white/[0.08] rounded px-2 py-1 text-[10px] text-white/70 placeholder:text-white/30 focus:outline-none focus:border-laap-accent/50" />
              <button onClick={addTodo}
                className="px-2 py-1 rounded bg-laap-accent/20 text-[10px] text-laap-accent/80 hover:bg-laap-accent/30 transition-colors">添加</button>
            </div>
          </div>
        </Section>

        {/* Agent 活动 */}
        <Section title="Agent 活动" icon={Bot}>
          {(agentActivities || []).length === 0 ? (
            <div className="text-[11px] text-white/30 italic">暂无活动</div>
          ) : (
            <div className="space-y-1.5">
              {(agentActivities || []).slice(0, 5).map((a, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-laap-accent/60" />
                  <span className="text-[11px] text-white/60">{a.name}</span>
                  <span className="text-[10px] text-white/40">{a.action}</span>
                </div>
              ))}
            </div>
          )}
          <div className="mt-2 flex items-center gap-1.5 text-[10px] text-white/30">
            <Brain className="w-3 h-3" />
            认知引擎运行中
          </div>
        </Section>
      </div>
    </div>
  )
}

function Section({ title, icon: Icon, children }: { title: string; icon: React.ElementType; children: React.ReactNode }) {
  return (
    <div className="bg-white/[0.03] rounded-lg border border-white/[0.06] overflow-hidden">
      <div className="flex items-center gap-1.5 px-3 py-2 border-b border-white/[0.04]">
        {Icon && <Icon className="w-3 h-3 text-white/40" />}
        <span className="text-[10px] font-medium text-white/50 uppercase tracking-wider">{title}</span>
      </div>
      <div className="px-3 py-2">
        {children}
      </div>
    </div>
  )
}