import { useEffect, useRef, useState } from 'react'
import { LiquidGlass } from './components/glass/LiquidGlass'
import { TitleBar } from './components/shell/TitleBar'
import { WindowFrame } from './components/shell/WindowFrame'
import { LeftSidebar } from './components/shell/LeftSidebar'
import { ChatPanel } from './components/chat/ChatPanel'
import { ThoughtStream } from './components/chat/ThoughtStream'
import { InputBar } from './components/chat/InputBar'
import { SceneRenderer } from './components/scene/SceneRenderer'
import { RateBufferPanel } from './components/panels/RateBufferPanel'
import { ColonyPanel } from './components/panels/ColonyPanel'
import { VoiceOrb } from './components/voice/VoiceOrb'
import { WaveformVisualizer } from './components/voice/WaveformVisualizer'
import { SettingsPanel } from './components/settings/SettingsPanel'
import { OnboardingModal } from './components/onboarding/OnboardingModal'
import { useLaap } from './hooks/useLaap'
import { useVoice } from './hooks/useVoice'
import { useTtsAudio } from './hooks/useTtsAudio'
import { useSettingsStore, type ThemeMode } from './store/settingsStore'
import { getCognitiveBus } from './store/laapStore'

/**
 * 获取连接状态对应的中文标签与样式类
 */
function getConnectionLabel(status: string): { text: string; className: string } {
  switch (status) {
    case 'open':
      return { text: '[OK] CognitiveBus 已连接', className: 'laap-status-ok' }
    case 'connecting':
      return { text: '[INFO] 正在连接 CognitiveBus...', className: 'laap-status-info' }
    case 'error':
      return { text: '[ERROR] 连接异常', className: 'laap-status-error' }
    case 'closed':
      return { text: '[INFO] 连接已关闭', className: 'laap-status-info' }
    default:
      return { text: '[INFO] 未知状态', className: 'laap-status-info' }
  }
}

/**
 * 安全触发桌面悬浮通知
 */
function showDesktopOverlay(title: string, content: string): void {
  const desktop = (window as unknown as { desktop?: { showOverlay: (payload: { title: string; content: string }) => void } }).desktop
  desktop?.showOverlay({ title, content })
}

/** 主题到主背景色的映射 */
const THEME_BG: Record<ThemeMode, string> = {
  dark: '#050608',
  midnight: '#0a0f1c',
  obsidian: '#100818',
}

function App() {
  const titleBarRef = useRef<HTMLDivElement>(null)
  const [inputText, setInputText] = useState('')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [activeRightPanel, setActiveRightPanel] = useState<'rate' | 'colony'>('colony')
  const [settingsOpen, setSettingsOpen] = useState(false)

  const {
    connectionStatus,
    messages,
    psiCycle,
    vitalSigns,
    rateBuffer,
    colony,
    thoughts,
    currentToolCall,
    isStreaming,
    error,
    voice,
    sendUserMessage,
    reconnect,
    retryToolCall,
    clearError,
    setVoiceStatus,
    setVoiceAudioLevel,
    setVoiceContinuousListening,
    sendVoiceInput,
    clearVoiceTtsAudio,
  } = useLaap()

  const {
    backendUrl,
    videoPath,
    glassIntensity,
    theme,
    audioInputDeviceId,
    hotkeys,
    hasCompletedOnboarding,
    wakeWordEnabled,
    wakeWordPhrase,
    wakeWordSensitivity,
    ttsEnabled,
    ttsVolume,
  } = useSettingsStore()

  const {
    status: voiceHookStatus,
    continuous,
    toggleContinuous,
    startPtt,
    stopPtt,
  } = useVoice({
    onAudioLevel: setVoiceAudioLevel,
    onStatusChange: setVoiceStatus,
    onSendVoice: sendVoiceInput,
    deviceId: audioInputDeviceId,
    wakeWordEnabled,
    wakeWordPhrase,
    wakeWordSensitivity,
    busClient: getCognitiveBus(),
  })

  const { analyserRef } = useTtsAudio({
    source: voice.ttsAudio,
    enabled: ttsEnabled,
    volume: ttsVolume,
    isRecording: voiceHookStatus === 'listening',
    continuousListening: continuous,
    onStatusChange: setVoiceStatus,
    onEnded: clearVoiceTtsAudio,
  })

  // 应用启动/后端地址变化时自动重连 CognitiveBus
  useEffect(() => {
    reconnect(backendUrl)
  }, [backendUrl, reconnect])

  // 应用启动时将 persisted 热键配置同步到 Electron 主进程
  useEffect(() => {
    window.desktop?.registerHotkeys(hotkeys)
  }, [])

  // 将玻璃强度、主题等设置应用到 CSS 变量与全局背景
  useEffect(() => {
    const root = document.documentElement
    root.style.setProperty('--laap-glass-blur', `${glassIntensity.blur}px`)
    root.style.setProperty('--laap-glass-saturate', String(glassIntensity.saturate))
    root.style.setProperty('--laap-glass-brightness', String(glassIntensity.brightness))
    root.style.setProperty('--laap-bg-primary', THEME_BG[theme])
    document.body.style.background = THEME_BG[theme]
  }, [glassIntensity, theme])

  // 监听全局 PTT 热键：按一次开始，再按一次停止（Electron globalShortcut 无 keyup 事件）
  useEffect(() => {
    const desktop = (window as unknown as { desktop?: { onPttPressed: (callback: () => void) => void } }).desktop
    if (!desktop?.onPttPressed) return

    let pttActive = false
    const unsubscribe = () => {
      // ipcRenderer 监听无法直接移除匿名函数，这里仅做占位
    }

    desktop.onPttPressed(() => {
      if (pttActive) {
        void stopPtt()
        pttActive = false
      } else {
        void startPtt()
        pttActive = true
      }
    })

    return unsubscribe
  }, [startPtt, stopPtt])

  // 新 thought 触发桌面悬浮通知
  useEffect(() => {
    const latest = thoughts[thoughts.length - 1]
    if (!latest) return
    showDesktopOverlay('LAAP Thought', latest.content.slice(0, 120))
  }, [thoughts])

  const handleSend = () => {
    const trimmed = inputText.trim()
    if (!trimmed) return
    sendUserMessage(trimmed)
    setInputText('')
  }

  const handleVoiceToggle = (active: boolean) => {
    setVoiceContinuousListening(active)
    toggleContinuous()
  }

  const status = getConnectionLabel(connectionStatus)

  return (
    <div className="h-screen w-screen p-2 overflow-hidden bg-transparent">
      {/* 液态玻璃滤镜定义，观察标题栏尺寸 */}
      <LiquidGlass targetRef={titleBarRef} />

      <WindowFrame
        titleBar={
          <TitleBar
            targetRef={titleBarRef}
            sidebarCollapsed={sidebarCollapsed}
            onSidebarToggle={() => setSidebarCollapsed((v) => !v)}
            onSettingsClick={() => setSettingsOpen(true)}
          />
        }
        bottomBar={
          <div className="flex items-center justify-between w-full text-xs text-white/40">
            <div className="flex items-center gap-4">
              <span className={status.className}>{status.text}</span>
              {error && (
                <button
                  type="button"
                  className="laap-status-error hover:underline"
                  onClick={clearError}
                  title="点击清除错误"
                >
                  {error}
                </button>
              )}
            </div>
            <div className="flex items-center gap-4">
              <WaveformVisualizer active={voice.isSpeaking} audioLevel={voice.audioLevel} className="w-32" analyserRef={analyserRef} />
              <VoiceOrb status={voice.status} audioLevel={voice.audioLevel} size={28} />
              <div className="font-mono text-white/50">
                PSI {psiCycle.phase} {Math.round(psiCycle.progress * 100)}%
              </div>
            </div>
          </div>
        }
      >
        <div className="h-full w-full flex gap-3 p-3">
          {/* 左侧边栏：视频 + 生命体征 */}
          <LeftSidebar
            collapsed={sidebarCollapsed}
            psiCycle={psiCycle}
            vitalSigns={vitalSigns}
            videoSrc={videoPath}
          />

          {/* 中间主交互区：聊天 + 思考流 + Scene 渲染 */}
          <div className="flex-1 min-w-0 flex flex-col gap-3">
            <div className="flex-1 min-h-0 flex gap-3 overflow-hidden">
              <ChatPanel
                messages={messages}
                isStreaming={isStreaming}
                currentToolCall={currentToolCall}
                onRetryToolCall={retryToolCall}
                className="flex-[2] min-w-0"
              />

              <div className="w-64 shrink-0 flex flex-col gap-3">
                <ThoughtStream thoughts={thoughts} className="flex-1 min-h-0" />
                <SceneRenderer className="h-1/2 min-h-0" />
              </div>
            </div>

            <InputBar
              value={inputText}
              onChange={setInputText}
              onSend={handleSend}
              onVoiceToggle={handleVoiceToggle}
              connectionStatus={connectionStatus}
              psiCycle={psiCycle}
              disabled={connectionStatus !== 'open'}
              voiceActive={continuous}
            />
          </div>

          {/* 右侧面板：RateBuffer / Colony 标签切换 */}
          <div className="hidden xl:flex w-[280px] shrink-0 flex-col gap-3">
            <div className="flex items-center gap-1 p-1 rounded-lg bg-white/[0.04] border border-white/[0.08]">
              <button
                type="button"
                onClick={() => setActiveRightPanel('rate')}
                className={`flex-1 text-xs py-1 rounded-md transition-colors ${
                  activeRightPanel === 'rate'
                    ? 'bg-white/[0.10] text-white/90'
                    : 'text-white/50 hover:text-white/70'
                }`}
              >
                RateBuffer
              </button>
              <button
                type="button"
                onClick={() => setActiveRightPanel('colony')}
                className={`flex-1 text-xs py-1 rounded-md transition-colors ${
                  activeRightPanel === 'colony'
                    ? 'bg-white/[0.10] text-white/90'
                    : 'text-white/50 hover:text-white/70'
                }`}
              >
                Colony
              </button>
            </div>

            {activeRightPanel === 'rate' && <RateBufferPanel stats={rateBuffer} className="flex-1 min-h-0" />}
            {activeRightPanel === 'colony' && <ColonyPanel colony={colony} className="flex-1 min-h-0" />}
          </div>
        </div>
      </WindowFrame>

      {/* 设置抽屉 */}
      <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} />

      {/* 首次启动引导 */}
      {!hasCompletedOnboarding && <OnboardingModal />}
    </div>
  )
}

export default App
