/**
 * MemoryPanel — 记忆浏览器面板
 *
 * 功能:
 * - 搜索记忆条目
 * - 按类型筛选 (episodic/semantic/procedural)
 * - 条目详情查看
 * - 实时监听新记忆
 *
 * 玻璃风格的搜索框 + 结果列表。
 */

import { useEffect, useState, useCallback } from 'react'
import { GlassPanel } from '../glass/GlassPanel'
import { Search, Brain, Clock, Tag, Trash2 } from 'lucide-react'
import { useAetherSDK } from '../../hooks/useAetherSDK'
import type { MemoryEntry } from '../../laap/sdk/memory'

export interface MemoryPanelProps {
  className?: string
}

type MemoryFilter = 'all' | 'episodic' | 'semantic' | 'procedural'

const FILTER_LABELS: Record<MemoryFilter, string> = {
  all: '全部',
  episodic: '情景',
  semantic: '语义',
  procedural: '程序',
}

/**
 * 格式化时间戳为可读字符串
 */
function formatTime(ts: number): string {
  const d = new Date(ts)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

/**
 * 记忆条目卡片
 */
function MemoryCard({ entry, onDelete }: { entry: MemoryEntry; onDelete?: (id: string) => void }) {
  const typeColors: Record<string, string> = {
    episodic: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    semantic: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    procedural: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  }

  return (
    <GlassPanel intensity="xs" className="p-3 group hover:bg-white/[0.06] transition-colors cursor-pointer">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-[10px] px-1.5 py-0.5 rounded-full border ${typeColors[entry.type] ?? 'text-white/50'}`}>
              {FILTER_LABELS[entry.type as MemoryFilter] ?? entry.type}
            </span>
            {entry.confidence != null && (
              <span className="text-[10px] text-white/40">
                置信度 {Math.round(entry.confidence * 100)}%
              </span>
            )}
          </div>
          <p className="text-sm text-white/85 line-clamp-3 leading-relaxed">{entry.content}</p>
          <div className="flex items-center gap-3 mt-2 text-[10px] text-white/40">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatTime(entry.timestamp)}
            </span>
            {entry.tags && entry.tags.length > 0 && (
              <span className="flex items-center gap-1">
                <Tag className="w-3 h-3" />
                {entry.tags.slice(0, 3).join(', ')}
              </span>
            )}
          </div>
        </div>
        {onDelete && (
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); onDelete(entry.id) }}
            className="shrink-0 p-1 rounded-md opacity-0 group-hover:opacity-100 hover:bg-red-500/20 text-white/40 hover:text-red-400 transition-all"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </GlassPanel>
  )
}

/**
 * 记忆浏览器主面板
 */
export function MemoryPanel({ className = '' }: MemoryPanelProps) {
  const { sdk } = useAetherSDK()
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<MemoryFilter>('all')
  const [entries, setEntries] = useState<MemoryEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = useCallback(async (q: string) => {
    setLoading(true)
    setError(null)
    try {
      const result = await sdk.memory.search(q || '', 20)
      const filtered = filter === 'all'
        ? result.entries
        : result.entries.filter((e) => e.type === filter)
      setEntries(filtered)
    } catch (err) {
      setError(err instanceof Error ? err.message : '搜索失败')
      setEntries([])
    } finally {
      setLoading(false)
    }
  }, [sdk, filter])

  // 初始化：加载最近记忆
  useEffect(() => {
    if (!query) {
      sdk.memory.recent(10).then(setEntries).catch(() => {})
    }
  }, [sdk, query, filter])

  // 实时监听新记忆
  useEffect(() => {
    const unsub = sdk.memory.onCreated((entry) => {
      setEntries((prev) => [entry, ...prev].slice(0, 50))
    })
    return unsub
  }, [sdk])

  const handleSearch = () => search(query)
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch()
  }

  const handleDelete = async (id: string) => {
    try {
      await sdk.memory.delete(id)
      setEntries((prev) => prev.filter((e) => e.id !== id))
    } catch {
      // ignore
    }
  }

  return (
    <GlassPanel className={`flex flex-col overflow-hidden ${className}`} intensity="sm" radius="var(--laap-radius-md)">
      {/* Header */}
      <div className="shrink-0 px-4 py-3 border-b border-white/[0.08]">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-medium text-white/90 flex items-center gap-2">
            <Brain className="w-4 h-4 text-laap-accent" />
            记忆浏览器
          </h2>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/[0.08] text-white/50 font-mono">
            {entries.length}
          </span>
        </div>

        {/* Search bar */}
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/40" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="搜索记忆..."
            className="w-full h-8 pl-8 pr-3 text-xs bg-white/[0.06] border border-white/[0.10] rounded-lg
                       text-white/85 placeholder:text-white/30 outline-none
                       focus:border-laap-accent/40 focus:bg-white/[0.08] transition-colors"
          />
        </div>

        {/* Filter chips */}
        <div className="flex gap-1.5 mt-2">
          {(Object.entries(FILTER_LABELS) as [MemoryFilter, string][]).map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => setFilter(key)}
              className={`text-[10px] px-2 py-1 rounded-md border transition-colors ${
                filter === key
                  ? 'bg-laap-accent/15 border-laap-accent/30 text-laap-accent'
                  : 'border-white/[0.08] text-white/50 hover:text-white/70 hover:bg-white/[0.04]'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-2">
        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="w-4 h-4 border-2 border-laap-accent/30 border-t-laap-accent rounded-full animate-spin" />
          </div>
        )}

        {error && (
          <div className="text-xs text-red-400/80 bg-red-500/10 rounded-lg p-3 text-center">
            {error}
          </div>
        )}

        {!loading && !error && entries.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 text-white/30 text-xs gap-2">
            <Brain className="w-8 h-8 opacity-40" />
            <p>{query ? '未找到匹配的记忆' : '暂无记忆'}</p>
          </div>
        )}

        {!loading && entries.map((entry) => (
          <MemoryCard key={entry.id} entry={entry} onDelete={handleDelete} />
        ))}
      </div>
    </GlassPanel>
  )
}

export default MemoryPanel
