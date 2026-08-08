/**
 * useMicrosoftTts Hook
 *
 * 当 TTS provider 为 'microsoft' 时，在渲染进程直接调用 Azure Speech REST API
 * 合成音频并注入 laapStore.voice.ttsAudio，由 useTtsAudio 完成实际播放与波形可视化。
 *
 * 其他 provider（doubao 等）仍走后端 voice.tts 事件推送链路。
 */

import { useCallback, useRef } from 'react'
import type { TtsAudioSource } from '../laap/types'
import {
  synthesize,
  arrayBufferToBase64,
  formatToMimeType,
  type MicrosoftTtsConfig,
  type MicrosoftTtsFormat,
  DEFAULT_OUTPUT_FORMAT,
  DEFAULT_VOICE,
} from '../laap/microsoftTts'

export interface UseMicrosoftTtsOptions {
  /** 是否启用（仅当 TTS provider 为 'microsoft' 时应传 true） */
  enabled: boolean
  /** Azure Speech 订阅密钥 */
  subscriptionKey: string
  /** Azure Speech 区域 */
  region: string
  /** 语音短名称 */
  voice?: string
  /** 输出格式 */
  outputFormat?: MicrosoftTtsFormat
  /** 语速 [0.5, 3.0] */
  rate?: number
  /** 音调 [0.5, 2.0] */
  pitch?: number
  /** 音量 [0, 100] */
  volume?: number
  /** 合成完成回调，将 TtsAudioSource 注入到 voice.ttsAudio */
  onTtsReady: (source: TtsAudioSource) => void
  /** 合成失败回调 */
  onTtsError?: (error: Error) => void
}

/** 令牌缓存（10 分钟有效期，提前 60 秒刷新） */
interface TokenCache {
  token: string
  expiresAt: number
}

const TOKEN_LIFETIME_MS = 10 * 60 * 1000
const TOKEN_REFRESH_MARGIN_MS = 60 * 1000

export function useMicrosoftTts(options: UseMicrosoftTtsOptions) {
  const {
    enabled,
    subscriptionKey,
    region,
    voice = DEFAULT_VOICE,
    outputFormat = DEFAULT_OUTPUT_FORMAT,
    rate = 1.0,
    pitch = 1.0,
    volume = 100,
    onTtsReady,
    onTtsError,
  } = options

  const tokenCacheRef = useRef<TokenCache | null>(null)
  const synthesizingRef = useRef(false)

  /**
   * 获取缓存的访问令牌，过期时自动刷新。
   */
  const getAccessToken = useCallback(async (): Promise<string> => {
    const cache = tokenCacheRef.current
    const now = Date.now()

    if (cache && now < cache.expiresAt - TOKEN_REFRESH_MARGIN_MS) {
      return cache.token
    }

    const url = `https://${region}.api.cognitive.microsoft.com/sts/v1.0/issueToken`
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Ocp-Apim-Subscription-Key': subscriptionKey,
        'Content-Length': '0',
      },
    })

    if (!res.ok) {
      throw new Error(`[MicrosoftTTS] 获取令牌失败: ${res.status}`)
    }

    const token = await res.text()
    tokenCacheRef.current = { token, expiresAt: now + TOKEN_LIFETIME_MS }
    return token
  }, [subscriptionKey, region])

  /**
   * 将文本合成为语音并通过 onTtsReady 注入到播放链路。
   */
  const speak = useCallback(async (text: string) => {
    if (!enabled || !subscriptionKey || !region) return
    if (synthesizingRef.current) {
      console.warn('[MicrosoftTTS] 上一次合成尚未完成，跳过')
      return
    }

    synthesizingRef.current = true

    try {
      const config: MicrosoftTtsConfig = {
        subscriptionKey,
        region,
        voice,
        outputFormat,
        rate,
        pitch,
        volume,
      }

      const audioBuffer = await synthesize(text, config)
      const base64 = arrayBufferToBase64(audioBuffer)
      const mimeType = formatToMimeType(outputFormat)

      const source: TtsAudioSource = {
        audioBase64: base64,
        mimeType,
      }

      onTtsReady(source)
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err))
      console.error('[MicrosoftTTS] 合成失败:', error)
      onTtsError?.(error)
    } finally {
      synthesizingRef.current = false
    }
  }, [enabled, subscriptionKey, region, voice, outputFormat, rate, pitch, volume, onTtsReady, onTtsError, getAccessToken])

  return { speak }
}
