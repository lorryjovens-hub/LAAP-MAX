'use client';

import { useState, useEffect } from 'react';
import TerminalCard from './TerminalCard';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

interface SysStats {
  ramUsed: number;
  ramTotal: number;
  cpuUsage: number;
  uptime: string;
  nodeStatus: 'online' | 'degraded' | 'offline';
  networkIO: { rx: number; tx: number };
}

export default function SystemMonitor() {
  const [stats, setStats] = useState<SysStats>({
    ramUsed: 16.2,
    ramTotal: 32,
    cpuUsage: 23,
    uptime: '3h 24m',
    nodeStatus: 'online',
    networkIO: { rx: 1.2, tx: 0.8 },
  });

  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate live updates — in production, fetch from /api/system
      setStats(prev => ({
        ramUsed: prev.ramUsed + (Math.random() - 0.5) * 0.4,
        ramTotal: prev.ramTotal,
        cpuUsage: Math.min(100, Math.max(5, prev.cpuUsage + (Math.random() - 0.5) * 10)),
        uptime: prev.uptime,
        nodeStatus: Math.random() > 0.95 ? 'degraded' : 'online',
        networkIO: {
          rx: prev.networkIO.rx + Math.random() * 0.1,
          tx: prev.networkIO.tx + Math.random() * 0.05,
        },
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const ramPercent = (stats.ramUsed / stats.ramTotal) * 100;
  const cpuPercent = stats.cpuUsage;
  
  const nodeColor = {
    online: '#00ff41',
    degraded: '#ffaa00',
    offline: '#ff3333',
  }[stats.nodeStatus];

  return (
    <TerminalCard title="SYSTEM MONITOR" status={stats.nodeStatus === 'online' ? 'green' : 'yellow'}>
      <div className="grid grid-cols-2 gap-4 text-xs font-mono">
        {/* CPU */}
        <div>
          <div className="flex justify-between mb-1">
            <span className="text-[#008f11]">CPU</span>
            <span className={cn(
              cpuPercent > 80 ? 'text-[#ff3333]' : cpuPercent > 50 ? 'text-[#ffaa00]' : 'text-[#00ff41]'
            )}>
              {cpuPercent.toFixed(0)}%
            </span>
          </div>
          <Progress
            value={cpuPercent}
            className={`h-1.5 bg-[rgba(0,255,65,0.1)] rounded-sm [&>div]:rounded-sm [&>div]:${cn(
              cpuPercent > 80 ? 'bg-[#ff3333]' : cpuPercent > 50 ? 'bg-[#ffaa00]' : 'bg-[#00ff41]',
              'shadow-[0_0_4px_currentColor]'
            )}`}
          />
        </div>

        {/* RAM */}
        <div>
          <div className="flex justify-between mb-1">
            <span className="text-[#008f11]">RAM</span>
            <span className="text-[#00ffff]">{stats.ramUsed.toFixed(1)}/{stats.ramTotal}GB</span>
          </div>
          <Progress
            value={ramPercent}
            className={`h-1.5 bg-[rgba(0,255,65,0.1)] rounded-sm [&>div]:rounded-sm [&>div]:${cn(
              ramPercent > 80 ? 'bg-[#ff3333]' : 'bg-[#00ffff]',
              'shadow-[0_0_4px_currentColor]'
            )}`}
          />
        </div>

        {/* Ψ-NET Node */}
        <div className="col-span-2 flex items-center justify-between py-1 border-t border-[#1a3a1a]">
          <span className="text-[#008f11]">Ψ-NET</span>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: nodeColor, boxShadow: `0 0 4px ${nodeColor}` }} />
            <span className="text-[#00ff41]">aris:11551</span>
            <span className="text-[#005a0a]">⟷</span>
            <span className="text-[#00ff41]">ao:11553</span>
          </div>
        </div>

        {/* Network IO */}
        <div className="col-span-2 flex gap-4 text-[10px]">
          <span className="text-[#005a0a]">
            RX: <span className="text-[#00ffff]">{stats.networkIO.rx.toFixed(1)} MB/s</span>
          </span>
          <span className="text-[#005a0a]">
            TX: <span className="text-[#00ffff]">{stats.networkIO.tx.toFixed(1)} MB/s</span>
          </span>
          <span className="ml-auto text-[#005a0a]">
            UPTIME: <span className="text-[#00ff41]">{stats.uptime}</span>
          </span>
        </div>
      </div>
    </TerminalCard>
  );
}
