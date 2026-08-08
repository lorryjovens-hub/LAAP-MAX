import { useEffect, useState } from 'react'
import { TitleBar } from './components/shell/TitleBar'
import { WindowFrame } from './components/shell/WindowFrame'
import { LeftSidebar } from './components/shell/LeftSidebar'
import { ChatPanel } from './components/chat/ChatPanel'
import { ChatSidebar } from './components/chat/ChatSidebar'
import { ThoughtStream } from './components/chat/ThoughtStream'
import { InputBar } from './components/chat/InputBar'
import { SceneRenderer } from './components/scene/SceneRenderer'
import { TerminalPanel } from './components/terminal/TerminalPanel'
import { PSIBorder } from './components/shell/PSIBorder'
import { ThoughtFloat } from './components/shell/ThoughtFloat'

import './styles/consciousness.css'
import { SettingsPanel } from './components/settings/SettingsPanel'
import { OnboardingModal } from './components/onboarding/OnboardingModal'
import { useLaap } from './hooks/useLaap'
import { useVoice } from './hooks/useVoice'
import { useTtsAudio } from './hooks/useTtsAudio'
import { useMicrosoftTts } from './hooks/useMicrosoftTts'
import { useSettingsStore } from './store/settingsStore'
import { getCognitiveBus } from './store/laapStore'
import { StatusBar } from './components/hanako/HanakoLayout'
import { RightPanel } from './components/panels/RightPanel'
import type { TtsAudioSource } from './laap/types'

declare global {
  interface Window {
    setCloseToTray?: (enabled: boolean) => void
    onHotkeyWake?: (callback: () => void) => () => void
    setVoiceWakeEnabled?: (enabled: boolean) => void
    onVoiceWakeToggle?: (callback: (enabled: boolean) => void) => () => void
  }
}

function showDesktopOverlay(title: string, content: string): void {
  const desktop = (window as unknown as { desktop?: { showOverlay: (p: { title: string; content: string }) => void } }).desktop
  desktop?.showOverlay({ title, content })
}

function App() {
  const [inputText, setInputText] = useState('')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [activityOpen, setActivityOpen] = useState(true)
  const [settingsOpen, setSettingsOpen] = useState(false)

  const {
    connectionStatus, messages, psiCycle, vitalSigns,
    thoughts, currentToolCall, isStreaming, voice,
    sendUserMessage, reconnect, retryToolCall, confirmToolCall, rejectToolCall,
    setVoiceStatus, setVoiceAudioLevel, setVoiceContinuousListening,
    sendVoiceInput, clearVoiceTtsAudio,
    focusFrames, pendingToolConfirmations,
    sessions, activeSessionId, newSession, selectSession, deleteSession,
  } = useLaap()

  const {
    backendUrl, videoPath, glassIntensity, audioInputDeviceId,
    hotkeys, hasCompletedOnboarding, wakeWordEnabled, setWakeWordEnabled,
    wakeWordPhrase, wakeWordSensitivity, ttsEnabled, ttsVolume,
    tts,
  } = useSettingsStore()

  const { setVoiceTtsAudio } = useLaap()

  const isMicrosoftTts = tts.provider === 'microsoft'

  const { speak: microsoftSpeak } = useMicrosoftTts({
    enabled: isMicrosoftTts && ttsEnabled,
    subscriptionKey: tts.creds?.subscriptionKey ?? '',
    region: tts.baseUrl || 'eastasia',
    voice: tts.model || undefined,
    onTtsReady: (source: TtsAudioSource) => {
      setVoiceTtsAudio(source)
    },
  })

  const {
    status: voiceHookStatus, continuous, toggleContinuous,
    startListening, startPtt, stopPtt,
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

  useTtsAudio({
    source: voice.ttsAudio, enabled: ttsEnabled, volume: ttsVolume,
    isRecording: voiceHookStatus === 'listening',
    continuousListening: continuous,
    onStatusChange: setVoiceStatus,
    onEnded: clearVoiceTtsAudio,
  })

  useEffect(() => { reconnect(backendUrl) }, [backendUrl, reconnect])
  useEffect(() => { window.desktop?.registerHotkeys(hotkeys) }, [])

  useEffect(() => {
    const root = document.documentElement
    const stressBlur = glassIntensity.blur + (vitalSigns.stress ?? 0) * 6
    const pleasureSat = glassIntensity.saturate + (vitalSigns.pleasure ?? 0.5) * 0.3
    const arousalBright = glassIntensity.brightness + ((vitalSigns.arousal ?? 0.5) - 0.5) * 0.1
    root.style.setProperty('--laap-glass-blur', `${Math.min(stressBlur, 40)}px`)
    root.style.setProperty('--laap-glass-saturate', String(Math.min(pleasureSat, 2.5)))
    root.style.setProperty('--laap-glass-brightness', String(Math.min(Math.max(arousalBright, 0.8), 1.2)))
  }, [vitalSigns, glassIntensity])

  useEffect(() => {
    const root = document.documentElement
    root.classList.remove('psi-phase-perception', 'psi-phase-selection', 'psi-phase-integration', 'psi-phase-learning')
    root.classList.add(`psi-phase-${psiCycle.phase}`)
  }, [psiCycle.phase])

  useEffect(() => {
    const root = document.documentElement
    root.style.setProperty('--bg-breathe-opacity', '0.03')
  }, [])

  useEffect(() => {
    const desktop = (window as unknown as { desktop?: { onPttPressed: (cb: () => void) => void } }).desktop
    if (!desktop?.onPttPressed) return
    let pttActive = false
    desktop.onPttPressed(() => {
      if (pttActive) { void stopPtt(); pttActive = false }
      else { void startPtt(); pttActive = true }
    })
  }, [startPtt, stopPtt])

  useEffect(() => {
    window.setVoiceWakeEnabled?.(wakeWordEnabled)
  }, [wakeWordEnabled])

  // 当 voice.lastRecognizedText 更新且 TTS 为 microsoft 模式时，触发前端合成
  useEffect(() => {
    if (!isMicrosoftTts || !ttsEnabled) return
    const text = voice.lastRecognizedText
    if (!text) return
    void microsoftSpeak(text)
  }, [isMicrosoftTts, ttsEnabled, voice.lastRecognizedText, microsoftSpeak])

  useEffect(() => {
    const unsubscribe = window.onVoiceWakeToggle?.((enabled) => {
      setWakeWordEnabled(enabled)
    })
    return () => unsubscribe?.()
  }, [setWakeWordEnabled])

  useEffect(() => {
    const unsubscribe = window.onHotkeyWake?.(() => {
      void startListening()
    })
    return () => unsubscribe?.()
  }, [startListening])

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

  const perceptionHealth = vitalSigns.pleasure ?? 0.5
  const activeFocus = focusFrames.find(f => f.active)?.intent ?? null

  return (
    <div className="h-screen w-screen p-2 overflow-hidden bg-transparent">
      <PSIBorder phase={psiCycle.phase} stress={vitalSigns.stress} />

      <WindowFrame
        titleBar={
          <TitleBar
            sidebarCollapsed={sidebarCollapsed}
            onSidebarToggle={() => setSidebarCollapsed((v) => !v)}
            onSettingsClick={() => setSettingsOpen(true)}
          />
        }
        bottomBar={
          <StatusBar
            connectionStatus={connectionStatus}
            perceptionHealth={perceptionHealth}
            activeFocus={activeFocus}
            isStreaming={isStreaming}
            theme="dark"
          />
        }
      >
        <div className="h-full w-full flex gap-3 p-3">
          {/* 会话侧边栏（Hanako 风格） */}
          <ChatSidebar
            sessions={sessions}
            activeSessionId={activeSessionId}
            collapsed={sidebarCollapsed}
            onNewSession={newSession}
            onSelectSession={selectSession}
            onDeleteSession={deleteSession}
            onToggleCollapse={() => setSidebarCollapsed((v) => !v)}
            onOpenSettings={() => setSettingsOpen(true)}
            onToggleRightPanel={() => setActivityOpen((v) => !v)}
          />

          {/* Left sidebar */}
          <LeftSidebar
            collapsed={sidebarCollapsed}
            psiCycle={psiCycle}
            vitalSigns={vitalSigns}
            videoSrc={videoPath}
          />

          {/* Center: Chat + Thoughts + Scene + Terminal */}
          <div className="flex-1 min-w-0 flex flex-col gap-3">
            <div className="flex-1 min-h-0 flex flex-col gap-3 overflow-hidden">
              <div className="flex-1 min-h-0 flex gap-3 overflow-hidden">
                <ChatPanel
                  messages={messages}
                  isStreaming={isStreaming}
                  currentToolCall={currentToolCall}
                  onRetryToolCall={retryToolCall}
                  onConfirmToolCall={confirmToolCall}
                  onRejectToolCall={rejectToolCall}
                  pendingConfirmations={pendingToolConfirmations}
                  className="flex-[2] min-w-0"
                />
                <div className="w-64 shrink-0 flex flex-col gap-3">
                  <ThoughtStream thoughts={thoughts} className="flex-1 min-h-0" />
                  <SceneRenderer className="h-1/2 min-h-0" />
                </div>
              </div>
              <TerminalPanel />
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

          {/* Right activity panel - Hanako inspired */}
          {activityOpen && (
            <RightPanel
              onClose={() => setActivityOpen(false)}
              sessionStats={{ tokens: 0, cost: 0, messages: messages.length }}
            />
          )}
          {!activityOpen && (
            <button
              onClick={() => setActivityOpen(true)}
              className="fixed right-4 top-1/2 -translate-y-1/2 z-50 w-8 h-8 rounded-full bg-white/[0.06] border border-white/[0.1] flex items-center justify-center text-white/50 hover:text-white/80 hover:bg-white/[0.1] transition-all cursor-pointer"
              title="Show activity panel"
            >
              ◀
            </button>
          )}
        </div>
      </WindowFrame>

      <ThoughtFloat
        thoughts={thoughts}
        dismissAfterMs={8000}
        onDismiss={() => {}}
      />

      <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      {!hasCompletedOnboarding && <OnboardingModal />}
    </div>
  )
}

export default App
