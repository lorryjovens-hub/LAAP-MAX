/** ReplayAPI — Replay/Forgetting 检测接口 */
import type { AetherSDK } from './index'

export interface BenchmarkResult {
  id: string
  category: string
  description: string
  score: number | null
  trend: 'up' | 'down' | 'stable' | 'new'
  weight: number
}

export interface ReplayReport {
  timestamp: string
  totalBenchmarks: number
  regressions: number
  improvements: number
  results: BenchmarkResult[]
}

export interface InsightSummary {
  status: string
  stable: string[]
  declining: string[]
  improving: string[]
  new: string[]
}

export class ReplayAPI {
  constructor(private sdk: AetherSDK) {}

  async getLatestReport(): Promise<ReplayReport | null> {
    return this.sdk.request('replay.latest_report', {})
  }

  async getInsight(): Promise<InsightSummary> {
    return this.sdk.request('replay.insight', {})
  }

  async listReports(limit = 10): Promise<ReplayReport[]> {
    return this.sdk.request('replay.list_reports', { limit })
  }

  onReport(callback: (report: ReplayReport) => void): () => void {
    return this.sdk.on('replay.report', (msg) => callback(msg.payload as ReplayReport))
  }

  onRegression(callback: (alert: { benchmark: string; delta: number }) => void): () => void {
    return this.sdk.on('replay.regression', (msg) => callback(msg.payload as { benchmark: string; delta: number }))
  }
}
