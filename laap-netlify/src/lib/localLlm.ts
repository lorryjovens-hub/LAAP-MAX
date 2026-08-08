import type { LLMConfig } from '@/lib/config';
import type { LlmConfig } from '@/lib/llmConfig';
import { getActiveProvider, normalizeApiBase } from '@/lib/llmConfig';
import type { PersonalityConfig } from '@/lib/personality';
import { buildLaapSystemPrompt } from '@/lib/prompt';
import { detectDomain, detectTaskType, buildScienceSystemPrompt } from '@/lib/sciencePrompts';
import type { StreamEvent, ChatAttachment } from '@/lib/chat';
import type { AppSettings } from '@/lib/settings';
import { getCurrentUser } from '@/lib/userMode';
import { ToolExecutor, type ToolExecutionRecord } from '@/lib/toolExecutor';
import { ToolRegistry, type ToolDefinition } from '@/lib/toolRegistry';
import {
  buildAdvancedContextMessages,
  type ContextMessage,
  type ContextBudget,
  DEFAULT_CONTEXT_BUDGET,
} from '@/lib/contextMemory';

type ContentPart =
  | { type: 'text'; text: string }
  | { type: 'image_url'; image_url: { url: string } };

export interface HistoryMessage {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string | ContentPart[];
  tool_calls?: ToolCall[];
  tool_call_id?: string;
  name?: string;
}

export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

export interface Tool {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  execute: (args: Record<string, unknown>) => Promise<string>;
  readonly?: boolean;
  agentLevel?: boolean;
  toolset?: string;
}

interface ResolvedConfig {
  baseUrl: string;
  model: string;
  apiKey: string;
}

function isKeylessEndpoint(baseUrl: string, model: string): boolean {
  const lowerBase = baseUrl.toLowerCase();
  return (
    lowerBase.includes('localhost') ||
    lowerBase.includes('127.0.0.1') ||
    lowerBase.includes('omniroute') ||
    lowerBase.startsWith('/api/sensenova') ||
    model.toLowerCase().startsWith('omniroute/')
  );
}

// ---------------------------------------------------------------------------
// 免费额度限制：每位用户可免费调用 30 次，超出后提示配置自己的 API Key。
// ---------------------------------------------------------------------------
const FREE_CALL_LIMIT = 30;
const FREE_CALL_KEY_PREFIX = 'laap_free_call_count_';

/** 判定当前调用是否属于免费额度（未配置自有 API Key 的本地/免费端点）。 */
function isFreeTierCall(resolved: ResolvedConfig): boolean {
  return !resolved.apiKey && isKeylessEndpoint(resolved.baseUrl, resolved.model);
}

function readFreeCallCount(userId: string): number {
  try {
    if (typeof localStorage === 'undefined') return 0;
    return Number(localStorage.getItem(`${FREE_CALL_KEY_PREFIX}${userId}`) ?? 0);
  } catch {
    return 0;
  }
}

/**
 * 针对免费额度调用进行计数与拦截。每次用户对话（一次完整调用）记 1 次，
 * 超过 30 次后抛出错误，提示用户配置自己的 API Key。
 */
async function checkAndCountFreeCall(resolved: ResolvedConfig): Promise<void> {
  if (!isFreeTierCall(resolved)) return;

  const user = await getCurrentUser();
  const userId = user?.id ?? 'guest';
  const count = readFreeCallCount(userId) + 1;
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(`${FREE_CALL_KEY_PREFIX}${userId}`, String(count));
    }
  } catch {
    // ignore storage errors
  }

  if (count > FREE_CALL_LIMIT) {
    throw new Error(
      `免费调用次数已用完（每位用户 ${FREE_CALL_LIMIT} 次）。请在「设置 → LLM」中配置你自己的 API Key，或连接 OmniRoute 网关后继续使用。`
    );
  }
}

export interface LocalChatOptions {
  config: LLMConfig | LlmConfig;
  history: HistoryMessage[];
  userMessage: string;
  attachments?: ChatAttachment[];
  personality: PersonalityConfig;
  memories: string[];
  settings: AppSettings;
  tools?: Tool[];
}

interface LocalChatResult {
  content: string;
  reasoning_steps: Record<string, unknown>[];
  tool_calls: Record<string, unknown>[];
}

function isLegacyConfig(config: LLMConfig | LlmConfig): config is LLMConfig {
  return 'provider' in config;
}

function resolveLlmConfig(config: LLMConfig | LlmConfig): ResolvedConfig {
  if (isLegacyConfig(config)) {
    const defaults =
      config.provider === 'deepseek'
        ? { base_url: 'https://api.deepseek.com/v1', model: 'deepseek-chat' }
        : { base_url: 'https://api.openai.com/v1', model: 'gpt-4o-mini' };

    return {
      baseUrl: normalizeApiBase(config.base_url?.trim() || defaults.base_url),
      model: config.model?.trim() || defaults.model,
      apiKey: config.api_key,
    };
  }

  const active = getActiveProvider(config);
  if (!active) {
    return { baseUrl: '', model: '', apiKey: '' };
  }

  const defaultBase = active.baseURL?.toLowerCase().includes('deepseek')
    ? 'https://api.deepseek.com/v1'
    : 'https://api.openai.com/v1';

  return {
    baseUrl: normalizeApiBase(active.baseURL?.trim() || defaultBase),
    model: active.defaultModel?.trim() || active.models[0]?.trim() || '',
    apiKey: active.apiKey,
  };
}

function buildUserContent(userMessage: string, attachments?: ChatAttachment[]): string | ContentPart[] {
  if (!attachments || attachments.length === 0) return userMessage;

  const parts: ContentPart[] = [];
  parts.push({ type: 'text', text: userMessage });

  for (const att of attachments) {
    if (att.type === 'image') {
      parts.push({
        type: 'image_url',
        image_url: { url: `data:${att.mimeType};base64,${att.content}` },
      });
    } else if (att.type === 'document') {
      parts.push({
        type: 'text',
        text: `\n[文档 ${att.name}${att.pages !== undefined ? `，共 ${att.pages} 页` : ''}]\n${att.content}\n[文档结束]`,
      });
    } else if (att.type === 'text') {
      parts.push({
        type: 'text',
        text: `\n[文件 ${att.name}]\n${att.content.slice(0, 8000)}\n[文件结束]`,
      });
    } else {
      parts.push({
        type: 'text',
        text: `\n[附件 ${att.name}，类型 ${att.mimeType}，已上传但无法直接解析内容]`,
      });
    }
  }

  return parts;
}

function resolveContextBudget(model: string, userBudget?: number): ContextBudget {
  const lower = model.toLowerCase();
  let maxTotal = DEFAULT_CONTEXT_BUDGET.maxTotal;

  if (lower.includes('kimi') || lower.includes('moonshot')) {
    maxTotal = 2_000_000;
  } else if (lower.includes('claude')) {
    maxTotal = 200_000;
  } else if (lower.includes('gpt-4') && !lower.includes('mini')) {
    maxTotal = 128_000;
  } else if (lower.includes('deepseek')) {
    maxTotal = 64_000;
  }

  // 尊重用户在设置中指定的上下文窗口（最高支持百万+），
  // 允许用户通过配置把上下文扩展到超出模型默认上限。
  const MAX_USER_CONTEXT = 2_000_000;
  if (userBudget && userBudget > 0) {
    maxTotal = Math.min(Math.max(maxTotal, Math.min(userBudget, MAX_USER_CONTEXT)), MAX_USER_CONTEXT);
  }

  return {
    maxTotal,
    reserveSystem: 4096,
    reserveCompletion: 8192,
  };
}

function buildScienceEnhancedSystemPrompt(
  baseSystemText: string,
  userMessage: string
): string {
  const domain = detectDomain(userMessage);
  const taskType = detectTaskType(userMessage);
  const sciencePrompt = buildScienceSystemPrompt(domain, taskType);
  return `${baseSystemText}\n\n当前问题涉及自然科学研究领域，请在回答中遵循以下学科规范：\n${sciencePrompt}`;
}

function buildInitialMessages(
  systemText: string,
  history: HistoryMessage[],
  userMessage: string,
  settings: AppSettings,
  attachments?: ChatAttachment[],
  model?: string
): HistoryMessage[] {
  const userContent = buildUserContent(userMessage, attachments);
  const userTextForBudget =
    typeof userContent === 'string'
      ? userContent
      : userContent.map((p) => (p.type === 'text' ? p.text : '[image]')).join(' ');

  const contextHistory: ContextMessage[] = history
    .filter((h) => h.role === 'user' || h.role === 'assistant' || h.role === 'tool')
    .map((h) => ({
      role: h.role,
      content: typeof h.content === 'string' ? h.content : '[image/attachment]',
      tool_call_id: h.tool_call_id,
      name: h.name,
    }));

  const budget = resolveContextBudget(model || 'default', settings.llm.contextWindow);
  const messages = buildAdvancedContextMessages(systemText, contextHistory, {
    budget,
    userMessage: userTextForBudget,
    recallTopK: settings.memory.enabled ? 8 : 0,
    shortTermWindow: 12,
    enableSummarization: true,
  }) as HistoryMessage[];

  // Replace the final user message with the real content that may include attachments.
  messages[messages.length - 1] = {
    role: 'user',
    content: userContent,
  };
  return messages;
}

async function parseErrorMessage(response: Response): Promise<string> {
  const text = await response.text();
  try {
    const data = JSON.parse(text) as { error?: { message?: string }; message?: string; detail?: unknown };
    if (data.error && typeof data.error.message === 'string') return data.error.message;
    if (typeof data.message === 'string') return data.message;
    if (data.detail) return JSON.stringify(data.detail);
  } catch {
    // ignore
  }
  return text || `请求失败 (${response.status})`;
}

function buildRequestBody(
  resolved: ResolvedConfig,
  messages: HistoryMessage[],
  settings: AppSettings,
  tools?: Tool[],
  stream = false
) {
  const llm = settings.llm;
  const body: Record<string, unknown> = {
    model: resolved.model,
    messages,
    temperature: llm.temperature,
    max_tokens: llm.maxTokens,
    top_p: llm.topP,
    presence_penalty: llm.presencePenalty,
    frequency_penalty: llm.frequencyPenalty,
    stream,
  };

  if (tools && tools.length > 0) {
    body.tools = tools.map((t) => ({
      type: 'function',
      function: {
        name: t.name,
        description: t.description,
        parameters: t.parameters,
      },
    }));
  }

  return body;
}

async function postChat(
  resolved: ResolvedConfig,
  body: Record<string, unknown>
): Promise<{
  choices?: {
    message?: {
      content?: string | null;
      tool_calls?: ToolCall[];
    };
  }[];
}> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (resolved.apiKey) {
    headers.Authorization = `Bearer ${resolved.apiKey}`;
  }
  const response = await fetch(`${resolved.baseUrl}/chat/completions`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json();
}

async function executeToolLoop(
  resolved: ResolvedConfig,
  messages: HistoryMessage[],
  tools: Tool[],
  settings: AppSettings,
  onEvent?: (event: StreamEvent) => void
): Promise<{ messages: HistoryMessage[]; toolCalls: ToolExecutionRecord[] }> {
  const maxRounds = Math.max(1, Math.min(settings.agent.maxToolRounds, 5));
  let currentMessages = [...messages];
  const allToolCalls: ToolExecutionRecord[] = [];

  const registry = new ToolRegistry();
  for (const tool of tools) {
    registry.register(tool as ToolDefinition);
  }

  const executor = new ToolExecutor(registry, {
    maxRounds,
    onEvent,
  });

  for (let round = 0; round < maxRounds; round++) {
    const data = await postChat(resolved, buildRequestBody(resolved, currentMessages, settings, tools, false));
    const message = data.choices?.[0]?.message;
    const rawToolCalls = message?.tool_calls;
    const assistantContent = message?.content ?? '';

    const result = await executor.execute(currentMessages, rawToolCalls, assistantContent);
    currentMessages = result.messages;
    allToolCalls.push(...result.toolCalls);

    if (result.toolCalls.length === 0) {
      break;
    }
  }

  return { messages: currentMessages, toolCalls: allToolCalls };
}

export async function completeLocalChat(options: LocalChatOptions): Promise<LocalChatResult> {
  const { config, history, userMessage, attachments, personality, memories, settings, tools } = options;
  const resolved = resolveLlmConfig(config);
  if (!resolved.apiKey && !isKeylessEndpoint(resolved.baseUrl, resolved.model)) {
    throw new Error('请先配置 LLM API Key');
  }
  await checkAndCountFreeCall(resolved);

  const baseSystemText = buildLaapSystemPrompt({ personality, memories, influence: settings.influence, agent: settings.agent });
  const systemText = buildScienceEnhancedSystemPrompt(baseSystemText, userMessage);
  let messages = buildInitialMessages(systemText, history, userMessage, settings, attachments, resolved.model);
  let toolCalls: ToolExecutionRecord[] = [];

  if (tools && tools.length > 0 && settings.agent.toolCalling) {
    const loop = await executeToolLoop(resolved, messages, tools, settings);
    messages = loop.messages;
    toolCalls = loop.toolCalls;
  }

  const data = await postChat(resolved, buildRequestBody(resolved, messages, settings, undefined, false));
  const content = data.choices?.[0]?.message?.content ?? '';
  return {
    content,
    reasoning_steps: [],
    tool_calls: toolCalls.map((t) => ({ name: t.name, args: t.args, result: t.result, id: t.id })),
  };
}

export async function streamLocalChat(
  options: LocalChatOptions & { onEvent: (event: StreamEvent) => void; signal?: AbortSignal }
): Promise<LocalChatResult> {
  const { config, history, userMessage, attachments, personality, memories, settings, tools, onEvent, signal } = options;
  const resolved = resolveLlmConfig(config);
  if (!resolved.apiKey && !isKeylessEndpoint(resolved.baseUrl, resolved.model)) {
    throw new Error('请先配置 LLM API Key');
  }
  await checkAndCountFreeCall(resolved);

  const baseSystemText = buildLaapSystemPrompt({ personality, memories, influence: settings.influence, agent: settings.agent });
  const systemText = buildScienceEnhancedSystemPrompt(baseSystemText, userMessage);
  let messages = buildInitialMessages(systemText, history, userMessage, settings, attachments, resolved.model);
  let toolCalls: ToolExecutionRecord[] = [];

  // If tools are enabled, run the agent loop first (non-streaming) to resolve tool calls,
  // then stream the final response so the user still sees a typing effect.
  if (tools && tools.length > 0 && settings.agent.toolCalling) {
    const loop = await executeToolLoop(resolved, messages, tools, settings, onEvent);
    messages = loop.messages;
    toolCalls = loop.toolCalls;
  }

  const streamHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (resolved.apiKey) {
    streamHeaders.Authorization = `Bearer ${resolved.apiKey}`;
  }
  const response = await fetch(`${resolved.baseUrl}/chat/completions`, {
    method: 'POST',
    headers: streamHeaders,
    body: JSON.stringify(buildRequestBody(resolved, messages, settings, undefined, true)),
    signal,
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  if (!response.body) {
    throw new Error('LLM 未返回流式响应');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let content = '';

  try {
    while (true) {
      if (signal?.aborted) {
        throw new Error('Aborted');
      }
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith('data:')) continue;
        const payload = trimmed.slice(5).trim();
        if (payload === '[DONE]') {
          onEvent({ type: 'done', data: {} });
          return {
            content,
            reasoning_steps: [],
            tool_calls: toolCalls.map((t) => ({ name: t.name, args: t.args, result: t.result, id: t.id })),
          };
        }
        try {
          const chunk = JSON.parse(payload) as {
            choices?: { delta?: { content?: string } }[];
          };
          const delta = chunk.choices?.[0]?.delta?.content;
          if (typeof delta === 'string') {
            content += delta;
            onEvent({ type: 'response', data: { content } });
          }
        } catch {
          // ignore malformed chunks
        }
      }
    }

    if (buffer.trim()) {
      const trimmed = buffer.trim();
      if (trimmed.startsWith('data:')) {
        const payload = trimmed.slice(5).trim();
        if (payload !== '[DONE]') {
          try {
            const chunk = JSON.parse(payload) as {
              choices?: { delta?: { content?: string } }[];
            };
            const delta = chunk.choices?.[0]?.delta?.content;
            if (typeof delta === 'string') {
              content += delta;
              onEvent({ type: 'response', data: { content } });
            }
          } catch {
            // ignore
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }

  onEvent({ type: 'done', data: {} });
  return {
    content,
    reasoning_steps: [],
    tool_calls: toolCalls.map((t) => ({ name: t.name, args: t.args, result: t.result, id: t.id })),
  };
}

export async function completeRawChat(
  config: LLMConfig | LlmConfig,
  messages: { role: 'system' | 'user' | 'assistant'; content: string }[]
): Promise<string> {
  const resolved = resolveLlmConfig(config);
  if (!resolved.apiKey) {
    throw new Error('请先配置 LLM API Key');
  }

  const response = await fetch(`${resolved.baseUrl}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${resolved.apiKey}`,
    },
    body: JSON.stringify({
      model: resolved.model,
      messages,
      temperature: 0.5,
      max_tokens: 4096,
    }),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  const data = (await response.json()) as {
    choices?: { message?: { content?: string | null } }[];
  };
  return data.choices?.[0]?.message?.content ?? '';
}
