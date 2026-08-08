/** ToolAPI — 工具系统操作接口 */
import type { AetherSDK } from './index'

export interface ToolDefinition {
  id: string
  name: string
  description: string
  category: string
  parameters: Record<string, unknown>
  enabled: boolean
}

export interface ToolCallRequest {
  id: string
  name: string
  arguments: Record<string, unknown>
  status: 'pending' | 'running' | 'success' | 'failure'
  result?: unknown
}

export class ToolAPI {
  constructor(private sdk: AetherSDK) {}

  async list(): Promise<ToolDefinition[]> {
    return this.sdk.request('tool.list', {})
  }

  async get(name: string): Promise<ToolDefinition | null> {
    return this.sdk.request('tool.get', { name })
  }

  async toggle(name: string, enabled: boolean): Promise<boolean> {
    return this.sdk.request('tool.toggle', { name, enabled })
  }

  async execute(name: string, args: Record<string, unknown>): Promise<ToolCallRequest> {
    return this.sdk.request('tool.execute', { name, arguments: args })
  }

  onCall(callback: (call: ToolCallRequest) => void): () => void {
    return this.sdk.on('tool.call', (msg) => callback(msg.payload as ToolCallRequest))
  }

  onResult(callback: (call: ToolCallRequest) => void): () => void {
    return this.sdk.on('tool.result', (msg) => callback(msg.payload as ToolCallRequest))
  }
}
