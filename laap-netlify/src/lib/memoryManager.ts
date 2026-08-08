import {
  addLocalMemory,
  listLocalMemories,
  type LocalMemory,
  getLocalConfig,
  setLocalConfig,
} from '@/lib/db';
import { broadcastSync } from '@/lib/syncManager';

export type MemoryType = 'fact' | 'preference' | 'episodic' | 'task' | 'relationship' | 'concept';

export interface StructuredMemory {
  id: string;
  content: string;
  type: MemoryType;
  source?: string;
  importance: number; // 0-100
  priority: number; // 0-10
  lastAccessed: string;
  createdAt: string;
  embeddings?: number[];
  keywords: string[];
}

export interface MemorySearchResult {
  memory: StructuredMemory;
  score: number;
}

const MEMORY_INDEX_KEY = 'laap_memory_index';

const MEMORY_TYPE_DESCRIPTIONS: Record<MemoryType, string> = {
  fact: '用户陈述的客观事实',
  preference: '用户的偏好、习惯或口味',
  episodic: '具体发生的事件或对话片段',
  task: '用户需要完成的目标或任务',
  relationship: '用户的人际关系或社交背景',
  concept: '用户正在学习或讨论的概念',
};

function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .split(/[^\p{L}\p{N}]+/u)
    .filter((w) => w.length >= 2);
}

function extractKeywords(text: string): string[] {
  const stops = new Set([
    '的', '是', '在', '我', '你', '我们', '了', '和', '与', '有', '一个', '这个', 'the', 'is', 'a', 'and', 'to',
    'of', 'in', 'that', 'it', 'for', 'on', 'with', 'as', 'this', 'but', 'be', 'are', 'was', 'were', 'have', 'has',
  ]);
  const tokens = tokenize(text).filter((w) => !stops.has(w));
  return [...new Set(tokens)];
}

function classifyContent(content: string): MemoryType {
  const text = content.toLowerCase();
  if (/\b(喜欢|讨厌|偏好|习惯|想|要|觉得|认为)\b/.test(text)) return 'preference';
  if (/\b(任务|计划|目标|完成|todo|deadline|截止)\b/.test(text)) return 'task';
  if (/\b(朋友|家人|同事|老板|女友|男友|妈妈|爸爸)\b/.test(text)) return 'relationship';
  if (/\b(概念|定义|原理|理论|框架|模型|算法)\b/.test(text)) return 'concept';
  if (/\b(发生|当时|那天|后来|记得|经历)\b/.test(text)) return 'episodic';
  return 'fact';
}

function estimateImportance(content: string): number {
  let score = 50;
  if (/\b(重要|关键|记住|永远|总是|从不|必须|一定)\b/.test(content)) score += 20;
  if (/\b(喜欢|讨厌|梦想|目标|计划|身份|职业)\b/.test(content)) score += 15;
  if (content.length > 20 && content.length < 300) score += 10;
  if (/\?|？/.test(content)) score -= 10;
  return Math.min(100, Math.max(10, score));
}

export interface ProfileFact {
  content: string;
  priority: number;
  category: 'preference' | 'interest' | 'goal' | 'fact';
}

const PROFILE_PATTERNS: {
  category: ProfileFact['category'];
  priority: number;
  regex: RegExp;
  extract: (match: RegExpMatchArray, text: string) => string | undefined;
}[] = [
  {
    category: 'preference',
    priority: 9,
    regex: /(?:我|本人)\s*(?:非常|特别|很|十分)?\s*(喜欢|讨厌|厌恶|反感|偏爱|钟爱)\s*(.*?)(?:[。，；;]|$)/,
    extract: (m) => (m[1] && m[2] ? `${m[1]}${m[2].trim()}` : undefined),
  },
  {
    category: 'preference',
    priority: 8,
    regex: /(?:我|本人)\s*(?:习惯|通常|总是|经常)\s*(.*?)(?:[。，；;]|$)/,
    extract: (m) => (m[1] ? `习惯：${m[1].trim()}` : undefined),
  },
  {
    category: 'goal',
    priority: 9,
    regex: /(?:我|本人)\s*(?:想|希望|打算|计划|立志|目标是?)\s*(?:要|成为|做到|实现|完成)?\s*(.*?)(?:[。，；;]|$)/,
    extract: (m) => (m[1] ? `目标：${m[1].trim()}` : undefined),
  },
  {
    category: 'fact',
    priority: 10,
    regex: /(?:我|本人)\s*(?:是|从事|担任|做)\s*(一名|个)?\s*(.*?)(?:[。，；;]|$)/,
    extract: (m) => (m[2] ? `身份/职业：${m[2].trim()}` : undefined),
  },
  {
    category: 'fact',
    priority: 9,
    regex: /(?:我|本人)\s*(?:已经|曾经|刚刚)?\s*(结婚|离婚|毕业|入职|离职|退休|生病|康复|搬家|出国|回国)(?:了)?/,
    extract: (m) => (m[1] ? `重要经历：${m[1]}` : undefined),
  },
  {
    category: 'interest',
    priority: 6,
    regex: /(?:我|本人)\s*(?:对|对于)\s*(.*?)\s*(?:很|非常|特别|比较)?\s*(感兴趣|有兴趣|热衷|着迷|关注)/,
    extract: (m) => (m[1] && m[2] ? `兴趣：${m[1].trim()}` : undefined),
  },
  {
    category: 'interest',
    priority: 5,
    regex: /(?:我|本人)\s*(?:正在|近期)?\s*(学习|研究|阅读|关注|尝试|探索)\s*(.*?)(?:[。，；;]|$)/,
    extract: (m) => (m[1] && m[2] ? `${m[1]}：${m[2].trim()}` : undefined),
  },
  {
    category: 'preference',
    priority: 7,
    regex: /(?:我|本人)\s*(?:认为|觉得|相信)\s*(.*?)(?:[。，；;]|$)/,
    extract: (m) => (m[1] ? `观点：${m[1].trim()}` : undefined),
  },
];

export async function extractUserProfileFacts(
  _userId: string,
  userMessage: string
): Promise<ProfileFact[]> {
  const text = userMessage.trim();
  if (text.length < 5) return [];

  const facts: ProfileFact[] = [];
  const seen = new Set<string>();

  for (const pattern of PROFILE_PATTERNS) {
    const regex = new RegExp(pattern.regex.source, 'g');
    let match: RegExpExecArray | null;
    while ((match = regex.exec(text)) !== null) {
      const content = pattern.extract(match, text);
      if (!content) continue;
      const normalized = content.replace(/\s+/g, ' ').trim();
      if (normalized.length < 3 || normalized.length > 200) continue;
      if (seen.has(normalized)) continue;
      seen.add(normalized);
      facts.push({ content: normalized, priority: pattern.priority, category: pattern.category });
    }
  }

  // Deduplicate overlapping facts by keeping the higher priority one.
  const unique: ProfileFact[] = [];
  for (const fact of facts) {
    const existing = unique.find((u) => u.content.includes(fact.content) || fact.content.includes(u.content));
    if (existing) {
      if (fact.priority > existing.priority) {
        existing.content = fact.content;
        existing.priority = fact.priority;
        existing.category = fact.category;
      }
    } else {
      unique.push(fact);
    }
  }

  return unique.sort((a, b) => b.priority - a.priority);
}

function buildStructuredMemory(
  local: LocalMemory,
  overrides?: Partial<StructuredMemory>
): StructuredMemory {
  const basePriority = typeof local.priority === 'number' ? local.priority : 5;
  const base: StructuredMemory = {
    id: local.id,
    content: local.content,
    type: classifyContent(local.content),
    source: local.source,
    importance: estimateImportance(local.content),
    priority: basePriority,
    lastAccessed: local.created_at,
    createdAt: local.created_at,
    keywords: extractKeywords(local.content),
  };
  if (!overrides) return base;
  return {
    ...base,
    ...overrides,
    priority: typeof overrides.priority === 'number' ? overrides.priority : basePriority,
  };
}

export async function getStructuredMemories(userId: string, limit = 50): Promise<StructuredMemory[]> {
  const locals = await listLocalMemories(userId, limit * 2);
  return locals.map((l) => buildStructuredMemory(l));
}

export async function addStructuredMemory(
  userId: string,
  content: string,
  type?: MemoryType,
  source?: string,
  priority?: number
): Promise<StructuredMemory> {
  const trimmed = content.trim().slice(0, 1000);
  const local = await addLocalMemory(userId, trimmed, type || 'fact', source, priority);
  const overrides: Partial<StructuredMemory> = { type: type || classifyContent(trimmed) };
  if (typeof priority === 'number') overrides.priority = priority;
  broadcastSync('memory-updated', { memoryId: local.id, userId });
  return buildStructuredMemory(local, overrides);
}

export function keywordSimilarity(a: string[], b: string[]): number {
  if (a.length === 0 || b.length === 0) return 0;
  const setA = new Set(a);
  const intersection = b.filter((x) => setA.has(x)).length;
  return intersection / Math.sqrt(a.length * b.length);
}

export function searchMemories(
  memories: StructuredMemory[],
  query: string,
  topK = 8
): MemorySearchResult[] {
  const queryKeywords = extractKeywords(query);
  const scored = memories.map((memory) => {
    const recency = Math.max(0, 1 - (Date.now() - new Date(memory.createdAt).getTime()) / (1000 * 60 * 60 * 24 * 90));
    const kwScore = keywordSimilarity(memory.keywords, queryKeywords);
    const contentScore = keywordSimilarity(extractKeywords(memory.content), queryKeywords);
    const importance = memory.importance / 100;
    const score = kwScore * 3 + contentScore * 2 + recency * 0.5 + importance * 0.3;
    return { memory, score };
  });

  return scored
    .filter((r) => r.score > 0.05)
    .sort((a, b) => b.memory.priority - a.memory.priority || b.score - a.score)
    .slice(0, topK);
}

export function formatMemoriesForPrompt(memories: StructuredMemory[]): string {
  if (memories.length === 0) return '';
  const byType: Partial<Record<MemoryType, StructuredMemory[]>> = {};
  for (const m of memories) {
    byType[m.type] = byType[m.type] || [];
    byType[m.type]!.push(m);
  }

  const lines: string[] = ['\n【长期记忆】'];
  for (const type of Object.keys(byType) as MemoryType[]) {
    lines.push(`\n${MEMORY_TYPE_DESCRIPTIONS[type]}：`);
    for (const m of byType[type]!.slice(0, 6)) {
      lines.push(`- ${m.content}`);
    }
  }
  return lines.join('\n');
}

export async function rememberFact(userId: string, content: string, source?: string): Promise<StructuredMemory> {
  return addStructuredMemory(userId, content, 'fact', source);
}

export async function rememberPreference(userId: string, content: string, source?: string): Promise<StructuredMemory> {
  return addStructuredMemory(userId, content, 'preference', source);
}

export async function rememberTask(userId: string, content: string, source?: string): Promise<StructuredMemory> {
  return addStructuredMemory(userId, content, 'task', source);
}

export async function buildMemoryContext(userId: string, query: string, maxMemories = 8): Promise<string[]> {
  const memories = await getStructuredMemories(userId, 100);
  const results = searchMemories(memories, query, maxMemories);
  return results.map((r) => `(${MEMORY_TYPE_DESCRIPTIONS[r.memory.type]}) ${r.memory.content}`);
}

export async function consolidateMemories(userId: string): Promise<void> {
  const memories = await getStructuredMemories(userId, 200);
  const duplicates: string[][] = [];
  const seen = new Set<string>();

  for (let i = 0; i < memories.length; i++) {
    if (seen.has(memories[i].id)) continue;
    const group = [memories[i].id];
    for (let j = i + 1; j < memories.length; j++) {
      if (seen.has(memories[j].id)) continue;
      const sim = keywordSimilarity(memories[i].keywords, memories[j].keywords);
      if (sim > 0.7) {
        group.push(memories[j].id);
        seen.add(memories[j].id);
      }
    }
    if (group.length > 1) duplicates.push(group);
  }

  // Store consolidation metadata for future review.
  const index = (await getLocalConfig<Record<string, unknown>>(MEMORY_INDEX_KEY, userId)) || {};
  index.lastConsolidated = new Date().toISOString();
  index.duplicateGroups = duplicates.length;
  await setLocalConfig(MEMORY_INDEX_KEY, index, userId);
}
