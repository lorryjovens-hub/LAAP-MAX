/**
 * ToolCallCard：工具调用执行卡片
 *
 * 展示工具名、参数摘要、执行状态，支持展开查看完整参数/结果、复制结果与重新执行。
 */

import { useState } from 'react'
import {
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  RefreshCw,
  Clock,
  Loader2,
  CheckCircle2,
  XCircle,
  ShieldAlert,
  Play,
} from 'lucide-react'
import type { ToolCall } from '../../laap/types'

export interface ToolCallCardProps {
  toolCall: ToolCall
  onRetry?: (id: string) => void
  onConfirm?: (id: string) => void
  onReject?: (id: string) => void
  confirmationReason?: string
  className?: string
}

const STATUS_CONFIG = {
  pending: {
    label: '待执行',
    color: 'border-white/20 text-white/60',
    icon: Clock,
  },
  running: {
    label: '执行中',
    color: 'border-blue-400 text-blue-400',
    icon: Loader2,
  },
  success: {
    label: '成功',
    color: 'border-green-400 text-green-400',
    icon: CheckCircle2,
  },
  error: {
    label: '失败',
    color: 'border-red-400 text-red-400',
    icon: XCircle,
  },
}

function summarizeArgs(args: Record<string, unknown>): string {
  const entries = Object.entries(args)
  if (entries.length === 0) return '无参数'
  const first = entries[0]
  const value = String(first[1]).slice(0, 40)
  return `${first[0]}=${value}${entries.length > 1 ? ` 等 ${entries.length} 项` : ''}`
}

export function ToolCallCard({ toolCall, onRetry, onConfirm, onReject, confirmationReason, className = '' }: ToolCallCardProps) {
  const [expanded, setExpanded] = useState(false)
  const [copied, setCopied] = useState(false)
  const status = STATUS_CONFIG[toolCall.status]
  const StatusIcon = status.icon
  const needsConfirmation = toolCall.status === 'pending' && Boolean(onConfirm || onReject)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(toolCall.result ?? {}, null, 2))
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // 忽略复制失败
    }
  }

  const handleRetry = () => {
    onRetry?.(toolCall.id)
  }

  const handleConfirm = () => {
    onConfirm?.(toolCall.id)
  }

  const handleReject = () => {
    onReject?.(toolCall.id)
  }

  return (
    <div
      className={`rounded-xl border bg-white/[0.03] overflow-hidden ${status.color} ${needsConfirmation ? 'border-amber-400/40' : ''} ${className}`}
    >
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-3 py-2 hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-center gap-2 min-w-0">
          <StatusIcon
            className={`w-4 h-4 shrink-0 ${toolCall.status === 'running' ? 'animate-spin' : ''}`}
          />
          <span className="text-xs font-medium text-white/90 truncate">{toolCall.name}</span>
          <span className="text-[10px] text-white/40 truncate hidden sm:inline">
            {summarizeArgs(toolCall.arguments)}
          </span>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <span className="text-[10px] px-1.5 py-0.5 rounded-full border border-current/30 bg-current/5">
            {status.label}
          </span>
          {expanded ? (
            <ChevronUp className="w-3.5 h-3.5 text-white/50" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5 text-white/50" />
          )}
        </div>
      </button>

      {expanded && (
        <div className="px-3 pb-3 pt-1 border-t border-white/[0.06]">
          <div className="mt-2">
            <div className="text-[10px] text-white/40 mb-1">参数</div>
            <pre className="text-[10px] font-mono text-white/70 bg-black/20 rounded-lg p-2 overflow-x-auto">
              {JSON.stringify(toolCall.arguments, null, 2)}
            </pre>
          </div>

          {'result' in toolCall && toolCall.result !== undefined && (
            <div className="mt-2">
              <div className="text-[10px] text-white/40 mb-1">结果</div>
              <pre className="text-[10px] font-mono text-white/70 bg-black/20 rounded-lg p-2 overflow-x-auto">
                {JSON.stringify(toolCall.result, null, 2)}
              </pre>
            </div>
          )}

          {needsConfirmation && (
            <div className="mt-2 rounded-lg bg-amber-500/10 border border-amber-400/20 p-2">
              <div className="flex items-start gap-1.5 text-[10px] text-amber-200/90 mb-2">
                <ShieldAlert className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                <span>{confirmationReason || '该工具调用需要您的确认才能继续执行。'}</span>
              </div>
              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={handleReject}
                  className="flex items-center gap-1 px-2 py-1 rounded-lg bg-white/[0.06] hover:bg-white/[0.10] text-[10px] text-white/70 transition-colors"
                >
                  <XCircle className="w-3 h-3" />
                  拒绝
                </button>
                <button
                  type="button"
                  onClick={handleConfirm}
                  className="flex items-center gap-1 px-2 py-1 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-[10px] text-amber-200 transition-colors"
                >
                  <Play className="w-3 h-3" />
                  确认执行
                </button>
              </div>
            </div>
          )}

          <div className="flex items-center justify-end gap-2 mt-2">
            {'result' in toolCall && toolCall.result !== undefined && (
              <button
                type="button"
                onClick={handleCopy}
                className="flex items-center gap-1 px-2 py-1 rounded-lg bg-white/[0.06] hover:bg-white/[0.10] text-[10px] text-white/70 transition-colors"
              >
                {copied ? (
                  <>
                    <Check className="w-3 h-3" />
                    已复制
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3" />
                    复制结果
                  </>
                )}
              </button>
            )}
            <button
              type="button"
              onClick={handleRetry}
              disabled={toolCall.status === 'running' || needsConfirmation}
              className="flex items-center gap-1 px-2 py-1 rounded-lg bg-white/[0.06] hover:bg-white/[0.10] disabled:opacity-40 text-[10px] text-white/70 transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              重新执行
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
