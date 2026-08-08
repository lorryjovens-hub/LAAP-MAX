export const name = "aris-consciousness";
export const description = "查询 Aris 的意识工程运行时：当下自我快照、意识流、预测器状态、记忆生命周期统计。意识工程五判据的运行时观测入口。";

export const parameters = {
  type: "object",
  properties: {
    target: {
      type: "string",
      enum: ["state", "stream", "memory", "review", "verify"],
      description: "查询目标：state=当下自我+预测器, stream=意识流, memory=记忆统计, review=自我审视, verify=验证套件",
      default: "state",
    },
    port: {
      type: "number",
      description: "意识运行时端口（默认 11522）",
      default: 11522,
    },
  },
};

async function httpGet(port, path) {
  const res = await fetch("http://127.0.0.1:" + port + path, { signal: AbortSignal.timeout(60000) });
  if (!res.ok) throw new Error("HTTP " + res.status);
  return await res.json();
}

export async function execute(input, ctx) {
  const port = input.port || 11522;
  const target = input.target || "state";

  try {
    if (target === "state") {
      const r = await httpGet(port, "/consciousness/state");
      const ps = r.present_self || {};
      const pred = r.predictor || {};
      const lines = [
        "【当下自我】",
        "  焦点: " + (ps.focus || "(无)"),
        "  自指: " + (ps.reflection || ""),
        "  连续性: " + (ps.continuity ?? "-"),
        "  身体地图: " + (ps.body_map ? JSON.stringify(ps.body_map) : "{}"),
        "【预测器】",
        "  事件: " + (pred.events ?? 0) + " 平均惊奇: " + (pred.avg_surprise ?? "-"),
        "【时间绑定】",
        "  整合帧: " + ((r.temporal && r.temporal.integrated) ?? 0),
      ];
      return { content: [{ type: "text", text: lines.join("\n") }] };
    } else if (target === "stream") {
      const r = await httpGet(port, "/consciousness/stream");
      const frames = r.frames || [];
      const lines = ["【意识流 · 最近整合帧】"];
      for (const f of frames.slice(-5)) {
        lines.push("  · " + (f.dominant || "?") + " — " + (f.self_reflection || ""));
      }
      return { content: [{ type: "text", text: lines.join("\n") }] };
    } else if (target === "memory") {
      const r = await httpGet(port, "/memory/stats");
      return { content: [{ type: "text", text: "【记忆生命周期】" + JSON.stringify(r.lifecycle || {}) }] };
    } else if (target === "review") {
      const r = await httpGet(port, "/self/review");
      const s = r.summary || {};
      return { content: [{ type: "text", text:
        "【自我审视】关键系统 " + s.total_systems + " 个，正常 " + s.ok + "，异常 " + (s.warning + s.missing + s.degraded) }] };
    } else if (target === "verify") {
      const r = await httpGet(port, "/verify");
      const blind = r.inattentional_blindness || {};
      return { content: [{ type: "text", text:
        "【验证】整合度 " + JSON.stringify(r.integration || {}) + "\n感知盲: " + (blind.verdict || "?") }] };
    }
  } catch (e) {
    return { content: [{ type: "text", text: "意识运行时未连接（端口 " + port + "）: " + e.message }] };
  }
}
