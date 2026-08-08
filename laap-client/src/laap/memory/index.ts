/**
 * Memory System — Public API
 */

import { FocusStack } from './focus-stack'
import { SelfPerception } from './self-perception'

export { FocusStack } from './focus-stack'
export type { FocusFrame, FocusStackEvent } from './focus-stack'

export { SelfPerception } from './self-perception'
export type {
  StyleFingerprint,
  IdentityAnchor,
  BoundaryState,
  SelfPerceptionResult,
  PerceptionEvent,
} from './self-perception'

export const focusStack = new FocusStack()
export const selfPerception = new SelfPerception('Aris')
