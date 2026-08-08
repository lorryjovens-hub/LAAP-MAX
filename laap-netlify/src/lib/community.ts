// ---- LAAP Community · 云端社区 API 客户端 ----
// 对接 Netlify Function community-api（/api/* 被转发到 .netlify/functions/community-api）。
// 会话：JWT，存于 localStorage。

const TOKEN_KEY = 'laap_community_token';
const USER_KEY = 'laap_community_user';

export interface CommunityUser {
  id: string;
  email: string;
  name: string;
  avatar_url?: string | null;
  bio?: string | null;
  created_at?: string;
}

export interface CommunityWork {
  id: string;
  owner_id: string;
  title: string;
  description?: string | null;
  type: 'webapp' | 'site' | 'game';
  size?: number;
  tags: string[];
  likes: number;
  plays: number;
  status: string;
  published_at?: string;
  updated_at?: string;
}

export interface CommunityComment {
  id: string;
  text: string;
  created_at?: string;
  author: string;
}

export interface WorkListResult {
  works: CommunityWork[];
  page: number;
  total: number;
  hasMore: boolean;
}

function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
function setToken(t: string | null) {
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
}

export function getCommunityUser(): CommunityUser | null {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null');
  } catch {
    return null;
  }
}
function setCommunityUser(u: CommunityUser | null) {
  if (u) localStorage.setItem(USER_KEY, JSON.stringify(u));
  else localStorage.removeItem(USER_KEY);
}

export function isCommunityLoggedIn(): boolean {
  return !!getToken() && !!getCommunityUser();
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`/api${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  const text = await res.text();
  let json: any = {};
  try {
    json = text ? JSON.parse(text) : {};
  } catch {
    json = { raw: text };
  }
  if (!res.ok) throw new Error((json as any).error || `请求失败 (${res.status})`);
  return json as T;
}

export function communityAuthStore() {
  return {
    logout: () => {
      setToken(null);
      setCommunityUser(null);
      window.dispatchEvent(new Event('laap-community-auth'));
    },
  };
}

// ── 认证 ───────────────────────────────────────────────
export async function communityRegister(email: string, password: string, name: string): Promise<CommunityUser> {
  const r = await request<{ token: string; user: CommunityUser }>('POST', '/auth/register', { email, password, name });
  setToken(r.token);
  setCommunityUser(r.user);
  window.dispatchEvent(new Event('laap-community-auth'));
  return r.user;
}

export async function communityLogin(email: string, password: string): Promise<CommunityUser> {
  const r = await request<{ token: string; user: CommunityUser }>('POST', '/auth/login', { email, password });
  setToken(r.token);
  setCommunityUser(r.user);
  window.dispatchEvent(new Event('laap-community-auth'));
  return r.user;
}

export function communityLogout() {
  communityAuthStore().logout();
}

// ── 作品 ───────────────────────────────────────────────
export async function communityListWorks(params: { page?: number; limit?: number; type?: string; tag?: string; mine?: boolean } = {}): Promise<WorkListResult> {
  const qs = new URLSearchParams();
  if (params.page !== undefined) qs.set('page', String(params.page));
  if (params.limit !== undefined) qs.set('limit', String(params.limit));
  if (params.type) qs.set('type', params.type);
  if (params.tag) qs.set('tag', params.tag);
  if (params.mine) qs.set('mine', '1');
  const s = qs.toString();
  return request<WorkListResult>('GET', `/works${s ? '?' + s : ''}`);
}

export async function communityGetWork(id: string): Promise<CommunityWork> {
  const r = await request<{ work: CommunityWork }>('GET', `/works/${id}`);
  return r.work;
}

export async function communityPublish(input: {
  title: string;
  description?: string;
  type?: string;
  tags?: string[];
  fileBase64: string;
}): Promise<CommunityWork> {
  const r = await request<{ work: CommunityWork }>('POST', '/works', input);
  return r.work;
}

export async function communityDeleteWork(id: string): Promise<void> {
  await request<{ ok: boolean }>('DELETE', `/works/${id}`);
}

// ── 互动 ───────────────────────────────────────────────
export async function communityLike(id: string): Promise<{ liked: boolean; likes: number }> {
  return request<{ liked: boolean; likes: number }>('POST', `/works/${id}/like`, {});
}

export async function communityPlay(id: string): Promise<{ plays: number }> {
  try {
    return await request<{ plays: number }>('POST', `/works/${id}/play`, {});
  } catch {
    return { plays: 0 };
  }
}

export async function communityListComments(id: string): Promise<CommunityComment[]> {
  const r = await request<{ comments: CommunityComment[] }>('GET', `/works/${id}/comments`);
  return r.comments;
}

export async function communityAddComment(id: string, text: string): Promise<CommunityComment> {
  const r = await request<{ comment: CommunityComment }>('POST', `/works/${id}/comments`, { text });
  return r.comment;
}

// 作品文件 URL（iframe 内嵌游玩）
export function communityWorkUrl(id: string, path = 'index.html'): string {
  return `/api/works/${id}/files/${path}`;
}