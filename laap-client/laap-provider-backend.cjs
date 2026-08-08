/**
 * laap-provider-backend.cjs — 供应商 API 代理后端
 *
 * 接收来自 laap-client 前端的 LLM/TTS/ASR 配置请求,
 * 转发到真实 API（DeepSeek / OpenAI / 豆包等）。
 *
 * 作为独立进程运行: node laap-provider-backend.cjs
 * 或与 mock server 一起: node laap-all-in-one.cjs
 */

const { createServer } = require('http')
const { WebSocketServer } = require('ws')

// ─── LLM Provider 路由 ───

const LLM_ENDPOINTS = {
  deepseek:  { base: 'https://api.deepseek.com', path: '/chat/completions' },
  openai:    { base: 'https://api.openai.com/v1', path: '/chat/completions' },
  minimax:   { base: 'https://api.minimax.chat/v1', path: '/chat/completions' },
  qwen:      { base: 'https://dashscope.aliyuncs.com/compatible-mode/v1', path: '/chat/completions' },
  moonshot:  { base: 'https://api.moonshot.cn/v1', path: '/chat/completions' },
  zhipu:     { base: 'https://open.bigmodel.cn/api/paas/v4', path: '/chat/completions' },
  mimo:      { base: 'https://api.xiaomimimo.com/v1', path: '/chat/completions' },
}

async function handleLLMRequest(provider, apiKey, model, messages) {
  const ep = LLM_ENDPOINTS[provider]
  if (!ep) return { error: `未知提供商: ${provider}` }
  if (!apiKey) return { error: `未配置 ${provider} API Key` }

  const url = ep.base + ep.path
  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ model: model || 'default', messages, stream: false }),
      signal: AbortSignal.timeout(30000),
    })
    if (!resp.ok) {
      const err = await resp.text().catch(() => '')
      return { error: `${provider} API ${resp.status}: ${err.slice(0, 200)}` }
    }
    const data = await resp.json()
    return { success: true, data }
  } catch (err) {
    return { error: `${provider} 请求失败: ${err.message}` }
  }
}

// ─── TTS Provider 路由 ───

async function handleTTSRequest(provider, text, voiceId, creds) {
  if (provider === 'openai' && creds.openaiTtsKey) {
    const resp = await fetch('https://api.openai.com/v1/audio/speech', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${creds.openaiTtsKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'tts-1', input: text, voice: voiceId || 'nova',
        response_format: 'mp3',
      }),
      signal: AbortSignal.timeout(30000),
    })
    if (!resp.ok) return { error: `TTS ${resp.status}` }
    const buffer = await resp.arrayBuffer()
    return { success: true, audioBase64: Buffer.from(buffer).toString('base64'), format: 'mp3' }
  }
  // 其他 TTS 提供商类似...
  return { error: `TTS 提供商 ${provider} 暂未实现` }
}

// ─── WebSocket 服务器 ───

function startProviderBackend(port = 8766) {
  const wss = new WebSocketServer({ host: '127.0.0.1', port })
  console.log(`[ProviderBackend] 供应商 API 代理启动 → ws://127.0.0.1:${port}`)

  wss.on('connection', (ws) => {
    ws.on('message', async (raw) => {
      let msg
      try { msg = JSON.parse(String(raw)) } catch { return }
      const { topic, payload, id } = msg

      let result = { success: false, error: 'unknown' }

      try {
        if (topic === 'llm.chat') {
          result = await handleLLMRequest(payload.provider, payload.apiKey, payload.model, payload.messages)
        } else if (topic === 'tts.speak') {
          result = await handleTTSRequest(payload.provider, payload.text, payload.voiceId, payload.creds || {})
        } else if (topic === 'provider.list_models') {
          result = { success: true, data: LLM_ENDPOINTS }
        } else {
          result = { error: `未知 topic: ${topic}` }
        }
      } catch (err) {
        result = { error: err.message }
      }

      if (ws.readyState === 1) {
        ws.send(JSON.stringify({ topic: `response.${id || 'anon'}`, payload: result, timestamp: Date.now() }))
      }
    })
  })

  return wss
}

// ─── 独立启动 ───
if (require.main === module) {
  startProviderBackend(parseInt(process.argv[2] || '8766', 10))
  console.log('[ProviderBackend] 按 Ctrl+C 停止')
}

module.exports = { startProviderBackend, handleLLMRequest, handleTTSRequest }
