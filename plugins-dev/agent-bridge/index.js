/**
 * Agent Bridge 插件主入口
 *
 * 为主session和subagent之间提供消息通道。
 * 使用文件持久化存储，所有session共享同一存储。
 */

import fs from "node:fs";
import path from "node:path";

export default class AgentBridgePlugin {
  async onload() {
    const { dataDir, log } = this.ctx;

    // 存储目录：优先使用用户配置，否则用dataDir
    const storeDir = await readConfig(this.ctx, "bridgeDataDir", "") || dataDir;
    fs.mkdirSync(storeDir, { recursive: true });

    const storePath = path.join(storeDir, "bridge-store.json");

    // 消息存储引擎
    const store = {
      _init: false,
      _data: { channels: {} },

      _persist() {
        try {
          fs.writeFileSync(storePath, JSON.stringify(this._data, null, 2), "utf-8");
        } catch (err) {
          log.warn(`[Agent Bridge] persist failed: ${err.message}`);
        }
      },

      _load() {
        try {
          if (fs.existsSync(storePath)) {
            const raw = fs.readFileSync(storePath, "utf-8");
            this._data = JSON.parse(raw);
          }
        } catch (err) {
          log.warn(`[Agent Bridge] load failed: ${err.message}, starting fresh`);
          this._data = { channels: {} };
        }
        // 确保 channels 存在
        if (!this._data.channels) this._data.channels = {};
        this._init = true;
      },

      ensureChannel(name) {
        if (!this._data.channels[name]) {
          this._data.channels[name] = { messages: [] };
        }
        return this._data.channels[name];
      },

      postMessage(channel, from, content) {
        if (!this._init) this._load();
        const ch = this.ensureChannel(channel);
        const msg = {
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          from,
          content,
          ts: new Date().toISOString(),
        };
        ch.messages.push(msg);
        this._persist();
        return msg;
      },

      getMessages(channel, since = null) {
        if (!this._init) this._load();
        const ch = this._data.channels[channel];
        if (!ch) return [];
        if (!since) return ch.messages;
        return ch.messages.filter((m) => m.id > since);
      },

      listChannels() {
        if (!this._init) this._load();
        return Object.entries(this._data.channels).map(([name, ch]) => ({
          name,
          count: ch.messages.length,
          lastTs: ch.messages.length > 0 ? ch.messages[ch.messages.length - 1].ts : null,
        }));
      },

      getChannelInfo(name) {
        if (!this._init) this._load();
        const ch = this._data.channels[name];
        if (!ch) return null;
        return { name, count: ch.messages.length };
      },
    };

    // 启动时载入
    store._load();

    // 挂载到运行时上下文，工具通过 ctx._agentBridge 访问
    this.ctx._agentBridge = store;

    this.register(() => {
      store._persist();
      delete this.ctx._agentBridge;
      log.info("[Agent Bridge] 引擎已关闭");
    });

    log.info(`[Agent Bridge] 已启动 — 存储路径: ${storePath}`);
  }
}

async function readConfig(ctx, key, fallback) {
  try {
    const value = await ctx.config?.get?.(key);
    return value ?? fallback;
  } catch {
    return fallback;
  }
}
