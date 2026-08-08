import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type ThemeMode = 'dark' | 'midnight' | 'obsidian'

export interface GlassIntensity {
  blur: number; saturate: number; brightness: number
}

export interface HotkeyConfig {
  showWindow: string; ptt: string
}

export interface ProviderCredential {
  provider: string
  model: string
  creds: Record<string, string>
  baseUrl: string
}

export interface SettingsState {
  backendUrl: string
  apiKey: string
  useEnvApiKey: boolean
  videoPath: string
  glassIntensity: GlassIntensity
  theme: ThemeMode
  audioInputDeviceId: string
  hotkeys: HotkeyConfig
  wakeWordEnabled: boolean
  wakeWordPhrase: string
  wakeWordSensitivity: number
  ttsEnabled: boolean
  ttsVolume: number
  hasCompletedOnboarding: boolean
  useRealApi: boolean
  llm: ProviderCredential
  tts: ProviderCredential
  asr: ProviderCredential
  engineMode: 'direct' | 'consciousness'
  consciousnessUrl: string
  thinkingLevel: number
}

export interface SettingsActions {
  setBackendUrl: (url: string) => void
  setApiKey: (key: string) => void
  setUseEnvApiKey: (v: boolean) => void
  setVideoPath: (path: string) => void
  setGlassIntensity: (val: GlassIntensity) => void
  setTheme: (theme: ThemeMode) => void
  setAudioInputDeviceId: (id: string) => void
  setHotkeys: (hk: HotkeyConfig) => void
  setWakeWordEnabled: (en: boolean) => void
  setWakeWordPhrase: (p: string) => void
  setWakeWordSensitivity: (s: number) => void
  setTtsEnabled: (en: boolean) => void
  setTtsVolume: (v: number) => void
  setUseRealApi: (v: boolean) => void
  setLLM: (v: Partial<ProviderCredential>) => void
  setTTS: (v: Partial<ProviderCredential>) => void
  setASR: (v: Partial<ProviderCredential>) => void
  setEngineMode: (mode: 'direct' | 'consciousness') => void
  setConsciousnessUrl: (url: string) => void
  setThinkingLevel: (level: number) => void
  completeOnboarding: () => void
  resetOnboarding: () => void
  getEffectiveApiKey: () => string
  resetToDefaults: () => void
}

const DEFAULT_LLM: ProviderCredential = {
  provider: 'deepseek', model: 'deepseek-v4-pro',
  creds: {}, baseUrl: 'https://api.deepseek.com',
}

const DEFAULT_TTS: ProviderCredential = {
  provider: 'microsoft', model: 'zh-CN-XiaoxiaoNeural',
  creds: {}, baseUrl: 'eastasia',
}

const DEFAULT_ASR: ProviderCredential = {
  provider: 'aliyun', model: '',
  creds: {}, baseUrl: '',
}

const DEFAULTS: SettingsState = {
  backendUrl: 'ws://127.0.0.1:8763',
  apiKey: '',
  useEnvApiKey: false,
  videoPath: '',
  glassIntensity: { blur: 12, saturate: 1.8, brightness: 1.0 },
  theme: 'midnight',
  audioInputDeviceId: '',
  hotkeys: {
    showWindow: typeof process !== 'undefined' && (process as any)?.platform === 'win32'
      ? 'Super+Shift+A'
      : 'CommandOrControl+Shift+A',
    ptt: 'CommandOrControl+Shift+Space',
  },
  wakeWordEnabled: true,
  wakeWordPhrase: 'Hey LAAP',
  wakeWordSensitivity: 0.5,
  ttsEnabled: true,
  ttsVolume: 1,
  hasCompletedOnboarding: false,
  useRealApi: false,
  llm: { ...DEFAULT_LLM },
  tts: { ...DEFAULT_TTS },
  asr: { ...DEFAULT_ASR },
  engineMode: 'direct',
  consciousnessUrl: 'http://127.0.0.1:19420',
  thinkingLevel: 0,
}

export const useSettingsStore = create<SettingsState & SettingsActions>()(
  persist(
    (set, get) => ({
      ...DEFAULTS,

      setBackendUrl: (url) => set({ backendUrl: url }),
      setApiKey: (key) => set({ apiKey: key }),
      setUseEnvApiKey: (v) => set({ useEnvApiKey: v }),
      setVideoPath: (path) => set({ videoPath: path }),
      setGlassIntensity: (val) => set({ glassIntensity: val }),
      setTheme: (theme) => set({ theme }),
      setAudioInputDeviceId: (id) => set({ audioInputDeviceId: id }),
      setHotkeys: (hk) => set({ hotkeys: hk }),
      setWakeWordEnabled: (en) => set({ wakeWordEnabled: en }),
      setWakeWordPhrase: (p) => set({ wakeWordPhrase: p }),
      setWakeWordSensitivity: (s) => set({ wakeWordSensitivity: Math.min(1, Math.max(0, s)) }),
      setTtsEnabled: (en) => set({ ttsEnabled: en }),
      setTtsVolume: (v) => set({ ttsVolume: Math.min(1, Math.max(0, v)) }),
      setUseRealApi: (v) => set({ useRealApi: v }),
      setLLM: (v) => set((s) => ({ llm: { ...s.llm, ...v } })),
      setTTS: (v) => set((s) => ({ tts: { ...s.tts, ...v } })),
      setASR: (v) => set((s) => ({ asr: { ...s.asr, ...v } })),
      setEngineMode: (mode) => set({ engineMode: mode }),
      setConsciousnessUrl: (url) => set({ consciousnessUrl: url }),
      setThinkingLevel: (level) => set({ thinkingLevel: level }),
      completeOnboarding: () => set({ hasCompletedOnboarding: true }),
      resetOnboarding: () => set({ hasCompletedOnboarding: false }),

      getEffectiveApiKey: () => {
        const state = get()
        if (state.useEnvApiKey && typeof import.meta !== 'undefined') {
          return (import.meta as any).env?.VITE_API_KEY || state.apiKey
        }
        return state.apiKey
      },

      resetToDefaults: () => set((state) => ({ ...DEFAULTS, hasCompletedOnboarding: state.hasCompletedOnboarding })),
    }),
    {
      name: 'laap-client-settings',
      partialize: (state) => ({
        backendUrl: state.backendUrl,
        apiKey: state.apiKey,
        useEnvApiKey: state.useEnvApiKey,
        videoPath: state.videoPath,
        glassIntensity: state.glassIntensity,
        theme: state.theme,
        hotkeys: state.hotkeys,
        wakeWordEnabled: state.wakeWordEnabled,
        wakeWordPhrase: state.wakeWordPhrase,
        wakeWordSensitivity: state.wakeWordSensitivity,
        ttsEnabled: state.ttsEnabled,
        ttsVolume: state.ttsVolume,
        hasCompletedOnboarding: state.hasCompletedOnboarding,
        useRealApi: state.useRealApi,
        llm: state.llm,
        tts: state.tts,
        asr: state.asr,
      }),
    },
  ),
)
