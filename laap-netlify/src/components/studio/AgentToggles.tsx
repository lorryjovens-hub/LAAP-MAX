import { Brain, Database, GitBranch, Wrench, Orbit, Sparkles, Network, Lightbulb, FlaskConical } from 'lucide-react';
import type { AppSettings } from '@/lib/settings';

interface AgentTogglesProps {
  settings: AppSettings;
  onChange: (settings: AppSettings) => void;
}

const CAPABILITY_ITEMS: { key: keyof AgentCapabilities; label: string; icon: typeof Brain }[] = [
  { key: 'psi', label: 'PSI 驱动', icon: Brain },
  { key: 'memory', label: '长期记忆', icon: Database },
  { key: 'causal', label: '因果推理', icon: GitBranch },
  { key: 'tools', label: '工具调用', icon: Wrench },
];

const LAAP_ITEMS: { key: keyof AgentCapabilities; label: string; icon: typeof Brain }[] = [
  { key: 'aether', label: 'Aether 编排', icon: Network },
  { key: 'rsi', label: 'True RSI', icon: Orbit },
  { key: 'qpsi', label: 'QPSI-N', icon: FlaskConical },
  { key: 'meta', label: '元认知', icon: Sparkles },
  { key: 'reasoning', label: '推理引擎', icon: Lightbulb },
];

interface AgentCapabilities {
  psi: boolean;
  memory: boolean;
  causal: boolean;
  tools: boolean;
  aether: boolean;
  rsi: boolean;
  qpsi: boolean;
  meta: boolean;
  reasoning: boolean;
}

export function AgentToggles({ settings, onChange }: AgentTogglesProps) {
  const capabilities: AgentCapabilities = {
    psi: settings.agent.psiDepth !== 'surface',
    memory: settings.memory.enabled,
    causal: settings.agent.causalReasoning,
    tools: settings.agent.toolCalling,
    aether: settings.agent.aetherOrchestration,
    rsi: settings.agent.trueRsi,
    qpsi: settings.agent.qpsiN,
    meta: settings.agent.metaCognition,
    reasoning: settings.agent.reasoningEngine,
  };

  function toggle(key: keyof AgentCapabilities) {
    const next = { ...settings };
    switch (key) {
      case 'psi':
        next.agent = { ...next.agent, psiDepth: capabilities.psi ? 'surface' : 'balanced' };
        break;
      case 'memory':
        next.memory = { ...next.memory, enabled: !capabilities.memory };
        break;
      case 'causal':
        next.agent = { ...next.agent, causalReasoning: !capabilities.causal };
        break;
      case 'tools':
        next.agent = { ...next.agent, toolCalling: !capabilities.tools };
        break;
      case 'aether':
        next.agent = { ...next.agent, aetherOrchestration: !capabilities.aether };
        break;
      case 'rsi':
        next.agent = { ...next.agent, trueRsi: !capabilities.rsi };
        break;
      case 'qpsi':
        next.agent = { ...next.agent, qpsiN: !capabilities.qpsi };
        break;
      case 'meta':
        next.agent = { ...next.agent, metaCognition: !capabilities.meta };
        break;
      case 'reasoning':
        next.agent = { ...next.agent, reasoningEngine: !capabilities.reasoning };
        break;
    }
    onChange(next);
  }

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2">
        {CAPABILITY_ITEMS.map(({ key, label, icon: Icon }) => {
          const active = capabilities[key];
          return (
            <button
              key={key}
              onClick={() => toggle(key)}
              className={`flex items-center gap-2 px-2.5 py-2 rounded-sm text-xs border transition-colors min-h-[44px] ${
                active
                  ? 'bg-laap-gold/10 border-laap-gold/40 text-laap-gold'
                  : 'bg-laap-bg-tertiary/50 border-laap-border text-laap-text-tertiary hover:text-white'
              }`}
            >
              <Icon size={13} />
              <span className="truncate">{label}</span>
            </button>
          );
        })}
      </div>

      <div className="font-mono text-[10px] text-laap-text-tertiary uppercase tracking-wider">LAAP 黑科技</div>

      <div className="grid grid-cols-2 gap-2">
        {LAAP_ITEMS.map(({ key, label, icon: Icon }) => {
          const active = capabilities[key];
          return (
            <button
              key={key}
              onClick={() => toggle(key)}
              className={`flex items-center gap-2 px-2.5 py-2 rounded-sm text-xs border transition-colors min-h-[44px] ${
                active
                  ? 'bg-laap-cyan/10 border-laap-cyan/40 text-laap-cyan'
                  : 'bg-laap-bg-tertiary/50 border-laap-border text-laap-text-tertiary hover:text-white'
              }`}
            >
              <Icon size={13} />
              <span className="truncate">{label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
