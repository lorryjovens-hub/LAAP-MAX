/**
 * useTtsAudio Hook
 *
 * 负责播放后端通过 voice.tts / audio.stream 推送的真实 TTS 音频。
 * 支持 base64 编码音频与音频 URL，通过 Web Audio API 构建分析节点，
 * 将 AnalyserNode 暴露给 WaveformVisualizer 实现真实波形。
 *
 * 行为：
 * - 收到 source 时开始播放，并在 canplay/playing 时将 voice.status 置为 speaking。
 * - 播放结束或出错时恢复为 idle（连续监听模式下恢复为 listening）。
 * - 检测到 isRecording 为 true 时主动暂停播放，避免与麦克风 ASR 冲突。
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import type { TtsAudioSource, VoiceStatus } from '../laap/types'

export interface UseTtsAudioOptions {
  /** 当前待播放的 TTS 音频来源 */
  source: TtsAudioSource | null
  /** 是否启用 TTS 播放（默认 true） */
  enabled?: boolean
  /** 播放音量 0-1（默认 1） */
  volume?: number
  /** 是否正在录音；变为 true 时自动停止 TTS */
  isRecording?: boolean
  /** 连续监听模式；播放结束后恢复到 listening */
  continuousListening?: boolean
  /** 播放状态变化回调 */
  onStatusChange?: (status: VoiceStatus) => void
  /** 播放结束或出错回调，用于上层清理 ttsAudio */
  onEnded?: () => void
}

export interface UseTtsAudioReturn {
  /** 与 TTS 音频源连接的 AnalyserNode，供波形可视化组件读取 */
  analyserRef: React.RefObject<AnalyserNode | null>
  /** 当前是否正在播放 */
  isPlaying: boolean
  /** 手动停止播放 */
  stop: () => void
}

/**
 * 将 TtsAudioSource 构建为 Audio 元素可播放的 src。
 */
function buildAudioSrc(source: TtsAudioSource): string | undefined {
  if (source.audioUrl) return source.audioUrl
  if (!source.audioBase64) return undefined
  if (source.audioBase64.startsWith('data:')) return source.audioBase64
  const mimeType = source.mimeType ?? 'audio/wav'
  return `data:${mimeType};base64,${source.audioBase64}`
}

export function useTtsAudio(options: UseTtsAudioOptions): UseTtsAudioReturn {
  const {
    source,
    enabled = true,
    volume = 1,
    isRecording = false,
    continuousListening = false,
    onStatusChange,
    onEnded,
  } = options

  const analyserRef = useRef<AnalyserNode | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const ctxRef = useRef<AudioContext | null>(null)
  const sourceNodeRef = useRef<MediaElementAudioSourceNode | null>(null)
  const cleanupRef = useRef<(() => void) | null>(null)
  const activeRef = useRef(false)
  const [isPlaying, setIsPlaying] = useState(false)

  const resetStatus = useCallback(() => {
    onStatusChange?.(continuousListening ? 'listening' : 'idle')
  }, [onStatusChange, continuousListening])

  const stop = useCallback(() => {
    if (cleanupRef.current) {
      cleanupRef.current()
      cleanupRef.current = null
    }
  }, [])

  // 开始录音时立即暂停 TTS，避免回采麦克风
  useEffect(() => {
    if (isRecording && activeRef.current) {
      console.log('[INFO] 检测到开始录音，暂停 TTS 播放')
      stop()
      setIsPlaying(false)
      resetStatus()
      onEnded?.()
    }
  }, [isRecording, stop, resetStatus, onEnded])

  // source/enabled/volume 变化时启动或停止播放
  useEffect(() => {
    if (!source || !enabled) {
      stop()
      return
    }

    const src = buildAudioSrc(source)
    if (!src) {
      console.warn('[WARN] TTS 音频来源无效，跳过播放')
      stop()
      return
    }

    let cancelled = false

    const start = async () => {
      stop()

      if (cancelled) return

      const ctx = new AudioContext()
      ctxRef.current = ctx
      const audio = new Audio(src)
      audio.crossOrigin = 'anonymous'
      audio.volume = Math.min(1, Math.max(0, volume))
      audioRef.current = audio
      activeRef.current = true

      const handlePlaying = () => {
        if (cancelled) return
        setIsPlaying(true)
        onStatusChange?.('speaking')
      }

      const handleEnded = () => {
        if (cancelled) return
        activeRef.current = false
        setIsPlaying(false)
        resetStatus()
        onEnded?.()
        cleanup()
      }

      const handleError = (e: Event | string) => {
        if (cancelled) return
        console.error('[ERROR] TTS 音频播放失败:', e)
        activeRef.current = false
        setIsPlaying(false)
        resetStatus()
        onEnded?.()
        cleanup()
      }

      function cleanup() {
        cancelled = true
        activeRef.current = false
        audio.removeEventListener('playing', handlePlaying)
        audio.removeEventListener('ended', handleEnded)
        audio.removeEventListener('error', handleError)
        try {
          audio.pause()
        } catch {
          // 忽略已停止的情况
        }
        try {
          audio.src = ''
          audio.load()
        } catch {
          // 忽略
        }
        try {
          sourceNodeRef.current?.disconnect()
        } catch {
          // 忽略
        }
        try {
          analyserRef.current?.disconnect()
        } catch {
          // 忽略
        }
        if (ctxRef.current && ctxRef.current.state !== 'closed') {
          try {
            void ctxRef.current.close()
          } catch {
            // 忽略
          }
        }
        ctxRef.current = null
        audioRef.current = null
        sourceNodeRef.current = null
        analyserRef.current = null
        cleanupRef.current = null
      }

      cleanupRef.current = cleanup

      audio.addEventListener('playing', handlePlaying)
      audio.addEventListener('ended', handleEnded)
      audio.addEventListener('error', handleError)

      try {
        if (ctx.state === 'suspended') {
          await ctx.resume()
        }

        const audioSource = ctx.createMediaElementSource(audio)
        sourceNodeRef.current = audioSource
        const analyser = ctx.createAnalyser()
        analyser.fftSize = 256
        analyserRef.current = analyser

        audioSource.connect(analyser)
        analyser.connect(ctx.destination)
      } catch (err) {
        console.error('[ERROR] TTS 音频图构建失败:', err)
        activeRef.current = false
        setIsPlaying(false)
        resetStatus()
        onEnded?.()
        cleanup()
        return
      }

      try {
        await audio.play()
      } catch (err) {
        handleError(err instanceof Error ? err.message : String(err))
      }
    }

    void start()

    return () => {
      cancelled = true
      stop()
    }
  }, [source, enabled, volume, stop, onStatusChange, resetStatus, onEnded])

  return { analyserRef, isPlaying, stop }
}
