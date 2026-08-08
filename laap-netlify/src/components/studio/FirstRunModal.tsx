import { useEffect, useState } from 'react';
import { Sparkles, Rocket, SkipForward } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { LLMConfigModal } from './LLMConfigModal';
import type { LlmConfig } from '@/lib/llmConfig';
import { buildOmniRouteProvider, buildSenseNovaProvider, markLlmConfigured } from '@/lib/llmConfig';

interface FirstRunModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  config: LlmConfig;
  onChange: (config: LlmConfig) => void;
  onSave: (nextConfig?: LlmConfig) => void | Promise<void>;
}

/**
 * First-run welcome modal. Shows on the user's first visit to LAAP Studio
 * (controlled by the `laap_llm_configured` localStorage flag in StudioPage).
 *
 * If the user has no provider configured, preseeds an OmniRoute provider so the
 * "开始使用" button just works (zero-config). If they prefer their own provider,
 * they can click "配置 LLM" to open the full LLMConfigModal.
 */
export function FirstRunModal({ open, onOpenChange, config, onChange, onSave }: FirstRunModalProps) {
  const [showFullConfig, setShowFullConfig] = useState(false);

  useEffect(() => {
    if (!open) {
      setShowFullConfig(false);
    }
  }, [open]);

  async function handleQuickStart() {
    // Seed an OmniRoute provider if the user has none.
    let next = config;
    if (config.providers.length === 0) {
      const provider = buildOmniRouteProvider();
      next = { providers: [provider], activeProviderId: provider.id };
      onChange(next);
    }
    await onSave(next);
    markLlmConfigured();
    onOpenChange(false);
  }

  async function handleSenseNovaQuickStart() {
    let next = config;
    if (config.providers.length === 0) {
      const provider = buildSenseNovaProvider();
      next = { providers: [provider], activeProviderId: provider.id };
      onChange(next);
    }
    await onSave(next);
    markLlmConfigured();
    onOpenChange(false);
  }

  function handleSkip() {
    markLlmConfigured();
    onOpenChange(false);
  }

  async function handleSaveAndClose(nextConfig?: LlmConfig) {
    await onSave(nextConfig);
    markLlmConfigured();
    setShowFullConfig(false);
    onOpenChange(false);
  }

  // When the user wants full control, swap to the LLMConfigModal layout
  // (still rendered inside the same Dialog).
  if (showFullConfig) {
    return (
      <LLMConfigModal
        open={open}
        onOpenChange={(o) => {
          if (!o) {
            setShowFullConfig(false);
          }
        }}
        config={config}
        onChange={onChange}
        onSave={handleSaveAndClose}
        title="配置 LLM Provider"
        description="选择 OmniRoute 走免费模型，或填写自己的 OpenAI / DeepSeek / Anthropic 端点。"
      />
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px] bg-laap-bg-secondary border-laap-border text-laap-text-primary p-0">
        <DialogHeader className="px-6 pt-6 pb-3">
          <DialogTitle className="flex items-center gap-2 text-lg font-display text-white">
            <Sparkles size={18} className="text-laap-gold" />
            欢迎使用 LAAP Studio
          </DialogTitle>
          <DialogDescription className="text-xs text-laap-text-tertiary pt-1">
            首次使用需要配置一个 LLM Provider。推荐使用内置的 OmniRoute 网关 —— 122+ 免费模型，无需 API Key。
          </DialogDescription>
        </DialogHeader>

        <div className="px-6 pb-6 space-y-4">
          <div className="rounded-sm border border-laap-gold/30 bg-laap-gold/5 p-3 space-y-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-laap-gold/20 border border-laap-gold/40 flex items-center justify-center flex-shrink-0">
                <Rocket size={14} className="text-laap-gold" />
              </div>
              <div className="text-sm font-medium text-white">OmniRoute 免费网关</div>
            </div>
            <ul className="text-xs text-laap-text-secondary space-y-1 pl-1">
              <li>· 122+ 免费模型（Claude / GPT / Gemini / DeepSeek / Qwen 等）</li>
              <li>· 无需 API Key，开箱即用</li>
              <li>· 需先启动本地 OmniRoute 网关 (D:\LAAP\scripts\start_omniroute.cmd)</li>
            </ul>
          </div>

          <div className="rounded-sm border border-laap-cyan/30 bg-laap-cyan/5 p-3 space-y-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-laap-cyan/20 border border-laap-cyan/40 flex items-center justify-center flex-shrink-0">
                <Sparkles size={14} className="text-laap-cyan" />
              </div>
              <div className="text-sm font-medium text-white">SenseNova 免费模型</div>
            </div>
            <ul className="text-xs text-laap-text-secondary space-y-1 pl-1">
              <li>· sensenova-6.7-flash-lite / deepseek-v4-flash / glm5.2 / sensenova-u1-fast</li>
              <li>· 内置 API Key，无需手动填写</li>
              <li>· 云端直接访问，无需本地 OmniRoute</li>
            </ul>
          </div>

          <div className="space-y-2">
            <button
              type="button"
              onClick={handleSenseNovaQuickStart}
              className="w-full flex items-center justify-center gap-2 py-3 text-sm font-medium text-laap-bg-primary bg-laap-cyan rounded-sm hover:bg-laap-cyan/80 transition-colors min-h-[44px]"
            >
              <Sparkles size={14} />
              一键启用 SenseNova 免费模型
            </button>
            <button
              type="button"
              onClick={handleQuickStart}
              className="w-full flex items-center justify-center gap-2 py-2.5 text-sm font-medium text-laap-text-secondary border border-laap-border rounded-sm hover:text-white hover:border-laap-gold/50 transition-colors min-h-[40px]"
            >
              <Rocket size={13} />
              使用 OmniRoute 免费网关
            </button>
            <button
              type="button"
              onClick={() => setShowFullConfig(true)}
              className="w-full flex items-center justify-center gap-2 py-2.5 text-sm font-medium text-laap-text-secondary border border-laap-border rounded-sm hover:text-white hover:border-laap-gold/50 transition-colors min-h-[40px]"
            >
              <Sparkles size={13} />
              配置自己的 LLM Provider
            </button>
            <button
              type="button"
              onClick={handleSkip}
              className="w-full flex items-center justify-center gap-1.5 py-2 text-xs text-laap-text-tertiary hover:text-laap-text-secondary transition-colors min-h-[36px]"
            >
              <SkipForward size={11} />
              稍后配置（仍可使用 LAAP 默认模型）
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
