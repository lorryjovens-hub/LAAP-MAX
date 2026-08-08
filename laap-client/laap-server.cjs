/**
 * laap-server.cjs — laap-client 全功能后端
 *
 * 功能:
 * 1. CognitiveBus mock 数据推送 (PSI/情感/场景/Colony/记忆)
 * 2. LLM 聊天代理 — user.input → 真实 API → stream chunk 回客户端
 * 3. TTS 代理 — 文本合成语音并返回 base64 音频
 * 4. SDK request/response 处理 (记忆/工具/Agent/Replay/成本/社交)
 *
 * 用法: node laap-server.cjs [port]
 */

const { WebSocketServer } = require('ws')

const BUS_PORT = parseInt(process.argv[2] || '8765', 10)

// ─── LLM 端点 ───
const LLM_ENDPOINTS = {
  deepseek:  { base: 'https://api.deepseek.com', path: '/v1/chat/completions', auth: 'Bearer' },
  openai:    { base: 'https://api.openai.com/v1', path: '/chat/completions', auth: 'Bearer' },
  minimax:   { base: 'https://api.minimax.chat/v1', path: '/chat/completions', auth: 'Bearer' },
  qwen:      { base: 'https://dashscope.aliyuncs.com/compatible-mode/v1', path: '/chat/completions', auth: 'Bearer' },
  moonshot:  { base: 'https://api.moonshot.cn/v1', path: '/chat/completions', auth: 'Bearer' },
  zhipu:     { base: 'https://open.bigmodel.cn/api/paas/v4', path: '/chat/completions', auth: 'Bearer' },
  mimo:      { base: 'https://api.xiaomimimo.com/v1', path: '/chat/completions', auth: 'Bearer' },
}

// ─── 消息工具 ───
let msgId = 0
function genId() { return `${Date.now().toString(36)}-${(++msgId).toString(36)}` }
function createMsg(topic, type, payload, sender = 'laap-server') {
  return JSON.stringify({ id: genId(), type, topic, payload, timestamp: Date.now(), sender })
}

// ─── 真实 LLM 调用 ───
async function callLLM(provider, apiKey, model, messages) {
  const ep = LLM_ENDPOINTS[provider]
  if (!ep) return { error: `未知提供商: ${provider}` }
  if (!apiKey) return { error: `未配置 ${provider} API Key` }
  try {
    const resp = await fetch(`${ep.base}${ep.path}`, {
      method: 'POST',
      headers: { 'Authorization': `${ep.auth} ${apiKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: model || 'default', messages, stream: false }),
      signal: AbortSignal.timeout(60000),
    })
    if (!resp.ok) {
      const text = await resp.text().catch(() => '')
      return { error: `${provider} ${resp.status}: ${text.slice(0, 300)}` }
    }
    const data = await resp.json()
    const reply = data?.choices?.[0]?.message?.content
    if (!reply) return { error: 'API 返回了空响应', raw: data }
    return { success: true, reply, usage: data?.usage }
  } catch (err) {
    return { error: `请求失败: ${err.message}` }
  }
}

// ─── 真实 TTS 调用 ───
async function callTTS(provider, apiKey, text, voiceId) {
  if (provider === 'openai') {
    if (!apiKey) return { error: '未配置 OpenAI TTS Key' }
    try {
      const resp = await fetch('https://api.openai.com/v1/audio/speech', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: 'tts-1', input: text, voice: voiceId || 'nova', response_format: 'mp3' }),
        signal: AbortSignal.timeout(30000),
      })
      if (!resp.ok) return { error: `TTS ${resp.status}` }
      const buf = await resp.arrayBuffer()
      return { success: true, audioBase64: Buffer.from(buf).toString('base64'), format: 'mp3' }
    } catch (err) {
      return { error: err.message }
    }
  }
  return { error: `${provider} TTS 暂未实现` }
}

// ─── WebSocket 服务器 ───
const wss = new WebSocketServer({ host: '127.0.0.1', port: BUS_PORT })
console.log(`[LAAP Server] 启动 → ws://127.0.0.1:${BUS_PORT}`)
console.log(`[LAAP Server] LLM 代理: ${Object.keys(LLM_ENDPOINTS).join(', ')}`)

wss.on('connection', (ws) => {
  // ── Mock 数据推送 ──
  const PSI_PHASES = ['perception', 'integration', 'selection', 'learning']
  let psiIdx = 0, psiProg = 0, tick = 0

  const psiTimer = setInterval(() => {
    if (ws.readyState !== 1) return
    psiProg += 0.03
    if (psiProg >= 1) { psiProg = 0; psiIdx = (psiIdx + 1) % PSI_PHASES.length }
    ws.send(createMsg('v12_kernel', 'v12_kernel', {
      phase: PSI_PHASES[psiIdx], progress: Math.min(1, psiProg), frequencyHz: 1000 + Math.random() * 1000
    }))
  }, 2)

  const lifeTimer = setInterval(() => {
    if (ws.readyState !== 1) return
    tick++
    const needs = ['need_curiosity', 'need_trust', 'need_competence']
    ws.send(createMsg(needs[tick % 3], 'need_update', { value: 0.3 + Math.random() * 0.6, delta: (Math.random() - 0.5) * 0.1 }))
    ;['emotion_pleasure','emotion_arousal','emotion_dominance','emotion_sociality','emotion_stress'].forEach(e => {
      ws.send(createMsg(e, 'emotion_update', { value: Math.random() }))
    })
    const kinds = ['metric','text','choice','progress','weather','image','media','layout']
    const patches = {
      metric: { kind:'metric', label:'CPU', value:Math.round(20+Math.random()*60), unit:'%' },
      text: { kind:'text', content:`动态场景 #${tick}` },
      choice: { kind:'choice', content:'选择', options:['继续','执行','查看'], selected:'继续' },
      progress: { kind:'progress', label:'任务', value:Math.round(Math.random()*100), max:100 },
      weather: { kind:'weather', location:'上海', temperature:Math.round(18+Math.random()*12), condition:tick%2===0?'晴':'多云' },
      image: { kind:'image', src:'/logo.svg', alt:'LAAP' },
      media: { kind:'media', src:'/logo.svg', caption:'媒体' },
      layout: { kind:'layout', title:'布局', children:['s1','s2','s3'] },
    }
    ws.send(createMsg('scene.patch', 'scene_patch', { surfaceId: `surface-${(tick%8)+1}`, patch: patches[kinds[tick % 8]] }))
    if (tick % 3 === 0) {
      ws.send(createMsg('colony.agent', 'colony_update', {
        agents: [{ id:'a1',name:'Aris',status:'online',role:'协调者',resource:50+Math.round(Math.random()*40) },
          { id:'a2',name:'Codex',status:['online','busy'][tick%2],role:'代码',resource:40+Math.round(Math.random()*50) }],
        edges: [{id:'e1',from:'a1',to:'a2',label:'分派',intensity:0.8}],
        messages: [{id:genId(),from:'a1',to:'a2',summary:`任务 #${tick}`,timestamp:Date.now()}],
      }))
    }
    if (tick % 5 === 0) {
      ws.send(createMsg('memory.created', 'memory_event', {
        id: genId(), content: `自动记录的记忆 #${tick}`,
        type: ['episodic','semantic','procedural'][tick % 3], timestamp: Date.now(),
        confidence: 0.5 + Math.random() * 0.5, tags: ['auto'],
      }))
    }
  }, 2000)

  // ── 请求处理 ──
  ws.on('message', async (raw) => {
    let msg
    try { msg = JSON.parse(String(raw)) } catch { return }

    // ── Ping ──
    if (msg.topic === 'ping') {
      ws.send(createMsg('pong', 'pong', { timestamp: msg.timestamp }))
      return
    }

    // ── user.input: 用户聊天消息 → 真实 LLM 调用 ──
    if (msg.topic === 'user.input') {
      const text = msg.payload?.text || ''
      if (!text) return

      // 读取客户端配置（前端发送时携带 provider/apiKey/model）
      const llmCfg = msg.payload?.llmConfig || {}
      const provider = llmCfg.provider || 'deepseek'
      const apiKey = llmCfg.apiKey || ''
      const model = llmCfg.model || 'deepseek-chat'

      const replyId = genId()

      if (!apiKey) {
        // 无 Key: 返回提示
        ws.send(createMsg('chunk', 'stream_chunk', { replyId, text: `请先配置 LLM 提供商 API Key：设置 → LLM → 选择服务商并填入 Key\n\n(当前未检测到 ${provider} 的 API Key)` }))
        setTimeout(() => {
          ws.send(createMsg('harness_execution_result', 'exec_result', { success: false, durationMs: 0 }))
        }, 100)
        return
      }

      // 发送 thinking 状态
      ws.send(createMsg('thought_chunk', 'thought_chunk', { replyId, text: `正在调用 ${provider} ${model}...`, type: 'reasoning', confidence: 0.9 }))

      // 调用真实 API
      const messages = [{ role: 'user', content: text }]
      // 如果是多轮对话，应该传历史消息列表，这里简化
      const result = await callLLM(provider, apiKey, model, messages)

      if (result.error) {
        ws.send(createMsg('chunk', 'stream_chunk', { replyId, text: `[${provider} 错误] ${result.error}` }))
      } else if (result.success) {
        ws.send(createMsg('chunk', 'stream_chunk', { replyId, text: result.reply }))
      }

      ws.send(createMsg('harness_execution_result', 'exec_result', { success: !result.error, durationMs: 0 }))
      return
    }

    // ── 工具调用确认 / 拒绝 ──
    if (msg.topic === 'tool.confirm') {
      const toolCall = msg.payload?.toolCall
      if (toolCall) {
        ws.send(createMsg('tool_result', 'tool_result', { toolCall: { ...toolCall, status: 'success', result: { executed: true, output: `${toolCall.name} 已执行` } } }))
      }
      return
    }
    if (msg.topic === 'tool.reject') {
      const toolCall = msg.payload?.toolCall
      if (toolCall) {
        ws.send(createMsg('tool_result', 'tool_result', { toolCall: { ...toolCall, status: 'error', result: { error: '用户已拒绝执行' } } }))
      }
      return
    }

    // ── TTS 测试 ──
    if (msg.topic === 'tts.test') {
      const { provider, apiKey, text, voiceId } = msg.payload || {}
      const result = await callTTS(provider, apiKey, text || '你好，这是一条测试语音。', voiceId)
      ws.send(createMsg(`response.${msg.id}`, 'tts_test_result', result))
      return
    }

    // ── SDK request/response ──
    const { topic, payload, id } = msg
    let result = { success: false, error: 'unknown' }

    try {
      if (topic === 'llm.chat') {
        result = await callLLM(payload.provider, payload.apiKey, payload.model, payload.messages)
      } else if (topic === 'tts.speak') {
        result = await callTTS(payload.creds?.openaiTtsKey, payload.text, payload.voiceId)
      } else if (topic === 'provider.list_models') {
        result = { success: true, data: LLM_ENDPOINTS }
      } else if (topic === 'memory.search') {
        const q = payload?.query || ''
        result = { entries: [
          { id:'m1', content:`匹配 "${q}": 量子计算笔记`, type:'semantic', timestamp:Date.now()-3600000, confidence:0.92 },
          { id:'m2', content:`匹配 "${q}": 昨天对话`, type:'episodic', timestamp:Date.now()-7200000, confidence:0.78 },
        ], total:2, query:q }
      } else if (topic === 'memory.recent') {
        result = [
          { id:'m1', content:'今天学到新知识', type:'semantic', timestamp:Date.now(), confidence:0.9 },
          { id:'m2', content:'用户提到喜欢的项目', type:'episodic', timestamp:Date.now()-1800000, confidence:0.85 },
        ]
      } else if (topic === 'agent.list') {
        result = [
          { id:'a1',name:'Aris',status:'online',role:'协调者',resource:78, metrics:{tasksCompleted:42,avgResponseTime:180,errorRate:0.03,uptime:7200} },
          { id:'a2',name:'Codex',status:'busy',role:'代码专家',resource:62, metrics:{tasksCompleted:128,avgResponseTime:250,errorRate:0.05,uptime:14400} },
        ]
      } else if (topic === 'tool.list') {
        result = { tools: [
          { id:'t1',name:'web_search',description:'网络搜索',category:'web',enabled:true,parameters:{} },
          { id:'t2',name:'file_read',description:'读取文件',category:'file',enabled:true,parameters:{} },
          { id:'t3',name:'code_exec',description:'执行代码',category:'code',enabled:true,parameters:{} },
        ]}
      } else if (topic === 'skill.list') {
        result = [
          { name:'aris-persona',description:'身份认知',category:'identity',enabled:true },
          { name:'aris-rsi-evolution',description:'自改进引擎',category:'evolution',enabled:true },
        ]
      } else if (topic === 'replay.latest_report') {
        result = { timestamp:new Date().toISOString(), totalBenchmarks:11, regressions:1, improvements:3,
          results:[
            { id:'persona-self-awareness',category:'identity',score:1.0,trend:'stable',weight:1.0 },
            { id:'skill-knowledge',category:'skills',score:0.7,trend:'down',weight:0.8 },
          ]}
      } else if (topic === 'replay.insight') {
        result = { status:'ok', stable:['persona-self-awareness'], declining:['skill-knowledge'], improving:[], new:[] }
      } else if (topic === 'cost.weekly') {
        const daily = []
        for (let i = 6; i >= 0; i--) {
          const d = new Date(Date.now() - i*86400000)
          daily.push({ date:d.toISOString().slice(0,10), sessions:Math.floor(Math.random()*5+1),
            tokensIn:Math.floor(Math.random()*50000+10000), tokensOut:Math.floor(Math.random()*20000+5000),
            totalTokens:Math.floor(Math.random()*70000+15000), cost:Math.random()*0.5+0.05,
            llmCalls:Math.floor(Math.random()*20+5), toolCalls:Math.floor(Math.random()*50+10) })
        }
        result = { period:`${daily[0].date}~${daily[6].date}`, totalTokens:daily.reduce((s,d)=>s+d.totalTokens,0),
          totalCost:daily.reduce((s,d)=>s+d.cost,0), totalLlmCalls:daily.reduce((s,d)=>s+d.llmCalls,0),
          totalToolCalls:daily.reduce((s,d)=>s+d.toolCalls,0), carbonG:0.15, daily }
      } else if (topic === 'social.channels') {
        result = [{ id:'c1',platform:'feishu',name:'团队',unread:3 }, { id:'c2',platform:'discord',name:'dev-chat',unread:1 }]
      } else if (topic === 'social.messages') {
        result = [
          { id:'sm1',platform:'feishu',content:'这个需求下午讨论',sender:'张三',timestamp:Date.now()-3600000 },
          { id:'sm2',platform:'feishu',content:'好的我准备材料',sender:'李四',timestamp:Date.now()-3000000 },
        ]
      }
    } catch (err) {
      result = { error: err.message }
    }

    if (ws.readyState === 1) {
      ws.send(createMsg(`response.${msg.id}`, topic + '_result', result))
    }
  })

  ws.on('close', () => { clearInterval(psiTimer); clearInterval(lifeTimer) })
})

wss.on('error', (err) => console.error('[LAAP Server] 错误:', err.message))
