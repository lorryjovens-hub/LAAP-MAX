import { ensureLocalUser, getLocalConfig, setLocalConfig } from '@/lib/db';
import { buildMemoryContext } from '@/lib/memoryManager';
import type { AppSettings } from '@/lib/settings';

export interface Paper {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  url: string;
  pdfUrl?: string;
  publishedAt: string;
  updatedAt: string;
  categories: string[];
  primaryCategory: string;
}

export interface PaperAnalysis {
  paper: Paper;
  summary: string;
  breakthroughScore: number;
  relevanceScore: number;
  keywords: string[];
}

export interface AcademicFeedState {
  interests: string[];
  lastFetchAt: string | null;
  cachedAnalyses: PaperAnalysis[];
  notifiedIds: string[];
}

const ACADEMIC_FEED_KEY = 'laap_academic_feed_state';
const BREAKTHROUGH_SCORE_THRESHOLD = 0.75;

function extractKeywords(text: string): string[] {
  const stops = new Set([
    'the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'to', 'for', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were',
    '的', '是', '在', '和', '与', '了', '我', '你', '我们', '这个', '一个', '为', '对', '有', '将', '就', '不', '也',
  ]);
  return text
    .toLowerCase()
    .split(/[^\p{L}\p{N}]+/u)
    .filter((w) => w.length >= 3 && !stops.has(w))
    .slice(0, 20);
}

function relevanceScore(paper: Paper, interests: string[]): number {
  if (interests.length === 0) return 0.5;
  const paperText = `${paper.title} ${paper.abstract} ${paper.categories.join(' ')}`.toLowerCase();
  let matches = 0;
  for (const interest of interests) {
    const query = interest.toLowerCase();
    if (paperText.includes(query)) matches++;
  }
  return Math.min(1, matches / Math.max(1, interests.length) + 0.2);
}

function breakthroughScore(paper: Paper): number {
  let score = 0.5;
  const abstract = paper.abstract.toLowerCase();
  const title = paper.title.toLowerCase();

  const breakthroughMarkers = [
    'breakthrough', 'novel', 'state-of-the-art', 'sota', 'first time', 'outperform',
    'significant improvement', 'milestone', 'paradigm shift', 'new approach',
    '突破', '首次', '超越', '最先进', '里程碑', '范式转变',
  ];
  for (const marker of breakthroughMarkers) {
    if (abstract.includes(marker) || title.includes(marker)) score += 0.08;
  }

  const methodMarkers = ['transformer', 'llm', 'large language model', 'agent', 'reasoning', 'multimodal', 'agi'];
  for (const marker of methodMarkers) {
    if (abstract.includes(marker) || title.includes(marker)) score += 0.03;
  }

  return Math.min(1, score);
}

export async function getAcademicFeedState(): Promise<AcademicFeedState> {
  const stored = await getLocalConfig<AcademicFeedState>(ACADEMIC_FEED_KEY);
  return stored || { interests: [], lastFetchAt: null, cachedAnalyses: [], notifiedIds: [] };
}

export async function setAcademicFeedState(state: AcademicFeedState): Promise<void> {
  await setLocalConfig(ACADEMIC_FEED_KEY, state);
}

export async function setAcademicInterests(interests: string[]): Promise<void> {
  const state = await getAcademicFeedState();
  state.interests = interests.map((s) => s.trim()).filter(Boolean).slice(0, 10);
  await setAcademicFeedState(state);
}

export async function searchPapers(query: string, maxResults = 10): Promise<Paper[]> {
  const encoded = encodeURIComponent(query);
  const url = `https://export.arxiv.org/api/query?search_query=all:${encoded}&start=0&max_results=${maxResults}&sortBy=submittedDate&sortOrder=descending`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`arXiv 请求失败：${response.status}`);
  }

  const xml = await response.text();
  const entries = xml.split('<entry>').slice(1);
  const papers: Paper[] = [];

  for (const entry of entries) {
    const idMatch = entry.match(/<id>([^<]+)<\/id>/);
    const titleMatch = entry.match(/<title>([\s\S]*?)<\/title>/);
    const summaryMatch = entry.match(/<summary>([\s\S]*?)<\/summary>/);
    const publishedMatch = entry.match(/<published>([^<]+)<\/published>/);
    const updatedMatch = entry.match(/<updated>([^<]+)<\/updated>/);
    const categoryMatches = entry.match(/<category term="([^"]+)"/g) || [];

    if (!idMatch || !titleMatch || !summaryMatch) continue;

    const id = idMatch[1].trim();
    const title = titleTitle(titleMatch[1].trim());
    const abstract = cleanText(summaryMatch[1].trim());
    const authors: string[] = [];
    const authorMatches = entry.match(/<name>([^<]+)<\/name>/g) || [];
    for (const am of authorMatches) {
      const m = am.match(/<name>([^<]+)<\/name>/);
      if (m) authors.push(m[1].trim());
    }

    papers.push({
      id,
      title,
      authors,
      abstract,
      url: id,
      pdfUrl: id.replace('/abs/', '/pdf/'),
      publishedAt: publishedMatch?.[1].trim() || updatedMatch?.[1].trim() || '',
      updatedAt: updatedMatch?.[1].trim() || '',
      categories: categoryMatches.map((c) => {
        const m = c.match(/term="([^"]+)"/);
        return m ? m[1] : '';
      }).filter(Boolean),
      primaryCategory: categoryMatches[0] ? (categoryMatches[0].match(/term="([^"]+)"/)?.[1] || '') : '',
    });
  }

  return papers;
}

function titleTitle(text: string): string {
  return text.replace(/\s+/g, ' ').trim();
}

function cleanText(text: string): string {
  return text.replace(/\s+/g, ' ').trim();
}

export function analyzePaper(paper: Paper, interests: string[] = []): PaperAnalysis {
  const keywords = extractKeywords(`${paper.title} ${paper.abstract}`);
  const firstSentence = paper.abstract.split(/[.!?。！？]/)?.[0]?.trim() || paper.abstract.slice(0, 200);
  return {
    paper,
    summary: firstSentence,
    breakthroughScore: breakthroughScore(paper),
    relevanceScore: relevanceScore(paper, interests),
    keywords,
  };
}

export async function getRecommendedPapers(_settings: AppSettings, maxResults = 5): Promise<PaperAnalysis[]> {
  const user = await ensureLocalUser();
  const state = await getAcademicFeedState();
  let interests = state.interests;

  if (interests.length === 0) {
    const context = await buildMemoryContext(user.id, 'research interests academic topics', 12);
    interests = context.flatMap((m) => extractKeywords(m));
  }

  const query = interests.length > 0 ? interests.join(' AND ') : 'artificial intelligence';
  const papers = await searchPapers(query, Math.max(maxResults, 20));
  const analyses = papers.map((p) => analyzePaper(p, interests));
  analyses.sort((a, b) => b.relevanceScore - a.relevanceScore);

  state.cachedAnalyses = analyses.slice(0, 20);
  state.lastFetchAt = new Date().toISOString();
  await setAcademicFeedState(state);

  return analyses.slice(0, maxResults);
}

export async function getBreakthroughPapers(maxResults = 3): Promise<PaperAnalysis[]> {
  const state = await getAcademicFeedState();
  if (state.cachedAnalyses.length > 0) {
    const candidates = state.cachedAnalyses
      .filter((a) => a.breakthroughScore >= BREAKTHROUGH_SCORE_THRESHOLD)
      .filter((a) => !state.notifiedIds.includes(a.paper.id))
      .sort((a, b) => b.breakthroughScore - a.breakthroughScore)
      .slice(0, maxResults);
    if (candidates.length > 0) return candidates;
  }

  const papers = await searchPapers('breakthrough artificial intelligence', Math.max(maxResults, 20));
  const analyses = papers.map((p) => analyzePaper(p, state.interests));
  return analyses
    .filter((a) => a.breakthroughScore >= BREAKTHROUGH_SCORE_THRESHOLD)
    .sort((a, b) => b.breakthroughScore - a.breakthroughScore)
    .slice(0, maxResults);
}

export async function markNotified(analysis: PaperAnalysis): Promise<void> {
  const state = await getAcademicFeedState();
  if (!state.notifiedIds.includes(analysis.paper.id)) {
    state.notifiedIds.push(analysis.paper.id);
    await setAcademicFeedState(state);
  }
}

export function formatPaperAsMarkdown(analysis: PaperAnalysis): string {
  const { paper, summary, breakthroughScore, relevanceScore } = analysis;
  const lines = [
    `### ${paper.title}`,
    '',
    `**作者**：${paper.authors.slice(0, 5).join(', ')}${paper.authors.length > 5 ? ' 等' : ''}`,
    `**发布时间**：${paper.publishedAt.slice(0, 10)}`,
    `**领域**：${paper.primaryCategory || paper.categories[0] || 'N/A'}`,
    `**相关度**：${Math.round(relevanceScore * 100)}% · **突破性**：${Math.round(breakthroughScore * 100)}%`,
    '',
    `> ${summary}`,
    '',
    `[查看论文](${paper.url})${paper.pdfUrl ? ` · [PDF](${paper.pdfUrl})` : ''}`,
  ];
  return lines.join('\n');
}
