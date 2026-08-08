import { useEffect, useId, useRef, useState } from 'react';
import { Settings, Image as ImageIcon, Save, X, FileDown, FileCode2, BrainCircuit, Volume2, Mic } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import type { AppSettings, BackgroundType } from '@/lib/settings';
import type { ChatMessage } from '@/lib/chat';
import {
  exportChatAsMarkdown,
  exportChatAsHtml,
  exportMemoriesAsMarkdown,
  exportMemoriesAsHtml,
  downloadTextFile,
} from '@/lib/export';
import { getCurrentUser } from '@/lib/userMode';
import { getStructuredMemories } from '@/lib/memoryManager';
import type { TtsConfig, AsrConfig } from '@/lib/audioConfig';
import {
  DEFAULT_TTS_CONFIG,
  DEFAULT_ASR_CONFIG,
  getTtsConfig,
  getAsrConfig,
  saveTtsConfig,
  saveAsrConfig,
} from '@/lib/audioConfig';
import { TTSConfigPanel } from '@/components/studio/TTSConfigPanel';
import { ASRConfigPanel } from '@/components/studio/ASRConfigPanel';

interface SettingsModalProps {
  settings: AppSettings;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (settings: AppSettings) => void | Promise<void>;
  username?: string;
  onUsernameChange?: (name: string) => void;
  sessionTitle?: string;
  sessionMessages?: ChatMessage[];
  ttsConfig?: TtsConfig;
  asrConfig?: AsrConfig;
  onTtsConfigChange?: (config: TtsConfig) => void;
  onAsrConfigChange?: (config: AsrConfig) => void;
  onTtsConfigSave?: (config?: TtsConfig) => void | Promise<void>;
  onAsrConfigSave?: (config?: AsrConfig) => void | Promise<void>;
}

const TABS = [
  { value: 'general', label: '通用' },
  { value: 'llm', label: 'LLM' },
  { value: 'tts', label: 'TTS' },
  { value: 'asr', label: 'ASR' },
  { value: 'ui', label: '界面' },
  { value: 'data', label: '数据' },
  { value: 'agent', label: 'Agent' },
  { value: 'memory', label: '记忆' },
  { value: 'influence', label: 'LAAP' },
] as const;

export function SettingsModal({
  settings, open, onOpenChange, onSave, username, onUsernameChange,
  sessionTitle, sessionMessages,
  ttsConfig: ttsConfigProp, asrConfig: asrConfigProp,
  onTtsConfigChange, onAsrConfigChange,
  onTtsConfigSave, onAsrConfigSave,
}: SettingsModalProps) {
  const [draft, setDraft] = useState<AppSettings>(settings);
  const [userName, setUserName] = useState(username ?? '');
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState<'chat-md' | 'chat-html' | 'mem-md' | 'mem-html' | null>(null);
  const [ttsConfig, setTtsConfig] = useState<TtsConfig>(ttsConfigProp ?? DEFAULT_TTS_CONFIG);
  const [asrConfig, setAsrConfig] = useState<AsrConfig>(asrConfigProp ?? DEFAULT_ASR_CONFIG);
  const fileRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLInputElement>(null);
  const userAvatarRef = useRef<HTMLInputElement>(null);
  const robotAvatarRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setDraft(settings); // eslint-disable-line react-hooks/set-state-in-effect
      setUserName(username ?? '');
      setTtsConfig(ttsConfigProp ?? DEFAULT_TTS_CONFIG);
      setAsrConfig(asrConfigProp ?? DEFAULT_ASR_CONFIG);
    }
  }, [open, settings, username, ttsConfigProp, asrConfigProp]);

  function updateSection<K extends keyof AppSettings>(section: K, patch: Partial<AppSettings[K]>) {
    setDraft((prev) => ({ ...prev, [section]: { ...prev[section], ...patch } } as AppSettings));
  }

  async function handleSave() {
    setSaving(true);
    try {
      await onSave(draft);
      if (onUsernameChange) {
        onUsernameChange(userName);
      }
      onOpenChange(false);
    } finally {
      setSaving(false);
    }
  }

  function handleExportChat(format: 'md' | 'html') {
    if (!sessionMessages || sessionMessages.length === 0) {
      alert('当前没有可导出的聊天记录');
      return;
    }
    const title = sessionTitle?.trim() || 'LAAP 对话';
    const safeTitle = title.replace(/[\\/:*?"<>|]/g, '_');
    const stamp = new Date().toISOString().slice(0, 10);
    if (format === 'md') {
      const content = exportChatAsMarkdown(title, sessionMessages, userName || '用户');
      downloadTextFile(`${safeTitle}_${stamp}.md`, content, 'text/markdown');
    } else {
      const content = exportChatAsHtml(title, sessionMessages, userName || '用户');
      downloadTextFile(`${safeTitle}_${stamp}.html`, content, 'text/html');
    }
  }

  async function handleExportMemories(format: 'md' | 'html') {
    setExporting(format === 'md' ? 'mem-md' : 'mem-html');
    try {
      const user = await getCurrentUser();
      const memories = await getStructuredMemories(user.id, 200);
      if (memories.length === 0) {
        alert('暂无记忆数据可导出');
        return;
      }
      const stamp = new Date().toISOString().slice(0, 10);
      const name = userName || user.username || '用户';
      if (format === 'md') {
        const content = exportMemoriesAsMarkdown(memories, name);
        downloadTextFile(`LAAP记忆备份_${stamp}.md`, content, 'text/markdown');
      } else {
        const content = exportMemoriesAsHtml(memories, name);
        downloadTextFile(`LAAP记忆备份_${stamp}.html`, content, 'text/html');
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : '导出记忆失败');
    } finally {
      setExporting(null);
    }
  }

  function handleBackgroundFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      alert('图片过大，请选择小于 5MB 的文件');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result ?? '');
      updateSection('ui', {
        backgroundType: 'image',
        backgroundValue: result,
      });
    };
    reader.readAsDataURL(file);
  }

  function handleVideoFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 50 * 1024 * 1024) {
      alert('视频过大，请选择小于 50MB 的文件');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result ?? '');
      updateSection('ui', {
        backgroundType: 'video',
        backgroundVideo: result,
        backgroundValue: '',
      });
    };
    reader.readAsDataURL(file);
  }

  function handleAvatarFile(e: React.ChangeEvent<HTMLInputElement>, key: 'userAvatar' | 'robotAvatar') {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      alert('头像过大，请选择小于 2MB 的文件');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      updateSection('ui', { [key]: String(reader.result ?? '') });
    };
    reader.readAsDataURL(file);
  }

  const bgPreview =
    draft.ui.backgroundType === 'image'
      ? `url(${draft.ui.backgroundValue})`
      : draft.ui.backgroundType === 'gradient'
      ? draft.ui.backgroundValue
      : draft.ui.backgroundType === 'video'
      ? 'transparent'
      : draft.ui.backgroundValue;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] p-0 overflow-hidden flex flex-col">
        <DialogHeader className="px-6 pt-6 pb-2">
          <DialogTitle className="flex items-center gap-2 text-white">
            <Settings size={18} />
            LAAP 设置
          </DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="general" className="flex-1 flex flex-col min-h-0">
          <div className="px-6 pb-2">
            <TabsList className="grid grid-cols-5 sm:grid-cols-9 w-full bg-laap-bg-tertiary/50">
              {TABS.map((t) => (
                <TabsTrigger
                  key={t.value}
                  value={t.value}
                  className="text-xs data-[state=active]:bg-laap-bg-secondary data-[state=active]:text-laap-gold min-h-[40px]"
                >
                  {t.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </div>

          <div className="flex-1 overflow-y-auto px-6 pb-4">
            {/* 通用 */}
            <TabsContent value="general" className="space-y-4 mt-2">
              <SettingGroup title="实例信息">
                <TextField
                  label="用户名"
                  value={userName}
                  onChange={setUserName}
                  placeholder={username || '你的名字'}
                />
                <TextField
                  label="实例名称"
                  value={draft.general.instanceName}
                  onChange={(v) => updateSection('general', { instanceName: v })}
                />
                <SelectField
                  label="语言"
                  value={draft.general.language}
                  onChange={(v) => updateSection('general', { language: v as AppSettings['general']['language'] })}
                  options={[
                    { value: 'zh', label: '中文' },
                    { value: 'en', label: 'English' },
                    { value: 'auto', label: '自动' },
                  ]}
                />
              </SettingGroup>
              <SettingGroup title="交互">
                <SwitchField
                  label="自动保存"
                  checked={draft.general.autoSave}
                  onChange={(v) => updateSection('general', { autoSave: v })}
                />
                <SwitchField
                  label="声音反馈"
                  checked={draft.general.sound}
                  onChange={(v) => updateSection('general', { sound: v })}
                />
                <SwitchField
                  label="Enter 发送"
                  checked={draft.general.enterToSend}
                  onChange={(v) => updateSection('general', { enterToSend: v })}
                />
              </SettingGroup>
            </TabsContent>

            {/* LLM */}
            <TabsContent value="llm" className="space-y-4 mt-2">
              <SettingGroup title="生成参数">
                <SliderField
                  label="Temperature"
                  value={draft.llm.temperature}
                  min={0}
                  max={2}
                  step={0.05}
                  format={(v) => v.toFixed(2)}
                  onChange={(v) => updateSection('llm', { temperature: v })}
                />
                <SliderField
                  label="Top P"
                  value={draft.llm.topP}
                  min={0}
                  max={1}
                  step={0.05}
                  format={(v) => v.toFixed(2)}
                  onChange={(v) => updateSection('llm', { topP: v })}
                />
                <NumberField
                  label="最大 Tokens"
                  value={draft.llm.maxTokens}
                  min={256}
                  max={32768}
                  step={128}
                  onChange={(v) => updateSection('llm', { maxTokens: v })}
                />
                <NumberField
                  label="上下文窗口"
                  value={draft.llm.contextWindow}
                  min={4096}
                  max={1_000_000}
                  step={1000}
                  onChange={(v) => updateSection('llm', { contextWindow: v })}
                />
                <SliderField
                  label="Presence Penalty"
                  value={draft.llm.presencePenalty}
                  min={-2}
                  max={2}
                  step={0.1}
                  format={(v) => v.toFixed(1)}
                  onChange={(v) => updateSection('llm', { presencePenalty: v })}
                />
                <SliderField
                  label="Frequency Penalty"
                  value={draft.llm.frequencyPenalty}
                  min={-2}
                  max={2}
                  step={0.1}
                  format={(v) => v.toFixed(1)}
                  onChange={(v) => updateSection('llm', { frequencyPenalty: v })}
                />
                <SliderField
                  label="System Prompt 权重"
                  value={draft.llm.systemWeight}
                  min={0}
                  max={2}
                  step={0.1}
                  format={(v) => v.toFixed(1)}
                  onChange={(v) => updateSection('llm', { systemWeight: v })}
                />
              </SettingGroup>
            </TabsContent>

            {/* TTS */}
            <TabsContent value="tts" className="space-y-4 mt-2">
              <TTSConfigPanel
                config={ttsConfig}
                saved={ttsConfigProp ?? null}
                onChange={(next) => {
                  setTtsConfig(next);
                  onTtsConfigChange?.(next);
                }}
                onSave={async (next) => {
                  const cfg = next ?? ttsConfig;
                  if (onTtsConfigSave) {
                    await onTtsConfigSave(cfg);
                  } else {
                    await saveTtsConfig(cfg);
                  }
                }}
              />
            </TabsContent>

            {/* ASR */}
            <TabsContent value="asr" className="space-y-4 mt-2">
              <ASRConfigPanel
                config={asrConfig}
                saved={asrConfigProp ?? null}
                onChange={(next) => {
                  setAsrConfig(next);
                  onAsrConfigChange?.(next);
                }}
                onSave={async (next) => {
                  const cfg = next ?? asrConfig;
                  if (onAsrConfigSave) {
                    await onAsrConfigSave(cfg);
                  } else {
                    await saveAsrConfig(cfg);
                  }
                }}
              />
            </TabsContent>

            {/* 界面 */}
            <TabsContent value="ui" className="space-y-4 mt-2">
              <SettingGroup title="主题">
                <SelectField
                  label="主题色"
                  value={draft.ui.themeColor}
                  onChange={(v) => updateSection('ui', { themeColor: v as AppSettings['ui']['themeColor'] })}
                  options={[
                    { value: 'gold', label: '鎏金' },
                    { value: 'cyan', label: '青蓝' },
                    { value: 'rose', label: '玫瑰' },
                    { value: 'violet', label: '紫罗兰' },
                  ]}
                />
                <SelectField
                  label="字体大小"
                  value={draft.ui.fontSize}
                  onChange={(v) => updateSection('ui', { fontSize: v as AppSettings['ui']['fontSize'] })}
                  options={[
                    { value: 'sm', label: '小' },
                    { value: 'base', label: '中' },
                    { value: 'lg', label: '大' },
                  ]}
                />
                <SelectField
                  label="消息间距"
                  value={draft.ui.messageDensity}
                  onChange={(v) => updateSection('ui', { messageDensity: v as AppSettings['ui']['messageDensity'] })}
                  options={[
                    { value: 'compact', label: '紧凑' },
                    { value: 'normal', label: '适中' },
                    { value: 'relaxed', label: '宽松' },
                  ]}
                />
              </SettingGroup>

              <SettingGroup title="背景">
                <div className="flex gap-2">
                  {(['solid', 'gradient', 'image', 'video'] as BackgroundType[]).map((type) => (
                    <button
                      key={type}
                      onClick={() => updateSection('ui', { backgroundType: type })}
                      className={`flex-1 py-1.5 text-xs rounded-sm border transition-colors min-h-[40px] ${
                        draft.ui.backgroundType === type
                          ? 'bg-laap-gold/10 border-laap-gold/50 text-laap-gold'
                          : 'bg-laap-bg-tertiary/50 border-laap-border text-laap-text-secondary hover:text-white'
                      }`}
                    >
                      {type === 'solid' ? '纯色' : type === 'gradient' ? '渐变' : type === 'image' ? '图片' : '视频'}
                    </button>
                  ))}
                </div>

                {draft.ui.backgroundType === 'solid' && (
                  <div className="flex items-center gap-3">
                    <input
                      type="color"
                      value={draft.ui.backgroundValue}
                      onChange={(e) => updateSection('ui', { backgroundValue: e.target.value })}
                      className="w-10 h-10 rounded-sm bg-transparent border-0 p-0 cursor-pointer"
                    />
                    <TextField
                      label="颜色值"
                      value={draft.ui.backgroundValue}
                      onChange={(v) => updateSection('ui', { backgroundValue: v })}
                    />
                  </div>
                )}

                {draft.ui.backgroundType === 'gradient' && (
                  <div className="space-y-2">
                    <label className="text-xs text-laap-text-tertiary">渐变 CSS</label>
                    <textarea
                      value={draft.ui.backgroundValue}
                      onChange={(e) => updateSection('ui', { backgroundValue: e.target.value })}
                      placeholder="linear-gradient(135deg, #050505 0%, #1a1a2e 100%)"
                      rows={3}
                      className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-xs text-laap-text-secondary focus:outline-none focus:border-laap-gold/50 resize-none min-h-[80px]"
                    />
                  </div>
                )}

                <SliderField
                  label="背景透明度"
                  value={draft.ui.backgroundOpacity}
                  min={0}
                  max={1}
                  step={0.05}
                  format={(v) => `${Math.round(v * 100)}%`}
                  onChange={(v) => updateSection('ui', { backgroundOpacity: v })}
                />

                {draft.ui.backgroundType === 'image' && (
                  <div className="space-y-3">
                    <div className="grid grid-cols-4 gap-2">
                      {draft.ui.backgroundPresets.map((src) => (
                        <button
                          key={src}
                          onClick={() => updateSection('ui', { backgroundValue: src })}
                          className={`relative rounded-sm overflow-hidden border aspect-video ${
                            draft.ui.backgroundValue === src
                              ? 'border-laap-gold ring-1 ring-laap-gold'
                              : 'border-laap-border hover:border-laap-gold/50'
                          }`}
                        >
                          <img src={src} alt="preset" className="w-full h-full object-cover" />
                        </button>
                      ))}
                    </div>
                    <input
                      ref={fileRef}
                      type="file"
                      accept="image/*"
                      onChange={handleBackgroundFile}
                      className="hidden"
                    />
                    <button
                      type="button"
                      onClick={() => fileRef.current?.click()}
                      className="flex items-center gap-2 px-3 py-2 text-xs border border-laap-border rounded-sm text-laap-text-secondary hover:text-white hover:border-laap-gold/50 transition-colors min-h-[40px]"
                    >
                      <ImageIcon size={14} />
                      上传背景图片
                    </button>
                    {draft.ui.backgroundValue && (
                      <div className="relative group rounded-sm overflow-hidden border border-laap-border">
                        <img
                          src={draft.ui.backgroundValue}
                          alt="background"
                          className="w-full h-32 object-cover"
                        />
                        <button
                          type="button"
                          onClick={() => updateSection('ui', { backgroundValue: '', backgroundType: 'solid' })}
                          className="absolute top-2 right-2 p-1 min-h-[40px] min-w-[40px] flex items-center justify-center bg-black/60 text-white rounded-sm opacity-0 group-hover:opacity-100 transition-opacity"
                          aria-label="清除背景图片"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {draft.ui.backgroundType === 'video' && (
                  <div className="space-y-2">
                    <input
                      ref={videoRef}
                      type="file"
                      accept="video/*"
                      onChange={handleVideoFile}
                      className="hidden"
                    />
                    <button
                      type="button"
                      onClick={() => videoRef.current?.click()}
                      className="flex items-center gap-2 px-3 py-2 text-xs border border-laap-border rounded-sm text-laap-text-secondary hover:text-white hover:border-laap-gold/50 transition-colors min-h-[40px]"
                    >
                      <ImageIcon size={14} />
                      上传背景视频
                    </button>
                    {draft.ui.backgroundVideo && (
                      <div className="relative group rounded-sm overflow-hidden border border-laap-border">
                        <video
                          src={draft.ui.backgroundVideo}
                          muted
                          loop
                          className="w-full h-32 object-cover"
                        />
                        <button
                          type="button"
                          onClick={() =>
                            updateSection('ui', { backgroundVideo: '', backgroundType: 'solid' })
                          }
                          className="absolute top-2 right-2 p-1 min-h-[40px] min-w-[40px] flex items-center justify-center bg-black/60 text-white rounded-sm opacity-0 group-hover:opacity-100 transition-opacity"
                          aria-label="清除背景视频"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    )}
                  </div>
                )}

                <div
                  className="h-24 rounded-sm border border-laap-border relative overflow-hidden"
                  style={{
                    background:
                      draft.ui.backgroundType === 'image'
                        ? `url(${draft.ui.backgroundValue}) center/cover no-repeat`
                        : bgPreview,
                    opacity: draft.ui.backgroundType === 'image' ? draft.ui.backgroundOpacity : 1,
                  }}
                >
                  {draft.ui.backgroundType === 'video' && draft.ui.backgroundVideo && (
                    <video
                      src={draft.ui.backgroundVideo}
                      autoPlay
                      loop
                      muted
                      playsInline
                      className="absolute inset-0 w-full h-full object-cover"
                    />
                  )}
                </div>
              </SettingGroup>

              <SettingGroup title="头像">
                <div className="grid grid-cols-2 gap-4">
                  <AvatarUploader
                    label="用户头像"
                    value={draft.ui.userAvatar}
                    inputRef={userAvatarRef}
                    onUpload={(e) => handleAvatarFile(e, 'userAvatar')}
                    onClear={() => updateSection('ui', { userAvatar: '' })}
                  />
                  <AvatarUploader
                    label="机器人头像"
                    value={draft.ui.robotAvatar}
                    inputRef={robotAvatarRef}
                    onUpload={(e) => handleAvatarFile(e, 'robotAvatar')}
                    onClear={() => updateSection('ui', { robotAvatar: '' })}
                  />
                </div>
              </SettingGroup>
            </TabsContent>

            {/* 数据 */}
            <TabsContent value="data" className="space-y-4 mt-2">
              <SettingGroup title="备份">
                <SwitchField
                  label="自动备份"
                  checked={draft.data.autoBackup}
                  onChange={(v) => updateSection('data', { autoBackup: v })}
                />
                <NumberField
                  label="备份间隔（天）"
                  value={draft.data.backupIntervalDays}
                  min={1}
                  max={30}
                  step={1}
                  onChange={(v) => updateSection('data', { backupIntervalDays: v })}
                />
              </SettingGroup>

              <SettingGroup title="导出聊天记录">
                <p className="text-[11px] text-laap-text-tertiary leading-relaxed">
                  以纸质风格 Q&A 排版导出当前对话，支持 Markdown 与 HTML 两种格式。
                </p>
                <div className="grid grid-cols-2 gap-2 mt-1">
                  <ExportButton
                    icon={<FileDown size={14} />}
                    label="导出 .md"
                    disabled={!sessionMessages || sessionMessages.length === 0}
                    onClick={() => handleExportChat('md')}
                  />
                  <ExportButton
                    icon={<FileCode2 size={14} />}
                    label="导出 .html"
                    disabled={!sessionMessages || sessionMessages.length === 0}
                    onClick={() => handleExportChat('html')}
                  />
                </div>
                {(!sessionMessages || sessionMessages.length === 0) && (
                  <p className="text-[10px] text-laap-text-tertiary">当前会话暂无消息，先开始对话再导出。</p>
                )}
              </SettingGroup>

              <SettingGroup title="记忆备份 / 导出">
                <p className="text-[11px] text-laap-text-tertiary leading-relaxed">
                  将长期记忆以纸质风格 Q&A 排版导出，便于备份与迁移。
                </p>
                <div className="grid grid-cols-2 gap-2 mt-1">
                  <ExportButton
                    icon={<BrainCircuit size={14} />}
                    label={exporting === 'mem-md' ? '导出中…' : '备份 .md'}
                    disabled={exporting !== null}
                    onClick={() => void handleExportMemories('md')}
                  />
                  <ExportButton
                    icon={<BrainCircuit size={14} />}
                    label={exporting === 'mem-html' ? '导出中…' : '备份 .html'}
                    disabled={exporting !== null}
                    onClick={() => void handleExportMemories('html')}
                  />
                </div>
              </SettingGroup>
            </TabsContent>

            {/* Agent */}
            <TabsContent value="agent" className="space-y-4 mt-2">
              <SettingGroup title="PSI 循环">
                <SelectField
                  label="PSI 深度"
                  value={draft.agent.psiDepth}
                  onChange={(v) => updateSection('agent', { psiDepth: v as AppSettings['agent']['psiDepth'] })}
                  options={[
                    { value: 'surface', label: '浅层' },
                    { value: 'balanced', label: '平衡' },
                    { value: 'deep', label: '深层' },
                  ]}
                />
              </SettingGroup>
              <SettingGroup title="能力开关">
                <SwitchField
                  label="因果推理"
                  checked={draft.agent.causalReasoning}
                  onChange={(v) => updateSection('agent', { causalReasoning: v })}
                />
                <SwitchField
                  label="工具调用"
                  checked={draft.agent.toolCalling}
                  onChange={(v) => updateSection('agent', { toolCalling: v })}
                />
                <SwitchField
                  label="主动记忆"
                  checked={draft.agent.proactiveMemory}
                  onChange={(v) => updateSection('agent', { proactiveMemory: v })}
                />
                <SliderField
                  label="最大工具轮数"
                  value={draft.agent.maxToolRounds}
                  min={1}
                  max={5}
                  step={1}
                  format={(v) => String(Math.round(v))}
                  onChange={(v) => updateSection('agent', { maxToolRounds: Math.round(v) })}
                />
              </SettingGroup>
              <SettingGroup title="网络搜索">
                <TextField
                  label="Serper API Key"
                  type="password"
                  value={draft.agent.webSearchApiKey}
                  onChange={(v) => updateSection('agent', { webSearchApiKey: v })}
                  placeholder="用于 web_search 工具"
                />
              </SettingGroup>
            </TabsContent>

            {/* 记忆 */}
            <TabsContent value="memory" className="space-y-4 mt-2">
              <SettingGroup title="记忆管理">
                <SwitchField
                  label="启用长期记忆"
                  checked={draft.memory.enabled}
                  onChange={(v) => updateSection('memory', { enabled: v })}
                />
                <SliderField
                  label="最大记忆条数"
                  value={draft.memory.maxMemories}
                  min={0}
                  max={50}
                  step={1}
                  format={(v) => String(Math.round(v))}
                  onChange={(v) => updateSection('memory', { maxMemories: Math.round(v) })}
                />
                <SwitchField
                  label="自动总结"
                  checked={draft.memory.autoSummarize}
                  onChange={(v) => updateSection('memory', { autoSummarize: v })}
                />
              </SettingGroup>
            </TabsContent>

            {/* LAAP 影响 */}
            <TabsContent value="influence" className="space-y-4 mt-2">
              <SettingGroup title="LAAP 表达调制">
                <SliderField
                  label="影响强度"
                  value={draft.influence.intensity}
                  min={0}
                  max={100}
                  step={1}
                  format={(v) => `${Math.round(v)}%`}
                  onChange={(v) => updateSection('influence', { intensity: Math.round(v) })}
                />
                <SelectField
                  label="情绪风格"
                  value={draft.influence.mood}
                  onChange={(v) => updateSection('influence', { mood: v as AppSettings['influence']['mood'] })}
                  options={[
                    { value: 'warm', label: '温暖' },
                    { value: 'witty', label: '机智' },
                    { value: 'poetic', label: '诗意' },
                    { value: 'playful', label: '俏皮' },
                    { value: 'calm', label: '沉稳' },
                    { value: 'passionate', label: '热烈' },
                  ]}
                />
                <SelectField
                  label="响应深度"
                  value={draft.influence.responseDepth}
                  onChange={(v) => updateSection('influence', { responseDepth: v as AppSettings['influence']['responseDepth'] })}
                  options={[
                    { value: 'concise', label: '简洁' },
                    { value: 'balanced', label: '平衡' },
                    { value: 'deep', label: '深入' },
                  ]}
                />
              </SettingGroup>
            </TabsContent>
          </div>
        </Tabs>

        <div className="px-6 py-4 border-t border-laap-border flex justify-end gap-2">
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            className="px-4 py-2 text-xs text-laap-text-secondary hover:text-white transition-colors min-h-[40px]"
          >
            取消
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-laap-bg-primary bg-laap-gold rounded-sm hover:bg-laap-gold-light disabled:opacity-60 transition-colors min-h-[40px]"
          >
            <Save size={12} />
            {saving ? '保存中…' : '保存设置'}
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function SettingGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-3">
      <div className="font-mono text-[10px] text-laap-text-tertiary uppercase tracking-wider">{title}</div>
      <div className="space-y-3">{children}</div>
    </div>
  );
}

function TextField({
  label,
  value,
  onChange,
  type = 'text',
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-xs text-laap-text-tertiary mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-xs text-laap-text-secondary placeholder:text-laap-text-tertiary/60 focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
      />
    </div>
  );
}

function NumberField({
  label,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
}) {
  return (
    <div>
      <label className="block text-xs text-laap-text-tertiary mb-1">{label}</label>
      <input
        type="number"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-xs text-laap-text-secondary focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
      />
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div>
      <label className="block text-xs text-laap-text-tertiary mb-1">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-laap-bg-tertiary/50 border border-laap-border rounded-sm px-2 py-1.5 text-xs text-laap-text-secondary focus:outline-none focus:border-laap-gold/50 min-h-[40px]"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function SwitchField({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  const id = useId();
  return (
    <label htmlFor={id} className="flex items-center justify-between min-h-[40px] cursor-pointer">
      <span className="text-xs text-laap-text-secondary">{label}</span>
      <Switch id={id} checked={checked} onCheckedChange={onChange} />
    </label>
  );
}

function SliderField({
  label,
  value,
  min,
  max,
  step,
  format,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  format: (v: number) => string;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <label className="text-xs text-laap-text-tertiary">{label}</label>
        <span className="text-[10px] text-laap-text-tertiary font-mono">{format(value)}</span>
      </div>
      <Slider value={[value]} min={min} max={max} step={step} onValueChange={([v]) => onChange(v)} />
    </div>
  );
}

function ExportButton({
  icon,
  label,
  disabled,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="flex items-center justify-center gap-1.5 px-3 py-2 text-xs border border-laap-border rounded-sm text-laap-text-secondary hover:text-laap-gold hover:border-laap-gold/50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors min-h-[40px]"
    >
      {icon}
      {label}
    </button>
  );
}

function AvatarUploader({
  label,
  value,
  inputRef,
  onUpload,
  onClear,
}: {
  label: string;
  value: string;
  inputRef: React.RefObject<HTMLInputElement | null>;
  onUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onClear: () => void;
}) {
  return (
    <div className="space-y-2">
      <label className="text-xs text-laap-text-tertiary">{label}</label>
      <input ref={inputRef} type="file" accept="image/*" onChange={onUpload} className="hidden" />
      {value ? (
        <div className="relative group w-20 h-20 rounded-full overflow-hidden border border-laap-border mx-auto">
          <img src={value} alt={label} className="w-full h-full object-cover" />
          <button
            type="button"
            onClick={onClear}
            className="absolute inset-0 flex items-center justify-center bg-black/50 text-white opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <X size={16} />
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="w-20 h-20 rounded-full border border-dashed border-laap-border flex items-center justify-center text-laap-text-tertiary hover:text-white hover:border-laap-gold/50 transition-colors mx-auto"
        >
          <ImageIcon size={20} />
        </button>
      )}
    </div>
  );
}
