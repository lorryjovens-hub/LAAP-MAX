import { useEffect, useMemo, useState } from 'react';
import { Key, Save, Eye, EyeOff, Loader2, AlertCircle, Sparkles, Check } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import type { LlmConfig, LlmProvider } from '@/lib/llmConfig';
import {
  fetchModels,
  getActiveProvider,
  isOmniRouteProvider,
  isOmniRouteBaseURL,
  guessProviderPresetKey,
  LLM_PROVIDER_PRESETS,
  SENSENOVA_MODELS,
  type LlmProviderPresetKey,
} from '@/lib/llmConfig';
import { OMNIROUTE_PRESET_MODELS } from '@/lib/omnirouteModels';

interface LLMConfigModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  config: LlmConfig;
  onChange: (config: LlmConfig) => void;
  onSave: (nextConfig?: LlmConfig) => void | Promise<void>;
  /** When true, hides the "switch provider" tab strip and only shows the active provider form. */
  hidePresets?: boolean;
  /** Optional title override (used by FirstRunModal). */
  title?: string;
  /** Optional description override (used by FirstRunModal). */
  description?: string;
}

/**
 * Modal version of the LLM config panel. Lets the user pick a provider preset
 * (OmniRoute / OpenAI / DeepSeek / Anthropic / Custom), then enter baseURL +
 * apiKey + model. When OmniRoute is selected, shows a searchable dropdown of
 * all curated free models.
 */
export function LLMConfigModal({
  open,
  onOpenChange,
  config,
  onChange,
  onSave,
  hidePresets = false,
  title = 'LLM 配置',
  description = '选择 provider 并填写 Base URL、API Key 与模型，保存后立即生效。',
}: LLMConfigModalProps) {
  const activeProvider = useMemo(() => getActiveProvider(config), [config]);

  // Determine the current preset key based on the active provider.
  const initialPresetKey: LlmProviderPresetKey = useMemo(() => {
    if (!activeProvider) return 'omniroute';
    if (isOmniRouteProvider(activeProvider)) return 'omniroute';
    const name = activeProvider.name.toLowerCase();
    if (name.includes('sensenova') || name.includes('sensetime')) return 'sensenova';
    if (name.includes('openai')) return 'openai';
    if (name.includes('deepseek')) return 'deepseek';
    if (name.includes('anthropic') || name.includes('claude')) return 'anthropic';
    return 'custom';
  }, [activeProvider]);

  const [presetKey, setPresetKey] = useState<LlmProviderPresetKey>(initialPresetKey);
  const [showKey, setShowKey] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [modelSearch, setModelSearch] = useState('');
  const [saving, setSaving] = useState(false);

  // Draft fields — kept in sync with the active provider.
  const [draftName, setDraftName] = useState('');
  const [draftBaseURL, setDraftBaseURL] = useState('');
  const [draftApiKey, setDraftApiKey] = useState('');
  const [draftModel, setDraftModel] = useState('');

  // Re-sync draft from active provider whenever modal opens or active provider changes.
  useEffect(() => {
    if (!open) return;
    setPresetKey(initialPresetKey);
    setFetchError(null);
    setGlobalError(null);
    setModelSearch('');
    if (activeProvider) {
      setDraftName(activeProvider.name);
      setDraftBaseURL(activeProvider.baseURL);
      setDraftApiKey(activeProvider.apiKey);
      setDraftModel(activeProvider.defaultModel || activeProvider.models[0] || '');
    } else {
      // No provider yet — prefill with OmniRoute defaults (the recommended first-run path).
      const preset = LLM_PROVIDER_PRESETS.omniroute;
      setDraftName(preset.name);
      setDraftBaseURL(preset.baseURL);
      setDraftApiKey(preset.apiKey);
      setDraftModel(OMNIROUTE_PRESET_MODELS[0]?.id || '');
    }
  }, [open, activeProvider, initialPresetKey]);

  function applyPreset(key: LlmProviderPresetKey) {
    setPresetKey(key);
    setFetchError(null);
    const preset = LLM_PROVIDER_PRESETS[key];
    if (key !== 'custom') {
      setDraftName(preset.name);
      setDraftBaseURL(preset.baseURL);
    }
    if (key === 'omniroute') {
      setDraftApiKey(preset.apiKey);
      if (!OMNIROUTE_PRESET_MODELS.some((m) => m.id === draftModel)) {
        setDraftModel(OMNIROUTE_PRESET_MODELS[0]?.id || '');
      }
    } else if (key === 'sensenova') {
      setDraftApiKey(preset.apiKey);
      if (!SENSENOVA_MODELS.some((m) => m.id === draftModel)) {
        setDraftModel(SENSENOVA_MODELS[0]?.id || '');
      }
    } else if (key !== 'custom') {
      // Clear the api key for paid presets so the user types their own.
      if (!draftApiKey || draftApiKey === LLM_PROVIDER_PRESETS.omniroute.apiKey || draftApiKey === LLM_PROVIDER_PRESETS.sensenova.apiKey) {
        setDraftApiKey(preset.apiKey);
      }
    }
  }

  function getModelsForDraft(): string[] {
    if (presetKey === 'sensenova') {
      return SENSENOVA_MODELS.map((m) => m.id);
    }
    if (presetKey === 'omniroute') {
      return draftModel.trim() ? [draftModel.trim()] : [];
    }
    return draftModel.trim() ? [draftModel.trim()] : [];
  }

  function commitDraftToConfig(): LlmConfig {
    if (!activeProvider) {
      // Create a new provider from the draft.
      const newProvider: LlmProvider = {
        id: crypto.randomUUID(),
        name: draftName.trim() || LLM_PROVIDER_PRESETS[presetKey].name || 'Custom',
        baseURL: draftBaseURL.trim(),
        apiKey: draftApiKey.trim(),
        models: getModelsForDraft(),
        defaultModel: draftModel.trim() || undefined,
        createdAt: new Date().toISOString(),
      };
      return {
        providers: [newProvider],
        activeProviderId: newProvider.id,
      };
    }
    const nextProviders = config.providers.map((p) =>
      p.id === activeProvider.id
        ? {
            ...p,
            name: draftName.trim() || p.name,
            baseURL: draftBaseURL.trim(),
            apiKey: draftApiKey.trim(),
            defaultModel: draftModel.trim() || p.defaultModel,
            models: getModelsForDraft(),
          }
        : p
    );
    return { ...config, providers: nextProviders };
  }

  async function handleFetchModels() {
    setFetchError(null);
    setFetching(true);
    try {
      const { models, error } = await fetchModels(draftBaseURL, draftApiKey);
      if (error) {
        setFetchError(error);
      }
      // Update draft model list (commit to config so the modal can show picked model).
      if (models.length > 0 && !models.includes(draftModel)) {
        setDraftModel(models[0]);
      }
      // Commit the fetched model list to the active provider so LLMConfigPanel
      // (in the sidebar) reflects it next time the user opens the panel.
      if (activeProvider) {
        const next = commitDraftToConfig();
        const updated = {
          ...next,
          providers: next.providers.map((p) =>
            p.id === activeProvider.id
              ? { ...p, models: models.length > 0 ? models : p.models }
              : p
          ),
        };
        onChange(updated);
      }
    } finally {
      setFetching(false);
    }
  }

  async function handleSave() {
    setGlobalError(null);
    setSaving(true);
    try {
      const next = commitDraftToConfig();
      onChange(next);
      await onSave(next);
      onOpenChange(false);
    } catch (err) {
      setGlobalError(err instanceof Error ? err.message : '保存失败');
    } finally {
      setSaving(false);
    }
  }

  const isOmniRoute = presetKey === 'omniroute' || isOmniRouteBaseURL(draftBaseURL);
  const isSenseNova = presetKey === 'sensenova';
  const filteredOmniModels = useMemo(() => {
    const q = modelSearch.trim().toLowerCase();
    if (!q) return OMNIROUTE_PRESET_MODELS;
    return OMNIROUTE_PRESET_MODELS.filter(
      (m) =>
        m.label.toLowerCase().includes(q) ||
        m.id.toLowerCase().includes(q) ||
        m.provider.toLowerCase().includes(q)
    );
  }, [modelSearch]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[560px] max-h-[90dvh] overflow-y-auto bg-laap-bg-secondary border-laap-border text-laap-text-primary p-0">
        <DialogHeader className="px-5 pt-5 pb-3">
          <DialogTitle className="flex items-center gap-2 text-base font-display text-white">
            <Key size={16} className="text-laap-gold" />
            {title}
          </DialogTitle>
          <DialogDescription className="text-xs text-laap-text-tertiary">
            {description}
          </DialogDescription>
        </DialogHeader>

        <div className="px-5 pb-5 space-y-4">
          {globalError && (
            <div className="px-3 py-2 text-xs text-laap-rose bg-laap-rose/10 border border-laap-rose/30 rounded-sm flex items-start gap-1.5">
              <AlertCircle size={13} className="mt-0.5 flex-shrink-0" />
              {globalError}
            </div>
          )}

          {!hidePresets && (
            <div>
              <label className="block text-[10px] text-laap-text-tertiary mb-1.5 font-mono uppercase tracking-wider">
                Provider 预设
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                {(Object.keys(LLM_PROVIDER_PRESETS) as LlmProviderPresetKey[]).map((key) => {
                  const preset = LLM_PROVIDER_PRESETS[key];
                  const active = presetKey === key;
                  return (
                    <button
                      key={key}
                      type="button"
                      onClick={() => applyPreset(key)}
                      className={`px-2.5 py-2 text-xs font-medium rounded-sm border transition-colors min-h-[40px] flex items-center justify-center gap-1 ${
                        active
                          ? 'border-laap-gold/60 bg-laap-gold/10 text-laap-gold'
                          : 'border-laap-border text-laap-text-secondary hover:text-white hover:border-laap-gold/40'
                      }`}
                    >
                      {active && <Check size={11} className="flex-shrink-0" />}
                      {preset.label}
                    </button>
                  );
                })}
              </div>
              <p className="mt-1.5 text-[10px] text-laap-text-tertiary">
                {LLM_PROVIDER_PRESETS[presetKey].description}
              </p>
            </div>
          )}

          <div>
            <label className="block text-[10px] text-laap-text-tertiary mb-1.5 font-mono uppercase tracking-wider">
              名称
            </label>
            <input
              type="text"
              value={draftName}
              onChange={(e) => {
                const value = e.target.value;
                setDraftName(value);
                const guessed = guessProviderPresetKey(value, draftBaseURL);
                if (guessed) {
                  const preset = LLM_PROVIDER_PRESETS[guessed];
                  setPresetKey(guessed);
                  setDraftBaseURL(preset.baseURL);
                  if (guessed === 'omniroute') {
                    setDraftApiKey(preset.apiKey);
                    setDraftModel(OMNIROUTE_PRESET_MODELS[0]?.id || '');
                  } else if (guessed === 'sensenova') {
                    setDraftApiKey(preset.apiKey);
                    setDraftModel(SENSENOVA_MODELS[0]?.id || '');
                  } else if (!draftApiKey || draftApiKey === LLM_PROVIDER_PRESETS.omniroute.apiKey || draftApiKey === LLM_PROVIDER_PRESETS.sensenova.apiKey) {
                    setDraftApiKey(preset.apiKey);
                  }
                }
              }}
              placeholder="例如 OmniRoute、OpenAI"
              className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-3 py-2 text-sm text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
            />
          </div>

          <div>
            <label className="block text-[10px] text-laap-text-tertiary mb-1.5 font-mono uppercase tracking-wider">
              Base URL
            </label>
            <input
              type="text"
              value={draftBaseURL}
              onChange={(e) => setDraftBaseURL(e.target.value)}
              placeholder="https://api.openai.com/v1"
              className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-3 py-2 text-sm text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px] font-mono text-xs"
            />
          </div>

          <div>
            <label className="block text-[10px] text-laap-text-tertiary mb-1.5 font-mono uppercase tracking-wider">
              API Key {isOmniRoute && <span className="text-laap-emerald">· OmniRoute 无需填写</span>}
            </label>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={draftApiKey}
                onChange={(e) => setDraftApiKey(e.target.value)}
                placeholder={isOmniRoute ? 'omniroute-free' : 'sk-...'}
                className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-3 py-2 pr-10 text-sm text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px] font-mono text-xs"
              />
              <button
                type="button"
                onClick={() => setShowKey((v) => !v)}
                className="absolute right-0 top-0 h-full px-3 text-laap-text-tertiary hover:text-laap-text-secondary min-w-[40px] flex items-center justify-center"
                title={showKey ? '隐藏' : '显示'}
              >
                {showKey ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-[10px] text-laap-text-tertiary mb-1.5 font-mono uppercase tracking-wider">
              模型
            </label>
            {isOmniRoute ? (
              <div className="space-y-2">
                <input
                  type="text"
                  value={modelSearch}
                  onChange={(e) => setModelSearch(e.target.value)}
                  placeholder={`搜索 ${OMNIROUTE_PRESET_MODELS.length} 个免费模型...`}
                  className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-3 py-2 text-xs text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                />
                <select
                  value={draftModel}
                  onChange={(e) => setDraftModel(e.target.value)}
                  size={6}
                  className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-xs text-laap-text-secondary focus:outline-none focus:border-laap-gold/50 min-h-[160px] max-h-[200px]"
                >
                  {filteredOmniModels.map((m) => (
                    <option key={m.id} value={m.id} title={m.id}>
                      {m.label} [{m.provider}]
                    </option>
                  ))}
                </select>
                <p className="text-[10px] text-laap-text-tertiary">
                  已选: <span className="text-laap-text-secondary font-mono break-all">{draftModel || '未选择'}</span>
                </p>
              </div>
            ) : isSenseNova ? (
              <div className="space-y-2">
                <select
                  value={draftModel}
                  onChange={(e) => setDraftModel(e.target.value)}
                  className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-3 py-2 text-sm text-laap-text-secondary focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                >
                  {SENSENOVA_MODELS.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.label}
                    </option>
                  ))}
                </select>
                <p className="text-[10px] text-laap-text-tertiary">
                  已选: <span className="text-laap-text-secondary font-mono break-all">{draftModel || '未选择'}</span>
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <input
                  type="text"
                  value={draftModel}
                  onChange={(e) => setDraftModel(e.target.value)}
                  placeholder="例如 gpt-4o-mini"
                  className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-3 py-2 text-sm text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px] font-mono text-xs"
                />
                <button
                  type="button"
                  onClick={handleFetchModels}
                  disabled={fetching || !draftBaseURL.trim()}
                  className="w-full flex items-center justify-center gap-1.5 py-2 text-xs font-medium text-laap-text-secondary border border-laap-border rounded-sm hover:text-white hover:border-laap-gold/50 disabled:opacity-50 transition-colors min-h-[36px]"
                >
                  {fetching ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
                  {fetching ? '获取模型列表...' : '从 /v1/models 拉取模型列表'}
                </button>
              </div>
            )}
            {fetchError && (
              <div className="mt-2 text-[10px] text-laap-rose flex items-start gap-1">
                <AlertCircle size={11} className="mt-0.5 flex-shrink-0" />
                {fetchError}
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 pt-1">
            <button
              type="button"
              onClick={handleSave}
              disabled={saving || !draftBaseURL.trim() || (!isOmniRoute && !draftModel.trim())}
              className="flex-1 flex items-center justify-center gap-1.5 py-2.5 text-sm font-medium text-laap-bg-primary bg-laap-gold rounded-sm hover:bg-laap-gold-light disabled:opacity-50 disabled:cursor-not-allowed transition-colors min-h-[40px]"
            >
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
              {saving ? '保存中...' : '保存'}
            </button>
            <button
              type="button"
              onClick={() => onOpenChange(false)}
              className="px-4 py-2.5 text-sm font-medium text-laap-text-secondary border border-laap-border rounded-sm hover:text-white hover:border-laap-gold/50 transition-colors min-h-[40px]"
            >
              取消
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
