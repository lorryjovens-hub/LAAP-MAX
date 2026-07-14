import { create } from 'zustand'

export type Theme = 'dark' | 'light'

export interface SettingsState {
  theme: Theme
  domain: string
  usePSI: boolean
  ttsEnabled: boolean
  autoConnect: boolean
  backendUrl: string
  wsUrl: string
  setTheme: (theme: Theme) => void
  setDomain: (domain: string) => void
  setUsePSI: (use: boolean) => void
  setTtsEnabled: (enabled: boolean) => void
  setAutoConnect: (auto: boolean) => void
}

const STORAGE_KEY = 'laap-desktop-settings'

function loadSettings(): Partial<SettingsState> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function saveSettings(state: SettingsState) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      theme: state.theme,
      domain: state.domain,
      usePSI: state.usePSI,
      ttsEnabled: state.ttsEnabled,
      autoConnect: state.autoConnect,
    }))
  } catch { /* ignore quota errors */ }
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  ...{
    theme: 'dark' as Theme,
    domain: 'general',
    usePSI: false,
    ttsEnabled: false,
    autoConnect: true,
    backendUrl: 'http://localhost:8081',
    wsUrl: 'ws://localhost:8766',
  },
  ...loadSettings(),

  setTheme: (theme) => {
    set({ theme })
    document.documentElement.setAttribute('data-theme', theme)
    saveSettings(get())
  },
  setDomain: (domain) => {
    set({ domain })
    saveSettings(get())
  },
  setUsePSI: (use) => {
    set({ usePSI: use })
    saveSettings(get())
  },
  setTtsEnabled: (enabled) => {
    set({ ttsEnabled: enabled })
    saveSettings(get())
  },
  setAutoConnect: (auto) => {
    set({ autoConnect: auto })
    saveSettings(get())
  },
}))
