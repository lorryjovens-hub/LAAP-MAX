import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router';
import { Bot, User, ArrowLeft, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { ScrollArea } from '@/components/ui/scroll-area';
import { decodeSharedChat, type SharedChat } from '@/lib/share';
import type { ChatMessage } from '@/lib/chat';

export default function SharePage() {
  const { token } = useParams<{ token: string }>();
  const [shared, setShared] = useState<SharedChat | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) {
      setError('分享链接无效');
      return;
    }
    const decoded = decodeSharedChat(token);
    if (!decoded) {
      setError('无法解析分享内容，链接可能已损坏或过期。');
      return;
    }
    setShared(decoded);
  }, [token]);

  return (
    <div className="min-h-screen bg-laap-bg-primary text-laap-text-primary">
      <header className="h-16 border-b border-laap-border bg-laap-bg-primary/90 backdrop-blur-md flex items-center justify-between px-4 sm:px-6">
        <Link
          to="/"
          className="flex items-center gap-2 text-sm text-laap-text-secondary hover:text-white transition-colors"
        >
          <ArrowLeft size={16} />
          返回 LAAP
        </Link>
        <div className="font-display text-white tracking-wide">LAAP Studio</div>
        <Link
          to="/studio"
          className="text-sm text-laap-gold hover:text-laap-gold-light transition-colors"
        >
          开始对话
        </Link>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8">
        {error ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <AlertCircle size={48} className="text-laap-rose mb-4" />
            <h1 className="text-xl text-white mb-2">分享内容无法打开</h1>
            <p className="text-sm text-laap-text-secondary">{error}</p>
          </div>
        ) : !shared ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-10 h-10 border-2 border-laap-gold border-t-transparent rounded-full animate-spin mb-4" />
            <p className="text-sm text-laap-text-secondary">正在加载分享内容…</p>
          </div>
        ) : (
          <>
            <div className="mb-6">
              <h1 className="text-xl font-display text-white mb-1">{shared.title}</h1>
              <p className="text-xs text-laap-text-tertiary">
                分享于 {new Date(shared.exportedAt).toLocaleString('zh-CN')} · {shared.messages.length} 条消息
              </p>
            </div>

            <ScrollArea className="h-[calc(100vh-200px)] rounded-sm border border-laap-border bg-laap-bg-secondary/30 p-4">
              <div className="space-y-6">
                {shared.messages.map((message) => (
                  <SharedMessageBubble key={message.id} message={message} />
                ))}
              </div>
            </ScrollArea>
          </>
        )}
      </main>
    </div>
  );
}

function SharedMessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex gap-3 max-w-[90%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
            isUser
              ? 'bg-laap-bg-tertiary border border-laap-border'
              : 'bg-laap-gold/10 border border-laap-gold/30'
          }`}
        >
          {isUser ? <User size={16} className="text-laap-text-secondary" /> : <Bot size={16} className="text-laap-gold" />}
        </div>

        <div className={`space-y-2 ${isUser ? 'items-end' : 'items-start'}`}>
          <div
            className={`px-4 py-3 text-sm leading-relaxed rounded-sm ${
              isUser
                ? 'bg-laap-gold/10 border border-laap-gold/30 text-white'
                : 'bg-laap-bg-secondary/50 border border-laap-border text-laap-text-primary'
            }`}
          >
            {isUser ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : (
              <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                  {message.content || ' '}
                </ReactMarkdown>
              </div>
            )}
          </div>

          {message.attachments && message.attachments.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {message.attachments.map((att) => {
                const dataUrl = att.type === 'image' ? `data:${att.mimeType};base64,${att.content}` : undefined;
                return dataUrl ? (
                  <a key={att.id} href={dataUrl} target="_blank" rel="noreferrer">
                    <img
                      src={dataUrl}
                      alt={att.name}
                      className="max-h-32 max-w-[200px] rounded-sm border border-laap-border object-cover hover:border-laap-gold/50 transition-colors"
                    />
                  </a>
                ) : (
                  <div
                    key={att.id}
                    className="flex items-center gap-1.5 px-2 py-1 text-xs bg-laap-bg-tertiary/50 border border-laap-border rounded-sm"
                  >
                    <span className="max-w-[140px] truncate text-laap-text-secondary">{att.name}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
