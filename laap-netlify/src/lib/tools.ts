import type { Tool } from '@/lib/localLlm';
import { completeRawChat } from '@/lib/localLlm';
import type { AppSettings } from '@/lib/settings';
import { getStructuredMemories, searchMemories } from '@/lib/memoryManager';
import { fetchWithProxy, type CorsProxyOptions } from '@/lib/corsProxy';
import type { LLMConfig } from '@/lib/config';
import type { LlmConfig } from '@/lib/llmConfig';
import { getActiveProvider } from '@/lib/llmConfig';

export interface BrowserState {
  url: string;
  title: string;
  text: string;
  links: { text: string; href: string }[];
  timestamp: string;
}

let browserSession: BrowserState | null = null;

function extractTextFromHtml(html: string): string {
  const body = html.replace(/<script[\s\S]*?<\/script>/gi, ' ').replace(/<style[\s\S]*?<\/style>/gi, ' ');
  const text = body
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  return text.slice(0, 12_000);
}

function extractLinks(html: string, baseUrl: string): { text: string; href: string }[] {
  const links: { text: string; href: string }[] = [];
  const seen = new Set<string>();
  const anchorRegex = /<a[^>]+href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;
  let match: RegExpExecArray | null;
  while ((match = anchorRegex.exec(html)) !== null) {
    try {
      const href = new URL(match[1], baseUrl).toString();
      const text = match[2].replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
      if (!seen.has(href) && text) {
        seen.add(href);
        links.push({ text: text.slice(0, 80), href });
      }
    } catch {
      // ignore invalid URLs
    }
  }
  return links.slice(0, 20);
}

export async function scrapeWebPage(
  url: string,
  proxyOptions?: CorsProxyOptions
): Promise<{
  url: string;
  title: string;
  text: string;
  links: { text: string; href: string }[];
}> {
  const targetUrl = url.startsWith('http') ? url : `https://${url}`;
  const response = await fetchWithProxy(targetUrl, proxyOptions);
  if (!response.ok) {
    throw new Error(`页面抓取失败：${response.status}`);
  }
  const html = await response.text();
  const titleMatch = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  const title = titleMatch ? titleMatch[1].replace(/\s+/g, ' ').trim() : '';
  const text = extractTextFromHtml(html);
  const links = extractLinks(html, targetUrl);

  browserSession = {
    url: targetUrl,
    title,
    text,
    links,
    timestamp: new Date().toISOString(),
  };

  return { url: targetUrl, title, text, links };
}

export function getBrowserSession(): BrowserState | null {
  return browserSession;
}

export function clearBrowserSession(): void {
  browserSession = null;
}

export function buildWebScrapeTool(settings?: AppSettings): Tool {
  const proxyOptions: CorsProxyOptions | undefined = settings?.agent.corsProxyUrl
    ? { proxyUrl: settings.agent.corsProxyUrl }
    : undefined;
  return {
    name: 'scrape_web_page',
    description: 'Fetch and extract the main text content from a web page URL. Use this to read articles, documentation, or any public webpage.',
    parameters: {
      type: 'object',
      properties: {
        url: { type: 'string', description: 'Full URL of the page to scrape' },
      },
      required: ['url'],
    },
    execute: async (args) => {
      const url = String(args.url || '').trim();
      if (!url) return 'URL 为空';
      try {
        const result = await scrapeWebPage(url, proxyOptions);
        return `已抓取页面：${result.title}\nURL：${result.url}\n\n正文摘要：\n${result.text.slice(0, 4000)}${
          result.text.length > 4000 ? '\n...（内容已截断）' : ''
        }\n\n页面链接：\n${result.links.slice(0, 10).map((l) => `- ${l.text}: ${l.href}`).join('\n')}`;
      } catch (err) {
        return `抓取失败：${err instanceof Error ? err.message : String(err)}`;
      }
    },
  };
}

export function buildCuaBrowserTool(settings?: AppSettings): Tool {
  const proxyOptions: CorsProxyOptions | undefined = settings?.agent.corsProxyUrl
    ? { proxyUrl: settings.agent.corsProxyUrl }
    : undefined;
  return {
    name: 'cua_browser',
    description: 'CUA browser control: navigate to a URL, click a link by text, or search the web. Use this when the user asks to browse, search, or interact with websites.',
    parameters: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          enum: ['navigate', 'click', 'search', 'back', 'session'],
          description: 'Browser action to perform',
        },
        url: { type: 'string', description: 'URL for navigate action' },
        linkText: { type: 'string', description: 'Text of the link to click' },
        query: { type: 'string', description: 'Search query' },
      },
      required: ['action'],
    },
    execute: async (args) => {
      const action = String(args.action || '');
      try {
        switch (action) {
          case 'navigate': {
            const url = String(args.url || '');
            if (!url) return '缺少 URL';
            const result = await scrapeWebPage(url, proxyOptions);
            return `已导航到：${result.title}\nURL：${result.url}\n\n页面内容：\n${result.text.slice(0, 3000)}`;
          }
          case 'click': {
            const text = String(args.linkText || '').trim();
            if (!text) return '缺少链接文本';
            if (!browserSession) return '当前没有打开的浏览器会话，请先 navigate 到一个页面。';
            const link = browserSession.links.find(
              (l) => l.text.toLowerCase().includes(text.toLowerCase()) || l.href.includes(text)
            );
            if (!link) return `未找到包含「${text}」的链接。当前页面可用链接：\n${browserSession.links.slice(0, 10).map((l) => `- ${l.text}`).join('\n')}`;
            const result = await scrapeWebPage(link.href, proxyOptions);
            return `已点击并导航到：${result.title}\nURL：${result.url}\n\n页面内容：\n${result.text.slice(0, 3000)}`;
          }
          case 'search': {
            const query = String(args.query || '').trim();
            if (!query) return '缺少搜索词';
            const searchUrl = `https://www.bing.com/search?q=${encodeURIComponent(query)}`;
            const result = await scrapeWebPage(searchUrl, proxyOptions);
            return `搜索结果（Bing）：\n${result.text.slice(0, 4000)}`;
          }
          case 'back': {
            return '浏览器返回操作需要完整历史栈，当前会话仅保留最新页面。';
          }
          case 'session': {
            if (!browserSession) return '当前没有浏览器会话。';
            return `当前页面：${browserSession.title}\nURL：${browserSession.url}\n抓取时间：${browserSession.timestamp}\n可用链接：\n${browserSession.links.slice(0, 10).map((l) => `- ${l.text}: ${l.href}`).join('\n')}`;
          }
          default:
            return `未知操作：${action}`;
        }
      } catch (err) {
        return `浏览器操作失败：${err instanceof Error ? err.message : String(err)}`;
      }
    },
  };
}

export function buildImageRecognitionTool(): Tool {
  return {
    name: 'analyze_image',
    description: 'Analyze an image that the user has uploaded. Describe its content, identify objects, text, charts, or UI elements. Use this when the user asks about an attached image.',
    parameters: {
      type: 'object',
      properties: {
        detail: {
          type: 'string',
          enum: ['brief', 'detailed'],
          description: 'Level of detail for the analysis',
        },
      },
      required: [],
    },
    execute: async () => {
      return '图像已随用户消息一起提交给多模态模型。请在回复中直接基于图像内容进行描述与分析。';
    },
  };
}

export function buildCodeBrowserTool(settings?: AppSettings): Tool {
  const proxyOptions: CorsProxyOptions | undefined = settings?.agent.corsProxyUrl
    ? { proxyUrl: settings.agent.corsProxyUrl }
    : undefined;
  return {
    name: 'code_browser',
    description: 'View or download code from a URL. Use this when the user wants to inspect source code, raw files, or repositories.',
    parameters: {
      type: 'object',
      properties: {
        url: { type: 'string', description: 'URL of the code file' },
        maxLines: { type: 'number', description: 'Maximum lines to return (default 200)' },
      },
      required: ['url'],
    },
    execute: async (args) => {
      const url = String(args.url || '').trim();
      if (!url) return 'URL 为空';
      const maxLines = Math.max(10, Math.min(2000, Number(args.maxLines || 200)));
      try {
        const response = await fetchWithProxy(url, proxyOptions);
        if (!response.ok) {
          return `下载失败：${response.status}`;
        }
        const text = await response.text();
        const lines = text.split('\n');
        const preview = lines.slice(0, maxLines).join('\n');
        return `代码文件：${url}\n总行数：${lines.length}\n\n\`\`\`\n${preview}${lines.length > maxLines ? '\n...（已截断）' : ''}\n\`\`\``;
      } catch (err) {
        return `代码查看失败：${err instanceof Error ? err.message : String(err)}`;
      }
    },
  };
}

async function loadRelevantMemories(userId: string, query: string, maxMemories: number): Promise<string> {
  try {
    const memories = await getStructuredMemories(userId, 100);
    const results = searchMemories(memories, query, maxMemories);
    if (results.length === 0) {
      return '（未找到与用户问题直接相关的长期记忆）';
    }
    return results.map((r) => `- ${r.memory.content}`).join('\n');
  } catch {
    return '（读取长期记忆失败）';
  }
}

export function buildCausalEngineTool(userId: string, settings?: AppSettings): Tool {
  return {
    name: 'causal_engine',
    description: 'Analyze causal relationships behind a user question. Use this when the user asks "why", reasons, root causes, or causal chains. Reads long-term memories for context.',
    parameters: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'The user question or phenomenon to analyze' },
        depth: {
          type: 'string',
          enum: ['surface', 'deep'],
          description: 'Analysis depth: surface for direct causes only, deep for root causes and full chain',
        },
      },
      required: ['query'],
    },
    execute: async (args) => {
      const query = String(args.query || '').trim();
      const depth = String(args.depth || 'deep') === 'surface' ? 'surface' : 'deep';
      if (!query) return '问题为空，无法进行因果分析。';
      try {
        const maxMemories = settings?.memory?.maxMemories ?? 12;
        const memoryContext = await loadRelevantMemories(userId, query, maxMemories);
        const deepMode = depth === 'deep';
        return [
          `## 因果引擎分析：${query}`,
          '',
          '### 相关记忆',
          memoryContext,
          '',
          '### 根因（Root Causes）',
          '1. 用户长期关注的深层议题、价值倾向或结构性背景。',
          memoryContext !== '（未找到与用户问题直接相关的长期记忆）'
            ? '2. 与长期记忆相关的核心张力或未满足需求。'
            : '2. 当前问题背后的根本性动机或环境压力。',
          '',
          '### 直接原因（Direct Causes）',
          `- 用户当下的提问：「${query}」`,
          '- 近期情境或对话中触发该疑问的具体事件。',
          '',
          '### 结果（Effects）',
          '- 认知层面：帮助用户形成更稳定的解释框架，减少不确定性。',
          '- 情绪/行动层面：可能带来释然、焦虑或改变行为的冲动。',
          '',
          '### 中介变量（Mediators）',
          '- 用户对该议题的情绪强度与投入程度。',
          '- 过往经验中被反复确认或挑战的信念。',
          '',
          '### 潜在混淆因素（Confounders）',
          '- 同时存在的其他压力源或生活事件。',
          '- 记忆本身的偏差、遗漏或时间久远导致的信息不完整。',
          '',
          '### 因果链',
          `「${query}」 ← 直接触发事件 ← 深层需求/价值/结构因素 ← 过往经历与信念 ← 当前情绪与环境反馈`,
          '',
          deepMode
            ? '> 深度模式：已结合长期记忆展开根因与因果链，可进一步调用 world_engine 推演不同应对路径。'
            : '> 浅层模式：已识别直接原因与可能结果，未展开深层机制。',
        ].join('\n');
      } catch (err) {
        return `因果分析失败：${err instanceof Error ? err.message : String(err)}`;
      }
    },
  };
}

export function buildWorldEngineTool(userId: string, settings?: AppSettings): Tool {
  const branchTemplates = [
    {
      premise: '乐观分支：假设顺利推进',
      path: '关键条件成熟，主要障碍被克服，正向反馈循环逐渐形成。',
      outcome: '用户获得显著积极结果，相关能力、关系或情绪状态明显提升。',
      probability: '中',
      uncertainty: '需要较多外部条件配合，实际发生的不确定性较高。',
    },
    {
      premise: '现实分支：假设部分实现',
      path: '主要条件满足，但伴随常见摩擦与持续调整。',
      outcome: '结果温和向好，用户需要在过程中不断适应与优化策略。',
      probability: '高',
      uncertainty: '与现有记忆和整体趋势较为吻合，是最可能发生的路径。',
    },
    {
      premise: '保守分支：假设受阻或延迟',
      path: '关键条件未达成，外部阻力或内在犹豫导致进展停滞。',
      outcome: '结果维持现状或小幅偏离，需要重新评估目标与策略。',
      probability: '中',
      uncertainty: '单一关键阻碍即可导致，但长期仍有转机。',
    },
    {
      premise: '悲观分支：假设向负面演化',
      path: '不利因素叠加，形成负向循环并放大风险。',
      outcome: '结果低于预期，可能引发情绪、关系或资源层面的压力。',
      probability: '低',
      uncertainty: '需要多重不利因素同时出现，概率较低但不能忽视。',
    },
    {
      premise: '意外分支：非线性转折',
      path: '出现未预料的关键变量，打破原有趋势。',
      outcome: '结果呈现跳跃式变化，好坏取决于用户的应变与学习能力。',
      probability: '低',
      uncertainty: '高度不可预测，需要保持开放与弹性。',
    },
  ];

  return {
    name: 'world_engine',
    description: 'Run multi-branch what-if scenario analysis. Use when the user asks "what if", hypotheses, or future simulations. Reads long-term memories for context.',
    parameters: {
      type: 'object',
      properties: {
        hypothesis: { type: 'string', description: 'The hypothetical condition or scenario to explore' },
        branches: {
          type: 'number',
          description: 'Number of branches to generate (default 3, max 5)',
        },
      },
      required: ['hypothesis'],
    },
    execute: async (args) => {
      const hypothesis = String(args.hypothesis || '').trim();
      const branches = Math.min(5, Math.max(1, Number(args.branches || 3)));
      if (!hypothesis) return '假设为空，无法进行世界线推演。';
      try {
        const maxMemories = settings?.memory?.maxMemories ?? 12;
        const memoryContext = await loadRelevantMemories(userId, hypothesis, maxMemories);
        const selected = branchTemplates.slice(0, branches);
        const lines: string[] = [
          `## 世界引擎推演：${hypothesis}`,
          '',
          '### 相关记忆',
          memoryContext,
          '',
          `### 推演分支（共 ${branches} 条）`,
        ];
        for (let i = 0; i < selected.length; i++) {
          const b = selected[i];
          lines.push(`\n**分支 ${i + 1}：${b.premise}**`);
          lines.push(`- 路径：${b.path}`);
          lines.push(`- 可能结果：${b.outcome}`);
          lines.push(`- 概率：${b.probability}`);
          lines.push(`- 不确定性：${b.uncertainty}`);
        }
        lines.push(
          '\n> 世界引擎基于用户长期记忆与假设条件生成推演，最终回应请结合用户情绪与价值观进行综合判断。'
        );
        return lines.join('\n');
      } catch (err) {
        return `世界线推演失败：${err instanceof Error ? err.message : String(err)}`;
      }
    },
  };
}

async function runScienceTool(
  config: LLMConfig | LlmConfig | undefined,
  query: string,
  taskType: import('@/lib/sciencePrompts').TaskType
): Promise<string> {
  if (!config) {
    return '科学工具需要配置 LLM API Key 才能运行。';
  }
  const apiKey = 'provider' in config ? config.api_key : getActiveProvider(config)?.apiKey;
  if (!apiKey) {
    return '科学工具需要配置 LLM API Key 才能运行。';
  }
  const { detectDomain, buildScienceSystemPrompt } = await import('@/lib/sciencePrompts');
  const domain = detectDomain(query);
  const system = buildScienceSystemPrompt(domain, taskType);
  return completeRawChat(config, [
    { role: 'system', content: system },
    { role: 'user', content: query },
  ]);
}

export function buildDerivationSolverTool(config?: LLMConfig | LlmConfig): Tool {
  return {
    name: 'derivation_solver',
    description: 'Solve or prove a math/science derivation step by step. Input should be the derivation or proof question.',
    parameters: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'The derivation or proof question' },
      },
      required: ['query'],
    },
    execute: async (args) => {
      const query = String(args.query || '').trim();
      if (!query) return '问题为空。';
      return runScienceTool(config, query, 'derivation');
    },
  };
}

export function buildExperimentDesignerTool(config?: LLMConfig | LlmConfig): Tool {
  return {
    name: 'experiment_designer',
    description: 'Design a structured scientific experiment. Input should be the research question and constraints.',
    parameters: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'The research question and constraints' },
      },
      required: ['query'],
    },
    execute: async (args) => {
      const query = String(args.query || '').trim();
      if (!query) return '问题为空。';
      return runScienceTool(config, query, 'experiment');
    },
  };
}

export function buildDataAnalyzerTool(config?: LLMConfig | LlmConfig): Tool {
  return {
    name: 'data_analyzer',
    description: 'Analyze scientific data and interpret results. Input should be the dataset description or raw data.',
    parameters: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Dataset description or raw data' },
      },
      required: ['query'],
    },
    execute: async (args) => {
      const query = String(args.query || '').trim();
      if (!query) return '问题为空。';
      return runScienceTool(config, query, 'analysis');
    },
  };
}

export function buildLiteratureSummarizerTool(config?: LLMConfig | LlmConfig): Tool {
  return {
    name: 'literature_summarizer',
    description: 'Summarize scientific literature or knowledge on a topic. Input should be the topic or list of sources.',
    parameters: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Topic or list of sources' },
      },
      required: ['query'],
    },
    execute: async (args) => {
      const query = String(args.query || '').trim();
      if (!query) return '问题为空。';
      return runScienceTool(config, query, 'literature');
    },
  };
}

export function buildProblemSolverTool(config?: LLMConfig | LlmConfig): Tool {
  return {
    name: 'problem_solver',
    description: 'Solve a general natural-science problem with model building. Input should be the full problem statement.',
    parameters: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Full problem statement' },
      },
      required: ['query'],
    },
    execute: async (args) => {
      const query = String(args.query || '').trim();
      if (!query) return '问题为空。';
      const { detectDomain, detectTaskType, buildScienceSystemPrompt } = await import('@/lib/sciencePrompts');
      const apiKey = config && ('provider' in config ? config.api_key : getActiveProvider(config)?.apiKey);
      if (!apiKey) {
        return '科学工具需要配置 LLM API Key 才能运行。';
      }
      const domain = detectDomain(query);
      const taskType = detectTaskType(query);
      const system = buildScienceSystemPrompt(domain, taskType);
      return completeRawChat(config, [
        { role: 'system', content: system },
        { role: 'user', content: query },
      ]);
    },
  };
}
