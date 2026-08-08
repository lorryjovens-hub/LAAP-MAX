/**
 * Scene Protocol — Type Definitions
 *
 * Adapted from BaiLongma's SCENE-PROTOCOL.md
 *
 * The agent NEVER commands UI. It maintains a **scene** (list of surfaces).
 * The UI shell is a **pure projection** of that scene.
 * User interactions flow back as **intents**.
 */

/** Semantic gravity of a surface — drives animation intensity */
export type SurfaceIntent = 'ambient' | 'inform' | 'confront'

/** Surface kind — determines which component renders it */
export type SurfaceKind =
  | 'text' | 'metric' | 'image' | 'media' | 'choice' | 'progress'
  | 'weather' | 'selfcheck' | 'awakening'
  | 'stack' | 'row' | 'col'  // layout primitives

/** A single surface in the scene */
export interface Surface {
  id: string
  kind: SurfaceKind
  data: Record<string, unknown>
  intent: SurfaceIntent
  focus: boolean
  order: number
}

/** Scene = flat list of surfaces (projection source) */
export interface Scene {
  revision: number
  surfaces: Surface[]
}

/** Patch operation for incremental updates */
export interface ScenePatch {
  base: number  // Expected base revision
  revision: number
  ops: ScenePatchOp[]
}

export type ScenePatchOp =
  | { op: 'upsert'; surface: Surface }
  | { op: 'remove'; id: string }

/** Protocol message from core to shell */
export type CoreMessage =
  | { type: 'scene'; revision: number; surfaces: Surface[] }
  | { type: 'scene.patch'; base: number; revision: number; ops: ScenePatchOp[] }
  | { type: 'welcome'; revision: number }

/** Protocol message from shell to core */
export type ShellMessage =
  | { type: 'hello'; version: number; shell: string; capabilities: string[] }
  | { type: 'intent'; surface: string; name: string; data: unknown; timestamp: number }
  | { type: 'resync'; reason: 'gap' | 'init' | 'error' }

/** Protocol version */
export const SCENE_PROTOCOL_VERSION = 1

/** Standard capabilities */
export const SCENE_CAPABILITIES = ['scene', 'patch'] as const

/** Default scene (empty) */
export const EMPTY_SCENE: Scene = { revision: 0, surfaces: [] }
