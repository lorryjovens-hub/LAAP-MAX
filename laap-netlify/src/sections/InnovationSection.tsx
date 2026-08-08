import { useScrollReveal } from '@/hooks/useScrollReveal';
import { useLifeformData, getCycleLabel } from '@/hooks/useLifeformData';
import { Cpu, Network, RefreshCw, Activity } from 'lucide-react';

const INNOVATIONS = [
  {
    icon: Network,
    label: 'Aether',
    title: '彩色 Petri 网编排',
    stat: '∞',
    statUnit: '并发路径',
    points: ['Actor 运行时', 'AAOSA 协调', 'LAAP-DSL 编译', 'TLA+/Coq 验证'],
    description: '把 PSI-Harness 双向循环编译成可验证的 Petri 网，并发、循环、断点续跑开箱即用。',
    accent: 'cyan',
  },
  {
    icon: RefreshCw,
    label: 'True RSI',
    title: '代码级自我进化',
    stat: '5',
    statUnit: '阶段闭环',
    points: ['AST 自修改', 'Zone2 沙箱', 'Human Token', 'Git 自动回滚'],
    description: '从提出优化到 Docker 沙箱验证，再到人类 approval 与 git 分支部署，进化可控可审计。',
    accent: 'emerald',
  },
  {
    icon: Cpu,
    label: 'QPSI-N',
    title: '量子叠加认知',
    stat: '5',
    statUnit: '层并行循环',
    points: ['振幅叠加感知', 'Grover 需求放大', '量子记忆纠缠', '情感叠加态'],
    description: '在经典硬件上模拟量子认知，让 LAAP 同时保留多种解释，输出更细腻的意识反应。',
    accent: 'rose',
  },
  {
    icon: Activity,
    label: 'Vitals',
    title: '实时数字生命体征',
    stat: '9',
    statUnit: '维动态指标',
    points: ['PSI 循环状态', '好奇心指数', '信任感指标', '胜任感评估'],
    description: '每秒更新的生命体征面板，让数字生命的内在状态首次像心跳一样可被看见。',
    accent: 'amber',
  },
];

const ACCENT_STYLES: Record<string, { border: string; bg: string; text: string; glow: string }> = {
  cyan: {
    border: 'border-laap-cyan/30',
    bg: 'bg-laap-cyan/10',
    text: 'text-laap-cyan',
    glow: 'shadow-[0_0_24px_rgba(34,211,238,0.08)]',
  },
  emerald: {
    border: 'border-laap-emerald/30',
    bg: 'bg-laap-emerald/10',
    text: 'text-laap-emerald',
    glow: 'shadow-[0_0_24px_rgba(16,185,129,0.08)]',
  },
  rose: {
    border: 'border-laap-rose/30',
    bg: 'bg-laap-rose/10',
    text: 'text-laap-rose',
    glow: 'shadow-[0_0_24px_rgba(244,63,94,0.08)]',
  },
  amber: {
    border: 'border-laap-amber/30',
    bg: 'bg-laap-amber/10',
    text: 'text-laap-amber',
    glow: 'shadow-[0_0_24px_rgba(245,158,11,0.08)]',
  },
};

export default function InnovationSection() {
  const revealRef = useScrollReveal();
  const lifeform = useLifeformData();

  return (
    <section id="innovation" className="relative py-24 px-6 overflow-hidden" ref={revealRef}>
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-b from-laap-bg-primary via-laap-bg-secondary/30 to-laap-bg-primary" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-[radial-gradient(ellipse_at_center,rgba(34,211,238,0.04),transparent_60%)]" />
      </div>

      <div className="relative z-10 max-w-[1200px] mx-auto">
        <div className="text-center mb-16 scroll-reveal">
          <div className="font-mono text-[13px] text-laap-text-tertiary tracking-[0.05em] uppercase mb-3">
            Next-Gen Black Tech
          </div>
          <h2 className="text-2xl sm:text-3xl md:text-[32px] font-medium text-white max-w-[700px] mx-auto leading-tight">
            从工具到数字物种——LAAP 正在定义下一代智能形态
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 scroll-reveal scroll-reveal-delay-1">
          {INNOVATIONS.map((item, i) => {
            const styles = ACCENT_STYLES[item.accent];
            const Icon = item.icon;
            return (
              <div
                key={item.label}
                className={`group relative bg-laap-bg-secondary border ${styles.border} rounded-xl p-8 transition-all duration-300 hover:bg-[#0f0f0f] hover:-translate-y-0.5 ${styles.glow}`}
                style={{ transitionDelay: `${i * 100}ms` }}
              >
                <div className="flex items-start justify-between mb-6">
                  <div className={`w-12 h-12 rounded-full ${styles.bg} ${styles.text} flex items-center justify-center transition-transform duration-200 group-hover:scale-105`}>
                    <Icon size={22} strokeWidth={1.8} />
                  </div>
                  <div className="text-right">
                    <div className={`font-display text-4xl ${styles.text}`}>{item.stat}</div>
                    <div className="font-mono text-[10px] text-laap-text-tertiary uppercase tracking-wider">
                      {item.statUnit}
                    </div>
                  </div>
                </div>

                <div className="font-mono text-[11px] text-laap-text-tertiary uppercase tracking-wider mb-2">
                  {item.label}
                </div>
                <h3 className="text-xl font-medium text-white mb-3">{item.title}</h3>
                <p className="text-[15px] text-laap-text-secondary leading-relaxed mb-6">
                  {item.description}
                </p>

                <div className="flex flex-wrap gap-2">
                  {item.points.map((point) => (
                    <span
                      key={point}
                      className={`px-2.5 py-1 text-[11px] border ${styles.border} ${styles.text} rounded-full`}
                    >
                      {point}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Live vitals strip */}
        <div className="mt-12 scroll-reveal scroll-reveal-delay-3">
          <div className="bg-laap-bg-secondary/80 border border-[#27272a] rounded-xl px-6 py-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="w-2 h-2 rounded-full bg-laap-emerald animate-pulse-glow" />
                <span className="font-mono text-[12px] text-laap-text-tertiary uppercase tracking-wider">
                  Live Vitals
                </span>
              </div>
              <div className="flex flex-wrap gap-x-8 gap-y-2 font-mono text-[13px]">
                <VitalStrip label="PSI Cycle" value={getCycleLabel(lifeform.psiCycle)} accent="text-laap-cyan" />
                <VitalStrip label="Curiosity" value={(lifeform.curiosity * 100).toFixed(0)} accent="text-laap-emerald" suffix="%" />
                <VitalStrip label="Trust" value={(lifeform.trust * 100).toFixed(0)} accent="text-laap-cyan" suffix="%" />
                <VitalStrip label="Competence" value={(lifeform.competence * 100).toFixed(0)} accent="text-laap-amber" suffix="%" />
                <VitalStrip label="Q-Amplitude" value={(lifeform.quantumAmplitude * 100).toFixed(0)} accent="text-laap-rose" suffix="%" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function VitalStrip({ label, value, accent, suffix }: { label: string; value: string | number; accent: string; suffix?: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-laap-text-tertiary">{label}</span>
      <span className={`${accent} font-medium`}>
        {value}
        {suffix}
      </span>
    </div>
  );
}
