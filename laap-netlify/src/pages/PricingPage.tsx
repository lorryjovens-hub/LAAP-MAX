import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { Check, Zap, Shield, Building2, Crown, ArrowRight, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';

// ─── Stripe 环境变量（Vite_ 前缀暴露给前端）────────────────────────────────
const STRIPE_PUBLISHABLE_KEY = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || '';
const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

// ─── 套餐定义 ──────────────────────────────────────────────────────────────
type BillingCycle = 'monthly' | 'yearly';

const PRICING_PLANS = {
  free: {
    monthly: { id: 'free', name: 'Free', priceCents: 0, priceDisplay: '¥0', period: '' },
    yearly:  { id: 'free', name: 'Free', priceCents: 0, priceDisplay: '¥0', period: '' },
  },
  pro: {
    monthly: {
      id: 'pro_monthly',
      name: 'Pro',
      priceCents: 2900,            // ￥29.00
      priceDisplay: '¥29',
      period: '/月',
      stripePriceId: import.meta.env.VITE_STRIPE_PRICE_PRO_MONTHLY || '',
    },
    yearly: {
      id: 'pro_yearly',
      name: 'Pro',
      priceCents: 28800,           // ￥288.00（年付 17% off ≈ ￥24/月）
      priceDisplay: '¥288',
      period: '/年',
      stripePriceId: import.meta.env.VITE_STRIPE_PRICE_PRO_YEARLY || '',
      highlight: '省 ¥60',
    },
  },
  team: {
    monthly: {
      id: 'team_monthly',
      name: 'Team',
      priceCents: 19900,           // ￥199.00 / 5人
      priceDisplay: '¥199',
      period: '/月/5人',
      stripePriceId: import.meta.env.VITE_STRIPE_PRICE_TEAM_MONTHLY || '',
    },
    yearly: {
      id: 'team_yearly',
      name: 'Team',
      priceCents: 199900,          // ￥1999.00 / 5人年（省 ￥389）
      priceDisplay: '¥1,999',
      period: '/年/5人',
      stripePriceId: import.meta.env.VITE_STRIPE_PRICE_TEAM_YEARLY || '',
      highlight: '省 ¥389',
    },
  },
  enterprise: {
    monthly: { id: 'enterprise', name: 'Enterprise', priceCents: -1, priceDisplay: '联系销售', period: '' },
    yearly:  { id: 'enterprise', name: 'Enterprise', priceCents: -1, priceDisplay: '联系销售', period: '' },
  },
};

// ─── Feature 对比矩阵 ──────────────────────────────────────────────────────
const FEATURE_GROUPS = [
  {
    group: '基础 AI 能力',
    features: [
      { name: '免费 OmniRoute 模型调用（30 次/对话上限）', free: true, pro: true, team: true, enterprise: true },
      { name: '接入自有 LLM Key（SenseNova/DeepSeek/OpenAI）', free: true, pro: true, team: true, enterprise: true },
      { name: '云端托管调用（1000 次/月）', free: false, pro: true, team: true, enterprise: '不限' },
      { name: '1,000,000 Token 上下文窗口', free: true, pro: true, team: true, enterprise: '2M+' },
      { name: '视觉理解多模态（图片分析）', free: true, pro: true, team: true, enterprise: true },
    ],
  },
  {
    group: '认知与治理（LAAP 护城河）',
    features: [
      { name: 'PSI 因果验证（幻觉拦截）', free: '基础', pro: '标准', team: '标准', enterprise: '企业级' },
      { name: '三层记忆系统（工作/近期/核心）', free: 'IndexedDB', pro: '云端同步', team: '团队共享', enterprise: '私有化' },
      { name: '审计迹 & 哈希注册表（合规必查）', free: false, pro: true, team: true, enterprise: '不可篡改' },
      { name: 'CLP 组件匹配（Token 节省 98%）', free: false, pro: true, team: true, enterprise: true },
      { name: '宪章治理 & 紧急中止协议', free: false, pro: false, team: '基础版', enterprise: '完整 SLA' },
    ],
  },
  {
    group: '协作与部署',
    features: [
      { name: 'Ψ-Net 多端同步（桌面/手机/云端）', free: false, pro: true, team: true, enterprise: true },
      { name: '团队记忆共享与协作', free: false, pro: false, team: true, enterprise: '无限空间' },
      { name: 'SSO 单点登录（OIDC / SAML）', free: false, pro: false, team: false, enterprise: true },
      { name: '私有化部署 K8s Helm Chart', free: false, pro: false, team: false, enterprise: true },
      { name: '专属架构师 & 7×24 支持', free: false, pro: false, team: false, enterprise: true },
    ],
  },
];

// ─── 主组件 ────────────────────────────────────────────────────────────────
export default function PricingPage() {
  const navigate = useNavigate();
  const [billing, setBilling] = useState<BillingCycle>('yearly');
  const [loadingPlanId, setLoadingPlanId] = useState<string | null>(null);
  const [stripeLoaded, setStripeLoaded] = useState(false);

  // 懒加载 Stripe.js（避免首屏阻塞）
  useEffect(() => {
    if (!STRIPE_PUBLISHABLE_KEY || stripeLoaded || typeof window === 'undefined') return;
    if ((window as any).Stripe) { setStripeLoaded(true); return; }
    const script = document.createElement('script');
    script.src = 'https://js.stripe.com/v3/';
    script.async = true;
    script.onload = () => setStripeLoaded(true);
    document.head.appendChild(script);
  }, [stripeLoaded]);

  const handleCheckout = async (planId: string, stripePriceId: string) => {
    if (!STRIPE_PUBLISHABLE_KEY || !stripePriceId) {
      toast.warning('支付通道暂未配置，请稍后或联系销售');
      return;
    }
    setLoadingPlanId(planId);
    try {
      // Step 1: 调我们自己的 Netlify Function 创建 Checkout Session
      const resp = await fetch(`${API_BASE}/stripe-checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          priceId: stripePriceId,
          successUrl: `${window.location.origin}/studio?checkout=success&session_id={CHECKOUT_SESSION_ID}`,
          cancelUrl: `${window.location.origin}/pricing?checkout=cancelled`,
        }),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ error: resp.statusText }));
        throw new Error(err.error || '创建支付会话失败');
      }
      const { sessionId } = await resp.json();

      // Step 2: 跳转到 Stripe Checkout
      const stripe = (window as any).Stripe(STRIPE_PUBLISHABLE_KEY);
      const { error } = await stripe.redirectToCheckout({ sessionId });
      if (error) throw error;
    } catch (e: any) {
      console.error('[Stripe Checkout]', e);
      toast.error(e.message || '支付跳转失败，请重试');
    } finally {
      setLoadingPlanId(null);
    }
  };

  const handleEnterpriseContact = () => {
    const subject = encodeURIComponent('[LAAP] 企业版采购咨询');
    const body = encodeURIComponent(
      '您好 LAAP 团队，\n\n我公司希望了解 LAAP Enterprise 私有化部署方案，请提供：\n1. 公司名称 & 规模：\n2. 使用场景（金融合规/科研/具身/其他）：\n3. 预期 Agent 数量：\n4. 联系人 & 电话：\n\n谢谢。'
    );
    window.location.href = `mailto:sales@laap.ai?subject=${subject}&body=${body}`;
  };

  return (
    <div className="min-h-screen bg-laap-bg-primary text-laap-text-primary">
      {/* ─── Hero 标题区 ─────────────────────────────────────── */}
      <section className="relative overflow-hidden pt-24 pb-16">
        <div className="absolute inset-0 bg-gradient-to-b from-laap-accent-cyan/10 via-transparent to-transparent pointer-events-none" />
        <div className="container mx-auto px-6 relative">
          <div className="max-w-3xl mx-auto text-center">
            <Badge variant="outline" className="mb-4 border-laap-accent-cyan/40 text-laap-accent-cyan px-4 py-1.5">
              <Sparkles className="w-3.5 h-3.5 mr-2 inline-block align-[-2px]" />
              全新定价 · 年付立省 17%
            </Badge>
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-r from-white via-laap-text-primary to-laap-accent-cyan">
              简单、透明的定价
            </h1>
            <p className="text-lg md:text-xl text-laap-text-secondary leading-relaxed">
              为个人开发者、团队与企业打造。从免费体验到私有化部署，
              <br className="hidden md:block" />
              每一层都为「可信、可治理、持续进化」的数字生命而设计。
            </p>
          </div>

          {/* Billing Tabs */}
          <div className="mt-12 flex justify-center">
            <Tabs
              value={billing}
              onValueChange={(v) => setBilling(v as BillingCycle)}
              className="w-[320px]"
            >
              <TabsList className="grid grid-cols-2 bg-laap-bg-secondary border border-laap-border rounded-full p-1">
                <TabsTrigger value="monthly" className="rounded-full data-[state=active]:bg-laap-accent-cyan/15 data-[state=active]:text-laap-accent-cyan">
                  月付
                </TabsTrigger>
                <TabsTrigger value="yearly" className="rounded-full data-[state=active]:bg-laap-accent-cyan/15 data-[state=active]:text-laap-accent-cyan">
                  年付 <span className="ml-1.5 text-xs text-emerald-400 font-medium">省 17%</span>
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </div>
      </section>

      {/* ─── 四档套餐卡片 ───────────────────────────────────── */}
      <section className="container mx-auto px-6 pb-20">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 max-w-7xl mx-auto">
          <PricingCard
            tier="free"
            icon={Zap}
            plan={PRICING_PLANS.free[billing]}
            description="个人体验与轻量使用，开箱即用"
            features={[
              'OmniRoute 免费模型（30 次/对话）',
              '接入自有 LLM Key',
              '1,000,000 Token 上下文',
              '本地 IndexedDB 存储',
              '视觉理解多模态',
            ]}
            cta="免费开始"
            ctaVariant="outline"
            onCta={() => navigate('/studio')}
          />

          <PricingCard
            tier="pro"
            icon={Crown}
            plan={PRICING_PLANS.pro[billing]}
            description="独立开发者与重度用户，云端无限可能"
            highlight
            features={[
              '1,000 次/月云端托管调用',
              'Ψ-Net 多端记忆同步',
              'PSI 因果验证（标准版）',
              'Token 节省 98%（CLP 匹配）',
              '审计迹导出（JSON/CSV）',
              '优先客服支持',
            ]}
            cta={billing === 'yearly' ? '立即订阅 Pro · 年付' : '立即订阅 Pro'}
            ctaVariant="default"
            loading={loadingPlanId === PRICING_PLANS.pro[billing].id}
            onCta={() => handleCheckout(
              PRICING_PLANS.pro[billing].id,
              (PRICING_PLANS.pro[billing] as any).stripePriceId
            )}
            badge="最受欢迎"
          />

          <PricingCard
            tier="team"
            icon={Building2}
            plan={PRICING_PLANS.team[billing]}
            description="5 人小团队共享记忆与协作"
            features={[
              '团队记忆共享空间',
              'Ψ-Net 多端同步（全员）',
              '宪章治理（基础版）',
              '无限云端托管调用',
              '1 对 1 上线指导（1 小时）',
              '团队管理员权限',
            ]}
            cta={billing === 'yearly' ? '订阅 Team · 年付' : '订阅 Team'}
            ctaVariant="default"
            loading={loadingPlanId === PRICING_PLANS.team[billing].id}
            onCta={() => handleCheckout(
              PRICING_PLANS.team[billing].id,
              (PRICING_PLANS.team[billing] as any).stripePriceId
            )}
          />

          <PricingCard
            tier="enterprise"
            icon={Shield}
            plan={PRICING_PLANS.enterprise[billing]}
            description="金融/政务/科研定制私有化部署"
            features={[
              '私有化 K8s / VPC 部署',
              'SSO（OIDC / SAML / LDAP）',
              '完整宪章治理 + SLA',
              '行业 Harness（金融/科研/医药）',
              '专属架构师 7×24',
              '定制合规审计报告',
            ]}
            cta="联系销售"
            ctaVariant="default"
            onCta={handleEnterpriseContact}
          />
        </div>
      </section>

      {/* ─── Feature 对比矩阵 ───────────────────────────────── */}
      <section className="container mx-auto px-6 pb-24">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-4">全功能对比</h2>
          <p className="text-center text-laap-text-secondary mb-12">
            清晰透明，每一层能力差异一目了然。
          </p>

          <Card className="border-laap-border bg-laap-bg-secondary/40 backdrop-blur overflow-hidden">
            <CardHeader className="grid grid-cols-5 gap-4 bg-laap-bg-secondary/60 border-b border-laap-border">
              <div className="col-span-2 font-semibold text-laap-text-secondary">功能</div>
              {['Free', 'Pro', 'Team', 'Enterprise'].map((t) => (
                <div key={t} className="text-center font-semibold">{t}</div>
              ))}
            </CardHeader>
            <CardContent className="p-0">
              {FEATURE_GROUPS.map((group, gi) => (
                <div key={group.group}>
                  <div className="px-6 py-3 bg-laap-bg-tertiary/40 border-b border-laap-border text-sm font-semibold text-laap-accent-cyan">
                    {group.group}
                  </div>
                  {group.features.map((f, fi) => (
                    <div
                      key={f.name}
                      className={`grid grid-cols-5 gap-4 px-6 py-3.5 items-center ${
                        fi !== group.features.length - 1 ? 'border-b border-laap-border/60' : ''
                      } ${gi !== FEATURE_GROUPS.length - 1 || fi !== group.features.length - 1 ? '' : ''}`}
                    >
                      <div className="col-span-2 text-sm text-laap-text-primary">{f.name}</div>
                      {(['free', 'pro', 'team', 'enterprise'] as const).map((tier) => {
                        const v = (f as any)[tier];
                        return (
                          <div key={tier} className="flex items-center justify-center text-sm">
                            {v === true ? (
                              <Check className="w-5 h-5 text-emerald-400" />
                            ) : v === false || v === undefined ? (
                              <span className="text-laap-text-muted">—</span>
                            ) : (
                              <span className="text-laap-accent-amber text-xs font-medium">{v}</span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ))}
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </section>

      {/* ─── FAQ 常见问题 ───────────────────────────────────── */}
      <section className="container mx-auto px-6 pb-24">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">常见问题</h2>
          <div className="space-y-5">
            <FaqItem
              q="Free 版的 30 次对话限制是怎么计算的？"
              a="Free 版基于浏览器 IndexedDB 本地计数，每个独立对话最多 30 次 OmniRoute 免费模型调用。超过后会引导你填入自己的 LLM API Key（SenseNova/DeepSeek/OpenAI 均可），之后完全免费使用，无次数限制——因为费用是你直接付给模型供应商。"
            />
            <FaqItem
              q="Pro 年付的省 ¥60 是怎么算的？"
              a="月付 ￥29 × 12 = ￥348，年付 ￥288，直接省下 ￥60（约 17%）。年付用户还将提前体验内测中的金融 Harness 功能。"
            />
            <FaqItem
              q="可以升级/降级套餐吗？退款政策是怎样的？"
              a="随时可以在个人中心升级套餐，差价按剩余天数比例计算。7 天内未使用任何 Pro 付费资源可全额退款，超过 7 天按比例退款。Enterprise 私有化项目按合同 SOW 执行。"
            />
            <FaqItem
              q="企业版支持哪些合规要求？"
              a="Enterprise 支持等保三级、ISO 27001、EU AI Act 附录 III 高风险场景清单、中国《生成合成内容标识办法》等合规要求；审计日志哈希链防篡改、私有化数据主权完全在客户侧；可提供合规咨询与联合申报服务。"
            />
            <FaqItem
              q="团队记忆和 Ψ-Net 同步的数据安全吗？"
              a="数据传输全链路 TLS 1.3；存储端 AES-256 加密；团队空间按组织 ID 逻辑隔离；Enterprise 可部署在客户 VPC 内，LAAP 侧零数据留存。合规报告可按需提供。"
            />
          </div>
        </div>
      </section>

      {/* ─── CTA ────────────────────────────────────────────── */}
      <section className="container mx-auto px-6 pb-28">
        <Card className="border-laap-accent-cyan/30 bg-gradient-to-br from-laap-accent-cyan/10 via-laap-bg-secondary to-laap-bg-secondary max-w-4xl mx-auto">
          <CardContent className="py-12 px-8 text-center">
            <h3 className="text-2xl md:text-3xl font-bold mb-3">
              还在犹豫？先免费体验 Studio 全功能
            </h3>
            <p className="text-laap-text-secondary mb-8 max-w-2xl mx-auto">
              不需要信用卡，不需要注册。用自己的 LLM Key 即可享受 LAAP 全部认知能力。
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button
                size="lg"
                onClick={() => navigate('/studio')}
                className="bg-laap-accent-cyan hover:bg-laap-accent-cyan/85 text-laap-bg-primary font-semibold px-8"
              >
                进入 Studio
                <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
              <Button size="lg" variant="outline" onClick={handleEnterpriseContact}>
                预约企业演示
              </Button>
            </div>
            <Separator className="my-8 border-laap-border/50" />
            <p className="text-xs text-laap-text-muted">
              销售邮箱：sales@laap.ai · 商务合作：bd@laap.ai · 隐私与条款：/legal
            </p>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

// ─── 子组件：PricingCard ────────────────────────────────────────────────────
function PricingCard(props: {
  tier: string;
  icon: any;
  plan: any;
  description: string;
  features: string[];
  cta: string;
  ctaVariant: 'default' | 'outline';
  onCta: () => void;
  highlight?: boolean;
  loading?: boolean;
  badge?: string;
}) {
  const { tier, icon: Icon, plan, description, features, cta, ctaVariant, onCta, highlight, loading, badge } = props;
  return (
    <Card className={`relative flex flex-col border transition-all duration-300 ${
      highlight
        ? 'border-laap-accent-cyan/50 shadow-[0_0_60px_-15px_rgba(34,211,238,0.35)] bg-gradient-to-b from-laap-accent-cyan/[0.07] to-laap-bg-secondary scale-[1.02]'
        : 'border-laap-border bg-laap-bg-secondary/40 hover:border-laap-accent-cyan/30'
    }`}>
      {badge && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <Badge className="bg-laap-accent-cyan text-laap-bg-primary font-semibold px-3 py-1">
            {badge}
          </Badge>
        </div>
      )}
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3 mb-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
            highlight ? 'bg-laap-accent-cyan text-laap-bg-primary' : 'bg-laap-bg-tertiary text-laap-accent-cyan'
          }`}>
            <Icon className="w-5 h-5" />
          </div>
          <div>
            <CardTitle className="text-xl">{plan.name}</CardTitle>
          </div>
        </div>
        <CardDescription className="text-sm min-h-[40px]">{description}</CardDescription>
        <div className="flex items-baseline gap-1 mt-4">
          <span className="text-4xl font-bold tracking-tight">{plan.priceDisplay}</span>
          <span className="text-laap-text-secondary">{plan.period}</span>
        </div>
        {plan.highlight && (
          <Badge variant="secondary" className="mt-2 bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
            {plan.highlight}
          </Badge>
        )}
      </CardHeader>
      <CardContent className="flex-1 pb-2">
        <ul className="space-y-2.5">
          {features.map((f, i) => (
            <li key={i} className="flex items-start gap-2.5 text-sm">
              <Check className="w-4 h-4 mt-0.5 text-laap-accent-cyan flex-shrink-0" />
              <span className="text-laap-text-primary leading-relaxed">{f}</span>
            </li>
          ))}
        </ul>
      </CardContent>
      <CardFooter className="pt-2">
        <Button
          className={`w-full ${highlight ? 'bg-laap-accent-cyan hover:bg-laap-accent-cyan/85 text-laap-bg-primary font-semibold' : ''}`}
          variant={ctaVariant}
          size="lg"
          onClick={onCta}
          disabled={loading}
        >
          {loading ? (
            <span className="inline-flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
              支付准备中…
            </span>
          ) : (
            cta
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}

// ─── 子组件：FAQ ────────────────────────────────────────────────────────────
function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <Card className="border-laap-border bg-laap-bg-secondary/30 overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full px-6 py-5 flex items-center justify-between text-left hover:bg-laap-bg-tertiary/30 transition-colors"
      >
        <span className="font-semibold pr-8">{q}</span>
        <span className={`text-laap-accent-cyan transition-transform duration-200 ${open ? 'rotate-45' : ''}`}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
        </span>
      </button>
      {open && (
        <div className="px-6 pb-5 text-laap-text-secondary leading-relaxed text-sm border-t border-laap-border/50 pt-4">
          {a}
        </div>
      )}
    </Card>
  );
}
