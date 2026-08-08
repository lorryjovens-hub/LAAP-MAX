/**
 * SocialPanel — 社交面板
 *
 * 飞书/Discord 频道列表 + 消息流。支持频道切换、消息发送。
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import { GlassPanel } from '../glass/GlassPanel'
import {
  MessageSquare, Send,
  MessageCircle, Bell,
} from 'lucide-react'
import { useAetherSDK } from '../../hooks/useAetherSDK'
import type { SocialChannel, SocialMessage } from '../../laap/sdk/social'

export interface SocialPanelProps {
  className?: string
}

const PLATFORM_ICONS: Record<string, string> = {
  feishu: '飞书',
  discord: 'Discord',
  wechat: '微信',
}

const PLATFORM_COLORS: Record<string, string> = {
  feishu: 'text-blue-400',
  discord: 'text-indigo-400',
  wechat: 'text-emerald-400',
}

function formatMsgTime(ts: number): string {
  const d = new Date(ts)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

export function SocialPanel({ className = '' }: SocialPanelProps) {
  const { sdk } = useAetherSDK()
  const [channels, setChannels] = useState<SocialChannel[]>([])
  const [activeChannel, setActiveChannel] = useState<string | null>(null)
  const [messages, setMessages] = useState<SocialMessage[]>([])
  const [inputText, setInputText] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const loadChannels = useCallback(async () => {
    try {
      const list = await sdk.social.listChannels()
      setChannels(list)
      if (list.length > 0 && !activeChannel) setActiveChannel(list[0].id)
    } catch {
      setChannels([])
    }
  }, [sdk, activeChannel])

  const loadMessages = useCallback(async (channelId: string) => {
    try {
      const msgs = await sdk.social.getMessages(channelId)
      setMessages(msgs)
    } catch {
      setMessages([])
    }
  }, [sdk])

  useEffect(() => {
    loadChannels()
  }, [loadChannels])

  useEffect(() => {
    if (activeChannel) {
      loadMessages(activeChannel)
      const unsub = sdk.social.onMessage((msg) => {
        if (msg.channelId === activeChannel) {
          setMessages((prev) => [...prev, msg])
        }
      })
      return unsub
    }
  }, [sdk, activeChannel, loadMessages])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!inputText.trim() || !activeChannel) return
    try {
      await sdk.social.send(activeChannel, inputText.trim())
      setInputText('')
    } catch {
      // ignore
    }
  }

  const activeChannelData = channels.find((c) => c.id === activeChannel)

  return (
    <GlassPanel className={`flex flex-col overflow-hidden ${className}`} intensity="sm" radius="var(--laap-radius-md)">
      <div className="flex flex-1 min-h-0">
        {/* Channel list */}
        <div className="w-28 shrink-0 border-r border-white/[0.06] overflow-y-auto p-1.5 space-y-0.5">
          <div className="text-[9px] text-white/40 font-medium px-2 py-1 uppercase">频道</div>
          {channels.map((ch) => (
            <button
              key={ch.id}
              type="button"
              onClick={() => setActiveChannel(ch.id)}
              className={`w-full text-left px-2 py-1.5 rounded-md text-xs transition-colors ${
                activeChannel === ch.id
                  ? 'bg-laap-accent/15 text-laap-accent'
                  : 'text-white/60 hover:bg-white/[0.04] hover:text-white/80'
              }`}
            >
              <div className="flex items-center gap-1.5">
                <MessageCircle className="w-3 h-3" />
                <span className="truncate">{ch.name}</span>
              </div>
              <div className="flex items-center gap-1 mt-0.5">
                <span className="text-[9px] text-white/40">{ch.platform}</span>
                {ch.unread > 0 && (
                  <span className="ml-auto text-[9px] px-1 rounded-full bg-red-500/20 text-red-400">{ch.unread}</span>
                )}
              </div>
            </button>
          ))}
        </div>

        {/* Message area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Channel header */}
          <div className="shrink-0 px-3 py-2 border-b border-white/[0.06] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell className="w-3.5 h-3.5 text-white/40" />
              <span className="text-xs text-white/70">{activeChannelData?.name ?? '选择频道'}</span>
              {activeChannelData && (
                <span className={`text-[9px] ${PLATFORM_COLORS[activeChannelData.platform] ?? 'text-white/40'}`}>
                  {PLATFORM_ICONS[activeChannelData.platform] ?? activeChannelData.platform}
                </span>
              )}
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-white/30 text-xs gap-2">
                <MessageSquare className="w-8 h-8 opacity-40" />
                <p>暂无消息</p>
              </div>
            )}
            {messages.map((msg) => (
              <div key={msg.id} className="flex gap-2">
                <div className="shrink-0 w-6 h-6 rounded-full bg-white/[0.06] flex items-center justify-center text-[9px] text-white/50">
                  {msg.sender.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-white/70 font-medium">{msg.sender}</span>
                    <span className="text-[9px] text-white/30">{formatMsgTime(msg.timestamp)}</span>
                  </div>
                  <p className="text-xs text-white/80 mt-0.5 whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="shrink-0 px-3 py-2 border-t border-white/[0.06]">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder={`发送到 ${activeChannelData?.name ?? '...'}`}
                disabled={!activeChannel}
                className="flex-1 h-8 px-3 text-xs bg-white/[0.06] border border-white/[0.10] rounded-lg
                           text-white/85 placeholder:text-white/30 outline-none
                           focus:border-laap-accent/40 focus:bg-white/[0.08] transition-colors
                           disabled:opacity-40"
              />
              <button
                type="button"
                onClick={handleSend}
                disabled={!activeChannel || !inputText.trim()}
                className="shrink-0 w-8 h-8 rounded-lg bg-laap-accent/20 border border-laap-accent/30
                           flex items-center justify-center text-laap-accent
                           hover:bg-laap-accent/30 transition-colors disabled:opacity-30"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </GlassPanel>
  )
}

export default SocialPanel
