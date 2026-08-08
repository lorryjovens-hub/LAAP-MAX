/** Convex HTTP actions exposing the LAAP API. */

import { httpAction } from "./_generated/server";
import { api } from "./_generated/api";
import { httpRouter } from "convex/server";
import {
  createUser,
  getUserByEmail,
  getUserById,
  getUserByUsername,
  hashPassword,
  signJwt,
  storeRefreshToken,
  getRefreshToken,
  deleteRefreshToken,
  verifyJwt,
  verifyPassword,
  ACCESS_TOKEN_TTL,
  REFRESH_TOKEN_TTL,
} from "./auth";
import {
  createSession,
  listSessions,
  getSession,
  addMessage,
  listMessages,
  deleteSession,
  updateSessionTitle,
  updateMessageFeedback,
} from "./sessions";
import { generateChatResponse, type LLMConfig } from "./lib/llm";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...CORS_HEADERS },
  });

async function readJson(request: Request): Promise<unknown> {
  return request.json();
}

function handleOptions() {
  return new Response(null, { status: 204, headers: CORS_HEADERS });
}

async function getCurrentUser(ctx: any, request: Request) {
  const auth = request.headers.get("Authorization") || "";
  const token = auth.startsWith("Bearer ") ? auth.slice(7) : "";
  if (!token) return null;
  const payload = await verifyJwt(token);
  if (!payload || typeof payload.sub !== "string") return null;
  return await ctx.runQuery(api.auth.getUserById, { id: payload.sub as any });
}

function getLLMConfig(): LLMConfig {
  const provider = process.env.MODEL_PROVIDER || "deepseek";
  const api_key = process.env.DEEPSEEK_API_KEY || process.env.OPENAI_API_KEY || "";
  const base_url = process.env.DEEPSEEK_BASE_URL || process.env.OPENAI_BASE_URL;
  const model = process.env.MODEL;
  if (provider !== "openai" && provider !== "deepseek") {
    throw new Error("Unsupported provider");
  }
  return { provider, api_key, base_url, model };
}

const http = httpRouter();

http.route({
  path: "/health",
  method: "GET",
  handler: httpAction(async () => {
    return json({ status: "ok", backend: "convex" });
  }),
});

// Config endpoints for frontend settings compatibility.
http.route({
  path: "/api/v1/config/llm",
  method: "GET",
  handler: httpAction(async () => {
    return json({ provider: "deepseek", base_url: "", model: "" });
  }),
});

http.route({
  path: "/api/v1/config/llm/full",
  method: "GET",
  handler: httpAction(async () => {
    return json({ provider: "deepseek", api_key: "", base_url: "", model: "" });
  }),
});

http.route({
  path: "/api/v1/config/llm",
  method: "PUT",
  handler: httpAction(async (_ctx, request) => {
    const body = (await readJson(request)) as {
      provider?: string;
      base_url?: string;
      model?: string;
    };
    return json({
      provider: body.provider ?? "deepseek",
      base_url: body.base_url ?? "",
      model: body.model ?? "",
    });
  }),
});

// CORS preflight handlers
http.route({ path: "/api/v1/auth/:path", method: "OPTIONS", handler: httpAction(handleOptions) });
http.route({ path: "/api/v1/sessions", method: "OPTIONS", handler: httpAction(handleOptions) });
http.route({ path: "/api/v1/sessions/:id", method: "OPTIONS", handler: httpAction(handleOptions) });
http.route({ path: "/api/v1/sessions/:id/messages", method: "OPTIONS", handler: httpAction(handleOptions) });
http.route({ path: "/api/v1/messages/:id/feedback", method: "OPTIONS", handler: httpAction(handleOptions) });
http.route({ path: "/api/v1/chat", method: "OPTIONS", handler: httpAction(handleOptions) });
http.route({ path: "/api/v1/chat/stream", method: "OPTIONS", handler: httpAction(handleOptions) });
http.route({ path: "/api/v1/config/:path", method: "OPTIONS", handler: httpAction(handleOptions) });

// Auth
http.route({
  path: "/api/v1/auth/register",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = (await readJson(request)) as { username?: string; email?: string; password?: string };
    const username = body.username?.trim();
    const email = body.email?.trim().toLowerCase();
    const password = body.password;
    if (!username || !email || !password) {
      return json({ detail: "Missing username, email or password" }, 422);
    }
    if (!email.includes("@")) {
      return json({ detail: "Invalid email" }, 422);
    }

    const existing = await ctx.runQuery(api.auth.getUserByEmail, { email });
    if (existing) return json({ detail: "Email already registered" }, 409);

    const userId = await ctx.runMutation(api.auth.createUser, {
      username,
      email,
      password_hash: await hashPassword(password),
    });

    const access_token = await signJwt({ sub: userId, email }, ACCESS_TOKEN_TTL);
    const refresh_token = await signJwt({ sub: userId, type: "refresh" }, REFRESH_TOKEN_TTL);
    const refreshHash = await crypto.subtle.digest(
      "SHA-256",
      new TextEncoder().encode(refresh_token)
    );
    await ctx.runMutation(api.auth.storeRefreshToken, {
      user_id: userId,
      token_hash: Array.from(new Uint8Array(refreshHash))
        .map((b) => b.toString(16).padStart(2, "0"))
        .join(""),
      expires_at: Date.now() + REFRESH_TOKEN_TTL,
    });

    return json({ access_token, refresh_token, token_type: "bearer" });
  }),
});

http.route({
  path: "/api/v1/auth/login",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = (await readJson(request)) as { username_or_email?: string; password?: string };
    const usernameOrEmail = body.username_or_email?.trim();
    const password = body.password;
    if (!usernameOrEmail || !password) {
      return json({ detail: "Missing credentials" }, 422);
    }

    let user = await ctx.runQuery(api.auth.getUserByEmail, { email: usernameOrEmail.toLowerCase() });
    if (!user) {
      user = await ctx.runQuery(api.auth.getUserByUsername, { username: usernameOrEmail });
    }
    if (!user || !user.is_active || !(await verifyPassword(password, user.password_hash))) {
      return json({ detail: "Invalid credentials" }, 401);
    }

    const access_token = await signJwt({ sub: user._id, email: user.email }, ACCESS_TOKEN_TTL);
    const refresh_token = await signJwt({ sub: user._id, type: "refresh" }, REFRESH_TOKEN_TTL);
    const refreshHash = await crypto.subtle.digest(
      "SHA-256",
      new TextEncoder().encode(refresh_token)
    );
    await ctx.runMutation(api.auth.storeRefreshToken, {
      user_id: user._id,
      token_hash: Array.from(new Uint8Array(refreshHash))
        .map((b) => b.toString(16).padStart(2, "0"))
        .join(""),
      expires_at: Date.now() + REFRESH_TOKEN_TTL,
    });

    return json({ access_token, refresh_token, token_type: "bearer" });
  }),
});

http.route({
  path: "/api/v1/auth/refresh",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = (await readJson(request)) as { refresh_token?: string };
    if (!body.refresh_token) return json({ detail: "Missing refresh token" }, 422);

    const payload = await verifyJwt(body.refresh_token);
    if (!payload || payload.type !== "refresh" || typeof payload.sub !== "string") {
      return json({ detail: "Invalid refresh token" }, 401);
    }

    const refreshHash = await crypto.subtle.digest(
      "SHA-256",
      new TextEncoder().encode(body.refresh_token)
    );
    const tokenHash = Array.from(new Uint8Array(refreshHash))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
    const stored = await ctx.runQuery(api.auth.getRefreshToken, { token_hash: tokenHash });
    if (!stored || stored.expires_at < Date.now()) {
      return json({ detail: "Invalid refresh token" }, 401);
    }

    const user = await ctx.runQuery(api.auth.getUserById, { id: payload.sub as any });
    if (!user) return json({ detail: "User not found" }, 401);

    const access_token = await signJwt({ sub: user._id, email: user.email }, ACCESS_TOKEN_TTL);
    return json({ access_token, refresh_token: body.refresh_token, token_type: "bearer" });
  }),
});

http.route({
  path: "/api/v1/auth/me",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const user = await getCurrentUser(ctx, request);
    if (!user) return json({ detail: "Unauthorized" }, 401);
    return json({
      id: user._id,
      username: user.username,
      email: user.email,
      is_active: user.is_active,
      created_at: new Date(user._creationTime).toISOString(),
    });
  }),
});

http.route({
  path: "/api/v1/auth/logout",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = (await readJson(request)) as { refresh_token?: string };
    if (body.refresh_token) {
      const refreshHash = await crypto.subtle.digest(
        "SHA-256",
        new TextEncoder().encode(body.refresh_token)
      );
      const tokenHash = Array.from(new Uint8Array(refreshHash))
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("");
      const stored = await ctx.runQuery(api.auth.getRefreshToken, { token_hash: tokenHash });
      if (stored) {
        await ctx.runMutation(api.auth.deleteRefreshToken, { id: stored._id });
      }
    }
    return json({ ok: true });
  }),
});

// Sessions
http.route({
  path: "/api/v1/sessions",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const user = await getCurrentUser(ctx, request);
    if (!user) return json({ detail: "Unauthorized" }, 401);
    const sessions = await ctx.runQuery(api.sessions.listSessions, { user_id: user._id });
    return json(sessions);
  }),
});

http.route({
  path: "/api/v1/sessions",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const user = await getCurrentUser(ctx, request);
    if (!user) return json({ detail: "Unauthorized" }, 401);
    const body = (await readJson(request)) as { title?: string };
    const id = await ctx.runMutation(api.sessions.createSession, {
      user_id: user._id,
      title: body.title,
    });
    return json({ id });
  }),
});

http.route({
  path: "/api/v1/sessions/:id",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const user = await getCurrentUser(ctx, request);
    if (!user) return json({ detail: "Unauthorized" }, 401);
    const id = (request as any).params?.id as string;
    const session = await ctx.runQuery(api.sessions.getSession, { id: id as any });
    if (!session || session.user_id !== user._id) return json({ detail: "Not found" }, 404);
    return json(session);
  }),
});

http.route({
  path: "/api/v1/sessions/:id/messages",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const user = await getCurrentUser(ctx, request);
    if (!user) return json({ detail: "Unauthorized" }, 401);
    const id = (request as any).params?.id as string;
    const session = await ctx.runQuery(api.sessions.getSession, { id: id as any });
    if (!session || session.user_id !== user._id) return json({ detail: "Not found" }, 404);
    const messages = await ctx.runQuery(api.sessions.listMessages, { session_id: id as any });
    return json(messages);
  }),
});

http.route({
  path: "/api/v1/sessions/:id",
  method: "DELETE",
  handler: httpAction(async (ctx, request) => {
    const user = await getCurrentUser(ctx, request);
    if (!user) return json({ detail: "Unauthorized" }, 401);
    const id = (request as any).params?.id as string;
    const session = await ctx.runQuery(api.sessions.getSession, { id: id as any });
    if (!session || session.user_id !== user._id) return json({ detail: "Not found" }, 404);
    await ctx.runMutation(api.sessions.deleteSession, { id: id as any });
    return json({ ok: true });
  }),
});

http.route({
  path: "/api/v1/sessions/:id",
  method: "PATCH",
  handler: httpAction(async (ctx, request) => {
    const user = await getCurrentUser(ctx, request);
    if (!user) return json({ detail: "Unauthorized" }, 401);
    const id = (request as any).params?.id as string;
    const session = await ctx.runQuery(api.sessions.getSession, { id: id as any });
    if (!session || session.user_id !== user._id) return json({ detail: "Not found" }, 404);
    const body = (await readJson(request)) as { title?: string };
    if (body.title) {
      await ctx.runMutation(api.sessions.updateSessionTitle, { id: id as any, title: body.title });
    }
    return json({ ok: true });
  }),
});

http.route({
  path: "/api/v1/messages/:id/feedback",
  method: "PUT",
  handler: httpAction(async (ctx, request) => {
    const user = await getCurrentUser(ctx, request);
    if (!user) return json({ detail: "Unauthorized" }, 401);
    const id = (request as any).params?.id as string;
    const body = (await readJson(request)) as { feedback?: "positive" | "negative" };
    if (!body.feedback) return json({ detail: "Missing feedback" }, 422);

    const message = await ctx.runQuery(api.sessions.getMessage, { id: id as any });
    if (!message) return json({ detail: "Not found" }, 404);
    const session = await ctx.runQuery(api.sessions.getSession, { id: message.session_id });
    if (!session || session.user_id !== user._id) return json({ detail: "Not found" }, 404);

    await ctx.runMutation(api.sessions.updateMessageFeedback, { id: id as any, feedback: body.feedback });
    return json({ ok: true });
  }),
});

// Chat
http.route({
  path: "/api/v1/chat",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const user = await getCurrentUser(ctx, request);
    if (!user) return json({ detail: "Unauthorized" }, 401);

    const body = (await readJson(request)) as {
      message: string;
      session_id?: string;
      llm_config?: LLMConfig;
      personality?: Record<string, string>;
      history?: { role: string; content: string }[];
    };

    if (!body.message) return json({ detail: "Missing message" }, 422);

    let sessionId = body.session_id;
    if (!sessionId) {
      sessionId = await ctx.runMutation(api.sessions.createSession, {
        user_id: user._id,
        title: body.message.slice(0, 30),
      });
    } else {
      const session = await ctx.runQuery(api.sessions.getSession, { id: sessionId as any });
      if (!session || session.user_id !== user._id) return json({ detail: "Not found" }, 404);
    }

    await ctx.runMutation(api.sessions.addMessage, {
      session_id: sessionId as any,
      role: "user",
      content: body.message,
    });

    const history = (body.history || [])
      .filter((m) => m.role === "user" || m.role === "assistant" || m.role === "system")
      .map((m) => ({ role: m.role as "user" | "assistant" | "system", content: m.content }));

    try {
      const config = body.llm_config || getLLMConfig();
      const result = await generateChatResponse(
        config,
        body.message,
        history,
        body.personality,
        ""
      );

      await ctx.runMutation(api.sessions.addMessage, {
        session_id: sessionId as any,
        role: "assistant",
        content: result.content,
        validation_report: result.validation_report,
      });

      return json({
        content: result.content,
        session_id: sessionId,
        reasoning_steps: [],
        tool_calls: [],
        validation_report: result.validation_report,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return json({ detail: message }, 500);
    }
  }),
});

http.route({
  path: "/api/v1/chat/stream",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const user = await getCurrentUser(ctx, request);
    if (!user) return json({ detail: "Unauthorized" }, 401);

    const body = (await readJson(request)) as {
      message: string;
      session_id?: string;
      llm_config?: LLMConfig;
      personality?: Record<string, string>;
      history?: { role: string; content: string }[];
    };

    if (!body.message) return json({ detail: "Missing message" }, 422);

    let sessionId = body.session_id;
    if (!sessionId) {
      sessionId = await ctx.runMutation(api.sessions.createSession, {
        user_id: user._id,
        title: body.message.slice(0, 30),
      });
    } else {
      const session = await ctx.runQuery(api.sessions.getSession, { id: sessionId as any });
      if (!session || session.user_id !== user._id) return json({ detail: "Not found" }, 404);
    }

    await ctx.runMutation(api.sessions.addMessage, {
      session_id: sessionId as any,
      role: "user",
      content: body.message,
    });

    const history = (body.history || [])
      .filter((m) => m.role === "user" || m.role === "assistant" || m.role === "system")
      .map((m) => ({ role: m.role as "user" | "assistant" | "system", content: m.content }));

    try {
      const config = body.llm_config || getLLMConfig();
      const result = await generateChatResponse(
        config,
        body.message,
        history,
        body.personality,
        ""
      );

      await ctx.runMutation(api.sessions.addMessage, {
        session_id: sessionId as any,
        role: "assistant",
        content: result.content,
        validation_report: result.validation_report,
      });

      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(
            encoder.encode(
              `event: response\ndata: ${JSON.stringify(result.content)}\n\n`
            )
          );
          controller.enqueue(
            encoder.encode(`event: done\ndata: ${JSON.stringify({ session_id: sessionId })}\n\n`)
          );
          controller.close();
        },
      });

      return new Response(stream, {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
          ...CORS_HEADERS,
        },
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return json({ detail: message }, 500);
    }
  }),
});

export default http;
