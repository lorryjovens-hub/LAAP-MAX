package org.laap.mobile.ui.ide

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import org.laap.mobile.data.db.ide.ProjectEntity
import org.laap.mobile.ide.ProjectManager

/**
 * VM for [IdeHomeScreen]. Exposes the live project list (DB-backed) and
 * `create(name, templateId)` / `delete(id)` entry points. Navigation to
 * the project workspace is delegated back to the screen via the
 * `onProjectCreated` callback — the VM stays navigation-agnostic.
 */
class IdeHomeViewModel(
    private val projectManager: ProjectManager,
) : ViewModel() {

    val projects: StateFlow<List<ProjectEntity>> = projectManager.observeProjects()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = emptyList(),
        )

    fun createProject(name: String, templateId: String, onCreated: (String) -> Unit) {
        viewModelScope.launch {
            val entity = projectManager.create(name, templateId)
            onCreated(entity.id)
        }
    }

    fun deleteProject(id: String) {
        viewModelScope.launch { projectManager.delete(id) }
    }

    companion object {
        fun factory(projectManager: ProjectManager): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T {
                    return IdeHomeViewModel(projectManager) as T
                }
            }
    }
}
