export interface ContextMessage {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  tool_call_id?: string;
  name?: string;
}

export interface ContextBudget {
  maxTotal: number;
  reserveSystem: number;
  reserveCompletion: number;
}

export interface ContextSnapshot {
  totalTokens: number;
  systemTokens: number;
  historyTokens: number;
  userTokens: number;
  includedMessages: number;
  summarizedMessages: number;
  recalledMessages: number;
  budget: ContextBudget;
}

export interface MemoryTier {
  type: 'short_term' | 'long_term_summary' | 'recalled';
  content: string;
  priority: number;
  tokens: number;
}

export const DEFAULT_CONTEXT_BUDGET: ContextBudget = {
  maxTotal: 1_000_000,
  reserveSystem: 4096,
  reserveCompletion: 8192,
};

export const COMPACT_CONTEXT_BUDGET: ContextBudget = {
  maxTotal: 128_000,
  reserveSystem: 2048,
  reserveCompletion: 4096,
};

export function estimateTokens(text: string): number {
  if (!text) return 0;
  const cjkMatches = text.match(/\p{Unified_Ideograph}/gu);
  const cjk = cjkMatches ? cjkMatches.length : 0;
  const nonCjk = text.replace(/\p{Unified_Ideograph}/gu, ' ');
  const words = nonCjk
    .trim()
    .split(/\s+/)
    .filter((w) => w.length > 0).length;
  return Math.ceil(cjk + words * 1.3);
}

export function estimateMessageTokens(message: ContextMessage): number {
  const base = 6;
  const content = typeof message.content === 'string' ? message.content : JSON.stringify(message.content);
  return base + estimateTokens(content);
}

function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .split(/[^\p{L}\p{N}]+/u)
    .filter((w) => w.length >= 2);
}

function extractKeywords(text: string): Map<string, number> {
  const tokens = tokenize(text);
  const counts = new Map<string, number>();
  for (const t of tokens) {
    const root = stem(t);
    counts.set(root, (counts.get(root) || 0) + 1);
  }
  return counts;
}

function stem(word: string): string {
  // Minimal stemming for CJK and Latin; sufficient for keyword overlap.
  if (/\p{Unified_Ideograph}/u.test(word)) return word;
  return word
    .replace(/(?:ing|ed|s|es|ly)$/, '')
    .replace(/([^aeiou])y$/, '$1i');
}

function expandSynonyms(word: string): string[] {
  const synonyms: Record<string, string[]> = {
    ai: ['人工智能', 'artificial intelligence', 'llm', '大模型'],
    llm: ['大模型', '大语言模型', '语言模型', 'ai'],
    模型: ['model', 'llm', '大模型'],
    记忆: ['memory', 'remember', '回忆', '记得'],
    任务: ['task', 'plan', 'todo', '工作'],
    代码: ['code', '编程', 'program', 'programming'],
    问题: ['question', 'issue', 'bug', '疑问'],
    项目: ['project', '应用', 'app', 'product'],
    用户: ['user', '你', '我'],
    设置: ['settings', '配置', 'config'],
  };
  return synonyms[word.toLowerCase()] || [];
}

function relevanceScore(message: ContextMessage, query: string): number {
  const queryKeywords = extractKeywords(query);
  const msgKeywords = extractKeywords(message.content);

  let score = 0;
  let matched = 0;

  for (const [word, weight] of queryKeywords.entries()) {
    const direct = msgKeywords.get(word) || 0;
    const synonyms = expandSynonyms(word);
    const synonym = synonyms.reduce((sum, syn) => sum + (msgKeywords.get(stem(syn)) || 0), 0);
    if (direct > 0 || synonym > 0) {
      matched++;
      score += (direct + synonym * 0.5) * weight;
    }
  }

  // Coverage bonus: messages that cover more query concepts rank higher.
  const coverage = matched / queryKeywords.size;
  score += coverage * 2;

  // Prefer concise, information-dense messages.
  const msgTokens = estimateMessageTokens(message);
  const density = msgTokens > 0 ? score / msgTokens : 0;

  return score * (1 + density) * (message.role === 'user' ? 1.15 : 1.0);
}

function priorityScore(message: ContextMessage, index: number, total: number, query: string): number {
  const recency = (index + 1) / total;
  const relevance = relevanceScore(message, query);
  const lengthPenalty = Math.min(1, 500 / Math.max(50, estimateTokens(message.content)));

  // User questions and factual statements get a small boost.
  let contentBoost = 1;
  const text = message.content;
  if (message.role === 'user' && /[？?]/.test(text)) contentBoost += 0.2;
  if (/\b(记住|记得|事实是|关键|重要)\b/.test(text)) contentBoost += 0.3;
  if (/\b(plan|spec|任务|拆解|步骤)\b/i.test(text)) contentBoost += 0.2;

  return recency * 3 + relevance * 4 + lengthPenalty * 0.5 + contentBoost;
}

export function rankMessagesByPriority(
  history: ContextMessage[],
  query: string
): Array<{ message: ContextMessage; index: number; score: number }> {
  const total = history.length;
  return history
    .map((message, index) => ({
      message,
      index,
      score: priorityScore(message, index, total, query),
    }))
    .sort((a, b) => b.score - a.score);
}

function summarizeSegment(messages: ContextMessage[]): string {
  const total = messages.length;
  const userCount = messages.filter((m) => m.role === 'user').length;
  const assistantCount = messages.filter((m) => m.role === 'assistant').length;
  const topics = extractTopics(messages);

  const keyFacts: string[] = [];
  for (const m of messages) {
    const facts = extractFacts(m.content);
    keyFacts.push(...facts);
  }

  const uniqueFacts = [...new Set(keyFacts)].slice(0, 6);

  return [
    '[早期会话摘要]',
    `本段包含 ${total} 条消息（用户 ${userCount} / 助手 ${assistantCount}）。`,
    topics ? `主题：${topics}。` : '',
    uniqueFacts.length ? `关键事实：${uniqueFacts.join('；')}。` : '',
    '详细内容已折叠，可追问具体细节。',
  ]
    .filter(Boolean)
    .join('\n');
}

function summarizeSegmentAggressively(messages: ContextMessage[], maxCharsPerPair = 50): string {
  const turns: ContextMessage[][] = [];
  let current: ContextMessage[] = [];
  for (const m of messages) {
    current.push(m);
    if (m.role === 'assistant') {
      turns.push(current);
      current = [];
    }
  }
  if (current.length > 0) turns.push(current);

  const parts: string[] = [];
  for (const turn of turns) {
    const userText = turn.find((m) => m.role === 'user')?.content ?? '';
    const assistantText = turn.find((m) => m.role === 'assistant')?.content ?? '';
    const facts = [...new Set(turn.flatMap((m) => extractFacts(m.content)))].slice(0, 2).join('；');
    let line = '';
    if (userText) line += `用户：${userText.slice(0, 15)}`;
    if (assistantText) line += `${line ? '；' : ''}助手：${assistantText.slice(0, 15)}`;
    if (facts) line += `${line ? '；' : ''}要点：${facts.slice(0, 15)}`;
    if (!line) line = '[空轮次]';
    parts.push(line.slice(0, maxCharsPerPair));
  }

  return ['[早期会话高度摘要]', ...parts].join('\n');
}

function extractTopics(messages: ContextMessage[]): string {
  const users = messages
    .filter((m) => m.role === 'user')
    .map((m) => m.content)
    .join(' ');
  const words = tokenize(users)
    .filter((w) => !isStopWord(w))
    .reduce((acc, w) => {
      acc.set(w, (acc.get(w) || 0) + 1);
      return acc;
    }, new Map<string, number>());

  return Array.from(words.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([w]) => w)
    .join('、');
}

function extractFacts(text: string): string[] {
  const facts: string[] = [];
  const sentences = text.split(/[。！？\n]/);
  for (const s of sentences) {
    const trimmed = s.trim();
    if (!trimmed) continue;
    if (/\b(是|为|等于|喜欢|需要|想要|目标|计划|使用|基于)\b/.test(trimmed)) {
      facts.push(trimmed.slice(0, 60));
    }
  }
  return facts.slice(0, 3);
}

function isStopWord(word: string): boolean {
  const stops = new Set([
    '的', '是', '在', '我', '你', '我们', '你们', '了', '和', '与', '有', '一个', '这个', '那个', '为', '要',
    '就', '都', '而', '及', '或', '但', '对', '能', '会', '可以', '没有', '不是', 'the', 'a', 'an', 'is', 'are',
    'was', 'were', 'i', 'you', 'we', 'he', 'she', 'it', 'this', 'that', 'to', 'of', 'in', 'for', 'on', 'with',
    'at', 'by', 'from', 'as', 'and', 'or', 'but', 'not', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
    'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used',
  ]);
  return stops.has(word.toLowerCase());
}

export function buildContextSnapshot(
  systemText: string,
  history: ContextMessage[],
  userMessage: string,
  budget: ContextBudget = DEFAULT_CONTEXT_BUDGET
): ContextSnapshot {
  const systemTokens = estimateTokens(systemText);
  const userTokens = estimateTokens(userMessage);
  const availableForHistory = Math.max(
    0,
    budget.maxTotal - systemTokens - userTokens - budget.reserveCompletion
  );

  let historyTokens = 0;
  let includedMessages = 0;
  const reversed = [...history].reverse();
  for (const msg of reversed) {
    const tokens = estimateMessageTokens(msg);
    if (historyTokens + tokens > availableForHistory) break;
    historyTokens += tokens;
    includedMessages++;
  }

  const summarizedMessages = Math.max(0, history.length - includedMessages);
  const totalTokens = systemTokens + historyTokens + userTokens;

  return {
    totalTokens,
    systemTokens,
    historyTokens,
    userTokens,
    includedMessages,
    summarizedMessages,
    recalledMessages: 0,
    budget,
  };
}

export interface AdvancedContextOptions {
  budget?: ContextBudget;
  recallTopK?: number;
  shortTermWindow?: number;
  enableSummarization?: boolean;
  userMessage: string;
}

export function buildAdvancedContextMessages(
  systemText: string,
  history: ContextMessage[],
  options: AdvancedContextOptions
): ContextMessage[] {
  const {
    budget = DEFAULT_CONTEXT_BUDGET,
    recallTopK = 8,
    shortTermWindow = 12,
    enableSummarization = true,
    userMessage,
  } = options;

  const systemTokens = estimateTokens(systemText);
  const userTokens = estimateTokens(userMessage);

  const result: ContextMessage[] = [{ role: 'system', content: systemText }];
  let usedTokens = systemTokens + userTokens;

  // Always preserve the most recent 4 messages for conversational coherence.
  const recent4 = history.slice(-4);
  const older = history.slice(0, Math.max(0, history.length - 4));

  // Project total tokens if the entire history were included.
  const allHistoryTokens = history.reduce((sum, m) => sum + estimateMessageTokens(m), 0);
  const projectedTotal = usedTokens + allHistoryTokens;
  const ratio = projectedTotal / budget.maxTotal;

  const recent4Tokens = recent4.reduce((sum, m) => sum + estimateMessageTokens(m), 0);

  if (ratio > 0.95) {
    // Critical budget pressure: keep only recent N rounds that fit + high-priority summary.
    const availableForExtra = budget.maxTotal * 0.95 - usedTokens - recent4Tokens;
    const reversedOlder = [...older].reverse();
    const extraRecent: ContextMessage[] = [];
    let extraTokens = 0;
    for (const msg of reversedOlder) {
      const t = estimateMessageTokens(msg);
      if (extraTokens + t > availableForExtra) break;
      extraTokens += t;
      extraRecent.unshift(msg);
    }

    const dropped = older.filter((m) => !extraRecent.includes(m));
    if (dropped.length > 0) {
      const summary = summarizeSegmentAggressively(dropped, 50);
      const summaryMsg: ContextMessage = {
        role: 'system',
        content: `[上下文高度压缩]\n${summary}`,
      };
      result.push(summaryMsg);
      usedTokens += estimateMessageTokens(summaryMsg);

      if (recallTopK > 0) {
        const ranked = rankMessagesByPriority(dropped, userMessage).slice(0, recallTopK);
        if (ranked.length > 0) {
          const recallHeader: ContextMessage = {
            role: 'system',
            content: `[相关记忆召回]\n以下是从早期对话中召回的 ${ranked.length} 条高度相关内容：`,
          };
          const recallTokens =
            estimateMessageTokens(recallHeader) +
            ranked.reduce((sum, r) => sum + estimateMessageTokens(r.message), 0);
          if (usedTokens + recallTokens <= budget.maxTotal - budget.reserveCompletion) {
            result.push(recallHeader);
            for (const r of ranked) result.push(r.message);
            usedTokens += recallTokens;
          }
        }
      }
    }

    result.push(...extraRecent, ...recent4);
    result.push({ role: 'user', content: userMessage });
    return result;
  }

  // Normal or moderately high pressure path.
  const aggressive = ratio > 0.8;

  const shortTerm = history.slice(-shortTermWindow);
  const olderForWindow = history.slice(0, Math.max(0, history.length - shortTermWindow));

  const ranked = rankMessagesByPriority(olderForWindow, userMessage).slice(0, recallTopK);
  const recalled = ranked.map((r) => r.message);
  const summarized = olderForWindow.filter((m) => !recalled.includes(m));

  const ordered: ContextMessage[] = [];

  if (summarized.length > 0 && enableSummarization) {
    const summary = aggressive
      ? summarizeSegmentAggressively(summarized, 50)
      : summarizeSegment(summarized);
    ordered.push({
      role: 'system',
      content: aggressive ? `[上下文高度压缩]\n${summary}` : summary,
    });
  }

  if (recalled.length > 0) {
    ordered.push({
      role: 'system',
      content: `[相关记忆召回]\n以下是从早期对话中召回的 ${recalled.length} 条高度相关内容：`,
    });
    ordered.push(...recalled);
  }

  ordered.push(...shortTerm);

  // Fit within budget, but never drop the most recent 4 messages.
  const mandatory = new Set(recent4);
  const included: ContextMessage[] = [];
  for (const msg of ordered) {
    const tokens = estimateMessageTokens(msg);
    if (mandatory.has(msg)) {
      included.push(msg);
      usedTokens += tokens;
    } else if (usedTokens + tokens <= budget.maxTotal - budget.reserveCompletion) {
      included.push(msg);
      usedTokens += tokens;
    }
  }

  result.push(...included);
  result.push({ role: 'user', content: userMessage });

  return result;
}

export function buildContextSnapshotAdvanced(
  systemText: string,
  history: ContextMessage[],
  options: AdvancedContextOptions
): ContextSnapshot {
  const messages = buildAdvancedContextMessages(systemText, history, options);
  const systemTokens = estimateTokens(systemText);
  const userTokens = estimateTokens(options.userMessage);
  const historyMessages = messages.filter((m) => m.role !== 'system');
  const historyTokens = historyMessages.reduce((sum, m) => sum + estimateMessageTokens(m), 0);
  const systemCount = messages.filter((m) => m.role === 'system').length - 1; // exclude main system prompt
  const totalTokens = messages.reduce((sum, m) => sum + estimateMessageTokens(m), 0);

  return {
    totalTokens,
    systemTokens,
    historyTokens,
    userTokens,
    includedMessages: historyMessages.length,
    summarizedMessages: Math.max(0, history.length - historyMessages.length),
    recalledMessages: systemCount,
    budget: options.budget || DEFAULT_CONTEXT_BUDGET,
  };
}

// Backward-compatible wrapper using the advanced algorithm.
export function buildContextMessages(
  systemText: string,
  history: ContextMessage[],
  userMessage: ContextMessage,
  budget: ContextBudget = DEFAULT_CONTEXT_BUDGET
): ContextMessage[] {
  return buildAdvancedContextMessages(systemText, history, {
    budget,
    userMessage: userMessage.content,
  });
}
