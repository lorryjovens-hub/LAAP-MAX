import React, { useEffect, useState } from 'react'

interface AgentState {
  agent: boolean
  psi_available: boolean
  modules: number
  psi?: Record<string, unknown>
}

const COLORS = {
  accent: '#00d4aa',
  online: '#00d4aa',
  offline: '#555',
}

const MetricCard: React.FC<{
  label: string
  value: string | number
  icon: React.ReactNode
  color?: string
}> = ({ label, value, icon, color }) => (
  <div
    style={{
      backgroundColor: 'var(--bg-elevated)',
      borderRadius: 12,
      padding: '16px 20px',
      border: '1px solid var(--border)',
      display: 'flex',
      alignItems: 'center',
      gap: 14,
      transition: 'all var(--transition-fast)',
    }}
  >
    <div style={{ color: color || COLORS.accent, flexShrink: 0 }}>
      {icon}
    </div>
    <div>
      <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2 }}>
        {value}
      </div>
      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
        {label}
      </div>
    </div>
  </div>
)

const Dashboard: React.FC = () => {
  const [state, setState] = useState<AgentState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  const fetchState = async () => {
    setRefreshing(true)
    try {
      const res = await fetch('http://localhost:8081/api/agent/state')
      const data = await res.json()
      setState(data)
      setError(null)
    } catch (e) {
      setError('Could not connect to backend')
    } finally {
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchState()
    const interval = setInterval(fetchState, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div style={{ padding: 32, height: '100%', overflowY: 'auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28 }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>
          Dashboard
        </h1>
        <button
          onClick={fetchState}
          style={{
            backgroundColor: 'transparent',
            border: '1px solid var(--border)',
            borderRadius: 8,
            padding: '6px 14px',
            color: 'var(--text-secondary)',
            fontSize: 12,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            transition: 'all var(--transition-fast)',
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.borderColor = 'var(--accent)'
            e.currentTarget.style.color = 'var(--accent)'
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.borderColor = 'var(--border)'
            e.currentTarget.style.color = 'var(--text-secondary)'
          }}
        >
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }}
          >
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
          Refresh
        </button>
      </div>

      {/* Connection status */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '10px 16px',
          borderRadius: 8,
          backgroundColor: error ? 'rgba(255,107,107,0.08)' : 'rgba(0,212,170,0.08)',
          marginBottom: 24,
          fontSize: 13,
          color: error ? '#ff6b6b' : COLORS.accent,
        }}
      >
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            backgroundColor: error ? '#ff6b6b' : COLORS.online,
            flexShrink: 0,
          }}
        />
        {error || (state?.agent ? 'Agent running' : 'Agent offline')}
      </div>

      {/* Metrics grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12, marginBottom: 28 }}>
        <MetricCard
          label="Agent Status"
          value={state?.agent ? 'Online' : 'Offline'}
          color={state?.agent ? COLORS.online : COLORS.offline}
          icon={
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          }
        />
        <MetricCard
          label="PSI Mode"
          value={state?.psi_available ? 'Active' : 'Inactive'}
          color={state?.psi_available ? COLORS.online : COLORS.offline}
          icon={
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <circle cx="12" cy="12" r="10" />
              <circle cx="12" cy="12" r="6" />
              <circle cx="12" cy="12" r="2" />
            </svg>
          }
        />
        <MetricCard
          label="Modules"
          value={state?.modules ?? '?'}
          icon={
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <rect x="2" y="2" width="8" height="8" rx="1" />
              <rect x="14" y="2" width="8" height="8" rx="1" />
              <rect x="2" y="14" width="8" height="8" rx="1" />
              <rect x="14" y="14" width="8" height="8" rx="1" />
            </svg>
          }
        />
        <MetricCard
          label="Connection"
          value={error ? 'Lost' : 'OK'}
          color={error ? '#ff6b6b' : COLORS.online}
          icon={
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M5 12h14" />
              <path d="M12 5l7 7-7 7" />
            </svg>
          }
        />
      </div>

      {/* Quick actions */}
      <h2 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>
        Quick Actions
      </h2>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {[
          { label: 'Open Chat', icon: '💬', action: 'chat' },
          { label: 'Settings', icon: '⚙', action: 'settings' },
        ].map((action) => (
          <div
            key={action.label}
            style={{
              padding: '12px 18px',
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border)',
              borderRadius: 10,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 13,
              color: 'var(--text-primary)',
              transition: 'all var(--transition-fast)',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.borderColor = 'var(--accent)'
              e.currentTarget.style.backgroundColor = 'var(--bg-active)'
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.borderColor = 'var(--border)'
              e.currentTarget.style.backgroundColor = 'var(--bg-elevated)'
            }}
          >
            <span>{action.icon}</span>
            <span>{action.label}</span>
          </div>
        ))}
      </div>

      {/* PSI details */}
      {state?.psi && Object.keys(state.psi).length > 0 && (
        <div style={{ marginTop: 28 }}>
          <h2 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>
            PSI State
          </h2>
          <pre style={{
            backgroundColor: 'var(--bg-elevated)',
            padding: 16,
            borderRadius: 8,
            fontSize: 12,
            color: 'var(--text-secondary)',
            overflow: 'auto',
            maxHeight: 200,
            border: '1px solid var(--border)',
          }}>
            {JSON.stringify(state.psi, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

export default Dashboard
