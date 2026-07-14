import React, { useState, useRef, useEffect, useCallback } from 'react'
import { laap, Message } from '../../laap_api'
import Markdown from '../../components/Markdown'
import ToolCallView from '../../components/ToolCall'
import Avatar from '../../components/Avatar'
import { useSessionStore } from '../../useSessionStore'
import { useSettingsStore } from '../../useSettingsStore'

type Domain = 'general' | 'coding' | 'debugging' | 'architecture'
const DOMAINS: Domain[] = ['general', 'coding', 'debugging', 'architecture']

let messageCounter = 0

function generateId(): string {
  messageCounter++
  return `msg_${Date.now()}_${messageCounter}`
}

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [domain, setDomain] = useState<Domain>('general')
  const [loading, setLoading] = useState(false)
  const [streamingMsgId, setStreamingMsgId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [connected, setConnected] = useState(false)
  const [emotion, setEmotion] = useState('neutral')
  const [isSpeaking, setIsSpeaking] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Stores
  const activeSessionId = useSessionStore((s) => s.activeSessionId)
  const updateSessionActivity = useSessionStore((s) => s.updateSessionActivity)
  const settings = useSettingsStore()

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => { scrollToBottom() }, [messages, scrollToBottom])

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 120) + 'px'
    }
  }, [input])

  const handleSend = useCallback(() => {
    const text = input.trim()
    if (!text || loading) return

    const userMsg: Message = {
      id: generateId(),
      role: 'user',
      content: text,
      timestamp: Date.now(),
    }

    const assistantMsgId = generateId()
    const assistantMsg: Message = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
    }

    setMessages((prev) => [...prev, userMsg, assistantMsg])
    setInput('')
    setLoading(true)
    setStreamingMsgId(assistantMsgId)
    setError(null)
    setIsSpeaking(false)

    laap.chat(text, domain, settings.usePSI, {
      onToken: (token: string) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId ? { ...m, content: m.content + token } : m
          )
        )
      },
      onResponse: (fullText: string) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId ? { ...m, content: fullText } : m
          )
        )
        setLoading(false)
        setStreamingMsgId(null)
        updateSessionActivity(activeSessionId || '')

        // Auto TTS
        if (settings.ttsEnabled && fullText.length < 500) {
          laap.tts(fullText)
          setIsSpeaking(true)
          setTimeout(() => setIsSpeaking(false), fullText.length * 50)
        }
      },
      onToolCall: () => {
        setIsSpeaking(false)
      },
      onEmotion: (name: string) => {
        setEmotion(name)
      },
      onError: (err: string) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId ? { ...m, content: `Error: ${err}` } : m
          )
        )
        setError(err)
        setLoading(false)
        setStreamingMsgId(null)
      },
      onConnected: () => {
        setConnected(true)
        setError(null)
      },
      onDisconnected: () => {
        setConnected(false)
      },
    })
  }, [input, loading, domain, settings.usePSI, settings.ttsEnabled, activeSessionId, updateSessionActivity])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend]
  )

  const handleClearChat = useCallback(() => {
    setMessages([])
    setError(null)
    setLoading(false)
    setStreamingMsgId(null)
    laap.disconnect()
  }, [])

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* ── Top bar ── */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '10px 20px',
          borderBottom: '1px solid var(--border)',
          backgroundColor: 'var(--bg-secondary)',
        }}
      >
        {/* Left: Avatar + Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <Avatar size={36} emotion={emotion} isSpeaking={isSpeaking} />

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {/* Domain selector */}
            <select
              value={domain}
              onChange={(e) => setDomain(e.target.value as Domain)}
              disabled={loading}
              style={{
                backgroundColor: 'var(--input-bg)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border)',
                borderRadius: 6,
                padding: '6px 24px 6px 10px',
                fontSize: 12,
                fontWeight: 500,
                outline: 'none',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.5 : 1,
                appearance: 'none',
                backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%238892b0'/%3E%3C/svg%3E")`,
                backgroundRepeat: 'no-repeat',
                backgroundPosition: 'right 8px center',
              }}
            >
              {DOMAINS.map((d) => (
                <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
              ))}
            </select>

            {/* Connection status */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                backgroundColor: connected ? 'var(--online)' : 'var(--offline)',
                transition: 'background-color var(--transition-fast)',
              }} />
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                {connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>

        {/* Right: Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* PSI Toggle */}
          <div
            style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}
            onClick={() => settings.setUsePSI(!settings.usePSI)}
          >
            <div style={{
              width: 32,
              height: 18,
              borderRadius: 10,
              backgroundColor: settings.usePSI ? 'var(--accent)' : 'var(--text-muted)',
              position: 'relative',
              transition: 'background-color var(--transition-fast)',
            }}>
              <div style={{
                width: 14,
                height: 14,
                borderRadius: '50%',
                backgroundColor: '#fff',
                position: 'absolute',
                top: 2,
                left: settings.usePSI ? 16 : 2,
                transition: 'left var(--transition-fast)',
                boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
              }} />
            </div>
            <span style={{
              fontSize: 11,
              fontWeight: 600,
              color: settings.usePSI ? 'var(--accent)' : 'var(--text-muted)',
              transition: 'color var(--transition-fast)',
            }}>
              PSI
            </span>
          </div>

          <button
            onClick={handleClearChat}
            style={{
              backgroundColor: 'transparent',
              border: '1px solid var(--border)',
              borderRadius: 6,
              color: 'var(--text-muted)',
              fontSize: 12,
              padding: '6px 12px',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.borderColor = 'var(--error)'
              e.currentTarget.style.color = 'var(--error)'
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.borderColor = 'var(--border)'
              e.currentTarget.style.color = 'var(--text-muted)'
            }}
          >
            Clear
          </button>
        </div>
      </div>

      {/* ── Messages ── */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px 24px 0',
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
        }}
      >
        {messages.length === 0 && (
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-muted)',
              gap: 16,
            }}
          >
            <Avatar size={80} emotion="neutral" />
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>
                Start a conversation
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                Type a message to talk to the LAAP agent
              </div>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
              animation: 'fadeIn 0.2s ease',
            }}
          >
            <div
              style={{
                maxWidth: '75%',
                padding: '10px 16px',
                borderRadius: msg.role === 'user'
                  ? '14px 14px 4px 14px'
                  : '14px 14px 14px 4px',
                backgroundColor: msg.role === 'user'
                  ? 'var(--user-bubble)'
                  : 'var(--assistant-bubble)',
                border: msg.role === 'assistant' ? '1px solid var(--border)' : 'none',
                color: 'var(--text-primary)',
                fontSize: 14,
                lineHeight: 1.6,
                wordBreak: 'break-word',
              }}
            >
              {/* Tool calls visualization */}
              {msg.role === 'assistant' && (
                <ToolCallView message={msg} isStreaming={msg.id === streamingMsgId} />
              )}

              {/* Content */}
              {msg.role === 'assistant' && msg.content === '' && loading ? (
                <div style={{ display: 'flex', gap: 4, padding: '4px 0' }}>
                  <div className="typing-dot" style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: 'var(--accent)', animation: 'bounce 1.2s ease infinite' }} />
                  <div className="typing-dot" style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: 'var(--accent)', animation: 'bounce 1.2s ease infinite 0.2s' }} />
                  <div className="typing-dot" style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: 'var(--accent)', animation: 'bounce 1.2s ease infinite 0.4s' }} />
                </div>
              ) : msg.role === 'assistant' ? (
                <Markdown content={msg.content} />
              ) : (
                <span style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</span>
              )}

              {/* Timestamp */}
              <div style={{
                fontSize: 10,
                color: 'var(--text-muted)',
                marginTop: 6,
                textAlign: 'right',
              }}>
                {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* ── Input ── */}
      <div
        style={{
          padding: '12px 20px 20px',
          borderTop: '1px solid var(--border)',
          backgroundColor: 'var(--bg-primary)',
        }}
      >
        <div
          style={{
            display: 'flex',
            gap: 10,
            alignItems: 'flex-end',
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid var(--border)',
            borderRadius: 12,
            padding: '8px 8px 8px 16px',
            transition: 'border-color var(--transition-fast)',
          }}
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={loading ? 'Waiting...' : 'Type a message...'}
            disabled={loading}
            rows={1}
            style={{
              flex: 1,
              backgroundColor: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text-primary)',
              fontSize: 14,
              fontFamily: 'inherit',
              resize: 'none',
              maxHeight: 120,
              padding: '6px 0',
              lineHeight: 1.4,
            }}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            style={{
              backgroundColor: loading || !input.trim() ? 'var(--text-muted)' : 'var(--accent)',
              border: 'none',
              borderRadius: 8,
              width: 36,
              height: 36,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
              opacity: loading || !input.trim() ? 0.4 : 1,
              transition: 'all var(--transition-fast)',
              flexShrink: 0,
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>

        {error && (
          <div style={{ marginTop: 8, fontSize: 12, color: 'var(--error)', textAlign: 'center' }}>
            {error}
          </div>
        )}
      </div>

      {/* Animations */}
      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; } 40% { transform: scale(1); opacity: 1; } }
        @keyframes spin { to { transform: rotate(360deg); } }
        .typing-dot { display: inline-block; }
        select option { background-color: var(--bg-secondary); color: var(--text-primary); }
        textarea::placeholder { color: var(--text-muted); }
      `}</style>
    </div>
  )
}

export default Chat
