'use client';

import TerminalCard from './TerminalCard';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Memory } from '@/lib/data';

export default function MemoryPanel({ memories }: { memories: Memory[] }) {
  return (
    <TerminalCard title="MEMORY STORE" status="green">
      <ScrollArea className="h-[200px] pr-2">
        <div className="space-y-1.5">
          {memories.map((m) => (
            <div key={m.id} className="flex items-start gap-2 py-1 border-b border-[rgba(0,255,65,0.03)] last:border-0">
              <span className="text-[10px] text-[#005a0a] mt-0.5 shrink-0 font-mono">
                {m.timestamp.slice(11, 16)}
              </span>
              <Badge 
                variant="outline"
                className="text-[10px] px-1.5 py-0 border-[#1a3a1a] text-[#00ffff] bg-transparent font-mono shrink-0"
              >
                {(m.emotional_weight * 100).toFixed(0)}%
              </Badge>
              <span className="text-xs text-[#00ff41] leading-relaxed">{m.content}</span>
            </div>
          ))}
        </div>
      </ScrollArea>
      <div className="mt-2 text-[10px] text-[#005a0a] font-mono">
        {memories.length} MEMORIES · LAST 24H
      </div>
    </TerminalCard>
  );
}
