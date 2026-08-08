// ---- LAAP Community · auth helpers (JWT HS256 + bcrypt password) ----
// 零外部依赖：JWT 用 Node 内置 crypto（HS256），密码用项目已有的 bcryptjs。
"use strict";

import crypto from "node:crypto";
import bcrypt from "bcryptjs";

const SECRET = process.env.JWT_SECRET || "laap-dev-secret-change-me";
const TOKEN_TTL_SECONDS = 7 * 24 * 3600; // 7 天

function b64url(input) {
  return Buffer.from(input).toString("base64url");
}

export async function hashPassword(plain) {
  return bcrypt.hash(plain, 10);
}

export async function verifyPassword(plain, hash) {
  return bcrypt.compare(plain, hash);
}

export function signToken(payload) {
  const header = b64url(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const now = Math.floor(Date.now() / 1000);
  const body = b64url(JSON.stringify({ ...payload, iat: now, exp: now + TOKEN_TTL_SECONDS }));
  const data = `${header}.${body}`;
  const sig = crypto.createHmac("sha256", SECRET).update(data).digest("base64url");
  return `${data}.${sig}`;
}

export function verifyToken(token) {
  if (!token) throw new Error("missing token");
  const parts = token.split(".");
  if (parts.length !== 3) throw new Error("malformed token");
  const data = `${parts[0]}.${parts[1]}`;
  const expect = crypto.createHmac("sha256", SECRET).update(data).digest("base64url");
  if (expect !== parts[2]) throw new Error("bad signature");
  const payload = JSON.parse(Buffer.from(parts[1], "base64url").toString("utf8"));
  if (payload.exp < Math.floor(Date.now() / 1000)) throw new Error("token expired");
  return payload;
}

// 从请求 Authorization 头提取用户（返回 payload 或 null，不抛错）
export function authUserFromEvent(event) {
  const auth = event.headers?.authorization || event.headers?.Authorization || "";
  const m = /^Bearer\s+(.+)$/i.exec(auth.trim());
  if (!m) return null;
  try {
    return verifyToken(m[1]);
  } catch {
    return null;
  }
}