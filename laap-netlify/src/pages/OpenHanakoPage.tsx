import { useState } from 'react';
import { Folder, Diamond, Plus, Sparkles, TerminalSquare, Send } from 'lucide-react';

const AGENTS = [
  { id: 'ao', name: 'AO', avatar: '/assets/aris-digital.png' },
  { id: 'butter', name: 'butter', avatar: '/assets/openhanako/Butter.png' },
  { id: 'aris', name: 'aris', avatar: '/assets/aris.png' },
  { id: 'hanako', name: 'hanako', avatar: '/assets/openhanako/Hanako.png' },
];

export default function OpenHanakoPage() {
  const [activeAgent, setActiveAgent] = useState('hanako');
  const [input, setInput] = useState('');

  const current = AGENTS.find((a) => a.id === activeAgent) || AGENTS[3];

  return (
    <div className="min-h-screen bg-[#f5f1ec] text-[#4a4a4a] flex flex-col items-center justify-center px-4">
      {/* Center avatar */}
      <div className="relative mb-6">
        <div className="w-28 h-28 rounded-full overflow-hidden border-4 border-white shadow-lg">
          <img
            src={current.avatar}
            alt={current.name}
            className="w-full h-full object-cover"
          />
        </div>
      </div>

      <h1 className="text-lg text-[#6b6b6b] mb-6 tracking-wide">想到什么就说什么吧～</h1>

      {/* Agent selector */}
      <div className="flex items-center gap-3 mb-5">
        {AGENTS.map((agent) => {
          const active = agent.id === activeAgent;
          return (
            <button
              key={agent.id}
              onClick={() => setActiveAgent(agent.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full border transition-all ${
                active
                  ? 'bg-white border-[#d4c4b0] shadow-sm text-[#4a4a4a]'
                  : 'bg-transparent border-transparent text-[#8a8a8a] hover:bg-white/50'
              }`}
            >
              <img
                src={agent.avatar}
                alt={agent.name}
                className="w-6 h-6 rounded-full object-cover"
              />
              <span className="text-sm font-medium">{agent.name}</span>
            </button>
          );
        })}
      </div>

      {/* Workspace & memory */}
      <div className="flex items-center gap-6 mb-6 text-[#8a8a8a]">
        <button className="flex items-center gap-2 text-sm hover:text-[#4a4a4a] transition-colors">
          <Folder size={16} />
          <span>工作台：OH-WorkSpace</span>
        </button>
        <button className="flex items-center gap-2 text-sm hover:text-[#4a4a4a] transition-colors">
          <Diamond size={16} />
          <span>记忆</span>
        </button>
      </div>

      {/* Input card */}
      <div className="w-full max-w-2xl bg-white rounded-3xl shadow-sm border border-[#e8e2da] p-4">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="文件备份功能可以解决一些安全上的顾虑"
          className="w-full resize-none bg-transparent text-[#4a4a4a] placeholder:text-[#b8b0a6] text-base outline-none min-h-[64px] px-2"
          rows={2}
        />
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center gap-2">
            <button className="w-9 h-9 flex items-center justify-center rounded-full border border-[#e8e2da] text-[#9a9a9a] hover:bg-[#f5f1ec] transition-colors">
              <Plus size={18} />
            </button>
            <button className="w-9 h-9 flex items-center justify-center rounded-full border border-[#e8e2da] text-[#9a9a9a] hover:bg-[#f5f1ec] transition-colors">
              <Sparkles size={18} />
            </button>
            <button className="w-9 h-9 flex items-center justify-center rounded-full border border-[#e8e2da] text-[#9a9a9a] hover:bg-[#f5f1ec] transition-colors">
              <TerminalSquare size={18} />
            </button>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-[#9a9a9a] flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#9dd3a8]" />
              DeepSeek V4 Flash
            </span>
            <button
              disabled={!input.trim()}
              className="flex items-center gap-1 px-4 py-2 rounded-full bg-[#d4c4b0] text-white text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#c4b4a0] transition-colors"
            >
              <Send size={16} />
              发送
            </button>
          </div>
        </div>
      </div>

      <p className="mt-6 text-xs text-[#b0a89e]">
        OpenHanako 界面预览 · 基于{' '}
        <a
          href="https://github.com/liliMozi/openhanako"
          target="_blank"
          rel="noreferrer"
          className="underline hover:text-[#4a4a4a]"
        >
          liliMozi/openhanako
        </a>
      </p>
    </div>
  );
}
