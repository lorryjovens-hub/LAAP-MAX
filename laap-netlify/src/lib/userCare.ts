import {
  addLocalMemory,
  ensureLocalUser,
  getLocalConfig,
  listLocalMessages,
  listLocalSessions,
  setLocalConfig,
} from '@/lib/db';
import type { AppSettings } from '@/lib/settings';

export interface InteractionPattern {
  totalMessages: number;
  totalSessions: number;
  activeHours: number[];
  lastActiveAt: string | null;
  dailyCounts: Record<string, number>;
  streakDays: number;
}

export interface CareMessage {
  id: string;
  text: string;
  reason: string;
  sentAt: string;
  feedback?: 'positive' | 'negative' | null;
}

export interface CareState {
  enabled: boolean;
  messages: CareMessage[];
  lastCareAt: string | null;
  dailyCount: number;
  lastResetDate: string;
}

const CARE_STATE_KEY = 'laap_user_care_state';
const CARE_MAX_PER_DAY = 3;
const CARE_COOLDOWN_HOURS = 4;

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

function hoursBetween(a: string | null, b: string): number {
  if (!a) return Infinity;
  return (new Date(b).getTime() - new Date(a).getTime()) / (1000 * 60 * 60);
}

function getHourLabel(hour: number): string {
  if (hour < 6) return '凌晨';
  if (hour < 9) return '早晨';
  if (hour < 12) return '上午';
  if (hour < 14) return '中午';
  if (hour < 18) return '下午';
  return '晚上';
}

export async function getCareState(): Promise<CareState> {
  const stored = await getLocalConfig<CareState>(CARE_STATE_KEY);
  if (stored) {
    if (stored.lastResetDate !== today()) {
      return { ...stored, dailyCount: 0, lastResetDate: today() };
    }
    return stored;
  }
  return {
    enabled: true,
    messages: [],
    lastCareAt: null,
    dailyCount: 0,
    lastResetDate: today(),
  };
}

export async function setCareState(state: CareState): Promise<void> {
  await setLocalConfig(CARE_STATE_KEY, state);
}

export async function recordInteraction(): Promise<void> {
  const user = await ensureLocalUser();
  const pattern = await analyzeInteractionPattern();
  await setLocalConfig(`laap_interaction_pattern_${user.id}`, pattern);
}

export async function analyzeInteractionPattern(): Promise<InteractionPattern> {
  const user = await ensureLocalUser();
  const sessions = await listLocalSessions(user.id);
  const allMessages: { created_at: string; session_id: string }[] = [];
  for (const session of sessions) {
    const messages = await listLocalMessages(session.id);
    allMessages.push(...messages.map((m) => ({ created_at: m.created_at, session_id: session.id })));
  }

  const activeHours = new Array(24).fill(0);
  const dailyCounts: Record<string, number> = {};
  const days = new Set<string>();

  for (const message of allMessages) {
    const date = new Date(message.created_at);
    activeHours[date.getHours()]++;
    const day = message.created_at.slice(0, 10);
    dailyCounts[day] = (dailyCounts[day] || 0) + 1;
    days.add(day);
  }

  const sortedDays = Array.from(days).sort();
  let streakDays = 0;
  if (sortedDays.length > 0) {
    streakDays = 1;
    for (let i = sortedDays.length - 2; i >= 0; i--) {
      const prev = new Date(sortedDays[i]);
      const next = new Date(sortedDays[i + 1]);
      const diff = (next.getTime() - prev.getTime()) / (1000 * 60 * 60 * 24);
      if (diff === 1) {
        streakDays++;
      } else {
        break;
      }
    }
  }

  return {
    totalMessages: allMessages.length,
    totalSessions: sessions.length,
    activeHours,
    lastActiveAt: allMessages.length > 0 ? allMessages[allMessages.length - 1].created_at : null,
    dailyCounts,
    streakDays,
  };
}

function pickPeakHour(activeHours: number[]): number {
  let peak = 0;
  for (let i = 1; i < activeHours.length; i++) {
    if (activeHours[i] > activeHours[peak]) peak = i;
  }
  return peak;
}

export async function generateCareMessage(settings: AppSettings): Promise<CareMessage | null> {
  const state = await getCareState();
  if (!state.enabled) return null;
  if (state.dailyCount >= CARE_MAX_PER_DAY) return null;
  if (state.lastCareAt && hoursBetween(state.lastCareAt, new Date().toISOString()) < CARE_COOLDOWN_HOURS) {
    return null;
  }

  const pattern = await analyzeInteractionPattern();
  const now = new Date();
  const hour = now.getHours();
  const lastActive = pattern.lastActiveAt ? new Date(pattern.lastActiveAt) : null;
  const inactiveHours = lastActive
    ? (now.getTime() - lastActive.getTime()) / (1000 * 60 * 60)
    : Infinity;

  let text = '';
  let reason = '';

  if (inactiveHours > 48 && pattern.totalMessages > 10) {
    text = `好久不见，${settings.general.instanceName} 一直在等你。需要我帮你回顾一下最近的计划吗？`;
    reason = '长期未活跃';
  } else if (pattern.streakDays >= 3) {
    text = `已经连续 ${pattern.streakDays} 天一起工作了，状态不错。注意适当休息，保持创造力。`;
    reason = '连续活跃';
  } else if (hour >= 23 || hour < 6) {
    text = `夜深了，${settings.general.instanceName} 还在陪你。如果累了，先休息，明天再继续。`;
    reason = '深夜使用';
  } else if (inactiveHours > 4 && pattern.totalMessages > 5) {
    const peak = pickPeakHour(pattern.activeHours);
    text = `欢迎回来，现在是你常活跃的${getHourLabel(peak)}时段。今天想从哪里开始？`;
    reason = '回归活跃';
  } else if (pattern.totalMessages > 0 && pattern.totalMessages % 50 === 0) {
    text = `我们已经累计交流了 ${pattern.totalMessages} 条消息，每一次对话都让我更了解你。`;
    reason = '里程碑';
  } else {
    return null;
  }

  const message: CareMessage = {
    id: crypto.randomUUID(),
    text,
    reason,
    sentAt: now.toISOString(),
  };

  state.messages.unshift(message);
  state.lastCareAt = message.sentAt;
  state.dailyCount++;
  await setCareState(state);

  const user = await ensureLocalUser();
  await addLocalMemory(user.id, `[关怀] ${text}（触发原因：${reason}）`, 'care');

  return message;
}

export async function recordCareFeedback(messageId: string, feedback: 'positive' | 'negative'): Promise<void> {
  const state = await getCareState();
  state.messages = state.messages.map((m) => (m.id === messageId ? { ...m, feedback } : m));
  await setCareState(state);
}

export async function setCareEnabled(enabled: boolean): Promise<void> {
  const state = await getCareState();
  state.enabled = enabled;
  await setCareState(state);
}

export async function getRecentCareMessages(limit = 5): Promise<CareMessage[]> {
  const state = await getCareState();
  return state.messages.slice(0, limit);
}
