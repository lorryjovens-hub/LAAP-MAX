'use client';

import { useEffect, useState, useCallback } from 'react';
import PSIMonitor from '@/components/PSIMonitor';
import MemoryPanel from '@/components/MemoryPanel';
import DesirePanel from '@/components/DesirePanel';
import GoalPanel from '@/components/GoalPanel';
import CameraChat from '@/components/CameraChat';
import TerminalCard from '@/components/TerminalCard';
import MatrixRain from '@/components/MatrixRain';
import CommandTerminal from '@/components/CommandTerminal';
import SystemMonitor from '@/components/SystemMonitor';
import PsiNetViz from '@/components/PsiNetViz';
import Sidebar, { NavItem } from '@/components/Sidebar';
import TaskPanel, { Task } from '@/components/TaskPanel';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';

interface ArisState {
  psi: any;
  memories: any[];
  desires: any[];
  goals: any[];
  system: any;
}

const defaultState: ArisState = {
  psi: { emotion: 'loading', emotion_intensity: 0, attention: 'idle', self_presence: 0, openness: 0, conscientiousness: 0, psi_cycle_phase: 'INIT' },
  memories: [],
  desires: [],
  goals: [],
  system: { node: 'Ψ-NET', kernel: 'loading', cron_jobs: [] },
};

const NAV_ITEMS: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: '◈', status: 'green' },
  { id: 'memories', label: 'Memories', icon: '▤', status: 'green' },
  { id: 'camera', label: 'Camera', icon: '◉', status: 'yellow' },
  { id: 'system', label: 'System', icon: '◎', status: 'green' },
  { id: 'terminal', label: 'Terminal', icon: '>', badge: 'CLI' },
];

const MOCK_TASKS: Task[] = [
  {
    id: 't1', label: 'Aris Chat — 今日总结',
    status: 'running', type: 'chat',
    output: ['> 正在分析今日对话...', '> 已提取 5 条关键记忆', '> 情感评分中...'],
    createdAt: new Date(),
  },
  {
    id: 't2', label: 'VLM 视觉扫描',
    status: 'queued', type: 'vision',
    output: [],
    createdAt: new Date(),
  },
  {
    id: 't3', label: 'ComfyUI 生成测试',
    status: 'queued', type: 'build',
    output: [],
    createdAt: new Date(),
  },
  {
    id: 't4', label: '记忆整合 — Cron触发',
    status: 'done', type: 'command',
    output: ['✓ 247 概念已索引', '✓ 92 记忆已持久化'],
    createdAt: new Date(Date.now() - 300000),
  },
];

let taskIdCounter = 5;

export default function Home() {
  const [state, setState] = useState<ArisState>(defaultState);
  const [time, setTime] = useState('');
  const [dataSource, setDataSource] = useState<'live' | 'fallback'>('live');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [matrixOn, setMatrixOn] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [tasks, setTasks] = useState<Task[]>(MOCK_TASKS);

  const fetchState = useCallback(async () => {
    try {
      const resp = await fetch('/api/aris-state');
      const data = await resp.json();
      setState(data);
      setDataSource(resp.headers.get('X-Data-Source') === 'fallback' ? 'fallback' : 'live');
    } catch {
      setDataSource('fallback');
    }
  }, []);

  useEffect(() => {
    fetchState();
    const tick = () => setTime(new Date().toLocaleTimeString('zh-CN', { hour12: false }));
    tick();
    const clockInterval = setInterval(tick, 1000);
    const refreshInterval = autoRefresh ? setInterval(fetchState, 10000) : null;
    return () => {
      clearInterval(clockInterval);
      if (refreshInterval) clearInterval(refreshInterval);
    };
  }, [autoRefresh, fetchState]);

  // Simulate task progression
  useEffect(() => {
    const interval = setInterval(() => {
      setTasks(prev => prev.map(t => {
        if (t.status === 'running') {
          const newOutput = [...t.output, `[${new Date().toLocaleTimeString()}] 处理中...`];
          if (newOutput.length > 8) {
            return { ...t, status: 'done' as const, output: [...newOutput, '✓ 完成'] };
          }
          return { ...t, output: newOutput.slice(-6) };
        }
        return t;
      }));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  function handleNewTask(label: string) {
    const newTask: Task = {
      id: `t${taskIdCounter++}`,
      label,
      status: 'queued',
      type: label.toLowerCase().includes('chat') ? 'chat' :
            label.toLowerCase().includes('vision') || label.toLowerCase().includes('视觉') ? 'vision' :
            label.toLowerCase().includes('build') || label.toLowerCase().includes('生成') ? 'build' :
            'command',
      output: [],
      createdAt: new Date(),
    };
    setTasks(prev => [...prev, newTask]);
    // Auto-start after 1s
    setTimeout(() => {
      setTasks(prev => prev.map(t => t.id === newTask.id ? { ...t, status: 'running' as const, output: ['> 开始执行...'] } : t));
    }, 1000);
  }

  function handleCancelTask(id: string) {
    setTasks(prev => prev.map(t => t.id === id ? { ...t, status: 'error' as const, output: [...t.output, '✕ 已取消'] } : t));
  }

  const cronOk = state.system?.cron_jobs?.filter((c: any) => c.status === 'ok').length ?? 0;
  const cronTotal = state.system?.cron_jobs?.length ?? 6;

  // ─── Task Panel ───
  const taskPanel = (
    <TaskPanel
      tasks={tasks}
      onCancelTask={handleCancelTask}
      onNewTask={handleNewTask}
    />
  );

  return (
    <div className="flex h-screen overflow-hidden bg-[#050505]">
      {/* Matrix Rain */}
      <MatrixRain enabled={matrixOn} />

      {/* ─── Sidebar ─── */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        navItems={NAV_ITEMS}
        taskPanel={taskPanel}
      />

      {/* ─── Main Content ─── */}
      <main className="flex-1 overflow-y-auto p-4 md:p-6 relative z-10">
        {/* ─── Breadcrumb ─── */}
        <nav className="flex items-center gap-2 mb-3 text-xs font-mono">
          <span className="text-[#008f11]">{'>'}</span>
          <span className="text-[#00ff41]">ROOT</span>
          <span className="text-[#005a0a]">/</span>
          <span className="text-[#00ff41] glow-green font-bold">{NAV_ITEMS.find(n => n.id === activeTab)?.label?.toUpperCase() || 'CONSOLE'}</span>
        </nav>

        {/* ─── Header ─── */}
        <header className="mb-4">
          <pre className="text-[#00ff41] text-[10px] md:text-xs leading-tight whitespace-pre overflow-x-auto glow-green font-mono">
{`╔══════════════════════════════════════════════════════════════════╗
║  ARIS v11 · NEURAL CONSOLE                         █ █ █ █ █ █ ║
║  ROOT://neural_interface/console                    █  █  █  █  ║
╚══════════════════════════════════════════════════════════════════════╝`}
          </pre>
          <div className="flex flex-wrap items-center gap-3 mt-2 text-[10px]">
            <span>
              <span className="text-[#005a0a]">STATUS</span>{' '}
              <Badge variant="outline" className={cn(
                'font-mono text-[8px] px-1.5 py-0 uppercase tracking-wider bg-transparent',
                dataSource === 'live'
                  ? 'text-[#00ff41] border-[#00ff41]'
                  : 'text-[#ffaa00] border-[#ffaa00]'
              )}>
                {dataSource === 'live' ? 'LIVE' : 'FALLBACK'}
              </Badge>
            </span>
            <span><span className="text-[#005a0a]">TIME</span> <span className="text-[#00ffff]">{time}</span></span>
            <div className="ml-auto flex gap-2">
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={cn(
                  'text-[8px] px-1.5 py-0.5 border rounded font-mono uppercase tracking-wider',
                  autoRefresh ? 'text-[#00ff41] border-[#00ff41] bg-[rgba(0,255,65,0.05)]' : 'text-[#005a0a] border-[#1a3a1a]'
                )}
              >
                {autoRefresh ? 'AUTO' : 'MANUAL'}
              </button>
              <button onClick={fetchState} className="text-[8px] px-1.5 py-0.5 border border-[#00ffff] text-[#00ffff] rounded font-mono uppercase">
                REFRESH
              </button>
            </div>
          </div>
        </header>

        {/* ─── Content Area ─── */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="hidden">
          {/* We use custom sidebar navigation instead of tabs list */}
        </Tabs>

        {/* Dashboard */}
        {activeTab === 'dashboard' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
              <PSIMonitor psi={state.psi} />
              <MemoryPanel memories={state.memories} />
              <DesirePanel desires={state.desires} />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <GoalPanel goals={state.goals} />
              <TerminalCard title="CRON FLEET" status={cronOk === cronTotal ? 'green' : 'yellow'}>
                <div className="grid grid-cols-2 gap-2">
                  {state.system?.cron_jobs?.map((c: any, i: number) => (
                    <div key={i} className="flex items-center gap-2 text-xs py-1 font-mono">
                      <span className={cn('w-1.5 h-1.5 rounded-full', c.status === 'ok' ? 'bg-[#00ff41] shadow-[0_0_4px_#00ff41]' : 'bg-[#ff3333] shadow-[0_0_4px_#ff3333]')} />
                      <span className="text-[#00ff41]">{c.name || c}</span>
                      <span className={cn('ml-auto text-[10px]', c.status === 'ok' ? 'text-[#00ff41]' : 'text-[#ff3333]')}>{c.status?.toUpperCase?.() || 'OK'}</span>
                    </div>
                  ))}
                </div>
                <div className="mt-3 pt-2 border-t border-[#1a3a1a] text-[10px] text-[#005a0a] font-mono">{cronOk}/{cronTotal} JOBS HEALTHY</div>
              </TerminalCard>
            </div>
          </div>
        )}

        {/* Memories */}
        {activeTab === 'memories' && <MemoryPanel memories={state.memories} />}

        {/* Camera */}
        {activeTab === 'camera' && <CameraChat />}

        {/* System */}
        {activeTab === 'system' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <SystemMonitor />
              <PsiNetViz />
            </div>
            <TerminalCard title="SYSTEM INFO" status="green">
              <div className="space-y-2 font-mono text-xs">
                <div className="flex gap-4"><span className="text-[#005a0a]">NODE:</span><span className="text-[#00ff41]">{state.system?.node}</span></div>
                <div className="flex gap-4"><span className="text-[#005a0a]">KERNEL:</span><span className="text-[#00ff41]">{state.system?.kernel}</span></div>
                <div className="flex gap-4"><span className="text-[#005a0a]">SOURCE:</span><span className={dataSource === 'live' ? 'text-[#00ff41]' : 'text-[#ffaa00]'}>{dataSource === 'live' ? 'LIVE LAAP DATA' : 'MOCK FALLBACK'}</span></div>
              </div>
            </TerminalCard>
          </div>
        )}

        {/* Terminal */}
        {activeTab === 'terminal' && (
          <CommandTerminal onCommand={(cmd) => {
            if (cmd === 'matrix') setMatrixOn(!matrixOn);
            if (cmd === 'newtask' || cmd === 'task') {
              handleNewTask('手动任务 — ' + new Date().toLocaleTimeString());
              return 'Task created.';
            }
            return '';
          }} />
        )}

        {/* Footer */}
        <footer className="text-center text-[8px] text-[#005a0a] py-3 mt-4 border-t border-[#1a3a1a] font-mono">
          Ψ-NET · Aris:11551 ⟷ Ao:11553 · PSI v12.5 · laap_core v0.1.0 · {cronOk}/{cronTotal} cron · Next.js + shadcn/ui
        </footer>
      </main>
    </div>
  );
}
