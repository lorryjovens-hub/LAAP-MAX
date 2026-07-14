'use client';

import { useEffect, useRef } from 'react';

interface MatrixRainProps {
  enabled?: boolean;
  density?: number; // chars per column
  speed?: number;
}

export default function MatrixRain({ enabled = true, density = 30, speed = 50 }: MatrixRainProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!enabled) return;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*+=-_<>/\\|{}[]ψΨαβγδεθηλμνπρστφχωΔΩΣΠ';
    const fontSize = 12;
    const columns = Math.floor(canvas.width / fontSize);
    const drops: number[] = Array(columns).fill(0);

    function draw() {
      ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.fillStyle = '#00ff41';
      ctx.font = `${fontSize}px "JetBrains Mono", monospace`;

      for (let i = 0; i < drops.length; i++) {
        const char = chars[Math.floor(Math.random() * chars.length)];
        const x = i * fontSize;
        const y = drops[i] * fontSize;

        // Head character brighter
        ctx.fillStyle = '#00ff41';
        ctx.fillText(char, x, y);

        // Trail
        for (let j = 1; j < 5; j++) {
          ctx.fillStyle = `rgba(0, 255, 65, ${0.15 / j})`;
          const trailY = y - j * fontSize;
          if (trailY > 0) {
            ctx.fillText(chars[Math.floor(Math.random() * chars.length)], x, trailY);
          }
        }

        if (y > canvas.height && Math.random() > 0.975) {
          drops[i] = 0;
        }
        drops[i]++;
      }
    }

    const interval = setInterval(draw, speed);
    const handleResize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    return () => {
      clearInterval(interval);
      window.removeEventListener('resize', handleResize);
    };
  }, [enabled, speed]);

  if (!enabled) return null;

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0 opacity-30"
      style={{ mixBlendMode: 'screen' }}
    />
  );
}
