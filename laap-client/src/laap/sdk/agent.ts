/** AgentAPI — Agent 管理系统操作接口 */
import type { AetherSDK } from './index'
import type { Agent } from '../types'

export interface AgentInfo extends Agent {
  metrics?: AgentMetrics
}

export interface AgentMetrics {
  tasksCompleted: number
  avgResponseTime: number
  errorRate: number
  uptime: number
}

export class AgentAPI {
  constructor(private sdk: AetherSDK) {}

  async list(): Promise<AgentInfo[]> {
    return this.sdk.request('agent.list', {})
  }

  async get(id: string): Promise<AgentInfo | null> {
    return this.sdk.request('agent.get', { id })
  }

  async create(name: string, role: string): Promise<AgentInfo> {
    return this.sdk.request('agent.create', { name, role })
  }

  async update(id: string, updates: Partial<AgentInfo>): Promise<AgentInfo> {
    return this.sdk.request('agent.update', { id, ...updates })
  }

  async delete(id: string): Promise<boolean> {
    return this.sdk.request('agent.delete', { id })
  }

  async assignTask(agentId: string, task: string): Promise<boolean> {
    return this.sdk.request('agent.assign_task', { agentId, task })
  }

  onUpdate(callback: (agents: AgentInfo[]) => void): () => void {
    return this.sdk.on('colony.agent', (msg) => callback((msg.payload as { agents?: AgentInfo[] }).agents ?? []))
  }
}
