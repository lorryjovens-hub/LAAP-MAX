/** CostAPI — Token 成本追踪接口 */
import type { AetherSDK } from './index'

export interface CostSummary {
  date: string
  sessions: number
  tokensIn: number
  tokensOut: number
  totalTokens: number
  cost: number
  llmCalls: number
  toolCalls: number
}

export interface WeeklyCostReport {
  period: string
  totalTokens: number
  totalCost: number
  totalLlmCalls: number
  totalToolCalls: number
  carbonG: number
  daily: CostSummary[]
}

export class CostAPI {
  constructor(private sdk: AetherSDK) {}

  async getDailySummary(date?: string): Promise<CostSummary | null> {
    return this.sdk.request('cost.daily', { date })
  }

  async getWeeklyReport(): Promise<WeeklyCostReport> {
    return this.sdk.request('cost.weekly', {})
  }

  async getAggregate(): Promise<{ total: CostSummary }> {
    return this.sdk.request('cost.aggregate', {})
  }

  onUpdate(callback: (summary: CostSummary) => void): () => void {
    return this.sdk.on('cost.updated', (msg) => callback(msg.payload as CostSummary))
  }
}
