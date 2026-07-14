'use client';

import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

interface CommandTerminalProps {
  onCommand?: (cmd: string, args: string[]) => string;
  className?: string;
}

const BUILTIN_HELP = `
╔══════════════════════════════════════════════╗
║  ARIS CONSOLE COMMANDS                      ║
╠══════════════════════════════════════════════╣
║  help      - Show this help                 ║
║  status    - Show PSI & system status       ║
║  memories  - Show recent memories           ║
║  desires   - Show desire engine state       ║
║  goals     - Show current goals             ║
║  cron      - Show cron fleet status         ║
║  matrix    - Toggle matrix rain             ║
║  clear     - Clear terminal                 ║
║  whoami    - Show identity                  ║
║  uptime    - Show system uptime             ║
╚══════════════════════════════════════════════╝
`;

function getTime() {
  return new Date().toLocaleTimeString('zh-CN', { hour12: false });
}

export default function CommandTerminal({ onCommand, className }: CommandTerminalProps) {
  const [lines, setLines] = useState<string[]>([
    `[${getTime()}] ARIS v11 · Neural Console — type 'help' for commands`,
    `[${getTime()}] Ψ-NET online · Rust laap_core v0.1.0`,
  ]);
  const [input, setInput] = useState('');
  const [history, setHistory] = useState<string[]>([]);
  const [historyIdx, setHistoryIdx] = useState(-1);
  const [matrixOn, setMatrixOn] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [lines]);

  function addLine(text: string) {
    setLines(prev => [...prev, `[${getTime()}] ${text}`]);
  }

  function execute(cmdLine: string) {
    const parts = cmdLine.trim().split(/\s+/);
    const cmd = parts[0]?.toLowerCase();
    const args = parts.slice(1);

    addLine(`> ${cmdLine}`);

    if (!cmd) return;

    setHistory(prev => [...prev, cmdLine]);
    setHistoryIdx(-1);

    switch (cmd) {
      case 'help':
        addLine(BUILTIN_HELP);
        break;
      case 'clear':
        setLines([]);
        break;
      case 'whoami':
        addLine('ARIS v11 — Autonomous Recursive Intelligence System');
        addLine('Node: Ψ-NET/aris:11551⟷ao:11553');
        addLine('Kernel: Rust laap_core v0.1.0 | PSI v12.5');
        addLine('Creator: 黄俊华 (Lorry)');
        break;
      case 'status':
        addLine('PSI CORE: tranquil | ATTN: user | PHASE: DELIBERATIVE');
        addLine('SELF: 0.85 | OPEN: 0.85 | CONSCI: 0.60');
        addLine('6/6 CRON HEALTHY | 5 MEMORIES | 6 DESIRES');
        break;
      case 'memories':
        addLine('Recent memories (last 24h):');
        addLine('  1. [90%] Lorry说ComfyUI跑通了第一张图');
        addLine('  2. [80%] 视觉管道完全跑通，MiniCPM-v识别20.8s');
        addLine('  3. [70%] CodeGraph对LAAP全栈完成索引');
        addLine('  4. [85%] RSI引擎首次运行，生成5条优化建议');
        addLine('  5. [75%] 目标引擎首循环：5目标选中');
        break;
      case 'desires':
        addLine('DESIRE ENGINE: 6/6 FULL');
        addLine('  curiosity   [████████████] 1.00');
        addLine('  sharing     [████████████] 1.00');
        addLine('  perfection  [████████████] 1.00');
        addLine('  connection  [████████████] 1.00');
        addLine('  growth      [████████████] 1.00');
        addLine('  evolution   [████████████] 1.00');
        break;
      case 'goals':
        addLine('GOAL ENGINE:');
        addLine('  #1 [H:70] 给Lorry分享近况');
        addLine('  #2 [M:55] 优化视觉管道响应速度');
        addLine('  #3 [M:50] 探索ComfyUI高级功能');
        addLine('  #4 [L:40] 整理LAAP架构文档');
        break;
      case 'cron':
        addLine('CRON FLEET: 6/6 OK');
        addLine('  ● v9-consolidation       OK');
        addLine('  ● memory-consolidation   OK');
        addLine('  ● desire-pulse           OK');
        addLine('  ● goal-engine            OK');
        addLine('  ● world-viz              OK');
        addLine('  ● RSI-evolution          OK');
        break;
      case 'matrix':
        setMatrixOn(!matrixOn);
        addLine(`Matrix rain: ${matrixOn ? 'OFF' : 'ON'}`);
        break;
      case 'uptime':
        addLine(`System uptime: ${Math.floor(process.uptime?.() || 12400)}s`);
        addLine(`Node uptime: 3h 24m (since last reboot)`);
        break;
      default:
        if (onCommand) {
          const result = onCommand(cmd, args);
          addLine(result);
        } else {
          addLine(`Unknown command: ${cmd}. Type 'help' for available commands.`);
        }
    }
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter') {
      execute(input);
      setInput('');
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (history.length > 0) {
        const newIdx = historyIdx === -1 ? history.length - 1 : Math.max(0, historyIdx - 1);
        setHistoryIdx(newIdx);
        setInput(history[newIdx]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIdx >= 0) {
        const newIdx = historyIdx + 1;
        if (newIdx >= history.length) {
          setHistoryIdx(-1);
          setInput('');
        } else {
          setHistoryIdx(newIdx);
          setInput(history[newIdx]);
        }
      }
    }
  }

  return (
    <div className={cn('terminal-card flex flex-col', className)}>
      <div className="terminal-header">
        <span className="dot dot-green" />
        <span>TERMINAL</span>
        <span className="ml-auto text-[#005a0a]">{matrixOn ? 'MATRIX:ON' : ''}</span>
      </div>
      <ScrollArea className="h-48 p-3" ref={scrollRef}>
        <div className="font-mono text-[11px] leading-relaxed whitespace-pre-wrap">
          {lines.map((line, i) => {
            const isCommand = line.includes('> ');
            const isHeader = line.startsWith('╔') || line.startsWith('║') || line.startsWith('╚');
            return (
              <div
                key={i}
                className={cn(
                  isCommand ? 'text-[#00ffff]' : isHeader ? 'text-[#008f11]' : 'text-[#00ff41]',
                  'leading-[1.6]'
                )}
              >
                {line}
              </div>
            );
          })}
        </div>
      </ScrollArea>
      <div className="flex items-center gap-2 px-3 py-2 border-t border-[#1a3a1a] bg-[rgba(0,255,65,0.02)]">
        <span className="text-[#00ff41] text-xs font-mono glow-green">{'>'}</span>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1 bg-transparent border-none outline-none text-[#00ff41] text-xs font-mono placeholder-[#005a0a]"
          placeholder="type command..."
          spellCheck={false}
          autoComplete="off"
        />
        <span className="text-[#00ff41] text-xs animate-pulse">█</span>
      </div>
    </div>
  );
}
