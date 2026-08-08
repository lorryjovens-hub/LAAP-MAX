// Aris Voice Chat — 查询语音服务状态

const BASE = "http://127.0.0.1:18080";

export const name = 'aris_voice_status';
export const description = '查询端到端语音对话服务的运行状态';
export const parameters = { type: 'object', properties: {} };

export async function execute(args, ctx) {
  try {
    const r = await fetch(`${BASE}/voice-chat/api/status`);
    const d = await r.json();
    return { ok: true, running: d.running, port: d.port, url: d.url, config: d.config };
  } catch (e) {
    return { ok: false, running: false, error: e.message };
  }
}