#!/usr/bin/env node
/*
 * LAAP Community Server — desktop local server.
 *
 * Runs on the user's desktop and provides:
 *   1. A community catalog where user-generated web apps / websites / games
 *      are published, browsed and played (hosted in-browser).
 *   2. A desktop "one-click export APK" UI that shells out to
 *      `tools/apk-export/export_webapp_apk.ps1` to build a standalone APK
 *      from any published app.
 *
 * Zero external dependencies — plain Node `http` + `fs`. The mobile app
 * connects to `http://<desktop-ip>:<port>` to browse and play.
 *
 * Usage:
 *   node server.js [--port 8790]
 */
"use strict";

const http = require("http");
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");
const { URL } = require("url");

const HOST = "0.0.0.0"; // reachable from phones on the LAN
const PORT = Number(process.argv[process.argv.indexOf("--port") + 1]) || 8790;

const ROOT = __dirname;
const PUBLIC_DIR = path.join(ROOT, "public");
const DATA_DIR = path.join(ROOT, "data");
const APPS_DIR = path.join(DATA_DIR, "apps");
const DOWNLOADS_DIR = path.join(ROOT, "downloads");
const CATALOG_FILE = path.join(DATA_DIR, "catalog.json");

// Absolute path to the desktop APK export script (sibling tool).
const EXPORT_SCRIPT = path.join(ROOT, "..", "apk-export", "export_webapp_apk.ps1");

for (const d of [DATA_DIR, APPS_DIR, DOWNLOADS_DIR, PUBLIC_DIR]) {
  fs.mkdirSync(d, { recursive: true });
}
if (!fs.existsSync(CATALOG_FILE)) fs.writeFileSync(CATALOG_FILE, "[]");

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
  ".ico": "image/x-icon",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".ttf": "font/ttf",
  ".mp3": "audio/mpeg",
  ".mp4": "video/mp4",
  ".webm": "video/webm",
  ".wasm": "application/wasm",
  ".apk": "application/vnd.android.package-archive",
  ".zip": "application/zip",
};

function readCatalog() {
  try {
    return JSON.parse(fs.readFileSync(CATALOG_FILE, "utf8"));
  } catch {
    return [];
  }
}
function writeCatalog(list) {
  fs.writeFileSync(CATALOG_FILE, JSON.stringify(list, null, 2));
}

function sendJson(res, code, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(code, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
    "Cache-Control": "no-store",
  });
  res.end(body);
}

function sendFile(res, filePath, downloadName) {
  if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
    sendJson(res, 404, { error: "not found" });
    return;
  }
  const ext = path.extname(filePath).toLowerCase();
  const headers = { "Content-Type": MIME[ext] || "application/octet-stream" };
  if (downloadName) headers["Content-Disposition"] = `attachment; filename="${downloadName}"`;
  res.writeHead(200, headers);
  fs.createReadStream(filePath).pipe(res);
}

function serveStatic(res, filePath) {
  if (!fs.statSync(filePath, { throwIfNoEntry: false })?.isFile()) {
    sendJson(res, 404, { error: "not found" });
    return;
  }
  sendFile(res, filePath);
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  const pathname = decodeURIComponent(url.pathname);

  // ── API ───────────────────────────────────────────────────────────────
  if (pathname === "/api/apps" && req.method === "GET") {
    return sendJson(res, 200, readCatalog());
  }

  if (pathname === "/api/apps" && req.method === "POST") {
    return handlePublish(req, res);
  }

  if (pathname === "/api/export" && req.method === "POST") {
    return handleExport(req, res);
  }

  if (pathname.startsWith("/api/apps/") && req.method === "DELETE") {
    const id = pathname.slice("/api/apps/".length);
    const list = readCatalog().filter((a) => a.id !== id);
    writeCatalog(list);
    fs.rmSync(path.join(APPS_DIR, id), { recursive: true, force: true });
    return sendJson(res, 200, { ok: true });
  }

  // ── Hosted app: /app/<id>/... ─────────────────────────────────────────
  const appMatch = pathname.match(/^\/app\/([^/]+)(?:\/(.*))?$/);
  if (appMatch) {
    const id = appMatch[1];
    const rest = appMatch[2] || "index.html";
    const appDir = path.join(APPS_DIR, id);
    if (!fs.existsSync(appDir)) return sendJson(res, 404, { error: "app not found" });
    const filePath = path.resolve(appDir, rest);
    if (!filePath.startsWith(appDir)) return sendJson(res, 403, { error: "forbidden" });
    return serveStatic(res, filePath);
  }

  // ── Downloads (exported APKs / zips) ─────────────────────────────────
  if (pathname.startsWith("/downloads/")) {
    const name = path.basename(pathname);
    return sendFile(res, path.join(DOWNLOADS_DIR, name), name);
  }

  // ── Web UI ────────────────────────────────────────────────────────────
  if (pathname === "/" || pathname === "/index.html") {
    return serveStatic(res, path.join(PUBLIC_DIR, "index.html"));
  }
  if (pathname === "/export" || pathname === "/export.html") {
    return serveStatic(res, path.join(PUBLIC_DIR, "export.html"));
  }

  // Static public asset.
  const rel = pathname.replace(/^\/+/, "");
  if (rel) {
    const fp = path.resolve(PUBLIC_DIR, rel);
    if (fp.startsWith(PUBLIC_DIR)) return serveStatic(res, fp);
  }

  sendJson(res, 404, { error: "not found" });
});

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(Buffer.from(c)));
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

/** Publish an app: stores the uploaded zip as the app's web assets. */
async function handlePublish(req, res) {
  try {
    const ct = req.headers["content-type"] || "";
    if (!ct.includes("multipart/form-data")) {
      // JSON publish: { name, description, type, url } — external link app.
      const raw = await readBody(req);
      const body = JSON.parse(raw || "{}");
      const id = "app-" + Date.now().toString(36);
      const app = {
        id,
        name: body.name || "Untitled",
        description: body.description || "",
        type: body.type || "web",
        author: body.author || "anonymous",
        createdAt: Date.now(),
        url: body.url || `/app/${id}/`,
        downloads: 0,
      };
      const list = readCatalog();
      list.unshift(app);
      writeCatalog(list);
      return sendJson(res, 201, app);
    }

    // Multipart: zip file containing the built web app.
    const boundary = ct.split("boundary=")[1];
    const raw = Buffer.from(await readBody(req), "binary");
    const parts = parseMultipart(raw, boundary);
    const str = (k) => (parts[k] ? parts[k].toString("utf8").trim() : "");

    const name = str("name") || "Untitled";
    const description = str("description") || "";
    const type = str("type") || "web";
    const author = str("author") || "anonymous";
    const zipBuf = parts.file;

    if (!zipBuf) return sendJson(res, 400, { error: "missing file" });

    const id = "app-" + Date.now().toString(36);
    const appDir = path.join(APPS_DIR, id);
    fs.mkdirSync(appDir, { recursive: true });
    const zipPath = path.join(appDir, "__upload.zip");
    fs.writeFileSync(zipPath, zipBuf);
    extractZip(zipPath, appDir);
    fs.rmSync(zipPath, { force: true });

    const app = {
      id,
      name,
      description,
      type,
      author,
      createdAt: Date.now(),
      url: `/app/${id}/`,
      downloads: 0,
    };
    const list = readCatalog();
    list.unshift(app);
    writeCatalog(list);
    return sendJson(res, 201, app);
  } catch (e) {
    return sendJson(res, 500, { error: String(e.message || e) });
  }
}

/** Runs export_webapp_apk.ps1 -Build for a published app. */
async function handleExport(req, res) {
  try {
    const raw = await readBody(req);
    const body = JSON.parse(raw || "{}");
    const app = readCatalog().find((a) => a.id === body.appId);
    if (!app) return sendJson(res, 404, { error: "app not found" });

    const sourceDir = path.join(APPS_DIR, app.id);
    if (!fs.existsSync(path.join(sourceDir, "index.html"))) {
      return sendJson(res, 400, {
        error: "该应用没有可打包的 index.html（可能是外部链接应用）",
      });
    }

    const outDir = DOWNLOADS_DIR;
    const permissions = Array.isArray(body.permissions) ? body.permissions : [];
    const appName = body.appName || app.name;
    const packageId = body.packageId || `org.laap.webapp.${app.name.replace(/[^a-zA-Z0-9]/g, "").toLowerCase() || "app"}`;

    const permsArg = (permissions.length ? permissions.join(",") : "none");
    const args = [
      "-NoProfile",
      "-ExecutionPolicy", "Bypass",
      "-File", EXPORT_SCRIPT,
      "-SourceDir", sourceDir,
      "-AppName", appName,
      "-PackageId", packageId,
      "-Permissions", permsArg,
      "-OutDir", outDir,
      "-Build",
    ];
    const stdout = execFileSync("powershell.exe", args, {
      encoding: "utf8",
      timeout: 10 * 60 * 1000,
      maxBuffer: 64 * 1024 * 1024,
    });

    const apkName = packageId.replace(/\./g, "_") + ".apk";
    const apkPath = path.join(outDir, apkName);
    if (!fs.existsSync(apkPath)) {
      return sendJson(res, 500, { error: "构建完成但未找到 APK", log: stdout.slice(-4000) });
    }
    app.downloads = (app.downloads || 0) + 1;
    writeCatalog(readCatalog());
    return sendJson(res, 200, {
      ok: true,
      downloadUrl: `/downloads/${apkName}`,
      stdout: stdout.slice(-2000),
    });
  } catch (e) {
    return sendJson(res, 500, { error: String((e.stderr || e.message || e)).slice(-4000) });
  }
}

// ── Minimal multipart parser (file + text fields) ───────────────────────
function parseMultipart(buf, boundary) {
  const out = { file: null };
  const delim = Buffer.from(`--${boundary}`);
  const parts = [];
  let start = 0;
  while (start < buf.length) {
    const idx = buf.indexOf(delim, start);
    if (idx === -1) break;
    let end = buf.indexOf(Buffer.from("\r\n"), idx + delim.length);
    if (buf.subarray(idx + delim.length, idx + delim.length + 2).toString() === "--") break; // closing
    const headerEnd = buf.indexOf(Buffer.from("\r\n\r\n"), end);
    const dataEnd = buf.indexOf(delim, headerEnd + 4) - 2; // trim trailing \r\n
    const part = buf.subarray(headerEnd + 4, dataEnd);
    const header = buf.subarray(end + 2, headerEnd).toString();
    const nameMatch = header.match(/name="([^"]+)"/);
    if (nameMatch && part.length < 512 * 1024 * 1024) {
      out[nameMatch[1]] = part;
    }
    start = headerEnd + 4;
    void parts;
  }
  return out;
}

function extractZip(zipPath, destDir) {
  // Uses PowerShell's Expand-Archive (no external deps).
  const ps = `Expand-Archive -Path '${zipPath.replace(/'/g, "''")}' -DestinationPath '${destDir
    .replace(/'/g, "''")}' -Force`;
  execFileSync("powershell.exe", ["-ExecutionPolicy", "Bypass", "-NoProfile", "-Command", ps], {
    encoding: "utf8",
    timeout: 120000,
  });
}

server.listen(PORT, HOST, () => {
  const ifaces = require("os").networkInterfaces();
  const lan = [];
  for (const k of Object.keys(ifaces)) {
    for (const it of ifaces[k] || []) {
      if (it.family === "IPv4" && !it.internal) lan.push(it.address);
    }
  }
  /* eslint-disable-next-line no-console */
  console.log(`[COMPLETE] LAAP Community Server listening on http://${HOST}:${PORT}`);
  /* eslint-disable-next-line no-console */
  console.log(`  Local:    http://localhost:${PORT}`);
  for (const ip of lan) console.log(`  LAN (mobile): http://${ip}:${PORT}`);
  /* eslint-disable-next-line no-console */
  console.log(`  Export UI: http://localhost:${PORT}/export`);
});