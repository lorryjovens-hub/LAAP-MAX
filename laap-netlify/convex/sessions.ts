/** Convex internal functions for sessions and messages. */

import { v } from "convex/values";
import { internalMutation, internalQuery } from "./_generated/server";

export const createSession = internalMutation({
  args: {
    user_id: v.id("users"),
    title: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const now = Date.now();
    return await ctx.db.insert("sessions", {
      user_id: args.user_id,
      title: args.title || "新对话",
      created_at: now,
      updated_at: now,
    });
  },
});

export const listSessions = internalQuery({
  args: { user_id: v.id("users") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("sessions")
      .withIndex("by_user", (q) => q.eq("user_id", args.user_id))
      .order("desc")
      .take(100);
  },
});

export const getSession = internalQuery({
  args: { id: v.id("sessions") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const getMessage = internalQuery({
  args: { id: v.id("messages") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const updateSessionTitle = internalMutation({
  args: {
    id: v.id("sessions"),
    title: v.string(),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, { title: args.title, updated_at: Date.now() });
  },
});

export const deleteSession = internalMutation({
  args: { id: v.id("sessions") },
  handler: async (ctx, args) => {
    const messages = await ctx.db
      .query("messages")
      .withIndex("by_session", (q) => q.eq("session_id", args.id))
      .collect();
    for (const msg of messages) {
      await ctx.db.delete(msg._id);
    }
    await ctx.db.delete(args.id);
  },
});

export const addMessage = internalMutation({
  args: {
    session_id: v.id("sessions"),
    role: v.string(),
    content: v.string(),
    reasoning_steps: v.optional(v.array(v.any())),
    tool_calls: v.optional(v.array(v.any())),
    validation_report: v.optional(v.any()),
  },
  handler: async (ctx, args) => {
    const now = Date.now();
    await ctx.db.insert("messages", { ...args, created_at: now });
    await ctx.db.patch(args.session_id, { updated_at: now });
  },
});

export const listMessages = internalQuery({
  args: { session_id: v.id("sessions") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("messages")
      .withIndex("by_session", (q) => q.eq("session_id", args.session_id))
      .order("asc")
      .take(200);
  },
});

export const updateMessageFeedback = internalMutation({
  args: {
    id: v.id("messages"),
    feedback: v.union(v.literal("positive"), v.literal("negative")),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, { feedback: args.feedback });
  },
});
