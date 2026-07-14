/**
 * ToolCallList：当前会话中的工具调用列表
 */

import { ToolCallCard } from './ToolCallCard'
import type { ChatMessage } from '../../laap/types'

export interface ToolCallListProps {
  messages: ChatMessage[]
  onRetry?: (id: string) => void
  className?: string
}

export function ToolCallList({ messages, onRetry, className = '' }: ToolCallListProps) {
  const toolCalls = messages
    .map((msg) => msg.toolCall)
    .filter((tc): tc is NonNullable<typeof tc> => tc !== undefined)

  const unique = Array.from(new Map(toolCalls.map((tc) => [tc.id, tc])).values())

  if (unique.length === 0) {
    return (
      <div className={`text-xs text-white/30 ${className}`}>暂无工具调用</div>
    )
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {unique.map((tc) => (
        <ToolCallCard key={tc.id} toolCall={tc} onRetry={onRetry} />
      ))}
    </div>
  )
}
