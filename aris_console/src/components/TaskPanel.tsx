'use client';

import { useState, useRef, useEffect } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

export interface Task {
  id: string;
  label: string;
  status: 'running' | 'queued' | 'done' | 'error';
  type: 'chat' | 'command' | 'build' | 'vision';
  output: string[];
  createdAt: Date;
}

interface TaskPanelProps {
  tasks: Task[];
  onCancelTask?: (id: string) => void;
  onNewTask?: (label: string) => void;
  className?: string;
}

const typeIcons: Record<string, string> = {
  chat: '💬',
  command: '>',
  build: '⚙',
  vision: '👁',
};

const statusColor = {
  running: '#00ff41',
  queued: '#ffaa00',
  done: '#005a0a',
  error: '#ff3333',
};

function TaskItem({ task, onCancel }: { task: Task; onCancel?: (id: string) => void }) {
  const [expanded, setExpanded] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (expanded && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [expanded, task.output]);

  return (
    <div className="border-b border-[rgba(0,255,65,0.05)] last:border-0">
      {/* Header */}
      <div
        className="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-[rgba(0,255,65,0.02)] transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        {/* Status dot */}
        <span
          className="w-1.5 h-1.5 rounded-full shrink-0"
          style={{ backgroundColor: statusColor[task.status], boxShadow: `0 0 3px ${statusColor[task.status]}` }}
        />
        
        {/* Type icon */}
        <span className="text-[9px] shrink-0">{typeIcons[task.type] || '>'}</span>
        
        {/* Label */}
        <span className="text-[10px] text-[#00ff41] font-mono truncate flex-1">{task.label}</span>
        
        {/* Status text */}
        <span
          className="text-[8px] font-mono uppercase shrink-0"
          style={{ color: statusColor[task.status] }}
        >
          {task.status}
        </span>

        {/* Cancel button */}
        {(task.status === 'running' || task.status === 'queued') && onCancel && (
          <button
            onClick={(e) => { e.stopPropagation(); onCancel(task.id); }}
            className="text-[#ff3333] text-[10px] hover:text-[#ff6666] shrink-0"
          >
            ✕
          </button>
        )}
      </div>

      {/* Expanded output */}
      {expanded && (
        <div
          ref={scrollRef}
          className="max-h-[120px] overflow-y-auto bg-[#050505] mx-2 mb-2 rounded border border-[rgba(0,255,65,0.05)] p-2"
        >
          {task.output.length === 0 ? (
            <div className="text-[9px] text-[#005a0a] font-mono italic">waiting...</div>
          ) : (
            task.output.map((line, i) => (
              <div key={i} className="text-[9px] text-[#008f11] font-mono leading-relaxed whitespace-pre-wrap">
                {line}
              </div>
            ))
          )}
          {task.status === 'running' && (
            <span className="text-[#00ff41] text-[10px] animate-pulse">█</span>
          )}
        </div>
      )}
    </div>
  );
}

export default function TaskPanel({ tasks, onCancelTask, onNewTask, className }: TaskPanelProps) {
  const [newLabel, setNewLabel] = useState('');
  const [showInput, setShowInput] = useState(false);

  function handleAdd() {
    if (newLabel.trim() && onNewTask) {
      onNewTask(newLabel.trim());
      setNewLabel('');
      setShowInput(false);
    }
  }

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Add task button */}
      <div className="p-2 border-b border-[rgba(0,255,65,0.05)]">
        {showInput ? (
          <div className="flex gap-1">
            <input
              autoFocus
              value={newLabel}
              onChange={e => setNewLabel(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') handleAdd(); if (e.key === 'Escape') setShowInput(false); }}
              className="flex-1 bg-[#050505] border border-[#1a3a1a] rounded px-2 py-1 text-[10px] text-[#00ff41] font-mono outline-none placeholder-[#005a0a]"
              placeholder="task name..."
            />
            <button onClick={handleAdd} className="text-[10px] text-[#00ff41] border border-[#00ff41] px-2 rounded font-mono hover:bg-[rgba(0,255,65,0.05)]">
              +
            </button>
          </div>
        ) : (
          <button
            onClick={() => setShowInput(true)}
            className="w-full text-[10px] text-[#005a0a] border border-dashed border-[#1a3a1a] rounded py-1.5 font-mono hover:text-[#008f11] hover:border-[#008f11] transition-colors"
          >
            + NEW TASK
          </button>
        )}
      </div>

      {/* Task list */}
      <ScrollArea className="flex-1">
        {tasks.length === 0 ? (
          <div className="p-3 text-[9px] text-[#005a0a] font-mono text-center italic">
            {'>'} Queue empty
          </div>
        ) : (
          tasks.map(task => (
            <TaskItem key={task.id} task={task} onCancel={onCancelTask} />
          ))
        )}
      </ScrollArea>

      {/* Summary */}
      {tasks.length > 0 && (
        <div className="p-2 border-t border-[rgba(0,255,65,0.05)] text-[8px] text-[#005a0a] font-mono flex justify-between">
          <span>{tasks.filter(t => t.status === 'running').length} RUNNING</span>
          <span>{tasks.filter(t => t.status === 'queued').length} QUEUED</span>
          <span>{tasks.filter(t => t.status === 'done').length} DONE</span>
        </div>
      )}
    </div>
  );
}
