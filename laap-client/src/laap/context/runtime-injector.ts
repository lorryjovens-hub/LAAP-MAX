/**
 * Runtime Injector — Context Pipeline Orchestrator
 *
 * Adapted from BaiLongma's src/context/runtime-injector.js
 *
 * Orchestrates the full context injection pipeline:
 *   1. Collect raw context sections
 *   2. Run section-gate (relevance scoring + filtering)
 *   3. Run gatherer (sufficiency check)
 *   4. Build final context block
 *   5. Return InjectionResult with diagnostics
 */

import type { ContextSection, InjectionResult, PipelineConfig } from './types'
import { DEFAULT_PIPELINE_CONFIG } from './types'
import { gateSections, applyGate } from './section-gate'
import { runGatherer, type GathererOptions } from './gatherer'

export interface InjectionInput {
  /** Current user message or tick label */
  message: string
  /** Raw context sections to process */
  sections: ContextSection[]
  /** Focus topic (from focus stack) */
  focusTopic?: string
  /** Current task context */
  taskContext?: string
  /** User profile text */
  userProfile?: string
  /** Last tool call result */
  lastToolResult?: string
  /** Whether this is a tick (vs user message) */
  isTick?: boolean
  config?: Partial<PipelineConfig>
}

/**
 * Estimate token count from text (rough heuristic: 4 chars ≈ 1 token)
 */
function estimateTokens(text: string): number {
  // Chinese chars count as ~1.5 tokens each
  const chineseChars = (text.match(/[\u4e00-\u9fff]/g) || []).length
  const otherChars = text.length - chineseChars
  return Math.ceil(chineseChars * 1.5 + otherChars / 4)
}

/**
 * Build the final context block from sections.
 * Uses XML-like structure for clear delimiters.
 */
function buildContextBlock(sections: ContextSection[]): string {
  if (sections.length === 0) return ''

  const parts: string[] = ['<context>']

  // Group sections by kind for coherent rendering
  const kindOrder = ['system', 'self', 'memory', 'profile', 'task', 'tool', 'thought', 'knowledge', 'scene', 'social', 'action-log']

  const grouped = new Map<string, ContextSection[]>()
  for (const section of sections) {
    const list = grouped.get(section.kind) || []
    list.push(section)
    grouped.set(section.kind, list)
  }

  for (const kind of kindOrder) {
    const items = grouped.get(kind)
    if (!items || items.length === 0) continue

    parts.push(`  <${kind}>`)
    for (const item of items) {
      parts.push(`    <item id="${item.id}" label="${escapeXml(item.label)}" score="${item.relevanceScore.toFixed(3)}">`)
      parts.push(`      ${item.content}`)
      parts.push('    </item>')
    }
    parts.push(`  </${kind}>`)
  }

  parts.push('</context>')
  return parts.join('\n')
}

function escapeXml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

/**
 * Main entry point: run the full context injection pipeline.
 *
 * @returns InjectionResult with gated sections, context block, and diagnostics
 */
export async function runInjectionPipeline(input: InjectionInput): Promise<InjectionResult> {
  const startTime = Date.now()
  const config: PipelineConfig = { ...DEFAULT_PIPELINE_CONFIG, ...input.config }

  // Skip pipeline for ticks if configured
  if (input.isTick && !config.gatherOnTick) {
    return {
      sections: input.sections,
      contextBlock: buildContextBlock(input.sections),
      totalTokens: input.sections.reduce((sum, s) => sum + s.estimatedTokens, 0),
      diagnostics: { sectionsInput: input.sections.length, sectionsDropped: 0, gathererRounds: 0, gathererActions: [], durationMs: 0 },
    }
  }

  // Phase 1: Section Gate — score and filter
  const referenceFrame = [input.message, input.focusTopic, input.taskContext]
    .filter(Boolean)
    .join(' ')

  const scores = gateSections(input.sections, referenceFrame, config)
  const gatedSections = applyGate(input.sections, scores, config.maxSections)

  const sectionsDropped = input.sections.length - gatedSections.length

  // Phase 2: Gatherer — check sufficiency
  const gathererInput: GathererOptions = {
    message: input.message,
    sections: gatedSections,
    taskContext: input.taskContext,
    userProfile: input.userProfile,
    lastToolResult: input.lastToolResult,
    allowExternalFetch: !input.isTick,
    config,
  }

  const { resolution, rounds } = runGatherer(gathererInput)
  const gathererActions = resolution.actions.map(a => a.type)

  // Phase 3: Build context block
  // If gatherer requested more data, we'd fetch it here and re-run gate.
  // For now, we proceed with what we have.
  const contextBlock = buildContextBlock(gatedSections)
  const totalTokens = gatedSections.reduce((sum, s) => sum + s.estimatedTokens, 0)

  return {
    sections: gatedSections,
    contextBlock,
    totalTokens,
    diagnostics: {
      sectionsInput: input.sections.length,
      sectionsDropped,
      gathererRounds: rounds,
      gathererActions,
      durationMs: Date.now() - startTime,
    },
  }
}

/**
 * Create a context section helper
 */
export function createSection(
  id: string,
  kind: ContextSection['kind'],
  label: string,
  content: string,
  options?: { pinned?: boolean; meta?: Record<string, unknown> },
): ContextSection {
  return {
    id,
    kind,
    label,
    content,
    estimatedTokens: estimateTokens(content),
    relevanceScore: 0,
    pinned: options?.pinned ?? kind === 'system',
    meta: options?.meta,
  }
}
