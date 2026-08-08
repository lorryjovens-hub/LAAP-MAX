#!/usr/bin/env node
/*
 * LAAP Remote Bridge — desktop LAAP agent <-> mobile/LAN remote control.
 * =====================================================================
 *
 * Spawns the desktop LAAP agent (pi.exe --mode rpc, with the aris-laap
 * extension auto-loaded from ~/.pi/agent/extensions) and exposes it over
 * plain HTTP + Server-Sent Events so a phone on the same LAN can control
 * the desktop LAAP: send prompts, run bash, read state, watch the event
 * stream in real time.
 *
 * Protocol to pi (JSONL over stdin/stdout — see pi docs/rpc.md):
 *   -> {"id":"req-1","type":"prompt","message":"..."}
 *   <- {"id":"req-1","type":"response","command":"prompt","success":true}
 *   <- {"id":"req-1","type":"event","data":{...}}   (streaming events)
 *
 * HTTP surface (bound to 0.0.0.0 so phones can reach it):
 *   GET  /                 -> mobile control UI (control.html)
 *   GET  /api/status       -> bridge + agent state (JSON)
 *   POST /api/command      -> { type, id?, message?, ... } -> forward to pi
 *   GET  /api/events       -> SSE stream of agent events
 *
 * Optional auth: set LAAP_BRIDGE_TOKEN to require ?token=<token> on calls.
 *
 * Usage:
 *   node remote-bridge.js [--port 8791]
 *
 * Env overrides:
 *   LAAP_PI_EXE    path to the pi binary     (default D:\LAAP\Pi\pi-windows-x64\pi.exe)
 *   LAAP_PI_MODEL  model to use              (default deepseek-v4-flash)
 *   LAAP_BRIDGE_TOKEN  require a token       (default none)
 */
"use strict";

const http = require("http");
const os = require("os");
const path = require("path");
const fs = require("fs");
const { spawn } = require("child_process");
const { URL } = require("url");
const crypto = require("crypto");

const HOST = "0.0.0.0";
const PORT = Number(process.argv[process.argv.indexOf("--port") + 1]) || 8791;

const PI_EXE = process.env.LAAP_PI_EXE || "D:\\LAAP\\Pi\\pi-windows-x64\\pi.exe";
const PI_CWD = path.dirname(PI_EXE);
const PI_MODEL = process.env.LAAP_PI_MODEL || "deepseek-v4-flash";
const BRIDGE_TOKEN = process.env.LAAP_BRIDGE_TOKEN || "";

const PUBLIC_DIR = path.join(__dirname, "public");

// ── Tiny JSONL client to the pi RPC subprocess ────────────────────────
class PiRpc {
  constructor() {
    this.proc = null;
    this.buf = "";
    this.seq = 0;
    this.pending = new Map(); // id -> {resolve, reject, timer}
    this.events = [];         // rolling event buffer for late SSE joiners
    this.maxEvents = 200;
    this.listeners = new Set(); // SSE/WS subscribers (fn(eventLine))
    this.status = { running: false, model: null, streaming: false };
    this.lastState = null;
  }

  start() {
    if (this.proc) return;
    const args = ["--mode", "rpc", "--model", PI_MODEL, "--no-session"];
    this.status.running = false;
    /* eslint-disable-next-line no-console */
    console.log(`[INFO] Spawning LAAP agent: ${PI_EXE} ${args.join(" ")} (cwd=${PI_CWD})`);
    this.proc = spawn(PI_EXE, args, {
      cwd: PI_CWD,
      stdio: ["pipe", "pipe", "pipe"],
      windowsHide: true,
      env: { ...process.env, LAAP_CLIENT_ID: "remote" },
    });
    this.proc.stdout.on("data", (c) => this.onData(c.toString("utf8")));
    this.proc.stderr.on("data", (c) => {
      const t = c.toString("utf8");
      if (/error|traceback|failed/i.test(t)) this.emit({ type: "pi_stderr", data: t.slice(0, 500) });
    });
    this.proc.on("exit", (code) => {
      /* eslint-disable-next-line no-console */
      console.log(`[WARN] LAAP agent exited (code ${code}); respawning in 2s`);
      this.proc = null;
      this.status.running = false;
      for (const [, p] of this.pending) { clearTimeout(p.timer); p.reject(new Error("agent exited")); }
      this.pending.clear();
      setTimeout(() => this.start(), 2000);
    });
    this.proc.on("spawn", () => { this.status.running = true; });
  }

  onData(text) {
    this.buf += text;
    let idx;
    while ((idx = this.buf.indexOf("\n")) >= 0) {
      const line = this.buf.slice(0, idx).replace(/\r$/, "");
      this.buf = this.buf.slice(idx + 1);
      if (!line.trim()) continue;
      let msg;
      try { msg = JSON.parse(line); } catch { continue; } // ignore non-JSON noise
      this.handleMessage(msg);
    }
  }

  handleMessage(msg) {
    if (!msg || typeof msg !== "object") return;
    this.emit(msg);

    if (msg.type === "response") {
      const p = this.pending.get(msg.id);
      if (p) {
        clearTimeout(p.timer);
        this.pending.delete(msg.id);
        if (msg.success) p.resolve(msg.data);
        else p.reject(new Error((msg.error) || "agent command failed"));
      }
      return;
    }

    // Track live state from events for /api/status
    if (msg.type === "get_state" || (msg.data && msg.data.isStreaming !== undefined)) {
      this.lastState = msg.data;
    } else if (msg.type === "agent_start" || msg.type === "turn_start") {
      this.status.streaming = true;
    } else if (msg.type === "agent_end" || msg.type === "turn_end") {
      this.status.streaming = false;
    } else if (msg.type === "model_update" && msg.data) {
      this.status.model = msg.data;
    }
  }

  emit(msg) {
    const line = JSON.stringify(msg);
    this.events.push(line);
    if (this.events.length > this.maxEvents) this.events.shift();
    for (const fn of this.listeners) { try { fn(line); } catch { /* ignore */ } }
  }

  request(type, payload = {}) {
    if (!this.proc) return Promise.reject(new Error("agent not started"));
    const id = "r" + (++this.seq) + "-" + crypto.randomBytes(4).toString("hex");
    const req = { id, type, ...payload };
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`agent timeout: ${type}`));
      }, 120000);
      this.pending.set(id, { resolve, reject, timer });
      this.proc.stdin.write(JSON.stringify(req) + "\n");
    });
  }

  async asyncRequest(type, payload) {
    try { return await this.request(type, payload); }
    catch (e) { return { bridge_error: String(e.message || e) }; }
  }

  stop() {
    if (this.proc) { try { this.proc.kill(); } catch { /* ignore */ } this.proc = null; }
  }
}

const pi = new PiRpc();

// ── HTTP server ────────────────────────────────────────────────────────
function sendJson(res, code, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(code, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "*",
  });
  res.end(body);
}

function sendFile(res, filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const mime = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8" };
  res.writeHead(200, { "Content-Type": mime[ext] || "text/plain; charset=utf-8", "Cache-Control": "no-store" });
  fs.createReadStream(filePath).pipe(res);
}

function authorized(req) {
  if (!BRIDGE_TOKEN) return true;
  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  return url.searchParams.get("token") === BRIDGE_TOKEN;
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(Buffer.from(c)));
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

const server = http.createServer((req, res) => {
  if (req.method === "OPTIONS") {
    res.writeHead(204, { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET,POST,OPTIONS", "Access-Control-Allow-Headers": "Content-Type" });
    return res.end();
  }
  if (!authorized(req)) return sendJson(res, 401, { error: "unauthorized" });

  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  const p = url.pathname;

  // Control UI
  if (p === "/" || p === "/control.html") {
    return sendFile(res, path.join(PUBLIC_DIR, "control.html"));
  }

  // Status
  if (p === "/api/status") {
    return sendJson(res, 200, {
      bridge: "laap-remote-bridge",
      port: PORT,
      agent: PI_EXE,
      running: pi.status.running,
      streaming: pi.status.streaming,
      model: pi.status.model,
      state: pi.lastState,
      eventsBuffered: pi.events.length,
      lan: lanIps(),
      tokenRequired: !!BRIDGE_TOKEN,
    });
  }

  // Command
  if (p === "/api/command" && req.method === "POST") {
    return (async () => {
      let body = {};
      try { body = JSON.parse((await readBody(req)).toString("utf8")); } catch { return sendJson(res, 400, { error: "invalid json" }); }
      const type = body.type;
      if (!type) return sendJson(res, 400, { error: "missing type" });
      const supported = new Set([
        "prompt", "steer", "follow_up", "abort", "new_session",
        "get_state", "get_messages", "get_session_stats", "get_available_models",
        "set_model", "cycle_model", "set_thinking_level", "cycle_thinking_level",
        "bash", "abort_bash", "compact", "set_auto_compaction", "set_auto_retry",
        "abort_retry", "set_steering_mode", "set_follow_up_mode", "export_html",
      ]);
      if (!supported.has(type)) return sendJson(res, 400, { error: `unsupported command: ${type}` });
      const payload = { ...body };
      delete payload.type;
      const data = await pi.asyncRequest(type, payload);
      return sendJson(res, 200, { type, data });
    })().catch((e) => sendJson(res, 500, { error: String(e.message || e) }));
  }

  // Server-Sent Events stream
  if (p === "/api/events") {
    res.writeHead(200, {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-store",
      "Connection": "keep-alive",
      "Access-Control-Allow-Origin": "*",
    });
    res.write(`retry: 2000\n\n`);
    const since = Number(url.searchParams.get("since") || 0);
    const start = Math.max(0, pi.events.length - since);
    for (const line of pi.events.slice(start)) {
      res.write(`data: ${line}\n\n`);
    }
    const push = (line) => { try { res.write(`data: ${line}\n\n`); } catch { /* closed */ } };
    pi.listeners.add(push);
    const hb = setInterval(() => { try { res.write(": ping\n\n"); } catch { /* closed */ } }, 15000);
    req.on("close", () => { clearInterval(hb); pi.listeners.delete(push); });
    return;
  }

  sendJson(res, 404, { error: "not found" });
});

function lanIps() {
  const out = [];
  for (const k of Object.keys(os.networkInterfaces())) {
    for (const it of os.networkInterfaces()[k] || []) {
      if (it.family === "IPv4" && !it.internal) out.push(it.address);
    }
  }
  return out;
}

// ── Lifecycle ─────────────────────────────────────────────────────────
pi.start();
server.listen(PORT, HOST, () => {
  /* eslint-disable-next-line no-console */
  console.log(`[COMPLETE] LAAP Remote Bridge listening on http://${HOST}:${PORT}`);
  /* eslint-disable-next-line no-console */
  console.log(`  Local:    http://localhost:${PORT}`);
  for (const ip of lanIps()) console.log(`  LAN (phone): http://${ip}:${PORT}`);
  /* eslint-disable-next-line no-console */
  console.log(`  Control UI on phone: http://<desktop-ip>:${PORT}/`);
  if (BRIDGE_TOKEN) console.log(`  Token auth enabled (append ?token=...)`);
});

process.on("SIGINT", () => { pi.stop(); process.exit(0); });
process.on("SIGTERM", () => { pi.stop(); process.exit(0); });