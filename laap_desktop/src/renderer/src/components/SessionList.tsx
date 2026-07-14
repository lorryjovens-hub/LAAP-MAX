import React from 'react'
import { useSessionStore, type Session } from '../useSessionStore'

interface Props {
  onNewChat: () => void
}

const SessionList: React.FC<Props> = ({ onNewChat }) => {
  const sessions = useSessionStore((s) => s.sessions)
  const activeId = useSessionStore((s) => s.activeSessionId)
  const setActive = useSessionStore((s) => s.setActiveSession)
  const deleteSession = useSessionStore((s) => s.deleteSession)
  const renameSession = useSessionStore((s) => s.renameSession)

  const formatDate = (ts: number) => {
    const d = new Date(ts)
    const now = new Date()
    const diff = now.getTime() - d.getTime()
    if (diff < 86400000) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    if (diff < 604800000) return d.toLocaleDateString([], { weekday: 'short' })
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* New chat button */}
      <div style={{ padding: '12px 10px' }}>
        <button
          onClick={onNewChat}
          style={{
            width: '100%',
            padding: '8px 12px',
            borderRadius: 8,
            border: '1px dashed var(--border-light)',
            backgroundColor: 'transparent',
            color: 'var(--text-secondary)',
            fontSize: 13,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            transition: 'all var(--transition-fast)',
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.borderColor = 'var(--accent)'
            e.currentTarget.style.color = 'var(--accent)'
            e.currentTarget.style.backgroundColor = 'var(--accent-dim)'
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.borderColor = 'var(--border-light)'
            e.currentTarget.style.color = 'var(--text-secondary)'
            e.currentTarget.style.backgroundColor = 'transparent'
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New Chat
        </button>
      </div>

      {/* Session list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 6px' }}>
        {sessions.map((session) => (
          <div
            key={session.id}
            onClick={() => setActive(session.id)}
            style={{
              padding: '10px 12px',
              borderRadius: 8,
              marginBottom: 2,
              cursor: 'pointer',
              backgroundColor: session.id === activeId ? 'var(--bg-active)' : 'transparent',
              border: session.id === activeId ? '1px solid var(--border-accent)' : '1px solid transparent',
              transition: 'all var(--transition-fast)',
            }}
            onMouseOver={(e) => {
              if (session.id !== activeId) {
                e.currentTarget.style.backgroundColor = 'var(--bg-hover)'
              }
            }}
            onMouseOut={(e) => {
              if (session.id !== activeId) {
                e.currentTarget.style.backgroundColor = 'transparent'
              }
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round" style={{ flexShrink: 0 }}>
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 13,
                    fontWeight: 500,
                    color: session.id === activeId ? 'var(--accent)' : 'var(--text-primary)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                  title={session.title}
                >
                  {session.title}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                  {session.messageCount} msgs · {formatDate(session.updatedAt)}
                </div>
              </div>
              {/* Delete button */}
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  deleteSession(session.id)
                }}
                style={{
                  backgroundColor: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: 2,
                  borderRadius: 4,
                  opacity: 0,
                  transition: 'opacity var(--transition-fast)',
                  flexShrink: 0,
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.opacity = '1'
                  e.currentTarget.style.color = 'var(--error)'
                }}
                title="Delete session"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Bottom spacer for delete button hover */}
      <div style={{ padding: 8, textAlign: 'center', fontSize: 10, color: 'var(--text-muted)' }}>
        {sessions.length} conversations
      </div>
    </div>
  )
}

export default SessionList
