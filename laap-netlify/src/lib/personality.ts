import { getCurrentUser } from '@/lib/userMode';
import { getLocalConfig, setLocalConfig } from '@/lib/db';

const PERSONALITY_CONFIG_KEY = 'personality';

export interface PersonalityConfig {
  name: string;
  agentName?: string;
  traits: string;
  tone: string;
  backstory: string;
}

export const DEFAULT_PERSONALITY: PersonalityConfig = {
  name: 'LAAP',
  agentName: 'LAAP',
  traits: '',
  tone: '',
  backstory: '',
};

function normalizePersonality(config: Partial<PersonalityConfig>): PersonalityConfig {
  return {
    name: config.name ?? DEFAULT_PERSONALITY.name,
    agentName: config.agentName ?? config.name ?? DEFAULT_PERSONALITY.agentName,
    traits: config.traits ?? DEFAULT_PERSONALITY.traits,
    tone: config.tone ?? DEFAULT_PERSONALITY.tone,
    backstory: config.backstory ?? DEFAULT_PERSONALITY.backstory,
  };
}

export async function getPersonalityConfig(): Promise<PersonalityConfig | null> {
  const user = await getCurrentUser();
  const cfg = await getLocalConfig<PersonalityConfig>(PERSONALITY_CONFIG_KEY, user.id);
  return cfg ? normalizePersonality(cfg) : null;
}

export async function savePersonalityConfig(
  config: PersonalityConfig
): Promise<{ ok: true; config: PersonalityConfig } | { ok: false; error: string }> {
  const user = await getCurrentUser();
  const normalized = normalizePersonality(config);
  await setLocalConfig(PERSONALITY_CONFIG_KEY, normalized, user.id);
  return { ok: true, config: normalized };
}
