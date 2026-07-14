/**
 * useLaap hook
 *
 * 便捷访问 LAAP 全局状态与操作，组件无需直接依赖 Zustand store。
 */

import { useLaapStore } from '../store/laapStore'

/**
 * 返回 LAAP store 中的状态与 actions
 */
export function useLaap() {
  const store = useLaapStore()

  return {
    connectionStatus: store.connectionStatus,
    messages: store.messages,
    psiCycle: store.psiCycle,
    vitalSigns: store.vitalSigns,
    rateBuffer: store.rateBuffer,
    colony: store.colony,
    scene: store.scene,
    currentToolCall: store.currentToolCall,
    thoughts: store.thoughts,
    isStreaming: store.isStreaming,
    error: store.error,
    voice: store.voice,

    sendUserMessage: store.sendUserMessage,
    connect: store.connect,
    disconnect: store.disconnect,
    reconnect: store.reconnect,
    updateVitalSigns: store.updateVitalSigns,
    retryToolCall: store.retryToolCall,
    clearError: store.clearError,
    setVoiceStatus: store.setVoiceStatus,
    setVoiceAudioLevel: store.setVoiceAudioLevel,
    setVoiceContinuousListening: store.setVoiceContinuousListening,
    sendVoiceInput: store.sendVoiceInput,
    clearVoiceTtsAudio: store.clearVoiceTtsAudio,
  }
}
