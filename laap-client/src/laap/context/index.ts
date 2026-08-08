/**
 * Context Injection Pipeline — Public API
 */

export { runInjectionPipeline, createSection } from './runtime-injector'
export { gateSections, applyGate } from './section-gate'
export { checkContextSufficiency, runGatherer, extractEntities } from './gatherer'

export type {
  ContextSection,
  InjectionResult,
  SectionScore,
  GathererResolution,
  GathererAction,
  PipelineConfig,
} from './types'

export { DEFAULT_PIPELINE_CONFIG } from './types'
