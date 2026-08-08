/**
 * ToolRegistryPanel — 工具注册表面板
 *
 * 显示当前系统中所有注册的工具、技能，支持启停切换。
 */

import { useEffect, useState } from 'react'
import { GlassPanel } from '../glass/GlassPanel'
import { Wrench, Power, PowerOff, RotateCw, Search } from 'lucide-react'
import { useAetherSDK } from '../../hooks/useAetherSDK'
import type { ToolDefinition } from '../../laap/sdk/tool'
import type { SkillDefinition } from '../../laap/sdk/skill'

export interface ToolRegistryPanelProps {
  className?: string
}

type Tab = 'tools' | 'skills'

export function ToolRegistryPanel({ className = '' }: ToolRegistryPanelProps) {
  const { sdk } = useAetherSDK()
  const [tab, setTab] = useState<Tab>('tools')
  const [tools, setTools] = useState<ToolDefinition[]>([])
  const [skills, setSkills] = useState<SkillDefinition[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    setLoading(true)
    if (tab === 'tools') {
      sdk.tool.list().then(setTools).catch(() => {}).finally(() => setLoading(false))
    } else {
      sdk.skill.list().then(setSkills).catch(() => {}).finally(() => setLoading(false))
    }
  }, [sdk, tab])

  const toggleTool = async (name: string, enabled: boolean) => {
    await sdk.tool.toggle(name, !enabled)
    setTools((prev) => prev.map((t) => (t.name === name ? { ...t, enabled: !enabled } : t)))
  }

  const toggleSkill = async (name: string, enabled: boolean) => {
    await sdk.skill.toggle(name, !enabled)
    setSkills((prev) => prev.map((s) => (s.name === name ? { ...s, enabled: !enabled } : s)))
  }

  const filteredTools = tools.filter((t) =>
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const filteredSkills = skills.filter((s) =>
    s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <GlassPanel className={`flex flex-col overflow-hidden ${className}`} intensity="sm" radius="var(--laap-radius-md)">
      {/* Header */}
      <div className="shrink-0 px-4 py-3 border-b border-white/[0.08]">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-medium text-white/90 flex items-center gap-2">
            <Wrench className="w-4 h-4 text-laap-accent" />
            工具 & 技能
          </h2>
        </div>

        {/* Search */}
        <div className="relative mb-2">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/40" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索..."
            className="w-full h-8 pl-8 pr-3 text-xs bg-white/[0.06] border border-white/[0.10] rounded-lg
                       text-white/85 placeholder:text-white/30 outline-none
                       focus:border-laap-accent/40 focus:bg-white/[0.08] transition-colors"
          />
        </div>

        {/* Tabs */}
        <div className="flex gap-1.5">
          {(['tools', 'skills'] as const).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTab(t)}
              className={`text-[10px] px-2 py-1 rounded-md border transition-colors ${
                tab === t
                  ? 'bg-laap-accent/15 border-laap-accent/30 text-laap-accent'
                  : 'border-white/[0.08] text-white/50 hover:text-white/70'
              }`}
            >
              {t === 'tools' ? `工具 (${tools.length})` : `技能 (${skills.length})`}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-1.5">
        {loading && (
          <div className="flex items-center justify-center py-8">
            <RotateCw className="w-4 h-4 text-white/40 animate-spin" />
          </div>
        )}

        {!loading && tab === 'tools' && filteredTools.length === 0 && (
          <div className="text-center py-8 text-white/30 text-xs">暂无工具</div>
        )}

        {!loading && tab === 'skills' && filteredSkills.length === 0 && (
          <div className="text-center py-8 text-white/30 text-xs">暂无技能</div>
        )}

        {!loading && tab === 'tools' && filteredTools.map((tool) => (
          <GlassPanel key={tool.id} intensity="xs" className="p-2.5 flex items-center gap-2">
            <button
              type="button"
              onClick={() => toggleTool(tool.name, tool.enabled)}
              className={`shrink-0 p-1 rounded-md transition-colors ${
                tool.enabled ? 'text-emerald-400 hover:text-emerald-300' : 'text-white/30 hover:text-white/50'
              }`}
            >
              {tool.enabled ? <Power className="w-3.5 h-3.5" /> : <PowerOff className="w-3.5 h-3.5" />}
            </button>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-white/85">{tool.name}</span>
                <span className={`text-[9px] px-1 py-0.5 rounded-full ${
                  tool.enabled ? 'bg-emerald-500/15 text-emerald-400' : 'bg-white/[0.06] text-white/40'
                }`}>
                  {tool.enabled ? '启用' : '禁用'}
                </span>
              </div>
              <p className="text-[10px] text-white/40 truncate mt-0.5">{tool.description}</p>
            </div>
          </GlassPanel>
        ))}

        {!loading && tab === 'skills' && filteredSkills.map((skill) => (
          <GlassPanel key={skill.name} intensity="xs" className="p-2.5 flex items-center gap-2">
            <button
              type="button"
              onClick={() => toggleSkill(skill.name, skill.enabled)}
              className={`shrink-0 p-1 rounded-md transition-colors ${
                skill.enabled ? 'text-emerald-400 hover:text-emerald-300' : 'text-white/30 hover:text-white/50'
              }`}
            >
              {skill.enabled ? <Power className="w-3.5 h-3.5" /> : <PowerOff className="w-3.5 h-3.5" />}
            </button>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs text-white/85">{skill.name}</span>
                <span className="text-[9px] px-1 py-0.5 rounded-full bg-white/[0.06] text-white/40">{skill.category}</span>
              </div>
              <p className="text-[10px] text-white/40 truncate mt-0.5">{skill.description}</p>
            </div>
          </GlassPanel>
        ))}
      </div>
    </GlassPanel>
  )
}

export default ToolRegistryPanel
