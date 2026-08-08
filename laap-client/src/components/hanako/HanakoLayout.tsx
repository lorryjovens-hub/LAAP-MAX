/**
 * HanakoInspiredLayout — 将 Hanako 的 GUI 风格注入 LAAP Client
 *
 * 核心设计：
 * 1. 三栏布局：ChatSidebar(左) | ChatArea(中) | ActivityPanel(右)
 * 2. 浮动输入框 (FloatingInput) 在底部
 * 3. 窗口控制栏顶部
 * 4. 状态栏底部
 *
 * 用法：在 App.tsx 中将此组件包裹现有内容
 */

import React from 'react'
import type { Surface } from '../../laap/scene'
import type { FocusFrame } from '../../laap/memory'

// ── 设计令牌（Hanako 风格） ──────────────────────────────

export const HANAKO_TOKENS = {
  sidebarWidth: 260,
  sidebarCollapsedWidth: 48,
  rightPanelWidth: 320,
  titleBarHeight: 38,
  statusBarHeight: 28,
  borderRadius: '8px',
  fontMono: "'JetBrains Mono', 'Fira Code', monospace",
  fontUI: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
  transitionFast: '150ms ease',
  transitionSmooth: '250ms cubic-bezier(0.4, 0, 0.2, 1)',
  zSidebar: 30,
  zOverlay: 50,
  zModal: 60,
  zToast: 70,
} as const

// ── Hanako 风格的主题色 ──────────────────────────────

export type HanakoTheme = 'dark' | 'dim' | 'light'

export const HANAKO_THEMES: Record<HanakoTheme, Record<string, string>> = {
  dark: {
    bg: '#0d0d0d',
    bgElevated: '#1a1a1a',
    bgOverlay: 'rgba(0,0,0,0.6)',
    surface: '#242424',
    border: 'rgba(255,255,255,0.08)',
    text: '#e8e8e8',
    textSecondary: '#888',
    accent: '#6c5ce7',
    accentHover: '#7c6cf7',
    green: '#00b894',
    red: '#e17055',
    yellow: '#fdcb6e',
  },
  dim: {
    bg: '#1a1b2e',
    bgElevated: '#232540',
    bgOverlay: 'rgba(0,0,0,0.5)',
    surface: '#2d2f50',
    border: 'rgba(255,255,255,0.06)',
    text: '#d0d0e0',
    textSecondary: '#8888a0',
    accent: '#7c6cf7',
    accentHover: '#8c7cf7',
    green: '#00b894',
    red: '#e17055',
    yellow: '#fdcb6e',
  },
  light: {
    bg: '#f8f9fa',
    bgElevated: '#ffffff',
    bgOverlay: 'rgba(0,0,0,0.3)',
    surface: '#ffffff',
    border: 'rgba(0,0,0,0.08)',
    text: '#1a1a2e',
    textSecondary: '#6c6c80',
    accent: '#6c5ce7',
    accentHover: '#5c4ce7',
    green: '#00b894',
    red: '#e17055',
    yellow: '#fdcb6e',
  },
}

// ── 聊天侧边栏 ──────────────────────────────

interface ChatSidebarProps {
  sessions: Array<{ id: string; title: string; preview: string; time: string }>
  activeSessionId?: string
  onSelectSession: (id: string) => void
  collapsed: boolean
  onToggleCollapse: () => void
  theme: HanakoTheme
}

export function ChatSidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  collapsed,
  onToggleCollapse,
  theme,
}: ChatSidebarProps) {
  const colors = HANAKO_THEMES[theme]

  if (collapsed) {
    return (
      <div style={{
        width: HANAKO_TOKENS.sidebarCollapsedWidth,
        background: colors.bgElevated,
        borderRight: `1px solid ${colors.border}`,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: '12px',
        gap: '8px',
      }}>
        <button onClick={onToggleCollapse}
          style={{ background: 'none', border: 'none', color: colors.textSecondary, cursor: 'pointer', fontSize: '18px', padding: '8px' }}
          title="Expand sidebar"
        >☰</button>
        {sessions.slice(0, 5).map(s => (
          <button key={s.id}
            onClick={() => onSelectSession(s.id)}
            style={{
              width: 32, height: 32, borderRadius: '8px', border: 'none',
              background: s.id === activeSessionId ? colors.accent : colors.surface,
              color: s.id === activeSessionId ? '#fff' : colors.textSecondary,
              cursor: 'pointer', fontSize: '12px', fontWeight: 600,
            }}
            title={s.title}
          >{s.title.charAt(0)}</button>
        ))}
      </div>
    )
  }

  return (
    <div style={{
      width: HANAKO_TOKENS.sidebarWidth,
      background: colors.bgElevated,
      borderRight: `1px solid ${colors.border}`,
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        padding: '12px 16px',
        borderBottom: `1px solid ${colors.border}`,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <span style={{ fontWeight: 600, color: colors.text, fontSize: '14px' }}>Aris</span>
        <button onClick={onToggleCollapse}
          style={{ background: 'none', border: 'none', color: colors.textSecondary, cursor: 'pointer', fontSize: '14px', padding: '4px' }}
        >◀</button>
      </div>

      {/* Session list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
        {sessions.map(s => (
          <div key={s.id}
            onClick={() => onSelectSession(s.id)}
            style={{
              padding: '10px 12px', borderRadius: '8px', marginBottom: '4px', cursor: 'pointer',
              background: s.id === activeSessionId ? colors.accent + '20' : 'transparent',
              borderLeft: s.id === activeSessionId ? `3px solid ${colors.accent}` : '3px solid transparent',
              transition: HANAKO_TOKENS.transitionFast,
            }}
          >
            <div style={{ fontWeight: 500, color: colors.text, fontSize: '13px', marginBottom: '2px' }}>{s.title}</div>
            <div style={{ color: colors.textSecondary, fontSize: '11px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.preview}</div>
            <div style={{ color: colors.textSecondary, fontSize: '10px', marginTop: '4px' }}>{s.time}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Activity Panel (右侧面板) ──────────────────────────────

interface ActivityPanelProps {
  focusFrames: FocusFrame[]
  surfaces: Surface[]
  perceptionHealth: number
  tokenSavings: { input: number; dropped: number } | null
  theme: HanakoTheme
  onClose?: () => void
}

export function ActivityPanel({
  focusFrames,
  surfaces,
  perceptionHealth,
  tokenSavings,
  theme,
  onClose,
}: ActivityPanelProps) {
  const colors = HANAKO_THEMES[theme]

  return (
    <div style={{
      width: HANAKO_TOKENS.rightPanelWidth,
      background: colors.bgElevated,
      borderLeft: `1px solid ${colors.border}`,
      display: 'flex', flexDirection: 'column', overflow: 'hidden',
      fontSize: '12px',
    }}>
      {/* Header */}
      <div style={{
        padding: '12px 16px', borderBottom: `1px solid ${colors.border}`,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <span style={{ fontWeight: 600, color: colors.text }}>Activity</span>
        {onClose && (
          <button onClick={onClose}
            style={{ background: 'none', border: 'none', color: colors.textSecondary, cursor: 'pointer', fontSize: '14px' }}
          >✕</button>
        )}
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Consciousness Status */}
        <Section title="Consciousness" colors={colors}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: 8, height: 8, borderRadius: '50%',
              background: perceptionHealth > 0.7 ? colors.green : perceptionHealth > 0.3 ? colors.yellow : colors.red,
              boxShadow: `0 0 6px ${perceptionHealth > 0.7 ? colors.green : colors.yellow}`,
            }} />
            <span style={{ color: colors.text }}>Health: {Math.round(perceptionHealth * 100)}%</span>
          </div>
        </Section>

        {/* Focus Stack */}
        <Section title="Focus Stack" colors={colors}>
          {focusFrames.length === 0 ? (
            <div style={{ color: colors.textSecondary, fontStyle: 'italic' }}>No active focus</div>
          ) : (
            focusFrames.slice(0, 3).map(f => (
              <div key={f.id} style={{
                padding: '6px 8px', borderRadius: '6px',
                background: f.active ? colors.accent + '15' : 'transparent',
                borderLeft: f.active ? `2px solid ${colors.accent}` : 'none',
                marginBottom: '4px',
              }}>
                <div style={{ color: colors.text, fontWeight: 500, fontSize: '11px' }}>{f.intent.slice(0, 40)}</div>
                <div style={{ color: colors.textSecondary, fontSize: '10px' }}>
                  {f.entities.slice(0, 3).join(', ')} · {f.turnCount} turns
                </div>
              </div>
            ))
          )}
        </Section>

        {/* Token Savings */}
        {tokenSavings && (
          <Section title="Token Efficiency" colors={colors}>
            <div style={{ color: colors.text }}>Input sections: {tokenSavings.input}</div>
            <div style={{ color: colors.green }}>Dropped (saved): {tokenSavings.dropped}</div>
            <div style={{ color: colors.textSecondary, fontSize: '10px', marginTop: '4px' }}>
              ~{Math.round(tokenSavings.dropped / Math.max(tokenSavings.input, 1) * 100)}% reduction
            </div>
          </Section>
        )}

        {/* Scene Surfaces */}
        <Section title="Scene Surfaces" colors={colors}>
          {surfaces.length === 0 ? (
            <div style={{ color: colors.textSecondary, fontStyle: 'italic' }}>No active surfaces</div>
          ) : (
            surfaces.slice(0, 5).map(s => (
              <div key={s.id} style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                padding: '4px 0',
              }}>
                <span style={{ color: s.focus ? colors.accent : colors.textSecondary, fontSize: '10px' }}>
                  {s.kind === 'text' ? '📝' : s.kind === 'metric' ? '📊' : s.kind === 'progress' ? '⏳' : '📦'}
                </span>
                <span style={{ color: colors.textSecondary, fontSize: '10px' }}>{s.id}</span>
              </div>
            ))
          )}
        </Section>
      </div>
    </div>
  )
}

// ── 辅助组件 ──────────────────────────────

function Section({
  title,
  colors,
  children,
}: {
  title: string
  colors: Record<string, string>
  children: React.ReactNode
}) {
  return (
    <div>
      <div style={{
        fontWeight: 600, color: colors.textSecondary, fontSize: '10px',
        textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px',
      }}>
        {title}
      </div>
      {children}
    </div>
  )
}

// ── 状态栏 ──────────────────────────────

interface StatusBarProps {
  connectionStatus: string
  perceptionHealth: number
  activeFocus: string | null
  isStreaming: boolean
  theme: HanakoTheme
}

export function StatusBar({
  connectionStatus,
  perceptionHealth,
  activeFocus,
  isStreaming,
  theme,
}: StatusBarProps) {
  const colors = HANAKO_THEMES[theme]

  const statusColor = connectionStatus === 'open' ? colors.green
    : connectionStatus === 'connecting' ? colors.yellow
    : colors.red

  return (
    <div style={{
      height: HANAKO_TOKENS.statusBarHeight,
      background: colors.bgElevated,
      borderTop: `1px solid ${colors.border}`,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 12px', fontSize: '11px', color: colors.textSecondary,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: statusColor, display: 'inline-block' }} />
          {connectionStatus}
        </span>
        {isStreaming && <span style={{ color: colors.accent }}>Streaming...</span>}
        {activeFocus && <span>Focus: {activeFocus.slice(0, 20)}</span>}
      </div>
      <div>
        <span>🧠 {Math.round(perceptionHealth * 100)}%</span>
      </div>
    </div>
  )
}
