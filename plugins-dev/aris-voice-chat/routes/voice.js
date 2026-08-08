// Aris Voice Chat — 端到端语音对话后端管理
// 管理 HuggingFace speech-to-speech 子进程生命周期
import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import net from "node:net";

const S2S_PORT = 8765;
const WS_PATH = "/v1/realtime";

// 全局单例子进程句柄
let s2sProcess = null;
let s2sLogBuffer = [];
let s2sStartedAt = null;
let s2sConfig = {};

function logLine(tag, line) {
  const ts = new Date().toISOString();
  s2sLogBuffer.push({ ts, tag, line });
  if (s2sLogBuffer.length > 500) s2sLogBuffer.shift();
}

function isPortOpen(port) {
  return new Promise((resolve) => {
    const sock = net.connect({ port, host: "127.0.0.1", timeout: 1500 });
    sock.on("connect", () => { sock.destroy(); resolve(true); });
    sock.on("error", () => resolve(false));
    sock.on("timeout", () => { sock.destroy(); resolve(false); });
  });
}

async function bridgeStatus() {
  const open = await isPortOpen(S2S_PORT);
  return {
    running: open,
    port: S2S_PORT,
    url: open ? `ws://127.0.0.1:${S2S_PORT}${WS_PATH}` : null,
    startedAt: s2sStartedAt,
    config: s2sConfig,
    log: s2sLogBuffer.slice(-50)
  };
}

function buildArgs(cfg) {
  const args = ["serve", "--host", "127.0.0.1", "--port", String(cfg.port || S2S_PORT)];
  if (cfg.sttBackend) args.push("--stt", cfg.sttBackend);
  if (cfg.llmBackend) args.push("--llm_backend", cfg.llmBackend);
  if (cfg.modelName) args.push("--model_name", cfg.modelName);
  if (cfg.ttsBackend) args.push("--tts", cfg.ttsBackend);
  if (cfg.language) args.push("--language", cfg.language);
  if (cfg.voice) args.push("--qwen3_tts_speaker", cfg.voice);
  if (cfg.responsesApiBaseUrl) args.push("--responses_api_base_url", cfg.responsesApiBaseUrl);
  if (cfg.responsesApiApiKey) args.push("--responses_api_api_key", cfg.responsesApiApiKey);
  args.push("--enable_live_transcription");
  return args;
}

export default function registerRoutes(app, ctx) {
  // 页面
  app.get("/voice-chat", async (c) => {
    const htmlPath = path.join(ctx.pluginDir, "page", "index.html");
    try { return c.html(await fs.readFile(htmlPath, "utf-8")); }
    catch { return c.text("Not found", 404); }
  });

  // 状态
  app.get("/voice-chat/api/status", async (c) => {
    return c.json(await bridgeStatus());
  });

  // 启动服务
  app.post("/voice-chat/api/start", async (c) => {
    try {
      const body = await c.req.json().catch(() => ({}));
      const cfg = { ...s2sConfig, ...body };
      s2sConfig = {
        port: cfg.s2sPort || S2S_PORT,
        sttBackend: cfg.sttBackend || "faster-whisper",
        llmBackend: cfg.llmBackend || "responses-api",
        modelName: cfg.modelName || "deepseek-chat",
        ttsBackend: cfg.ttsBackend || "qwen3",
        language: cfg.language || "zh",
        voice: cfg.voice || "Aiden",
        responsesApiBaseUrl: cfg.responsesApiBaseUrl || "",
        responsesApiApiKey: cfg.responsesApiApiKey || process.env.DEEPSEEK_API_KEY || ""
      };

      if (s2sProcess) {
        return c.json({ ok: true, alreadyRunning: true, ...(await bridgeStatus()) });
      }

      const args = buildArgs(s2sConfig);
      logLine("sys", `启动: speech-to-speech ${args.join(" ")}`);

      const fullPath = "speech-to-speech";
      s2sProcess = spawn(fullPath, args, {
        env: { ...process.env, OPENAI_API_KEY: s2sConfig.responsesApiApiKey || process.env.OPENAI_API_KEY || "not-needed" },
        shell: false
      });

      s2sStartedAt = new Date().toISOString();

      s2sProcess.stdout.on("data", (d) => String(d).split("\n").forEach((l) => l.trim() && logLine("out", l)));
      s2sProcess.stderr.on("data", (d) => String(d).split("\n").forEach((l) => l.trim() && logLine("err", l)));
      s2sProcess.on("exit", (code) => {
        logLine("sys", `服务退出 code=${code}`);
        s2sProcess = null;
        s2sStartedAt = null;
      });
      s2sProcess.on("error", (e) => {
        logLine("err", `spawn error: ${e.message}`);
        if (s2sProcess === null) s2sProcess = null;
        s2sProcess = null;
        s2sStartedAt = null;
      });

      return c.json({ ok: true, ...(await bridgeStatus()) });
    } catch (e) {
      return c.json({ ok: false, error: e.message }, 500);
    }
  });

  // 停止服务
  app.post("/voice-chat/api/stop", async (c) => {
    if (!s2sProcess) return c.json({ ok: true, alreadyStopped: true });
    s2sProcess.kill();
    logLine("sys", "发送停止信号");
    return c.json({ ok: true });
  });

  // 日志
  app.get("/voice-chat/api/logs", async (c) => {
    return c.json({ log: s2sLogBuffer });
  });
}