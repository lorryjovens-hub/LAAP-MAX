'use client';

import TerminalCard from './TerminalCard';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Desire } from '@/lib/data';

export default function DesirePanel({ desires }: { desires: Desire[] }) {
  return (
    <TerminalCard title="DESIRE ENGINE" status="green">
      <div className="space-y-3">
        {desires.map((d) => (
          <div key={d.name}>
            <div className="flex justify-between mb-1.5">
              <span className="text-xs text-[#00ff41] uppercase tracking-wider font-mono">{d.name}</span>
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-[#1a3a1a] text-[#005a0a] bg-transparent font-mono">
                {d.category}
              </Badge>
            </div>
            <Progress 
              value={d.intensity * 100} 
              className={`h-1 bg-[rgba(0,255,65,0.1)] rounded-sm [&>div]:rounded-sm [&>div]:${d.intensity === 1.0 
                ? 'bg-[#00ff41] shadow-[0_0_4px_#00ff41]' 
                : 'bg-[#00ffff] shadow-[0_0_4px_#00ffff]'}`}
            />
          </div>
        ))}
      </div>
    </TerminalCard>
  );
}
