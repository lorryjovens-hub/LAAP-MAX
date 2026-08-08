/**
 * bridge-upload — 上传文件到 Agent Bridge 存储
 *
 * 接受 base64 编码的文件数据，存储到服务器 uploads 目录。
 * 返回文件路径供后续在消息中引用。Agent 可通过 read 工具读取。
 */

import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

export const name = "bridge-upload";
export const description = "上传文件到 Agent Bridge 存储。接受 base64 数据，返回可被 read 工具访问的文件路径。可在子 Agent（subagent）上下文中使用。";

export const parameters = {
  type: "object",
  properties: {
    channel: {
      type: "string",
      description: "关联的频道名称（可选），上传完成后自动在频道中发送一条带附件的消息",
    },
    filename: {
      type: "string",
      description: "文件名（含扩展名），例如 'screenshot.png'",
    },
    data: {
      type: "string",
      description: "文件内容的 base64 编码字符串",
    },
    caption: {
      type: "string",
      description: "可选的消息正文，随附件一起发送",
    },
  },
  required: ["filename", "data"],
};

export async function execute(input, ctx) {
  const store = ctx._agentBridge;
  if (!store) {
    return {
      content: [{ type: "text", text: "Agent Bridge 引擎未就绪。请确认插件已正确加载。" }],
    };
  }

  // 解析 base64 data（支持 data: URI 格式和纯 base64）
  let rawData = input.data;
  let mimeType = null;

  if (rawData.startsWith("data:")) {
    const match = rawData.match(/^data:([^;]+);base64,(.+)$/);
    if (match) {
      mimeType = match[1];
      rawData = match[2];
    }
  }

  // 生成安全文件名：加随机前缀防冲突
  const ext = path.extname(input.filename);
  const baseName = path.basename(input.filename, ext);
  const safeName = `${baseName}-${crypto.randomBytes(4).toString("hex")}${ext}`;

  // 确认存储路径
  // 优先使用 bridge store 所在目录旁的 uploads/，否则 fallback 到 uploads 目录
  let uploadDir;

  // 尝试从 bridge store 路径推断
  const storePath = ctx._agentBridgeStorePath;
  if (storePath) {
    uploadDir = path.join(path.dirname(storePath), "uploads");
  } else {
    // fallback: 使用插件 dataDir
    const { dataDir } = ctx;
    uploadDir = path.join(dataDir || process.cwd(), "uploads");
  }

  fs.mkdirSync(uploadDir, { recursive: true });
  const filePath = path.join(uploadDir, safeName);

  // 写入文件
  try {
    const buffer = Buffer.from(rawData, "base64");
    fs.writeFileSync(filePath, buffer);
  } catch (err) {
    return {
      content: [{ type: "text", text: `文件写入失败: ${err.message}` }],
    };
  }

  // 检测 MIME 类型（简单映射）
  if (!mimeType) {
    const mimeMap = {
      ".png": "image/png",
      ".jpg": "image/jpeg",
      ".jpeg": "image/jpeg",
      ".gif": "image/gif",
      ".webp": "image/webp",
      ".bmp": "image/bmp",
      ".svg": "image/svg+xml",
      ".pdf": "application/pdf",
      ".txt": "text/plain",
      ".json": "application/json",
      ".md": "text/markdown",
      ".html": "text/html",
    };
    mimeType = mimeMap[ext.toLowerCase()] || "application/octet-stream";
  }

  const result = {
    filePath,
    filename: safeName,
    originalName: input.filename,
    mimeType,
    size: fs.statSync(filePath).size,
  };

  // 如果指定了频道，自动发送带附件的消息
  if (input.channel) {
    const from = ctx.agentId || ctx.agentLabel || "unknown";
    const caption = input.caption || "";
    const attachmentText = caption
      ? `${caption}\n\n[附件: ${safeName}](${filePath})`
      : `[附件: ${safeName}](${filePath})`;

    store.postMessage(input.channel, from, attachmentText);
  }

  return {
    content: [{
      type: "text",
      text: `文件已上传 ✅\n\n` +
        `**文件名**: ${safeName}\n` +
        `**原始名**: ${input.filename}\n` +
        `**类型**: ${mimeType}\n` +
        `**大小**: ${(result.size / 1024).toFixed(1)} KB\n` +
        `**路径**: ${filePath}\n` +
        `${input.channel ? `**已发送到**: #${input.channel}\n` : ""}` +
        `\nAgent 可使用 read 工具查看此文件。`,
    }],
    details: result,
  };
}
