import { useCallback, useEffect, useRef, useState } from 'react';

// ============================================================================
// Types
// ============================================================================

export type VoiceChatState = 'idle' | 'listening' | 'thinking' | 'speaking';

export interface VoiceChatOptions {
  /** Language for speech recognition (default: zh-CN) */
  language?: string;
  /** Whether to auto-start listening after assistant finishes speaking */
  continuousMode?: boolean;
  /** Allow barge-in: keep ASR active during TTS so user can interrupt */
  bargeInEnabled?: boolean;
  /** Callback when speech is transcribed */
  onTranscript?: (text: string) => void;
  /** Callback when voice state changes */
  onStateChange?: (state: VoiceChatState) => void;
  /** Whether TTS is enabled for assistant responses */
  ttsEnabled?: boolean;
}

// ============================================================================
// Speech Recognition Types & API
// ============================================================================

interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message: string;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  onstart: (() => void) | null;
}

const SpeechRecognitionAPI =
  typeof window !== 'undefined'
    ? (window as unknown as Record<string, new () => SpeechRecognition>).SpeechRecognition ||
      (window as unknown as Record<string, new () => SpeechRecognition>).webkitSpeechRecognition
    : undefined;

function createSpeechRecognition(lang: string, continuous = false): SpeechRecognition | null {
  if (!SpeechRecognitionAPI) return null;
  const recognition = new SpeechRecognitionAPI();
  recognition.continuous = continuous;
  recognition.interimResults = true;
  recognition.lang = lang;
  return recognition;
}

// ============================================================================
// Debug Logger
// ============================================================================

let logIdCounter = 0;
const LOG_PREFIX = '[BARGEIN]';

/** Returns ms since the session start (first call to logBargein) */
function logBargein(...args: unknown[]) {
  const ts = performance.now().toFixed(1);
  // eslint-disable-next-line no-console
  console.log(`%c${LOG_PREFIX}[+${ts}ms]`, 'color:#f59e0b;font-weight:bold', ...args);
}

// ============================================================================
// Voice Activity Detector (fast audio-level based barge-in trigger)
// Uses Web Audio API AnalyserNode to detect microphone volume in real-time.
// Responds in ~10-50ms, much faster than ASR warm-up (300-500ms).
// ============================================================================

class VoiceActivityDetector {
  private stream: MediaStream | null = null;
  private audioCtx: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private dataArray: Uint8Array | null = null;
  private rafId: number | null = null;
  private onVoiceDetected: (() => void) | null = null;
  private threshold: number;
  private requiredFrames: number;
  private consecutiveFrames = 0;
  private running = false;

  /**
   * @param threshold      RMS threshold (0-1). 0.08~0.15 works for most mics.
   * @param requiredFrames How many consecutive frames above threshold trigger.
   *                       At 60fps, 3 frames ≈ 50ms of sustained speech.
   */
  constructor(threshold = 0.10, requiredFrames = 3) {
    this.threshold = threshold;
    this.requiredFrames = requiredFrames;
  }

  get isRunning(): boolean {
    return this.running;
  }

  async start(onVoiceDetected: () => void): Promise<void> {
    if (this.running) return;
    this.onVoiceDetected = onVoiceDetected;
    this.consecutiveFrames = 0;

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.audioCtx = new AudioContext();
      const source = this.audioCtx.createMediaStreamSource(this.stream);
      this.analyser = this.audioCtx.createAnalyser();
      this.analyser.fftSize = 256;
      source.connect(this.analyser);
      this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
      this.running = true;
      logBargein('VoiceActivityDetector started (threshold=', this.threshold, ', requiredFrames=', this.requiredFrames, ')');
      this.poll();
    } catch (err) {
      logBargein('VoiceActivityDetector: getUserMedia failed:', err);
      this.running = false;
    }
  }

  private poll = () => {
    if (!this.running || !this.analyser || !this.dataArray) return;

    this.analyser.getByteTimeDomainData(this.dataArray);

    // Compute RMS (root mean square) volume
    let sumSquares = 0;
    for (let i = 0; i < this.dataArray.length; i++) {
      const normalized = (this.dataArray[i] - 128) / 128;
      sumSquares += normalized * normalized;
    }
    const rms = Math.sqrt(sumSquares / this.dataArray.length);

    if (rms > this.threshold) {
      this.consecutiveFrames++;
      if (this.consecutiveFrames >= this.requiredFrames) {
        logBargein('VAD triggered! rms=', rms.toFixed(4), 'consecutiveFrames=', this.consecutiveFrames);
        this.consecutiveFrames = 0;
        this.onVoiceDetected?.();
      }
    } else {
      if (this.consecutiveFrames > 0) {
        this.consecutiveFrames = 0;
      }
    }

    this.rafId = requestAnimationFrame(this.poll);
  };

  stop() {
    if (!this.running) return;
    this.running = false;
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    if (this.audioCtx) {
      this.audioCtx.close().catch(() => {});
      this.audioCtx = null;
    }
    if (this.stream) {
      this.stream.getTracks().forEach((t) => t.stop());
      this.stream = null;
    }
    this.analyser = null;
    this.dataArray = null;
    logBargein('VoiceActivityDetector stopped');
  }
}

// ============================================================================
// Speech Synthesis Manager
// ============================================================================

let currentUtterance: SpeechSynthesisUtterance | null = null;

function getVoices(): SpeechSynthesisVoice[] {
  if (typeof window === 'undefined' || !window.speechSynthesis) return [];
  return window.speechSynthesis.getVoices();
}

/**
 * Find the best TTS voice — prefer Microsoft Neural voices (most natural).
 * Priority order: Xiaoxiao (晓晓) > Yunjian (云健) > Yunxi (云希) > any zh-CN local > any zh-CN > any voice
 */
function findBestVoice(lang: string): SpeechSynthesisVoice | null {
  const voices = getVoices();
  const langPrefix = lang.split('-')[0];

  const preferred: string[] = [
    'Microsoft Xiaoxiao',
    'Microsoft Yunjian',
    'Microsoft Yunxi',
    'Microsoft Yunyang',
    'Microsoft Yunfeng',
    'Microsoft Xiaoyi',
    'Microsoft Xiaohan',
    'Microsoft Xiaochen',
  ];

  for (const name of preferred) {
    const match = voices.find(
      (v) => v.name.includes(name) && v.lang.startsWith(langPrefix)
    );
    if (match) return match;
  }

  // Fallback: any local voice matching the language
  const localMatch = voices.find((v) => v.lang.startsWith(langPrefix) && v.localService);
  if (localMatch) return localMatch;

  // Fallback: any voice matching the language
  const anyMatch = voices.find((v) => v.lang.startsWith(langPrefix));
  if (anyMatch) return anyMatch;

  // Last resort: any Chinese voice, then any voice
  return voices.find((v) => v.lang.startsWith('zh')) || voices[0] || null;
}

function speakTextAsync(text: string, lang: string, rate = 1.0): Promise<void> {
  return new Promise((resolve, reject) => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      resolve();
      return;
    }

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang;
    utterance.rate = rate;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    const voice = findBestVoice(lang);
    if (voice) utterance.voice = voice;

    currentUtterance = utterance;

    utterance.onend = () => {
      currentUtterance = null;
      resolve();
    };

    utterance.onerror = (event) => {
      currentUtterance = null;
      if (event.error !== 'canceled' && event.error !== 'interrupted') {
        reject(event.error);
      } else {
        resolve();
      }
    };

    window.speechSynthesis.speak(utterance);
  });
}

function stopSpeaking() {
  if (typeof window !== 'undefined' && window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
  currentUtterance = null;
}

// ============================================================================
// Clean text for TTS (strip markdown/HTML)
// ============================================================================

function cleanForTTS(text: string): string {
  return text
    .replace(/<[^>]*>/g, '')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/[*_~#>`|\\]/g, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function splitIntoChunks(text: string, maxLen = 200): string[] {
  const chunks: string[] = [];
  let current = '';
  for (const sentence of text.split(/(?<=[。！？.!?\n])/)) {
    if ((current + sentence).length > maxLen && current) {
      chunks.push(current.trim());
      current = sentence;
    } else {
      current += sentence;
    }
  }
  if (current.trim()) chunks.push(current.trim());
  return chunks;
}

// ============================================================================
// React Hook
// ============================================================================

export function useVoiceChat(options: VoiceChatOptions = {}) {
  const {
    language = 'zh-CN',
    continuousMode = false,
    bargeInEnabled = true,
    ttsEnabled = true,
    onTranscript,
    onStateChange,
  } = options;

  const [state, setState] = useState<VoiceChatState>('idle');
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [isSupported, setIsSupported] = useState(false);
  const [continuousEnabled, setContinuousEnabled] = useState(continuousMode);

  const stateRef = useRef(state);
  stateRef.current = state;

  // Main ASR recognition (for user-initiated listening)
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  // Barge-in ASR recognition (runs alongside TTS to detect interruption)
  const bargeinRef = useRef<SpeechRecognition | null>(null);
  // Voice activity detector (fast audio-level trigger)
  const vadRef = useRef<VoiceActivityDetector | null>(null);
  const pendingTranscriptRef = useRef('');

  // Check browser support
  useEffect(() => {
    const asrSupported = !!SpeechRecognitionAPI;
    const ttsSupported = typeof window !== 'undefined' && !!window.speechSynthesis;
    setIsSupported(asrSupported || ttsSupported);

    if (ttsSupported) {
      const updateVoices = () => setVoices(getVoices());
      updateVoices();
      window.speechSynthesis.onvoiceschanged = updateVoices;
      return () => {
        window.speechSynthesis.onvoiceschanged = null;
      };
    }
  }, []);

  const updateState = useCallback(
    (newState: VoiceChatState) => {
      setState(newState);
      onStateChange?.(newState);
    },
    [onStateChange]
  );

  // ─── Stop barge-in recognition ───
  const stopBargein = useCallback(() => {
    if (bargeinRef.current) {
      try {
        logBargein('Stopping barge-in ASR');
        bargeinRef.current.abort();
      } catch { /* ignore */ }
      bargeinRef.current = null;
    }
    if (vadRef.current) {
      vadRef.current.stop();
      vadRef.current = null;
    }
  }, []);

  // ─── Start listening (main ASR) ───
  const startListening = useCallback(() => {
    if (stateRef.current === 'listening') return;
    if (!SpeechRecognitionAPI) {
      console.warn('[VoiceChat] SpeechRecognition not supported');
      return;
    }

    // Cancel any ongoing speech
    stopSpeaking();

    const recognition = createSpeechRecognition(language, false);
    if (!recognition) {
      console.warn('[VoiceChat] Failed to create SpeechRecognition');
      return;
    }

    recognitionRef.current = recognition;
    pendingTranscriptRef.current = '';

    const startTs = performance.now();

    recognition.onstart = () => {
      logBargein('Main ASR engine ready (', (performance.now() - startTs).toFixed(0), 'ms)');
      updateState('listening');
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let final = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          final += result[0].transcript;
        }
      }
      if (final) {
        pendingTranscriptRef.current += final;
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      logBargein('Main ASR error:', event.error, event.message || '');
      if (event.error === 'no-speech' || event.error === 'aborted') {
        if (stateRef.current === 'listening' && continuousEnabled) {
          setTimeout(() => startListening(), 300);
        }
      }
      updateState('idle');
    };

    recognition.onend = () => {
      const transcript = pendingTranscriptRef.current;
      if (transcript) {
        logBargein('Main ASR transcript:', JSON.stringify(transcript));
        onTranscript?.(transcript);
        pendingTranscriptRef.current = '';
      }
      if (stateRef.current === 'listening' && continuousEnabled) {
        logBargein('Main ASR ended, restarting (continuous mode)');
        setTimeout(() => startListening(), 500);
      } else {
        updateState('idle');
      }
    };

    try {
      logBargein('Main ASR start()');
      recognition.start();
    } catch (err) {
      console.warn('[VoiceChat] Recognition start failed:', err);
      updateState('idle');
    }
  }, [language, continuousEnabled, onTranscript, updateState]);

  // ─── Stop listening (main ASR) ───
  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch { /* ignore */ }
      recognitionRef.current = null;
    }
    if (stateRef.current === 'listening') {
      updateState('idle');
    }
  }, [updateState]);

  const toggleListening = useCallback(() => {
    if (stateRef.current === 'listening') {
      stopListening();
    } else {
      startListening();
    }
  }, [startListening, stopListening]);

  // ─── Barge-in: start VAD + continuous ASR during TTS ───
  //
  // Two-layer approach for fast barge-in:
  //
  //   Layer 1 (fast, ~10-50ms): VoiceActivityDetector
  //     Uses Web Audio API AnalyserNode to detect microphone volume.
  //     When RMS exceeds threshold for N consecutive frames, triggers barge-in.
  //
  //   Layer 2 (precise, ~300-500ms): ASR with continuous + interimResults
  //     Browser SpeechRecognition warms up and provides transcripts.
  //     Once ASR is ready, interim results also trigger barge-in.
  //
  // Combined: The VAD catches the first moment of speech (fast),
  // while ASR catches up and provides the actual transcription.
  //
  const startBargein = useCallback(() => {
    if (!SpeechRecognitionAPI || !bargeInEnabled) return;
    if (stateRef.current === 'listening') return;

    stopBargein();
    pendingTranscriptRef.current = '';

    logBargein('=== Barge-in start ===');
    const startTs = performance.now();

    // ── Layer 1: Voice Activity Detector (fast) ──
    const vad = new VoiceActivityDetector(0.10, 3);
    vadRef.current = vad;
    let vadTriggered = false;

    vad.start(() => {
      if (vadTriggered) return;
      vadTriggered = true;
      const elapsed = (performance.now() - startTs).toFixed(0);
      logBargein(`[VAD] Voice detected! (${elapsed}ms since start) → cancelling TTS`);
      stopSpeaking();
      updateState('listening');
    });

    // ── Layer 2: ASR-based detection (precise) ──
    const recognition = createSpeechRecognition(language, true);
    if (!recognition) return;

    bargeinRef.current = recognition;
    let asrTriggered = false;
    let asrWarmedUp = false;

    recognition.onstart = () => {
      asrWarmedUp = true;
      logBargein('Barge-in ASR engine ready (', (performance.now() - startTs).toFixed(0), 'ms)');
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      // Check each new result for speech
      let hasSpeech = false;
      let interimText = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript.trim();
        if (transcript.length > 0) {
          hasSpeech = true;
          interimText += transcript;
          if (event.results[i].isFinal) {
            pendingTranscriptRef.current += transcript;
          }
        }
      }

      // Log interim results for debugging
      if (hasSpeech && interimText) {
        const elapsed = (performance.now() - startTs).toFixed(0);
        if (!asrTriggered) {
          logBargein(`[ASR] Interim result: "${interimText}" (${elapsed}ms since start, warmedUp=${asrWarmedUp})`);
        }
      }

      if (hasSpeech && !asrTriggered) {
        asrTriggered = true;
        const elapsed = (performance.now() - startTs).toFixed(0);
        logBargein(`[ASR] Barge-in triggered! (${elapsed}ms since start) → cancelling TTS`);
        stopSpeaking();
        updateState('listening');
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      logBargein('Barge-in ASR error:', event.error, event.message || '');
    };

    recognition.onend = () => {
      logBargein('Barge-in ASR ended (triggered=', asrTriggered, ')');
      bargeinRef.current = null;

      if (asrTriggered) {
        const transcript = pendingTranscriptRef.current;
        if (transcript) {
          logBargein('Barge-in transcript:', JSON.stringify(transcript));
          onTranscript?.(transcript);
          pendingTranscriptRef.current = '';
        }
      }

      // If barge-in was triggered but state is still listening, keep listening
      // If no barge-in happened, the VAD is still running, keep it
    };

    try {
      logBargein('Barge-in ASR start()');
      recognition.start();
    } catch (err) {
      logBargein('Barge-in ASR start() failed:', err);
      bargeinRef.current = null;
    }
  }, [language, bargeInEnabled, continuousEnabled, onTranscript, updateState, stopBargein]);

  // ─── Speak text (TTS) with barge-in ───
  const speak = useCallback(
    async (text: string) => {
      if (!ttsEnabled) return;
      if (typeof window === 'undefined' || !window.speechSynthesis) return;

      if (stateRef.current === 'listening') {
        stopListening();
      }

      const clean = cleanForTTS(text);
      if (!clean) return;

      updateState('speaking');

      // Start barge-in (VAD + ASR) in parallel with TTS
      if (continuousEnabled && bargeInEnabled) {
        startBargein();
      }

      logBargein('TTS started, chunks=', splitIntoChunks(clean, 200).length);

      try {
        const chunks = splitIntoChunks(clean, 200);
        for (let ci = 0; ci < chunks.length; ci++) {
          // Check if barge-in already cancelled us
          if (stateRef.current === 'idle') {
            logBargein('TTS chunk', ci, 'skipped (state=idle, barge-in cancelled)');
            break;
          }
          if (stateRef.current === 'speaking' || stateRef.current === 'listening') {
            await speakTextAsync(chunks[ci], language, 1.0);
          }
        }
      } catch (err) {
        console.warn('[VoiceChat] TTS error:', err);
      } finally {
        stopBargein();

        if (stateRef.current === 'speaking') {
          logBargein('TTS finished naturally');
          updateState('idle');
        }
        if (continuousEnabled && stateRef.current === 'idle') {
          logBargein('TTS done, starting listening (continuous mode)');
          setTimeout(() => startListening(), 500);
        }
      }
    },
    [ttsEnabled, language, continuousEnabled, bargeInEnabled, stopListening, updateState, startListening, startBargein, stopBargein]
  );

  // ─── Stop speaking ───
  const stopSpeaking_ = useCallback(() => {
    stopSpeaking();
    stopBargein();
    if (stateRef.current === 'speaking') {
      updateState('idle');
    }
  }, [updateState, stopBargein]);

  // ─── Toggle continuous mode ───
  const toggleContinuous = useCallback(() => {
    const next = !continuousEnabled;
    logBargein('Continuous mode:', next ? 'ON' : 'OFF');
    setContinuousEnabled(next);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopListening();
      stopSpeaking();
      stopBargein();
    };
  }, [stopListening, stopBargein]);

  return {
    state,
    isSupported,
    voices,
    continuousEnabled,
    isListening: state === 'listening',
    isSpeaking: state === 'speaking',
    startListening,
    stopListening,
    toggleListening,
    speak,
    stopSpeaking: stopSpeaking_,
    toggleContinuous,
    setContinuousEnabled,
  };
}

// Re-export voice helpers for external use
export { findBestVoice, getVoices, cleanForTTS, splitIntoChunks };