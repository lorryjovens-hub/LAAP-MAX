/**
 * OmniRoute free model preset list for LAAP Studio.
 *
 * Source: D:\LAAP\OmniRoute-release-v3.8.50\open-sse\config\freeModelCatalog.data.ts
 * Curated: 2026-07-22 catalog pass.
 *
 * Selection rules (per project_memory.md constraint: prioritize OmniRoute free models,
 * cost=0, registered with `omniroute/` prefix):
 *   1. All `freeType === "keyless"` entries (zero-config — no API key needed).
 *   2. A curated subset of `recurring-daily` and `recurring-uncapped` entries from
 *      high-reliability pools (bazaarlink auto:free, baidu ERNIE 4.0, etc.).
 *
 * Model id format sent to OmniRoute gateway: `omniroute/<provider>/<modelId>`.
 * The OmniRoute provider strips the `omniroute/` prefix when calling upstream.
 */

export const OMNIROUTE_DEFAULT_BASE_URL = 'http://localhost:20128/v1';

/** OmniRoute is a keyless gateway — any non-empty placeholder works for OpenAI-compatible auth headers. */
export const OMNIROUTE_PLACEHOLDER_API_KEY = 'omniroute-free';

export type OmniRouteFreeType =
  | 'keyless'
  | 'recurring-daily'
  | 'recurring-monthly'
  | 'recurring-uncapped'
  | 'recurring-credit'
  | 'one-time-initial';

export interface OmniRoutePresetModel {
  /** Full id used as the LLM model name, e.g. `omniroute/puter/gpt-5.5`. */
  id: string;
  /** Display label shown in the model dropdown. */
  label: string;
  /** OmniRoute provider key, e.g. `puter`, `agy`. */
  provider: string;
  /** Upstream model id (without `omniroute/` prefix). */
  modelId: string;
  freeType: OmniRouteFreeType;
  /** Terms-of-service confidence: ok > caution > ambiguous > avoid > unknown. */
  tos: 'ok' | 'caution' | 'ambiguous' | 'avoid' | 'unknown';
}

interface CatalogEntry {
  provider: string;
  modelId: string;
  displayName: string;
  freeType: OmniRouteFreeType;
  tos: 'ok' | 'caution' | 'ambiguous' | 'avoid' | 'unknown';
}

// Auto-extracted from freeModelCatalog.data.ts (keyless + selected recurring entries).
const CATALOG: CatalogEntry[] = [
  // agy (keyless) — Gemini / Claude / GPT-OSS via agy proxy
  { provider: 'agy', modelId: 'claude-opus-4-6-thinking', displayName: 'Claude Opus 4.6 (Thinking)', freeType: 'keyless', tos: 'avoid' },
  { provider: 'agy', modelId: 'claude-sonnet-4-6', displayName: 'Claude Sonnet 4.6 (Thinking)', freeType: 'keyless', tos: 'avoid' },
  { provider: 'agy', modelId: 'gemini-3.1-pro-low', displayName: 'Gemini 3.1 Pro (Low)', freeType: 'keyless', tos: 'avoid' },
  { provider: 'agy', modelId: 'gemini-pro-agent', displayName: 'Gemini 3.1 Pro (High)', freeType: 'keyless', tos: 'avoid' },
  { provider: 'agy', modelId: 'gemini-3.6-flash-high', displayName: 'Gemini 3.6 Flash (High)', freeType: 'keyless', tos: 'avoid' },
  { provider: 'agy', modelId: 'gemini-3.6-flash-medium', displayName: 'Gemini 3.6 Flash (Medium)', freeType: 'keyless', tos: 'avoid' },
  { provider: 'agy', modelId: 'gemini-3.6-flash-low', displayName: 'Gemini 3.6 Flash (Low)', freeType: 'keyless', tos: 'avoid' },
  { provider: 'agy', modelId: 'gemini-3-flash-agent', displayName: 'Gemini 3.5 Flash (High)', freeType: 'keyless', tos: 'avoid' },
  { provider: 'agy', modelId: 'gemini-3.5-flash-low', displayName: 'Gemini 3.5 Flash (Medium)', freeType: 'keyless', tos: 'avoid' },
  { provider: 'agy', modelId: 'gemini-3.5-flash-extra-low', displayName: 'Gemini 3.5 Flash (Low)', freeType: 'keyless', tos: 'avoid' },
  { provider: 'agy', modelId: 'gemini-3.1-flash-lite', displayName: 'Gemini 3.1 Flash Lite', freeType: 'keyless', tos: 'avoid' },
  { provider: 'agy', modelId: 'gemini-2.5-flash', displayName: 'Gemini 2.5 Flash', freeType: 'keyless', tos: 'avoid' },
  { provider: 'agy', modelId: 'gemini-2.5-flash-thinking', displayName: 'Gemini 2.5 Flash Thinking', freeType: 'keyless', tos: 'avoid' },
  { provider: 'agy', modelId: 'gemini-2.5-flash-lite', displayName: 'Gemini 2.5 Flash Lite', freeType: 'keyless', tos: 'avoid' },
  { provider: 'agy', modelId: 'gpt-oss-120b-medium', displayName: 'GPT-OSS 120B (Medium)', freeType: 'keyless', tos: 'avoid' },

  // aihorde (keyless, tos: ok) — community GPU cluster
  { provider: 'aihorde', modelId: 'aphrodite/TheDrummer/Cydonia-24B-v4.3', displayName: 'Cydonia 24B (AI Horde)', freeType: 'keyless', tos: 'ok' },
  { provider: 'aihorde', modelId: 'aphrodite/TheDrummer/Skyfall-31B-v4.2', displayName: 'Skyfall 31B (AI Horde)', freeType: 'keyless', tos: 'ok' },
  { provider: 'aihorde', modelId: 'google/gemma-4-31b', displayName: 'Gemma 4 31B (AI Horde)', freeType: 'keyless', tos: 'ok' },

  // blackbox (keyless)
  { provider: 'blackbox', modelId: 'gpt-4o', displayName: 'GPT-4o', freeType: 'keyless', tos: 'avoid' },
  { provider: 'blackbox', modelId: 'gemini-2.5-flash', displayName: 'Gemini 2.5 Flash', freeType: 'keyless', tos: 'avoid' },
  { provider: 'blackbox', modelId: 'claude-sonnet-4', displayName: 'Claude Sonnet 4', freeType: 'keyless', tos: 'avoid' },
  { provider: 'blackbox', modelId: 'deepseek-v3', displayName: 'DeepSeek V3', freeType: 'keyless', tos: 'avoid' },
  { provider: 'blackbox', modelId: 'blackboxai', displayName: 'Blackbox AI', freeType: 'keyless', tos: 'avoid' },
  { provider: 'blackbox', modelId: 'blackboxai-pro', displayName: 'Blackbox AI Pro', freeType: 'keyless', tos: 'avoid' },

  // duckduckgo-web (keyless)
  { provider: 'duckduckgo-web', modelId: 'gpt-5.4-mini', displayName: 'GPT-5.4 Mini', freeType: 'keyless', tos: 'avoid' },
  { provider: 'duckduckgo-web', modelId: 'gpt-5.4-nano', displayName: 'GPT-5.4 Nano', freeType: 'keyless', tos: 'avoid' },
  { provider: 'duckduckgo-web', modelId: 'claude-haiku-4-5', displayName: 'Claude Haiku 4.5', freeType: 'keyless', tos: 'avoid' },
  { provider: 'duckduckgo-web', modelId: 'mistral-small-2603', displayName: 'Mistral Small 4', freeType: 'keyless', tos: 'avoid' },
  { provider: 'duckduckgo-web', modelId: 'tinfoil/gpt-oss-120b', displayName: 'gpt-oss 120B', freeType: 'keyless', tos: 'avoid' },
  { provider: 'duckduckgo-web', modelId: 'tinfoil/gemma4-31b', displayName: 'Gemma 4 31B', freeType: 'keyless', tos: 'avoid' },

  // felo-web (keyless)
  { provider: 'felo-web', modelId: 'felo-chat', displayName: 'Felo Chat', freeType: 'keyless', tos: 'avoid' },
  { provider: 'felo-web', modelId: 'felo-search', displayName: 'Felo Search', freeType: 'keyless', tos: 'avoid' },
  { provider: 'felo-web', modelId: 'felo-scholar', displayName: 'Felo Scholar', freeType: 'keyless', tos: 'avoid' },
  { provider: 'felo-web', modelId: 'felo-social', displayName: 'Felo Social', freeType: 'keyless', tos: 'avoid' },
  { provider: 'felo-web', modelId: 'felo-document', displayName: 'Felo Document', freeType: 'keyless', tos: 'avoid' },

  // friendliai (keyless)
  { provider: 'friendliai', modelId: 'meta-llama-3.1-70b-instruct', displayName: 'Llama 3.1 70B Instruct', freeType: 'keyless', tos: 'avoid' },
  { provider: 'friendliai', modelId: 'meta-llama-3.1-8b-instruct', displayName: 'Llama 3.1 8B Instruct', freeType: 'keyless', tos: 'avoid' },

  // hackclub (keyless, tos: caution)
  { provider: 'hackclub', modelId: 'meta-llama/llama-3.3-70b-instruct', displayName: 'Llama 3.3 70B', freeType: 'keyless', tos: 'caution' },
  { provider: 'hackclub', modelId: 'mistralai/mistral-7b-instruct', displayName: 'Mistral 7B', freeType: 'keyless', tos: 'caution' },
  { provider: 'hackclub', modelId: 'deepseek-ai/deepseek-coder-33b', displayName: 'DeepSeek Coder 33B', freeType: 'keyless', tos: 'caution' },

  // iflytek (keyless)
  { provider: 'iflytek', modelId: 'generalv3.5', displayName: 'iFlytek Spark General V3.5', freeType: 'keyless', tos: 'avoid' },

  // liquid (keyless)
  { provider: 'liquid', modelId: 'liquid-lfm-40b', displayName: 'Liquid LFM 40B', freeType: 'keyless', tos: 'unknown' },

  // muse-spark-web (keyless)
  { provider: 'muse-spark-web', modelId: 'muse-spark', displayName: 'Muse Spark', freeType: 'keyless', tos: 'avoid' },
  { provider: 'muse-spark-web', modelId: 'muse-spark-thinking', displayName: 'Muse Spark Thinking', freeType: 'keyless', tos: 'avoid' },
  { provider: 'muse-spark-web', modelId: 'muse-spark-contemplating', displayName: 'Muse Spark Contemplating', freeType: 'keyless', tos: 'avoid' },

  // opencode (keyless)
  { provider: 'opencode', modelId: 'big-pickle', displayName: 'Big Pickle', freeType: 'keyless', tos: 'avoid' },
  { provider: 'opencode', modelId: 'deepseek-v4-flash-free', displayName: 'DeepSeek V4 Flash Free', freeType: 'keyless', tos: 'avoid' },
  { provider: 'opencode', modelId: 'minimax-m2.5-free', displayName: 'MiniMax M2.5 Free', freeType: 'keyless', tos: 'avoid' },
  { provider: 'opencode', modelId: 'ling-2.6-1t-free', displayName: 'Ling 2.6 Free', freeType: 'keyless', tos: 'avoid' },
  { provider: 'opencode', modelId: 'trinity-large-preview-free', displayName: 'Trinity Large Preview Free', freeType: 'keyless', tos: 'avoid' },
  { provider: 'opencode', modelId: 'nemotron-3-super-free', displayName: 'Nemotron 3 Super Free', freeType: 'keyless', tos: 'avoid' },
  { provider: 'opencode', modelId: 'qwen3.6-plus-free', displayName: 'Qwen3.6 Plus Free', freeType: 'keyless', tos: 'avoid' },

  // ovhcloud (keyless, tos: ok — higher trust anonymous tier)
  { provider: 'ovhcloud', modelId: 'gpt-oss-120b', displayName: 'GPT-OSS 120B (OVH)', freeType: 'keyless', tos: 'ok' },
  { provider: 'ovhcloud', modelId: 'gpt-oss-20b', displayName: 'GPT-OSS 20B (OVH)', freeType: 'keyless', tos: 'ok' },
  { provider: 'ovhcloud', modelId: 'Qwen3.6-27B', displayName: 'Qwen3.6 27B (OVH)', freeType: 'keyless', tos: 'ok' },
  { provider: 'ovhcloud', modelId: 'Mistral-Small-3.2-24B-Instruct-2506', displayName: 'Mistral Small 3.2 24B (OVH)', freeType: 'keyless', tos: 'ok' },
  { provider: 'ovhcloud', modelId: 'Qwen2.5-VL-72B-Instruct', displayName: 'Qwen2.5 VL 72B (OVH)', freeType: 'keyless', tos: 'ok' },

  // pollinations (keyless)
  { provider: 'pollinations', modelId: 'openai', displayName: 'OpenAI (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'openai-fast', displayName: 'OpenAI Fast (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'openai-large', displayName: 'OpenAI Large (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'qwen-coder', displayName: 'Qwen Coder (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'mistral', displayName: 'Mistral (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'gemini-flash-lite-3.1', displayName: 'Gemini Flash Lite 3.1 (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'deepseek', displayName: 'DeepSeek (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'grok', displayName: 'Grok (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'grok-large', displayName: 'Grok Large (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'gemini-search', displayName: 'Gemini Search (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'perplexity-fast', displayName: 'Perplexity Fast (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'perplexity-reasoning', displayName: 'Perplexity Reasoning (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'kimi', displayName: 'Kimi (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'gemini-large', displayName: 'Gemini Large (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'nova-fast', displayName: 'Nova Fast (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'nova', displayName: 'Nova (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'glm', displayName: 'GLM (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'minimax', displayName: 'MiniMax (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'mistral-large', displayName: 'Mistral Large (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'qwen-coder-large', displayName: 'Qwen Coder Large (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'qwen-large', displayName: 'Qwen Large (Pollinations)', freeType: 'keyless', tos: 'caution' },
  { provider: 'pollinations', modelId: 'qwen-vision', displayName: 'Qwen Vision (Pollinations)', freeType: 'keyless', tos: 'caution' },

  // puter (keyless, tos: caution — broad upstream coverage)
  { provider: 'puter', modelId: 'gpt-5.5', displayName: 'GPT-5.5 (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'gpt-5.4', displayName: 'GPT-5.4 (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'gpt-5.4-mini', displayName: 'GPT-5.4 Mini (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'gpt-5.4-nano', displayName: 'GPT-5.4 Nano (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'gpt-4o', displayName: 'GPT-4o (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'gpt-4o-mini', displayName: 'GPT-4o Mini (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'o3', displayName: 'OpenAI o3 (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'claude-haiku-4-5', displayName: 'Claude Haiku 4.5 (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'claude-sonnet-4-6', displayName: 'Claude Sonnet 4.6 (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'claude-opus-4-7', displayName: 'Claude Opus 4.7 (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'google/gemini-3.1-flash-lite-preview', displayName: 'Gemini 3.1 Flash Lite (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'google/gemini-3-flash', displayName: 'Gemini 3 Flash (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'google/gemini-3.1-pro-preview', displayName: 'Gemini 3.1 Pro (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'deepseek/deepseek-v4-pro', displayName: 'DeepSeek V4 Pro (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'deepseek/deepseek-v4-flash', displayName: 'DeepSeek V4 Flash (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'x-ai/grok-4.3', displayName: 'Grok 4.3 (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'x-ai/grok-4.20', displayName: 'Grok 4.20 (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'llama-4-scout', displayName: 'Llama 4 Scout (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'llama-4-maverick', displayName: 'Llama 4 Maverick (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'llama-3.3-70b-instruct', displayName: 'Llama 3.3 70B (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'mistral-small-2603', displayName: 'Mistral Small 4 (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'mistral-medium-3-5', displayName: 'Mistral Medium 3.5 (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'mistral-large-2512', displayName: 'Mistral Large (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'devstral-2512', displayName: 'Devstral 2 (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'codestral-2508', displayName: 'Codestral (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'mistral-nemo', displayName: 'Mistral Nemo (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'qwen/qwen3.6-plus', displayName: 'Qwen 3.6 Plus (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'qwen/qwen3.5-397b-a17b', displayName: 'Qwen 3.5 397B (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'perplexity/sonar-deep-research', displayName: 'Sonar Deep Research (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'perplexity/sonar-pro-search', displayName: 'Sonar Pro Search (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'perplexity/sonar-pro', displayName: 'Sonar Pro (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'perplexity/sonar-reasoning-pro', displayName: 'Sonar Reasoning Pro (Puter)', freeType: 'keyless', tos: 'caution' },
  { provider: 'puter', modelId: 'perplexity/sonar', displayName: 'Sonar (Puter)', freeType: 'keyless', tos: 'caution' },

  // qwen-web (keyless) — official Qwen web tier
  { provider: 'qwen-web', modelId: 'qwen3.8-max-preview', displayName: 'Qwen3.8 Max Preview', freeType: 'keyless', tos: 'avoid' },
  { provider: 'qwen-web', modelId: 'qwen3.7-max', displayName: 'Qwen3.7 Max', freeType: 'keyless', tos: 'avoid' },
  { provider: 'qwen-web', modelId: 'qwen3.7-plus', displayName: 'Qwen3.7 Plus', freeType: 'keyless', tos: 'avoid' },
  { provider: 'qwen-web', modelId: 'qwen3.6-plus', displayName: 'Qwen3.6 Plus', freeType: 'keyless', tos: 'avoid' },

  // sparkdesk (keyless)
  { provider: 'sparkdesk', modelId: 'lite', displayName: 'iFlytek Spark Lite', freeType: 'keyless', tos: 'caution' },

  // uncloseai (keyless)
  { provider: 'uncloseai', modelId: 'adamo1139/Hermes-3-Llama-3.1-8B-FP8-Dynamic', displayName: 'Hermes 3 Llama 3.1 8B', freeType: 'keyless', tos: 'caution' },
  { provider: 'uncloseai', modelId: 'qwen3.6:27b', displayName: 'Qwen3 Coder 27B', freeType: 'keyless', tos: 'caution' },
  { provider: 'uncloseai', modelId: 'gemma4:31b', displayName: 'Gemma 4 31B', freeType: 'keyless', tos: 'caution' },

  // --- Selected recurring-daily / recurring-uncapped fallbacks (reliable pools) ---

  // baidu ERNIE 4.0 8K (recurring-uncapped — permanently free)
  { provider: 'baidu', modelId: 'ernie-4.0-8k', displayName: 'ERNIE 4.0 8K', freeType: 'recurring-uncapped', tos: 'caution' },

  // bazaarlink auto:free — Zero Cost Router (recurring-daily, broad coverage)
  { provider: 'bazaarlink', modelId: 'auto:free', displayName: 'Auto Free (Zero Cost Router)', freeType: 'recurring-daily', tos: 'caution' },
  { provider: 'bazaarlink', modelId: 'claude-opus-4.7', displayName: 'Claude Opus 4.7 (Bazaar)', freeType: 'recurring-daily', tos: 'caution' },
  { provider: 'bazaarlink', modelId: 'claude-sonnet-4.6', displayName: 'Claude Sonnet 4.6 (Bazaar)', freeType: 'recurring-daily', tos: 'caution' },
  { provider: 'bazaarlink', modelId: 'gpt-5.5', displayName: 'GPT-5.5 (Bazaar)', freeType: 'recurring-daily', tos: 'caution' },
  { provider: 'bazaarlink', modelId: 'gpt-5.4', displayName: 'GPT-5.4 (Bazaar)', freeType: 'recurring-daily', tos: 'caution' },
  { provider: 'bazaarlink', modelId: 'gemini-3.1-pro-preview', displayName: 'Gemini 3.1 Pro (Bazaar)', freeType: 'recurring-daily', tos: 'caution' },
  { provider: 'bazaarlink', modelId: 'deepseek-v3.2', displayName: 'DeepSeek V3.2 (Bazaar)', freeType: 'recurring-daily', tos: 'caution' },
  { provider: 'bazaarlink', modelId: 'kimi-k2.6', displayName: 'Kimi K2.6 (Bazaar)', freeType: 'recurring-daily', tos: 'caution' },
  { provider: 'bazaarlink', modelId: 'glm-5.1', displayName: 'GLM 5.1 (Bazaar)', freeType: 'recurring-daily', tos: 'caution' },
  { provider: 'bazaarlink', modelId: 'mistral-large-2512', displayName: 'Mistral Large 3 (Bazaar)', freeType: 'recurring-daily', tos: 'caution' },
  { provider: 'bazaarlink', modelId: 'qwen3.6-plus', displayName: 'Qwen 3.6 Plus (Bazaar)', freeType: 'recurring-daily', tos: 'caution' },
];

function toPreset(entry: CatalogEntry): OmniRoutePresetModel {
  return {
    id: `omniroute/${entry.provider}/${entry.modelId}`,
    label: entry.displayName,
    provider: entry.provider,
    modelId: entry.modelId,
    freeType: entry.freeType,
    tos: entry.tos,
  };
}

/** All curated OmniRoute free models, keyless first then recurring fallbacks. */
export const OMNIROUTE_PRESET_MODELS: OmniRoutePresetModel[] = CATALOG.map(toPreset);

/** Keyless models only — best for first-run zero-config setup. */
export const OMNIROUTE_KEYLESS_MODELS: OmniRoutePresetModel[] = OMNIROUTE_PRESET_MODELS.filter(
  (m) => m.freeType === 'keyless'
);

/** Helper: get a "recommended" model for first-run default. Prefers tos:ok keyless, then caution keyless. */
export function getOmniRouteRecommendedModel(): OmniRoutePresetModel {
  const keyless = OMNIROUTE_KEYLESS_MODELS;
  return (
    keyless.find((m) => m.tos === 'ok') ??
    keyless.find((m) => m.tos === 'caution' && m.provider === 'puter') ??
    keyless.find((m) => m.tos === 'caution') ??
    keyless[0] ??
    OMNIROUTE_PRESET_MODELS[0]
  );
}

/** Helper: list unique provider keys in the catalog, sorted alphabetically. */
export function getOmniRouteProviders(): string[] {
  return Array.from(new Set(OMNIROUTE_PRESET_MODELS.map((m) => m.provider))).sort();
}

/** Helper: filter preset models by provider key. */
export function getOmniRouteModelsByProvider(provider: string): OmniRoutePresetModel[] {
  return OMNIROUTE_PRESET_MODELS.filter((m) => m.provider === provider);
}

/** Helper: check if a model id is an OmniRoute preset. */
export function isOmniRouteModelId(modelId: string): boolean {
  return modelId.startsWith('omniroute/');
}
