/**
 * Context Injection Pipeline — Type Definitions
 *
 * Adapted from BaiLongma's architecture:
 *   gatherer.ts → section-gate.ts → runtime-injector.ts
 *
 * Each section carries semantic metadata for relevance scoring.
 * The pipeline decides WHAT to inject and HOW MUCH.
 */

/** A single context section that may be injected into the LLM prompt */
export interface ContextSection {
  id: string
  kind: 'memory' | 'tool' | 'profile' | 'task' | 'thought' | 'system'
          | 'self' | 'social' | 'knowledge' | 'scene' | 'action-log'
  label: string
  content: string
  /** Estimated token contribution (cached for budget tracking) */
  estimatedTokens: number
  /** Relevance score set by section-gate (0-1), 0 = drop */
  relevanceScore: number
  /** Hard pinned — bypass relevance gating */
  pinned: boolean
  /** Metadata for downstream consumers */
  meta?: Record<string, unknown>
}

/** Result of the full injection pipeline */
export interface InjectionResult {
  sections: ContextSection[]
  /** Concatenated prompt-ready context block */
  contextBlock: string
  /** Total estimated tokens injected */
  totalTokens: number
  /** Pipeline diagnostics */
  diagnostics: {
    sectionsInput: number
    sectionsDropped: number
    gathererRounds: number
    gathererActions: string[]
    durationMs: number
  }
}

/** Scoring criteria output by section-gate */
export interface SectionScore {
  sectionId: string
  score: number
  matchedKeywords: string[]
  dropped: boolean
  reason?: string
}

/** Gatherer resolution — what the gatherer decides is missing */
export interface GathererResolution {
  needsMore: boolean
  actions: GathererAction[]
}

export type GathererAction =
  | { type: 'search_memory'; query: string }
  | { type: 'read_file'; path: string }
  | { type: 'recall'; topic: string }
  | { type: 'fetch_web'; url: string }
  | { type: 'none'; reason: string }

/** Pipeline configuration */
export interface PipelineConfig {
  /** Maximum sections to inject per turn */
  maxSections: number
  /** Keyword relevance threshold (0-1), below this = dropped */
  relevanceThreshold: number
  /** Maximum gatherer rounds */
  maxGathererRounds: number
  /** Whether to run gatherer on user messages */
  gatherOnUserMessage: boolean
  /** Whether to run gatherer on tick messages */
  gatherOnTick: boolean
  /** Token budget for context block */
  tokenBudget: number
}

export const DEFAULT_PIPELINE_CONFIG: PipelineConfig = {
  maxSections: 20,
  relevanceThreshold: 0.15,
  maxGathererRounds: 3,
  gatherOnUserMessage: true,
  gatherOnTick: false,
  tokenBudget: 4096,
}
