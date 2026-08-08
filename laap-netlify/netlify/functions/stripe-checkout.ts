/**
 * Netlify Function: stripe-checkout
 * ──────────────────────────────────
 * 创建 Stripe Checkout Session（订阅制）。
 * 前端 PricingPage.tsx 点击「订阅 Pro/Team」时调用本函数。
 *
 * 必须的 Netlify Environment Variables：
 *   STRIPE_SECRET_KEY        = sk_live_xxx  （生产）或 sk_test_xxx（测试）
 *   STRIPE_PRICE_PRO_MONTHLY = price_xxx（Pro 月付 Price ID）
 *   STRIPE_PRICE_PRO_YEARLY  = price_xxx（Pro 年付 Price ID）
 *   STRIPE_PRICE_TEAM_MONTHLY= price_xxx（Team 月付 Price ID）
 *   STRIPE_PRICE_TEAM_YEARLY = price_xxx（Team 年付 Price ID）
 *   VITE_APP_DOMAIN          = https://laap.ai（成功/取消回调域名）
 */

import type { Handler, HandlerEvent, HandlerContext } from '@netlify/functions';

// ─── 动态 import Stripe（Netlify Functions ESM 兼容）────────────────────────
let stripeClient: any = null;
async function getStripe() {
  if (stripeClient) return stripeClient;
  const Stripe = (await import('stripe')).default;
  stripeClient = new Stripe(process.env.STRIPE_SECRET_KEY || '', {
    apiVersion: '2024-06-20',
    typescript: false,
  });
  return stripeClient;
}

const ALLOWED_PRICE_IDS = new Set([
  process.env.STRIPE_PRICE_PRO_MONTHLY,
  process.env.STRIPE_PRICE_PRO_YEARLY,
  process.env.STRIPE_PRICE_TEAM_MONTHLY,
  process.env.STRIPE_PRICE_TEAM_YEARLY,
].filter(Boolean) as string[]);

const PLAN_TIER_BY_PRICE: Record<string, string> = {
  [process.env.STRIPE_PRICE_PRO_MONTHLY || '']: 'pro',
  [process.env.STRIPE_PRICE_PRO_YEARLY  || '']: 'pro',
  [process.env.STRIPE_PRICE_TEAM_MONTHLY || '']: 'team',
  [process.env.STRIPE_PRICE_TEAM_YEARLY  || '']: 'team',
};

export const handler: Handler = async (event: HandlerEvent, _context: HandlerContext) => {
  // ── CORS 预检 ───────────────────────────────────────────────────────────
  if (event.httpMethod === 'OPTIONS') {
    return cors({ statusCode: 204, body: '' });
  }
  if (event.httpMethod !== 'POST') {
    return cors({ statusCode: 405, body: JSON.stringify({ error: 'Method Not Allowed' }) });
  }

  try {
    const { priceId, successUrl, cancelUrl } = JSON.parse(event.body || '{}');

    // ── 安全校验 ───────────────────────────────────────────────────────────
    if (!priceId || typeof priceId !== 'string') {
      return cors({ statusCode: 400, body: JSON.stringify({ error: '缺少 priceId 参数' }) });
    }
    if (!ALLOWED_PRICE_IDS.has(priceId)) {
      return cors({ statusCode: 400, body: JSON.stringify({ error: '非法的 priceId' }) });
    }
    if (!process.env.STRIPE_SECRET_KEY) {
      return cors({ statusCode: 500, body: JSON.stringify({ error: '服务端支付配置未就绪（STRIPE_SECRET_KEY）' }) });
    }

    const tier = PLAN_TIER_BY_PRICE[priceId] || 'pro';
    const domain = process.env.VITE_APP_DOMAIN || process.env.URL || '';
    const finalSuccess = successUrl || `${domain}/studio?checkout=success&session_id={CHECKOUT_SESSION_ID}`;
    const finalCancel  = cancelUrl  || `${domain}/pricing?checkout=cancelled`;

    // ── 尝试从 Authorization / Cookie 解析当前用户（如果已登录）─────────────
    //    如果未登录，则 Stripe Checkout 后在 success 页面再补绑用户
    const authHeader = event.headers['authorization'] || '';
    const userId = authHeader.startsWith('Bearer ') ? authHeader.slice(7) : null;

    const stripe = await getStripe();
    const session = await stripe.checkout.sessions.create({
      mode: 'subscription',
      payment_method_types: ['card', 'alipay', 'wechat_pay'].filter(Boolean) as any,
      allow_promotion_codes: true,
      line_items: [{ price: priceId, quantity: 1 }],
      customer_email: undefined, // 让 Stripe 填，或之后回写
      metadata: {
        tier,
        price_id: priceId,
        source: 'laap-netlify-pricing',
        user_id: userId || 'anonymous',
      },
      subscription_data: {
        metadata: { tier, user_id: userId || 'anonymous' },
        trial_period_days: tier === 'pro' ? 7 : undefined, // Pro 7 天免费试用
      },
      success_url: finalSuccess,
      cancel_url: finalCancel,
      expires_at: Math.floor(Date.now() / 1000) + 30 * 60, // 30 分钟过期
    });

    console.log(`[OK] Stripe Checkout session created: id=${session.id} tier=${tier} user=${userId || 'anon'}`);
    return cors({
      statusCode: 200,
      body: JSON.stringify({ sessionId: session.id, tier, url: session.url }),
    });
  } catch (e: any) {
    console.error('[ERROR] stripe-checkout:', e);
    return cors({
      statusCode: e.statusCode || 500,
      body: JSON.stringify({
        error: e.raw?.message || e.message || '创建支付会话失败',
      }),
    });
  }
};

// ─── 工具：CORS 响应头 ─────────────────────────────────────────────────────
function cors(resp: { statusCode: number; body: string; headers?: any }) {
  return {
    ...resp,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Content-Type': 'application/json; charset=utf-8',
      ...(resp.headers || {}),
    },
  };
}
