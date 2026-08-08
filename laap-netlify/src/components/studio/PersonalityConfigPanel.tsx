import { useState } from 'react';
import { Sparkles, Save } from 'lucide-react';
import type { PersonalityConfig } from '@/lib/personality';

interface PersonalityConfigPanelProps {
  config: PersonalityConfig;
  onChange: (config: PersonalityConfig) => void;
  onSave: () => void | Promise<void>;
}

export function PersonalityConfigPanel({
  config,
  onChange,
  onSave,
}: PersonalityConfigPanelProps) {
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      await onSave();
    } finally {
      setSaving(false);
    }
  }

  function update<K extends keyof PersonalityConfig>(key: K, value: PersonalityConfig[K]) {
    onChange({ ...config, [key]: value });
  }

  return (
    <div className="space-y-3">
      <div className="font-mono text-[10px] text-laap-text-tertiary uppercase tracking-wider flex items-center gap-1.5">
        <Sparkles size={11} />
        性格与记忆
      </div>

      <div className="space-y-2 text-xs">
        <div>
          <label className="block text-laap-text-tertiary mb-1">性格特质</label>
          <textarea
            value={config.traits}
            onChange={(e) => update('traits', e.target.value)}
            placeholder="例如：温柔、好奇、幽默、略带诗意"
            rows={2}
            className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 resize-none min-h-[60px]"
          />
        </div>

        <div>
          <label className="block text-laap-text-tertiary mb-1">说话风格</label>
          <textarea
            value={config.tone}
            onChange={(e) => update('tone', e.target.value)}
            placeholder="例如：像老朋友一样温暖、真诚"
            rows={2}
            className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 resize-none min-h-[60px]"
          />
        </div>

        <div>
          <label className="block text-laap-text-tertiary mb-1">LAAP 名称</label>
          <input
            type="text"
            value={config.agentName ?? ''}
            onChange={(e) => update('agentName', e.target.value)}
            placeholder="给你的 LAAP 起个名字"
            className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
          />
        </div>

        <div>
          <label className="block text-laap-text-tertiary mb-1">身份与经历</label>
          <textarea
            value={config.backstory}
            onChange={(e) => update('backstory', e.target.value)}
            placeholder="简短描述这个 LAAP 数字生命体的身份背景"
            rows={3}
            className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 resize-none min-h-[80px]"
          />
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full flex items-center justify-center gap-1.5 py-2.5 mt-1 text-xs font-medium text-laap-bg-primary bg-laap-gold/90 rounded-sm hover:bg-laap-gold disabled:opacity-60 transition-colors min-h-[40px]"
        >
          <Save size={12} />
          {saving ? '保存中…' : '保存性格'}
        </button>
      </div>
    </div>
  );
}
