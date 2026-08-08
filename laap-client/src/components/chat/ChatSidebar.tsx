/**
 * ChatSidebar — 对话侧边栏（Hanako 风格）
 *
 * 左侧会话列表，支持新建/切换/删除会话。
 * 折叠后仅显示图标。
 */

import { useState } from 'react'
import { MessageSquare, Plus, Trash2, Settings, ChevronLeft, PanelRight } from 'lucide-react'

export interface ChatSession {
  id: string
  title: string
  updatedAt: number
  messageCount: number
}

export interface ChatSidebarProps {
  sessions: ChatSession[]
  activeSessionId: string | null
  collapsed: boolean
  onNewSession: () => void
  onSelectSession: (id: string) => void
  onDeleteSession: (id: string) => void
  onToggleCollapse: () => void
  onOpenSettings: () => void
  onToggleRightPanel: () => void
}

export function ChatSidebar({
  sessions, activeSessionId, collapsed,
  onNewSession, onSelectSession, onDeleteSession,
  onToggleCollapse, onOpenSettings, onToggleRightPanel,
}: ChatSidebarProps) {
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)

  if (collapsed) {
    return (
      <div className="flex flex-col items-center gap-3 py-3 w-14 shrink-0 bg-black/20 border-r border-white/[0.06]">
        <button onClick={onNewSession} title="新建会话"
          className="w-9 h-9 rounded-xl bg-white/[0.06] hover:bg-white/[0.12] border border-white/[0.08] 
                     flex items-center justify-center transition-colors">
          <Plus className="w-4 h-4 text-white/70" />
        </button>
        <div className="flex-1 flex flex-col items-center gap-2 overflow-y-auto py-1">
          {sessions.map((s) => (
            <button key={s.id} onClick={() => onSelectSession(s.id)}
              title={s.title}
              className={`w-9 h-9 rounded-xl flex items-center justify-center transition-colors
                ${s.id === activeSessionId
                  ? 'bg-laap-accent/20 border border-laap-accent/40'
                  : 'bg-white/[0.04] hover:bg-white/[0.08] border border-transparent'}`}>
              <MessageSquare className="w-4 h-4 text-white/60" />
            </button>
          ))}
        </div>
        <button onClick={onToggleCollapse} title="展开侧边栏"
          className="w-9 h-9 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.06]
                     flex items-center justify-center transition-colors">
          <ChevronLeft className="w-4 h-4 text-white/50 rotate-180" />
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col w-56 shrink-0 bg-black/20 border-r border-white/[0.06]">
      {/* 头部 */}
      <div className="flex items-center justify-between px-3 h-11 border-b border-white/[0.06]">
        <span className="text-xs font-medium text-white/70">会话</span>
        <div className="flex items-center gap-1">
          <button onClick={onNewSession} title="新建会话"
            className="w-7 h-7 rounded-lg hover:bg-white/[0.08] flex items-center justify-center transition-colors">
            <Plus className="w-3.5 h-3.5 text-white/60" />
          </button>
          <button onClick={onToggleCollapse} title="折叠侧边栏"
            className="w-7 h-7 rounded-lg hover:bg-white/[0.08] flex items-center justify-center transition-colors">
            <ChevronLeft className="w-3.5 h-3.5 text-white/50" />
          </button>
        </div>
      </div>

      {/* 会话列表 */}
      <div className="flex-1 overflow-y-auto py-1 space-y-0.5 px-1.5">
        {sessions.length === 0 ? (
          <div className="text-center py-8">
            <MessageSquare className="w-8 h-8 text-white/15 mx-auto mb-2" />
            <p className="text-[11px] text-white/30">暂无会话</p>
            <button onClick={onNewSession}
              className="mt-2 text-[11px] text-laap-accent/60 hover:text-laap-accent transition-colors">
              新建一个
            </button>
          </div>
        ) : (
          sessions.map((s) => (
            <div key={s.id}
              className={`group flex items-center gap-2 px-2.5 py-2 rounded-lg cursor-pointer transition-colors
                ${s.id === activeSessionId
                  ? 'bg-laap-accent/12 text-white'
                  : 'hover:bg-white/[0.05] text-white/70'}`}
              onClick={() => onSelectSession(s.id)}>
              <MessageSquare className="w-3.5 h-3.5 shrink-0 text-white/40" />
              <span className="flex-1 text-xs truncate">{s.title}</span>
              <span className="text-[10px] text-white/30 shrink-0">{s.messageCount}</span>
              {confirmDelete === s.id ? (
                <button onClick={(e) => { e.stopPropagation(); onDeleteSession(s.id); setConfirmDelete(null) }}
                  className="w-5 h-5 rounded flex items-center justify-center bg-red-500/20 text-red-400 text-[10px]">
                  确认
                </button>
              ) : (
                <button onClick={(e) => { e.stopPropagation(); setConfirmDelete(s.id) }}
                  className="w-5 h-5 rounded flex items-center justify-center opacity-0 group-hover:opacity-100
                             hover:bg-white/[0.08] transition-all">
                  <Trash2 className="w-3 h-3 text-white/40 hover:text-red-400" />
                </button>
              )}
            </div>
          ))
        )}
      </div>

      {/* 底部操作 */}
      <div className="flex items-center gap-1 px-2 py-2 border-t border-white/[0.06]">
        <button onClick={onOpenSettings} title="设置"
          className="flex-1 flex items-center gap-1.5 px-2 py-1.5 rounded-lg hover:bg-white/[0.06] text-xs text-white/50 hover:text-white/70 transition-colors">
          <Settings className="w-3.5 h-3.5" />
          设置
        </button>
        <button onClick={onToggleRightPanel} title="右侧面板"
          className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg hover:bg-white/[0.06] text-xs text-white/50 hover:text-white/70 transition-colors">
          <PanelRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  )
}