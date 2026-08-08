import { useState, useMemo } from 'react';
import { ChevronDown, ChevronUp, Wrench, Sparkles, BrainCircuit, Terminal } from 'lucide-react';
import type { ReasoningStep, ToolCall } from '@/lib/chat';
import { cn } from '@/lib/utils';

interface ThinkingProcessProps {
  steps: ReasoningStep[];
  toolCalls: ToolCall[];
  loading?: boolean;
  agentName?: string;
}

const STAGES = [
  { key: 'perceive', label: '感知', desc: '读取输入与上下文' },
  { key: 'analyze', label: '分析', desc: '拆解问题与调用工具' },
  { key: 'deduce', label: '推演', desc: '因果推理与世界建模' },
  { key: 'respond', label: '回应', desc: '生成最终回答' },
];

export function ThinkingProcess({ steps, toolCalls, loading = false, agentName = 'LAAP' }: ThinkingProcessProps) {
  const [expanded, setExpanded] = useState(false);

  const activeStage = useMemo(() => {
    if (!loading) return 'respond';
    if (steps.length > 0) return 'deduce';
    if (toolCalls.length > 0) return 'analyze';
    return 'perceive';
  }, [loading, steps.length, toolCalls.length]);

  const activeIndex = STAGES.findIndex((s) => s.key === activeStage);

  function formatArgs(args?: Record<string, unknown>): string {
    if (!args || Object.keys(args).length === 0) return '';
    const entries = Object.entries(args).slice(0, 3);
    const summary = entries.map(([k, v]) => `${k}=${truncate(String(v), 24)}`).join(', ');
    return summary;
  }

  function truncate(value: string, max: number): string {
    if (value.length <= max) return value;
    return `${value.slice(0, max)}…`;
  }

  const hasContent = steps.length > 0 || toolCalls.length > 0;

  return (
    <div className="border border-laap-border rounded-sm overflow-hidden bg-laap-bg-secondary/30">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-3 py-2 text-xs hover:bg-laap-bg-tertiary/30 transition-colors"
      >
        <span className="flex items-center gap-2">
          <span className={cn('flex items-center justify-center w-5 h-5 rounded-full border', stageBadgeClass(activeStage, loading))}>
            {loading ? (
              <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
            ) : (
              <Sparkles size={10} />
            )}
          </span>
          <span className="text-laap-text-secondary">
            {loading ? `${agentName} 正在思考` : '思考过程'}
          </span>
          <span className="text-laap-text-tertiary">
            {toolCalls.length > 0 && `${toolCalls.length} 个工具`}
            {toolCalls.length > 0 && steps.length > 0 && ' · '}
            {steps.length > 0 && `${steps.length} 步推理`}
          </span>
        </span>
        {expanded ? <ChevronUp size={14} className="text-laap-text-tertiary" /> : <ChevronDown size={14} className="text-laap-text-tertiary" />}
      </button>

      <div className="px-3 pb-2 space-y-2">
        <StageIndicator activeIndex={activeIndex} loading={loading} />

        {expanded && (
          <div className="border-t border-laap-border/50 pt-2 space-y-2 animate-in fade-in slide-in-from-top-1 duration-200">
            {toolCalls.length > 0 && (
              <div className="space-y-1.5">
                <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-laap-text-tertiary">
                  <Wrench size={10} />
                  工具调用
                </div>
                {toolCalls.map((tool, idx) => {
                  const name = tool.name || 'tool';
                  const args = tool.args || (tool.arguments as Record<string, unknown> | undefined);
                  return (
                    <div
                      key={idx}
                      className="flex items-start gap-2 px-2 py-1.5 rounded-sm bg-laap-bg-tertiary/40 border border-laap-border/50 text-xs"
                    >
                      <Terminal size={12} className="text-laap-gold mt-0.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="font-mono text-laap-gold truncate">{name}</div>
                        {args && Object.keys(args).length > 0 && (
                          <div className="font-mono text-laap-text-tertiary truncate">{formatArgs(args)}</div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {steps.length > 0 && (
              <div className="space-y-1.5">
                <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-laap-text-tertiary">
                  <BrainCircuit size={10} />
                  推理步骤
                </div>
                {steps.map((step, idx) => (
                  <div
                    key={idx}
                    className="px-2 py-1.5 rounded-sm bg-laap-bg-tertiary/40 border border-laap-border/50 text-xs text-laap-text-secondary leading-relaxed"
                  >
                    {typeof step.step === 'string' && (
                      <div className="text-laap-cyan mb-0.5">{step.step}</div>
                    )}
                    {typeof step.content === 'string' ? (
                      <div className="font-mono text-laap-text-tertiary">{step.content}</div>
                    ) : (
                      <div className="font-mono text-laap-text-tertiary">{JSON.stringify(step)}</div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {!hasContent && loading && (
              <div className="flex items-center gap-2 text-xs text-laap-text-tertiary py-1">
                <span className="w-1.5 h-1.5 rounded-full bg-laap-gold animate-pulse" />
                等待首个中间事件…
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function StageIndicator({ activeIndex, loading }: { activeIndex: number; loading: boolean }) {
  return (
    <div className="flex items-center justify-between py-1.5">
      {STAGES.map((stage, idx) => {
        const isCompleted = idx < activeIndex;
        const isActive = idx === activeIndex;
        return (
          <div key={stage.key} className="flex-1 flex items-center">
            <div className="flex flex-col items-center gap-1 w-full">
              <div
                className={cn(
                  'w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-medium border transition-colors duration-300',
                  isActive
                    ? 'border-laap-gold text-laap-gold bg-laap-gold/10 animate-pulse-glow'
                    : isCompleted
                      ? 'border-laap-emerald text-laap-emerald bg-laap-emerald/10'
                      : 'border-laap-border text-laap-text-tertiary bg-laap-bg-tertiary/30'
                )}
              >
                {idx + 1}
              </div>
              <div className="text-center">
                <div
                  className={cn(
                    'text-[10px] transition-colors duration-300',
                    isActive ? 'text-laap-gold' : isCompleted ? 'text-laap-emerald' : 'text-laap-text-tertiary'
                  )}
                >
                  {stage.label}
                  {isActive && loading && '中'}
                </div>
                <div className="text-[9px] text-laap-text-tertiary hidden sm:block">{stage.desc}</div>
              </div>
            </div>
            {idx < STAGES.length - 1 && (
              <div className="flex-1 h-px mx-1 bg-laap-border relative overflow-hidden">
                <div
                  className={cn(
                    'absolute inset-y-0 left-0 bg-laap-gold transition-all duration-500',
                    isCompleted ? 'w-full' : 'w-0'
                  )}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function stageBadgeClass(stage: string, loading: boolean): string {
  if (stage === 'respond' && !loading) return 'border-laap-emerald text-laap-emerald bg-laap-emerald/10';
  return 'border-laap-gold text-laap-gold bg-laap-gold/10';
}
