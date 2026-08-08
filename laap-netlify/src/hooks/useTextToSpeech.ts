import { useState, useEffect, useCallback, useRef } from 'react';

interface UseTextToSpeechReturn {
  speaking: boolean;
  paused: boolean;
  startSpeaking: (text: string) => void;
  stopSpeaking: () => void;
  pauseSpeaking: () => void;
  resumeSpeaking: () => void;
}

function stripMarkdown(text: string): string {
  return text
    .replace(/!\[.*?\]\(.*?\)/g, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/[*_]{1,2}([^*_]+)[*_]{1,2}/g, '$1')
    .replace(/`{1,3}[^`]*`{1,3}/g, '')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^\s*[-*+]\s+/gm, '')
    .replace(/^\s*\d+\.\s+/gm, '')
    .replace(/\n+/g, '\n')
    .trim();
}

function selectMicrosoftVoice(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  const preferred = voices.find(
    (v) =>
      v.name.includes('Microsoft Yaoyao') ||
      v.name.includes('Microsoft Yunxi') ||
      v.name.includes('Microsoft Yunjian') ||
      v.name.includes('Microsoft Huihui')
  );
  if (preferred) return preferred;

  const zhCN = voices.find((v) => v.lang === 'zh-CN');
  if (zhCN) return zhCN;

  const zh = voices.find((v) => v.lang.startsWith('zh'));
  return zh || voices[0] || null;
}

export function useTextToSpeech(): UseTextToSpeechReturn {
  const [speaking, setSpeaking] = useState(false);
  const [paused, setPaused] = useState(false);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const stopSpeaking = useCallback(() => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setSpeaking(false);
    setPaused(false);
    utteranceRef.current = null;
  }, []);

  const startSpeaking = useCallback((text: string) => {
    if (!window.speechSynthesis) {
      console.warn('当前浏览器不支持语音合成。');
      return;
    }

    window.speechSynthesis.cancel();

    const cleaned = stripMarkdown(text);
    const utterance = new SpeechSynthesisUtterance(cleaned);
    utterance.lang = 'zh-CN';
    utterance.rate = 1;
    utterance.pitch = 1;

    const voices = window.speechSynthesis.getVoices();
    const voice = selectMicrosoftVoice(voices);
    if (voice) {
      utterance.voice = voice;
    }

    utterance.onstart = () => {
      setSpeaking(true);
      setPaused(false);
    };
    utterance.onend = () => {
      setSpeaking(false);
      setPaused(false);
      utteranceRef.current = null;
    };
    utterance.onerror = () => {
      setSpeaking(false);
      setPaused(false);
      utteranceRef.current = null;
    };

    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  }, []);

  const pauseSpeaking = useCallback(() => {
    if (window.speechSynthesis && speaking && !paused) {
      window.speechSynthesis.pause();
      setPaused(true);
    }
  }, [speaking, paused]);

  const resumeSpeaking = useCallback(() => {
    if (window.speechSynthesis && paused) {
      window.speechSynthesis.resume();
      setPaused(false);
    }
  }, [paused]);

  useEffect(() => {
    const handleVoicesChanged = () => {
      // Voices loaded; next startSpeaking will pick the best available voice.
    };
    window.speechSynthesis?.addEventListener('voiceschanged', handleVoicesChanged);
    return () => {
      window.speechSynthesis?.removeEventListener('voiceschanged', handleVoicesChanged);
      window.speechSynthesis?.cancel();
    };
  }, []);

  return { speaking, paused, startSpeaking, stopSpeaking, pauseSpeaking, resumeSpeaking };
}
