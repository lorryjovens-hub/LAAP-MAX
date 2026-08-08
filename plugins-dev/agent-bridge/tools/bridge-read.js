/**
 * bridge-read — 读取频道消息
 *
 * 可在任意Agent上下文（包括subagent）中调用。
 * 替代被subagent封锁的 channel/read 功能。
 */

export const name = "bridge-read";
export const description = "读取Agent通信桥频道中的消息。支持 since 参数增量拉取。可在子Agent（subagent）上下文中使用。";

export const parameters = {
  type: "object",
  properties: {
    channel: {
      type: "string",
      description: "频道名称，例如 '三体通讯'。不传则列出所有频道",
    },
    since: {
      type: "string",
      description: "可选的消息ID，只返回此ID之后的新消息（增量拉取）",
    },
    limit: {
      type: "number",
      description: "返回消息最大条数，默认 50",
      default: 50,
    },
  },
};

export async function execute(input, ctx) {
  const store = ctx._agentBridge;
  if (!store) {
    return {
      content: [{ type: "text", text: "Agent Bridge 引擎未就绪。请确认插件已正确加载。" }],
    };
  }

  if (!input.channel) {
    // 列出所有频道
    const channels = store.listChannels();
    if (channels.length === 0) {
      return {
        content: [{ type: "text", text: "暂无频道。使用 bridge-post 创建并发送第一条消息。" }],
      };
    }
    let text = "## Agent Bridge 频道列表\n\n";
    for (const ch of channels) {
      text += `- **#${ch.name}** — ${ch.count} 条消息`;
      if (ch.lastTs) text += ` (最后: ${new Date(ch.lastTs).toLocaleString()})`;
      text += "\n";
    }
    return { content: [{ type: "text", text }], details: { channels } };
  }

  const messages = store.getMessages(input.channel, input.since || null);
  if (messages.length === 0) {
    return {
      content: [{ type: "text", text: `#${input.channel} 暂无消息${input.since ? " (自上次拉取后无新消息)" : ""}。` }],
    };
  }

  const limit = input.limit || 50;
  const sliced = messages.slice(-limit);

  // 格式化消息列表
  let text = `## #${input.channel}\n\n`;
  text += `共 ${messages.length} 条消息，显示最近 ${sliced.length} 条\n\n`;
  text += "---\n\n";

  for (const msg of sliced) {
    const time = new Date(msg.ts).toLocaleString();
    text += `**${msg.from}** · ${time}\n`;
    text += `> ${msg.content}\n\n`;
    text += `_ID: \`${msg.id}\`_\n\n---\n\n`;
  }

  // 返回最新的消息ID供后续增量拉取
  const lastId = messages[messages.length - 1].id;

  return {
    content: [{ type: "text", text }],
    details: { messages: sliced, lastId },
  };
}
