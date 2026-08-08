/**
 * 服务商配置数据 — 与 BaiLongma config.js 完全对齐
 */

export interface LLMProvider {
  id: string; label: string; baseURL: string; envVar: string
  defaultModel: string
  models: { id: string; label: string; deprecated?: boolean; custom?: boolean }[]
}

export const LLM_PROVIDERS: LLMProvider[] = [
  {
    id: 'deepseek', label: 'DeepSeek', baseURL: 'https://api.deepseek.com',
    envVar: 'DEEPSEEK_API_KEY', defaultModel: 'deepseek-v4-pro',
    models: [
      { id: 'deepseek-v4-flash', label: 'deepseek-v4-flash' },
      { id: 'deepseek-v4-pro', label: 'deepseek-v4-pro' },
      { id: 'deepseek-chat', label: 'deepseek-chat (deprecated)', deprecated: true },
      { id: 'deepseek-reasoner', label: 'deepseek-reasoner (deprecated)', deprecated: true },
    ],
  },
  {
    id: 'openai', label: 'OpenAI', baseURL: 'https://api.openai.com/v1',
    envVar: 'OPENAI_API_KEY', defaultModel: 'gpt-5.5',
    models: [
      { id: 'gpt-5.5', label: 'GPT-5.5' },
      { id: 'gpt-5.5-2026-04-23', label: 'GPT-5.5 (2026-04-23)' },
      { id: 'gpt-5.4', label: 'GPT-5.4' },
      { id: 'gpt-5.4-2026-03-05', label: 'GPT-5.4 (2026-03-05)' },
      { id: 'gpt-5.4-mini', label: 'GPT-5.4 mini' },
      { id: 'gpt-5.4-nano', label: 'GPT-5.4 nano' },
      { id: 'gpt-5.3-chat-latest', label: 'GPT-5.3 Chat latest' },
      { id: 'gpt-5.2', label: 'GPT-5.2' },
      { id: 'gpt-5.2-chat-latest', label: 'GPT-5.2 Chat latest', deprecated: true },
      { id: 'gpt-5.1', label: 'GPT-5.1' },
      { id: 'gpt-5.1-chat-latest', label: 'GPT-5.1 Chat latest' },
      { id: 'gpt-5', label: 'GPT-5' },
      { id: 'gpt-5-chat-latest', label: 'GPT-5 Chat latest', deprecated: true },
      { id: 'gpt-5-mini', label: 'GPT-5 mini' },
      { id: 'gpt-5-nano', label: 'GPT-5 nano' },
      { id: 'gpt-4.1', label: 'GPT-4.1' },
      { id: 'gpt-4.1-mini', label: 'GPT-4.1 mini' },
      { id: 'gpt-4.1-nano', label: 'GPT-4.1 nano' },
      { id: 'gpt-4o', label: 'GPT-4o' },
      { id: 'gpt-4o-mini', label: 'GPT-4o mini' },
      { id: 'o3', label: 'o3' },
      { id: 'o4-mini', label: 'o4-mini' },
    ],
  },
  {
    id: 'minimax', label: 'MiniMax', baseURL: 'https://api.minimax.chat/v1',
    envVar: 'MINIMAX_API_KEY', defaultModel: 'MiniMax-M2.7',
    models: [
      { id: 'MiniMax-M2.7', label: 'MiniMax-M2.7' },
      { id: 'MiniMax-M1', label: 'MiniMax-M1' },
    ],
  },
  {
    id: 'qwen', label: 'Qwen（阿里云）', baseURL: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    envVar: 'DASHSCOPE_API_KEY', defaultModel: 'qwen-turbo',
    models: [
      { id: 'qwen-turbo', label: 'qwen-turbo' },
      { id: 'qwen-plus', label: 'qwen-plus' },
    ],
  },
  {
    id: 'moonshot', label: 'Moonshot（月之暗面）', baseURL: 'https://api.moonshot.cn/v1',
    envVar: 'MOONSHOT_API_KEY', defaultModel: 'kimi-k2.6',
    models: [
      { id: 'kimi-k2.7-code', label: 'kimi-k2.7-code' },
      { id: 'kimi-k2.7-code-highspeed', label: 'kimi-k2.7-code-highspeed' },
      { id: 'kimi-k2.6', label: 'kimi-k2.6' },
      { id: 'kimi-k2.5', label: 'kimi-k2.5' },
      { id: 'moonshot-v1-32k', label: 'moonshot-v1-32k' },
      { id: 'moonshot-v1-128k', label: 'moonshot-v1-128k' },
      { id: 'moonshot-v1-8k', label: 'moonshot-v1-8k' },
      { id: 'moonshot-v1-8k-vision-preview', label: 'moonshot-v1-8k-vision-preview' },
      { id: 'moonshot-v1-32k-vision-preview', label: 'moonshot-v1-32k-vision-preview' },
      { id: 'moonshot-v1-128k-vision-preview', label: 'moonshot-v1-128k-vision-preview' },
      { id: 'kimi-k2-thinking', label: 'kimi-k2-thinking (deprecated)', deprecated: true },
    ],
  },
  {
    id: 'zhipu', label: '智谱 GLM', baseURL: 'https://open.bigmodel.cn/api/paas/v4',
    envVar: 'ZHIPU_API_KEY', defaultModel: 'glm-5.1',
    models: [
      { id: 'glm-5.1', label: 'glm-5.1' },
      { id: 'glm-5-turbo', label: 'glm-5-turbo' },
      { id: 'glm-5', label: 'glm-5' },
      { id: 'glm-4.7', label: 'glm-4.7' },
      { id: 'glm-4.7-flash', label: 'glm-4.7-flash' },
      { id: 'glm-4.7-flashx', label: 'glm-4.7-flashx' },
      { id: 'glm-4.6', label: 'glm-4.6' },
      { id: 'glm-4.5-air', label: 'glm-4.5-air' },
      { id: 'glm-4.5-airx', label: 'glm-4.5-airx' },
      { id: 'glm-4.5-flash', label: 'glm-4.5-flash' },
      { id: 'glm-5.1-highspeed', label: 'glm-5.1-highspeed (limited)' },
      { id: 'glm-4-flash-250414', label: 'glm-4-flash-250414' },
      { id: 'glm-4-flashx-250414', label: 'glm-4-flashx-250414' },
    ],
  },
  {
    id: 'mimo', label: '小米 MiMo', baseURL: 'https://api.xiaomimimo.com/v1',
    envVar: 'MIMO_API_KEY', defaultModel: 'mimo-v2.5-pro',
    models: [
      { id: 'mimo-v2.5-pro', label: 'MiMo-V2.5-Pro' },
      { id: 'mimo-v2.5', label: 'MiMo-V2.5' },
      { id: 'mimo-v2-pro', label: 'MiMo-V2-Pro' },
      { id: 'mimo-v2-flash', label: 'MiMo-V2-Flash' },
      { id: 'MiMo-V2.5-Pro-UltraSpeed', label: 'MiMo-V2.5-Pro-UltraSpeed（极速版）' },
    ],
  },
]

export interface TTSProvider {
  id: string; label: string; streaming: boolean
  voices: { id: string; label: string }[]
  credentialFields: { key: string; label: string }[]
}

export const TTS_PROVIDERS: TTSProvider[] = [
  {
    id: 'microsoft', label: '微软 Azure TTS（免费）', streaming: false,
    credentialFields: [
      { key: 'subscriptionKey', label: '订阅密钥 (Subscription Key)' },
    ],
    voices: [
      { id: 'zh-CN-XiaoxiaoNeural', label: '晓晓（女声，多风格）' },
      { id: 'zh-CN-XiaoyiNeural', label: '晓伊（女声）' },
      { id: 'zh-CN-YunjianNeural', label: '云健（男声，多风格）' },
      { id: 'zh-CN-YunxiNeural', label: '云希（男声，多风格）' },
      { id: 'zh-CN-YunxiaNeural', label: '云夏（女声，多风格）' },
      { id: 'zh-CN-YunyangNeural', label: '云扬（男声，新闻）' },
      { id: 'zh-CN-liaoning-XiaobeiNeural', label: '晓北（东北话，女声）' },
      { id: 'zh-CN-shaanxi-XiaoniNeural', label: '晓妮（陕西话，女声）' },
      { id: 'zh-HK-HiuGaaiNeural', label: '曉佳（粤语，女声）' },
      { id: 'zh-HK-WanLungNeural', label: '雲龍（粤语，男声）' },
      { id: 'zh-TW-HsiaoChenNeural', label: '曉臻（台湾，女声）' },
      { id: 'zh-TW-YunJheNeural', label: '雲哲（台湾，男声）' },
      { id: 'en-US-JennyNeural', label: 'Jenny（英文，女声）' },
      { id: 'en-US-GuyNeural', label: 'Guy（英文，男声）' },
      { id: 'ja-JP-NanamiNeural', label: '七海（日文，女声）' },
      { id: 'ko-KR-SunHiNeural', label: 'SunHi（韩文，女声）' },
    ],
  },
  {
    id: 'doubao', label: '豆包（方舟）', streaming: true,
    credentialFields: [
      { key: 'doubaoAccessKey', label: 'Access Key' },
      { key: 'doubaoKey', label: 'API Key' },
      { key: 'doubaoAppId', label: 'App ID' },
      { key: 'doubaoResourceId', label: 'Resource ID' },
    ],
    voices: [
      { id: 'zh_female_xiaohe_uranus_bigtts', label: '小何 2.0（女声，通用）' },
      { id: 'zh_female_vv_uranus_bigtts', label: 'Vivi 2.0（女声，通用/多语种）' },
      { id: 'zh_female_shuangkuaisisi_uranus_bigtts', label: '爽快思思 2.0（女声，活泼）' },
      { id: 'zh_female_cancan_uranus_bigtts', label: '知性灿灿 2.0（女声，角色）' },
      { id: 'zh_female_tianmeixiaoyuan_uranus_bigtts', label: '甜美小源 2.0（女声，甜美）' },
      { id: 'zh_male_m191_uranus_bigtts', label: '云舟 2.0（男声，通用）' },
      { id: 'zh_male_taocheng_uranus_bigtts', label: '小天 2.0（男声，通用）' },
      { id: 'zh_female_kefunvsheng_uranus_bigtts', label: '暖阳女声 2.0（客服）' },
    ],
  },
  {
    id: 'minimax', label: 'MiniMax', streaming: false,
    credentialFields: [{ key: 'minimaxKey', label: 'API Key' }],
    voices: [
      { id: 'male-qn-qingse', label: '青涩男声' },
      { id: 'male-qn-jingying', label: '精英男声' },
      { id: 'male-qn-badao', label: '霸道男声' },
      { id: 'female-shaonv', label: '少女' },
      { id: 'female-yujie', label: '御姐' },
      { id: 'female-chengshu', label: '成熟女声' },
    ],
  },
  {
    id: 'openai', label: 'OpenAI TTS', streaming: true,
    credentialFields: [
      { key: 'openaiTtsKey', label: 'API Key' },
      { key: 'openaiBaseURL', label: 'Base URL（可选）' },
    ],
    voices: [
      { id: 'nova', label: 'Nova（女声，自然）' },
      { id: 'shimmer', label: 'Shimmer（女声，轻柔）' },
      { id: 'alloy', label: 'Alloy（中性）' },
      { id: 'echo', label: 'Echo（男声）' },
      { id: 'fable', label: 'Fable（男声，叙事）' },
      { id: 'onyx', label: 'Onyx（男声，低沉）' },
    ],
  },
  {
    id: 'elevenlabs', label: 'ElevenLabs', streaming: true,
    credentialFields: [{ key: 'elevenLabsKey', label: 'API Key' }],
    voices: [
      { id: 'pNInz6obpgDQGcFmaJgB', label: 'Adam（男声）' },
      { id: 'ErXwobaYiN019PkySvjV', label: 'Antoni（男声，温和）' },
      { id: 'MF3mGyEYCl7XYWbV9V6O', label: 'Elli（女声，年轻）' },
      { id: '21m00Tcm4TlvDq8ikWAM', label: 'Rachel（女声，自然）' },
    ],
  },
  {
    id: 'volcano', label: '火山引擎', streaming: false,
    credentialFields: [
      { key: 'volcanoAppId', label: 'AppId' },
      { key: 'volcanoToken', label: 'Token' },
    ],
    voices: [
      { id: 'zh_female_qingxin', label: '清心（女声）' },
      { id: 'zh_female_tianmei_jingpin', label: '甜美精品（女声）' },
      { id: 'zh_female_meiqi', label: '魅琦（女声，成熟）' },
      { id: 'zh_male_rap', label: '说唱（男声）' },
      { id: 'zh_male_qingchengnanzhu', label: '倾城男主（男声）' },
      { id: 'BV001_streaming', label: '通用女声' },
      { id: 'BV002_streaming', label: '通用男声' },
    ],
  },
]

export interface ASRProvider {
  id: string; label: string
  credentialFields: { key: string; label: string; placeholder?: string }[]
}

export const ASR_PROVIDERS: ASRProvider[] = [
  {
    id: 'aliyun', label: '阿里云（Paraformer）',
    credentialFields: [{ key: 'aliyunAsrKey', label: 'API Key', placeholder: 'sk-...' }],
  },
  {
    id: 'tencent', label: '腾讯云 ASR',
    credentialFields: [
      { key: 'tencentSecretId', label: 'SecretId' },
      { key: 'tencentSecretKey', label: 'SecretKey' },
      { key: 'tencentAppId', label: 'AppId' },
    ],
  },
  {
    id: 'xunfei', label: '科大讯飞 RTASR',
    credentialFields: [
      { key: 'xunfeiAppId', label: 'AppId' },
      { key: 'xunfeiApiKey', label: 'API Key' },
    ],
  },
  {
    id: 'volcengine', label: '火山引擎 ASR',
    credentialFields: [
      { key: 'volcAsrApiKey', label: 'API Key' },
      { key: 'volcAsrAppKey', label: 'App Key' },
      { key: 'volcAsrAccessKey', label: 'Access Key' },
      { key: 'volcAsrResourceId', label: 'Resource ID' },
    ],
  },
  {
    id: 'local', label: '本地识别（macOS Speech）',
    credentialFields: [],
  },
]
