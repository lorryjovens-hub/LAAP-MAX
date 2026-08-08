// ---- LAAP Community · 云端 API 统一入口 (Netlify Function) ----
// 完整实现：
//   health / auth(register,login,me)
//   works(list, detail, create[上传 zip], delete)
//   files(提供作品资源)
//   like / play / comments
//
// 存储：作品以 zip 形式存到 Supabase Storage（bucket: works），files_ref = "<id>.zip"
// 提供：从 Storage 下载 zip，内存解压后返回所请求文件。
//
// 路由：`/api/<segments>`（由 netlify.toml 把 /api/* 转发到本函数）
"use strict";

import AdmZip from "adm-zip";
import {
  ok, created, bad, unauthorized, notFound, internal, corsOptions, parseBody,
} from "./_shared/response.mjs";
import { hashPassword, verifyPassword, signToken, authUserFromEvent } from "./_shared/auth.mjs";
import { supabase, isDbReady } from "./_shared/db.mjs";

const BUCKET = "works";
const MAX_ZIP_MB = 200;

// 把请求路径解析为段数组，兼容两种前缀：
//   /.netlify/functions/community-api/auth/register
//   /api/auth/register
function route(event) {
  let p = event.path || "/";
  const apiIdx = p.indexOf("/api/");
  if (apiIdx >= 0) p = p.slice(apiIdx + 4);
  return p.replace(/^\/+/, "").split("/").filter(Boolean);
}

const MIME = {
  ".html": "text/html; charset=utf-8", ".htm": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8",
  ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
  ".svg": "image/svg+xml", ".webp": "image/webp", ".ico": "image/x-icon",
  ".woff": "font/woff", ".woff2": "font/woff2", ".ttf": "font/ttf",
  ".mp3": "audio/mpeg", ".mp4": "video/mp4", ".webm": "video/webm",
  ".wasm": "application/wasm", ".txt": "text/plain; charset=utf-8",
};

function publicUser(row) {
  return {
    id: row.id, email: row.email, name: row.name,
    avatar_url: row.avatar_url, bio: row.bio, created_at: row.created_at,
  };
}

function publicWork(row) {
  return {
    id: row.id, owner_id: row.owner_id, title: row.title, description: row.description,
    type: row.type, size: row.size, tags: row.tags || [], likes: row.likes, plays: row.plays,
    status: row.status, published_at: row.published_at, updated_at: row.updated_at,
  };
}

// ── 认证 ───────────────────────────────────────────────────
async function handleRegister(event) {
  const { email, password, name } = parseBody(event);
  if (!email || !password || !name) return bad("email, password, name required");
  if (String(password).length < 6) return bad("password too short (min 6)");
  const hash = await hashPassword(password);
  const { data, error } = await supabase.from("users").insert({ email, password_hash: hash, name }).select().single();
  if (error) {
    if (String(error.message).includes("duplicate")) return bad("email already registered");
    return internal(error.message);
  }
  const token = signToken({ sub: data.id, email: data.email });
  return created({ token, user: publicUser(data) });
}

async function handleLogin(event) {
  const { email, password } = parseBody(event);
  if (!email || !password) return bad("email, password required");
  const { data, error } = await supabase.from("users").select("*").eq("email", email).maybeSingle();
  if (error) return internal(error.message);
  if (!data) return unauthorized("email or password incorrect");
  const okPass = await verifyPassword(password, data.password_hash);
  if (!okPass) return unauthorized("email or password incorrect");
  const token = signToken({ sub: data.id, email: data.email });
  return ok({ token, user: publicUser(data) });
}

async function handleMe(event) {
  const user = authUserFromEvent(event);
  if (!user) return unauthorized("not logged in");
  const { data, error } = await supabase.from("users").select("*").eq("id", user.sub).maybeSingle();
  if (error) return internal(error.message);
  if (!data) return unauthorized("user not found");
  return ok({ user: publicUser(data) });
}

// ── 作品 ───────────────────────────────────────────────────
async function handleListWorks(event) {
  const url = new URL(event.rawUrl || `http://x${event.path || "/"}`);
  const page = Math.max(0, parseInt(url.searchParams.get("page") || "0", 10) || 0);
  const pageSize = Math.min(50, Math.max(1, parseInt(url.searchParams.get("limit") || "20", 10) || 20));
  const type = url.searchParams.get("type");
  const tag = url.searchParams.get("tag");
  const mine = url.searchParams.get("mine") === "1";
  const user = authUserFromEvent(event);

  let q = supabase
    .from("works")
    .select("id, owner_id, title, description, type, size, tags, likes, plays, status, published_at, updated_at", { count: "exact" })
    .order("published_at", { ascending: false })
    .range(page * pageSize, (page + 1) * pageSize - 1);
  if (mine) {
    if (!user) return unauthorized("not logged in");
    q = q.eq("owner_id", user.sub);
  } else {
    q = q.eq("status", "published");
  }
  if (type) q = q.eq("type", type);
  if (tag) q = q.contains("tags", [tag]);

  const { data, error, count } = await q;
  if (error) return internal(error.message);
  return ok({ works: (data || []).map(publicWork), page, total: count || 0, hasMore: (data?.length || 0) === pageSize });
}

async function handleCreateWork(event) {
  const user = authUserFromEvent(event);
  if (!user) return unauthorized("not logged in");
  const body = parseBody(event);
  const { title, description, type = "webapp", tags = [], fileBase64 } = body;
  if (!title) return bad("title required");
  if (!fileBase64) return bad("fileBase64 required (作品 zip 的 base64)");

  let zipBuf;
  try {
    zipBuf = Buffer.from(fileBase64, "base64");
  } catch {
    return bad("fileBase64 invalid");
  }
  if (zipBuf.length > MAX_ZIP_MB * 1024 * 1024) return bad(`zip too large (max ${MAX_ZIP_MB}MB)`);

  // 1) 先建 DB 记录拿 work.id
  const { data: work, error: werr } = await supabase
    .from("works")
    .insert({ owner_id: user.sub, title, description, type, tags, size: zipBuf.length, files_ref: "" })
    .select()
    .single();
  if (werr) return internal(werr.message);

  // 2) 上传 zip 到 Storage
  const path = `${work.id}.zip`;
  const { error: uerr } = await supabase.storage.from(BUCKET).upload(path, zipBuf, { contentType: "application/zip", upsert: true });
  if (uerr) {
    await supabase.from("works").delete().eq("id", work.id);
    return internal(`storage upload failed: ${uerr.message}`);
  }

  // 3) 回填 files_ref
  await supabase.from("works").update({ files_ref: path }).eq("id", work.id);
  return created({ work: { ...publicWork(work), files_ref: path } });
}

async function handleGetWork(event, id) {
  const work = await getWorkRaw(id);
  if (!work) return notFound("work not found");
  return ok({ work: publicWork(work) });
}

async function handleDeleteWork(event, id) {
  const user = authUserFromEvent(event);
  if (!user) return unauthorized("not logged in");
  const work = await getWorkRaw(id);
  if (!work) return notFound("work not found");
  if (work.owner_id !== user.sub) return unauthorized("not your work");
  const { error } = await supabase.from("works").delete().eq("id", id);
  if (error) return internal(error.message);
  await supabase.storage.from(BUCKET).remove([`${id}.zip`]).catch(() => {});
  return ok({ ok: true });
}

async function getWorkRaw(id) {
  const { data } = await supabase.from("works").select("*").eq("id", id).maybeSingle();
  return data;
}

// ── 作品文件提供 ───────────────────────────────────────────
async function handleWorkFile(event, id, filePath) {
  const work = await getWorkRaw(id);
  if (!work) return notFound("work not found");
  if (work.files_ref !== `${id}.zip`) return notFound("work has no file bundle");

  const { data: blob, error } = await supabase.storage.from(BUCKET).download(`${id}.zip`);
  if (error || !blob) return notFound("work files unavailable");

  let zip;
  try {
    const buf = Buffer.from(await blob.arrayBuffer());
    zip = new AdmZip(buf);
  } catch {
    return internal("unable to open work bundle");
  }

  const requested = filePath ? filePath.replace(/^\/+/, "") : "index.html";
  const entries = zip.getEntries();
  let target = entries.find((e) => e.entryName === requested);
  if (!target) {
    // 尝试 index.html 作为 SPA fallback
    const fallback = entries.find((e) => /^index\.html$/i.test(e.entryName) && !e.isDirectory);
    if (fallback && (!requested || requested === "index.html")) target = fallback;
  }
  if (!target || target.isDirectory) return notFound("file not found in work");

  const ext = "." + (target.entryName.split(".").pop() || "").toLowerCase();
  const body = target.getData().toString("binary");
  return {
    statusCode: 200,
    headers: {
      "Content-Type": MIME[ext] || "application/octet-stream",
      "Access-Control-Allow-Origin": "*",
      "Cache-Control": "public, max-age=300",
    },
    isBase64Encoded: true,
    body: Buffer.from(body, "binary").toString("base64"),
  };
}

// ── 点赞 / 播放 / 评论 ─────────────────────────────────────
async function handleWorkZip(event, id) {
  const work = await getWorkRaw(id);
  if (!work) return notFound("work not found");
  if (work.files_ref !== `${id}.zip`) return notFound("work has no file bundle");
  const { data: blob, error } = await supabase.storage.from(BUCKET).download(`${id}.zip`);
  if (error || !blob) return notFound("work files unavailable");
  const buf = Buffer.from(await blob.arrayBuffer());
  return {
    statusCode: 200,
    headers: { "Content-Type": "application/zip", "Access-Control-Allow-Origin": "*" },
    isBase64Encoded: true,
    body: buf.toString("base64"),
  };
}

async function handleLike(event, id) {
  const user = authUserFromEvent(event);
  if (!user) return unauthorized("not logged in");
  const work = await getWorkRaw(id);
  if (!work) return notFound("work not found");

  const { data: existing } = await supabase.from("work_likes").select().eq("work_id", id).eq("user_id", user.sub).maybeSingle();
  if (existing) {
    // 取消点赞
    await supabase.from("work_likes").delete().eq("work_id", id).eq("user_id", user.sub);
    await supabase.from("works").update({ likes: Math.max(0, (work.likes || 0) - 1) }).eq("id", id);
    return ok({ liked: false, likes: Math.max(0, (work.likes || 0) - 1) });
  }
  await supabase.from("work_likes").insert({ work_id: id, user_id: user.sub });
  await supabase.from("works").update({ likes: (work.likes || 0) + 1 }).eq("id", id);
  return ok({ liked: true, likes: (work.likes || 0) + 1 });
}

async function handlePlay(event, id) {
  const work = await getWorkRaw(id);
  if (!work) return notFound("work not found");
  await supabase.from("works").update({ plays: (work.plays || 0) + 1 }).eq("id", id);
  return ok({ plays: (work.plays || 0) + 1 });
}

async function handleComments(event, id, method) {
  const work = await getWorkRaw(id);
  if (!work) return notFound("work not found");
  if (method === "GET") {
    const { data, error } = await supabase
      .from("comments")
      .select("id, work_id, user_id, text, created_at, users(name)")
      .eq("work_id", id)
      .order("created_at", { ascending: true });
    if (error) return internal(error.message);
    return ok({ comments: (data || []).map((c) => ({ id: c.id, text: c.text, created_at: c.created_at, author: c.users?.name || "匿名" })) });
  }
  // POST
  const user = authUserFromEvent(event);
  if (!user) return unauthorized("not logged in");
  const { text } = parseBody(event);
  if (!text || !String(text).trim()) return bad("text required");
  const { data, error } = await supabase.from("comments").insert({ work_id: id, user_id: user.sub, text: String(text).trim() }).select().single();
  if (error) return internal(error.message);
  return created({ comment: { id: data.id, text: data.text, created_at: data.created_at, author: "me" } });
}

// ── 入口 ───────────────────────────────────────────────────
export const handler = async (event) => {
  try {
    if (event.httpMethod === "OPTIONS") return corsOptions();

    const seg = route(event);
    const method = event.httpMethod;

    if (seg[0] === "health") return ok({ status: "ok", service: "laap-community-api", version: "0.2.0", db: isDbReady() });
    if (!isDbReady()) return internal("database not configured (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)");

    // auth
    if (seg[0] === "auth" && seg[1] === "register" && method === "POST") return handleRegister(event);
    if (seg[0] === "auth" && seg[1] === "login" && method === "POST") return handleLogin(event);
    if (seg[0] === "me" && method === "GET") return handleMe(event);

    // works
    if (seg[0] === "works") {
      if (seg.length === 1 && method === "GET") return handleListWorks(event);
      if (seg.length === 1 && method === "POST") return handleCreateWork(event);
      if (seg.length === 2 && method === "GET") return handleGetWork(event, seg[1]);
      if (seg.length === 2 && method === "DELETE") return handleDeleteWork(event, seg[1]);
      if (seg.length === 3) {
        if (seg[2] === "like" && method === "POST") return await handleLike(event, seg[1]);
        if (seg[2] === "play" && method === "POST") return await handlePlay(event, seg[1]);
        if (seg[2] === "comments" && (method === "GET" || method === "POST")) return await handleComments(event, seg[1], method);
        if (seg[2] === "files" && method === "GET") return await handleWorkFile(event, seg[1], seg[3] || "index.html");
        if (seg[2] === "zip" && method === "GET") return await handleWorkZip(event, seg[1]);
      }
      if (seg.length === 4 && seg[2] === "files" && method === "GET") return await handleWorkFile(event, seg[1], seg[3]);
    }

    return notFound("route not found");
  } catch (e) {
    return internal(e.message || String(e));
  }
};