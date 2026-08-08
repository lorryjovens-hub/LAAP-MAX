// ---- LAAP Community · shared response helpers (Netlify Functions) ----
"use strict";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

export function respond(code, body) {
  return {
    statusCode: code,
    headers: { "Content-Type": "application/json; charset=utf-8", ...CORS },
    body: JSON.stringify(body),
  };
}

export function ok(body) {
  return respond(200, body);
}

export function created(body) {
  return respond(201, body);
}

export function err(code, message) {
  return respond(code, { error: message });
}

export function bad(message) {
  return err(400, message || "bad request");
}

export function unauthorized(message) {
  return err(401, message || "unauthorized");
}

export function notFound(message) {
  return err(404, message || "not found");
}

export function internal(message) {
  return err(500, message || "internal server error");
}

// CORS 预检
export function corsOptions() {
  return {
    statusCode: 204,
    headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS", "Access-Control-Allow-Headers": "Content-Type, Authorization" },
    body: "",
  };
}

// 解析 JSON body（容错）
export function parseBody(event) {
  if (!event.body) return {};
  try {
    return JSON.parse(event.body);
  } catch {
    return {};
  }
}