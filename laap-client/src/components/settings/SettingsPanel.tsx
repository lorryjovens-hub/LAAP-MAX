/**
 * SettingsPanel：应用设置面板
 *
 * 从标题栏设置按钮以抽屉形式展开，支持配置后端地址、API Key、全局热键、
 * 音频输入设备、玻璃强度、主题以及本地视频路径。
 * 所有改动仅在点击“保存”后写入 settingsStore，测试连接使用临时 WebSocket。
 */

import { useEffect, useRef, useState } from 'react'
import {
  X,
  Save,
  RotateCcw,
  Link,
  Keyboard,
  Mic,
  SlidersHorizontal,
  Film,
  Check,
  AlertCircle,
  Loader2,
  Volume2,
} from 'lucide-react'
import { GlassPanel } from '../glass/GlassPanel'
import { GlassButton } from '../glass/GlassButton'
import { useSettingsStore, type GlassIntensity, type ThemeMode, type HotkeyConfig } from '../../store/settingsStore'

export interface SettingsPanelProps {
  open: boolean
  onClose: () => void
}

interface AudioDeviceInfo {
  deviceId: string
  label: string
}

type TestStatus = 'idle' | 'testing' | 'success' | 'error'

const THEME_OPTIONS: { value: ThemeMode; label: string; bg: string }[] = [
  { value: 'dark', label: '深空黑', bg: '#050608' },
  { value: 'midnight', label: '午夜蓝', bg: '#0a0f1c' },
  { value: 'obsidian', label: '曜石紫', bg: '#100818' },
]

function formatShortcut(shortcut: string): string {
  return shortcut
    .replace('CommandOrControl', 'Ctrl')
    .replace('Shift', 'Shift')
    .replace('Space', '空格')
}

function SectionTitle({ icon: Icon, title }: { icon: React.ElementType; title: string }) {
  return (
    <div className="flex items-center gap-2 text-xs font-medium text-white/50 uppercase tracking-wider mb-3">
      <Icon className="w-3.5 h-3.5" />
      <span>{title}</span>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="block text-xs text-white/60">{label}</label>
      {children}
    </div>
  )
}

export function SettingsPanel({ open, onClose }: SettingsPanelProps) {
  const store = useSettingsStore()
  const [draft, setDraft] = useState({
    backendUrl: store.backendUrl,
    apiKey: store.apiKey,
    useEnvApiKey: store.useEnvApiKey,
    videoPath: store.videoPath,
    glassIntensity: { ...store.glassIntensity },
    theme: store.theme,
    audioInputDeviceId: store.audioInputDeviceId,
    hotkeys: { ...store.hotkeys },
    wakeWordEnabled: store.wakeWordEnabled,
    wakeWordPhrase: store.wakeWordPhrase,
    wakeWordSensitivity: store.wakeWordSensitivity,
    ttsEnabled: store.ttsEnabled,
    ttsVolume: store.ttsVolume,
  })
  const [devices, setDevices] = useState<AudioDeviceInfo[]>([])
  const [testStatus, setTestStatus] = useState<TestStatus>('idle')
  const testWsRef = useRef<WebSocket | null>(null)

  // 面板打开时从 store 同步最新值，并枚举音频设备
  useEffect(() => {
    if (!open) return
    setDraft({
      backendUrl: store.backendUrl,
      apiKey: store.apiKey,
      useEnvApiKey: store.useEnvApiKey,
      videoPath: store.videoPath,
      glassIntensity: { ...store.glassIntensity },
      theme: store.theme,
      audioInputDeviceId: store.audioInputDeviceId,
      hotkeys: { ...store.hotkeys },
      wakeWordEnabled: store.wakeWordEnabled,
      wakeWordPhrase: store.wakeWordPhrase,
      wakeWordSensitivity: store.wakeWordSensitivity,
      ttsEnabled: store.ttsEnabled,
      ttsVolume: store.ttsVolume,
    })
    setTestStatus('idle')

    async function enumerateDevices() {
      try {
        if (!navigator.mediaDevices?.enumerateDevices) return
        const list = await navigator.mediaDevices.enumerateDevices()
        const audioInputs = list
          .filter((d) => d.kind === 'audioinput')
          .map((d) => ({
            deviceId: d.deviceId,
            label: d.label || `麦克风 ${d.deviceId.slice(0, 8) || '默认'}`,
          }))
        setDevices(audioInputs)
      } catch {
        setDevices([])
      }
    }

    void enumerateDevices()
  }, [open, store])

  // 关闭时清理测试连接
  useEffect(() => {
    if (open) return
    if (testWsRef.current) {
      testWsRef.current.close()
      testWsRef.current = null
    }
  }, [open])

  const updateGlass = (patch: Partial<GlassIntensity>) => {
    setDraft((prev) => ({
      ...prev,
      glassIntensity: { ...prev.glassIntensity, ...patch },
    }))
  }

  const handleSave = () => {
    store.setBackendUrl(draft.backendUrl)
    store.setApiKey(draft.apiKey)
    store.setUseEnvApiKey(draft.useEnvApiKey)
    store.setVideoPath(draft.videoPath)
    store.setGlassIntensity(draft.glassIntensity)
    store.setTheme(draft.theme)
    store.setAudioInputDeviceId(draft.audioInputDeviceId)
    store.setHotkeys(draft.hotkeys)
    store.setWakeWordEnabled(draft.wakeWordEnabled)
    store.setWakeWordPhrase(draft.wakeWordPhrase)
    store.setWakeWordSensitivity(draft.wakeWordSensitivity)
    store.setTtsEnabled(draft.ttsEnabled)
    store.setTtsVolume(draft.ttsVolume)
    // 将新的热键配置同步到 Electron 主进程
    window.desktop?.registerHotkeys(draft.hotkeys)
    onClose()
  }

  const handleReset = () => {
    store.resetToDefaults()
    setDraft({
      backendUrl: store.backendUrl,
      apiKey: store.apiKey,
      useEnvApiKey: store.useEnvApiKey,
      videoPath: store.videoPath,
      glassIntensity: { ...store.glassIntensity },
      theme: store.theme,
      audioInputDeviceId: store.audioInputDeviceId,
      hotkeys: { ...store.hotkeys },
      wakeWordEnabled: store.wakeWordEnabled,
      wakeWordPhrase: store.wakeWordPhrase,
      wakeWordSensitivity: store.wakeWordSensitivity,
      ttsEnabled: store.ttsEnabled,
      ttsVolume: store.ttsVolume,
    })
  }

  const handleSelectVideo = async () => {
    try {
      const result = await window.desktop?.selectVideo()
      if (result?.filePath) {
        setDraft((prev) => ({ ...prev, videoPath: result.filePath }))
      }
    } catch {
      // 选择失败时保持原值
    }
  }

  const handleTestConnection = () => {
    if (testWsRef.current) {
      testWsRef.current.close()
      testWsRef.current = null
    }

    setTestStatus('testing')
    const url = draft.backendUrl

    try {
      const ws = new WebSocket(url)
      testWsRef.current = ws

      const timer = setTimeout(() => {
        setTestStatus('error')
        ws.close()
      }, 5000)

      ws.onopen = () => {
        clearTimeout(timer)
        setTestStatus('success')
        ws.close()
      }

      ws.onerror = () => {
        clearTimeout(timer)
        setTestStatus('error')
      }

      ws.onclose = () => {
        testWsRef.current = null
      }
    } catch {
      setTestStatus('error')
    }
  }

  const effectiveApiKey = store.getEffectiveApiKey()
  const envKeyAvailable = !!import.meta.env.VITE_API_KEY

  return (
    <>
      {/* 背景遮罩 */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm transition-opacity"
          onClick={onClose}
          role="presentation"
        />
      )}

      {/* 抽屉面板 */}
      <div
        className={`fixed top-2 right-2 bottom-2 z-50 w-[420px] transition-transform duration-300 ease-out ${
          open ? 'translate-x-0' : 'translate-x-[calc(100%+16px)]'
        }`}
      >
        <GlassPanel
          className="h-full flex flex-col overflow-hidden"
          radius="var(--laap-radius-lg)"
          intensity="lg"
          liquidGlass
        >
          {/* 头部 */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.08]">
            <div className="flex items-center gap-2">
              <SlidersHorizontal className="w-4 h-4 text-laap-accent" />
              <h2 className="text-sm font-medium text-white/90">设置</h2>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="no-drag p-1.5 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors"
              title="关闭"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* 设置表单 */}
          <div className="flex-1 min-h-0 overflow-y-auto p-5 space-y-6">
            {/* 后端连接 */}
            <section>
              <SectionTitle icon={Link} title="后端连接" />
              <div className="space-y-3">
                <Field label="WebSocket 地址">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={draft.backendUrl}
                      onChange={(e) =>
                        setDraft((prev) => ({ ...prev, backendUrl: e.target.value }))
                      }
                      className="flex-1 min-w-0 px-3 py-2 rounded-lg bg-black/20 border border-white/[0.08] text-xs text-white/90 placeholder:text-white/30 focus:outline-none focus:border-laap-accent/50"
                      placeholder="ws://127.0.0.1:8765"
                    />
                    <button
                      type="button"
                      onClick={handleTestConnection}
                      disabled={testStatus === 'testing'}
                      className="px-3 py-2 rounded-lg bg-white/[0.06] hover:bg-white/[0.10] border border-white/[0.08] text-xs text-white/80 transition-colors disabled:opacity-50 flex items-center gap-1.5"
                    >
                      {testStatus === 'testing' ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : testStatus === 'success' ? (
                        <Check className="w-3.5 h-3.5 text-laap-secondary" />
                      ) : testStatus === 'error' ? (
                        <AlertCircle className="w-3.5 h-3.5 text-red-400" />
                      ) : null}
                      测试连接
                    </button>
                  </div>
                  {testStatus === 'success' && (
                    <p className="text-[10px] text-laap-secondary mt-1.5">连接测试成功</p>
                  )}
                  {testStatus === 'error' && (
                    <p className="text-[10px] text-red-400 mt-1.5">无法连接到该地址，请检查后重试</p>
                  )}
                </Field>

                <Field label="API Key">
                  <input
                    type="password"
                    value={draft.useEnvApiKey ? effectiveApiKey : draft.apiKey}
                    onChange={(e) =>
                      setDraft((prev) => ({ ...prev, apiKey: e.target.value }))
                    }
                    disabled={draft.useEnvApiKey}
                    className="w-full px-3 py-2 rounded-lg bg-black/20 border border-white/[0.08] text-xs text-white/90 placeholder:text-white/30 focus:outline-none focus:border-laap-accent/50 disabled:opacity-50"
                    placeholder={draft.useEnvApiKey ? '使用环境变量中的 API Key' : '输入 API Key'}
                  />
                  <label className="flex items-center gap-2 mt-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={draft.useEnvApiKey}
                      onChange={(e) =>
                        setDraft((prev) => ({ ...prev, useEnvApiKey: e.target.checked }))
                      }
                      disabled={!envKeyAvailable}
                      className="rounded border-white/20 bg-black/20 text-laap-accent focus:ring-0"
                    />
                    <span className="text-[11px] text-white/60">
                      优先使用环境变量 {envKeyAvailable ? '' : '（未配置）'}
                    </span>
                  </label>
                </Field>
              </div>
            </section>

            {/* 全局热键 */}
            <section>
              <SectionTitle icon={Keyboard} title="全局热键（保存后立即生效）" />
              <div className="grid grid-cols-2 gap-3">
                <Field label="显示/隐藏窗口">
                  <input
                    type="text"
                    value={draft.hotkeys.showWindow}
                    onChange={(e) =>
                      setDraft((prev) => ({
                        ...prev,
                        hotkeys: { ...prev.hotkeys, showWindow: e.target.value },
                      }))
                    }
                    placeholder="CommandOrControl+Shift+L"
                    className="w-full px-3 py-2 rounded-lg bg-black/20 border border-white/[0.08] text-xs text-white/90 placeholder:text-white/30 focus:outline-none focus:border-laap-accent/50"
                  />
                  <p className="text-[10px] text-white/40 mt-1">
                    当前：{formatShortcut(draft.hotkeys.showWindow)}
                  </p>
                </Field>
                <Field label="按住说话 (PTT)">
                  <input
                    type="text"
                    value={draft.hotkeys.ptt}
                    onChange={(e) =>
                      setDraft((prev) => ({
                        ...prev,
                        hotkeys: { ...prev.hotkeys, ptt: e.target.value },
                      }))
                    }
                    placeholder="CommandOrControl+Shift+Space"
                    className="w-full px-3 py-2 rounded-lg bg-black/20 border border-white/[0.08] text-xs text-white/90 placeholder:text-white/30 focus:outline-none focus:border-laap-accent/50"
                  />
                  <p className="text-[10px] text-white/40 mt-1">
                    当前：{formatShortcut(draft.hotkeys.ptt)}
                  </p>
                </Field>
              </div>
            </section>

            {/* 语音输入 */}
            <section>
              <SectionTitle icon={Mic} title="语音输入" />
              <Field label="麦克风设备">
                <select
                  value={draft.audioInputDeviceId}
                  onChange={(e) =>
                    setDraft((prev) => ({ ...prev, audioInputDeviceId: e.target.value }))
                  }
                  className="w-full px-3 py-2 rounded-lg bg-black/20 border border-white/[0.08] text-xs text-white/90 focus:outline-none focus:border-laap-accent/50"
                >
                  <option value="">使用系统默认设备</option>
                  {devices.map((device) => (
                    <option key={device.deviceId} value={device.deviceId}>
                      {device.label}
                    </option>
                  ))}
                </select>
                {devices.length === 0 && (
                  <p className="text-[10px] text-white/40 mt-1.5">未检测到可用麦克风</p>
                )}
              </Field>

              <div className="mt-4 space-y-4">
                <Field label="启用唤醒词">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={draft.wakeWordEnabled}
                      onChange={(e) =>
                        setDraft((prev) => ({ ...prev, wakeWordEnabled: e.target.checked }))
                      }
                      className="rounded border-white/20 bg-black/20 text-laap-accent focus:ring-0"
                    />
                    <span className="text-[11px] text-white/60">开启后持续监听麦克风，说出唤醒词开始语音输入</span>
                  </label>
                </Field>

                <Field label="唤醒词短语">
                  <input
                    type="text"
                    value={draft.wakeWordPhrase}
                    onChange={(e) =>
                      setDraft((prev) => ({ ...prev, wakeWordPhrase: e.target.value }))
                    }
                    disabled={!draft.wakeWordEnabled}
                    className="w-full px-3 py-2 rounded-lg bg-black/20 border border-white/[0.08] text-xs text-white/90 placeholder:text-white/30 focus:outline-none focus:border-laap-accent/50 disabled:opacity-50"
                    placeholder="Hey LAAP"
                  />
                  <p className="text-[10px] text-white/40 mt-1">
                    当前实现为能量启发式检测，不会真正识别该短语内容。
                  </p>
                </Field>

                <Field label={`唤醒灵敏度：${draft.wakeWordSensitivity.toFixed(1)}`}>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.05}
                    value={draft.wakeWordSensitivity}
                    onChange={(e) =>
                      setDraft((prev) => ({
                        ...prev,
                        wakeWordSensitivity: Number(e.target.value),
                      }))
                    }
                    disabled={!draft.wakeWordEnabled}
                    className="w-full h-1 rounded-lg appearance-none bg-white/[0.12] accent-laap-accent cursor-pointer disabled:opacity-50"
                  />
                </Field>
              </div>
            </section>

            {/* 语音合成 */}
            <section>
              <SectionTitle icon={Volume2} title="语音合成 (TTS)" />
              <div className="space-y-4">
                <Field label="启用 TTS 播放">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={draft.ttsEnabled}
                      onChange={(e) =>
                        setDraft((prev) => ({ ...prev, ttsEnabled: e.target.checked }))
                      }
                      className="rounded border-white/20 bg-black/20 text-laap-accent focus:ring-0"
                    />
                    <span className="text-[11px] text-white/60">收到后端语音回复时自动播放音频</span>
                  </label>
                </Field>

                <Field label={`TTS 音量：${Math.round(draft.ttsVolume * 100)}%`}>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.05}
                    value={draft.ttsVolume}
                    onChange={(e) =>
                      setDraft((prev) => ({
                        ...prev,
                        ttsVolume: Number(e.target.value),
                      }))
                    }
                    disabled={!draft.ttsEnabled}
                    className="w-full h-1 rounded-lg appearance-none bg-white/[0.12] accent-laap-accent cursor-pointer disabled:opacity-50"
                  />
                </Field>
              </div>
            </section>

            {/* 外观 */}
            <section>
              <SectionTitle icon={SlidersHorizontal} title="外观" />
              <Field label="主题">
                <div className="flex gap-2">
                  {THEME_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => setDraft((prev) => ({ ...prev, theme: option.value }))}
                      className={`flex-1 px-3 py-2 rounded-lg border text-xs transition-colors flex items-center gap-2 ${
                        draft.theme === option.value
                          ? 'border-laap-accent/60 bg-laap-accent/10 text-white/90'
                          : 'border-white/[0.08] bg-black/20 text-white/60 hover:bg-white/[0.06]'
                      }`}
                    >
                      <span
                        className="w-3 h-3 rounded-full border border-white/20"
                        style={{ background: option.bg }}
                      />
                      {option.label}
                    </button>
                  ))}
                </div>
              </Field>

              <div className="mt-4 space-y-4">
                <Field label={`玻璃模糊：${draft.glassIntensity.blur}px`}>
                  <input
                    type="range"
                    min={4}
                    max={40}
                    step={1}
                    value={draft.glassIntensity.blur}
                    onChange={(e) => updateGlass({ blur: Number(e.target.value) })}
                    className="w-full h-1 rounded-lg appearance-none bg-white/[0.12] accent-laap-accent cursor-pointer"
                  />
                </Field>
                <Field label={`饱和度：${draft.glassIntensity.saturate.toFixed(1)}`}>
                  <input
                    type="range"
                    min={0.5}
                    max={3}
                    step={0.1}
                    value={draft.glassIntensity.saturate}
                    onChange={(e) => updateGlass({ saturate: Number(e.target.value) })}
                    className="w-full h-1 rounded-lg appearance-none bg-white/[0.12] accent-laap-accent cursor-pointer"
                  />
                </Field>
                <Field label={`亮度：${draft.glassIntensity.brightness.toFixed(2)}`}>
                  <input
                    type="range"
                    min={0.5}
                    max={2}
                    step={0.05}
                    value={draft.glassIntensity.brightness}
                    onChange={(e) => updateGlass({ brightness: Number(e.target.value) })}
                    className="w-full h-1 rounded-lg appearance-none bg-white/[0.12] accent-laap-accent cursor-pointer"
                  />
                </Field>
              </div>
            </section>

            {/* 本地视频 */}
            <section>
              <SectionTitle icon={Film} title="本地视频" />
              <Field label="默认视频路径">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={draft.videoPath}
                    onChange={(e) =>
                      setDraft((prev) => ({ ...prev, videoPath: e.target.value }))
                    }
                    className="flex-1 min-w-0 px-3 py-2 rounded-lg bg-black/20 border border-white/[0.08] text-xs text-white/90 placeholder:text-white/30 focus:outline-none focus:border-laap-accent/50"
                    placeholder="留空使用默认视频"
                  />
                  <button
                    type="button"
                    onClick={handleSelectVideo}
                    className="px-3 py-2 rounded-lg bg-white/[0.06] hover:bg-white/[0.10] border border-white/[0.08] text-xs text-white/80 transition-colors"
                  >
                    选择
                  </button>
                </div>
              </Field>
            </section>
          </div>

          {/* 底部操作栏 */}
          <div className="px-5 py-4 border-t border-white/[0.08] flex items-center justify-between gap-3">
            <button
              type="button"
              onClick={handleReset}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs text-white/60 hover:text-white/90 hover:bg-white/[0.06] transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              重置默认
            </button>
            <div className="flex items-center gap-2">
              <GlassButton
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-xs"
              >
                取消
              </GlassButton>
              <GlassButton
                type="button"
                onClick={handleSave}
                className="px-4 py-2 text-xs bg-laap-accent/20"
              >
                <Save className="w-3.5 h-3.5 mr-1.5" />
                保存
              </GlassButton>
            </div>
          </div>
        </GlassPanel>
      </div>
    </>
  )
}
