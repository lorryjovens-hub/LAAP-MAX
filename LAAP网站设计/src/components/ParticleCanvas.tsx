import { useEffect, useRef } from 'react';

const ACCENT_COLORS = ['#22d3ee', '#f59e0b', '#f43f5e', '#10b981'];
const PARTICLE_COUNT = 70;
const CONNECTION_DISTANCE = 120;
const MOUSE_RADIUS = 150;

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  color: string;
}

export default function ParticleCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const mouseRef = useRef({ x: -1000, y: -1000 });
  const rafRef = useRef<number>(0);
  const opacityRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;

    function resize() {
      const rect = canvas!.getBoundingClientRect();
      canvas!.width = rect.width * dpr;
      canvas!.height = rect.height * dpr;
      ctx!.scale(dpr, dpr);
    }

    resize();

    // Initialize particles
    const rect = canvas.getBoundingClientRect();
    particlesRef.current = Array.from({ length: PARTICLE_COUNT }, () => ({
      x: Math.random() * rect.width,
      y: Math.random() * rect.height,
      vx: (Math.random() - 0.5) * 0.6,
      vy: (Math.random() - 0.5) * 0.6,
      radius: Math.random() * 2 + 1,
      color: ACCENT_COLORS[Math.floor(Math.random() * ACCENT_COLORS.length)],
    }));

    function animate() {
      const w = canvas!.getBoundingClientRect().width;
      const h = canvas!.getBoundingClientRect().height;

      // Fade in
      if (opacityRef.current < 1) {
        opacityRef.current = Math.min(1, opacityRef.current + 0.008);
      }

      ctx!.clearRect(0, 0, w, h);
      ctx!.save();
      ctx!.globalAlpha = opacityRef.current;

      const particles = particlesRef.current;
      const mouse = mouseRef.current;

      // Update and draw particles
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;

        // Clamp position
        p.x = Math.max(0, Math.min(w, p.x));
        p.y = Math.max(0, Math.min(h, p.y));

        // Mouse attraction
        const dx = mouse.x - p.x;
        const dy = mouse.y - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < MOUSE_RADIUS && dist > 0) {
          p.x += dx * 0.02;
          p.y += dy * 0.02;
        }
      }

      // Draw connections
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < CONNECTION_DISTANCE) {
            const opacity = (1 - dist / CONNECTION_DISTANCE) * 0.25;
            ctx!.beginPath();
            ctx!.strokeStyle = `rgba(255, 255, 255, ${opacity})`;
            ctx!.lineWidth = 0.5;
            ctx!.moveTo(particles[i].x, particles[i].y);
            ctx!.lineTo(particles[j].x, particles[j].y);
            ctx!.stroke();
          }
        }
      }

      // Draw particles
      for (const p of particles) {
        ctx!.beginPath();
        ctx!.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx!.fillStyle = p.color;
        ctx!.fill();
      }

      ctx!.restore();
      rafRef.current = requestAnimationFrame(animate);
    }

    rafRef.current = requestAnimationFrame(animate);

    function onMouseMove(e: MouseEvent) {
      const rect = canvas!.getBoundingClientRect();
      mouseRef.current = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      };
    }

    function onMouseLeave() {
      mouseRef.current = { x: -1000, y: -1000 };
    }

    function onResize() {
      resize();
      const rect = canvas!.getBoundingClientRect();
      for (const p of particlesRef.current) {
        p.x = Math.min(p.x, rect.width);
        p.y = Math.min(p.y, rect.height);
      }
    }

    canvas.addEventListener('mousemove', onMouseMove);
    canvas.addEventListener('mouseleave', onMouseLeave);
    window.addEventListener('resize', onResize);

    return () => {
      cancelAnimationFrame(rafRef.current);
      canvas.removeEventListener('mousemove', onMouseMove);
      canvas.removeEventListener('mouseleave', onMouseLeave);
      window.removeEventListener('resize', onResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 0,
      }}
    />
  );
}
