import { create } from 'zustand'

export interface Session {
  id: string
  title: string
  createdAt: number
  updatedAt: number
  messageCount: number
}

export interface SessionState {
  sessions: Session[]
  activeSessionId: string | null
  setActiveSession: (id: string | null) => void
  createSession: () => string
  deleteSession: (id: string) => void
  renameSession: (id: string, title: string) => void
  updateSessionActivity: (id: string) => void
}

function generateId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

const STORAGE_KEY = 'laap-desktop-sessions'

const defaultSession: Session = {
  id: generateId(),
  title: 'New Chat',
  createdAt: Date.now(),
  updatedAt: Date.now(),
  messageCount: 0,
}

function loadSessions(): Session[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : [defaultSession]
  } catch {
    return [defaultSession]
  }
}

function persistSessions(sessions: Session[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions))
  } catch { /* ignore */ }
}

export const useSessionStore = create<SessionState>((set, get) => ({
  sessions: loadSessions(),
  activeSessionId: loadSessions()[0]?.id ?? null,

  setActiveSession: (id) => set({ activeSessionId: id }),

  createSession: () => {
    const session: Session = {
      id: generateId(),
      title: 'New Chat',
      createdAt: Date.now(),
      updatedAt: Date.now(),
      messageCount: 0,
    }
    const sessions = [session, ...get().sessions]
    set({ sessions, activeSessionId: session.id })
    persistSessions(sessions)
    return session.id
  },

  deleteSession: (id) => {
    const sessions = get().sessions.filter((s) => s.id !== id)
    const activeSessionId = get().activeSessionId === id
      ? (sessions[0]?.id ?? null)
      : get().activeSessionId
    set({ sessions, activeSessionId })
    persistSessions(sessions)
  },

  renameSession: (id, title) => {
    const sessions = get().sessions.map((s) =>
      s.id === id ? { ...s, title } : s
    )
    set({ sessions })
    persistSessions(sessions)
  },

  updateSessionActivity: (id) => {
    const sessions = get().sessions.map((s) =>
      s.id === id
        ? { ...s, updatedAt: Date.now(), messageCount: s.messageCount + 1 }
        : s
    )
    set({ sessions })
    persistSessions(sessions)
  },
}))
