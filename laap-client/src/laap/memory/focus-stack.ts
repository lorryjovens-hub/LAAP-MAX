/**
 * Focus Stack — Multi-Frame Context Memory
 *
 * Adapted from BaiLongma's src/memory/focus.js
 *
 * A stack of focus frames. Each frame captures:
 *  - intent: what the user/agent was trying to do
 *  - entities: key entities mentioned
 *  - timeRange: when this focus was active
 *  - regression: whether recent conversation returned to a previous topic
 *
 * The stack enables **regression judgment**: when the current conversation
 * returns to a previously discussed topic, we can inject the relevant
 * frame's context instead of keeping everything in the prompt.
 *
 * This is the KEY mechanism for token-efficient context management.
 */

export interface FocusFrame {
  id: string
  intent: string
  entities: string[]
  summary: string
  startedAt: number
  lastActiveAt: number
  turnCount: number
  /** 0-1 how resolved this frame is (1 = fully resolved, can archive) */
  resolution: number
  /** Whether this frame is the currently active one */
  active: boolean
}

export type FocusStackEvent =
  | { type: 'frame-pushed'; frame: FocusFrame }
  | { type: 'frame-popped'; frameId: string }
  | { type: 'frame-regressed'; frameId: string }
  | { type: 'frame-archived'; frameId: string }
  | { type: 'focus-cleared' }

export type FocusListener = (event: FocusStackEvent) => void

export class FocusStack {
  private frames: FocusFrame[] = []
  private listeners = new Set<FocusListener>()
  private nextId = 1

  /** Max frames in active stack */
  private maxActiveFrames = 5

  /** How long (ms) without activity before a frame is auto-archived */
  private archiveTimeoutMs = 30 * 60 * 1000 // 30 minutes

  /** Get all active frames */
  getFrames(): FocusFrame[] {
    return [...this.frames]
  }

  /** Get the current (most recent) active frame */
  getCurrentFrame(): FocusFrame | undefined {
    return this.frames.find(f => f.active)
  }

  /** Get frame by ID */
  getFrame(id: string): FocusFrame | undefined {
    return this.frames.find(f => f.id === id)
  }

  /**
   * Push a new focus frame.
   * Deactivates the current frame and creates a new active one.
   */
  push(intent: string, entities: string[], summary: string): FocusFrame {
    // Deactivate current frames
    for (const frame of this.frames) {
      if (frame.active) {
        frame.active = false
        frame.resolution = Math.min(frame.resolution + 0.3, 1)
      }
    }

    const frame: FocusFrame = {
      id: `focus-${this.nextId++}`,
      intent,
      entities,
      summary,
      startedAt: Date.now(),
      lastActiveAt: Date.now(),
      turnCount: 1,
      resolution: 0,
      active: true,
    }

    this.frames.push(frame)
    this.emit({ type: 'frame-pushed', frame })
    this.prune()
    return frame
  }

  /**
   * Check if the current conversation returns to a previous topic.
   * This is **regression judgment** — the core innovation.
   *
   * @returns the regressed-to frame if found, null if it's a new topic
   */
  detectRegression(intent: string, entities: string[]): FocusFrame | null {
    // Check non-active frames for topic match
    for (const frame of this.frames) {
      if (frame.active) continue

      // Check entity overlap
      const entityOverlap = entities.filter(e =>
        frame.entities.some(fe => fe.toLowerCase() === e.toLowerCase()),
      ).length

      // Check intent similarity (simple word overlap)
      const intentWords = new Set(intent.toLowerCase().split(/\s+/))
      const frameIntentWords = frame.intent.toLowerCase().split(/\s+/)
      const intentOverlap = frameIntentWords.filter(w => intentWords.has(w)).length

      const minOverlap = Math.min(entities.length, frame.entities.length)
      const entityScore = minOverlap > 0 ? entityOverlap / minOverlap : 0
      const intentScore = frameIntentWords.length > 0 ? intentOverlap / frameIntentWords.length : 0

      // Regression threshold: significant entity match OR strong intent match
      if (entityScore >= 0.5 || (entityScore >= 0.3 && intentScore >= 0.4)) {
        // Regression detected! Reactivate this frame
        frame.active = true
        frame.lastActiveAt = Date.now()
        frame.turnCount++

        // Deactivate other active frames
        for (const f of this.frames) {
          if (f.id !== frame.id) f.active = false
        }

        this.emit({ type: 'frame-regressed', frameId: frame.id })
        this.prune()
        return frame
      }
    }

    return null
  }

  /**
   * Update the current frame with new entities and intent.
   * Called each turn to keep the frame fresh.
   */
  updateCurrent(intent: string, entities: string[], summary: string): void {
    const current = this.getCurrentFrame()
    if (!current) {
      this.push(intent, entities, summary)
      return
    }

    current.lastActiveAt = Date.now()
    current.turnCount++

    // Merge new entities
    for (const entity of entities) {
      if (!current.entities.some(e => e.toLowerCase() === entity.toLowerCase())) {
        current.entities.push(entity)
      }
    }

    // Update summary (keep latest)
    current.summary = summary

    // Slightly reduce resolution (topic is still active)
    current.resolution = Math.max(current.resolution - 0.1, 0)
  }

  /** Pop (remove) a specific frame */
  pop(frameId: string): void {
    this.frames = this.frames.filter(f => f.id !== frameId)
    this.emit({ type: 'frame-popped', frameId })

    // If the active frame was popped, activate the most recent non-active
    if (!this.getCurrentFrame() && this.frames.length > 0) {
      const latest = this.frames[this.frames.length - 1]
      latest.active = true
    }
  }

  /** Mark a frame as resolved */
  resolve(frameId: string): void {
    const frame = this.frames.find(f => f.id === frameId)
    if (!frame) return

    frame.resolution = 1
    if (frame.active) {
      frame.active = false
      // Activate previous frame if exists
      const previous = this.frames
        .filter(f => f.id !== frameId)
        .sort((a, b) => b.lastActiveAt - a.lastActiveAt)
      if (previous.length > 0) {
        previous[0].active = true
      }
    }
  }

  /** Clear all frames */
  clear(): void {
    this.frames = []
    this.emit({ type: 'focus-cleared' })
  }

  /** Subscribe to focus events */
  onEvent(listener: FocusListener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  /**
   * Render the focus stack for context injection.
   * Returns a compact text representation.
   */
  renderForContext(maxFrames = 2): string {
    const relevant = this.frames
      .filter(f => f.resolution < 1 || f.active)
      .sort((a, b) => {
        // Active frames first, then by recency
        if (a.active !== b.active) return a.active ? -1 : 1
        return b.lastActiveAt - a.lastActiveAt
      })
      .slice(0, maxFrames)

    if (relevant.length === 0) return ''

    const lines = ['<focus_stack>']
    for (const frame of relevant) {
      const status = frame.active ? 'ACTIVE' : frame.resolution >= 1 ? 'RESOLVED' : 'BACKGROUND'
      lines.push(`  <frame id="${frame.id}" status="${status}" turns="${frame.turnCount}">`)
      lines.push(`    <intent>${escapeXml(frame.intent)}</intent>`)
      lines.push(`    <entities>${frame.entities.join(', ')}</entities>`)
      if (frame.summary) {
        lines.push(`    <summary>${escapeXml(frame.summary)}</summary>`)
      }
      lines.push('  </frame>')
    }
    lines.push('</focus_stack>')
    return lines.join('\n')
  }

  // ── Private ──

  private emit(event: FocusStackEvent): void {
    for (const listener of this.listeners) {
      listener(event)
    }
  }

  /** Prune old, resolved frames */
  private prune(): void {
    const now = Date.now()

    this.frames = this.frames.filter(f => {
      // Keep active frames
      if (f.active) return true

      // Keep unresolved frames
      if (f.resolution < 1) return true

      // Keep recently resolved frames (within archive timeout)
      if (now - f.lastActiveAt < this.archiveTimeoutMs) return true

      // Archive everything else
      this.emit({ type: 'frame-archived', frameId: f.id })
      return false
    })

    // Enforce max active frames
    if (this.frames.length > this.maxActiveFrames) {
      const sorted = [...this.frames].sort((a, b) => {
        if (a.active !== b.active) return a.active ? -1 : 1
        return b.lastActiveAt - a.lastActiveAt
      })
      this.frames = sorted.slice(0, this.maxActiveFrames)
    }
  }
}

function escapeXml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}
