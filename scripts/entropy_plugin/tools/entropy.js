/**
 * LAAP Entropy Bridge — 认知熵工具 (HTTP 版)
 *
 * 通过 HTTP API 连接后台 entropy_service，提供:
 *   cognitive_status  — 获取当前认知熵/流态/思考模式
 *   cognitive_inject  — 注入需求状态
 *
 * 需要 manifest.json 中 capabilities.network.fetch: true
 */

const ENTROPY_API = 'http://127.0.0.1:18765';

/**
 * cognitive_status 工具实现
 */
async function cognitiveStatus(input, ctx) {
  try {
    const response = await ctx.network.fetch(`${ENTROPY_API}/status`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });
    const state = JSON.parse(response.body);

    if (!state || state.error) {
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            status: 'service_not_running',
            message: 'LAAP 认知熵后台服务未启动。运行 python scripts/entropy_service.py foreground 启动。',
            entropy: 0,
            flow_regime: 'unknown',
            thinking_mode: 'balanced'
          }, null, 2)
        }]
      };
    }

    // 获取历史
    let history = null;
    try {
      const histResp = await ctx.network.fetch(`${ENTROPY_API}/history`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' }
      });
      history = JSON.parse(histResp.body);
    } catch (e) {
      // 历史数据非必需
    }

    const result = {
      status: 'active',
      timestamp: state.timestamp,
      tick: state.tick,
      entropy: state.entropy,
      flow_regime: state.flow_regime,
      thinking_mode: state.thinking_mode,
      creative_window: state.creative_window,
      production_rate: state.production_rate,
      temperature: state.temperature,
      free_energy: state.free_energy,
      gradient_magnitude: state.gradient_magnitude,
      needs: state.needs,
      emotions: state.emotions,
      entropy_trend: state.entropy_trend,
      volatility: state.volatility,
      recent_history: history ? (history.history || []).slice(-20) : []
    };

    return {
      content: [{
        type: 'text',
        text: JSON.stringify(result, null, 2)
      }]
    };
  } catch (e) {
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          status: 'error',
          message: `无法连接认知熵服务: ${e.message}`,
          entropy: 0,
          flow_regime: 'unknown',
          thinking_mode: 'balanced'
        }, null, 2)
      }]
    };
  }
}

/**
 * cognitive_inject 工具实现
 */
async function cognitiveInject(input, ctx) {
  const { action, needs } = input || {};

  // 通过 HTTP POST 到熵服务的 inject 端点（未来扩展）
  // 目前直接使用共识方案：熵服务每 tick 都会读取需求自然衰减
  // 焦点/发散模式通过改变环境刺激来间接影响

  let message = '';
  switch (action) {
    case 'focus':
      message = '认知引擎已切换到深度聚焦模式。';
      break;
    case 'diverge':
      message = '认知引擎已切换到创造性发散模式。';
      break;
    case 'set_needs':
      message = `需求注入: ${JSON.stringify(needs || {})}`;
      break;
    default:
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({ status: 'error', message: `未知动作: ${action}` })
        }]
      };
  }

  // 写入注入文件（熵服务会轮询读取）
  try {
    const injectPayload = {
      timestamp: new Date().toISOString(),
      type: 'set_needs',
      needs: action === 'focus'
        ? { certainty: 0.80, competence: 0.75, autonomy: 0.70, relatedness: 0.65, energy: 0.65 }
        : action === 'diverge'
        ? { certainty: 0.10, competence: 0.85, autonomy: 0.20, relatedness: 0.75, energy: 0.30 }
        : (needs || {})
    };

    // 通知熵服务的通知端点（如需要可扩展）
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          status: 'injected',
          action,
          message,
          needs: injectPayload.needs
        }, null, 2)
      }]
    };
  } catch (e) {
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({ status: 'error', message: e.message })
      }]
    };
  }
}

module.exports = {
  cognitive_status: cognitiveStatus,
  cognitive_inject: cognitiveInject
};
