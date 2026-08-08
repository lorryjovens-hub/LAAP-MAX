/**
 * useVoice Hook
 *
 * 封装 Web Audio API 麦克风输入、MediaRecorder 录音、PTT（按住说话）、
 * 连续监听模式以及本地唤醒词检测。
 *
 * 唤醒词使用轻量级能量启发式：当输入音频 RMS 超过灵敏度阈值并持续一段短语长度时，
 * 触发一次性 ASR 录音并通过 onSendVoice 发送给后端。同时支持后端通过 CognitiveBus
 * 发送 voice.wake 事件来触发录音。
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import type { CognitiveBusClient } from '../laap/bus'
import type { VoiceStatus } from '../laap/types'

declare global {
  interface Window {
    electron?: {
      showWindow?: () => void
      send?: (channel: string, ...args: unknown[]) => void
    }
  }
}

export interface UseVoiceOptions {
  onAudioLevel?: (level: number) => void
  onStatusChange?: (status: VoiceStatus) => void
  onSendVoice?: (base64Audio: string, mimeType: string) => void
  /** 指定音频输入设备 ID，空字符串表示使用默认设备 */
  deviceId?: string
  /** 是否启用本地唤醒词监听（默认 false） */
  wakeWordEnabled?: boolean
  /** 唤醒词短语，仅用于日志与设置展示 */
  wakeWordPhrase?: string
  /** 唤醒词灵敏度 0-1（默认 0.5） */
  wakeWordSensitivity?: number
  /** CognitiveBus 客户端，用于后端 voice.wake 事件 */
  busClient?: CognitiveBusClient
}

export interface UseVoiceReturn {
  status: VoiceStatus
  audioLevel: number
  continuous: boolean
  isSupported: boolean
  permissionError: string | null
  startListening: () => Promise<void>
  stopListening: () => void
  toggleContinuous: () => void
  startPtt: () => Promise<void>
  stopPtt: () => void
}

/** 唤醒词检测帧间隔（毫秒） */
const WAKE_FRAME_MS = 50
/** 唤醒词短语窗口（毫秒） */
const PHRASE_WINDOW_MS = 1200
/** 窗口内需达到的能量活跃比例 */
const WINDOW_ACTIVE_RATIO = 0.25
/** 连续活跃帧数阈值 */
const CONSECUTIVE_FRAMES = 5
/** 触发冷却（毫秒） */
const WAKE_COOLDOWN_MS = 2000
/** 一次性录音最大时长（毫秒） */
const MAX_UTTERANCE_MS = 8000
/** 录音静音停止超时（毫秒） */
const SILENCE_TIMEOUT_MS = 1200
/** 静音检测帧间隔（毫秒） */
const SILENCE_CHECK_MS = 100

/** 录音模式 */
type RecordingMode = 'ptt' | 'continuous' | 'wake'

/**
 * 检测浏览器是否支持所需 API
 */
function checkSupport(): boolean {
  return (
    typeof navigator !== 'undefined' &&
    typeof navigator.mediaDevices !== 'undefined' &&
    typeof MediaRecorder !== 'undefined' &&
    typeof AudioContext !== 'undefined'
  )
}

/**
 * 将灵敏度映射为能量阈值。
 * sensitivity 越高阈值越低，越容易触发；范围 [0, 1]。
 */
export function sensitivityToThreshold(sensitivity: number): number {
  const clamped = Math.min(1, Math.max(0, sensitivity))
  return 0.15 - clamped * 0.14
}

/**
 * 从 AnalyserNode 的时域数据中计算 RMS（均方根）。
 */
export function computeRms(timeData: Uint8Array): number {
  let sum = 0
  for (let i = 0; i < timeData.length; i += 1) {
    const normalized = (timeData[i] - 128) / 128
    sum += normalized * normalized
  }
  return Math.sqrt(sum / timeData.length)
}

export function useVoice(options: UseVoiceOptions = {}): UseVoiceReturn {
  const {
    onAudioLevel,
    onStatusChange,
    onSendVoice,
    deviceId = '',
    wakeWordEnabled = false,
    wakeWordPhrase = 'Hey LAAP',
    wakeWordSensitivity = 0.5,
    busClient,
  } = options

  const [status, setStatus] = useState<VoiceStatus>('idle')
  const [audioLevel, setAudioLevel] = useState(0)
  const [continuous, setContinuous] = useState(false)
  const [permissionError, setPermissionError] = useState<string | null>(null)
  const [isSupported] = useState(() => checkSupport())

  const streamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const recorderMimeTypeRef = useRef('audio/webm')
  const rafRef = useRef<number | null>(null)
  const wakeIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const oneShotTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const silenceIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const pttActiveRef = useRef(false)
  const statusRef = useRef(status)
  const continuousRef = useRef(continuous)
  const wakeWordEnabledRef = useRef(wakeWordEnabled)
  const wakeWordSensitivityRef = useRef(wakeWordSensitivity)
  const wakeWordPhraseRef = useRef(wakeWordPhrase)
  const recordingModeRef = useRef<RecordingMode | null>(null)
  const lastWakeAtRef = useRef(0)
  const consecutiveActiveRef = useRef(0)
  const wakeHistoryRef = useRef<Array<{ active: boolean; time: number }>>([])

  statusRef.current = status
  continuousRef.current = continuous
  wakeWordEnabledRef.current = wakeWordEnabled
  wakeWordSensitivityRef.current = wakeWordSensitivity
  wakeWordPhraseRef.current = wakeWordPhrase

  const updateStatus = useCallback(
    (next: VoiceStatus) => {
      setStatus(next)
      onStatusChange?.(next)
    },
    [onStatusChange],
  )

  const updateAudioLevel = useCallback(
    (level: number) => {
      const clamped = Math.min(1, Math.max(0, level))
      setAudioLevel(clamped)
      onAudioLevel?.(clamped)
    },
    [onAudioLevel],
  )

  const clearOneShotTimers = useCallback(() => {
    if (oneShotTimeoutRef.current) {
      clearTimeout(oneShotTimeoutRef.current)
      oneShotTimeoutRef.current = null
    }
    if (silenceIntervalRef.current) {
      clearInterval(silenceIntervalRef.current)
      silenceIntervalRef.current = null
    }
  }, [])

  const stopAudioMonitor = useCallback(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current)
      rafRef.current = null
    }
  }, [])

  const stopWakeDetection = useCallback(() => {
    if (wakeIntervalRef.current) {
      clearInterval(wakeIntervalRef.current)
      wakeIntervalRef.current = null
    }
    consecutiveActiveRef.current = 0
    wakeHistoryRef.current = []
  }, [])

  const releaseStream = useCallback(() => {
    stopAudioMonitor()
    stopWakeDetection()
    clearOneShotTimers()
    if (analyserRef.current) {
      try {
        analyserRef.current.disconnect()
      } catch {
        // 忽略已断开的情况
      }
      analyserRef.current = null
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      void audioContextRef.current.close()
      audioContextRef.current = null
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
  }, [stopAudioMonitor, stopWakeDetection, clearOneShotTimers])

  const maybeReleaseStream = useCallback(() => {
    if (
      !continuousRef.current &&
      !wakeWordEnabledRef.current &&
      !recorderRef.current &&
      !pttActiveRef.current
    ) {
      releaseStream()
    }
  }, [releaseStream])

  const ensureStream = useCallback(async () => {
    if (streamRef.current) return streamRef.current
    if (!isSupported) {
      throw new Error('当前环境不支持麦克风或录音 API')
    }

    const audioConstraints = deviceId ? { deviceId: { exact: deviceId } } : true
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: audioConstraints })
      streamRef.current = stream
      setPermissionError(null)
      return stream
    } catch (err) {
      const message = err instanceof Error ? err.message : '无法访问麦克风'
      setPermissionError(message)
      console.warn(`[WARN] 麦克风权限获取失败：${message}`)
      throw err
    }
  }, [deviceId, isSupported])

  const ensureAudioContext = useCallback(async () => {
    if (analyserRef.current) return analyserRef.current
    const stream = await ensureStream()
    const ctx = new AudioContext()
    audioContextRef.current = ctx
    const source = ctx.createMediaStreamSource(stream)
    const analyser = ctx.createAnalyser()
    analyser.fftSize = 2048
    source.connect(analyser)
    analyserRef.current = analyser
    return analyser
  }, [ensureStream])

  const startAudioMonitor = useCallback(async () => {
    const analyser = await ensureAudioContext()
    if (rafRef.current) return

    const data = new Uint8Array(analyser.frequencyBinCount)
    const loop = () => {
      if (!analyserRef.current || !rafRef.current) return
      analyser.getByteFrequencyData(data)
      let sum = 0
      for (let i = 0; i < data.length; i += 1) {
        sum += data[i]
      }
      const avg = sum / data.length / 255
      updateAudioLevel(avg)
      rafRef.current = requestAnimationFrame(loop)
    }
    rafRef.current = requestAnimationFrame(loop)
  }, [ensureAudioContext, updateAudioLevel])

  const startRecording = useCallback(async () => {
    if (!isSupported) {
      setPermissionError('当前环境不支持麦克风或录音 API')
      return
    }
    if (recorderRef.current) return

    try {
      await ensureStream()
      await startAudioMonitor()

      const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4'
      recorderMimeTypeRef.current = mimeType
      const recorder = new MediaRecorder(streamRef.current!, { mimeType })
      recorderRef.current = recorder
      chunksRef.current = []

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      recorder.onstop = () => {
        clearOneShotTimers()
        const blob = new Blob(chunksRef.current, { type: recorderMimeTypeRef.current })
        chunksRef.current = []
        const reader = new FileReader()
        reader.onloadend = () => {
          const base64 = String(reader.result).split(',')[1] ?? ''
          if (base64) {
            onSendVoice?.(base64, recorderMimeTypeRef.current)
          }
        }
        reader.readAsDataURL(blob)
        updateAudioLevel(0)

        if (recordingModeRef.current === 'continuous') {
          updateStatus('idle')
        } else {
          updateStatus('thinking')
        }
        recordingModeRef.current = null
        pttActiveRef.current = false
        maybeReleaseStream()
      }

      recorder.start(100)
      updateStatus('listening')
    } catch (err) {
      setPermissionError(err instanceof Error ? err.message : '无法访问麦克风')
      recordingModeRef.current = null
      pttActiveRef.current = false
      updateStatus('idle')
      maybeReleaseStream()
    }
  }, [
    isSupported,
    ensureStream,
    startAudioMonitor,
    updateAudioLevel,
    updateStatus,
    onSendVoice,
    clearOneShotTimers,
    maybeReleaseStream,
  ])

  const stopRecording = useCallback(() => {
    if (!recorderRef.current) return
    recorderRef.current.stop()
    recorderRef.current = null
    updateAudioLevel(0)
  }, [updateAudioLevel])

  const startWakeRecording = useCallback(async () => {
    if (recorderRef.current || statusRef.current !== 'idle') return
    recordingModeRef.current = 'wake'
    await startRecording()

    oneShotTimeoutRef.current = setTimeout(() => {
      stopRecording()
    }, MAX_UTTERANCE_MS)

    const analyser = analyserRef.current
    if (!analyser) return
    const silenceThreshold = sensitivityToThreshold(wakeWordSensitivityRef.current) * 0.8
    const timeData = new Uint8Array(analyser.fftSize)
    let silentFrames = 0

    silenceIntervalRef.current = setInterval(() => {
      if (!recorderRef.current) {
        clearOneShotTimers()
        return
      }
      analyser.getByteTimeDomainData(timeData)
      const rms = computeRms(timeData)
      if (rms < silenceThreshold) {
        silentFrames += 1
        if (silentFrames * SILENCE_CHECK_MS >= SILENCE_TIMEOUT_MS) {
          clearOneShotTimers()
          stopRecording()
        }
      } else {
        silentFrames = 0
      }
    }, SILENCE_CHECK_MS)
  }, [startRecording, stopRecording, clearOneShotTimers])

  const startWakeDetection = useCallback(async () => {
    if (!isSupported) {
      console.warn('[WARN] 当前环境不支持唤醒词检测')
      return
    }
    if (wakeIntervalRef.current) return

    try {
      await startAudioMonitor()
    } catch (err) {
      console.warn('[WARN] 无法启动音频监听：', err)
      return
    }

    const analyser = analyserRef.current
    if (!analyser) return

    const timeData = new Uint8Array(analyser.fftSize)
    wakeIntervalRef.current = setInterval(() => {
      if (
        !analyserRef.current ||
        recorderRef.current ||
        pttActiveRef.current ||
        continuousRef.current ||
        statusRef.current !== 'idle'
      ) {
        consecutiveActiveRef.current = 0
        return
      }

      analyserRef.current.getByteTimeDomainData(timeData)
      const rms = computeRms(timeData)
      const threshold = sensitivityToThreshold(wakeWordSensitivityRef.current)
      const now = Date.now()
      const isActive = rms > threshold

      if (isActive) {
        consecutiveActiveRef.current += 1
      } else {
        consecutiveActiveRef.current = 0
      }

      wakeHistoryRef.current.push({ active: isActive, time: now })
      wakeHistoryRef.current = wakeHistoryRef.current.filter((s) => now - s.time <= PHRASE_WINDOW_MS)
      const activeCount = wakeHistoryRef.current.filter((s) => s.active).length
      const windowSize = wakeHistoryRef.current.length

      const phraseLike = windowSize > 0 && activeCount / windowSize >= WINDOW_ACTIVE_RATIO
      const sustained = consecutiveActiveRef.current >= CONSECUTIVE_FRAMES

      if (phraseLike && sustained && now - lastWakeAtRef.current > WAKE_COOLDOWN_MS) {
        lastWakeAtRef.current = now
        consecutiveActiveRef.current = 0
        wakeHistoryRef.current = []
        console.log(
          `[INFO] 检测到本地唤醒词：${wakeWordPhraseRef.current}（RMS=${rms.toFixed(3)}）`,
        )
        if (window.electron?.showWindow) {
          window.electron.showWindow()
        } else {
          window.electron?.send?.('window:show')
        }
        void startWakeRecording()
      }
    }, WAKE_FRAME_MS)
  }, [isSupported, startAudioMonitor, startWakeRecording])

  const startListening = useCallback(async () => {
    if (statusRef.current === 'listening') return
    recordingModeRef.current = 'wake'
    await startRecording()
  }, [startRecording])

  const stopListening = useCallback(() => {
    if (statusRef.current !== 'listening') return
    stopRecording()
  }, [stopRecording])

  const startPtt = useCallback(async () => {
    if (pttActiveRef.current) return
    pttActiveRef.current = true
    recordingModeRef.current = 'ptt'
    stopWakeDetection()
    await startRecording()
  }, [startRecording, stopWakeDetection])

  const stopPtt = useCallback(() => {
    if (!pttActiveRef.current) return
    pttActiveRef.current = false
    stopRecording()
    if (wakeWordEnabledRef.current) {
      void startWakeDetection()
    }
  }, [stopRecording, startWakeDetection])

  const toggleContinuous = useCallback(() => {
    setContinuous((prev) => {
      const next = !prev
      continuousRef.current = next
      if (next) {
        recordingModeRef.current = 'continuous'
        void startRecording()
      } else {
        stopRecording()
      }
      return next
    })
  }, [startRecording, stopRecording])

  // 根据 wakeWordEnabled 启停持续麦克风监听与唤醒词检测
  useEffect(() => {
    if (!wakeWordEnabled || !isSupported) {
      stopWakeDetection()
      maybeReleaseStream()
      return
    }
    void startWakeDetection()
    return () => {
      stopWakeDetection()
      maybeReleaseStream()
    }
  }, [wakeWordEnabled, isSupported, startWakeDetection, stopWakeDetection, maybeReleaseStream])

  // 后端辅助唤醒：监听 voice.wake 事件
  useEffect(() => {
    if (!busClient || !wakeWordEnabled) return
    const unsubscribe = busClient.subscribe('voice.wake', () => {
      if (recorderRef.current || statusRef.current !== 'idle') return
      console.log('[INFO] 收到后端 voice.wake 事件，触发一次性录音')
      void startWakeRecording()
    })
    return () => unsubscribe()
  }, [busClient, wakeWordEnabled, startWakeRecording])

  // 卸载时释放所有音频资源
  useEffect(() => {
    return () => {
      releaseStream()
    }
  }, [releaseStream])

  return {
    status,
    audioLevel,
    continuous,
    isSupported,
    permissionError,
    startListening,
    stopListening,
    toggleContinuous,
    startPtt,
    stopPtt,
  }
}
