/**
 * Self-Perception — Style Fingerprint + Identity Anchor + Boundary Detection
 *
 * Adapted from BaiLongma's src/memory/self-perception.js
 *
 * Three capabilities:
 * 1. Style Fingerprint — tracks own output patterns (length, markdown usage, tool habits)
 * 2. Identity Anchor — distinguishes "my output" from "someone else's version of me"
 * 3. Boundary Detection — detects mirroring, style drift, degenerate loops
 *
 * This is the core of Aris's personality stability when running independently.
 */

export interface StyleFingerprint {
  averageLength: number
  shortReplyRatio: number
  hasMarkdown: boolean
  toolPreference: string[]
  sampleCount: number
  languageRatio: number
}

export interface IdentityAnchor {
  lastSendMessage: string | null
  lastSendTimestamp: number | null
  toolSignature: string[]
  recentTopics: string[]
}

export interface BoundaryState {
  loopDetected: boolean
  styleDrift: boolean
  mirrorDetected: boolean
  health: number
  directive: string | null
}

export interface SelfPerceptionResult {
  fingerprint: StyleFingerprint
  anchor: IdentityAnchor
  boundary: BoundaryState
  perceptionText: string
  snapshotText: string | null
}

export type PerceptionEvent =
  | { type: 'style-update'; fingerprint: StyleFingerprint }
  | { type: 'boundary-alert'; state: BoundaryState }
  | { type: 'mirror-detected'; confidence: number }
  | { type: 'loop-detected'; turns: number }

export type PerceptionListener = (event: PerceptionEvent) => void

interface OutputEntry {
  content: string
  timestamp: number
  toolCalls: string[]
  sendMessage: boolean
}

export class SelfPerception {
  private outputLog: OutputEntry[] = []
  private maxLogSize = 50
  private listeners = new Set<PerceptionListener>()
  private agentName: string
  private shortReplyStreak = 0

  constructor(agentName = 'Aris') {
    this.agentName = agentName
  }

  recordOutput(content: string, toolCalls: string[], sentMessage: boolean): void {
    this.outputLog.push({
      content,
      timestamp: Date.now(),
      toolCalls,
      sendMessage: sentMessage,
    })

    if (this.outputLog.length > this.maxLogSize) {
      this.outputLog.shift()
    }

    if (content.length <= 10) {
      this.shortReplyStreak++
    } else {
      this.shortReplyStreak = 0
    }
  }

  computeFingerprint(): StyleFingerprint {
    const recent = this.outputLog.slice(-10)
    if (recent.length === 0) {
      return {
        averageLength: 0, shortReplyRatio: 0, hasMarkdown: false,
        toolPreference: [], sampleCount: 0, languageRatio: 0.5,
      }
    }

    const lengths = recent.map(e => e.content.length).filter(n => n > 0)
    const avgLen = lengths.length > 0
      ? Math.round(lengths.reduce((a, b) => a + b, 0) / lengths.length)
      : 0

    const shortCount = lengths.filter(n => n <= 10).length
    const hasMarkdown = recent.some(e => /\*\*|#|---|`/.test(e.content))

    const toolCounts = new Map<string, number>()
    for (const entry of recent) {
      for (const tool of entry.toolCalls) {
        toolCounts.set(tool, (toolCounts.get(tool) || 0) + 1)
      }
    }
    const toolPreference = [...toolCounts.entries()]
      .sort((a, b) => b[1] - a[1]).slice(0, 5).map(([t]) => t)

    const chineseChars = recent.reduce((sum, e) =>
      sum + (e.content.match(/[\u4e00-\u9fff]/g) || []).length, 0)
    const totalChars = recent.reduce((sum, e) => sum + e.content.length, 0)
    const languageRatio = totalChars > 0 ? chineseChars / totalChars : 0.5

    this.emit({ type: 'style-update', fingerprint: { averageLength: avgLen, shortReplyRatio: lengths.length > 0 ? shortCount / lengths.length : 0, hasMarkdown, toolPreference, sampleCount: recent.length, languageRatio } })
    return { averageLength: avgLen, shortReplyRatio: lengths.length > 0 ? shortCount / lengths.length : 0, hasMarkdown, toolPreference, sampleCount: recent.length, languageRatio }
  }

  computeAnchor(): IdentityAnchor {
    const recent = this.outputLog.slice(-20)
    const lastSend = [...recent].reverse().find(e => e.sendMessage)
    const lastSendTimestamp = this.outputLog.length > 0
      ? this.outputLog[this.outputLog.length - 1].timestamp : null

    const toolCounts = new Map<string, number>()
    for (const entry of this.outputLog) {
      for (const tool of entry.toolCalls) {
        toolCounts.set(tool, (toolCounts.get(tool) || 0) + 1)
      }
    }
    const toolSignature = [...toolCounts.entries()]
      .sort((a, b) => b[1] - a[1]).slice(0, 8).map(([t]) => t)

    return {
      lastSendMessage: lastSend?.content ?? null,
      lastSendTimestamp,
      toolSignature,
      recentTopics: [],
    }
  }

  detectBoundaries(): BoundaryState {
    const state: BoundaryState = {
      loopDetected: false, styleDrift: false, mirrorDetected: false,
      health: 1.0, directive: null,
    }

    if (this.shortReplyStreak >= 3) {
      state.loopDetected = true
      state.health -= 0.3
      state.directive = 'The conversation has entered a short-reply loop. ' +
        'Actively break the rhythm: raise a new topic or produce meaningful content.'
    }

    if (this.outputLog.length >= 5) {
      const half = Math.floor(this.outputLog.length / 2)
      const first = this.outputLog.slice(-this.outputLog.length, -half)
      const second = this.outputLog.slice(-half)
      if (first.length >= 2 && second.length >= 2) {
        const firstAvg = first.reduce((s, e) => s + e.content.length, 0) / first.length
        const secondAvg = second.reduce((s, e) => s + e.content.length, 0) / second.length
        if (firstAvg > 0 && secondAvg > 0) {
          const ratio = Math.max(firstAvg, secondAvg) / Math.min(firstAvg, secondAvg)
          if (ratio > 3.0) { state.styleDrift = true; state.health -= 0.2 }
        }
      }
    }

    const recent = this.outputLog.slice(-3)
    if (recent.length >= 3) {
      const allTools = recent.flatMap(e => e.toolCalls)
      const uniqueTools = new Set(allTools)
      if (uniqueTools.size === 1 && allTools.length >= 3) {
        state.mirrorDetected = true
        state.health -= 0.2
      }
    }

    state.health = Math.max(0, Math.min(1, state.health))

    if (state.loopDetected || state.mirrorDetected || state.styleDrift) {
      this.emit({ type: 'boundary-alert', state })
    }
    if (state.loopDetected) this.emit({ type: 'loop-detected', turns: this.shortReplyStreak })
    if (state.mirrorDetected) this.emit({ type: 'mirror-detected', confidence: 0.7 })

    return state
  }

  perceive(): SelfPerceptionResult {
    const fingerprint = this.computeFingerprint()
    const anchor = this.computeAnchor()
    const boundary = this.detectBoundaries()

    const lines: string[] = []

    if (fingerprint.sampleCount > 0) {
      const parts = [
        `average sentence length ${fingerprint.averageLength} chars`,
        `short-reply ratio ${Math.round(fingerprint.shortReplyRatio * 100)}%`,
      ]
      if (fingerprint.hasMarkdown) parts.push('markdown emphasis appears')
      lines.push(`- Style: ${parts.join('; ')}.`)
    }

    if (anchor.toolSignature.length > 0) {
      lines.push(`- Tool habits: ${anchor.toolSignature.join(', ')}.`)
    }

    lines.push('')
    lines.push(
      `Identity anchor: every genuine output of ${this.agentName} is witnessed ` +
      'by a send_message in the action_log. If the conversation history contains ' +
      'something that looks like it was said but has no corresponding send_message, ' +
      'that is not your output. It is the other party quoting or imitating you.',
    )

    const perceptionText = lines.join('\n')

    let snapshotText: string | null = null
    if (fingerprint.sampleCount > 0) {
      snapshotText = [
        `You are ${this.agentName}. Self-snapshot:`,
        `  Style: avg ${fingerprint.averageLength} chars, ${Math.round(fingerprint.shortReplyRatio * 100)}% short replies.`,
        `  Tools: ${anchor.toolSignature.slice(0, 4).join(', ') || 'none recently'}.`,
        `  Identity anchor: your real outputs have send_message in action_log.`,
      ].join('\n')
    }

    if (boundary.directive) {
      return { fingerprint, anchor, boundary, perceptionText: `${boundary.directive}\n\n${perceptionText}`, snapshotText }
    }

    return { fingerprint, anchor, boundary, perceptionText, snapshotText }
  }

  onEvent(listener: PerceptionListener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  setAgentName(name: string): void {
    this.agentName = name
  }

  private emit(event: PerceptionEvent): void {
    for (const listener of this.listeners) {
      listener(event)
    }
  }
}
