import { useState } from 'react';
import { Save, Plus, Trash2, Check, ChevronDown, ChevronUp, Eye, EyeOff, Mic } from 'lucide-react';
import type { AsrConfig, AsrProvider } from '@/lib/audioConfig';
import {
  ASR_PROVIDER_PRESETS,
  guessAsrPresetKey,
  buildDefaultAsrProvider,
} from '@/lib/audioConfig';

interface ASRConfigPanelProps {
  config: AsrConfig;
  saved?: AsrConfig | null;
  onChange: (config: AsrConfig) => void;
  onSave: (nextConfig?: AsrConfig) => void | Promise<void>;
}

const EMPTY_PROVIDER: Omit<AsrProvider, 'id' | 'createdAt'> = {
  provider: '',
  name: '',
  baseURL: '',
  apiKey: '',
  model: '',
  language: 'zh-CN',
  extraCreds: {},
};

export function ASRConfigPanel({ config, saved, onChange, onSave }: ASRConfigPanelProps) {
  const [showKeyMap, setShowKeyMap] = useState<Record<string, boolean>>({});
  const [expandedMap, setExpandedMap] = useState<Record<string, boolean>>({});

  function updateConfig(next: AsrConfig) {
    onChange(next);
  }

  function ensureExpanded(id: string) {
    setExpandedMap((prev) => ({ ...prev, [id]: true }));
  }

  function addProvider() {
    const id = crypto.randomUUID();
    const provider: AsrProvider = {
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

  function updateProviderField(id: string, field: keyof Omit<AsrProvider, 'id' | 'createdAt'>, value: string) {
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
    const guessed = guessAsrPresetKey(value);
    if (guessed) {
      const preset = ASR_PROVIDER_PRESETS[guessed];
      updateProviderField(id, 'provider', preset.provider);
      updateProviderField(id, 'baseURL', preset.baseURL);
      if (!config.providers.find((p) => p.id === id)?.model) {
        updateProviderField(id, 'model', preset.defaultModel);
      }
      if (!config.providers.find((p) => p.id === id)?.language) {
        updateProviderField(id, 'language', preset.defaultLanguage);
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

  const activeLabel = (() => {
    const active = config.providers.find((p) => p.id === config.activeProviderId);
    if (!active) return '未配置';
    return `${active.name || '未命名'} / ${active.model || '默认模型'}`;
  })();

  const LANGUAGES = [
    { value: 'zh-CN', label: '中文（普通话）' },
    { value: 'zh-TW', label: '中文（繁体）' },
    { value: 'en-US', label: 'English' },
    { value: 'ja-JP', label: '日本語' },
    { value: 'ko-KR', label: '한국어' },
  ];

  return (
    <div className="space-y-3">
      <div className="font-mono text-[10px] text-laap-text-tertiary uppercase tracking-wider flex items-center gap-1.5">
        <Mic size={11} />
        ASR 语音识别配置
      </div>

      <div className="space-y-2 text-xs max-h-[55dvh] md:max-h-none pb-6 pr-1 scroll-smooth">
        {config.providers.length === 0 && (
          <div className="text-[10px] text-laap-text-tertiary px-1 py-2 text-center border border-dashed border-laap-border rounded-sm">
            暂无 ASR provider，点击下方按钮添加
          </div>
        )}

        {config.providers.map((provider) => {
          const expanded = expandedMap[provider.id] ?? true;
          const showKey = showKeyMap[provider.id] ?? false;
          const isActive = config.activeProviderId === provider.id;

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
                      placeholder="例如 阿里云 ASR、本地 ASR"
                      className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                    />
                  </div>

                  {/* API Key (hidden for local provider) */}
                  {provider.provider !== 'local' && (
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

                  {/* Model (Aliyun) */}
                  {provider.provider === 'aliyun' && (
                    <div>
                      <label className="block text-laap-text-tertiary mb-1">模型</label>
                      <input
                        type="text"
                        value={provider.model}
                        onChange={(e) => updateProviderField(provider.id, 'model', e.target.value)}
                        placeholder="paraformer-v1"
                        className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                      />
                    </div>
                  )}

                  {/* Language */}
                  <div>
                    <label className="block text-laap-text-tertiary mb-1">语言</label>
                    <select
                      value={provider.language || 'zh-CN'}
                      onChange={(e) => updateProviderField(provider.id, 'language', e.target.value)}
                      className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                    >
                      {LANGUAGES.map((lang) => (
                        <option key={lang.value} value={lang.value}>
                          {lang.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Provider-specific extra credentials */}
                  {provider.provider === 'xunfei' && (
                    <div>
                      <label className="block text-laap-text-tertiary mb-1">讯飞 App ID</label>
                      <input
                        type="text"
                        value={provider.extraCreds.xunfeiAppId || ''}
                        onChange={(e) => updateExtraCred(provider.id, 'xunfeiAppId', e.target.value)}
                        placeholder="科大讯飞 App ID"
                        className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                      />
                    </div>
                  )}

                  {provider.provider === 'tencent' && (
                    <>
                      <div>
                        <label className="block text-laap-text-tertiary mb-1">Secret ID</label>
                        <input
                          type="text"
                          value={provider.extraCreds.tencentSecretId || ''}
                          onChange={(e) => updateExtraCred(provider.id, 'tencentSecretId', e.target.value)}
                          placeholder="腾讯云 Secret ID"
                          className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                        />
                      </div>
                      <div>
                        <label className="block text-laap-text-tertiary mb-1">Secret Key</label>
                        <input
                          type="password"
                          value={provider.extraCreds.tencentSecretKey || ''}
                          onChange={(e) => updateExtraCred(provider.id, 'tencentSecretKey', e.target.value)}
                          placeholder="腾讯云 Secret Key"
                          className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                        />
                      </div>
                      <div>
                        <label className="block text-laap-text-tertiary mb-1">App ID</label>
                        <input
                          type="text"
                          value={provider.extraCreds.tencentAppId || ''}
                          onChange={(e) => updateExtraCred(provider.id, 'tencentAppId', e.target.value)}
                          placeholder="腾讯云 App ID"
                          className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                        />
                      </div>
                    </>
                  )}

                  {provider.provider === 'volcengine' && (
                    <>
                      <div>
                        <label className="block text-laap-text-tertiary mb-1">App Key</label>
                        <input
                          type="text"
                          value={provider.extraCreds.volcAsrAppKey || ''}
                          onChange={(e) => updateExtraCred(provider.id, 'volcAsrAppKey', e.target.value)}
                          placeholder="火山引擎 App Key"
                          className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                        />
                      </div>
                      <div>
                        <label className="block text-laap-text-tertiary mb-1">Access Key</label>
                        <input
                          type="text"
                          value={provider.extraCreds.volcAsrAccessKey || ''}
                          onChange={(e) => updateExtraCred(provider.id, 'volcAsrAccessKey', e.target.value)}
                          placeholder="火山引擎 Access Key"
                          className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                        />
                      </div>
                      <div>
                        <label className="block text-laap-text-tertiary mb-1">Resource ID</label>
                        <input
                          type="text"
                          value={provider.extraCreds.volcAsrResourceId || ''}
                          onChange={(e) => updateExtraCred(provider.id, 'volcAsrResourceId', e.target.value)}
                          placeholder="火山引擎 Resource ID"
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
          添加 ASR provider
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