export interface CorsProxyOptions {
  proxyUrl?: string;
  timeoutMs?: number;
  maxLength?: number;
}

const DEFAULT_TIMEOUT_MS = 15_000;
const DEFAULT_MAX_LENGTH = 12_000;

const BUILTIN_PROXIES = [
  'https://api.allorigins.win/raw?url=',
  'https://corsproxy.io/?',
];

function normalizeUrl(url: string): string {
  const trimmed = url.trim();
  if (!trimmed) return '';
  if (/^[a-z][+a-z0-9-]*:\/\//i.test(trimmed)) {
    return trimmed;
  }
  return `https://${trimmed}`;
}

export function getProxiedUrl(url: string, options?: CorsProxyOptions): string {
  const targetUrl = normalizeUrl(url);
  if (!targetUrl) return url;
  const proxyUrl = options?.proxyUrl?.trim() || BUILTIN_PROXIES[0];
  return `${proxyUrl}${encodeURIComponent(targetUrl)}`;
}

export function isUrlBlacklisted(url: string): boolean {
  const trimmed = url.trim();
  if (!trimmed) return true;

  if (trimmed.toLowerCase().startsWith('file://')) return true;

  let target = trimmed;
  if (!/^[a-z][+a-z0-9-]*:\/\//i.test(target)) {
    target = `https://${target}`;
  }

  let hostname: string;
  try {
    hostname = new URL(target).hostname.toLowerCase();
  } catch {
    return true;
  }

  if (hostname === 'localhost') return true;

  const ipParts = hostname.split('.').map((part) => Number.parseInt(part, 10));
  if (ipParts.length === 4 && ipParts.every((p) => Number.isFinite(p) && p >= 0 && p <= 255)) {
    if (ipParts[0] === 127) return true;
    if (ipParts[0] === 10) return true;
    if (ipParts[0] === 172 && ipParts[1] >= 16 && ipParts[1] <= 31) return true;
    if (ipParts[0] === 192 && ipParts[1] === 168) return true;
    if (ipParts[0] >= 224) return true;
    return false;
  }

  const parts = hostname.split('.');
  if (parts.length >= 2) {
    const secondLast = parts[parts.length - 2];
    if (secondLast === 'local' || secondLast === 'internal' || secondLast === 'lan') return true;
  }

  return false;
}

function buildProxyUrls(url: string, userProxy?: string): string[] {
  const normalized = normalizeUrl(url);
  if (!normalized) return [];

  const proxies = userProxy?.trim() ? [userProxy.trim()] : [];
  for (const fallback of BUILTIN_PROXIES) {
    if (!proxies.includes(fallback)) {
      proxies.push(fallback);
    }
  }
  return proxies.map((proxy) => `${proxy}${encodeURIComponent(normalized)}`);
}

export async function fetchWithProxy(
  url: string,
  options?: RequestInit & CorsProxyOptions
): Promise<Response> {
  if (isUrlBlacklisted(url)) {
    throw new Error('目标地址在黑名单中，禁止通过代理访问');
  }

  const timeoutMs = options?.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  const fetchOptions: RequestInit = {
    ...options,
    signal: controller.signal,
  };
  delete (fetchOptions as Partial<CorsProxyOptions>).proxyUrl;
  delete (fetchOptions as Partial<CorsProxyOptions>).timeoutMs;
  delete (fetchOptions as Partial<CorsProxyOptions>).maxLength;

  const urls = buildProxyUrls(url, options?.proxyUrl);
  if (urls.length === 0) {
    window.clearTimeout(timeoutId);
    throw new Error('无法构造代理 URL');
  }

  let lastError: unknown;
  for (const proxyUrl of urls) {
    try {
      const response = await fetch(proxyUrl, fetchOptions);
      if (response.ok) {
        window.clearTimeout(timeoutId);
        return response;
      }
      lastError = new Error(`代理返回非成功状态：${response.status}`);
    } catch (err) {
      lastError = err;
    }
  }

  window.clearTimeout(timeoutId);
  throw lastError ?? new Error('通过代理获取失败');
}

export { DEFAULT_TIMEOUT_MS, DEFAULT_MAX_LENGTH };
