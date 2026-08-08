import { useEffect, useRef, useState } from 'react';
import { Send, Bot, User, Loader2, Wrench } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { streamLocalChat, type HistoryMessage, type Tool } from '@/lib/localLlm';
import { buildCodeAgentTools } from '@/lib/codeAgentTools';
import { DEFAULT_APP_SETTINGS } from '@/lib/settings';
import { getLlmConfig } from '@/lib/llmConfig';
import { DEFAULT_PERSONALITY } from '@/lib/personality';
import { getCurrentUser } from '@/lib/userMode';
import type { StreamEvent } from '@/lib/chat';

interface CodeAgentPanelProps {
  projectId: string;
}

interface ChatMsg {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: { name?: string; args?: Record<string, unknown>; result?: unknown }[];
}

export function CodeAgentPanel({ projectId }: CodeAgentPanelProps) {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const historyRef = useRef<HistoryMessage[]>([]);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    const user = await getCurrentUser();
    const cfg = await getLlmConfig(user.id);
    if (!cfg || cfg.providers.length === 0) {
      setError('请先配置 LLM（设置 → LLM 配置）');
      return;
    }

    const userMsg: ChatMsg = { id: `${Date.now()}-u`, role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setError(null);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const tools: Tool[] = buildCodeAgentTools();
      const currentHistory = [...historyRef.current];

      let assistantContent = '';
      const assistantToolCalls: ChatMsg['toolCalls'] = [];

      await streamLocalChat({
        config: cfg,
        history: currentHistory,
        userMessage: text,
        attachments: undefined,
        personality: DEFAULT_PERSONALITY,
        memories: [],
        settings: DEFAULT_APP_SETTINGS,
        tools,
        signal: controller.signal,
        onEvent: (event: StreamEvent) => {
          if (event.type === 'response') {
            assistantContent = String(event.data.content || '');
            setMessages((prev) => {
              const last = prev[prev.length - 1];
              if (last && last.role === 'assistant') {
                return [...prev.slice(0, -1), { ...last, content: assistantContent }];
              }
              return [...prev, { id: `${Date.now()}-a`, role: 'assistant', content: assistantContent, toolCalls: assistantToolCalls }];
            });
          } else if (event.type === 'tool_result') {
            const data = event.data as { name?: string; args?: Record<string, unknown>; result?: unknown };
            assistantToolCalls.push(data);
            setMessages((prev) => {
              const last = prev[prev.length - 1];
              if (last && last.role === 'assistant') {
                return [...prev.slice(0, -1), { ...last, toolCalls: [...(last.toolCalls || []), data] }];
              }
              return prev;
            });
          }
        },
      });

      historyRef.current = [
        ...currentHistory,
        { role: 'user', content: text },
        { role: 'assistant', content: assistantContent },
      ];
    } catch (err) {
      if (err instanceof Error && err.message === 'Aborted') return;
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  }

  return (
    <div className="flex flex-col h-full w-80 border-l border-white/10 bg-laap-bg-secondary/50">
      <div className="px-3 py-2 border-b border-white/10 flex items-center gap-2">
        <Bot size={14} className="text-laap-cyan" />
        <span className="text-xs font-medium text-laap-text-secondary">Code Agent</span>
        <span className="text-[10px] text-laap-text-tertiary ml-auto truncate max-w-[80px]" title={projectId}>
          {projectId}
        </span>
      </div>

      <ScrollArea className="flex-1 px-3 py-2">
        {messages.length === 0 && (
          <div className="text-xs text-laap-text-tertiary leading-relaxed">
            描述你想构建的网页或游戏，例如：
            <br />
            “帮我做一个打砖块游戏，用 canvas 实现。”
            <br />
            Agent 会自动创建文件、安装依赖并启动预览。
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`mb-3 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
            <div className={`inline-flex items-start gap-2 max-w-[95%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`p-1.5 rounded-full ${msg.role === 'user' ? 'bg-laap-cyan/20' : 'bg-laap-gold/20'}`}>
                {msg.role === 'user' ? <User size={12} className="text-laap-cyan" /> : <Bot size={12} className="text-laap-gold" />}
              </div>
              <div className={`text-xs rounded-md px-2.5 py-2 whitespace-pre-wrap ${
                msg.role === 'user' ? 'bg-laap-cyan/10 text-laap-text-primary' : 'bg-white/5 text-laap-text-secondary'
              }`}>
                {msg.content}
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {msg.toolCalls.map((tc, idx) => (
                      <div key={idx} className="flex items-center gap-1 text-[10px] text-laap-gold">
                        <Wrench size={10} />
                        <span className="truncate">{tc.name}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-xs text-laap-text-tertiary">
            <Loader2 size={12} className="animate-spin" />
            Agent 正在思考…
          </div>
        )}
        {error && <div className="text-xs text-laap-rose mt-2">{error}</div>}
        <div ref={bottomRef} />
      </ScrollArea>

      <div className="p-2 border-t border-white/10">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                void handleSend();
              }
            }}
            placeholder="输入需求…"
            className="flex-1 min-h-[60px] max-h-[120px] px-2 py-1.5 text-xs bg-black/30 border border-white/10 rounded-sm focus:outline-none focus:border-laap-cyan/50 text-laap-text-primary resize-y"
          />
          <Button size="sm" className="h-auto px-2" onClick={handleSend} disabled={loading || !input.trim()}>
            <Send size={14} />
          </Button>
        </div>
      </div>
    </div>
  );
}
