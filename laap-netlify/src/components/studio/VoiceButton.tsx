import { Mic, MicOff, Loader2, Square } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { VoiceChatState } from '@/hooks/useVoiceChat';

interface VoiceButtonProps {
  state: VoiceChatState;
  isSupported: boolean;
  continuousEnabled: boolean;
  onToggleListening: () => void;
  onToggleContinuous: () => void;
  onStopSpeaking?: () => void;
  disabled?: boolean;
}

export function VoiceButton({
  state,
  isSupported,
  continuousEnabled,
  onToggleListening,
  onToggleContinuous,
  onStopSpeaking,
  disabled,
}: VoiceButtonProps) {
  if (!isSupported) return null;

  const isActive = state === 'listening';
  const isSpeaking = state === 'speaking';
  const isThinking = state === 'thinking';

  function handleClick() {
    if (isSpeaking) {
      onStopSpeaking?.();
    } else {
      onToggleListening();
    }
  }

  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        onClick={handleClick}
        disabled={disabled || isThinking}
        className={cn(
          'p-1.5 min-h-[40px] min-w-[40px] flex items-center justify-center rounded-sm transition-all',
          isActive && 'bg-laap-rose/20 text-laap-rose border border-laap-rose/50 animate-pulse',
          isSpeaking && 'bg-laap-gold/20 text-laap-gold border border-laap-gold/50',
          !isActive && !isSpeaking && 'text-laap-text-tertiary border border-transparent hover:text-white hover:border-laap-gold/50',
          isThinking && 'opacity-50 cursor-not-allowed',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
        title={
          isActive ? '点击停止录音' :
          isSpeaking ? '点击停止语音播放' :
          '点击开始语音输入'
        }
        aria-label={
          isActive ? '停止录音' :
          isSpeaking ? '停止语音播放' :
          '语音输入'
        }
      >
        {isThinking ? (
          <Loader2 size={16} className="animate-spin" />
        ) : isSpeaking ? (
          <Square size={16} />
        ) : isActive ? (
          <MicOff size={16} />
        ) : (
          <Mic size={16} />
        )}
      </button>

      {isActive && (
        <button
          type="button"
          onClick={onToggleContinuous}
          className={cn(
            'px-1.5 py-1 min-h-[28px] text-[10px] border rounded-sm transition-colors',
            continuousEnabled
              ? 'text-laap-emerald border-laap-emerald/50 bg-laap-emerald/10'
              : 'text-laap-text-tertiary border-laap-border hover:text-white'
          )}
          title={continuousEnabled ? '关闭连续对话模式' : '开启连续对话模式（说话可打断）'}
          aria-pressed={continuousEnabled}
        >
          {continuousEnabled ? '连续' : '单次'}
        </button>
      )}
    </div>
  );
}