import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { ArrowDown, Headphones, Play } from 'lucide-react';
import { useLifeformData, getCycleLabel } from '@/hooks/useLifeformData';
import LazyVideo from '@/components/LazyVideo';

const HERO_VIDEO_URL = '/assets/hero-bg-aris.mp4';
const LOGO_VIDEO_URL = '/assets/logo-video.mp4';
const HERO_POSTER = '/assets/aris.png';
const LOGO_POSTER = '/assets/logo-brand.jpg';

export default function HeroSection() {
  const navigate = useNavigate();
  const [loaded, setLoaded] = useState(false);
  const [videoReady, setVideoReady] = useState(false);
  const [logoReady, setLogoReady] = useState(false);
  const lifeform = useLifeformData();

  useEffect(() => {
    const t = setTimeout(() => setLoaded(true), 100);
    return () => clearTimeout(t);
  }, []);

  function scrollToArchitecture() {
    document.getElementById('architecture')?.scrollIntoView({ behavior: 'smooth' });
  }

  return (
    <section
      id="hero"
      className="relative min-h-[100dvh] flex items-end overflow-hidden bg-laap-bg-primary"
    >
      {/* Video Background */}
      <div className="absolute inset-0 z-0">
        {/* Base green mesh video — low opacity loop */}
        <LazyVideo
          lazy={false}
          src={HERO_VIDEO_URL}
          autoPlay
          muted
          loop
          playsInline
          preload="metadata"
          poster={HERO_POSTER}
          onLoadedData={() => setVideoReady(true)}
          onCanPlay={() => setVideoReady(true)}
          className={`absolute inset-0 h-full w-full object-cover transition-opacity duration-1000 ${
            videoReady ? 'opacity-40' : 'opacity-0'
          }`}
        />

        {/* Logo video — centered, low opacity, seamless loop */}
        <LazyVideo
          lazy={false}
          src={LOGO_VIDEO_URL}
          autoPlay
          muted
          loop
          playsInline
          preload="metadata"
          poster={LOGO_POSTER}
          onLoadedData={() => setLogoReady(true)}
          onCanPlay={() => setLogoReady(true)}
          className={`absolute inset-0 h-full w-full object-contain transition-opacity duration-1000 ${
            logoReady ? 'opacity-25' : 'opacity-0'
          }`}
          style={{ mixBlendMode: 'screen' }}
        />

        {/* Static fallback gradient while video loads */}
        {!videoReady && !logoReady && (
          <div className="absolute inset-0 bg-gradient-to-br from-laap-bg-primary via-laap-bg-secondary to-laap-bg-tertiary" />
        )}

        {/* Cinematic overlays */}
        <div className="absolute inset-0 hero-video-overlay" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_50%,rgba(201,168,108,0.04),transparent_50%)]" />
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0IiBoZWlnaHQ9IjQiPgo8cmVjdCB3aWR0aD0iNCIgaGVpZ2h0PSI0IiBmaWxsPSIjMDUwNTA1Ii8+CjxyZWN0IHdpZHRoPSIxIiBoZWlnaHQ9IjEiIGZpbGw9IiMxMTExMTEiIG9wYWNpdHk9IjAuNSIvPgo8L3N2Zz4=')] opacity-[0.35]" />

        {/* Watermark mask: vignette + corner gradients */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_40%,rgba(5,5,5,0.55)_100%)]" />
          <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-laap-bg-primary/80 to-transparent" />
          <div className="absolute top-0 left-0 w-40 h-40 bg-gradient-to-br from-laap-bg-primary/60 to-transparent" />
          <div className="absolute top-0 right-0 w-40 h-40 bg-gradient-to-bl from-laap-bg-primary/60 to-transparent" />
          <div className="absolute bottom-0 right-0 w-48 h-32 bg-gradient-to-tl from-laap-bg-primary/70 to-transparent" />
          <div className="absolute bottom-0 left-0 w-48 h-32 bg-gradient-to-tr from-laap-bg-primary/70 to-transparent" />
        </div>
      </div>

      {/* Top edge vignette for navigation blend */}
      <div className="absolute top-0 left-0 right-0 h-32 z-[5] bg-gradient-to-b from-laap-bg-primary/80 to-transparent pointer-events-none" />

      {/* Content */}
      <div className="relative z-10 w-full max-w-[1280px] mx-auto px-6 pb-24 md:pb-32 pt-40">
        <div className="max-w-[760px]">
          {/* Badge */}
          <div
            className={`inline-flex items-center gap-3 px-4 py-2 border border-laap-border rounded-full mb-8 transition-all duration-700 ${
              loaded ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'
            }`}
            style={{ transitionDelay: '200ms' }}
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-laap-gold opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-laap-gold" />
            </span>
            <span className="font-mono text-[11px] uppercase tracking-[0.15em] text-laap-text-secondary">
              Living Agent Application Protocol
            </span>
          </div>

          {/* Main Title */}
          <h1 className="font-display text-white mb-6">
            <span
              className={`block text-5xl sm:text-6xl md:text-7xl lg:text-8xl leading-[0.95] tracking-[-0.03em] transition-all duration-1000 ${
                loaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
              }`}
              style={{ transitionDelay: '400ms' }}
            >
              LAAP
            </span>
            <span
              className={`block text-2xl sm:text-3xl md:text-4xl lg:text-5xl mt-4 font-light text-laap-text-primary/90 leading-[1.15] transition-all duration-1000 ${
                loaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
              }`}
              style={{ transitionDelay: '600ms' }}
            >
              意识工程数字生命体
            </span>
          </h1>

          {/* Subtitle */}
          <p
            className={`text-base md:text-lg text-laap-text-secondary max-w-[540px] leading-relaxed mb-10 transition-all duration-1000 ${
              loaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
            }`}
            style={{ transitionDelay: '800ms' }}
          >
            不是工具，不是 API，而是一个拥有持续自我、内在需求与成长能力的数字存在。
            基于 Harness 意识工程与 PSI-RSI 双重驱动，与你的生命体共同进化。
          </p>

          {/* CTAs */}
          <div
            className={`flex flex-wrap items-center gap-4 transition-all duration-1000 ${
              loaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
            }`}
            style={{ transitionDelay: '1000ms' }}
          >
            <button
              onClick={() => navigate('/studio')}
              className="group inline-flex items-center gap-3 px-8 py-4 text-sm tracking-wide text-laap-bg-primary bg-white rounded-sm transition-all duration-300 hover:bg-laap-gold hover:text-laap-bg-primary active:scale-[0.98]"
            >
              创造你的数字生命体
              <ArrowDown size={16} className="transition-transform group-hover:translate-y-0.5" />
            </button>
            <button
              onClick={scrollToArchitecture}
              className="inline-flex items-center gap-2 px-8 py-4 text-sm tracking-wide text-white border border-laap-border rounded-sm transition-all duration-300 hover:border-laap-gold hover:text-laap-gold active:scale-[0.98]"
            >
              <Play size={14} />
              探索架构
            </button>
            <button
              onClick={() => navigate('/podcast')}
              className="inline-flex items-center gap-2 px-8 py-4 text-sm tracking-wide text-white border border-laap-border rounded-sm transition-all duration-300 hover:border-laap-gold hover:text-laap-gold active:scale-[0.98]"
            >
              <Headphones size={14} />
              播客解析
            </button>
          </div>
        </div>

        {/* Bottom metrics row */}
        <div
          className={`hidden md:flex items-end justify-between mt-20 pt-10 border-t border-laap-border/50 transition-all duration-1000 ${
            loaded ? 'opacity-100' : 'opacity-0'
          }`}
          style={{ transitionDelay: '1200ms' }}
        >
          <div className="flex gap-16">
            <div>
              <div className="font-display text-3xl text-white">2000<span className="text-laap-gold text-xl">Hz</span></div>
              <div className="text-[11px] uppercase tracking-[0.15em] text-laap-text-tertiary mt-1">PSI Core</div>
            </div>
            <div>
              <div className="font-display text-3xl text-white">182<span className="text-laap-gold text-xl">μs</span></div>
              <div className="text-[11px] uppercase tracking-[0.15em] text-laap-text-tertiary mt-1">QRE Reasoning</div>
            </div>
            <div>
              <div className="font-display text-3xl text-white">Zero<span className="text-laap-gold text-xl">-LLM</span></div>
              <div className="text-[11px] uppercase tracking-[0.15em] text-laap-text-tertiary mt-1">Core Loop</div>
            </div>
          </div>

          {/* Lifeform Status Panel */}
          <div className="w-[320px] bg-laap-bg-secondary/80 backdrop-blur-md border border-laap-border rounded-sm p-5 animate-breathe">
            <div className="flex items-center justify-between mb-4">
              <div className="font-mono text-[10px] text-laap-text-tertiary tracking-[0.15em] uppercase">
                Lifeform Status
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-laap-gold animate-pulse-glow" />
                <span className="font-mono text-laap-gold text-[10px] uppercase tracking-wider">Online</span>
              </div>
            </div>

            <div className="font-mono text-[13px] space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-laap-text-tertiary">Frame</span>
                <span className="text-white">#{lifeform.frame.toLocaleString()}</span>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-[12px]">
                  <span className="text-laap-text-tertiary">PSI Cycle</span>
                  <span className="text-laap-cyan uppercase">{getCycleLabel(lifeform.psiCycle)}</span>
                </div>
                <div className="h-[2px] bg-laap-border rounded-full overflow-hidden">
                  <div
                    className="h-full bg-laap-cyan rounded-full transition-all duration-500"
                    style={{ width: `${lifeform.psiCycleProgress * 100}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-x-4 gap-y-2 pt-1">
                <VitalMetric label="Valence" value={lifeform.valence} color="bg-laap-gold" />
                <VitalMetric label="Curiosity" value={lifeform.curiosity} color="bg-laap-emerald" />
                <VitalMetric label="Trust" value={lifeform.trust} color="bg-laap-cyan" />
                <VitalMetric label="Competence" value={lifeform.competence} color="bg-laap-amber" />
                <VitalMetric label="Coherence" value={lifeform.coherence} color="bg-laap-rose" />
                <VitalMetric label="Q-Amplitude" value={lifeform.quantumAmplitude} color="bg-[#a78bfa]" />
              </div>

              <div className="flex justify-between items-center pt-1">
                <span className="text-laap-text-tertiary">Consolidation</span>
                <div className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-laap-gold animate-pulse-glow" />
                  <span className="text-laap-gold text-[11px]">Active</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function VitalMetric({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between text-[11px]">
        <span className="text-laap-text-tertiary">{label}</span>
        <span className="text-white">{value.toFixed(2)}</span>
      </div>
      <div className="h-[2px] bg-laap-border rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${value * 100}%` }}
        />
      </div>
    </div>
  );
}
