'use client';

import { useState, useEffect } from 'react';
import TerminalCard from './TerminalCard';

interface NetNode {
  id: string;
  label: string;
  x: number;
  y: number;
  status: 'online' | 'busy' | 'idle';
}

const NODES: NetNode[] = [
  { id: 'aris', label: 'ARIS', x: 50, y: 30, status: 'online' },
  { id: 'ao', label: 'AO', x: 200, y: 60, status: 'online' },
  { id: 'psi', label: 'PSI', x: 120, y: 100, status: 'busy' },
  { id: 'mem', label: 'MEM', x: 30, y: 120, status: 'online' },
  { id: 'desire', label: 'DSR', x: 180, y: 140, status: 'online' },
  { id: 'goal', label: 'GOL', x: 100, y: 160, status: 'idle' },
  { id: 'cron', label: 'CRN', x: 60, y: 50, status: 'online' },
  { id: 'viz', label: 'VIZ', x: 160, y: 20, status: 'online' },
];

const EDGES = [
  ['aris', 'ao'], ['aris', 'psi'], ['aris', 'mem'],
  ['psi', 'desire'], ['psi', 'goal'],
  ['mem', 'desire'], ['mem', 'goal'],
  ['cron', 'aris'], ['cron', 'psi'],
  ['viz', 'aris'], ['viz', 'ao'],
];

const statusColor = {
  online: '#00ff41',
  busy: '#ffaa00',
  idle: '#005a0a',
};

export default function PsiNetViz() {
  const [pulses, setPulses] = useState<number[]>([]);

  useEffect(() => {
    const interval = setInterval(() => {
      setPulses(prev => {
        const next = [...prev, Date.now()];
        return next.slice(-8);
      });
    }, 800);
    return () => clearInterval(interval);
  }, []);

  return (
    <TerminalCard title="Ψ-NET TOPOLOGY" status="green">
      <svg viewBox="0 0 230 190" className="w-full h-auto max-h-[200px]">
        {/* Edges */}
        {EDGES.map(([from, to]) => {
          const f = NODES.find(n => n.id === from)!;
          const t = NODES.find(n => n.id === to)!;
          return (
            <line
              key={`${from}-${to}`}
              x1={f.x} y1={f.y} x2={t.x} y2={t.y}
              stroke="#1a3a1a"
              strokeWidth={0.5}
              strokeDasharray="2,2"
            />
          );
        })}

        {/* Data pulses */}
        {pulses.map((ts, i) => {
          const edge = EDGES[i % EDGES.length];
          const f = NODES.find(n => n.id === edge[0])!;
          const t = NODES.find(n => n.id === edge[1])!;
          const progress = ((Date.now() - ts) % 1500) / 1500;
          const cx = f.x + (t.x - f.x) * progress;
          const cy = f.y + (t.y - f.y) * progress;
          return (
            <circle
              key={ts}
              cx={cx} cy={cy} r={2}
              fill="#00ff41"
              opacity={1 - progress}
            />
          );
        })}

        {/* Nodes */}
        {NODES.map((node) => (
          <g key={node.id}>
            {/* Glow */}
            <circle
              cx={node.x} cy={node.y} r={8}
              fill="none"
              stroke={statusColor[node.status]}
              strokeWidth={0.5}
              opacity={0.3}
            />
            {/* Node circle */}
            <circle
              cx={node.x} cy={node.y} r={4}
              fill={statusColor[node.status]}
              className="animate-pulse"
              style={{ animationDuration: '3s' }}
            />
            {/* Label */}
            <text
              x={node.x} y={node.y - 8}
              textAnchor="middle"
              fill="#008f11"
              fontSize={7}
              fontFamily="monospace"
            >
              {node.label}
            </text>
          </g>
        ))}
      </svg>

      {/* Legend */}
      <div className="flex gap-4 mt-2 text-[9px] font-mono">
        <span className="flex items-center gap-1 text-[#00ff41]">
          <span className="w-2 h-2 rounded-full bg-[#00ff41]" /> ONLINE
        </span>
        <span className="flex items-center gap-1 text-[#ffaa00]">
          <span className="w-2 h-2 rounded-full bg-[#ffaa00]" /> BUSY
        </span>
        <span className="flex items-center gap-1 text-[#005a0a]">
          <span className="w-2 h-2 rounded-full bg-[#005a0a]" /> IDLE
        </span>
        <span className="ml-auto text-[#005a0a]">8 NODES · 12 EDGES</span>
      </div>
    </TerminalCard>
  );
}
