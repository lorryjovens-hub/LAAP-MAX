package org.laap.mobile.ui.ide

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.laap.mobile.data.db.ide.ProjectEntity
import org.laap.mobile.data.db.ide.RunConfigEntity
import org.laap.mobile.ide.ProjectManager
import org.laap.mobile.ide.ProjectRunManager
import org.laap.mobile.ide.ProjectTemplates
import java.io.File

/**
 * State for the Files tab. Recursive depth-1 listing of the project dir.
 * (MVP — no nested navigation; the user just sees top-level files plus
 * one level of subdirectory contents, sufficient for the templates we ship.)
 */
data class FilesTabState(
    val entries: List<FileEntry> = emptyList(),
    val isLoading: Boolean = false,
)

data class FileEntry(
    val relativePath: String,
    val name: String,
    val isDirectory: Boolean,
    val size: Long,
)

/** State for the Editor tab. */
data class EditorTabState(
    val openFile: String? = null,
    val content: String = "",
    val savedContent: String = "",
    val languageId: String = "text",
) {
    val isDirty: Boolean get() = content != savedContent
}

/** State for the Run tab. */
data class RunTabState(
    val runConfigs: List<RunConfigEntity> = emptyList(),
    val selectedConfigId: String? = null,
    val isRunning: Boolean = false,
    val outputLines: List<String> = emptyList(),
    val previewUrl: String? = null,
)

/**
 * Backs the [ProjectWorkspaceScreen]. Owns three independent sub-states
 * (Files / Editor / Run) so each tab can render off its own slice
 * without recomposing the whole tree.
 */
class ProjectWorkspaceViewModel(
    private val projectId: String,
    private val appContext: Context,
    private val projectManager: ProjectManager,
    private val runManager: ProjectRunManager,
) : ViewModel() {

    private val _project = MutableStateFlow<ProjectEntity?>(null)
    val project: StateFlow<ProjectEntity?> = _project.asStateFlow()

    private val _files = MutableStateFlow(FilesTabState(isLoading = true))
    val files: StateFlow<FilesTabState> = _files.asStateFlow()

    private val _editor = MutableStateFlow(EditorTabState())
    val editor: StateFlow<EditorTabState> = _editor.asStateFlow()

    private val _run = MutableStateFlow(RunTabState())
    val run: StateFlow<RunTabState> = _run.asStateFlow()

    /** Host directory for this project. */
    private val projectHostDir: File
        get() = projectManager.hostDirFor(projectId)

    init {
        loadProject()
        refreshFiles()
        loadRunConfigs()
        collectOutput()
    }

    private fun loadProject() {
        viewModelScope.launch {
            _project.value = projectManager.get(projectId)
            projectManager.touchOpenedAt(projectId)
        }
    }

    /** Re-list the project dir (depth-1: top-level + one nested level). */
    fun refreshFiles() {
        viewModelScope.launch {
            _files.value = _files.value.copy(isLoading = true)
            val entries = withContext(Dispatchers.IO) {
                val root = projectHostDir
                if (!root.exists()) return@withContext emptyList()
                val out = mutableListOf<FileEntry>()
                root.listFiles()?.sortedBy { it.name }?.forEach { top ->
                    val rel = top.name
                    out += FileEntry(
                        relativePath = rel,
                        name = top.name,
                        isDirectory = top.isDirectory,
                        size = if (top.isDirectory) 0 else top.length(),
                    )
                    if (top.isDirectory) {
                        top.listFiles()?.sortedBy { it.name }?.forEach { nested ->
                            out += FileEntry(
                                relativePath = "$rel/${nested.name}",
                                name = nested.name,
                                isDirectory = nested.isDirectory,
                                size = if (nested.isDirectory) 0 else nested.length(),
                            )
                        }
                    }
                }
                out
            }
            _files.value = FilesTabState(entries = entries, isLoading = false)
        }
    }

    fun openFile(relativePath: String) {
        viewModelScope.launch {
            val file = File(projectHostDir, relativePath)
            val content = withContext(Dispatchers.IO) {
                if (file.exists()) file.readText() else ""
            }
            val template = _project.value?.let { ProjectTemplates.byId(it.templateId) }
            val lang = template?.languageId ?: languageForExtension(file.extension)
            _editor.value = EditorTabState(
                openFile = relativePath,
                content = content,
                savedContent = content,
                languageId = lang,
            )
        }
    }

    fun updateContent(newContent: String) {
        _editor.value = _editor.value.copy(content = newContent)
    }

    /** Persist current editor buffer to disk. No-op if no file is open. */
    fun saveOpenFile() {
        val state = _editor.value
        val rel = state.openFile ?: return
        viewModelScope.launch {
            withContext(Dispatchers.IO) {
                val target = File(projectHostDir, rel)
                target.parentFile?.mkdirs()
                target.writeText(state.content)
            }
            _editor.value = state.copy(savedContent = state.content)
            refreshFiles()
        }
    }

    private fun loadRunConfigs() {
        viewModelScope.launch {
            val configs = runManager.runConfigsForProject(projectId)
            val defaultId = configs.firstOrNull { it.isDefault == 1 }?.id
                ?: configs.firstOrNull()?.id
            _run.value = _run.value.copy(
                runConfigs = configs,
                selectedConfigId = defaultId,
            )
        }
    }

    fun selectRunConfig(id: String) {
        _run.value = _run.value.copy(selectedConfigId = id)
    }

    fun startRun() {
        val configId = _run.value.selectedConfigId ?: return
        if (_run.value.isRunning) return
        _run.value = _run.value.copy(
            isRunning = true,
            outputLines = emptyList(),
            previewUrl = null,
        )
        viewModelScope.launch {
            val config = runManager.startRun(projectId, configId)
            val url = runManager.previewUrlNow(projectId)
            _run.value = _run.value.copy(
                isRunning = false,
                previewUrl = url,
            )
            if (config == null) {
                appendOutput("[no run config found]")
            }
        }
    }

    fun stopRun() {
        runManager.stopRun(projectId)
        // isRunning flips false from startRun's coroutine as soon as the
        // coordinator call returns; but stop can land first, so mark here too.
        _run.value = _run.value.copy(isRunning = false)
    }

    private fun collectOutput() {
        viewModelScope.launch {
            runManager.tailOutput(projectId).collect { line ->
                appendOutput(line)
            }
        }
    }

    private fun appendOutput(line: String) {
        val current = _run.value.outputLines
        // Cap the in-memory buffer so a long-running dev server doesn't
        // grow it without bound. 2000 lines ≈ 80–200 KB depending on width.
        val next = if (current.size >= 2_000) {
            current.drop(current.size - 1_999) + line
        } else {
            current + line
        }
        _run.value = _run.value.copy(outputLines = next)
    }

    companion object {
        fun factory(
            projectId: String,
            appContext: Context,
            projectManager: ProjectManager,
            runManager: ProjectRunManager,
        ): ViewModelProvider.Factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                return ProjectWorkspaceViewModel(
                    projectId, appContext, projectManager, runManager,
                ) as T
            }
        }

        /** Maps a file extension to a language id understood by SyntaxHighlighter. */
        fun languageForExtension(ext: String): String = when (ext.lowercase()) {
            "html", "htm" -> "html"
            "css" -> "css"
            "js", "mjs", "cjs", "jsx" -> "javascript"
            "ts", "tsx" -> "typescript"
            "json" -> "json"
            "py" -> "python"
            "kt", "kts" -> "kotlin"
            "java" -> "java"
            "sh", "bash" -> "bash"
            "md", "markdown" -> "markdown"
            else -> "text"
        }
    }
}
