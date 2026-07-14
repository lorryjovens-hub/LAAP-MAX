/**
 * 应用设置状态管理（Zustand + persist）
 *
 * 持久化保存用户偏好到 localStorage，并在启动时恢复。
 * 后端地址、API Key、视频路径、玻璃强度、主题、全局热键、音频输入设备等配置均在此管理。
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/** 主题模式 */
export type ThemeMode = 'dark' | 'midnight' | 'obsidian'

/** 玻璃强度参数（模糊、饱和度、亮度） */
export interface GlassIntensity {
  blur: number
  saturate: number
  brightness: number
}

/** 全局热键配置 */
export interface HotkeyConfig {
  /** 显示/隐藏主窗口 */
  showWindow: string
  /** 按住说话（PTT） */
  ptt: string
}

/** 设置状态接口 */
export interface SettingsState {
  backendUrl: string
  apiKey: string
  /** 是否优先使用环境变量中的 API Key */
  useEnvApiKey: boolean
  videoPath: string
  glassIntensity: GlassIntensity
  theme: ThemeMode
  hotkeys: HotkeyConfig
  audioInputDeviceId: string
  /** 是否启用本地唤醒词监听 */
  wakeWordEnabled: boolean
  /** 唤醒词短语 */
  wakeWordPhrase: string
  /** 唤醒词灵敏度，0-1 */
  wakeWordSensitivity: number
  /** 是否启用 TTS 语音播放 */
  ttsEnabled: boolean
  /** TTS 播放音量，0-1 */
  ttsVolume: number
  /** 是否已完成首次启动引导 */
  hasCompletedOnboarding: boolean

  setBackendUrl: (url: string) => void
  setApiKey: (key: string) => void
  setUseEnvApiKey: (use: boolean) => void
  setVideoPath: (path: string) => void
  setGlassIntensity: (patch: Partial<GlassIntensity>) => void
  setTheme: (theme: ThemeMode) => void
  setHotkeys: (hotkeys: Partial<HotkeyConfig>) => void
  setAudioInputDeviceId: (id: string) => void
  setWakeWordEnabled: (enabled: boolean) => void
  setWakeWordPhrase: (phrase: string) => void
  setWakeWordSensitivity: (sensitivity: number) => void
  setTtsEnabled: (enabled: boolean) => void
  setTtsVolume: (volume: number) => void
  /** 重置为默认设置（保留 onboarding 完成状态） */
  resetToDefaults: () => void
  /** 标记引导已完成 */
  completeOnboarding: () => void
  /** 获取实际生效的 API Key */
  getEffectiveApiKey: () => string
}

/** 从环境变量读取默认后端地址与 API Key */
const ENV_BACKEND_URL = (import.meta.env.VITE_BACKEND_URL as string | undefined) ?? ''
const ENV_API_KEY = (import.meta.env.VITE_API_KEY as string | undefined) ?? ''

/** 默认玻璃强度 */
const defaultGlassIntensity: GlassIntensity = {
  blur: 12,
  saturate: 1.8,
  brightness: 1.16,
}

/** 默认全局热键（与 Electron 主进程注册保持一致） */
const defaultHotkeys: HotkeyConfig = {
  showWindow: 'CommandOrControl+Shift+L',
  ptt: 'CommandOrControl+Shift+Space',
}

/** 默认设置值 */
const defaultSettings: Omit<
  SettingsState,
  | 'setBackendUrl'
  | 'setApiKey'
  | 'setUseEnvApiKey'
  | 'setVideoPath'
  | 'setGlassIntensity'
  | 'setTheme'
  | 'setHotkeys'
  | 'setAudioInputDeviceId'
  | 'setWakeWordEnabled'
  | 'setWakeWordPhrase'
  | 'setWakeWordSensitivity'
  | 'setTtsEnabled'
  | 'setTtsVolume'
  | 'resetToDefaults'
  | 'completeOnboarding'
  | 'getEffectiveApiKey'
> = {
  backendUrl: ENV_BACKEND_URL || 'ws://127.0.0.1:8765',
  apiKey: '',
  useEnvApiKey: true,
  videoPath: '',
  glassIntensity: defaultGlassIntensity,
  theme: 'dark',
  hotkeys: defaultHotkeys,
  audioInputDeviceId: '',
  wakeWordEnabled: true,
  wakeWordPhrase: 'Hey LAAP',
  wakeWordSensitivity: 0.5,
  ttsEnabled: true,
  ttsVolume: 1,
  hasCompletedOnboarding: false,
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      ...defaultSettings,

      setBackendUrl: (url) => set({ backendUrl: url.trim() }),

      setApiKey: (key) => set({ apiKey: key }),

      setUseEnvApiKey: (use) => set({ useEnvApiKey: use }),

      setVideoPath: (path) => set({ videoPath: path }),

      setGlassIntensity: (patch) =>
        set((state) => ({
          glassIntensity: { ...state.glassIntensity, ...patch },
        })),

      setTheme: (theme) => set({ theme }),

      setHotkeys: (patch) =>
        set((state) => ({
          hotkeys: { ...state.hotkeys, ...patch },
        })),

      setAudioInputDeviceId: (id) => set({ audioInputDeviceId: id }),

      setWakeWordEnabled: (enabled) => set({ wakeWordEnabled: enabled }),

      setWakeWordPhrase: (phrase) => set({ wakeWordPhrase: phrase.trim() }),

      setWakeWordSensitivity: (sensitivity) =>
        set({ wakeWordSensitivity: Math.min(1, Math.max(0, sensitivity)) }),

      setTtsEnabled: (enabled) => set({ ttsEnabled: enabled }),

      setTtsVolume: (volume) =>
        set({ ttsVolume: Math.min(1, Math.max(0, volume)) }),

      resetToDefaults: () =>
        set((state) => ({
          ...defaultSettings,
          hasCompletedOnboarding: state.hasCompletedOnboarding,
        })),

      completeOnboarding: () => set({ hasCompletedOnboarding: true }),

      getEffectiveApiKey: () => {
        if (get().useEnvApiKey && ENV_API_KEY) {
          return ENV_API_KEY
        }
        return get().apiKey
      },
    }),
    {
      name: 'laap-client-settings',
    },
  ),
)
