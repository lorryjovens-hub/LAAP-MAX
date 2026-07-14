'use client';

import TerminalCard from './TerminalCard';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import { PSIState } from '@/lib/data';

function Gauge({ label, value, color = 'green', suffix = '' }: { label: string; value: number; color?: 'green' | 'cyan' | 'magenta'; suffix?: string }) {
  const colorMap = {
    green: 'bg-[#00ff41]',
    cyan: 'bg-[#00ffff]',
    magenta: 'bg-[#ff00ff]',
  };
  const glowMap = {
    green: 'shadow-[0_0_4px_#00ff41]',
    cyan: 'shadow-[0_0_4px_#00ffff]',
    magenta: 'shadow-[0_0_4px_#ff00ff]',
  };
  
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-xs text-[#008f11]">{label}</span>
        <span className={cn('text-xs', color === 'cyan' ? 'text-[#00ffff]' : color === 'magenta' ? 'text-[#ff00ff]' : 'text-[#00ff41]')}>
          {suffix}{value.toFixed(suffix ? 0 : 2)}
        </span>
      </div>
      <Progress 
        value={value * 100} 
        className={`h-1 bg-[rgba(0,255,65,0.1)] rounded-sm [&>div]:rounded-sm [&>div]:${cn(colorMap[color], glowMap[color])}`}
      />
    </div>
  );
}

export default function PSIMonitor({ psi }: { psi: PSIState }) {
  return (
    <TerminalCard title="PSI CORE" status="green">
      <div className="grid grid-cols-2 gap-x-8 gap-y-4">
        <Gauge label="EMOTION" value={psi.emotion_intensity} suffix="%" color="cyan" />
        <Gauge label="SELF" value={psi.self_presence} color="magenta" />
        <Gauge label="OPENNESS" value={psi.openness} />
        <Gauge label="CONSCI." value={psi.conscientiousness} />
      </div>
      <div className="mt-4 pt-3 border-t border-[#1a3a1a] flex justify-between text-xs font-mono">
        <span>
          <span className="text-[#005a0a]">ATTN:</span>{' '}
          <span className="text-[#00ffff]">{psi.attention.toUpperCase()}</span>
        </span>
        <span>
          <span className="text-[#005a0a]">EMOTION:</span>{' '}
          <span className="text-[#00ff41]">{psi.emotion.toUpperCase()}</span>
        </span>
        <span>
          <span className="text-[#005a0a]">PHASE:</span>{' '}
          <span className="text-[#00ff41]">{psi.psi_cycle_phase}</span>
        </span>
      </div>
    </TerminalCard>
  );
}
