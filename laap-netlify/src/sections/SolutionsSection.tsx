import { useScrollReveal } from '@/hooks/useScrollReveal';
import { ShieldAlert, BrainCircuit, Network, MemoryStick, Coins, CheckCircle2, XCircle } from 'lucide-react';

const PAIN_POINTS = [
  {
    icon: ShieldAlert,
    title: 'Agent 泛滥与治理真空',
    stat: '最大瓶颈',
    description:
      '企业同时运行数十到数百个 Agent，跨语言、跨框架、跨协议。数据泄露、权限失控、合规难适配、人工接管缺失——安全与治理成为规模化落地的最大瓶颈。',
    accent: 'rose',
  },
  {
    icon: BrainCircuit,
    title: '幻觉与不可信输出',
    stat: '不敢用',
    description:
      'LLM 输出天然概率性，金融、政务、医疗场景一次幻觉的代价可能超过全部效率收益。现有框架缺乏原生的事实锚定与因果验证机制。',
    accent: 'amber',
  },
  {
    icon: Network,
    title: '多 Agent 协作失控',
    stat: '93+ Agent',
    description:
      '当 93 个 Agent 同时运行时，状态合并、故障恢复、死循环检测、Token 成本控制全部失守。缺少统一认知总线与断点恢复能力。',
    accent: 'cyan',
  },
  {
    icon: MemoryStick,
    title: '会话级记忆断裂',
    stat: '知识蒸发',
    description:
      '企业期望 AI 越用越懂业务，但主流框架每轮会话从零开始，知识资产随对话关闭而蒸发，无法沉淀为组织级数字资产。',
    accent: 'emerald',
  },
  {
    icon: Coins,
    title: 'Token 成本失控',
    stat: 'ROI 告急',
    description:
      '长对话、多轮检索、重复生成吞噬预算，CFO 要求每一笔 Token 支出都能算得出产出，传统 Agent 架构的单位经济模型难以为继。',
    accent: 'gold',
  },
];

const ADVANTAGES = [
  {
    title: '治理内建，而非外挂',
    points: [
      '不可变 SHA-256 哈希注册表',
      '文件系统写白名单与 KL 散度漂移监控',
      '审计迹、权限矩阵、紧急中止三级权力',
    ],
    highlight: '让 AI 从“黑箱”变成“可审计、可干预”的治理对象',
  },
  {
    title: '三层记忆，知识资产化',
    points: [
      '工作 / 近期 / 核心三层记忆 + 情景检索',
      '跨平台 Ψ-Net 同步，手机 / 桌面 / 云端一致',
      '记忆检索 O(1)，与语料规模无关',
    ],
    highlight: 'AI 越用越懂业务，从一次性工具变成持续增值的资产',
  },
  {
    title: '因果验证，拦截幻觉',
    points: [
      'PSI 因果验证抽取输出中的因果断言',
      'Truth Grounding Engine 锚定可验证事实源',
      '议会审议系统多角色交叉校验',
    ],
    highlight: '在高风险场景下也能放心交付结果',
  },
  {
    title: '成本引擎，算得出 ROI',
    points: [
      'CLP 组件链接协议：匹配型负载节省 98.2% Token',
      'MeMo 记忆即模型：小模型记忆化，执行模型冻结',
      '零 Token 视觉复制：sub-500ms、0 LLM 成本',
    ],
    highlight: '用真实数据向 CFO 证明 AI 投入回报',
  },
];

const METRICS = [
  { value: '98.2%', label: '匹配型负载 Token 节省' },
  { value: '57×', label: '组件检索提速' },
  { value: '-27.22%', label: '整体 Token 消耗降低' },
  { value: '+66%', label: '任务质量提升' },
];

const COMPETITORS = [
  { name: 'LangChain / LangGraph', features: [false, false, false, false] },
  { name: 'CrewAI', features: [false, false, false, false] },
  { name: 'Dify / Coze', features: [false, false, false, false] },
  { name: 'LAAP', features: [true, true, true, true], isLaap: true },
];

const COMPARE_FEATURES = ['原生治理层', '三层持续记忆', '因果幻觉验证', '成本优化引擎'];

const ACCENT_STYLES: Record<string, { bg: string; text: string; border: string; glow: string }> = {
  rose: {
    bg: 'bg-rose-500/10',
    text: 'text-laap-rose',
    border: 'border-laap-rose/30',
    glow: 'shadow-[0_0_30px_-6px_rgba(244,63,94,0.25)]',
  },
  amber: {
    bg: 'bg-amber-500/10',
    text: 'text-laap-amber',
    border: 'border-laap-amber/30',
    glow: 'shadow-[0_0_30px_-6px_rgba(245,158,11,0.25)]',
  },
  cyan: {
    bg: 'bg-cyan-500/10',
    text: 'text-laap-cyan',
    border: 'border-laap-cyan/30',
    glow: 'shadow-[0_0_30px_-6px_rgba(34,211,238,0.25)]',
  },
  emerald: {
    bg: 'bg-emerald-500/10',
    text: 'text-laap-emerald',
    border: 'border-laap-emerald/30',
    glow: 'shadow-[0_0_30px_-6px_rgba(16,185,129,0.25)]',
  },
  gold: {
    bg: 'bg-[rgba(201,168,108,0.1)]',
    text: 'text-laap-gold',
    border: 'border-laap-gold/30',
    glow: 'shadow-[0_0_30px_-6px_rgba(201,168,108,0.25)]',
  },
};

export default function SolutionsSection() {
  const revealRef = useScrollReveal();

  return (
    <section id="solutions" className="relative py-28 px-6 overflow-hidden" ref={revealRef}>
      {/* Atmospheric background */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-b from-laap-bg-primary via-laap-bg-tertiary/30 to-laap-bg-primary" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1200px] h-[600px] bg-[radial-gradient(ellipse_at_top,rgba(201,168,108,0.08),transparent_60%)]" />
        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage:
              'linear-gradient(rgba(255,255,255,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.06) 1px, transparent 1px)',
            backgroundSize: '64px 64px',
          }}
        />
      </div>

      <div className="relative z-10 max-w-[1200px] mx-auto">
        {/* Section header */}
        <div className="text-center mb-20 scroll-reveal">
          <div className="font-mono text-[13px] text-laap-text-tertiary tracking-[0.05em] uppercase mb-3">
            Problems & Advantages
          </div>
          <h2 className="text-2xl sm:text-3xl md:text-[34px] font-medium text-white max-w-[720px] mx-auto leading-tight">
            企业 AI 规模化落地的五大瓶颈，LAAP 用范式升级回答
          </h2>
          <p className="mt-5 text-[15px] text-laap-text-secondary max-w-[640px] mx-auto leading-relaxed">
            主流框架诞生于「让 Agent 跑起来」的时代；LAAP 诞生于「让 Agent 活下来、值得信任、越用越聪明」的需求。
          </p>
        </div>

        {/* Pain points grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-24">
          {PAIN_POINTS.map((pain, i) => {
            const Icon = pain.icon;
            const accent = ACCENT_STYLES[pain.accent];
            return (
              <div
                key={pain.title}
                className={`scroll-reveal scroll-reveal-delay-${i + 1} group relative bg-laap-bg-secondary border border-[#27272a] rounded-xl p-7 transition-all duration-300 hover:border-[#3f3f46] hover:bg-[#111111] hover:-translate-y-0.5 ${accent.glow}`}
              >
                <div
                  className={`absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-${pain.accent === 'gold' ? 'laap-gold' : pain.accent + '-500'} to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500`}
                />
                <div className="flex items-start justify-between mb-5">
                  <div className={`w-11 h-11 rounded-lg flex items-center justify-center ${accent.bg} ${accent.text}`}>
                    <Icon size={22} strokeWidth={1.8} />
                  </div>
                  <span className="font-mono text-[11px] text-laap-text-tertiary border border-[#27272a] px-2 py-0.5 rounded">
                    {pain.stat}
                  </span>
                </div>
                <h3 className="text-lg font-medium text-white mb-2">{pain.title}</h3>
                <p className="text-[14px] text-laap-text-secondary leading-relaxed">{pain.description}</p>
              </div>
            );
          })}
        </div>

        {/* Metrics band */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-24 scroll-reveal">
          {METRICS.map((metric, i) => (
            <div
              key={metric.label}
              className={`scroll-reveal scroll-reveal-delay-${i + 1} bg-laap-bg-secondary border border-[#27272a] rounded-xl p-7 text-center transition-all duration-300 hover:border-laap-gold/40 hover:bg-[#111111]`}
            >
              <div className="font-display text-3xl md:text-4xl text-laap-gold mb-2">{metric.value}</div>
              <div className="text-[13px] text-laap-text-secondary">{metric.label}</div>
            </div>
          ))}
        </div>

        {/* Advantages + comparison */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 mb-24">
          {/* Advantages */}
          <div className="scroll-reveal space-y-5">
            <div className="mb-8">
              <div className="font-mono text-[13px] text-laap-text-tertiary tracking-[0.05em] uppercase mb-2">
                Why LAAP
              </div>
              <h3 className="text-2xl md:text-[28px] font-medium text-white leading-tight">
                卖的不是编排，是「信任 + 记忆 + 经济性」
              </h3>
            </div>
            {ADVANTAGES.map((adv, i) => (
              <div
                key={adv.title}
                className={`scroll-reveal scroll-reveal-delay-${i + 1} bg-laap-bg-secondary/60 border border-[#27272a] rounded-xl p-6 transition-all duration-300 hover:border-[#3f3f46] hover:bg-laap-bg-secondary`}
              >
                <h4 className="text-lg font-medium text-white mb-3 flex items-center gap-2">
                  <CheckCircle2 size={18} className="text-laap-gold" />
                  {adv.title}
                </h4>
                <ul className="space-y-2 mb-3">
                  {adv.points.map((point) => (
                    <li key={point} className="text-[14px] text-laap-text-secondary flex items-start gap-2">
                      <span className="w-1 h-1 rounded-full bg-laap-gold mt-2 shrink-0" />
                      {point}
                    </li>
                  ))}
                </ul>
                <p className="text-[13px] text-laap-gold/90 border-t border-[#27272a] pt-3 leading-relaxed">
                  {adv.highlight}
                </p>
              </div>
            ))}
          </div>

          {/* Comparison table */}
          <div className="scroll-reveal scroll-reveal-delay-2">
            <div className="mb-8">
              <div className="font-mono text-[13px] text-laap-text-tertiary tracking-[0.05em] uppercase mb-2">
                Competitive Comparison
              </div>
              <h3 className="text-2xl md:text-[28px] font-medium text-white leading-tight">
                这不是功能差距，是范式差距
              </h3>
            </div>
            <div className="bg-laap-bg-secondary border border-[#27272a] rounded-xl overflow-hidden">
              <div className="grid grid-cols-[1fr_repeat(4,60px)] gap-2 px-5 py-4 border-b border-[#27272a] text-[11px] font-mono text-laap-text-tertiary uppercase tracking-wider">
                <div>Framework</div>
                {COMPARE_FEATURES.map((f) => (
                  <div key={f} className="text-center leading-tight">
                    {f}
                  </div>
                ))}
              </div>
              {COMPETITORS.map((comp) => (
                <div
                  key={comp.name}
                  className={`grid grid-cols-[1fr_repeat(4,60px)] gap-2 px-5 py-4 border-b border-[#27272a] last:border-b-0 items-center ${
                    comp.isLaap ? 'bg-laap-gold/5' : ''
                  }`}
                >
                  <div className={`text-[14px] ${comp.isLaap ? 'text-laap-gold font-medium' : 'text-white'}`}>
                    {comp.name}
                  </div>
                  {comp.features.map((ok, idx) => (
                    <div key={idx} className="flex justify-center">
                      {ok ? (
                        <CheckCircle2 size={18} className="text-laap-emerald" />
                      ) : (
                        <XCircle size={18} className="text-laap-rose/60" />
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </div>
            <p className="mt-4 text-[13px] text-laap-text-secondary leading-relaxed">
              LAAP 的差异化来自架构假设的根本不同：持续存在的自我、原生治理层、模型无关与私有化优先。
              竞品无法通过简单加功能追赶。
            </p>
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="scroll-reveal text-center bg-gradient-to-r from-laap-gold/10 via-laap-gold/5 to-laap-gold/10 border border-laap-gold/20 rounded-2xl p-10 md:p-14">
          <h3 className="text-2xl md:text-3xl font-medium text-white mb-4">
            让 AI 从“能跑 Demo”进化到“值得托付”
          </h3>
          <p className="text-[15px] text-laap-text-secondary max-w-[600px] mx-auto mb-8 leading-relaxed">
            面向金融、政务、制造、企业服务四大垂直行业，LAAP Enterprise 提供私有化部署、治理合规与持续认知能力，
            帮助企业在 Agentic AI 时代建立可信的数字员工体系。
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              href="/studio"
              className="px-8 py-3 text-[14px] font-medium text-laap-bg-primary bg-laap-gold rounded-sm transition-all duration-200 hover:bg-laap-gold-light"
            >
              进入 Studio 体验
            </a>
            <a
              href="/docs"
              className="px-8 py-3 text-[14px] font-medium text-white border border-laap-border rounded-sm transition-all duration-200 hover:border-laap-gold hover:text-laap-gold"
            >
              阅读技术白皮书
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
