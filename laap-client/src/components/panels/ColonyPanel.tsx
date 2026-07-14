/**
 * ColonyPanel：展示 Agent 网格、协作图与团队状态摘要。
 *
 * 使用 GlassPanel 包装，包含：
 * - Agent 网格：头像、名称、状态圆点、资源进度条
 * - SVG 协作图：节点 + 流动边 + 最近消息摘要
 * - 团队状态摘要：在线 / 忙碌 / 离线计数
 */

import { useMemo } from 'react'
import { GlassPanel } from '../glass/GlassPanel'
import { ColonyGraph } from './ColonyGraph'
import type { Agent, AgentStatus, ColonyState } from '../../laap/types'

export interface ColonyPanelProps {
  colony: ColonyState
  className?: string
}

const statusColor: Record<AgentStatus, string> = {
  online: 'bg-laap-secondary shadow-[0_0_6px_#00f5d4]',
  busy: 'bg-laap-warn shadow-[0_0_6px_#f7b801]',
  offline: 'bg-white/30',
}

const statusLabel: Record<AgentStatus, string> = {
  online: '在线',
  busy: '忙碌',
  offline: '离线',
}

const avatarGradients = [
  'from-violet-500 to-fuchsia-500',
  'from-cyan-500 to-blue-500',
  'from-emerald-500 to-teal-500',
  'from-amber-500 to-orange-500',
]

/**
 * Agent 卡片
 */
function AgentCard({ agent, index }: { agent: Agent; index: number }) {
  const initial = agent.name.charAt(0).toUpperCase()
  const resource = Math.min(100, Math.max(0, agent.resource ?? 0))
  const gradient = avatarGradients[index % avatarGradients.length]

  return (
    <div className="flex items-center gap-3 p-2.5 rounded-xl bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.07] transition-colors">
      <div
        className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold text-white bg-gradient-to-br ${gradient} shrink-0`}
      >
        {initial}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-white/90 truncate">{agent.name}</span>
          <span className={`w-2 h-2 rounded-full ${statusColor[agent.status]}`} title={statusLabel[agent.status]} />
        </div>
        <div className="text-[10px] text-white/50 truncate">{agent.role || 'Agent'}</div>
        <div className="mt-1.5 h-1 w-full rounded-full bg-white/10 overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-laap-accent to-laap-secondary transition-all duration-500"
            style={{ width: `${resource}%` }}
          />
        </div>
      </div>
    </div>
  )
}

/**
 * 团队状态摘要
 */
function ColonySummary({ colony }: { colony: ColonyState }) {
  return (
    <div className="flex items-center justify-between text-xs">
      <div className="flex items-center gap-3">
        <span className="flex items-center gap-1.5 text-white/60">
          <span className="w-2 h-2 rounded-full bg-laap-secondary" />
          在线 {colony.onlineCount}
        </span>
        <span className="flex items-center gap-1.5 text-white/60">
          <span className="w-2 h-2 rounded-full bg-laap-warn" />
          忙碌 {colony.busyCount}
        </span>
        <span className="flex items-center gap-1.5 text-white/60">
          <span className="w-2 h-2 rounded-full bg-white/30" />
          离线 {colony.offlineCount}
        </span>
      </div>
      <span className="text-white/40">共 {colony.agents.length} 个 Agent</span>
    </div>
  )
}

export function ColonyPanel({ colony, className = '' }: ColonyPanelProps) {
  const messages = useMemo(() => colony.messages.slice(-4), [colony.messages])

  return (
    <GlassPanel className={`flex flex-col gap-3 p-4 ${className}`} intensity="md" radius="var(--laap-radius-md)">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-white/90">Colony</h2>
        <ColonySummary colony={colony} />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {colony.agents.map((agent, index) => (
          <AgentCard key={agent.id} agent={agent} index={index} />
        ))}
      </div>

      <div className="flex-1 min-h-0 rounded-xl overflow-hidden border border-white/[0.08] bg-white/[0.03]">
        <ColonyGraph agents={colony.agents} edges={colony.edges} messages={messages} />
      </div>

      <div className="text-[10px] text-white/40 truncate">
        最近消息：
        {messages.length === 0 ? '暂无' : messages.map((m) => `${m.from}→${m.to}: ${m.summary}`).join('；')}
      </div>
    </GlassPanel>
  )
}
