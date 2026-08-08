/**
 * Cognitive Engine — Integrates Context Pipeline, Scene Protocol,
 * Focus Stack, and Self-Perception into the LAAP runtime.
 *
 * This is the bridge between the new BaiLongma-derived modules
 * and the existing CognitiveBus + laapStore.
 */

import { CognitiveBusClient } from './bus'
import type { AetherMessage } from './types'
import { sceneStore, createSurface, type Surface, type ScenePatch } from './scene'
import { focusStack, selfPerception } from './memory'
import {
  runInjectionPipeline,
  type ContextSection,
  type InjectionResult,
} from './context'

export interface EngineConfig {
  agentName: string
  enableContextPipeline: boolean
  enableSceneProtocol: boolean
  enableFocusStack: boolean
  enableSelfPerception: boolean
}

const DEFAULT_CONFIG: EngineConfig = {
  agentName: 'Aris',
  enableContextPipeline: true,
  enableSceneProtocol: true,
  enableFocusStack: true,
  enableSelfPerception: true,
}

export interface EngineState {
  lastInjectionResult: InjectionResult | null
  lastPerceptionResult: ReturnType<typeof selfPerception.perceive> | null
  activeSurfaces: Surface[]
  activeFocusFrame: ReturnType<typeof focusStack.getCurrentFrame> | null
}

export class CognitiveEngine {
  private config: EngineConfig
  private bus: CognitiveBusClient
  private state: EngineState = {
    lastInjectionResult: null,
    lastPerceptionResult: null,
    activeSurfaces: [],
    activeFocusFrame: null,
  }
  private cleanups: (() => void)[] = []

  constructor(bus: CognitiveBusClient, config?: Partial<EngineConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config }
    this.bus = bus
    selfPerception.setAgentName(this.config.agentName)
  }

  /**
   * Start the engine — subscribe to CognitiveBus events.
   */
  start(): void {
    if (this.config.enableSceneProtocol) {
      // Listen for scene patches from the backend
      const unsubScene = this.bus.subscribe('scene.*', (msg) => {
        this.handleSceneMessage(msg)
      })
      this.cleanups.push(unsubScene)
    }

    if (this.config.enableFocusStack) {
      // Track conversation focus
      const unsubFocus = this.bus.subscribe('user.input', (msg) => {
        const text = typeof msg.payload === 'object' && msg.payload !== null
          ? String((msg.payload as Record<string, unknown>).text || '')
          : ''
        if (text) {
          this.updateFocus(text)
        }
      })
      this.cleanups.push(unsubFocus)
    }

    if (this.config.enableSelfPerception) {
      // Listen for own outputs
      const unsubPerception = this.bus.subscribe('agent.output', (msg) => {
        const content = typeof msg.payload === 'object' && msg.payload !== null
          ? String((msg.payload as Record<string, unknown>).content || '')
          : ''
        const tools = typeof msg.payload === 'object' && msg.payload !== null
          ? (msg.payload as Record<string, unknown>).tools as string[] || []
          : []
        if (content) {
          selfPerception.recordOutput(content, tools, true)
        }
      })
      this.cleanups.push(unsubPerception)
    }

    // Also subscribe to scene store for frontend updates
    if (this.config.enableSceneProtocol) {
      const unsubSceneStore = sceneStore.onScene((scene) => {
        this.state.activeSurfaces = scene.surfaces
      })
      this.cleanups.push(unsubSceneStore)
    }
  }

  /**
   * Stop the engine and clean up subscriptions.
   */
  stop(): void {
    for (const cleanup of this.cleanups) {
      cleanup()
    }
    this.cleanups = []
  }

  /**
   * Process a user message through the context pipeline.
   * Returns context sections + perception + focus info.
   */
  async processMessage(
    text: string,
    options?: {
      taskContext?: string
      sections?: ContextSection[]
    },
  ): Promise<{
    contextBlock: string
    perceptionText: string
    selfSnapshot: string | null
    focusContext: string
    diagnostics: InjectionResult['diagnostics'] | null
  }> {
    const sections = options?.sections ?? []
    const taskContext = options?.taskContext

    // Context pipeline
    let contextBlock = ''
    let diagnostics: InjectionResult['diagnostics'] | null = null
    if (this.config.enableContextPipeline && sections.length > 0) {
      const result = await runInjectionPipeline({
        message: text,
        sections,
        taskContext,
        isTick: false,
      })
      this.state.lastInjectionResult = result
      contextBlock = result.contextBlock
      diagnostics = result.diagnostics
    }

    // Self-perception
    let perceptionText = ''
    let selfSnapshot: string | null = null
    if (this.config.enableSelfPerception) {
      const perception = selfPerception.perceive()
      this.state.lastPerceptionResult = perception
      perceptionText = perception.perceptionText
      selfSnapshot = perception.snapshotText
    }

    // Focus stack context
    let focusContext = ''
    if (this.config.enableFocusStack) {
      focusContext = focusStack.renderForContext()
    }

    return { contextBlock, perceptionText, selfSnapshot, focusContext, diagnostics }
  }

  /**
   * Update focus stack based on incoming message.
   */
  private updateFocus(text: string): void {
    if (!this.config.enableFocusStack) return
    const entities = extractSimpleEntities(text)

    const current = focusStack.getCurrentFrame()
    if (current) {
      focusStack.updateCurrent(current.intent, entities, text.slice(0, 100))
    } else {
      // Extract intent from first 50 chars
      const intent = text.slice(0, 50).trim()
      focusStack.push(intent, entities, text.slice(0, 100))
    }

    this.state.activeFocusFrame = focusStack.getCurrentFrame()
  }

  /**
   * Handle a scene protocol message from the backend.
   */
  private handleSceneMessage(msg: AetherMessage): void {
    if (!this.config.enableSceneProtocol) return

    const payload = msg.payload as Record<string, unknown>
    const topic = msg.topic

    if (topic === 'scene.snapshot') {
      const surfaces = payload.surfaces as Surface[] | undefined
      if (surfaces) {
        sceneStore.reset()
        for (const surface of surfaces) {
          sceneStore.upsert(surface)
        }
      }
    } else if (topic === 'scene.patch') {
      const patch = payload as unknown as ScenePatch
      sceneStore.applyPatch({
        base: patch.base,
        revision: patch.revision,
        ops: patch.ops,
      })
    } else if (topic === 'scene.upsert') {
      const surface = payload as unknown as Surface
      sceneStore.upsert(surface)
    } else if (topic === 'scene.remove') {
      const id = payload.id as string
      sceneStore.remove(id)
    }
  }

  /**
   * Send a scene update to the backend.
   */
  sendSceneUpdate(surface: Surface): void {
    this.bus.sendAetherMessage({
      id: `scene-${Date.now()}`,
      type: 'scene_update',
      topic: 'scene.upsert',
      payload: surface,
      timestamp: Date.now(),
      sender: 'laap-client',
    })
  }

  /**
   * Send a user intent (from scene interaction) to the backend.
   */
  sendIntent(surfaceId: string, name: string, data: unknown): void {
    this.bus.sendAetherMessage({
      id: `intent-${Date.now()}`,
      type: 'intent',
      topic: 'scene.intent',
      payload: { surface: surfaceId, name, data },
      timestamp: Date.now(),
      sender: 'laap-client',
    })
  }

  /**
   * Get current engine state snapshot.
   */
  getState(): EngineState {
    return { ...this.state }
  }

  /**
   * Get focus stack frames.
   */
  getFocusFrames() {
    return focusStack.getFrames()
  }

  /**
   * Get current scene.
   */
  getScene() {
    return sceneStore.getScene()
  }

  /** Create a sample demonstration to verify the engine works */
  createDemoSurfaces(): void {
    sceneStore.reset()

    sceneStore.upsert(createSurface('greeting', 'text', {
      content: 'Hello, I am Aris. How can I help you today?',
    }, { intent: 'inform', order: 1 }))

    sceneStore.upsert(createSurface('status-metrics', 'metric', {
      label: 'System Status',
      value: 98,
      max: 100,
      unit: '%',
    }, { intent: 'ambient', order: 2 }))

    sceneStore.upsert(createSurface('loading-progress', 'progress', {
      label: 'Initializing',
      value: 0.65,
    }, { intent: 'ambient', order: 3 }))
  }
}

/**
 * Simple entity extraction for focus stack updates.
 */
function extractSimpleEntities(text: string): string[] {
  const entities: string[] = []
  const words = text.split(/[\s,，。]+/)
  for (const word of words) {
    const t = word.trim()
    if (t.length >= 3 && !STOP.has(t.toLowerCase())) {
      entities.push(t)
    }
  }
  return [...new Set(entities)]
}

const STOP = new Set([
  'this', 'that', 'these', 'those', 'the', 'and', 'for', 'are', 'was',
  '你好', '谢谢', '请问', '可以', '知道', '觉得', '想要', '需要',
])
