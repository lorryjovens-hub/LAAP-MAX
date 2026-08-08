// ---- LAAP Community · DB client (Supabase) ----
// 默认用 Supabase service-role key（REST）。也可换成其它 Postgres 客户端。
// 环境变量：SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY（在 Netlify 环境变量里配置）
"use strict";

import { createClient } from "@supabase/supabase-js";

const url = process.env.SUPABASE_URL;
const key = process.env.SUPABASE_SERVICE_ROLE_KEY;

// 未配置时不抛错，便于本地 skeleton 冒烟；调用接口时才真正报错。
export const supabase = url && key ? createClient(url, key, { auth: { persistSession: false } }) : null;

export function isDbReady() {
  return !!supabase;
}