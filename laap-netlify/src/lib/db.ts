import { openDB, type DBSchema, type IDBPDatabase } from 'idb';
import { broadcastSync } from '@/lib/syncManager';

export interface LocalUser {
  id: string;
  username: string;
  email: string;
  created_at: string;
}

export interface LocalAccount {
  id: string;
  username: string;
  email: string;
  password_hash: string;
  created_at: string;
}

export interface LocalSession {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface LocalAttachment {
  id: string;
  type: 'image' | 'text' | 'file' | 'document';
  name: string;
  mimeType: string;
  content: string;
  pages?: number;
  wordCount?: number;
  size?: number;
}

export interface LocalMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  attachments?: LocalAttachment[];
  reasoning_steps?: Record<string, unknown>[];
  tool_calls?: Record<string, unknown>[];
  hallucination_report?: Record<string, unknown>;
  feedback?: 'positive' | 'negative' | null;
  created_at: string;
}

export interface LocalMemory {
  id: string;
  user_id: string;
  content: string;
  memory_type: string;
  source?: string;
  priority?: number;
  created_at: string;
}

interface LaapDB extends DBSchema {
  users: {
    key: string;
    value: LocalUser;
  };
  accounts: {
    key: string;
    value: LocalAccount;
    indexes: { by_username: string; by_email: string };
  };
  sessions: {
    key: string;
    value: LocalSession;
    indexes: { user_id: string };
  };
  messages: {
    key: string;
    value: LocalMessage;
    indexes: { session_id: string };
  };
  memories: {
    key: string;
    value: LocalMemory;
    indexes: { user_id: string };
  };
  configs: {
    key: string;
    value: { key: string; value: unknown };
  };
}

const DB_NAME = 'laap-studio-local';
const DB_VERSION = 3;

let dbPromise: Promise<IDBPDatabase<LaapDB>> | null = null;

export function getDb(): Promise<IDBPDatabase<LaapDB>> {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('IndexedDB is only available in the browser'));
  }
  if (dbPromise) return dbPromise;
  dbPromise = openDB<LaapDB>(DB_NAME, DB_VERSION, {
    async upgrade(db, oldVersion) {
      if (oldVersion < 1) {
        db.createObjectStore('users', { keyPath: 'id' });

        const sessionStore = db.createObjectStore('sessions', { keyPath: 'id' });
        sessionStore.createIndex('user_id', 'user_id', { unique: false });

        const messageStore = db.createObjectStore('messages', { keyPath: 'id' });
        messageStore.createIndex('session_id', 'session_id', { unique: false });

        const memoryStore = db.createObjectStore('memories', { keyPath: 'id' });
        memoryStore.createIndex('user_id', 'user_id', { unique: false });

        db.createObjectStore('configs', { keyPath: 'key' });
      }

      if (oldVersion < 3) {
        // v3: introduce named local accounts (LOCAL_ONLY 模式下支持注册/登录).
        // v2 was an in-memory no-op upgrade; v3 carries the actual schema change.
        if (!db.objectStoreNames.contains('accounts')) {
          const accountStore = db.createObjectStore('accounts', { keyPath: 'id' });
          accountStore.createIndex('by_username', 'username', { unique: true });
          accountStore.createIndex('by_email', 'email', { unique: true });
        }
      }

      // Version 2 adds the optional `priority` field to memory records.
      // Existing records without priority are normalized to 5 at read time
      // via listLocalMemories, so no data migration is required here.
    },
  });
  return dbPromise;
}

const LOCAL_USER_ID_KEY = 'laap_local_user_id';

export async function getCurrentGuestUser(): Promise<LocalUser | undefined> {
  const id = localStorage.getItem(LOCAL_USER_ID_KEY);
  if (!id) return undefined;
  const db = await getDb();
  return db.get('users', id);
}

export async function ensureGuestUser(): Promise<LocalUser> {
  const existing = await getCurrentGuestUser();
  if (existing) return existing;

  const id = `guest_${crypto.randomUUID()}`;
  const user: LocalUser = {
    id,
    username: `guest_${id.slice(7, 15)}`,
    email: `${id}@laap.local`,
    created_at: new Date().toISOString(),
  };
  const db = await getDb();
  await db.put('users', user);
  localStorage.setItem(LOCAL_USER_ID_KEY, user.id);
  return user;
}

// Backward-compatible aliases used by existing call sites.
export const ensureLocalUser = ensureGuestUser;

export async function clearGuestData(): Promise<void> {
  const user = await getCurrentGuestUser();
  if (!user) return;

  const db = await getDb();
  const userId = user.id;

  const sessions = await db.getAllFromIndex('sessions', 'user_id', userId);
  await Promise.all(sessions.map((s) => deleteLocalSession(s.id)));

  const memories = await db.getAllFromIndex('memories', 'user_id', userId);
  await Promise.all(memories.map((m) => db.delete('memories', m.id)));

  const configKeys = await db.getAllKeys('configs');
  const prefix = `${userId}:`;
  await Promise.all(
    configKeys
      .filter((k): k is string => typeof k === 'string' && k.startsWith(prefix))
      .map((k) => db.delete('configs', k))
  );
}

async function resolveGuestUserId(userId?: string): Promise<string> {
  if (userId) return userId;
  const user = await ensureGuestUser();
  return user.id;
}

export async function listLocalSessions(userId?: string): Promise<LocalSession[]> {
  const resolvedUserId = await resolveGuestUserId(userId);
  const db = await getDb();
  const sessions = await db.getAllFromIndex('sessions', 'user_id', resolvedUserId);
  return sessions.sort((a, b) => b.updated_at.localeCompare(a.updated_at));
}

export async function createLocalSession(userId?: string, title = '新对话'): Promise<LocalSession> {
  const resolvedUserId = await resolveGuestUserId(userId);
  const now = new Date().toISOString();
  const session: LocalSession = {
    id: crypto.randomUUID(),
    user_id: resolvedUserId,
    title,
    created_at: now,
    updated_at: now,
  };
  const db = await getDb();
  await db.add('sessions', session);
  broadcastSync('session-updated', { sessionId: session.id, userId: resolvedUserId });
  return session;
}

export async function getLocalSession(sessionId: string): Promise<LocalSession | undefined> {
  const db = await getDb();
  return db.get('sessions', sessionId);
}

export async function updateLocalSession(sessionId: string, updates: Partial<LocalSession>): Promise<void> {
  const db = await getDb();
  const existing = await db.get('sessions', sessionId);
  if (!existing) return;
  await db.put('sessions', { ...existing, ...updates, id: sessionId });
}

export async function deleteLocalSession(sessionId: string): Promise<void> {
  const db = await getDb();
  await db.delete('sessions', sessionId);
  const messages = await db.getAllFromIndex('messages', 'session_id', sessionId);
  await Promise.all(messages.map((m) => db.delete('messages', m.id)));
  broadcastSync('session-updated', { sessionId });
}

export async function listLocalMessages(sessionId: string, userId?: string): Promise<LocalMessage[]> {
  const resolvedUserId = await resolveGuestUserId(userId);
  const db = await getDb();
  const session = await db.get('sessions', sessionId);
  if (!session || session.user_id !== resolvedUserId) return [];
  const messages = await db.getAllFromIndex('messages', 'session_id', sessionId);
  return messages.sort((a, b) => a.created_at.localeCompare(b.created_at));
}

export async function addLocalMessage(
  sessionId: string,
  message: Omit<LocalMessage, 'id' | 'session_id' | 'created_at'>,
  userId?: string
): Promise<LocalMessage> {
  const resolvedUserId = await resolveGuestUserId(userId);
  const db = await getDb();
  const session = await db.get('sessions', sessionId);
  if (!session || session.user_id !== resolvedUserId) {
    throw new Error('Session not found for current user');
  }
  const now = new Date().toISOString();
  const record: LocalMessage = {
    ...message,
    id: crypto.randomUUID(),
    session_id: sessionId,
    created_at: now,
  };
  await db.add('messages', record);
  await db.put('sessions', { ...session, updated_at: now });
  broadcastSync('session-updated', { sessionId, messageId: record.id, userId: resolvedUserId });
  return record;
}

export async function updateLocalMessage(
  messageId: string,
  updates: Partial<Omit<LocalMessage, 'id' | 'session_id' | 'created_at'>>
): Promise<LocalMessage | undefined> {
  const db = await getDb();
  const existing = await db.get('messages', messageId);
  if (!existing) return undefined;
  const updated: LocalMessage = { ...existing, ...updates };
  await db.put('messages', updated);
  return updated;
}

export async function listLocalMemories(userId: string, limit = 10): Promise<LocalMemory[]> {
  const db = await getDb();
  const memories = await db.getAllFromIndex('memories', 'user_id', userId);
  return memories
    .map((m) => ({ ...m, priority: typeof m.priority === 'number' ? m.priority : 5 }))
    .sort((a, b) => b.created_at.localeCompare(a.created_at))
    .slice(0, limit);
}

export async function addLocalMemory(
  userId: string,
  content: string,
  memoryType = 'chat',
  source?: string,
  priority = 5
): Promise<LocalMemory> {
  const db = await getDb();
  const memory: LocalMemory = {
    id: crypto.randomUUID(),
    user_id: userId,
    content: content.trim().slice(0, 1000),
    memory_type: memoryType,
    source,
    priority: Math.min(10, Math.max(0, priority)),
    created_at: new Date().toISOString(),
  };
  await db.add('memories', memory);
  broadcastSync('memory-updated', { memoryId: memory.id, userId });
  return memory;
}

function configStoreKey(userId: string, key: string): string {
  return `${userId}:${key}`;
}

export async function getLocalConfig<T>(key: string, userId?: string): Promise<T | null> {
  const resolvedUserId = await resolveGuestUserId(userId);
  const db = await getDb();
  const scopedKey = configStoreKey(resolvedUserId, key);
  const scoped = await db.get('configs', scopedKey);
  if (scoped) return scoped.value as T;

  // Backward compatibility: migrate a pre-isolation global config into the
  // current guest's namespace, then remove the global entry.
  const legacy = await db.get('configs', key);
  if (legacy) {
    await db.put('configs', { key: scopedKey, value: legacy.value });
    await db.delete('configs', key);
    return legacy.value as T;
  }

  return null;
}

export async function setLocalConfig<T>(key: string, value: T, userId?: string): Promise<void> {
  const resolvedUserId = await resolveGuestUserId(userId);
  const db = await getDb();
  const scopedKey = configStoreKey(resolvedUserId, key);
  await db.put('configs', { key: scopedKey, value });
  broadcastSync('settings-updated', { key, userId: resolvedUserId });
  // Remove the pre-isolation global entry if it exists so later reads cannot
  // fall back to a shared value.
  try {
    await db.delete('configs', key);
  } catch {
    // Ignore failures when there is no legacy entry.
  }
}

// ============================================================================
// 本地账户（LOCAL_ONLY 模式下的注册/登录支持）
// ============================================================================

const LOCAL_AUTH_USER_ID_KEY = 'laap_local_account_user_id';
const LOCAL_AUTH_FLAG_KEY = 'laap_local_account_authenticated';

/**
 * 创建本地命名账户。用户名与邮箱在 IndexedDB 中唯一。
 * 密码以 SHA-256 哈希存储，明文绝不落盘。
 */
export async function createLocalAccount(
  username: string,
  email: string,
  password: string
): Promise<LocalAccount> {
  const db = await getDb();
  const normalizedEmail = email.trim().toLowerCase();
  const normalizedUsername = username.trim();

  const existingByUsername = await db.getFromIndex('accounts', 'by_username', normalizedUsername);
  if (existingByUsername) throw new Error('用户名已被注册');
  const existingByEmail = await db.getFromIndex('accounts', 'by_email', normalizedEmail);
  if (existingByEmail) throw new Error('邮箱已被注册');

  const account: LocalAccount = {
    id: `user_${crypto.randomUUID()}`,
    username: normalizedUsername,
    email: normalizedEmail,
    password_hash: await sha256(password),
    created_at: new Date().toISOString(),
  };
  await db.add('accounts', account);
  return account;
}

/**
 * 通过用户名或邮箱查找本地账户。
 */
export async function findLocalAccount(identifier: string): Promise<LocalAccount | undefined> {
  const db = await getDb();
  const normalized = identifier.trim().toLowerCase();
  if (!normalized) return undefined;
  const byEmail = await db.getFromIndex('accounts', 'by_email', normalized);
  if (byEmail) return byEmail;
  // 用户名大小写敏感时回退到原始值
  const byUsername = await db.getFromIndex('accounts', 'by_username', identifier.trim());
  return byUsername;
}

/**
 * 校验密码与账户哈希是否匹配。
 */
export async function verifyLocalAccountPassword(
  account: LocalAccount,
  password: string
): Promise<boolean> {
  const hash = await sha256(password);
  return hash === account.password_hash;
}

/**
 * 将当前浏览器会话切换到指定账户身份。
 * 这会把 `laap_local_user_id` 指向该账户 ID，并在 users 表中
 * 创建/更新对应的 LocalUser 记录，从而让 sessions / messages / configs
 * 自动按该用户 ID 隔离。
 */
export async function signInLocalAccount(account: LocalAccount): Promise<LocalUser> {
  const db = await getDb();
  const user: LocalUser = {
    id: account.id,
    username: account.username,
    email: account.email,
    created_at: account.created_at,
  };
  await db.put('users', user);
  localStorage.setItem(LOCAL_USER_ID_KEY, account.id);
  localStorage.setItem(LOCAL_AUTH_USER_ID_KEY, account.id);
  localStorage.setItem(LOCAL_AUTH_FLAG_KEY, '1');
  return user;
}

/**
 * 更新本地用户的显示名称。同时同步更新对应的命名账户（若存在），
 * 返回更新后的 LocalUser；用户不存在时返回 undefined。
 */
export async function updateLocalUsername(
  userId: string,
  username: string
): Promise<LocalUser | undefined> {
  const trimmed = username.trim();
  if (!trimmed) return undefined;
  const db = await getDb();
  const existing = await db.get('users', userId);
  if (!existing) return undefined;

  const updated: LocalUser = { ...existing, username: trimmed };
  await db.put('users', updated);

  // 若该用户是对应命名账户，同步账户表中的用户名，保持唯一索引一致。
  const account = await db.get('accounts', userId);
  if (account) {
    await db.put('accounts', { ...account, username: trimmed });
  }
  return updated;
}

/**
 * 退出本地账户身份：清除认证标记，下次访问会自动生成新游客。
 */
export function signOutLocalAccount(): void {
  localStorage.removeItem(LOCAL_AUTH_USER_ID_KEY);
  localStorage.removeItem(LOCAL_AUTH_FLAG_KEY);
  // 不清除 laap_local_user_id —— 保留游客身份继续可用。
}

/**
 * 当前是否已通过本地账户登录（非游客）。
 */
export function isLocalAccountAuthenticated(): boolean {
  if (typeof window === 'undefined') return false;
  return localStorage.getItem(LOCAL_AUTH_FLAG_KEY) === '1'
    && !!localStorage.getItem(LOCAL_AUTH_USER_ID_KEY);
}

/**
 * 获取当前已登录的本地账户对应的 LocalUser。
 */
export async function getAuthenticatedLocalUser(): Promise<LocalUser | undefined> {
  if (!isLocalAccountAuthenticated()) return undefined;
  const id = localStorage.getItem(LOCAL_AUTH_USER_ID_KEY);
  if (!id) return undefined;
  const db = await getDb();
  return db.get('users', id);
}

async function sha256(text: string): Promise<string> {
  if (typeof crypto === 'undefined' || !crypto.subtle) {
    // 回退到简单哈希（仅在非 HTTPS 环境下）
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
      hash = ((hash << 5) - hash) + text.charCodeAt(i);
      hash |= 0;
    }
    return `fallback_${hash.toString(16)}`;
  }
  const encoder = new TextEncoder();
  const data = encoder.encode(text);
  const buffer = await crypto.subtle.digest('SHA-256', data);
  return Array.from(new Uint8Array(buffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}
