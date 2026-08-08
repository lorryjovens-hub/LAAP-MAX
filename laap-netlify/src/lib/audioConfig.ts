import { getLocalConfig, setLocalConfig } from '@/lib/db';

// ============================================================================
// Types
// ============================================================================

export interface TtsProvider {
  id: string;
  /** Provider type: microsoft | openai | elevenlabs | doubao | minimax | volcano */
  provider: string;
  name: string;
  baseURL: string;
  apiKey: string;
  /** Model / voice model name */
  model: string;
  /** Voice / speaker ID */
  voice: string;
  /** Provider-specific extra credentials */
  extraCreds: Record<string, string>;
  createdAt: string;
}

export interface AsrProvider {
  id: string;
  /** Provider type: aliyun | local | xunfei | tencent | volcengine */
  provider: string;
  name: string;
  baseURL: string;
  apiKey: string;
  model: string;
  language: string;
  /** Provider-specific extra credentials */
  extraCreds: Record<string, string>;
  createdAt: string;
}

export interface TtsConfig {
  providers: TtsProvider[];
  activeProviderId?: string;
}

export interface AsrConfig {
  providers: AsrProvider[];
  activeProviderId?: string;
}

// ============================================================================
// Keys
// ============================================================================

const TTS_CONFIG_KEY = 'tts_config';
const ASR_CONFIG_KEY = 'asr_config';

// ============================================================================
// Defaults
// ============================================================================

export const DEFAULT_TTS_CONFIG: TtsConfig = {
  providers: [],
};

export const DEFAULT_ASR_CONFIG: AsrConfig = {
  providers: [],
};

// ============================================================================
// TTS Provider Presets
// ============================================================================

export const TTS_PROVIDER_PRESETS = {
  microsoft: {
    label: 'Microsoft Edge (免费)',
    provider: 'microsoft',
    name: 'Microsoft Edge TTS',
    baseURL: '',
    apiKey: '',
    description: '基于 edge-tts 的本地免费 TTS · 无需 API Key',
    defaultModel: 'zh-CN-XiaoxiaoNeural',
    defaultVoice: '',
    extraCreds: {},
  },
  openai: {
    label: 'OpenAI TTS',
    provider: 'openai',
    name: 'OpenAI',
    baseURL: 'https://api.openai.com/v1',
    apiKey: '',
    description: 'OpenAI TTS API · 需要 API Key',
    defaultModel: 'tts-1',
    defaultVoice: 'alloy',
    extraCreds: {},
  },
  elevenlabs: {
    label: 'ElevenLabs TTS',
    provider: 'elevenlabs',
    name: 'ElevenLabs',
    baseURL: 'https://api.elevenlabs.io',
    apiKey: '',
    description: 'ElevenLabs TTS · 需要 API Key',
    defaultModel: 'eleven_multilingual_v2',
    defaultVoice: '21m00Tcm4TlvDq8ikWAM',
    extraCreds: {},
  },
  doubao: {
    label: '豆包（火山方舟）TTS',
    provider: 'doubao',
    name: '豆包 TTS',
    baseURL: 'https://ark.cn-beijing.volces.com/api/v3',
    apiKey: '',
    description: '火山方舟豆包 TTS · 需要 API Key 和 Resource ID',
    defaultModel: '',
    defaultVoice: '',
    extraCreds: { doubaoResourceId: '' },
  },
  minimax: {
    label: 'MiniMax TTS',
    provider: 'minimax',
    name: 'MiniMax',
    baseURL: 'https://api.minimax.chat',
    apiKey: '',
    description: 'MiniMax TTS · 需要 API Key 和 Group ID',
    defaultModel: 'speech-01-turbo',
    defaultVoice: 'male-qn-qingse',
    extraCreds: { minimaxGroupId: '' },
  },
  volcano: {
    label: '火山引擎 TTS',
    provider: 'volcano',
    name: '火山引擎 TTS',
    baseURL: 'https://openspeech.bytedance.com',
    apiKey: '',
    description: '火山引擎 TTS · 需要 App ID 和 Token',
    defaultModel: '',
    defaultVoice: 'BV001_streaming',
    extraCreds: { volcanoAppId: '', volcanoToken: '' },
  },
} as const;

export type TtsProviderPresetKey = keyof typeof TTS_PROVIDER_PRESETS;

// ============================================================================
// ASR Provider Presets
// ============================================================================

export const ASR_PROVIDER_PRESETS = {
  local: {
    label: '本地 ASR (免费)',
    provider: 'local',
    name: '本地 ASR',
    baseURL: '',
    apiKey: '',
    description: '基于 SpeechRecognition 的本地 ASR · 无需 API Key',
    defaultModel: '',
    defaultLanguage: 'zh-CN',
    extraCreds: {},
  },
  aliyun: {
    label: '阿里云 ASR',
    provider: 'aliyun',
    name: '阿里云 ASR',
    baseURL: '',
    apiKey: '',
    description: '阿里云 Paraformer ASR · 需要 API Key',
    defaultModel: 'paraformer-v1',
    defaultLanguage: 'zh-cn',
    extraCreds: {},
  },
  xunfei: {
    label: '科大讯飞 ASR',
    provider: 'xunfei',
    name: '科大讯飞 ASR',
    baseURL: '',
    apiKey: '',
    description: '科大讯飞 RTASR · 需要 App ID 和 API Key',
    defaultModel: '',
    defaultLanguage: 'zh',
    extraCreds: { xunfeiAppId: '' },
  },
  tencent: {
    label: '腾讯云 ASR',
    provider: 'tencent',
    name: '腾讯云 ASR',
    baseURL: '',
    apiKey: '',
    description: '腾讯云 ASR · 需要 Secret ID、Secret Key 和 App ID',
    defaultModel: '',
    defaultLanguage: 'zh',
    extraCreds: { tencentSecretId: '', tencentSecretKey: '', tencentAppId: '' },
  },
  volcengine: {
    label: '火山引擎 ASR',
    provider: 'volcengine',
    name: '火山引擎 ASR',
    baseURL: '',
    apiKey: '',
    description: '火山引擎 ASR · 需要 API Key、App Key、Access Key、Resource ID',
    defaultModel: '',
    defaultLanguage: 'zh',
    extraCreds: { volcAsrAppKey: '', volcAsrAccessKey: '', volcAsrResourceId: '' },
  },
} as const;

export type AsrProviderPresetKey = keyof typeof ASR_PROVIDER_PRESETS;

// ============================================================================
// TTS Voices (display names for common providers)
// ============================================================================

export const MICROSOFT_TTS_VOICES: { value: string; label: string }[] = [
  { value: 'zh-CN-XiaoxiaoNeural', label: '晓晓（女声）' },
  { value: 'zh-CN-XiaoyiNeural', label: '晓伊（女声）' },
  { value: 'zh-CN-YunjianNeural', label: '云健（男声）' },
  { value: 'zh-CN-YunxiNeural', label: '云希（男声）' },
  { value: 'zh-CN-YunyangNeural', label: '云扬（男声）' },
  { value: 'zh-CN-XiaochenNeural', label: '晓辰（女声）' },
  { value: 'zh-CN-XiaohanNeural', label: '晓涵（女声）' },
  { value: 'zh-CN-XiaomengNeural', label: '晓梦（女声）' },
  { value: 'zh-CN-XiaoqiuNeural', label: '晓秋（女声）' },
  { value: 'zh-CN-XiaoruiNeural', label: '晓睿（女声）' },
  { value: 'zh-CN-XiaoshuangNeural', label: '晓双（女声）' },
  { value: 'zh-CN-XiaoxuanNeural', label: '晓萱（女声）' },
  { value: 'zh-CN-XiaoyanNeural', label: '晓颜（女声）' },
  { value: 'zh-CN-XiaozhenNeural', label: '晓珍（女声）' },
  { value: 'zh-CN-YunfengNeural', label: '云峰（男声）' },
  { value: 'zh-CN-YunhaoNeural', label: '云浩（男声）' },
  { value: 'zh-CN-YunjieNeural', label: '云杰（男声）' },
  { value: 'zh-CN-YunxiaoNeural', label: '云霄（男声）' },
  { value: 'zh-CN-YunzeNeural', label: '云泽（男声）' },
];

export const OPENAI_TTS_VOICES: { value: string; label: string }[] = [
  { value: 'alloy', label: 'Alloy' },
  { value: 'echo', label: 'Echo' },
  { value: 'fable', label: 'Fable' },
  { value: 'onyx', label: 'Onyx' },
  { value: 'nova', label: 'Nova' },
  { value: 'shimmer', label: 'Shimmer' },
];

export const ELEVENLABS_TTS_VOICES: { value: string; label: string }[] = [
  { value: '21m00Tcm4TlvDq8ikWAM', label: 'Rachel' },
  { value: 'AZnzlk1XvdvUeBnXmlld', label: 'Domi' },
  { value: 'EXAVITQu4vrVxnDB2cz1', label: 'Bella' },
  { value: 'ErXwobaYiN019PkySvjV', label: 'Antoni' },
  { value: 'MF3mGyEYCl7XYWbV9V6O', label: 'Elli' },
  { value: 'TxGEqnHWrfWFTfGW9XjX', label: 'Josh' },
  { value: 'VR6AewLTigWG4xSOuka', label: 'Arnold' },
  { value: 'pNInz6obpgDQGcFmaJgB', label: 'Adam' },
  { value: 'yoZ06aMxZJJ28mfd3POQ', label: 'Sam' },
];

// ============================================================================
// Guess provider preset key from name
// ============================================================================

export function guessTtsPresetKey(name: string): TtsProviderPresetKey | undefined {
  const lower = name.toLowerCase();
  if (lower.includes('microsoft') || lower.includes('edge')) return 'microsoft';
  if (lower.includes('openai')) return 'openai';
  if (lower.includes('elevenlabs')) return 'elevenlabs';
  if (lower.includes('doubao') || lower.includes('豆包') || lower.includes('volces')) return 'doubao';
  if (lower.includes('minimax')) return 'minimax';
  if (lower.includes('volcano') || lower.includes('火山')) return 'volcano';
  return undefined;
}

export function guessAsrPresetKey(name: string): AsrProviderPresetKey | undefined {
  const lower = name.toLowerCase();
  if (lower.includes('local') || lower.includes('本地')) return 'local';
  if (lower.includes('aliyun') || lower.includes('阿里')) return 'aliyun';
  if (lower.includes('xunfei') || lower.includes('讯飞')) return 'xunfei';
  if (lower.includes('tencent') || lower.includes('腾讯')) return 'tencent';
  if (lower.includes('volcengine') || lower.includes('火山')) return 'volcengine';
  return undefined;
}

// ============================================================================
// Active provider helpers
// ============================================================================

export function getActiveTtsProvider(config: TtsConfig): TtsProvider | undefined {
  if (!config.providers.length) return undefined;
  return config.providers.find((p) => p.id === config.activeProviderId) ?? config.providers[0];
}

export function getActiveAsrProvider(config: AsrConfig): AsrProvider | undefined {
  if (!config.providers.length) return undefined;
  return config.providers.find((p) => p.id === config.activeProviderId) ?? config.providers[0];
}

// ============================================================================
// Storage
// ============================================================================

export async function getTtsConfig(userId?: string): Promise<TtsConfig> {
  const stored = await getLocalConfig<TtsConfig>(TTS_CONFIG_KEY, userId);
  if (stored && Array.isArray(stored.providers)) {
    return stored;
  }
  return { providers: [] };
}

export async function saveTtsConfig(config: TtsConfig, userId?: string): Promise<void> {
  await setLocalConfig(TTS_CONFIG_KEY, config, userId);
}

export async function getAsrConfig(userId?: string): Promise<AsrConfig> {
  const stored = await getLocalConfig<AsrConfig>(ASR_CONFIG_KEY, userId);
  if (stored && Array.isArray(stored.providers)) {
    return stored;
  }
  return { providers: [] };
}

export async function saveAsrConfig(config: AsrConfig, userId?: string): Promise<void> {
  await setLocalConfig(ASR_CONFIG_KEY, config, userId);
}

// ============================================================================
// Build default providers
// ============================================================================

export function buildDefaultTtsProvider(): TtsProvider {
  const preset = TTS_PROVIDER_PRESETS.microsoft;
  return {
    id: crypto.randomUUID(),
    provider: preset.provider,
    name: preset.name,
    baseURL: preset.baseURL,
    apiKey: preset.apiKey,
    model: preset.defaultModel,
    voice: preset.defaultVoice,
    extraCreds: { ...preset.extraCreds },
    createdAt: new Date().toISOString(),
  };
}

export function buildDefaultAsrProvider(): AsrProvider {
  const preset = ASR_PROVIDER_PRESETS.local;
  return {
    id: crypto.randomUUID(),
    provider: preset.provider,
    name: preset.name,
    baseURL: preset.baseURL,
    apiKey: preset.apiKey,
    model: preset.defaultModel,
    language: preset.defaultLanguage,
    extraCreds: { ...preset.extraCreds },
    createdAt: new Date().toISOString(),
  };
}