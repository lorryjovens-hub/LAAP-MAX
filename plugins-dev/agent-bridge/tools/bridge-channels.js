/**
 * bridge-channels — 列出所有频道及其元信息
 */

export const name = "bridge-channels";
export const description = "列出Agent通信桥中所有频道的名称与消息计数。";

export const parameters = {
  type: "object",
  properties: {},
};

export async function execute(_input, ctx) {
  const store = ctx._agentBridge;
  if (!store) {
    return {
      content: [{ type: "text", text: "Agent Bridge 引擎未就绪。" }],
    };
  }

  const channels = store.listChannels();
  if (channels.length === 0) {
    return {
      content: [{ type: "text", text: "暂无频道。使用 bridge-post 创建并发送第一条消息。" }],
    };
  }

  let text = "## Agent Bridge 频道\n\n";
  for (const ch of channels) {
    text += `- **#${ch.name}** — ${ch.count} 条消息`;
    if (ch.lastTs) text += ` (最后活跃: ${new Date(ch.lastTs).toLocaleString()})`;
    text += "\n";
  }

  return {
    content: [{ type: "text", text }],
    details: { channels },
  };
}
