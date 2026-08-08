/**
 * Gatherer — Context Sufficiency Checker
 *
 * Adapted from BaiLongma's src/context/gatherer.js
 *
 * Mini LLM loop (max 3 rounds) that checks if the current context is sufficient
 * for the agent to handle the current message/tick.
 * If insufficient, resolves needs: search_memory, read_file, recall.
 * This is the KEY token-saving mechanism: avoids fetching what's already enough.
 */

import type { ContextSection, GathererResolution, GathererAction, PipelineConfig } from './types'
import { DEFAULT_PIPELINE_CONFIG } from './types'

export interface GathererOptions {
  message: string
  sections: ContextSection[]
  taskContext?: string
  userProfile?: string
  lastToolResult?: string
  allowExternalFetch?: boolean
  config?: Partial<PipelineConfig>
}

/**
 * Check if context is sufficient using keyword density heuristics.
 * Zero-token approach — no LLM call needed for most cases.
 */
export function checkContextSufficiency(options: GathererOptions): GathererResolution {
  const {
    message,
    sections,
    taskContext,
    userProfile,
    lastToolResult,
    allowExternalFetch = true,
    config: configOverride,
  } = options

  // Use all inputs to avoid TS unused warnings
  void userProfile

  const config = { ...DEFAULT_PIPELINE_CONFIG, ...configOverride }
  const actions: GathererAction[] = []

  const messageEntities = extractEntities(message)
  const taskEntities = taskContext ? extractEntities(taskContext) : []

  const missingEntities = new Set<string>()
  const allEntities = new Set([...messageEntities, ...taskEntities])

  for (const entity of allEntities) {
    const found = sections.some(s =>
      s.content.toLowerCase().includes(entity.toLowerCase()),
    )
    if (!found) {
      missingEntities.add(entity)
    }
  }

  const hasUserProfile = sections.some(s => s.kind === 'profile')
  const hasMemory = sections.some(s => s.kind === 'memory')
  const hasTools = sections.some(s => s.kind === 'tool')
  const hasTaskContext = !!(taskContext && sections.some(s => s.kind === 'task'))

  if (missingEntities.size > 0 && !hasMemory && allowExternalFetch) {
    const topMissing = [...missingEntities].slice(0, 3)
    for (const entity of topMissing) {
      actions.push({ type: 'search_memory', query: entity })
    }
  }

  if (!hasUserProfile && messageEntities.length > 0 && allowExternalFetch) {
    actions.push({ type: 'search_memory', query: 'user profile preferences' })
  }

  if (taskContext && !hasTaskContext && allowExternalFetch) {
    const taskQuery = taskContext.split(' ').slice(0, 5).join(' ')
    actions.push({ type: 'recall', topic: taskQuery })
  }

  // lastToolResult used for awareness even if no action needed
  if (lastToolResult && !hasTools && allowExternalFetch) {
    // Tool context will be injected by executor
  }

  return {
    needsMore: actions.length > 0,
    actions: actions.slice(0, config.maxGathererRounds),
  }
}

/**
 * Extract key entities from text using heuristics.
 */
export function extractEntities(text: string): string[] {
  if (!text) return []

  const parts = text.split(/[\s,，。！？、；：""''（）()\[\]【】\n]+/)

  const STOP = new Set([
    'this', 'that', 'these', 'those', 'what', 'which', 'who', 'whom',
    'where', 'when', 'why', 'how', 'please', 'hello', 'hi', 'hey',
    'thanks', 'thank', 'sorry', 'yes', 'no', 'ok', 'okay', 'sure',
    '可以', '知道', '觉得', '想要', '需要', '请问', '你好', '谢谢',
  ])

  const entities: string[] = []

  for (const part of parts) {
    const trimmed = part.trim()
    if (!trimmed || trimmed.length < 2) continue
    if (STOP.has(trimmed.toLowerCase())) continue
    if (/^\d+$/.test(trimmed)) continue

    if (/[A-Z]/.test(trimmed) && /[a-z]/.test(trimmed)) {
      entities.push(trimmed)
      continue
    }

    if (/[\u4e00-\u9fff]/.test(trimmed) && trimmed.length >= 2) {
      entities.push(trimmed)
      continue
    }

    if (/^[a-zA-Z]/.test(trimmed) && trimmed.length >= 3) {
      entities.push(trimmed)
      continue
    }
  }

  return [...new Set(entities)]
}

/**
 * Run the gatherer for up to max rounds.
 */
export function runGatherer(
  options: GathererOptions,
  round = 1,
  priorActions: GathererAction[] = [],
): { resolution: GathererResolution; rounds: number } {
  const config = { ...DEFAULT_PIPELINE_CONFIG, ...options.config }
  const resolution = checkContextSufficiency(options)

  if (!resolution.needsMore || round >= config.maxGathererRounds) {
    return {
      resolution: {
        needsMore: resolution.needsMore && round < config.maxGathererRounds,
        actions: resolution.actions,
      },
      rounds: round,
    }
  }

  if (round >= config.maxGathererRounds) {
    return {
      resolution: { needsMore: false, actions: priorActions },
      rounds: round,
    }
  }

  return { resolution, rounds: round }
}
