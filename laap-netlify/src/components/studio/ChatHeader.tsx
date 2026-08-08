import { Menu, Plus, Sparkles, LogIn, LogOut, PanelRightOpen, Maximize2, Minimize2, Share2, Key, Code2 } from 'lucide-react';
import type { User as AuthUser } from '@/lib/auth';
import { isGuest } from '@/lib/userMode';
import { cn } from '@/lib/utils';

interface ChatHeaderProps {
  title: string;
  model: string;
  user: AuthUser | null;
  agentName?: string;
  onModelChange: (model: string) => void;
  onLogout: () => void;
  onNewChat: () => void;
  onOpenAuthModal?: () => void;
  onOpenLeftSidebar?: () => void;
  onOpenRightSidebar?: () => void;
  onOpenLLMConfig?: () => void;
  focusMode?: boolean;
  onToggleFocusMode?: () => void;
  onShare?: () => void;
  workbenchOpen?: boolean;
  onToggleWorkbench?: () => void;
}

const MODELS = [
  { value: 'laap-fast', label: 'LAAP 快速', shortLabel: '快速', desc: 'LAAP Fast' },
  { value: 'laap-long', label: 'LAAP 深度思考', shortLabel: '深度', desc: 'LAAP Long Thinking' },
  { value: 'laap-vision', label: 'LAAP 视觉', shortLabel: '视觉', desc: 'LAAP Vision' },
];

export function ChatHeader({
  title,
  model,
  user,
  agentName = 'LAAP',
  onModelChange,
  onLogout,
  onNewChat,
  onOpenAuthModal,
  onOpenLeftSidebar,
  onOpenRightSidebar,
  onOpenLLMConfig,
  focusMode = false,
  onToggleFocusMode,
  onShare,
  workbenchOpen = false,
  onToggleWorkbench,
}: ChatHeaderProps) {
  const guest = isGuest();

  if (focusMode) {
    return (
      <header className="h-12 flex items-center justify-between px-3 sm:px-4 border-b border-laap-border bg-laap-bg-primary/80 backdrop-blur-md">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-sm font-medium text-white truncate">{agentName}</span>
          <div className="flex items-center gap-1.5 text-[10px] text-laap-text-tertiary font-mono uppercase tracking-wider">
            <span className="w-1.5 h-1.5 rounded-full bg-laap-gold animate-pulse-glow" />
            在线
          </div>
        </div>

        <button
          type="button"
          onClick={onToggleFocusMode}
          className="flex items-center gap-1.5 px-2 py-1 text-xs text-laap-text-secondary hover:text-white border border-laap-border rounded-sm hover:border-laap-gold/50 transition-colors"
          title="退出专注模式 (F / Esc)"
          aria-label="退出专注模式"
        >
          <Minimize2 size={14} />
          <span className="hidden sm:inline">退出专注</span>
        </button>
      </header>
    );
  }

  return (
    <header className="h-16 flex items-center justify-between px-3 sm:px-4 border-b border-laap-border bg-laap-bg-primary/80 backdrop-blur-md">
      <div className="flex items-center gap-2 sm:gap-3" title={user?.username || ''}>
        <button
          type="button"
          onClick={onOpenLeftSidebar}
          className="md:hidden p-2 min-w-[40px] min-h-[40px] flex items-center justify-center text-laap-text-secondary hover:text-white active:text-laap-gold transition-colors"
          aria-label="打开左侧面板"
        >
          <Menu size={20} />
        </button>
        <button
          type="button"
          onClick={onNewChat}
          className="md:hidden p-2 min-w-[40px] min-h-[40px] flex items-center justify-center text-laap-text-secondary hover:text-white active:text-laap-gold transition-colors"
          aria-label="新对话"
        >
          <Plus size={20} />
        </button>
        <div className="min-w-0">
          <h2 className="text-sm font-medium text-white truncate max-w-[100px] sm:max-w-[300px]">{title}</h2>
          <div className="flex items-center gap-1.5 text-[10px] text-laap-text-tertiary font-mono uppercase tracking-wider">
            <span className="w-1.5 h-1.5 rounded-full bg-laap-gold animate-pulse-glow" />
            在线
          </div>
        </div>
      </div>

      <div className="flex items-center gap-1.5 sm:gap-3">
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 border border-laap-border rounded-sm bg-laap-bg-secondary/30">
          <Sparkles size={13} className="text-laap-gold" />
          <select
            value={model}
            onChange={(e) => onModelChange(e.target.value)}
            className="bg-transparent text-xs text-laap-text-secondary focus:outline-none cursor-pointer"
          >
            {MODELS.map((m) => (
              <option key={m.value} value={m.value} className="bg-laap-bg-secondary text-laap-text-primary">
                {m.label}
              </option>
            ))}
          </select>
        </div>

        <div className="md:hidden">
          <label htmlFor="mobile-model-select" className="sr-only">选择模型</label>
          <select
            id="mobile-model-select"
            value={model}
            onChange={(e) => onModelChange(e.target.value)}
            className="bg-laap-bg-secondary/50 border border-laap-border rounded-sm px-1.5 py-1.5 text-xs text-laap-text-secondary focus:outline-none focus:border-laap-gold/50 cursor-pointer max-w-[80px] sm:max-w-[110px] min-h-[40px]"
          >
            {MODELS.map((m) => (
              <option key={m.value} value={m.value} className="bg-laap-bg-secondary text-laap-text-primary">
                {m.shortLabel}
              </option>
            ))}
          </select>
        </div>

        {onOpenLLMConfig && (
          <button
            type="button"
            onClick={onOpenLLMConfig}
            className="md:hidden flex items-center justify-center p-2 min-w-[40px] min-h-[40px] text-laap-text-secondary hover:text-laap-gold border border-laap-border rounded-sm hover:border-laap-gold/50 transition-colors"
            title="LLM 配置"
            aria-label="LLM 配置"
          >
            <Key size={16} />
          </button>
        )}

        {onShare && (
          <button
            type="button"
            onClick={onShare}
            className="hidden md:flex items-center gap-1.5 px-2 py-1.5 text-xs text-laap-text-secondary border border-laap-border rounded-sm hover:text-white hover:border-laap-gold/50 transition-colors"
            title="分享聊天记录"
            aria-label="分享聊天记录"
          >
            <Share2 size={14} />
            分享
          </button>
        )}

        {onToggleWorkbench && (
          <button
            type="button"
            onClick={onToggleWorkbench}
            className={cn(
              'hidden md:flex items-center gap-1.5 px-2 py-1.5 text-xs border border-laap-border rounded-sm transition-colors',
              workbenchOpen
                ? 'text-laap-cyan border-laap-cyan/50 bg-laap-cyan/10'
                : 'text-laap-text-secondary hover:text-white hover:border-laap-gold/50'
            )}
            title="代码工作台"
            aria-label="代码工作台"
          >
            <Code2 size={14} />
            工作台
          </button>
        )}

        <button
          type="button"
          onClick={onToggleFocusMode}
          className="hidden md:flex items-center gap-1.5 px-2 py-1.5 text-xs text-laap-text-secondary border border-laap-border rounded-sm hover:text-white hover:border-laap-gold/50 transition-colors"
          title="进入专注模式 (F)"
          aria-label="进入专注模式"
        >
          <Maximize2 size={14} />
          专注模式
        </button>

        {onOpenLLMConfig && (
          <button
            type="button"
            onClick={onOpenLLMConfig}
            className="hidden md:flex items-center gap-1.5 px-2 py-1.5 text-xs text-laap-text-secondary border border-laap-border rounded-sm hover:text-white hover:border-laap-gold/50 transition-colors"
            title="LLM 配置"
            aria-label="LLM 配置"
          >
            <Key size={14} />
            <span className="hidden lg:inline">LLM 配置</span>
          </button>
        )}

        <button
          type="button"
          onClick={onOpenRightSidebar}
          className="md:hidden p-2 min-w-[40px] min-h-[40px] flex items-center justify-center text-laap-text-secondary hover:text-white active:text-laap-gold transition-colors"
          aria-label="打开右侧面板"
        >
          <PanelRightOpen size={20} />
        </button>

        {!guest && user && (
          <div className="hidden md:flex items-center gap-1.5 text-xs text-laap-text-secondary">
            <span className="w-1.5 h-1.5 rounded-full bg-laap-emerald animate-pulse-glow" />
            <span className="truncate max-w-[120px]">{user.username || user.email}</span>
            <span className="hidden lg:inline text-[10px] font-mono text-laap-text-tertiary" title={user.id}>
              · {user.id.slice(0, 12)}
            </span>
          </div>
        )}

        {!guest && user && (
          <div className="md:hidden flex items-center gap-1 text-[10px] text-laap-text-tertiary font-mono" title={user.id}>
            <span className="w-1.5 h-1.5 rounded-full bg-laap-emerald animate-pulse-glow" />
            <span className="truncate max-w-[80px]">{user.id.slice(0, 12)}</span>
          </div>
        )}

        <button
          type="button"
          onClick={guest ? onOpenAuthModal : onLogout}
          className="flex items-center justify-center w-10 h-10 min-w-[40px] min-h-[40px] rounded-full bg-laap-bg-tertiary border border-laap-border text-laap-text-secondary hover:text-white hover:border-laap-gold transition-colors"
          title={guest ? '登录 / 注册' : '退出登录'}
          aria-label={guest ? '登录 / 注册' : '退出登录'}
        >
          {guest ? <LogIn size={16} /> : <LogOut size={16} />}
        </button>
      </div>
    </header>
  );
}
