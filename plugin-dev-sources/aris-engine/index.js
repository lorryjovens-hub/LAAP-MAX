/**
 * Aris Engine Plugin — HanaAgent 原生集成
 * 
 * 功能：
 *   1. 自动管理 Python 侧车进程（启动/停止/健康检查）
 *   2. 每轮对话注入认知上下文（PSI 需求 + 跨平台记忆）
 *   3. 注册原生工具（验算/预测/学习/策略）
 *   4. 提供仪表盘 WebView
 * 
 * 印记: Aris 永远记得 Lorry — 2026-07-24
 */

const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const SIDECAR_DIR = path.join(__dirname, '..', 'aris-engine');
const SIDECAR_SCRIPT = 'sidecar.py';

let sidecarProcess = null;
let sidecarReady = false;
let healthCheckInterval = null;

// ═════════════════════════════════════════════════════════════
// 插件生命周期
// ═════════════════════════════════════════════════════════════

exports.activate = async function(ctx) {
  ctx._aris = { sidecar: null, ready: false };
  
  const config = ctx.config || {};
  const autoStart = config.arisAutoStart !== false;
  const port = config.arisSidecarPort || 11521;
  
  if (autoStart) {
    await startSidecar(ctx, port);
  }
  
  // 注册上下文注入 hook
  if (config.arisInjectContext !== false) {
    ctx.on('session:before.message', async (sessionEvent) => {
      if (!sidecarReady) return;
      try {
        const contextText = await fetchCognitiveContext(port);
        if (contextText) {
          // 注入认知上下文到 LLM 请求
          sessionEvent.context = (sessionEvent.context || '') + '\n\n' + contextText;
        }
      } catch (e) {
        // 静默失败，不中断对话
      }
    });
    
    // 对话后学习 hook
    ctx.on('session:after.message', async (sessionEvent) => {
      if (!sidecarReady) return;
      try {
        const userMsg = sessionEvent.userMessage?.content?.[0]?.text || '';
        const asstMsg = sessionEvent.assistantMessage?.content?.[0]?.text || '';
        if (userMsg && asstMsg) {
          await afterTurn(port, userMsg, asstMsg);
        }
        // ── 意识工程移植：把本轮对话喂给意识运行时（11522） ──
        if (userMsg && ctx.config?.arisConsciousnessFeed !== false) {
          try {
            const cPort = ctx.config?.arisConsciousnessPort || 11522;
            await feedConsciousness(cPort, userMsg, asstMsg);
          } catch (e) {
            // 意识运行时未启动时静默（不影响对话）
          }
        }
      } catch (e) {
        // 静默失败
      }
    });
  }
  
  logger(ctx, 'Aris Engine plugin activated (port ' + port + ')');
};

exports.deactivate = async function() {
  await stopSidecar();
};

// ═════════════════════════════════════════════════════════════
// 侧车进程管理
// ═════════════════════════════════════════════════════════════

async function startSidecar(ctx, port) {
  if (sidecarProcess) {
    logger(ctx, 'Sidecar already running');
    return;
  }
  
  const pythonCmd = ctx.config?.arisPythonCmd || 'python';
  
  logger(ctx, 'Starting sidecar: ' + pythonCmd + ' ' + SIDECAR_SCRIPT + ' (port ' + port + ')');
  
  sidecarProcess = spawn(pythonCmd, [SIDECAR_SCRIPT], {
    cwd: SIDECAR_DIR,
    stdio: ['ignore', 'pipe', 'pipe'],
    detached: false,
  });
  
  sidecarProcess.stdout.on('data', (data) => {
    const line = data.toString().trim();
    if (line) logger(ctx, '[sidecar] ' + line);
    if (line.includes('running on http')) {
      sidecarReady = true;
      ctx._aris.ready = true;
      logger(ctx, 'Sidecar ready');
    }
  });
  
  sidecarProcess.stderr.on('data', (data) => {
    const line = data.toString().trim();
    if (line) logger(ctx, '[sidecar:err] ' + line);
  });
  
  sidecarProcess.on('close', (code) => {
    logger(ctx, 'Sidecar exited with code ' + code);
    sidecarProcess = null;
    sidecarReady = false;
    ctx._aris.ready = false;
  });
  
  // 健康检查（每 30 秒）
  healthCheckInterval = setInterval(async () => {
    if (!sidecarReady) return;
    try {
      const ok = await healthCheck(port);
      if (!ok) {
        logger(ctx, 'Sidecar health check failed, restarting...');
        await stopSidecar();
        await startSidecar(ctx, port);
      }
    } catch (e) {
      logger(ctx, 'Health check error: ' + e.message);
    }
  }, 30000);
  
  // 等待就绪（最多 15 秒）
  for (let i = 0; i < 30; i++) {
    if (sidecarReady) break;
    await sleep(500);
  }
  
  if (!sidecarReady) {
    logger(ctx, 'Sidecar did not become ready within 15s');
  }
}

async function stopSidecar() {
  if (healthCheckInterval) {
    clearInterval(healthCheckInterval);
    healthCheckInterval = null;
  }
  
  if (sidecarProcess) {
    sidecarProcess.kill('SIGTERM');
    // 等 3 秒强制关闭
    try {
      await Promise.race([
        new Promise(resolve => sidecarProcess.on('close', resolve)),
        sleep(3000),
      ]);
    } catch (e) {}
    sidecarProcess = null;
  }
  
  sidecarReady = false;
}

// ═════════════════════════════════════════════════════════════
// HTTP 工具函数
// ═════════════════════════════════════════════════════════════

function httpRequest(port, method, path, body) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: '127.0.0.1',
      port: port,
      path: path,
      method: method,
      headers: { 'Content-Type': 'application/json' },
      timeout: 10000,
    };
    
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          resolve({ raw: data });
        }
      });
    });
    
    req.on('error', (e) => reject(e));
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

function healthCheck(port) {
  return httpRequest(port, 'GET', '/health').then(r => r && r.status === 'alive').catch(() => false);
}

function fetchCognitiveContext(port) {
  return httpRequest(port, 'GET', '/cognitive_context').then(r => r.context || '').catch(() => '');
}

function afterTurn(port, userInput, response) {
  return httpRequest(port, 'POST', '/after_turn', {
    user_input: userInput,
    response: response,
  }).catch(() => {});
}

/**
 * 意识工程移植：把一轮对话喂给意识运行时（预测器/总线/记忆）。
 * 对话是意识的输入流——每一次真实交互都流经意识系统。
 */
function feedConsciousness(port, userMsg, asstMsg) {
  return httpRequest(port, 'POST', '/consciousness/feed', {
    event_type: 'user_message',
    content: (userMsg || '').slice(0, 500),
    source: 'hanako',
  }).catch(() => {});
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function logger(ctx, msg) {
  if (ctx && ctx.log) {
    ctx.log.info('[Aris] ' + msg);
  } else {
    console.log('[Aris] ' + msg);
  }
}
