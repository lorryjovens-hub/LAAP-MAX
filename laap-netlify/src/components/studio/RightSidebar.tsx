import { useEffect, useId, useRef, useState } from 'react';
import {
  PanelRightClose,
  PanelRightOpen,
  Brain,
  Wrench,
  Cpu,
  Upload,
  Plus,
  Trash2,
  Power,
  Search,
  Key,
  Link,
  FileJson,
  Sparkles,
  ListChecks,
  Heart,
  BookOpen,
  RefreshCw,
  X,
} from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { Switch } from '@/components/ui/switch';
import { useIsMobile } from '@/hooks/use-mobile';
import type { ChatMessage } from '@/lib/chat';
import type { AppSettings } from '@/lib/settings';
import { saveAppSettings } from '@/lib/settings';
import { estimateMessageTokens } from '@/lib/contextMemory';
import { parseMcpConfigFile, addMcpServer, updateMcpServer, removeMcpServer, type McpServer } from '@/lib/mcp';
import {
  loadActivePlan,
  updateTaskStatus,
  saveActivePlan,
  formatPlanAsMarkdown,
  type TaskPlan,
} from '@/lib/taskPlanning';
import { getCareState, getRecentCareMessages, setCareEnabled, type CareMessage } from '@/lib/userCare';
import {
  getAcademicFeedState,
  getRecommendedPapers,
  searchPapers,
  setAcademicInterests,
  formatPaperAsMarkdown,
  type PaperAnalysis,
} from '@/lib/academicUpdate';

import {
  installBuiltinSkill,
  uninstallSkill,
  setSkillEnabled,
  installSkill,
  parseSkillManifest,
  BUILTIN_SKILLS,
  type SkillManifest,
} from '@/lib/skills';

interface RightSidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  settings: AppSettings;
  onSettingsChange: (settings: AppSettings) => void;
  messages: ChatMessage[];
  mcpServers: McpServer[];
  onMcpChange: () => void;
  skills: SkillManifest[];
  onSkillsChange: () => void;
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

const ONE_MILLION = 1_000_000;

export function RightSidebar({
  collapsed,
  onToggleCollapse,
  settings,
  onSettingsChange,
  messages,
  mcpServers,
  onMcpChange,
  skills,
  onSkillsChange,
  mobileOpen = false,
  onMobileClose,
}: RightSidebarProps) {
  const isMobile = useIsMobile();
  const careSwitchId = useId();
  const [openSections, setOpenSections] = useState({ context: true, tools: true, skills: true, plan: false, care: false, papers: false });
  const [activePlan, setActivePlan] = useState<TaskPlan | null>(null);
  const [careMessages, setCareMessages] = useState<CareMessage[]>([]);
  const [careEnabled, setCareEnabledState] = useState(true);
  const [paperQuery, setPaperQuery] = useState('');
  const [papers, setPapers] = useState<PaperAnalysis[]>([]);
  const [paperLoading, setPaperLoading] = useState(false);
  const [interestsInput, setInterestsInput] = useState('');
  const mcpRef = useRef<HTMLInputElement>(null);
  const skillRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      const [plan, care, careState, feedState] = await Promise.all([
        loadActivePlan(),
        getRecentCareMessages(5),
        getCareState(),
        getAcademicFeedState(),
      ]);
      if (!mounted) return;
      setActivePlan(plan);
      setCareMessages(care);
      setCareEnabledState(careState.enabled);
      setInterestsInput(feedState.interests.join(', '));
    })();
    return () => {
      mounted = false;
    };
  }, []);

  function toggleSection(key: keyof typeof openSections) {
    setOpenSections((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  async function handleToggleTask(taskId: string) {
    if (!activePlan) return;
    const task = activePlan.tasks.find((t) => t.id === taskId);
    if (!task) return;
    const nextStatus = task.status === 'completed' ? 'pending' : 'completed';
    const updated = updateTaskStatus(activePlan, taskId, nextStatus);
    await saveActivePlan(updated);
    setActivePlan(updated);
  }

  async function handleToggleCareEnabled(enabled: boolean) {
    await setCareEnabled(enabled);
    setCareEnabledState(enabled);
  }

  async function handleSearchPapers() {
    if (!paperQuery.trim()) return;
    setPaperLoading(true);
    try {
      const list = await searchPapers(paperQuery.trim(), 5);
      setPapers(list.map((p) => ({ paper: p, summary: p.abstract.slice(0, 200), breakthroughScore: 0.5, relevanceScore: 0.5, keywords: [] })));
    } finally {
      setPaperLoading(false);
    }
  }

  async function handleRecommendPapers() {
    setPaperLoading(true);
    try {
      const list = await getRecommendedPapers(settings, 3);
      setPapers(list);
    } finally {
      setPaperLoading(false);
    }
  }

  async function handleSaveInterests() {
    const interests = interestsInput.split(/[,，]/).map((s) => s.trim()).filter(Boolean);
    await setAcademicInterests(interests);
  }

  const tokenCount = messages.reduce((sum, m) => sum + estimateMessageTokens({ role: m.role, content: m.content }), 0);
  const tokenPercent = Math.min(100, Math.round((tokenCount / ONE_MILLION) * 100));

  async function updateAgentSettings(nextAgent: AppSettings['agent']) {
    const next: AppSettings = { ...settings, agent: nextAgent };
    await saveAppSettings(next);
    onSettingsChange(next);
  }

  async function handleMcpFileSave(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const servers = parseMcpConfigFile(text);
      for (const s of servers) {
        await addMcpServer(s);
      }
      onMcpChange();
    } catch (err) {
      alert(err instanceof Error ? err.message : '导入失败');
    } finally {
      if (mcpRef.current) mcpRef.current.value = '';
    }
  }

  async function toggleMcp(server: McpServer) {
    await updateMcpServer(server.id, { enabled: !server.enabled });
    onMcpChange();
  }

  async function deleteMcp(id: string) {
    await removeMcpServer(id);
    onMcpChange();
  }

  async function installBuiltin(id: string) {
    try {
      await installBuiltinSkill(id);
      onSkillsChange();
    } catch (err) {
      alert(err instanceof Error ? err.message : '安装失败');
    }
  }

  async function toggleSkill(skill: SkillManifest) {
    await setSkillEnabled(skill.id, !skill.enabled);
    onSkillsChange();
  }

  async function removeSkill(id: string) {
    await uninstallSkill(id);
    onSkillsChange();
  }

  async function handleSkillFileSave(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const manifest = parseSkillManifest(text);
      await installSkill(manifest);
      onSkillsChange();
    } catch (err) {
      alert(err instanceof Error ? err.message : '安装失败');
    } finally {
      if (skillRef.current) skillRef.current.value = '';
    }
  }

  const renderExpandedContent = ({ showMobileClose = false }: { showMobileClose?: boolean } = {}) => (
    <>
      <div className="h-16 flex items-center justify-between px-4 border-b border-laap-border flex-shrink-0">
        <div className="flex items-center gap-2">
          <Brain size={16} className="text-laap-gold" />
          <span className="text-sm font-medium text-white">上下文与工具</span>
        </div>
        <button
          onClick={onToggleCollapse}
          className="hidden md:block p-1.5 text-laap-text-tertiary hover:text-white transition-colors"
          title="收起右侧面板"
        >
          <PanelRightClose size={16} />
        </button>
        {showMobileClose && (
          <button
            onClick={onMobileClose}
            className="md:hidden p-2 min-h-[40px] min-w-[40px] flex items-center justify-center text-laap-text-tertiary hover:text-white transition-colors"
            aria-label="关闭右侧面板"
          >
            <X size={18} />
          </button>
        )}
      </div>

      <ScrollArea className="flex-1 px-4 py-4">
        <div className="space-y-5">
          {/* Context Budget */}
          <SidebarSection
            title="上下文记忆"
            icon={Brain}
            open={openSections.context}
            onToggle={() => toggleSection('context')}
          >
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs text-laap-text-secondary mb-1">
                  <span>Token 占用</span>
                  <span>{tokenCount.toLocaleString()} / {ONE_MILLION.toLocaleString()}</span>
                </div>
                <div className="h-1.5 bg-laap-bg-tertiary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-laap-gold transition-all duration-500"
                    style={{ width: `${tokenPercent}%` }}
                  />
                </div>
                <div className="mt-1 text-[10px] text-laap-text-tertiary">{tokenPercent}% · {messages.length} 条消息</div>
              </div>
              <div className="text-[10px] text-laap-text-tertiary leading-relaxed">
                采用动态上下文预算，自动保留最近的对话并在超出预算时摘要早期消息，支持百万级 token 历史。
              </div>
            </div>
          </SidebarSection>

          {/* Task Plan */}
          <SidebarSection
            title="任务计划"
            icon={ListChecks}
            open={openSections.plan}
            onToggle={() => toggleSection('plan')}
          >
            <div className="space-y-3">
              {!activePlan ? (
                <div className="text-[10px] text-laap-text-tertiary">暂无活动计划。在输入框发送 /plan 目标 即可创建。</div>
              ) : (
                <>
                  <div className="text-xs text-white font-medium">{activePlan.title}</div>
                  <div className="space-y-1.5">
                    {activePlan.tasks.slice(0, 6).map((task) => (
                      <button
                        key={task.id}
                        type="button"
                        onClick={() => handleToggleTask(task.id)}
                        className="w-full text-left flex items-start gap-2 text-[11px] text-laap-text-secondary hover:text-white transition-colors min-h-[40px]"
                      >
                        <span className={task.status === 'completed' ? 'text-laap-emerald' : 'text-laap-text-tertiary'}>
                          {task.status === 'completed' ? '✅' : '⬜'}
                        </span>
                        <span className={task.status === 'completed' ? 'line-through opacity-60' : ''}>{task.title}</span>
                      </button>
                    ))}
                  </div>
                  <button
                    type="button"
                    onClick={() => navigator.clipboard.writeText(formatPlanAsMarkdown(activePlan))}
                    className="text-[10px] text-laap-gold hover:underline min-h-[40px]"
                  >
                    复制完整计划
                  </button>
                </>
              )}
            </div>
          </SidebarSection>

          {/* User Care */}
          <SidebarSection
            title="用户关怀"
            icon={Heart}
            open={openSections.care}
            onToggle={() => toggleSection('care')}
          >
            <div className="space-y-3">
              <label htmlFor={careSwitchId} className="flex items-center justify-between min-h-[40px] cursor-pointer">
                <span className="text-[10px] text-laap-text-tertiary">启用主动关怀</span>
                <Switch
                  id={careSwitchId}
                  checked={careEnabled}
                  onCheckedChange={handleToggleCareEnabled}
                />
              </label>
              {careMessages.length === 0 ? (
                <div className="text-[10px] text-laap-text-tertiary">暂无关怀记录。</div>
              ) : (
                <div className="space-y-2">
                  {careMessages.slice(0, 3).map((m) => (
                    <div key={m.id} className="text-[10px] text-laap-text-secondary border-l-2 border-laap-gold/30 pl-2">
                      <div className="line-clamp-2">{m.text}</div>
                      <div className="text-laap-text-tertiary mt-0.5">{m.reason}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </SidebarSection>

          {/* Academic Updates */}
          <SidebarSection
            title="学术动态"
            icon={BookOpen}
            open={openSections.papers}
            onToggle={() => toggleSection('papers')}
          >
            <div className="space-y-3">
              <div className="space-y-1.5">
                <label className="text-[10px] text-laap-text-tertiary">研究兴趣（用逗号分隔）</label>
                <div className="flex gap-1.5">
                  <input
                    type="text"
                    value={interestsInput}
                    onChange={(e) => setInterestsInput(e.target.value)}
                    placeholder="LLM, agent, reasoning"
                    className="flex-1 bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1 text-[11px] text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                  />
                  <button
                    type="button"
                    onClick={handleSaveInterests}
                    className="px-2 py-1 text-[10px] border border-laap-border rounded-sm text-laap-text-secondary hover:text-white hover:border-laap-gold/50 transition-colors min-h-[40px]"
                  >
                    保存
                  </button>
                </div>
              </div>

              <div className="flex gap-1.5">
                <input
                  type="text"
                  value={paperQuery}
                  onChange={(e) => setPaperQuery(e.target.value)}
                  placeholder="搜索 arXiv 论文"
                  className="flex-1 bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1 text-[11px] text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                />
                <button
                  type="button"
                  onClick={handleSearchPapers}
                  disabled={paperLoading}
                  className="px-2 py-1 text-[10px] border border-laap-border rounded-sm text-laap-text-secondary hover:text-white hover:border-laap-gold/50 transition-colors disabled:opacity-50 min-h-[40px] min-w-[40px] flex items-center justify-center"
                  aria-label="搜索论文"
                >
                  <Search size={11} />
                </button>
              </div>

              <button
                type="button"
                onClick={handleRecommendPapers}
                disabled={paperLoading}
                className="w-full flex items-center justify-center gap-1.5 py-1.5 text-xs border border-laap-border rounded-sm text-laap-text-secondary hover:text-white hover:border-laap-gold/50 transition-colors disabled:opacity-50 min-h-[40px]"
              >
                <RefreshCw size={12} className={paperLoading ? 'animate-spin' : ''} />
                获取推荐
              </button>

              {papers.length > 0 && (
                <div className="space-y-2 max-h-60 overflow-y-auto pr-1 custom-scrollbar">
                  {papers.map((a, i) => (
                    <div key={a.paper.id + i} className="text-[10px] text-laap-text-secondary border border-laap-border rounded-sm p-2 bg-laap-bg-tertiary/20">
                      <div className="font-medium text-white mb-1">{a.paper.title}</div>
                      <div className="line-clamp-3 mb-1">{a.summary}</div>
                      <div className="flex items-center justify-between text-laap-text-tertiary">
                        <span>{a.paper.publishedAt.slice(0, 10)}</span>
                        <button
                          type="button"
                          onClick={() => navigator.clipboard.writeText(formatPaperAsMarkdown(a))}
                          className="text-laap-gold hover:underline min-h-[40px]"
                        >
                          复制
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </SidebarSection>

          {/* Tools */}
          <SidebarSection
            title="工具集成"
            icon={Wrench}
            open={openSections.tools}
            onToggle={() => toggleSection('tools')}
          >
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-[10px] text-laap-text-tertiary uppercase tracking-wider flex items-center gap-1.5">
                  <Link size={11} />
                  CORS 代理
                </label>
                <input
                  type="text"
                  value={settings.agent.corsProxyUrl}
                  onChange={(e) =>
                    updateAgentSettings({ ...settings.agent, corsProxyUrl: e.target.value })
                  }
                  placeholder="https://api.allorigins.win/raw?url="
                  className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-xs text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                />
                <div className="text-[10px] text-laap-text-tertiary">留空将使用内置公共代理。</div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] text-laap-text-tertiary uppercase tracking-wider flex items-center gap-1.5">
                  <Search size={11} />
                  网络搜索
                </label>
                <div className="relative">
                  <Key size={12} className="absolute left-2 top-1/2 -translate-y-1/2 text-laap-text-tertiary" />
                  <input
                    type="password"
                    value={settings.agent.webSearchApiKey}
                    onChange={(e) =>
                      updateAgentSettings({ ...settings.agent, webSearchApiKey: e.target.value })
                    }
                    placeholder="Serper.dev API Key"
                    className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm pl-7 pr-2 py-1.5 text-xs text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
                  />
                </div>
                <div className="text-[10px] text-laap-text-tertiary">配置后 LAAP 可在对话中实时搜索网络。</div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] text-laap-text-tertiary uppercase tracking-wider flex items-center gap-1.5">
                  <Cpu size={11} />
                  MCP 服务器
                </label>
                <input
                  ref={mcpRef}
                  type="file"
                  accept=".json,application/json"
                  onChange={handleMcpFileSave}
                  className="hidden"
                />
                <button
                  onClick={() => mcpRef.current?.click()}
                  className="w-full flex items-center justify-center gap-1.5 py-1.5 text-xs border border-laap-border rounded-sm text-laap-text-secondary hover:text-white hover:border-laap-gold/50 transition-colors min-h-[40px]"
                >
                  <Upload size={12} />
                  上传 MCP 配置
                </button>
                <div className="space-y-1.5">
                  {mcpServers.length === 0 && (
                    <div className="text-[10px] text-laap-text-tertiary py-1">暂无 MCP 服务器</div>
                  )}
                  {mcpServers.map((server) => (
                    <div
                      key={server.id}
                      className="flex items-center justify-between px-2 py-1.5 text-xs border border-laap-border rounded-sm bg-laap-bg-tertiary/30"
                    >
                      <div className="min-w-0">
                        <div className="truncate text-laap-text-secondary">{server.name}</div>
                        <div className="text-[10px] text-laap-text-tertiary uppercase">{server.transport}</div>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => toggleMcp(server)}
                          className={`p-2 rounded-sm transition-colors min-h-[40px] min-w-[40px] flex items-center justify-center ${server.enabled ? 'text-laap-emerald' : 'text-laap-text-tertiary'}`}
                          title={server.enabled ? '已启用' : '已禁用'}
                          aria-label={server.enabled ? '已启用' : '已禁用'}
                        >
                          <Power size={14} />
                        </button>
                        <button
                          onClick={() => deleteMcp(server.id)}
                          className="p-2 text-laap-text-tertiary hover:text-laap-rose transition-colors min-h-[40px] min-w-[40px] flex items-center justify-center"
                          title="删除"
                          aria-label="删除"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </SidebarSection>

          {/* Skills */}
          <SidebarSection
            title="技能管理"
            icon={Sparkles}
            open={openSections.skills}
            onToggle={() => toggleSection('skills')}
          >
            <div className="space-y-3">
              <div className="grid grid-cols-1 gap-1.5">
                {BUILTIN_SKILLS.map((builtin) => {
                  const installed = skills.find((s) => s.id === builtin.id);
                  return (
                    <button
                        key={builtin.id}
                        onClick={() => installBuiltin(builtin.id)}
                        disabled={!!installed}
                      className="flex items-center justify-between px-2 py-1.5 text-xs border border-laap-border rounded-sm text-laap-text-secondary hover:text-white hover:border-laap-gold/50 transition-colors disabled:opacity-50 min-h-[40px]"
                    >
                      <span className="truncate">{builtin.name}</span>
                      {installed ? (
                        <span className="text-[10px] text-laap-emerald">已安装</span>
                      ) : (
                        <Plus size={12} />
                      )}
                    </button>
                  );
                })}
              </div>

              <input
                ref={skillRef}
                type="file"
                accept=".json,application/json"
                onChange={handleSkillFileSave}
                className="hidden"
              />
              <button
                onClick={() => skillRef.current?.click()}
                className="w-full flex items-center justify-center gap-1.5 py-1.5 text-xs border border-laap-border rounded-sm text-laap-text-secondary hover:text-white hover:border-laap-gold/50 transition-colors min-h-[40px]"
              >
                <FileJson size={12} />
                安装自定义技能
              </button>

              <div className="space-y-1.5">
                {skills.length === 0 && (
                  <div className="text-[10px] text-laap-text-tertiary py-1">暂无已安装技能</div>
                )}
                {skills.map((skill) => (
                  <div
                    key={skill.id}
                    className="flex items-center justify-between px-2 py-1.5 text-xs border border-laap-border rounded-sm bg-laap-bg-tertiary/30"
                  >
                    <div className="min-w-0">
                      <div className="truncate text-laap-text-secondary">{skill.name}</div>
                      <div className="text-[10px] text-laap-text-tertiary truncate">{skill.description}</div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Switch
                        checked={skill.enabled}
                        onCheckedChange={() => toggleSkill(skill)}
                      />
                      <button
                        onClick={() => removeSkill(skill.id)}
                        className="p-2 text-laap-text-tertiary hover:text-laap-rose transition-colors min-h-[40px] min-w-[40px] flex items-center justify-center"
                        title="卸载"
                        aria-label="卸载"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </SidebarSection>
        </div>
      </ScrollArea>
    </>
  );

  if (collapsed) {
    return (
      <aside className="hidden md:flex w-12 flex-col items-center border-l border-laap-border bg-laap-bg-secondary/50 py-3">
        <button
          onClick={onToggleCollapse}
          className="p-2 text-laap-text-tertiary hover:text-white transition-colors"
          title="展开右侧面板"
        >
          <PanelRightOpen size={18} />
        </button>
      </aside>
    );
  }

  return (
    <>
      <aside className="hidden md:flex w-[300px] flex-col border-l border-laap-border bg-laap-bg-secondary/50">
        {renderExpandedContent()}
      </aside>

      {isMobile && (
        <Sheet open={mobileOpen} onOpenChange={(open) => !open && onMobileClose?.()}>
          <SheetContent
            side="right"
            className="w-[300px] p-0 bg-laap-bg-secondary/95 border-l border-laap-border [&>button]:hidden"
          >
            <SheetHeader className="sr-only">
              <SheetTitle>右侧面板</SheetTitle>
              <SheetDescription>上下文、工具集成与技能管理</SheetDescription>
            </SheetHeader>
            {renderExpandedContent({ showMobileClose: true })}
          </SheetContent>
        </Sheet>
      )}
    </>
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
            {open ? <PanelRightOpen size={14} /> : <PanelRightClose size={14} />}
          </span>
        </button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="pb-1">{children}</div>
      </CollapsibleContent>
    </Collapsible>
  );
}
