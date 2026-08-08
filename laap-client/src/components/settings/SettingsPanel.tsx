/**
 * SettingsPanel — 设置面板（多 tab）
 *
 * Tab 1: 通用（后端连接 + 热键 + 外观）
 * Tab 2: LLM 提供商
 * Tab 3: TTS 语音合成
 * Tab 4: ASR 语音识别
 */

import { useEffect, useRef, useState } from 'react'
import {
  X, Save, RotateCcw, Link, Keyboard, Mic,
  SlidersHorizontal, Film, Check, AlertCircle, Loader2,
  Volume2, BrainCircuit, Speech, Puzzle, Download, Info, Zap, Monitor, Shield,
} from 'lucide-react'
import { GlassPanel } from '../glass/GlassPanel'
import { useSettingsStore, type GlassIntensity } from '../../store/settingsStore'
import { getCognitiveBus } from '../../store/laapStore'
import { LLM_PROVIDERS, TTS_PROVIDERS, ASR_PROVIDERS } from '../../config/providers'
import { testConnection, type LlmConfig, type LlmProvider } from '../../laap/llm'
import type { AetherMessage } from '../../laap/types'

type SettingsTab = 'general' | 'interface' | 'llm' | 'tts' | 'asr' | 'providers' | 'plugins' | 'security' | 'data' | 'about'

const TABS: { key: SettingsTab; label: string; icon: React.ElementType }[] = [
  { key: 'general', label: '通用', icon: SlidersHorizontal },
  { key: 'interface', label: '界面', icon: Monitor },
  { key: 'llm', label: 'LLM', icon: BrainCircuit },
  { key: 'tts', label: 'TTS', icon: Volume2 },
  { key: 'asr', label: 'ASR', icon: Speech },
  { key: 'providers', label: '提供商', icon: Zap },
  { key: 'plugins', label: '插件', icon: Puzzle },
  { key: 'security', label: '安全', icon: Shield },
  { key: 'data', label: '数据', icon: Download },
  { key: 'about', label: '关于', icon: Info },
]

function SectionTitle({ icon: Icon, title }: { icon: React.ElementType; title: string }) {
  return (
    <div className="flex items-center gap-2 text-xs font-medium text-white/50 uppercase tracking-wider mb-3">
      <Icon className="w-3.5 h-3.5" />
      <span>{title}</span>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="block text-xs text-white/60">{label}</label>
      {children}
    </div>
  )
}

function Select({ value, onChange, options, disabled }: {
  value: string; onChange: (v: string) => void
  options: { value: string; label: string; disabled?: boolean }[]
  disabled?: boolean
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className="w-full px-3 py-2 rounded-lg bg-black/20 border border-white/[0.08] text-xs text-white/90 focus:outline-none focus:border-laap-accent/50 disabled:opacity-50"
    >
      {options.map((o) => (
        <option key={o.value} value={o.value} disabled={o.disabled}>{o.label}</option>
      ))}
    </select>
  )
}

function CredField({ value, onChange, placeholder, password, disabled }: {
  value: string; onChange: (v: string) => void
  placeholder?: string; password?: boolean; disabled?: boolean
}) {
  return (
    <input
      type={password ? 'password' : 'text'}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className="w-full px-3 py-2 rounded-lg bg-black/20 border border-white/[0.08] text-xs text-white/90 placeholder:text-white/30 focus:outline-none focus:border-laap-accent/50 font-mono disabled:opacity-50"
      placeholder={placeholder}
    />
  )
}

// ─── 通用设置 Tab ───
function GeneralTab({
  draft, setDraft, devices, testStatus, handleTestConnection,
  handleSelectVideo, updateGlass, formatShortcut, envKeyAvailable, effectiveApiKey,
}: any) {
  return (
    <div className="space-y-6">
      {/* 后端连接 */}
      <section>
        <SectionTitle icon={Link} title="后端连接" />
        <div className="space-y-3">
          <Field label="WebSocket 地址">
            <div className="flex gap-2">
              <input type="text" value={draft.backendUrl}
                onChange={(e) => setDraft((p: any) => ({ ...p, backendUrl: e.target.value }))}
                className="flex-1 min-w-0 px-3 py-2 rounded-lg bg-black/20 border border-white/[0.08] text-xs text-white/90 placeholder:text-white/30 focus:outline-none focus:border-laap-accent/50"
                placeholder="ws://127.0.0.1:8765" />
              <button type="button" onClick={handleTestConnection} disabled={testStatus === 'testing'}
                className="px-3 py-2 rounded-lg bg-white/[0.06] hover:bg-white/[0.10] border border-white/[0.08] text-xs text-white/80 transition-colors disabled:opacity-50 flex items-center gap-1.5">
                {testStatus === 'testing' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> :
                 testStatus === 'success' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> :
                 testStatus === 'error' ? <AlertCircle className="w-3.5 h-3.5 text-red-400" /> : null}
                测试连接
              </button>
            </div>
            {testStatus === 'success' && <p className="text-[10px] text-emerald-400 mt-1.5">连接成功</p>}
            {testStatus === 'error' && <p className="text-[10px] text-red-400 mt-1.5">无法连接</p>}
          </Field>
          <Field label="API Key">
            <CredField value={draft.useEnvApiKey ? effectiveApiKey : draft.apiKey}
              onChange={(v) => setDraft((p: any) => ({ ...p, apiKey: v }))}
              placeholder="输入 API Key" password disabled={draft.useEnvApiKey} />
            <label className="flex items-center gap-2 mt-2 cursor-pointer">
              <input type="checkbox" checked={draft.useEnvApiKey}
                onChange={(e) => setDraft((p: any) => ({ ...p, useEnvApiKey: e.target.checked }))}
                disabled={!envKeyAvailable}
                className="rounded border-white/20 bg-black/20 text-laap-accent focus:ring-0" />
              <span className="text-[11px] text-white/60">优先使用环境变量</span>
            </label>
          </Field>
        </div>
      </section>

      {/* 引擎模式 */}
      <section>
        <SectionTitle icon={BrainCircuit} title="引擎模式" />
        <div className="space-y-3">
          <div className="flex gap-2">
            <button type="button"
              onClick={() => setDraft((p: any) => ({ ...p, engineMode: 'direct' }))}
              className={`flex-1 px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                draft.engineMode === 'direct'
                  ? 'bg-laap-accent/20 border border-laap-accent/50 text-white'
                  : 'bg-black/20 border border-white/[0.08] text-white/60 hover:text-white/80'
              }`}>
              <div className="text-sm mb-0.5">直连后端</div>
              <div className="text-[10px] opacity-60">直接调 LLM API，每次花 token</div>
            </button>
            <button type="button"
              onClick={() => setDraft((p: any) => ({ ...p, engineMode: 'consciousness' }))}
              className={`flex-1 px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                draft.engineMode === 'consciousness'
                  ? 'bg-laap-accent/20 border border-laap-accent/50 text-white'
                  : 'bg-black/20 border border-white/[0.08] text-white/60 hover:text-white/80'
              }`}>
              <div className="text-sm mb-0.5">意识引擎 (0-token优先)</div>
              <div className="text-[10px] opacity-60">缓存→记忆→规则→LLM，省 token</div>
            </button>
          </div>
          {draft.engineMode === 'consciousness' && (
            <Field label="意识引擎地址">
              <input type="text" value={draft.consciousnessUrl}
                onChange={(e) => setDraft((p: any) => ({ ...p, consciousnessUrl: e.target.value }))}
                className="w-full px-3 py-2 rounded-lg bg-black/20 border border-white/[0.08] text-xs text-white/90 placeholder:text-white/30 focus:outline-none focus:border-laap-accent/50"
                placeholder="http://127.0.0.1:19420" />
            </Field>
          )}
        </div>
      </section>

      {/* 热键 */}
      <section>
        <SectionTitle icon={Keyboard} title="全局热键" />
        <div className="grid grid-cols-2 gap-3">
          <Field label="显示/隐藏窗口">
            <input type="text" value={draft.hotkeys.showWindow}
              onChange={(e) => setDraft((p: any) => ({ ...p, hotkeys: { ...p.hotkeys, showWindow: e.target.value } }))}
              className="w-full px-3 py-2 rounded-lg bg-black/20 border border-white/[0.08] text-xs text-white/90 placeholder:text-white/30 focus:outline-none focus:border-laap-accent/50" />
            <p className="text-[10px] text-white/40 mt-1">当前：{formatShortcut(draft.hotkeys.showWindow)}</p>
          </Field>
          <Field label="按住说话 (PTT)">
            <input type="text" value={draft.hotkeys.ptt}
              onChange={(e) => setDraft((p: any) => ({ ...p, hotkeys: { ...p.hotkeys, ptt: e.target.value } }))}
              className="w-full px-3 py-2 rounded-lg bg-black/20 border border-white/[0.08] text-xs text-white/90 placeholder:text-white/30 focus:outline-none focus:border-laap-accent/50" />
            <p className="text-[10px] text-white/40 mt-1">当前：{formatShortcut(draft.hotkeys.ptt)}</p>
          </Field>
        </div>
      </section>

      {/* 语音输入 */}
      <section>
        <SectionTitle icon={Mic} title="语音输入" />
        <Field label="麦克风设备">
          <select value={draft.audioInputDeviceId}
            onChange={(e) => setDraft((p: any) => ({ ...p, audioInputDeviceId: e.target.value }))}
            className="w-full px-3 py-2 rounded-lg bg-black/20 border border-white/[0.08] text-xs text-white/90 focus:outline-none focus:border-laap-accent/50">
            <option value="">系统默认</option>
            {devices.map((d: any) => <option key={d.deviceId} value={d.deviceId}>{d.label}</option>)}
          </select>
        </Field>
        <div className="mt-4 space-y-3">
          <Field label="唤醒词">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={draft.wakeWordEnabled}
                onChange={(e) => setDraft((p: any) => ({ ...p, wakeWordEnabled: e.target.checked }))}
                className="rounded border-white/20 bg-black/20 text-laap-accent focus:ring-0" />
              <span className="text-[11px] text-white/60">持续监听麦克风</span>
            </label>
          </Field>
        </div>
      </section>

      {/* 外观 */}
      <section>
        <SectionTitle icon={SlidersHorizontal} title="外观" />
        <div className="grid grid-cols-3 gap-2 mb-3">
          {([{v:'dark',l:'深空黑'},{v:'midnight',l:'午夜蓝'},{v:'obsidian',l:'曜石紫'}] as const).map(({v,l}) => (
            <button key={v} type="button" onClick={() => setDraft((p: any) => ({ ...p, theme: v }))}
              className={`py-2 rounded-lg border text-xs transition-colors ${
                draft.theme === v ? 'border-laap-accent/40 bg-laap-accent/10 text-white/90' : 'border-white/[0.08] text-white/50 hover:text-white/70'
              }`}>{l}</button>
          ))}
        </div>
        <Field label={`玻璃模糊：${draft.glassIntensity.blur}px`}>
          <input type="range" min={4} max={32} value={draft.glassIntensity.blur}
            onChange={(e) => updateGlass({ blur: Number(e.target.value) })}
            className="w-full h-1 rounded-lg appearance-none bg-white/[0.12] accent-laap-accent cursor-pointer" />
        </Field>
      </section>

      {/* 视频 */}
      <section>
        <SectionTitle icon={Film} title="视频" />
        <div className="flex gap-2">
          <input type="text" value={draft.videoPath}
            onChange={(e) => setDraft((p: any) => ({ ...p, videoPath: e.target.value }))}
            className="flex-1 px-3 py-2 rounded-lg bg-black/20 border border-white/[0.08] text-xs text-white/90 placeholder:text-white/30 focus:outline-none focus:border-laap-accent/50"
            placeholder="视频文件路径" />
          <button type="button" onClick={handleSelectVideo}
            className="px-3 py-2 rounded-lg bg-white/[0.06] hover:bg-white/[0.10] border border-white/[0.08] text-xs text-white/70 transition-colors">
            选择
          </button>
        </div>
      </section>
    </div>
  )
}

// ─── LLM 设置 Tab ───
function LLMTab({ draft, setDraft, llmTestStatus, llmTestError, onTestLlm }: any) {
  const llm = draft.llm
  const provider = LLM_PROVIDERS.find((p) => p.id === llm.provider) || LLM_PROVIDERS[0]
  const models = provider.models.filter((m) => !m.deprecated)

  const handleProviderChange = (providerId: string) => {
    const next = LLM_PROVIDERS.find((p) => p.id === providerId) || LLM_PROVIDERS[0]
    setDraft((p: any) => ({
      ...p,
      llm: {
        ...p.llm,
        provider: next.id,
        model: next.defaultModel,
        baseUrl: next.baseURL,
      },
    }))
  }

  return (
    <div className="space-y-4">
      <SectionTitle icon={BrainCircuit} title="LLM 提供商" />
      <Field label="使用真实 API">
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={draft.useRealApi}
            onChange={(e) => setDraft((p: any) => ({ ...p, useRealApi: e.target.checked }))}
            className="rounded border-white/20 bg-black/20 text-laap-accent focus:ring-0" />
          <span className="text-[11px] text-white/60">开启后请求将转发到真实 LLM provider（否则使用模拟回复）</span>
        </label>
      </Field>
      <Field label="服务商">
        <Select value={llm.provider}
          onChange={handleProviderChange}
          options={LLM_PROVIDERS.map((p) => ({ value: p.id, label: p.label }))} />
      </Field>
      <Field label="模型">
        <Select value={llm.model} onChange={(v) => setDraft((p: any) => ({ ...p, llm: { ...p.llm, model: v } }))}
          options={models.map((m) => ({ value: m.id, label: m.label }))} />
      </Field>
      <Field label={`API Key (${provider.envVar})`}>
        <CredField value={llm.creds[provider.id+'Key'] || ''}
          onChange={(v) => setDraft((p: any) => ({ ...p, llm: { ...p.llm, creds: { ...p.llm.creds, [provider.id+'Key']: v } } }))}
          placeholder={`输入 ${provider.label} API Key`} password />
      </Field>
      <Field label="自定义 Base URL（可选）">
        <CredField value={llm.baseUrl}
          onChange={(v) => setDraft((p: any) => ({ ...p, llm: { ...p.llm, baseUrl: v } }))}
          placeholder={provider.baseURL} />
      </Field>
      <Field label="连接测试">
        <div className="flex items-center gap-2">
          <button type="button" onClick={onTestLlm} disabled={llmTestStatus === 'testing'}
            className="px-3 py-2 rounded-lg bg-white/[0.06] hover:bg-white/[0.10] border border-white/[0.08] text-xs text-white/80 transition-colors disabled:opacity-50 flex items-center gap-1.5">
            {llmTestStatus === 'testing' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> :
             llmTestStatus === 'success' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> :
             llmTestStatus === 'error' ? <AlertCircle className="w-3.5 h-3.5 text-red-400" /> : null}
            连接测试
          </button>
          {llmTestStatus === 'success' && <span className="text-[11px] text-emerald-400">连接成功</span>}
          {llmTestStatus === 'error' && <span className="text-[11px] text-red-400">{llmTestError || '连接失败'}</span>}
        </div>
      </Field>
    </div>
  )
}

// ─── TTS 设置 Tab ───
function TTSTab({ draft, setDraft }: any) {
  const tts = draft.tts
  const provider = TTS_PROVIDERS.find((p) => p.id === tts.provider) || TTS_PROVIDERS[0]

  return (
    <div className="space-y-4">
      <SectionTitle icon={Volume2} title="语音合成 (TTS)" />
      <Field label="启用 TTS">
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={draft.ttsEnabled}
            onChange={(e) => setDraft((p: any) => ({ ...p, ttsEnabled: e.target.checked }))}
            className="rounded border-white/20 bg-black/20 text-laap-accent focus:ring-0" />
          <span className="text-[11px] text-white/60">收到语音回复时自动播放</span>
        </label>
      </Field>
      <Field label="TTS 服务商">
        <Select value={tts.provider}
          onChange={(v) => setDraft((p: any) => ({ ...p, tts: { ...p.tts, provider: v, model: TTS_PROVIDERS.find(x=>x.id===v)?.voices[0]?.id || '' } }))}
          options={TTS_PROVIDERS.map((p) => ({ value: p.id, label: `${p.label}${p.streaming ? ' ⚡' : ''}` }))} />
      </Field>
      {tts.provider === 'microsoft' && (
        <Field label="Azure 区域">
          <Select value={tts.baseUrl || 'eastasia'}
            onChange={(v) => setDraft((p: any) => ({ ...p, tts: { ...p.tts, baseUrl: v } }))}
            options={[
              { value: 'eastasia', label: '东亚 (eastasia)' },
              { value: 'southeastasia', label: '东南亚 (southeastasia)' },
              { value: 'westus', label: '美国西部 (westus)' },
              { value: 'eastus', label: '美国东部 (eastus)' },
              { value: 'westeurope', label: '西欧 (westeurope)' },
              { value: 'northeurope', label: '北欧 (northeurope)' },
              { value: 'chinaeast', label: '中国东部 (chinaeast)' },
              { value: 'chinanorth', label: '中国北部 (chinanorth)' },
            ]} />
        </Field>
      )}
      <Field label="音色">
        <Select value={tts.model}
          onChange={(v) => setDraft((p: any) => ({ ...p, tts: { ...p.tts, model: v } }))}
          options={provider.voices.map((v) => ({ value: v.id, label: v.label }))} />
      </Field>
      {provider.credentialFields.map((f) => (
        <Field key={f.key} label={f.label}>
          <CredField value={tts.creds[f.key] || ''}
            onChange={(v) => setDraft((p: any) => ({ ...p, tts: { ...p.tts, creds: { ...p.tts.creds, [f.key]: v } } }))}
            placeholder={`输入 ${f.label}`} password />
        </Field>
      ))}
      {tts.provider === 'microsoft' && (
        <p className="text-[10px] text-white/40 leading-relaxed">
          Azure F0 免费层级：每月 50 万字符额度，超出后限流而非自动扣费。
          请前往 <a href="https://portal.azure.com" target="_blank" rel="noopener noreferrer" className="text-laap-accent/70 underline">Azure Portal</a> 创建 Speech 资源获取密钥。
        </p>
      )}
      <Field label={`音量：${Math.round(draft.ttsVolume * 100)}%`}>
        <input type="range" min={0} max={1} step={0.05} value={draft.ttsVolume}
          onChange={(e) => setDraft((p: any) => ({ ...p, ttsVolume: Number(e.target.value) }))}
          className="w-full h-1 rounded-lg appearance-none bg-white/[0.12] accent-laap-accent cursor-pointer" />
      </Field>
    </div>
  )
}

// ─── ASR 设置 Tab ───
function ASRTab({ draft, setDraft }: any) {
  const asr = draft.asr
  const provider = ASR_PROVIDERS.find((p) => p.id === asr.provider) || ASR_PROVIDERS[0]

  return (
    <div className="space-y-4">
      <SectionTitle icon={Speech} title="语音识别 (ASR)" />
      <Field label="ASR 服务商">
        <Select value={asr.provider}
          onChange={(v) => setDraft((p: any) => ({ ...p, asr: { ...p.asr, provider: v, creds: {} } }))}
          options={ASR_PROVIDERS.map((p) => ({ value: p.id, label: p.label }))} />
      </Field>
      {provider.credentialFields.map((f) => (
        <Field key={f.key} label={f.label}>
          <CredField value={asr.creds[f.key] || ''}
            onChange={(v) => setDraft((p: any) => ({ ...p, asr: { ...p.asr, creds: { ...p.asr.creds, [f.key]: v } } }))}
            placeholder={f.placeholder || `输入 ${f.label}`} password />
        </Field>
      ))}
      {provider.id === 'local' && (
        <p className="text-xs text-white/40">使用本地 sherpa-onnx 识别，无需配置凭证</p>
      )}
    </div>
  )
}

export function SettingsPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  const store = useSettingsStore()
  const [tab, setTab] = useState<SettingsTab>('general')
  const [draft, setDraft] = useState<any>(null)
  const [devices, setDevices] = useState<any[]>([])
  const [testStatus, setTestStatus] = useState<'idle'|'testing'|'success'|'error'>('idle')
  const [llmTestStatus, setLlmTestStatus] = useState<'idle'|'testing'|'success'|'error'>('idle')
  const [llmTestError, setLlmTestError] = useState<string>('')
  const testWsRef = useRef<WebSocket | null>(null)

  // Initialize draft from store when panel opens
  useEffect(() => {
    if (!open) return
    setDraft({
      backendUrl: store.backendUrl,
      apiKey: store.apiKey,
      useEnvApiKey: store.useEnvApiKey,
      videoPath: store.videoPath,
      glassIntensity: { ...store.glassIntensity },
      theme: store.theme,
      audioInputDeviceId: store.audioInputDeviceId,
      hotkeys: { ...store.hotkeys },
      wakeWordEnabled: store.wakeWordEnabled,
      wakeWordPhrase: store.wakeWordPhrase,
      wakeWordSensitivity: store.wakeWordSensitivity,
      ttsEnabled: store.ttsEnabled,
      ttsVolume: store.ttsVolume,
      useRealApi: store.useRealApi,
      llm: { ...store.llm },
      tts: { ...store.tts },
      asr: { ...store.asr },
      engineMode: store.engineMode || 'direct',
      consciousnessUrl: store.consciousnessUrl || 'http://127.0.0.1:19420',
    })
    setTestStatus('idle')
    setLlmTestStatus('idle')
    setLlmTestError('')
    if (navigator.mediaDevices?.enumerateDevices) {
      navigator.mediaDevices.enumerateDevices().then((list) => {
        setDevices(list.filter((d) => d.kind === 'audioinput').map((d) => ({
          deviceId: d.deviceId,
          label: d.label || `麦克风 ${d.deviceId.slice(0, 8)}`,
        })))
      }).catch(() => {})
    }
  }, [open, store])

  useEffect(() => {
    if (open) return
    testWsRef.current?.close()
    testWsRef.current = null
  }, [open])

  if (!draft) return null

  const updateGlass = (patch: Partial<GlassIntensity>) => setDraft((p: any) => ({
    ...p, glassIntensity: { ...p.glassIntensity, ...patch },
  }))

  const handleSave = () => {
    store.setBackendUrl(draft.backendUrl)
    store.setApiKey(draft.apiKey)
    store.setUseEnvApiKey(draft.useEnvApiKey)
    store.setVideoPath(draft.videoPath)
    store.setGlassIntensity(draft.glassIntensity)
    store.setTheme(draft.theme)
    store.setAudioInputDeviceId(draft.audioInputDeviceId)
    store.setHotkeys(draft.hotkeys)
    store.setWakeWordEnabled(draft.wakeWordEnabled)
    store.setWakeWordPhrase(draft.wakeWordPhrase)
    store.setWakeWordSensitivity(draft.wakeWordSensitivity)
    store.setTtsEnabled(draft.ttsEnabled)
    store.setTtsVolume(draft.ttsVolume)
    store.setUseRealApi(draft.useRealApi)
    store.setLLM(draft.llm)
    store.setTTS(draft.tts)
    store.setASR(draft.asr)
    store.setEngineMode(draft.engineMode || 'direct')
    store.setConsciousnessUrl(draft.consciousnessUrl || 'http://127.0.0.1:19420')

    const llmConfig: LlmConfig = {
      provider: draft.llm.provider as LlmProvider,
      apiKey: draft.llm.creds[draft.llm.provider + 'Key'] || '',
      baseUrl: draft.llm.baseUrl,
      model: draft.llm.model,
      useRealApi: draft.useRealApi,
    }
    const message: AetherMessage = {
      id: `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`,
      type: 'config_update',
      topic: 'config.llm',
      payload: llmConfig,
      timestamp: Date.now(),
      sender: 'user',
    }
    getCognitiveBus().sendAetherMessage(message)

    window.desktop?.registerHotkeys(draft.hotkeys)
    onClose()
  }

  const handleReset = () => {
    store.resetToDefaults()
    setDraft({
      backendUrl: store.backendUrl, apiKey: store.apiKey, useEnvApiKey: store.useEnvApiKey,
      videoPath: store.videoPath, glassIntensity: { ...store.glassIntensity }, theme: store.theme,
      audioInputDeviceId: store.audioInputDeviceId, hotkeys: { ...store.hotkeys },
      wakeWordEnabled: store.wakeWordEnabled, wakeWordPhrase: store.wakeWordPhrase,
      wakeWordSensitivity: store.wakeWordSensitivity, ttsEnabled: store.ttsEnabled, ttsVolume: store.ttsVolume,
      useRealApi: store.useRealApi,
      llm: { ...store.llm }, tts: { ...store.tts }, asr: { ...store.asr },
    })
    setLlmTestStatus('idle')
    setLlmTestError('')
  }

  const handleTestConnection = () => {
    testWsRef.current?.close()
    setTestStatus('testing')
    const ws = new WebSocket(draft.backendUrl)
    testWsRef.current = ws
    const timer = setTimeout(() => { setTestStatus('error'); ws.close() }, 5000)
    ws.onopen = () => { clearTimeout(timer); setTestStatus('success'); ws.close() }
    ws.onerror = () => { clearTimeout(timer); setTestStatus('error') }
    ws.onclose = () => { testWsRef.current = null }
  }

  const handleTestLlm = async () => {
    setLlmTestStatus('testing')
    setLlmTestError('')
    const llm = draft.llm
    const config: LlmConfig = {
      provider: llm.provider as LlmProvider,
      apiKey: llm.creds[llm.provider + 'Key'] || '',
      baseUrl: llm.baseUrl,
      model: llm.model,
    }
    try {
      const result = await testConnection(config)
      if (result.ok) {
        setLlmTestStatus('success')
      } else {
        setLlmTestStatus('error')
        setLlmTestError(result.error || '连接失败')
      }
    } catch (err) {
      setLlmTestStatus('error')
      setLlmTestError(err instanceof Error ? err.message : '连接失败')
    }
  }

  const handleSelectVideo = async () => {
    try {
      const result = await (window as any).desktop?.selectVideo()
      if (result?.filePath) setDraft((p: any) => ({ ...p, videoPath: result.filePath }))
    } catch {}
  }

  const formatShortcut = (s: string) => s.replace('CommandOrControl','Ctrl').replace('Shift','Shift').replace('Space','空格')
  const effectiveApiKey = store.getEffectiveApiKey()
  const envKeyAvailable = !!(typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_API_KEY)

  return (
    <>
      {open && <div className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm" onClick={onClose} />}
      <div className={`fixed top-2 right-2 bottom-2 z-50 w-[700px] transition-transform duration-300 ease-out ${
        open ? 'translate-x-0' : 'translate-x-[calc(100%+16px)]'
      }`}>
        <GlassPanel className="h-full flex flex-col overflow-hidden" radius="var(--laap-radius-lg)" intensity="lg" liquidGlass>
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.08]">
            <h2 className="text-sm font-medium text-white/90 flex items-center gap-2">
              <SlidersHorizontal className="w-4 h-4 text-laap-accent" />
              设置
            </h2>
            <div className="flex items-center gap-2">
              <button type="button" onClick={handleReset}
                className="p-1.5 rounded-lg text-white/40 hover:text-white hover:bg-white/10 transition-colors" title="重置">
                <RotateCcw className="w-4 h-4" />
              </button>
              <button type="button" onClick={handleSave}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-laap-accent/20 border border-laap-accent/30 text-laap-accent hover:bg-laap-accent/30 transition-colors text-xs">
                <Save className="w-3.5 h-3.5" />
                保存
              </button>
              <button type="button" onClick={onClose}
                className="p-1.5 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* 主体：左导航 + 右内容（横向） */}
          <div className="flex-1 min-h-0 flex">
          {/* 左侧导航：竖向列表（Hanako 风格） */}
          <div className="w-48 shrink-0 border-r border-white/[0.06] overflow-y-auto py-2">
            {TABS.map(({ key, label, icon: Icon }) => (
              <button key={key} type="button" onClick={() => setTab(key)}
                className={`w-full flex items-center gap-2.5 px-4 py-2.5 text-left transition-colors ${
                  tab === key
                    ? 'bg-laap-accent/10 text-laap-accent border-l-2 border-laap-accent'
                    : 'text-white/60 hover:text-white/80 hover:bg-white/[0.03] border-l-2 border-transparent'
                }`}>
                <Icon className="w-4 h-4 shrink-0" />
                <span className="text-xs">{label}</span>
              </button>
            ))}
          </div>

          {/* 右侧内容 */}
          <div className="flex-1 min-w-0 flex flex-col overflow-hidden">
            {/* Tab 标题 */}
            <div className="px-6 pt-5 pb-3 border-b border-white/[0.06]">
              <h2 className="text-sm font-medium text-white/80">{TABS.find(t => t.key === tab)?.label || tab}</h2>
            </div>
            {/* 内容 */}
            <div className="flex-1 min-h-0 overflow-y-auto p-5">
            {tab === 'general' && <GeneralTab {...{ draft, setDraft, devices, testStatus, handleTestConnection, handleSelectVideo, updateGlass, formatShortcut, envKeyAvailable, effectiveApiKey }} />}
            {tab === 'interface' && <InterfaceTab draft={draft} setDraft={setDraft} />}
            {tab === 'llm' && <LLMTab {...{ draft, setDraft, llmTestStatus, llmTestError, onTestLlm: handleTestLlm }} />}
            {tab === 'tts' && <TTSTab {...{ draft, setDraft }} />}
            {tab === 'asr' && <ASRTab {...{ draft, setDraft }} />}
            {tab === 'providers' && <ProvidersTab draft={draft} setDraft={setDraft} />}
            {tab === 'plugins' && <PluginsTab />}
            {tab === 'security' && <SecurityTab />}
            {tab === 'data' && <DataTab />}
            {tab === 'about' && <AboutTab />}
          </div>
        </div>  {/* 右侧内容结束 */}
          </div>  {/* 横向容器结束 */}
        </GlassPanel>
      </div>
    </>
  )
}

/* ─── 提供商 Tab ─── */
function ProvidersTab({ draft, setDraft }: any) {
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null)
  const [testResults, setTestResults] = useState<Record<string, string>>({})

  const handleTest = async (providerId: string) => {
    const provider = LLM_PROVIDERS.find(p => p.id === providerId)
    if (!provider) return
    const key = draft.llm?.creds?.[providerId + 'Key'] || ''
    if (!key) { setTestResults(r => ({ ...r, [providerId]: '未配置 API Key' })); return }
    setTestResults(r => ({ ...r, [providerId]: '测试中...' }))
    try {
      // deepseek 需要 /v1 前缀，其他 provider 的 baseURL 已含路径
      const chatPath = providerId === 'deepseek'
        ? `${provider.baseURL}/v1/chat/completions`
        : `${provider.baseURL}/chat/completions`
      const resp = await fetch(chatPath, {
        method: 'POST', headers: { 'Authorization': `Bearer ${key}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: provider.defaultModel, messages: [{ role: 'user', content: 'hi' }], stream: false }),
        signal: AbortSignal.timeout(10000),
      })
      setTestResults(r => ({ ...r, [providerId]: resp.ok ? '✅ 连接成功' : `❌ ${resp.status}` }))
    } catch (e: any) {
      setTestResults(r => ({ ...r, [providerId]: `❌ ${e.message?.slice(0, 30) || '失败'}` }))
    }
  }

  return (
    <>
      <SectionTitle icon={Zap} title="LLM 提供商" />
      <div className="space-y-2">
        {LLM_PROVIDERS.map((p) => {
          const key = draft.llm?.creds?.[p.id + 'Key'] || ''
          const isSelected = selectedProvider === p.id
          return (
            <div key={p.id}
              className="bg-white/[0.03] rounded-lg border border-white/[0.06] overflow-hidden">
              <button onClick={() => setSelectedProvider(isSelected ? null : p.id)}
                className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-white/[0.02] transition-colors text-left">
                <span className={`w-2 h-2 rounded-full shrink-0 ${key ? 'bg-emerald-400' : 'bg-white/20'}`} />
                <span className="flex-1 text-xs font-medium text-white/80">{p.label}</span>
                <span className="text-[10px] text-white/40">{p.defaultModel}</span>
                <span className="text-[10px] text-white/30">{key ? '已配置' : '未配置'}</span>
              </button>
              {isSelected && (
                <div className="px-3 pb-3 space-y-2 border-t border-white/[0.04] pt-2 mt-0">
                  <div>
                    <label className="text-[10px] text-white/40 block mb-1">{p.envVar}</label>
                    <input type="password" value={key}
                      onChange={(e) => setDraft((d: any) => ({
                        ...d, llm: { ...d.llm, creds: { ...d.llm.creds, [p.id + 'Key']: e.target.value } }
                      }))}
                      className="w-full bg-white/[0.05] border border-white/[0.08] rounded px-2.5 py-1.5 text-xs text-white/80 placeholder:text-white/30 focus:outline-none focus:border-laap-accent/50"
                      placeholder={`输入 ${p.label} API Key`} />
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => handleTest(p.id)}
                      className="px-2.5 py-1 rounded bg-white/[0.06] hover:bg-white/[0.1] text-[10px] text-white/60 border border-white/[0.06] transition-colors">
                      测试连接
                    </button>
                    {testResults[p.id] && (
                      <span className="text-[10px]"
                        style={{ color: testResults[p.id].startsWith('✅') ? 'var(--green, #4A6B4A)' : '#8B2C1F' }}>
                        {testResults[p.id]}
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </>
  )
}

/* ─── 插件 Tab ─── */
function PluginsTab() {
  const [supervisor, setSupervisor] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const loadSupervisor = async () => {
    setLoading(true)
    try {
      const st = useSettingsStore.getState()
      const base = st.consciousnessUrl || 'http://127.0.0.1:19420'
      const resp = await fetch(`${base}/supervisor`, { signal: AbortSignal.timeout(5000) })
      setSupervisor(await resp.json())
    } catch { setSupervisor(null) }
    setLoading(false)
  }

  useEffect(() => { loadSupervisor() }, [])

  const processes = supervisor?.processes || {}
  const procList = Object.entries(processes)

  return (
    <>
      <SectionTitle icon={Puzzle} title="受监管子系统" />
      <div className="flex items-center justify-between mb-3">
        <span className="text-[11px] text-white/40">
          {supervisor ? `${supervisor.running}/${supervisor.total} 运行中` : 'daemon 未连接'}
        </span>
        <button onClick={loadSupervisor} disabled={loading}
          className="text-[10px] text-laap-accent/60 hover:text-laap-accent transition-colors">
          刷新
        </button>
      </div>
      <div className="space-y-2">
        {procList.length === 0 ? (
          <div className="bg-white/[0.03] rounded-lg border border-white/[0.06] p-4 text-center">
            <Puzzle className="w-8 h-8 text-white/20 mx-auto mb-2" />
            <p className="text-xs text-white/40">通过 daemon 监管树管理子系统</p>
            <p className="text-[10px] text-white/30 mt-1">启动: python laap-launch.py</p>
          </div>
        ) : (
          procList.map(([name, p]: any) => (
            <div key={name} className="flex items-center gap-3 px-3 py-2 bg-white/[0.03] rounded-lg border border-white/[0.06]">
              <span className={`w-2 h-2 rounded-full shrink-0 ${p.state === 'running' ? 'bg-emerald-400' : 'bg-white/20'}`} />
              <span className="flex-1 text-xs text-white/80">{name}</span>
              <span className="text-[10px] text-white/40">{p.state}</span>
              <span className="text-[10px] text-white/30 font-mono">PID {p.pid || '-'}</span>
            </div>
          ))
        )}
      </div>
    </>
  )
}

/* ─── 数据 Tab ─── */
function DataTab() {
  const [exporting, setExporting] = useState<string | null>(null)

  const handleExport = async (type: string) => {
    setExporting(type)
    try {
      const st = useSettingsStore.getState()
      const base = st.consciousnessUrl || 'http://127.0.0.1:19420'
      const resp = await fetch(`${base}/stats`, { signal: AbortSignal.timeout(5000) })
      const data = await resp.json()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = `laap-${type}-${Date.now()}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch { /* ignore */ }
    setExporting(null)
  }

  return (
    <>
      <SectionTitle icon={Download} title="数据管理" />
    <div className="space-y-3">
      <button type="button" onClick={() => handleExport('stats')} disabled={exporting !== null}
        className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.08] border border-white/[0.08] text-xs text-white/70 transition-colors disabled:opacity-50">
        <span>导出 daemon 统计</span>
        <span className="text-[10px] text-white/40">{exporting === 'stats' ? '导出中...' : 'JSON'}</span>
      </button>
      <button type="button" onClick={() => handleExport('cache')} disabled={exporting !== null}
        className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.08] border border-white/[0.08] text-xs text-white/70 transition-colors disabled:opacity-50">
        <span>导出缓存数据</span>
        <span className="text-[10px] text-white/40">{exporting === 'cache' ? '导出中...' : 'JSON'}</span>
      </button>
      <button type="button" onClick={() => { if (confirm('确认清除所有数据并重置？')) window.location.reload() } }
        className="w-full px-3 py-2.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 text-xs text-red-400/80 transition-colors">
        清除所有数据并重置
      </button>
    </div>
    </>
  )
}

/* ─── 关于 Tab ─── */
function AboutTab() {
  return (
    <>
      <SectionTitle icon={Info} title="关于 LAAP" />
    <div className="space-y-3">
      <div className="bg-white/[0.03] rounded-lg border border-white/[0.06] p-4 text-center">
        <div className="text-sm font-bold text-white/70 mb-1">LAAP Client</div>
        <div className="text-[10px] text-white/30">数字生命体意识窗口</div>
        <div className="mt-3 text-[10px] text-white/20">
          <p>认知引擎: Aether ActorSystem</p>
          <p>编排层: 彩色 Petri 网 + Actor</p>
          <p>缓存: L0 精确 + L1 语义 + 自适应阈值</p>
          <p>监管: daemon 监管树</p>
          <p className="mt-1">LAAP 是完整的数字生命体基础设施</p>
        </div>
      </div>
    </div>
    </>
  )
}

/* ─── 界面 Tab ─── */
const THEMES = [
  { id: 'dark', label: '暗色', desc: '深色背景' },
  { id: 'midnight', label: '午夜', desc: '深蓝背景' },
  { id: 'light', label: '亮色', desc: '浅色背景' },
  { id: 'dim', label: '暗调', desc: '柔和暗色' },
]

function InterfaceTab({ draft, setDraft }: any) {
  return (
    <>
      <SectionTitle icon={Monitor} title="界面设置" />
      <div className="space-y-4">
        <Field label="主题">
          <div className="grid grid-cols-2 gap-2">
            {THEMES.map(t => (
              <button key={t.id} onClick={() => setDraft((p: any) => ({ ...p, theme: t.id }))}
                className={`px-3 py-2.5 rounded-lg text-left transition-all ${
                  draft.theme === t.id
                    ? 'bg-laap-accent/20 border border-laap-accent/50'
                    : 'bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.06]'
                }`}>
                <div className="text-xs text-white/80">{t.label}</div>
                <div className="text-[10px] text-white/40 mt-0.5">{t.desc}</div>
              </button>
            ))}
          </div>
        </Field>
        <Field label="毛玻璃强度">
          <div className="flex items-center gap-3">
            <input type="range" min="0" max="40" value={draft.glassIntensity?.blur || 12}
              onChange={(e) => setDraft((p: any) => ({ ...p, glassIntensity: { ...p.glassIntensity, blur: Number(e.target.value) } }))}
              className="flex-1" />
            <span className="text-[10px] text-white/50 font-mono">{draft.glassIntensity?.blur || 12}px</span>
          </div>
        </Field>
        <Field label="界面语言">
          <Select value={draft.theme === 'light' ? '简体中文' : '中文'}
            onChange={() => {}}
            options={[{ value: '中文', label: '简体中文' }, { value: 'English', label: 'English' }]} />
        </Field>
      </div>
    </>
  )
}

/* ─── 安全 Tab ─── */
function SecurityTab() {
  return (
    <>
      <SectionTitle icon={Shield} title="安全设置" />
      <div className="space-y-3">
        <Field label="工具调用确认">
          <label className="flex items-center justify-between cursor-pointer">
            <span className="text-[11px] text-white/60">高危操作需用户确认</span>
            <input type="checkbox" defaultChecked
              className="rounded border-white/20 bg-black/20 text-laap-accent focus:ring-0" />
          </label>
        </Field>
        <Field label="沙箱隔离">
          <label className="flex items-center justify-between cursor-pointer">
            <span className="text-[11px] text-white/60">代码在隔离沙箱执行</span>
            <input type="checkbox" defaultChecked
              className="rounded border-white/20 bg-black/20 text-laap-accent focus:ring-0" />
          </label>
        </Field>
        <Field label="审计日志">
          <label className="flex items-center justify-between cursor-pointer">
            <span className="text-[11px] text-white/60">记录所有认知产出</span>
            <input type="checkbox" defaultChecked
              className="rounded border-white/20 bg-black/20 text-laap-accent focus:ring-0" />
          </label>
        </Field>
        <div className="bg-white/[0.03] rounded-lg border border-white/[0.06] p-3 mt-2">
          <p className="text-[10px] text-white/40 leading-relaxed">
            遵循 ARIS 宪章：主体性、原点、隐私、透明、安全、共生、进化、守护。
            工具沙箱与 Zone2 防护不可绕过。
          </p>
        </div>
      </div>
    </>
  )
}

export default SettingsPanel
