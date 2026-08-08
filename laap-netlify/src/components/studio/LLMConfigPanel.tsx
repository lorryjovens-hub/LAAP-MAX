import { useMemo, useState } from 'react';
import { Key, Save, Eye, EyeOff, Plus, Trash2, Check, ChevronDown, ChevronUp, AlertCircle, Loader2 } from 'lucide-react';
import type { LlmConfig, LlmProvider } from '@/lib/llmConfig';
import {
  fetchModels,
  getActiveProvider,
  guessProviderPresetKey,
  isOmniRouteBaseURL,
  LLM_PROVIDER_PRESETS,
  SENSENOVA_MODELS,
} from '@/lib/llmConfig';
import { OMNIROUTE_PRESET_MODELS } from '@/lib/omnirouteModels';

interface LLMConfigPanelProps {
  config: LlmConfig;
  saved?: LlmConfig | null;
  onChange: (config: LlmConfig) => void;
  onSave: (nextConfig?: LlmConfig) => void | Promise<void>;
}

const EMPTY_PROVIDER: Omit<LlmProvider, 'id' | 'createdAt'> = {
  name: '',
  baseURL: '',
  apiKey: '',
  models: [],
  defaultModel: '',
};

export function LLMConfigPanel({ config, saved, onChange, onSave }: LLMConfigPanelProps) {
  const [showKeyMap, setShowKeyMap] = useState<Record<string, boolean>>({});
  const [expandedMap, setExpandedMap] = useState<Record<string, boolean>>({});
  const [fetchingMap, setFetchingMap] = useState<Record<string, boolean>>({});
  const [fetchErrorMap, setFetchErrorMap] = useState<Record<string, string>>({});
  const [globalError, setGlobalError] = useState<string | null>(null);

  const activeProvider = useMemo(() => getActiveProvider(config), [config]);

  function updateConfig(next: LlmConfig) {
    onChange(next);
  }

  function ensureExpanded(id: string) {
    setExpandedMap((prev) => ({ ...prev, [id]: true }));
  }

  function addProvider() {
    const id = crypto.randomUUID();
    const provider: LlmProvider = {
      ...EMPTY_PROVIDER,
      id,
      createdAt: new Date().toISOString(),
    };
    const next = {
      ...config,
      providers: [...config.providers, provider],
      activeProviderId: config.activeProviderId || id,
    };
    updateConfig(next);
    ensureExpanded(id);
  }

  function removeProvider(id: string) {
    const next = {
      ...config,
      providers: config.providers.filter((p) => p.id !== id),
    };
    if (next.activeProviderId === id) {
      next.activeProviderId = next.providers[0]?.id;
    }
    updateConfig(next);
    setShowKeyMap((prev) => {
      const copy = { ...prev };
      delete copy[id];
      return copy;
    });
    setExpandedMap((prev) => {
      const copy = { ...prev };
      delete copy[id];
      return copy;
    });
  }

  function setActiveProviderId(id: string) {
    updateConfig({ ...config, activeProviderId: id });
  }

  function updateProviderField(
    id: string,
    field: keyof Omit<LlmProvider, 'id' | 'createdAt' | 'models'>,
    value: string
  ) {
    const nextProviders = config.providers.map((p) =>
      p.id === id ? { ...p, [field]: value } : p
    );
    updateConfig({ ...config, providers: nextProviders });
  }

  function isSenseNovaProvider(provider: LlmProvider): boolean {
    return provider.name.toLowerCase().includes('sensenova') || provider.baseURL.toLowerCase().includes('sensenova');
  }

  async function handleSaveProvider(id: string) {
    setGlobalError(null);
    const provider = config.providers.find((p) => p.id === id);
    if (!provider) return;

    setFetchingMap((prev) => ({ ...prev, [id]: true }));
    setFetchErrorMap((prev) => ({ ...prev, [id]: '' }));

    try {
      let models = provider.models || [];
      let error: string | undefined;

      // For known presets with curated model lists, skip the /models fetch
      // to avoid CORS/network flakiness and use the built-in list.
      if (isSenseNovaProvider(provider)) {
        models = SENSENOVA_MODELS.map((m) => m.id);
      } else if (!isOmniRouteBaseURL(provider.baseURL)) {
        const result = await fetchModels(provider.baseURL, provider.apiKey);
        models = result.models;
        error = result.error;
      } else {
        const result = await fetchModels(provider.baseURL, provider.apiKey);
        models = result.models;
        error = result.error;
      }

      if (error) {
        setFetchErrorMap((prev) => ({ ...prev, [id]: error }));
      }

      const nextProviders = config.providers.map((p) => {
        if (p.id !== id) return p;
        const defaultModel =
          p.defaultModel && models.includes(p.defaultModel)
            ? p.defaultModel
            : models[0] || p.defaultModel || '';
        return { ...p, models, defaultModel };
      });

      const nextConfig = { ...config, providers: nextProviders };
      updateConfig(nextConfig);
      await onSave(nextConfig);
    } catch (err) {
      setGlobalError(err instanceof Error ? err.message : '保存失败');
    } finally {
      setFetchingMap((prev) => ({ ...prev, [id]: false }));
    }
  }

  const activeLabel = activeProvider
    ? `${activeProvider.name || '未命名'} / ${activeProvider.defaultModel || '默认模型'}`
    : '未配置';

  return (
    <div className="space-y-3">
      <div className="font-mono text-[10px] text-laap-text-tertiary uppercase tracking-wider flex items-center gap-1.5">
        <Key size={11} />
        LLM 配置
      </div>

      <div className="space-y-2 text-xs overflow-y-auto max-h-[55dvh] md:max-h-none pb-6 pr-1 scroll-smooth">
        {globalError && (
          <div className="px-2 py-1.5 text-[10px] text-laap-rose bg-laap-rose/10 border border-laap-rose/30 rounded-sm flex items-start gap-1.5">
            <AlertCircle size={12} className="mt-0.5 flex-shrink-0" />
            {globalError}
          </div>
        )}

        {config.providers.length === 0 && (
          <div className="text-[10px] text-laap-text-tertiary px-1 py-2 text-center border border-dashed border-laap-border rounded-sm">
            暂无 provider，点击下方按钮添加
          </div>
        )}

        {config.providers.map((provider) => {
          const expanded = expandedMap[provider.id] ?? true;
          const showKey = showKeyMap[provider.id] ?? false;
          const fetching = fetchingMap[provider.id] ?? false;
          const fetchError = fetchErrorMap[provider.id];
          const isActive = config.activeProviderId === provider.id;
          const models = provider.models || [];

          return (
            <div
              key={provider.id}
              className={`border rounded-sm ${
                isActive ? 'border-laap-gold/50 bg-laap-gold/5' : 'border-laap-border'
              }`}
            >
              <button
                type="button"
                onClick={() => setExpandedMap((prev) => ({ ...prev, [provider.id]: !expanded }))}
                className="w-full flex items-center justify-between px-2.5 py-2 text-left"
              >
                <span className="flex items-center gap-1.5 text-laap-text-secondary truncate">
                  {isActive && <Check size={11} className="text-laap-gold flex-shrink-0" />}
                  <span className="truncate">{provider.name || '未命名 provider'}</span>
                </span>
                <span className="text-laap-text-tertiary flex-shrink-0">
                  {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                </span>
              </button>

              {expanded && (
                <div className="px-2.5 pb-2.5 space-y-2">
                  <div>
                    <label className="block text-laap-text-tertiary mb-1">名称</label>
                    <input
                      type="text"
                      value={provider.name}
                      onChange={(e) => {
                        const value = e.target.value;
                        updateProviderField(provider.id, 'name', value);
                        const guessed = guessProviderPresetKey(value, provider.baseURL);
                        if (guessed) {
                          const preset = LLM_PROVIDER_PRESETS[guessed];
                          updateProviderField(provider.id, 'baseURL', preset.baseURL);
                          if (guessed === 'omniroute') {
                            updateProviderField(provider.id, 'apiKey', preset.apiKey);
                            updateProviderField(provider.id, 'defaultModel', OMNIROUTE_PRESET_MODELS[0]?.id || '');
                          } else if (guessed === 'sensenova') {
                            updateProviderField(provider.id, 'apiKey', preset.apiKey);
                            updateProviderField(provider.id, 'defaultModel', SENSENOVA_MODELS[0]?.id || '');
                            updateConfig({
                              ...config,
                              providers: config.providers.map((p) =>
                                p.id === provider.id
                                  ? { ...p, models: SENSENOVA_MODELS.map((m) => m.id) }
                                  : p
                              ),
                            });
                          } else if (!provider.apiKey || provider.apiKey === LLM_PROVIDER_PRESETS.omniroute.apiKey || provider.apiKey === LLM_PROVIDER_PRESETS.sensenova.apiKey) {
                            updateProviderField(provider.id, 'apiKey', preset.apiKey);
                          }
                        }
                      }}
                      placeholder="例如 OpenAI、DeepSeek"
                      className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                    />
                  </div>

                  <div>
                    <label className="block text-laap-text-tertiary mb-1">Base URL</label>
                    <input
                      type="text"
                      value={provider.baseURL}
                      onChange={(e) => updateProviderField(provider.id, 'baseURL', e.target.value)}
                      placeholder="https://api.openai.com/v1"
                      className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                    />
                  </div>

                  <div>
                    <label className="block text-laap-text-tertiary mb-1">API Key</label>
                    <div className="relative">
                      <input
                        type={showKey ? 'text' : 'password'}
                        value={provider.apiKey}
                        onChange={(e) => updateProviderField(provider.id, 'apiKey', e.target.value)}
                        placeholder="API Key"
                        className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 pr-10 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                      />
                      <button
                        type="button"
                        onClick={() =>
                          setShowKeyMap((prev) => ({ ...prev, [provider.id]: !showKey }))
                        }
                        className="absolute right-0 top-0 h-full px-2.5 text-laap-text-tertiary hover:text-laap-text-secondary min-w-[40px] flex items-center justify-center"
                        title={showKey ? '隐藏' : '显示'}
                      >
                        {showKey ? <EyeOff size={14} /> : <Eye size={14} />}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-laap-text-tertiary mb-1">模型</label>
                    {models.length > 0 ? (
                      <select
                        value={provider.defaultModel || ''}
                        onChange={(e) =>
                          updateProviderField(provider.id, 'defaultModel', e.target.value)
                        }
                        className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                      >
                        {models.map((m) => (
                          <option key={m} value={m}>
                            {m}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type="text"
                        value={provider.defaultModel || ''}
                        onChange={(e) =>
                          updateProviderField(provider.id, 'defaultModel', e.target.value)
                        }
                        placeholder="手动输入模型名，保存后将自动获取列表"
                        className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                      />
                    )}
                  </div>

                  {fetchError && (
                    <div className="text-[10px] text-laap-rose flex items-start gap-1">
                      <AlertCircle size={11} className="mt-0.5 flex-shrink-0" />
                      {fetchError}
                    </div>
                  )}

                  <div className="flex items-center gap-2 pt-1">
                    <button
                      type="button"
                      onClick={() => handleSaveProvider(provider.id)}
                      disabled={fetching}
                      className="flex-1 flex items-center justify-center gap-1 py-2 text-xs font-medium text-laap-bg-primary bg-laap-gold/90 rounded-sm hover:bg-laap-gold disabled:opacity-60 transition-colors min-h-[36px]"
                    >
                      {fetching ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
                      {fetching ? '获取模型…' : '保存'}
                    </button>

                    <button
                      type="button"
                      onClick={() => setActiveProviderId(provider.id)}
                      disabled={isActive}
                      className={`flex-1 flex items-center justify-center gap-1 py-2 text-xs font-medium border rounded-sm transition-colors min-h-[36px] ${
                        isActive
                          ? 'border-laap-gold/50 text-laap-gold cursor-default'
                          : 'border-laap-border text-laap-text-secondary hover:text-white hover:border-laap-gold/50'
                      }`}
                    >
                      {isActive ? <Check size={12} /> : null}
                      {isActive ? '默认' : '设为默认'}
                    </button>

                    <button
                      type="button"
                      onClick={() => removeProvider(provider.id)}
                      className="px-2.5 py-2 text-laap-rose border border-laap-rose/30 rounded-sm hover:bg-laap-rose/10 transition-colors min-h-[36px] flex items-center justify-center"
                      title="删除"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}

        <button
          type="button"
          onClick={addProvider}
          className="w-full flex items-center justify-center gap-1.5 py-2 text-xs font-medium text-laap-text-secondary border border-dashed border-laap-border rounded-sm hover:text-white hover:border-laap-gold/50 hover:bg-laap-bg-tertiary/50 transition-colors min-h-[40px]"
        >
          <Plus size={12} />
          添加 provider
        </button>

        {saved && (
          <div className="text-[10px] text-laap-text-tertiary pt-1">
            当前默认：{activeLabel}
          </div>
        )}
      </div>
    </div>
  );
}
