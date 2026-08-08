import { apiFetch } from '@/lib/auth';
import { LOCAL_ONLY } from '@/lib/env';
import { getLocalConfig, setLocalConfig } from '@/lib/db';

export const LLM_CONFIG_KEY = 'llm_config';

export interface LLMConfig {
  provider: 'openai' | 'deepseek';
  api_key: string;
  base_url: string;
  model: string;
}

export interface LLMConfigOut {
  provider: 'openai' | 'deepseek';
  base_url: string;
  model: string;
}

export const DEFAULT_LLM_CONFIG: LLMConfig = {
  provider: 'openai',
  api_key: '',
  base_url: '',
  model: '',
};

export type { LlmConfig, LlmProvider } from '@/lib/llmConfig';

export async function getLLMConfig(): Promise<LLMConfigOut | null> {
  if (LOCAL_ONLY) {
    const cfg = await getLocalConfig<LLMConfig>(LLM_CONFIG_KEY);
    if (!cfg) return null;
    return {
      provider: cfg.provider ?? 'openai',
      base_url: cfg.base_url ?? '',
      model: cfg.model ?? '',
    };
  }

  try {
    const response = await apiFetch('/api/v1/config/llm');
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

export async function getFullLLMConfig(): Promise<LLMConfig | null> {
  if (LOCAL_ONLY) {
    return await getLocalConfig<LLMConfig>(LLM_CONFIG_KEY);
  }
  try {
    const response = await apiFetch('/api/v1/config/llm/full');
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

export async function saveLLMConfig(
  config: LLMConfig
): Promise<{ ok: true; config: LLMConfigOut } | { ok: false; error: string }> {
  if (LOCAL_ONLY) {
    await setLocalConfig(LLM_CONFIG_KEY, config);
    return {
      ok: true,
      config: {
        provider: config.provider,
        base_url: config.base_url,
        model: config.model,
      },
    };
  }

  try {
    const response = await apiFetch('/api/v1/config/llm', {
      method: 'PUT',
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      const text = await response.text();
      return { ok: false, error: text || `保存失败 (${response.status})` };
    }

    const data: LLMConfigOut = await response.json();
    return { ok: true, config: data };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : '网络错误',
    };
  }
}
