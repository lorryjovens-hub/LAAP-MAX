'use client';

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { ScrollArea } from '@/components/ui/scroll-area';

export interface NavItem {
  id: string;
  label: string;
  icon?: string;
  badge?: string;
  status?: 'green' | 'yellow' | 'red';
}

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  navItems: NavItem[];
  taskPanel?: ReactNode;
  className?: string;
}

export default function Sidebar({ activeTab, onTabChange, navItems, taskPanel, className }: SidebarProps) {
  return (
    <aside className={cn(
      'w-64 shrink-0 bg-[#080808] border-r border-[#1a3a1a] flex flex-col h-screen sticky top-0',
      className
    )}>
      {/* ─── Logo / Header ─── */}
      <div className="p-4 border-b border-[#1a3a1a]">
        <div className="text-xs text-[#005a0a] font-mono tracking-[3px] uppercase mb-1">ROOT://</div>
        <div className="text-sm text-[#00ff41] font-mono font-bold glow-green">
          ARIS <span className="text-[#008f11]">v11</span>
        </div>
        <div className="flex items-center gap-1.5 mt-1">
          <span className="w-1.5 h-1.5 rounded-full bg-[#00ff41] shadow-[0_0_4px_#00ff41]" />
          <span className="text-[10px] text-[#008f11] font-mono uppercase">ONLINE</span>
        </div>
      </div>

      {/* ─── Navigation ─── */}
      <nav className="flex-1 py-2">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onTabChange(item.id)}
            className={cn(
              'w-full flex items-center gap-3 px-4 py-2.5 text-xs font-mono transition-all group',
              activeTab === item.id
                ? 'bg-[rgba(0,255,65,0.05)] text-[#00ff41] border-l-2 border-[#00ff41]'
                : 'text-[#005a0a] hover:text-[#008f11] hover:bg-[rgba(0,255,65,0.02)] border-l-2 border-transparent'
            )}
          >
            {/* Icon placeholder */}
            <span className={cn(
              'w-4 text-center text-[11px]',
              activeTab === item.id ? 'text-[#00ff41]' : 'text-[#005a0a]'
            )}>
              {item.icon || '>'}
            </span>
            <span className="flex-1 text-left uppercase tracking-wider">{item.label}</span>
            {item.status && (
              <span className={cn(
                'w-1.5 h-1.5 rounded-full',
                item.status === 'green' ? 'bg-[#00ff41] shadow-[0_0_4px_#00ff41]' :
                item.status === 'yellow' ? 'bg-[#ffaa00] shadow-[0_0_4px_#ffaa00]' :
                'bg-[#ff3333] shadow-[0_0_4px_#ff3333]'
              )} />
            )}
            {item.badge && (
              <span className="text-[9px] text-[#00ffff] border border-[#00ffff] px-1 rounded">
                {item.badge}
              </span>
            )}
          </button>
        ))}
      </nav>

      {/* ─── Divider ─── */}
      <div className="px-4 py-2 border-t border-[#1a3a1a]">
        <span className="text-[9px] text-[#005a0a] font-mono uppercase tracking-[2px]">Task Queue</span>
      </div>

      {/* ─── Task Panel ─── */}
      <div className="flex-1 max-h-[300px] border-t border-[#1a3a1a]">
        {taskPanel || (
          <div className="p-3 text-[10px] text-[#005a0a] font-mono text-center">
            No active tasks
          </div>
        )}
      </div>

      {/* ─── Footer ─── */}
      <div className="p-3 border-t border-[#1a3a1a] text-[9px] text-[#005a0a] font-mono text-center">
        Ψ-NET · laap_core v0.1.0
      </div>
    </aside>
  );
}
