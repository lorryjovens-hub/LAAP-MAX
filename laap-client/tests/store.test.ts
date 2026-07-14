/**
 * Zustand Store 单元测试
 *
 * 验证 laapStore 与 settingsStore 的状态更新、持久化与默认值行为。
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { useLaapStore, getCognitiveBus } from '../src/store/laapStore'
import { useSettingsStore } from '../src/store/settingsStore'
import type { AetherMessage } from '../src/laap/types'

function dispatchBusMessage(topic: string, payload: unknown): void {
  const bus = getCognitiveBus()
  const boundDispatch = (bus as unknown as { dispatch?: (msg: AetherMessage) => void }).dispatch?.bind(bus)
  if (typeof boundDispatch !== 'function') {
    throw new Error('CognitiveBus dispatch 方法不可访问')
  }
  boundDispatch({
    id: `test-${topic}`,
    type: 'event',
    topic,
    payload,
    timestamp: Date.now(),
    sender: 'test',
  })
}

describe('laapStore', () => {
  beforeEach(() => {
    useLaapStore.setState({
      vitalSigns: {
        curiosity: 0.5,
        trust: 0.5,
        competence: 0.5,
        pleasure: 0.5,
        arousal: 0.5,
        dominance: 0.5,
        sociality: 0.5,
        stress: 0.2,
      },
    })
  })

  it('updateVitalSigns 更新单个指标', () => {
    useLaapStore.getState().updateVitalSigns({ curiosity: 0.9 })
    expect(useLaapStore.getState().vitalSigns.curiosity).toBe(0.9)
  })

  it('clearError 清空错误信息', () => {
    useLaapStore.setState({ error: '网络异常' })
    useLaapStore.getState().clearError()
    expect(useLaapStore.getState().error).toBeNull()
  })

  it('sendUserMessage 添加用户消息', () => {
    useLaapStore.getState().sendUserMessage('hello')
    const messages = useLaapStore.getState().messages
    expect(messages.length).toBe(1)
    expect(messages[0].role).toBe('user')
    expect(messages[0].content).toBe('hello')
  })

  it('voice.tts 携带音频时设置 voice.ttsAudio', () => {
    useLaapStore.setState({ voice: { ...useLaapStore.getState().voice, ttsAudio: null } })
    dispatchBusMessage('voice.tts', { audioBase64: 'AAAA', text: 'hello' })
    expect(useLaapStore.getState().voice.ttsAudio).toEqual({
      audioBase64: 'AAAA',
      audioUrl: undefined,
      mimeType: undefined,
    })
  })

  it('voice.tts 无音频时不设置 ttsAudio', () => {
    useLaapStore.setState({ voice: { ...useLaapStore.getState().voice, ttsAudio: null } })
    dispatchBusMessage('voice.tts', { text: 'hello', speaking: true })
    expect(useLaapStore.getState().voice.ttsAudio).toBeNull()
  })

  it('audio.stream 携带音频时设置 voice.ttsAudio', () => {
    useLaapStore.setState({ voice: { ...useLaapStore.getState().voice, ttsAudio: null } })
    dispatchBusMessage('audio.stream', { audioUrl: 'http://example.com/tts.mp3' })
    expect(useLaapStore.getState().voice.ttsAudio).toEqual({
      audioBase64: undefined,
      audioUrl: 'http://example.com/tts.mp3',
      mimeType: undefined,
    })
  })

  it('clearVoiceTtsAudio 清空 TTS 音频', () => {
    useLaapStore.setState({
      voice: { ...useLaapStore.getState().voice, ttsAudio: { audioBase64: 'AAAA' } },
    })
    useLaapStore.getState().clearVoiceTtsAudio()
    expect(useLaapStore.getState().voice.ttsAudio).toBeNull()
    expect(useLaapStore.getState().voice.isSpeaking).toBe(false)
  })

  it('setVoiceStatus 同步更新 isSpeaking', () => {
    useLaapStore.getState().setVoiceStatus('speaking')
    expect(useLaapStore.getState().voice.status).toBe('speaking')
    expect(useLaapStore.getState().voice.isSpeaking).toBe(true)

    useLaapStore.getState().setVoiceStatus('idle')
    expect(useLaapStore.getState().voice.status).toBe('idle')
    expect(useLaapStore.getState().voice.isSpeaking).toBe(false)
  })
})

describe('settingsStore', () => {
  beforeEach(() => {
    useSettingsStore.getState().resetToDefaults()
  })

  it('默认后端地址正确', () => {
    expect(useSettingsStore.getState().backendUrl).toBe('ws://127.0.0.1:8765')
  })

  it('默认唤醒词设置正确', () => {
    const state = useSettingsStore.getState()
    expect(state.wakeWordEnabled).toBe(true)
    expect(state.wakeWordPhrase).toBe('Hey LAAP')
    expect(state.wakeWordSensitivity).toBe(0.5)
  })

  it('默认 TTS 设置正确', () => {
    const state = useSettingsStore.getState()
    expect(state.ttsEnabled).toBe(true)
    expect(state.ttsVolume).toBe(1)
  })

  it('setWakeWordEnabled 切换唤醒词开关', () => {
    useSettingsStore.getState().setWakeWordEnabled(false)
    expect(useSettingsStore.getState().wakeWordEnabled).toBe(false)
  })

  it('setWakeWordPhrase 更新唤醒词短语', () => {
    useSettingsStore.getState().setWakeWordPhrase('Hello LAAP')
    expect(useSettingsStore.getState().wakeWordPhrase).toBe('Hello LAAP')
  })

  it('setWakeWordSensitivity 将灵敏度限制在 0-1', () => {
    useSettingsStore.getState().setWakeWordSensitivity(1.5)
    expect(useSettingsStore.getState().wakeWordSensitivity).toBe(1)
    useSettingsStore.getState().setWakeWordSensitivity(-0.5)
    expect(useSettingsStore.getState().wakeWordSensitivity).toBe(0)
  })

  it('setTtsEnabled 切换 TTS 开关', () => {
    useSettingsStore.getState().setTtsEnabled(false)
    expect(useSettingsStore.getState().ttsEnabled).toBe(false)
    useSettingsStore.getState().setTtsEnabled(true)
    expect(useSettingsStore.getState().ttsEnabled).toBe(true)
  })

  it('setTtsVolume 将音量限制在 0-1', () => {
    useSettingsStore.getState().setTtsVolume(1.5)
    expect(useSettingsStore.getState().ttsVolume).toBe(1)
    useSettingsStore.getState().setTtsVolume(-0.5)
    expect(useSettingsStore.getState().ttsVolume).toBe(0)
    useSettingsStore.getState().setTtsVolume(0.6)
    expect(useSettingsStore.getState().ttsVolume).toBe(0.6)
  })

  it('setBackendUrl 更新后端地址并持久化', () => {
    useSettingsStore.getState().setBackendUrl('ws://test.example.com:8765')
    expect(useSettingsStore.getState().backendUrl).toBe('ws://test.example.com:8765')

    const raw = window.localStorage.getItem('laap-client-settings')
    expect(raw).toBeTruthy()
    const parsed = JSON.parse(raw!)
    expect(parsed.state.backendUrl).toBe('ws://test.example.com:8765')
  })

  it('completeOnboarding 标记引导完成', () => {
    useSettingsStore.getState().completeOnboarding()
    expect(useSettingsStore.getState().hasCompletedOnboarding).toBe(true)
  })

  it('resetToDefaults 保留 onboarding 状态', () => {
    useSettingsStore.getState().completeOnboarding()
    useSettingsStore.getState().setBackendUrl('ws://other')
    useSettingsStore.getState().resetToDefaults()

    expect(useSettingsStore.getState().hasCompletedOnboarding).toBe(true)
    expect(useSettingsStore.getState().backendUrl).toBe('ws://127.0.0.1:8765')
  })
})
