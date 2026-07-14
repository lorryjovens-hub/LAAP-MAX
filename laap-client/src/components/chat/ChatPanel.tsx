/**
 * ChatPanel：主聊天消息列表
 *
 * 支持 Markdown 渲染、代码块复制、user/assistant 区分、自动滚动与空状态。
 * 消息气泡使用 GlassPanel 包装，流式输出时显示脉冲光标。
 * 用户向上滚动时暂停自动滚动，回到底部后恢复。
 */

import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Copy, Check, User, Bot } from 'lucide-react'
import { GlassPanel } from '../glass/GlassPanel'
import { ToolCallCard } from '../tools/ToolCallCard'
import type { ChatMessage, ToolCall } from '../../laap/types'

export interface ChatPanelProps {
  messages: ChatMessage[]
  isStreaming?: boolean
  currentToolCall?: ToolCall | null
  onRetryToolCall?: (id: string) => void
  className?: string
}

/**
 * 代码块组件：带语言标签与复制按钮
 */
function CodeBlock({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  const [copied, setCopied] = useState(false)
  const code = String(children).replace(/\n$/, '')
  const match = /language-(\w+)/.exec(className || '')
  const lang = match?.[1] || 'text'

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // 忽略复制失败
    }
  }

  return (
    <div className="relative group my-2 rounded-xl overflow-hidden bg-[#0d1117] border border-white/[0.08]">
      <div className="flex items-center justify-between px-3 py-1.5 bg-white/[0.04]">
        <span className="text-[10px] font-mono text-white/50">{lang}</span>
        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1 text-[10px] text-white/50 hover:text-white/80 transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3" />
              已复制
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              复制
            </>
          )}
        </button>
      </div>
      <pre className="px-3 py-2 overflow-x-auto">
        <code className="text-xs font-mono text-white/85">{children}</code>
      </pre>
    </div>
  )
}

/**
 * 行内代码
 */
function InlineCode({ children }: { children: React.ReactNode }) {
  return (
    <code className="px-1.5 py-0.5 rounded-md bg-white/[0.08] text-xs font-mono text-white/85">
      {children}
    </code>
  )
}

/**
 * 格式化时间戳
 */
function formatTime(timestamp: number): string {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * 单条消息气泡
 */
function MessageBubble({
  message,
  isLast,
  isStreaming,
  onRetryToolCall,
}: {
  message: ChatMessage
  isLast: boolean
  isStreaming: boolean
  onRetryToolCall?: (id: string) => void
}) {
  const isUser = message.role === 'user'
  const isAssistant = message.role === 'assistant'

  return (
    <div
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      {/* 头像 */}
      <div
        className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center border ${
          isUser
            ? 'bg-laap-accent/15 border-laap-accent/30 text-laap-accent'
            : 'bg-white/[0.05] border-white/[0.10] text-white/70'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      <div className={`flex flex-col max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
        <span className="text-[10px] text-white/40 mb-1">
          {isUser ? '你' : '助手'} · {formatTime(message.timestamp)}
        </span>

        <GlassPanel
          className={`px-4 py-3 ${isUser ? 'bg-laap-accent/10' : ''}`}
          intensity="sm"
          radius="var(--laap-radius-md)"
        >
          {isAssistant ? (
            <div className="laap-markdown text-sm text-white/85 leading-relaxed">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ className, children }) {
                    const match = /language-(\w+)/.exec(className || '')
                    return match ? (
                      <CodeBlock className={className}>{children}</CodeBlock>
                    ) : (
                      <InlineCode>{children}</InlineCode>
                    )
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
              {isLast && isStreaming && (
                <span className="inline-block w-2 h-4 ml-0.5 bg-laap-accent/80 animate-pulse" />
              )}
            </div>
          ) : (
            <p className="text-sm text-white/90 whitespace-pre-wrap">{message.content}</p>
          )}

          {message.toolCall && (
            <div className="mt-3">
              <ToolCallCard
                toolCall={message.toolCall}
                onRetry={onRetryToolCall}
              />
            </div>
          )}
        </GlassPanel>
      </div>
    </div>
  )
}

export function ChatPanel({
  messages,
  isStreaming = false,
  currentToolCall,
  onRetryToolCall,
  className = '',
}: ChatPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [userScrolled, setUserScrolled] = useState(false)

  /**
   * 监听滚动：当用户离开底部时暂停自动滚动
   */
  const handleScroll = () => {
    const el = scrollRef.current
    if (!el) return
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40
    setUserScrolled(!nearBottom)
  }

  /**
   * 消息变化时自动滚动到底部（用户未手动上滑）
   */
  useEffect(() => {
    if (userScrolled) return
    const el = scrollRef.current
    if (!el) return
    el.scrollTop = el.scrollHeight
  }, [messages, currentToolCall, userScrolled])

  const hasCurrentToolCall =
    currentToolCall &&
    !messages.some((msg) => msg.toolCall?.id === currentToolCall.id)

  return (
    <GlassPanel
      className={`flex flex-col overflow-hidden ${className}`}
      intensity="sm"
      radius="var(--laap-radius-md)"
    >
      <div className="shrink-0 px-4 py-3 border-b border-white/[0.08]">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-white/90">对话</h2>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/[0.08] text-white/50 font-mono">
            {messages.length}
          </span>
        </div>
      </div>

      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 min-h-0 overflow-y-auto p-4 space-y-5"
      >
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-white/30 text-sm gap-3">
            <Bot className="w-10 h-10 opacity-40" />
            <p>开始与 LAAP 对话</p>
            <p className="text-xs">输入消息后，将收到模拟流式回复</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <MessageBubble
              key={message.id}
              message={message}
              isLast={index === messages.length - 1}
              isStreaming={isStreaming}
              onRetryToolCall={onRetryToolCall}
            />
          ))
        )}

        {hasCurrentToolCall && (
          <div className="flex gap-3">
            <div className="shrink-0 w-8 h-8 rounded-full flex items-center justify-center border bg-white/[0.05] border-white/[0.10] text-white/70">
              <Bot className="w-4 h-4" />
            </div>
            <div className="flex-1">
              <ToolCallCard
                toolCall={currentToolCall}
                onRetry={onRetryToolCall}
              />
            </div>
          </div>
        )}
      </div>
    </GlassPanel>
  )
}
