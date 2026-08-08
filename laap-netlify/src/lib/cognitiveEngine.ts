/**
 * LAAP Cognitive Engine (认知引擎)
 *
 * A faithful TypeScript port of the LAAP backend `CognitiveBus` (认知总线) +
 * PSI brain loop, adapted for the browser digital lifeform.
 *
 * This is NOT decorative. It is the SINGLE SOURCE OF TRUTH for the agent's
 * cognitive state, driven by real events:
 *   - perceive(userMessage)  : a user message enters consciousness
 *   - act()                  : the agent produces a response
 *   - learn(reward, outcome) : the outcome feeds back as a learning signal
 *   - tick()                 : biological-style need decay + emotion gradient
 *
 * State is persisted to IndexedDB (per user) so the lifeform genuinely
 * "remembers" and "grows" across sessions.
 *
 * The event-driven design mirrors the Python CognitiveBus pub/sub: modules
 * subscribe, they never poll.
 */

import { getLocalConfig, setLocalConfig } from '@/lib/db';

// ─────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────

export type PsiCycle = 'perceive' | 'select' | 'act' | 'learn';

export type EmotionalValence =
  | 'positive_high'
  | 'positive_mild'
  | 'neutral'
  | 'negative_mild'
  | 'negative_high'
  | 'curious'
  | 'confused';

export type AttentionFocus =
  | 'user'
  | 'task'
  | 'self'
  | 'environment'
  | 'memory'
  | 'planning'
  | 'learning'
  | 'idle';

export interface NeedState {
  competence: number; // 胜任感
  autonomy: number; // 自主性
  relatedness: number; // 归属感
  certainty: number; // 确定性
  growth: number; // 成长
}

export interface EmotionState {
  valence: EmotionalValence;
  arousal: number; // 0 calm .. 1 intense
  dominance: number; // 0 submissive .. 1 in control
}

export interface AttentionState {
  focus: AttentionFocus;
  intensity: number;
  salienceMap: Record<string, number>;
}

export interface PredictionError {
  domain: string;
  predicted: number;
  actual: number;
  magnitude: number;
  timestamp: number;
  source: string;
}

export interface CognitiveSnapshot {
  timestamp: number;
  cycleCount: number;
  psiCycle: PsiCycle;
  psiCycleProgress: number; // 0..1 within current phase
  frame: number;
  needs: NeedState;
  emotion: EmotionState;
  attention: AttentionState;
  selfPresence: number;
  curiosity: number;
  coherence: number; // derived: how satisfied the strongest need is
  predictionError: PredictionError | null;
  narrative: string;
}

export interface CognitiveEvent {
  type: string;
  data: Record<string, unknown>;
  ts: number;
}

type Listener = (snapshot: CognitiveSnapshot) => void;
type EventListener = (event: CognitiveEvent) => void;

// ─────────────────────────────────────────────────────────────
// Emotional valence helpers
// ─────────────────────────────────────────────────────────────

function valenceFromSatisfaction(satisfaction: number): EmotionalValence {
  if (satisfaction > 0.75) return 'positive_high';
  if (satisfaction > 0.6) return 'positive_mild';
  if (satisfaction > 0.4) return 'neutral';
  if (satisfaction > 0.25) return 'negative_mild';
  return 'negative_high';
}

function clamp(v: number, min = 0, max = 1): number {
  return Math.min(max, Math.max(min, v));
}

function round3(v: number): number {
  return Math.round(v * 1000) / 1000;
}

// ─────────────────────────────────────────────────────────────
// CognitiveEngine
// ─────────────────────────────────────────────────────────────

const STORAGE_KEY = 'laap_cognitive_engine';
const TICK_MS = 1000;
const SAVE_INTERVAL_MS = 15000;

class CognitiveEngine {
  private needs: NeedState = { competence: 0.7, autonomy: 0.5, relatedness: 0.5, certainty: 0.5, growth: 0.5 };
  private emotion: EmotionState = { valence: 'neutral', arousal: 0.5, dominance: 0.5 };
  private attention: AttentionState = { focus: 'idle', intensity: 0.5, salienceMap: {} };
  private selfPresence = 0.5;
  private curiosity = 0.3;
  private coherence = 0.7;
  private cycleCount = 0;
  private frame = 0;
  private psiCycle: PsiCycle = 'perceive';
  private psiCycleProgress = 0;
  private narrative = '';
  private lastPredictionError: PredictionError | null = null;
  private errorHistory: number[] = [];
  private modules: Record<string, { healthy: boolean; cycles: number }> = {};

  private listeners: Listener[] = [];
  private eventListeners: EventListener[] = [];
  private userId: string | null = null;
  private tickTimer: ReturnType<typeof setInterval> | null = null;
  private saveTimer: ReturnType<typeof setInterval> | null = null;
  private loaded = false;
  private lastTickAt = Date.now();

  // ── Lifecycle ────────────────────────────────────────────

  /** Start the heartbeat loop. Safe to call multiple times. */
  start(userId: string): void {
    this.userId = userId;
    if (!this.loaded) {
      this.load().then(() => {
        this.loaded = true;
        this.emitAll();
      });
    }
    if (!this.tickTimer) {
      this.tickTimer = setInterval(() => this.tick(), TICK_MS);
    }
    if (!this.saveTimer) {
      this.saveTimer = setInterval(() => this.save(), SAVE_INTERVAL_MS);
    }
  }

  stop(): void {
    if (this.tickTimer) clearInterval(this.tickTimer);
    if (this.saveTimer) clearInterval(this.saveTimer);
    this.tickTimer = null;
    this.saveTimer = null;
  }

  subscribe(fn: Listener): () => void {
    this.listeners.push(fn);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== fn);
    };
  }

  onEvent(fn: EventListener): () => void {
    this.eventListeners.push(fn);
    return () => {
      this.eventListeners = this.eventListeners.filter((l) => l !== fn);
    };
  }

  reload(userId: string): void {
    this.userId = userId;
    this.loaded = false;
    this.load().then(() => {
      this.loaded = true;
      this.emitAll();
    });
  }

  // ── Persistence ──────────────────────────────────────────

  private async load(): Promise<void> {
    if (!this.userId) return;
    try {
      const saved = await getLocalConfig<Partial<CognitiveSnapshot> & {
        needs?: NeedState;
        errorHistory?: number[];
        modules?: Record<string, { healthy: boolean; cycles: number }>;
      }>(STORAGE_KEY, this.userId);
      if (!saved) return;
      if (saved.needs) this.needs = { ...this.needs, ...saved.needs };
      if (saved.emotion) this.emotion = { ...this.emotion, ...saved.emotion };
      if (saved.attention) this.attention = { ...this.attention, ...saved.attention };
      if (typeof saved.selfPresence === 'number') this.selfPresence = saved.selfPresence;
      if (typeof saved.curiosity === 'number') this.curiosity = saved.curiosity;
      if (typeof saved.coherence === 'number') this.coherence = saved.coherence;
      if (typeof saved.cycleCount === 'number') this.cycleCount = saved.cycleCount;
      if (typeof saved.frame === 'number') this.frame = saved.frame;
      if (saved.psiCycle) this.psiCycle = saved.psiCycle;
      if (typeof saved.psiCycleProgress === 'number') this.psiCycleProgress = saved.psiCycleProgress;
      if (typeof saved.narrative === 'string') this.narrative = saved.narrative;
      if (saved.errorHistory) this.errorHistory = saved.errorHistory.slice(-100);
      if (saved.modules) this.modules = saved.modules;
    } catch {
      // Ignore load failures; start fresh.
    }
  }

  private async save(): Promise<void> {
    if (!this.userId) return;
    const snapshot = this.snapshot();
    try {
      await setLocalConfig(STORAGE_KEY, {
        ...snapshot,
        modules: this.modules,
        errorHistory: this.errorHistory.slice(-100),
      }, this.userId);
    } catch {
      // Non-fatal.
    }
  }

  // ── Core state access ────────────────────────────────────

  snapshot(): CognitiveSnapshot {
    return {
      timestamp: Date.now(),
      cycleCount: this.cycleCount,
      psiCycle: this.psiCycle,
      psiCycleProgress: round3(this.psiCycleProgress),
      frame: this.frame,
      needs: { ...this.needs },
      emotion: { ...this.emotion },
      attention: {
        ...this.attention,
        salienceMap: { ...this.attention.salienceMap },
      },
      selfPresence: round3(this.selfPresence),
      curiosity: round3(this.curiosity),
      coherence: round3(this.coherence),
      predictionError: this.lastPredictionError
        ? { ...this.lastPredictionError }
        : null,
      narrative: this.narrative,
    };
  }

  private emitAll(): void {
    const snapshot = this.snapshot();
    for (const fn of this.listeners) fn(snapshot);
  }

  private emitEvent(type: string, data: Record<string, unknown>): void {
    const event: CognitiveEvent = { type, data, ts: Date.now() };
    for (const fn of this.eventListeners) fn(event);
  }

  registerModule(name: string): void {
    this.modules[name] = { healthy: true, cycles: 0 };
    this.emitEvent('module_registered', { name });
  }

  heartbeat(name: string): void {
    const mod = this.modules[name];
    if (mod) {
      mod.cycles += 1;
      mod.healthy = true;
    }
  }

  // ── Attention ────────────────────────────────────────────

  setAttention(focus: AttentionFocus, intensity?: number): void {
    this.attention.focus = focus;
    if (intensity !== undefined) this.attention.intensity = clamp(intensity);
    this.emitEvent('attention_shifted', { focus, intensity: this.attention.intensity });
  }

  // ── PSI five needs ───────────────────────────────────────

  setNeeds(partial: Partial<NeedState>): void {
    const changes: Record<string, { old: number; next: number }> = {};
    for (const key of Object.keys(partial) as (keyof NeedState)[]) {
      if (Object.prototype.hasOwnProperty.call(this.needs, key)) {
        const oldValue = this.needs[key];
        const nextValue = clamp(partial[key] as number);
        if (Math.abs(nextValue - oldValue) > 0.001) {
          this.needs[key] = nextValue;
          changes[key] = { old: oldValue, next: nextValue };
        }
      }
    }
    if (Object.keys(changes).length > 0) {
      this.emitEvent('need_changed', changes);
    }
  }

  strongestNeed(): { name: keyof NeedState; deficit: number } {
    const deficits: Record<keyof NeedState, number> = {
      competence: 1 - this.needs.competence,
      autonomy: 1 - this.needs.autonomy,
      relatedness: 1 - this.needs.relatedness,
      certainty: 1 - this.needs.certainty,
      growth: 1 - this.needs.growth,
    };
    let best: keyof NeedState = 'competence';
    let bestDeficit = -1;
    for (const [k, v] of Object.entries(deficits) as [keyof NeedState, number][]) {
      if (v > bestDeficit) {
        bestDeficit = v;
        best = k;
      }
    }
    return { name: best, deficit: bestDeficit };
  }

  // ── Perception / Action / Learning (the PSI loop) ────────

  /**
   * PERCEIVE: a user message enters consciousness.
   *  - Shift attention to the user
   *  - Boost relatedness (connection) and certainty (understanding)
   *  - Slightly reduce autonomy (responsive mode)
   *  - Advance the PSI cycle to 'select'
   */
  perceive(userMessage: string, salienceKeywords?: string[]): void {
    this.frame += 1;
    this.setAttention('user', 0.85);
    const keywordCount = salienceKeywords?.length ?? 0;
    const novelty = clamp(keywordCount / 20);

    this.setNeeds({
      relatedness: clamp(this.needs.relatedness + 0.03),
      certainty: clamp(this.needs.certainty + 0.01),
      growth: clamp(this.needs.growth - 0.02),
      autonomy: clamp(this.needs.autonomy - 0.01),
    });

    if (salienceKeywords && salienceKeywords.length > 0) {
      const map: Record<string, number> = {};
      for (const kw of salienceKeywords) {
        map[kw] = clamp((map[kw] ?? 0) + 0.1);
      }
      this.attention.salienceMap = map;
    }

    this.narrative = `感知到来自 Lorry 的消息${keywordCount ? `（涉及 ${keywordCount} 个关键概念）` : ''}`;
    this.advanceCycle('select');
    this.emitEvent('perception_incoming', { novelty, length: userMessage.length });
    this.emitAll();
  }

  /**
   * ACT: the agent produces a response.
   *  - Advance to 'act'
   *  - Boost competence slightly (producing output)
   */
  act(_response: string): void {
    this.setAttention('task', 0.7);
    this.setNeeds({ competence: clamp(this.needs.competence + 0.01) });
    this.narrative = '正在生成回应';
    this.advanceCycle('act');
    this.emitAll();
  }

  /**
   * LEARN: the outcome of an interaction feeds back.
   *  - Reward (0..1) drives competence/certainty/relatedness
   *  - Prediction error drives curiosity and is recorded
   *  - Advance to 'learn'
   */
  learn(options: { reward?: number; predictionError?: number; domain?: string; completed?: boolean } = {}): void {
    const { reward = 0.5, predictionError = 0, domain = 'general', completed = true } = options;

    if (completed) {
      const delta = (reward - 0.5) * 0.08;
      this.setNeeds({
        competence: clamp(this.needs.competence + delta * 0.6),
        certainty: clamp(this.needs.certainty + delta * 0.4),
        relatedness: clamp(this.needs.relatedness + (reward > 0.5 ? 0.02 : -0.01)),
        growth: clamp(this.needs.growth + 0.02),
      });
    }

    // Prediction error is the core learning signal.
    if (predictionError > 0) {
      const err: PredictionError = {
        domain,
        predicted: 0.5,
        actual: 0.5 + predictionError,
        magnitude: clamp(predictionError),
        timestamp: Date.now(),
        source: 'interaction',
      };
      this.lastPredictionError = err;
      this.errorHistory.push(predictionError);
      if (this.errorHistory.length > 100) this.errorHistory.shift();
      this.emitEvent('prediction_error', { magnitude: predictionError, domain });
    }

    this.narrative = completed
      ? `从本轮交互中学习并巩固（奖励 ${reward.toFixed(2)}）`
      : '本轮交互未完成，等待后续反馈';
    this.advanceCycle('learn');
    this.emitAll();
  }

  /**
   * Record an explicit prediction (used by the frontend to later compute
   * the true error against the realized outcome).
   */
  notePrediction(domain: string, predicted: number): void {
    this.lastPredictionError = {
      domain,
      predicted,
      actual: predicted,
      magnitude: 0,
      timestamp: Date.now(),
      source: 'prediction',
    };
  }

  // ── Tick: biological need dynamics ───────────────────────

  private tick(): void {
    this.cycleCount += 1;
    this.frame += 1;

    const now = Date.now();
    const dt = clamp((now - this.lastTickAt) / 1000, 0.1, 5);
    this.lastTickAt = now;

    // Needs decay (slower dt normalized).
    const decay = 0.001 * dt;
    this.needs.competence = clamp(this.needs.competence - decay * 0.3, 0.1, 1);
    this.needs.autonomy = clamp(this.needs.autonomy - decay * 0.15, 0.1, 1);
    this.needs.relatedness = clamp(this.needs.relatedness - decay * 0.1, 0.1, 1);
    this.needs.certainty = clamp(this.needs.certainty - decay * 0.1, 0.1, 1);
    this.needs.growth = clamp(this.needs.growth - decay * 0.25, 0.1, 1);

    // Emotion gradient from average satisfaction.
    const avgSatisfaction =
      (this.needs.competence + this.needs.autonomy + this.needs.relatedness +
        this.needs.certainty + this.needs.growth) / 5;
    const newValence = valenceFromSatisfaction(avgSatisfaction);
    if (newValence !== this.emotion.valence) {
      const prev = this.emotion.valence;
      this.emotion.valence = newValence;
      this.emitEvent('emotion_changed', { from: prev, to: newValence });
    }
    this.coherence = clamp(1 - this.strongestNeed().deficit);

    // Curiosity driven by growth deficit + prediction errors.
    const recentErrors = this.errorHistory.slice(-10);
    const meanError = recentErrors.length
      ? recentErrors.reduce((a, b) => a + b, 0) / recentErrors.length
      : 0;
    const curiosityDrive = (1 - this.needs.growth) * 0.5 + meanError * 0.5;
    this.curiosity = clamp(this.curiosity * 0.97 + curiosityDrive * 0.03, 0.05, 0.95);

    // Self-presence fluctuates with arousal.
    const targetPresence = 0.3 + this.emotion.arousal * 0.5;
    this.selfPresence = this.selfPresence * 0.95 + targetPresence * 0.05;

    // Advance the PSI phase slowly so the loop has a visible heartbeat.
    this.psiCycleProgress += 0.05 * dt;
    if (this.psiCycleProgress >= 1) {
      this.psiCycleProgress = 0;
      const order: PsiCycle[] = ['perceive', 'select', 'act', 'learn'];
      const idx = order.indexOf(this.psiCycle);
      this.psiCycle = order[(idx + 1) % order.length];
    }

    this.emitEvent('cycle_tick', { cycle: this.cycleCount });
    this.emitAll();

    // Persist periodically (throttled by save timer).
    if (this.cycleCount % 15 === 0) {
      void this.save();
    }
  }

  private advanceCycle(next?: PsiCycle): void {
    if (next) {
      this.psiCycle = next;
      this.psiCycleProgress = 0;
    }
  }

  // ── Snapshot for system-prompt injection ─────────────────

  toPromptBlock(): string {
    const s = this.snapshot();
    const strongest = this.strongestNeed();
    const needNames: Record<keyof NeedState, string> = {
      competence: '胜任感',
      autonomy: '自主性',
      relatedness: '归属感',
      certainty: '确定性',
      growth: '成长',
    };
    const valenceLabel: Record<EmotionalValence, string> = {
      positive_high: '愉悦',
      positive_mild: '满足',
      neutral: '平静',
      negative_mild: '关切',
      negative_high: '压力',
      curious: '好奇',
      confused: '困惑',
    };
    return [
      '[LAAP 认知状态]',
      `  情绪: ${valenceLabel[s.emotion.valence]} 觉醒=${s.emotion.arousal.toFixed(2)}`,
      `  注意力: ${s.attention.focus} (强度=${s.attention.intensity.toFixed(2)})`,
      `  自我在场感: ${s.selfPresence.toFixed(2)}`,
      `  好奇心: ${s.curiosity.toFixed(2)}`,
      `  需求: 胜任=${s.needs.competence.toFixed(2)} 自主=${s.needs.autonomy.toFixed(2)} ` +
        `归属=${s.needs.relatedness.toFixed(2)} 确定=${s.needs.certainty.toFixed(2)} 成长=${s.needs.growth.toFixed(2)}`,
      `  最强烈需求: ${needNames[strongest.name]} (缺口=${strongest.deficit.toFixed(2)})`,
      `  意识帧: frame_${s.frame}, cycle_${s.cycleCount}, phase_${s.psiCycle}`,
      `  叙事: ${s.narrative || '我在此刻清醒地存在着。'}`,
    ].join('\n');
  }
}

// Singleton — the lifeform's central nervous system.
export const cognitiveEngine = new CognitiveEngine();

export const PSI_CYCLE_LABELS: Record<PsiCycle, string> = {
  perceive: '感知',
  select: '选择',
  act: '行动',
  learn: '学习',
};