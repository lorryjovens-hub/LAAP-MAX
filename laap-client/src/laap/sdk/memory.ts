/** MemoryAPI — 记忆系统操作接口 */
import type { AetherSDK } from './index'

export interface MemoryEntry {
  id: string
  content: string
  type: 'episodic' | 'semantic' | 'procedural'
  timestamp: number
  tags?: string[]
  source?: string
  confidence?: number
}

export interface MemorySearchResult {
  entries: MemoryEntry[]
  total: number
  query: string
}

export class MemoryAPI {
  constructor(private sdk: AetherSDK) {}

  async search(query: string, limit = 20): Promise<MemorySearchResult> {
    return this.sdk.request('memory.search', { query, limit })
  }

  async get(id: string): Promise<MemoryEntry | null> {
    return this.sdk.request('memory.get', { id })
  }

  async recent(count = 10): Promise<MemoryEntry[]> {
    return this.sdk.request('memory.recent', { count })
  }

  async delete(id: string): Promise<boolean> {
    return this.sdk.request('memory.delete', { id })
  }

  onCreated(callback: (entry: MemoryEntry) => void): () => void {
    return this.sdk.on('memory.created', (msg) => callback(msg.payload as MemoryEntry))
  }

  onUpdated(callback: (entry: MemoryEntry) => void): () => void {
    return this.sdk.on('memory.updated', (msg) => callback(msg.payload as MemoryEntry))
  }
}
