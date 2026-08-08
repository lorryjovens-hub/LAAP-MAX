import { useMemo, useState } from 'react';
import {
  Plus,
  LogOut,
  LogIn,
  User,
  Settings,
  ChevronDown,
  ChevronUp,
  Brain,
  Key,
  Sparkles,
  PanelLeftClose,
  PanelLeftOpen,
  X,
} from 'lucide-react';
import { isGuest } from '@/lib/userMode';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { useIsMobile } from '@/hooks/use-mobile';
import { AgentToggles } from './AgentToggles';
import { LLMConfigPanel } from './LLMConfigPanel';
import { PersonalityConfigPanel } from './PersonalityConfigPanel';
import type { ChatSession } from '@/lib/chat';
import type { User as AuthUser } from '@/lib/auth';
import type { LlmConfig } from '@/lib/llmConfig';
import type { PersonalityConfig } from '@/lib/personality';
import type { AppSettings } from '@/lib/settings';

interface ChatSidebarProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  user: AuthUser | null;
  settings: AppSettings;
  llmConfig: LlmConfig;
  savedLLMConfig: LlmConfig | null;
  personality: PersonalityConfig;
  collapsed: boolean;
  onToggleCollapse: () => void;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onSettingsChange: (settings: AppSettings) => void;
  onLLMConfigChange: (config: LlmConfig) => void;
  onLLMConfigSave: () => void | Promise<void>;
  onOpenLLMConfigModal?: () => void;
  onPersonalityChange: (config: PersonalityConfig) => void;
  onPersonalitySave: () => void | Promise<void>;
  onOpenSettings: () => void;
  onLogout: () => void;
  onOpenAuthModal: () => void;
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

type SectionKey = 'agent' | 'personality' | 'llm';

export function ChatSidebar({
  sessions,
  activeSessionId,
  user,
  settings,
  llmConfig,
  savedLLMConfig,
  personality,
  collapsed,
  onToggleCollapse,
  onSelectSession,
  onNewChat,
  onSettingsChange,
  onLLMConfigChange,
  onLLMConfigSave,
  onOpenLLMConfigModal,
  onPersonalityChange,
  onPersonalitySave,
  onOpenSettings,
  onLogout,
  onOpenAuthModal,
  mobileOpen = false,
  onMobileClose,
}: ChatSidebarProps) {
  const isMobile = useIsMobile();
  const [openSections, setOpenSections] = useState<Record<SectionKey, boolean>>({
    agent: true,
    personality: true,
    llm: true,
  });

  function toggleSection(key: SectionKey) {
    setOpenSections((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  const expandedContent = useMemo(
    () => (
      <ExpandedChatSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        user={user}
        settings={settings}
        llmConfig={llmConfig}
        savedLLMConfig={savedLLMConfig}
        personality={personality}
        openSections={openSections}
        onToggleSection={toggleSection}
        onSelectSession={onSelectSession}
        onNewChat={onNewChat}
        onSettingsChange={onSettingsChange}
        onLLMConfigChange={onLLMConfigChange}
        onLLMConfigSave={onLLMConfigSave}
        onOpenLLMConfigModal={onOpenLLMConfigModal}
        onPersonalityChange={onPersonalityChange}
        onPersonalitySave={onPersonalitySave}
        onOpenSettings={onOpenSettings}
        onLogout={onLogout}
        onOpenAuthModal={onOpenAuthModal}
        onToggleCollapse={onToggleCollapse}
        onMobileClose={onMobileClose}
      />
    ),
    [
      sessions,
      activeSessionId,
      user,
      settings,
      llmConfig,
      savedLLMConfig,
      personality,
      openSections,
      onSelectSession,
      onNewChat,
      onSettingsChange,
      onLLMConfigChange,
      onLLMConfigSave,
      onOpenLLMConfigModal,
      onPersonalityChange,
      onPersonalitySave,
      onOpenSettings,
      onLogout,
      onOpenAuthModal,
      onToggleCollapse,
      onMobileClose,
    ]
  );

  return (
    <>
      {collapsed ? (
        <aside className="hidden md:flex w-14 flex-col items-center border-r border-laap-border bg-laap-bg-secondary/50 py-3">
          <button
            onClick={onToggleCollapse}
            className="p-2 text-laap-text-tertiary hover:text-white transition-colors"
            title="展开左侧面板"
          >
            <PanelLeftOpen size={18} />
          </button>
          <button
            onClick={onNewChat}
            className="mt-3 p-2 text-laap-gold hover:text-laap-gold-light transition-colors"
            title="新对话"
          >
            <Plus size={18} />
          </button>
        </aside>
      ) : (
        <aside className="hidden md:flex w-[280px] flex-col border-r border-laap-border bg-laap-bg-secondary/50">
          {expandedContent}
        </aside>
      )}

      {isMobile && (
        <Sheet open={mobileOpen} onOpenChange={(open) => !open && onMobileClose?.()}>
          <SheetContent
            side="left"
            className="w-[80vw] max-w-xs p-0 bg-laap-bg-secondary/95 border-r border-laap-border [&>button]:hidden"
          >
            <SheetHeader className="sr-only">
              <SheetTitle>左侧边栏</SheetTitle>
              <SheetDescription>会话、Agent 能力与 LLM 配置</SheetDescription>
            </SheetHeader>
            {expandedContent}
          </SheetContent>
        </Sheet>
      )}
    </>
  );
}

interface ExpandedChatSidebarProps extends Omit<ChatSidebarProps, 'collapsed' | 'onToggleCollapse' | 'mobileOpen'> {
  openSections: Record<SectionKey, boolean>;
  onToggleSection: (key: SectionKey) => void;
  onToggleCollapse: () => void;
  onMobileClose?: () => void;
}

function formatGuestLabel(id: string): string {
  const suffix = id.startsWith('guest_') ? id.slice(6) : id;
  return `游客 ${suffix.slice(0, 4)}`;
}

function getIdentity(user: AuthUser | null): { name: string; status: string; online: boolean } {
  if (!user) {
    return { name: '游客', status: '本地设备身份', online: false };
  }
  if (isGuest()) {
    return { name: formatGuestLabel(user.id), status: '本地设备身份', online: false };
  }
  return {
    name: user.username || user.email || 'User',
    status: '在线',
    online: true,
  };
}

function ExpandedChatSidebar({
  sessions,
  activeSessionId,
  user,
  settings,
  llmConfig,
  savedLLMConfig,
  personality,
  openSections,
  onToggleSection,
  onSelectSession,
  onNewChat,
  onSettingsChange,
  onLLMConfigChange,
  onLLMConfigSave,
  onOpenLLMConfigModal,
  onPersonalityChange,
  onPersonalitySave,
  onOpenSettings,
  onLogout,
  onOpenAuthModal,
  onToggleCollapse,
  onMobileClose,
}: ExpandedChatSidebarProps) {
  const isMobile = useIsMobile();
  return (
    <>
      <div className="h-16 flex items-center justify-between px-4 border-b border-laap-border flex-shrink-0">
        <div>
          <div className="font-display text-lg text-white tracking-wide">LAAP Studio</div>
          <div className="font-mono text-[10px] text-laap-text-tertiary uppercase tracking-wider">Agent Workspace</div>
        </div>
        <button
          onClick={onToggleCollapse}
          className="hidden md:block p-1.5 text-laap-text-tertiary hover:text-white transition-colors"
          title="收起左侧面板"
        >
          <PanelLeftClose size={16} />
        </button>
        <button
          onClick={onMobileClose}
          className="md:hidden p-2 text-laap-text-tertiary hover:text-white transition-colors"
          aria-label="关闭左侧面板"
        >
          <X size={18} />
        </button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-3">
          <button
            onClick={onNewChat}
            className="w-full flex items-center justify-center gap-2 py-2.5 text-sm font-medium text-laap-bg-primary bg-laap-gold rounded-sm hover:bg-laap-gold-light transition-colors min-h-[40px]"
          >
            <Plus size={16} />
            新对话
          </button>
        </div>

        <div className="px-3 pb-3">
          <div className="space-y-1">
            {sessions.length === 0 && (
              <div className="text-xs text-laap-text-tertiary px-2 py-4 text-center">暂无对话</div>
            )}
            {sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => onSelectSession(session.id)}
                className={`w-full text-left px-3 py-2.5 rounded-sm text-sm truncate transition-colors min-h-[40px] ${
                  session.id === activeSessionId
                    ? 'bg-laap-gold/10 text-laap-gold border border-laap-gold/30'
                    : 'text-laap-text-secondary hover:bg-laap-bg-tertiary hover:text-white'
                }`}
              >
                {session.title}
              </button>
            ))}
          </div>
        </div>

        <div className="p-4 border-t border-laap-border space-y-3">
          <SidebarSection
            title="Agent 能力"
            icon={Brain}
            open={openSections.agent}
            onToggle={() => onToggleSection('agent')}
          >
            <AgentToggles settings={settings} onChange={onSettingsChange} />
          </SidebarSection>

          <SidebarSection
            title="性格与记忆"
            icon={Sparkles}
            open={openSections.personality}
            onToggle={() => onToggleSection('personality')}
          >
            <PersonalityConfigPanel
              config={personality}
              onChange={onPersonalityChange}
              onSave={onPersonalitySave}
            />
          </SidebarSection>

          <SidebarSection
            title="LLM 配置"
            icon={Key}
            open={openSections.llm}
            onToggle={() => onToggleSection('llm')}
          >
            {isMobile && onOpenLLMConfigModal ? (
              <div className="space-y-2 py-1">
                <p className="text-[10px] text-laap-text-tertiary leading-relaxed">
                  手机端推荐使用弹窗配置，避免长表单滚动困难。
                </p>
                <button
                  type="button"
                  onClick={() => {
                    onMobileClose?.();
                    onOpenLLMConfigModal();
                  }}
                  className="w-full flex items-center justify-center gap-1.5 py-2 text-xs font-medium text-laap-bg-primary bg-laap-gold rounded-sm hover:bg-laap-gold-light transition-colors min-h-[36px]"
                >
                  <Key size={12} />
                  打开 LLM 配置弹窗
                </button>
              </div>
            ) : (
              <LLMConfigPanel
                config={llmConfig}
                saved={savedLLMConfig}
                onChange={onLLMConfigChange}
                onSave={onLLMConfigSave}
              />
            )}
          </SidebarSection>

          <button
            onClick={onOpenSettings}
            className="w-full flex items-center justify-center gap-2 py-2 text-xs font-medium text-laap-text-secondary border border-laap-border rounded-sm hover:text-white hover:border-laap-gold/50 hover:bg-laap-bg-tertiary/50 transition-colors min-h-[40px]"
          >
            <Settings size={14} />
            高级设置
          </button>

          <IdentityCard user={user} onLogout={onLogout} onOpenAuthModal={onOpenAuthModal} />
        </div>
      </ScrollArea>
    </>
  );
}

function IdentityCard({
  user,
  onLogout,
  onOpenAuthModal,
}: {
  user: AuthUser | null;
  onLogout: () => void;
  onOpenAuthModal: () => void;
}) {
  const identity = getIdentity(user);
  const guest = isGuest();

  return (
    <div className="rounded-sm border border-laap-border bg-laap-bg-primary/50 p-3 space-y-2">
      <div className="flex items-center gap-3">
        <div className="relative flex-shrink-0">
          <div className="w-9 h-9 rounded-full bg-laap-gold/10 border border-laap-gold/30 flex items-center justify-center">
            <User size={15} className="text-laap-gold" />
          </div>
          <span
            className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-laap-bg-primary ${
              identity.online ? 'bg-laap-emerald animate-pulse-glow' : 'bg-laap-text-tertiary'
            }`}
          />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm text-white truncate">{identity.name}</div>
          <div className="text-[10px] text-laap-text-tertiary truncate">{identity.status}</div>
        </div>
      </div>

      <button
        type="button"
        onClick={guest ? onOpenAuthModal : onLogout}
        className="w-full flex items-center justify-center gap-1.5 py-2 text-xs font-medium text-laap-text-secondary border border-laap-border rounded-sm hover:text-white hover:border-laap-gold/50 hover:bg-laap-bg-tertiary/50 transition-colors min-h-[36px]"
      >
        {guest ? <LogIn size={12} /> : <LogOut size={12} />}
        {guest ? '登录 / 注册' : '登出'}
      </button>
    </div>
  );
}

function SidebarSection({
  title,
  icon: Icon,
  open,
  onToggle,
  children,
}: {
  title: string;
  icon: typeof Brain;
  open: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <Collapsible open={open} onOpenChange={onToggle}>
      <CollapsibleTrigger asChild>
        <button
          type="button"
          className="w-full flex items-center justify-between py-2 text-left group min-h-[40px]"
        >
          <span className="font-mono text-[10px] text-laap-text-tertiary uppercase tracking-wider flex items-center gap-1.5 group-hover:text-white transition-colors">
            <Icon size={11} />
            {title}
          </span>
          <span className="text-laap-text-tertiary group-hover:text-white transition-colors">
            {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </span>
        </button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="pb-1">{children}</div>
      </CollapsibleContent>
    </Collapsible>
  );
}
