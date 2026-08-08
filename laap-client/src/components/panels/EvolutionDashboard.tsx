/**
 * EvolutionDashboard — 自进化仪表盘
 *
 * 三块核心指标:
 * 1. RSI 提案列表 — MetaAgent 发现了什么、建议了什么
 * 2. Replay 趋势 — benchmark 得分变化、回归检测
 * 3. 成本曲线 — token 消耗、工具调用、成本趋势
 *
 * 全部使用内联 SVG 图表（Sparkline / MiniBarChart），零额外依赖。
 */

import { useEffect, useState, useCallback } from 'react'
import { GlassPanel } from '../glass/GlassPanel'
import { Sparkline, MiniBarChart, TrendIndicator } from '../charts'
import {
  BrainCircuit,
  AlertTriangle,
  DollarSign,
  TrendingUp,
  RotateCw,
  FileText,
  CheckCircle2,
  XCircle,
  Lightbulb,
} from 'lucide-react'
import { useAetherSDK } from '../../hooks/useAetherSDK'
import type { ReplayReport } from '../../laap/sdk/replay'
import type { WeeklyCostReport } from '../../laap/sdk/cost'

export interface EvolutionDashboardProps {
  className?: string
}

type DashboardTab = 'replay' | 'proposals' | 'cost'

/**
 * 格式化数字
 */
function fmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return n.toFixed(0)
}

/**
 * 汇总卡片
 */
function SummaryCard({
  icon,
  label,
  value,
  sub,
  trend,
  color,
}: {
  icon: React.ReactNode
  label: string
  value: string
  sub?: string
  trend?: number
  color: string
}) {
  return (
    <GlassPanel intensity="xs" className="p-3 flex items-center gap-3">
      <div className={`shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${color}`}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[10px] text-white/40">{label}</div>
        <div className="text-sm font-semibold text-white/90 mt-0.5">{value}</div>
        {sub && <div className="text-[10px] text-white/40 mt-0.5">{sub}</div>}
      </div>
      {trend !== undefined && <TrendIndicator value={trend} />}
    </GlassPanel>
  )
}

/**
 * Replay 趋势面板
 */
function ReplayTab({ report }: { report: ReplayReport | null }) {
  if (!report) {
    return <div className="text-center py-8 text-white/30 text-xs">暂无 replay 数据</div>
  }

  // 按类别聚合分数
  const categoryScores: Record<string, number[]> = {}
  for (const r of report.results ?? []) {
    if (!categoryScores[r.category]) categoryScores[r.category] = []
    if (r.score != null) categoryScores[r.category].push(r.score)
  }

  return (
    <div className="space-y-3">
      {/* 汇总 */}
      <div className="grid grid-cols-3 gap-2">
        <SummaryCard
          icon={<CheckCircle2 className="w-4 h-4" />}
          label="改进"
          value={`${report.improvements ?? 0}`}
          color="bg-emerald-500/15 text-emerald-400"
        />
        <SummaryCard
          icon={<AlertTriangle className="w-4 h-4" />}
          label="回归"
          value={`${report.regressions ?? 0}`}
          color="bg-red-500/15 text-red-400"
          trend={-(report.regressions ?? 0)}
        />
        <SummaryCard
          icon={<BrainCircuit className="w-4 h-4" />}
          label="Benchmark"
          value={`${report.totalBenchmarks ?? 0}`}
          color="bg-blue-500/15 text-blue-400"
        />
      </div>

      {/* 各类别趋势 */}
      {Object.entries(categoryScores).map(([cat, scores]) => (
        <GlassPanel key={cat} intensity="xs" className="p-2.5">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-white/50 uppercase">{cat}</span>
            <span className="text-[10px] text-white/40">{scores.length} 项</span>
          </div>
          <Sparkline data={scores} width={240} height={28} showDot />
        </GlassPanel>
      ))}

      {/* Benchmark 详情列表 */}
      <div className="text-[10px] text-white/50 font-medium mt-3 mb-1">详情</div>
      {(report.results ?? []).slice(0, 10).map((r) => (
        <div key={r.id} className="flex items-center justify-between py-1.5 border-b border-white/[0.04] last:border-0">
          <div className="flex items-center gap-2 min-w-0">
            <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
              r.trend === 'up' ? 'bg-emerald-400' : r.trend === 'down' ? 'bg-red-400' : 'bg-white/30'
            }`} />
            <span className="text-xs text-white/70 truncate">{r.id}</span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-xs font-mono text-white/60">{r.score?.toFixed(2) ?? '-'}</span>
            <TrendIndicator value={r.trend === 'up' ? 0.2 : r.trend === 'down' ? -0.2 : 0} />
          </div>
        </div>
      ))}
    </div>
  )
}

/**
 * RSI 提案列表
 */
function ProposalsTab({ sdk }: { sdk: ReturnType<typeof useAetherSDK>['sdk'] }) {
  const [proposals, setProposals] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // 从 replay insights 获取提案数据
    sdk.replay.getInsight().then((insight) => {
      // 模拟提案格式（实际数据从后端拉取）
      const items: any[] = []
      for (const id of insight.declining ?? []) {
        items.push({ id, category: 'regression', status: 'open', description: `${id} 分数下降`, timestamp: Date.now() })
      }
      for (const id of (insight as any).new ?? []) {
        items.push({ id, category: 'new', status: 'pending', description: `${id} 新 benchmark 待评估`, timestamp: Date.now() })
      }
      setProposals(items)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [sdk])

  if (loading) {
    return <div className="flex items-center justify-center py-8"><RotateCw className="w-4 h-4 text-white/40 animate-spin" /></div>
  }

  if (proposals.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-white/30 text-xs gap-2">
        <Lightbulb className="w-8 h-8 opacity-40" />
        <p>暂无活跃提案</p>
      </div>
    )
  }

  const statusColor: Record<string, string> = {
    open: 'bg-amber-500/15 text-amber-400',
    pending: 'bg-blue-500/15 text-blue-400',
    resolved: 'bg-emerald-500/15 text-emerald-400',
    rejected: 'bg-red-500/15 text-red-400',
  }

  return (
    <div className="space-y-1.5">
      <div className="grid grid-cols-3 gap-2 mb-3">
        <SummaryCard
          icon={<AlertTriangle className="w-4 h-4" />}
          label="活跃"
          value={`${proposals.filter((p: any) => p.status === 'open').length}`}
          color="bg-amber-500/15 text-amber-400"
        />
        <SummaryCard
          icon={<CheckCircle2 className="w-4 h-4" />}
          label="已解决"
          value={`${proposals.filter((p: any) => p.status === 'resolved').length}`}
          color="bg-emerald-500/15 text-emerald-400"
        />
        <SummaryCard
          icon={<XCircle className="w-4 h-4" />}
          label="已拒绝"
          value={`${proposals.filter((p: any) => p.status === 'rejected').length}`}
          color="bg-red-500/15 text-red-400"
        />
      </div>

      {proposals.map((p: any) => (
        <GlassPanel key={p.id} intensity="xs" className="p-2.5">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-mono text-white/80">{p.id}</span>
            <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${statusColor[p.status] ?? 'bg-white/[0.06] text-white/40'}`}>
              {p.status}
            </span>
          </div>
          <p className="text-[10px] text-white/50">{p.description}</p>
        </GlassPanel>
      ))}
    </div>
  )
}

/**
 * 成本曲线面板
 */
function CostTab({ report }: { report: WeeklyCostReport | null }) {
  const [localReport, setLocalReport] = useState<WeeklyCostReport | null>(report)

  useEffect(() => {
    if (report) setLocalReport(report)
  }, [report])

  if (!localReport) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-white/30 text-xs gap-2">
        <DollarSign className="w-8 h-8 opacity-40" />
        <p>暂无成本数据</p>
      </div>
    )
  }

  const daily = localReport.daily ?? []
  const tokenData = daily.map((d) => d.totalTokens)
  const costData = daily.map((d) => Math.round(d.cost * 1000)) // convert to millicents for display

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-2">
        <SummaryCard
          icon={<DollarSign className="w-4 h-4" />}
          label="周成本"
          value={`$${localReport.totalCost.toFixed(4)}`}
          color="bg-emerald-500/15 text-emerald-400"
        />
        <SummaryCard
          icon={<FileText className="w-4 h-4" />}
          label="Token"
          value={fmt(localReport.totalTokens)}
          color="bg-blue-500/15 text-blue-400"
        />
        <SummaryCard
          icon={<TrendingUp className="w-4 h-4" />}
          label="调用次数"
          value={`${localReport.totalToolCalls}`}
          sub={`LLM ${localReport.totalLlmCalls} 次`}
          color="bg-purple-500/15 text-purple-400"
        />
      </div>

      {tokenData.length > 0 && (
        <GlassPanel intensity="xs" className="p-2.5">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] text-white/50">Token 消耗趋势</span>
            <span className="text-[10px] text-white/40">{daily.length} 天</span>
          </div>
          <MiniBarChart data={tokenData} width={240} height={36} />
        </GlassPanel>
      )}

      {costData.length > 0 && (
        <GlassPanel intensity="xs" className="p-2.5">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] text-white/50">成本趋势 (m$)</span>
            <span className="text-[10px] text-white/40">累计 ${localReport.totalCost.toFixed(4)}</span>
          </div>
          <MiniBarChart data={costData} width={240} height={36} color="#f59e0b" />
        </GlassPanel>
      )}

      {/* 每日明细 */}
      <div className="text-[10px] text-white/50 font-medium mt-2 mb-1">每日明细</div>
      {daily.map((d) => (
        <div key={d.date} className="flex items-center justify-between py-1.5 border-b border-white/[0.04] text-[10px]">
          <span className="text-white/60">{d.date.slice(5)}</span>
          <div className="flex items-center gap-3 text-white/50">
            <span>{fmt(d.totalTokens)} tok</span>
            <span>${d.cost.toFixed(4)}</span>
            <span>{d.llmCalls}c</span>
          </div>
        </div>
      ))}
    </div>
  )
}

/**
 * 自进化仪表盘主面板
 */
export function EvolutionDashboard({ className = '' }: EvolutionDashboardProps) {
  const { sdk } = useAetherSDK()
  const [tab, setTab] = useState<DashboardTab>('replay')
  const [replayReport, setReplayReport] = useState<ReplayReport | null>(null)
  const [costReport, setCostReport] = useState<WeeklyCostReport | null>(null)
  const [loading, setLoading] = useState(true)

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [replay, cost] = await Promise.all([
        sdk.replay.getLatestReport().catch(() => null),
        sdk.cost.getWeeklyReport().catch(() => null),
      ])
      setReplayReport(replay)
      setCostReport(cost)
    } finally {
      setLoading(false)
    }
  }, [sdk])

  useEffect(() => {
    loadData()
    // 实时监听 replay 报告更新
    const unsub = sdk.replay.onReport((report) => setReplayReport(report))
    return unsub
  }, [sdk, loadData])

  const tabs: { key: DashboardTab; label: string; icon: React.ReactNode }[] = [
    { key: 'replay', label: 'Replay 趋势', icon: <TrendingUp className="w-3.5 h-3.5" /> },
    { key: 'proposals', label: 'RSI 提案', icon: <Lightbulb className="w-3.5 h-3.5" /> },
    { key: 'cost', label: '成本分析', icon: <DollarSign className="w-3.5 h-3.5" /> },
  ]

  return (
    <GlassPanel className={`flex flex-col overflow-hidden ${className}`} intensity="sm" radius="var(--laap-radius-md)">
      {/* Header */}
      <div className="shrink-0 px-4 py-3 border-b border-white/[0.08]">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-medium text-white/90 flex items-center gap-2">
            <BrainCircuit className="w-4 h-4 text-laap-accent" />
            自进化仪表盘
          </h2>
          <button
            type="button"
            onClick={loadData}
            className="p-1 rounded-md hover:bg-white/[0.08] text-white/40 hover:text-white/70 transition-colors"
          >
            <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1.5">
          {tabs.map(({ key, label, icon }) => (
            <button
              key={key}
              type="button"
              onClick={() => setTab(key)}
              className={`flex items-center gap-1 text-[10px] px-2 py-1 rounded-md border transition-colors ${
                tab === key
                  ? 'bg-laap-accent/15 border-laap-accent/30 text-laap-accent'
                  : 'border-white/[0.08] text-white/50 hover:text-white/70'
              }`}
            >
              {icon}
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-h-0 overflow-y-auto p-3">
        {loading && !replayReport && (
          <div className="flex items-center justify-center py-8">
            <RotateCw className="w-4 h-4 text-white/40 animate-spin" />
          </div>
        )}
        {!loading && tab === 'replay' && <ReplayTab report={replayReport} />}
        {tab === 'proposals' && <ProposalsTab sdk={sdk} />}
        {tab === 'cost' && <CostTab report={costReport} />}
      </div>
    </GlassPanel>
  )
}

export default EvolutionDashboard
