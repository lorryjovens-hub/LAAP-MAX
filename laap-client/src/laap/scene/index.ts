/**
 * Scene Protocol — Public API
 *
 * Usage:
 *   import { sceneStore, createSurface } from '../laap/scene'
 */

import { SceneStore } from './store'
import type { Surface } from './types'

export const sceneStore = new SceneStore()

export { SceneClient } from './client'
export type { SceneClientStatus, SceneClientCallbacks } from './client'

export type {
  Surface, Scene, ScenePatch, ScenePatchOp,
  SurfaceKind, SurfaceIntent,
  CoreMessage, ShellMessage,
} from './types'

export {
  SCENE_PROTOCOL_VERSION, SCENE_CAPABILITIES, EMPTY_SCENE,
} from './types'

export function createSurface(
  id: string,
  kind: Surface['kind'],
  data: Record<string, unknown> = {},
  options?: {
    intent?: Surface['intent']
    focus?: boolean
    order?: number
  },
): Surface {
  return {
    id,
    kind,
    data,
    intent: options?.intent ?? 'ambient',
    focus: options?.focus ?? false,
    order: options?.order ?? 0,
  }
}
