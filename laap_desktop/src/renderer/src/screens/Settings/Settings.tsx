import React from 'react'
import { useSettingsStore, type Theme } from '../../useSettingsStore'

const COLORS = {
  accent: '#00d4aa',
  error: '#ff6b6b',
}

const Settings: React.FC = () => {
  const settings = useSettingsStore()
  const [saving, setSaving] = React.useState(false)

  const handleReset = () => {
    if (window.confirm('Reset all settings to defaults?')) {
      localStorage.removeItem('laap-desktop-settings')
      window.location.reload()
    }
  }

  return (
    <div style={{ padding: 32, maxWidth: 640, margin: '0 auto', height: '100%', overflowY: 'auto' }}>
      <h1 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 24 }}>
        Settings
      </h1>

      {/* Theme */}
      <Section title="Appearance">
        <SelectRow
          label="Theme"
          value={settings.theme}
          options={[
            { value: 'dark', label: 'Dark' },
            { value: 'light', label: 'Light' },
          ]}
          onChange={(v) => settings.setTheme(v as Theme)}
        />
      </Section>

      {/* Chat */}
      <Section title="Chat">
        <SelectRow
          label="Domain"
          value={settings.domain}
          options={[
            { value: 'general', label: 'General' },
            { value: 'coding', label: 'Coding' },
            { value: 'debugging', label: 'Debugging' },
            { value: 'architecture', label: 'Architecture' },
          ]}
          onChange={settings.setDomain}
        />
        <ToggleRow
          label="PSI Mode"
          desc="Enable PSI cognitive processing"
          checked={settings.usePSI}
          onChange={settings.setUsePSI}
        />
      </Section>

      {/* Voice */}
      <Section title="Voice & Audio">
        <ToggleRow
          label="Text-to-Speech"
          desc="Voice output for agent responses"
          checked={settings.ttsEnabled}
          onChange={settings.setTtsEnabled}
        />
      </Section>

      {/* Connection */}
      <Section title="Connection">
        <ToggleRow
          label="Auto-connect on start"
          checked={settings.autoConnect}
          onChange={settings.setAutoConnect}
        />
        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>
          Backend: {settings.backendUrl}
          <br />
          WebSocket: {settings.wsUrl}
        </div>
      </Section>

      {/* About */}
      <Section title="About">
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          <strong style={{ color: COLORS.accent }}>LAAP Desktop</strong> v0.1.0
          <br />
          Digital Lifeform Client
          <br />
          Powered by LAAP AGI Framework
        </div>
      </Section>

      {/* Reset */}
      <div style={{ marginTop: 32, paddingTop: 24, borderTop: '1px solid var(--border)' }}>
        <button
          onClick={handleReset}
          style={{
            padding: '8px 20px',
            borderRadius: 8,
            border: `1px solid ${COLORS.error}`,
            backgroundColor: 'transparent',
            color: COLORS.error,
            fontSize: 13,
            cursor: 'pointer',
            transition: 'all var(--transition-fast)',
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(255,107,107,0.1)'
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent'
          }}
        >
          Reset All Settings
        </button>
      </div>
    </div>
  )
}

// ── Helpers ──

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div style={{ marginBottom: 24 }}>
    <h2 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>
      {title}
    </h2>
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {children}
    </div>
  </div>
)

const SelectRow: React.FC<{
  label: string
  value: string
  options: { value: string; label: string }[]
  onChange: (v: string) => void
}> = ({ label, value, options, onChange }) => (
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', backgroundColor: 'var(--bg-elevated)', borderRadius: 8 }}>
    <span style={{ fontSize: 13, color: 'var(--text-primary)' }}>{label}</span>
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      style={{
        backgroundColor: 'var(--input-bg)',
        color: 'var(--text-primary)',
        border: '1px solid var(--border)',
        borderRadius: 6,
        padding: '6px 24px 6px 10px',
        fontSize: 13,
        outline: 'none',
        cursor: 'pointer',
        appearance: 'none',
        backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%238892b0'/%3E%3C/svg%3E")`,
        backgroundRepeat: 'no-repeat',
        backgroundPosition: 'right 8px center',
      }}
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  </div>
)

const ToggleRow: React.FC<{
  label: string
  desc?: string
  checked: boolean
  onChange: (v: boolean) => void
}> = ({ label, desc, checked, onChange }) => (
  <div
    style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '8px 12px',
      backgroundColor: 'var(--bg-elevated)',
      borderRadius: 8,
      cursor: 'pointer',
    }}
    onClick={() => onChange(!checked)}
  >
    <div>
      <div style={{ fontSize: 13, color: 'var(--text-primary)' }}>{label}</div>
      {desc && <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{desc}</div>}
    </div>
    <div
      style={{
        width: 36,
        height: 20,
        borderRadius: 10,
        backgroundColor: checked ? COLORS.accent : 'var(--text-muted)',
        position: 'relative',
        transition: 'background-color var(--transition-fast)',
        flexShrink: 0,
      }}
    >
      <div
        style={{
          width: 16,
          height: 16,
          borderRadius: '50%',
          backgroundColor: '#fff',
          position: 'absolute',
          top: 2,
          left: checked ? 18 : 2,
          transition: 'left var(--transition-fast)',
          boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
        }}
      />
    </div>
  </div>
)

export default Settings
