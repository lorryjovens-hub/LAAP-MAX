import { useState, useEffect, useRef } from 'react';

interface LifeformData {
  frame: number;
  valence: number;
  arousal: number;
  dominance: number;
  autonomy: number;
}

export function useLifeformData(): LifeformData {
  const [data, setData] = useState<LifeformData>({
    frame: 2847,
    valence: 0.72,
    arousal: 0.45,
    dominance: 0.61,
    autonomy: 0.68,
  });

  const frameRef = useRef(2847);

  useEffect(() => {
    const interval = setInterval(() => {
      frameRef.current += 1;
      setData((prev) => ({
        frame: frameRef.current,
        valence: clamp(prev.valence + (Math.random() - 0.5) * 0.04),
        arousal: clamp(prev.arousal + (Math.random() - 0.5) * 0.04),
        dominance: clamp(prev.dominance + (Math.random() - 0.5) * 0.04),
        autonomy: clamp(prev.autonomy + (Math.random() - 0.5) * 0.04),
      }));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return data;
}

function clamp(v: number): number {
  return Math.max(0, Math.min(1, Math.round(v * 100) / 100));
}
