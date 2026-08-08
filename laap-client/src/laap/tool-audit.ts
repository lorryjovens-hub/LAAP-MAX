/**
 * Tool Audit — 工具调用审计链
 *
 * Adapted from BaiLongma's src/tooling/tool-audit.js
 *
 * Records every tool invocation, policy decision, execution result, and
 * downstream effect. Provides an append-only audit log for debugging,
 * compliance, and replay.
 */

export type AuditEntryType = 'intent' | 'policy' | 'execution' | 'result' | 'error' | 'effect'

export interface AuditEntry {
  id: string
  type: AuditEntryType
  timestamp: number
  toolName?: string
  callId?: string
  caller?: 'user' | 'agent' | 'system'
  /** Human-readable summary */
  summary: string
  /** Structured payload for replay / inspection */
  payload: Record<string, unknown>
}

export type AuditListener = (entry: AuditEntry) => void

export class ToolAudit {
  private entries: AuditEntry[] = []
  private listeners = new Set<AuditListener>()
  private maxEntries = 500

  /**
   * Append an entry to the audit log.
   */
  log(entry: Omit<AuditEntry, 'id' | 'timestamp'>): AuditEntry {
    const full: AuditEntry = {
      ...entry,
      id: `audit-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      timestamp: Date.now(),
    }
    this.entries.push(full)
    if (this.entries.length > this.maxEntries) {
      this.entries.shift()
    }
    this.emit(full)
    return full
  }

  /**
   * Convenience methods for common audit events.
   */
  logIntent(toolName: string, args: Record<string, unknown>, caller: AuditEntry['caller'], callId?: string): AuditEntry {
    return this.log({
      type: 'intent',
      toolName,
      callId,
      caller,
      summary: `${caller ?? 'system'} requested ${toolName}`,
      payload: { args },
    })
  }

  logPolicy(toolName: string, decision: string, reason: string, callId?: string): AuditEntry {
    return this.log({
      type: 'policy',
      toolName,
      callId,
      summary: `Policy ${decision} for ${toolName}: ${reason}`,
      payload: { decision, reason },
    })
  }

  logExecution(toolName: string, args: Record<string, unknown>, callId?: string): AuditEntry {
    return this.log({
      type: 'execution',
      toolName,
      callId,
      summary: `Executing ${toolName}`,
      payload: { args },
    })
  }

  logResult(toolName: string, result: unknown, durationMs: number, callId?: string): AuditEntry {
    return this.log({
      type: 'result',
      toolName,
      callId,
      summary: `${toolName} completed in ${durationMs}ms`,
      payload: { result, durationMs },
    })
  }

  logError(toolName: string, error: unknown, callId?: string): AuditEntry {
    const message = error instanceof Error ? error.message : String(error)
    return this.log({
      type: 'error',
      toolName,
      callId,
      summary: `${toolName} failed: ${message}`,
      payload: { error: message },
    })
  }

  logEffect(toolName: string, description: string, callId?: string): AuditEntry {
    return this.log({
      type: 'effect',
      toolName,
      callId,
      summary: `Effect: ${description}`,
      payload: { description },
    })
  }

  /**
   * Get the full audit log.
   */
  getEntries(): AuditEntry[] {
    return [...this.entries]
  }

  /**
   * Get entries for a specific tool or call.
   */
  query(filters: { toolName?: string; callId?: string; type?: AuditEntryType }): AuditEntry[] {
    return this.entries.filter((e) => {
      if (filters.toolName && e.toolName !== filters.toolName) return false
      if (filters.callId && e.callId !== filters.callId) return false
      if (filters.type && e.type !== filters.type) return false
      return true
    })
  }

  /**
   * Get the last N entries.
   */
  tail(n = 20): AuditEntry[] {
    return this.entries.slice(-n)
  }

  /**
   * Render the audit trail as a compact text representation.
   */
  render(): string {
    return this.entries
      .map((e) => `[${new Date(e.timestamp).toISOString()}] ${e.type.toUpperCase().padEnd(10)} ${e.summary}`)
      .join('\n')
  }

  clear(): void {
    this.entries = []
  }

  onEntry(listener: AuditListener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  private emit(entry: AuditEntry): void {
    for (const listener of this.listeners) {
      listener(entry)
    }
  }
}

export const toolAudit = new ToolAudit()
