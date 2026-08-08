import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  users: defineTable({
    username: v.string(),
    email: v.string(),
    password_hash: v.string(),
    is_active: v.boolean(),
  })
    .index("by_email", ["email"])
    .index("by_username", ["username"]),

  sessions: defineTable({
    user_id: v.id("users"),
    title: v.optional(v.string()),
    created_at: v.number(),
    updated_at: v.number(),
  }).index("by_user", ["user_id"]),

  messages: defineTable({
    session_id: v.id("sessions"),
    role: v.string(), // 'user' | 'assistant' | 'system'
    content: v.string(),
    reasoning_steps: v.optional(v.array(v.any())),
    tool_calls: v.optional(v.array(v.any())),
    validation_report: v.optional(v.any()),
    feedback: v.optional(v.union(v.literal("positive"), v.literal("negative"))),
    created_at: v.number(),
  }).index("by_session", ["session_id"]),

  refresh_tokens: defineTable({
    user_id: v.id("users"),
    token_hash: v.string(),
    expires_at: v.number(),
  })
    .index("by_token_hash", ["token_hash"])
    .index("by_user", ["user_id"]),
});
