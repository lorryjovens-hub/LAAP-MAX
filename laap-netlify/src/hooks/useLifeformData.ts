import { useState, useEffect } from 'react';
import { cognitiveEngine, PSI_CYCLE_LABELS, type PsiCycle, type EmotionalValence } from '@/lib/cognitiveEngine';
import { ensureGuestUser } from '@/lib/db';

export interface LifeformData {
  frame: number;
  valence: number;
  arousal: number;
  dominance: number;
  autonomy: number;
  // LAAP 增强数字生命体征
  psiCycle: PsiCycle;
  psiCycleProgress: number;
  curiosity: number;
  trust: number;
  competence: number;
  coherence: number;
  quantumAmplitude: number;
}

const VALENCE_MAP: Record<EmotionalValence, number> = {
  positive_high: 0.9,
  positive_mild: 0.75,
  curious: 0.68,
  neutral: 0.55,
  confused: 0.45,
  negative_mild: 0.35,
  negative_high: 0.15,
};

function toLifeformData(): LifeformData {
  const s = cognitiveEngine.snapshot();
  return {
    frame: s.frame,
    valence: VALENCE_MAP[s.emotion.valence],
    arousal: s.emotion.arousal,
    dominance: s.emotion.dominance,
    autonomy: s.needs.autonomy,
    psiCycle: s.psiCycle,
    psiCycleProgress: s.psiCycleProgress,
    curiosity: s.curiosity,
    trust: s.needs.relatedness,
    competence: s.needs.competence,
    coherence: s.coherence,
    quantumAmplitude: s.needs.certainty,
  };
}

export function useLifeformData(): LifeformData {
  const [data, setData] = useState<LifeformData>(() => toLifeformData());

  useEffect(() => {
    let disposed = false;
    let mounted = true;

    // Start the real cognitive engine heartbeat for the current user.
    ensureGuestUser()
      .then((user) => {
        if (disposed) return;
        cognitiveEngine.start(user.id);
        if (mounted) setData(toLifeformData());
      })
      .catch(() => {
        // If the user can't be resolved, still show engine state.
        cognitiveEngine.start('guest');
      });

    const unsubscribe = cognitiveEngine.subscribe(() => {
      setData(toLifeformData());
    });

    return () => {
      disposed = true;
      mounted = false;
      unsubscribe();
    };
  }, []);

  return data;
}

export function getCycleLabel(cycle: PsiCycle): string {
  return PSI_CYCLE_LABELS[cycle];
}