/**
 * useLaap hook — extended with Cognitive Engine state.
 */

import { useLaapStore } from '../store/laapStore'

export function useLaap() {
  const store = useLaapStore()

  return {
    connectionStatus: store.connectionStatus,
    messages: store.messages,
    sessions: store.sessions,
    activeSessionId: store.activeSessionId,
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
    terminalSessions: store.terminalSessions,
    pendingToolConfirmations: store.pendingToolConfirmations,

    // Cognitive Engine extensions
    engine: store.engine,
    focusFrames: store.focusFrames,
    surfaces: store.surfaces,
    contextDiagnostics: store.contextDiagnostics,

    sendUserMessage: store.sendUserMessage,
    connect: store.connect,
    disconnect: store.disconnect,
    reconnect: store.reconnect,
    newSession: store.newSession,
    selectSession: store.selectSession,
    deleteSession: store.deleteSession,
    updateVitalSigns: store.updateVitalSigns,
    retryToolCall: store.retryToolCall,
    confirmToolCall: store.confirmToolCall,
    rejectToolCall: store.rejectToolCall,
    clearError: store.clearError,
    setVoiceStatus: store.setVoiceStatus,
    setVoiceAudioLevel: store.setVoiceAudioLevel,
    setVoiceContinuousListening: store.setVoiceContinuousListening,
    sendVoiceInput: store.sendVoiceInput,
    clearVoiceTtsAudio: store.clearVoiceTtsAudio,
    setVoiceTtsAudio: store.setVoiceTtsAudio,
    runShellCommand: store.runShellCommand,
    abortShellCommand: store.abortShellCommand,
    clearTerminal: store.clearTerminal,

    // Engine actions
    createDemoScene: store.createDemoScene,
    sendSceneIntent: store.sendSceneIntent,
  }
}
