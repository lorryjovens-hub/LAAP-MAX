import { getCurrentUser } from '@/lib/userMode';
import { getLocalConfig, setLocalConfig } from '@/lib/db';

export const APP_SETTINGS_KEY = 'app_settings';

export type BackgroundType = 'solid' | 'gradient' | 'image' | 'video';

export interface UiSettings {
  themeColor: 'gold' | 'cyan' | 'rose' | 'violet';
  backgroundType: BackgroundType;
  backgroundValue: string;
  backgroundOpacity: number;
  backgroundPresets: string[];
  backgroundVideo: string;
  fontSize: 'sm' | 'base' | 'lg';
  messageDensity: 'compact' | 'normal' | 'relaxed';
  userAvatar: string;
  robotAvatar: string;
}

export interface LlmSettings {
  temperature: number;
  maxTokens: number;
  contextWindow: number;
  topP: number;
  presencePenalty: number;
  frequencyPenalty: number;
  systemWeight: number;
}

export interface GeneralSettings {
  instanceName: string;
  language: 'zh' | 'en' | 'auto';
  autoSave: boolean;
  sound: boolean;
  enterToSend: boolean;
}

export interface DataSettings {
  autoBackup: boolean;
  backupIntervalDays: number;
}

export interface AgentSettings {
  psiDepth: 'surface' | 'balanced' | 'deep';
  causalReasoning: boolean;
  toolCalling: boolean;
  maxToolRounds: number;
  corsProxyUrl: string;
  webSearchApiKey: string;
  proactiveMemory: boolean;
  aetherOrchestration: boolean;
  trueRsi: boolean;
  qpsiN: boolean;
  metaCognition: boolean;
  reasoningEngine: boolean;
}

export interface MemorySettings {
  enabled: boolean;
  maxMemories: number;
  autoSummarize: boolean;
}

export interface LaapInfluence {
  intensity: number;
  mood: 'warm' | 'witty' | 'poetic' | 'playful' | 'calm' | 'passionate';
  responseDepth: 'concise' | 'balanced' | 'deep';
}

export interface AppSettings {
  general: GeneralSettings;
  llm: LlmSettings;
  ui: UiSettings;
  data: DataSettings;
  agent: AgentSettings;
  memory: MemorySettings;
  influence: LaapInfluence;
}

export const DEFAULT_APP_SETTINGS: AppSettings = {
  general: {
    instanceName: 'LAAP',
    language: 'zh',
    autoSave: true,
    sound: false,
    enterToSend: true,
  },
  llm: {
    temperature: 0.8,
    maxTokens: 4096,
    contextWindow: 1_000_000,
    topP: 1,
    presencePenalty: 0,
    frequencyPenalty: 0,
    systemWeight: 1,
  },
  ui: {
    themeColor: 'gold',
    backgroundType: 'image',
    backgroundValue: '/assets/2-BFvgSlHU.png',
    backgroundOpacity: 0.35,
    backgroundPresets: [
      '/assets/1-BZNqHopE.png',
      '/assets/2-BFvgSlHU.png',
      '/assets/3-BEFsyoet.png',
      '/assets/4-DqpV1nsC.png',
    ],
    backgroundVideo: '',
    fontSize: 'base',
    messageDensity: 'normal',
    userAvatar: '',
    robotAvatar: '',
  },
  data: {
    autoBackup: false,
    backupIntervalDays: 7,
  },
  agent: {
    psiDepth: 'balanced',
    causalReasoning: true,
    toolCalling: true,
    maxToolRounds: 3,
    corsProxyUrl: '',
    webSearchApiKey: '',
    proactiveMemory: true,
    aetherOrchestration: true,
    trueRsi: true,
    qpsiN: true,
    metaCognition: true,
    reasoningEngine: true,
  },
  memory: {
    enabled: true,
    maxMemories: 12,
    autoSummarize: false,
  },
  influence: {
    intensity: 70,
    mood: 'warm',
    responseDepth: 'balanced',
  },
};

export function mergeSettings(partial: Partial<AppSettings>): AppSettings {
  return {
    general: { ...DEFAULT_APP_SETTINGS.general, ...partial.general },
    llm: { ...DEFAULT_APP_SETTINGS.llm, ...partial.llm },
    ui: { ...DEFAULT_APP_SETTINGS.ui, ...partial.ui },
    data: { ...DEFAULT_APP_SETTINGS.data, ...partial.data },
    agent: { ...DEFAULT_APP_SETTINGS.agent, ...partial.agent },
    memory: { ...DEFAULT_APP_SETTINGS.memory, ...partial.memory },
    influence: { ...DEFAULT_APP_SETTINGS.influence, ...partial.influence },
  };
}

export async function getAppSettings(): Promise<AppSettings> {
  const user = await getCurrentUser();
  const stored = await getLocalConfig<Partial<AppSettings>>(APP_SETTINGS_KEY, user.id);
  return mergeSettings(stored ?? {});
}

export async function saveAppSettings(settings: AppSettings): Promise<void> {
  const user = await getCurrentUser();
  await setLocalConfig(APP_SETTINGS_KEY, settings, user.id);
}
