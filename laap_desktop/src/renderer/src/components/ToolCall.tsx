import React from 'react'
import type { Message } from '../laap_api'

interface ToolCallEvent {
  name: string
  args?: string
  status: 'running' | 'complete' | 'error'
  result?: string
  duration?: number
}

interface Props {
  message: Message
  isStreaming: boolean
}

const COLORS = {
  toolBg: 'rgba(245,158,11,0.08)',
  toolBorder: 'rgba(245,158,11,0.2)',
  toolRunning: '#f59e0b',
  toolDone: '#00d4aa',
  toolError: '#ff6b6b',
}

const ToolCallView: React.FC<Props> = ({ message, isStreaming }) => {
  // Parse tool calls from message content
  // Tool calls are formatted as: [TOOL_CALL] name(args) -> result
  const toolCalls: ToolCallEvent[] = React.useMemo(() => {
    const events: ToolCallEvent[] = []
    if (!message.content) return events

    const lines = message.content.split('\n')
    for (const line of lines) {
      const tcMatch = line.match(/\[TOOL_CALL\]\s*(\w+)\(([^)]*)\)/)
      const trMatch = line.match(/\[TOOL_RESULT\]\s*(.+)/)
      const teMatch = line.match(/\[TOOL_ERROR\]\s*(.+)/)

      if (tcMatch) {
        events.push({
          name: tcMatch[1],
          args: tcMatch[2],
          status: 'running',
        })
      } else if (trMatch && events.length > 0) {
        events[events.length - 1].status = 'complete'
        events[events.length - 1].result = trMatch[1].slice(0, 100)
      } else if (teMatch && events.length > 0) {
        events[events.length - 1].status = 'error'
        events[events.length - 1].result = teMatch[1].slice(0, 100)
      }
    }
    return events
  }, [message.content])

  if (toolCalls.length === 0) return null

  return (
    <div style={{ marginBottom: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
      {toolCalls.map((tc, i) => (
        <div
          key={i}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '6px 10px',
            borderRadius: 6,
            backgroundColor: COLORS.toolBg,
            border: `1px solid ${COLORS.toolBorder}`,
            fontSize: 12,
            animation: 'fadeIn 0.2s ease',
          }}
        >
          {/* Status indicator */}
          <div
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              backgroundColor:
                tc.status === 'running' ? COLORS.toolRunning :
                tc.status === 'complete' ? COLORS.toolDone :
                COLORS.toolError,
              animation: tc.status === 'running' ? 'pulse 1s ease infinite' : 'none',
              flexShrink: 0,
            }}
          />

          {/* Tool name */}
          <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: 12 }}>
            {tc.name}
          </span>

          {/* Args if present */}
          {tc.args && (
            <span style={{ color: 'var(--text-muted)', fontSize: 11, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              ({tc.args.slice(0, 40)})
            </span>
          )}

          {/* Status label */}
          <span style={{
            marginLeft: 'auto',
            fontSize: 11,
            color:
              tc.status === 'running' ? COLORS.toolRunning :
              tc.status === 'complete' ? COLORS.toolDone :
              COLORS.toolError,
            flexShrink: 0,
          }}>
            {tc.status === 'running' ? 'running...' :
             tc.status === 'complete' ? 'done' : 'error'}
          </span>
        </div>
      ))}
    </div>
  )
}

export default ToolCallView
