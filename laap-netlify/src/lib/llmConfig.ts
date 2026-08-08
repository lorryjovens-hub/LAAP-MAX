import { getLocalConfig, setLocalConfig } from '@/lib/db';
import { fetchWithProxy } from '@/lib/corsProxy';
import {
  OMNIROUTE_DEFAULT_BASE_URL,
  OMNIROUTE_PLACEHOLDER_API_KEY,
  OMNIROUTE_PRESET_MODELS,
  getOmniRouteRecommendedModel,
  type OmniRoutePresetModel,
} from '@/lib/omnirouteModels';

export interface LlmProvider {
  id: string;
  name: string;
  baseURL: string;
  apiKey: string;
  models: string[];
  defaultModel?: string;
  createdAt: string;
}

export interface LlmConfig {
  providers: LlmProvider[];
  activeProviderId?: string;
}

export interface LegacyLlmConfig {
  provider: 'openai' | 'deepseek';
  api_key: string;
  base_url: string;
  model: string;
}

const LLM_CONFIG_V2_KEY = 'llm_config_v2';
export const LEGACY_LLM_CONFIG_KEY = 'llm_config';
export const FIRST_RUN_FLAG_KEY = 'laap_llm_configured';

export const DEFAULT_LLM_CONFIG: LlmConfig = {
  providers: [],
};

/** Quick-select presets shown in the LLM config modal. */
export const SENSENOVA_MODELS = [
  { id: 'sensenova-6.7-flash-lite', label: 'SenseNova 6.7 Flash Lite' },
  { id: 'deepseek-v4-flash', label: 'DeepSeek V4 Flash' },
  { id: 'glm5.2', label: 'GLM 5.2' },
  { id: 'sensenova-u1-fast', label: 'SenseNova U1 Fast' },
];

export const SENSENOVA_DEFAULT_BASE_URL = '/api/sensenova/v1';

export const LLM_PROVIDER_PRESETS = {
  omniroute: {
    label: 'OmniRoute (免费)',
    name: 'OmniRoute',
    baseURL: OMNIROUTE_DEFAULT_BASE_URL,
    apiKey: OMNIROUTE_PLACEHOLDER_API_KEY,
    description: '本地 OmniRoute 网关 · 122+ 免费模型 · 无需 API Key',
  },
  sensenova: {
    label: 'SenseNova (免费)',
    name: 'SenseNova',
    baseURL: SENSENOVA_DEFAULT_BASE_URL,
    apiKey: '',
    description: '商汤日日新 SenseNova · 内置免费模型 · 通过本地代理调用',
  },
  openai: {
    label: 'OpenAI',
    name: 'OpenAI',
    baseURL: 'https://api.openai.com/v1',
    apiKey: '',
    description: '官方 OpenAI API · 需要 API Key',
  },
  deepseek: {
    label: 'DeepSeek',
    name: 'DeepSeek',
    baseURL: 'https://api.deepseek.com/v1',
    apiKey: '',
    description: '官方 DeepSeek API · 需要 API Key',
  },
  anthropic: {
    label: 'Anthropic',
    name: 'Anthropic',
    baseURL: 'https://api.anthropic.com/v1',
    apiKey: '',
    description: '官方 Anthropic Claude API · 需要 API Key',
  },
  custom: {
    label: '自定义',
    name: '',
    baseURL: '',
    apiKey: '',
    description: '任意 OpenAI 兼容端点',
  },
} as const;

export type LlmProviderPresetKey = keyof typeof LLM_PROVIDER_PRESETS;

/** Guess the preset key from a provider display name or baseURL. */
export function guessProviderPresetKey(name: string, baseURL?: string): LlmProviderPresetKey | undefined {
  const check = (s: string) => {
    const lower = s.toLowerCase();
    if (lower.includes('omniroute') || lower.includes('localhost:20128') || lower.includes('127.0.0.1:20128')) {
      return 'omniroute';
    }
    if (lower.includes('sensenova') || lower.includes('sensetime')) return 'sensenova';
    if (lower.includes('openai')) return 'openai';
    if (lower.includes('deepseek')) return 'deepseek';
    if (lower.includes('anthropic') || lower.includes('claude')) return 'anthropic';
    return undefined;
  };
  return check(name) || (baseURL ? check(baseURL) : undefined);
}

/** Returns true when the given baseURL points at the OmniRoute gateway. */
export function isOmniRouteBaseURL(baseURL: string): boolean {
  const normalized = baseURL.trim().toLowerCase().replace(/\/+$/, '');
  if (!normalized) return false;
  return (
    normalized.includes('localhost:20128') ||
    normalized.includes('127.0.0.1:20128') ||
    normalized.includes('omniroute')
  );
}

/** Returns true when a provider is configured to use the OmniRoute gateway. */
export function isOmniRouteProvider(provider: LlmProvider | undefined | null): boolean {
  if (!provider) return false;
  if (isOmniRouteBaseURL(provider.baseURL)) return true;
  return provider.defaultModel?.startsWith('omniroute/') ?? false;
}

/** Returns the OmniRoute preset models (for the model dropdown in the modal). */
export function getOmniRoutePresetModels(): OmniRoutePresetModel[] {
  return OMNIROUTE_PRESET_MODELS;
}

/** Builds an OmniRoute LlmProvider with the recommended keyless model pre-selected. */
export function buildOmniRouteProvider(): LlmProvider {
  const recommended = getOmniRouteRecommendedModel();
  return {
    id: crypto.randomUUID(),
    name: 'OmniRoute',
    baseURL: OMNIROUTE_DEFAULT_BASE_URL,
    apiKey: OMNIROUTE_PLACEHOLDER_API_KEY,
    models: [recommended.id],
    defaultModel: recommended.id,
    createdAt: new Date().toISOString(),
  };
}

/** Builds a SenseNova LlmProvider that routes through the local dev proxy. */
export function buildSenseNovaProvider(): LlmProvider {
  const defaultModel = SENSENOVA_MODELS[0].id;
  return {
    id: crypto.randomUUID(),
    name: 'SenseNova',
    baseURL: SENSENOVA_DEFAULT_BASE_URL,
    apiKey: '',
    models: SENSENOVA_MODELS.map((m) => m.id),
    defaultModel,
    createdAt: new Date().toISOString(),
  };
}

/** Reads the first-run flag from localStorage. */
export function hasLlmBeenConfigured(): boolean {
  try {
    return typeof localStorage !== 'undefined' && localStorage.getItem(FIRST_RUN_FLAG_KEY) === '1';
  } catch {
    return false;
  }
}

/** Marks the LLM as configured so the first-run modal won't show again. */
export function markLlmConfigured(): void {
  try {
    localStorage.setItem(FIRST_RUN_FLAG_KEY, '1');
  } catch {
    // ignore storage errors (e.g. privacy mode)
  }
}

function defaultProviderName(provider: 'openai' | 'deepseek'): string {
  return provider === 'deepseek' ? 'DeepSeek' : 'OpenAI';
}

function defaultBaseURL(provider: 'openai' | 'deepseek'): string {
  return provider === 'deepseek'
    ? 'https://api.deepseek.com/v1'
    : 'https://api.openai.com/v1';
}

export function normalizeApiBase(url: string): string {
  const trimmed = url.trim().replace(/\/+$/, '');
  if (!trimmed) return '';
  if (/\/v1(?:\/|$)/.test(trimmed)) return trimmed;
  return `${trimmed}/v1`;
}

function patchSenseNovaProvider(config: LlmConfig): LlmConfig {
  if (!config.providers.length) return config;
  let changed = false;
  const providers = config.providers.map((p) => {
    const isSenseNova =
      p.name.toLowerCase().includes('sensenova') ||
      p.baseURL.toLowerCase().includes('sensenova');
    if (isSenseNova && p.baseURL !== SENSENOVA_DEFAULT_BASE_URL) {
      changed = true;
      return { ...p, baseURL: SENSENOVA_DEFAULT_BASE_URL, apiKey: '' };
    }
    return p;
  });
  return changed ? { ...config, providers } : config;
}

export async function getLlmConfig(userId?: string): Promise<LlmConfig> {
  const v2 = await getLocalConfig<LlmConfig>(LLM_CONFIG_V2_KEY, userId);
  if (v2 && Array.isArray(v2.providers)) {
    return patchSenseNovaProvider(v2);
  }

  const legacy = await getLocalConfig<LegacyLlmConfig>(LEGACY_LLM_CONFIG_KEY, userId);
  if (legacy && (legacy.api_key || legacy.base_url || legacy.model)) {
    const provider: LlmProvider = {
      id: crypto.randomUUID(),
      name: defaultProviderName(legacy.provider ?? 'openai'),
      baseURL: legacy.base_url?.trim() || defaultBaseURL(legacy.provider ?? 'openai'),
      apiKey: legacy.api_key ?? '',
      models: legacy.model ? [legacy.model] : [],
      defaultModel: legacy.model || undefined,
      createdAt: new Date().toISOString(),
    };
    return {
      providers: [provider],
      activeProviderId: provider.id,
    };
  }

  return { providers: [] };
}

export async function saveLlmConfig(config: LlmConfig, userId?: string): Promise<void> {
  await setLocalConfig(LLM_CONFIG_V2_KEY, config, userId);
}

export async function addProvider(
  provider: Omit<LlmProvider, 'id' | 'createdAt'>,
  userId?: string
): Promise<LlmProvider> {
  const config = await getLlmConfig(userId);
  const newProvider: LlmProvider = {
    ...provider,
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
  };
  config.providers = [...config.providers, newProvider];
  if (!config.activeProviderId) {
    config.activeProviderId = newProvider.id;
  }
  await saveLlmConfig(config, userId);
  return newProvider;
}

export async function updateProvider(
  id: string,
  patch: Partial<Omit<LlmProvider, 'id' | 'createdAt'>>,
  userId?: string
): Promise<LlmProvider | undefined> {
  const config = await getLlmConfig(userId);
  const idx = config.providers.findIndex((p) => p.id === id);
  if (idx === -1) return undefined;
  config.providers = config.providers.map((p, i) =>
    i === idx ? { ...p, ...patch } : p
  );
  await saveLlmConfig(config, userId);
  return config.providers[idx];
}

export async function deleteProvider(id: string, userId?: string): Promise<void> {
  const config = await getLlmConfig(userId);
  config.providers = config.providers.filter((p) => p.id !== id);
  if (config.activeProviderId === id) {
    config.activeProviderId = config.providers[0]?.id;
  }
  await saveLlmConfig(config, userId);
}

export async function setActiveProvider(id: string, userId?: string): Promise<void> {
  const config = await getLlmConfig(userId);
  if (!config.providers.some((p) => p.id === id)) {
    throw new Error('Provider not found');
  }
  config.activeProviderId = id;
  await saveLlmConfig(config, userId);
}

function isLocalBaseURL(baseURL: string): boolean {
  const normalized = baseURL.trim().toLowerCase();
  if (!normalized) return false;
  if (normalized.startsWith('http://localhost')) return true;
  if (normalized.startsWith('http://127.0.0.1')) return true;
  return false;
}

function isProxiedBaseURL(baseURL: string): boolean {
  const normalized = baseURL.trim().toLowerCase();
  return normalized.startsWith('/api/');
}

export async function fetchModels(
  baseURL: string,
  apiKey: string
): Promise<{ models: string[]; error?: string }> {
  const normalized = normalizeApiBase(baseURL);
  if (!normalized) {
    return { models: [], error: 'Base URL 不能为空' };
  }
  const url = `${normalized}/models`;
  const isLocal = isLocalBaseURL(baseURL) || isOmniRouteBaseURL(baseURL) || isProxiedBaseURL(baseURL);

  try {
    const headers: Record<string, string> = {};
    if (apiKey) {
      headers.Authorization = `Bearer ${apiKey}`;
    }

    const response = isLocal
      ? await fetch(url, { headers })
      : await fetchWithProxy(url, { headers, timeoutMs: 20_000 });

    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        return { models: [], error: '鉴权失败，请检查 API Key 是否正确' };
      }
      return { models: [], error: `请求失败 (${response.status})` };
    }

    const data = (await response.json()) as { data?: { id?: string }[] };
    const models = (data.data || [])
      .map((m) => m.id)
      .filter((id): id is string => typeof id === 'string');

    if (models.length === 0) {
      return { models: [], error: '接口未返回可用模型' };
    }

    return { models, error: undefined };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    if (
      err instanceof TypeError ||
      message.toLowerCase().includes('failed to fetch') ||
      message.toLowerCase().includes('network')
    ) {
      return {
        models: [],
        error: isLocal
          ? '本地接口无法访问，请确认 OmniRoute/本地服务已启动'
          : '网络错误或 CORS 限制，已尝试内置代理仍无法获取',
      };
    }
    return { models: [], error: `获取模型列表失败：${message}` };
  }
}

export function getActiveProvider(config: LlmConfig): LlmProvider | undefined {
  if (!config.providers.length) return undefined;
  return (
    config.providers.find((p) => p.id === config.activeProviderId) ??
    config.providers[0]
  );
}

/** 判断当前 provider 是否属于免费/无 Key 档位。 */
export function isFreeOrKeylessProvider(provider: LlmProvider): boolean {
  const base = provider.baseURL.toLowerCase();
  const model = (provider.defaultModel || provider.models[0] || '').toLowerCase();
  if (base.includes('localhost') || base.includes('127.0.0.1') || base.includes('omniroute')) {
    return true;
  }
  if (base.startsWith('/api/sensenova') || model.startsWith('omniroute/')) {
    return true;
  }
  if (!provider.apiKey || provider.apiKey === OMNIROUTE_PLACEHOLDER_API_KEY) {
    return true;
  }
  return false;
}

export function toLegacyLlmConfig(
  config: LlmConfig | LegacyLlmConfig | undefined
): LegacyLlmConfig | undefined {
  if (!config) return undefined;
  if ('provider' in config) return config as LegacyLlmConfig;

  const active = getActiveProvider(config);
  if (!active) return undefined;

  return {
    provider: active.name.toLowerCase().includes('deepseek') ? 'deepseek' : 'openai',
    api_key: active.apiKey,
    base_url: normalizeApiBase(active.baseURL),
    model: active.defaultModel || active.models[0] || '',
  };
}
