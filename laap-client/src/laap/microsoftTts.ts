/**
 * Microsoft Azure TTS 客户端
 *
 * 通过 Azure Cognitive Services Speech REST API 实现文本转语音。
 * 免费 F0 层级每月 50 万字符额度，无需付费即可使用。
 *
 * 默认语音：zh-CN-XiaoxiaoNeural（晓晓）
 *
 * API 文档：https://learn.microsoft.com/azure/ai-services/speech-service/rest-text-to-speech
 */

/** 微软 TTS 配置 */
export interface MicrosoftTtsConfig {
  /** Azure Speech 资源订阅密钥 */
  subscriptionKey: string
  /** Azure Speech 资源区域，如 eastasia、westus 等 */
  region: string
  /** 语音短名称，默认 zh-CN-XiaoxiaoNeural */
  voice?: string
  /** 输出音频格式，默认 audio-24khz-48kbitrate-mono-mp3 */
  outputFormat?: MicrosoftTtsFormat
  /** 语速，范围 [0.5, 3.0]，默认 1.0 */
  rate?: number
  /** 音调，范围 [0.5, 2.0]，默认 1.0 */
  pitch?: number
  /** 音量，范围 [0, 100]，默认 100 */
  volume?: number
}

/** 支持的音频输出格式 */
export type MicrosoftTtsFormat =
  | 'audio-16khz-128kbitrate-mono-mp3'
  | 'audio-16khz-64kbitrate-mono-mp3'
  | 'audio-24khz-160kbitrate-mono-mp3'
  | 'audio-24khz-48kbitrate-mono-mp3'
  | 'audio-48khz-192kbitrate-mono-mp3'
  | 'audio-48khz-96kbitrate-mono-mp3'
  | 'riff-16khz-16bit-mono-pcm'
  | 'riff-24khz-16bit-mono-pcm'
  | 'riff-48khz-16bit-mono-pcm'

/** 微软语音列表项 */
export interface MicrosoftVoiceInfo {
  ShortName: string
  DisplayName: string
  LocalName: string
  Gender: 'Female' | 'Male'
  Locale: string
  LocaleName: string
  VoiceType: string
  Status: string
  StyleList?: string[]
  SampleRateHertz: string
  WordsPerMinute: string
}

/** 预置中文语音列表（常用，无需请求 API） */
export const CHINESE_VOICES: MicrosoftVoiceInfo[] = [
  { ShortName: 'zh-CN-XiaoxiaoNeural', DisplayName: 'Xiaoxiao', LocalName: '晓晓', Gender: 'Female', Locale: 'zh-CN', LocaleName: 'Chinese (Mainland)', VoiceType: 'Neural', Status: 'GA', SampleRateHertz: '24000', WordsPerMinute: '292', StyleList: ['assistant', 'chat', 'customerservice', 'newscast', 'angry', 'cheerful', 'sad', 'excited', 'friendly', 'terrified', 'shouting', 'unfriendly', 'whispering', 'hopeful', 'lyrical', 'serious', 'depressed'] },
  { ShortName: 'zh-CN-XiaoyiNeural', DisplayName: 'Xiaoyi', LocalName: '晓伊', Gender: 'Female', Locale: 'zh-CN', LocaleName: 'Chinese (Mainland)', VoiceType: 'Neural', Status: 'GA', SampleRateHertz: '24000', WordsPerMinute: '291' },
  { ShortName: 'zh-CN-YunjianNeural', DisplayName: 'Yunjian', LocalName: '云健', Gender: 'Male', Locale: 'zh-CN', LocaleName: 'Chinese (Mainland)', VoiceType: 'Neural', Status: 'GA', SampleRateHertz: '24000', WordsPerMinute: '291', StyleList: ['angry', 'cheerful', 'sad', 'serious', 'depressed'] },
  { ShortName: 'zh-CN-YunxiNeural', DisplayName: 'Yunxi', LocalName: '云希', Gender: 'Male', Locale: 'zh-CN', LocaleName: 'Chinese (Mainland)', VoiceType: 'Neural', Status: 'GA', SampleRateHertz: '24000', WordsPerMinute: '292', StyleList: ['assistant', 'chat', 'customerservice', 'newscast', 'angry', 'cheerful', 'sad', 'excited', 'friendly', 'unfriendly', 'whispering', 'serious'] },
  { ShortName: 'zh-CN-YunxiaNeural', DisplayName: 'Yunxia', LocalName: '云夏', Gender: 'Female', Locale: 'zh-CN', LocaleName: 'Chinese (Mainland)', VoiceType: 'Neural', Status: 'GA', SampleRateHertz: '24000', WordsPerMinute: '291', StyleList: ['chat', 'customerservice', 'narration', 'newscast', 'angry', 'cheerful', 'sad'] },
  { ShortName: 'zh-CN-YunyangNeural', DisplayName: 'Yunyang', LocalName: '云扬', Gender: 'Male', Locale: 'zh-CN', LocaleName: 'Chinese (Mainland)', VoiceType: 'Neural', Status: 'GA', SampleRateHertz: '24000', WordsPerMinute: '291', StyleList: ['chat', 'customerservice', 'narration', 'newscast', 'angry', 'cheerful', 'sad'] },
  { ShortName: 'zh-CN-liaoning-XiaobeiNeural', DisplayName: 'Xiaobei', LocalName: '晓北', Gender: 'Female', Locale: 'zh-CN-liaoning', LocaleName: 'Chinese (Liaoning)', VoiceType: 'Neural', Status: 'GA', SampleRateHertz: '24000', WordsPerMinute: '291' },
  { ShortName: 'zh-CN-shaanxi-XiaoniNeural', DisplayName: 'Xiaoni', LocalName: '晓妮', Gender: 'Female', Locale: 'zh-CN-shaanxi', LocaleName: 'Chinese (Shaanxi)', VoiceType: 'Neural', Status: 'GA', SampleRateHertz: '24000', WordsPerMinute: '291' },
  { ShortName: 'zh-HK-HiuGaaiNeural', DisplayName: 'HiuGaai', LocalName: '曉佳', Gender: 'Female', Locale: 'zh-HK', LocaleName: 'Chinese (Hong Kong)', VoiceType: 'Neural', Status: 'GA', SampleRateHertz: '24000', WordsPerMinute: '291' },
  { ShortName: 'zh-HK-WanLungNeural', DisplayName: 'WanLung', LocalName: '雲龍', Gender: 'Male', Locale: 'zh-HK', LocaleName: 'Chinese (Hong Kong)', VoiceType: 'Neural', Status: 'GA', SampleRateHertz: '24000', WordsPerMinute: '291' },
  { ShortName: 'zh-TW-HsiaoChenNeural', DisplayName: 'HsiaoChen', LocalName: '曉臻', Gender: 'Female', Locale: 'zh-TW', LocaleName: 'Chinese (Taiwan)', VoiceType: 'Neural', Status: 'GA', SampleRateHertz: '24000', WordsPerMinute: '291' },
  { ShortName: 'zh-TW-YunJheNeural', DisplayName: 'YunJhe', LocalName: '雲哲', Gender: 'Male', Locale: 'zh-TW', LocaleName: 'Chinese (Taiwan)', VoiceType: 'Neural', Status: 'GA', SampleRateHertz: '24000', WordsPerMinute: '291' },
]

/** 默认语音 */
export const DEFAULT_VOICE = 'zh-CN-XiaoxiaoNeural'
/** 默认输出格式 */
export const DEFAULT_OUTPUT_FORMAT: MicrosoftTtsFormat = 'audio-24khz-48kbitrate-mono-mp3'

/**
 * 构建 SSML（Speech Synthesis Markup Language）。
 * SSML 允许精细控制语速、音调、音量和语音风格。
 */
export function buildSsml(
  text: string,
  voice: string = DEFAULT_VOICE,
  rate: number = 1.0,
  pitch: number = 1.0,
  volume: number = 100,
  style?: string,
): string {
  // 将数值比例转为 SSML 百分比字符串
  const ratePercent = `${Math.round(rate * 100)}%`
  const pitchPercent = `${Math.round(pitch * 100)}%`
  const volumeNumber = Math.min(100, Math.max(0, Math.round(volume)))

  const voiceTag = style
    ? `<voice name="${voice}"><mstts:express-as style="${style}">`
    : `<voice name="${voice}">`

  const closeTag = style
    ? `</mstts:express-as></voice>`
    : `</voice>`

  return (
    `<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='http://www.w3.org/2001/mstts' xml:lang='zh-CN'>` +
    `<mstts:backgroundaudio volume='0'/>` +
    voiceTag +
    `<prosody rate='${ratePercent}' pitch='${pitchPercent}' volume='${volumeNumber}'>` +
    escapeXml(text) +
    `</prosody>` +
    closeTag +
    `</speak>`
  )
}

/** XML 特殊字符转义 */
function escapeXml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

/**
 * 获取访问令牌。
 * Azure TTS REST API 需要先通过订阅密钥换取 10 分钟有效的 Bearer token。
 */
export async function fetchAccessToken(region: string, subscriptionKey: string): Promise<string> {
  const url = `https://${region}.api.cognitive.microsoft.com/sts/v1.0/issueToken`
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Ocp-Apim-Subscription-Key': subscriptionKey,
      'Content-Length': '0',
    },
  })
  if (!res.ok) {
    throw new Error(`[MicrosoftTTS] 获取令牌失败: ${res.status} ${res.statusText}`)
  }
  return res.text()
}

/**
 * 通过微软 TTS REST API 将文本合成为音频。
 *
 * 返回 ArrayBuffer（音频二进制数据），格式由 outputFormat 决定（默认 MP3）。
 */
export async function synthesize(
  text: string,
  config: MicrosoftTtsConfig,
): Promise<ArrayBuffer> {
  const {
    subscriptionKey,
    region,
    voice = DEFAULT_VOICE,
    outputFormat = DEFAULT_OUTPUT_FORMAT,
    rate = 1.0,
    pitch = 1.0,
    volume = 100,
  } = config

  if (!subscriptionKey || !region) {
    throw new Error('[MicrosoftTTS] 缺少 subscriptionKey 或 region 配置')
  }

  const token = await fetchAccessToken(region, subscriptionKey)

  const url = `https://${region}.tts.speech.microsoft.com/cognitiveservices/v1`
  const ssml = buildSsml(text, voice, rate, pitch, volume)

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/ssml+xml',
      'X-Microsoft-OutputFormat': outputFormat,
      'User-Agent': 'LAAP-Client',
    },
    body: ssml,
  })

  if (!res.ok) {
    const errText = await res.text().catch(() => '')
    throw new Error(`[MicrosoftTTS] 合成失败: ${res.status} ${res.statusText} ${errText}`)
  }

  return res.arrayBuffer()
}

/**
 * 将 ArrayBuffer 编码为 Base64 字符串。
 */
export function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary)
}

/**
 * 获取指定区域可用的语音列表。
 */
export async function listVoices(
  region: string,
  subscriptionKey: string,
): Promise<MicrosoftVoiceInfo[]> {
  const url = `https://${region}.tts.speech.microsoft.com/cognitiveservices/voices/list`
  const res = await fetch(url, {
    method: 'GET',
    headers: {
      'Ocp-Apim-Subscription-Key': subscriptionKey,
    },
  })
  if (!res.ok) {
    throw new Error(`[MicrosoftTTS] 获取语音列表失败: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<MicrosoftVoiceInfo[]>
}

/**
 * 判断输出格式对应的 MIME 类型。
 */
export function formatToMimeType(format: MicrosoftTtsFormat): string {
  if (format.includes('mp3')) return 'audio/mpeg'
  if (format.includes('pcm')) return 'audio/wav'
  return 'audio/mpeg'
}
