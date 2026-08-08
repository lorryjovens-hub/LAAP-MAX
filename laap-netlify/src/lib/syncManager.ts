/**
 * 跨窗口/标签页同步管理器。
 *
 * 同一用户在多个窗口中操作时（游客走本地 IndexedDB，登录用户走 Convex），
 * 通过 BroadcastChannel（优先）或 storage 事件（fallback）广播数据变更，
 * 其他窗口收到后刷新本地视图，避免循环广播。
 */

export type SyncEventType =
  | 'memory-updated'
  | 'session-updated'
  | 'settings-updated'
  | 'personality-updated'
  | 'user-changed';

interface SyncMessage {
  event: SyncEventType;
  payload?: unknown;
  source: string;
  timestamp: number;
}

const CHANNEL_NAME = 'laap-studio-sync';
const STORAGE_KEY_PREFIX = 'laap:sync:';

let channel: BroadcastChannel | null = null;

function getChannel(): BroadcastChannel | null {
  if (typeof window === 'undefined') return null;
  if (!channel && 'BroadcastChannel' in window) {
    try {
      channel = new BroadcastChannel(CHANNEL_NAME);
    } catch {
      channel = null;
    }
  }
  return channel;
}

function generateSource(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

let sourceId = '';

function getSourceId(): string {
  if (!sourceId) sourceId = generateSource();
  return sourceId;
}

function buildStorageKey(event: SyncEventType): string {
  return `${STORAGE_KEY_PREFIX}${event}`;
}

/**
 * 向同源其他窗口广播同步事件。
 *
 * @param event 事件类型
 * @param payload 可选的附加数据
 */
export function broadcastSync(event: SyncEventType, payload?: unknown): void {
  if (typeof window === 'undefined') return;

  const message: SyncMessage = {
    event,
    payload,
    source: getSourceId(),
    timestamp: Date.now(),
  };

  const bc = getChannel();
  if (bc) {
    try {
      bc.postMessage(message);
    } catch {
      // ignore
    }
    return;
  }

  // Fallback: storage 事件
  try {
    const key = buildStorageKey(event);
    localStorage.setItem(key, JSON.stringify(message));
    // 立即移除，避免污染 localStorage 并允许再次触发同名事件
    localStorage.removeItem(key);
  } catch {
    // ignore
  }
}

/**
 * 订阅跨窗口同步事件。返回取消订阅函数。
 *
 * @param callback 收到同步事件时的回调
 */
export function onSyncEvent(
  callback: (event: SyncEventType, payload?: unknown) => void
): () => void {
  if (typeof window === 'undefined') return () => {};

  const localSource = getSourceId();

  const handleMessage = (ev: MessageEvent<unknown>) => {
    const message = ev.data as SyncMessage | undefined;
    if (!message || message.source === localSource) return;
    if (message.timestamp && Date.now() - message.timestamp > 5000) return;
    callback(message.event, message.payload);
  };

  const handleStorage = (ev: StorageEvent) => {
    if (!ev.key || !ev.key.startsWith(STORAGE_KEY_PREFIX)) return;
    if (!ev.newValue) return;
    try {
      const message = JSON.parse(ev.newValue) as SyncMessage;
      if (!message || message.source === localSource) return;
      if (message.timestamp && Date.now() - message.timestamp > 5000) return;
      callback(message.event, message.payload);
    } catch {
      // ignore malformed storage payload
    }
  };

  const bc = getChannel();
  if (bc) {
    bc.addEventListener('message', handleMessage);
  }

  window.addEventListener('storage', handleStorage);

  return () => {
    if (bc) {
      bc.removeEventListener('message', handleMessage);
    }
    window.removeEventListener('storage', handleStorage);
  };
}
