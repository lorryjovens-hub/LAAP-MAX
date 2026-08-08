// ---- LAAP Community · 本地同步 Agent（CommonJS 模块，供 server.cjs 使用）----
// 提供：登录态 / 推送(发布、下架) / 拉取(列表、导入) / 互动(点赞、播放、评论)
// 设计：本地作品 = 云端作品的"离线副本"。catalog.json 中的本地作品增加
//       `cloud_id` 字段，用于关联云端 Work.id。
"use strict";

const fs = require("fs");
const path = require("path");
const AdmZip = require("adm-zip");

const DEFAULT_CLOUD_URL = process.env.LAAP_CLOUD_URL || "https://laap-community.netlify.app/api";

// 创建云端同步客户端
// config: { cloudUrl?, appsDir, catalogFile, authFile }
module.exports = function createCloudSync(config) {
  const cloudUrl = (config.cloudUrl || DEFAULT_CLOUD_URL).replace(/\/+$/, "");
  const appsDir = config.appsDir;
  const catalogFile = config.catalogFile;
  const authFile = config.authFile;

  // ── 登录态持久化 ────────────────────────────────────────
  function readAuth() {
    try {
      return JSON.parse(fs.readFileSync(authFile, "utf8"));
    } catch {
      return null;
    }
  }
  function writeAuth(auth) {
    fs.mkdirSync(path.dirname(authFile), { recursive: true });
    fs.writeFileSync(authFile, JSON.stringify(auth, null, 2));
  }

  // ── 底层请求 ────────────────────────────────────────────
  async function request(method, pathname, body, { auth = true } = {}) {
    const headers = { "Content-Type": "application/json" };
    if (auth) {
      const a = readAuth();
      if (a?.token) headers.Authorization = `Bearer ${a.token}`;
    }
    const res = await fetch(`${cloudUrl}${pathname}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    const text = await res.text();
    let json = {};
    try {
      json = text ? JSON.parse(text) : {};
    } catch {
      json = { raw: text };
    }
    if (!res.ok) throw new Error(json.error || `${method} ${pathname} failed (${res.status})`);
    return json;
  }

  // ── 目录 <-> zip ────────────────────────────────────────
  function dirToZipBase64(appDir) {
    const zip = new AdmZip();
    zip.addLocalFolder(appDir, "");
    return zip.toBuffer().toString("base64");
  }
  function zipBase64ToDir(fileBase64, targetDir) {
    fs.mkdirSync(targetDir, { recursive: true });
    const zip = new AdmZip(Buffer.from(fileBase64, "base64"));
    zip.extractAllTo(targetDir, true);
  }

  // ── 公开 API ────────────────────────────────────────────
  return {
    get cloudUrl() { return cloudUrl; },

    async register(email, password, name) {
      const r = await request("POST", "/auth/register", { email, password, name }, { auth: false });
      writeAuth({ token: r.token, email: r.user.email, name: r.user.name, userId: r.user.id, at: Date.now() });
      return r.user;
    },

    async login(email, password) {
      const r = await request("POST", "/auth/login", { email, password }, { auth: false });
      writeAuth({ token: r.token, email: r.user.email, name: r.user.name, userId: r.user.id, at: Date.now() });
      return r.user;
    },

    logout() {
      try { fs.rmSync(authFile, { force: true }); } catch { /* ignore */ }
    },

    status() {
      const a = readAuth();
      return { loggedIn: !!a, email: a?.email || null, name: a?.name || null, cloudUrl };
    },

    // 拉取云端作品列表
    async listWorks(params = {}) {
      const qs = new URLSearchParams(params).toString();
      return request("GET", `/works${qs ? "?" + qs : ""}`);
    },

    // 把本地作品发布/更新到云端（app = catalog 条目）
    // 返回 { work, isNew }
    async publishApp(app) {
      const auth = readAuth();
      if (!auth) throw new Error("not logged in");
      const appDir = path.join(appsDir, app.id);
      if (!fs.existsSync(path.join(appDir, "index.html")) && !fs.existsSync(appDir)) {
        throw new Error("本地作品缺少可打包目录");
      }
      const fileBase64 = dirToZipBase64(appDir);
      const payload = {
        title: app.name || "Untitled",
        description: app.description || "",
        type: normalizeType(app.type),
        tags: app.tags || [],
        fileBase64,
      };
      const r = await request("POST", "/works", payload);
      const work = r.work;

      // 更新本地 catalog：记录 cloud_id 与同步时间
      const list = readCatalog();
      const idx = list.findIndex((a) => a.id === app.id);
      if (idx >= 0) {
        list[idx].cloud_id = work.id;
        list[idx].synced_at = Date.now();
        list[idx].cloud_likes = work.likes;
        writeCatalog(list);
      }
      return { work, isNew: true };
    },

    // 从云端导入作品到本地
    // work = 云端 work 对象
    async importWork(work) {
      const r = await request("GET", `/works/${work.id}/zip`);
      const localId = "cloud-" + work.id.slice(0, 8);
      const targetDir = path.join(appsDir, localId);
      zipBase64ToDir(r.body, targetDir);

      const list = readCatalog();
      // 若已导入则更新，否则新增
      const existing = list.find((a) => a.cloud_id === work.id);
      const entry = {
        id: existing ? existing.id : localId,
        name: work.title,
        description: work.description || "",
        type: work.type === "game" ? "game" : "web",
        author: "cloud",
        createdAt: Date.now(),
        url: `/app/${existing ? existing.id : localId}/`,
        downloads: 0,
        cloud_id: work.id,
        synced_at: Date.now(),
        cloud_likes: work.likes,
        cloud_plays: work.plays,
      };
      if (existing) {
        const idx = list.findIndex((a) => a.cloud_id === work.id);
        list[idx] = { ...list[idx], ...entry };
      } else {
        list.unshift(entry);
      }
      writeCatalog(list);
      return entry;
    },

    // 下架/删除云端作品
    async deleteWork(workId) {
      return request("DELETE", `/works/${workId}`);
    },

    async likeWork(workId) {
      return request("POST", `/works/${workId}/like`, {});
    },
    async playWork(workId) {
      return request("POST", `/works/${workId}/play`, {});
    },
    async listComments(workId) {
      return request("GET", `/works/${workId}/comments`);
    },
    async addComment(workId, text) {
      return request("POST", `/works/${workId}/comments`, { text });
    },
  };

  // ── 内部工具 ────────────────────────────────────────────
  function readCatalog() {
    try {
      return JSON.parse(fs.readFileSync(catalogFile, "utf8"));
    } catch {
      return [];
    }
  }
  function writeCatalog(list) {
    fs.writeFileSync(catalogFile, JSON.stringify(list, null, 2));
  }
  function normalizeType(t) {
    if (t === "game") return "game";
    if (t === "site") return "site";
    return "webapp";
  }
};