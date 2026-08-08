package org.laap.mobile.ui.chat

// [T-android-split-chat] Small UI-state toggle methods extracted from
// ChatViewModel as extension functions (verbatim): tool-detail sheet,
// browser sheet, memory sheet, attachment list. The 4 backing state fields
// were flipped private->internal. No logic change.

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.compose.foundation.lazy.LazyListState
import org.laap.mobile.agent.Level
import org.laap.mobile.agent.ToolLoopDetector
import org.laap.mobile.browser.BrowserActionInput
import org.laap.mobile.browser.BrowserTabPool
import org.laap.mobile.data.db.MessageEntity
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Compress
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.Psychology
import androidx.compose.material.icons.outlined.Build
import androidx.compose.material.icons.outlined.Extension
import org.laap.mobile.data.BPETokenizer
import org.laap.mobile.data.ContextOffload
import org.laap.mobile.data.ContextPolicy
import org.laap.mobile.logging.AppLogger
import org.laap.mobile.data.FileMentionIndex
import org.laap.mobile.data.db.CompactMarkerEntity
import org.laap.mobile.data.model.AgentContentPart
import org.laap.mobile.data.model.AgentToolDefinition
import org.laap.mobile.data.model.LLMMessage
import org.laap.mobile.data.model.LLMModel
import org.laap.mobile.data.model.LLMStreamChunk
import org.laap.mobile.data.model.LLMUsage
import org.laap.mobile.data.model.ModelGroup
import org.laap.mobile.data.model.ThinkingLevel
import org.laap.mobile.R
import org.laap.mobile.data.repository.ChatRepository
import org.laap.mobile.data.repository.MemoryRepository
import org.laap.mobile.data.repository.ProviderRepository
import org.laap.mobile.provider.ImageBudget
import org.laap.mobile.provider.LLMProvider
import org.laap.mobile.provider.ProviderFactory
import org.laap.mobile.sandbox.ExecutionCoordinator
import org.laap.mobile.terminal.LaapOpenUrlBroker
import org.laap.mobile.terminal.LaapUrlMarker
import org.laap.mobile.tools.AgentTools
import org.laap.mobile.tools.FileEditTool
import org.laap.mobile.tools.FileReadTool
import org.laap.mobile.tools.FileWriteTool
import org.laap.mobile.tools.MemoryTools
import org.laap.mobile.tools.ReadImageTool
import org.laap.mobile.tools.ToolExecutionResult
import org.laap.mobile.offload.OffloadPermissionManager
import org.laap.mobile.service.SessionActivityTracker
import org.laap.mobile.service.SessionConcurrencyManager
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.coroutines.yield
import org.json.JSONObject
import java.io.ByteArrayOutputStream

internal fun ChatViewModel.openToolDetail(toolBlockId: String) {
    _selectedToolDetailId.value = toolBlockId
}

internal fun ChatViewModel.closeToolDetail() {
    _selectedToolDetailId.value = null
}

internal fun ChatViewModel.toggleBrowserSheet() {
    val opening = !_showBrowserSheet.value
    if (opening) browserTabPool.ensureTabForUI()
    _showBrowserSheet.value = opening
}

internal fun ChatViewModel.dismissBrowserSheet() {
    _showBrowserSheet.value = false
}

/**
 * Open the session browser sheet, focused on the tab whose URL matches
 * [url]. If no pool tab currently has that URL, a new tab is created and
 * loaded. Used by the tool-call preview's globe button so the agent's
 * existing browser_use page is reused when available instead of spawning
 * a duplicate tab.
 */
internal fun ChatViewModel.openBrowserSheetForUrl(url: String) {
    if (url.isBlank()) {
        browserTabPool.ensureTabForUI()
    } else {
        browserTabPool.selectOrCreateTabForURL(url)
    }
    _showBrowserSheet.value = true
}

internal fun ChatViewModel.toggleMemorySheet() {
    _showMemorySheet.value = !_showMemorySheet.value
}

internal fun ChatViewModel.dismissMemorySheet() {
    _showMemorySheet.value = false
}

internal fun ChatViewModel.addAttachment(attachment: InputAttachment) {
    _attachments.value = _attachments.value + attachment
}

internal fun ChatViewModel.removeAttachment(id: String) {
    _attachments.value = _attachments.value.filter { it.id != id }
}

internal fun ChatViewModel.clearAttachments() {
    _attachments.value = emptyList()
}
