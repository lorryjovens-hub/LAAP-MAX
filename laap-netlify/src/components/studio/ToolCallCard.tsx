import { Wrench } from 'lucide-react';
import type { ToolCall } from '@/lib/chat';

interface ToolCallCardProps {
  tool: ToolCall;
}

export function ToolCallCard({ tool }: ToolCallCardProps) {
  const call = (tool.call as ToolCall | undefined) || tool;
  const name = call.name || tool.name || 'tool';
  const args = call.args || (call.arguments as Record<string, unknown> | undefined) || tool.args || {};
  const result = tool.result;

  return (
    <div className="border border-laap-border rounded-sm bg-laap-bg-secondary/30 p-3 text-xs">
      <div className="flex items-center gap-2 text-laap-gold mb-2">
        <Wrench size={12} />
        <span className="font-mono">{name}</span>
      </div>
      {Object.keys(args).length > 0 && (
        <div className="font-mono text-laap-text-tertiary mb-2">
          {JSON.stringify(args)}
        </div>
      )}
      {result !== undefined && (
        <div className="font-mono text-laap-text-secondary border-t border-laap-border/50 pt-2">
          {typeof result === 'string' ? result : JSON.stringify(result)}
        </div>
      )}
    </div>
  );
}
