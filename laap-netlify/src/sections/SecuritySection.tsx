import { useScrollReveal } from '@/hooks/useScrollReveal';

const SECURITY_LAYERS = [
  { num: 1, name: '先天威胁检测', accent: 'rose' as const },
  { num: 2, name: '适应性策略执行', accent: 'amber' as const },
  { num: 3, name: '审计日志', accent: 'cyan' as const },
  { num: 4, name: '隔离层', accent: 'emerald' as const },
  { num: 5, name: '加密身份 (DID)', accent: 'cyan' as const },
];

const ACCENT_BORDER: Record<string, string> = {
  rose: 'border-laap-rose/30',
  amber: 'border-laap-amber/30',
  cyan: 'border-laap-cyan/30',
  emerald: 'border-laap-emerald/30',
};

const ACCENT_TEXT: Record<string, string> = {
  rose: 'text-laap-rose',
  amber: 'text-laap-amber',
  cyan: 'text-laap-cyan',
  emerald: 'text-laap-emerald',
};

export default function SecuritySection() {
  const revealRef = useScrollReveal();

  return (
    <section id="security" className="py-24 px-6" ref={revealRef}>
      <div className="max-w-[800px] mx-auto text-center">
        {/* Section Title */}
        <div className="mb-12 scroll-reveal">
          <div className="font-mono text-[13px] text-laap-text-tertiary tracking-[0.05em] uppercase mb-3">
            Security &amp; Trust
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-medium text-white mb-6">
            进化需要边界
          </h2>
          <p className="text-base text-laap-text-secondary max-w-[560px] mx-auto leading-relaxed">
            五层安全免疫系统确保这个生命体的成长始终在安全的轨道上。它不会遗忘核心伦理，不会自我毁灭，不会泄露你的秘密。
          </p>
        </div>

        {/* Security Layers */}
        <div className="flex flex-col gap-3 max-w-[480px] mx-auto scroll-reveal scroll-reveal-delay-1">
          {SECURITY_LAYERS.map((layer, i) => (
            <div
              key={layer.num}
              className={`scroll-reveal scroll-reveal-delay-${i + 1} flex items-center gap-4 bg-laap-bg-secondary border ${ACCENT_BORDER[layer.accent]} rounded-lg px-6 py-4 text-left`}
            >
              <span
                className={`w-6 h-6 rounded-full border ${ACCENT_BORDER[layer.accent]} flex items-center justify-center text-[11px] font-mono ${ACCENT_TEXT[layer.accent]} shrink-0`}
              >
                {layer.num}
              </span>
              <span className="text-[15px] text-white">{layer.name}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
