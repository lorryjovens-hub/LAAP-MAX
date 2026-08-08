import {
  clearAuthTokens,
  getAccessToken,
  getCurrentUser as authGetCurrentUser,
  isLoggedIn as authIsLoggedIn,
  AUTH_CHANGE_EVENT,
} from '@/lib/auth';
import { ensureGuestUser, type LocalUser } from '@/lib/db';
import type { User } from '@/lib/auth';

let currentUserCache: User | null = null;

function localUserToUser(user: LocalUser): User {
  return {
    id: user.id,
    username: user.username,
    email: user.email,
    is_active: true,
    created_at: user.created_at,
  };
}

function setCache(user: User) {
  currentUserCache = user;
}

function readGuestIdFromStorage(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('laap_local_user_id');
}

function readUserIdFromToken(): string | null {
  const token = getAccessToken();
  if (!token) return null;
  try {
    const base64 = token.split('.')[1]?.replace(/-/g, '+').replace(/_/g, '/');
    if (!base64) return null;
    const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4);
    const payload = JSON.parse(atob(padded)) as { sub?: unknown };
    if (typeof payload.sub === 'string') return payload.sub;
  } catch {
    // ignore
  }
  return null;
}

/**
 * 返回当前用户对象。登录用户来自 Convex JWT；未登录时返回本地游客用户。
 */
export async function getCurrentUser(): Promise<User> {
  const user = await authGetCurrentUser();
  if (user) {
    setCache(user);
    return user;
  }

  const guest = await ensureGuestUser();
  const converted = localUserToUser(guest);
  setCache(converted);
  return converted;
}

/**
 * 同步获取当前用户 ID。若尚未初始化，会回退到 localStorage 游客 ID 或
 * access token 中的 sub；仍不存在时返回空字符串，调用方应先调用
 * `getCurrentUser()` 完成初始化。
 */
export function getCurrentUserId(): string {
  if (currentUserCache) return currentUserCache.id;
  return readGuestIdFromStorage() ?? readUserIdFromToken() ?? '';
}

/**
 * 当前是否为登录用户（非游客）。
 */
export function isLoggedIn(): boolean {
  return authIsLoggedIn();
}

/**
 * 当前是否为游客。
 */
export function isGuest(): boolean {
  return !isLoggedIn();
}

/**
 * 监听身份切换事件（登录/登出/切换到游客）。返回取消订阅函数。
 */
export function onUserChange(callback: () => void): () => void {
  if (typeof window === 'undefined') return () => {};

  const handler = () => {
    currentUserCache = null;
    callback();
  };

  window.addEventListener(AUTH_CHANGE_EVENT, handler);
  return () => window.removeEventListener(AUTH_CHANGE_EVENT, handler);
}

/**
 * 切换到游客身份。会清除登录 token 并确保本地游客用户存在。
 * 通常在登出后调用。
 */
export async function switchToGuest(): Promise<void> {
  clearAuthTokens();
  const guest = await ensureGuestUser();
  setCache(localUserToUser(guest));
}
