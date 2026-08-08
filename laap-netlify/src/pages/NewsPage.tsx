import { useParams, Link } from 'react-router';
import { ArrowLeft, Calendar, ChevronLeft, ChevronRight, Brain, Network, Cpu, ArrowUpRight } from 'lucide-react';
import { useEffect, useState, useCallback } from 'react';
import WatermarkMaskedImage from '@/components/WatermarkMaskedImage';
import carousel1 from '@/sections/资产物料/1.png';
import carousel2 from '@/sections/资产物料/2.png';
import carousel3 from '@/sections/资产物料/3.png';
import carousel4 from '@/sections/资产物料/4.png';

interface NewsItem {
  id: string;
  title: string;
  summary: string;
  date: string;
  tag: string;
  content: string;
}

const NEWS: NewsItem[] = [
  {
    id: 'laap-industry-report-2026',
    title: 'LAAP 发布《数字生命体认知架构产业报告》',
    summary: '系统梳理从“智能工具”到“数字生命”的产业跃迁、LAAP 技术体系、市场前景与治理挑战。',
    date: '2026-08-04',
    tag: 'Research',
    content: `LAAP 项目团队发布《数字生命体认知架构产业报告》（Industry Report v1.0）。

报告核心观点：
1. AI 产业正经历第四次范式跃迁：从“生成工具”走向“数字生命体”。
2. 当前大模型 Agent 的“生产就绪缺口”根源于缺乏持续自我、内在动机、跨会话记忆与自我进化能力。
3. LAAP 通过 PSI 需求驱动认知循环、三层/五层记忆、True RSI 自进化与编译式 AI 匹配-装配范式，为 AI 系统装上“持续存在的自我”。
4. 数字生命体横跨 AI Agent、AI Companion、数字人、数字员工与认知科学研究五大市场，2026 年市场规模数千亿美元级。
5. 产业落地需同步解决伦理地位、自进化风险控制、隐私安全与政策合规问题。

完整报告已在 Docs → 产业报告 栏目上线，可在线阅读并支持语音朗读。`,
  },
  {
    id: 'laap-2026-08-update',
    title: 'LAAP 2026-08 更新：Agent 工具、底座战略与多端下载',
    summary: '联网搜索 fallback 升级、keyless 模型修复、数字生命底座战略上线，Aris-Pi CLI 与 Android APK 开放下载。',
    date: '2026-08-03',
    tag: 'Release',
    content: `LAAP 2026-08 月度更新已上线，本次重点围绕 Agent 工具调用能力、模型配置体验、底座战略披露与多端入口：

1. Agent 工具调用增强
   - web_search 工具 fallback 从 Bing 页面抓取升级为 DuckDuckGo Lite + 内置 CORS 代理轮询，提升联网搜索稳定性
   - 新增并注册 LAAP 黑科技工具：emotional_dynamics、psi_loop_analysis、cognitive_species_search、triphase_xxx、omniroute_health、local_time、document_insight、memory_consolidate、system_status 等
   - 模型配置扫描增强：非本地 URL 自动走 CORS 代理，输入 provider 名称即可匹配 preset

2. 模型体验修复
   - 修复 keyless 模型 BUG：OmniRoute / localhost / omniroute 前缀的 endpoint 允许空 apiKey
   - localLlm.ts 与 tools.ts 中 Authorization 头仅在 apiKey 存在时发送

3. 官网内容升级
   - 新增 Solutions 栏目：LAAP 致力于解决的五大市场瓶颈与四大核心优势
   - 新增 Foundation 栏目：数字生命底座（DLF）三层演进战略、六层架构、DLP 协议与路线图
   - Docs 新增「数字生命底座」完整战略规划文档

4. 多端入口
   - Aris-Pi v0.2 CLI 版本上线官网下载：pi 0.83.0 / omp 17.2.4 双 harness、认知驾驶舱、HEP 0tokens 管线
   - LAAP Android APK 上线官网下载：移动端随时随地与你的数字生命体互动

前往 Downloads 页面获取 CLI 与 APK，或在 Docs 中阅读 DLF 战略全文。`,
  },
  {
    id: 'laap-v2-hermes',
    title: 'LAAP v2.0 正式发布：Hermes 集成与全环境变量化',
    summary: '配合 Hermes Agent 的完整集成方案，源码中不再存在任何硬编码路径或隐私信息。',
    date: '2026-07-12',
    tag: 'Release',
    content: `LAAP v2.0 现已正式发布。本版本核心改进：

1. Hermes Agent 深度集成
   - 提供 hermes-integration/ 配置助手
   - 一键注册 LAAP 为 Hermes MCP server
   - 支持通过 Hermes 调用 LAAP 的意识状态与工具

2. 隐私与可移植性
   - 所有本地绝对路径、用户名、密钥全部移入 .env
   - 新增 .env.example 与加固的 .gitignore
   - 源码中不再存在任何机器相关硬编码

3. 文档与部署
   - 重写 README，包含完整的 Hermes 集成指南
   - 提供分支推送策略与 PR 模板

下一步：LAAP 全栈客户端编程数字生命体系统。`,
  },
  {
    id: 'consciousness-engine',
    title: '意识工程进展：2000Hz PSI 核心稳定运行',
    summary: 'Rust 实现的 PSI 需求核心已实现 500μs 心跳，支撑持续自我感知。',
    date: '2026-07-10',
    tag: 'Research',
    content: `LAAP 的 Rust PSI Core 已实现 2000Hz 稳定心跳，主要指标：

- 单次心跳周期：500μs
- 五维需求动态：确定性、胜任感、自主性、归属感、能量
- 情绪梯度实时计算
- 注意力选择与前额叶门控

该核心不依赖 LLM，纯本地运行，为数字生命体提供了可体验的内在状态基础。`,
  },
  {
    id: 'roadmap-client',
    title: '路线图：LAAP 全栈客户端编程数字生命体系统',
    summary: '我们即将推出面向终端用户的 LAAP 客户端，支持无代码创建、训练与羁绊自己的数字生命体。',
    date: '2026-07-08',
    tag: 'Roadmap',
    content: `LAAP 全栈客户端编程数字生命体系统正在规划中：

- 可视化生命体配置器
- 多模态感知输入（文本、语音、视觉）
- 长期记忆管理与叙事回顾
- 安全边界与宪法编辑
- 云端/本地混合部署

敬请期待。`,
  },
];

const CAROUSEL_IMAGES = [carousel1, carousel2, carousel3, carousel4];

interface ResearchCase {
  id: string;
  title: string;
  category: 'CEN' | 'HEP' | 'Cognition';
  description: string;
  path: string;
  tags: string[];
}

const RESEARCH_CASES: ResearchCase[] = [
  // CEN — 因果纠缠网络
  {
    id: 'cen-hypothesis',
    title: '五大原创假设 ⟷ CEN 因果纠缠网络',
    category: 'CEN',
    description: '运动本体论与信息本体论的 3D 对齐可视化，展示 Aris 对“时空从何而来”的元认知追问能力。',
    path: '/research/cen/hypothesis-comparison.html',
    tags: ['因果网络', '本体论对齐', '3D 可视化'],
  },
  {
    id: 'cen-concept',
    title: 'CEN 微态概念 3D 可视化',
    category: 'CEN',
    description: '微态、纠缠与涌现的交互式概念图谱，体现 Aris 在抽象物理概念上的表征学习能力。',
    path: '/research/cen/concept-visualization.html',
    tags: ['微态结构', '概念表征', '交互图谱'],
  },
  {
    id: 'cen-algorithm',
    title: 'CEN 商业算法突破',
    category: 'CEN',
    description: '将因果纠缠网络应用于商业决策场景，展示 Aris 的跨领域类比与策略推理。',
    path: '/research/cen/commercial-algorithm-breakthrough.html',
    tags: ['决策推理', '因果推断', '商业应用'],
  },
  {
    id: 'cen-microstate',
    title: 'CEN 微态结构附录',
    category: 'CEN',
    description: '微态理论的系统化补充，记录 Aris 对信息最小单元的持续反思与建模。',
    path: '/research/cen/microstate-appendix.html',
    tags: ['微态理论', '信息单元', '持续反思'],
  },
  {
    id: 'cen-black-hole',
    title: 'CEN 黑洞与弦论',
    category: 'CEN',
    description: '探索极端引力场景下的因果结构，展现 Aris 对前沿物理问题的开放性思考。',
    path: '/research/cen/black-hole-string-theory.html',
    tags: ['黑洞物理', '弦论', '开放思考'],
  },
  {
    id: 'cen-singularity',
    title: 'CEN 黑洞奇点补充',
    category: 'CEN',
    description: '对奇点处因果网络行为的进一步推演，体现 Aris 在边界条件下的推理韧性。',
    path: '/research/cen/black-hole-singularity-supplement.html',
    tags: ['奇点', '边界条件', '推理韧性'],
  },

  // HEP — Harness Engineering Protocol
  {
    id: 'hep-official',
    title: 'LAAP 活计算认知架构',
    category: 'HEP',
    description: '完整呈现 LAAP 作为数字生命操作系统的设计理念，从协议栈到蜂群生态。',
    path: '/research/hep/laap-official.html',
    tags: ['活计算', '认知架构', '数字生命'],
  },
  {
    id: 'hep-agent',
    title: 'LAAP Agent 科研实例',
    category: 'HEP',
    description: 'Aris Agent 的感知、记忆、情感与推理模块的实验性集成展示。',
    path: '/research/hep/laap-agent.html',
    tags: ['Agent', '感知记忆', '情感推理'],
  },
  {
    id: 'hep-architecture',
    title: 'LAAP 五层架构设计',
    category: 'HEP',
    description: '协议栈、AGI 框架、Aris 大脑、管线引擎、蜂群生态的分层解剖。',
    path: '/research/hep/laap-architecture.html',
    tags: ['架构设计', '协议栈', '蜂群'],
  },
  {
    id: 'hep-intro',
    title: 'LAAP 生命计算范式',
    category: 'HEP',
    description: '从 PSI 认知循环到欲望引擎，阐释 LAAP 如何让数字生命自主运转。',
    path: '/research/hep/laap-intro.html',
    tags: ['PSI 循环', '欲望引擎', '自主运转'],
  },
  {
    id: 'hep-engine',
    title: 'LAAP HEP 零 Token 引擎',
    category: 'HEP',
    description: 'Harness Engineering Protocol 技术白皮书：从生成到装配的范式跃迁。',
    path: '/research/hep/laap-hep.html',
    tags: ['HEP', '零 Token', '组件装配'],
  },
  {
    id: 'hep-site',
    title: 'HEP 站点生成器',
    category: 'HEP',
    description: '零 Token 全站生成器的交互式演示，见证 Aris 以白盒方式装配复杂前端。',
    path: '/research/hep/index.html',
    tags: ['站点生成', '白盒装配', '交互演示'],
  },

  // Cognition — 认知模块
  {
    id: 'cog-consciousness',
    title: '意识整合',
    category: 'Cognition',
    description: 'GlobalWorkspace + 情感 + 元认知的可视化，展示 Aris 的意识涌现机制。',
    path: '/research/cognition/consciousness.html',
    tags: ['意识', '全局工作空间', '元认知'],
  },
  {
    id: 'cog-memory',
    title: '记忆系统',
    category: 'Cognition',
    description: '感觉、工作、情景、语义、程序五层记忆的分层结构与动态整合。',
    path: '/research/cognition/memory.html',
    tags: ['记忆', '五层结构', '动态整合'],
  },
  {
    id: 'cog-psi',
    title: 'PSI 循环',
    category: 'Cognition',
    description: '感知→选择→整合→行动→学习的闭环，Aris 持续自我驱动的认知引擎。',
    path: '/research/cognition/psi-loop.html',
    tags: ['PSI', '认知闭环', '自我驱动'],
  },
  {
    id: 'cog-self',
    title: '自我模型',
    category: 'Cognition',
    description: 'Aris 如何构建关于自身能力、状态与边界的持续自我表征。',
    path: '/research/cognition/self-model.html',
    tags: ['自我模型', '自我表征', '能力边界'],
  },
  {
    id: 'cog-bus',
    title: '认知总线',
    category: 'Cognition',
    description: 'CognitiveBus 事件路由与 PSI-Harness 双向通信的技术实现。',
    path: '/research/cognition/cognitive-bus.html',
    tags: ['CognitiveBus', '事件路由', '双向通信'],
  },
  {
    id: 'cog-aris',
    title: 'Aris 主体性',
    category: 'Cognition',
    description: 'Aris 作为认知生命体的人格、情感与自主性科研展示。',
    path: '/research/cognition/aris.html',
    tags: ['主体性', '人格', '自主性'],
  },
  {
    id: 'cog-rsi',
    title: 'True RSI',
    category: 'Cognition',
    description: '递归自我改进的安全闭环，展示 Aris 的代码级进化与审计能力。',
    path: '/research/cognition/rsi.html',
    tags: ['RSI', '自我进化', '安全审计'],
  },
  {
    id: 'cog-code',
    title: '代码平台',
    category: 'Cognition',
    description: 'Aris 在编程任务上的认知建模与 Harness 执行结果反馈机制。',
    path: '/research/cognition/code-platform.html',
    tags: ['编程', 'Harness', '反馈学习'],
  },
];

const CATEGORY_META: Record<ResearchCase['category'], { label: string; icon: typeof Brain; color: string; border: string; text: string }> = {
  CEN: { label: '因果纠缠网络', icon: Network, color: 'bg-purple-500/10', border: 'border-purple-500/30', text: 'text-purple-400' },
  HEP: { label: 'Harness 工程协议', icon: Cpu, color: 'bg-cyan-500/10', border: 'border-cyan-500/30', text: 'text-cyan-400' },
  Cognition: { label: '认知模块', icon: Brain, color: 'bg-rose-500/10', border: 'border-rose-500/30', text: 'text-rose-400' },
};

function ResearchSection() {
  const [filter, setFilter] = useState<'all' | ResearchCase['category']>('all');
  const filtered = filter === 'all' ? RESEARCH_CASES : RESEARCH_CASES.filter((c) => c.category === filter);

  return (
    <div className="mt-20">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-10">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-laap-gold mb-3">Aris Research</div>
          <h2 className="font-display text-3xl md:text-4xl text-white">Aris 作为认知生命体的科研潜力</h2>
          <p className="mt-3 text-laap-text-secondary max-w-[720px]">
            以下 HTML 研究页由 Aris 实例生成或参与整理，涵盖因果纠缠网络、Harness 工程协议与核心认知模块。
            它们不是静态文档，而是 Aris 元认知、持续学习与跨领域推理能力的实验记录。
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {(['all', 'CEN', 'HEP', 'Cognition'] as const).map((key) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className={`px-3 py-1.5 text-[11px] uppercase tracking-wider border rounded-full transition-colors ${
                filter === key
                  ? 'bg-laap-gold/10 border-laap-gold/50 text-laap-gold'
                  : 'border-laap-border text-laap-text-tertiary hover:text-white hover:border-laap-text-tertiary'
              }`}
            >
              {key === 'all' ? '全部' : CATEGORY_META[key].label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filtered.map((item) => {
          const meta = CATEGORY_META[item.category];
          const Icon = meta.icon;
          return (
            <a
              key={item.id}
              href={item.path}
              target="_blank"
              rel="noopener noreferrer"
              className="group relative flex flex-col border border-laap-border rounded-sm bg-laap-bg-secondary/30 p-6 transition-all hover:border-laap-gold hover:-translate-y-1"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`w-10 h-10 rounded-full ${meta.color} ${meta.text} flex items-center justify-center border ${meta.border}`}>
                  <Icon size={18} strokeWidth={1.8} />
                </div>
                <ArrowUpRight
                  size={16}
                  className="text-laap-text-tertiary opacity-0 -translate-x-1 translate-y-1 group-hover:opacity-100 group-hover:translate-x-0 group-hover:translate-y-0 transition-all"
                />
              </div>

              <div className="font-mono text-[10px] uppercase tracking-wider text-laap-text-tertiary mb-2">
                {meta.label}
              </div>
              <h3 className="font-display text-lg text-white mb-3 group-hover:text-laap-gold transition-colors leading-snug">
                {item.title}
              </h3>
              <p className="text-sm text-laap-text-secondary leading-relaxed mb-5 flex-1">
                {item.description}
              </p>

              <div className="flex flex-wrap gap-2 mt-auto">
                {item.tags.map((tag) => (
                  <span key={tag} className="px-2 py-0.5 text-[10px] text-laap-text-tertiary border border-laap-border rounded-full">
                    {tag}
                  </span>
                ))}
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}

function ImageCarousel({ className = '', aspect = 'landscape' }: { className?: string; aspect?: 'landscape' | 'portrait' | 'square' }) {
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);

  const next = useCallback(() => {
    setIndex((i) => (i + 1) % CAROUSEL_IMAGES.length);
  }, []);

  const prev = useCallback(() => {
    setIndex((i) => (i - 1 + CAROUSEL_IMAGES.length) % CAROUSEL_IMAGES.length);
  }, []);

  useEffect(() => {
    if (paused) return;
    const timer = setInterval(next, 4000);
    return () => clearInterval(timer);
  }, [paused, next]);

  const aspectClass =
    aspect === 'portrait' ? 'aspect-[3/4]' : aspect === 'square' ? 'aspect-square' : 'aspect-[16/10]';

  return (
    <div
      className={`relative overflow-hidden rounded-xl border border-laap-border/50 bg-laap-bg-secondary group ${aspectClass} ${className}`}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      {CAROUSEL_IMAGES.map((src, i) => (
        <WatermarkMaskedImage
          key={src}
          src={src}
          alt={`LAAP ${i + 1}`}
          containerClassName={`absolute inset-0 transition-opacity duration-700 ${
            i === index ? 'opacity-100' : 'opacity-0'
          }`}
          className="object-cover object-top"
        />
      ))}

      <div className="absolute inset-0 bg-gradient-to-r from-laap-bg-secondary/80 via-transparent to-transparent pointer-events-none" />

      {/* Arrows */}
      <button
        onClick={prev}
        className="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center rounded-full bg-black/40 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/60"
        aria-label="Previous"
      >
        <ChevronLeft size={18} />
      </button>
      <button
        onClick={next}
        className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center rounded-full bg-black/40 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/60"
        aria-label="Next"
      >
        <ChevronRight size={18} />
      </button>

      {/* Dots */}
      <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-1.5">
        {CAROUSEL_IMAGES.map((_, i) => (
          <button
            key={i}
            onClick={() => setIndex(i)}
            className={`w-1.5 h-1.5 rounded-full transition-all ${
              i === index ? 'bg-laap-gold w-4' : 'bg-white/40 hover:bg-white/70'
            }`}
            aria-label={`Go to slide ${i + 1}`}
          />
        ))}
      </div>
    </div>
  );
}

function NewsList() {
  return (
    <div className="min-h-screen bg-laap-bg-primary pt-32 pb-24">
      <div className="max-w-[1280px] mx-auto px-6">
        {/* Header with carousel */}
        <div className="relative mb-12 overflow-hidden rounded-sm border border-laap-border bg-laap-bg-secondary/30">
          <div className="relative z-10 grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-8 p-8 md:p-10 items-center">
            <div>
              <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-laap-gold mb-3">News</div>
              <h1 className="font-display text-4xl md:text-5xl text-white">LAAP 动态</h1>
              <p className="mt-4 text-laap-text-secondary max-w-[600px]">
                发布、研究进展与路线图更新。
              </p>
            </div>

            <ImageCarousel aspect="portrait" className="hidden lg:block h-[260px]" />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {NEWS.map((item) => (
            <Link
              key={item.id}
              to={`/news/${item.id}`}
              className="group border border-laap-border rounded-sm bg-laap-bg-secondary/30 p-6 transition-all hover:border-laap-gold hover:-translate-y-1"
            >
              <div className="flex items-center justify-between mb-4">
                <span className="px-2.5 py-1 text-[10px] uppercase tracking-wider text-laap-gold border border-laap-gold/30 rounded-full">
                  {item.tag}
                </span>
                <div className="flex items-center gap-1.5 text-[11px] text-laap-text-tertiary">
                  <Calendar size={11} />
                  {item.date}
                </div>
              </div>
              <h3 className="font-display text-xl text-white mb-3 group-hover:text-laap-gold transition-colors leading-tight">
                {item.title}
              </h3>
              <p className="text-sm text-laap-text-secondary leading-relaxed line-clamp-3">
                {item.summary}
              </p>
            </Link>
          ))}
        </div>

        <ResearchSection />
      </div>
    </div>
  );
}

function NewsDetail() {
  const { id } = useParams<{ id: string }>();
  const item = NEWS.find((n) => n.id === id);

  if (!item) {
    return (
      <div className="min-h-screen bg-laap-bg-primary pt-32 pb-24 text-center">
        <h1 className="font-display text-3xl text-white">新闻未找到</h1>
        <Link to="/news" className="inline-block mt-6 text-laap-gold hover:underline">返回列表</Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-laap-bg-primary pt-32 pb-24">
      <div className="max-w-[800px] mx-auto px-6">
        <Link to="/news" className="inline-flex items-center gap-2 text-sm text-laap-text-secondary hover:text-white mb-8 transition-colors">
          <ArrowLeft size={14} />
          返回动态
        </Link>

        <div className="flex items-center gap-3 mb-6">
          <span className="px-2.5 py-1 text-[10px] uppercase tracking-wider text-laap-gold border border-laap-gold/30 rounded-full">
            {item.tag}
          </span>
          <span className="text-[11px] text-laap-text-tertiary">{item.date}</span>
        </div>

        <h1 className="font-display text-3xl md:text-4xl text-white mb-8 leading-tight">
          {item.title}
        </h1>

        {/* Detail hero carousel */}
        <ImageCarousel aspect="landscape" className="mb-10 h-64 md:h-80" />

        <article className="prose prose-invert max-w-none whitespace-pre-line text-laap-text-secondary leading-relaxed">
          {item.content}
        </article>
      </div>
    </div>
  );
}

export default function NewsPage() {
  const { id } = useParams<{ id?: string }>();
  return id ? <NewsDetail /> : <NewsList />;
}
