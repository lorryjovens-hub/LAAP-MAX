import { useEffect, useRef, useState } from 'react';
import {
  Bot,
  User,
  ChevronDown,
  ChevronUp,
  FileText,
  Image as ImageIcon,
  ArrowDown,
  ThumbsUp,
  ThumbsDown,
  ShieldAlert,
  BrainCircuit,
  Volume2,
  VolumeX,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { ScrollArea } from '@/components/ui/scroll-area';
import type { ChatAttachment, ChatMessage } from '@/lib/chat';
import { ThinkingProcess } from './ThinkingProcess';
import { cn } from '@/lib/utils';
import laapLogo from '@/lib/LAAP logo.jpg';

interface ChatCanvasProps {
  messages: ChatMessage[];
  loading: boolean;
  userAvatar?: string;
  robotAvatar?: string;
  agentName?: string;
  onFeedback?: (messageId: string, feedback: 'positive' | 'negative') => void;
  /** Callback to speak a message via TTS */
  onSpeak?: (text: string) => void;
  /** Whether TTS is currently speaking */
  isSpeaking?: boolean;
}

const LONG_MESSAGE_THRESHOLD = 5000;

export function ChatCanvas({ messages, loading, userAvatar, robotAvatar, agentName = 'LAAP', onFeedback, onSpeak, isSpeaking }: ChatCanvasProps) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const [isNearBottom, setIsNearBottom] = useState(true);
  const userScrolledRef = useRef(false);
  const lastLengthRef = useRef(messages.length);

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;

    const handleScroll = () => {
      userScrolledRef.current = true;
      const distance = viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight;
      setIsNearBottom(distance < 80);
    };

    viewport.addEventListener('scroll', handleScroll, { passive: true });
    return () => viewport.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;

    const hasNewMessages = messages.length !== lastLengthRef.current;
    lastLengthRef.current = messages.length;

    if (hasNewMessages && (isNearBottom || !userScrolledRef.current)) {
      const id = requestAnimationFrame(() => {
        viewport.scrollTo({ top: viewport.scrollHeight, behavior: 'smooth' });
      });
      return () => cancelAnimationFrame(id);
    }
  }, [messages, loading, isNearBottom]);

  function scrollToBottom() {
    const viewport = viewportRef.current;
    if (!viewport) return;
    viewport.scrollTo({ top: viewport.scrollHeight, behavior: 'smooth' });
    setIsNearBottom(true);
  }

  return (
    <div className="flex-1 relative min-h-0">
      <ScrollArea className="h-full px-4 py-6" viewportRef={viewportRef}>
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="w-20 h-20 rounded-full bg-laap-gold/10 border border-laap-gold/30 flex items-center justify-center mb-4 overflow-hidden">
                <img src={laapLogo} alt="LAAP" className="w-4/5 h-4/5 object-contain" />
              </div>
              <h3 className="font-display text-2xl text-white mb-2">{agentName} Agent Studio</h3>
              <p className="text-sm text-laap-text-secondary max-w-sm">
                基于 Harness 意识工程与 PSI-RSI 双重驱动，与你的数字生命体共同进化。
              </p>
            </div>
          )}

          {messages.map((message, index) => (
            <MessageBubble
              key={message.id}
              message={message}
              userAvatar={userAvatar}
              robotAvatar={robotAvatar}
              agentName={agentName}
              onFeedback={onFeedback}
              onSpeak={onSpeak}
              isSpeaking={isSpeaking}
              isStreaming={loading && index === messages.length - 1 && message.role === 'assistant'}
            />
          ))}

          {loading && messages.length > 0 && messages[messages.length - 1]?.role === 'user' && (
            <ResponseProgress agentName={agentName} />
          )}

          <div className="h-1" />
        </div>
      </ScrollArea>

      {!isNearBottom && (
        <button
          type="button"
          onClick={scrollToBottom}
          className={cn(
            'absolute bottom-4 left-1/2 -translate-x-1/2 z-10',
            'flex items-center gap-1.5 px-3 py-1.5 rounded-full',
            'bg-laap-bg-secondary/90 border border-laap-gold/40 text-laap-gold',
            'text-xs shadow-lg backdrop-blur-sm',
            'hover:bg-laap-gold hover:text-laap-bg-primary transition-colors'
          )}
        >
          <ArrowDown size={12} />
          回到最新
        </button>
      )}
    </div>
  );
}

function MessageBubble({
  message,
  userAvatar,
  robotAvatar,
  agentName = 'LAAP',
  onFeedback,
  onSpeak,
  isSpeaking,
  isStreaming,
}: {
  message: ChatMessage;
  userAvatar?: string;
  robotAvatar?: string;
  agentName?: string;
  onFeedback?: (messageId: string, feedback: 'positive' | 'negative') => void;
  onSpeak?: (text: string) => void;
  isSpeaking?: boolean;
  isStreaming?: boolean;
}) {
  const isUser = message.role === 'user';
  const [reportOpen, setReportOpen] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState(message.feedback || null);
  const customAvatar = isUser ? userAvatar : robotAvatar;
  const hasThinking =
    isStreaming ||
    (message.reasoning_steps && message.reasoning_steps.length > 0) ||
    (message.tool_calls && message.tool_calls.length > 0);

  const report = message.hallucination_report;
  const speculativeCount = report ? report.claims.filter((c) => c.category === 'speculative').length : 0;
  const hasUncertainty = speculativeCount > 0 || (report?.uncertainPhrases.length || 0) > 0;

  function handleFeedback(value: 'positive' | 'negative') {
    setFeedbackGiven(value);
    onFeedback?.(message.id, value);
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex gap-3 max-w-[85%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 overflow-hidden ${
            isUser
              ? 'bg-laap-bg-tertiary border border-laap-border'
              : 'bg-laap-gold/10 border border-laap-gold/30'
          }`}
        >
          {customAvatar ? (
            <img src={customAvatar} alt="avatar" className="w-full h-full object-cover" />
          ) : isUser ? (
            <User size={16} className="text-laap-text-secondary" />
          ) : (
            <Bot size={16} className="text-laap-gold" />
          )}
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
              <LongContent content={message.content} isUser={true} isStreaming={false} />
            ) : (
              <LongContent content={message.content} isUser={false} isStreaming={isStreaming} />
            )}
          </div>

          {isUser && message.attachments && message.attachments.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {message.attachments.map((att) => (
                <AttachmentPreview key={att.id} attachment={att} />
              ))}
            </div>
          )}

          {!isUser && (
            <div className="w-full space-y-2">
              {hasUncertainty && (
                <button
                  onClick={() => setReportOpen(!reportOpen)}
                  className="flex items-center gap-1.5 text-xs text-laap-amber hover:text-laap-amber/80 transition-colors"
                >
                  <ShieldAlert size={12} />
                  {speculativeCount > 0 ? `包含 ${speculativeCount} 处推测性内容` : '包含不确定表述'}
                  {reportOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                </button>
              )}

              {reportOpen && report && (
                <div className="border border-laap-amber/30 rounded-sm bg-laap-amber/5 px-3 py-2 space-y-2">
                  <div className="text-xs text-laap-amber flex items-center gap-1.5">
                    <BrainCircuit size={12} />
                    事实核查报告
                  </div>
                  <div className="text-[10px] text-laap-text-secondary leading-relaxed">
                    {report.recommendation}
                  </div>
                  {report.uncertainPhrases.length > 0 && (
                    <div className="text-[10px] text-laap-text-tertiary">
                      不确定表述：{report.uncertainPhrases.join('、')}
                    </div>
                  )}
                  <div className="text-[10px] text-laap-text-tertiary">
                    事实 {report.claims.filter((c) => c.category === 'factual').length} / 推测 {speculativeCount} / 主观 {report.claims.filter((c) => c.category === 'subjective').length}
                  </div>
                </div>
              )}

              {hasThinking && (
                <ThinkingProcess
                  steps={message.reasoning_steps || []}
                  toolCalls={message.tool_calls || []}
                  loading={isStreaming}
                  agentName={agentName}
                />
              )}

              {!isUser && (
                <div className="flex items-center gap-1 pt-1">
                  {onSpeak && !isStreaming && (
                    <button
                      onClick={() => onSpeak(message.content)}
                      className={cn(
                        'p-1 rounded-sm transition-colors',
                        isSpeaking
                          ? 'text-laap-gold'
                          : 'text-laap-text-tertiary hover:text-laap-gold'
                      )}
                      title="语音播放"
                    >
                      {isSpeaking ? <Volume2 size={12} className="animate-pulse" /> : <Volume2 size={12} />}
                    </button>
                  )}
                  {onFeedback && (
                    <>
                      <button
                        onClick={() => handleFeedback('positive')}
                        className={cn(
                          'p-1 rounded-sm transition-colors',
                          feedbackGiven === 'positive'
                            ? 'text-laap-emerald'
                            : 'text-laap-text-tertiary hover:text-white'
                        )}
                        title="有用"
                      >
                        <ThumbsUp size={12} />
                      </button>
                      <button
                        onClick={() => handleFeedback('negative')}
                        className={cn(
                          'p-1 rounded-sm transition-colors',
                          feedbackGiven === 'negative'
                            ? 'text-laap-rose'
                            : 'text-laap-text-tertiary hover:text-white'
                        )}
                        title="不准确"
                      >
                        <ThumbsDown size={12} />
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const TABLE_IMAGE_PREFIX = 'TABLE_IMAGE:';

function extractTableImages(content: string): { text: string; images: string[] } {
  const images: string[] = [];
  const text = content.replace(new RegExp(`${TABLE_IMAGE_PREFIX}([A-Za-z0-9+/=]+)`, 'g'), (_, base64) => {
    images.push(base64);
    return '';
  }).trim();
  return { text, images };
}

function LongContent({
  content,
  isUser,
  isStreaming,
}: {
  content: string;
  isUser: boolean;
  isStreaming?: boolean;
}) {
  const [expanded, setExpanded] = useState(isStreaming ?? false);
  const shouldCollapse = !isStreaming && content.length > LONG_MESSAGE_THRESHOLD;

  useEffect(() => {
    if (isStreaming) {
      setExpanded(true);
    }
  }, [isStreaming]);

  const displayContent = shouldCollapse && !expanded
    ? content.slice(0, LONG_MESSAGE_THRESHOLD)
    : content;

  const { text, images } = isUser
    ? { text: displayContent, images: [] }
    : extractTableImages(displayContent);

  return (
    <div className="space-y-2">
      {isUser ? (
        <p className="whitespace-pre-wrap">{displayContent}</p>
      ) : (
        <div className="prose prose-invert prose-sm max-w-none">
          <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
            {text || ' '}
          </ReactMarkdown>
        </div>
      )}

      {!isUser && images.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-1">
          {images.map((base64, idx) => (
            <a
              key={idx}
              href={`data:image/png;base64,${base64}`}
              target="_blank"
              rel="noreferrer"
              className="block rounded-sm border border-laap-border overflow-hidden hover:border-laap-gold/50 transition-colors"
            >
              <img
                src={`data:image/png;base64,${base64}`}
                alt={`表格图片 ${idx + 1}`}
                className="max-h-64 max-w-full object-contain"
              />
            </a>
          ))}
        </div>
      )}

      {shouldCollapse && (
        <button
          type="button"
          onClick={() => setExpanded((prev) => !prev)}
          className="flex items-center gap-1 text-xs text-laap-gold hover:text-laap-gold-light transition-colors"
          aria-label={expanded ? '收起长消息' : '展开长消息'}
        >
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          {expanded
            ? '收起'
            : `展开剩余 ${(content.length - LONG_MESSAGE_THRESHOLD).toLocaleString()} 字符`}
        </button>
      )}
    </div>
  );
}

function AttachmentPreview({ attachment }: { attachment: ChatAttachment }) {
  const isImage = attachment.type === 'image';
  const isDocument = attachment.type === 'document';
  const dataUrl = isImage ? `data:${attachment.mimeType};base64,${attachment.content}` : undefined;

  if (isImage && dataUrl) {
    return (
      <a href={dataUrl} target="_blank" rel="noreferrer">
        <img
          src={dataUrl}
          alt={attachment.name}
          className="max-h-32 max-w-[200px] rounded-sm border border-laap-border object-cover hover:border-laap-gold/50 transition-colors"
        />
      </a>
    );
  }

  const metaParts: string[] = [];
  if (isDocument) {
    if (attachment.wordCount !== undefined) metaParts.push(`${attachment.wordCount.toLocaleString()} 字`);
    if (attachment.pages !== undefined) metaParts.push(`${attachment.pages} 页`);
  }

  return (
    <div className="flex items-center gap-1.5 px-2 py-1 text-xs bg-laap-bg-tertiary/50 border border-laap-border rounded-sm">
      {isDocument || attachment.type === 'text' ? <FileText size={12} /> : <ImageIcon size={12} />}
      <span className="max-w-[140px] truncate text-laap-text-secondary">{attachment.name}</span>
      {metaParts.length > 0 && (
        <span className="text-[10px] text-laap-text-tertiary">({metaParts.join(' · ')})</span>
      )}
    </div>
  );
}

function ResponseProgress({ agentName = 'LAAP' }: { agentName?: string }) {
  return (
    <div className="flex items-start gap-3">
      <div className="w-8 h-8 rounded-full bg-laap-gold/10 border border-laap-gold/30 flex items-center justify-center flex-shrink-0 overflow-hidden">
        <Bot size={16} className="text-laap-gold" />
      </div>
      <div className="flex-1 max-w-md space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs text-laap-text-secondary">{agentName} 思考中</span>
          <div className="flex-1 h-1 bg-laap-bg-tertiary rounded-full overflow-hidden">
            <div className="h-full w-1/3 bg-gradient-to-r from-transparent via-laap-gold to-transparent progress-scroll" />
          </div>
        </div>
        <div className="relative rounded-sm overflow-hidden border border-laap-border aspect-video max-w-[240px]">
          <video
            src="/assets/aris-coding.mp4"
            autoPlay
            loop
            muted
            playsInline
            className="w-full h-full object-cover opacity-80"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-laap-bg-primary/80 to-transparent" />
        </div>
      </div>
    </div>
  );
}
