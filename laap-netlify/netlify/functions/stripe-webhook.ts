/**
 * Netlify Function: stripe-webhook
 * ──────────────────────────────────
 * 接收 Stripe 事件回调，处理：
 *   ✓ checkout.session.completed  → 首次开通 → 发放 Pro/Team 权益
 *   ✓ customer.subscription.updated → 续费、升降级
 *   ✓ customer.subscription.deleted → 取消订阅 → 回退至 Free
 *   ✓ invoice.payment_failed      → 支付失败 → 邮件提醒 + 宽限期
 *
 * 必须的 Netlify Environment Variables：
 *   STRIPE_WEBHOOK_SECRET = whsec_xxxxxxxx
 *   STRIPE_SECRET_KEY     = sk_live_xxx
 */

import type { Handler, HandlerEvent, HandlerContext } from '@netlify/functions';

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

export const handler: Handler = async (event: HandlerEvent, _context: HandlerContext) => {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method Not Allowed' };
  }

  const sig = event.headers['stripe-signature'] || '';
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!webhookSecret) {
    console.error('[FATAL] STRIPE_WEBHOOK_SECRET 未配置');
    return { statusCode: 500, body: 'Server misconfigured' };
  }

  try {
    const stripe = await getStripe();
    const payload = event.body || '';
    const evt = stripe.webhooks.constructEvent(payload, sig, webhookSecret);

    console.log(`[WEBHOOK] Received: ${evt.type} id=${evt.id}`);

    switch (evt.type) {
      case 'checkout.session.completed':
        await handleCheckoutCompleted(evt.data.object);
        break;
      case 'customer.subscription.updated':
        await handleSubscriptionUpdated(evt.data.object);
        break;
      case 'customer.subscription.deleted':
        await handleSubscriptionDeleted(evt.data.object);
        break;
      case 'invoice.payment_failed':
        await handlePaymentFailed(evt.data.object);
        break;
      default:
        console.log(`[WEBHOOK] Ignored unhandled event: ${evt.type}`);
    }

    return { statusCode: 200, body: JSON.stringify({ received: true }) };
  } catch (e: any) {
    console.error('[WEBHOOK ERROR]', e?.message || e);
    return {
      statusCode: e.statusCode || 400,
      body: `Webhook Error: ${e.message}`,
    };
  }
};

// ─── 事件处理函数 ───────────────────────────────────────────────────────────

async function handleCheckoutCompleted(session: any) {
  const tier   = session.metadata?.tier   || 'pro';
  const userId = session.metadata?.user_id || null;
  const subId  = session.subscription;
  const custId = session.customer;
  const email  = session.customer_details?.email || session.customer_email;

  console.log(`[CHECKOUT OK] tier=${tier} user=${userId || 'anon'} sub=${subId} cust=${custId} email=${email}`);

  // ── TODO: 实际项目中，此处写入业务 DB ────────────────────────────────────
  //    1. user_subscriptions 表：(user_id, tier, stripe_sub_id, stripe_cust_id, status, current_period_end)
  //    2. 如果 user_id === 'anonymous'，生成 activation_token，之后登录后凭 session_id 绑定
  //    3. 发送欢迎邮件（Resend / SendGrid / 阿里云邮件）
  //
  // 伪代码：
  //   await db.execute(
  //     `INSERT INTO user_subscriptions (user_id, tier, stripe_sub_id, stripe_cust_id, email, status, started_at)
  //      VALUES (?, ?, ?, ?, ?, 'active', NOW())
  //      ON DUPLICATE KEY UPDATE tier=?, status='active'`,
  //     [userId || `anon_${subId}`, tier, subId, custId, email, tier]
  //   );
  //
  //   await sendWelcomeEmail(email, tier);
}

async function handleSubscriptionUpdated(sub: any) {
  const tier = sub.metadata?.tier || mapPlanToTier(sub.items?.data?.[0]?.plan?.id);
  const status = sub.status;              // active / past_due / canceled / unpaid
  const periodEnd = sub.current_period_end;
  console.log(`[SUB UPDATED] tier=${tier} status=${status} period_end=${periodEnd}`);

  // ── TODO: 更新 user_subscriptions 表 ─────────────────────────────────────
  //    升降级 -> 更新 tier
  //    续费成功 -> 延长 current_period_end
  //    状态变更（active / past_due）-> 相应限流
}

async function handleSubscriptionDeleted(sub: any) {
  const tier = sub.metadata?.tier || 'pro';
  console.log(`[SUB CANCELLED] tier=${tier} sub=${sub.id} at_period_end=${sub.cancel_at_period_end}`);

  // ── TODO: 取消后，current_period_end 之前仍可使用，到期降级为 Free ───────
  //    UPDATE user_subscriptions SET status='canceled', cancelled_at=NOW() WHERE stripe_sub_id = ?
}

async function handlePaymentFailed(invoice: any) {
  const attemptCount = invoice.attempt_count || 1;
  const nextAttempt  = invoice.next_payment_attempt;
  const email        = invoice.customer_email;
  console.error(`[PAYMENT FAILED] attempts=${attemptCount} next=${nextAttempt} email=${email}`);

  // ── TODO: 宽限期策略 ─────────────────────────────────────────────────────
  //    attempt=1 → 柔和提醒邮件
  //    attempt=2 → 强提醒 + 保留 Pro 权益
  //    attempt=3 → 降级 Free，但保留数据 14 天
}

// ─── 工具 ───────────────────────────────────────────────────────────────────
function mapPlanToTier(planId: string | undefined): string {
  if (!planId) return 'pro';
  if (planId === process.env.STRIPE_PRICE_TEAM_MONTHLY || planId === process.env.STRIPE_PRICE_TEAM_YEARLY) return 'team';
  return 'pro';
}
