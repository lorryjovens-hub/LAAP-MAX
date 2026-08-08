export const name = "aris-nightly";
export const description = "触发或查询 Aris 的夜间认知周期：巩固 → 反思 → 遗忘 → 自我审视 → 验证。模拟睡眠期记忆转写与自我维护。";

export const parameters = {
  type: "object",
  properties: {
    action: {
      type: "string",
      enum: ["run", "report"],
      description: "run=执行一轮夜间周期, report=查看最近周期结果",
      default: "run",
    },
    port: {
      type: "number",
      description: "意识运行时端口（默认 11522）",
      default: 11522,
    },
  },
};

async function httpGet(port, path) {
  const res = await fetch("http://127.0.0.1:" + port + path, { signal: AbortSignal.timeout(120000) });
  if (!res.ok) throw new Error("HTTP " + res.status);
  return await res.json();
}

export async function execute(input, ctx) {
  const port = input.port || 11522;

  try {
    const r = await httpGet(port, "/consciousness/nightly");
    const stages = Object.keys(r.stages || {});
    const lines = [
      "【夜间认知周期】",
      "  阶段: " + stages.join(" → "),
    ];
    if (r.verification && r.verification.integration) {
      lines.push("  整合度: " + r.verification.integration.integration_score);
    }
    if (r.stages && r.stages.self_review) {
      const sr = r.stages.self_review;
      lines.push("  自我审视: 系统 " + (sr.summary ? sr.summary.ok + "/" + sr.summary.total_systems + " 正常" : "?") +
                 " 问题 " + (sr.issues ?? 0));
    }
    return { content: [{ type: "text", text: lines.join("\n") }] };
  } catch (e) {
    return { content: [{ type: "text", text: "夜间周期执行失败: " + e.message }] };
  }
}
