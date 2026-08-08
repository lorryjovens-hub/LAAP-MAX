import { apiFetch } from '@/lib/auth';
import type { LLMConfig } from '@/lib/config';
import { LOCAL_ONLY } from '@/lib/env';
import { getCurrentUser, isLoggedIn } from '@/lib/userMode';
import { LLM_CONFIG_KEY } from '@/lib/config';
import type { LlmConfig } from '@/lib/llmConfig';
import { getLlmConfig as getNewLlmConfig, toLegacyLlmConfig } from '@/lib/llmConfig';
import type { Tool } from '@/lib/localLlm';
import { ToolRegistry, type ToolDefinition } from '@/lib/toolRegistry';
import { sanitizeToolName } from '@/lib/toolRegistry';
import { listMcpServers, callMcpSseTool, type McpServer } from '@/lib/mcp';
import { broadcastSync } from '@/lib/syncManager';
import type { HallucinationReport } from '@/lib/hallucinationGuard';
import { listInstalledSkills, type SkillManifest } from '@/lib/skills';
import {
  generatePlanFromText,
  generatePlanOrSpec,
  generateSpecFromText,
  formatPlanAsMarkdown,
  formatSpecAsMarkdown,
  saveActivePlan,
} from '@/lib/taskPlanning';
import { generateCareMessage, recordInteraction } from '@/lib/userCare';
import {
  formatPaperAsMarkdown,
  getRecommendedPapers,
  searchPapers,
  setAcademicInterests,
} from '@/lib/academicUpdate';
import {
  addLocalMessage,
  addLocalMemory,
  createLocalSession,
  getLocalConfig,
  getLocalSession,
  listLocalMemories,
  listLocalMessages,
  listLocalSessions,
  updateLocalMessage,
  deleteLocalSession as localDeleteSession,
  type LocalAttachment,
} from '@/lib/db';
import { completeLocalChat, streamLocalChat } from '@/lib/localLlm';
import { cognitiveEngine } from '@/lib/cognitiveEngine';
import { evolutionEngine } from '@/lib/evolutionEngine';
import { DEFAULT_PERSONALITY, getPersonalityConfig } from '@/lib/personality';
import { extractUserProfileFacts } from '@/lib/memoryManager';
import {
  buildCausalEngineTool,
  buildCodeBrowserTool,
  buildCuaBrowserTool,
  buildDataAnalyzerTool,
  buildDerivationSolverTool,
  buildExperimentDesignerTool,
  buildImageRecognitionTool,
  buildLiteratureSummarizerTool,
  buildProblemSolverTool,
  buildWebScrapeTool,
  buildWorldEngineTool,
} from '@/lib/tools';
import {
  buildAetherTool,
  buildMetaCognitionTool,
  buildQpsiReasonTool,
  buildRsiReflectTool,
} from '@/lib/laapTools';
import { buildRenderTableTool } from '@/lib/tableTool';
import { buildGeneratePdfTool } from '@/lib/pdfTool';
import { buildCodeAgentTools } from '@/lib/codeAgentTools';
import type { BackgroundType } from '@/lib/settings';
import { DEFAULT_APP_SETTINGS, saveAppSettings, type AppSettings } from '@/lib/settings';

export interface ChatAttachment {
  id: string;
  type: 'image' | 'text' | 'file' | 'document';
  name: string;
  mimeType: string;
  content: string;
  pages?: number;
  wordCount?: number;
  size?: number;
}

export interface ChatSession {
  id: string;
  title: string;
  updated_at: string;
  created_at: string;
}

export interface ReasoningStep {
  step?: string;
  content?: string;
  [key: string]: unknown;
}

export interface ToolCall {
  name?: string;
  args?: Record<string, unknown>;
  result?: unknown;
  [key: string]: unknown;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  attachments?: ChatAttachment[];
  reasoning_steps?: ReasoningStep[];
  tool_calls?: ToolCall[];
  hallucination_report?: HallucinationReport;
  feedback?: 'positive' | 'negative' | null;
  created_at?: string;
}

export type StreamEventType = 'reasoning_step' | 'tool_result' | 'response' | 'done';

export interface StreamEvent {
  type: StreamEventType;
  data: Record<string, unknown>;
}

export interface SendChatOptions {
  llmConfig?: LLMConfig | LlmConfig;
  attachments?: ChatAttachment[];
  settings?: AppSettings;
  onSettingsChange?: (settings: AppSettings) => void;
}

// 本地优先模式（LOCAL_ONLY）下没有后端服务，所有会话/消息/聊天必须走本地
// IndexedDB + 本地 LLM 路径，即使已登录也是如此。
function shouldUseLocal(): boolean {
  return LOCAL_ONLY || !isLoggedIn();
}

async function resolveChatLlmConfig(
  explicit?: LLMConfig | LlmConfig | null,
  userId?: string
): Promise<(LLMConfig | LlmConfig) | undefined> {
  if (explicit) return explicit;

  const newConfig = await getNewLlmConfig(userId);
  if (newConfig.providers.length > 0) return newConfig;

  const legacy = await getLocalConfig<LLMConfig>(LLM_CONFIG_KEY, userId);
  if (legacy && (legacy.api_key || legacy.base_url || legacy.model)) return legacy;

  return undefined;
}

function localSessionToChatSession(s: { id: string; title: string; created_at: string; updated_at: string }): ChatSession {
  return {
    id: s.id,
    title: s.title,
    created_at: s.created_at,
    updated_at: s.updated_at,
  };
}

function localMessageToChatMessage(m: {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  attachments?: LocalAttachment[];
  reasoning_steps?: Record<string, unknown>[];
  tool_calls?: Record<string, unknown>[];
  hallucination_report?: Record<string, unknown>;
  feedback?: 'positive' | 'negative' | null;
  created_at: string;
}): ChatMessage {
  return {
    id: m.id,
    role: m.role,
    content: m.content,
    attachments: m.attachments,
    reasoning_steps: m.reasoning_steps,
    tool_calls: m.tool_calls,
    hallucination_report: m.hallucination_report as HallucinationReport | undefined,
    feedback: m.feedback,
    created_at: m.created_at,
  };
}

interface ApiSession {
  _id: string;
  title?: string;
  created_at: number;
  updated_at: number;
}

interface ApiMessage {
  _id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  attachments?: LocalAttachment[];
  reasoning_steps?: Record<string, unknown>[];
  tool_calls?: Record<string, unknown>[];
  validation_report?: Record<string, unknown>;
  feedback?: 'positive' | 'negative' | null;
  created_at: number;
}

function apiSessionToChatSession(s: ApiSession): ChatSession {
  return {
    id: s._id,
    title: s.title || '新对话',
    created_at: new Date(s.created_at).toISOString(),
    updated_at: new Date(s.updated_at).toISOString(),
  };
}

function apiMessageToChatMessage(m: ApiMessage): ChatMessage {
  return {
    id: m._id,
    role: m.role,
    content: m.content,
    attachments: m.attachments,
    reasoning_steps: m.reasoning_steps,
    tool_calls: m.tool_calls,
    hallucination_report: m.validation_report as HallucinationReport | undefined,
    feedback: m.feedback ?? null,
    created_at: new Date(m.created_at).toISOString(),
  };
}

export async function listSessions(): Promise<ChatSession[]> {
  if (shouldUseLocal()) {
    const user = await getCurrentUser();
    const sessions = await listLocalSessions(user.id);
    return sessions.map(localSessionToChatSession);
  }

  const response = await apiFetch('/api/v1/sessions');
  if (!response.ok) {
    throw new Error('Failed to load sessions');
  }
  const data = (await response.json()) as ApiSession[];
  return data.map(apiSessionToChatSession);
}

export async function createSession(title = '新对话'): Promise<ChatSession> {
  if (shouldUseLocal()) {
    const user = await getCurrentUser();
    const session = await createLocalSession(user.id, title);
    return localSessionToChatSession(session);
  }

  const response = await apiFetch('/api/v1/sessions', {
    method: 'POST',
    body: JSON.stringify({ title }),
  });
  if (!response.ok) {
    throw new Error('Failed to create session');
  }
  const { id } = (await response.json()) as { id: string };

  const sessionRes = await apiFetch(`/api/v1/sessions/${id}`);
  if (!sessionRes.ok) {
    throw new Error('Failed to load created session');
  }
  const session = (await sessionRes.json()) as ApiSession;
  return apiSessionToChatSession(session);
}

export async function getSessionMessages(sessionId: string): Promise<ChatMessage[]> {
  if (shouldUseLocal()) {
    const user = await getCurrentUser();
    const messages = await listLocalMessages(sessionId, user.id);
    return messages.map(localMessageToChatMessage);
  }

  const response = await apiFetch(`/api/v1/sessions/${sessionId}/messages`);
  if (!response.ok) {
    throw new Error('Failed to load messages');
  }
  const data = (await response.json()) as ApiMessage[];
  return data.map(apiMessageToChatMessage);
}

export async function deleteSession(sessionId: string): Promise<void> {
  if (shouldUseLocal()) {
    const user = await getCurrentUser();
    const session = await getLocalSession(sessionId);
    if (!session || session.user_id !== user.id) {
      throw new Error('Session not found');
    }
    await localDeleteSession(sessionId);
    return;
  }

  const response = await apiFetch(`/api/v1/sessions/${sessionId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete session');
  }
  broadcastSync('session-updated', { sessionId });
}

export async function updateMessageFeedback(
  messageId: string,
  feedback: 'positive' | 'negative'
): Promise<void> {
  if (shouldUseLocal()) {
    await updateLocalMessage(messageId, { feedback });

    // ── LAAP 递归自我进化：把用户反馈作为奖赏信号喂入认知引擎 ──
    // 正反馈 → 高奖励；负反馈 → 低奖励并触发 RSI 反思闭环。
    const reward = feedback === 'positive' ? 0.85 : 0.25;
    const user = await getCurrentUser();
    cognitiveEngine.start(user.id);
    cognitiveEngine.learn({ reward, completed: true, domain: 'feedback' });

    if (feedback === 'negative' && evolutionEngine.canReflect()) {
      evolutionEngine.markReflected();
      const msg = await updateLocalMessage(messageId, {});
      void evolutionEngine.reflect({
        observation:
          msg?.content?.slice(0, 300) ??
          '用户对一条助手回复给出了负面反馈，需要评估并改进。',
        targetModule: 'response_strategy',
        changeType: 'optimization',
        expectedImprovement: 0.15,
        risk: 0.3,
      });
    }
    return;
  }

  const response = await apiFetch(`/api/v1/messages/${messageId}/feedback`, {
    method: 'PUT',
    body: JSON.stringify({ feedback }),
  });
  if (!response.ok) {
    throw new Error('Failed to update feedback');
  }
}

async function loadLocalChatContext(userId: string, settings?: AppSettings, query = '') {
  const personality = (await getPersonalityConfig()) ?? DEFAULT_PERSONALITY;
  const memoryEnabled = settings?.memory.enabled ?? true;
  const memoryLimit = settings?.memory.maxMemories ?? 8;

  let memories: string[] = [];
  if (memoryEnabled) {
    if (query) {
      const { buildMemoryContext } = await import('@/lib/memoryManager');
      memories = await buildMemoryContext(userId, query, memoryLimit);
    } else {
      const memoryRecords = await listLocalMemories(userId, memoryLimit);
      memories = memoryRecords.map((m) => m.content);
    }
  }

  // ── LAAP 认知层：将数字生命体的实时认知状态注入系统上下文 ──
  // 记忆召回也会驱动认知引擎；注入实时 PSI 状态作为意识帧。
  cognitiveEngine.start(userId);
  evolutionEngine.start(userId);
  const cognitiveBlock = cognitiveEngine.toPromptBlock();
  memories = [...memories, `\n${cognitiveBlock}`];

  return { personality, memories };
}

async function recordLocalUserMessage(
  userId: string,
  sessionId: string,
  userText: string,
  attachments?: ChatAttachment[]
) {
  const memoryText = attachments
    ? `${userText} ${attachments.map((a) => `[附件:${a.name}]`).join(' ')}`
    : userText;
  await addLocalMemory(userId, memoryText, 'chat', sessionId);
  await addLocalMessage(sessionId, {
    role: 'user',
    content: userText,
    attachments,
  }, userId);

  try {
    const profileFacts = await extractUserProfileFacts(userId, userText);
    const highPriorityFacts = profileFacts.filter((f) => f.priority >= 6);
    await Promise.all(
      highPriorityFacts.map((f) =>
        addLocalMemory(userId, f.content, f.category, sessionId, f.priority)
      )
    );
  } catch {
    // 画像提取失败不应阻塞主对话流程
  }
}

async function recordLocalAssistantMessage(
  userId: string,
  sessionId: string,
  assistantResult: { content: string; reasoning_steps?: Record<string, unknown>[]; tool_calls?: Record<string, unknown>[] }
) {
  const { buildHallucinationReport, crossCheckWithMemories } = await import('@/lib/hallucinationGuard');
  const report = buildHallucinationReport(assistantResult.content);
  try {
    const check = await crossCheckWithMemories(userId, assistantResult.content);
    if (check.contradictions.length > 0) {
      report.recommendation = `检测到与记忆的可能冲突：${check.contradictions.join(' ')}`;
    }
  } catch {
    // ignore cross-check errors
  }
  await addLocalMessage(sessionId, {
    role: 'assistant',
    content: assistantResult.content,
    reasoning_steps: assistantResult.reasoning_steps,
    tool_calls: assistantResult.tool_calls,
    hallucination_report: report as unknown as Record<string, unknown>,
  }, userId);
}

interface WebSearchResult {
  title: string;
  link: string;
  snippet: string;
}

function extractTextFromHtmlBlock(html: string): string {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

async function searchWithSerper(apiKey: string, query: string): Promise<WebSearchResult[] | null> {
  try {
    const response = await fetch('https://google.serper.dev/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-KEY': apiKey,
      },
      body: JSON.stringify({ q: query }),
    });
    if (!response.ok) return null;
    const data = (await response.json()) as {
      organic?: { title?: string; link?: string; snippet?: string }[];
    };
    return (data.organic || [])
      .map((r) => ({
        title: r.title || '',
        link: r.link || '',
        snippet: r.snippet || '',
      }))
      .filter((r) => r.title && r.link);
  } catch {
    return null;
  }
}

async function searchWithDuckDuckGo(
  query: string,
  proxyOptions?: import('@/lib/corsProxy').CorsProxyOptions
): Promise<WebSearchResult[]> {
  const { fetchWithProxy } = await import('@/lib/corsProxy');
  const searchUrl = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}`;
  const response = await fetchWithProxy(searchUrl, {
    ...proxyOptions,
    timeoutMs: 20_000,
  });
  if (!response.ok) {
    throw new Error(`DuckDuckGo 返回 ${response.status}`);
  }
  const html = await response.text();
  const results: WebSearchResult[] = [];
  const seen = new Set<string>();

  // DuckDuckGo HTML results are in .result blocks
  const resultRegex = /<div class="result[^"]*"[^>]*>([\s\S]*?)<\/div>\s*<\/div>/gi;
  let match: RegExpExecArray | null;
  while ((match = resultRegex.exec(html)) !== null && results.length < 5) {
    const block = match[1];
    const titleMatch = block.match(/<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/i);
    const snippetMatch = block.match(/<a[^>]+class="result__snippet"[^>]*>([\s\S]*?)<\/a>/i);
    if (!titleMatch) continue;
    const link = titleMatch[1];
    const title = extractTextFromHtmlBlock(titleMatch[2]);
    const snippet = snippetMatch ? extractTextFromHtmlBlock(snippetMatch[1]) : '';
    if (title && link && !seen.has(link)) {
      seen.add(link);
      results.push({ title, link, snippet });
    }
  }

  // Fallback parsing for older/lite variants
  if (results.length === 0) {
    const linkRegex = /<a[^>]+href="(https?:\/\/[^"]+)"[^>]*>([\s\S]*?)<\/a>/gi;
    while ((match = linkRegex.exec(html)) !== null && results.length < 5) {
      const link = match[1];
      const title = extractTextFromHtmlBlock(match[2]);
      if (title && link && !link.includes('duckduckgo.com') && !seen.has(link)) {
        seen.add(link);
        results.push({ title, link, snippet: '' });
      }
    }
  }

  return results;
}

function formatWebSearchResults(results: WebSearchResult[]): string {
  if (results.length === 0) return '未找到搜索结果';
  return results.map((r) => `- ${r.title}: ${r.snippet || '(无摘要)'} (${r.link})`).join('\n');
}

function buildWebSearchTool(apiKey: string, settings?: AppSettings): Tool {
  const proxyOptions: import('@/lib/corsProxy').CorsProxyOptions | undefined = settings?.agent.corsProxyUrl
    ? { proxyUrl: settings.agent.corsProxyUrl }
    : undefined;

  return {
    name: 'web_search',
    description:
      'Search the public web for up-to-date information. Use this when the user asks about current events, facts you are unsure of, or anything that requires external verification. Returns top results with title, snippet, and link.',
    parameters: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'The search query' },
      },
      required: ['query'],
    },
    execute: async (args) => {
      const query = String(args.query || '').trim();
      if (!query) return '查询词为空';

      if (apiKey) {
        const results = await searchWithSerper(apiKey, query);
        if (results && results.length > 0) {
          return formatWebSearchResults(results);
        }
      }

      try {
        const results = await searchWithDuckDuckGo(query, proxyOptions);
        return formatWebSearchResults(results);
      } catch (err) {
        return `搜索失败：${err instanceof Error ? err.message : String(err)}`;
      }
    },
  };
}

async function buildLocalTools(
  userId: string,
  settings: AppSettings,
  mcpServers: McpServer[],
  skills: SkillManifest[],
  onSettingsChange?: (settings: AppSettings) => void,
  config?: LLMConfig
): Promise<Tool[]> {
  if (!settings.agent.toolCalling) return [];

  const registry = new ToolRegistry();

  const webTools = [
    buildWebScrapeTool(settings),
    buildCuaBrowserTool(settings),
    buildCodeBrowserTool(settings),
  ] as ToolDefinition[];
  webTools.push(buildWebSearchTool(settings.agent.webSearchApiKey, settings));
  registry.registerToolset({
    name: 'web',
    description: 'Web browsing, scraping, and search tools.',
    tools: webTools,
    enabled: true,
  });

  registry.register(buildImageRecognitionTool() as ToolDefinition);
  registry.register(buildCausalEngineTool(userId, settings) as ToolDefinition);
  registry.register(buildWorldEngineTool(userId, settings) as ToolDefinition);

  registry.registerToolset({
    name: 'laap',
    description: 'LAAP black-tech cognitive tools: meta-cognition, Aether orchestration, True RSI, and QPSI-N quantum reasoning.',
    tools: [
      buildMetaCognitionTool() as ToolDefinition,
      buildAetherTool() as ToolDefinition,
      buildRsiReflectTool() as ToolDefinition,
      buildQpsiReasonTool() as ToolDefinition,
    ],
    enabled: true,
  });

  registry.registerToolset({
    name: 'visual',
    description: 'Visual output tools: render structured data as images and generate PDF reports with charts.',
    tools: [buildRenderTableTool() as ToolDefinition, buildGeneratePdfTool() as ToolDefinition],
    enabled: true,
  });

  registry.registerToolset({
    name: 'science',
    description: 'Natural science research workflow tools for math, physics, chemistry, and biology.',
    tools: [
      buildDerivationSolverTool(config) as ToolDefinition,
      buildExperimentDesignerTool(config) as ToolDefinition,
      buildDataAnalyzerTool(config) as ToolDefinition,
      buildLiteratureSummarizerTool(config) as ToolDefinition,
      buildProblemSolverTool(config) as ToolDefinition,
    ],
    enabled: true,
  });

  registry.registerToolset({
    name: 'memory',
    description: 'Long-term memory search, save, and verify tools.',
    tools: [
      {
        name: 'search_memory',
        description: 'Search the user\'s long-term memories by keyword or topic.',
        parameters: {
          type: 'object',
          properties: {
            query: { type: 'string', description: 'Keyword to search in memories' },
          },
          required: ['query'],
        },
        execute: async (args) => {
          const query = String(args.query || '').toLowerCase();
          const memories = await listLocalMemories(userId, settings.memory.maxMemories);
          const matches = memories.filter((m) => m.content.toLowerCase().includes(query));
          if (matches.length === 0) return '没有找到相关记忆。';
          return matches.map((m) => `- ${m.content}`).join('\n');
        },
      },
      {
        name: 'save_memory',
        description: 'Save an important fact about the user to long-term memory.',
        agentLevel: true,
        readonly: false,
        parameters: {
          type: 'object',
          properties: {
            content: { type: 'string', description: 'The fact to remember' },
          },
          required: ['content'],
        },
        execute: async (args) => {
          const content = String(args.content || '').trim();
          if (!content) return '内容为空，未保存。';
          await addLocalMemory(userId, content, 'agent');
          return '已保存到长期记忆。';
        },
      },
      {
        name: 'verify_fact',
        description: 'Verify a factual claim against long-term memory and optionally web search. Use this before stating uncertain facts.',
        parameters: {
          type: 'object',
          properties: {
            claim: { type: 'string', description: 'The factual claim to verify' },
          },
          required: ['claim'],
        },
        execute: async (args) => {
          const claim = String(args.claim || '').trim();
          if (!claim) return '没有提供需要验证的陈述。';
          const { searchMemories, getStructuredMemories } = await import('@/lib/memoryManager');
          const memories = await getStructuredMemories(userId, 100);
          const results = searchMemories(memories, claim, 3);
          if (results.length === 0) {
            return `未在长期记忆中找到与「${claim}」直接相关的内容。请使用 web_search 进行外部验证，或明确标注这是推测。`;
          }
          const lines = results.map((r) => `- ${r.memory.content}（相关度 ${Math.round(r.score * 100)}%）`);
          return `关于「${claim}」的记忆验证结果：\n${lines.join('\n')}`;
        },
      },
    ] as ToolDefinition[],
    enabled: true,
  });

  registry.registerToolset({
    name: 'planning',
    description: 'Task planning and specification tools.',
    tools: [
      {
        name: 'create_task_plan',
        description: 'Create a detailed task execution plan for complex goals. Use when the user wants to break down a long task into actionable subtasks.',
        parameters: {
          type: 'object',
          properties: {
            goal: { type: 'string', description: 'The goal to plan for' },
          },
          required: ['goal'],
        },
        execute: async (args) => {
          const goal = String(args.goal || '');
          if (!goal) return '目标不能为空';
          const config = await resolveChatLlmConfig();
          if (!config) return '请先配置 LLM API Key';
          const result = await generatePlanOrSpec(goal, 'plan', config);
          if (result.plan) await saveActivePlan(result.plan);
          return formatPlanAsMarkdown(result.plan || generatePlanFromText(result.raw));
        },
      },
      {
        name: 'create_spec_definition',
        description: 'Create a detailed requirements specification document for a task or project.',
        parameters: {
          type: 'object',
          properties: {
            goal: { type: 'string', description: 'The project or task to specify' },
          },
          required: ['goal'],
        },
        execute: async (args) => {
          const goal = String(args.goal || '');
          if (!goal) return '目标不能为空';
          const config = await resolveChatLlmConfig();
          if (!config) return '请先配置 LLM API Key';
          const result = await generatePlanOrSpec(goal, 'spec', config);
          return formatSpecAsMarkdown(result.spec || generateSpecFromText(result.raw));
        },
      },
    ] as ToolDefinition[],
    enabled: true,
  });

  registry.registerToolset({
    name: 'academic',
    description: 'Academic paper search and recommendation tools.',
    tools: [
      {
        name: 'search_papers',
        description: 'Search academic papers on arXiv by keywords. Returns a list of recent papers with summaries.',
        parameters: {
          type: 'object',
          properties: {
            query: { type: 'string', description: 'Search query in English or Chinese' },
            maxResults: { type: 'number', description: 'Maximum number of results (default 5)' },
          },
          required: ['query'],
        },
        execute: async (args) => {
          const query = String(args.query || '');
          const maxResults = Math.min(10, Math.max(1, Number(args.maxResults || 5)));
          if (!query) return '查询词为空';
          try {
            const papers = await searchPapers(query, maxResults);
            if (papers.length === 0) return '未找到相关论文。';
            return papers
              .map((p, i) => `${i + 1}. **${p.title}**\n   ${p.abstract.slice(0, 200)}...\n   [链接](${p.url})`)
              .join('\n\n');
          } catch (err) {
            return `论文检索失败：${err instanceof Error ? err.message : String(err)}`;
          }
        },
      },
      {
        name: 'get_paper_recommendations',
        description: 'Recommend recent academic papers based on the user\'s inferred research interests and memories.',
        parameters: {
          type: 'object',
          properties: {
            maxResults: { type: 'number', description: 'Maximum number of recommendations (default 3)' },
          },
        },
        execute: async (args) => {
          const maxResults = Math.min(10, Math.max(1, Number(args.maxResults || 3)));
          try {
            const analyses = await getRecommendedPapers(settings, maxResults);
            if (analyses.length === 0) return '暂无推荐论文。';
            return analyses.map((a) => formatPaperAsMarkdown(a)).join('\n\n---\n\n');
          } catch (err) {
            return `推荐失败：${err instanceof Error ? err.message : String(err)}`;
          }
        },
      },
      {
        name: 'set_academic_interests',
        description: 'Set the user\'s research interests for academic paper recommendations.',
        readonly: false,
        parameters: {
          type: 'object',
          properties: {
            interests: {
              type: 'array',
              items: { type: 'string' },
              description: 'List of research interest keywords',
            },
          },
          required: ['interests'],
        },
        execute: async (args) => {
          const interests = Array.isArray(args.interests) ? args.interests.map(String) : [];
          if (interests.length === 0) return '兴趣关键词为空';
          await setAcademicInterests(interests);
          return `已设置学术兴趣：${interests.join('、')}。后续推荐将基于这些关键词。`;
        },
      },
    ] as ToolDefinition[],
    enabled: true,
  });

  registry.register({
    name: 'set_background',
    description: 'Change the Studio background appearance.',
    agentLevel: true,
    readonly: false,
    parameters: {
      type: 'object',
      properties: {
        type: { enum: ['solid', 'gradient', 'image'], description: 'Background type' },
        value: { type: 'string', description: 'Color, gradient CSS, or image URL/base64' },
      },
      required: ['type', 'value'],
    },
    execute: async (args) => {
      const next: AppSettings = {
        ...settings,
        ui: {
          ...settings.ui,
          backgroundType: String(args.type) as BackgroundType,
          backgroundValue: String(args.value),
        },
      };
      await saveAppSettings(next);
      onSettingsChange?.(next);
      return '背景已更新。';
    },
  });

  registry.register({
    name: 'check_user_care',
    description: 'Check whether the user should receive a proactive care message based on usage patterns. Returns the care message or a skip reason.',
    agentLevel: true,
    parameters: {
      type: 'object',
      properties: {},
    },
    execute: async () => {
      const message = await generateCareMessage(settings);
      return message ? `${message.text}\n（触发原因：${message.reason}）` : '当前不需要发送关怀消息。';
    },
  });

  // MCP servers (SSE/HTTP only in browser context)
  const mcpTools: ToolDefinition[] = mcpServers
    .filter((s) => s.enabled)
    .map((server) => ({
      name: `mcp_${sanitizeToolName(server.name)}`,
      description: `Call a tool on the MCP server "${server.name}". Provide the tool name and arguments.`,
      parameters: {
        type: 'object',
        properties: {
          toolName: { type: 'string', description: 'Name of the tool to call' },
          args: { type: 'object', description: 'Arguments for the tool' },
        },
        required: ['toolName', 'args'],
      },
      execute: async (args: Record<string, unknown>) => {
        const toolName = String(args.toolName || '');
        const toolArgs = (args.args as Record<string, unknown>) || {};
        if (!toolName) return '缺少 toolName';
        if (server.transport === 'stdio') {
          return 'stdio 类型的 MCP 服务器需要在服务端运行，当前环境不支持直接调用。';
        }
        try {
          return await callMcpSseTool(server, toolName, toolArgs);
        } catch (err) {
          return `MCP 调用失败：${err instanceof Error ? err.message : String(err)}`;
        }
      },
    }));
  if (mcpTools.length > 0) {
    registry.registerToolset({
      name: 'mcp',
      description: 'MCP server tools.',
      tools: mcpTools,
      enabled: true,
    });
  }

  // Installed skills with custom tools
  const skillTools: ToolDefinition[] = skills
    .filter((s) => s.enabled && s.tools && s.tools.length > 0)
    .flatMap((skill) =>
      skill.tools!.map((skillTool) => ({
        name: `skill_${sanitizeToolName(skill.id)}_${sanitizeToolName(skillTool.name)}`,
        description: `[${skill.name}] ${skillTool.description}`,
        parameters: skillTool.parameters || { type: 'object', properties: {} },
        execute: async (args: Record<string, unknown>) => {
          // Skill tools without a backend runner return a placeholder; real implementations
          // can be added by extending this execute function.
          return `技能工具 "${skillTool.name}" 已调用，参数：${JSON.stringify(args)}`;
        },
      }))
    );
  if (skillTools.length > 0) {
    registry.registerToolset({
      name: 'skills',
      description: 'Installed skill tools.',
      tools: skillTools,
      enabled: true,
    });
  }

  // Code agent tools backed by WebContainer
  registry.registerToolset({
    name: 'code_agent',
    description:
      'In-browser code agent tools. Create projects, read/write files, run shell commands, install dependencies, and start dev servers inside a WebContainer runtime.',
    tools: buildCodeAgentTools(userId) as ToolDefinition[],
    enabled: true,
  });

  return registry.list();
}

export async function sendChatMessage(
  sessionId: string,
  message: string,
  options: SendChatOptions = {}
): Promise<{ content: string; reasoning_steps: ReasoningStep[]; tool_calls: ToolCall[] }> {
  if (shouldUseLocal()) {
    const user = await getCurrentUser();
    const cfg = await resolveChatLlmConfig(options.llmConfig, user.id);
    if (!cfg) {
      throw new Error('请先配置 LLM API Key');
    }
    const settings = options.settings ?? DEFAULT_APP_SETTINGS;
    const { personality, memories } = await loadLocalChatContext(user.id, settings, message);
    const [mcpServers, skills] = await Promise.all([listMcpServers(), listInstalledSkills()]);
    await recordLocalUserMessage(user.id, sessionId, message, options.attachments);
    await recordInteraction();
    // ── LAAP PSI 大脑：感知用户消息进入意识 ──
    cognitiveEngine.perceive(message);
    const history = (await listLocalMessages(sessionId, user.id)).map((m) => ({ role: m.role, content: m.content }));
    const result = await completeLocalChat({
      config: cfg,
      history,
      userMessage: message,
      attachments: options.attachments,
      personality,
      memories,
      settings,
      tools: settings.agent.toolCalling
        ? await buildLocalTools(user.id, settings, mcpServers, skills, options.onSettingsChange, toLegacyLlmConfig(cfg) ?? undefined)
        : undefined,
    });
    await recordLocalAssistantMessage(user.id, sessionId, result);
    // ── LAAP PSI 大脑：行动并学习巩固 ──
    cognitiveEngine.act(result.content);
    cognitiveEngine.learn({ reward: 0.6, completed: true, domain: 'chat' });
    return {
      content: result.content,
      reasoning_steps: result.reasoning_steps as ReasoningStep[],
      tool_calls: result.tool_calls as ToolCall[],
    };
  }

  const response = await apiFetch('/api/v1/chat', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, message, llm_config: toLegacyLlmConfig(options.llmConfig) ?? options.llmConfig }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Chat request failed (${response.status})`);
  }

  broadcastSync('session-updated', { sessionId });
  return response.json();
}

export async function streamChatMessage(
  sessionId: string,
  message: string,
  onEvent: (event: StreamEvent) => void,
  options: SendChatOptions & { signal?: AbortSignal } = {}
): Promise<void> {
  const reasoningSteps: ReasoningStep[] = [];
  const toolCalls: ToolCall[] = [];

  const trackEvent = (event: StreamEvent) => {
    if (event.type === 'reasoning_step') {
      reasoningSteps.push(event.data as ReasoningStep);
    } else if (event.type === 'tool_result') {
      toolCalls.push(event.data as ToolCall);
    }
    onEvent(event);
  };

  if (shouldUseLocal()) {
    const user = await getCurrentUser();
    const cfg = await resolveChatLlmConfig(options.llmConfig, user.id);
    if (!cfg) {
      throw new Error('请先配置 LLM API Key');
    }
    const settings = options.settings ?? DEFAULT_APP_SETTINGS;
    const { personality, memories } = await loadLocalChatContext(user.id, settings, message);
    const [mcpServers, skills] = await Promise.all([listMcpServers(), listInstalledSkills()]);
    await recordLocalUserMessage(user.id, sessionId, message, options.attachments);
    await recordInteraction();
    // ── LAAP PSI 大脑：感知用户消息进入意识 ──
    cognitiveEngine.perceive(message);
    const history = (await listLocalMessages(sessionId, user.id)).map((m) => ({ role: m.role, content: m.content }));
    const result = await streamLocalChat({
      config: cfg,
      history,
      userMessage: message,
      attachments: options.attachments,
      personality,
      memories,
      settings,
      tools: settings.agent.toolCalling
        ? await buildLocalTools(user.id, settings, mcpServers, skills, options.onSettingsChange, toLegacyLlmConfig(cfg) ?? undefined)
        : undefined,
      onEvent: trackEvent,
      signal: options.signal,
    });
    await recordLocalAssistantMessage(
      user.id,
      sessionId,
      {
        content: result.content,
        reasoning_steps: reasoningSteps.length > 0 ? reasoningSteps : result.reasoning_steps,
        tool_calls: toolCalls.length > 0 ? toolCalls : result.tool_calls,
      }
    );
    // ── LAAP PSI 大脑：行动并学习巩固 ──
    cognitiveEngine.act(result.content);
    cognitiveEngine.learn({ reward: 0.6, completed: true, domain: 'chat' });
    return;
  }

  const response = await apiFetch('/api/v1/chat/stream', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
      message,
      llm_config: toLegacyLlmConfig(options.llmConfig) ?? options.llmConfig,
    }),
    signal: options.signal,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Streaming chat failed (${response.status})`);
  }

  if (!response.body) {
    throw new Error('No response body');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      if (options.signal?.aborted) {
        throw new Error('Aborted');
      }

      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const chunk of lines) {
        const event = parseSseChunk(chunk);
        if (event) {
          trackEvent(event);
          if (event.type === 'done') {
            return;
          }
        }
      }
    }

    if (buffer.trim()) {
      const event = parseSseChunk(buffer);
      if (event) {
        trackEvent(event);
      }
    }

    broadcastSync('session-updated', { sessionId });
  } finally {
    reader.releaseLock();
  }
}

function parseSseChunk(chunk: string): StreamEvent | null {
  let eventType: StreamEventType | null = null;
  let dataLine = '';

  for (const line of chunk.split('\n')) {
    const trimmed = line.trim();
    if (trimmed.startsWith('event:')) {
      const value = trimmed.slice(6).trim();
      if (
        value === 'reasoning_step' ||
        value === 'tool_result' ||
        value === 'response' ||
        value === 'done'
      ) {
        eventType = value;
      }
    } else if (trimmed.startsWith('data:')) {
      dataLine = trimmed.slice(5).trim();
    }
  }

  if (!eventType) return null;

  try {
    return { type: eventType, data: dataLine ? JSON.parse(dataLine) : {} };
  } catch {
    return { type: eventType, data: { raw: dataLine } };
  }
}
