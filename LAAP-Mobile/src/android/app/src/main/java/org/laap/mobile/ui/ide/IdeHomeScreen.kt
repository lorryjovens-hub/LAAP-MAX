package org.laap.mobile.ui.ide

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Public
import androidx.compose.material.icons.outlined.Code
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import org.laap.mobile.LaapApp
import org.laap.mobile.data.db.ide.ProjectEntity
import org.laap.mobile.ide.ProjectTemplates
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * IDE home: project list + New-Project FAB.
 *
 * Each row taps into [onOpenProject]; long-press / trailing icon deletes
 * after the standard AlertDialog confirm (in-place, no separate screen).
 *
 * Empty state shows a friendly hint with the same FAB so the first-run
 * user doesn't have to scan the toolbar.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun IdeHomeScreen(
    onOpenProject: (projectId: String) -> Unit,
    onOpenCommunity: () -> Unit,
    onBack: () -> Unit,
) {
    val app = androidx.compose.ui.platform.LocalContext.current.applicationContext as LaapApp
    val vm: IdeHomeViewModel = viewModel(factory = IdeHomeViewModel.factory(app.projectManager))
    val projects by vm.projects.collectAsState()

    var showCreateDialog by remember { mutableStateOf(false) }
    var pendingDelete by remember { mutableStateOf<ProjectEntity?>(null) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("IDE") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Outlined.Code, contentDescription = "Back")
                    }
                },
                actions = {
                    // [community] entry to the LAAP Community (browse/play/publish).
                    IconButton(onClick = onOpenCommunity) {
                        Icon(Icons.Filled.Public, contentDescription = "社区")
                    }
                },
            )
        },
        floatingActionButton = {
            FloatingActionButton(onClick = { showCreateDialog = true }) {
                Icon(Icons.Filled.Add, contentDescription = "New project")
            }
        },
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            if (projects.isEmpty()) {
                EmptyStateHint(onCreate = { showCreateDialog = true })
            } else {
                LazyColumn(Modifier.fillMaxSize()) {
                    items(projects, key = { it.id }) { project ->
                        ProjectRow(
                            project = project,
                            onClick = { onOpenProject(project.id) },
                            onDelete = { pendingDelete = project },
                        )
                    }
                }
            }
        }
    }

    if (showCreateDialog) {
        CreateProjectDialog(
            onDismiss = { showCreateDialog = false },
            onConfirm = { name, templateId ->
                showCreateDialog = false
                vm.createProject(name, templateId) { id -> onOpenProject(id) }
            },
        )
    }

    pendingDelete?.let { target ->
        androidx.compose.material3.AlertDialog(
            onDismissRequest = { pendingDelete = null },
            title = { Text("Delete project?") },
            text = {
                Text("Delete \"${target.name}\"? Files in /var/laap/projects/${target.id}/ will be removed.")
            },
            confirmButton = {
                androidx.compose.material3.TextButton(onClick = {
                    vm.deleteProject(target.id)
                    pendingDelete = null
                }) { Text("Delete") }
            },
            dismissButton = {
                androidx.compose.material3.TextButton(onClick = { pendingDelete = null }) {
                    Text("Cancel")
                }
            },
        )
    }
}

@Composable
private fun ProjectRow(
    project: ProjectEntity,
    onClick: () -> Unit,
    onDelete: () -> Unit,
) {
    val template = remember(project.templateId) { ProjectTemplates.byId(project.templateId) }
    val dateText = remember(project.lastOpenedAt) {
        SimpleDateFormat("MMM d, HH:mm", Locale.getDefault()).format(Date(project.lastOpenedAt))
    }
    ListItem(
        leadingContent = {
            Icon(
                Icons.Outlined.Code,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.size(24.dp),
            )
        },
        headlineContent = {
            Text(project.name, fontWeight = FontWeight.SemiBold)
        },
        supportingContent = {
            Column {
                Text(
                    template?.displayName ?: project.templateId,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Text(dateText, style = MaterialTheme.typography.bodySmall)
            }
        },
        trailingContent = {
            IconButton(onClick = onDelete) {
                Icon(Icons.Filled.Delete, contentDescription = "Delete project")
            }
        },
        modifier = Modifier.clickable(onClick = onClick),
    )
}

@Composable
private fun EmptyStateHint(onCreate: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Icon(Icons.Outlined.Code, contentDescription = null, modifier = Modifier.size(56.dp))
        Text(
            "No projects yet",
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.padding(top = 12.dp),
        )
        Text(
            "Tap + to create one from a template.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 4.dp),
        )
    }
}
