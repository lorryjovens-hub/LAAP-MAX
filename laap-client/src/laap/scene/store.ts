/**
 * SceneStore — Monotonic Revision Source
 *
 * The single source of truth for scene state.
 * Agent calls ui.set() → SceneStore upserts/removes → increments revision.
 * The store emits patches for delta sync.
 */

import type { Surface, Scene, ScenePatch, ScenePatchOp } from './types'
import { EMPTY_SCENE } from './types'

export type SceneListener = (scene: Scene) => void
export type PatchListener = (patch: ScenePatch) => void

export class SceneStore {
  private scene: Scene = { ...EMPTY_SCENE }
  private surfaceMap = new Map<string, Surface>()
  private sceneListeners = new Set<SceneListener>()
  private patchListeners = new Set<PatchListener>()

  /** Get current scene snapshot */
  getScene(): Scene {
    return { ...this.scene, surfaces: [...this.scene.surfaces] }
  }

  /** Get current revision number */
  getRevision(): number {
    return this.scene.revision
  }

  /** Get a surface by ID */
  getSurface(id: string): Surface | undefined {
    return this.surfaceMap.get(id)
  }

  /** Upsert a surface (create or update) */
  upsert(surface: Surface): void {
    const prev = this.surfaceMap.get(surface.id)
    const exists = prev !== undefined

    // Update map
    this.surfaceMap.set(surface.id, surface)

    // Build patch op
    const op: ScenePatchOp = { op: 'upsert', surface }

    // Apply to scene array
    if (exists) {
      const idx = this.scene.surfaces.findIndex(s => s.id === surface.id)
      if (idx >= 0) {
        this.scene.surfaces[idx] = surface
      } else {
        this.scene.surfaces.push(surface)
      }
    } else {
      this.scene.surfaces.push(surface)
    }

    // Increment revision
    this.scene.revision++
    this.sortSurfaces()
    this.emitPatch([op])
    this.emitScene()
  }

  /** Remove a surface by ID */
  remove(id: string): void {
    const existed = this.surfaceMap.has(id)
    if (!existed) return

    this.surfaceMap.delete(id)
    this.scene.surfaces = this.scene.surfaces.filter(s => s.id !== id)

    this.scene.revision++
    this.emitPatch([{ op: 'remove', id }])
    this.emitScene()
  }

  /** Clear all non-layout surfaces (e.g., on scene reset) */
  clearTransient(): void {
    const kept: Surface[] = []
    const removed: string[] = []

    for (const surface of this.scene.surfaces) {
      if (surface.kind === 'stack' || surface.kind === 'row' || surface.kind === 'col') {
        kept.push(surface)
      } else {
        removed.push(surface.id)
        this.surfaceMap.delete(surface.id)
      }
    }

    if (removed.length === 0) return

    this.scene.surfaces = kept
    this.scene.revision++
    this.emitPatch(removed.map(id => ({ op: 'remove' as const, id })))
    this.emitScene()
  }

  /** Reset to empty scene */
  reset(): void {
    this.scene = { ...EMPTY_SCENE }
    this.surfaceMap.clear()
    this.emitScene()
  }

  /** Subscribe to scene changes */
  onScene(listener: SceneListener): () => void {
    this.sceneListeners.add(listener)
    // Immediately notify with current state
    listener(this.getScene())
    return () => this.sceneListeners.delete(listener)
  }

  /** Subscribe to patch changes */
  onPatch(listener: PatchListener): () => void {
    this.patchListeners.add(listener)
    return () => this.patchListeners.delete(listener)
  }

  /** Apply a remote patch (from WebSocket) */
  applyPatch(patch: ScenePatch): boolean {
    // Gap detection
    if (patch.base !== this.scene.revision) {
      return false // Caller should request resync
    }

    for (const op of patch.ops) {
      if (op.op === 'upsert') {
        this.applyUpsertFromRemote(op.surface)
      } else if (op.op === 'remove') {
        this.applyRemoveFromRemote(op.id)
      }
    }

    this.scene.revision = patch.revision
    this.sortSurfaces()
    // Don't emit from remote — the source already has the state
    return true
  }

  private applyUpsertFromRemote(surface: Surface): void {
    this.surfaceMap.set(surface.id, surface)
    const idx = this.scene.surfaces.findIndex(s => s.id === surface.id)
    if (idx >= 0) {
      this.scene.surfaces[idx] = surface
    } else {
      this.scene.surfaces.push(surface)
    }
  }

  private applyRemoveFromRemote(id: string): void {
    this.surfaceMap.delete(id)
    this.scene.surfaces = this.scene.surfaces.filter(s => s.id !== id)
  }

  private sortSurfaces(): void {
    this.scene.surfaces.sort((a, b) => a.order - b.order)
  }

  private emitPatch(ops: ScenePatchOp[]): void {
    const patch: ScenePatch = {
      base: this.scene.revision - 1,
      revision: this.scene.revision,
      ops,
    }
    for (const listener of this.patchListeners) {
      listener(patch)
    }
  }

  private emitScene(): void {
    const snapshot = this.getScene()
    for (const listener of this.sceneListeners) {
      listener(snapshot)
    }
  }
}
