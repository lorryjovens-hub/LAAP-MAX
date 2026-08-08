import { LOCAL_ONLY } from '@/lib/env';
import {
  ensureGuestUser,
  createLocalAccount,
  findLocalAccount,
  verifyLocalAccountPassword,
  signInLocalAccount,
  signOutLocalAccount,
  isLocalAccountAuthenticated,
  getAuthenticatedLocalUser,
  updateLocalUsername,
} from '@/lib/db';
import type { LocalUser } from '@/lib/db';
import { broadcastSync } from '@/lib/syncManager';

export interface User {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

interface TokenPayload {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

import { API_BASE_URL } from '@/lib/env';

const ACCESS_TOKEN_KEY = 'laap_access_token';
const REFRESH_TOKEN_KEY = 'laap_refresh_token';
export const AUTH_CHANGE_EVENT = 'laap:auth-change';

let memoryAccessToken: string | null = null;
let refreshPromise: Promise<string | null> | null = null;

export function notifyAuthChange() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(AUTH_CHANGE_EVENT));
  }
}

export function getAccessToken(): string | null {
  if (memoryAccessToken) return memoryAccessToken;
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function setAccessToken(token: string | null) {
  memoryAccessToken = token;
  if (typeof window === 'undefined') return;
  if (token) {
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
  } else {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
  }
}

function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

function setRefreshToken(token: string | null) {
  if (typeof window === 'undefined') return;
  if (token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  } else {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
}

function setTokens(payload: TokenPayload) {
  setAccessToken(payload.access_token);
  setRefreshToken(payload.refresh_token);
}

function clearTokens() {
  setAccessToken(null);
  setRefreshToken(null);
  notifyAuthChange();
}

export function clearAuthTokens() {
  clearTokens();
}

function localUserToUser(user: LocalUser): User {
  return {
    id: user.id,
    username: user.username,
    email: user.email,
    is_active: true,
    created_at: user.created_at,
  };
}

async function parseError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (data.detail) {
      if (Array.isArray(data.detail)) {
        return data.detail.map((d: { msg?: string; loc?: string[] }) => d.msg || JSON.stringify(d)).join('; ');
      }
      return String(data.detail);
    }
    if (data.message) return String(data.message);
  } catch {
    // ignore
  }
  return `请求失败 (${response.status})`;
}

export async function apiFetch(
  input: RequestInfo | URL,
  init: RequestInit = {}
): Promise<Response> {
  const url = typeof input === 'string' && input.startsWith('http')
    ? input
    : `${API_BASE_URL}${typeof input === 'string' ? input : ''}`;

  const headers = new Headers(init.headers);
  if (!headers.has('Content-Type') && init.body && typeof init.body === 'string') {
    headers.set('Content-Type', 'application/json');
  }

  const token = getAccessToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(url, { ...init, headers });

  if (response.status === 401) {
    const newToken = await refreshTokenInternal();
    if (newToken) {
      headers.set('Authorization', `Bearer ${newToken}`);
      return fetch(url, { ...init, headers });
    }
    clearTokens();
  }

  return response;
}

async function refreshTokenInternal(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;

  const refreshTokenValue = getRefreshToken();
  if (!refreshTokenValue) return null;

  refreshPromise = (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshTokenValue }),
      });

      if (!response.ok) {
        return null;
      }

      const data: TokenPayload = await response.json();
      setAccessToken(data.access_token);
      if (data.refresh_token) {
        setRefreshToken(data.refresh_token);
      }
      notifyAuthChange();
      return data.access_token;
    } catch {
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export async function refreshToken(): Promise<{ ok: true; accessToken: string } | { ok: false; error: string }> {
  const token = await refreshTokenInternal();
  if (token) {
    return { ok: true, accessToken: token };
  }
  clearTokens();
  return { ok: false, error: '刷新令牌已失效，请重新登录' };
}

export async function register(
  username: string,
  email: string,
  password: string
): Promise<{ ok: true; user: User } | { ok: false; error: string }> {
  if (LOCAL_ONLY) {
    // 本地模式：账户存 IndexedDB，密码哈希存储
    try {
      const account = await createLocalAccount(username, email, password);
      const localUser = await signInLocalAccount(account);
      const user = localUserToUser(localUser);
      notifyAuthChange();
      broadcastSync('user-changed', { userId: user.id, action: 'register' });
      return { ok: true, user };
    } catch (err) {
      return { ok: false, error: err instanceof Error ? err.message : '注册失败' };
    }
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.trim(), email: email.trim().toLowerCase(), password }),
    });

    if (!response.ok) {
      return { ok: false, error: await parseError(response) };
    }

    const data: TokenPayload = await response.json();
    setTokens(data);
    const user = await fetchCurrentUser();
    if (!user) {
      return { ok: false, error: '注册成功但无法获取用户信息' };
    }
    notifyAuthChange();
    broadcastSync('user-changed', { userId: user.id, action: 'register' });
    return { ok: true, user };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : '网络错误' };
  }
}

export async function login(
  emailOrUsername: string,
  password: string
): Promise<{ ok: true; user: User } | { ok: false; error: string }> {
  if (LOCAL_ONLY) {
    // 本地模式：在 IndexedDB 中查找账户并校验密码
    try {
      const account = await findLocalAccount(emailOrUsername);
      if (!account) {
        return { ok: false, error: '账户不存在，请先注册' };
      }
      const valid = await verifyLocalAccountPassword(account, password);
      if (!valid) {
        return { ok: false, error: '密码错误' };
      }
      const localUser = await signInLocalAccount(account);
      const user = localUserToUser(localUser);
      notifyAuthChange();
      broadcastSync('user-changed', { userId: user.id, action: 'login' });
      return { ok: true, user };
    } catch (err) {
      return { ok: false, error: err instanceof Error ? err.message : '登录失败' };
    }
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username_or_email: emailOrUsername.trim(), password }),
    });

    if (!response.ok) {
      return { ok: false, error: await parseError(response) };
    }

    const data: TokenPayload = await response.json();
    setTokens(data);
    const user = await fetchCurrentUser();
    if (!user) {
      return { ok: false, error: '登录成功但无法获取用户信息' };
    }
    notifyAuthChange();
    broadcastSync('user-changed', { userId: user.id, action: 'login' });
    return { ok: true, user };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : '网络错误' };
  }
}

async function fetchCurrentUser(): Promise<User | null> {
  try {
    const response = await apiFetch('/api/v1/auth/me');
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

export async function getCurrentUser(): Promise<User | null> {
  if (LOCAL_ONLY) {
    // 1) 优先返回已登录的本地账户
    if (isLocalAccountAuthenticated()) {
      const authed = await getAuthenticatedLocalUser();
      if (authed) return localUserToUser(authed);
      // 标记存在但用户记录丢失 —— 清理状态后回退到游客
      signOutLocalAccount();
    }
    // 2) 回退到本地游客身份
    try {
      const local = await ensureGuestUser();
      return localUserToUser(local);
    } catch {
      return null;
    }
  }

  if (getAccessToken()) {
    const user = await fetchCurrentUser();
    if (user) return user;
    // Token is invalid or expired; fall back to the local guest identity.
    clearTokens();
  }

  try {
    const local = await ensureGuestUser();
    return localUserToUser(local);
  } catch {
    return null;
  }
}

function isAccessTokenValid(token: string): boolean {
  try {
    const base64 = token.split('.')[1]?.replace(/-/g, '+').replace(/_/g, '/');
    if (!base64) return false;
    const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4);
    const payload = JSON.parse(atob(padded)) as { exp?: number };
    if (typeof payload.exp === 'number' && payload.exp * 1000 < Date.now()) return false;
    return true;
  } catch {
    return false;
  }
}

/**
 * 更新当前用户的显示名称（仅本地模式支持）。返回更新后的 User，
 * 更新失败时返回 null。
 */
export async function updateUsername(username: string): Promise<User | null> {
  const user = await getCurrentUser();
  if (!user) return null;
  const updated = await updateLocalUsername(user.id, username);
  if (!updated) return null;
  const converted = localUserToUser(updated);
  notifyAuthChange();
  broadcastSync('user-changed', { userId: user.id, action: 'update' });
  return converted;
}

export function isLoggedIn(): boolean {
  if (LOCAL_ONLY) return isLocalAccountAuthenticated();
  const token = getAccessToken();
  return !!token && isAccessTokenValid(token);
}

export async function logout(): Promise<void> {
  if (LOCAL_ONLY) {
    signOutLocalAccount();
    // 退出后自动切换到游客身份（确保 sessions 等仍可工作）
    await ensureGuestUser();
    notifyAuthChange();
    broadcastSync('user-changed', { action: 'logout' });
    return;
  }

  const refreshTokenValue = getRefreshToken();
  if (refreshTokenValue) {
    try {
      await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshTokenValue }),
      });
    } catch {
      // ignore
    }
  }
  clearTokens();
  broadcastSync('user-changed', { action: 'logout' });
}
