import type { ChatMessage } from '@/lib/chat';
import type { CodeProject } from '@/lib/codeProjectDb';

export interface SharedChat {
  title: string;
  messages: ChatMessage[];
  exportedAt: string;
  version: number;
}

export interface SharedProject {
  name: string;
  template: string;
  files: { path: string; content: string }[];
  exportedAt: string;
  version: number;
}

const SHARE_VERSION = 1;
const MAX_SHARE_BYTES = 64_000; // URL length safety margin (~64KB)
const MAX_PROJECT_SHARE_BYTES = 256_000; // projects can be larger (~256KB)

function stringToBase64(str: string): string {
  try {
    return btoa(encodeURIComponent(str));
  } catch {
    return '';
  }
}

function base64ToString(base64: string): string {
  try {
    return decodeURIComponent(atob(base64));
  } catch {
    return '';
  }
}

export function encodeSharedChat(title: string, messages: ChatMessage[]): string | null {
  const payload: SharedChat = {
    title: title || 'LAAP 对话分享',
    messages: messages.map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      attachments: m.attachments,
      reasoning_steps: m.reasoning_steps,
      tool_calls: m.tool_calls,
      created_at: m.created_at,
    })),
    exportedAt: new Date().toISOString(),
    version: SHARE_VERSION,
  };

  const json = JSON.stringify(payload);
  const base64 = stringToBase64(json);
  if (!base64 || base64.length > MAX_SHARE_BYTES) {
    return null;
  }
  return base64;
}

export function decodeSharedChat(token: string): SharedChat | null {
  const json = base64ToString(token);
  if (!json) return null;
  try {
    const parsed = JSON.parse(json) as SharedChat;
    if (!parsed || parsed.version !== SHARE_VERSION || !Array.isArray(parsed.messages)) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function buildShareUrl(token: string): string {
  return `${window.location.origin}/share/${token}`;
}

export function encodeSharedProject(project: CodeProject): string | null {
  const payload: SharedProject = {
    name: project.name || 'LAAP 项目分享',
    template: project.template,
    files: project.files.map((f) => ({ path: f.path, content: f.content })),
    exportedAt: new Date().toISOString(),
    version: SHARE_VERSION,
  };

  const json = JSON.stringify(payload);
  const base64 = stringToBase64(json);
  if (!base64 || base64.length > MAX_PROJECT_SHARE_BYTES) {
    return null;
  }
  return base64;
}

export function decodeSharedProject(token: string): SharedProject | null {
  const json = base64ToString(token);
  if (!json) return null;
  try {
    const parsed = JSON.parse(json) as SharedProject;
    if (
      !parsed ||
      parsed.version !== SHARE_VERSION ||
      !Array.isArray(parsed.files) ||
      typeof parsed.name !== 'string'
    ) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function buildProjectShareUrl(token: string): string {
  return `${window.location.origin}/share/project/${token}`;
}
