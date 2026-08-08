/** Convex auth internals (users, tokens). */

import { v } from "convex/values";
import { internalMutation, internalQuery } from "./_generated/server";

const ACCESS_TOKEN_TTL = 60 * 60 * 1000; // 1 hour
const REFRESH_TOKEN_TTL = 7 * 24 * 60 * 60 * 1000; // 7 days

function getSecret(): string {
  const secret = process.env.SECRET_KEY;
  if (!secret) throw new Error("SECRET_KEY environment variable is not set");
  return secret;
}

function base64UrlEncode(input: string): string {
  return btoa(input).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function base64UrlDecode(input: string): string {
  const padded = input.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat((4 - (input.length % 4)) % 4);
  return atob(padded);
}

async function hmacSha256(message: string, key: string): Promise<string> {
  // SubtleCrypto is available in Convex action/isolate runtime.
  const encoder = new TextEncoder();
  const cryptoKey = await crypto.subtle.importKey(
    "raw",
    encoder.encode(key),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const signature = await crypto.subtle.sign("HMAC", cryptoKey, encoder.encode(message));
  return base64UrlEncode(String.fromCharCode(...new Uint8Array(signature)));
}

export async function signJwt(payload: Record<string, unknown>, expiresInMs: number): Promise<string> {
  const header = base64UrlEncode(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const now = Date.now();
  const body = base64UrlEncode(
    JSON.stringify({ ...payload, iat: Math.floor(now / 1000), exp: Math.floor((now + expiresInMs) / 1000) })
  );
  const signature = await hmacSha256(`${header}.${body}`, getSecret());
  return `${header}.${body}.${signature}`;
}

export async function verifyJwt(token: string): Promise<Record<string, unknown> | null> {
  try {
    const [header, body, signature] = token.split(".");
    if (!header || !body || !signature) return null;
    const expected = await hmacSha256(`${header}.${body}`, getSecret());
    if (signature !== expected) return null;
    const payload = JSON.parse(base64UrlDecode(body)) as Record<string, unknown>;
    if (typeof payload.exp === "number" && payload.exp * 1000 < Date.now()) return null;
    return payload;
  } catch {
    return null;
  }
}

async function hashPasswordHmac(password: string): Promise<string> {
  // Convex isolate runtime provides SubtleCrypto but not bcryptjs.
  // Use HMAC-SHA256 with the app secret as the key for password storage.
  return hmacSha256(password, getSecret());
}

export const hashPassword = (password: string) => hashPasswordHmac(password);
export const verifyPassword = async (password: string, hash: string) =>
  (await hashPasswordHmac(password)) === hash;

export const createUser = internalMutation({
  args: {
    username: v.string(),
    email: v.string(),
    password_hash: v.string(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("users")
      .withIndex("by_email", (q) => q.eq("email", args.email))
      .unique();
    if (existing) throw new Error("Email already registered");
    return await ctx.db.insert("users", {
      username: args.username,
      email: args.email,
      password_hash: args.password_hash,
      is_active: true,
    });
  },
});

export const getUserByEmail = internalQuery({
  args: { email: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db.query("users").withIndex("by_email", (q) => q.eq("email", args.email)).unique();
  },
});

export const getUserById = internalQuery({
  args: { id: v.id("users") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const getUserByUsername = internalQuery({
  args: { username: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("users")
      .withIndex("by_username", (q) => q.eq("username", args.username))
      .unique();
  },
});

export const storeRefreshToken = internalMutation({
  args: {
    user_id: v.id("users"),
    token_hash: v.string(),
    expires_at: v.number(),
  },
  handler: async (ctx, args) => {
    await ctx.db.insert("refresh_tokens", args);
  },
});

export const getRefreshToken = internalQuery({
  args: { token_hash: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("refresh_tokens")
      .withIndex("by_token_hash", (q) => q.eq("token_hash", args.token_hash))
      .unique();
  },
});

export const deleteRefreshToken = internalMutation({
  args: { id: v.id("refresh_tokens") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});

export { ACCESS_TOKEN_TTL, REFRESH_TOKEN_TTL };
