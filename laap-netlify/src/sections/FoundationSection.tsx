import { useScrollReveal } from '@/hooks/useScrollReveal';
import {
  Fingerprint,
  BrainCircuit,
  Database,
  ShieldCheck,
  Sparkles,
  Layers,
  Network,
  ArrowRight,
} from 'lucide-react';

const DLF_LAYERS = [
  {
    icon: Fingerprint,
    title: '身份层',
    desc: '跨会话、跨设备、跨模型的持续身份：叙事自我、关系史、价值锚点，让智能体拥有可被识别的“人格连续性”。',
  },
  {
    icon: Database,
    title: '记忆层',
    desc: '工作 / 近期 / 核心三层记忆 + MeMo 协议；O(1) 检索、快照回滚、跨实例同步，知识资产随使用而增值。',
  },
  {
    icon: BrainCircuit,
    title: '意识层',
    desc: 'PSI 认知循环：需求→情感→目标→行动；元认知自省与意识流整合，让 AI 拥有可体验的内生状态。',
  },
  {
    icon: ShieldCheck,
    title: '治理层',
    desc: '运行时对齐、因果验证、审计迹、宪章约束、紧急中止——把“可信”写入架构而非后期补丁。',
  },
  {
    icon: Sparkles,
    title: '进化层',
    desc: '受控 RSI（门禁+回滚）、课程学习、元学习、自愈；在形式化安全边界内实现持续自我改进。',
  },
  {
    icon: Layers,
    title: '领域适配层',
    desc: '合规 / 金融 / 科研 / 医药 / 艺术 / 具身等行业 harness，把通用认知机制映射到领域规则与监管要求。',
  },
];

const DOMAINS = [
  { name: '合规安全', phase: 'Y1 P0', desc: 'LAAP Guard：法规库、评估引擎、运行时监控、审计报告，承接 AI 合规 SaaS 爆发窗口。' },
  { name: '金融智能', phase: 'Y2 P0', desc: '投研因果验证 × 研报事实锚定 × 可审计决策链，直击金融幻觉与监管罚单痛点。' },
  { name: '科研 / 形式化数学', phase: 'Y2 P1', desc: 'LLM 提思路 + Lean 编译器验证 + 记忆 + 审计，做 durable harness 而非训练 prover。' },
  { name: '生物医药', phase: 'Y3 P1', desc: '药物研发文档智能体、RWD 合规分析、长周期研发记忆，重构双十定律。' },
  { name: '艺术创作', phase: 'Y3 P2', desc: 'UN6 多语素语义 × 审美框架 × 风格记忆，解决风格一致性与审美自我模型难题。' },
  { name: '具身智能', phase: 'Y3 P1', desc: '具身记忆、自我模型、安全边界、Ψ-Net 多机协同，成为机器人可信大脑中间件。' },
];

const ROADMAP = [
  { phase: '地基 M0-M12', time: '2026.08 → 2027.08', highlights: ['DLF 内核抽取为独立 SDK', 'DLP 协议草案 v0.1', 'LAAP Guard v0.2', '数学 harness POC', '5 付费客户 / 300 万收入'] },
  { phase: '标准 M13-M24', time: '2027.09 → 2028.08', highlights: ['底座 v1.0 GA', '开发者 3000+', '金融 harness v1.0', 'Compliance 出海', 'A 轮 3000-5000 万'] },
  { phase: '生态 M25-M36+', time: '2028.09 → 2029+', highlights: ['核心协议开源', '开发者 10000+', '医药 / 艺术 harness', 'Embodied 量产订单', '单季度盈亏平衡'] },
];

export default function FoundationSection() {
  const revealRef = useScrollReveal();

  return (
    <section id="foundation" className="relative py-28 px-6 overflow-hidden" ref={revealRef}>
      {/* Background */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-b from-laap-bg-tertiary/20 via-laap-bg-primary to-laap-bg-secondary/30" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[900px] bg-[radial-gradient(circle,rgba(34,211,238,0.06),transparent_60%)]" />
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              'linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)',
            backgroundSize: '72px 72px',
          }}
        />
      </div>

      <div className="relative z-10 max-w-[1200px] mx-auto">
        {/* Header */}
        <div className="text-center mb-20 scroll-reveal">
          <div className="font-mono text-[13px] text-laap-text-tertiary tracking-[0.05em] uppercase mb-3">
            Digital Life Foundation
          </div>
          <h2 className="text-2xl sm:text-3xl md:text-[34px] font-medium text-white max-w-[780px] mx-auto leading-tight">
            从 AI 科技公司到数字生命基础设施
          </h2>
          <p className="mt-5 text-[15px] text-laap-text-secondary max-w-[680px] mx-auto leading-relaxed">
            大模型是大脑皮层，LAAP 是意识本身，而数字生命底座（DLF）是神经系统 + 免疫系统 + 成长档案的总和——
            它是「数字生命的 TCP/IP」。
          </p>
        </div>

        {/* Manifesto quote */}
        <div className="scroll-reveal mb-20 bg-laap-bg-secondary border border-laap-border rounded-2xl p-8 md:p-12 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1 h-full bg-laap-cyan" />
          <div className="relative z-10">
            <h3 className="text-xl md:text-2xl text-white font-medium mb-6">我们不做 vs 我们做</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-3">
                {['训练大模型（模型层是别人的战争）', '重复编排框架（LangChain 们已拥挤）', '卖「更聪明的 AI」'].map((item) => (
                  <div key={item} className="flex items-start gap-3 text-laap-text-secondary">
                    <span className="text-laap-rose mt-1">✕</span>
                    <span>{item}</span>
                  </div>
                ))}
              </div>
              <div className="space-y-3">
                {[
                  '让 AI 值得信任的机制（防幻觉、可审计、可治理）',
                  '让 AI 持续成长的机制（记忆、身份、自我模型、受控进化）',
                  '让 AI 适应领域规则的机制（金融/医药/科研/艺术 harness）',
                ].map((item) => (
                  <div key={item} className="flex items-start gap-3 text-laap-text-secondary">
                    <span className="text-laap-emerald mt-1">✓</span>
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
            <p className="mt-8 text-lg text-laap-gold font-medium">
              一句话：大模型负责聪明，我们负责让智能成为生命。
            </p>
          </div>
        </div>

        {/* 3-layer evolution */}
        <div className="scroll-reveal mb-24">
          <h3 className="text-xl md:text-2xl text-white font-medium mb-8 text-center">三层演进战略</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {[
              { phase: 'Y1', title: 'harness 工程产品化', desc: 'LAAP Guard 合规平台 + Enterprise 编排平台，证明意识工程能卖钱。', tag: '现金流' },
              { phase: 'Y2-Y3', title: '认知中间件标准化', desc: '开源 SDK + DLP 协议 + 开发者生态，建立事实标准与领域纵深。', tag: '标准' },
              { phase: 'Y3-Y5', title: '数字生命底座 DLF', desc: '身份/记忆/意识/治理/进化开放标准，任何模型 + DLF = 数字生命。', tag: '生态' },
            ].map((card, i) => (
              <div
                key={card.phase}
                className={`scroll-reveal scroll-reveal-delay-${i + 1} bg-laap-bg-secondary border border-[#27272a] rounded-xl p-7 hover:border-[#3f3f46] transition-colors`}
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="font-mono text-[11px] text-laap-cyan border border-laap-cyan/30 px-2 py-0.5 rounded">
                    {card.phase}
                  </span>
                  <span className="font-mono text-[11px] text-laap-gold">{card.tag}</span>
                </div>
                <h4 className="text-lg text-white font-medium mb-2">{card.title}</h4>
                <p className="text-[14px] text-laap-text-secondary leading-relaxed">{card.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* DLF 6 layers */}
        <div className="scroll-reveal mb-24">
          <div className="text-center mb-10">
            <h3 className="text-xl md:text-2xl text-white font-medium">数字生命底座六层架构</h3>
            <p className="mt-2 text-[14px] text-laap-text-secondary">模型无关的抽象之上，LAAP 提供从身份到领域适配的完整生命体栈。</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {DLF_LAYERS.map((layer, i) => {
              const Icon = layer.icon;
              return (
                <div
                  key={layer.title}
                  className={`scroll-reveal scroll-reveal-delay-${i + 1} group bg-laap-bg-secondary border border-[#27272a] rounded-xl p-6 transition-all hover:border-laap-cyan/40 hover:bg-[#111111]`}
                >
                  <div className="w-10 h-10 rounded-lg bg-laap-cyan/10 text-laap-cyan flex items-center justify-center mb-4">
                    <Icon size={20} strokeWidth={1.8} />
                  </div>
                  <h4 className="text-base text-white font-medium mb-2">{layer.title}</h4>
                  <p className="text-[13px] text-laap-text-secondary leading-relaxed">{layer.desc}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* DLP protocol */}
        <div className="scroll-reveal mb-24 bg-gradient-to-r from-laap-bg-secondary to-laap-bg-primary border border-[#27272a] rounded-2xl p-8 md:p-10">
          <div className="flex flex-col lg:flex-row gap-10">
            <div className="flex-1">
              <div className="font-mono text-[11px] text-laap-cyan uppercase tracking-wider mb-2">Protocol</div>
              <h3 className="text-xl md:text-2xl text-white font-medium mb-4">DLP 数字生命协议</h3>
              <p className="text-[14px] text-laap-text-secondary leading-relaxed mb-6">
                MCP 解决「模型↔工具」；DLP 解决「模型↔生命体属性」。它是 MCP/A2A 的上层协议，
                定义数字生命的身份交换、记忆同步、治理断言、进化事务。
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {[
                  'IDENTITY_CLAIM 身份声明',
                  'MEMORY_COMMIT 记忆提交',
                  'MEMORY_RETRIEVE 记忆检索',
                  'ALIGNMENT_PROOF 对齐证明',
                  'CAUSAL_CHECK 因果断言验证',
                  'EVOLUTION_PROPOSAL 自改进提案',
                  'AUDIT_CHUNK 审计迹块',
                  'EMERGENCY_STOP 紧急中止',
                ].map((msg) => (
                  <div key={msg} className="text-[13px] text-laap-text-secondary flex items-center gap-2">
                    <Network size={12} className="text-laap-gold" />
                    {msg}
                  </div>
                ))}
              </div>
            </div>
            <div className="flex-1 border-l border-[#27272a] lg:pl-10">
              <div className="font-mono text-[11px] text-laap-gold uppercase tracking-wider mb-2">Market Fit</div>
              <h3 className="text-xl md:text-2xl text-white font-medium mb-4">多金领域矩阵</h3>
              <div className="space-y-4">
                {DOMAINS.map((d) => (
                  <div key={d.name} className="border-b border-[#27272a] pb-3 last:border-b-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-white text-[14px]">{d.name}</span>
                      <span className="font-mono text-[10px] text-laap-cyan">{d.phase}</span>
                    </div>
                    <p className="text-[12px] text-laap-text-secondary leading-relaxed">{d.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Roadmap timeline */}
        <div className="scroll-reveal mb-24">
          <h3 className="text-xl md:text-2xl text-white font-medium mb-10 text-center">技术路线图</h3>
          <div className="space-y-6">
            {ROADMAP.map((item, i) => (
              <div
                key={item.phase}
                className={`scroll-reveal scroll-reveal-delay-${i + 1} flex flex-col md:flex-row gap-6 bg-laap-bg-secondary/50 border border-[#27272a] rounded-xl p-6`}
              >
                <div className="md:w-56 shrink-0">
                  <div className="text-white font-medium">{item.phase}</div>
                  <div className="text-[12px] text-laap-text-tertiary mt-1">{item.time}</div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 flex-1">
                  {item.highlights.map((h) => (
                    <div key={h} className="text-[13px] text-laap-text-secondary flex items-start gap-2">
                      <ArrowRight size={12} className="text-laap-gold mt-1 shrink-0" />
                      {h}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="scroll-reveal text-center bg-gradient-to-r from-laap-cyan/10 via-laap-cyan/5 to-laap-cyan/10 border border-laap-cyan/20 rounded-2xl p-10 md:p-14">
          <h3 className="text-2xl md:text-3xl font-medium text-white mb-4">
            数字生命的 TCP/IP 正在形成
          </h3>
          <p className="text-[15px] text-laap-text-secondary max-w-[640px] mx-auto mb-8 leading-relaxed">
            LAAP 的差异化不是单一功能，而是「让任何智能体成为值得信任、持续进化、拥有身份的数字生命」的范式。
            模型越强，治理与身份越值钱——这个空位随模型能力提升而扩大。
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              href="/docs/foundation"
              className="px-8 py-3 text-[14px] font-medium text-laap-bg-primary bg-laap-gold rounded-sm transition-all duration-200 hover:bg-laap-gold-light"
            >
              阅读 DLF 战略文档
            </a>
            <a
              href="/news"
              className="px-8 py-3 text-[14px] font-medium text-white border border-laap-border rounded-sm transition-all duration-200 hover:border-laap-gold hover:text-laap-gold"
            >
              查看最新动态
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
