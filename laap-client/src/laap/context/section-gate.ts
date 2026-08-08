/**
 * Section Gate — Context Relevance Scoring Engine
 *
 * Adapted from BaiLongma's src/context/section-gate.js
 *
 * Scores each context section against a reference frame (user message + focus topic).
 * Drops sections with relevance below threshold.
 * Pinned sections bypass scoring.
 */

import type { ContextSection, SectionScore, PipelineConfig } from './types'
import { DEFAULT_PIPELINE_CONFIG } from './types'

/**
 * Extract weighted keywords from a reference text.
 * Common Chinese/English stop-words are filtered.
 */
function extractKeywords(text: string, maxKeywords = 20): Map<string, number> {
  const STOP_WORDS = new Set([
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'shall', 'can', 'need', 'dare', 'ought',
    'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
    'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'between', 'out', 'off', 'over', 'under', 'again', 'further', 'then',
    'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each',
    'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
    'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
    'just', 'because', 'but', 'and', 'or', 'if', 'while', 'although',
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
    '个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
    '没有', '看', '好', '自己', '这', '他', '她', '它', '们',
  ])

  const words = text.toLowerCase().split(/[\s,，。！？、；：""''（）()\[\]【】]+/)
  const freq = new Map<string, number>()

  for (const word of words) {
    const trimmed = word.trim()
    if (!trimmed || trimmed.length < 2 || STOP_WORDS.has(trimmed)) continue
    freq.set(trimmed, (freq.get(trimmed) || 0) + 1)
  }

  // Sort by frequency, take top N
  const sorted = [...freq.entries()].sort((a, b) => b[1] - a[1]).slice(0, maxKeywords)
  const maxFreq = sorted[0]?.[1] || 1

  // Normalize scores to 0-1
  const result = new Map<string, number>()
  for (const [word, count] of sorted) {
    result.set(word, count / maxFreq)
  }
  return result
}

/**
 * Score a single section against keyword map.
 * Returns 0-1 score based on keyword density.
 */
function scoreSection(section: ContextSection, keywords: Map<string, number>): number {
  if (section.pinned) return 1.0
  if (!section.content) return 0

  const content = section.content.toLowerCase()
  let totalScore = 0
  let matchCount = 0

  for (const [keyword, weight] of keywords) {
    const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const regex = new RegExp(escaped, 'gi')
    const matches = content.match(regex)
    if (matches) {
      // Weight by both keyword importance and frequency in the section
      totalScore += weight * Math.min(matches.length, 3)
      matchCount++
    }
  }

  if (matchCount === 0) return 0

  // Normalize: average score weighted by keyword coverage
  const avgScore = totalScore / Math.max(matchCount, 1)
  // Bonus for keyword diversity (more distinct keyword matches = more relevant)
  const diversityBonus = Math.min(matchCount / Math.max(keywords.size, 1), 0.3)

  return Math.min(avgScore + diversityBonus, 1.0)
}

/**
 * Main gate: score and filter context sections against a reference frame.
 *
 * @param sections - Raw context sections
 * @param referenceFrame - User message + focus topic (for keyword extraction)
 * @param config - Pipeline configuration
 * @returns Scored and filtered sections
 */
export function gateSections(
  sections: ContextSection[],
  referenceFrame: string,
  config: PipelineConfig = DEFAULT_PIPELINE_CONFIG,
): SectionScore[] {
  const keywords = extractKeywords(referenceFrame)
  const scores: SectionScore[] = []

  for (const section of sections) {
    const score = scoreSection(section, keywords)
    const matchedKeywords = [...keywords.keys()].filter(k =>
      new RegExp(k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi').test(section.content),
    )

    const dropped = !section.pinned && score < config.relevanceThreshold

    scores.push({
      sectionId: section.id,
      score,
      matchedKeywords: matchedKeywords.slice(0, 5), // Limit to top 5
      dropped,
      reason: dropped
        ? `Score ${score.toFixed(3)} below threshold ${config.relevanceThreshold}`
        : undefined,
    })
  }

  return scores
}

/**
 * Apply section scores to context sections — marks dropped sections and updates relevance.
 * Filters out dropped sections and sorts by relevance.
 */
export function applyGate(
  sections: ContextSection[],
  scores: SectionScore[],
  maxSections?: number,
): ContextSection[] {
  const scoreMap = new Map(scores.map(s => [s.sectionId, s]))

  const processed = sections
    .map(s => {
      const score = scoreMap.get(s.id)
      if (!score) return { ...s, relevanceScore: 0 }
      return {
        ...s,
        relevanceScore: score.score,
        pinned: s.pinned || false,
      }
    })
    .filter(s => s.pinned || s.relevanceScore > 0)
    .sort((a, b) => b.relevanceScore - a.relevanceScore)

  const limit = maxSections ?? sections.length
  return processed.slice(0, limit)
}
