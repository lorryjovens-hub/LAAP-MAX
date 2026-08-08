package org.laap.mobile.speech

import android.content.Context
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * 语音对话环 —— 豆包 / GPT 式端到端语音对话驱动 Agent 执行任务。
 *
 * 设计文档：docs/specs/voice-conversation-engine.md
 *
 * 复用现有积木，只编排"发送 → 播报 → 重听"闭环：
 *
 *   IDLE ──startConversation──▶ LISTENING ──onFinalTranscript──▶ THINKING
 *    ▲                                                              │
 *    │ stopConversation()              onStreamingChunk(首个 chunk)  │
 *    │                                                                ▼
 *    │  onPlaybackFinished ──delay──▶ VOICING ◀── onStreamEnd(flush)│
 *    │                                                               │
 *    └───────────────────────────────────────────────────────────────┘
 *   (barge-in: VOICING ──interrupt──▶ LISTENING)
 *
 * 状态语义：
 *  - [IDLE]       未进入对话模式。
 *  - [LISTENING]  聆听中，等待完整句（ASR final）。
 *  - [THINKING]   已发送给 Agent，Agent 执行 tool calls / 在生成回复。
 *  - [VOICING]    正在流式播报回复，播完自动回到 LISTENING。
 *
 * 与 [ChatViewModel] 的解耦：本引擎不依赖 UI 层。用户整句的发送通过
 * [onSendRequest] 回调由 ChatScreen 接线注入（绑定 sendMessage）；流式回复
 * 由 ChatScreen 在流式 chunk 到达时调用 [onStreamingChunk] / [onStreamEnd]。
 *
 * M1 固定系统 ASR（[SpeechRecognitionManager] 的 "system" 引擎）+ 系统 TTS
 * （经 [ReadAloudPlayer] 按已解析的 Voice Output 选择路由，含云端回退）。
 * 非线程安全；除特别说明外从主线程调用。
 */
object VoiceConversationEngine {

    private const val TAG = "VoiceConvEngine"

    /** 播报结束后距重新聆听的静默窗口（ms），避免误触发。 */
    private const val RESUME_DELAY_MS = 700L

    enum class State { IDLE, LISTENING, THINKING, VOICING }

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    private val _state = MutableStateFlow(State.IDLE)
    val state: StateFlow<State> = _state.asStateFlow()

    /**
     * 用户整句发送出口。由 ChatScreen 接线注入（绑定 ChatViewModel.sendMessage）。
     * 引擎在 [LISTENING] 收到非空 final 转录时调用。
     */
    @Volatile
    var onSendRequest: ((String) -> Unit)? = null

    private var readAloud: ReadAloudPlayer? = null
    private var resumeJob: Job? = null

    /** 是否处于对话模式（供 UI 渲染菜单/提示条）。 */
    val isActive: Boolean get() = _state.value != State.IDLE

    /**
     * 进入对话模式，开始聆听。若已在对话模式则幂等。
     * 需要应用 Context 以创建 [ReadAloudPlayer]。
     */
    fun startConversation(context: Context) {
        if (_state.value != State.IDLE) return
        _state.value = State.LISTENING
        readAloud = ReadAloudPlayer(context.applicationContext).also {
            it.onPlaybackFinished = { onPlaybackFinished() }
        }
        startListening()
    }

    /** 退出对话模式：停止识别、播报、待重听任务。 */
    fun stopConversation() {
        resumeJob?.cancel()
        resumeJob = null
        readAloud?.stop()
        // 播报播放器随会话销毁，避免泄漏。
        readAloud?.shutdown()
        readAloud = null
        stopListening()
        _state.value = State.IDLE
    }

    /** barge-in：用户又说话时立即停止播报，切回聆听。 */
    fun interrupt() {
        if (_state.value != State.VOICING) return
        resumeJob?.cancel()
        resumeJob = null
        readAloud?.stop()
        _state.value = State.LISTENING
        startListening()
    }

    /**
     * 流式回复 chunk 到达时由 ChatScreen 调用。THINKING 收到首个非空 chunk
     * 自动转 VOICING；VOICING 时喂给 [ReadAloudPlayer] 逐句朗读。
     */
    fun onStreamingChunk(chunk: String) {
        if (chunk.isEmpty()) return
        if (_state.value == State.THINKING) _state.value = State.VOICING
        if (_state.value == State.VOICING) readAloud?.appendText(chunk)
    }

    /** 流式回复结束，由 ChatScreen 调用；flush 尾句。 */
    fun onStreamEnd() {
        if (_state.value == State.VOICING) readAloud?.flush()
    }

    // ── 内部 ──────────────────────────────────────────────

    private fun startListening() {
        SpeechRecognitionManager.selectEngine("system")
        SpeechRecognitionManager.startRecording(
            onPartialOrFinal = { text, isFinal -> if (isFinal) onFinalTranscript(text) },
            onError = { error, _ ->
                Log.w(TAG, "ASR error: $error")
                if (_state.value == State.LISTENING) {
                    // 静默/临时错误：短暂延迟后重试聆听，不打断对话。
                    resumeJob = scope.launch {
                        delay(RESUME_DELAY_MS)
                        if (_state.value == State.LISTENING) startListening()
                    }
                }
            },
        )
    }

    private fun stopListening() {
        SpeechRecognitionManager.cancelRecording()
    }

    private fun onFinalTranscript(text: String) {
        if (_state.value != State.LISTENING) return
        val trimmed = text.trim()
        if (trimmed.isEmpty()) {
            // 空转录不要发送，继续聆听。
            startListening()
            return
        }
        _state.value = State.THINKING
        onSendRequest?.invoke(trimmed)
    }

    private fun onPlaybackFinished() {
        if (_state.value != State.VOICING) return
        // 播完短暂静默后重听。
        resumeJob = scope.launch {
            delay(RESUME_DELAY_MS)
            if (_state.value == State.VOICING) {
                _state.value = State.LISTENING
                startListening()
            }
        }
    }
}