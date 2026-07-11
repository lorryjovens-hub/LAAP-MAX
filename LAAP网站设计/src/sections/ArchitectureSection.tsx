import { useEffect, useRef, useState } from 'react';
import { useScrollReveal } from '@/hooks/useScrollReveal';

const LAYERS = [
  { num: '06', title: 'Meta Layer', desc: 'RSI · AEvo · Security Immunology', protocol: '同步协议', width: '70%' },
  { num: '05', title: 'AGI Layer', desc: '11 Cognitive Modules — World, Self, Causal, Analogical, Conscious...', protocol: '交互协议', width: '76%' },
  { num: '04', title: 'Cognition Layer', desc: 'PSI Needs · Emotion · Brain · Meta-Cognition · Parliament', protocol: '记忆协议', width: '82%' },
  { num: '03', title: 'Memory Layer', desc: '5-Level Hierarchy · Consolidation · Forgetting', protocol: '生命协议', width: '88%' },
  { num: '02', title: 'Perception Layer', desc: 'Tools · Senses · Hermes Bridge', protocol: '身份协议', width: '94%' },
  { num: '01', title: 'Infrastructure', desc: 'LLM Provider · Rust Core · Network', protocol: '通信协议', width: '100%' },
];

const STATS = [
  { value: 19850, label: 'Lines of Code' },
  { value: 61, label: 'Source Files' },
  { value: 11, label: 'AGI Modules' },
  { value: 100, label: 'Rust Acceleration', suffix: '×' },
];

function AnimatedNumber({ target, suffix = '' }: { target: number; suffix?: string }) {
  const [display, setDisplay] = useState(0);
  const ref = useRef<HTMLDivElement>(null);
  const hasAnimated = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasAnimated.current) {
            hasAnimated.current = true;
            const duration = 1500;
            const start = performance.now();

            function animate(now: number) {
              const progress = Math.min((now - start) / duration, 1);
              const eased = 1 - Math.pow(1 - progress, 3);
              setDisplay(Math.round(target * eased));
              if (progress < 1) requestAnimationFrame(animate);
            }

            requestAnimationFrame(animate);
          }
        });
      },
      { threshold: 0.5 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [target]);

  return (
    <div ref={ref} className="font-mono text-4xl md:text-5xl text-white font-medium">
      {display.toLocaleString()}{suffix}
    </div>
  );
}

export default function ArchitectureSection() {
  const revealRef = useScrollReveal();
  const [expandedLayer, setExpandedLayer] = useState<number | null>(null);

  return (
    <section id="architecture" className="py-24 px-6" ref={revealRef}>
      <div className="max-w-[1000px] mx-auto">
        {/* Section Title */}
        <div className="text-center mb-16 scroll-reveal">
          <div className="font-mono text-[13px] text-laap-text-tertiary tracking-[0.05em] uppercase mb-3">
            System Architecture
          </div>
          <h2 className="text-2xl sm:text-3xl md:text-[32px] font-medium text-white leading-tight">
            六层六协议——数字生命的完整基础设施
          </h2>
        </div>

        {/* Architecture Stack */}
        <div className="flex flex-col-reverse gap-2 mb-16">
          {LAYERS.map((layer, i) => (
            <div
              key={layer.num}
              className={`scroll-reveal mx-auto transition-all duration-400`}
              style={{
                width: layer.width,
                transitionDelay: `${i * 150}ms`,
              }}
            >
              <button
                onClick={() => setExpandedLayer(expandedLayer === i ? null : i)}
                className="w-full bg-laap-bg-secondary border border-[#27272a] rounded-lg px-6 py-4 flex items-center gap-4 text-left transition-all duration-200 hover:border-[#3f3f46] hover:bg-[#161616]"
              >
                <span className="font-mono text-2xl md:text-3xl text-laap-text-tertiary opacity-50 shrink-0 w-10">
                  {layer.num}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="text-lg md:text-xl font-medium text-white">{layer.title}</span>
                    <span className="text-[11px] font-mono text-laap-cyan/70 border border-laap-cyan/20 px-2 py-0.5 rounded">
                      {layer.protocol}
                    </span>
                  </div>
                  <p className="text-[13px] text-laap-text-secondary mt-1 truncate">{layer.desc}</p>
                </div>
              </button>

              {expandedLayer === i && (
                <div className="mt-2 ml-14 p-4 bg-laap-bg-code border border-[#27272a] rounded-lg animate-in fade-in slide-in-from-top-1 duration-200">
                  <p className="text-[13px] text-laap-text-secondary leading-relaxed">
                    {layer.desc} — 该层通过 {layer.protocol} 与其他层通信，确保 LAAP 生命体的每一层都能协调运作。
                  </p>
                </div>
              )}

              {i < LAYERS.length - 1 && (
                <div className="flex justify-center py-1">
                  <svg width="16" height="12" viewBox="0 0 16 12" fill="none" className="text-[#27272a]">
                    <path d="M8 12L1 2h14L8 12z" fill="currentColor" opacity="0.5" />
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 scroll-reveal">
          {STATS.map((stat, i) => (
            <div
              key={stat.label}
              className={`scroll-reveal scroll-reveal-delay-${i + 1} bg-laap-bg-secondary border border-[#27272a] rounded-xl p-8 text-center transition-all duration-300 hover:border-[#3f3f46] hover:bg-[#161616]`}
            >
              <AnimatedNumber target={stat.value} suffix={stat.suffix} />
              <div className="text-[13px] text-laap-text-tertiary mt-2">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
