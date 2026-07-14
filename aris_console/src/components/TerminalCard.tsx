'use client';

import { ReactNode } from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface TerminalCardProps {
  title: string;
  children: ReactNode;
  className?: string;
  status?: 'green' | 'yellow' | 'red';
}

const dotColor = {
  green: 'bg-[#00ff41] shadow-[0_0_6px_#00ff41]',
  yellow: 'bg-[#ffaa00] shadow-[0_0_4px_#ffaa00]',
  red: 'bg-[#ff3333] shadow-[0_0_4px_#ff3333]',
};

export default function TerminalCard({ title, children, className, status = 'green' }: TerminalCardProps) {
  return (
    <Card className={cn(
      'bg-[#0d1117] border-[#1a3a1a] rounded shadow-none',
      'relative overflow-hidden',
      'before:content-[""] before:absolute before:top-0 before:left-0 before:right-0 before:h-px',
      'before:bg-gradient-to-r before:from-transparent before:via-[#008f11] before:to-transparent before:opacity-50',
      'hover:border-[#008f11] hover:shadow-[0_0_10px_rgba(0,255,65,0.05)] transition-all',
      className
    )}>
      <CardHeader className="bg-[rgba(0,255,65,0.03)] border-b border-[#1a3a1a] py-1.5 px-3 flex flex-row items-center gap-2 text-[11px] text-[#008f11] uppercase tracking-[2px] font-mono">
        <span className={cn('w-2 h-2 rounded-full inline-block', dotColor[status])} />
        {title}
      </CardHeader>
      <CardContent className="p-4 text-[13px] leading-relaxed font-mono">
        {children}
      </CardContent>
    </Card>
  );
}
