import { useState } from 'react';
import { Save, Plus, Trash2, Check, ChevronDown, ChevronUp, Eye, EyeOff, Volume2 } from 'lucide-react';
import type { TtsConfig, TtsProvider } from '@/lib/audioConfig';
import {
  TTS_PROVIDER_PRESETS,
  MICROSOFT_TTS_VOICES,
  OPENAI_TTS_VOICES,
  ELEVENLABS_TTS_VOICES,
  guessTtsPresetKey,
  buildDefaultTtsProvider,
} from '@/lib/audioConfig';

interface TTSConfigPanelProps {
  config: TtsConfig;
  saved?: TtsConfig | null;
  onChange: (config: TtsConfig) => void;
  onSave: (nextConfig?: TtsConfig) => void | Promise<void>;
}

const EMPTY_PROVIDER: Omit<TtsProvider, 'id' | 'createdAt'> = {
  provider: '',
  name: '',
  baseURL: '',
  apiKey: '',
  model: '',
  voice: '',
  extraCreds: {},
};

export function TTSConfigPanel({ config, saved, onChange, onSave }: TTSConfigPanelProps) {
  const [showKeyMap, setShowKeyMap] = useState<Record<string, boolean>>({});
  const [expandedMap, setExpandedMap] = useState<Record<string, boolean>>({});

  function updateConfig(next: TtsConfig) {
    onChange(next);
  }

  function ensureExpanded(id: string) {
    setExpandedMap((prev) => ({ ...prev, [id]: true }));
  }

  function addProvider() {
    const id = crypto.randomUUID();
    const provider: TtsProvider = {
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

  function updateProviderField(id: string, field: keyof Omit<TtsProvider, 'id' | 'createdAt'>, value: string) {
    const nextProviders = config.providers.map((p) =>
      p.id === id ? { ...p, [field]: value } : p
    );
    updateConfig({ ...config, providers: nextProviders });
  }

  function updateExtraCred(id: string, key: string, value: string) {
    const nextProviders = config.providers.map((p) =>
      p.id === id ? { ...p, extraCreds: { ...p.extraCreds, [key]: value } } : p
    );
    updateConfig({ ...config, providers: nextProviders });
  }

  function handleNameChange(id: string, value: string) {
    updateProviderField(id, 'name', value);
    const guessed = guessTtsPresetKey(value);
    if (guessed) {
      const preset = TTS_PROVIDER_PRESETS[guessed];
      updateProviderField(id, 'provider', preset.provider);
      updateProviderField(id, 'baseURL', preset.baseURL);
      if (!config.providers.find((p) => p.id === id)?.model) {
        updateProviderField(id, 'model', preset.defaultModel);
      }
      if (!config.providers.find((p) => p.id === id)?.voice) {
        updateProviderField(id, 'voice', preset.defaultVoice);
      }
      // Merge extra creds
      const nextProviders = config.providers.map((p) =>
        p.id === id
          ? { ...p, extraCreds: { ...p.extraCreds, ...preset.extraCreds } }
          : p
      );
      updateConfig({ ...config, providers: nextProviders });
    }
  }

  async function handleSaveProvider(id: string) {
    const nextConfig = { ...config };
    await onSave(nextConfig);
  }

  function getVoicesForProvider(provider: TtsProvider): { value: string; label: string }[] {
    switch (provider.provider) {
      case 'microsoft':
        return MICROSOFT_TTS_VOICES;
      case 'openai':
        return OPENAI_TTS_VOICES;
      case 'elevenlabs':
        return ELEVENLABS_TTS_VOICES;
      default:
        return [];
    }
  }

  const activeLabel = (() => {
    const active = config.providers.find((p) => p.id === config.activeProviderId);
    if (!active) return '未配置';
    return `${active.name || '未命名'} / ${active.voice || active.model || '默认音色'}`;
  })();

  return (
    <div className="space-y-3">
      <div className="font-mono text-[10px] text-laap-text-tertiary uppercase tracking-wider flex items-center gap-1.5">
        <Volume2 size={11} />
        TTS 语音合成配置
      </div>

      <div className="space-y-2 text-xs max-h-[55dvh] md:max-h-none pb-6 pr-1 scroll-smooth">
        {config.providers.length === 0 && (
          <div className="text-[10px] text-laap-text-tertiary px-1 py-2 text-center border border-dashed border-laap-border rounded-sm">
            暂无 TTS provider，点击下方按钮添加
          </div>
        )}

        {config.providers.map((provider) => {
          const expanded = expandedMap[provider.id] ?? true;
          const showKey = showKeyMap[provider.id] ?? false;
          const isActive = config.activeProviderId === provider.id;
          const voices = getVoicesForProvider(provider);

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
                  {/* Provider name */}
                  <div>
                    <label className="block text-laap-text-tertiary mb-1">名称</label>
                    <input
                      type="text"
                      value={provider.name}
                      onChange={(e) => handleNameChange(provider.id, e.target.value)}
                      placeholder="例如 Microsoft Edge TTS、OpenAI TTS"
                      className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                    />
                  </div>

                  {/* Base URL (only for providers that need it) */}
                  {provider.provider !== 'microsoft' && provider.provider !== 'local' && (
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
                  )}

                  {/* API Key (hidden for Microsoft free provider) */}
                  {provider.provider !== 'microsoft' && (
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
                  )}

                  {/* Model (OpenAI, MiniMax) */}
                  {(provider.provider === 'openai' || provider.provider === 'minimax' || provider.provider === 'elevenlabs') && (
                    <div>
                      <label className="block text-laap-text-tertiary mb-1">模型</label>
                      <input
                        type="text"
                        value={provider.model}
                        onChange={(e) => updateProviderField(provider.id, 'model', e.target.value)}
                        placeholder="tts-1 / eleven_multilingual_v2 / speech-01-turbo"
                        className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                      />
                    </div>
                  )}

                  {/* Voice selection */}
                  {voices.length > 0 ? (
                    <div>
                      <label className="block text-laap-text-tertiary mb-1">音色</label>
                      <select
                        value={provider.voice || ''}
                        onChange={(e) => updateProviderField(provider.id, 'voice', e.target.value)}
                        className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                      >
                        <option value="">选择音色</option>
                        {voices.map((v) => (
                          <option key={v.value} value={v.value}>
                            {v.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  ) : (
                    <div>
                      <label className="block text-laap-text-tertiary mb-1">音色 / Voice ID</label>
                      <input
                        type="text"
                        value={provider.voice}
                        onChange={(e) => updateProviderField(provider.id, 'voice', e.target.value)}
                        placeholder="音色名称或 ID"
                        className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                      />
                    </div>
                  )}

                  {/* Provider-specific extra credentials */}
                  {provider.provider === 'doubao' && (
                    <div>
                      <label className="block text-laap-text-tertiary mb-1">Resource ID</label>
                      <input
                        type="text"
                        value={provider.extraCreds.doubaoResourceId || ''}
                        onChange={(e) => updateExtraCred(provider.id, 'doubaoResourceId', e.target.value)}
                        placeholder="火山方舟 Resource ID"
                        className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                      />
                    </div>
                  )}

                  {provider.provider === 'minimax' && (
                    <div>
                      <label className="block text-laap-text-tertiary mb-1">Group ID</label>
                      <input
                        type="text"
                        value={provider.extraCreds.minimaxGroupId || ''}
                        onChange={(e) => updateExtraCred(provider.id, 'minimaxGroupId', e.target.value)}
                        placeholder="MiniMax Group ID"
                        className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                      />
                    </div>
                  )}

                  {provider.provider === 'volcano' && (
                    <>
                      <div>
                        <label className="block text-laap-text-tertiary mb-1">App ID</label>
                        <input
                          type="text"
                          value={provider.extraCreds.volcanoAppId || ''}
                          onChange={(e) => updateExtraCred(provider.id, 'volcanoAppId', e.target.value)}
                          placeholder="火山引擎 App ID"
                          className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                        />
                      </div>
                      <div>
                        <label className="block text-laap-text-tertiary mb-1">Token</label>
                        <input
                          type="password"
                          value={provider.extraCreds.volcanoToken || ''}
                          onChange={(e) => updateExtraCred(provider.id, 'volcanoToken', e.target.value)}
                          placeholder="火山引擎 Token"
                          className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                        />
                      </div>
                    </>
                  )}

                  <div className="flex items-center gap-2 pt-1">
                    <button
                      type="button"
                      onClick={() => handleSaveProvider(provider.id)}
                      className="flex-1 flex items-center justify-center gap-1 py-2 text-xs font-medium text-laap-bg-primary bg-laap-gold/90 rounded-sm hover:bg-laap-gold disabled:opacity-60 transition-colors min-h-[36px]"
                    >
                      <Save size={12} />
                      保存
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
          添加 TTS provider
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