/**
 * bridge-post — 发送消息到频道（支持文本+附件）
 *
 * 可在任意Agent上下文（包括subagent）中调用。
 * 替代被subagent封锁的 channel/post 功能。
 */

export const name = "bridge-post";
export const description = "发送消息到Agent通信桥频道。支持文本+附件。可在子Agent（subagent）上下文中使用。";

export const parameters = {
  type: "object",
  properties: {
    channel: {
      type: "string",
      description: "频道名称，例如 '三体通讯'",
    },
    content: {
      type: "string",
      description: "消息正文。支持 @提及 标记",
    },
    attachments: {
      type: "array",
      description: "可选，附件列表（文件路径、上传ID等）",
      items: {
        type: "object",
        properties: {
          path: { type: "string", description: "文件绝对路径" },
          type: { type: "string", description: "MIME 类型，如 image/png" },
          name: { type: "string", description: "显示名称" },
        },
        required: ["path"],
      },
    },
    from: {
      type: "string",
      description: "发送者标识。留空则自动填入当前Agent信息",
    },
  },
  required: ["channel"],
};

export async function execute(input, ctx) {
  const store = ctx._agentBridge;
  if (!store) {
    return {
      content: [{ type: "text", text: "Agent Bridge 引擎未就绪。请确认插件已正确加载。" }],
    };
  }

  const from = input.from || ctx.agentId || ctx.agentLabel || "unknown";

  // 构建消息内容
  let messageContent = input.content || "";
  const attachments = input.attachments || [];

  if (attachments.length > 0) {
    const attachLines = attachments.map((a, i) => {
      const name = a.name || a.path.split(/[\\/]/).pop();
      const typeInfo = a.type ? ` (${a.type})` : "";
      return `  [${i + 1}] ${name}${typeInfo} — \`${a.path}\``;
    });

    if (messageContent) {
      messageContent += "\n\n---\n";
    }
    messageContent += "**附件:**\n" + attachLines.join("\n");
  }

  if (!messageContent.trim()) {
    messageContent = "_（附件消息）_";
  }

  const msg = store.postMessage(input.channel, from, messageContent);

  if (attachments.length > 0 && msg) {
    msg.attachments = attachments;
    try {
      store._persist?.();
    } catch {}
  }

  let response = `[桥] → #${input.channel}\n\n` +
    `**来自**: ${msg.from}\n` +
    `**时间**: ${new Date(msg.ts).toLocaleString()}\n`;

  if (input.content) {
    response += `**正文**: ${input.content}\n`;
  }
  if (attachments.length > 0) {
    response += `**附件**: ${attachments.length} 个\n`;
  }
  response += `**消息ID**: \`${msg.id}\``;

  return {
    content: [{ type: "text", text: response }],
    details: { message: msg, attachments },
  };
}
