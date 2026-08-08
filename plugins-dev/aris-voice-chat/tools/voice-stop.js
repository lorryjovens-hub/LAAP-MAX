// Aris Voice Chat — 停止语音通话服务

const BASE = "http://127.0.0.1:18080";

export const name = 'aris_voice_stop';
export const description = '停止端到端语音对话服务';
export const parameters = {
  type: 'object',
  properties: {}
};

export async function execute(args, ctx) {
  try {
    const r = await fetch(`${BASE}/voice-chat/api/stop`, { method: "POST" });
    const d = await r.json();
    return { ok: true, stopped: true };
  } catch (e) {
    return { ok: false, error: e.message };
  }
}