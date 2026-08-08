/**
 * laap-mock-server.js — 独立运行，零依赖
 * 模拟 CognitiveBus WebSocket 后端，为 laap-client 提供测试数据
 *
 * 用法: node laap-mock-server.js
 * 端口: 8765 (默认)
 */

const { WebSocketServer } = require('ws')

const PORT = parseInt(process.argv[2] || '8765', 10)
const PSI_PHASES = ['perception', 'integration', 'selection', 'learning']

let msgId = 0
function genId() { return `${Date.now().toString(36)}-${(++msgId).toString(36)}` }
function createMsg(topic, type, payload, sender = 'mock-backend') {
  return JSON.stringify({ id: genId(), type, topic, payload, timestamp: Date.now(), sender })
}

function generateBeepWavBase64() {
  const sampleRate = 8000, duration = 1, freq = 440, numSamples = sampleRate * duration
  const buf = Buffer.alloc(44 + numSamples * 2)
  buf.write('RIFF', 0); buf.writeUInt32LE(36 + numSamples * 2, 4)
  buf.write('WAVE', 8); buf.write('fmt ', 12)
  buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20); buf.writeUInt16LE(1, 22)
  buf.writeUInt32LE(sampleRate, 24); buf.writeUInt32LE(sampleRate * 2, 28)
  buf.writeUInt16LE(2, 32); buf.writeUInt16LE(16, 34); buf.write('data', 36)
  buf.writeUInt32LE(numSamples * 2, 40)
  for (let i = 0; i < numSamples; i++) {
    const s = Math.sin(2 * Math.PI * freq * (i / sampleRate)) * 0.5
    buf.writeInt16LE(Math.max(-32768, Math.min(32767, s * 32767)), 44 + i * 2)
  }
  return buf.toString('base64')
}

const colonyAgents = [
  { id: 'a1', name: 'Aris', status: 'online', role: '协调者', resource: 78 },
  { id: 'a2', name: 'Codex', status: 'busy', role: '代码专家', resource: 62 },
  { id: 'a3', name: 'Guardian', status: 'offline', role: '安全审查', resource: 0 },
  { id: 'a4', name: 'Nexus', status: 'online', role: '记忆检索', resource: 55 },
]
const colonyEdges = [
  { id: 'e1', from: 'a1', to: 'a2', label: '任务分派', intensity: 0.8 },
  { id: 'e2', from: 'a2', to: 'a3', label: '代码审查', intensity: 0.5 },
  { id: 'e3', from: 'a3', to: 'a1', label: '报告风险', intensity: 0.3 },
]
const colonyMsgTemplates = [
  { from: 'a1', to: 'a2', summary: '请优化推理链' },
  { from: 'a2', to: 'a3', summary: '请求安全审计' },
  { from: 'a3', to: 'a1', summary: '发现潜在风险' },
]

const wss = new WebSocketServer({ host: '127.0.0.1', port: PORT })
console.log(`[MockServer] CognitiveBus 模拟后端启动 → ws://127.0.0.1:${PORT}`)

wss.on('connection', (ws) => {
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

    // Needs
    const needs = ['need_curiosity', 'need_trust', 'need_competence']
    const nt = needs[tick % 3]
    ws.send(createMsg(nt, 'need_update', { value: 0.3 + Math.random() * 0.6, delta: (Math.random() - 0.5) * 0.1 }))

    // Emotions
    ;['emotion_pleasure','emotion_arousal','emotion_dominance','emotion_sociality','emotion_stress'].forEach(e => {
      ws.send(createMsg(e, 'emotion_update', { value: Math.random() }))
    })

    // Scene patch
    const kinds = ['metric','text','choice','progress','weather','image','media','layout']
    const kind = kinds[tick % 8]
    const patches = {
      metric: { kind:'metric', label:'CPU', value:Math.round(20+Math.random()*60), unit:'%' },
      text: { kind:'text', content:`动态场景内容 #${tick}` },
      choice: { kind:'choice', content:'选择操作', options:['继续','执行','查看'], selected:'继续' },
      progress: { kind:'progress', label:'任务', value:Math.round(Math.random()*100), max:100 },
      weather: { kind:'weather', location:'上海', temperature:Math.round(18+Math.random()*12), condition:tick%2===0?'晴':'多云' },
      image: { kind:'image', src:'/logo.svg', alt:'LAAP' },
      media: { kind:'media', src:'/logo.svg', caption:'媒体' },
      layout: { kind:'layout', title:'主布局', children:['s1','s2','s3'] },
    }
    ws.send(createMsg('scene.patch', 'scene_patch', { surfaceId: `surface-${(tick%8)+1}`, patch: patches[kind] }))

    // Colony
    colonyAgents.forEach(a => {
      if (Math.random() > 0.7) a.status = ['online','busy','offline'][Math.floor(Math.random()*3)]
      a.resource = Math.max(0, Math.min(100, (a.resource||50) + Math.round((Math.random()-0.5)*10)))
    })
    const cm = colonyMsgTemplates[tick % colonyMsgTemplates.length]
    ws.send(createMsg('colony.agent', 'colony_update', {
      agents: colonyAgents.map(a => ({...a})),
      edges: colonyEdges.map(e => ({...e})),
      messages: [{ id: genId(), ...cm, timestamp: Date.now() }],
    }))

    // Memory created (every 5 ticks)
    if (tick % 5 === 0) {
      ws.send(createMsg('memory.created', 'memory_event', {
        id: genId(), content: `自动记录的记忆 #${tick} — 由系统在 tick ${tick} 时生成。`,
        type: ['episodic','semantic','procedural'][tick % 3],
        timestamp: Date.now(), confidence: 0.5 + Math.random() * 0.5, tags: ['auto', 'system'],
      }))
    }

    // Tool list (every 10 ticks)
    if (tick % 10 === 0) {
      ws.send(createMsg('response.tool_list', 'tool_list', {
        tools: [
          { id: 't1', name: 'web_search', description: '网络搜索', category: 'web', enabled: true, parameters: {} },
          { id: 't2', name: 'file_read', description: '读取文件', category: 'file', enabled: true, parameters: {} },
          { id: 't3', name: 'code_exec', description: '执行代码', category: 'code', enabled: false, parameters: {} },
          { id: 't4', name: 'memory_search', description: '记忆检索', category: 'memory', enabled: true, parameters: {} },
        ]
      }))
    }
  }, 2000)

  // Handle incoming messages
  ws.on('message', (raw) => {
    let msg; try { msg = JSON.parse(String(raw)) } catch { return }
    
    if (msg.topic === 'ping') {
      ws.send(createMsg('pong', 'pong', { timestamp: msg.timestamp }))
    } else if (msg.topic === 'memory.search') {
      const q = msg.payload?.query || ''
      ws.send(createMsg(`response.${msg.id}`, 'memory_search_result', {
        entries: [
          { id: 'm1', content: `记忆匹配 "${q}": 关于量子计算的笔记`, type: 'semantic', timestamp: Date.now()-3600000, confidence: 0.92, tags: ['量子','AI'] },
          { id: 'm2', content: `记忆匹配 "${q}": 昨天的对话记录`, type: 'episodic', timestamp: Date.now()-7200000, confidence: 0.78, tags: ['对话'] },
          { id: 'm3', content: `记忆匹配 "${q}": 技能使用流程`, type: 'procedural', timestamp: Date.now()-86400000, confidence: 0.65, tags: ['技能'] },
        ], total: 3, query: q,
      }))
    } else if (msg.topic === 'memory.recent') {
      ws.send(createMsg(`response.${msg.id}`, 'memory_recent', [
        { id: 'm1', content: '今天学到的新知识', type: 'semantic', timestamp: Date.now(), confidence: 0.9 },
        { id: 'm2', content: '用户提到喜欢的项目', type: 'episodic', timestamp: Date.now()-1800000, confidence: 0.85 },
        { id: 'm3', content: '系统自动整理的工作流', type: 'procedural', timestamp: Date.now()-3600000, confidence: 0.7 },
      ]))
    } else if (msg.topic === 'agent.list') {
      ws.send(createMsg(`response.${msg.id}`, 'agent_list', colonyAgents.map(a => ({
        ...a, metrics: { tasksCompleted: Math.floor(Math.random()*100), avgResponseTime: Math.floor(Math.random()*500+100), errorRate: Math.random()*0.1, uptime: Math.floor(Math.random()*86400) }
      }))))
    } else if (msg.topic === 'tool.list' || msg.topic === 'tool_list') {
      ws.send(createMsg(`response.${msg.id || 'tool_list'}`, 'tool_list', {
        tools: [
          { id: 't1', name: 'web_search', description: '网络搜索引擎', category: 'web', enabled: true, parameters: {} },
          { id: 't2', name: 'file_read', description: '读取本地文件', category: 'file', enabled: true, parameters: {} },
          { id: 't3', name: 'code_exec', description: '执行 Python 代码', category: 'code', enabled: true, parameters: {} },
          { id: 't4', name: 'memory_search', description: '搜索记忆库', category: 'memory', enabled: true, parameters: {} },
        ]
      }))
    } else if (msg.topic === 'skill.list') {
      ws.send(createMsg(`response.${msg.id}`, 'skill_list', [
        { name: 'aris-persona', description: 'Aris 身份与认知架构', category: 'identity', enabled: true },
        { name: 'aris-rsi-evolution', description: '递归自改进引擎', category: 'evolution', enabled: true },
        { name: 'flutter-app-development', description: 'Flutter 开发', category: 'development', enabled: false },
        { name: 'python-fastapi-backend', description: 'FastAPI 后端开发', category: 'development', enabled: true },
      ]))
    } else if (msg.topic === 'replay.latest_report') {
      ws.send(createMsg(`response.${msg.id}`, 'replay_report', {
        timestamp: new Date().toISOString(), totalBenchmarks: 11, regressions: 1, improvements: 3,
        results: [
          { id: 'persona-self-awareness', category: 'identity', score: 1.0, trend: 'stable', weight: 1.0 },
          { id: 'persona-creator', category: 'identity', score: 1.0, trend: 'stable', weight: 1.0 },
          { id: 'memory-personal', category: 'memory', score: 0.8, trend: 'stable', weight: 1.0 },
          { id: 'tool-file-read', category: 'tools', score: 0.9, trend: 'up', weight: 1.0 },
          { id: 'skill-knowledge', category: 'skills', score: 0.7, trend: 'down', weight: 0.8 },
          { id: 'code-understanding-python', category: 'code', score: 0.85, trend: 'stable', weight: 0.8 },
          { id: 'harness-self-awareness', category: 'harness', score: 0.6, trend: 'up', weight: 0.7 },
        ]
      }))
    } else if (msg.topic === 'replay.insight') {
      ws.send(createMsg(`response.${msg.id}`, 'replay_insight', {
        status: 'ok', stable: ['persona-self-awareness','persona-creator','memory-personal','code-understanding-python'],
        declining: ['skill-knowledge'], improving: ['tool-file-read','harness-self-awareness'], new: [],
      }))
    } else if (msg.topic === 'cost.weekly') {
      const daily = []
      for (let i = 6; i >= 0; i--) {
        const d = new Date(Date.now() - i*86400000)
        daily.push({ date: d.toISOString().slice(0,10), sessions: Math.floor(Math.random()*5+1),
          tokensIn: Math.floor(Math.random()*50000+10000), tokensOut: Math.floor(Math.random()*20000+5000),
          totalTokens: Math.floor(Math.random()*70000+15000), cost: Math.random()*0.5+0.05,
          llmCalls: Math.floor(Math.random()*20+5), toolCalls: Math.floor(Math.random()*50+10) })
      }
      ws.send(createMsg(`response.${msg.id}`, 'cost_weekly', {
        period: `${daily[0].date} ~ ${daily[6].date}`, totalTokens: daily.reduce((s,d)=>s+d.totalTokens,0),
        totalCost: daily.reduce((s,d)=>s+d.cost,0), totalLlmCalls: daily.reduce((s,d)=>s+d.llmCalls,0),
        totalToolCalls: daily.reduce((s,d)=>s+d.toolCalls,0), carbonG: daily.reduce((s,d)=>s+d.totalTokens,0)*0.00015,
        daily,
      }))
    } else if (msg.topic === 'social.channels') {
      ws.send(createMsg(`response.${msg.id}`, 'social_channels', [
        { id: 'c1', platform: 'feishu', name: '团队讨论', unread: 3, lastMessage: '下午开会' },
        { id: 'c2', platform: 'discord', name: 'dev-chat', unread: 1, lastMessage: 'PR approved' },
        { id: 'c3', platform: 'wechat', name: '项目群', unread: 0 },
      ]))
    } else if (msg.topic === 'social.messages') {
      ws.send(createMsg(`response.${msg.id}`, 'social_messages', [
        { id: 'sm1', platform: 'feishu', content: '这个需求我们下午讨论一下', sender: '张三', timestamp: Date.now()-3600000, channelId: 'c1' },
        { id: 'sm2', platform: 'feishu', content: '好的，我准备一下材料', sender: '李四', timestamp: Date.now()-3000000, channelId: 'c1' },
        { id: 'sm3', platform: 'feishu', content: '新版本已经发布了', sender: '王五', timestamp: Date.now()-1800000, channelId: 'c1' },
      ]))
    }
  })

  ws.on('close', () => { clearInterval(psiTimer); clearInterval(lifeTimer) })
})

wss.on('error', (err) => console.error('[MockServer] 错误:', err.message))
