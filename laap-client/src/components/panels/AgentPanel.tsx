/**
 * AgentPanel — Agent 管理面板
 *
 * 完整的 Colony agent CRUD + 状态管理 + 实时指标。
 * 玻璃风格表格 + 内联操作。
 */

import { useEffect, useState, useCallback } from 'react'
import { GlassPanel } from '../glass/GlassPanel'
import {
  Users, Plus, Power, PowerOff, RotateCw, Search,
  Trash2, Activity, Cpu, Clock, Bug,
} from 'lucide-react'
import { useAetherSDK } from '../../hooks/useAetherSDK'
import type { AgentInfo } from '../../laap/sdk/agent'

export interface AgentPanelProps {
  className?: string
}

const STATUS_COLORS: Record<string, string> = {
  online: 'bg-emerald-500',
  busy: 'bg-amber-500',
  offline: 'bg-white/20',
}

const STATUS_LABELS: Record<string, string> = {
  online: '在线',
  busy: '忙碌',
  offline: '离线',
}

function AgentMetric({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center gap-1.5 text-[10px] text-white/50">
      {icon}
      <span>{label}</span>
      <span className="text-white/70 font-mono">{value}</span>
    </div>
  )
}

export function AgentPanel({ className = '' }: AgentPanelProps) {
  const { sdk } = useAetherSDK()
  const [agents, setAgents] = useState<AgentInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [newRole, setNewRole] = useState('')

  const loadAgents = useCallback(async () => {
    setLoading(true)
    try {
      const list = await sdk.agent.list()
      setAgents(list)
    } catch {
      // fallback to empty
    } finally {
      setLoading(false)
    }
  }, [sdk])

  useEffect(() => {
    loadAgents()
    const unsub = sdk.agent.onUpdate((updated) => setAgents(updated))
    return unsub
  }, [sdk, loadAgents])

  const handleCreate = async () => {
    if (!newName.trim()) return
    try {
      const agent = await sdk.agent.create(newName.trim(), newRole.trim() || '助手')
      setAgents((prev) => [...prev, agent])
      setNewName('')
      setNewRole('')
      setShowCreate(false)
    } catch {
      // ignore
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await sdk.agent.delete(id)
      setAgents((prev) => prev.filter((a) => a.id !== id))
    } catch {
      // ignore
    }
  }

  const handleToggle = async (agent: AgentInfo) => {
    const newStatus = agent.status === 'offline' ? 'online' : 'offline'
    try {
      const updated = await sdk.agent.update(agent.id, { status: newStatus })
      setAgents((prev) => prev.map((a) => (a.id === agent.id ? updated : a)))
    } catch {
      // ignore
    }
  }

  const filtered = agents.filter((a) =>
    a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (a.role?.toLowerCase() ?? '').includes(searchQuery.toLowerCase())
  )

  const onlineCount = agents.filter((a) => a.status === 'online').length
  const busyCount = agents.filter((a) => a.status === 'busy').length

  return (
    <GlassPanel className={`flex flex-col overflow-hidden ${className}`} intensity="sm" radius="var(--laap-radius-md)">
      {/* Header */}
      <div className="shrink-0 px-4 py-3 border-b border-white/[0.08]">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-medium text-white/90 flex items-center gap-2">
            <Users className="w-4 h-4 text-laap-accent" />
            Agent 管理
          </h2>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-1 text-[10px] px-2 py-1 rounded-md
                         bg-laap-accent/15 border border-laap-accent/30 text-laap-accent
                         hover:bg-laap-accent/25 transition-colors"
            >
              <Plus className="w-3 h-3" />
              新建
            </button>
            <button
              type="button"
              onClick={loadAgents}
              className="p-1 rounded-md hover:bg-white/[0.08] text-white/40 hover:text-white/70 transition-colors"
            >
              <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Stats bar */}
        <div className="flex items-center gap-3 mb-2 text-[10px]">
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            在线 {onlineCount}
          </span>
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            忙碌 {busyCount}
          </span>
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-white/20" />
            离线 {agents.length - onlineCount - busyCount}
          </span>
          <span className="text-white/40">总计 {agents.length}</span>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/40" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索 agent..."
            className="w-full h-8 pl-8 pr-3 text-xs bg-white/[0.06] border border-white/[0.10] rounded-lg
                       text-white/85 placeholder:text-white/30 outline-none
                       focus:border-laap-accent/40 focus:bg-white/[0.08] transition-colors"
          />
        </div>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="shrink-0 px-4 py-3 border-b border-white/[0.08] bg-white/[0.02]">
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="名称"
              className="flex-1 h-8 px-3 text-xs bg-white/[0.06] border border-white/[0.10] rounded-lg
                         text-white/85 placeholder:text-white/30 outline-none
                         focus:border-laap-accent/40 transition-colors"
              autoFocus
              onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            />
            <input
              type="text"
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
              placeholder="角色 (可选)"
              className="flex-1 h-8 px-3 text-xs bg-white/[0.06] border border-white/[0.10] rounded-lg
                         text-white/85 placeholder:text-white/30 outline-none
                         focus:border-laap-accent/40 transition-colors"
              onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            />
          </div>
          <div className="flex gap-2">
            <button type="button" onClick={handleCreate}
              className="text-[10px] px-3 py-1 rounded-md bg-laap-accent/20 text-laap-accent hover:bg-laap-accent/30 transition-colors">
              确认创建
            </button>
            <button type="button" onClick={() => setShowCreate(false)}
              className="text-[10px] px-3 py-1 rounded-md text-white/50 hover:text-white/70 transition-colors">
              取消
            </button>
          </div>
        </div>
      )}

      {/* Agent list */}
      <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-2">
        {loading && agents.length === 0 && (
          <div className="flex items-center justify-center py-8">
            <RotateCw className="w-4 h-4 text-white/40 animate-spin" />
          </div>
        )}

        {!loading && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 text-white/30 text-xs gap-2">
            <Users className="w-8 h-8 opacity-40" />
            <p>{searchQuery ? '未匹配的 agent' : '暂无 agent，点击右上角新建'}</p>
          </div>
        )}

        {filtered.map((agent) => (
          <GlassPanel key={agent.id} intensity="xs" className="p-3 group">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3 min-w-0">
                {/* Status dot + avatar placeholder */}
                <div className="shrink-0 relative">
                  <div className="w-8 h-8 rounded-full bg-white/[0.06] border border-white/[0.10] flex items-center justify-center text-xs text-white/60 font-medium">
                    {agent.name.charAt(0).toUpperCase()}
                  </div>
                  <span className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-[#0a0f1c] ${STATUS_COLORS[agent.status] ?? 'bg-white/20'}`} />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-white/90 font-medium">{agent.name}</span>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${
                      agent.status === 'online' ? 'bg-emerald-500/15 text-emerald-400' :
                      agent.status === 'busy' ? 'bg-amber-500/15 text-amber-400' :
                      'bg-white/[0.06] text-white/40'
                    }`}>
                      {STATUS_LABELS[agent.status] ?? agent.status}
                    </span>
                  </div>
                  <span className="text-[10px] text-white/40">{agent.role}</span>
                  {agent.resource != null && (
                    <div className="flex items-center gap-1.5 mt-1">
                      <div className="flex-1 h-1 rounded-full bg-white/[0.08] overflow-hidden max-w-[60px]">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-laap-accent to-purple-400 transition-all"
                          style={{ width: `${agent.resource}%` }}
                        />
                      </div>
                      <span className="text-[9px] text-white/40 font-mono">{agent.resource}%</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  type="button"
                  onClick={() => handleToggle(agent)}
                  className="p-1.5 rounded-md hover:bg-white/[0.08] text-white/40 hover:text-white/70 transition-colors"
                  title={agent.status === 'offline' ? '上线' : '下线'}
                >
                  {agent.status === 'offline' ? <Power className="w-3.5 h-3.5" /> : <PowerOff className="w-3.5 h-3.5" />}
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(agent.id)}
                  className="p-1.5 rounded-md hover:bg-red-500/20 text-white/40 hover:text-red-400 transition-colors"
                  title="删除"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Metrics */}
            {agent.metrics && (
              <div className="flex items-center gap-3 mt-2 pt-2 border-t border-white/[0.04]">
                <AgentMetric icon={<Activity className="w-3 h-3" />} label="任务" value={`${agent.metrics.tasksCompleted}`} />
                <AgentMetric icon={<Clock className="w-3 h-3" />} label="响应" value={`${agent.metrics.avgResponseTime}ms`} />
                <AgentMetric icon={<Bug className="w-3 h-3" />} label="错误" value={`${(agent.metrics.errorRate * 100).toFixed(1)}%`} />
                <AgentMetric icon={<Cpu className="w-3 h-3" />} label="运行" value={`${Math.round(agent.metrics.uptime / 3600)}h`} />
              </div>
            )}
          </GlassPanel>
        ))}
      </div>
    </GlassPanel>
  )
}

export default AgentPanel
