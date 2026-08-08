import { useEffect, useRef, useState, useCallback } from 'react';
import { Heart, ThumbsUp, ThumbsDown, X } from 'lucide-react';
import { getCurrentUser, logout, updateUsername } from '@/lib/auth';
import { useVoiceChat } from '@/hooks/useVoiceChat';
import type { User as AuthUser } from '@/lib/auth';
import { onUserChange } from '@/lib/userMode';
import { ChatSidebar } from '@/components/studio/ChatSidebar';
import { AuthModal } from '@/components/auth/AuthModal';
import { ChatHeader } from '@/components/studio/ChatHeader';
import { ChatCanvas } from '@/components/studio/ChatCanvas';
import { ChatInput } from '@/components/studio/ChatInput';
import { RightSidebar } from '@/components/studio/RightSidebar';
import { CodeWorkbench } from '@/components/studio/CodeWorkbench';
import { SettingsModal } from '@/components/studio/SettingsModal';
import { LLMConfigModal } from '@/components/studio/LLMConfigModal';
import { FirstRunModal } from '@/components/studio/FirstRunModal';
import type { ChatSession, ChatMessage, ChatAttachment } from '@/lib/chat';
import { createSession, listSessions, getSessionMessages, streamChatMessage, sendChatMessage, updateMessageFeedback } from '@/lib/chat';
import type { LlmConfig } from '@/lib/llmConfig';
import {
  DEFAULT_LLM_CONFIG,
  getLlmConfig,
  saveLlmConfig,
  hasLlmBeenConfigured,
  markLlmConfigured,
  buildSenseNovaProvider,
  getActiveProvider,
  isFreeOrKeylessProvider,
} from '@/lib/llmConfig';
import type { PersonalityConfig } from '@/lib/personality';
import { DEFAULT_PERSONALITY, getPersonalityConfig, savePersonalityConfig } from '@/lib/personality';
import {
  formatPlanAsMarkdown,
  formatSpecAsMarkdown,
  generatePlanOrSpec,
  parseCommand,
  saveActivePlan,
} from '@/lib/taskPlanning';
import { generateCareMessage, recordCareFeedback, type CareMessage } from '@/lib/userCare';
import { encodeSharedChat, buildShareUrl } from '@/lib/share';
import { DEFAULT_APP_SETTINGS, getAppSettings, saveAppSettings, type AppSettings } from '@/lib/settings';
import type { TtsConfig, AsrConfig } from '@/lib/audioConfig';
import {
  DEFAULT_TTS_CONFIG,
  DEFAULT_ASR_CONFIG,
  getTtsConfig,
  getAsrConfig,
  saveTtsConfig,
  saveAsrConfig,
} from '@/lib/audioConfig';
import { getFocusMode, saveFocusMode } from '@/lib/focusMode';
import { listMcpServers, type McpServer } from '@/lib/mcp';
import { listInstalledSkills, type SkillManifest } from '@/lib/skills';
import { onSyncEvent } from '@/lib/syncManager';
import { getStructuredMemories } from '@/lib/memoryManager';
import { onActiveCodeProjectChange } from '@/lib/codeAgentTools';

export default function StudioPage() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [model, setModel] = useState('laap-fast');
  const [llmConfig, setLLMConfig] = useState<LlmConfig>(DEFAULT_LLM_CONFIG);
  const llmConfigRef = useRef(llmConfig);
  const [savedLLMConfig, setSavedLLMConfig] = useState<LlmConfig | null>(null);

  useEffect(() => {
    llmConfigRef.current = llmConfig;
  }, [llmConfig]);
  const [personality, setPersonality] = useState<PersonalityConfig>(DEFAULT_PERSONALITY);
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_APP_SETTINGS);
  const [ttsConfig, setTTSConfig] = useState<TtsConfig>(DEFAULT_TTS_CONFIG);
  const [asrConfig, setASRConfig] = useState<AsrConfig>(DEFAULT_ASR_CONFIG);
  const [savedTTSConfig, setSavedTTSConfig] = useState<TtsConfig | null>(null);
  const [savedASRConfig, setSavedASRConfig] = useState<AsrConfig | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [llmConfigModalOpen, setLLMConfigModalOpen] = useState(false);
  const [firstRunOpen, setFirstRunOpen] = useState(false);
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [leftMobileOpen, setLeftMobileOpen] = useState(false);
  const [rightMobileOpen, setRightMobileOpen] = useState(false);
  const [focusMode, setFocusMode] = useState(false);
  const [workbenchOpen, setWorkbenchOpen] = useState(false);
  const [activeCodeProjectId, setActiveCodeProjectId] = useState<string | null>(null);
  const [webSearchEnabled, setWebSearchEnabled] = useState(false);
  const [mcpServers, setMcpServers] = useState<McpServer[]>([]);
  const [skills, setSkills] = useState<SkillManifest[]>([]);
  const [careMessage, setCareMessage] = useState<CareMessage | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const handleSendRef = useRef<(text: string, attachments: ChatAttachment[]) => void>(() => {});
  const lastSpokenContentRef = useRef('');

  // Voice chat hook — uses a ref for onTranscript to avoid stale closure issues
  const voice = useVoiceChat({
    language: 'zh-CN',
    continuousMode: false,
    bargeInEnabled: true,
    ttsEnabled: true,
    onTranscript: useCallback((text: string) => {
      if (text.trim()) {
        requestAnimationFrame(() => {
          handleSendRef.current(text.trim(), []);
        });
      }
    }, []),
    onStateChange: useCallback((state) => {
      // Voice state changes are handled via the return value
    }, []),
  });

  // Keep handleSendRef up-to-date with the latest handleSend
  useEffect(() => {
    handleSendRef.current = handleSend;
  });

  // Auto-speak the latest assistant message when it arrives
  const prevMessagesLengthRef = useRef(messages.length);
  useEffect(() => {
    if (messages.length > prevMessagesLengthRef.current && messages.length > 0) {
      const lastMsg = messages[messages.length - 1];
      if (lastMsg.role === 'assistant' && lastMsg.content && !loading) {
        const content = lastMsg.content;
        if (content !== lastSpokenContentRef.current) {
          lastSpokenContentRef.current = content;
          voice.speak(content);
        }
      }
    }
    prevMessagesLengthRef.current = messages.length;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages, loading, voice.speak]);

  useEffect(() => {
    let mounted = true;

    async function resetStudioState() {
      abortRef.current?.abort();
      abortRef.current = null;
      setActiveSessionId(null);
      setSessions([]);
      setMessages([]);
      setError(null);
      setCareMessage(null);
      setLLMConfig(DEFAULT_LLM_CONFIG);
      setSavedLLMConfig(null);
      setPersonality(DEFAULT_PERSONALITY);
      setSettings(DEFAULT_APP_SETTINGS);
      setTTSConfig(DEFAULT_TTS_CONFIG);
      setASRConfig(DEFAULT_ASR_CONFIG);
      setSavedTTSConfig(null);
      setSavedASRConfig(null);

      const u = await getCurrentUser();
      if (!mounted) return;
      setUser(u);
      await loadSessions();
      if (mounted) await loadLLMConfig();
      if (mounted) await loadPersonality();
      if (mounted) await loadSettings();
      if (mounted) await loadAudioConfig();
      if (mounted) await loadTools();
      if (mounted && u) await loadMemories(u.id);
      if (mounted) {
        try {
          const savedFocus = await getFocusMode(u?.id);
          setFocusMode(savedFocus);
        } catch {
          // ignore focus mode load errors
        }
      }

      // First-run modal: shows once per browser (localStorage flag) when no
      // LLM provider has been configured yet.
      if (mounted && !hasLlmBeenConfigured()) {
        const cfg = await getLlmConfig(u?.id);
        if (mounted && cfg.providers.length === 0) {
          setFirstRunOpen(true);
        } else if (mounted) {
          // Already has a provider — mark configured so the modal never shows.
          markLlmConfigured();
        }
      }
    }

    resetStudioState();
    const unsubscribe = onUserChange(() => {
      if (mounted) resetStudioState();
    });

    return () => {
      mounted = false;
      unsubscribe();
      abortRef.current?.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const unsubscribe = onSyncEvent((event) => {
      if (event === 'session-updated') {
        void loadSessions();
        if (activeSessionId) {
          void selectSession(activeSessionId);
        }
      } else if (event === 'memory-updated') {
        void loadMemories();
      } else if (event === 'user-changed') {
        window.location.reload();
      }
    });
    return unsubscribe;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSessionId, user?.id]);

  useEffect(() => {
    void saveFocusMode(focusMode, user?.id);
  }, [focusMode, user?.id]);

  useEffect(() => {
    const unsubscribe = onActiveCodeProjectChange((id) => {
      if (id) {
        setActiveCodeProjectId(id);
        setWorkbenchOpen(true);
      }
    });
    return unsubscribe;
  }, []);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      const target = e.target as HTMLElement | null;
      const isTyping =
        target &&
        (target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.isContentEditable);

      if (e.key === 'f' || e.key === 'F') {
        if (isTyping) return;
        e.preventDefault();
        setFocusMode((prev) => !prev);
      } else if (e.key === 'Escape' && focusMode) {
        setFocusMode(false);
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [focusMode]);

  function handleToggleFocusMode() {
    setFocusMode((prev) => !prev);
  }

  async function loadSettings() {
    const cfg = await getAppSettings();
    setSettings(cfg);
    try {
      const message = await generateCareMessage(cfg);
      if (message) setCareMessage(message);
    } catch {
      // ignore care generation errors
    }
  }

  async function loadAudioConfig() {
    const [tts, asr] = await Promise.all([getTtsConfig(user?.id), getAsrConfig(user?.id)]);
    setTTSConfig(tts);
    setASRConfig(asr);
    setSavedTTSConfig(tts.providers.length > 0 ? tts : null);
    setSavedASRConfig(asr.providers.length > 0 ? asr : null);
  }

  async function loadTools() {
    try {
      const [servers, installed] = await Promise.all([listMcpServers(), listInstalledSkills()]);
      setMcpServers(servers);
      setSkills(installed);
    } catch {
      // ignore
    }
  }

  async function loadMemories(userId?: string) {
    const targetUserId = userId ?? user?.id;
    if (!targetUserId) return;
    try {
      // Re-fetch memories from storage so other windows' updates are reflected
      // in this window's memory cache (future UI can consume the data here).
      await getStructuredMemories(targetUserId, 50);
    } catch {
      // ignore memory load errors
    }
  }

  async function handleSettingsChange(next: AppSettings) {
    setSettings(next);
    try {
      await saveAppSettings(next);
    } catch {
      // ignore
    }
  }

  async function handleUsernameChange(name: string) {
    if (!name.trim()) return;
    try {
      const updated = await updateUsername(name.trim());
      if (updated) {
        setUser((u) => (u ? { ...u, username: updated.username } : u));
      }
    } catch {
      // ignore username update failures
    }
  }

  async function loadLLMConfig() {
    let cfg = await getLlmConfig(user?.id);
    // Auto-seed a free SenseNova provider so users can call models directly
    // without any manual key configuration.
    if (cfg.providers.length === 0) {
      const provider = buildSenseNovaProvider();
      cfg = { providers: [provider], activeProviderId: provider.id };
      await saveLlmConfig(cfg, user?.id);
      markLlmConfigured();
    }
    setLLMConfig(cfg);
    setSavedLLMConfig(cfg.providers.length > 0 ? cfg : null);

    // Encourage users to configure their own API Key for stable, high-quality
    // responses whenever the active provider is free/keyless.
    const active = getActiveProvider(cfg);
    if (active && isFreeOrKeylessProvider(active)) {
      setLLMConfigModalOpen(true);
    }
  }

  async function handleSaveLLMConfig(nextConfig?: LlmConfig) {
    const current = nextConfig ?? llmConfigRef.current;
    try {
      await saveLlmConfig(current, user?.id);
      setSavedLLMConfig(current.providers.length > 0 ? current : null);
      if (current.providers.length > 0) {
        markLlmConfigured();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存 LLM 配置失败');
    }
  }

  function handleOpenLLMConfig() {
    setLLMConfigModalOpen(true);
  }

  async function loadPersonality() {
    const saved = await getPersonalityConfig();
    if (saved) {
      setPersonality(saved);
    }
  }

  async function handleSavePersonality() {
    const result = await savePersonalityConfig(personality);
    if (!result.ok) {
      setError(result.error);
    }
  }

  async function loadSessions() {
    try {
      const data = await listSessions();
      setSessions(data);
      if (data.length > 0 && !activeSessionId) {
        await selectSession(data[0].id);
      }
    } catch {
      // Backend sessions may not be available; rely on local creation.
    }
  }

  async function selectSession(sessionId: string) {
    setActiveSessionId(sessionId);
    setLeftMobileOpen(false);
    setError(null);
    try {
      const history = await getSessionMessages(sessionId);
      setMessages(history);
    } catch {
      setMessages([]);
    }
  }

  async function handleNewChat() {
    try {
      const session = await createSession('新对话');
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
      setLeftMobileOpen(false);
      setMessages([]);
      inputRef.current?.focus();
    } catch {
      setError('无法创建新对话');
    }
  }

  function ensureSession(): Promise<string | null> {
    if (activeSessionId) return Promise.resolve(activeSessionId);
    return createSession('新对话').then((session) => {
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
      return session.id;
    }).catch(() => null);
  }

  async function handleCommand(mode: 'plan' | 'spec', query: string) {
    setError(null);
    const sessionId = await ensureSession();
    if (!sessionId) {
      setError('无法创建会话');
      return;
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: `/${mode} ${query}`,
    };

    const assistantMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setLoading(true);

    try {
      const cfg = llmConfig.providers.length > 0 ? llmConfig : undefined;
      if (!cfg) {
        throw new Error('请先配置 LLM API Key');
      }
      const result = await generatePlanOrSpec(query, mode, cfg);
      if (mode === 'plan' && result.plan) {
        await saveActivePlan(result.plan);
      }
      const markdown = mode === 'plan'
        ? formatPlanAsMarkdown(result.plan!)
        : formatSpecAsMarkdown(result.spec!);
      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (!last || last.role !== 'assistant') return prev;
        return [...prev.slice(0, -1), { ...last, content: markdown }];
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成失败');
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setLoading(false);
      setSessions((prev) =>
        prev.map((s) =>
          s.id === sessionId && s.title === '新对话'
            ? { ...s, title: mode === 'plan' ? '任务规划' : '需求规格', updated_at: new Date().toISOString() }
            : s
        )
      );
    }
  }

  async function handleSend(text: string, attachments: ChatAttachment[]) {
    if ((!text.trim() && attachments.length === 0) || loading) return;

    const command = parseCommand(text.trim());
    if (command.mode && attachments.length === 0) {
      await handleCommand(command.mode, command.query);
      return;
    }

    setError(null);
    const sessionId = await ensureSession();
    if (!sessionId) {
      setError('无法创建会话');
      return;
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text.trim(),
      attachments,
    };

    const assistantMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      reasoning_steps: [],
      tool_calls: [],
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setLoading(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      let streamFailed = false;
      try {
        await streamChatMessage(
          sessionId,
          userMessage.content,
          (event) => {
            setMessages((prev) => {
              const last = prev[prev.length - 1];
              if (!last || last.role !== 'assistant') return prev;

              const updated = { ...last };
              if (event.type === 'response' && typeof event.data.content === 'string') {
                updated.content = event.data.content;
              } else if (event.type === 'reasoning_step') {
                updated.reasoning_steps = [...(updated.reasoning_steps || []), event.data];
              } else if (event.type === 'tool_result') {
                updated.tool_calls = [...(updated.tool_calls || []), event.data];
              }

              return [...prev.slice(0, -1), updated];
            });
          },
          {
            signal: controller.signal,
            llmConfig,
            attachments,
            settings,
            onSettingsChange: handleSettingsChange,
          }
        );
      } catch {
        streamFailed = true;
      }

      if (streamFailed) {
        const result = await sendChatMessage(sessionId, userMessage.content, {
          llmConfig,
          attachments,
          settings,
          onSettingsChange: handleSettingsChange,
        });
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (!last || last.role !== 'assistant') return prev;
          return [
            ...prev.slice(0, -1),
            {
              ...last,
              content: result.content,
              reasoning_steps: result.reasoning_steps?.length ? result.reasoning_steps : last.reasoning_steps,
              tool_calls: result.tool_calls?.length ? result.tool_calls : last.tool_calls,
            },
          ];
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '发送失败');
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setLoading(false);
      abortRef.current = null;
      // Refresh session title if it's still "新对话" and we have messages.
      setSessions((prev) =>
        prev.map((s) =>
          s.id === sessionId && s.title === '新对话'
            ? { ...s, title: generateSessionTitle([userMessage]), updated_at: new Date().toISOString() }
            : s
        )
      );
    }
  }

  function generateSessionTitle(msgs: ChatMessage[]): string {
    const firstUser = msgs.find((m) => m.role === 'user');
    if (firstUser) {
      const text = firstUser.content.slice(0, 20);
      return text.length >= 20 ? `${text}…` : text;
    }
    return '新对话';
  }

  async function handleLogout() {
    abortRef.current?.abort();
    await logout();
    // onUserChange 监听器会自动重置 Studio 状态并切换到游客身份
  }

  async function handleFeedback(messageId: string, feedback: 'positive' | 'negative') {
    try {
      await updateMessageFeedback(messageId, feedback);
      setMessages((prev) =>
        prev.map((m) => (m.id === messageId ? { ...m, feedback } : m))
      );
    } catch {
      // ignore
    }
  }

  function handleShare() {
    if (!activeSession || messages.length === 0) {
      alert('当前没有可分享的聊天记录');
      return;
    }
    const token = encodeSharedChat(activeSession.title, messages);
    if (!token) {
      alert('聊天记录过长，无法生成分享链接');
      return;
    }
    const url = buildShareUrl(token);
    navigator.clipboard.writeText(url).then(() => {
      alert('分享链接已复制到剪贴板');
    }).catch(() => {
      prompt('请复制以下分享链接', url);
    });
  }

  async function handleCareFeedback(feedback: 'positive' | 'negative') {
    if (!careMessage) return;
    try {
      await recordCareFeedback(careMessage.id, feedback);
    } catch {
      // ignore
    }
    setCareMessage(null);
  }

  function dismissCare() {
    setCareMessage(null);
  }

  function handleOpenSettings() {
    setSettingsOpen(true);
    setLeftMobileOpen(false);
  }

  const activeSession = sessions.find((s) => s.id === activeSessionId);

  const isImageBg = settings.ui.backgroundType === 'image';
  const isGradientBg = settings.ui.backgroundType === 'gradient';
  const isVideoBg = settings.ui.backgroundType === 'video';

  return (
    <div className="fixed inset-0 z-0 flex text-laap-text-primary bg-laap-bg-primary">
      {/* Background layer */}
      {isImageBg && settings.ui.backgroundValue && (
        <div
          className="absolute inset-0 -z-20"
          style={{
            backgroundImage: `url(${settings.ui.backgroundValue})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundRepeat: 'no-repeat',
            opacity: settings.ui.backgroundOpacity,
          }}
        />
      )}
      {isGradientBg && (
        <div
          className="absolute inset-0 -z-20"
          style={{ background: settings.ui.backgroundValue }}
        />
      )}
      {isVideoBg && settings.ui.backgroundVideo && (
        <video
          src={settings.ui.backgroundVideo}
          autoPlay
          loop
          muted
          playsInline
          className="absolute inset-0 w-full h-full object-cover -z-20"
        />
      )}

      <div className={focusMode ? 'hidden' : 'contents'}>
        <ChatSidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          user={user}
          settings={settings}
          llmConfig={llmConfig}
          savedLLMConfig={savedLLMConfig}
          personality={personality}
          collapsed={leftCollapsed}
          onToggleCollapse={() => setLeftCollapsed((v) => !v)}
          onSelectSession={selectSession}
          onNewChat={handleNewChat}
          onSettingsChange={handleSettingsChange}
          onLLMConfigChange={setLLMConfig}
          onLLMConfigSave={handleSaveLLMConfig}
          onOpenLLMConfigModal={handleOpenLLMConfig}
          onPersonalityChange={setPersonality}
          onPersonalitySave={handleSavePersonality}
          onOpenSettings={handleOpenSettings}
          onLogout={handleLogout}
          onOpenAuthModal={() => setAuthModalOpen(true)}
          mobileOpen={leftMobileOpen}
          onMobileClose={() => setLeftMobileOpen(false)}
        />
      </div>

      {/* Main area */}
      <main className={`flex-1 flex flex-col min-w-0 bg-laap-bg-primary/60 backdrop-blur-[1px] ${leftMobileOpen ? 'overflow-hidden' : ''}`}>
        {careMessage && !focusMode && (
          <div className="mx-4 mt-3 px-3 py-2 rounded-sm border border-laap-gold/30 bg-laap-gold/10 backdrop-blur-sm flex items-start gap-3">
            <Heart size={16} className="text-laap-gold mt-0.5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="text-xs text-white leading-relaxed">{careMessage.text}</div>
              <div className="text-[10px] text-laap-text-tertiary mt-1">{careMessage.reason}</div>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => handleCareFeedback('positive')}
                className="p-1 text-laap-text-tertiary hover:text-laap-emerald transition-colors"
                title="有用"
              >
                <ThumbsUp size={14} />
              </button>
              <button
                type="button"
                onClick={() => handleCareFeedback('negative')}
                className="p-1 text-laap-text-tertiary hover:text-laap-rose transition-colors"
                title="无用"
              >
                <ThumbsDown size={14} />
              </button>
              <button
                type="button"
                onClick={dismissCare}
                className="p-1 text-laap-text-tertiary hover:text-white transition-colors"
                title="关闭"
              >
                <X size={14} />
              </button>
            </div>
          </div>
        )}

        <ChatHeader
          title={activeSession?.title || '新对话'}
          model={model}
          agentName={personality.agentName || personality.name || 'LAAP'}
          onModelChange={setModel}
          user={user}
          onLogout={handleLogout}
          onNewChat={handleNewChat}
          onOpenAuthModal={() => setAuthModalOpen(true)}
          onOpenLeftSidebar={() => setLeftMobileOpen(true)}
          onOpenRightSidebar={() => setRightMobileOpen(true)}
          onOpenLLMConfig={handleOpenLLMConfig}
          focusMode={focusMode}
          onToggleFocusMode={handleToggleFocusMode}
          onShare={handleShare}
          workbenchOpen={workbenchOpen}
          onToggleWorkbench={() => setWorkbenchOpen((v) => !v)}
        />

        <div className="flex-1 flex flex-col min-h-0">
          <ChatCanvas
            messages={messages}
            loading={loading}
            userAvatar={settings.ui.userAvatar}
            robotAvatar={settings.ui.robotAvatar}
            agentName={personality.agentName || personality.name || 'LAAP'}
            onFeedback={handleFeedback}
            onSpeak={voice.speak}
            isSpeaking={voice.isSpeaking}
          />

          {workbenchOpen && (
            <div className="h-[420px] border-t border-laap-border bg-laap-bg-secondary">
              <CodeWorkbench initialProjectId={activeCodeProjectId ?? undefined} onClose={() => setWorkbenchOpen(false)} />
            </div>
          )}
        </div>

        {error && (
          <div className="px-4 py-2 mx-4 mb-2 text-xs text-laap-rose bg-laap-rose/10 border border-laap-rose/30 rounded-sm">
            {error}
          </div>
        )}

        <ChatInput
          onSend={handleSend}
          loading={loading}
          ref={inputRef}
          enterToSend={settings.general.enterToSend}
          focusMode={focusMode}
          webSearch={webSearchEnabled}
          onWebSearchChange={setWebSearchEnabled}
          voiceState={voice.state}
          voiceSupported={voice.isSupported}
          voiceContinuousEnabled={voice.continuousEnabled}
          onVoiceToggleListening={voice.toggleListening}
          onVoiceToggleContinuous={voice.toggleContinuous}
          onVoiceStopSpeaking={voice.stopSpeaking}
        />
      </main>

      <div className={focusMode ? 'hidden' : 'contents'}>
        <RightSidebar
          collapsed={rightCollapsed}
          onToggleCollapse={() => setRightCollapsed((v) => !v)}
          settings={settings}
          onSettingsChange={handleSettingsChange}
          messages={messages}
          mcpServers={mcpServers}
          onMcpChange={loadTools}
          skills={skills}
          onSkillsChange={loadTools}
          mobileOpen={rightMobileOpen}
          onMobileClose={() => setRightMobileOpen(false)}
        />
      </div>

      <SettingsModal
        settings={settings}
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
        onSave={handleSettingsChange}
        username={user?.username}
        onUsernameChange={handleUsernameChange}
        sessionTitle={activeSession?.title}
        sessionMessages={messages}
        ttsConfig={ttsConfig}
        asrConfig={asrConfig}
        onTtsConfigChange={setTTSConfig}
        onAsrConfigChange={setASRConfig}
        onTtsConfigSave={async (next) => {
          const cfg = next ?? ttsConfig;
          await saveTtsConfig(cfg, user?.id);
          setSavedTTSConfig(cfg.providers.length > 0 ? cfg : null);
        }}
        onAsrConfigSave={async (next) => {
          const cfg = next ?? asrConfig;
          await saveAsrConfig(cfg, user?.id);
          setSavedASRConfig(cfg.providers.length > 0 ? cfg : null);
        }}
      />

      <LLMConfigModal
        open={llmConfigModalOpen}
        onOpenChange={setLLMConfigModalOpen}
        config={llmConfig}
        onChange={setLLMConfig}
        onSave={handleSaveLLMConfig}
        title="配置你的 LLM API Key"
        description="使用自己的 API Key 可获得更稳定、更高质量的回复，且不受免费额度限制。你也可以继续选择免费的 SenseNova 或 OmniRoute。"
      />

      <FirstRunModal
        open={firstRunOpen}
        onOpenChange={setFirstRunOpen}
        config={llmConfig}
        onChange={setLLMConfig}
        onSave={handleSaveLLMConfig}
      />

      <AuthModal
        open={authModalOpen}
        onOpenChange={setAuthModalOpen}
        onSuccess={() => {
          setAuthModalOpen(false);
          void loadSessions();
        }}
      />
    </div>
  );
}
