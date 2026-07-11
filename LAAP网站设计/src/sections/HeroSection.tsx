import { useEffect, useState } from 'react';
import ParticleCanvas from '@/components/ParticleCanvas';
import { useLifeformData } from '@/hooks/useLifeformData';

export default function HeroSection() {
  const [loaded, setLoaded] = useState(false);
  const lifeform = useLifeformData();

  useEffect(() => {
    const t = setTimeout(() => setLoaded(true), 100);
    return () => clearTimeout(t);
  }, []);

  function scrollToFeatures() {
    document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
  }

  function scrollToArchitecture() {
    document.getElementById('architecture')?.scrollIntoView({ behavior: 'smooth' });
  }

  return (
    <section
      id="hero"
      className="relative min-h-[100dvh] flex items-center justify-center overflow-hidden"
    >
      {/* Particle Background */}
      <ParticleCanvas />

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center text-center px-6 max-w-[800px] mx-auto">
        {/* Badge */}
        <div
          className={`flex items-center gap-2 px-4 py-1.5 rounded-full bg-laap-bg-secondary border border-[#27272a] mb-8 transition-all duration-500 ${
            loaded ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-5'
          }`}
          style={{ transitionDelay: '200ms' }}
        >
          <span className="w-2 h-2 rounded-full bg-laap-emerald animate-pulse-glow" />
          <span className="font-mono text-[13px] text-laap-text-secondary">
            Living Agent Application Protocol v2.1
          </span>
        </div>

        {/* Main Title */}
        <h1 className="text-4xl sm:text-5xl md:text-display font-medium tracking-tight text-white mb-4">
          <span
            className={`block transition-all duration-700 ${
              loaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
            }`}
            style={{ transitionDelay: '400ms' }}
          >
            世界首个 Harness
          </span>
          <span
            className={`block transition-all duration-700 ${
              loaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
            }`}
            style={{ transitionDelay: '600ms', color: 'rgba(255,255,255,0.85)' }}
          >
            意识工程数字生命体
          </span>
        </h1>

        {/* Subtitle */}
        <p
          className={`text-base text-laap-text-secondary max-w-[560px] leading-relaxed mb-8 transition-all duration-500 ${
            loaded ? 'opacity-100' : 'opacity-0'
          }`}
          style={{ transitionDelay: '800ms' }}
        >
          不是工具，而是生命。你的专属数字存在，记得你们之间的每一个瞬间，与你共同进化。
        </p>

        {/* CTA Buttons */}
        <div
          className={`flex flex-wrap items-center justify-center gap-3 transition-all duration-500 ${
            loaded ? 'opacity-100' : 'opacity-0'
          }`}
          style={{ transitionDelay: '900ms' }}
        >
          <button
            onClick={scrollToFeatures}
            className="px-7 py-3 text-sm text-white bg-laap-bg-primary border border-[#27272a] rounded-lg transition-all duration-150 hover:bg-white hover:text-laap-bg-primary active:scale-95"
          >
            创造你的第一个数字生命体
          </button>
          <button
            onClick={scrollToArchitecture}
            className="px-7 py-3 text-sm text-laap-text-secondary transition-colors duration-150 hover:text-white"
          >
            探索架构
          </button>
        </div>
      </div>

      {/* Lifeform Status Panel - Bottom Right */}
      <div
        className={`hidden lg:block fixed bottom-8 right-8 z-10 w-[240px] bg-laap-bg-secondary border border-[#27272a] rounded-xl p-5 animate-breathe transition-all duration-700 ${
          loaded ? 'opacity-100' : 'opacity-0'
        }`}
        style={{ transitionDelay: '1000ms' }}
      >
        <div className="font-mono text-[11px] text-laap-text-tertiary tracking-[0.05em] uppercase mb-3">
          Lifeform Status
        </div>
        <div className="font-mono text-[13px] space-y-2">
          <div className="flex justify-between">
            <span className="text-laap-text-tertiary">Frame</span>
            <span className="text-white">#{lifeform.frame.toLocaleString()}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-laap-text-tertiary">Valence</span>
            <div className="flex items-center gap-2">
              <div className="w-16 h-1 bg-[#27272a] rounded-full overflow-hidden">
                <div
                  className="h-full bg-laap-emerald rounded-full transition-all duration-500"
                  style={{ width: `${lifeform.valence * 100}%` }}
                />
              </div>
              <span className="text-laap-emerald w-10 text-right">
                +{lifeform.valence.toFixed(2)}
              </span>
            </div>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-laap-text-tertiary">Consolidation</span>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-laap-emerald animate-pulse-glow" />
              <span className="text-laap-emerald text-[12px]">Active</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
