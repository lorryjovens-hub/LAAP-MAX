import { forwardRef, useEffect, useRef, useState } from 'react';
import { Send, Paperclip, X, FileText, Image as ImageIcon, Loader2, AlertCircle, Globe } from 'lucide-react';
import type { ChatAttachment } from '@/lib/chat';
import { isDocumentFile, parseDocument } from '@/lib/documentParser';
import { VoiceButton } from './VoiceButton';
import type { VoiceChatState } from '@/hooks/useVoiceChat';

interface ChatInputProps {
  onSend: (text: string, attachments: ChatAttachment[]) => void;
  loading: boolean;
  enterToSend?: boolean;
  focusMode?: boolean;
  webSearch?: boolean;
  onWebSearchChange?: (enabled: boolean) => void;
  // Voice chat props
  voiceState?: VoiceChatState;
  voiceSupported?: boolean;
  voiceContinuousEnabled?: boolean;
  onVoiceToggleListening?: () => void;
  onVoiceToggleContinuous?: () => void;
  onVoiceStopSpeaking?: () => void;
}

const TEXT_MIME_TYPES = [
  'text/plain',
  'text/markdown',
  'text/html',
  'text/css',
  'text/javascript',
  'application/json',
  'application/typescript',
];

const MAX_INPUT_LENGTH = 200_000;

export const ChatInput = forwardRef<HTMLTextAreaElement, ChatInputProps>(function ChatInput(
  {
    onSend, loading, enterToSend = true, focusMode = false,
    webSearch: webSearchProp, onWebSearchChange,
    voiceState, voiceSupported, voiceContinuousEnabled,
    onVoiceToggleListening, onVoiceToggleContinuous, onVoiceStopSpeaking,
  },
  ref
) {
  const [text, setText] = useState('');
  const [attachments, setAttachments] = useState<ChatAttachment[]>([]);
  const [parsing, setParsing] = useState(false);
  const [charCount, setCharCount] = useState(0);
  const [overLimit, setOverLimit] = useState(false);
  const [limitWarning, setLimitWarning] = useState(false);
  const [internalWebSearch, setInternalWebSearch] = useState(false);
  const webSearch = webSearchProp !== undefined ? webSearchProp : internalWebSearch;
  const fileRef = useRef<HTMLInputElement>(null);
  const validationRafRef = useRef<number | null>(null);
  const warningTimeoutRef = useRef<number | null>(null);

  function scheduleValidation(value: string) {
    if (validationRafRef.current) {
      cancelAnimationFrame(validationRafRef.current);
    }
    validationRafRef.current = requestAnimationFrame(() => {
      setCharCount(value.length);
      setOverLimit(value.length > MAX_INPUT_LENGTH);
    });
  }

  function showLimitWarning() {
    setLimitWarning(true);
    if (warningTimeoutRef.current) {
      window.clearTimeout(warningTimeoutRef.current);
    }
    warningTimeoutRef.current = window.setTimeout(() => {
      setLimitWarning(false);
    }, 2000);
  }

  useEffect(() => {
    return () => {
      if (validationRafRef.current) cancelAnimationFrame(validationRafRef.current);
      if (warningTimeoutRef.current) window.clearTimeout(warningTimeoutRef.current);
    };
  }, []);

  function toggleWebSearch() {
    const next = !webSearch;
    if (webSearchProp === undefined) {
      setInternalWebSearch(next);
    }
    onWebSearchChange?.(next);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      if (enterToSend) {
        e.preventDefault();
        submit();
      }
    } else if (e.key === 'Enter' && e.ctrlKey && !enterToSend) {
      e.preventDefault();
      submit();
    }
  }

  function submit() {
    const trimmed = text.trim();
    if ((!trimmed && attachments.length === 0) || loading || parsing) return;
    if (text.length > MAX_INPUT_LENGTH) {
      showLimitWarning();
      return;
    }
    const message = webSearch && trimmed ? `请先使用 web_search 工具联网搜索，再基于搜索结果回答：${trimmed}` : trimmed;
    onSend(message, attachments);
    setText('');
    setCharCount(0);
    setOverLimit(false);
    setAttachments([]);
    if (webSearchProp === undefined) {
      setInternalWebSearch(false);
    }
    onWebSearchChange?.(false);
  }

  function handleChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    const rawValue = e.target.value;
    if (rawValue.length > MAX_INPUT_LENGTH) {
      const clamped = rawValue.slice(0, MAX_INPUT_LENGTH);
      setText(clamped);
      scheduleValidation(clamped);
      showLimitWarning();
      return;
    }
    setText(rawValue);
    scheduleValidation(rawValue);
  }

  function readFileAttachment(file: File): Promise<ChatAttachment> {
    return new Promise((resolve, reject) => {
      const isImage = file.type.startsWith('image/');
      const isText = file.type.startsWith('text/') || TEXT_MIME_TYPES.includes(file.type);
      const reader = new FileReader();

      reader.onload = () => {
        const raw = String(reader.result ?? '');
        if (isImage) {
          const match = raw.match(/^data:([^;]+);base64,(.+)$/);
          if (match) {
            resolve({
              id: crypto.randomUUID(),
              type: 'image',
              name: file.name,
              mimeType: match[1],
              content: match[2],
            });
          } else {
            reject(new Error('无法解析图片'));
          }
        } else if (isText) {
          resolve({
            id: crypto.randomUUID(),
            type: 'text',
            name: file.name,
            mimeType: file.type || 'text/plain',
            content: raw,
          });
        } else {
          resolve({
            id: crypto.randomUUID(),
            type: 'file',
            name: file.name,
            mimeType: file.type || 'application/octet-stream',
            content: raw.replace(/^data:.*;base64,/, ''),
          });
        }
      };

      reader.onerror = () => reject(reader.error);

      if (isText) {
        reader.readAsText(file);
      } else {
        reader.readAsDataURL(file);
      }
    });
  }

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    const MAX_SIZE = 5 * 1024 * 1024;
    const results: ChatAttachment[] = [];
    const documentFiles: File[] = [];

    for (const file of files) {
      if (file.size > MAX_SIZE) continue;
      if (isDocumentFile(file)) {
        documentFiles.push(file);
      } else {
        try {
          const att = await readFileAttachment(file);
          results.push(att);
        } catch {
          // ignore failed reads
        }
      }
    }

    if (documentFiles.length > 0) {
      setParsing(true);
      for (const file of documentFiles) {
        try {
          const { attachment, truncated } = await parseDocument(file);
          results.push({
            id: attachment.id,
            type: 'document',
            name: attachment.name,
            mimeType: attachment.mimeType,
            content: attachment.text,
            pages: attachment.pages,
            wordCount: attachment.text.length,
            size: attachment.size,
          });
          if (truncated) {
            // 截断提示已写入 content 末尾，附件卡片会显示警告图标
          }
        } catch {
          // 文档解析失败时静默跳过，避免阻塞其他文件
        }
      }
      setParsing(false);
    }

    if (results.length > 0) {
      setAttachments((prev) => [...prev, ...results]);
    }

    if (fileRef.current) {
      fileRef.current.value = '';
    }
  }

  function removeAttachment(id: string) {
    setAttachments((prev) => prev.filter((a) => a.id !== id));
  }

  const hasContent = text.trim().length > 0 || attachments.length > 0;
  const canSend = hasContent && !overLimit && !loading && !parsing;

  return (
    <div className={`${focusMode ? 'px-2 py-2' : 'p-4'} border-t border-laap-border bg-laap-bg-primary/80 backdrop-blur-md`}>
      <div className="max-w-3xl mx-auto">
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-2">
            {attachments.map((att) => (
              <AttachmentChip key={att.id} attachment={att} onRemove={() => removeAttachment(att.id)} />
            ))}
          </div>
        )}

        <div className="border border-laap-border rounded-sm bg-laap-bg-secondary/30 focus-within:border-laap-gold/50 transition-colors">
          <textarea
            ref={ref}
            value={text}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="输入消息，Enter 发送，Shift+Enter 换行…"
            rows={1}
            className="w-full bg-transparent px-4 py-3 text-base sm:text-sm text-white placeholder:text-laap-text-tertiary focus:outline-none resize-none max-h-40"
            style={{ minHeight: focusMode ? '40px' : '48px' }}
          />
          <div className="flex items-center justify-between px-3 pb-2">
            <div className="flex items-center gap-2">
              <input
                ref={fileRef}
                type="file"
                multiple
                accept="image/*,.txt,.md,.markdown,.json,.csv,.js,.ts,.html,.css,.py,.pdf,.docx,.doc"
                onChange={handleFileChange}
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileRef.current?.click()}
                disabled={parsing}
                className="p-1.5 min-h-[40px] min-w-[40px] flex items-center justify-center text-laap-text-tertiary hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="上传图片或文件"
              >
                {parsing ? <Loader2 size={16} className="animate-spin" /> : <Paperclip size={16} />}
              </button>
              {!focusMode && (
                <button
                  type="button"
                  onClick={toggleWebSearch}
                  className={`flex items-center gap-1 px-2 py-1 min-h-[40px] text-xs border rounded-sm transition-colors ${
                    webSearch
                      ? 'text-laap-gold border-laap-gold/50 bg-laap-gold/10'
                      : 'text-laap-text-tertiary border-laap-border hover:text-white hover:border-laap-gold/50'
                  }`}
                  title={webSearch ? '已启用联网搜索' : '启用联网搜索'}
                  aria-pressed={webSearch}
                >
                  <Globe size={12} />
                  联网
                </button>
              )}
              {voiceSupported !== undefined && onVoiceToggleListening && (
                <VoiceButton
                  state={voiceState ?? 'idle'}
                  isSupported={voiceSupported}
                  continuousEnabled={voiceContinuousEnabled ?? false}
                  onToggleListening={onVoiceToggleListening}
                  onToggleContinuous={onVoiceToggleContinuous ?? (() => {})}
                  onStopSpeaking={onVoiceStopSpeaking}
                  disabled={loading}
                />
              )}
            </div>
            <button
              type="button"
              onClick={submit}
              disabled={!canSend}
              className="p-2 min-h-[40px] min-w-[40px] flex items-center justify-center bg-laap-gold text-laap-bg-primary rounded-sm hover:bg-laap-gold-light transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
        <div className="mt-2 text-[10px] text-center text-laap-text-tertiary">
          {enterToSend ? 'Enter 发送 · Shift+Enter 换行' : 'Ctrl+Enter 发送 · Enter 换行'}
          {!focusMode && (
            <span className="ml-2">
              · 最大 {MAX_INPUT_LENGTH.toLocaleString()} 字符
              <span className={`ml-1 ${overLimit ? 'text-laap-rose' : 'text-laap-text-tertiary'}`}>
                ({charCount.toLocaleString()})
              </span>
            </span>
          )}
          {limitWarning && (
            <span className="ml-2 text-laap-rose">已超出最大字符限制</span>
          )}
        </div>
      </div>
    </div>
  );
});

function AttachmentChip({ attachment, onRemove }: { attachment: ChatAttachment; onRemove: () => void }) {
  const isImage = attachment.type === 'image';
  const isDocument = attachment.type === 'document';
  const dataUrl = isImage ? `data:${attachment.mimeType};base64,${attachment.content}` : undefined;
  const isTruncated = isDocument && attachment.content.includes('[文档内容过长，已截断');

  let metaText = '';
  if (isDocument) {
    const parts: string[] = [];
    if (attachment.wordCount !== undefined) {
      parts.push(`${attachment.wordCount.toLocaleString()} 字`);
    }
    if (attachment.pages !== undefined) {
      parts.push(`${attachment.pages} 页`);
    }
    metaText = parts.join(' · ');
  }

  return (
    <div className="flex items-center gap-2 pl-1 pr-2 py-1 text-xs bg-laap-bg-tertiary/50 border border-laap-border rounded-sm group">
      {isImage && dataUrl ? (
        <img src={dataUrl} alt={attachment.name} className="w-6 h-6 rounded-sm object-cover" />
      ) : (
        <span className="p-1 text-laap-text-tertiary">
          {isDocument ? <FileText size={14} /> : attachment.type === 'text' ? <FileText size={14} /> : <ImageIcon size={14} />}
        </span>
      )}
      <div className="flex flex-col min-w-0">
        <span className="max-w-[160px] truncate text-laap-text-secondary">{attachment.name}</span>
        {metaText && (
          <span className="max-w-[160px] truncate text-[10px] text-laap-text-tertiary flex items-center gap-1">
            {metaText}
            {isTruncated && (
              <span title="文档内容过长，已截断至前 100,000 字符">
                <AlertCircle size={10} className="text-laap-gold" />
              </span>
            )}
          </span>
        )}
      </div>
      <button
        type="button"
        onClick={onRemove}
        className="min-h-[40px] min-w-[40px] flex items-center justify-center text-laap-text-tertiary hover:text-laap-rose transition-colors"
        aria-label="删除附件"
      >
        <X size={12} />
      </button>
    </div>
  );
}
