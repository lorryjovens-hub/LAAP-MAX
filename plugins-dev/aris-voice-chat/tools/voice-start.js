// Aris Voice Chat — 启动语音通话服务
// Agent 可调用：启动端到端语音对话后端

const BASE = "http://127.0.0.1:18080";

async function s2sStatus() {
  try {
    const r = await fetch(`${BASE}/voice-chat/api/status`);
    return await r.json();
  } catch { return { running: false, error: "插件路由不可达" }; }
}

export const name = 'aris_voice_start';
export const description = '启动端到端语音对话服务（Speech-to-Speech），让用户能与 Aris 实时语音交谈';
export const parameters = {
  type: 'object',
  properties: {}
};

export async function execute(args, ctx) {
  const st = await s2sStatus();
  if (st.running) {
    return { ok: true, running: true, message: "语音对话服务已在运行", url: st.url };
  }
  try {
    const r = await fetch(`${BASE}/voice-chat/api/start`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: "{}"
    });
    const d = await r.json();
    return { ok: d.ok, running: d.running, message: d.ok ? "语音对话服务启动中，首次需下载模型" : ("启动失败: " + (d.error || "未知")) };
  } catch (e) {
    return { ok: false, error: e.message };
  }
}