'use client';

import TerminalCard from './TerminalCard';
import { Goal } from '@/lib/data';

const priorityColor = (p: string) => {
  switch (p) {
    case 'HIGH': return 'var(--danger)';
    case 'MEDIUM': return 'var(--warning)';
    default: return 'var(--text-muted)';
  }
};

export default function GoalPanel({ goals }: { goals: Goal[] }) {
  return (
    <TerminalCard title="GOAL ENGINE" status="green">
      <div className="space-y-2">
        {goals.map((g, i) => (
          <div key={g.id} className="flex items-center gap-3 py-1 border-b border-[rgba(0,255,65,0.03)] last:border-0">
            <span className="text-[10px] w-5 text-[var(--text-muted)]">#{i + 1}</span>
            <span className="text-[10px] font-bold" style={{ color: priorityColor(g.priority) }}>
              [{g.priority.slice(0, 1)}]
            </span>
            <span className="text-xs text-[var(--text-primary)] flex-1">{g.description}</span>
            <span className="text-[10px] text-[var(--text-muted)]">
              {g.score}
            </span>
          </div>
        ))}
      </div>
    </TerminalCard>
  );
}
